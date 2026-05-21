import requests
import pandas as pd

def sonda_2022_bruta():
    print("--- SONDA DE DADOS: ANO 2022 (Pós-Mudança PCASP) ---")
    id_ente = "5107909" # Sinop-MT
    ano = 2022
    
    url = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
    params = {
        "an_exercicio": ano,
        "id_ente": id_ente,
        "no_anexo": "DCA-Anexo I-C"
    }
    
    print(f"Consultando API para {ano}...")
    try:
        r = requests.get(url, params=params, timeout=10)
        items = r.json().get('items', [])
        
        if not items:
            print("ERRO: API retornou lista vazia para {ano}.")
            return

        df = pd.DataFrame(items)
        
        # 1. VERIFICAR NOME DA COLUNA
        print("\n[1] QUAIS COLUNAS EXISTEM EM?")
        colunas_unicas = df['coluna'].unique()
        for c in colunas_unicas:
            print(f"   - '{c}'")

        # 2. VERIFICAR CÓDIGOS DAS CONTAS (Valor > 0)
        # Vamos pegar a coluna que parece ser a de valor realizado
        col_valor = [c for c in colunas_unicas if "Realizada" in c or "Valor" in c]
        
        if col_valor:
            col_alvo = col_valor[0]
            print(f"\n[2] AMOSTRA DE CONTAS (Coluna: '{col_alvo}')")
            
            # Filtra onde tem valor
            df_filtro = df[df['coluna'] == col_alvo].copy()
            df_filtro['valor'] = pd.to_numeric(df_filtro['valor'])
            df_filtro = df_filtro[df_filtro['valor'] > 0]
            
            # Procura Impostos (1.1...)
            print("\n>>> IMPOSTOS (Começam com 1.1):")
            ex_impostos = df_filtro[df_filtro['conta'].str.startswith('1.1.')]['conta'].unique()[:50]
            for i in ex_impostos: print(f"   {i}")
            
            # Procura Transferências (1.7...)
            print("\n>>> TRANSFERÊNCIAS (Começam com 1.7):")
            ex_transf = df_filtro[df_filtro['conta'].str.startswith('1.7.')]['conta'].unique()[:50]
            for i in ex_transf: print(f"   {i}")
            
        else:
            print("Não consegui identificar a coluna de valor automaticamente.")
            print(df.head())

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    sonda_2022_bruta()