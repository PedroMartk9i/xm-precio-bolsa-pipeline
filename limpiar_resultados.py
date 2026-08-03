"""
Regenera los archivos derivados a partir de un CSV ya descargado, sin volver
a consultar la API de XM.

Produce, junto al CSV de entrada:
  - <nombre>.clean.csv    un registro por dia, con 'Daily Average' y 'Monthly Average'
  - promedio_mensual.csv  la serie mensual agregada

Uso:
    python limpiar_resultados.py [ruta_csv]

Por defecto lee Results/precios_bolsa_nacional.csv.
"""

import argparse
import os

import pandas as pd

import procesamiento

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
CSV_POR_DEFECTO = os.path.join(RUTA_BASE, "Results", "precios_bolsa_nacional.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv",
        nargs="?",
        default=CSV_POR_DEFECTO,
        help="CSV crudo de la extraccion (por defecto: Results/precios_bolsa_nacional.csv)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        parser.error(f"No existe el archivo: {args.csv}")

    carpeta = os.path.dirname(os.path.abspath(args.csv))
    raiz = os.path.splitext(os.path.basename(args.csv))[0]
    salida_limpia = os.path.join(carpeta, f"{raiz}.clean.csv")
    salida_mensual = os.path.join(carpeta, "promedio_mensual.csv")

    print(f"Leyendo {args.csv} ...")
    df = pd.read_csv(args.csv, encoding="utf-8-sig")
    print(f"Registros de entrada: {len(df)}")

    df = procesamiento.procesar(df)
    mensual = procesamiento.serie_mensual(df)

    df.to_csv(salida_limpia, index=False, encoding="utf-8-sig")
    mensual.to_csv(salida_mensual, index=False, encoding="utf-8-sig")

    print(f"\n{salida_limpia}")
    print(f"  {len(df)} registros diarios")
    print(f"{salida_mensual}")
    print(f"  {len(mensual)} registros mensuales")


if __name__ == "__main__":
    main()
