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
- **Hierarquia de fontes:** medido na lavoura (1.0) › estação INMET próxima (0.85) ›
  **climatologia histórica do ponto** (Open-Meteo ~10 anos, com ET0 real) (0.7) ›
  clima sintético regional (0.3).
- **Hoje na ferramenta:** ao ligar "clima real", buscamos a série histórica do
  Open-Meteo para a **coordenada exata do talhão** (verificado: ~148 dias/ciclo, ~654 mm,
  ET0 real). É local, porém **histórico** — não a safra corrente. Por isso o clima ainda
  carrega ±6 sc/ha de incerteza mesmo no melhor tier (anos secos × úmidos), e o Monte
  Carlo amostra essa distribuição. Isso é honesto, não escondido.
- **Como melhorar:** registrar a chuva medida no talhão durante a safra, ou conectar a
  estação INMET mais próxima, para sair da média histórica e usar o observado.

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

## Roadmap de acurácia (próximos ganhos)

1. **Clima da safra corrente** — combinar o observado até hoje + previsão para o restante
   do ciclo, em vez de só climatologia histórica (sai de 0.7 para perto do real).
2. **Solo por zonas de manejo** — múltiplas análises/zonas dentro do talhão.
3. **Calibração com histórico** — o Knowledge Engine corrige previsto×realizado por
   talhão após cada safra (já existe; ganha força com mais safras).
4. **Estação na lavoura** (versão futura) — chuva/umidade medidas no ponto.
