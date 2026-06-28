# Fontes de dados públicas

Prioridade: **gratuitas, com licença que permite uso comercial**, e relevantes para a
soja no Noroeste do RS.

## Clima

| Fonte | O que oferece | Licença / acesso | Uso no projeto |
|-------|---------------|------------------|----------------|
| **Open-Meteo** (Archive) | clima diário 1940+ (Tmax/min, chuva, radiação, ET0 FAO) | CC-BY 4.0, uso comercial, **sem chave** | fonte padrão de clima histórico (`apps/api/app/weather.py`) |
| **NASA POWER** | clima + radiação solar, satélite, 1981+ | pública/gratuita | alternativa / validação cruzada |
| **INMET / BDMEP** | estações brasileiras | pública | calibração local (futuro) |

> O motor calcula **déficit hídrico por estádio fenológico** — por isso precisa de
> série **diária**, não médias mensais.

## Zoneamento e agronomia

| Fonte | O que oferece | Uso |
|-------|---------------|-----|
| **ZARC / MAPA** | janela de semeadura por município × solo × ciclo | base da recomendação de melhor data de plantio ([`data/zarc`](../data/zarc)) |
| **Embrapa Soja** | fenologia, exigência nutricional, manejo, indicações técnicas | parâmetros do motor ([`data/reference`](../data/reference)) |
| **DSSAT / CROPGRO-Soybean** | modelo de processo (referência científica) | inspiração metodológica (fenologia GDD, balanço de água/N) |
| **CONAB** | preços e custos de produção de referência | econômico (futuro: integração automática) |

## Satélite e geoespacial (fases futuras)

| Fonte | O que oferece | Licença |
|-------|---------------|---------|
| **Sentinel-2** (Copernicus) | multiespectral 10 m, revisita ~5 dias → NDVI/EVI/NDRE | gratuita (Copernicus/AWS/Google Earth Engine) |
| **SICAR/CAR** | perímetros das propriedades | público | onboarding (import de talhões) |
| **MapBiomas** | uso e cobertura do solo histórico | gratuito | contexto/histórico do talhão |
| **SRTM/Copernicus DEM** | relevo (altitude, declividade) | gratuito | topografia, fluxo de água |

## Boas práticas de integração

- **Cache obrigatório**: nunca consultar a API a cada request (tabela `weather_cache`).
- **Feature engineering**: a IA futura recebe *atributos derivados* (ex.: "déficit
  hídrico em R3", "nº de dias > 34 °C em R5"), nunca a série crua.
- **Atribuição**: respeitar CC-BY (Open-Meteo) e termos de cada fonte.
