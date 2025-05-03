# Manual do geemap-tools

Este manual foi gerado automaticamente a partir das funções presentes no módulo `gee_utils.py`.

## Funções disponíveis

### `roi_to_file(roi, filename, format='geojson', wrap_geometry=True)`

Exporta uma ROI do GEE para GeoJSON ou Shapefile.

    Args:
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Objeto de entrada.
        filename (str): Nome base do arquivo de saída (sem extensão).
        format (str): 'geojson' ou 'shp'.
        wrap_geometry (bool): Se True, transforma ee.Geometry em ee.Feature.

    Returns:
        str: Caminho completo do arquivo gerado.

### `file_to_roi(filepath)`

Converte um arquivo shapefile, geojson, kml ou kmz em uma ee.FeatureCollection.

    Args:
        filepath (str): Caminho completo para o arquivo.

    Returns:
        ee.FeatureCollection: FeatureCollection correspondente.

### `custom_mask_clouds(img):
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


def list_sat_images(collection_id, roi, max_imgs=500, compute_clear_sky=False, time_range=None)`

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
