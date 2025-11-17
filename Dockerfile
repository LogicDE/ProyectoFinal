# Base image
FROM python:3.11-slim

# Variables de entorno para no pedir interacción
ENV DEBIAN_FRONTEND=noninteractive

# 1️⃣ Instalar dependencias del sistema necesarias para mysqlclient y cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 2️⃣ Crear directorio de trabajo
WORKDIR /app

# 3️⃣ Copiar solo requirements.txt primero para cachear pip install
COPY requirements.txt requirements.txt

# 4️⃣ Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copiar toda la aplicación
COPY . .

# 6️⃣ Exponer puerto de Flask
EXPOSE 5000

# 7️⃣ Comando para iniciar Flask
CMD ["python", "app.py"]
