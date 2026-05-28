# ==============================================================================
# SETUP: CARREGAR PACOTES
# ==============================================================================
# Se for a primeira vez, instale os pacotes:
# install.packages(c("readxl", "plm", "dplyr", "lmtest", "sandwich"))
library(plm)
library(readxl)
library(dplyr)
library(lmtest)
library(sandwich)


# ==============================================================================
# 1. CARREGAMENTO DOS DADOS
# ==============================================================================
print("Carregando o painel de dados...")
df_bruto <- read_excel("Painel_Completo_2013_2023.xlsx")


# ==============================================================================
# 2. PREPARAÇÃO E AGRUPAMENTO DAS VARIÁVEIS
# ==============================================================================
# Agrupando as funções de despesa conforme o escopo do modelo econométrico.
# Utilizando as variáveis reais (_r) que já estão a preços constantes de 2023.
df_painel <- df_bruto %>%
  mutate(
    # Agrupar despesas reais
    desp_leg_adm   = d_leg_r + d_adm_r,
    desp_educ_cult = d_educ_r + d_cult_r,
    desp_saude_san = d_saude_r + d_san_r,
    desp_hab_urb   = d_habit_r + d_urb_r,
    desp_agri      = d_agri_r,
    
    # Aplicar transformação (seno hiperbólico inverso, asinh)
    # asinh(x) é uma alternativa ao log(x) que lida bem com valores zero.
    ln_pib_pc         = asinh(pib_pc),
    ln_transuniao     = asinh(transuniao_r),
    ln_desp_leg_adm   = asinh(desp_leg_adm),
    ln_desp_educ_cult = asinh(desp_educ_cult),
    ln_desp_saude_san = asinh(desp_saude_san),
    ln_desp_hab_urb   = asinh(desp_hab_urb),
    ln_desp_agri      = asinh(desp_agri),
    ln_transest       = asinh(transest_r)
  )

# ==============================================================================
# 3. DECLARAÇÃO DA ESTRUTURA DE PAINEL
# ==============================================================================
# Informa ao R quem são os indivíduos (cod_ibge) e o tempo (ano)
painel <- pdata.frame(df_painel, index = c("cod_ibge", "ano"))


# ==============================================================================
# 4. ESTIMAÇÃO E SELEÇÃO DO MODELO
# ==============================================================================

# --- 4.1. Definição da Fórmula ---
# PIB per capita em função das Transferências da União e das categorias de despesa
modelo_ln <- ln_pib_pc ~ ln_transuniao + ln_desp_leg_adm + ln_desp_educ_cult + 
                          ln_desp_saude_san + ln_desp_hab_urb + ln_desp_agri + ln_transest

modelo_base <- pib_r ~ transuniao_r + desp_leg_adm + desp_educ_cult + 
                          desp_saude_san + desp_hab_urb + desp_agri
# ==============================================================================
# 5. ESTIMAÇÃO DOS MODELOS CLÁSSICOS
# ==============================================================================
print("Estimando os modelos (POLS, Efeitos Fixos e Efeitos Aleatórios)...")

# Pooled OLS (POLS) - Ignora a heterogeneidade dos municípios
# Pooled OLS (POLS)
pols_ln <- plm(modelo_ln, data = painel, model = "pooling")
pols <- plm(modelo_base, data = painel, model = "pooling")
summary(pols_ln)
summary(pols)

# Efeitos Fixos (Within) - Controla características não observáveis invariantes no tempo
fe_ln <- plm(modelo_ln, data = painel, model = "within", effect = "twoways") # Controla efeitos individuais e temporais
fe <- plm(modelo_base, data = painel, model = "within", effect = "twoways")
summary(fe_ln)
summary(fe)
# Efeitos Fixos (FE) - Controla características não observáveis de cada município
fe_ln <- plm(modelo_ln, data = painel, model = "within", effect = "twoways")

# Efeitos Aleatórios (Random)
re_ln <- plm(modelo_ln, data = painel, model = "random") # Controla efeitos individuais e temporais
re <- plm(modelo_base, data = painel, model = "random", effect = "twoways")
summary(re_ln)
summary(re)
# Efeitos Aleatórios (RE)
re_ln <- plm(modelo_ln, data = painel, model = "random", effect = "twoways")

# --- 4.3. Teste de Hausman (Efeitos Fixos vs. Aleatórios) ---
# H0: Efeitos Aleatórios é o modelo preferível (consistente e eficiente).
# H1: Efeitos Fixos é o modelo preferível (Efeitos Aleatórios é inconsistente).
teste_hausman <- phtest(fe_ln, re_ln)

cat("\n\n=========================================================\n")
cat("               TESTE DE HAUSMAN\n")
cat("=========================================================\n")
print(teste_hausman)
cat("Interpretação: Se o p-valor for < 0.05, rejeitamos H0 e escolhemos o modelo de Efeitos Fixos.\n\n")


# ==============================================================================
# 5. RESULTADO FINAL COM ERROS-PADRÃO ROBUSTOS
# ==============================================================================
# Com base no teste de Hausman, apresentamos o modelo de Efeitos Fixos (FE)
# corrigido para heterocedasticidade e autocorrelação (erros robustos de Arellano).
resumo_robusto <- coeftest(fe_ln, vcov = vcovHC(fe_ln, method = "arellano", type = "HC1"))

cat("\n=========================================================\n")
cat("      MODELO FINAL: EFEITOS FIXOS (ERROS ROBUSTOS)\n")
cat("=========================================================\n")
print(resumo_robusto)


# ==============================================================================
# 6. TESTES DE RAIZ UNITÁRIA EM PAINEL (MADDALA-WU)
# ==============================================================================
# H0: Todas as séries possuem raiz unitária (não são estacionárias).
# H1: Pelo menos uma série é estacionária.
# Um p-valor baixo (< 0.05) sugere que podemos rejeitar H0.

cat("\n\n=========================================================\n")
cat("         TESTES DE ESTACIONARIEDADE (RAIZ UNITÁRIA)\n")
cat("=========================================================\n")

# Função auxiliar para rodar o teste e imprimir o resultado de forma limpa
run_purtest <- function(variable, var_name) {
  cat(paste("\n--- Teste para:", var_name, "---\n"))
  # Usamos tryCatch para o script não parar caso uma variável tenha problemas
  tryCatch({
    test_result <- purtest(variable, test = "madwu", exo = "intercept", lags = "AIC")
    print(summary(test_result))
  }, error = function(e) {
    cat("   ERRO ao testar a variável:", e$message, "\n")
  })
}

# Executando os testes para as variáveis do modelo
run_purtest(painel$ln_pib_pc, "ln_pib_pc")
run_purtest(painel$ln_transuniao, "ln_transuniao")
run_purtest(painel$ln_desp_leg_adm, "ln_desp_leg_adm")
run_purtest(painel$ln_desp_educ_cult, "ln_desp_educ_cult")
run_purtest(painel$ln_desp_saude_san, "ln_desp_saude_san")
run_purtest(painel$ln_desp_hab_urb, "ln_desp_hab_urb")
run_purtest(painel$ln_desp_agri, "ln_desp_agri")
run_purtest(painel$ln_transest, "ln_transest")
