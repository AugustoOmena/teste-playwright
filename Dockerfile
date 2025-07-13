FROM public.ecr.aws/lambda/python:3.11-x86_64

# Define o diretório de trabalho
WORKDIR /var/task

# Atualiza o sistema e instala dependências necessárias
RUN yum update -y && yum install -y \
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
    xorg-x11-fonts-Type1 \
    xorg-x11-fonts-misc \
    libdrm \
    libxshmfence \
    mesa-libgbm \
    && yum clean all

# Copia requirements.txt
COPY requirements.txt .

# Instala dependências Python
RUN python -m pip install --no-cache-dir -r requirements.txt

# Define variáveis de ambiente para o Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/var/task/browsers
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Cria diretório para browsers
RUN mkdir -p /var/task/browsers

# Instala o Chromium diretamente no diretório correto
RUN python -m playwright install chromium

# Move o Chromium para o diretório esperado se necessário
RUN if [ -d "/root/.cache/ms-playwright" ]; then \
    cp -r /root/.cache/ms-playwright/* /var/task/browsers/ || true; \
    fi

# Verifica se o Chromium foi instalado e ajusta permissões
RUN find /var/task -name "chrome" -type f -exec chmod +x {} \; || echo "Chrome executable not found in /var/task"
RUN find /var/task -name "chrome-linux" -type d -exec chmod 755 {} \; || echo "Chrome directory not found"

# Cria diretório tmp com permissões adequadas
RUN mkdir -p /tmp && chmod 1777 /tmp

# Define variáveis de ambiente adicionais
ENV TMPDIR=/tmp
ENV TEMP=/tmp
ENV TMP=/tmp

# Lista onde o Chromium foi instalado para debug
RUN find /var/task -name "chrome*" -type f 2>/dev/null || echo "Chrome not found in /var/task"

# Copia o código da aplicação
COPY app.py .

# Define o comando padrão
CMD [ "app.lambda_handler" ]