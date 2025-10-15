#!/usr/bin/env python
"""
Script to setup sample data for development/testing.

Run with: python setup_sample_data.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Profile
from trading.models import Product
from decimal import Decimal


def create_sample_products():
    """Create sample gold products."""
    products_data = [
        {
            'name': 'سکه بهار آزادی',
            'buy_price': Decimal('65000000'),
            'sell_price': Decimal('68000000'),
            'is_active': True,
        },
        {
            'name': 'نیم سکه',
            'buy_price': Decimal('35000000'),
            'sell_price': Decimal('36500000'),
            'is_active': True,
        },
        {
            'name': 'ربع سکه',
            'buy_price': Decimal('19000000'),
            'sell_price': Decimal('19800000'),
            'is_active': True,
        },
        {
            'name': 'طلای 18 عیار',
            'buy_price': Decimal('2500000'),
            'sell_price': Decimal('2600000'),
            'is_active': True,
        },
        {
            'name': 'طلای 24 عیار',
            'buy_price': Decimal('3300000'),
            'sell_price': Decimal('3450000'),
            'is_active': True,
        },
    ]
    
    print("Creating sample products...")
    created_count = 0
    
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            defaults=product_data
        )
        if created:
            print(f"  ✓ Created: {product.name}")
            created_count += 1
        else:
            print(f"  - Already exists: {product.name}")
    
    print(f"\nCreated {created_count} new products.")
    return created_count


def create_test_user():
    """Create a test approved user for testing bot."""
    print("\nCreating test user...")
    
    try:
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'first_name': 'علی',
                'last_name': 'احمدی',
                'email': 'test@example.com'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print("  ✓ Created user: test_user")
        else:
            print("  - User already exists: test_user")
        
        # Create profile if doesn't exist
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'telegram_id': '123456789',  # Fake ID for testing
                'telegram_username': 'test_user',
                'phone_number': '+989121234567',
                'is_approved': True,
                'rial_balance': Decimal('100000000'),  # 100M Rial
                'gold_balance_grams': Decimal('10.5000'),  # 10.5 grams
            }
        )
        
        if created:
            print("  ✓ Created profile with sample balances")
        else:
            print("  - Profile already exists")
            
        return user, profile
        
    except Exception as e:
        print(f"  ✗ Error creating test user: {str(e)}")
        return None, None


def main():
    """Main function."""
    print("=" * 60)
    print("Gold Shop - Sample Data Setup")
    print("=" * 60)
    
    # Create products
    create_sample_products()
    
    # Create test user
    create_test_user()
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Run migrations: python manage.py migrate")
    print("3. Start Django server: python manage.py runserver")
    print("4. Access admin panel: http://localhost:8000/admin")
    print("5. Start bot: python manage.py runbot")
    print("\nFor testing, use:")
    print("  Username: test_user")
    print("  Password: testpass123")
    print("=" * 60)


if __name__ == '__main__':
    main()
