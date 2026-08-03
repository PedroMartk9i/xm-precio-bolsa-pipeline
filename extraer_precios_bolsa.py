"""
Script para extraer datos históricos del Precio de Bolsa Nacional
del Mercado de Energía Mayorista colombiano usando la API de XM.

Los datos se guardan en CSV para procesarlos en Google Colab.
"""

import datetime as dt
import time
import os
import pandas as pd
from pydataxm.pydataxm import ReadDB

# --- Configuración ---
# La API de XM tiene datos disponibles desde el 2000-01-01.
FECHA_INICIO = dt.date(2000, 1, 1)
FECHA_FIN = dt.date.today()

# La API permite máximo 30 días por consulta para datos horarios/diarios.
# Un delta de 29 días cubre 30 días calendario inclusive (inicio .. inicio+29).
DIAS_POR_CONSULTA = 29

# Carpeta de resultados
RUTA_RESULTADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Results")
ARCHIVO_CSV = os.path.join(RUTA_RESULTADOS, "precios_bolsa_nacional.csv")

# --- Funciones ---

def generar_rangos_fechas(inicio, fin, dias):
    """Genera pares (inicio, fin) de máximo `dias` días cada uno."""
    rangos = []
    actual = inicio
    while actual <= fin:
        fin_rango = min(actual + dt.timedelta(days=dias), fin)
        rangos.append((actual, fin_rango))
        actual = fin_rango + dt.timedelta(days=1)
    return rangos


def agregar_promedio_diario(df):
    """Agrega una columna 'Daily Average' = promedio de las 24 horas del día."""
    horas = [c for c in df.columns if c.startswith("Values_Hour")]
    if horas:
        df["Daily Average"] = df[horas].mean(axis=1)
    return df


def agregar_promedio_mensual(df):
    """Agrega 'Monthly Average' = promedio del 'Daily Average' de cada mes-año."""
    if "Daily Average" not in df.columns:
        return df
    fechas = pd.to_datetime(df["Date"])
    df["Monthly Average"] = df.groupby([fechas.dt.year, fechas.dt.month])[
        "Daily Average"
    ].transform("mean")
    return df


def extraer_precios():
    """Consulta la API de XM en bloques de 30 días calendario y concatena los resultados."""
    api = ReadDB()
    rangos = generar_rangos_fechas(FECHA_INICIO, FECHA_FIN, DIAS_POR_CONSULTA)
    total = len(rangos)

    print(f"Precio de Bolsa Nacional - Extracción histórica")
    print(f"Rango: {FECHA_INICIO} a {FECHA_FIN}")
    print(f"Total de consultas a realizar: {total}")
    print("-" * 50)

    frames = []
    errores = []

    for i, (inicio, fin) in enumerate(rangos, 1):
        print(f"[{i}/{total}] Consultando {inicio} -> {fin} ... ", end="", flush=True)
        try:
            df = api.request_data(
                coleccion="PrecBolsNaci",
                metrica="Sistema",
                start_date=inicio,
                end_date=fin,
            )
            if df is not None and not df.empty:
                frames.append(df)
                print(f"OK ({len(df)} registros)")
            else:
                print("Sin datos")
        except Exception as e:
            msg = str(e)
            # Errores 204 = sin contenido para ese rango, es normal en fechas antiguas
            if "204" in msg:
                print("Sin datos (204)")
            else:
                print(f"Error: {msg}")
                errores.append({"inicio": inicio, "fin": fin, "error": msg})

        # Pausa breve para no saturar la API
        time.sleep(0.5)

    if not frames:
        print("\nNo se obtuvieron datos en ningún rango.")
        return None

    resultado = pd.concat(frames, ignore_index=True)

    # La API devuelve el día de frontera repetido en bloques contiguos: eliminar duplicados.
    antes = len(resultado)
    resultado.drop_duplicates(inplace=True, ignore_index=True)
    if antes != len(resultado):
        print(f"\nFilas duplicadas eliminadas: {antes - len(resultado)}")

    # Ordenar por fecha
    col_fecha = [c for c in resultado.columns if "fecha" in c.lower() or "date" in c.lower()]
    if col_fecha:
        resultado.sort_values(by=col_fecha[0], inplace=True)
        resultado.reset_index(drop=True, inplace=True)

    # Promedio diario calculado a partir de las 24 horas (consistente con los datos).
    resultado = agregar_promedio_diario(resultado)
    # Promedio mensual (por mes-año) replicado en cada fila del mes.
    resultado = agregar_promedio_mensual(resultado)

    if errores:
        print(f"\nAdvertencia: {len(errores)} rangos con error:")
        for e in errores:
            print(f"  {e['inicio']} - {e['fin']}: {e['error']}")

    return resultado


def main():
    os.makedirs(RUTA_RESULTADOS, exist_ok=True)

    print("Conectando a la API de XM (no requiere autenticación)...\n")
    df = extraer_precios()

    if df is not None:
        df.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8-sig")
        print(f"\nDatos guardados en: {ARCHIVO_CSV}")
        print(f"Total de registros: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        if not df.empty:
            col_fecha = [c for c in df.columns if "fecha" in c.lower() or "date" in c.lower()]
            if col_fecha:
                print(f"Rango de fechas en datos: {df[col_fecha[0]].min()} a {df[col_fecha[0]].max()}")
    else:
        print("No se generó archivo CSV.")


if __name__ == "__main__":
    main()
