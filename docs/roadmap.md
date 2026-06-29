# Roadmap — Fases 1 → 5

A evolução é incremental: cada fase entrega valor real e prepara a próxima. A regra de
ouro: **sem dados de qualidade, nenhuma IA é boa** — por isso a base vem primeiro.

## ✅ Fase 1 — Fundação do Gêmeo Digital + Motor v0  *(Marco 1, atual)*

- Monorepo, banco PostGIS, cadastro de fazendas/talhões/solo/safras/custos.
- Motor determinístico: fenologia, água (FAO-56), janela ZARC, IPPD, econômico.
- Laboratório Virtual no front (waterfall + economia + comparação de cenários).
- ✅ **Cockpit persistido**: criar/selecionar fazenda e talhão no front, salvar análise
  de solo e safras (linha do tempo) e carregar o talhão de volta no laboratório — fecha
  o loop do gêmeo digital na interface.
- **Entregue:** simular manejos e ver impacto em produtividade ± incerteza e lucro.
- ✅ **Acompanhamento da Safra ao Vivo** (`crop_plan.py`) — passo-a-passo por fase
  (preparo → semeadura → vegetativo → reprodutivo → colheita) ancorado na fenologia GDD
  e no mapa canônico de manejos: janela, status vs. hoje, manejos planejados (impacto
  sc/ha e R$) + sugeridos faltantes (custo de referência da KB), estresse hídrico e a
  proveniência dos dados de cada etapa. Tela "Acompanhamento" + **onboarding guiado** de
  3 passos.
- ✅ **Acurácia por talhão** (`data_sources.py` + `data_sources.json`) — de onde vem cada
  variável, quão local é, alavancagem (sc/ha) e como melhorar; índice de precisão do
  talhão (medido: 37% só com defaults → 89% com dados reais). Ver
  [acuracia-por-talhao.md](acuracia-por-talhao.md). Endpoints `/accuracy`, `/crop-plan`,
  `/reference/inputs` (preços de insumo com fonte citada).
- ✅ **Resumo da Safra (Briefing)** — a *resposta única* do gêmeo para o agricultor.
  Compõe os motores já existentes (simulação, Monte Carlo, decisão, janela ZARC,
  veracidade dos dados) num **veredito priorizado** com **status de saúde**
  (verde/amarelo/vermelho), os 4 números que importam (colho, ganho, risco, janela),
  alertas e a **lista de ações ordenada por retorno** — em linguagem de produtor.
  Não inventa nada: só orquestra os números dos motores. Motor (`briefing.py`, com
  testes), endpoint `/briefing` e painel-herói no topo do cockpit; os demais painéis
  passam a ser o *detalhamento* (auditar cada número).

## Fase 2 — Motor agronômico completo  *(em andamento)*

- ✅ **Monte Carlo**: simula milhares de safras (clima + preço estocásticos) →
  distribuição de lucro, "chance de lucro ≥ R$ X/ha" e probabilidade de prejuízo.
  Motor (`montecarlo.py`, com testes), endpoint `/simulate/montecarlo` e UI de risco.
- ✅ **Mais variáveis no IPPD**: daninhas (herbicida), pragas (inseticida) e doenças
  (fungicida) como fatores separados, + **estresse térmico** (dias > 34 °C em R1–R6).
- ✅ **Orçamento + fluxo de caixa + capital de giro** e **impacto por manejo** (quanto
  cada ação representa em sc/ha e R$). Motor `budget.py` + `operations_impact`, endpoint
  `/season-plan`, painel "Plano da Safra".
- Curvas de nutrição mais ricas (Ca, Mg, S, micros; resposta a calagem/gessagem).
- Excesso hídrico/geada; risco fitossanitário dinâmico em função do clima observado.

## Fase 3 — IA personalizada por talhão  *(fundação entregue)*

- ✅ **Knowledge Engine (v0)** — calibração previsto-vs-real por talhão com
  **encolhimento bayesiano** (correção tímida com poucas safras, convergindo para o
  viés real conforme acumula; a incerteza encolhe com o aprendizado). Motor
  (`knowledge.py`), endpoints stateless e persistidos (PostGIS) e painel de aprendizado.
- ✅ **Feature engineering** (`season_features`) — extrai atributos por safra (déficit
  em R3/R4/R5, desvio da janela, etc.), nunca dados crus, persistidos em `seasons.features`.
- 🔜 Quando houver dezenas de talhões × safras: trocar o encolhimento por
  **CatBoost/LightGBM** sobre os mesmos atributos, mantendo a interface.
- Meta: erro médio de previsão caindo para a faixa de 3–5% após algumas safras.

## Fase 4 — Gêmeo Digital "vivo"

- **Sentinel-2**: NDVI/EVI/NDRE por talhão, comparação com safra passada/vizinhos.
- Import de monitor de colheita, piloto automático, mapas de aplicação.
- Relevo (DEM): zonas de drenagem, erosão, variabilidade intra-talhão.
- Estado quase em tempo real → simulações futuras muito mais precisas.

## Fase 5 — Assistente de decisão

- ✅ **Motor de Decisão (v0)** — já entregue: prioriza intervenções por **retorno
  esperado**, com Δprodutividade, Δlucro, ROI da ação, justificativa técnica e
  **probabilidade de retorno positivo** (Monte Carlo pareado com números aleatórios
  comuns). Motor (`decision.py`), endpoint `/decisions` e painel de recomendações.
- O sistema deixa de ser consultado e passa a **recomendar**: prioriza intervenções
  por **retorno esperado**, com justificativa técnica, probabilidade e impacto em R$.
- **Motor de causalidade** (inferência causal) para separar correlação de causa.
- ✅ **Assistente LLM (v0)** — o "ChatGPT da fazenda": **Claude Opus 4.8** via *tool use*
  consulta os motores (simulação, Monte Carlo, decisão) e **narra os números — nunca
  calcula**. Endpoint `/assistant` e painel de chat no cockpit. Sem chave de IA, um
  **narrador determinístico** monta a resposta a partir dos mesmos motores.
- Visão de longo prazo: um **Sistema Operacional da Fazenda** (planejamento, custos,
  estoque, máquinas, clima, satélite, comercialização) — ciclo de aprendizado difícil
  de replicar.
