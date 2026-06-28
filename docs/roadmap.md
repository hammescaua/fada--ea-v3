# Roadmap — Fases 1 → 5

A evolução é incremental: cada fase entrega valor real e prepara a próxima. A regra de
ouro: **sem dados de qualidade, nenhuma IA é boa** — por isso a base vem primeiro.

## ✅ Fase 1 — Fundação do Gêmeo Digital + Motor v0  *(Marco 1, atual)*

- Monorepo, banco PostGIS, cadastro de fazendas/talhões/solo/safras/custos.
- Motor determinístico: fenologia, água (FAO-56), janela ZARC, IPPD, econômico.
- Laboratório Virtual no front (waterfall + economia + comparação de cenários).
- **Entregue:** simular manejos e ver impacto em produtividade ± incerteza e lucro.

## Fase 2 — Motor agronômico completo

- Curvas de nutrição mais ricas (Ca, Mg, S, micros; resposta a calagem/gessagem).
- Risco fitossanitário dinâmico (ferrugem/percevejo em função do clima e do estádio).
- Excesso hídrico, geada, calor extremo (VPD, dias > 34 °C).
- **Monte Carlo**: em vez de uma safra, simular milhares → "chance de lucro > R$ X/ha".
- Cronograma/orçamento da safra ponta a ponta (planejamento → colheita → faturamento).

## Fase 3 — IA personalizada por talhão

- Após ≥1 safra real, modelos **CatBoost/LightGBM** aprendem a *correção* entre o
  motor e o realizado, por propriedade e por talhão.
- Feature engineering pesado (atributos derivados por estádio, não dados crus).
- Intervalos de confiança calibrados pelo histórico do talhão.
- Meta: erro médio de previsão caindo para a faixa de 3–5% após algumas safras.

## Fase 4 — Gêmeo Digital "vivo"

- **Sentinel-2**: NDVI/EVI/NDRE por talhão, comparação com safra passada/vizinhos.
- Import de monitor de colheita, piloto automático, mapas de aplicação.
- Relevo (DEM): zonas de drenagem, erosão, variabilidade intra-talhão.
- Estado quase em tempo real → simulações futuras muito mais precisas.

## Fase 5 — Assistente de decisão

- O sistema deixa de ser consultado e passa a **recomendar**: prioriza intervenções
  por **retorno esperado**, com justificativa técnica, probabilidade e impacto em R$.
- **Motor de causalidade** (inferência causal) para separar correlação de causa.
- **LLM** que conversa e interpreta, mas nunca calcula — sempre consulta os motores.
- Visão de longo prazo: um **Sistema Operacional da Fazenda** (planejamento, custos,
  estoque, máquinas, clima, satélite, comercialização) — ciclo de aprendizado difícil
  de replicar.
