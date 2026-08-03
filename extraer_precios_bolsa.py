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

import procesamiento

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
ARCHIVO_MENSUAL = os.path.join(RUTA_RESULTADOS, "promedio_mensual.csv")

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

    # Deduplicar los días frontera, ordenar cronológicamente y calcular los
    # promedios diario y mensual a partir de las columnas horarias.
    print()
    resultado = procesamiento.procesar(resultado)

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

        mensual = procesamiento.serie_mensual(df)
        mensual.to_csv(ARCHIVO_MENSUAL, index=False, encoding="utf-8-sig")
        print(f"Serie mensual guardada en: {ARCHIVO_MENSUAL} ({len(mensual)} meses)")

        if not df.empty:
            fechas = pd.to_datetime(df[procesamiento.columna_fecha(df)])
            print(f"Rango de fechas en datos: {fechas.min().date()} a {fechas.max().date()}")
    else:
        print("No se generó archivo CSV.")


if __name__ == "__main__":
    main()
