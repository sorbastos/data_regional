To vendo ainda o que vou escrever aqui pequeno gafanhoto


📂 Arquivos do Projeto
siconfi.py: Conectado na API do Tesouro Nacional (Siconfi) para baixar os dados brutos.

Raio_x_siconfi_ic: pasta com algumas autditorias, pois alguns codigos do de receitas e transferencias sofreram alterações.
pib.py: baixa os dados de PIB da API do IBGE e o IPCA da API do Bacen.
Siconfi.py: baixa os dados de população, gastos e receitas da API do Siconfi dos anos de 2014 a 2023
siconfi_2013.py: Script de processamento (ETL). 
painel.py: Script de processamento (ETL). Unifica as bases, deflaciona os valores de gastos e receitas pelo IPCA (a preços de 2023), calcula o PIB per capita e gera os indicadores fiscais (Autonomia e Dependência) e gastos per capita.

