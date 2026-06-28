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
talhão a cada safra + feature engineering). 33 testes passando.
✅ **API** (`apps/api`): FastAPI expondo `/simulate`, `/sowing-window`, catálogos, e
CRUD de fazendas/talhões em PostGIS. Cliente de clima real (Open-Meteo).
✅ **Web** (`apps/web`): Next.js + MapLibre + Recharts. Mapa do talhão, controles do
cenário e o **Laboratório Virtual** com gráfico waterfall do IPPD, **recomendações de
manejo priorizadas por retorno** (Motor de Decisão), bloco econômico, calendário
fenológico, **análise de risco Monte Carlo** (histograma de lucro + probabilidades) e
comparação "cenário base vs atual".

🔜 Próximas fases: IA personalizada por talhão, satélite (Sentinel-2/NDVI), import de
monitor de colheita/piloto automático, Monte Carlo, assistente de decisão (LLM).
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

- [`docs/arquitetura.md`](docs/arquitetura.md) — camadas, decisões e os 5 motores.
- [`docs/motores-agronomicos.md`](docs/motores-agronomicos.md) — fórmulas e referências.
- [`docs/modelo-dados.md`](docs/modelo-dados.md) — o gêmeo digital no banco.
- [`docs/fontes-dados.md`](docs/fontes-dados.md) — APIs públicas, licenças, ZARC.
- [`docs/metodologia-captacao-dados.md`](docs/metodologia-captacao-dados.md) — onboarding progressivo.
- [`docs/roadmap.md`](docs/roadmap.md) — fases 1 → 5.
