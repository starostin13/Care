# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p db static/uploads templates logs

# Устанавливаем права доступа
RUN chmod +x *.py

# Создаем пользователя для запуска приложения
RUN useradd -m -u 1000 carebot && chown -R carebot:carebot /app
USER carebot

# Экспонируем порты
EXPOSE 5000 8080

# Переменные окружения
ENV PYTHONPATH=/app
ENV FLASK_APP=server_app.py
ENV FLASK_ENV=production

# Команда по умолчанию (может быть переопределена в docker-compose)
CMD ["python", "server_app.py"]
