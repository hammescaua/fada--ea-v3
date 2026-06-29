# Matrizes da soja do Noroeste do RS — os drivers de produtividade

> Pesquisa dos fatores que de fato governam a produtividade da soja no Noroeste gaúcho
> (Planalto Médio, Missões, Alto Uruguai — Santo Ângelo, Ijuí, Cruz Alta, Santa Rosa,
> Panambi, Três de Maio…), com fontes, valores típicos da região e **como cada um entra
> (ou ainda não entra) no FADA**. É o mapa que mantém o gêmeo fiel à realidade local.

## Contexto regional
- **Solos:** predominam **Latossolos e Nitossolos Vermelhos argilosos** (origem basáltica),
  com **Argissolos** em relevo mais movimentado. Argila alta → boa retenção de água, porém
  **alta fixação de fósforo** (óxidos de Fe/Al) e tendência à **acidez**.
- **Clima:** Cfa subtropical úmido; chuva anual ~1.700–1.900 mm, mas **mal distribuída no
  verão** — veranicos em jan/fev coincidem com o enchimento de grãos.
- **Sistema:** plantio direto consolidado; soja após trigo/aveia/cobertura; 2ª safra de
  milho em parte da área.

## As matrizes, por impacto

### 1. Água / déficit hídrico — o fator nº 1
- **Por quê:** o déficit hídrico é a **maior causa de quebra** da soja no RS; a necessidade
  hídrica da cultura é **~450–850 mm/ciclo**, e os estádios mais sensíveis são o
  **florescimento e o enchimento de grãos (R1–R6, crítico R3–R5)**.
- **NO-RS:** veranicos de jan/fev derrubam safras; solo argiloso tampona, mas não elimina.
- **No FADA:** ✅ balanço hídrico **FAO-56** diário com sensibilidade por estádio
  (`water_balance.py`, `WATER_SENSITIVITY_BY_STAGE`), clima real do ponto e Monte Carlo.

### 2. ENSO — El Niño / La Niña
- **Por quê:** no Sul do Brasil, **La Niña → estiagens longas e quebra** (2004/05, 2011/12,
  2019/20, 2021/22); El Niño → chuva acima da média. É o modulador climático nº 1 da região.
- **No FADA:** ✅ adicionado como **driver de risco** (`enso` no Monte Carlo: La Niña 0,74×
  a chuva e +25% de variância; El Niño 1,18×). Permite "planejar para o ano de La Niña".

### 3. Ferrugem-asiática (*Phakopsora pachyrhizi*)
- **Por quê:** doença mais devastadora da soja no Brasil — **perdas de 10% a 80%** sem
  controle. Manejo: fungicida no momento certo + **cultivar tolerante**; respeitar o vazio
  sanitário e o calendário.
- **No FADA:** ✅ fator Doenças (pressão × tolerância da cultivar × nº/eficiência de
  fungicida) + **lavagem por chuva** (rainfastness) na camada de evidências.

### 4. Fertilidade do solo (pH, V%, P, K) e calagem
- **Por quê:** Latossolos ácidos e **P naturalmente baixo** (alta fixação). N vem da
  **fixação biológica** (inoculação), então a ênfase é **P e K**. Exportação ~**12–15 kg
  P₂O₅ e 20–25 kg K₂O por tonelada** de grão. Calagem pela **saturação por bases (V% alvo
  65%)**.
- **No FADA:** ✅ fatores Solo e Nutrição + **motor de fertilidade** (CQFS-RS/SC 2016:
  calagem por V%, P/K por construção+manutenção, ROI amortizado).

### 5. Cultivar (grupo de maturação, potencial, tolerâncias)
- **Por quê:** GMR ~**5.0–6.2** na região; define ciclo, casamento com a janela e tolerância
  a ferrugem **e a nematoides**.
- **No FADA:** ✅ potencial/ciclo/tolerância a doença na cascata e na fenologia GDD.

### 6. Janela de semeadura (ZARC)
- **Por quê:** semear no período que casa R1–R5 com melhor radiação/chuva e foge do veranico
  tardio. **No FADA:** ✅ ZARC por município + penalidade por desvio.

### 7. População, estande e qualidade da semeadura
- **Por quê:** estande define o número de vagens; falhas por umidade/regulagem custam teto.
  **No FADA:** ✅ fator População + **estande observado** sobrepõe o planejado (evidências).

### 8. Pragas (percevejos, lagartas) e daninhas resistentes
- **Por quê:** percevejos (*Euschistus, Dichelops, Nezara*) e lagartas (*Helicoverpa,
  Spodoptera*); **buva e capim-amargoso resistentes** ao glifosato. **No FADA:** ✅ fatores
  Pragas e Daninhas (pressão × controle).

### 9. Compactação / estrutura e acidez subsuperficial (gessagem)
- **Por quê:** tráfego compacta; Al em subsuperfície limita raiz e agrava o déficit hídrico
  (gessagem aprofunda a raiz). **No FADA:** ✅ fator Compactação; ✅ gessagem na evidência de
  manejo (parcial — não modela o ganho radicular em profundidade).

## Lacunas priorizadas (o que falta para ficar ainda mais local)

| Matriz | Status | Plano |
|--------|--------|-------|
| **Nematoides** (cisto *Heterodera glycines*, galha *Meloidogyne*, *Pratylenchus*) — infestação **crescente no RS**, perdas por reboleira | ❌ não modelado | adicionar driver de solo/contexto: pressão (análise de nematoide) × resistência da cultivar × rotação → penalidade de produtividade |
| **Rotação / cultura anterior / cobertura** (palhada, MO, ciclagem, supressão de nematoide/daninha) | ❌ contexto | campo de rotação que modula água (palhada), MO e pressão de nematoide/daninha |
| **Micronutrientes** (Mn, B, Co/Mo) e **enxofre** | parcial | refino do fator Nutrição com micros/S quando houver análise |
| **Geada/granizo** (riscos de cauda) | parcial (ruído do Monte Carlo) | eventos de evidência → penalidade pontual |

Essas três primeiras — **nematoides, rotação e ENSO** — são as que mais diferenciam um
talhão do outro no NO-RS; ENSO já entrou, e nematoide+rotação são o próximo passo de
personalização.

## Fontes
- Embrapa Soja — Tecnologias de Produção de Soja; pesquisa sobre estiagem e mitigação
  (palhada, bioestimulantes).
- CQFS-RS/SC — Manual de Calagem e Adubação para RS e SC, 2016.
- Berlato & Cordeiro — efeitos do El Niño/La Niña sobre a produtividade no RS.
- ZARC/MAPA — Zoneamento Agrícola de Risco Climático.
- Literatura citada na pesquisa (ver links no resumo do projeto).
