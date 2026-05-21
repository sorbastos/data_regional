To vendo ainda o que vou escrever aqui pequeno gafanhoto


📂 Arquivos do Projeto
siconfi.py: Conectado na API do Tesouro Nacional (Siconfi) para baixar os dados brutos.

auditoria.py: Ferramenta de validação. Verifique a integridade dos arquivos baixados para garantir que não haja anos faltantes.

painel.py: Script de processamento (ETL). Unifica as bases, deflaciona os valores de gastos e receitas pelo IPCA (a preços de 2023), calcula o PIB per capita e gera os indicadores fiscais (Autonomia e Dependência).