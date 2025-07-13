# USAGE

This document was generated automatically from the public functions defined in `geemap_tools`.

Each function is documented using bilingual docstrings (Portuguese and English) and grouped by module.

---


## Module `analysis`

### `index_to_timeseries(df, roi, index_name, scale=None, debug=False)`

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

------------------------------------------------------------------------

Computes the mean and standard deviation of a spectral index (from eemont)
over a given ROI for each image listed in a DataFrame.

Args:
df (pd.DataFrame): DataFrame with a column 'id' containing image IDs.
roi (ee.Geometry): Region of interest.
index_name (str): Name of the spectral index (e.g., 'NDWI', 'NDMI', 'MNDWI', etc.).
scale (int, optional): Export scale in meters (automatically detected if None).
debug (bool): If True, prints debug messages.

Returns:
pd.DataFrame: The same DataFrame with additional columns <index_name>_mean and _std.

### `describe_roi(roi, show_pixels_table=True, print_summary=True, pixel_res=None)`

Descreve uma ROI do Google Earth Engine, retornando área, perímetro
e estimativa do número de pixels para diferentes resoluções espaciais.

Args:
roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Região de interesse.
show_pixels_table (bool): Se True, exibe uma tabela com nº estimado de pixels por resolução.
print_summary (bool): Se True, imprime área e perímetro formatados.
pixel_res (int | float | list, opcional): Resolução em metros para estimativa.
Por padrão usa [10, 30, 60]. Pode ser usada com valores como 4000 (TerraClimate) ou 5000 (CHIRPS).

Returns:
dict: {
"area_km2": área total em km²,
"perimetro_km": perímetro total em km,
"n_pixels": dicionário com estimativas de número de pixels por resolução,
"df": DataFrame com a tabela (se show_pixels_table=True)
}

------------------------------------------------------------------------

Describes a Google Earth Engine ROI, returning area, perimeter,
and an estimate of the number of pixels at different spatial resolutions.

Args:
roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Region of interest.
show_pixels_table (bool): If True, displays a table with estimated number of pixels per resolution.
print_summary (bool): If True, prints formatted area and perimeter.
pixel_res (int | float | list, optional): Resolution(s) in meters for estimation.
Default is [10, 30, 60]. You may also use values like 4000 (TerraClimate) or 5000 (CHIRPS).

Returns:
dict: {
"area_km2": total area in km²,
"perimetro_km": total perimeter in km,
"n_pixels": dictionary with pixel count estimates by resolution,
"df": DataFrame with the table (if show_pixels_table=True)
}

