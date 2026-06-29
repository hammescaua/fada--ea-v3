# Avaliação crítica — o produto ajuda o produtor? E o método de previsão está bom?

> Análise honesta, no lugar do agricultor do Noroeste do RS, do que o FADA já entrega e
> dos limites reais. Sem marketing: onde ajuda na decisão, onde ainda não, e o caminho para
> aumentar acurácia e personalização.

## 1. No lugar do produtor — ajuda a decidir na safra?

Percorrendo a safra como o agricultor a vive:

| Momento | Pergunta do produtor | O FADA responde hoje? |
|--------|----------------------|------------------------|
| **Pré-safra** | "Quando planto, qual cultivar, qual população, vale calar/adubar?" | **Sim, forte.** Melhor plano (data×população×fungicida), fertilidade com ROI, janela ZARC, resumo da safra. |
| **Planejamento financeiro** | "Quanto invisto, qual meu capital de giro, qual o risco de prejuízo?" | **Sim.** Orçamento, fluxo de caixa, Monte Carlo com P(prejuízo) e agora **outlook ENSO** ("e se for La Niña?"). |
| **Durante a safra** | "Apliquei e choveu — perdi eficácia? Meu estande ficou baixo, e agora?" | **Sim, novo.** Evidências + Plano vs. Realidade ajustam o número e recomendam ação, com fonte. |
| **Decisão pontual** | "Vale a pena mais um fungicida agora?" | **Sim.** Motor de decisão (Δlucro, prob. de retorno) e contrafactuais ("e se…"). |
| **Pós-safra** | "Por que colhi isso? O que mudo no ano que vem?" | **Sim.** Calibração por talhão + personalidade aprendida + aprendizados da linha do tempo. |

**Veredito honesto:** para **planejamento e apoio à decisão**, sim — a ferramenta já guia
o produtor de forma concreta, transparente (todo número é decomposto e tem fonte) e cada
vez mais personalizada. O que ela **ainda não é**: um sistema operacional do dia a dia
(ordens de serviço, estoque, integração com máquinas) nem um previsor "mágico" de
produtividade — e isso é proposital: ela **decide melhor**, não "adivinha".

## 2. O método de previsão — está bom? Dá para aumentar o acerto?

**O método** é um **motor agronômico determinístico e explicável (IPPD)**: parte do
potencial genético e aplica fatores multiplicativos transparentes (solo, nutrição,
compactação, população, janela, água, calor, daninhas, pragas, doenças, **calibração do
talhão**), com incerteza e Monte Carlo para o risco. **Não é caixa-preta** — é o oposto do
que o agricultor desconfia.

**Forças:** explicável (waterfall por fator), fundamentado (Embrapa/CQFS/ZARC/FAO-56 com
fonte por coeficiente), coerente (o impacto de cada manejo sai do mesmo modelo), e
**auto-corrige** por talhão com as safras (encolhimento bayesiano → ML no futuro).

**Limites (honestos):**
- a previsão pontual depende fortemente do **clima da safra**, que é incerto por natureza —
  por isso entregamos **faixa + risco**, não um número seco;
- vários coeficientes são **valores de literatura** (ponto de partida), refinados pela
  calibração só quando há histórico real;
- **falta modelar** nematoides e rotação (ver matrizes) — relevantes no NO-RS.

**Como aumentar acurácia e certeza (alavancas reais, em ordem de retorno):**
1. **Dados reais do talhão** — análise de solo, cultivar real, clima do ponto e manejo
   registrado já levam a precisão de **37% → ~89%** (medido). É a maior alavanca, e está
   pronta.
2. **Clima da safra corrente** — observado+previsão em vez de média histórica (já feito);
   reduz a maior fonte de incerteza conforme a safra avança.
3. **Calibração com histórico** — cada safra encerrada corrige o viés do talhão (medido:
   MAE 7,0 → 4,2 sc/ha com 2 safras) e encolhe a incerteza; melhora ano a ano.
4. **Modelar nematoides + rotação** — fecha as lacunas que mais diferenciam talhões.
5. **Calibração segmentada / ML (Nível 2)** — quando houver dezenas de talhões×safras,
   trocar o encolhimento por CatBoost/LightGBM sobre `season_features`.

## 3. Está personalizado para cada lavoura? (sem ser genérico)

**Sim, e de forma crescente.** A personalização hoje vem de cinco frentes:
- **perfil do talhão** (solo, cultivar, população, manejo) entra direto na cascata;
- **clima do ponto exato** (lat/lon) — não média regional;
- **evidências reais** (chuva, estande, ferrugem) corrigem o número da safra (Plano vs.
  Realidade);
- **personalidade aprendida** (responde a P, risco de ferrugem, estável, propensão a
  lavagem…) com % de conhecimento que cresce;
- **calibração** que ajusta as previsões daquele talhão específico.

A honestidade está embutida: cada variável mostra **se é específica do talhão ou um default
regional**, e a precisão sobe à medida que o produtor preenche o real.

## 4. E se o gargalo for o dado? Estratégia de dados

O gargalo **é** o dado — e a arquitetura foi desenhada para isso:

- **Fontes públicas já integradas (grátis):** clima histórico+previsão do ponto
  (Open-Meteo), ZARC/MAPA (janela), CQFS/Embrapa (coeficientes), CONAB/CEPEA (preços).
- **Dado do produtor (onboarding progressivo):** análise de solo, cultivar, manejo — cada
  um eleva a proveniência automaticamente.
- **Camada de evidências (o ativo que cresce):** **tudo vira observação** com fonte e
  confiança; a cada safra o talhão acumula chuva, estande, ferrugem, aplicações, colheita.
  **Sim — essas evidências e o acompanhamento alimentam o modelo ao longo dos anos**: viram
  calibração, personalidade e regras evento→consequência. Quanto mais safras, mais o gêmeo
  conhece aquele lugar.
- **Pronto para o futuro (roadmap, não fingido):** a `Observation` já aceita `source`
  satélite/drone/monitor e `geom` — quando houver Sentinel-2 (NDVI grátis), monitor de
  colheita ou estação na lavoura, é plugar, não reescrever.

## 5. Veredito e fechamento desta versão

O FADA **já é um apoio real à decisão** para a safra de soja do NO-RS: planeja, simula,
prioriza ação por retorno, mede risco (inclusive ENSO), aprende com a realidade e explica
tudo com fonte — personalizado por talhão e honesto sobre sua própria confiança.

**Para fechar a versão com qualidade**, o que falta é pequeno e claro:
1. **Nematoides + rotação** como drivers (maior ganho de fidelidade local restante).
2. **Calibração segmentada** (recorrência → ajuste padrão das recomendações — já iniciado).
3. Polimento de UX e um **relatório de safra** exportável.

A tese está provada: tratar dado como **evidência conectada no tempo e no espaço** torna o
gêmeo fiel à lavoura específica — e essa fidelidade é o que, de fato, ajuda o produtor a
decidir melhor.
