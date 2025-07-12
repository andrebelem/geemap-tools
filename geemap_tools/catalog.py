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


def list_sat_images(collection_id, roi, max_imgs=500, compute_clear_sky=False, time_range=None):
    """
    Lista imagens de uma coleção Earth Engine com metadados úteis e interseção com uma ROI.

    Args:
        collection_id (str): ID da coleção (ex: 'LANDSAT/LC08/C02/T1_L2', 'COPERNICUS/S2_SR')
        roi (ee.Geometry): Geometria da área de interesse (obrigatória).
        max_imgs (int): Máximo de imagens a processar (default: 500)
        compute_clear_sky (bool): Se True, calcula percentual de céu claro com base na máscara de nuvem.
        time_range (tuple): Par de strings com data inicial e final no formato 'YYYY-MM-DD', exemplo: time_range=("2021-01-01", "2021-12-31")

    Returns:
        pd.DataFrame: Tabela com metadados e percentual da ROI coberto.

    Raises:
        ValueError: Se a ROI não for fornecida.
    """
    if roi is None:
        raise ValueError("É necessário fornecer uma ROI (ee.Geometry) para usar esta função.")

    # Cria a coleção
    collection = ee.ImageCollection(collection_id).filterBounds(roi)

    # Aplica filtro temporal, se fornecido
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
        proportion = 0
        try:
            geom = img.geometry()
            inter = geom.intersection(roi, ee.ErrorMargin(1))
            inter_area = inter.area(ee.ErrorMargin(1)).getInfo()
            proportion = (inter_area / roi_area) * 100 if inter_area > 0 else 0
        except:
            proportion = 0

        # Ajuste de propriedades por sensor
        if 'SPACECRAFT_ID' in props:  # Landsat
            satellite = props.get('SPACECRAFT_ID')
            img_cloud_cover = props.get('CLOUD_COVER')
            solar_elevation = props.get('SUN_ELEVATION')
            solar_azimuth = props.get('SUN_AZIMUTH')
        elif 'SPACECRAFT_NAME' in props:  # Sentinel
            satellite = props.get('SPACECRAFT_NAME')
            img_cloud_cover = props.get('CLOUDY_PIXEL_PERCENTAGE')
            solar_elevation = props.get('MEAN_SOLAR_ZENITH_ANGLE')
            solar_azimuth = props.get('MEAN_SOLAR_AZIMUTH_ANGLE')
            if solar_elevation is not None:
                solar_elevation = 90 - solar_elevation
        else:
            satellite = props.get('platform', 'unknown')
            img_cloud_cover = props.get('CLOUD_COVER', None)
            solar_elevation = None
            solar_azimuth = None

        # Cálculo opcional de céu claro
        clear_pct = None
        if compute_clear_sky:
            try:
                clear_pct = get_clear_sky_percentage(img, roi)
            except Exception as e:
                print(f"[DEBUG] Erro ao calcular clear_sky para {img_id}: {e}")
                clear_pct = None

        metadata = {
            'id': img_id,
            'date': pd.to_datetime(props.get('system:time_start'), unit='ms'),
            'satellite': satellite,
            'img_cloud_cover': img_cloud_cover,
            'solar_elevation': solar_elevation,
            'solar_azimuth': solar_azimuth,
            'proportion_roi_%': proportion,
            'clear_sky_%': clear_pct,
        }

        metadata_list.append(metadata)

    return pd.DataFrame(metadata_list)

