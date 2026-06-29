# Proveniência dos dados — de onde vem cada variável e como torná-la local

Resposta direta a "de onde vêm todas essas variáveis e como melhorar a personalização".
Cada variável tem uma **fonte**, uma **resolução espacial** e um **tier de qualidade**. A
plataforma usa a melhor fonte disponível e **diz qual está usando** (veja o Índice de
Confiança dos Dados). Quanto mais local o dado, mais verídica a recomendação.

## Hierarquia de fontes (da mais para a menos verídica)

```
sensor_lavoura  >  estacao_inmet  >  reanalise (Open-Meteo/NASA POWER)  >  sintetico
   (seu talhão)     (estação próxima)   (grade ~9–25 km)                  (default regional)
```

## Mapa por variável

| Variável | Fonte hoje | Resolução | Tier | Como ficar local (melhorar) |
|---|---|---|---|---|
| **Chuva** | Open-Meteo (ERA5) | grade ~9–25 km | reanálise | **Pluviômetro na lavoura** (a chuva é pontual; a grade não captura veranicos/pancadas) |
| **Umidade do solo** | *modelada* (balanço FAO-56) | — | modelo | **Sonda de umidade** — mede o estado real da água; ancora o balanço (maior ganho de precisão) |
| **Temperatura / calor** | Open-Meteo (ERA5) | grade | reanálise | Sensor de T° na estação; estação INMET próxima |
| **ET0** | Open-Meteo (FAO PM) | grade | reanálise | Derivada da estação local |
| **Solo (pH, V%, P, K, argila)** | informado pelo agricultor / default | talhão (se informado) | real/estimado | **Análise de solo** do laboratório (idealmente por zona/grade do talhão) |
| **Cultivar** | informado / default | — | real/estimado | Informar a cultivar e o grupo de maturação reais |
| **Janela de semeadura** | ZARC/MAPA | município × solo × ciclo | regional | Calibrar com o histórico real do talhão (Knowledge Engine) |
| **Coeficientes de resposta** | Embrapa/CQFS/FAO | regional/literatura | científico | Calibração por talhão com safras reais |
| **Preços (soja/insumos)** | catálogo de referência (CONAB/CEPEA/mercado) | nacional/regional | referência | **Informar o preço real** negociado |
| **Produtividade histórica** | — | — | ausente | Importar monitor de colheita (fecha o loop previsto-vs-real) |

## O que melhora a personalização, em ordem de impacto

1. **Sonda de umidade do solo na lavoura** — a água é o fator nº 1; medir o estado real
   substitui a estimativa. Já implementado: leituras ancoram o balanço hídrico.
2. **Pluviômetro na lavoura** — sobrepõe a chuva da grade. Já implementado.
3. **Análise de solo do talhão** (idealmente por zonas) — torna Solo/Nutrição reais.
4. **Estação INMET próxima** — quando não há sensor, melhor que a reanálise (a integrar).
5. **Monitor de colheita** — alimenta o Knowledge Engine; a cada safra o modelo do talhão
   fica mais certeiro.
6. **Preços reais** — torna o econômico verídico.

## Como a plataforma já lida com a falta de dado

- Usa a **melhor fonte disponível** e **sinaliza o tier** (`water.source`).
- Calcula o **Índice de Confiança dos Dados** e ranqueia as lacunas por
  **valor-da-informação** (quanto a estimativa muda se o dado for real) — dizendo
  objetivamente o que medir primeiro (ver `provenance.py`).
- Para coletar o dado mais valioso (clima/umidade locais), há a via da **miniestação na
  lavoura** — ver [`docs/estacao-diy.md`](estacao-diy.md).
