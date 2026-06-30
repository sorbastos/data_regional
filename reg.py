import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS, RandomEffects, PooledOLS
import warnings
import numpy.linalg as la
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import os

warnings.filterwarnings('ignore')

def load_and_prepare_data(filepath="Painel_Completo_2013_2023.xlsx"):
    print("=========================================================")
    print("1. CARREGAMENTO DOS DADOS")
    print("=========================================================")
    if not os.path.exists(filepath):
        print(f"ERRO: Arquivo {filepath} não encontrado.")
        return None
        
    print(f"Carregando o painel de dados: {filepath}...")
    df_bruto = pd.read_excel(filepath)
    
    print("\n=========================================================")
    print("2. PREPARAÇÃO E AGRUPAMENTO DAS VARIÁVEIS")
    print("=========================================================")
    # Agrupando despesas (Lidando com NaNs com preenchimento zero onde somamos, ou deixando NaN)
    # Preferimos tratar com dropna posteriormente.
    df_bruto['desp_leg_adm'] = df_bruto['d_leg_r'].fillna(0) + df_bruto['d_adm_r'].fillna(0)
    df_bruto['desp_educ_cult'] = df_bruto['d_educ_r'].fillna(0) + df_bruto['d_cult_r'].fillna(0)
    df_bruto['desp_saude_san'] = df_bruto['d_saude_r'].fillna(0) + df_bruto['d_san_r'].fillna(0)
    df_bruto['desp_hab_urb'] = df_bruto['d_habit_r'].fillna(0) + df_bruto['d_urb_r'].fillna(0)
    df_bruto['desp_agri_v'] = df_bruto['d_agri_r'].fillna(0)
    
    # Transformação logarítmica tradicional (log(x + 1) para evitar zeros nas despesas)
    df_bruto['ln_pib_pc'] = np.log(df_bruto['pib_pc'])
    df_bruto['ln_transuniao'] = np.log(df_bruto['transuniao_r'] + 1)
    df_bruto['ln_desp_leg_adm'] = np.log(df_bruto['desp_leg_adm'] + 1)
    df_bruto['ln_desp_educ_cult'] = np.log(df_bruto['desp_educ_cult'] + 1)
    df_bruto['ln_desp_saude_san'] = np.log(df_bruto['desp_saude_san'] + 1)
    df_bruto['ln_desp_hab_urb'] = np.log(df_bruto['desp_hab_urb'] + 1)
    df_bruto['ln_desp_agri'] = np.log(df_bruto['desp_agri_v'] + 1)
    df_bruto['ln_transest'] = np.log(df_bruto['transest_r'] + 1)
    
    # Declarando a estrutura de Painel (MultiIndex: Entidade, Tempo)
    df_painel = df_bruto.set_index(['cod_ibge', 'ano'])

    return df_painel

def hausman_test(fe_res, re_res):
    """
    Calcula o Teste de Hausman para escolher entre Efeitos Fixos e Aleatórios.
    H0: O modelo de Efeitos Aleatórios é consistente e mais eficiente.
    H1: O modelo de Efeitos Fixos é consistente (RE não é).
    """
    b_fe, b_re = fe_res.params, re_res.params
    v_fe, v_re = fe_res.cov, re_res.cov
    
    # Isolar os coeficientes comuns
    common_coef = list(set(b_fe.index).intersection(b_re.index))
    b_fe, b_re = b_fe[common_coef], b_re[common_coef]
    v_fe, v_re = v_fe.loc[common_coef, common_coef], v_re.loc[common_coef, common_coef]
    
    df = len(common_coef)
    diff = b_fe - b_re
    v_diff = v_fe - v_re
    
    try:
        chi2 = diff.dot(la.inv(v_diff)).dot(diff)
        pval = stats.chi2.sf(np.abs(chi2), df)
        return chi2, df, pval
    except la.LinAlgError:
        return np.nan, df, np.nan

def fisher_adf_test(panel_series):
    """
    Teste Fisher-ADF de Raiz Unitária para dados em painel.
    H0: As séries temporais individuais possuem raiz unitária.
    """
    p_values = []
    entities = panel_series.index.levels[0]
    for entity in entities:
        series = panel_series.xs(entity).dropna()
        if len(series) > 3:  # Necessário um mínimo de observações na série histórica
            try:
                res = adfuller(series, maxlag=1, autolag=None)
                p_values.append(res[1])
            except: pass
            
    if not p_values: return np.nan, np.nan
        
    p_values = np.array(p_values)
    p_values[p_values == 0] = 1e-10 # Prevenir log(0)
    fisher_stat = -2 * np.sum(np.log(p_values))
    df = 2 * len(p_values)
    pval = stats.chi2.sf(fisher_stat, df)
    
    return fisher_stat, pval

