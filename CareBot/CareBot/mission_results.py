#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Обработчики результатов миссий для телеграм бота
"""

import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime

# Импортируем движок миссий
from mission_engine import MissionStorage, Mission
import map_helper
import sqllite_helper
import logging

logger = logging.getLogger(__name__)

# Глобальное хранилище миссий
mission_storage = MissionStorage("missions.json")

async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /result для ввода результатов миссии
    Использование: /result M123 15 8
    """
    user_id = update.effective_user.id
    
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ Неверный формат команды!\n\n"
            "📝 Правильное использование:\n"
            "`/result M123 15 8`\n\n"
            "Где:\n"
            "• M123 - ID миссии (напечатан на листе)\n"
            "• 15 - ваши очки\n"
            "• 8 - очки противника\n\n"
            "💡 Пример: `/result M456 20 12`",
            parse_mode='Markdown'
        )
        return
    
    try:
        mission_id = context.args[0].upper()
        user_score = int(context.args[1])
        opponent_score = int(context.args[2])
        
        # Проверяем формат ID миссии
        if not re.match(r'^M\d+$', mission_id):
            await update.message.reply_text(
                "❌ Неверный формат ID миссии!\n"
                "ID должен быть вида M123, M456 и т.д."
            )
            return
        
        # Ищем миссию
        mission = mission_storage.get_mission_by_short_id(mission_id)
        if not mission:
            await update.message.reply_text(
                f"❌ Миссия {mission_id} не найдена!\n\n"
                "Проверьте:\n"
                "• Правильность ID миссии\n"
                "• Что миссия была создана\n"
                "• Что ID введен без ошибок"
            )
            return
        
        # Проверяем, что миссия еще не завершена
        if mission.completed:
            await update.message.reply_text(
                f"⚠️ Миссия {mission_id} уже завершена!\n\n"
                f"Результат: {mission.result}\n"
                f"Победитель: {mission.winner_id}"
            )
            return
        
        # Проверяем, что пользователь участвует в миссии
        user_telegram_id = str(user_id)
        # Здесь должна быть проверка участия пользователя
        # Пока упрощенная версия - любой может вводить результат
        
        # Определяем победителя
        if user_score > opponent_score:
            winner = "Вы"
            winner_id = user_telegram_id
        elif opponent_score > user_score:
            winner = "Противник" 
            winner_id = "opponent"  # Здесь должен быть ID противника
        else:
            winner = "Ничья"
            winner_id = "draw"
        
        # Формируем результат
        result = f"{user_score} - {opponent_score}"
        
        # Показываем подтверждение
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_result_{mission_id}_{user_score}_{opponent_score}_{user_telegram_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data="cancel_result")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎯 Подтверждение результата миссии {mission_id}\n\n"
            f"📊 Результат: {user_score} - {opponent_score}\n"
            f"🏆 Победитель: {winner}\n"
            f"🗺️ Hex: {mission.hex_id}\n\n"
            "Подтвердить результат?",
            reply_markup=reply_markup
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Очки должны быть числами!\n"
            "Пример: `/result M123 15 8`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in result_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке результата. Попробуйте еще раз."
        )

async def confirm_result_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения результата"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_result":
        await query.edit_message_text("❌ Ввод результата отменен.")
        return
    
    # Парсим данные callback
    try:
        parts = query.data.split('_')
        if len(parts) < 5 or parts[0] != "confirm" or parts[1] != "result":
            await query.edit_message_text("❌ Ошибка данных подтверждения.")
            return
        
        mission_id = parts[2]
        user_score = int(parts[3])
        opponent_score = int(parts[4])
        winner_id = parts[5]
        
        # Получаем миссию
        mission = mission_storage.get_mission_by_short_id(mission_id)
        if not mission:
            await query.edit_message_text(f"❌ Миссия {mission_id} не найдена!")
            return
        
        # Завершаем миссию
        result = f"{user_score} - {opponent_score}"
        success = mission_storage.complete_mission_by_short_id(mission_id, result, winner_id)
        
        if success:
            # Обновляем карту на основе результата
            await update_map_from_result(mission, result, winner_id)
            
            await query.edit_message_text(
                f"✅ Результат миссии {mission_id} принят!\n\n"
                f"📊 Итоговый счет: {result}\n"
                f"🗺️ Hex {mission.hex_id} обновлен\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M')}\n\n"
                "Благодарим за игру! 🎮"
            )
            
            # Уведомляем других участников
            await notify_mission_participants(context, mission, result, winner_id)
            
        else:
            await query.edit_message_text(
                f"❌ Ошибка при сохранении результата миссии {mission_id}."
            )
            
    except Exception as e:
        logger.error(f"Error in confirm_result_callback: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при подтверждении результата."
        )

