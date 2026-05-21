import sqlite3
import pandas as pd
import os

# Configuração para mostrar todas as colunas no terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', '{:,.4f}'.format) # Formata números grandes sem notação científica

def inspecionar_banco_pib():
    nome_banco = "pib_regional.db"
    
    print(f"--- INSPEÇÃO GERAL: {nome_banco} ---\n")
    
    if not os.path.exists(nome_banco):
        print(f"ERRO: O arquivo '{nome_banco}' não foi encontrado.")
        return

    try:
        conn = sqlite3.connect(nome_banco)
        cursor = conn.cursor()

        # 1. PEGAR LISTA DE TABELAS
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        
        if not tabelas:
            print("O banco está vazio (sem tabelas).")
            return
            
        print(f"Tabelas encontradas: {[t[0] for t in tabelas]}\n")

        # 2. LOOP PARA MOSTRAR DADOS DE CADA TABELA
        for t in tabelas:
            nome_tabela = t[0]
            print(f"{'='*20} TABELA: {nome_tabela} {'='*20}")
            
            # Conta total de registros
            total = pd.read_sql_query(f"SELECT COUNT(*) FROM {nome_tabela}", conn).iloc[0,0]
            print(f"Total de registros: {total:,}".replace(",", "."))
            
            # Mostra as 11 primeiras linhas
            print(f"Amostra (Top 15):")
            df = pd.read_sql_query(f"SELECT * FROM {nome_tabela} LIMIT 15", conn)
            print(df)
            print("\n")

        conn.close()

    except Exception as e:
        print(f"Erro ao ler o banco: {e}")

if __name__ == "__main__":
    inspecionar_banco_pib()