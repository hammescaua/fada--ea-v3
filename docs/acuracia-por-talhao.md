# Acurácia por Talhão — de onde vem cada dado e como torná-lo mais preciso

> A estimativa só é tão boa quanto o dado que a alimenta. Este documento explica,
> variável por variável e etapa por etapa, **de onde vem cada número**, quão específico
> ele é para o talhão/localidade, e **o que fazer para deixá-lo mais verídico**. É a
> resposta honesta à pergunta central do produto: *quão preciso é isto para a MINHA
> lavoura?*

A ficha de fontes é externa e auditável (`data/knowledge/data_sources.json`); o motor
`data_sources.py` detecta a fonte em uso, calcula a **alavancagem** (quanto a estimativa
oscila se aquele dado for o real, por perturbação do próprio modelo) e devolve um
**índice de precisão do talhão** com as melhorias priorizadas. Os mesmos números
aparecem no painel "Precisão para este talhão" e em cada etapa do Acompanhamento.

## Quanto muda na prática

Mesmo talhão, só trocando a origem dos dados (medido no motor):

| Estado dos dados | Índice de precisão |
|---|---|
| Tudo default/regional | **37 %** (baixa) |
| Solo + clima + cultivar + manejo reais | **89 %** (alta) |

O salto vem de personalizar o que é local: solo, clima do ponto e cultivar real.

## De onde vem cada variável

### Clima → governa fenologia (graus-dia), balanço hídrico (FAO-56) e calor reprodutivo
- **Hierarquia de fontes:** medido na lavoura (1.0) › **clima realizado da safra**
  (observado do ponto) (0.95) › **safra corrente** (observado até hoje + previsão 16 d +
  climatologia para o resto) (0.85) › estação INMET próxima (0.85) › climatologia
  histórica do ponto (0.7) › sintético regional (0.3).
- **Hoje na ferramenta — o clima se adapta ao momento da safra** (`get_season_weather`):
  - **safra no passado** → série **realizada** observada do ponto (Open-Meteo Archive);
    é o que de fato ocorreu, então a incerteza climática a "medir" cai a **0**;
  - **safra corrente** (hoje dentro do ciclo) → **observado até hoje + previsão de 16
    dias + climatologia** só para o fim do ciclo (verificado: ex. 60 d obs + 15 prev +
    63 clim). A alavancagem do clima encolhe na proporção do que já é conhecido;
  - **safra futura** → climatologia do ponto (ano típico observado, ET0 FAO real).
- **Honestidade mantida à mostra:** só o trecho ainda não observado carrega incerteza, e
  o Monte Carlo amostra essa faixa. Nada de chamar "100% real" o que é média histórica.
- **Como melhorar ainda mais:** registrar a chuva medida no talhão ou conectar a estação
  INMET mais próxima fecha o pouco que resta de climatologia no fim do ciclo.

### Solo → governa nutrição (P, K, pH, V%), fator solo/CTC e água disponível
- **Hierarquia:** análise do próprio talhão (1.0) › análise de outro talhão da
  propriedade (0.6) › default regional Latossolo argiloso (0.2).
- **É o MAIOR ganho de acurácia.** Sem análise, P/K/pH/V% são suposição regional e a
  recomendação de calagem/adubação é genérica.
- **Como melhorar:** fazer/importar a análise de solo do talhão (idealmente por zonas de
  manejo). É a única forma de personalizar a fertilidade.

### Cultivar → governa teto produtivo, ciclo/datas e tolerância à ferrugem
- **Hierarquia:** cultivar real da obtentora (1.0) › só o grupo de maturação (0.6) ›
  genérica RR 5.5 (0.3).
- **Como melhorar:** informar a cultivar realmente semeada (a obtentora publica GMR,
  potencial e tolerância) — ajusta ciclo, janela ZARC e resposta a fungicida.

### Data de semeadura → governa a posição na janela ZARC (penalidade por desvio)
- **Fonte:** decisão do agricultor; o risco é avaliado por município (ZARC/MAPA-Embrapa)
  cruzado com o clima do ponto. **Como melhorar:** confirmar a data real.

### População/estande → governa o fator população
- **Hierarquia:** estande aferido a campo (1.0) › população de regulagem (0.7) › default
  300 mil/ha (0.3). **Como melhorar:** aferir o estande real após a emergência.

### Manejo → governa daninhas, pragas, doenças e os custos
- **Hierarquia:** programa registrado (datas/produtos/doses) (1.0) › programa-padrão
  regional (0.5). **Como melhorar:** registrar cada aplicação.

### Preços (soja e insumos) → governam receita, lucro, ROI, break-even e custo de cada manejo
- **Hierarquia:** preço negociado pelo agricultor (1.0) › referência CONAB/CEPEA/catálogo
  (0.6). Os preços de insumo de referência ficam em `inputs_catalog.json` (mercado BR/RS
  2025), expostos em `/reference/inputs`. **Como melhorar:** informar o preço real
  negociado.

## Como isso aparece para o agricultor

- **Painel "Precisão para este talhão"**: índice geral + cada variável (fonte em uso,
  específico-do-talhão × regional, alavancagem, como melhorar) + "meça primeiro" ranqueado.
- **Acompanhamento da safra**: cada fase mostra "🔎 de onde vêm os dados desta etapa", com
  a fonte atual e o que medir para aquela etapa ficar mais verídica.
- **Resumo da safra**: o veredito já aponta o dado de maior alavancagem a medir primeiro.

## Como o agricultor torna as variáveis "verdadeiras" (e o modelo aprende)

Duas alavancas, ambas implementadas:

1. **Preencher o real → a proveniência sobe sozinha** (`infer_provenance`). Ao informar a
   cultivar real, registrar o manejo de fato feito (produto/dose) e a data já realizada,
   o sistema reconhece e eleva o nível da fonte — sem toggle manual. Verificado: ao
   preencher esses dados, a precisão do talhão sobe.
2. **Registrar a colheita → o talhão calibra a si mesmo** (Knowledge Engine). A cada safra
   guardamos previsto×colhido; o resíduo vira uma **correção aditiva com encolhimento
   bayesiano** que entra como fator transparente "Calibração do talhão" na cascata IPPD e
   corrige TODAS as previsões seguintes (produtividade, lucro, risco, decisões). A
   incerteza também encurta conforme o talhão acumula histórico.
   - Verificado ponta-a-ponta (PostGIS): 2 safras previstas 46,4 e colhidas 53,4 →
     correção **+2,8 sc/ha** (encolhida de +7 bruto, porque 2 safras ainda são poucas) →
     erro médio cai de 7,0 para 4,2 sc/ha; nova previsão 46,4 → 49,2.
   - Quanto mais safras, mais a correção converge para o viés real e mais a incerteza cai.

## Roadmap de acurácia (próximos ganhos)

1. ✅ **Clima da safra corrente** — observado até hoje + previsão (16 d) + climatologia só
   no fim do ciclo; safra passada usa o realizado (`get_season_weather`).
2. ✅ **Calibração com histórico** — correção previsto×realizado por talhão, aplicada como
   fator transparente da cascata e refletida em todos os motores.
3. **Solo por zonas de manejo** — múltiplas análises/zonas dentro do talhão.
4. **ML (Nível 2)** — quando houver dezenas de talhões × safras, trocar o encolhimento por
   CatBoost/LightGBM sobre os mesmos atributos (`season_features`), mantendo a interface.
5. **Estação na lavoura** (versão futura) — chuva/umidade medidas no ponto.
