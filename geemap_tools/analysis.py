# geemap_tools/gee_utils.py
import ee
import geemap
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

def describe_roi(roi, show_pixels_table=True, print_summary=True, pixel_res=None):
    """
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
    """
    import pandas as pd

    # Unifica em uma única geometria se necessário
    if isinstance(roi, ee.FeatureCollection):
        geom = roi.geometry()
    elif isinstance(roi, ee.Feature):
        geom = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        geom = roi
    else:
        raise TypeError("Tipo inválido. Use ee.Geometry, ee.Feature ou ee.FeatureCollection.")

    # Cálculo da área e perímetro
    area_m2 = geom.area(ee.ErrorMargin(1)).getInfo()
    perimeter_m = geom.perimeter(maxError=1).getInfo()

    area_km2 = area_m2 / 1e6
    perimeter_km = perimeter_m / 1000

    if print_summary:
        print(f"📐 Área total: {area_km2:,.2f} km²")
        print(f"📏 Perímetro total: {perimeter_km:,.2f} km")

    # Resoluções padrão ou personalizadas
    if pixel_res is None:
        resolutions = [10, 30, 60]
    elif isinstance(pixel_res, (int, float)):
        resolutions = [pixel_res]
    elif isinstance(pixel_res, (list, tuple)):
        resolutions = list(pixel_res)
    else:
        raise ValueError("pixel_res deve ser int, float ou lista de valores numéricos.")

    # Estima número de pixels por resolução
    pixels_dict = {
        f"{int(res)}m": int(round(area_m2 / (res**2)))
        for res in resolutions
    }

    df = None
    if show_pixels_table:
        df = pd.DataFrame({
            "Resolução (m)": resolutions,
            "Área de pixel (m²)": [res**2 for res in resolutions],
            "Nº estimado de pixels": list(pixels_dict.values())
        })
        display(df)

    return {
        "area_km2": area_km2,
        "perimetro_km": perimeter_km,
        "n_pixels": pixels_dict,
        "df": df if show_pixels_table else None
    }


