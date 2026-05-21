import sqlite3
import pandas as pd

# Configuração visual para mostrar todas as colunas no terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 50) 
pd.set_option('display.float_format', '{:,.2f}'.format)

def visualizar_siconfi_norte_co():
    # NOME CORRETO DO ARQUIVO QUE TEM DADOS (Conforme seu print)
    nome_banco = "siconfi_v10_final.db"
    tabela = "dados_siconfi"

    print(f"--- LENDO ARQUIVO: {nome_banco} ---\n")
    
    if not os.path.exists(nome_banco):
        print(f"ERRO: O arquivo '{nome_banco}' não foi encontrado.")
        return

    try:
        conn = sqlite3.connect(nome_banco)
        
        # Carrega as 11 primeiras linhas
        query = f"SELECT * FROM {tabela} LIMIT 50"
        df = pd.read_sql(query, conn)
        
        conn.close()

        if df.empty:
            print("ALERTA: A tabela existe mas não retornou linhas.")
        else:
            print(f">>> AMOSTRA (TOP 50 REGISTROS):")
            print(df)
            print("-" * 60)
            
            # Dica extra: Verifica se tem 2023 nessa amostra ou no banco
            conn = sqlite3.connect(nome_banco)
            anos = pd.read_sql(f"SELECT DISTINCT ano FROM {tabela} ORDER BY ano", conn)
            conn.close()
            print(f"Anos presentes no banco completo: {anos['ano'].tolist()}")

    except Exception as e:
        print(f"Erro ao abrir banco: {e}")

# Import necessário para o os.path.exists
import os

if __name__ == "__main__":
    visualizar_siconfi_norte_co()