import requests
import pandas as pd
import sqlite3
import time

def baixar_credito_rural_api():
    print("=========================================================")
    print("EXTRAÇÃO RESILIENTE: CRÉDITO RURAL (API BCB - OLINDA)")
    print("=========================================================")
    
    # Criamos um banco separado só para o crédito bruto
    db_name = "credito_rural_bruto.db"
    conn = sqlite3.connect(db_name)
    
    # Endpoint do SICOR na API Olinda (Custeio, Investimento, Comercialização)
    url_base = "https://olinda.bcb.gov.br/olinda/servico/SICOR/versao/v2/odata/CusteioInvestimentoComercializacaoIndustrializacao"
    
    anos = list(range(2013, 2024))
    
    for ano in anos:
        print(f"\n--- Iniciando extração do ano {ano} ---")
        skip = 0
        top = 10000  # Limite máximo imposto pelo BCB
        tem_dados = True
        
        while tem_dados:
            # Filtramos pelo ano de emissão do contrato
            url = f"{url_base}?$filter=AnoEmissao eq '{ano}'&$top={top}&$skip={skip}&$format=json"
            sucesso_na_requisicao = False
            tentativas = 0
            
            # O laço do "ATÉ DAR CERTO"
            while not sucesso_na_requisicao:
                try:
                    tentativas += 1
                    print(f"[{ano}] Buscando registros {skip} a {skip+top} (Tentativa {tentativas})...")
                    
                    # Timeout de 60 segundos evita que o script fique travado infinitamente
                    resposta = requests.get(url, timeout=60)
                    
                    if resposta.status_code == 200:
                        dados_json = resposta.json().get('value', [])
                        
                        if not dados_json:
                            print(f"[{ano}] Fim dos dados para este ano.")
                            tem_dados = False
                            sucesso_na_requisicao = True
                            break
                        
                        # Converte a página para DataFrame
                        df = pd.DataFrame(dados_json)
                        
                        # Padroniza as colunas e renomeia chaves importantes para o seu projeto
                        df.columns = [c.lower() for c in df.columns]
                        df.rename(columns={
                            'cdmunicipioibge': 'cod_ibge',
                            'vlrmutuo': 'valor_credito_nominal',
                            'anoemissao': 'ano'
                        }, inplace=True, errors='ignore')
                        
                        # Mantemos apenas as colunas essenciais para o seu modelo poupar espaço
                        colunas_desejadas = ['cod_ibge', 'ano', 'valor_credito_nominal']
                        colunas_presentes = [c for c in colunas_desejadas if c in df.columns]
                        df = df[colunas_presentes]
                        
                        # Salva o pacote imediatamente no banco
                        df.to_sql(f"credito_{ano}", conn, if_exists='append', index=False)
                        
                        print(f"   -> ✅ {len(df)} registros salvos!")
                        skip += top
                        sucesso_na_requisicao = True
                        
                        # Pausa educada de 1 segundo para não sofrer bloqueio do BCB
                        time.sleep(1)
                        
                    elif resposta.status_code == 429:
                        print(f"   -> ⚠️ Aviso: Muitas requisições (Erro 429). Aguardando 15 segundos...")
                        time.sleep(15)
                    else:
                        print(f"   -> ❌ Erro {resposta.status_code}. Retentando em 5 segundos...")
                        time.sleep(5)
                        
                except Exception as e:
                    print(f"   -> ⚠️ Falha de conexão: {e}. Retentando em 10 segundos...")
                    time.sleep(10)
                    
    conn.close()
    print("\n✅ Extração completa concluída com sucesso!")

if __name__ == "__main__":
    baixar_credito_rural_api()