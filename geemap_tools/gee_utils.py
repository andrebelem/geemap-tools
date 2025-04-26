# geemap_tools/gee_utils.py
import ee
import eemont
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import os
import warnings


def roi_to_file(roi, filename, format='geojson', wrap_geometry=True):
    """
    Exporta uma ROI do GEE para GeoJSON ou Shapefile.

    Args:
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Objeto de entrada.
        filename (str): Nome base do arquivo de saída (sem extensão).
        format (str): 'geojson' ou 'shp'.
        wrap_geometry (bool): Se True, transforma ee.Geometry em ee.Feature.

    Returns:
        str: Caminho completo do arquivo gerado.
    """
    # Verifica se é Geometry
    if isinstance(roi, ee.Geometry):
        if roi.type().getInfo() not in ['Polygon', 'MultiPolygon']:
            raise ValueError("A geometria deve ser Polygon ou MultiPolygon.")
        if wrap_geometry:
            feature = ee.Feature(roi)
        else:
            raise ValueError("A geometria precisa ser embrulhada como Feature para exportação.")
        features = [feature.getInfo()]

    # Verifica se é Feature
    elif isinstance(roi, ee.Feature):
        features = [roi.getInfo()]

    # Verifica se é FeatureCollection
    elif isinstance(roi, ee.FeatureCollection):
        try:
            feature_dict = roi.getInfo()
            features = feature_dict['features']
        except Exception as e:
            raise RuntimeError(f"Erro ao acessar FeatureCollection com getInfo(): {e}")

    else:
        raise TypeError(
            f"Tipo inválido: {type(roi)}. Esperado ee.Geometry, ee.Feature ou ee.FeatureCollection."
        )

    # Converte para GeoDataFrame
    try:
        gdf = gpd.GeoDataFrame.from_features(features)
    except Exception as e:
        raise RuntimeError(f"Erro ao converter para GeoDataFrame: {e}")

    # Exporta
    if format == 'geojson':
        output_path = f"{filename}.geojson"
        gdf.to_file(output_path, driver='GeoJSON')
    elif format == 'shp':
        output_path = f"{filename}.shp"
        gdf.to_file(output_path)
    else:
        raise ValueError("Formato inválido. Use 'geojson' ou 'shp'.")

    return os.path.abspath(output_path)

def file_to_roi(filepath):
    """
    Converte um arquivo shapefile, geojson, kml ou kmz em uma ee.FeatureCollection.

    Args:
        filepath (str): Caminho completo para o arquivo.

    Returns:
        ee.FeatureCollection: FeatureCollection correspondente.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    # Lê o arquivo com geopandas
    try:
        gdf = gpd.read_file(filepath)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler o arquivo com geopandas: {e}")

    # Converte cada geometria para ee.Feature
    try:
        features = []
        for _, row in gdf.iterrows():
            geom_geojson = row.geometry.__geo_interface__
            props = row.drop(labels='geometry').to_dict()
            ee_geom = ee.Geometry(geom_geojson)
            ee_feat = ee.Feature(ee_geom, props)
            features.append(ee_feat)
    except Exception as e:
        raise RuntimeError(f"Erro ao converter para ee.Feature: {e}")

    return ee.FeatureCollection(features)

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