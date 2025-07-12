# 📘 Manual do geemap-tools

Este manual foi gerado automaticamente a partir das funções públicas presentes nos submódulos de `geemap_tools`.

## 📂 Módulo `analysis`

### `index_to_timeseries(df, roi, index_name, scale, debug)`

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

### `describe_roi(roi, show_pixels_table, print_summary, pixel_res)`

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

### `get_TerraClimate(roi, start, end, variables, debug)`

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

### `get_CHIRPS(roi, start, end, frequency, debug)`

Extrai dados da coleção CHIRPS Daily para uma região e período definidos.

Args:
    roi (ee.Geometry): Região de interesse (ex: ee.Geometry.Polygon).
    start (str): Data inicial no formato 'YYYY-MM-DD'.
    end (str): Data final no formato 'YYYY-MM-DD'.
    frequency (str): 'daily' ou 'monthly'. Define a frequência dos dados.
    debug (bool): Se True, imprime mensagens adicionais para depuração.

Returns:
    pd.DataFrame: DataFrame com estatísticas de precipitação (mm), com índice temporal.

## 📂 Módulo `catalog`

### `list_sat_images(collection_id, roi, max_imgs, compute_clear_sky, time_range)`

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

## 📂 Módulo `clouds`

### `custom_mask_clouds(img, debug)`

Aplica uma máscara de nuvens personalizada a uma imagem do Earth Engine.

Suporta imagens com bandas QA_PIXEL (Landsat), SCL (Sentinel-2) ou MSK_CLDPRB (probabilidade de nuvem).
Para Sentinel-2, utiliza a banda SCL com fallback para MSK_CLDPRB caso a máscara esteja completamente vazia.

Args:
    img (ee.Image): Imagem de entrada contendo bandas de qualidade relacionadas a nuvens.
    debug (bool, optional): Se True, imprime mensagens de depuração. Padrão é False.

Returns:
    ee.Image: Imagem com nuvens mascaradas (pixels de nuvem removidos).

### `get_clear_sky_percentage(img, roi, debug)`

Calcula a porcentagem de céu claro (sem nuvens) sobre uma ROI com base na máscara de nuvem da imagem.

Utiliza a função `custom_mask_clouds()` para aplicar a máscara apropriada à imagem.
A porcentagem é obtida a partir da média da máscara binária (1 = claro, 0 = nublado) sobre a ROI.

Args:
    img (ee.Image): Imagem do Earth Engine com bandas de máscara de nuvem.
    roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Região de interesse.
    debug (bool, optional): Se True, imprime mensagens de depuração. Padrão é False.

Returns:
    float | None: Porcentagem de pixels com céu claro (0 a 100), ou None se falhar.

## 📂 Módulo `io`

### `roi_to_file(roi, filename, format, wrap_geometry)`

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

### `file_to_roi(filepath)`

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

## 📂 Módulo `sidra_tools`

### `get_sidra_cultura(cod_mun, cod_cultura, debug)`

Extrai dados da Tabela 5457 da SIDRA/IBGE sobre produção agrícola municipal.

Args:
    cod_mun (str): Código do município no IBGE (ex: '3169406' para Três Pontas-MG).
    cod_cultura (str): Código da cultura no IBGE (ex: '40139' para Café em grão).
    debug (bool): Se True, imprime informações de progresso e diagnóstico.

Returns:
    pd.DataFrame: DataFrame com colunas:
        - A.plantada (ha)
        - A.colhida (ha)
        - Q.colhida (kg)
        - Rendimento (kg/ha)
    O índice é uma série de anos no formato datetime.
