# geemap_tools/io.py
import ee
import eemont
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import os
import warnings
from pathlib import Path
from zipfile import ZipFile
import zipfile
import tempfile
from tempfile import TemporaryDirectory


def roi_to_file(roi, filename, format='geojson', wrap_geometry=True):
    """
    Exporta uma ROI (região de interesse) do Earth Engine para arquivo no disco local.

    A ROI pode ser uma `ee.Geometry`, `ee.Feature` ou `ee.FeatureCollection`, e será convertida
    para um arquivo `.geojson` ou `.shp` (compactado como `.zip`) com sistema de referência EPSG:4326.

    Args:
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Objeto de entrada do Earth Engine.
        filename (str): Caminho base (sem extensão) para salvar o arquivo de saída.
        format (str, optional): Formato de saída. Pode ser `'geojson'` ou `'shp'`. Padrão é `'geojson'`.
        wrap_geometry (bool, optional): Se `True`, embrulha `ee.Geometry` como `ee.Feature` antes da exportação. Necessário para `ee.Geometry`.

    Returns:
        str: Caminho absoluto do arquivo salvo (ex: `/caminho/arquivo.geojson` ou `/caminho/arquivo.zip`).

    Raises:
        ValueError: Se a geometria for inválida ou não estiver embrulhada corretamente.
        TypeError: Se o tipo da ROI for incompatível.
        RuntimeError: Se falhar ao converter para GeoDataFrame ou salvar o arquivo.
    """
    filename = str(Path(filename).with_suffix(''))
    os.makedirs(os.path.dirname(filename), exist_ok=True)

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
        raise TypeError(f"Tipo inválido: {type(roi)}. Esperado ee.Geometry, ee.Feature ou ee.FeatureCollection.")

    try:
        gdf = gpd.GeoDataFrame.from_features(features)
        gdf = gdf.set_crs("EPSG:4326")
    except Exception as e:
        raise RuntimeError(f"Erro ao converter para GeoDataFrame: {e}")

    if format == 'geojson':
        output_path = f"{filename}.geojson"
        gdf.to_file(output_path, driver='GeoJSON')
    elif format == 'shp':
        with tempfile.TemporaryDirectory() as tmpdir:
            base_name = Path(filename).name
            tmp_shp = os.path.join(tmpdir, base_name + ".shp")
            gdf.to_file(tmp_shp)
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
    Converte um arquivo local (GeoJSON, SHP ou ZIP contendo SHP) em uma FeatureCollection do Earth Engine.

    O arquivo é lido com `geopandas` e convertido para `ee.FeatureCollection`, com reprojectado para EPSG:4326.
    Suporta arquivos `.geojson`, `.shp` ou `.zip` contendo shapefile.

    Args:
        filepath (str): Caminho para o arquivo de entrada.

    Returns:
        ee.FeatureCollection: Objeto Earth Engine correspondente à geometria do arquivo.

    Raises:
        FileNotFoundError: Se o arquivo não for encontrado.
        ValueError: Se o zip não contiver um shapefile válido.
        RuntimeError: Se houver erro ao ler com geopandas ou ao converter para `ee.Feature`.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    if filepath.endswith(".zip"):
        with TemporaryDirectory() as tmpdir:
            with ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
            if not shp_files:
                raise ValueError("Nenhum .shp encontrado no .zip.")
            filepath = os.path.join(tmpdir, shp_files[0])
            gdf = gpd.read_file(filepath)
    else:
        try:
            gdf = gpd.read_file(filepath)
        except Exception as e:
            raise RuntimeError(f"Erro ao ler o arquivo com geopandas: {e}")

    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    else:
        gdf = gdf.to_crs("EPSG:4326")

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

