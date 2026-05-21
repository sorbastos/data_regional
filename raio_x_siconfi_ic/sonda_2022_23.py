import requests
import pandas as pd

# Configuração para ver o texto completo
pd.set_option('display.max_colwidth', None)

def sondar_2022_2023():
    print("--- SONDA DE CÓDIGOS: 2020 e 2021 ---")
    id_ente = "5107909" # Sinop-MT (Nossa cobaia padrão)
    anos = [2020, 2021]
    
    for ano in anos:
        print(f"\n{'='*20} ANO {ano} {'='*20}")
        url = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
        params = {
            "an_exercicio": ano,
            "id_ente": id_ente,
            "no_anexo": "DCA-Anexo I-C"
        }
        
        try:
            r = requests.get(url, params=params, timeout=10)
            items = r.json().get('items', [])
            
            if not items:
                print(f"ALERTA: Nenhuma linha retornada para {ano}.")
                continue
                
            # Filtra linhas com valor > 0 para limpar a visualização
            # Procura qualquer coluna que tenha "Realizada" no nome (para evitar erros de nome exato)
            dados_uteis = []
            for item in items:
                coluna = item.get('coluna', '')
                if "Realizada" in coluna or "Arrecadada" in coluna:
                    valor = item.get('valor', 0)
                    conta = item.get('conta', '')
                    
                    if valor > 0 and conta.startswith("1.7."):
                        # Filtra Transf da União (1.7.1...)
                        if "1.7.1." in conta:
                            # Tenta pegar as contas principais (com final .0.0)
                            if conta.endswith(".0.0") or conta.endswith(".00.00"):
                                dados_uteis.append(f"[UNIÃO]  {conta}")
                                
                        # Filtra Transf dos Estados (1.7.2...) - só para garantir
                        if "1.7.2." in conta:
                            if conta.endswith(".0.0") or conta.endswith(".00.00"):
                                dados_uteis.append(f"[ESTADO] {conta}")

            # Imprime os resultados encontrados
            if not dados_uteis:
                print("Nenhuma transferência encontrada com valor > 0.")
            else:
                # Mostra os top 15 para não poluir demais, focando nos códigos
                for d in sorted(list(set(dados_uteis)))[:15]:
                    print(d)

        except Exception as e:
            print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    sondar_2022_2023()