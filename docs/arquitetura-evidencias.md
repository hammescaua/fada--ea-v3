# Arquitetura de Evidências — o gêmeo orientado a eventos

> Mudança conceitual central: **parar de tratar dados como registros e tratá-los como
> evidências**. Cada informação responde a quatro perguntas — *o que aconteceu? onde? com
> que confiança? qual foi a consequência?* — conectadas no tempo e no espaço. A partir
> daí o gêmeo digital deixa de ser um cadastro inteligente e passa a representar a
> realidade da fazenda.

## A camada de evidências (`observations`)

Tudo que acontece no talhão vira uma **Observation**: chuva, NDVI, ferrugem, emergência,
aplicação, praga, colheita, relato do agrônomo. Cada uma carrega:

| Campo | Significado |
|------|-------------|
| `kind` | o que aconteceu (chuva, ndvi, ferrugem, aplicacao, colheita…) |
| `source` | de onde veio (api_clima, satelite, drone, agronomo, nota_fiscal, gps, monitor…) |
| `observed_at` / `geom` | quando e **onde** (ponto georreferenciado) |
| `value` (JSONB) | o valor, livre: `{mm:21}`, `{ndvi:0.74}`, `{severidade:'baixa'}` |
| `confidence` | **o quanto acreditar** (0..1), atribuído pelo Reality Engine |
| `consequence` | o efeito observado (ex.: "eficiência do fungicida caiu após chuva") |

## Reality Engine (`evidence.py`)

Decide *o quanto confiar em cada dado*:
- **confiança por fonte** — drone 0,98 · monitor 0,96 · agrônomo 0,95 · satélite 0,92 ·
  nota fiscal 0,90 · API clima 0,90 · relato do produtor 0,65 · manual 0,50;
- **corroboração** — fontes independentes que confirmam o mesmo fato (kind+dia) **elevam**
  a confiança (cada uma reduz a incerteza pela metade). Ex.: chuva por API (0,90) +
  estação INMET sobe para ~0,94 (verificado).

## Data Quality Engine

`data_quality()` dá nota 0–100 por grupo (solo, clima, fitossanidade, produtividade,
mercado) combinando **completude × confiança**. Diz à IA **quando não confiar** — um grupo
sem evidência fica com nota 0 (honesto), não é mascarado.

## Genética / Personalidade do Talhão (`personality.py`)

Traços **aprendidos** (não cadastrados) das safras e evidências, cada um com confiança,
base e flag *aprendendo*; um **% de conhecimento** cresce com o histórico:
estabilidade produtiva, viés vs. modelo, resposta ao fósforo, risco de ferrugem,
sensibilidade ao atraso no plantio, resiliência hídrica. Com poucas safras, os traços
vêm como "aprendendo" — a ferramenta nunca finge saber mais do que a evidência permite.

## Counterfactual Engine (`counterfactual.py`)

Os "universos paralelos" da safra: *e se eu não tivesse aplicado o fungicida? e se tivesse
plantado 8 dias antes? e se o fósforo estivesse corrigido?* Re-simula com a mudança e mede
o Δ em sc/ha e R$. É simulação causal sobre a safra real, coerente com o resto da
plataforma.

## O que está implementado vs. roadmap (honestidade)

**Implementado e verificado (PostGIS real):** camada `observations`, Reality Engine
(confiança + corroboração), Data Quality Engine, Personalidade do Talhão, Counterfactual
Engine, e a aplicação da calibração por talhão na cascata IPPD.

**No roadmap — deliberadamente NÃO fingido** (exige fontes/infra que ainda não temos; a
camada de evidências já está pronta para recebê-los):
- **Spatial Engine** (talhão → zona → pixel) — a `Observation` já tem `geom` POINT;
  falta a malha de zonas e o pipeline de variabilidade intra-talhão.
- **Sensoriamento remoto** (Sentinel-2 NDVI/EVI, drone) e **máquinas** (monitor de
  colheita/plantadeira, GPS) — entram como `source` da Observation quando houver ingestão.
- **Event bus / Farm OS** completo — hoje a persistência é orientada a eventos no modelo
  de dados; o barramento de eventos em tempo real é evolução de infraestrutura.

A tese da crítica está incorporada: quando tudo é evidência conectada no tempo e no
espaço, os motores de simulação, aprendizado e recomendação ficam mais robustos porque
aprendem com a **sequência de eventos**, não só com o resultado final.
