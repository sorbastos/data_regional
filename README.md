# Análise de Dados Regionais: Painel Fiscal Municipal (2013-2023)

Este projeto consiste em um pipeline de dados completo para a construção de um painel de dados municipais, focando nas regiões Norte e Centro-Oeste do Brasil. O objetivo é coletar, tratar e consolidar informações fiscais e macroeconômicas para permitir análises econométricas sobre o impacto de gastos e transferências governamentais no desenvolvimento local.

## 🚀 Como Executar o Pipeline

Para reproduzir o projeto do zero, siga a ordem de execução abaixo. Os scripts são projetados para serem executados em sequência, onde cada um gera um artefato que alimenta o próximo.

1.  **Instale as dependências** Python e R (veja a seção de pré-requisitos).

2.  **Execute os scripts Python** na ordem correta para construir a base de dados:
    ```bash
    # 1. Coleta dados de PIB (IBGE) e IPCA (BCB)
    python pib.py

    # 2. Coleta dados fiscais de 2014 a 2023 via API
    python siconfi_v10.py

    # 3. Adiciona os dados fiscais históricos de 2013 (via CSV)
    python siconfi_2013.py

    # 4. Unifica tudo, deflaciona e gera o painel final em Excel
    python painel.py
    ```

3.  **Execute a análise econométrica** no R, utilizando o painel gerado:
    - Abra o arquivo `Reg.R` no RStudio e execute o script.

## 🔧 Pré-requisitos

- **Python 3.8+** com as bibliotecas: `pandas`, `sidrapy`, `requests`, `openpyxl`, `tqdm`.
- **R 4.0+** com os pacotes: `readxl`, `plm`, `dplyr`, `lmtest`, `sandwich`.
- Os arquivos `receitas_2013.csv` e `despesas_2013.csv` devem estar na raiz do projeto para a execução do `siconfi_2013.py`.

##  Estrutura do Projeto e Arquivos

| Arquivo / Diretório | Descrição do Componente |
| :--- | :--- |
| `🐍 pib.py` | **ETL 1:** Extrai o PIB municipal (IBGE) e o índice de inflação IPCA (Banco Central), salvando-os no banco `pib_regional.db`. |
| `🐍 siconfi_v10.py` | **ETL 2:** Coleta dados fiscais (receitas, despesas, população) de 2014 a 2023 via API do Siconfi para os municípios definidos em `pib.py`. Salva em `siconfi_v10_final.db`. |
| `🐍 siconfi_2013.py` | **ETL 3:** Processa e anexa os dados fiscais de 2013 (a partir de arquivos CSV) ao banco de dados `siconfi_v10_final.db`. |
| `🐍 painel.py` | **ETL Final & Modelagem:** Unifica as bases de dados, deflaciona os valores monetários para preços de 2023, calcula indicadores per capita e exporta o painel consolidado `Painel_Completo_2013_2023.xlsx`. |
| ` R  Reg.R` | **Análise Econométrica:** Carrega o painel final e executa os modelos de dados em painel (Efeitos Fixos, Aleatórios), testes de especificação (Hausman) e testes de raiz unitária. |
| `📁 raio_x_siconfi_ic/` | Diretório com scripts de diagnóstico usados para investigar e validar as mudanças nos códigos de contas fiscais do Siconfi ao longo dos anos. |
| `📄 *.csv` | Arquivos de dados brutos para o ano de 2013, que servem de entrada para o script `siconfi_2013.py`. |
