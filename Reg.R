# Instale os pacotes caso ainda não os tenha:
# install.packages(c("readxl", "plm", "dplyr", "lmtest", "sandwich"))

library(readxl)
library(plm)
library(dplyr)
library(lmtest)
library(sandwich)

# ==============================================================================
# 1. CARREGAMENTO DOS DADOS
# ==============================================================================
print("Carregando o painel de dados...")
df_bruto <- read_excel("Painel_Completo_2013_2023.xlsx")
View(df_bruto)
# ==============================================================================
# 2. PREPARAÇÃO E AGRUPAMENTO DAS VARIÁVEIS
# ==============================================================================
# Agrupando as funções de despesa conforme o escopo do modelo econométrico.
# Utilizando as variáveis reais (_r) que já estão a preços constantes de 2023.

df_painel <- df_bruto %>%
  mutate(
    # Passo A: Agrupar as despesas reais
    desp_leg_adm   = d_leg_r + d_adm_r,
    desp_educ_cult = d_educ_r + d_cult_r,
    desp_saude_san = d_saude_r + d_san_r,
    desp_hab_urb   = d_habit_r + d_urb_r,
    desp_agri      = d_agri_r,
  )
    # Passo B: Aplicar o logaritmo natural (ln)
    # Somamos 1 para evitar o erro de log(0) = -Infinito nas contas financeiras
    df_painel <- df_painel %>%
  mutate(
    ln_pib_pc         = asinh(pib_pc + 1),
    ln_pib            = asinh(pib_r + 1),
    ln_transuniao     = asinh(transuniao_r + 1),
    ln_desp_leg_adm   = asinh(desp_leg_adm + 1),
    ln_desp_educ_cult = asinh(desp_educ_cult + 1),
    ln_desp_saude_san = asinh(desp_saude_san + 1),
    ln_desp_hab_urb   = asinh(desp_hab_urb + 1),
    ln_desp_agri      = asinh(desp_agri + 1),
    ln_transest       = asinh(transest_r + 1),
    ln_rectrib        = asinh(rectrib_r + 1),
    ln_pop             = asinh(pop + 1),
    ln_transest         = asinh(transest_r + 1)
  )



# ==============================================================================
# 3. DECLARAÇÃO DA ESTRUTURA DE PAINEL
# ==============================================================================
# Informa ao R quem são os indivíduos (cod_ibge) e o tempo (ano)
painel <- pdata.frame(df_painel, index = c("cod_ibge", "ano"))
View(painel)
# ==============================================================================
# 4. DEFINIÇÃO DA FÓRMULA DO MODELO
# ==============================================================================
# PIB Real em função das Transferências da União e das categorias de despesa
modelo_ln <- ln_pib_pc ~ ln_transuniao + ln_desp_leg_adm + ln_desp_educ_cult + 
                          ln_desp_saude_san + ln_desp_hab_urb + ln_desp_agri + ln_transest

modelo_base <- pib_r ~ transuniao_r + desp_leg_adm + desp_educ_cult + 
                          desp_saude_san + desp_hab_urb + desp_agri
# ==============================================================================
# 5. ESTIMAÇÃO DOS MODELOS CLÁSSICOS
# ==============================================================================
print("Estimando os modelos (POLS, Efeitos Fixos e Efeitos Aleatórios)...")

# Pooled OLS (POLS) - Ignora a heterogeneidade dos municípios
pols_ln <- plm(modelo_ln, data = painel, model = "pooling")
pols <- plm(modelo_base, data = painel, model = "pooling")
summary(pols_ln)
summary(pols)

# Efeitos Fixos (Within) - Controla características não observáveis invariantes no tempo
fe_ln <- plm(modelo_ln, data = painel, model = "within", effect = "twoways") # Controla efeitos individuais e temporais
fe <- plm(modelo_base, data = painel, model = "within", effect = "twoways")
summary(fe_ln)
summary(fe)

# Efeitos Aleatórios (Random)
re_ln <- plm(modelo_ln, data = painel, model = "random") # Controla efeitos individuais e temporais
re <- plm(modelo_base, data = painel, model = "random", effect = "twoways")
summary(re_ln)
summary(re)

# ==============================================================================
# 6. TESTES DE ESPECIFICAÇÃO
# ==============================================================================
# Teste de Hausman: Compara Efeitos Fixos vs Efeitos Aleatórios
# H0: O modelo de Efeitos Aleatórios é consistente e mais eficiente.
# H1: O modelo de Efeitos Aleatórios é inconsistente, usar Efeitos Fixos.
teste_hausman <- phtest(fe_ln, re_ln)
print(teste_hausman)
print("---------------------------------------------------------")
print("TESTE DE HAUSMAN")
print("---------------------------------------------------------")
print(teste_hausman)

# ==============================================================================
# 7. RESULTADOS COM ERROS ROBUSTOS
# ==============================================================================
print("---------------------------------------------------------")
print("RESULTADOS DO MODELO DE EFEITOS FIXOS (COM ERROS ROBUSTOS HAC)")
print("---------------------------------------------------------")

# Em painéis municipais, problemas de heterocedasticidade e autocorrelação 
# são quase uma certeza. A função vcovHC aplica a correção de Arellano.
resumo_robusto <- coeftest(fe_ln, vcov = vcovHC(fe_ln, method = "arellano", type = "HC1"))
print(resumo_robusto)


# ==============================================================================
# TESTES DE RAIZ UNITÁRIA EM PAINEL (FISHER-ADF / MADDALA-WU)
# ==============================================================================
print("Rodando Testes de Estacionariedade (Fisher-ADF)...")

# A função purtest() exige que a variável seja chamada diretamente do objeto pdata.frame.
# test = "madwu" chama o equivalente ao Augmented Dickey-Fuller para painéis.
# exo = "intercept" controla o intercepto na tendência.
# lags = "AIC" usa o Critério de Akaike para definir defasagens automaticamente.

# 1. Teste para o PIB (Variável Dependente)
teste_pib <- purtest(painel$ln_pib, test = "madwu", exo = "intercept", lags = "AIC")
print("--- Resultado para o ln_pib ---")
summary(teste_pib)

# 2. Teste para Despesas com Educação e Cultura
teste_educ <- purtest(painel$ln_desp_educ_cult, test = "madwu", exo = "intercept", lags = "AIC")
print("--- Resultado para ln_desp_educ_cult ---")
summary(teste_educ)

# 3. Teste para Transferências da União
teste_transf <- purtest(painel$ln_transuniao, test = "madwu", exo = "intercept", lags = "AIC")
print("--- Resultado para ln_transuniao ---")
summary(teste_transf)
