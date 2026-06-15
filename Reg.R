# ==============================================================================
# SETUP: CARREGAR PACOTES E PREPARAR AMBIENTE
# ==============================================================================
# install.packages(c("readxl", "plm", "dplyr", "lmtest", "sandwich", "car"))
suppressPackageStartupMessages({
  library(plm)
  library(readxl)
  library(dplyr)
  library(lmtest)
  library(sandwich)
  library(car) # Para VIF
})

# ==============================================================================
# 1. CARREGAMENTO DOS DADOS
# ==============================================================================
cat("\n=========================================================\n")
cat("1. CARREGANDO O PAINEL DE DADOS\n")
cat("=========================================================\n")
df_bruto <- read_excel("Painel_Completo_2013_2023.xlsx")

# ==============================================================================
# 2. PREPARAÇÃO E AGRUPAMENTO DAS VARIÁVEIS
# ==============================================================================
df_painel <- df_bruto %>%
  mutate(
    # Agrupar despesas reais (tratando NA como 0 para a soma, depois pode ter NA de novo se a base for filtrada)
    desp_leg_adm   = ifelse(is.na(d_leg_r), 0, d_leg_r) + ifelse(is.na(d_adm_r), 0, d_adm_r),
    desp_educ_cult = ifelse(is.na(d_educ_r), 0, d_educ_r) + ifelse(is.na(d_cult_r), 0, d_cult_r),
    desp_saude_san = ifelse(is.na(d_saude_r), 0, d_saude_r) + ifelse(is.na(d_san_r), 0, d_san_r),
    desp_hab_urb   = ifelse(is.na(d_habit_r), 0, d_habit_r) + ifelse(is.na(d_urb_r), 0, d_urb_r),
    desp_agri      = d_agri_r,
    
    # Aplicar transformação (seno hiperbólico inverso, asinh)
    ln_pib_pc         = asinh(pib_pc),
    ln_transuniao     = asinh(transuniao_r),
    ln_desp_leg_adm   = asinh(desp_leg_adm),
    ln_desp_educ_cult = asinh(desp_educ_cult),
    ln_desp_saude_san = asinh(desp_saude_san),
    ln_desp_hab_urb   = asinh(desp_hab_urb),
    ln_desp_agri      = asinh(desp_agri),
    ln_transest       = asinh(transest_r)
  ) %>%
  filter(!is.na(ln_pib_pc)) # remover NAs na variável dependente

# ==============================================================================
# 3. DECLARAÇÃO DA ESTRUTURA DE PAINEL
# ==============================================================================
painel <- pdata.frame(df_painel, index = c("cod_ibge", "ano"))

# ==============================================================================
# 4. DEFINIÇÃO DA FÓRMULA DO MODELO
# ==============================================================================
modelo_ln <- ln_pib_pc ~ ln_transuniao + ln_desp_leg_adm + ln_desp_educ_cult + 
                          ln_desp_saude_san + ln_desp_hab_urb + ln_desp_agri + ln_transest

# ==============================================================================
# 5. ESTIMAÇÃO DOS MODELOS CLÁSSICOS (POLS, FE, RE)
# ==============================================================================
cat("\n=========================================================\n")
cat("5. ESTIMAÇÃO DOS MODELOS (POLS, FE, RE)\n")
cat("=========================================================\n")

# Pooled OLS (POLS)
pols_ln <- plm(modelo_ln, data = painel, model = "pooling")

# Efeitos Fixos (FE) - Twoways
fe_ln <- plm(modelo_ln, data = painel, model = "within", effect = "twoways")

# Efeitos Aleatórios (RE) - Twoways
re_ln <- plm(modelo_ln, data = painel, model = "random", effect = "twoways")

# --- Teste de Hausman ---
teste_hausman <- phtest(fe_ln, re_ln)
cat("--- TESTE DE HAUSMAN ---\n")
print(teste_hausman)
cat("Se p-valor < 0.05, rejeitamos H0 (preferimos Efeitos Fixos).\n")

# ==============================================================================
# 6. DIAGNÓSTICOS E TESTES DE ROBUSTEZ (PRESSUPOSTOS)
# ==============================================================================
cat("\n=========================================================\n")
cat("6. DIAGNÓSTICOS DO MODELO (TESTES DE PRESSUPOSTOS)\n")
cat("=========================================================\n")

# 6.1. Teste de Heterocedasticidade (Breusch-Pagan)
cat("\n--- Teste de Heterocedasticidade (Breusch-Pagan) ---\n")
teste_bp <- bptest(modelo_ln, data = painel, studentize = TRUE)
print(teste_bp)
cat("H0: Homocedasticidade. Se p-valor < 0.05, os resíduos são heterocedásticos.\n")

