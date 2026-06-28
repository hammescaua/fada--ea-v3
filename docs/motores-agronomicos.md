# Motores agronômicos — fórmulas e referências

Todos os parâmetros estão versionados em [`data/reference/soybean_params.json`](../data/reference/soybean_params.json)
e em `packages/agro_engine/agro_engine/reference.py`. São valores de literatura
(Embrapa Soja, FAO-56, DSSAT/CROPGRO), conservadores, e serão **calibrados pela IA por
talhão** nas fases futuras.

## 1. Fenologia — graus-dia (GDD)

```
GDD_dia = clamp(Tméd, Tbase, Tsup) − Tbase     (Tbase = 10 °C, Tsup = 30 °C)
```

Acumula-se GDD a partir da semeadura. A emergência (VE) ocorre a ~110 GDD; de VE a R8,
o total é ~1450 GDD para o grupo de maturação 5,5, ajustado ±8% por ponto de grupo.
Cada estádio (V1, R1…R8) é atingido numa fração desse total. Saída: data de cada
estádio — base para alocar chuva, nutrição e sensibilidade no momento certo.

## 2. Balanço hídrico — FAO-56 (zona radicular)

```
TAW = AWC · profundidade_radicular            (água total disponível)
RAW = p · TAW            (p = 0,5)            (água facilmente disponível)
ETc = Kc(estádio) · ET0                       (ET0 informado ou Hargreaves)
Dr  = Dr_ant + ETc − (chuva − escoamento)     (depleção diária)
Ks  = (TAW − Dr)/(TAW − RAW)  se Dr > RAW; senão 1   (coef. de estresse)
estresse_dia = 1 − Ks
```

O estresse diário é agregado por estádio e ponderado pela **sensibilidade hídrica**
(R3–R5 são os mais críticos). O **déficit hídrico** é a variável que mais determina
quebra de produtividade na soja — por isso é calculado *quando* ocorre, não só o total.
AWC por textura: arenoso 90, médio 140, argiloso 160 mm/m.

## 3. Janela de semeadura — ZARC

Cruza a data escolhida com a janela oficial do município (ZARC/MAPA). Define o
**núcleo ótimo** (terço inicial da janela). Fora dele, aplica penalidade de
~0,18 sc/ha por dia de desvio. Ver [`data/zarc/zarc_soja_no_rs.json`](../data/zarc/zarc_soja_no_rs.json).

## 4. Produtividade — IPPD (decomposição multiplicativa)

Parte do **potencial genético** da cultivar e aplica fatores sequenciais, cada um um
multiplicador em torno de 1,0:

```
esperado = potencial × f_solo × f_nutrição × f_compactação
                     × f_janela × f_água × f_sanidade
```

A cascata é decomposta em contribuições **aditivas** (± sc/ha) que somam exatamente ao
resultado — é o gráfico waterfall da UI. Cada fator tem uma **confiança**; a incerteza
agregada vira o intervalo `esperado ± X sc/ha (confiança Y%)`.

| Fator | Dirigido por |
|------|--------------|
| Solo | pH, V%, MO |
| Nutrição | P, K disponíveis |
| Compactação | classe (nenhuma→severa) |
| População | estande vs. faixa ótima |
| Janela | desvio da janela ZARC |
| Água | estresse hídrico ponderado por estádio |
| Calor | dias > 34 °C em estádio reprodutivo (R1–R6) |
| Daninhas | competição × eficiência do herbicida |
| Pragas | percevejo/lagartas × eficiência do inseticida |
| Doenças | ferrugem × tolerância da cultivar × qualidade dos fungicidas |

Cada manejo de proteção (herbicida, inseticida, fungicida) reduz a perda remanescente
da sua pressão — por isso aparece como fator próprio e é avaliável individualmente
(ver Motor de Orçamento abaixo).

> Filosofia (do briefing): a pergunta não é "quanto vou colher?", mas **"quais fatores
> limitaram o potencial e quanto cada um pesou?"**. É isso que orienta a ação.

## 5. Econômico

```
receita   = produtividade × preço
lucro     = receita − custo_total
ROI       = lucro / custo
break-even (sc) = custo / preço          break-even (preço) = custo / produtividade
```

Produtividade alta não é lucro: o motor sempre devolve break-even e preço mínimo para
avaliar se um investimento de manejo se paga.

## 6. Monte Carlo — distribuição de risco

Roda o motor N vezes (default 2000–3000) variando clima (chuva/temperatura sintéticas
da climatologia de verão do NO-RS) e preço. Devolve percentis p10/p50/p90, histogramas
e probabilidades: `P(lucro ≥ meta)`, `P(produtividade ≥ meta)`, `P(prejuízo)`. Como a
água só reduz o teto (multiplicador ≤ 1), a distribuição é assimétrica à esquerda — anos
ruins pesam mais que anos bons, o que é realista. `montecarlo.py`.

## 7. Motor de Decisão — "vender decisão, não previsão"

O sexto motor não prevê: ele **recomenda**. Para cada decisão candidata (aplicar/remover
fungicida, antecipar semeadura, corrigir P, calagem, ajustar população) transforma o
cenário (embutindo o custo da ação), re-simula e mede Δprodutividade e Δlucro vs. a base.
A **probabilidade de retorno positivo** vem de um **Monte Carlo pareado** (números
aleatórios comuns): o mesmo clima e o mesmo preço são sorteados para os dois cenários em
cada iteração, isolando o efeito da decisão. As ações saem ordenadas por Δlucro, com ROI
da ação e justificativa técnica. `decision.py`.

> No futuro, o LLM (Nível 3) apenas **narra** estes números — nunca os calcula.

## 8. Motor de Orçamento e Fluxo de Caixa + Impacto por Manejo

`budget.py` traduz o plano da safra (custos por categoria + operações datadas) num
**fluxo de caixa** ao longo do ciclo: saídas nas datas dos manejos/insumos e a entrada
na colheita (R8). Devolve o custo por categoria, o lucro e o **capital de giro** (pico
de caixa negativo) — quanto o agricultor precisa financiar até o faturamento.

`operations_impact` (em `decision.py`) responde *"quanto cada manejo representa na
safra?"*: para cada operação do plano, compara o cenário com e sem ela e devolve a
**produtividade agregada (sc/ha), o valor bruto, o valor líquido (descontando o custo)
e o ROI**. É o que deixa explícito ao agricultor o retorno de cada ação — ex.: um
herbicida que custa R$160/ha pode agregar +6 sc/ha (R$720), líquido +R$560, ROI 4,5x.

## Limitações do v0 (honestidade do modelo)

- Talhão tratado como homogêneo (sem variabilidade espacial intra-talhão ainda).
- Sem pragas/doenças dinâmicas por clima (sanidade é simplificada).
- Penalidades calibradas por literatura, não pelo histórico do talhão — isso muda na
  Fase 3 com a IA. O objetivo declarado é **reduzir a incerteza safra após safra**,
  não prever com exatidão absoluta.