def run_regressions(df_painel):
    print("\n=========================================================")
    print("3. ESTIMAÇÃO DOS MODELOS")
    print("=========================================================")
    
    exog_vars = [
        'd_leg', 'd_adm', 'd_educ', 'd_cult', 'd_saude', 'd_san',
        'd_habit', 'd_urb', 'd_agri', 'transuniao', 'transest'
    ]
    exog_vars_ln = [
        'ln_desp_leg_adm', 'ln_desp_educ_cult', 'ln_desp_saude_san',
        'ln_desp_hab_urb', 'ln_desp_agri', 'ln_transuniao', 'ln_transest'
    ]
    exog_varsg = [
        'desp_leg_adm', 'desp_educ_cult', 'desp_saude_san',
        'desp_hab_urb', 'd_agri', 'transuniao', 'transest'
    ]

    endog = df_painel['pib_pc']
    endog_ln = df_painel['ln_pib_pc']
    exog = df_painel[exog_vars]
    exog_ln = df_painel[exog_vars_ln]
    
    # 1. Pooled OLS
    print(">>> Pooled OLS (POLS)...")
    pols = PooledOLS(endog, exog)
    pols_res = pols.fit()

    # 2. Efeitos Fixos (Two-ways: Entidade e Tempo)
    print(">>> Efeitos Fixos (Within - Twoways)...")
    fe = PanelOLS(endog, exog, entity_effects=True, time_effects=True)
    fe_res = fe.fit() 
    
    fe_res_ln = PanelOLS(endog_ln, exog_ln, entity_effects=True, time_effects=True)
    fe_res_ln = fe_res_ln.fit() 
    
    # 3. Efeitos Aleatórios
    print(">>> Efeitos Aleatórios...")
    re = RandomEffects(endog, exog)
    re_res = re.fit()
    
    re_res_ln = RandomEffects(endog_ln, exog_ln)
    re_res_ln = re_res_ln.fit()
    
    # === RESULTADOS ===
    print("\n" + "="*80)
    print("RESUMO DO MODELO DE POOLED OLS (Mínimos Quadrados Ordinários)")
    print("="*80)
    print(pols_res.summary)

    print("\n" + "="*80)
    print("RESUMO DO MODELO DE POOLED OLS (LOG) (Mínimos Quadrados Ordinários)")
    print("="*80)
    
    print("\n" + "="*80)
    print("RESUMO DO MODELO DE EFEITOS FIXOS")
    print("="*80)
    print(fe_res.summary)

    print("\n" + "="*80)
    print("RESUMO DO MODELO DE EFEITOS FIXOS (LOG)")
    print("="*80)
    print(fe_res_ln.summary)
    
    print("\n" + "="*80)
    print("RESUMO DO MODELO DE EFEITOS ALEATÓRIOS")
    print("="*80)
    print(re_res.summary)

    print("\n" + "="*80)
    print("RESUMO DO MODELO DE EFEITOS ALEATÓRIOS (LOG)")
    print("="*80)
    print(re_res_ln.summary)

    return fe_res, re_res, fe_res_ln, re_res_ln

def run_diagnostics(df_painel, fe_res, re_res, fe_res_ln, re_res_ln):
    endog = df_painel['pib_pc']
    endog_ln = df_painel['ln_pib_pc']
    
    # === TESTES DE DIAGNÓSTICO ===
    print("\n" + "="*80)
    print("TESTE DE HAUSMAN (Efeitos Fixos vs Efeitos Aleatórios)")
    print("="*80)
    h_stat, h_df, h_pval = hausman_test(fe_res, re_res)
    print("--- Modelo em Nível ---")
    print(f"Estatística Chi-quadrado ({h_df} df): {h_stat:.4f} | P-valor: {h_pval:.4f}")
    if h_pval < 0.05: print("Conclusão: Rejeita H0 -> Efeitos Fixos é preferido.")
    else: print("Conclusão: Não rejeita H0 -> Efeitos Aleatórios é preferido.")

    h_stat_ln, h_df_ln, h_pval_ln = hausman_test(fe_res_ln, re_res_ln)
    print("\n--- Modelo em LOG ---")
    print(f"Estatística Chi-quadrado ({h_df_ln} df): {h_stat_ln:.4f} | P-valor: {h_pval_ln:.4f}")
    if h_pval_ln < 0.05: print("Conclusão: Rejeita H0 -> Efeitos Fixos é preferido.")
    else: print("Conclusão: Não rejeita H0 -> Efeitos Aleatórios é preferido.")

    print("\n" + "="*80)
    print("TESTE DE RAIZ UNITÁRIA EM PAINEL (Fisher-ADF)")
    print("="*80)
    f_stat, f_pval = fisher_adf_test(endog)
    print("Variável dependente Nível (pib):")
    print(f"Estatística Fisher: {f_stat:.4f} | P-valor: {f_pval:.4f}")
    if f_pval < 0.05: print("Conclusão: Rejeita H0 -> Pelo menos uma série é estacionária.")
    else: print("Conclusão: Não rejeita H0 -> As séries possuem raiz unitária.")

    f_stat_ln, f_pval_ln = fisher_adf_test(endog_ln)
    print("\nVariável dependente LOG (ln_pib):")
    print(f"Estatística Fisher: {f_stat_ln:.4f} | P-valor: {f_pval_ln:.4f}")
    if f_pval_ln < 0.05: print("Conclusão: Rejeita H0 -> Pelo menos uma série é estacionária.")
    else: print("Conclusão: Não rejeita H0 -> As séries possuem raiz unitária.")

if __name__ == "__main__":
    df = load_and_prepare_data()
    if df is not None:
        fe_res, re_res, fe_res_ln, re_res_ln = run_regressions(df)
        run_diagnostics(df, fe_res, re_res, fe_res_ln, re_res_ln)
