# Precio de Bolsa Nacional — Mercado de Energía Mayorista de Colombia

Proyecto de análisis del Precio de Bolsa Nacional a partir de los datos públicos de
[XM](https://www.xm.com.co/), operador del Mercado de Energía Mayorista colombiano.

Esta rama (`main`) es solo el índice del proyecto. Cada componente vive en su propia rama.

## Ramas

| Rama | Contenido |
| --- | --- |
| [`xm-pipeline`](../../tree/xm-pipeline) | Extracción de la serie histórica desde la API de XM, post-proceso y resultados en CSV |

## Datos

La API de XM es pública y no requiere autenticación. El pipeline consulta la colección
`PrecBolsNaci` (métrica `Sistema`) y cubre desde el 2000-01-01, con precios horarios en
COP/kWh y promedios diario y mensual derivados.

Para trabajar con el pipeline:

```bash
git checkout xm-pipeline
```
