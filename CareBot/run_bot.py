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

from CareBot import handlers

def main():
    """Запуск Telegram бота"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting CareBot Telegram bot...")
    
    try:
        # Запускаем поллинг бота
        # handlers.py уже содержит bot.run_polling() в конце
        # Поэтому просто импортируем handlers и он автоматически запустится
        logger.info("Bot is running...")
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()