# 6.2. Teste de Autocorrelação Serial (Breusch-Godfrey/Wooldridge)
cat("\n--- Teste de Autocorrelação Serial (Breusch-Godfrey) ---\n")
teste_bg <- pbgtest(fe_ln)
print(teste_bg)
cat("H0: Não há autocorrelação serial. Se p-valor < 0.05, há autocorrelação.\n")

# 6.3. Teste de Dependência Seccional Cruzada (Pesaran CD)
cat("\n--- Teste de Dependência Seccional Cruzada (Pesaran CD) ---\n")
# Usamos tryCatch pois painéis desbalanceados podem gerar erro
tryCatch({
  teste_cd <- pcdtest(fe_ln, test = c("cd"))
  print(teste_cd)
  cat("H0: Não há dependência transversal. Se p-valor < 0.05, os resíduos são correlacionados entre indivíduos.\n")
}, error = function(e) {
  cat("Teste CD de Pesaran falhou (possivelmente devido a painel muito desbalanceado ou tempo curto):", e$message, "\n")
})

# 6.4. Teste de Multicolinearidade (VIF)
cat("\n--- Teste de Multicolinearidade (VIF) ---\n")
vif_resultado <- car::vif(lm(modelo_ln, data = df_painel))
print(vif_resultado)
cat("Valores de VIF > 10 indicam problemas severos de multicolinearidade.\n")

# ==============================================================================
# 7. MODELO FINAL COM ERROS ROBUSTOS (ARELLANO / DRISCOLL-KRAAY)
# ==============================================================================
cat("\n=========================================================\n")
cat("7. MODELO FINAL COM ERROS ROBUSTOS\n")
cat("=========================================================\n")
cat("Como o teste de Hausman geralmente indica Efeitos Fixos e é comum encontrar\n")
cat("heterocedasticidade e autocorrelação em painéis longos, utilizamos erros\n")
cat("robustos de Arellano.\n\n")

resumo_robusto <- coeftest(fe_ln, vcov = vcovHC(fe_ln, method = "arellano", type = "HC1"))
print(resumo_robusto)

# ==============================================================================
# 8. TESTE DE ROBUSTEZ: MODELO COM DEFASAGENS (Lags)
# ==============================================================================
cat("\n=========================================================\n")
cat("8. TESTE DE ROBUSTEZ: INCLUINDO DEFASAGENS (LAGS)\n")
cat("=========================================================\n")
cat("Incluindo defasagens (lag 1) das variáveis independentes para mitigar\n")
cat("potencial endogeneidade e causalidade reversa.\n")

# Modelo com Lags (Defasagem temporal)
modelo_lag <- ln_pib_pc ~ lag(ln_transuniao, 1) + lag(ln_desp_leg_adm, 1) + 
                          lag(ln_desp_educ_cult, 1) + lag(ln_desp_saude_san, 1) + 
                          lag(ln_desp_hab_urb, 1) + lag(ln_desp_agri, 1) + lag(ln_transest, 1)

fe_lag <- plm(modelo_lag, data = painel, model = "within", effect = "twoways")
resumo_lag_robusto <- coeftest(fe_lag, vcov = vcovHC(fe_lag, method = "arellano", type = "HC1"))
print(resumo_lag_robusto)

# ==============================================================================
# 9. TESTES DE RAIZ UNITÁRIA (ESTACIONARIEDADE)
# ==============================================================================
cat("\n=========================================================\n")
cat("9. TESTES DE ESTACIONARIEDADE (RAIZ UNITÁRIA: MADDALA-WU)\n")
cat("=========================================================\n")

run_purtest <- function(variable, var_name) {
  cat(paste("\n--- Teste para:", var_name, "---\n"))
  tryCatch({
    test_result <- purtest(variable, test = "madwu", exo = "intercept", lags = "AIC")
    cat("Estatística MW:", test_result$statistic$statistic, "| p-valor:", test_result$statistic$p.value, "\n")
  }, error = function(e) {
    cat("   ERRO ao testar a variável:", e$message, "\n")
  })
}

run_purtest(painel$ln_pib_pc, "ln_pib_pc")
run_purtest(painel$ln_transuniao, "ln_transuniao")
run_purtest(painel$ln_desp_leg_adm, "ln_desp_leg_adm")
run_purtest(painel$ln_desp_educ_cult, "ln_desp_educ_cult")
run_purtest(painel$ln_desp_saude_san, "ln_desp_saude_san")
run_purtest(painel$ln_desp_hab_urb, "ln_desp_hab_urb")
run_purtest(painel$ln_desp_agri, "ln_desp_agri")
run_purtest(painel$ln_transest, "ln_transest")

cat("\n=================== ANÁLISE CONCLUÍDA ===================\n")
