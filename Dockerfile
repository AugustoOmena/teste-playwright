# =========================================================================
# ESTÁGIO 1: BUILDER
# Usando a imagem correta: amazonlinux:2023, que corresponde à base do Lambda
# =========================================================================
FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS builder

# 1. Instala as dependências de sistema e de compilação usando DNF
#    No AL2023, os comandos são mais diretos.
RUN dnf install -y \
    alsa-lib \
    at-spi2-atk \
    cups-libs \
    libXcomposite \
    libXdamage \
    libXrandr \
    libXtst \
    nss \
    pango \
    # Ferramentas de build
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    gcc \
    gcc-c++ \
    && dnf clean all

# 2. Cria o virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# =========================================================================
# ESTÁGIO 2: FINAL
# Imagem do Lambda (baseada em AL2023)
# =========================================================================
FROM public.ecr.aws/lambda/python:3.11

WORKDIR /var/task

# Copia os artefatos do builder (que agora é 100% compatível)
COPY --from=builder /opt/venv /var/task
COPY --from=builder /usr/lib64 /var/task/lib/

# Aponta para o nosso novo diretório de bibliotecas
ENV LD_LIBRARY_PATH=/var/task/lib:$LD_LIBRARY_PATH

# Copia o código da sua aplicação
COPY app.py .
COPY data/ ./data/

# Define o handler da sua função Lambda
CMD [ "app.handler" ]