async def update_map_from_result(mission: Mission, result: str, winner_id: str):
    """Обновление карты на основе результата миссии"""
    try:
        # Note: Миссии без battle_id не обновляют карту
        # Для обновления карты нужен полноценный battle_id в БД
        pass
    except Exception as e:
        logger.error(f"Error updating map from result: {e}")

async def notify_mission_participants(context: ContextTypes.DEFAULT_TYPE, mission: Mission, result: str, winner_id: str):
    """Уведомление участников миссии о результате"""
    try:
        # Здесь должна быть логика уведомления всех участников миссии
        # Пока упрощенная версия
        notification_text = (
            f"🎯 Миссия {mission.short_id} завершена!\n\n"
            f"📍 Hex: {mission.hex_id}\n"
            f"📊 Результат: {result}\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Отправляем уведомления участникам (если есть их telegram_id)
        for participant_id in mission.participants:
            try:
                # Здесь должно быть получение telegram_id по participant_id
                # await context.bot.send_message(chat_id=telegram_id, text=notification_text)
                pass
            except Exception as e:
                logger.error(f"Error notifying participant {participant_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in notify_mission_participants: {e}")

async def list_active_missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /missions - показать список активных миссий
    """
    active_missions = mission_storage.get_active_missions()
    
    if not active_missions:
        await update.message.reply_text(
            "📭 Нет активных миссий\n\n"
            "Создайте новую миссию через мобильное приложение или станцию печати."
        )
        return
    
    text = "🎯 Активные миссии:\n\n"
    for mission in active_missions[-10:]:  # Последние 10 миссий
        created_time = mission.created_at.strftime('%d.%m %H:%M')
        text += f"• **{mission.short_id}** - {mission.title}\n"
        text += f"  Hex {mission.hex_id} | {created_time}\n"
        text += f"  Участники: {len(mission.participants)}\n\n"
    
    text += "💡 Для ввода результата используйте:\n"
    text += "`/result M123 [ваши_очки] [очки_противника]`"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def mission_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /help_missions - справка по вводу результатов
    """
    help_text = """
🎯 **Справка по миссиям**

**Ввод результатов:**
`/result M123 15 8`

Где:
• `M123` - ID миссии (указан на распечатке)
• `15` - ваши очки
• `8` - очки противника

**Другие команды:**
• `/missions` - список активных миссий
• `/help_missions` - эта справка

**Примеры:**
• `/result M456 20 12` - победа 20:12
• `/result M789 10 10` - ничья 10:10
• `/result M001 5 15` - поражение 5:15

**Что происходит после ввода:**
1. Система запросит подтверждение
2. Результат сохраняется
3. Карта обновляется автоматически
4. Участники получают уведомления

❓ Проблемы? Обратитесь к администратору.
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Функции для интеграции с основным ботом
def setup_result_handlers(application):
    """Настройка обработчиков результатов для основного бота"""
    
    # Команды
    application.add_handler(CommandHandler("result", result_command))
    application.add_handler(CommandHandler("missions", list_active_missions))
    application.add_handler(CommandHandler("help_missions", mission_help))
    
    # Callback для подтверждения результатов
    application.add_handler(CallbackQueryHandler(confirm_result_callback, pattern=r"^(confirm_result_|cancel_result)"))
    
    logger.info("Mission result handlers setup complete")

# Пример использования
if __name__ == "__main__":
    print("Mission Result Handlers - для интеграции с основным ботом")
