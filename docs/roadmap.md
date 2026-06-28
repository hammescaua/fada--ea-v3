# Roadmap — Fases 1 → 5

A evolução é incremental: cada fase entrega valor real e prepara a próxima. A regra de
ouro: **sem dados de qualidade, nenhuma IA é boa** — por isso a base vem primeiro.

## ✅ Fase 1 — Fundação do Gêmeo Digital + Motor v0  *(Marco 1, atual)*

- Monorepo, banco PostGIS, cadastro de fazendas/talhões/solo/safras/custos.
- Motor determinístico: fenologia, água (FAO-56), janela ZARC, IPPD, econômico.
- Laboratório Virtual no front (waterfall + economia + comparação de cenários).
- **Entregue:** simular manejos e ver impacto em produtividade ± incerteza e lucro.

## Fase 2 — Motor agronômico completo  *(em andamento)*

- ✅ **Monte Carlo**: simula milhares de safras (clima + preço estocásticos) →
  distribuição de lucro, "chance de lucro ≥ R$ X/ha" e probabilidade de prejuízo.
  Motor (`montecarlo.py`, com testes), endpoint `/simulate/montecarlo` e UI de risco.
- Curvas de nutrição mais ricas (Ca, Mg, S, micros; resposta a calagem/gessagem).
- Risco fitossanitário dinâmico (ferrugem/percevejo em função do clima e do estádio).
- Excesso hídrico, geada, calor extremo (VPD, dias > 34 °C).
- Cronograma/orçamento da safra ponta a ponta (planejamento → colheita → faturamento).

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
- **LLM** que conversa e interpreta, mas nunca calcula — sempre consulta os motores.
- Visão de longo prazo: um **Sistema Operacional da Fazenda** (planejamento, custos,
  estoque, máquinas, clima, satélite, comercialização) — ciclo de aprendizado difícil
  de replicar.