### `get_TerraClimate(roi, start="2000-01-01", end="2025-12-31",
                     variables=["pr", "pet", "tmmx", "tmmn"],
                     debug=False)`

Extrai estatísticas mensais da coleção TerraClimate para uma ROI.

Args:
roi (ee.Geometry): Região de interesse.
start (str): Data inicial no formato 'YYYY-MM-DD'.
end (str): Data final no formato 'YYYY-MM-DD'.
variables (list): Lista com variáveis desejadas.
Opções válidas:
['aet', 'def', 'pdsi', 'pet', 'pr', 'q', 'soil',
'swe', 'tmmx', 'tmmn', 'vap', 'vpd', 'ws']
debug (bool): Se True, imprime mensagens de depuração.

Returns:
pd.DataFrame: DataFrame com estatísticas mensais para cada variável selecionada.
Cada variável terá colunas com os sufixos:
_mean, _median, _max, _min, _stdDev.

------------------------------------------------------------------------

Extracts monthly statistics from the TerraClimate collection for a given ROI.

Args:
roi (ee.Geometry): Region of interest.
start (str): Start date in 'YYYY-MM-DD' format.
end (str): End date in 'YYYY-MM-DD' format.
variables (list): List of desired variables.
Valid options:
['aet', 'def', 'pdsi', 'pet', 'pr', 'q', 'soil',
'swe', 'tmmx', 'tmmn', 'vap', 'vpd', 'ws']
debug (bool): If True, prints debug messages.

Returns:
pd.DataFrame: DataFrame with monthly statistics for each selected variable.
Each variable will have columns with the suffixes:
_mean, _median, _max, _min, _stdDev.

### `stats_by_month(img):
        stats = img.reduceRegion(
            reducer=reducer,
            geometry=roi,
            scale=4000,
            maxPixels=1e9
        )

        result = {'date': img.date().format("YYYY-MM")}
        for var in vars_selected:
            for stat in ['mean', 'median', 'max', 'min', 'stdDev']:
                result[f"{var}_{stat}"] = stats.get(f"{var}_{stat}")
        return ee.Feature(None, result)

    # Aplica a função
    features = ee.FeatureCollection(terra.map(stats_by_month))

    # Converte para DataFrame
    df = geemap.ee_to_df(features)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')

    # Ajusta temperaturas (de décimos de grau para °C)
    for tvar in ['tmmx', 'tmmn']:
        if tvar in vars_selected:
            for stat in ['mean', 'median', 'max', 'min', 'stdDev']:
                col = f"{tvar}_{stat}"
                if col in df.columns:
                    df[col] = df[col] / 10.0

    # Define atributos com unidades
    units = {
        "aet": "mm",
        "def": "mm",
        "pdsi": "índice (adimensional)",
        "pet": "mm",
        "pr": "mm",
        "q": "mm",
        "soil": "mm",
        "swe": "mm",
        "tmmx": "°C",
        "tmmn": "°C",
        "vap": "kPa",
        "vpd": "kPa",
        "ws": "m/s"
    }
    df.attrs = {f"{v}_unit": units[v] for v in vars_selected}

    if debug:
        print(f"[DEBUG] Variáveis selecionadas: {vars_selected}")
        print(f"[DEBUG] Linhas retornadas: {len(df)}")
        print(f"[DEBUG] Colunas: {list(df.columns)}")

    return df

import ee
import pandas as pd
import warnings
from tqdm import tqdm
import geemap

