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


def get_TerraClimate(roi, start="2000-01-01", end="2025-12-31",
                     variables=["pr", "pet", "tmmx", "tmmn"],
                     debug=False):
    """
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
    """

    # Lista completa de variáveis disponíveis no TerraClimate
    valid_vars = [
        'aet',  # Evapotranspiração real
        'def',  # Déficit hídrico
        'pdsi', # Índice de seca de Palmer
        'pet',  # Evapotranspiração potencial
        'pr',   # Precipitação
        'q',    # Vazão superficial
        'soil', # Umidade do solo
        'swe',  # Equivalente em água da neve
        'tmmx', # Temperatura máxima
        'tmmn', # Temperatura mínima
        'vap',  # Pressão de vapor
        'vpd',  # Déficit de pressão de vapor
        'ws'    # Velocidade do vento
    ]

    vars_selected = [v for v in variables if v in valid_vars]
    if len(vars_selected) == 0:
        raise ValueError(f"Nenhuma variável válida selecionada. Use alguma das seguintes: {valid_vars}")

    # Carrega a coleção filtrada por ROI e datas
    terra = (
        ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")
        .select(vars_selected)
        .filterBounds(roi)
        .filterDate(start, end)
    )

    # Redutor composto
    reducer = (
        ee.Reducer.mean()
        .combine(ee.Reducer.median(), sharedInputs=True)
        .combine(ee.Reducer.minMax(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True)
    )

    # Função para extrair estatísticas por imagem mensal
    def stats_by_month(img):
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


