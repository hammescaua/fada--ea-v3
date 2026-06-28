# Modelo Canônico da Safra — um método, não N motores soltos

Este documento fecha o escopo: em vez de criar um motor diferente para cada insumo
(fertilizante, inseticida, máquina…), define **um único método** que vale para qualquer
manejo/variável, e a **taxonomia fechada** do que entra no modelo. Adicionar algo novo é
uma entrada de **dados** (catálogo), não código novo.

## O método único (vale para todo manejo e variável)

```
            preço-base (catálogo)            coeficiente + fonte (base de conhecimento)
                   │                                       │
   manejo/insumo ──┴──► CUSTO (dose × preço)      variável ──► FATOR no IPPD (resposta transparente)
                                   │                                  │
                                   └────────────► SIMULAÇÃO ◄─────────┘
                                                     │
                  impacto de cada item = re-simular COM e SEM ele (Δ produtividade, Δ R$)
                                                     │
                              MOTOR DE CENÁRIOS: combina datas × população × programas,
                              simula tudo, ranqueia por lucro → MELHOR PLANO + explicação
```

Cada peça segue **exatamente o mesmo padrão** — por isso não precisamos reescrever o
motor para cada insumo:

1. **Preço-base** vem do catálogo de insumos (`inputs_catalog.json`), com fonte e data;
   o agricultor pode sobrescrever pelo preço real.
2. **Coeficiente de impacto** vem da base de conhecimento (`agronomic_responses.json`),
   com fonte (Embrapa/CQFS/FAO/ZARC); a IA por talhão refina com dados reais.
3. **Custo** = dose × preço (dose por fórmula oficial quando existe — ex.: calagem por
   saturação por bases).
4. **Impacto** = re-simulação do mesmo modelo IPPD com e sem o item (nunca um número fixo).
5. **Cenários** = o motor combina os manejos e acha o que mais combina com o talhão.
6. **Explicação** = a cascata IPPD + as razões de cada escolha.

## A taxonomia fechada (definida como dados)

| Catálogo | Arquivo | O que define |
|---|---|---|
| Manejos | [`data/knowledge/operations_catalog.json`](../data/knowledge/operations_catalog.json) | **todos** os manejos possíveis na soja, cada um com fase/janela, variável-alvo (fator do IPPD) e insumo associado |
| Variáveis de impacto | [`data/knowledge/impact_variables.json`](../data/knowledge/impact_variables.json) | a lista **fechada** de variáveis que mais impactam, agrupadas (solo, clima, planta, manejo, máquina, histórico/relevo, mercado) e como cada uma entra no modelo |
| Coeficientes | [`data/knowledge/agronomic_responses.json`](../data/knowledge/agronomic_responses.json) | os números de resposta, com fonte |
| Insumos/preços | [`data/knowledge/inputs_catalog.json`](../data/knowledge/inputs_catalog.json) | composição + preço de referência |

**Regra de ouro:** um manejo/insumo/variável novo entra como **linha nestes JSON**,
mapeado a um fator que já existe — sem reabrir o motor. É assim que o escopo fica fechado
e a base científica, consistente.

## O motor de cenários (`scenario_search.py`)

`optimize_season(scenario)` varre o espaço de decisões (data de semeadura × população ×
nº de fungicidas — extensível), simula cada combinação pelo método único, ranqueia por
lucro e devolve:

- **melhor plano** para o talhão (data, população, programa) + Δlucro vs. o plano atual,
- o **ranking** das alternativas,
- a **decomposição IPPD** do vencedor e os **porquês** (janela ZARC, faixa de população,
  pressão de doença),
- as **correções de solo** mais rentáveis (motor de fertilidade).

Exemplo: 45 combinações avaliadas → "plantar 11/out, 280 mil/ha, 2 fungicidas: 57,8 sc/ha,
+R$870/ha vs. o plano atual; porque a data está na janela do ZARC, a população está na
faixa ótima e 2 fungicidas cobrem a pressão de ferrugem".

## Próximos passos dentro deste método (sem mudar a arquitetura)

- Estender o grid do motor de cenários (espaçamento, cultivar/grupo de maturação,
  programas de daninha/praga, fertilidade dentro do orçamento).
- Tornar os fatores fitossanitários **iterados a partir do catálogo** (doença/praga/
  daninha já compartilham a mesma fórmula de proteção).
- Catálogo de **produtos comerciais** (marca → eficiência/preço) sob o mesmo método.
- Qualidade de **operação/máquina** modulando a eficiência dos manejos.
