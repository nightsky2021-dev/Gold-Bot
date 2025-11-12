"""
Test script to verify portal functionality is properly configured.

Run with: python test_bot_portal.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from bot.constants import MENU_PORTAL, CALLBACK_PORTAL_REFRESH
from bot.handlers.portal import portal_access, portal_refresh_callback, portal_info
from bot.keyboards import get_main_menu_keyboard
from trading.portal_services import PortalTokenService
from django.conf import settings

def test_portal_configuration():
    """Test all portal-related configurations."""
    
    print("=" * 60)
    print("🔍 Testing Portal Configuration")
    print("=" * 60)
    
    # Test 1: Check constants
    print("\n1. Checking Constants...")
    assert MENU_PORTAL == "🌐 پورتال وب", "Portal menu constant is incorrect"
    assert CALLBACK_PORTAL_REFRESH == "portal_refresh", "Portal refresh callback is incorrect"
    print("   ✅ Constants are correctly defined")
    
    # Test 2: Check keyboard
    print("\n2. Checking Main Menu Keyboard...")
    keyboard = get_main_menu_keyboard()
    keyboard_text = str(keyboard)
    assert MENU_PORTAL in keyboard_text, "Portal button not in main menu keyboard"
    print("   ✅ Portal button is in main menu keyboard")
    
    # Test 3: Check handlers exist
    print("\n3. Checking Portal Handlers...")
    assert callable(portal_access), "portal_access handler is not callable"
    assert callable(portal_refresh_callback), "portal_refresh_callback is not callable"
    assert callable(portal_info), "portal_info is not callable"
    print("   ✅ All portal handlers are defined and callable")
    
    # Test 4: Check services
    print("\n4. Checking Portal Services...")
    assert hasattr(PortalTokenService, 'generate_token'), "PortalTokenService.generate_token not found"
    assert hasattr(PortalTokenService, 'validate_token'), "PortalTokenService.validate_token not found"
    print("   ✅ Portal services are available")
    
    # Test 5: Check settings
    print("\n5. Checking Settings...")
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        print("   ⚠️  WARNING: TELEGRAM_BOT_TOKEN is not set!")
        print("      Set it in your environment or .env file")
    else:
        print(f"   ✅ Bot token is configured (length: {len(bot_token)})")
    
    portal_url = getattr(settings, 'PORTAL_BASE_URL', None)
    if portal_url:
        print(f"   ✅ Portal base URL: {portal_url}")
    else:
        print("   ⚠️  WARNING: PORTAL_BASE_URL is not set!")
    
    # Test 6: Check imports in runbot
    print("\n6. Checking Bot Command Registration...")
    try:
        from bot.management.commands.runbot import Command
        print("   ✅ Bot command module loads successfully")
    except Exception as e:
        print(f"   ❌ ERROR loading bot command: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("   1. Make sure TELEGRAM_BOT_TOKEN is set in your environment")
    print("   2. Run: python manage.py runbot")
    print("   3. In Telegram, click the '🌐 پورتال وب' button")
    print("   4. You should receive a portal access link")
    print("\n💡 If the button still doesn't appear:")
    print("   - Send /start command to the bot to refresh the keyboard")
    print("   - Make sure you're using the correct bot token")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_portal_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

