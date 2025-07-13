import pandas as pd
from datetime import datetime
import os
from playwright.sync_api import sync_playwright
import time

def scrape_b3_data():
    """
    Extrai dados da B3 usando Playwright - equivalente à função obtemDadosB3
    """
    url = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br"
    
    try:
        with sync_playwright() as p:
            print("Iniciando browser...")
            
            # Configuração para container
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            page = browser.new_page()
            print(f"Acessando: {url}")
            
            # Aguardar carregamento completo
            page.goto(url, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            
            print("Página carregada.")

            try:
                h2_element = page.locator('#divContainerIframeB3 form h2').first
            
                if h2_element.is_visible():
                    h2_text = h2_element.text_content().strip()
                    
                    # Extrair data do texto "Carteira do Dia - 17/07/25"
                    if "Carteira do Dia" in h2_text and "-" in h2_text:
                        data_parte = h2_text.split("-")[-1].strip()
                        
                        data_formatada = data_parte.replace("/", "-")

            except Exception as e:
                print(f"Erro ao obter o dia: {e}")

            # Filtrando por Setor de Atuação
            try:
                print("Selecionando setor de atuação...")
                segment_select = page.locator('#segment')
                segment_select.select_option(index=1)  # option[2] = index 1
                page.wait_for_timeout(2000)
                print("Setor selecionado com sucesso")
            except Exception as e:
                print(f"Erro ao selecionar setor: {e}")
            
            # Selecionar todas as ações
            try:
                print("Selecionando 'Todas as ações'...")
                page_select = page.locator('#selectPage')
                page_select.select_option(index=3)  # option[4] = index 3
                page.wait_for_timeout(2000)
                print("'Todas as ações' selecionado com sucesso")
            except Exception as e:
                print(f"Erro ao selecionar 'Todas as ações': {e}")
            
            print("Aguardando carregamento final da tabela...")
            page.wait_for_timeout(3000)  # 3 segundos adicionais
            
            # Obter as linhas da tabela
            print("Extraindo dados da tabela...")
            
            # Tentar diferentes seletores para encontrar a tabela
            table_selectors = [
                '#divContainerIframeB3 table tbody tr',
                'table tbody tr',
                '#divContainerIframeB3 tr',
                'tbody tr'
            ]
            
            dados = []
            rows_found = False
            
            for selector in table_selectors:
                try:
                    print(f"Tentando seletor: {selector}")
                    rows = page.locator(selector).all()
                    print(f"Encontradas {len(rows)} linhas com '{selector}'")
                    
                    if len(rows) > 0:
                        for row in rows:
                            try:
                                # Obter todas as células (td) da linha
                                cells = row.locator('td').all()
                                if len(cells) > 0:  # Verificar se tem células
                                    row_data = []
                                    for cell in cells:
                                        cell_text = cell.text_content().strip()
                                        row_data.append(cell_text)
                                    
                                    #Adicionando dados
                                    dados.append(row_data)
                                    rows_found = True
                            except Exception as e:
                                print(f"Erro ao processar linha: {e}")
                                continue
                    
                    if rows_found:
                        break
                        
                except Exception as e:
                    print(f"Erro com seletor '{selector}': {e}")
                    continue
            
            browser.close()

            colunas = ["Setor", "Código", "Ação", "Tipo", "Qtde. Teórica", "Part. (%)", "Part. (%)Acum."]
            
            print(f"Extraídos {len(dados)} registros")
            
            if dados:
                # Ajustar dados se necessário para corresponder ao número de colunas
                dados_ajustados = []
                for linha in dados:
                    if len(linha) >= len(colunas):
                        dados_ajustados.append(linha[:len(colunas)])
                    elif len(linha) > 0:
                        # Preencher com valores vazios se necessário
                        linha_ajustada = linha + [''] * (len(colunas) - len(linha))
                        dados_ajustados.append(linha_ajustada)
                
                return dados_ajustados, colunas, data_formatada
            else:
                print("Nenhum dado extraído")
                return [], colunas, data_formatada
                
    except Exception as e:
        print(f"Erro geral: {e}")
        return [], ["Setor", "Código", "Ação", "Tipo", "Qtde. Teórica", "Part. (%)", "Part. (%)Acum."]

def save_to_parquet(dados, colunas, filename, data_formatada):
    """
    Salva os dados em formato parquet
    """
    try:
        os.makedirs('data', exist_ok=True)
        
        # Criar DataFrame
        df = pd.DataFrame(dados, columns=colunas)
        
        # Adicionar timestamp
        df['Dia'] = data_formatada
        
        filepath = os.path.join('data', filename)

        print(f"DEBUG: Tentando salvar o arquivo em: {os.path.abspath(filepath)}")
        
        df.to_parquet(filepath, engine='pyarrow')
        
        print(f"Dados salvos em: {filepath}")
        print(f"Shape do DataFrame: {df.shape}")
        print(f"Primeiras 3 linhas:")
        print(df.head(3))
        
        return filepath
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return None

def main():
    """
    Função principal
    """
    print("=== B3 Scraper com Playwright - Dados Completos ===")
    
    dados, colunas, data_formatada = scrape_b3_data()
    
    if dados:

        filename = f"b3_data_{data_formatada}.parquet"
        
        if save_to_parquet(dados, colunas, filename, data_formatada):
            print("Sucesso!")
        else:
            print("Falha ao salvar")
    else:
        print("Nenhum dado extraído")

# Para Lambda
def lambda_handler(event, context):
    """
    Handler para AWS Lambda
    """
    dados, colunas, data_formatada = scrape_b3_data()
    
    if dados:
        # Converter para formato JSON para retorno
        df = pd.DataFrame(dados, columns=colunas)
        
        return {
            'statusCode': 200,
            'body': {
                'message': f'Dados extraídos com sucesso: {len(dados)} registros',
                'data': df.to_dict('records')
            }
        }
    else:
        return {
            'statusCode': 500,
            'body': {'error': 'Falha no scraping - nenhum dado extraído'}
        }

if __name__ == "__main__":
    main()