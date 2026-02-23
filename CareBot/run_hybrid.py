#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Гибридный запуск CareBot: Flask веб-сервер + Telegram бот
"""
import asyncio
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Добавляем путь к модулю CareBot
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot'))

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO
    )
    # Понижаем уровень для httpx чтобы не засорять логи
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

def start_flask_server():
    """Запуск Flask веб-сервера в отдельном потоке"""
    logger = logging.getLogger("FlaskServer")
    logger.info("Starting Flask web server...")
    
    try:
        from CareBot import app
        
        # Получаем настройки из переменных окружения
        host = os.getenv('SERVER_HOST', '0.0.0.0')
        port = int(os.getenv('SERVER_PORT', 5555))
        
        # SSL настройки для HTTPS (опционально)
        ssl_cert = os.getenv('SSL_CERT_PATH')
        ssl_key = os.getenv('SSL_KEY_PATH')
        ssl_context = None
        
        if ssl_cert and ssl_key:
            if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
                ssl_context = (ssl_cert, ssl_key)
                logger.info(f"Flask server starting on https://{host}:{port} (SSL enabled)")
            else:
                logger.warning(f"SSL files not found, falling back to HTTP")
                logger.info(f"Flask server starting on http://{host}:{port}")
        else:
            logger.info(f"Flask server starting on http://{host}:{port}")
        
        app.run(host=host, port=port, debug=False, use_reloader=False, ssl_context=ssl_context)
        
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")

def start_telegram_bot():
    """Запуск Telegram бота"""
    logger = logging.getLogger("TelegramBot")
    logger.info("Starting Telegram bot...")
    
    try:
        # Импортируем и запускаем бота
        from CareBot.handlers import start_bot
        success = start_bot()
        if success:
            logger.info("Telegram bot started successfully")
        else:
            logger.error("Telegram bot failed to start")
        
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")

def main():
    """Главная функция - запускает и Flask и Telegram бота"""
    setup_logging()
    logger = logging.getLogger("CareBot")
    
    logger.info("Starting CareBot hybrid application...")
    logger.info("Components: Flask web server + Telegram bot")
    
    try:
        # Создаем пул потоков для параллельного запуска
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Запускаем Flask сервер в отдельном потоке
            flask_future = executor.submit(start_flask_server)
            
            # Запускаем Telegram бота в главном потоке
            # (поскольку bot.run_polling() блокирующий)
            start_telegram_bot()
            
    except KeyboardInterrupt:
        logger.info("Shutting down CareBot...")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()