def get_TerraClimate(
    roi,
    start="2000-01-01",
    end="2025-12-31",
    variables=None,
    stats=None,
    scale=4000,
    maxPixels=1e13,
    debug=False,
):
    """
    Extrai estatísticas mensais da coleção TerraClimate para uma ROI.

    Args:
        roi (ee.Geometry): Região de interesse.
        start (str): Data inicial no formato 'YYYY-MM-DD'.
        end (str): Data final no formato 'YYYY-MM-DD'.
        variables (list): Lista com variáveis desejadas.  
                          Opções válidas:
                          ['aet', 'def', 'pdsi', 'pet', 'pr', 'ro', 'soil',
                           'srad', 'swe', 'tmmx', 'tmmn', 'vap', 'vpd', 'vs'].
                          Default: ['pr', 'pet', 'srad', 'tmmx', 'tmmn'].
        stats (list): Estatísticas desejadas entre:
                      ['mean', 'median', 'min', 'max', 'stdDev'].
                      Default: todas.
        scale (int/float): Resolução em metros usada no reduceRegion.
        maxPixels (float): maxPixels do reduceRegion.
        debug (bool): Se True, imprime mensagens de depuração.

    Returns:
        pd.DataFrame: DataFrame com estatísticas mensais para cada variável
                      e cada estatística selecionada, com colunas do tipo
                      <variável>_<stat>, ex: pr_mean, tmmx_min, vs_stdDev.
    """

    # ----- Variáveis disponíveis no TerraClimate -----
    valid_vars = [
        'aet',  # Actual evapotranspiration
        'def',  # Climate water deficit
        'pdsi', # Palmer Drought Severity Index
        'pet',  # Reference evapotranspiration
        'pr',   # Precipitation
        'ro',   # Runoff
        'soil', # Soil moisture
        'srad', # Downward surface shortwave radiation
        'swe',  # Snow water equivalent
        'tmmx', # Maximum temperature
        'tmmn', # Minimum temperature
        'vap',  # Vapor pressure
        'vpd',  # Vapor pressure deficit
        'vs'    # Wind-speed at 10 m
    ]

    # Fatores de escala (Data Catalog: coluna "Scale")
    # Valor_final = valor_bruto * scale_factor[var]
    scale_factor = {
        'aet': 0.1,
        'def': 0.1,
        'pdsi': 0.01,
        'pet': 0.1,
        'pr': 0.1,
        'ro': 0.1,
        'soil': 0.1,
        'srad': 0.1,
        'swe': 0.1,
        'tmmx': 0.1,
        'tmmn': 0.1,
        'vap': 0.001,
        'vpd': 0.01,
        'vs': 0.01,
    }

    # Defaults de variáveis e estatísticas
    if variables is None:
        variables = ['pr', 'pet', 'srad', 'tmmx', 'tmmn']

    valid_stats = ['mean', 'median', 'min', 'max', 'stdDev']
    if stats is None:
        stats = valid_stats.copy()

    # Validação de variáveis e stats
    vars_selected = [v for v in variables if v in valid_vars]
    if len(vars_selected) == 0:
        raise ValueError(
            f"Nenhuma variável válida selecionada. Use alguma das seguintes: {valid_vars}"
        )

    stats_selected = [s for s in stats if s in valid_stats]
    if len(stats_selected) == 0:
        raise ValueError(
            f"Nenhuma estatística válida selecionada. Use alguma das seguintes: {valid_stats}"
        )

    # ----- Carrega coleção filtrada por ROI e datas -----
    terra = (
        ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")
        .select(vars_selected)
        .filterBounds(roi)
        .filterDate(start, end)
    )

    n_img = terra.size().getInfo()
    if n_img == 0:
        raise ValueError("Nenhuma imagem TerraClimate disponível para esse período/ROI.")

    # ----- Monta o redutor conforme as estatísticas solicitadas -----
    reducer = None

    if 'mean' in stats_selected:
        reducer = ee.Reducer.mean()

    if 'median' in stats_selected:
        reducer = reducer.combine(ee.Reducer.median(), sharedInputs=True) if reducer \
            else ee.Reducer.median()

    if 'min' in stats_selected or 'max' in stats_selected:
        reducer = reducer.combine(ee.Reducer.minMax(), sharedInputs=True) if reducer \
            else ee.Reducer.minMax()

    if 'stdDev' in stats_selected:
        reducer = reducer.combine(ee.Reducer.stdDev(), sharedInputs=True) if reducer \
            else ee.Reducer.stdDev()

    # ----- Função para extrair estatísticas por imagem (mensal) -----
    def stats_by_month(img):
        stats_dict = img.reduceRegion(
            reducer=reducer,
            geometry=roi,
            scale=scale,
            maxPixels=maxPixels
        )

        result = {'date': img.date().format("YYYY-MM")}

        for var in vars_selected:
            for stat in stats_selected:
                if stat in ['mean', 'median', 'stdDev']:
                    key = f"{var}_{stat}"
                elif stat == 'min':
                    key = f"{var}_min"
                elif stat == 'max':
                    key = f"{var}_max"
                else:
                    continue
                result[key] = stats_dict.get(key)

        return ee.Feature(None, result)

    # Aplica a função em toda a coleção mensal
    features = ee.FeatureCollection(terra.map(stats_by_month))

    # ----- Converte para DataFrame -----
    df = geemap.ee_to_df(features)

    # Converte coluna de data e ordena
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')

    # Trata None como NaN e tenta converter numéricos
    df = df.replace({None: pd.NA})
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    # ----- Aplica fatores de escala do TerraClimate -----
    for var in vars_selected:
        sf = scale_factor.get(var, 1.0)
        for stat in stats_selected:
            if stat in ['mean', 'median', 'stdDev']:
                col = f"{var}_{stat}"
            elif stat in ['min', 'max']:
                col = f"{var}_{stat}"
            else:
                continue

            if col in df.columns and sf != 1.0:
                df[col] = df[col] * sf

    # ----- Atributos de unidades -----
    units = {
        "aet": "mm",
        "def": "mm",
        "pdsi": "índice (adimensional)",
        "pet": "mm",
        "pr": "mm",
        "ro": "mm",
        "soil": "mm",
        "srad": "W/m^2",
        "swe": "mm",
        "tmmx": "°C",
        "tmmn": "°C",
        "vap": "kPa",
        "vpd": "kPa",
        "vs": "m/s"
    }
    df.attrs = {f"{v}_unit": units[v] for v in vars_selected}

    if debug:
        print(f"[DEBUG] Imagens na coleção: {n_img}")
        print(f"[DEBUG] Variáveis selecionadas: {vars_selected}")
        print(f"[DEBUG] Estatísticas selecionadas: {stats_selected}")
        print(f"[DEBUG] Linhas retornadas: {len(df)}")
        print(f"[DEBUG] Colunas: {list(df.columns)}")

    return df

