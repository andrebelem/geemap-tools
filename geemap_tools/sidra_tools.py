import pandas as pd
import requests
import warnings
from io import BytesIO
import urllib3

# Suprime avisos de certificado não verificado da SIDRA
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_sidra_cultura(cod_mun, cod_cultura, debug=False):
    """
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
    """

    if not cod_mun or not cod_cultura:
        raise ValueError("Você deve fornecer os códigos de município (cod_mun) e cultura (cod_cultura).")

    # Variáveis da Tabela 5457
    vars = ['8331', '216', '214', '112']
    vars_names = ['A.plantada', 'A.colhida', 'Q.colhida', 'Rendimento']

    data = pd.DataFrame()

    for ii, var in enumerate(vars):
        url = (
            f"https://sidra.ibge.gov.br/geratabela?format=xlsx&name=tabela5457.xlsx"
            f"&terr=N&rank=-&query=t/5457/n6/{cod_mun}/v/{var}/p/all/c782/{cod_cultura}/l/c782%2Bt,,p%2Bv"
        )

        if debug:
            print(f"[DEBUG] Baixando variável {vars_names[ii]} de {url}")

        try:
            r = requests.get(url, verify=False)
            df_raw = pd.read_excel(BytesIO(r.content), skiprows=4, header=None)
        except Exception as e:
            raise RuntimeError(f"Erro ao baixar ou ler o Excel da SIDRA: {e}")

        if df_raw.empty or df_raw.shape[1] < 3:
            raise ValueError("Arquivo retornado pela SIDRA parece inválido ou sem dados.")

        if ii == 0:
            data['Ano'] = df_raw.iloc[:, 0]

        data[vars_names[ii]] = df_raw.iloc[:, 2]

    # Limpa última linha se for rodapé
    data = data.iloc[:-1, :]

    # Conversões e formatações
    data = data.apply(pd.to_numeric, errors='coerce')
    data["Ano"] = pd.to_datetime(data["Ano"], format="%Y")
    data = data.set_index("Ano")

    # Avisos baseados na documentação da Tabela 5457
    if data["A.plantada"].isna().all():
        warnings.warn("A variável 'Área plantada' só é informada a partir de 1988.")

    if int(cod_cultura) in [40139, 40140] and data.index.min().year < 2002:
        warnings.warn("⚠️ Café passou a ser informado como grão/beneficiado apenas a partir de 2002.")

    # Atributos do DataFrame
    data.attrs = {
        "A.plantada": "ha",
        "A.colhida": "ha",
        "Q.colhida": "kg",
        "Rendimento": "kg/ha",
        "fonte": "IBGE - SIDRA (Tabela 5457)",
        "código_município": cod_mun,
        "código_cultura": cod_cultura,
    }

    if debug:
        print(f"[DEBUG] Dados extraídos com sucesso:")
        print(data.head())
        print(f"[DEBUG] Unidades: {data.attrs}")

    return data
