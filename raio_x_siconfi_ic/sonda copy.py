import requests
import pandas as pd

def caçar_codigos_novos_2018():
    print("--- CAÇANDO CÓDIGOS NOVOS (ANO BASE 2018) ---")
    id_ente = "5107909" # Sinop-MT
    
    url = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
    params = {
        "an_exercicio": 2018,
        "id_ente": id_ente,
        "no_anexo": "DCA-Anexo I-C"
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        items = r.json().get('items', [])
        
        print(f"Total de linhas baixadas: {len(items)}")
        
        # Filtra apenas linhas com valores realizados > 0 para limpar a vista
        linhas_uteis = [i for i in items if "Receitas Brutas Realizadas" in i.get('coluna', '') and i.get('valor', 0) > 0]
        
        print("\n>>> 1. ONDE ESTÁ O TOTAL?")
        # Procura qualquer coisa que tenha "TOTAL" ou "RECEITAS (" no nome
        for item in linhas_uteis:
            conta = item.get('conta', '')
            if "TOTAL" in conta.upper() or "RECEITAS (" in conta.upper():
                print(f"   ACHEI: {conta}")

        print("\n>>> 2. ONDE ESTÃO OS ESTADOS?")
        # Procura transferências (1.7...) que falem de Estados
        for item in linhas_uteis:
            conta = item.get('conta', '')
            if conta.startswith("1.7.") and "ESTADOS" in conta.upper():
                # Mostra apenas as contas "mãe" (com final .0.00.00 ou .00.0.0) para não listar tudo
                if conta.count("0") >= 5: 
                    print(f"   ACHEI: {conta}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    caçar_codigos_novos_2018()