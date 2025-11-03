#!/usr/bin/env python
"""
Test Data Setup Script for Gold Trading Bot

This script creates test users, products, and balances for testing the trading system.

Usage:
    python setup_test_data.py

Run this from your Django project root with the virtual environment activated.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth.models import User
from users.models import Profile, BankAccount
from trading.models import Product


def create_test_products():
    """Create or update test products with realistic prices."""
    print("\n📦 Creating/Updating Products...")
    
    products_data = [
        {
            'product_code': 'gold',
            'name': 'طلای آبشده',
            'buy_price': Decimal('4500000'),  # 4.5M Rial/gram (we buy from user)
            'sell_price': Decimal('5000000'),  # 5M Rial/gram (we sell to user)
            'is_active': True
        },
        {
            'product_code': 'coin',
            'name': 'سکه تمام بهار آزادی',
            'buy_price': Decimal('19000000'),  # 19M Rial/coin
            'sell_price': Decimal('20000000'),  # 20M Rial/coin
            'is_active': True
        },
        {
            'product_code': 'dollar',
            'name': 'دلار آمریکا',
            'buy_price': Decimal('450000'),  # 450K Rial/dollar
            'sell_price': Decimal('500000'),  # 500K Rial/dollar
            'is_active': True
        },
    ]
    
    for data in products_data:
        product, created = Product.objects.update_or_create(
            product_code=data['product_code'],
            defaults={
                'name': data['name'],
                'buy_price': data['buy_price'],
                'sell_price': data['sell_price'],
                'is_active': data['is_active']
            }
        )
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} {product.name}")
        print(f"   Buy: {product.buy_price:,} | Sell: {product.sell_price:,}")


def create_test_user(telegram_id: str = "123456789", phone: str = "+989123456789"):
    """Create a test user with balances."""
    print(f"\n👤 Creating Test User (Telegram ID: {telegram_id})...")
    
    # Create Django user
    username = f"tg_{telegram_id}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
        }
    )
    
    if created:
        print(f"✅ Created Django user: {username}")
    else:
        print(f"🔄 User exists: {username}")
    
    # Create or update profile
    profile, created = Profile.objects.update_or_create(
        telegram_id=telegram_id,
        defaults={
            'user': user,
            'telegram_username': 'testuser',
            'phone_number': phone,
            'is_approved': True,  # Auto-approve for testing
            'rial_balance': Decimal('100000000'),  # 100M Rial
            'gold_balance_grams': Decimal('20.0'),  # 20 grams
            'coin_balance': Decimal('10'),  # 10 coins
            'dollar_balance': Decimal('500'),  # 500 dollars
        }
    )
    
    if created:
        print(f"✅ Created profile for {user.get_full_name()}")
    else:
        # Update balances for existing profile
        profile.is_approved = True
        profile.rial_balance = Decimal('100000000')
        profile.gold_balance_grams = Decimal('20.0')
        profile.coin_balance = Decimal('10')
        profile.dollar_balance = Decimal('500')
        profile.save()
        print(f"🔄 Updated profile for {user.get_full_name()}")
    
    print("\n💼 Test User Balances:")
    print(f"   💰 Rial: {profile.rial_balance:,} ریال")
    print(f"   🪙 Gold: {profile.gold_balance_grams} گرم")
    print(f"   🥇 Coin: {profile.coin_balance} عدد")
    print(f"   💵 Dollar: {profile.dollar_balance} دلار")
    
    return profile


def create_test_bank_account(profile: Profile):
    """Create a test bank account for the user."""
    print("\n🏦 Creating Test Bank Account...")
    
    bank_account, created = BankAccount.objects.get_or_create(
        profile=profile,
        account_number='1234567890123456',
        defaults={
            'bank_name': 'ملی',
            'account_holder_name': profile.user.get_full_name() or 'Test User',
            'account_type': 'SAVINGS',
            'is_verified': True,  # Auto-verify for testing
        }
    )
    
    if created:
        print(f"✅ Created bank account: {bank_account.bank_name} - ****{bank_account.account_number[-4:]}")
    else:
        # Ensure it's verified
        if not bank_account.is_verified:
            bank_account.is_verified = True
            bank_account.save()
        print(f"🔄 Bank account exists: {bank_account.bank_name} - ****{bank_account.account_number[-4:]}")
    
    return bank_account


def create_poor_test_user(telegram_id: str = "987654321", phone: str = "+989129876543"):
    """Create a test user with low balances (for testing insufficient balance scenarios)."""
    print(f"\n👤 Creating Poor Test User (Telegram ID: {telegram_id})...")
    
    username = f"tg_{telegram_id}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': 'Poor',
            'last_name': 'User',
        }
    )
    
    profile, created = Profile.objects.update_or_create(
        telegram_id=telegram_id,
        defaults={
            'user': user,
            'telegram_username': 'pooruser',
            'phone_number': phone,
            'is_approved': True,
            'rial_balance': Decimal('5000000'),  # Only 5M Rial
            'gold_balance_grams': Decimal('0.5'),  # Only 0.5 grams
            'coin_balance': Decimal('0'),  # No coins
            'dollar_balance': Decimal('10'),  # Only 10 dollars
        }
    )
    
    print(f"{'✅ Created' if created else '🔄 Updated'} poor user profile")
    print("\n💼 Poor User Balances (for testing errors):")
    print(f"   💰 Rial: {profile.rial_balance:,} ریال")
    print(f"   🪙 Gold: {profile.gold_balance_grams} گرم")
    print(f"   🥇 Coin: {profile.coin_balance} عدد")
    print(f"   💵 Dollar: {profile.dollar_balance} دلار")
    
    return profile


def display_summary():
    """Display summary of created test data."""
    print("\n" + "="*60)
    print("📊 TEST DATA SUMMARY")
    print("="*60)
    
    # Products
    products = Product.objects.filter(is_active=True)
    print(f"\n✅ Active Products: {products.count()}")
    for product in products:
        print(f"   • {product.name}")
        print(f"     Buy: {product.buy_price:,} | Sell: {product.sell_price:,}")
    
    # Users
    profiles = Profile.objects.filter(is_approved=True)
    print(f"\n✅ Approved Users: {profiles.count()}")
    for profile in profiles:
        print(f"   • {profile.get_display_name()} (TG: {profile.telegram_id})")
        print(f"     Rial: {profile.rial_balance:,}")
    
    # Bank Accounts
    bank_accounts = BankAccount.objects.filter(is_verified=True)
    print(f"\n✅ Verified Bank Accounts: {bank_accounts.count()}")
    
    print("\n" + "="*60)
    print("✅ Test data setup complete!")
    print("="*60)
    print("\n🚀 You can now start the bot and test with these users:")
    print("   • Rich User: Telegram ID 123456789")
    print("   • Poor User: Telegram ID 987654321")
    print("\n📝 Next steps:")
    print("   1. Run: python manage.py runbot")
    print("   2. Send /start to the bot from test Telegram account")
    print("   3. Follow TRADING_TESTING_GUIDE.md for test scenarios")
    print()


def main():
    """Main setup function."""
    print("="*60)
    print("🚀 GOLD BOT - TEST DATA SETUP")
    print("="*60)
    
    try:
        # Create products
        create_test_products()
        
        # Create rich test user
        rich_profile = create_test_user()
        create_test_bank_account(rich_profile)
        
        # Create poor test user
        poor_profile = create_poor_test_user()
        create_test_bank_account(poor_profile)
        
        # Display summary
        display_summary()
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

