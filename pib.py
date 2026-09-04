import sidrapy
import pandas as pd
import sqlite3
import requests
import os

def extrair_e_salvar_dados():
    nome_banco = "pib_regional.db"
    conn = sqlite3.connect(nome_banco)

    # =========================================================================
    # 1. EXTRAÇÃO DO IPCA (VIA BCB - SÉRIE 13522: ACUMULADO EM 12 MESES)
    # =========================================================================
    print("1. A procurar IPCA acumulado em 12 meses via Banco Central (SGS)...")
    url_bcb = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados?formato=json"

    try:
        resposta = requests.get(url_bcb, timeout=15)
        if resposta.status_code == 200:
            df_ipca = pd.DataFrame(resposta.json())
            df_ipca['data'] = pd.to_datetime(df_ipca['data'], format='%d/%m/%Y')
            df_ipca['valor'] = pd.to_numeric(df_ipca['valor'])

            # Em dezembro, a série 13522 corresponde à inflação acumulada no
            # ano. A divisão por 100 armazena a taxa em forma decimal.
            df_anual = df_ipca[df_ipca['data'].dt.month == 12].copy()
            df_anual['ano'] = df_anual['data'].dt.year
            df_ipca_final = df_anual[
                (df_anual['ano'] >= 2013) & (df_anual['ano'] <= 2023)
            ][['ano', 'valor']].copy()
            df_ipca_final['ipca_anual'] = df_ipca_final['valor'] / 100
            df_ipca_final = df_ipca_final[['ano', 'ipca_anual']].reset_index(drop=True)

            anos_esperados = set(range(2013, 2024))
            anos_ausentes = sorted(
                anos_esperados - set(df_ipca_final['ano'].astype(int))
            )
            if anos_ausentes:
                raise ValueError(
                    f"Série do IPCA incompleta. Anos ausentes: {anos_ausentes}"
                )

            # Salva na base de dados
            df_ipca_final.to_sql("indice_ipca", conn, if_exists='replace', index=False)
            print(f"✅ IPCA anual salvo! ({len(df_ipca_final)} anos)")
        else:
            print(f"❌ Erro API BCB: HTTP {resposta.status_code}")
    except Exception as e:
        print(f"❌ Falha na conexão com o Banco Central: {e}")


    # =========================================================================
    # 2. EXTRAÇÃO DO PIB NOMINAL (IBGE)
    # =========================================================================
    print("\n2. A iniciar extração de dados do PIB nominal pelo IBGE...")
    try:
        df_raw = sidrapy.get_table(
            table_code="5938",
            territorial_level="6",
            ibge_territorial_code="in n2 1,5",
            variable="37",
            period="all"
        )

        # Limpeza do cabeçalho
        primeira_celula = str(df_raw.iloc[0, 4])
        if primeira_celula in ['V', 'Valor', '37']:
            df_raw = df_raw.iloc[1:]

        df_pib = df_raw.iloc[:, [4, 5, 6, 8]].copy()
        df_pib.columns = ['pib_nominal', 'cod_ibge', 'municipio', 'ano']

        # Converte para numérico e multiplica por 1000 para obter o valor absoluto
        df_pib['pib_nominal'] = pd.to_numeric(df_pib['pib_nominal'], errors='coerce') * 1000
        df_pib['ano'] = pd.to_numeric(df_pib['ano'], errors='coerce')

        # Aplica os filtros de tempo e remove Brasília (5300108)
        df_pib = df_pib[(df_pib['ano'] >= 2013) & (df_pib['cod_ibge'].astype(str) != '5300108')].dropna()

        # Salva puramente nominal, conforme solicitado
        df_pib.to_sql("pib_municipios", conn, if_exists='replace', index=False)
        print(f"✅ PIB Nominal extraído e salvo! Total de registros: {len(df_pib)}")
    except Exception as e:
        print(f"❌ Erro ao extrair PIB do IBGE: {e}")


    # =========================================================================
    # 3. EXTRAÇÃO DO CRÉDITO RURAL NOMINAL
    # =========================================================================
    print("\n3. A integrar base de Crédito Rural (SICOR/MDCR)...")

    # Nome do arquivo CSV que você baixará do Banco Central
    arquivo_credito = "credito_rural_bruto.csv"

    if os.path.exists(arquivo_credito):
        try:
            # Lê a base bruta, garantindo que o separador e o encoding estejam corretos
            df_cred = pd.read_csv(arquivo_credito, sep=';', encoding='utf-8')

            # Limpeza básica e padronização (ajuste os nomes das colunas conforme seu CSV)
            # Espera-se que o CSV tenha as colunas: 'cod_ibge', 'ano', 'valor_credito_nominal'
            df_cred['ano'] = pd.to_numeric(df_cred['ano'], errors='coerce')
            df_cred['valor_credito_nominal'] = pd.to_numeric(df_cred['valor_credito_nominal'], errors='coerce')

            # Filtra NAs e restringe ao período da pesquisa (2013-2023)
            df_cred = df_cred[(df_cred['ano'] >= 2013) & (df_cred['ano'] <= 2023)].dropna(subset=['cod_ibge'])

            # Salva no banco de dados regional
            df_cred.to_sql("credito_municipal", conn, if_exists='replace', index=False)
            print(f"✅ Tabela de Crédito Rural Nominal salva com sucesso! ({len(df_cred)} registros)")
        except Exception as e:
            print(f"❌ Erro ao processar o arquivo de crédito rural: {e}")
    else:
        print(f"⚠️ O arquivo '{arquivo_credito}' não foi encontrado na pasta.")
        print("   -> Por favor, baixe o CSV consolidado do MDCR e coloque-o neste diretório.")

    conn.close()

    # =========================================================================
    # 4. RELATÓRIO DE VERIFICAÇÃO
    # =========================================================================
    print("\n" + "="*25)
    print("RELATÓRIO PÓS-EXTRAÇÃO")
    print("="*25)

    try:
        conn_report = sqlite3.connect(nome_banco)
        tabelas = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn_report)
        print(f"Tabelas presentes no banco '{nome_banco}': {tabelas['name'].tolist()}\n")

        for tabela in tabelas['name']:
            print(f"--- AMOSTRA DA TABELA: {tabela} ---")
            print(pd.read_sql_query(f"SELECT * FROM {tabela} LIMIT 3", conn_report))
            print("-" * 50 + "\n")
        conn_report.close()
    except Exception as e:
        print(f"Erro ao gerar o relatório final: {e}")

if __name__ == "__main__":
    extrair_e_salvar_dados()
