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


def custom_mask_clouds(img):
    bands = img.bandNames().getInfo()

    if 'QA_PIXEL' in bands:  # Landsat
        cloud_mask = img.select('QA_PIXEL').bitwiseAnd(1 << 3).eq(0)
        return img.updateMask(cloud_mask)

    elif 'SCL' in bands:  # Sentinel-2
        scl = img.select('SCL')
        # Remove nuvem média, alta, cirros, sombra (ajuste conforme necessário)
        cloud_mask = scl.remap([3, 8, 9, 10], [0]*4, defaultValue=1).eq(1)
        return img.updateMask(cloud_mask)

    else:
        print("[DEBUG] Nenhuma banda de nuvem detectada.")
        return img

def get_clear_sky_percentage(img, roi, debug=False):
    try:
        bands = img.bandNames().getInfo()

        if 'QA_PIXEL' in bands:
            scale = 30
        elif 'SCL' in bands:
            scale = 20
        else:
            scale = 10

        cloud_masked = custom_mask_clouds(img)
        clear = cloud_masked.mask().reduce(ee.Reducer.min()).rename('clear')

        # Usa média de 1s (céu claro)
        stats = clear.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=scale,
            maxPixels=1e9
        ).getInfo()

        clear_mean = stats.get('clear')

        if clear_mean is None:
            if debug:
                print(f"[DEBUG] Nenhum pixel válido na média: {stats}")
            return None

        return clear_mean * 100  # transforma proporção em %

    except Exception as e:
        if debug:
            print(f"[DEBUG] Erro geral em get_clear_sky_percentage: {e}")
        return None


