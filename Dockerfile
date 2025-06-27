FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Копируем зависимости отдельно для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY . .

CMD ["python", "main.py"]