#def get_TerraClimate(roi, start="2000-01-01", end="2025-12-31",
#                     variables=["pr", "pet","srad","tmmx","tmmn"],
#                     debug=False):
#    """
#    Extrai estatísticas mensais da coleção TerraClimate para uma ROI.
#
#    Args:
#        roi (ee.Geometry): Região de interesse.
#        start (str): Data inicial no formato 'YYYY-MM-DD'.
#        end (str): Data final no formato 'YYYY-MM-DD'.
#        variables (list): Lista com variáveis desejadas.  
#                          Opções válidas:
#                          ['aet', 'def', 'pdsi', 'pet', 'pr', 'q', 'soil',
#                           'swe', 'tmmx', 'tmmn', 'vap', 'vpd', 'vs']
#        debug (bool): Se True, imprime mensagens de depuração.
#
#    Returns:
#        pd.DataFrame: DataFrame com estatísticas mensais para cada variável selecionada.
#                      Cada variável terá colunas com os sufixos:
#                      _mean, _median, _max, _min, _stdDev.
#
#    ------------------------------------------------------------------------
#
#    Extracts monthly statistics from the TerraClimate collection for a given ROI.
#
#    Args:
#        roi (ee.Geometry): Region of interest.
#        start (str): Start date in 'YYYY-MM-DD' format.
#        end (str): End date in 'YYYY-MM-DD' format.
#        variables (list): List of desired variables.  
#                          Valid options:
#                          ['aet', 'def', 'pdsi', 'pet', 'pr', 'soil',
#                           'srad','swe', 'tmmx', 'tmmn', 'vap', 'vpd', 'vs']
#        debug (bool): If True, prints debug messages.
#
#    Returns:
#        pd.DataFrame: DataFrame with monthly statistics for each selected variable.
#                      Each variable will have columns with the suffixes:
#                      _mean, _median, _max, _min, _stdDev.
#    """
#
#    # Lista completa de variáveis disponíveis no TerraClimate
#    valid_vars = [
#        'aet',  # Evapotranspiração real
#        'def',  # Déficit hídrico
#        'pdsi', # Índice de seca de Palmer
#        'pet',  # Evapotranspiração potencial
#        'pr',   # Precipitação
#        'soil', # Umidade do solo
#        'srad', # Radiação de ondas curtas da superfície para baixo
#        'swe',  # Equivalente em água da neve
#        'tmmx', # Temperatura máxima
#        'tmmn', # Temperatura mínima
#        'vap',  # Pressão de vapor
#        'vpd',  # Déficit de pressão de vapor
#        'vs'    # Velocidade do vento
#    ]
#
#    vars_selected = [v for v in variables if v in valid_vars]
#    if len(vars_selected) == 0:
#        raise ValueError(f"Nenhuma variável válida selecionada. Use alguma das seguintes: {valid_vars}")
#
#    # Carrega a coleção filtrada por ROI e datas
#    terra = (
#        ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")
#        .select(vars_selected)
#        .filterBounds(roi)
#        .filterDate(start, end)
#    )
#
#    # Redutor composto
#    reducer = (
#        ee.Reducer.mean()
#        .combine(ee.Reducer.median(), sharedInputs=True)
#        .combine(ee.Reducer.minMax(), sharedInputs=True)
#        .combine(ee.Reducer.stdDev(), sharedInputs=True)
#    )
#
#    # Função para extrair estatísticas por imagem mensal
#    def stats_by_month(img):
#        stats = img.reduceRegion(
#            reducer=reducer,
#            geometry=roi,
#            scale=4000,
#            maxPixels=1e9
#        )
#
#        result = {'date': img.date().format("YYYY-MM")}
#        for var in vars_selected:
#            for stat in ['mean', 'median', 'max', 'min', 'stdDev']:
#                result[f"{var}_{stat}"] = stats.get(f"{var}_{stat}")
#        return ee.Feature(None, result)
#
#    # Aplica a função
#    features = ee.FeatureCollection(terra.map(stats_by_month))
#
#    # Converte para DataFrame
#    df = geemap.ee_to_df(features)
#    df['date'] = pd.to_datetime(df['date'])
#    df = df.sort_values('date').set_index('date')
#
#    # Ajusta temperaturas (de décimos de grau para °C)
#    for tvar in ['tmmx', 'tmmn']:
#        if tvar in vars_selected:
#            for stat in ['mean', 'median', 'max', 'min', 'stdDev']:
#                col = f"{tvar}_{stat}"
#                if col in df.columns:
#                    df[col] = df[col] / 10.0
#
#    # Define atributos com unidades
#    units = {
#        "aet": "mm",
#        "def": "mm",
#        "pdsi": "índice (adimensional)",
#        "pet": "mm",
#        "pr": "mm",
#        "srad": "W/m^2",
#        "soil": "mm",
#        "swe": "mm",
#        "tmmx": "°C",
#        "tmmn": "°C",
#        "vap": "kPa",
#        "vpd": "kPa",
#        "vs": "m/s"
#    }
#    df.attrs = {f"{v}_unit": units[v] for v in vars_selected}
#
#    if debug:
#        print(f"[DEBUG] Variáveis selecionadas: {vars_selected}")
#        print(f"[DEBUG] Linhas retornadas: {len(df)}")
#        print(f"[DEBUG] Colunas: {list(df.columns)}")
#
#    return df