def get_CHIRPS(roi, start="2000-01-01", end="2025-12-31", frequency="monthly", debug=False)`

Extrai dados da coleção CHIRPS Daily para uma região e período definidos.

Args:
roi (ee.Geometry): Região de interesse (ex: ee.Geometry.Polygon).
start (str): Data inicial no formato 'YYYY-MM-DD'.
end (str): Data final no formato 'YYYY-MM-DD'.
frequency (str): 'daily' ou 'monthly'. Define a frequência dos dados.
debug (bool): Se True, imprime mensagens adicionais para depuração.

Returns:
pd.DataFrame: DataFrame com estatísticas de precipitação (mm), com índice temporal.

------------------------------------------------------------------------

Extracts data from the CHIRPS Daily collection for a given region and time period.

Args:
roi (ee.Geometry): Region of interest (e.g., ee.Geometry.Polygon).
start (str): Start date in 'YYYY-MM-DD' format.
end (str): End date in 'YYYY-MM-DD' format.
frequency (str): 'daily' or 'monthly'. Defines the temporal frequency of the data.
debug (bool): If True, prints additional debug messages.

Returns:
pd.DataFrame: DataFrame with precipitation statistics (mm) indexed by time.

### `extract_daily(img):
            reducer = (ee.Reducer.mean()
                       .combine(ee.Reducer.median(), sharedInputs=True)
                       .combine(ee.Reducer.minMax(), sharedInputs=True)
                       .combine(ee.Reducer.stdDev(), sharedInputs=True))

            stats = img.reduceRegion(
                reducer=reducer,
                geometry=roi,
                scale=5000,
                maxPixels=1e9
            )

            return ee.Feature(None, {
                'date': img.date().format("YYYY-MM-dd"),
                'pr_mean': stats.get('precipitation_mean'),
                'pr_median': stats.get('precipitation_median'),
                'pr_max': stats.get('precipitation_max'),
                'pr_min': stats.get('precipitation_min'),
                'pr_stdDev': stats.get('precipitation_stdDev')
            })

        features = ee.FeatureCollection(chirps.map(extract_daily))

    # === Modo mensal ===
    else:
        years = list(range(int(start[:4]), int(end[:4]) + 1))
        dfs = []

        for year in tqdm(years, desc="Processando CHIRPS mensal"):
            try:
                year_chirps = chirps.filterDate(f"{year}-01-01", f"{year}-12-31")

                def annotate_month(img):
                    date = ee.Date(img.get("system:time_start"))
                    return img.set({
                        "year": date.get("year"),
                        "month": date.get("month"),
                        "year_month": date.format("YYYY-MM")
                    })

                year_chirps = year_chirps.map(annotate_month)
                months = year_chirps.aggregate_array("year_month").distinct()

                def reduce_month(month):
                    month_imgs = year_chirps.filter(ee.Filter.eq("year_month", month))
                    monthly_sum = month_imgs.sum().set("month", month)
                    return monthly_sum

                chirps_monthly_sum = ee.ImageCollection(months.map(reduce_month))

                def stats_month(img):
                    reducer = (ee.Reducer.mean()
                               .combine(ee.Reducer.median(), sharedInputs=True)
                               .combine(ee.Reducer.minMax(), sharedInputs=True)
                               .combine(ee.Reducer.stdDev(), sharedInputs=True))

                    stats = img.reduceRegion(
                        reducer=reducer,
                        geometry=roi,
                        scale=5000,
                        maxPixels=1e9
                    )

                    return ee.Feature(None, {
                        'date': img.get("month"),
                        'pr_mean': stats.get('precipitation_mean'),
                        'pr_median': stats.get('precipitation_median'),
                        'pr_max': stats.get('precipitation_max'),
                        'pr_min': stats.get('precipitation_min'),
                        'pr_stdDev': stats.get('precipitation_stdDev')
                    })

                features_year = chirps_monthly_sum.map(stats_month)
                df_year = geemap.ee_to_df(ee.FeatureCollection(features_year))
                dfs.append(df_year)

            except Exception as e:
                warnings.warn(f"[CHIRPS] Erro no ano {year}: {e}")

        features = pd.concat(dfs, ignore_index=True)

    # === Conversão final para DataFrame
    if isinstance(features, pd.DataFrame):
        df = features
    else:
        df = geemap.ee_to_df(features)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")

    df.attrs = {
        "units": "mm",
        "source": "CHIRPS Daily",
        "frequency": frequency
    }

    if debug:
        print("[DEBUG] Linhas retornadas:", len(df))
        print("[DEBUG] Colunas:", df.columns.tolist())
        print("[DEBUG] Período:", df.index.min(), "a", df.index.max())

    return df

import ee
import geemap
import numpy as np
import xarray as xr
import datetime
import os
import shutil
from pathlib import Path
from tqdm import tqdm
from contextlib import redirect_stdout
import io
import rioxarray as rxr
import geopandas as gpd
from geemap import ee_to_geojson
from geemap_tools.io import roi_to_file
import time

