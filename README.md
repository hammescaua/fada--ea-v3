# 🌱 FADA EA v3 — Copiloto Agronômico da Soja (Noroeste do RS)

**Gêmeo Digital vivo de cada talhão de soja**, que vira um **copiloto de decisão**: em vez
de uma "caixa-preta" que cospe um número, o FADA **decompõe** a produtividade esperada,
**diagnostica** por que ela é o que é, **prioriza** as ações por retorno e **aprende** com
cada safra — sempre explicando o porquê, o impacto esperado e o quanto se pode confiar.

> **Filosofia:** primeiro um **motor agronômico determinístico e explicável** (fenologia,
> FAO-56, ZARC, CQFS), com cada coeficiente **citado**. A IA entra *acima*, como correção
> personalizada por talhão — **nunca no centro, nunca inventando números**.

A "estrela do norte": ao abrir, o agricultor vê **as 4 respostas que importam** — qual o
maior risco hoje, qual a melhor decisão agora, quanto ela vale e por quê (com a confiança).

---

## O que a plataforma faz

- **🛰️ Radar da safra** — saúde em 6 dimensões (Solo, Clima, Sanidade, Nutrição, Mercado,
  Execução), as 4 respostas-chave e a **fila de decisão por urgência** (o que fazer
  primeiro, com impacto em sc/ha e R$, ROI, prazo e confiança).
- **🔬 Diagnóstico** — pensa como agrônomo: **hipóteses** ranqueadas para *por que não colho
  mais*, cada uma com a **cadeia de impacto** (causa → efeito → … → produtividade), a
  probabilidade, a controlabilidade e o que medir para confirmar.
- **📅 Acompanhamento ao vivo** — passo-a-passo por fase do ciclo (preparo → semeadura →
  vegetativo → reprodutivo → colheita), com a base científica de cada manejo.
- **⚖️ Plano vs. Realidade** — registra-se o que aconteceu (chuva, ferrugem, estande) e o
  gêmeo **realimenta o número** (ex.: aplicação lavada por chuva vale menos), com fonte.
- **🧬 Personalidade do talhão & Memória** — traços aprendidos a cada safra + *"esta safra
  está 87% parecida com 2024/25"*.
- **🎲 Risco & cenários** — Monte Carlo (com outlook **ENSO** El Niño/La Niña), **melhor
  plano** (busca data × população × fungicida) e **contrafactuais** ("e se…").
- **🎯 Precisão & dados que faltam** — quão verídico é cada dado para *este* talhão e o que
  medir primeiro para reduzir a incerteza.
- **💬 Assistente** — Claude Opus 4.8 via *tool use* narra os números dos motores (nunca
  calcula); sem chave de IA, um narrador determinístico responde dos mesmos motores.

Tudo personalizado por talhão (solo, clima do ponto, cultivar, histórico) e **honesto**
sobre a própria confiança.

---

## Arquitetura — o cérebro

```
Next.js (cockpit do copiloto)               apps/web        ← painéis SÓ apresentam
        │  REST
FastAPI (serviços + clima + IA)             apps/api
        │
agro_engine (o cérebro — Python puro)       packages/agro_engine
   núcleo determinístico → estado único → raciocínio → decisão → aprendizado
        │
PostgreSQL + PostGIS (gêmeo digital)        infra/docker-compose.yml
```

O `state.world_state` é a **fonte única de verdade**: roda a simulação e a análise de
acurácia uma vez e as compartilha com todos os motores — consistência total, sem recálculo.
Catálogo completo dos motores por responsabilidade em [`docs/arquitetura.md`](docs/arquitetura.md).

Stack 100% open-source / custo mínimo: **MapLibre** (sem Mapbox), **Open-Meteo / NASA
POWER** (clima gratuito), **PostGIS** self-host.

---

## Estado — v1.0 (consolidada, pronta para validação com agricultores)

✅ **31 motores** organizados por responsabilidade única, sobre um núcleo determinístico
(fenologia GDD · água FAO-56 · janela ZARC · IPPD · economia).
✅ **Base de conhecimento auditável** (coeficientes, preços, cadeias de impacto, regras de
interação) com **fonte citada** e teste de consistência.
✅ **Camada de evidências** (tudo vira observação com confiança), **Knowledge Engine**
(calibra previsto×real por talhão) e os 5 motores do copiloto: **State, Reasoning,
Decision Queue, Memory, Missing Information**.
✅ **124 testes** no motor passando · web e API buildam · fluxo ponta-a-ponta verificado no
PostGIS (criar fazenda → talhão → solo → safra → colheita → calibração → memória).

Matrizes do NO-RS cobertas: água/déficit, **ENSO**, ferrugem, fertilidade P/K/calagem,
cultivar, ZARC, população, pragas, daninhas, compactação, **nematoides, rotação** +
calibração por talhão.

🔜 Próximas fases (não nesta versão): satélite Sentinel-2/NDVI, import de monitor de
colheita, ML (CatBoost) sobre os mesmos atributos. Ver [`docs/roadmap.md`](docs/roadmap.md).

---

## Como rodar (dev)

Pré-requisitos: Docker, Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
make install      # instala engine, api e web
make db-up        # sobe o PostGIS
make migrate      # cria o schema
make api          # API em http://localhost:8000  (docs em /docs)
make web          # web em http://localhost:3000
make test         # 124 testes do motor agronômico
```

O cockpit funciona **sem banco** (o motor é stateless); o PostGIS é necessário só para a
persistência do gêmeo (fazendas, talhões, safras, evidências). Sem `ANTHROPIC_API_KEY`, o
assistente usa o narrador determinístico. **Comece pela página `/guia`** para entender a
plataforma em linguagem de produtor.

---

## Estrutura do repositório

```
apps/
  web/                Next.js (App Router) + MapLibre + Recharts — só apresentação
  api/                FastAPI + SQLAlchemy + PostGIS + Alembic
packages/
  agro_engine/        o cérebro: 31 motores determinísticos + 124 testes
data/
  knowledge/          base de conhecimento auditável (coeficientes, preços, impact graph)
infra/                docker-compose (PostGIS)
docs/                 arquitetura, matrizes do NO-RS, avaliação, fontes, roadmap
```

## Documentação

- [`docs/arquitetura.md`](docs/arquitetura.md) — camadas, **catálogo de motores**, fluxo de dados, contrato de recomendação.
- [`docs/arquitetura-evidencias.md`](docs/arquitetura-evidencias.md) — a camada de evidências e o núcleo de raciocínio (State, Reasoning, Decision Queue, Memory, Missing Information).
- [`docs/matrizes-soja-noroeste-rs.md`](docs/matrizes-soja-noroeste-rs.md) — os drivers de produtividade da região, com fontes.
- [`docs/base-conhecimento.md`](docs/base-conhecimento.md) — de onde vêm os números (coeficientes + preços + evidência por manejo).
- [`docs/acuracia-por-talhao.md`](docs/acuracia-por-talhao.md) — de onde vem cada dado e como torná-lo mais preciso.
- [`docs/avaliacao-produto-e-metodo.md`](docs/avaliacao-produto-e-metodo.md) — avaliação crítica do produto e do método.
- [`docs/modelo-canonico.md`](docs/modelo-canonico.md) · [`docs/modelo-dados.md`](docs/modelo-dados.md) · [`docs/motores-agronomicos.md`](docs/motores-agronomicos.md) · [`docs/fontes-dados.md`](docs/fontes-dados.md) · [`docs/roadmap.md`](docs/roadmap.md).
