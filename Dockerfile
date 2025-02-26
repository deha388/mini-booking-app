FROM python:3.11-slim

# Ortam değişkenlerini ayarla
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Çalışma dizinini oluştur
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Port ayarı
EXPOSE 8000

# Çalıştırma komutu
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 