# Arquitetura

## Princípio central

A IA **não fica no centro**. O centro é um **motor agronômico determinístico e
explicável**. A IA é uma camada *acima* dele, em três níveis:

1. **Determinístico (atual)** — modelos científicos: fenologia (graus-dia), balanço
   hídrico (FAO-56), curvas de resposta nutricional, janela ZARC, potencial produtivo.
   Tudo baseado em literatura, auditável e calibrável.
2. **Machine Learning (Fase 3)** — Gradient Boosting (CatBoost/LightGBM) que aprende a
   **correção** entre o que o motor prevê e o que o talhão realmente colhe. Um modelo
   por propriedade, e idealmente por talhão.
3. **LLM (Fase 5)** — interpreta e conversa, mas **nunca faz contas**: consulta os
   motores e traduz números em linguagem natural com a justificativa técnica.

Esse desenho cria uma vantagem competitiva que cresce com o tempo: o ativo não é o
código, é o **modelo digital de conhecimento de cada talhão**, refinado a cada safra.

## Camadas

```
┌─────────────────────────────────────────────────────────┐
│  Aplicação Web  (Next.js + MapLibre + Recharts)          │  apps/web
│  Mapa · Laboratório Virtual · Cockpit do talhão          │
├─────────────────────────────────────────────────────────┤
│  Camada de Serviços (FastAPI)                            │  apps/api
│  Simulação · Clima · CRUD · (futuro: IA, relatórios)     │
├─────────────────────────────────────────────────────────┤
│  Motor de Simulação (Python puro)                       │  packages/agro_engine
│  Fenologia · Água · Nutrição · Janela · Sanidade · Econ. │
├─────────────────────────────────────────────────────────┤
│  Banco Geoespacial (PostgreSQL + PostGIS)                │  infra
│  Talhões · Solo · Safras · Manejos · Custos · Clima      │
├─────────────────────────────────────────────────────────┤
│  Fontes externas: Open-Meteo · NASA POWER · ZARC ·       │
│  (futuro) Sentinel-2 · monitor de colheita · sensores    │
└─────────────────────────────────────────────────────────┘
```

## Os cinco motores (+ orquestrador)

| Motor | Pacote | Entrada → Saída |
|------|--------|-----------------|
| Fenológico | `phenology.py` | clima + cultivar → datas de VE…R8 (graus-dia) |
| Hídrico | `water_balance.py` | clima + solo + fenologia → estresse hídrico por estádio |
| Janela (ZARC) | `sowing_window.py` | município + data → penalidade de produtividade |
| Produtividade (IPPD) | `yield_model.py` | potencial × fatores → sc/ha ± incerteza, decomposto |
| Econômico | `economics.py` | custos + preço + produtividade → lucro, ROI, break-even |
| **Orquestrador** | `simulate.py` | cenário → resultado completo do Laboratório Virtual |

## Decisões de stack (solo / custo mínimo)

- **MapLibre GL** em vez de Mapbox (sem custo/chave; basemap OSM).
- **Open-Meteo** (CC-BY, uso comercial, sem chave) como clima padrão; **NASA POWER**
  como alternativa; cache local para nunca reconsultar a cada request.
- **PostGIS** self-host via docker-compose (ou Supabase free tier).
- **Python/FastAPI** porque toda a modelagem científica e a IA futura são Python.
- **`agro_engine` isolado** (sem framework): testável, versionável, exportável.

## Por que stateless na simulação

O endpoint `/simulate` recebe um cenário completo e devolve o resultado sem tocar no
banco. Isso torna o Laboratório Virtual instantâneo e permite usá-lo antes mesmo de o
agricultor cadastrar a propriedade. A persistência (gêmeo digital) é uma camada
separada que alimenta os cenários com dados reais do talhão.
