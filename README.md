<<<<<<< HEAD
To vendo ainda o que vou escrever aqui pequeno gafanhoto(em construção)
=======
To vendo ainda o que vou escrever aqui pequeno gafanhoto
>>>>>>> b5cc7f0cacd60156057f29e768c26c6ad694918f

## 📂 Estrutura do Projeto e Arquivos

<<<<<<< HEAD
| Arquivo / Diretório | Descrição do Componente |
| :--- | :--- |
| `📁 Raio_x_siconfi_ic/` | Diretório contendo auditorias e análises de consistência, documentando o racional das alterações realizadas nos códigos de classificação de receitas e transferências. |
| `🐍 siconfi.py` | **Script de Extração:** Conecta-se à API do Siconfi (Tesouro Nacional) para automatizar a coleta de dados brutos de população, receitas e gastos públicos referentes ao período de 2014 a 2023. |
| `🐍 pib.py` | **Script de Dados Macroeconômicos:** Responsável por consumir a API do IBGE (para dados de PIB) e a API do Banco Central do Brasil (para o índice de inflação IPCA). |
| `🐍 siconfi_2013.py` | **Pipeline ETL Histórico:** Processa especificamente a base de dados do ano de 2013, realizando a limpeza e inserção no banco de dados estruturado (`siconfi_v10_final.db`). |
| `🐍 painel.py` | **Script Principal de ETL e Modelagem:** Unifica todas as bases coletadas. Aplica regras de negócio essenciais, como a deflação de gastos e receitas pelo IPCA (trazendo a preços de 2023), cálculo do PIB *per capita*, gastos *per capita* e a geração dos indicadores fiscais (Índices de Autonomia e Dependência). |
| `📄 Arquivos .csv` | Bases brutas locais (ex: `receitas_2013.csv` e `despesas_2013.csv`). *Nota: Estes arquivos estão mapeados no `.gitignore` devido ao tamanho, mas são gerados/necessários para a execução inicial do pipeline localmente.* |
=======
📂 Arquivos do Projeto
siconfi.py: Conectado na API do Tesouro Nacional (Siconfi) para baixar os dados brutos.

Raio_x_siconfi_ic: pasta com algumas autditorias, pois alguns codigos do de receitas e transferencias sofreram alterações.
pib.py: baixa os dados de PIB da API do IBGE e o IPCA da API do Bacen.
Siconfi.py: baixa os dados de população, gastos e receitas da API do Siconfi dos anos de 2014 a 2023
siconfi_2013.py: Script de processamento (ETL). 
painel.py: Script de processamento (ETL). Unifica as bases, deflaciona os valores de gastos e receitas pelo IPCA (a preços de 2023), calcula o PIB per capita e gera os indicadores fiscais (Autonomia e Dependência) e gastos per capita.

>>>>>>> b5cc7f0cacd60156057f29e768c26c6ad694918f
