# 🌱 FADA EA v3 — Gêmeo Digital da Soja (Noroeste do RS)

Plataforma de apoio à decisão que constrói um **Gêmeo Digital (Digital Twin) vivo de
cada talhão** de soja. Em vez de uma "caixa-preta" que cospe um número, o sistema
**decompõe** a produtividade esperada e mostra *por que* aquele resultado é previsto —
e quanto cada fator (solo, água, nutrição, janela de plantio, sanidade…) contribuiu.

> **Filosofia:** primeiro um **motor agronômico determinístico e explicável**, baseado
> em ciência consolidada (fenologia, FAO-56, ZARC). A **IA entra depois**, como camada
> de *correção* personalizada por talhão, quando houver dados reais de safras — nunca
> no centro.

O diferencial é a personalização: cada talhão tem seu perfil de solo, clima local e
histórico; o agricultor pode rodar um **Laboratório Virtual** — "e se eu plantar 10
dias antes?", "e se reduzir o fungicida?", "vale investir R$180/ha em adubação?" — e
ver, em segundos, o impacto na produtividade (± incerteza) e na rentabilidade.

---

## Estado atual — Marco 1 (vertical slice rodável)

✅ **Motor agronômico v0** (`packages/agro_engine`): fenologia por graus-dia, balanço
hídrico FAO-56, janela de semeadura ZARC, **decomposição IPPD** com intervalo de
confiança, modelo econômico (lucro, ROI, break-even), **simulador Monte Carlo**
(distribuição de lucro e risco de prejuízo), **Motor de Decisão** (prioriza
intervenções por retorno esperado, com probabilidade via Monte Carlo pareado) e
**Knowledge Engine** (calibração previsto-vs-real que aprende a correção de cada
talhão a cada safra) e **Orçamento/fluxo de caixa + impacto por manejo** (quanto cada
ação representa em sc/ha e R$). IPPD com 10 fatores (inclui daninhas, pragas, doenças,
calor). 37 testes passando.
✅ **API** (`apps/api`): FastAPI expondo `/simulate`, `/sowing-window`, catálogos, e
CRUD de fazendas/talhões em PostGIS. Cliente de clima real (Open-Meteo).
✅ **Web** (`apps/web`): Next.js + MapLibre + Recharts. **Cockpit persistido** (criar/
selecionar fazenda e talhão, salvar análise de solo e safras — carrega o talhão no
laboratório), mapa, controles do cenário e o **Laboratório Virtual** com assistente de
chat, gráfico waterfall do IPPD, **recomendações de manejo priorizadas por retorno**,
bloco econômico, calendário fenológico, **análise de risco Monte Carlo** e comparação
"cenário base vs atual".

✅ **Assistente de decisão (Nível 3)**: o "ChatGPT da fazenda" — **Claude Opus 4.8** via
*tool use* consulta os motores e **narra os números, nunca calcula**. Endpoint
`/assistant` + painel de chat. Sem `ANTHROPIC_API_KEY`, um narrador determinístico
responde a partir dos mesmos motores.

🔜 Próximas fases: satélite (Sentinel-2/NDVI), import de monitor de colheita/piloto
automático, motor de causalidade, cockpit talhão-cêntrico persistido.
Ver [`docs/roadmap.md`](docs/roadmap.md).

---

## Arquitetura

```
Next.js (mapa + laboratório virtual)        apps/web
        │  REST
FastAPI (serviços + clima)                  apps/api
        │
agro_engine (motores determinísticos)       packages/agro_engine
        │
PostgreSQL + PostGIS (gêmeo digital)        infra/docker-compose.yml
```

Stack 100% open-source / custo mínimo: **MapLibre** (sem Mapbox), **Open-Meteo /
NASA POWER** (clima gratuito), **PostGIS** self-host. Detalhes em
[`docs/arquitetura.md`](docs/arquitetura.md).

---

## Como rodar (dev)

Pré-requisitos: Docker, Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 20+, pnpm.

```bash
make install      # instala engine, api e web
make db-up        # sobe o PostGIS
make migrate      # cria o schema
make seed         # cultivares + fazenda-demo (opcional)
make api          # API em http://localhost:8000  (docs em /docs)
make web          # web em http://localhost:3000
make test         # testes do motor agronômico
```

O Laboratório Virtual funciona **sem banco** (a simulação é stateless). O banco é
necessário apenas para o cadastro/persistência do gêmeo digital.

---

## Estrutura do repositório

```
apps/
  web/                Next.js (App Router) + MapLibre + Recharts
  api/                FastAPI + SQLAlchemy + PostGIS + Alembic
packages/
  agro_engine/        motor determinístico (fenologia, água, IPPD, economia) + testes
data/
  zarc/               janelas de semeadura ZARC (NO do RS)
  reference/          parâmetros agronômicos da soja (auditáveis)
infra/                docker-compose (PostGIS)
docs/                 arquitetura, modelo de dados, motores, fontes, roadmap, captação
```

## Documentação

- [`docs/modelo-canonico.md`](docs/modelo-canonico.md) — **o método único** (um padrão para todo manejo/variável) + a taxonomia fechada (catálogo de manejos e de variáveis) + o motor de cenários.
- [`docs/base-conhecimento.md`](docs/base-conhecimento.md) — **de onde vêm os números** (coeficientes com fonte + catálogo de insumos/preços + motor de fertilidade).
- [`docs/arquitetura.md`](docs/arquitetura.md) — camadas, decisões e os 5 motores.
- [`docs/motores-agronomicos.md`](docs/motores-agronomicos.md) — fórmulas e referências.
- [`docs/modelo-dados.md`](docs/modelo-dados.md) — o gêmeo digital no banco.
- [`docs/fontes-dados.md`](docs/fontes-dados.md) — APIs públicas, licenças, ZARC.
- [`docs/metodologia-captacao-dados.md`](docs/metodologia-captacao-dados.md) — onboarding progressivo.
- [`docs/roadmap.md`](docs/roadmap.md) — fases 1 → 5.