def extract_mapbiomas(roi, years=range(1985, 2023), include_srtm=True,
                      include_terrain=False, terrain_vars=("hillshade",),
                      comment=None, debug=False, scale=30)`

Extrai dados da Coleção 9 do MapBiomas para um ROI, com opção de incluir elevação
(SRTM) e variáveis derivadas do relevo (via ee.Terrain), exportando ano a ano e
retornando como um xarray.Dataset com metadados e coordenadas geográficas.

Args:
roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Região de interesse.
Pode ser uma geometria simples ou uma coleção de feições do Earth Engine.
years (iterable): Lista de anos a extrair do MapBiomas (padrão: 1985 a 2022).
include_srtm (bool): Se True, inclui a variável de elevação (SRTM), interpolada
para coincidir com a resolução e grade do MapBiomas.
include_terrain (bool): Se True, inclui variáveis topográficas derivadas de
elevação usando `ee.Terrain`.
terrain_vars (tuple of str): Conjunto de variáveis de relevo a incluir.
As opções válidas são:
- "elevation": altitude bruta (equivalente ao SRTM)
- "slope": declividade do terreno (graus)
- "aspect": orientação do declive (azimute em graus)
- "hillshade": sombreamento simulado baseado em iluminação solar
comment (str): Comentário opcional incluído nos metadados do dataset final.
debug (bool): Se True, imprime mensagens informativas durante o processo.
scale (int): Resolução espacial da exportação, em metros (padrão: 30 m).

Returns:
xr.Dataset: Conjunto de dados georreferenciados com dimensões (time, y, x),
contendo uma variável de uso da terra por ano e, se solicitado, camadas
adicionais de elevação e relevo.

------------------------------------------------------------------------

Extracts data from MapBiomas Collection 9 for a given ROI, with optional inclusion
of elevation (SRTM) and topographic variables (via ee.Terrain), exporting year-by-year
and returning the result as an `xarray.Dataset` with full geospatial metadata.

Args:
roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Region of interest.
Can be a simple geometry or a feature collection from Earth Engine.
years (iterable): List of years to extract from MapBiomas (default: 1985 to 2022).
include_srtm (bool): If True, includes interpolated SRTM elevation aligned to
MapBiomas resolution and grid.
include_terrain (bool): If True, adds terrain-derived variables using `ee.Terrain`.
terrain_vars (tuple of str): Set of terrain variables to include.
Valid options include:
- "elevation": raw elevation (equivalent to SRTM)
- "slope": terrain slope in degrees
- "aspect": slope aspect in degrees (azimuth)
- "hillshade": simulated hill shading based on sun position
comment (str): Optional string to be saved as a metadata comment.
debug (bool): If True, prints informative messages during processing.
scale (int): Spatial resolution in meters (default: 30 m).

Returns:
xr.Dataset: Georeferenced dataset with dimensions (time, y, x),
containing land use per year and, if requested, elevation and terrain layers.

## Module `catalog`

### `list_sat_images(collection_id, roi, max_imgs=500, compute_clear_sky=False, time_range=None)`

Lista imagens de uma coleção Earth Engine com metadados úteis e interseção com uma ROI.

Parâmetros:
collection_id (str): ID da coleção (ex: 'LANDSAT/LC08/C02/T1_L2', 'COPERNICUS/S2_SR').
roi (ee.Geometry): Geometria da área de interesse (obrigatória).
max_imgs (int): Máximo de imagens a processar (padrão: 500).
compute_clear_sky (bool): Se True, calcula percentual de céu claro com base na máscara de nuvem.
time_range (tuple): Par de strings com data inicial e final no formato 'YYYY-MM-DD'.

Retorno:
pd.DataFrame: Tabela com metadados das imagens e percentual da ROI coberto.

Erros:
ValueError: Se a ROI não for fornecida ou a coleção não for reconhecida.

----
List satellite images from an Earth Engine collection with useful metadata and intersection with a ROI.

Args:
collection_id (str): Collection ID (e.g., 'LANDSAT/LC08/C02/T1_L2', 'COPERNICUS/S2_SR').
roi (ee.Geometry): Geometry of the region of interest (required).
max_imgs (int): Maximum number of images to process (default: 500).
compute_clear_sky (bool): If True, computes clear sky percentage based on the cloud mask.
time_range (tuple): Pair of strings with start and end date in the 'YYYY-MM-DD' format.

Returns:
pd.DataFrame: Table with image metadata and percentage of ROI covered.

Raises:
ValueError: If ROI is not provided or the collection is not recognized.

## Module `clouds`

### `custom_mask_clouds(img, debug=False)`

Aplica uma máscara de nuvens personalizada a uma imagem do Earth Engine.

Suporta imagens com bandas QA_PIXEL (Landsat), SCL (Sentinel-2) ou MSK_CLDPRB (probabilidade de nuvem).
Para Sentinel-2, utiliza a banda SCL com fallback para MSK_CLDPRB caso a máscara esteja completamente vazia.

Parâmetros:
img (ee.Image): Imagem de entrada contendo bandas de qualidade relacionadas a nuvens.
debug (bool, opcional): Se True, imprime mensagens de depuração. Padrão é False.

Retorno:
ee.Image: Imagem com nuvens mascaradas (pixels de nuvem removidos).

----
Apply a custom cloud mask to an Earth Engine image.

Supports images with QA_PIXEL (Landsat), SCL (Sentinel-2), or MSK_CLDPRB (cloud probability) bands.
For Sentinel-2, uses the SCL band with fallback to MSK_CLDPRB if the mask is completely empty.

Args:
img (ee.Image): Input image containing cloud-related quality bands.
debug (bool, optional): If True, prints debug messages. Default is False.

Returns:
ee.Image: Image with clouds masked (cloud pixels removed).

### `get_clear_sky_percentage(img, roi, debug=False)`

Calcula a porcentagem de céu claro (sem nuvens) sobre uma ROI com base na máscara de nuvem da imagem.

Utiliza a função `custom_mask_clouds()` para aplicar a máscara apropriada à imagem.
A porcentagem é obtida a partir da média da máscara binária (1 = claro, 0 = nublado) sobre a ROI.

Parâmetros:
img (ee.Image): Imagem do Earth Engine com bandas de máscara de nuvem.
roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Região de interesse.
debug (bool, opcional): Se True, imprime mensagens de depuração. Padrão é False.

Retorno:
float | None: Porcentagem de pixels com céu claro (0 a 100), ou None se falhar.

----
Computes the percentage of clear sky (cloud-free) pixels over a ROI based on the image's cloud mask.

Uses the `custom_mask_clouds()` function to apply the appropriate mask to the image.
The percentage is calculated from the mean value of a binary mask (1 = clear, 0 = cloudy) over the ROI.

Args:
img (ee.Image): Earth Engine image with cloud mask bands.
roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Region of interest.
debug (bool, optional): If True, prints debug messages. Default is False.

Returns:
float | None: Percentage of cloud-free pixels (0 to 100), or None if it fails.

## Module `io`

### `roi_to_file(roi, filename, format='geojson', wrap_geometry=True)`

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

### `file_to_roi(filepath)`

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

## Module `sidra_tools`

### `get_sidra_cultura(cod_mun, cod_cultura, debug=False)`

Extrai dados da Tabela 5457 da SIDRA/IBGE sobre produção agrícola municipal.

Parâmetros:
cod_mun (str): Código do município no IBGE (ex: '3169406' para Três Pontas-MG).
cod_cultura (str): Código da cultura no IBGE (ex: '40139' para Café em grão).
debug (bool): Se True, imprime informações de progresso e diagnóstico.

Retorno:
pd.DataFrame: DataFrame com colunas:
- A.plantada (ha)
- A.colhida (ha)
- Q.colhida (kg)
- Rendimento (kg/ha)
O índice é uma série de anos no formato datetime.

----
Extracts data from SIDRA/IBGE Table 5457 on municipal agricultural production.

Args:
cod_mun (str): IBGE code of the municipality (e.g., '3169406' for Três Pontas-MG).
cod_cultura (str): IBGE code of the crop (e.g., '40139' for Coffee beans).
debug (bool): If True, prints progress and diagnostic information.

Returns:
pd.DataFrame: DataFrame with the following columns:
- A.plantada (ha)
- A.colhida (ha)
- Q.colhida (kg)
- Rendimento (kg/ha)
The index is a time series of years in datetime format.