import ee
import pandas as pd
import warnings
from tqdm import tqdm
import geemap

def get_CHIRPS(roi, start="2000-01-01", end="2025-12-31", frequency="monthly", debug=False):
    """
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
    """
    # === Validação da frequência ===
    frequency = frequency.lower()
    if frequency not in ["daily", "monthly"]:
        raise ValueError("frequency deve ser 'daily' ou 'monthly'.")

    # === Carrega coleção ===
    chirps = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
              .filterBounds(roi)
              .filterDate(start, end)
              .select("precipitation"))

    # === Modo diário ===
    if frequency == "daily":
        count = chirps.size().getInfo()
        if count > 2000:
            warnings.warn(f"Atenção: {count} imagens diárias encontradas. Isso pode levar a uma execução demorada.")

        def extract_daily(img):
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
                      comment=None, debug=False, scale=30):
    """
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
    """
    if isinstance(roi, ee.FeatureCollection) or isinstance(roi, ee.Feature):
        roi = roi.geometry()

    bounds = roi.bounds().getInfo()
    if not bounds or "coordinates" not in bounds:
        raise ValueError("A geometria do ROI é inválida ou vazia.")
       
    base_image = ee.Image("projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1")

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_dir = Path(f"temp_{timestamp}")
    temp_dir.mkdir(exist_ok=True)

    # === ROI to GeoJSON ===
    roi_geojson_path = temp_dir / "roi.geojson"
    roi_to_file(roi, roi_geojson_path, format="geojson")
    gdf = gpd.read_file(roi_geojson_path)
    
    temp_paths = []
    da_list = []
    if debug:
        tqdm.write("📦 Exportando bandas ano a ano:")
        
    # Verifica os anos disponíveis na imagem base
    available_bands = base_image.bandNames().getInfo()
    available_years = [
        int(band.split("_")[1]) for band in available_bands if band.startswith("classification_")
    ]
    valid_years = [year for year in years if year in available_years]
    
    # Aviso se houver anos inválidos
    invalid_years = set(years) - set(valid_years)
    if invalid_years:
        tqdm.write(f"⚠️ Aviso: Os seguintes anos não estão disponíveis e serão ignorados: {sorted(invalid_years)}")
    
    for year in tqdm(valid_years, desc="Exportando bandas ano a ano"):
        band = f"classification_{year}"
        band_name = f"mapbiomas_{year}"
        mask = ee.Image.constant(1).clip(roi).selfMask()
        image = base_image.select(band).rename(band_name).updateMask(mask)
        temp_tif = temp_dir / f"{band_name}.tif"
        temp_paths.append(temp_tif)

        f = io.StringIO()
        with redirect_stdout(f):
            geemap.ee_export_image(
                image,
                filename=str(temp_tif),
                region=roi,
                scale=scale,
                file_per_band=False
            )

        with rxr.open_rasterio(temp_tif, masked=True, cache=False) as da:
            da = da.squeeze("band", drop=True)
            da.name = "mapbiomas_class"
            da = da.expand_dims(time=[np.datetime64(f"{year}-01-01")])
            da = da.rio.clip(gdf.geometry, gdf.crs, drop=True)
            da_list.append(da)

    stacked = xr.concat(da_list, dim="time")
    ds = stacked.to_dataset(name="mapbiomas_class")

    if include_srtm:
        if debug:
            tqdm.write("🗻 Incluindo SRTM...")

        srtm = ee.Image("USGS/SRTMGL1_003").rename("srtm_elevation")
        temp_srtm = temp_dir / "srtm.tif"

        f = io.StringIO()
        with redirect_stdout(f):
            geemap.ee_export_image(
                srtm,
                filename=str(temp_srtm),
                region=roi.bounds(),
                scale=scale,
                file_per_band=False
            )

        with rxr.open_rasterio(temp_srtm, masked=True, cache=False) as da_srtm:
            da_srtm = da_srtm.squeeze("band", drop=True)
            da_srtm = da_srtm.rio.clip(gdf.geometry, gdf.crs, drop=True)
            da_srtm_interp = da_srtm.interp_like(stacked)
            ds["srtm_elevation"] = da_srtm_interp

    if include_terrain:
        terrain = ee.Terrain.products(ee.Image("USGS/SRTMGL1_003"))
        for var in terrain_vars:
            if debug:
                tqdm.write(f"⛰️  Incluindo Terrain: {var}...")
            try:
                terrain_img = terrain.select(var)
                temp_terrain = temp_dir / f"terrain_{var}.tif"

                f = io.StringIO()
                with redirect_stdout(f):
                    geemap.ee_export_image(
                        terrain_img,
                        filename=str(temp_terrain),
                        region=roi.bounds(),
                        scale=scale,
                        file_per_band=False
                    )

                with rxr.open_rasterio(temp_terrain, masked=True, cache=False) as da_terrain:
                    da_terrain = da_terrain.squeeze("band", drop=True)
                    da_terrain = da_terrain.rio.clip(gdf.geometry, gdf.crs, drop=True)
                    da_terrain_interp = da_terrain.interp_like(stacked)
                    ds[var] = da_terrain_interp
            except Exception as e:
                tqdm.write(f"⚠️ Falha ao incluir {var}: {e}")

    ds.attrs["title"] = "MapBiomas Collection 9" + (" + SRTM" if include_srtm else "")
    ds.attrs["created"] = str(datetime.datetime.now())
    ds.attrs["scale"] = f"{scale} m"
    ds.attrs["source"] = "https://mapbiomas.org"
    ds.attrs["comment"] = comment if comment else ""

    class_legend = {
        1: 'Floresta', 3: 'Formação Florestal', 4: 'Formação Savânica',
        11: 'Campo Alagado', 12: 'Formação Campestre', 15: 'Pastagem',
        18: 'Agricultura', 21: 'Área não Vegetada', 23: 'Praia e Duna',
        24: 'Área Urbanizada', 25: 'Mineração', 29: 'Afloramento Rochoso',
        33: 'Apicum', 39: 'Aquicultura', 41: 'Silvicultura', 49: 'Soja',
        50: 'Milho', 62: 'Cana', 64: 'Arroz', 66: 'Algodão',
        67: 'Outras Lavouras Temporárias', 68: 'Café', 69: 'Citrus',
        70: 'Outras Lavouras Perenes', 72: 'Mosaico Agricultura + Pastagem',
        80: 'Reflorestamento com Espécie Nativa', 90: 'Infraestrutura', 95: 'Outros'
    }
    ds.attrs['mapbiomas_classes'] = str(class_legend)

    if debug:
        tqdm.write("✅ Dataset final criado com sucesso.")

    # Tentativa segura com espera
    for _ in range(5):
        try:
            shutil.rmtree(temp_dir)
            if debug:
                tqdm.write(f"🧹 Diretório temporário {temp_dir} removido.")
            break
        except PermissionError as e:
            tqdm.write(f"⏳ Aguardando liberação do diretório ({e})...")
            time.sleep(1)
    else:
        tqdm.write(f"⚠️ Não foi possível remover o diretório {temp_dir} após múltiplas tentativas.")

    return ds
