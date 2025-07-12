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


def roi_to_file(roi, filename, format='geojson', wrap_geometry=True):
    """
    Exporta uma ROI do GEE para GeoJSON ou Shapefile (.zip).

    Args:
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Objeto Earth Engine.
        filename (str): Caminho base para o arquivo de saída (sem extensão).
        format (str): 'geojson' ou 'shp'. No caso de 'shp', gera um arquivo .zip.
        wrap_geometry (bool): Se True, transforma ee.Geometry em ee.Feature.

    Returns:
        str: Caminho absoluto do arquivo gerado.
    """
    # Garante que filename não tenha extensão e cria diretório se necessário
    filename = str(Path(filename).with_suffix(''))
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Determina tipo de entrada
    if isinstance(roi, ee.Geometry):
        if roi.type().getInfo() not in ['Polygon', 'MultiPolygon']:
            raise ValueError("A geometria deve ser Polygon ou MultiPolygon.")
        if wrap_geometry:
            roi = ee.Feature(roi)
        else:
            raise ValueError("A geometria precisa ser embrulhada como Feature para exportação.")
        features = [roi.getInfo()]

    elif isinstance(roi, ee.Feature):
        features = [roi.getInfo()]

    elif isinstance(roi, ee.FeatureCollection):
        try:
            features = roi.getInfo().get('features', [])
        except Exception as e:
            raise RuntimeError(f"Erro ao acessar FeatureCollection com getInfo(): {e}")

    else:
        raise TypeError(
            f"Tipo inválido: {type(roi)}. Esperado ee.Geometry, ee.Feature ou ee.FeatureCollection."
        )

    # Converte para GeoDataFrame e aplica CRS
    try:
        gdf = gpd.GeoDataFrame.from_features(features)
        gdf = gdf.set_crs("EPSG:4326")
    except Exception as e:
        raise RuntimeError(f"Erro ao converter para GeoDataFrame: {e}")

    # Exporta para o formato escolhido
    if format == 'geojson':
        output_path = f"{filename}.geojson"
        gdf.to_file(output_path, driver='GeoJSON')

    elif format == 'shp':
        # Cria diretório temporário para armazenar arquivos .shp, .dbf, etc.
        with tempfile.TemporaryDirectory() as tmpdir:
            base_name = Path(filename).name
            tmp_shp = os.path.join(tmpdir, base_name + ".shp")
            gdf.to_file(tmp_shp)

            # Cria .zip com todos os componentes do shapefile
            zip_path = f"{filename}.zip"
            with ZipFile(zip_path, 'w') as zipf:
                for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                    f = os.path.join(tmpdir, base_name + ext)
                    if os.path.exists(f):
                        zipf.write(f, arcname=os.path.basename(f))

        output_path = zip_path

    else:
        raise ValueError("Formato inválido. Use 'geojson' ou 'shp'.")

    return os.path.abspath(output_path)

def file_to_roi(filepath):
    """
    Converte um arquivo shapefile (.shp ou .zip), GeoJSON, KML ou KMZ em uma ee.FeatureCollection.

    Args:
        filepath (str): Caminho completo para o arquivo.

    Returns:
        ee.FeatureCollection: FeatureCollection correspondente.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    # Suporte para ZIP com shapefile
    if filepath.endswith(".zip"):
        with TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
            if not shp_files:
                raise ValueError("Nenhum .shp encontrado no .zip.")
            filepath = os.path.join(tmpdir, shp_files[0])

            # Lê shapefile extraído
            gdf = gpd.read_file(filepath)
    else:
        try:
            gdf = gpd.read_file(filepath)
        except Exception as e:
            raise RuntimeError(f"Erro ao ler o arquivo com geopandas: {e}")

    # Garante CRS WGS84
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    else:
        gdf = gdf.to_crs("EPSG:4326")

    # Converte para ee.FeatureCollection
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

