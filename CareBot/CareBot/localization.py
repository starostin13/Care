"""
Localization module for CareBot.
Handles text translations based on user's language preference.
"""

import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Localization using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Localization using REAL SQLite helper")
import logging

logger = logging.getLogger(__name__)

# Cache for texts to avoid frequent database queries
_text_cache = {}

async def get_user_language(user_telegram_id):
    """Get user's language preference from database."""
    try:
        settings = await sqllite_helper.get_settings(user_telegram_id)
        if settings and len(settings) >= 3:
            return settings[2] if settings[2] else 'ru'
        return 'ru'  # Default to Russian
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'ru'

async def get_text(key, language='ru', **kwargs):
    """
    Get localized text by key and language.
    
    Args:
        key: Text key (e.g., 'welcome_message')
        language: Language code ('ru', 'en', etc.)
        **kwargs: Variables to format into the text
        
    Returns:
        Formatted text string
    """
    try:
        # Check cache first
        cache_key = f"{key}_{language}"
        if cache_key not in _text_cache:
            # Load from database
            text = await sqllite_helper.get_text_by_key(key, language)
            if text is None:
                # Fallback to Russian if text not found
                if language != 'ru':
                    text = await sqllite_helper.get_text_by_key(key, 'ru')
                
                # If still not found, return the key as fallback
                if text is None:
                    logger.warning(f"Text not found for key: {key}, language: {language}")
                    return f"[{key}]"
            
            _text_cache[cache_key] = text
        
        text = _text_cache[cache_key]
        
        # Format text with provided variables
        if kwargs:
            return text.format(**kwargs)
        return text
        
    except Exception as e:
        logger.error(f"Error getting text for key {key}: {e}")
        return f"[{key}]"

async def get_text_for_user(user_telegram_id, key, **kwargs):
    """
    Get localized text for a specific user based on their language preference.
    
    Args:
        user_telegram_id: User's Telegram ID
        key: Text key
        **kwargs: Variables to format into the text
        
    Returns:
        Formatted text string in user's language
    """
    language = await get_user_language(user_telegram_id)
    return await get_text(key, language, **kwargs)

def clear_cache():
    """Clear the text cache. Useful for testing or after text updates."""
    global _text_cache
    _text_cache.clear()

# Convenience functions for common text patterns
async def get_button_text(button_key, language='ru', **kwargs):
    """Get text for a button."""
    return await get_text(f"btn_{button_key}", language, **kwargs)

async def get_button_text_for_user(user_telegram_id, button_key, **kwargs):
    """Get button text for a specific user."""
    language = await get_user_language(user_telegram_id)
    return await get_button_text(button_key, language, **kwargs)

async def get_message_text(message_key, language='ru', **kwargs):
    """Get text for a message."""
    return await get_text(message_key, language, **kwargs)

async def get_message_text_for_user(user_telegram_id, message_key, **kwargs):
    """Get message text for a specific user."""
    language = await get_user_language(user_telegram_id)
    return await get_message_text(message_key, language, **kwargs)