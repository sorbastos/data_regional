# Resultados da Estimação de Efeitos Fixos (Modelos em Nível)

## Modelo 2: Efeitos Fixos (Lag 1)
> **Critérios de Seleção:** AIC = 346584.31 | BIC = 353071.41

```text
                          PanelOLS Estimation Summary                           
================================================================================
Dep. Variable:                    pib   R-squared:                        0.5451
Estimator:                   PanelOLS   R-squared (Between):              0.9031
No. Observations:                7906   R-squared (Within):               0.5736
Date:                Wed, Sep 02 2026   R-squared (Overall):              0.8860
Time:                        14:38:29   Log-likelihood                -1.724e+05
Cov. Estimator:                Robust                                           
                                        F-statistic:                      1194.2
Entities:                         915   P-value                           0.0000
Avg Obs:                       8.6404   Distribution:                  F(7,6976)
Min Obs:                       4.0000                                           
Max Obs:                       9.0000   F-statistic (robust):             13.117
                                        P-value                           0.0000
Time periods:                       9   Distribution:                  F(7,6976)
Avg Obs:                       878.44                                           
Min Obs:                       793.00                                           
Max Obs:                       913.00                                           
                                                                                
                                  Parameter Estimates                                  
=======================================================================================
                     Parameter  Std. Err.     T-stat    P-value    Lower CI    Upper CI
---------------------------------------------------------------------------------------
desp_leg_adm_lag1      -2.3829     6.3832    -0.3733     0.7089     -14.896      10.130
desp_educ_cult_lag1     13.867     6.2981     2.2018     0.0277      1.5211      26.214
desp_saude_san_lag1    -4.1654     5.2245    -0.7973     0.4253     -14.407      6.0762
desp_hab_urb_lag1       4.5717     5.5859     0.8184     0.4131     -6.3784      15.522
desp_agri_lag1         -197.12     77.829    -2.5328     0.0113     -349.69     -44.553
transuniao_lag1         13.544     4.9043     2.7617     0.0058      3.9303      23.158
transest_lag1           28.949     6.5813     4.3986     0.0000      16.048      41.850
=======================================================================================

F-test for Poolability: 4.9530
P-value: 0.0000
Distribution: F(922,6976)

Included effects: Entity, Time
```

## Modelo 3: Efeitos Fixos (Lag 2)
> **Critérios de Seleção:** AIC = 308756.43 | BIC = 315122.69

```text
                          PanelOLS Estimation Summary                           
================================================================================
Dep. Variable:                    pib   R-squared:                        0.3740
Estimator:                   PanelOLS   R-squared (Between):              0.9617
No. Observations:                6994   R-squared (Within):               0.4067
Date:                Wed, Sep 02 2026   R-squared (Overall):              0.9347
Time:                        14:38:29   Log-likelihood                -1.534e+05
Cov. Estimator:                Robust                                           
                                        F-statistic:                      517.62
Entities:                         915   P-value                           0.0000
Avg Obs:                       7.6437   Distribution:                  F(7,6065)
Min Obs:                       3.0000                                           
Max Obs:                       8.0000   F-statistic (robust):             6.3188
                                        P-value                           0.0000
Time periods:                       8   Distribution:                  F(7,6065)
Avg Obs:                       874.25                                           
Min Obs:                       777.00                                           
Max Obs:                       911.00                                           
                                                                                
                                  Parameter Estimates                                  
=======================================================================================
                     Parameter  Std. Err.     T-stat    P-value    Lower CI    Upper CI
---------------------------------------------------------------------------------------
desp_leg_adm_lag2      -3.3655     8.2284    -0.4090     0.6825     -19.496      12.765
desp_educ_cult_lag2     11.751     7.8023     1.5060     0.1321     -3.5447      27.046
desp_saude_san_lag2    -3.2717     6.9109    -0.4734     0.6359     -16.820      10.276
desp_hab_urb_lag2      -0.1309     9.5494    -0.0137     0.9891     -18.851      18.589
desp_agri_lag2         -233.34     101.76    -2.2929     0.0219     -432.84     -33.846
transuniao_lag2         13.444     6.0478     2.2230     0.0263      1.5884      25.300
transest_lag2           26.937     10.573     2.5478     0.0109      6.2108      47.664
=======================================================================================

F-test for Poolability: 3.8721
P-value: 0.0000
Distribution: F(921,6065)

Included effects: Entity, Time
```
