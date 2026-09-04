import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS
import warnings
import os

warnings.filterwarnings('ignore')

def load_and_prepare_data(filepath="Painel_Completo_2013_2023.xlsx"):
    print("=========================================================")
    print("1. CARREGAMENTO E PREPARAÇÃO DOS DADOS (EM NÍVEL)")
    print("=========================================================")
    if not os.path.exists(filepath):
        print(f"ERRO: Arquivo {filepath} não encontrado.")
        return None
        
    df_bruto = pd.read_excel(filepath)
    
    # Agrupando despesas
    df_bruto['desp_leg_adm'] = df_bruto['d_leg_r'].fillna(0) + df_bruto['d_adm_r'].fillna(0)
    df_bruto['desp_educ_cult'] = df_bruto['d_educ_r'].fillna(0) + df_bruto['d_cult_r'].fillna(0)
    df_bruto['desp_saude_san'] = df_bruto['d_saude_r'].fillna(0) + df_bruto['d_san_r'].fillna(0)
    df_bruto['desp_hab_urb'] = df_bruto['d_habit_r'].fillna(0) + df_bruto['d_urb_r'].fillna(0)
    df_bruto['desp_agri'] = df_bruto['d_agri_r'].fillna(0)
    df_bruto['transuniao'] = df_bruto['transuniao_r']
    df_bruto['transest'] = df_bruto['transest_r']
    
    # Declarando a estrutura de Painel (MultiIndex: Entidade, Tempo)
    df_painel = df_bruto.set_index(['cod_ibge', 'ano'])
    
    # Variáveis em nível a serem defasadas
    variaveis_base = [
        'desp_leg_adm', 'desp_educ_cult', 'desp_saude_san',
        'desp_hab_urb', 'desp_agri', 'transuniao', 'transest'
    ]
    
    print("Criando variáveis defasadas (t-1 e t-2)...")
    for var in variaveis_base:
        # Lag de 1 ano
        df_painel[f'{var}_lag1'] = df_painel.groupby(level=0)[var].shift(1)
        # Lag de 2 anos
        df_painel[f'{var}_lag2'] = df_painel.groupby(level=0)[var].shift(2)
        
    return df_painel

def calcular_criterios(res):
    """Calcula AIC e BIC com base no log-likelihood para comparação formal."""
    loglik = res.loglik
    k = res.df_model
    n = res.nobs
    aic = -2 * loglik + 2 * k
    bic = -2 * loglik + k * np.log(n)
    return aic, bic

def run_regressions(df_painel):
    print("\n=========================================================")
    print("2. ESTIMAÇÃO DOS MODELOS EM NÍVEL (EFEITOS FIXOS)")
    print("=========================================================")
    
    variaveis_base = [
        'desp_leg_adm', 'desp_educ_cult', 'desp_saude_san',
        'desp_hab_urb', 'desp_agri', 'transuniao', 'transest'
    ]
    
    # === MODELO 2: Efeitos Fixos Defasado em 1 Ano (Lag 1) ===
    exog_lag1 = [f'{var}_lag1' for var in variaveis_base]
    
    # Filtra NAs para o modelo com lag 1
    df_m2 = df_painel[['pib'] + exog_lag1].dropna()
    Y_m2 = df_m2['pib']
    X_m2 = df_m2[exog_lag1]
    
    print("\n>>> Estimando Efeitos Fixos Bidirecionais (Lag 1)...")
    fe_m2 = PanelOLS(Y_m2, X_m2, entity_effects=True, time_effects=True)
    res_m2 = fe_m2.fit(cov_type='robust')
    aic_m2, bic_m2 = calcular_criterios(res_m2)
    
    # === MODELO 3: Efeitos Fixos Defasado em 2 Anos (Lag 2 - Isolado) ===
    exog_lag2 = [f'{var}_lag2' for var in variaveis_base]
    
    # Filtra NAs para o modelo com lag 2
    df_m3 = df_painel[['pib'] + exog_lag2].dropna()
    Y_m3 = df_m3['pib']
    X_m3 = df_m3[exog_lag2]
    
    print(">>> Estimando Efeitos Fixos Bidirecionais (Lag 2)...")
    fe_m3 = PanelOLS(Y_m3, X_m3, entity_effects=True, time_effects=True)
    res_m3 = fe_m3.fit(cov_type='robust')
    aic_m3, bic_m3 = calcular_criterios(res_m3)
    
    # === RESULTADOS ===
    print("\n" + "="*80)
    print("MODELO 2: EFEITOS FIXOS (LAG 1)")
    print("="*80)
    print(res_m2.summary)

    print("\n" + "="*80)
    print("MODELO 3: EFEITOS FIXOS (LAG 2)")
    print("="*80)
    print(res_m3.summary)
    
    # ------------------------------------------------------------------
    # SALVANDO OS RESULTADOS EM UM ARQUIVO MARKDOWN (.md)
    # ------------------------------------------------------------------
    print("\nSalvando os resultados no arquivo 'resultados_efeitos_fixos_sem_log.md'...")
    md_content = "# Resultados da Estimação de Efeitos Fixos (Modelos em Nível)\n\n"
    
    md_content += "## Modelo 2: Efeitos Fixos (Lag 1)\n"
    md_content += f"> **Critérios de Seleção:** AIC = {aic_m2:.2f} | BIC = {bic_m2:.2f}\n\n"
    md_content += f"```text\n{res_m2.summary.as_text()}\n```\n\n"
    
    md_content += "## Modelo 3: Efeitos Fixos (Lag 2)\n"
    md_content += f"> **Critérios de Seleção:** AIC = {aic_m3:.2f} | BIC = {bic_m3:.2f}\n\n"
    md_content += f"```text\n{res_m3.summary.as_text()}\n```\n"

    try:
        with open('resultados_efeitos_fixos_sem_log.md', 'w', encoding='utf-8') as f:
            f.write(md_content)
        print("Arquivo 'resultados_efeitos_fixos_sem_log.md' gerado com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar arquivo markdown: {e}")

if __name__ == "__main__":
    df = load_and_prepare_data()
    if df is not None:
        run_regressions(df)