# Metodologia de captação de dados (onboarding progressivo)

O maior erro dos softwares agrícolas é exigir formulários gigantes. Aqui o princípio é:
**quanto menos o agricultor digitar, melhor** — o sistema vai *descobrindo*.

## Funil progressivo

```
1º acesso        Onde fica? (município, coordenadas) → desenhe/importe o talhão
                 ↓
Logo depois      Importe a análise de solo · confirme a cultivar/população/data
                 ↓
Durante a safra  1 pergunta por semana: "o que aconteceu?" (aplicou? qual? dose? custo?)
                 ↓
Pós-colheita     Importe o monitor de colheita → fecha o loop (previsto vs real)
```

A cada etapa, poucas perguntas. O histórico se monta sozinho.

## Hierarquia de captação (do mais automático ao manual)

1. **Automático (meta: 90%)** — clima (API), satélite (NDVI), relevo (DEM), perímetro
   (CAR). Não exige digitação.
2. **Import de arquivo** — análise de solo (PDF/CSV), shapefile/CAR, monitor de
   colheita, mapa de aplicação do pulverizador/plantadeira.
3. **Confirmação assistida** — o sistema sugere ("usou esta cultivar?") e o agricultor
   só confirma.
4. **Entrada manual mínima** — apenas o que não dá para inferir (ex.: custo real de um
   insumo específico).

## Qualidade do dado importa tanto quanto o dado

Registrar "aplicou fungicida" não basta. O sistema captura **condições da aplicação**
(temperatura, vento, umidade) e deriva uma `quality` (0..1) — pois uma aplicação a
36 °C com vento de 18 km/h rende menos. Isso já existe no modelo (`operations.quality`).

## Veracidade explícita: o Índice de Confiança dos Dados (implementado)

A plataforma é **honesta sobre o que sabe**. O motor `provenance.py` calcula, por talhão:

- um **índice de confiança dos dados** (0–100%) ponderado pela influência de cada grupo
  (clima, solo, cultivar, manejo, população, preço) e por sua **fonte** (real / parcial /
  estimado);
- a lista de **lacunas ranqueadas por valor-da-informação** — quanto a estimativa pode
  oscilar (±sc/ha) se aquele dado fosse o real, calculado perturbando a entrada e medindo
  o swing no próprio modelo. Isso responde objetivamente *"o que medir primeiro"*.

Exibido no painel "Confiança dos dados deste talhão". Exemplo: *"Confiança 64%. O dado que
mais aumentaria a precisão é o clima (±6 sc/ha): ligar o histórico real da localização."*

**Clima real por padrão.** O balanço hídrico usa a **climatologia real da localização**
(histórico ~10 anos do Open-Meteo/NASA POWER, média por dia-do-ano, com ET0 FAO real) —
não um fallback genérico. Assim a água/calor são específicos de cada talhão (ex.: Santo
Ângelo e Cruz Alta dão estresses diferentes). A fonte é sinalizada (`climatologia_real`
vs `sintetico`).

## Lidando com dados ausentes (estratégia de defaults)

Quando falta um dado-chave, o motor **não trava**: usa um default regional explícito
(documentado em `data/reference`) e **sinaliza menor confiança** no resultado. Conforme
o agricultor fornece o dado real, a confiança sobe. Assim o valor aparece desde o
primeiro dia, e a precisão cresce com o engajamento.

## Loop de aprendizado (fecha na Fase 3)

```
Cenário planejado → manejo real registrado → colheita (monitor) →
erro previsto-vs-real → correção do modelo daquele talhão → próxima safra mais precisa
```

Esse loop é o que transforma médias regionais no **modelo específico do talhão** —
o diferencial competitivo central do produto.
