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
3. **LLM (Fase 5, v0 entregue)** — interpreta e conversa, mas **nunca faz contas**:
   **Claude Opus 4.8** via *tool use* (`app/assistant.py`) chama os motores (simulação,
   Monte Carlo, decisão), que calculam de verdade, e narra os números retornados. Sem
   chave de IA, um narrador determinístico usa os mesmos motores — o princípio "nunca
   inventar números" vale nos dois caminhos.

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

## Núcleo de simulação (5 motores + orquestrador)

Estes são os motores determinísticos sobre os quais todo o resto se apoia. O catálogo
completo dos motores de decisão/raciocínio vem logo abaixo.

| Motor | Pacote | Entrada → Saída |
|------|--------|-----------------|
| Fenológico | `phenology.py` | clima + cultivar → datas de VE…R8 (graus-dia) |
| Hídrico | `water_balance.py` | clima + solo + fenologia → estresse hídrico por estádio |
| Janela (ZARC) | `sowing_window.py` | município + data → penalidade de produtividade |
| Produtividade (IPPD) | `yield_model.py` | potencial × fatores → sc/ha ± incerteza, decomposto |
| Econômico | `economics.py` | custos + preço + produtividade → lucro, ROI, break-even |
| **Orquestrador** | `simulate.py` | cenário → resultado completo do Laboratório Virtual |

## Catálogo de motores v1.0 (responsabilidade única por motor)

Acima do núcleo de simulação, a plataforma evoluiu para um **copiloto de decisão**. Cada
motor tem **uma** responsabilidade e conversa com os demais por interfaces de dados (dicts/
dataclasses), com baixo acoplamento. Todos partem do mesmo núcleo determinístico.

| Camada | Motores | Responsabilidade |
|--------|---------|------------------|
| **Núcleo determinístico** | `phenology` · `water_balance` · `sowing_window` · `yield_model` (IPPD) · `economics` · **`simulate`** | Calcular a safra: datas, água, janela, produtividade ± , economia. |
| **Conhecimento** | `kb` (loader) · `reference` (constantes, sync da KB) · `data/knowledge/*.json` | Coeficientes, preços, cadeias de impacto e fontes — auditáveis e citados. |
| **Risco & cenários** | `montecarlo` · `scenario_search` · `counterfactual` | Distribuição de resultados (ENSO), melhor plano, "e se…". |
| **Decisão** | `decision` (avalia intervenções) · `priorities` (fila por urgência + Decision Value) · `fertility` · `budget` | Transformar análise em ações priorizadas por retorno. |
| **Veracidade dos dados** | `provenance` (primitivas de alavancagem) · `data_sources` (**`accuracy_report`** — motor único) · `missing_info` | Quão confiável é o dado, o que medir primeiro, qual dado pedir. |
| **Raciocínio** | `reasoning` (hipóteses + impact graph ponderado) · `radar` (copiloto/dimensões) · `briefing` | Diagnosticar *por quê* e responder as 4 perguntas. |
| **Evidências & aprendizado** | `evidence` (confiança/corroboração) · `interactions` (evento→consequência) · `knowledge` (calibração) · `personality` · `memory` | A safra vira evidência; o talhão aprende e recorda. |
| **Estado unificado** | **`state`** (`world_state` — fonte única) · `crop_plan` (fase do ciclo) | Reúne tudo num só estado de realidade que as vistas consomem. |

**Fonte única de verdade.** `state.world_state` roda `simulate` e `accuracy_report` **uma
vez** e os compartilha com `radar`, `reasoning` e `missing_info` (parâmetros `sim`/`acc`).
Assim todas as vistas veem exatamente os mesmos números, sem recálculo.

**Veracidade dos dados = um motor só.** `data_sources.accuracy_report` é o único ponto que
mede confiança/lacunas; `provenance` fornece apenas as primitivas (pesos, scores e a
alavancagem por perturbação) que ele usa. O briefing e o State consomem esse mesmo motor.

## Fluxo de dados (entrada → decisão → interface)

```
Entrada (cenário do talhão)
   ↓  validação (Pydantic, schemas.py)
   ↓  proveniência efetiva (_with_climate_prov: clima detectado + inferência do conteúdo)
Observações (evidências reais: chuva, ferrugem, estande…)  ──┐
   ↓                                                          │ realimentam
Estado da safra  (state.world_state: simulate + accuracy 1×)  │
   ↓                                                          │
Reasoning (hipóteses + impact graph)  ·  Diagnóstico          │
   ↓                                                          │
Simulações (Monte Carlo, contrafactual, melhor plano)         │
   ↓                                                          │
Decision Engine (priorities: fila por urgência + Decision Value)
   ↓
Interface (painéis = apenas apresentação; nenhuma lógica de negócio)
```

**Regra de ouro:** nenhum painel faz conta. Toda lógica vive nos motores; a UI só
apresenta o estado e, se algo não melhora uma decisão do agricultor, fica no backend.

## Contrato de recomendação (formato único)

Toda recomendação ao agricultor — venha do Radar, do Briefing ou da fila de decisão —
carrega o **mesmo conjunto de campos**, originados em `decision.recommend_decisions` (a
fonte) e formatados por `priorities.prioritized_actions`:

| Campo | Significado |
|------|-------------|
| `acao` / `porque` | a ação sugerida e a justificativa técnica |
| `impacto_sc_ha` / `impacto_rs` | impacto esperado em produtividade e em R$/ha |
| `custo_per_ha` / `roi` | custo da ação e retorno sobre o investimento |
| `probabilidade` | chance de melhorar o lucro (Monte Carlo pareado) |
| `urgencia` | 0–100 = retorno × prazo × confiança (ordem da fila) |
| `veredito` | Decision Value: `recomendar` / `avaliar` (o que não vale é filtrado) |
| `prazo` / `janela_status` | quando agir e se a janela ainda está aberta (estado da safra) |

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
