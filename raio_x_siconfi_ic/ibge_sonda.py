import requests

def verificar_anos_disponiveis():
    # Tabela 5938: Produto Interno Bruto dos Municípios (Série 2010 em diante)
    url_metadata = "https://servicodados.ibge.gov.br/api/v3/agregados/5938/metadados"
    
    print("⏳ Consultando o IBGE...")
    
    try:
        response = requests.get(url_metadata)
        response.raise_for_status() # Garante que não deu erro 404/500
        dados = response.json()
        
        # O IBGE guarda os anos dentro da chave 'periodos'
        lista_periodos = dados.get('periodos', [])
        
        # Extrai apenas o número do ano (campo 'id')
        anos = [p['id'] for p in lista_periodos]
        
        if anos:
            print("\n✅ Consulta realizada com sucesso!")
            print(f"📅 Primeiro ano disponível: {anos[0]}")
            print(f"📅 ÚLTIMO ano disponível (Mais recente): {anos[-1]}")
            print("-" * 30)
            print("Lista completa de anos:", ", ".join(anos))
            
            return anos
        else:
            print("❌ A tabela existe, mas não retornou anos (estranho).")
            return []

    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return []

# Executar
anos = verificar_anos_disponiveis()