"""
Test script to check ConversationHandler configuration
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from handlers import conv_handler, SETTINGS, MAIN_MENU

def test_conversation_handler():
    """Test that the conversation handler is properly configured."""
    
    print("Testing ConversationHandler configuration...")
    print("=" * 50)
    
    # Check if SETTINGS state exists
    if SETTINGS in conv_handler.states:
        print(f"✅ SETTINGS state ({SETTINGS}) exists")
        
        # Check handlers in SETTINGS state
        settings_handlers = conv_handler.states[SETTINGS]
        print(f"📋 Found {len(settings_handlers)} handlers in SETTINGS state:")
        
        for i, handler in enumerate(settings_handlers):
            handler_type = type(handler).__name__
            pattern = getattr(handler, 'pattern', 'No pattern')
            callback_name = getattr(handler.callback, '__name__', 'Unknown')
            
            print(f"  {i+1}. {handler_type}")
            print(f"     Pattern: {pattern}")
            print(f"     Callback: {callback_name}")
            
            # Check if there's a handler for 'start' pattern
            if hasattr(handler, 'pattern') and handler.pattern:
                import re
                if re.match(handler.pattern, 'start'):
                    print(f"     ✅ This handler matches 'start' callback_data")
    else:
        print(f"❌ SETTINGS state not found in conversation handler")
    
    print("\n" + "=" * 50)
    print("Available states:", list(conv_handler.states.keys()))

if __name__ == "__main__":
    test_conversation_handler()