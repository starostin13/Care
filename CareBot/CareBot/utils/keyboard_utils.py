#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
import sqllite_helper

def build_settings_keyboard():
    # Define the settings buttons
    buttons = [
        [KeyboardButton("Настройки профиля")],
        [KeyboardButton("Уведомления")],
        [KeyboardButton("Помощь")],
        [KeyboardButton("Главное меню")]
    ]

    # Return a ReplyKeyboardMarkup with the defined buttons
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def get_crusaid_main_menu() -> ReplyKeyboardMarkup:
    """Returns the main Crusade menu with 'Play' and 'View Players' options."""
    menu = [
        [KeyboardButton("Хочу играть")],
        [KeyboardButton("Кто уже вписался")]
    ]
    return ReplyKeyboardMarkup(menu, resize_keyboard=True)

async def get_keyboard_rules_keyboard_for_user(user_id) -> list:
    """Constructs a keyboard with rules options based on the user’s ID."""
    rules = await sqllite_helper.get_rules_for_user(user_id)
    buttons = [[InlineKeyboardButton(rule, callback_data=f"rule_{rule}")] for rule in rules]
    return buttons

async def this_week(user_id) -> list:
    """Constructs a keyboard with weekly schedule options for the user."""
    schedule = await sqllite_helper.get_week_schedule(user_id)
    buttons = [
        [InlineKeyboardButton(f"{entry['date']} - {entry['time']}", callback_data=f"{entry['date']},{entry['rule']}")]
        for entry in schedule
    ]
    return buttons
