FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (pypdf ve diğerleri için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Önce requirements — Docker cache için
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 8000

# Başlatma komutu
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
