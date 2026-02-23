#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Точка входа для запуска Telegram бота CareBot
"""
import asyncio
import logging
import os
import sys

# Добавляем путь к модулю CareBot
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot'))

def main():
    """Запуск Telegram бота"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting CareBot Telegram bot...")
    
    try:
        # Импортируем и вызываем функцию start_bot
        from CareBot.handlers import start_bot
        success = start_bot()
        if not success:
            logger.error("Bot failed to start")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()