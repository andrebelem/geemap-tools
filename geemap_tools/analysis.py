# geemap_tools/gee_utils.py
import ee
import eemont
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import os
import warnings
from pathlib import Path
from zipfile import ZipFile
import tempfile
from tempfile import TemporaryDirectory


def index_to_timeseries(df, roi, index_name, scale=None, debug=False):
    """
    Calcula o valor médio e o desvio padrão de um índice espectral do eemont
    sobre uma ROI, para cada imagem listada em um DataFrame.

    Args:
        df (pd.DataFrame): DataFrame com coluna 'id' contendo IDs de imagens.
        roi (ee.Geometry): Região de interesse.
        index_name (str): Nome do índice (ex: 'NDWI', 'NDMI', 'MNDWI', etc.).
        scale (int, optional): Escala em metros (detectada automaticamente se None).
        debug (bool): Se True, imprime mensagens de debug.

    Returns:
        pd.DataFrame: Mesmo DataFrame com colunas <index_name>_mean e _std.
    """
    index_means = []
    index_stds = []

    for img_id in tqdm(df['id'], desc=f"Calculando {index_name} na ROI"):
        try:
            img = ee.Image(img_id)
            img = img.spectralIndices(index_name)

            # Detecta escala baseada no sensor (se necessário)
            if scale is None:
                bands = img.bandNames().getInfo()
                if 'QA_PIXEL' in bands:
                    used_scale = 30  # Landsat
                elif 'SCL' in bands:
                    used_scale = 20  # Sentinel-2
                else:
                    used_scale = 10
                if debug:
                    print(f"[DEBUG] Escala auto-definida para {img_id}: {used_scale}")
            else:
                used_scale = scale

            # Redução do índice sobre a ROI
            stats = img.select(index_name).reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
                geometry=roi,
                scale=used_scale,
                maxPixels=1e9
            ).getInfo()

            index_means.append(stats.get(f"{index_name}_mean"))
            index_stds.append(stats.get(f"{index_name}_stdDev"))

        except Exception as e:
            if debug:
                print(f"[DEBUG] Falha ao calcular {index_name} para {img_id}: {e}")
            index_means.append(None)
            index_stds.append(None)

    df = df.copy()
    df[f"{index_name}_mean"] = index_means
    df[f"{index_name}_std"] = index_stds

    return df