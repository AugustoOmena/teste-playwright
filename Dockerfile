FROM public.ecr.aws/lambda/python:3.11

# Define o diretório de trabalho dentro do contêiner
WORKDIR /var/task

# dependências de sistema estritamente necessárias para o Playwright.
RUN yum install -y \
    alsa-lib \
    atk \
    at-spi2-atk \
    cups-libs \
    dbus-libs \
    expat \
    fontconfig \
    gtk3 \
    libX11 \
    libX11-xcb \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXfixes \
    libXi \
    libXrandr \
    libXrender \
    libXtst \
    nss \
    pango \
    && yum clean all

# Copia o arquivo de dependências Python para o contêiner
COPY requirements.txt .

# Instala as dependências Python a partir do requirements.txt com versões fixadas.
RUN python -m pip install --no-cache-dir -r requirements.txt

# Instala o browser Chromium para o Playwright
RUN playwright install chromium

# Copia o código da sua aplicação
COPY app.py .

# Define o comando padrão para o Lambda
CMD [ "app.lambda_handler" ]
