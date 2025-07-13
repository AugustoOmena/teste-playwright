import pandas as pd
from datetime import datetime
import os
import glob
from playwright.sync_api import sync_playwright
import time
import boto3
import io
import json
import tempfile
import shutil

def scrape_b3_data():
    """
    Extrai dados da B3 usando Playwright - equivalente à função obtemDadosB3
    """
    url = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br"
    data_formatada = None
    
    try:
        with sync_playwright() as p:
            print("Iniciando browser...")
            
            # Paths possíveis para o Chromium em diferentes ambientes
            possible_paths = [
                '/var/task/browsers/chromium-*/chrome-linux/chrome',
                '/var/task/.playwright/chromium-*/chrome-linux/chrome',
                '/root/.cache/ms-playwright/chromium-*/chrome-linux/chrome',
                '/home/pwuser/.cache/ms-playwright/chromium-*/chrome-linux/chrome'
            ]
            
            chrome_executable = None
            for pattern in possible_paths:
                matches = glob.glob(pattern)
                if matches:
                    chrome_executable = matches[0]
                    print(f"Encontrado Chromium em: {chrome_executable}")
                    break
            
            # Criar diretório temporário único para user data
            temp_dir = tempfile.mkdtemp(prefix="playwright_", dir="/tmp")
            
            # Configuração otimizada para Lambda
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-ipc-flooding-protection',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--disable-translate',
                    '--disable-features=TranslateUI,VizDisplayCompositor,AudioServiceOutOfProcess',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--no-zygote',
                    '--single-process',
                    '--disable-breakpad',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-component-update',
                    '--disable-client-side-phishing-detection',
                    '--memory-pressure-off',
                    '--max_old_space_size=4096',
                    '--enable-logging',
                    '--log-level=0',
                    '--data-path=/tmp',
                    '--disk-cache-dir=/tmp',
                    '--homedir=/tmp',
                    '--remote-debugging-port=9222',
                    '--disable-background-networking',
                    '--disable-popup-blocking',
                    '--disable-web-resources',
                    '--enable-automation',
                    '--force-color-profile=srgb',
                    '--metrics-recording-only',
                    '--no-service-autorun',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--export-tagged-pdf'
                ]
            }
            
            # Se encontrou o executável, usar o caminho específico
            if chrome_executable:
                launch_options['executable_path'] = chrome_executable
                print(f"Usando executável: {chrome_executable}")
            else:
                print("Usando Chromium padrão do sistema")
            
            # Definir variáveis de ambiente específicas para o Chrome
            os.environ['CHROME_DEVEL_SANDBOX'] = '/usr/local/sbin/chrome-devel-sandbox'
            os.environ['DISPLAY'] = ':99'
            
            try:
                print("Lançando browser com contexto persistente...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=temp_dir,
                    headless=True,
                    args=launch_options['args'],
                    executable_path=launch_options.get('executable_path')
                )
                
                print("Browser/contexto iniciado com sucesso!")
                
                # Configurar page com timeouts apropriados
                page = context.new_page()
                page.set_default_timeout(30000)  # 30 segundos
                page.set_default_navigation_timeout(30000)
                
                print(f"Acessando: {url}")
                
                # Aguardar carregamento completo
                page.goto(url, wait_until='networkidle')
                page.wait_for_timeout(5000)  # Aguardar mais tempo
                
                print("Página carregada.")
                
                # DEBUG: Verificar estrutura da página
                print("=== DEBUG: Verificando estrutura da página ===")
                
                # Verificar se há iframes
                iframe_count = page.locator('iframe').count()
                print(f"Número de iframes encontrados: {iframe_count}")
                
                if iframe_count > 0:
                    for i in range(iframe_count):
                        iframe = page.locator('iframe').nth(i)
                        src = iframe.get_attribute('src')
                        id_attr = iframe.get_attribute('id')
                        print(f"Iframe {i}: src={src}, id={id_attr}")
                
                # Verificar elementos principais
                main_elements = ['#divContainerIframeB3', '#segment', '#selectPage', 'h2', 'form']
                for element in main_elements:
                    count = page.locator(element).count()
                    print(f"Elemento '{element}': {count} encontrado(s)")
                
                # Tentar encontrar o iframe correto
                working_page = page
                if iframe_count > 0:
                    try:
                        # Tentar o iframe principal (geralmente o primeiro)
                        main_iframe = page.frame_locator('iframe').first
                        print("Tentando usar iframe principal...")
                        
                        # Testar se consegue acessar elementos dentro do iframe
                        test_h2 = main_iframe.locator('h2').count()
                        test_form = main_iframe.locator('form').count()
                        print(f"No iframe - h2: {test_h2}, form: {test_form}")
                        
                        if test_h2 > 0 or test_form > 0:
                            print("Usando iframe para extrair dados")
                            # Usar o iframe como contexto
                            working_context = main_iframe
                        else:
                            print("Iframe não contém os elementos esperados, usando página principal")
                            working_context = page
                    except Exception as e:
                        print(f"Erro ao acessar iframe: {e}")
                        working_context = page
                else:
                    working_context = page

                # Extrair data com diferentes estratégias
                data_formatada = datetime.now().strftime("%d-%m-%y")  # Valor padrão
                
                try:
                    print("Tentando extrair data...")
                    
                    # Diferentes seletores para tentar encontrar a data
                    date_selectors = [
                        'h2:has-text("Carteira")',
                        'h2',
                        'form h2',
                        '#divContainerIframeB3 form h2',
                        '.title',
                        '[class*="title"]',
                        '[class*="header"]'
                    ]
                    
                    date_found = False
                    for selector in date_selectors:
                        try:
                            if hasattr(working_context, 'locator'):
                                elements = working_context.locator(selector)
                            else:
                                elements = working_context.locator(selector)
                            
                            count = elements.count()
                            print(f"Seletor '{selector}': {count} elemento(s)")
                            
                            if count > 0:
                                for i in range(count):
                                    element = elements.nth(i)
                                    if element.is_visible():
                                        text = element.text_content().strip()
                                        print(f"Texto encontrado: '{text}'")
                                        
                                        if "Carteira" in text and "-" in text:
                                            data_parte = text.split("-")[-1].strip()
                                            data_formatada = data_parte.replace("/", "-")
                                            print(f"Data extraída: {data_formatada}")
                                            date_found = True
                                            break
                                
                                if date_found:
                                    break
                        except Exception as e:
                            print(f"Erro com seletor de data '{selector}': {e}")
                            continue
                    
                    if not date_found:
                        print("Data não encontrada, usando data atual")
                        
                except Exception as e:
                    print(f"Erro ao extrair data: {e}")

                # Tentar interagir com os elementos de seleção
                print("=== Tentando interagir com elementos ===")
                
                # Aguardar mais tempo para carregar
                page.wait_for_timeout(5000)
                
                # Tentar diferentes estratégias para encontrar e interagir com os elementos
                try:
                    # Procurar por elementos select em toda a página
                    all_selects = page.locator('select').count()
                    print(f"Total de elementos select na página: {all_selects}")
                    
                    if all_selects > 0:
                        for i in range(all_selects):
                            select_element = page.locator('select').nth(i)
                            select_id = select_element.get_attribute('id')
                            select_name = select_element.get_attribute('name')
                            print(f"Select {i}: id={select_id}, name={select_name}")
                            
                            # Se encontrar o select do segmento
                            if select_id == 'segment' or 'segment' in str(select_name):
                                print("Encontrado select de segmento, tentando selecionar...")
                                try:
                                    select_element.select_option(index=1)
                                    page.wait_for_timeout(2000)
                                    print("Segmento selecionado com sucesso")
                                except Exception as e:
                                    print(f"Erro ao selecionar segmento: {e}")
                            
                            # Se encontrar o select da página
                            elif select_id == 'selectPage' or 'page' in str(select_name):
                                print("Encontrado select de página, tentando selecionar...")
                                try:
                                    select_element.select_option(index=3)
                                    page.wait_for_timeout(3000)
                                    print("Página selecionada com sucesso")
                                except Exception as e:
                                    print(f"Erro ao selecionar página: {e}")
                
                except Exception as e:
                    print(f"Erro ao interagir com selects: {e}")
                
                # Aguardar carregamento final
                print("Aguardando carregamento final da tabela...")
                page.wait_for_timeout(5000)
                
                # Tentar extrair dados da tabela com diferentes estratégias
                print("=== Extraindo dados da tabela ===")
                
                # Verificar todas as tabelas na página
                table_count = page.locator('table').count()
                print(f"Total de tabelas encontradas: {table_count}")
                
                dados = []
                
                if table_count > 0:
                    for table_idx in range(table_count):
                        print(f"Analisando tabela {table_idx}")
                        table = page.locator('table').nth(table_idx)
                        
                        # Verificar linhas na tabela
                        row_selectors = ['tbody tr', 'tr']
                        
                        for row_selector in row_selectors:
                            try:
                                rows = table.locator(row_selector)
                                row_count = rows.count()
                                print(f"Tabela {table_idx} - '{row_selector}': {row_count} linhas")
                                
                                if row_count > 0:
                                    for i in range(min(row_count, 100)):  # Limitar a 100 linhas para teste
                                        try:
                                            row = rows.nth(i)
                                            cells = row.locator('td')
                                            cell_count = cells.count()
                                            
                                            if cell_count > 0:
                                                row_data = []
                                                for j in range(cell_count):
                                                    cell = cells.nth(j)
                                                    cell_text = cell.text_content().strip()
                                                    row_data.append(cell_text)
                                                
                                                if any(cell.strip() for cell in row_data):
                                                    dados.append(row_data)
                                                    
                                                    # Log das primeiras linhas para debug
                                                    if len(dados) <= 3:
                                                        print(f"Linha {len(dados)}: {row_data}")
                                        
                                        except Exception as e:
                                            print(f"Erro ao processar linha {i}: {e}")
                                            continue
                                    
                                    if dados:
                                        print(f"Dados extraídos da tabela {table_idx}: {len(dados)} linhas")
                                        break
                                        
                            except Exception as e:
                                print(f"Erro com seletor '{row_selector}' na tabela {table_idx}: {e}")
                                continue
                        
                        if dados:
                            break
                
                context.close()
                
                # Limpar diretório temporário
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

                colunas = ["Setor", "Código", "Ação", "Tipo", "Qtde. Teórica", "Part. (%)", "Part. (%)Acum."]
                
                print(f"=== RESULTADO FINAL ===")
                print(f"Total de registros extraídos: {len(dados)}")
                print(f"Data formatada: {data_formatada}")
                
                if dados:
                    # Ajustar dados se necessário
                    dados_ajustados = []
                    for linha in dados:
                        if len(linha) >= len(colunas):
                            dados_ajustados.append(linha[:len(colunas)])
                        elif len(linha) > 0:
                            linha_ajustada = linha + [''] * (len(colunas) - len(linha))
                            dados_ajustados.append(linha_ajustada)
                    
                    print(f"Dados ajustados: {len(dados_ajustados)} linhas")
                    return dados_ajustados, colunas, data_formatada
                else:
                    print("Nenhum dado extraído")
                    return [], colunas, data_formatada
                    
            except Exception as browser_error:
                print(f"Erro específico do browser: {browser_error}")
                import traceback
                traceback.print_exc()
                raise browser_error
                
    except Exception as e:
        print(f"Erro geral: {e}")
        import traceback
        traceback.print_exc()
        colunas = ["Setor", "Código", "Ação", "Tipo", "Qtde. Teórica", "Part. (%)", "Part. (%)Acum."]
        if data_formatada is None:
            data_formatada = datetime.now().strftime("%d-%m-%y")
        return [], colunas, data_formatada

