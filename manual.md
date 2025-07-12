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

*Sem descrição*

### `get_clear_sky_percentage(img, roi, debug)`

Calcula a porcentagem de céu claro sobre uma ROI com base na máscara de nuvem.

## 📂 Módulo `io`

### `roi_to_file(roi, filename, format, wrap_geometry)`

*Sem descrição*

### `file_to_roi(filepath)`

*Sem descrição*

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
