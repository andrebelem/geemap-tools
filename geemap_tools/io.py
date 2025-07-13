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
    
    Parâmetros:
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Objeto de entrada do Earth Engine.
        filename (str): Caminho base (sem extensão) para salvar o arquivo de saída.
        format (str, opcional): Formato de saída. Pode ser `'geojson'` ou `'shp'`. Padrão é `'geojson'`.
        wrap_geometry (bool, opcional): Se `True`, embrulha `ee.Geometry` como `ee.Feature` antes da exportação. Necessário para `ee.Geometry`.
    
    Retorno:
        str: Caminho absoluto do arquivo salvo (ex: `/caminho/arquivo.geojson` ou `/caminho/arquivo.zip`).
    
    Erros:
        ValueError: Se a geometria for inválida ou não estiver embrulhada corretamente.
        TypeError: Se o tipo da ROI for incompatível.
        RuntimeError: Se falhar ao converter para GeoDataFrame ou salvar o arquivo.
    
    ----
    Exports an Earth Engine ROI (region of interest) to a local file.
    
    The ROI can be an `ee.Geometry`, `ee.Feature`, or `ee.FeatureCollection`, and will be converted
    to a `.geojson` file or a `.shp` file (compressed as `.zip`) using the EPSG:4326 reference system.
    
    Args:
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Earth Engine input object.
        filename (str): Base path (without extension) to save the output file.
        format (str, optional): Output format. Can be `'geojson'` or `'shp'`. Default is `'geojson'`.
        wrap_geometry (bool, optional): If `True`, wraps an `ee.Geometry` as an `ee.Feature` before export. Required for `ee.Geometry`.
    
    Returns:
        str: Absolute path to the saved file (e.g., `/path/file.geojson` or `/path/file.zip`).
    
    Raises:
        ValueError: If the geometry is invalid or not wrapped correctly.
        TypeError: If the ROI type is incompatible.
        RuntimeError: If conversion to GeoDataFrame or file saving fails.
    """
    filename = str(Path(filename).with_suffix(''))
    output_dir = os.path.dirname(filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

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
    
    O arquivo é lido com `geopandas` e convertido para `ee.FeatureCollection`, reprojetado para EPSG:4326.
    Suporta arquivos `.geojson`, `.shp` ou `.zip` contendo shapefile.
    
    Parâmetros:
        filepath (str): Caminho para o arquivo de entrada.
    
    Retorno:
        ee.FeatureCollection: Objeto Earth Engine correspondente à geometria do arquivo.
    
    Erros:
        FileNotFoundError: Se o arquivo não for encontrado.
        ValueError: Se o zip não contiver um shapefile válido.
        RuntimeError: Se houver erro ao ler com geopandas ou ao converter para `ee.Feature`.
    
    ----
    Converts a local file (GeoJSON, SHP, or ZIP containing SHP) into an Earth Engine FeatureCollection.
    
    The file is read using `geopandas` and converted to an `ee.FeatureCollection`, reprojected to EPSG:4326.
    Supports `.geojson`, `.shp`, or `.zip` files containing a shapefile.
    
    Args:
        filepath (str): Path to the input file.
    
    Returns:
        ee.FeatureCollection: Earth Engine object corresponding to the file geometry.
    
    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the zip does not contain a valid shapefile.
        RuntimeError: If reading with geopandas or converting to `ee.Feature` fails.
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

