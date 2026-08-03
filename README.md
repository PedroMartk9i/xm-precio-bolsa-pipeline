# Precio de Bolsa Nacional — Pipeline de extracción (API XM)

Pipeline para extraer la serie histórica del **Precio de Bolsa Nacional** del Mercado de
Energía Mayorista colombiano usando la API pública de [XM](https://www.xm.com.co/)
(a través de `pydataxm`), y dejar los datos listos para análisis.

La API no requiere autenticación ni llaves.

> Esta rama (`xm-pipeline`) contiene el pipeline de extracción. La rama `main` es el
> índice del proyecto.

## Qué hace

1. Genera rangos de fechas de máximo 30 días calendario (límite de la API para datos horarios),
   desde `2000-01-01` hasta hoy.
2. Consulta la colección `PrecBolsNaci` / métrica `Sistema` en cada rango, con una pausa de
   0.5 s entre llamadas. Los rangos que devuelven 204 (sin contenido) se reportan y se omiten.
3. Post-procesa el resultado (`procesamiento.procesar`):
   - elimina las filas repetidas de los días frontera entre bloques contiguos,
   - ordena cronológicamente,
   - calcula `Daily Average` — promedio de las 24 horas del día,
   - calcula `Monthly Average` — promedio de los `Daily Average` del mes, replicado en cada
     fila del mes.
4. Guarda `Results/precios_bolsa_nacional.csv` (diario) y `Results/promedio_mensual.csv`
   (serie mensual), en UTF-8 con BOM.

El post-proceso es **idempotente**: los promedios se recalculan siempre desde las columnas
horarias, así que volver a aplicarlo no cambia el resultado.

## Uso

```bash
pip install -r requirements.txt
```

Extracción completa desde la API (~320 consultas, varios minutos):

```bash
python extraer_precios_bolsa.py
```

Para acotar el rango, edita `FECHA_INICIO` / `FECHA_FIN` en el encabezado del script.

Regenerar los derivados desde un CSV ya descargado, sin volver a llamar a la API:

```bash
python limpiar_resultados.py
```

Acepta una ruta opcional (`python limpiar_resultados.py otro.csv`) y escribe
`<nombre>.clean.csv` y `promedio_mensual.csv` junto al archivo de entrada.

## Archivos

| Archivo | Rol |
| --- | --- |
| `extraer_precios_bolsa.py` | Consulta la API por bloques y escribe los resultados |
| `procesamiento.py` | Transformaciones compartidas: deduplicar, ordenar, promedios, serie mensual |
| `limpiar_resultados.py` | Regenera los derivados desde un CSV existente, sin red |

## Estructura de los datos

Una fila por día, con las siguientes columnas:

| Columna | Descripción |
| --- | --- |
| `Id`, `Values_code` | Identificadores devueltos por la API (`Sistema`) |
| `Values_Hour01` … `Values_Hour24` | Precio de bolsa por hora, en COP/kWh |
| `Date` | Fecha del registro (`m/d/yyyy`) |
| `Daily Average` | Promedio de las 24 horas |
| `Monthly Average` | Promedio mensual del `Daily Average` |

## Resultados incluidos

La carpeta `Results/` trae una corrida con datos del **2000-01-01 al 2026-06-16**:

| Archivo | Filas | Contenido |
| --- | --- | --- |
| `precios_bolsa_nacional.csv` | 9.937 | Salida de una versión anterior del script (ver nota) |
| `precios_bolsa_nacional.original.csv` | 9.937 | Copia de respaldo, idéntica al anterior |
| `precios_bolsa_nacional.clean.csv` | 9.664 | Un registro por día, con ambos promedios |
| `promedio_mensual.csv` | 318 | Serie mensual agregada |

> **Nota sobre `precios_bolsa_nacional.csv`.** Este archivo quedó de una versión anterior del
> script y no refleja lo que produce el código actual: conserva 273 filas duplicadas de días
> frontera, le falta `Monthly Average`, y su `Daily Average` no corresponde al promedio de las
> 24 horas. `limpiar_resultados.py` lo corrige y regenera los otros dos archivos —
> se verificó que reproduce `precios_bolsa_nacional.clean.csv` y `promedio_mensual.csv`
> con diferencias del orden de 5e-08, es decir el redondeo del propio CSV.

## Requisitos

- Python 3.9+
- `pydataxm`, `pandas`
