# Modelo de dados — o Gêmeo Digital no banco

PostgreSQL + **PostGIS** (tudo é georreferenciado). Schema em
`apps/api/app/models.py`; migration inicial em `apps/api/migrations/versions/0001_initial.py`.

O modelo é desenhado para **acumular a história de cada talhão ao longo das safras** —
o ativo que cresce com o tempo e habilita a IA personalizada.

```
farms ──< fields ──< soil_tests
                 └──< seasons ──< operations
                              └──< cost_items
cultivars   (catálogo)
weather_cache  (séries climáticas por célula de grade)
simulations    (cenários simulados: entrada + saída)
```

| Tabela | Papel |
|--------|------|
| `farms` | propriedade (nome, município) |
| `fields` | **talhão** — geometria `Polygon(4326)`, área, centroide, município |
| `soil_tests` | análise por talhão e data: argila, MO, pH, CTC, V%, P, K |
| `cultivars` | catálogo: grupo de maturação, ciclo, potencial, tolerância |
| `seasons` | safra: talhão × cultivar × ano-safra × data de plantio × população |
| `operations` | manejos: tipo, data, produto, dose, custo, qualidade da aplicação |
| `cost_items` | itens de custo da safra (R$/ha) |
| `weather_cache` | clima diário em cache (evita reconsultar APIs) |
| `simulations` | histórico de cenários (entrada/saída JSON) para comparação |

## Notas de modelagem

- **Geometria**: o talhão é o objeto central. O polígono vem do desenho no mapa ou de
  import (CAR/shapefile na próxima fase) e é guardado em coluna PostGIS 4326.
- **Qualidade do manejo**: `operations.quality` (0..1) captura que uma aplicação de
  fungicida a 36 °C com vento de 18 km/h vale menos — isso alimenta o fator sanidade.
- **`simulations`**: cada "e se…" pode ser salvo, permitindo comparar estratégias e,
  no futuro, confrontar o previsto com o realizado (loop de aprendizado).

## Evolução futura (rumo ao "DNA do talhão")

À medida que safras são registradas, deriva-se um **perfil dinâmico** por talhão
(ex.: "argiloso, alta retenção, sensível a atraso de plantio, alto risco de ferrugem,
boa resposta a P"). Esse DNA muda devagar e personaliza as penalidades do IPPD —
saindo de defaults de literatura para a realidade daquele talhão.
