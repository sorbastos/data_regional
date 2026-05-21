import requests
import pandas as pd

def diagnostico_profundo():
    print("--- DIAGNÓSTICO PROFUNDO (MUDANÇA PCASP) ---")
    id_ente = "5107909" # Sinop-MT
    
    anos = [2014, 2020]
    
    for ano in anos:
        print(f"\n{'='*50} ANO {ano} {'='*50}")
        url = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
        params = {
            "an_exercicio": ano,
            "id_ente": id_ente,
            "no_anexo": "DCA-Anexo I-C"
        }
        
        try:
            r = requests.get(url, params=params, timeout=10)
            items = r.json().get('items', [])
            
            # Listas para armazenar o que acharmos
            lista_impostos = []
            lista_transf = []
            
            for item in items:
                # Foca apenas na coluna de valor realizado
                if "Receitas Brutas Realizadas" in item.get('coluna', ''):
                    conta = item.get('conta', '')
                    valor = item.get('valor', 0)
                    
                    # Se o valor for zero, ignoramos (para limpar a lista)
                    if valor == 0:
                        continue
                        
                    # Pega tudo que começa com 1.1 (Impostos)
                    if conta.startswith("1.1."):
                        # Pega apenas contas "raiz" (com menos pontos ou terminadas em 00)
                        # para não poluir com sub-sub-contas
                        if conta.count("00") >= 2:
                            lista_impostos.append(conta)
                            
                    # Pega tudo que começa com 1.7 (Transferências)
                    if conta.startswith("1.7."):
                        # Queremos ver União e Estados
                        if "União" in conta or "Estados" in conta:
                            # Filtra as contas principais
                            if conta.count("00") >= 2:
                                lista_transf.append(conta)

            # --- IMPRIMIR RESULTADOS ---
            print(f">>> IMPOSTOS (Começam com 1.1) em {ano}:")
            if not lista_impostos:
                print("   (Nenhum registro encontrado com valor > 0)")
            for i in sorted(list(set(lista_impostos)))[:10]: # Top 10
                print(f"   {i}")

            print(f"\n>>> TRANSFERÊNCIAS (Começam com 1.7) em {ano}:")
            if not lista_transf:
                print("   (Nenhum registro encontrado com valor > 0)")
            for i in sorted(list(set(lista_transf)))[:10]: # Top 10
                print(f"   {i}")
                
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    diagnostico_profundo()