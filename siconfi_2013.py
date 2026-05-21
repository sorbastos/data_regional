import pandas as pd
import sqlite3
import os

def importar_2013_direto():
    print("--- IMPORTAÇÃO 2013: DIRETO (SEM LIMPEZA PRÉVIA) ---")
    
    db_destino = "siconfi_v10_final.db"
    db_pib = "pib_regional.db"
    csv_desp = "despesas_2013.csv"
    csv_rec = "receitas_2013.csv"

    # =========================================================================
    # 1. CARREGAR FILTRO DE MUNICÍPIOS
    # =========================================================================
    lista_codigos = set()
    if os.path.exists(db_pib):
        conn_pib = sqlite3.connect(db_pib)
        try:
            # Tenta pegar da tabela PIB ou População
            df_muni = pd.read_sql("SELECT DISTINCT cod_ibge FROM pib_municipios", conn_pib)
            lista_codigos = set(df_muni['cod_ibge'].astype(str).tolist())
        except: pass
        conn_pib.close()
    
    # Funções alvo (apenas 2 dígitos)
    funcoes_alvo = ['01','04','06','08','09','10','11','12','13',
                    '15','16','17','18','19','20','22','23','26','27']

    buffer_insercao = []

    # =========================================================================
    # 2. LEITURA INTELIGENTE (FILTRO 'PAGA')
    # =========================================================================
    
    def processar(arquivo, tipo_dado):
        if not os.path.exists(arquivo):
            print(f"Pulei {arquivo} (não existe).")
            return

        print(f"Processando {arquivo}...")
        try:
            # Tenta ler (latin1 e ;)
            try:
                df = pd.read_csv(arquivo, sep=';', encoding='latin1', dtype=str, low_memory=False)
                if len(df.columns) < 3: raise ValueError()
            except:
                df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str, low_memory=False)

            # Normalizar colunas
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Mapear Colunas
            col_ibge = next((c for c in df.columns if 'cod' in c and 'ibge' in c), None)
            col_conta = next((c for c in df.columns if 'conta' in c or 'rubrica' in c), None)
            col_valor = next((c for c in df.columns if 'valor' in c or 'vlr' in c), None)
            
            # Coluna de Estágio (Essencial para não triplicar valor)
            col_estagio = next((c for c in df.columns if 'coluna' in c or 'estagio' in c or 'tipo' in c and 'conta' not in c), None)
            
            # --- NOVA COLUNA: POPULAÇÃO ---
            col_populacao = next((c for c in df.columns if 'popula' in c), None)
            
            if not (col_ibge and col_conta and col_valor):
                print(f"   Erro de layout em {arquivo}.")
                return

            if col_estagio:
                print(f"   -> Filtro de Estágio detectado na coluna: {col_estagio}")
            else:
                print("   -> AVISO: Coluna de estágio não encontrada.")

            if col_populacao:
                print(f"   -> Coluna de População detectada: {col_populacao}")
            else:
                print("   -> AVISO: Coluna de População não encontrada no CSV.")

            count_local = 0
            
            for _, row in df.iterrows():
                # --- FILTRO 1: MUNICÍPIO ---
                cod = str(row[col_ibge]).strip()
                if lista_codigos:
                    if cod not in lista_codigos:
                        if len(cod) == 6:
                            match = next((m for m in lista_codigos if m.startswith(cod)), None)
                            if match: cod = match
                            else: continue
                        else: continue

                # --- FILTRO 2: ESTÁGIO (CORREÇÃO DE VALOR) ---
                if col_estagio:
                    estagio = str(row[col_estagio]).upper()
                    if tipo_dado == 'Despesa':
                        # Só aceita despesa PAGA
                        if "PAGA" not in estagio: 
                            continue 
                    elif tipo_dado == 'Receita':
                        # Pula previsão
                        if "PREVI" in estagio or "INICIAL" in estagio:
                            continue

                # --- EXTRAÇÃO DA POPULAÇÃO ---
                populacao = None
                if col_populacao:
                    try:
                        # Extrai a string, remove pontos/virgulas ou casas decimais acidentais
                        pop_str = str(row[col_populacao]).split('.')[0].strip()
                        if pop_str and pop_str.lower() != 'nan':
                            populacao = int(pop_str)
                    except:
                        populacao = None

                # --- LIMPEZA VALOR ---
                val_str = str(row[col_valor])
                if ',' in val_str and '.' in val_str: val_str = val_str.replace('.', '').replace(',', '.')
                elif ',' in val_str: val_str = val_str.replace(',', '.')
                try: valor = float(val_str)
                except: valor = 0

                if valor > 0:
                    conta_full = str(row[col_conta])
                    
                    # === DESPESAS ===
                    if tipo_dado == 'Despesa':
                        partes = conta_full.replace('-', ' ').split()
                        codigo_extraido = partes[0].strip()
                        if len(codigo_extraido) == 1 and codigo_extraido.isdigit(): codigo_extraido = "0" + codigo_extraido
                        
                        # Filtro estrito: Aceita "10", rejeita "10.301"
                        if codigo_extraido in funcoes_alvo and "." not in codigo_extraido:
                            buffer_insercao.append({
                                'cod_ibge': cod, 'ano': 2013, 'tipo': 'Despesa',
                                'categoria': codigo_extraido, 'descricao': conta_full, 'valor': valor,
                                'populacao': populacao # <--- INSERIDO AQUI
                            })
                            count_local += 1

                    # === RECEITAS ===
                    elif tipo_dado == 'Receita':
                        cat_final = None
                        conta_limpa = conta_full.replace('.', '')
                        
                        # Impostos Próprios
                        if conta_limpa.startswith("110") and "TRIBUT" in conta_full.upper():
                             cat_final = "Rec_Impostos_Proprios"

                        # Transf União
                        elif "1.7.2.1.00.00.00" in conta_full or ("FPM" in conta_full.upper() and "COTA" in conta_full.upper()):
                             cat_final = "Rec_Transf_Uniao"
                        elif conta_limpa.startswith("1721") and "UNIÃO" in conta_full.upper() and "TOTAL" in conta_full.upper():
                             cat_final = "Rec_Transf_Uniao"

                        # Transf Estados
                        elif "1.7.2.2.00.00.00" in conta_full or ("ICMS" in conta_full.upper() and "COTA" in conta_full.upper()):
                             cat_final = "Rec_Transf_Estados"
                        elif conta_limpa.startswith("1722") and "ESTADO" in conta_full.upper() and "TOTAL" in conta_full.upper():
                             cat_final = "Rec_Transf_Estados"
                        
                        # Total
                        elif "TOTAL" in conta_full.upper() and ("RECEITA" in conta_full.upper() or "ORÇAMENTÁRIA" in conta_full.upper()):
                            cat_final = "Rec_Total"

                        if cat_final:
                            buffer_insercao.append({
                                'cod_ibge': cod, 'ano': 2013, 'tipo': 'Receita',
                                'categoria': cat_final, 'descricao': conta_full, 'valor': valor,
                                'populacao': populacao # <--- INSERIDO AQUI
                            })
                            count_local += 1
            
            print(f"   -> {count_local} linhas selecionadas em {arquivo}.")

        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")

    # Executar
    processar(csv_desp, 'Despesa')
    processar(csv_rec, 'Receita')

    # Salvar
    if buffer_insercao:
        print(f"\n3. Salvando no banco {db_destino}...")
        conn = sqlite3.connect(db_destino)
        df_new = pd.DataFrame(buffer_insercao)
        
        # Remove duplicatas exatas do buffer antes de inserir
        df_new.drop_duplicates(subset=['cod_ibge', 'categoria', 'tipo'], keep='first', inplace=True)
        
        df_new.to_sql("dados_siconfi", conn, if_exists='append', index=False)
        conn.close()
        print("SUCESSO! Dados de 2013 importados (Filtro 'Pagas' aplicado e População inserida).")
    else:
        print("Nenhum dado encontrado.")

if __name__ == "__main__":
    importar_2013_direto()