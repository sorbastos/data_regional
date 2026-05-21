import sidrapy
import pandas as pd
import sqlite3
import requests

def extrair_e_salvar_dados():
    nome_banco = "pib_regional.db"
    
    # Abrimos a conexão com o banco logo no início
    conn = sqlite3.connect(nome_banco)

    # =========================================================================
    # 1. EXTRAÇÃO DO IPCA (VIA BANCO CENTRAL DO BRASIL)
    # =========================================================================
    print("1. Buscando IPCA Anual via Banco Central (SGS)...")
    url_bcb = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados?formato=json"
    
    try:
        resposta = requests.get(url_bcb, timeout=15)
        if resposta.status_code == 200:
            df_ipca = pd.DataFrame(resposta.json())
            
            # Formatação de datas e valores
            df_ipca['data'] = pd.to_datetime(df_ipca['data'], format='%d/%m/%Y')
            df_ipca['valor'] = pd.to_numeric(df_ipca['valor'])
            
            # Isolar o mês de dezembro (que contém o acumulado fechado do ano)
            df_anual = df_ipca[df_ipca['data'].dt.month == 12].copy()
            df_anual['ano'] = df_anual['data'].dt.year
            df_anual['ipca_anual'] = df_anual['valor'] / 100
            
            # Filtrar a partir de 2013
            df_ipca_final = df_anual[(df_anual['ano'] >= 2013) & (df_anual['ano'] <= 2023)][['ano', 'ipca_anual']].reset_index(drop=True)
            
            # --- SOLUÇÃO DEFINITIVA EM SQL PURO ---
            cursor = conn.cursor()
            
            # 1. Destrói a tabela velha por completo (limpa o cache de tipos do SQLite)
            cursor.execute("DROP TABLE IF EXISTS indice_ipca")
            
            # 2. Cria a tabela exigindo categoricamente que a coluna seja decimal (REAL)
            cursor.execute("CREATE TABLE indice_ipca (ano INTEGER, ipca_anual REAL)")
            
            # 3. Converte os dados do Pandas para uma lista de tuplas Python nativas
            registros = list(df_ipca_final.itertuples(index=False, name=None))
            
            # 4. Injeta os dados diretamente no banco ignorando o to_sql do Pandas
            cursor.executemany("INSERT INTO indice_ipca (ano, ipca_anual) VALUES (?, ?)", registros)
            conn.commit()
            
            print(f"✅ Tabela de IPCA recriada e inserida via SQL puro! ({len(registros)} anos resgatados)")
        else:
            print(f"❌ Erro ao acessar API do Banco Central: HTTP {resposta.status_code}")
    except Exception as e:
        print(f"❌ Falha na conexão com o Banco Central: {e}")


    # =========================================================================
    # 2. EXTRAÇÃO DO PIB (VIA IBGE)
    # =========================================================================
    print("\n2. Iniciando extração de dados do PIB pelo IBGE (Norte e Centro-Oeste)...")

    try:
        # Usa 'all' para prevenir que a API trave ao pedir um ano recém-virado que ainda não existe
        df_raw = sidrapy.get_table(
            table_code="5938",          
            territorial_level="6",      
            ibge_territorial_code="in n2 1,5", 
            variable="37",              
            period="all" 
        )
    except Exception as e:
        print(f"❌ Erro de conexão com o IBGE: {e}")
        conn.close()
        return 

    # --- TRATAMENTO ROBUSTO DE CABEÇALHO ---
    coluna_valor_exemplo = df_raw.columns[4]
    
    e_dado_no_header = False
    try:
        float(coluna_valor_exemplo)
        e_dado_no_header = True
    except:
        pass

    if e_dado_no_header:
        linha_perdida = pd.DataFrame([df_raw.columns], columns=df_raw.columns)
        df_raw = pd.concat([linha_perdida, df_raw], axis=0, ignore_index=True)
    else:
        if not df_raw.empty:
            primeira_celula = str(df_raw.iloc[0, 4])
            if primeira_celula in ['V', 'Valor', '37']: 
                df_raw = df_raw.iloc[1:]

    # --- SELEÇÃO E LIMPEZA DE COLUNAS ---
    df_final = df_raw.iloc[:, [4, 5, 6, 8]].copy()
    df_final.columns = ['pib_valor', 'cod_ibge', 'municipio', 'ano']

    # Conversão de tipos
    df_final['pib_valor'] = pd.to_numeric(df_final['pib_valor'], errors='coerce')
    df_final['ano'] = pd.to_numeric(df_final['ano'], errors='coerce')
    
    # Removemos linhas vazias
    df_final.dropna(subset=['pib_valor', 'ano'], inplace=True)
    
    # Mantemos apenas os dados a partir de 2013
    df_final = df_final[df_final['ano'] >= 2013]
    
    # Filtro para excluir Brasília
    print("Aplicando filtro para remover Brasília...")
    df_final = df_final[df_final['cod_ibge'].astype(str) != '5300108']
    
    print(f"Extração concluída. Total de registros do PIB: {len(df_final)}")

    # =========================================================================
    # 3. SALVAR PIB NO BANCO
    # =========================================================================
    print(f"Salvando dados de PIB no arquivo '{nome_banco}'...")
    df_final.to_sql("pib_municipios", conn, if_exists='replace', index=False)
    
    conn.close()
    print("✅ Sucesso total! Bases do Banco Central e IBGE integradas e salvas no banco de dados.")

if __name__ == "__main__":
    extrair_e_salvar_dados()