def save_to_parquet(dados, colunas, filename, data_formatada):
    """
    Salva os dados em formato parquet no S3
    """
    try:
        # Criar DataFrame
        df = pd.DataFrame(dados, columns=colunas)
        
        # Adicionar timestamp
        df['Dia'] = data_formatada
        
        print(f"Shape do DataFrame: {df.shape}")
        print(f"Primeiras 3 linhas:")
        print(df.head(3))
        
        # Salvar em buffer de memória
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine='pyarrow')
        buffer.seek(0)
        
        # Configurar S3
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        s3_key = f"data/{filename}"
        
        if not bucket_name:
            raise ValueError("Variável de ambiente S3_BUCKET_NAME não definida")
        
        # Upload para S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=buffer.getvalue(),
            ContentType='application/octet-stream'
        )
        
        print(f"Dados salvos no S3: s3://{bucket_name}/{s3_key}")
        
        return f"s3://{bucket_name}/{s3_key}"
    except Exception as e:
        print(f"Erro ao salvar no S3: {e}")
        return None

# Para Lambda
def lambda_handler(event, context):
    """
    Handler para AWS Lambda
    """
    try:
        print("=== Iniciando Lambda Handler ===")
        
        dados, colunas, data_formatada = scrape_b3_data()
        
        if dados:
            # Salvar no S3 se houver dados
            filename = f"b3_data_{data_formatada}.parquet"
            s3_path = save_to_parquet(dados, colunas, filename, data_formatada)
            
            # Converter para formato JSON para retorno
            df = pd.DataFrame(dados, columns=colunas)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Dados extraídos com sucesso: {len(dados)} registros',
                    'data_formatada': data_formatada,
                    's3_path': s3_path,
                    'sample_data': df.head(5).to_dict('records')
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Scraping executado mas nenhum dado extraído',
                    'data_formatada': data_formatada,
                    'dados_count': 0
                })
            }
    except Exception as e:
        print(f"Erro no lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Erro no lambda_handler: {str(e)}',
                'message': 'Falha no scraping'
            })
        }

def main():
    """
    Função principal para teste local
    """
    print("=== B3 Scraper com Playwright - Dados Completos ===")
    
    dados, colunas, data_formatada = scrape_b3_data()
    
    if dados:
        filename = f"b3_data_{data_formatada}.parquet"
        
        # Para teste local, só mostrar os dados sem salvar no S3
        df = pd.DataFrame(dados, columns=colunas)
        df['Dia'] = data_formatada
        
        print(f"Dados extraídos: {len(dados)} registros")
        print(df.head())
        
        # Salvar localmente para teste
        df.to_parquet(f"./data/{filename}", engine='pyarrow')
        print(f"Dados salvos localmente: ./data/{filename}")
    else:
        print("Nenhum dado extraído")

if __name__ == "__main__":
    main()