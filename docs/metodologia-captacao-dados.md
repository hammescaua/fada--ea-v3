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
