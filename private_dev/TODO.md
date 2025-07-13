## Arquivo TODO

Listagem de coisas que ainda quero implementar no `geemap_tools`:

#### 1. `extract_band_values_to_dataframe(image, bands, roi, scale=30, reducer='mean')`
**Descrição**: Extrai valores de bandas de uma imagem para uma ROI e retorna um DataFrame com os valores por banda.

**Parâmetros**:
- `image`: `ee.Image` com as bandas desejadas  
- `bands`: `list` com nomes das bandas a extrair  
- `roi`: `ee.Geometry` ou `ee.FeatureCollection`  
- `scale`: resolução da imagem (default = 30)  
- `reducer`: `'mean'`, `'median'`, `'min'`, `'max'`, `'stdDev'` ou combinação  

**Retorna**: `pd.DataFrame` com os valores por banda e estatísticas.


#### 2. `plot_band_histogram(df, band_column, title=None)`
**Descrição**: Gera um histograma da distribuição de valores de uma banda extraída.

**Parâmetros**:
- `df`: DataFrame com a banda extraída  
- `band_column`: nome da coluna (string)  
- `title`: título opcional  

#### 3. `plot_band_boxplot(df, bands=None)`
**Descrição**: Plota um boxplot comparativo entre bandas extraídas.

**Parâmetros**:
- `df`: DataFrame com colunas de bandas  
- `bands`: lista opcional de colunas a incluir  

#### 4. `convert_featurecollection_to_dataframe(fc, properties=None)`
**Descrição**: Extrai propriedades de um `ee.FeatureCollection` para um DataFrame, filtrando apenas colunas de interesse.

#### 5. `add_band_statistics(image, roi, bands, scale=30)`
**Descrição**: Calcula estatísticas simples para múltiplas bandas de uma imagem sobre a ROI (`mean`, `median`, `min`, `max`, `stdDev`), retornando um dicionário com os resultados.

### Sugestões experimentais

#### 6. `compare_bands_across_images(image_list, bands, roi, stat='mean')`
**Descrição**: Compara valores médios (ou outro estatístico) de uma banda ou conjunto de bandas em várias imagens sobre a mesma ROI.  
**Retorna**: `DataFrame` com linha por imagem.

#### 7. `sample_band_values_to_points(image, bands, roi_points, scale=30)`
**Descrição**: Amostra valores de bandas diretamente em pontos definidos (útil para treinamento de modelos de Machine Learning).
