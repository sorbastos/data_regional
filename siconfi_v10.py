import pandas as pd
import sqlite3
import requests
import time
import os
from tqdm import tqdm

def extrair_siconfi_v10_multiversal():
    # --- CONFIGURAÇÕES ---
    # Usa o banco de PIB mais recente que você criou
    if os.path.exists("pib_norte_centro_oeste.db"):
        arquivo_origem_pib = "pib_norte_centro_oeste.db"
    else:
        arquivo_origem_pib = "pib_regional.db"

    arquivo_destino = "siconfi_v10_final.db"
    anos = range(2014, 2024) # 2014 a 2023

    # 1. DESPESAS (Mantém as 19 funções padrão)
    funcoes_despesa = [
        '01', '04', '06', '08', '09', '10', '11', '12', '13', 
        '15', '16', '17', '18', '19', '20', '22', '23', '26', '27'
    ]
    
    # 2. RECEITAS (O "Molho de Chaves")
    # Para cada categoria final, aceitamos QUALQUER um dos códigos/nomes da lista
    mapa_receitas_flexivel = {
        "Rec_Impostos_Proprios": [
            "1.1.0.0.00.00.00",   # Padrão
            "1.1.0.0.00.0.0", # Variação de zeros
        ],
        "Rec_Transf_Uniao": [
            "1.7.2.1.00.00.00", # Código Antigo (até 2017)
            "1.7.1.0.00.0.0",   # Código Novo (2018+ - Específicas)
        ],
        "Rec_Transf_Estados": [
            "1.7.2.2.00.00.00", # Código Antigo (até 2017)
            "1.7.2.0.00.0.0",   # Código Novo (2018+ - Específicas)
        ],
        "Rec_Total": [
            "Total Receitas", # Padrão
            "TOTAL DAS RECEITAS (III) = (I + II)",           # O caso específico de 2018
        ]
    }

    print("--- SICONFI V10: EXTRAÇÃO MULTIVERSAL (2014-2023) ---")
    
    if not os.path.exists(arquivo_origem_pib):
        print(f"ERRO: Banco de PIB '{arquivo_origem_pib}' não encontrado.")
        return

    # Lendo municípios
    conn = sqlite3.connect(arquivo_origem_pib)
    try:
        df_muni = pd.read_sql("SELECT DISTINCT cod_ibge FROM pib_municipios WHERE cod_ibge != '5300108'", conn)
    except:
        print("Erro ao ler tabela pib_municipios.")
        return
    conn.close()
    
    lista_codigos = df_muni['cod_ibge'].astype(str).unique()
    print(f"Municípios: {len(lista_codigos)}")
    print(f"Destino: {arquivo_destino}\n")
    
    if os.path.exists(arquivo_destino):
        os.remove(arquivo_destino)

    conn_dest = sqlite3.connect(arquivo_destino)
    contador = 0
    
    for cod in tqdm(lista_codigos, desc="Baixando"):
        buffer = []
        for ano in anos:
            # --- DESPESAS ---
            try:
                r = requests.get("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca", 
                               params={"an_exercicio": ano, "id_ente": cod, "no_anexo": "DCA-Anexo I-E"}, timeout=5)
                if r.status_code == 200:
                    for item in r.json().get('items', []):
                        if "Despesas Pagas" in item.get('coluna', ''):
                            conta = item.get('conta', '')
                            cod_conta = conta.split(' - ')[0].strip()
                            if cod_conta in funcoes_despesa:
                                buffer.append({
                                    'cod_ibge': cod, 'ano': ano, 'tipo': 'Despesa',
                                    'categoria': cod_conta, 'descricao': conta,
                                    'valor': item.get('valor', 0),
                                    'populacao': item.get('populacao')
                                })
            except: pass 

            # --- RECEITAS (Lógica Flexível) ---
            try:
                r = requests.get("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca", 
                               params={"an_exercicio": ano, "id_ente": cod, "no_anexo": "DCA-Anexo I-C"}, timeout=5)
                if r.status_code == 200:
                    for item in r.json().get('items', []):
                        if "Receitas Brutas Realizadas" in item.get('coluna', ''):
                            conta_texto = item.get('conta', '')
                            
                            # Verifica se o texto bate com ALGUMA das chaves do nosso mapa
                            encontrou = False
                            for cat_final, lista_chaves in mapa_receitas_flexivel.items():
                                for chave in lista_chaves:
                                    if chave in conta_texto:
                                        buffer.append({
                                            'cod_ibge': cod, 'ano': ano, 'tipo': 'Receita',
                                            'categoria': cat_final, # Salva o nome padronizado (ex: Rec_Total)
                                            'descricao': conta_texto,
                                            'valor': item.get('valor', 0),
                                            'populacao': item.get('populacao')
                                        })
                                        encontrou = True
                                        break # Sai do loop de chaves
                                if encontrou: break # Sai do loop de categorias (já achou a certa)
            except: pass
            
            time.sleep(0.005)

        if buffer:
            df = pd.DataFrame(buffer)
            df.to_sql("dados_siconfi", conn_dest, if_exists='append', index=False)
            contador += len(buffer)

    conn_dest.close()
    print(f"\nConcluído! {contador} registros salvos em {arquivo_destino}")

if __name__ == "__main__":
    extrair_siconfi_v10_multiversal()