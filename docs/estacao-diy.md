# Miniestação na lavoura (DIY) — coletar o dado mais verídico

A forma mais direta de tornar a previsão local é **medir na própria lavoura**. A
plataforma já aceita leituras de uma estação do agricultor: a **chuva** sobrepõe a
reanálise e a **umidade do solo** ancora o balanço hídrico (a água é o fator nº 1).

## Hardware sugerido (baixo custo, ~R$150–400)

| Peça | Função | Observação |
|---|---|---|
| **ESP32** (WiFi) | microcontrolador + envio | baixo consumo, WiFi nativo |
| **Pluviômetro de báscula** (tipping bucket) | chuva (mm) | conta "baldinhos" → mm |
| **Sensor capacitivo de umidade do solo** | umidade (fração/%) | capacitivo dura mais que resistivo; enterrar a ~20 cm |
| **BME280 / DHT22** | temperatura e umidade do ar | opcional, melhora calor/ET |
| Painel solar 5V + bateria 18650 | energia | autonomia no campo |

Calibre o sensor de umidade entre **seco (0)** e **capacidade de campo (1)** para enviar
a *fração de água disponível* (0..1). Alternativamente envie em **%** (com `unit: "%"`),
que a API converte.

## Contrato de integração (o que a estação envia)

1. **Descobrir o token do talhão:** `GET /api/fields/{field_id}/station` →
   devolve `ingest_token`, o `endpoint` e exemplos.
2. **Enviar leituras (a cada hora/evento):**

```
POST /api/fields/{field_id}/readings
Header: X-Ingest-Token: <ingest_token do talhão>
Content-Type: application/json

{
  "readings": [
    {"measured_at": "2025-12-01T12:00:00Z", "variable": "rain_mm",       "value": 12.4, "station_id": "esp32-01"},
    {"measured_at": "2025-12-01T12:00:00Z", "variable": "soil_moisture", "value": 0.62, "unit": "frac", "depth_cm": 20},
    {"measured_at": "2025-12-01T12:00:00Z", "variable": "temp_c",        "value": 28.7}
  ]
}
```

Variáveis aceitas: `rain_mm` (acumulada no intervalo), `soil_moisture` (fração 0..1 ou %),
`temp_c`, `rh_pct`. A API agrega por dia (chuva = soma; umidade = média) e usa nas
simulações daquele talhão automaticamente — a fonte do clima passa a `sensor_lavoura`.

## Esboço de firmware (ESP32 / Arduino-C++)

```cpp
// Pseudo-firmware — envia 1 leitura/hora
void enviarLeitura(float chuva_mm, float umidade_frac, float temp) {
  HTTPClient http;
  http.begin("https://SEU_HOST/api/fields/FIELD_ID/readings");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Ingest-Token", "TOKEN_DO_TALHAO");
  String body = String("{\"readings\":[") +
    "{\"measured_at\":\"" + isoTimeUTC() + "\",\"variable\":\"rain_mm\",\"value\":" + chuva_mm + "}," +
    "{\"measured_at\":\"" + isoTimeUTC() + "\",\"variable\":\"soil_moisture\",\"value\":" + umidade_frac + ",\"unit\":\"frac\",\"depth_cm\":20}" +
    "]}";
  http.POST(body);
  http.end();
}
```

## Sem estação? Alternativas de coleta

- **Pluviômetro manual** + lançar a chuva no app (mesma rota, sem hardware).
- **Estação INMET/Inmet-A próxima** (integração futura — tier `estacao_inmet`).
- **Análise de solo** e **monitor de colheita** (preenchem solo e histórico).

> Quanto mais leituras reais do talhão, maior o Índice de Confiança dos Dados e mais
> certeira a recomendação — a plataforma mostra exatamente o quanto cada dado agrega.
