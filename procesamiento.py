"""
Transformaciones sobre los datos del Precio de Bolsa Nacional.

Se comparten entre la extraccion (extraer_precios_bolsa.py) y la regeneracion
de derivados a partir de un CSV ya descargado (limpiar_resultados.py).
"""

import pandas as pd


def columnas_horarias(df):
    """Devuelve las columnas Values_HourNN presentes en el DataFrame."""
    return [c for c in df.columns if c.startswith("Values_Hour")]


def columna_fecha(df):
    """Nombre de la columna de fecha, o None si no se encuentra."""
    for c in df.columns:
        if "fecha" in c.lower() or "date" in c.lower():
            return c
    return None


def ordenar_por_fecha(df):
    """Ordena cronologicamente.

    No se puede ordenar por la columna de texto: la API entrega las fechas como
    'm/d/yyyy', y en ese formato '1/10/2000' es menor que '1/2/2000'.
    """
    col = columna_fecha(df)
    if col is None:
        return df
    orden = pd.to_datetime(df[col]).argsort(kind="stable")
    return df.iloc[orden].reset_index(drop=True)


def eliminar_duplicados(df):
    """Elimina filas repetidas y reporta cuantas se quitaron.

    La API devuelve el dia frontera repetido entre bloques contiguos de fechas.
    """
    antes = len(df)
    df = df.drop_duplicates(ignore_index=True)
    quitadas = antes - len(df)
    if quitadas:
        print(f"Filas duplicadas eliminadas: {quitadas}")
    return df


def agregar_promedio_diario(df):
    """Agrega 'Daily Average' = promedio de las 24 horas del dia."""
    horas = columnas_horarias(df)
    if horas:
        df["Daily Average"] = df[horas].mean(axis=1)
    return df


def agregar_promedio_mensual(df):
    """Agrega 'Monthly Average' = promedio del 'Daily Average' de cada mes-anio."""
    if "Daily Average" not in df.columns:
        return df
    fechas = pd.to_datetime(df[columna_fecha(df)])
    df["Monthly Average"] = df.groupby([fechas.dt.year, fechas.dt.month])[
        "Daily Average"
    ].transform("mean")
    return df


def procesar(df):
    """Pipeline completo de post-proceso: deduplicar, ordenar y agregar promedios.

    Es idempotente: aplicarlo dos veces da el mismo resultado, porque los
    promedios se recalculan siempre a partir de las columnas horarias.
    """
    df = eliminar_duplicados(df)
    df = ordenar_por_fecha(df)
    df = agregar_promedio_diario(df)
    df = agregar_promedio_mensual(df)
    return df


def serie_mensual(df):
    """Serie de un registro por mes, fechada el dia 1, con el promedio del mes."""
    if "Monthly Average" not in df.columns:
        raise ValueError("El DataFrame no tiene la columna 'Monthly Average'.")
    fechas = pd.to_datetime(df[columna_fecha(df)])
    mensual = (
        df.assign(_mes=fechas.dt.to_period("M"))
        .groupby("_mes", as_index=False)["Monthly Average"]
        .first()
    )
    mensual["Date"] = mensual["_mes"].dt.to_timestamp().dt.strftime("%m/%d/%Y")
    return mensual[["Date", "Monthly Average"]]
