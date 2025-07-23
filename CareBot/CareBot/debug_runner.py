#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug runner для запуска и телеграм бота, и веб-приложения одновременно
"""

import threading
import time
import logging
import sys
import os

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_telegram_bot():
    """Запуск телеграм бота в отдельном потоке"""
    try:
        logger.info("🤖 Starting Telegram Bot...")
        import handlers
        logger.info("✅ Telegram Bot started successfully!")
    except Exception as e:
        logger.error(f"❌ Error starting Telegram Bot: {e}")
        raise

def run_flask_app():
    """Запуск Flask веб-приложения в отдельном потоке"""
    try:
        logger.info("🌐 Starting Flask Web App...")
        from CareBot import app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        logger.info("✅ Flask Web App started successfully!")
    except Exception as e:
        logger.error(f"❌ Error starting Flask Web App: {e}")
        raise

def main():
    """Главная функция для запуска обоих сервисов"""
    logger.info("🚀 Starting debug environment...")
    logger.info("📁 Working directory: " + os.getcwd())
    logger.info("🐍 Python path: " + str(sys.path))
    
    try:
        # Запускаем Flask приложение в отдельном потоке
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        
        # Небольшая пауза для запуска Flask
        time.sleep(2)
        logger.info("🔗 Flask app should be available at: http://localhost:5000")
        logger.info("🗺️ Map should be available at: http://localhost:5000/map")
        
        # Запускаем телеграм бота в основном потоке
        run_telegram_bot()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down debug environment...")
    except Exception as e:
        logger.error(f"💥 Critical error in debug environment: {e}")
        raise

if __name__ == '__main__':
    main()
