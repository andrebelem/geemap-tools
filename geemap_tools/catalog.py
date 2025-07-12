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
from .clouds import get_clear_sky_percentage

def list_sat_images(collection_id, roi, max_imgs=500, compute_clear_sky=False, time_range=None):
    """
    Lista imagens de uma coleção Earth Engine com metadados úteis e interseção com uma ROI.

    Args:
        collection_id (str): ID da coleção (ex: 'LANDSAT/LC08/C02/T1_L2', 'COPERNICUS/S2_SR')
        roi (ee.Geometry): Geometria da área de interesse (obrigatória).
        max_imgs (int): Máximo de imagens a processar (default: 500)
        compute_clear_sky (bool): Se True, calcula percentual de céu claro com base na máscara de nuvem.
        time_range (tuple): Par de strings com data inicial e final no formato 'YYYY-MM-DD'.

    Returns:
        pd.DataFrame: Tabela com metadados e percentual da ROI coberto.

    Raises:
        ValueError: Se a ROI não for fornecida ou a coleção não for reconhecida.
    """
    if roi is None:
        raise ValueError("É necessário fornecer uma ROI (ee.Geometry) para usar esta função.")

    SATELLITE_METADATA = {
        "LANDSAT": {
            "satellite": "SPACECRAFT_ID",
            "cloud": "CLOUD_COVER",
            "elevation": "SUN_ELEVATION",
            "azimuth": "SUN_AZIMUTH"
        },
        "SENTINEL": {
            "satellite": "SPACECRAFT_NAME",
            "cloud": "CLOUDY_PIXEL_PERCENTAGE",
            "elevation": "MEAN_SOLAR_ZENITH_ANGLE",
            "azimuth": "MEAN_SOLAR_AZIMUTH_ANGLE",
            "zenith_to_elevation": True
        }
    }

    # Verifica o tipo de coleção
    if "LANDSAT" in collection_id.upper():
        meta = SATELLITE_METADATA["LANDSAT"]
    elif "S2" in collection_id.upper() or "SENTINEL" in collection_id.upper():
        meta = SATELLITE_METADATA["SENTINEL"]
    else:
        raise ValueError(f"A coleção '{collection_id}' não é compatível. Apenas LANDSAT ou SENTINEL são suportados.")

    # Cria a coleção
    collection = ee.ImageCollection(collection_id).filterBounds(roi)

    if time_range is not None:
        start_date, end_date = time_range
        collection = collection.filterDate(start_date, end_date)

    roi_area = roi.area(ee.ErrorMargin(1)).getInfo()
    ids = collection.aggregate_array('system:id').getInfo()
    ids = ids[:max_imgs]

    metadata_list = []

    for img_id in tqdm(ids, desc="Coletando metadados"):
        img = ee.Image(img_id)
        props = img.getInfo().get('properties', {})

        # Proporção da imagem que cobre a ROI
        try:
            geom = img.geometry()
            inter = geom.intersection(roi, ee.ErrorMargin(1))
            inter_area = inter.area(ee.ErrorMargin(1)).getInfo()
            proportion = round((inter_area / roi_area) * 100, 1) if inter_area > 0 else 0
        except:
            proportion = 0

        # Extrai campos conforme dicionário
        satellite = props.get(meta['satellite'], 'unknown')
        img_cloud_cover = props.get(meta['cloud'])
        solar_elevation = props.get(meta['elevation'])
        solar_azimuth = props.get(meta['azimuth'])

        if meta.get('zenith_to_elevation') and solar_elevation is not None:
            solar_elevation = 90 - solar_elevation

        # Cálculo opcional de céu claro
        clear_pct = None
        if compute_clear_sky:
            try:
                clear_pct = get_clear_sky_percentage(img, roi)
            except Exception as e:
                print(f"[DEBUG] Erro ao calcular clear_sky para {img_id}: {e}")
                clear_pct = None

        # Arredondamento
        metadata = {
            'id': img_id,
            'date': pd.to_datetime(props.get('system:time_start'), unit='ms'),
            'satellite': satellite,
            'img_cloud_cover': round(img_cloud_cover) if img_cloud_cover is not None else None,
            'solar_elevation': round(solar_elevation) if solar_elevation is not None else None,
            'solar_azimuth': round(solar_azimuth) if solar_azimuth is not None else None,
            'proportion_roi_%': round(proportion, 1),
            'clear_sky_%': round(clear_pct, 1) if clear_pct is not None else None,
        }

        metadata_list.append(metadata)

    return pd.DataFrame(metadata_list)



