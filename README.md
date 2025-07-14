📈 Web Scrapping de Dados da B3 com Docker e AWS Lambda
Este projeto utiliza uma imagem Docker para realizar o scrapping de dados da B3, processá-los e armazená-los. A execução do scrapping é orquestrada através de uma função AWS Lambda configurada com uma imagem de contêiner.

🚀 Requisitos
Certifique-se de ter os seguintes pré-requisitos instalados e configurados:

Docker: Para construir e gerenciar as imagens do contêiner.

Conta no Console AWS: Para implantar a solução.

AWS CLI: Ferramenta de linha de comando para interagir com os serviços da AWS.

Se você ainda não tem o AWS CLI instalado, siga as instruções em: Instalar AWS CLI.



📝 Como Usar
Siga os passos abaixo para configurar e executar seu projeto de scrapping.

1. Configurar Credenciais AWS CLI
O método de login na AWS CLI pode variar dependendo do tipo da sua conta. Para ambientes educacionais (como o fornecido pela FIAP), geralmente são utilizadas credenciais temporárias (Access Key ID, Secret Access Key e Session Token).

Obtenha suas Credenciais:

- Acesse o ambiente fornecido (ex: AWS Educate, plataforma da FIAP) e copie suas credenciais temporárias.
  <img width="1182" height="376" alt="image" src="https://github.com/user-attachments/assets/d6684278-85dc-4c43-bfec-c61827e6e835" />


- Configure a AWS CLI com as chaves temporárias:

Bash

      aws configure set aws_access_key_id SUA_NOVA_ACCESS_KEY_ID
      aws configure set aws_secret_access_key SUA_NOVA_SECRET_KEY
      aws configure set aws_session_token SEU_NOVO_SESSION_TOKEN
      # Opcional: Defina a região padrão, se ainda não estiver configurada
      aws configure set default.region us-east-1

Importante: Substitua SUA_NOVA_ACCESS_KEY_ID, SUA_NOVA_SECRET_KEY e SEU_NOVO_SESSION_TOKEN pelos valores que você copiou.
 
- Realize o Login no Amazon ECR (Elastic Container Registry):
  
      aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin SEU_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

Atenção: Substitua SEU_AWS_ACCOUNT_ID pelo seu ID de conta AWS (ex: 613365115546). Este comando autentica seu Docker CLI no registro ECR da sua conta.

2. Criar Repositório ECR e Enviar Imagem Docker
No seu terminal Bash, na raiz do projeto, execute os seguintes comandos:

- Crie o Repositório no Amazon ECR:

      aws ecr create-repository --repository-name seu-nome-de-repositorio --region us-east-1

Dica: Escolha um nome de repositório descritivo, por exemplo, b3-scrapper-image.

- Construa a Imagem Docker:
  
      docker build --no-cache -t nome-da-sua-imagem .

Exemplo: docker build --no-cache -t b3-scrapper .

- Marque a Imagem Docker (Tag):

      docker tag nome-da-sua-imagem:latest SEU_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/seu-nome-de-repositorio:sua-tag

Sugestão: Para cada push, utilize uma "tag" diferente (ex: v1.0, dev20, 20250714-01) para melhor controle de versão e para evitar falsos logs de erro.
Exemplo: docker tag b3-scrapper:latest 613365115546.dkr.ecr.us-east-1.amazonaws.com/b3-scrapper-image:dev20

- Envie a Imagem para o Amazon ECR:

      docker push SEU_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/seu-nome-de-repositorio:sua-tag
  
Exemplo: docker push 613365115546.dkr.ecr.us-east-1.amazonaws.com/b3-scrapper-image:dev20


3. Verificar Imagem no ECR
Após a finalização do push, você poderá visualizar sua imagem no console da AWS, dentro do serviço Elastic Container Registry.
<img width="1459" height="131" alt="image" src="https://github.com/user-attachments/assets/99b80fd0-5b94-4137-8d76-8e3327504801" />


4. Criar e Configurar Função AWS Lambda
Crie uma nova Função Lambda:

No console AWS, navegue até Lambda e clique em "Create function".

Selecione a opção "Container Image" e adicione a referência à sua imagem recém-enviada.

Em "Architecture", selecione a opção x86_64.

Configure sua Execution Role (Função de Execução): Certifique-se de que a role tenha permissões para acessar o ECR e qualquer outro serviço que sua Lambda precise (ex: S3 para salvar os dados).

Clique em "Create Function".
<img width="1644" height="388" alt="image" src="https://github.com/user-attachments/assets/d1312c31-3ef1-4cff-92ce-91e407c4bace" />





5. Adicionar Variáveis de Ambiente
Após criar a função Lambda, navegue até a aba "Configuration" e selecione "Environment variables".

Adicione uma nova variável de ambiente com a chave S3_BUCKET_NAME e o valor sendo o nome do seu bucket S3 onde os dados serão armazenados.
*
   <img width="1354" height="636" alt="image" src="https://github.com/user-attachments/assets/81117e57-4ecf-4b61-9710-2237c939ddd0" />




6. Testar a Função Lambda
Na aba "Test" da sua função Lambda:

Crie um novo Test event. Um evento vazio pode ser suficiente se sua função não depender de entrada.

Clique em "Save".

Em seguida, clique em "Test" para executar a função.
<img width="1311" height="802" alt="image" src="https://github.com/user-attachments/assets/8020cf2c-bfc2-4ca2-8524-931630faaa17" />

✔️ Resultado da Execução
Após a execução bem-sucedida da sua função Lambda, você deverá ver os logs de sucesso e a confirmação de que o scrapping foi realizado e os dados foram processados.

<img width="1312" height="581" alt="image" src="https://github.com/user-attachments/assets/cab74eb9-d955-4aa5-b422-2f9c6030c630" />

<img width="1382" height="262" alt="image" src="https://github.com/user-attachments/assets/a43a99d0-64ef-495c-9e47-34d709b0d85f" />

📊 Exibição no AWS Glue Job
Se você estiver integrando esses dados com o AWS Glue, o resultado processado pode ser visualizado em seu Glue Job ou catálogos de dados.
<img width="1497" height="839" alt="image" src="https://github.com/user-attachments/assets/a33f0102-1a21-4346-bf8c-c5f2c1386451" />




   







