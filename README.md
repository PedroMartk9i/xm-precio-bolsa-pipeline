# Precio de Bolsa Nacional — Pipeline de extracción (API XM)

Pipeline para extraer la serie histórica del **Precio de Bolsa Nacional** del Mercado de
Energía Mayorista colombiano usando la API pública de [XM](https://www.xm.com.co/)
(a través de `pydataxm`), y dejar los datos listos para análisis.

La API no requiere autenticación ni llaves.

## Qué hace

1. Genera rangos de fechas de máximo 30 días calendario (límite de la API para datos horarios),
   desde `2000-01-01` hasta hoy.
2. Consulta la colección `PrecBolsNaci` / métrica `Sistema` en cada rango, con una pausa de
   0.5 s entre llamadas. Los rangos que devuelven 204 (sin contenido) se reportan y se omiten.
3. Concatena, elimina duplicados de los días frontera entre bloques y ordena por fecha.
4. Calcula dos columnas derivadas:
   - `Daily Average` — promedio de las 24 horas del día.
   - `Monthly Average` — promedio de los `Daily Average` del mes, replicado en cada fila del mes.
5. Guarda el resultado en `Results/precios_bolsa_nacional.csv` (UTF-8 con BOM).

## Uso

```bash
pip install -r requirements.txt
```

```bash
python extraer_precios_bolsa.py
```

La extracción completa son ~320 consultas, así que toma varios minutos.

Para acotar el rango, edita `FECHA_INICIO` / `FECHA_FIN` en el encabezado del script.

## Estructura de los datos

Una fila por día, con las siguientes columnas:

| Columna | Descripción |
| --- | --- |
| `Id`, `Values_code` | Identificadores devueltos por la API (`Sistema`) |
| `Values_Hour01` … `Values_Hour24` | Precio de bolsa por hora, en COP/kWh |
| `Date` | Fecha del registro |
| `Daily Average` | Promedio de las 24 horas |
| `Monthly Average` | Promedio mensual del `Daily Average` |

## Resultados incluidos

La carpeta `Results/` trae una corrida del pipeline con datos del **2000-01-01 al 2026-06-16**:

| Archivo | Filas | Contenido |
| --- | --- | --- |
| `precios_bolsa_nacional.csv` | 9.937 | Salida cruda del pipeline |
| `precios_bolsa_nacional.original.csv` | 9.937 | Copia de respaldo de la salida cruda (idéntica al anterior) |
| `precios_bolsa_nacional.clean.csv` | 9.664 | Versión depurada — un registro por día, con `Monthly Average` |
| `promedio_mensual.csv` | 318 | Serie mensual agregada |

> Nota: `*.clean.csv` y `promedio_mensual.csv` se generaron en un paso de depuración
> posterior que no está incluido en este repositorio; `extraer_precios_bolsa.py` solo
> produce `precios_bolsa_nacional.csv`.

## Requisitos

- Python 3.9+
- `pydataxm`, `pandas`
