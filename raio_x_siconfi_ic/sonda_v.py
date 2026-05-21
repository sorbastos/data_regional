import requests
import pandas as pd

def sondar_finbra_2010():
    print("--- SONDAGEM DE DADOS ANTIGOS (FINBRA 2010) ---")
    
    # Tentativa 1: Endpoint Padrão (DCA) - Provavelmente falhará ou virá vazio
    print("1. Testando via DCA (Padrão Novo)...")
    url_dca = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
    try:
        r = requests.get(url_dca, params={"an_exercicio": 2010, "id_ente": "5107909", "no_anexo": "DCA-Anexo I-E"}, timeout=5)
        if r.status_code == 200 and r.json()['items']:
            print("   -> SURPRESA! O DCA retornou dados de 2010.")
            print(r.json()['items'][0])
        else:
            print("   -> (Esperado) DCA vazio para 2010.")
    except:
        print("   -> Erro na conexão DCA.")

    # Tentativa 2: Endpoint FINBRA (Onde moram os dados antigos)
    # Esse endpoint é mais 'chato', exige parâmetros específicos
    print("\n2. Testando via FINBRA (Formato Antigo)...")
    url_finbra = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/finbra"
    
    # Parâmetros típicos do Finbra antigo:
    # tipo_matriz = MSCC (Matriz de Saldos Contábeis) ou similar
    # Mas para 2010, usamos 'RREO' ou 'RGF' geralmente.
    
    # Vamos tentar baixar 'Despesas por Função' (Anexo 2 do RREO)
    params_finbra = {
        "an_exercicio": 2010,
        "id_ente": "5107909",
        "no_anexo": "RREO-Anexo 02", # Despesas por Função no RREO
        "co_tipo_matriz": "MSCC" # Às vezes necessário, às vezes não
    }
    
    try:
        r = requests.get(url_finbra, params=params_finbra, timeout=10)
        
        # A API do Finbra às vezes retorna estrutura diferente
        if r.status_code == 200:
            items = r.json().get('items', [])
            if items:
                print(f"   -> SUCESSO! Encontrados {len(items)} registros no FINBRA 2010.")
                df = pd.DataFrame(items)
                print(df.head(3))
                
                # Verifica se tem as colunas que precisamos
                cols = df.columns
                print(f"\n   Colunas: {list(cols)}")
                
                # Tenta achar a função
                if 'coluna' in cols and 'conta' in cols:
                    print("\n   Exemplo de Contas:")
                    print(df['conta'].head())
            else:
                print("   -> FINBRA retornou lista vazia para 2010.")
        else:
            print(f"   -> Erro HTTP: {r.status_code}")
            
    except Exception as e:
        print(f"   -> Erro na conexão FINBRA: {e}")

    print("\n--- VEREDITO ---")
    print("Se o teste 2 funcionou, podemos construir o painel longo.")
    print("Se falhou, teremos que baixar os CSVs manualmente no site do Tesouro (eu te ensino).")

if __name__ == "__main__":
    sondar_finbra_2010()