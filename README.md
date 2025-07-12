# GEEMAP-TOOLS

`geemap-tools` é um pacote auxiliar para facilitar o uso do Google Earth Engine e da biblioteca `geemap`, com foco em pesquisadores, estudantes e profissionais que precisam de ferramentas práticas e reutilizáveis para análise de dados geoespaciais.

O projeto é mantido pelo **Observatório Oceanográfico da UFF**, e foi criado para simplificar tarefas recorrentes em notebooks de pesquisa, ensino e extensão.

Ele é baseado principalmente nas bibliotecas:
- [`geemap`](https://github.com/giswqs/geemap)
- [`eemont`](https://github.com/davemlz/eemont)
- [`earthengine-api`](https://developers.google.com/earth-engine/guides/python_install)

Funciona tanto no Google Colab quanto em ambientes locais com Jupyter Notebook ou Jupyter Lab.<br>
Verifique o diretório `exemplos` para as principais funcionalidades.

## Funcionalidades principais

Atualmente o `geemap-tools` inclui funções organizadas em submódulos:

- `io.py`: Entrada e saída de ROIs e arquivos.
- `clouds.py`: Máscara de nuvens e qualidade de imagem.
- `catalog.py`: Listagem de imagens por ROI, satélite e intervalo.
- `analysis.py`: Séries temporais por índice (NDVI, EVI...), CHIRPS, TerraClimate etc.
- `sidra_tools.py`: Acesso programático à Tabela 5457 (Produção Agrícola Municipal – IBGE).
- `dev/`: Área de desenvolvimento e testes – não será instalada como parte do pacote.

## Instalação Rápida

### Ambiente Local (Recomendado)

Se estiver usando Anaconda ou Miniconda, sugerimos criar um novo ambiente para instalação. Os pacotes abaixo são os básicos essenciais para usar o Google Earth Engine. Note que ao instalar o `geemap-tools` abaixo, o sistema irá se encarregar de instalar tudo que você precisa:

```bash
conda create -n geemap-tools python=3.11
conda activate geemap-tools
mamba install -c conda-forge geemap pandas geopandas eemont xarray rioxarray matplotlib openpyxl
git clone https://github.com/andrebelem/geemap-tools.git
cd geemap-tools
pip install -e .
```
#### E no COLAB ?

Se você está no Colab, basta instalar o `geemap-tools` na sua máquina virtual do colab que ele já vem com todas as dependências.
```
!pip install git+https://github.com/andrebelem/geemap-tools.git
```
**Atenção**: Alguns recursos de geemap podem não funcionar perfeitamente no Colab devido a limitações do ambiente (ex: Map.addLayer interativo). Dê preferência ao uso local com JupyterLab. Tenha sempre cautela com ROIs muito grandes ou operações que demandam memória pois o GEE pode bloquear seus requests.

#### Desenvolvimento

Este projeto agora utiliza `pyproject.toml` com suporte a `setuptools` moderno. O diretório private_dev/ não é incluído na instalação. Para uso local com hot reload:
```bash
pip install -e .
```

**Contato**<br>
Dúvidas, sugestões de melhorias ou novas funções?
Entre em contato: [andrebelem@id.uff.br](mailto:andrebelem@id.uff.br)

### Quer um assistente para usar esse repo ?

Acesse o DeepWiki do geemap-tools ! [https://deepwiki.com/andrebelem/geemap-tools](https://deepwiki.com/andrebelem/geemap-tools)

