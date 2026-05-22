import sqlite3
import pandas as pd
import numpy as np
import os

def gerar_painel_completo_v2():
    print("--- GERANDO PAINEL FINAL CONSOLIDADO (2013-2023) ---")
    
    db_pib = "pib_regional.db"
    db_siconfi = "siconfi_v10_final.db"
    arquivo_saida = "Painel_Completo_2013_2023.xlsx"

    # =========================================================================
    # 1. CARREGAR DADOS DO SICONFI E ISOLAR A POPULAÇÃO
    # =========================================================================
    if not os.path.exists(db_siconfi):
        print(f"Erro: {db_siconfi} não encontrado.")
        return

    print("1. Carregando Siconfi e blindando a População contra somatórias...")
    conn_s = sqlite3.connect(db_siconfi)
    df_sic = pd.read_sql("SELECT * FROM dados_siconfi", conn_s)
    conn_s.close()
    
    # Remover duplicatas de segurança
    df_sic.drop_duplicates(subset=['cod_ibge', 'ano', 'categoria'], keep='first', inplace=True)

    # --- BLINDAGEM DA POPULAÇÃO ---
    if 'populacao' in df_sic.columns:
        df_pop = df_sic.groupby(['cod_ibge', 'ano'])['populacao'].max().reset_index()
    else:
        print("Aviso: Coluna 'populacao' não encontrada. O cálculo per capita pode falhar.")
        df_pop = pd.DataFrame(columns=['cod_ibge', 'ano', 'populacao'])

    # Pivotar (Linhas -> Colunas) APENAS as categorias e seus valores financeiros
    df_sic_pivot = df_sic.pivot_table(
        index=['cod_ibge', 'ano'], 
        columns='categoria', 
        values='valor', 
        aggfunc='sum'
    ).reset_index()

    # Mesclar a população de volta (intacta e sem somatório)
    df_sic_pivot = pd.merge(df_sic_pivot, df_pop, on=['cod_ibge', 'ano'], how='left')

    # Renomear para nomes amigáveis
    mapa_nomes = {
        '01': 'desp_legislativa', '04': 'desp_adm', '06': 'desp_seguranca',
        '08': 'desp_assist_social', '09': 'desp_previdencia', '10': 'desp_saude',
        '11': 'desp_trabalho', '12': 'desp_educacao', '13': 'desp_cultura',
        '15': 'desp_urbanismo', '16': 'desp_habitacao', '17': 'desp_saneamento',
        '18': 'desp_ambiental', '19': 'desp_ciencia', '20': 'desp_agricultura',
        '22': 'desp_industria', '23': 'desp_comercio', '26': 'desp_transporte',
        '27': 'desp_desporto',
        'Rec_Total': 'rec_orcamentaria_total',
        'Rec_Impostos_Proprios': 'rec_tributaria_propria',
        'Rec_Transf_Uniao': 'rec_transf_uniao',
        'Rec_Transf_Estados': 'rec_transf_estados'
    }
    df_sic_pivot.rename(columns=mapa_nomes, inplace=True)
    
    # IMPORTANTE: A instrução fillna(0) foi removida daqui!
    # Contas financeiras que não existirem para o município ficarão como NaN (vazias)

    # =========================================================================
    # 2. CARREGAR DADOS DO PIB E IPCA
    # =========================================================================
    if not os.path.exists(db_pib):
        print(f"Erro: {db_pib} não encontrado.")
        return

    print("2. Carregando dados de PIB e IPCA...")
    conn_p = sqlite3.connect(db_pib)
    df_lado_y = pd.read_sql("SELECT * FROM pib_municipios", conn_p)
    df_ipca = pd.read_sql("SELECT * FROM indice_ipca", conn_p)
    conn_p.close()

    # =========================================================================
    # 3. CRUZAMENTO FINAL (INNER JOIN)
    # =========================================================================
    print("3. Unificando as bases de dados...")
    
    # Garantir tipos compatíveis para o Merge
    df_sic_pivot['cod_ibge'] = df_sic_pivot['cod_ibge'].astype(str)
    df_sic_pivot['ano'] = df_sic_pivot['ano'].astype(int)
    df_lado_y['cod_ibge'] = df_lado_y['cod_ibge'].astype(str)
    df_lado_y['ano'] = df_lado_y['ano'].astype(int)

    df_final = pd.merge(df_lado_y, df_sic_pivot, on=['cod_ibge', 'ano'], how='inner')

    # =========================================================================
    # 4. DEFLACIONAR (PREÇOS CONSTANTES DE 2023)
    # =========================================================================
    print("4. Atualizando valores financeiros para Preços Constantes de 2023...")
    
    df_ipca.sort_values('ano', inplace=True)
    fatores = {}
    ano_base = 2023 
    
    for ano in df_final['ano'].unique():
        if ano >= ano_base:
            fatores[ano] = 1.0
        else:
            # IPCA Acumulado: Multiplica as taxas anuais a partir do ano seguinte até 2023
            taxas = df_ipca[(df_ipca['ano'] > ano) & (df_ipca['ano'] <= ano_base)]['ipca_anual']
            fator = np.prod(1 + taxas)
            fatores[ano] = fator

    df_final['deflator_ipca'] = df_final['ano'].map(fatores)
    
    # --- FILTRO ESTRITO PARA DEFLAÇÃO ---
    cols_monetarias = [c for c in df_final.columns if c.startswith('desp_') or c.startswith('rec_') or c == 'pib_valor']
    
    for col in cols_monetarias:
        # Células NaN multiplicadas pelo deflator continuarão NaN (vazias)
        df_final[f'{col}_real'] = df_final[col] * df_final['deflator_ipca']

    # =========================================================================
    # 5. CÁLCULO PER CAPITA (COM DADOS REAIS)
    # =========================================================================
    print("5. Calculando métricas Per Capita...")
    
    # Remove apenas se a população for nula ou zero, evitando quebrar a matemática global
    df_final = df_final[(df_final['populacao'].notna()) & (df_final['populacao'] > 0)]
    
    cols_reais = [c for c in df_final.columns if c.endswith('_real')]
    for col in cols_reais:
        nome_pc = col.replace('_real', '_pc')
        # Células NaN divididas pela população continuarão NaN (vazias)
        df_final[nome_pc] = df_final[col] / df_final['populacao']

    # =========================================================================
    # 6. EXPORTAR RELATÓRIO
    # =========================================================================
    df_final.to_excel(arquivo_saida, index=False)
    
    print("\n=== RELATÓRIO FINAL CONCLUÍDO ===")
    print(f"Arquivo gerado: {arquivo_saida}")
    print(f"Total de Municípios cruzados: {df_final['cod_ibge'].nunique()}")
    print("Distribuição das linhas por Ano:")
    print(df_final['ano'].value_counts().sort_index())

if __name__ == "__main__":
    gerar_painel_completo_v2()