# GEEMAP-TOOLS

`geemap-tools` é um conjunto de rotinas desenvolvidas para facilitar o uso do Google Earth Engine e do `geemap`, especialmente para usuários básicos de SIG (GIS) que preferem não se aprofundar muito na programação em Python.

O pacote é usado no dia a dia do Observatório Oceanográfico da Universidade Federal Fluminense (UFF), e foi criado para tornar o acesso a funções práticas mais simples e rápido.

Ele é baseado principalmente nas bibliotecas:
- [`geemap`](https://github.com/giswqs/geemap)
- [`eemont`](https://github.com/davemlz/eemont)
- [`earthengine-api`](https://developers.google.com/earth-engine/guides/python_install)

Funciona tanto no Google Colab quanto em ambientes locais com Jupyter Notebook ou Jupyter Lab.<br>
Verifique o diretório `exemplos` para as principais funcionalidades.

## Instalação Rápida

### Ambiente Local (Recomendado)

Se estiver usando Anaconda ou Miniconda, sugerimos criar um novo ambiente para instalação. Os pacotes abaixo são os básicos essenciais para usar o Google Earth Engine. Note que ao instalar o `geemap-tools` abaixo, o sistema irá se encarregar de instalar tudo que você precisa:

```bash
conda create -n MyGIS python=3.11
conda activate MyGIS
conda install -c conda-forge mamba
mamba install -c conda-forge geemap pygis eemont pandas geopandas
```
Não esqueça de instalar o Jupyter caso você não tenha instalado. Eu prefiro o jupyter lab.
```
conda install notebook
conda install jupyterlab
```
#### E no COLAB ?

Se você está no Colab, basta instalar o `geemap-tools` na sua máquina virtual do colab que ele já vem com todas as dependências.
```
!pip install git+https://github.com/andrebelem/geemap-tools.git
```
**Atenção**: Alguns recursos de geemap podem não funcionar perfeitamente no Colab devido a limitações do ambiente, e tenha sempre cautela com ROIs muito grandes ou operações que demandam memória pois o GEE pode bloquear seus requests.

**Contato**<br>
Dúvidas, sugestões de melhorias ou novas funções?
Entre em contato: [andrebelem@id.uff.br](mailto:andrebelem@id.uff.br)

### Quer um assistente para usar esse repo ?

Acesse o DeepWiki do geemap-tools ! [https://deepwiki.com/andrebelem/geemap-tools](https://deepwiki.com/andrebelem/geemap-tools)

