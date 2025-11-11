#!/usr/bin/env python
"""
Fix products for Anigold API compatibility:
1. Set proper margins for all products
2. Fix invalid slugs (remove Persian characters)
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from trading.models import Product
from decimal import Decimal

def fix_products():
    """Fix all products: margins and slugs."""
    
    print("=" * 60)
    print("🔧 Fixing Products for Anigold API")
    print("=" * 60)
    print()
    
    # Product configuration: reasonable margins as percentage of typical price
    product_configs = {
        # Currencies - 1% margin seems reasonable
        'dollar_usa': {'slug': 'dollar-usa', 'margin_percent': 0.01},
        'euro': {'slug': 'euro', 'margin_percent': 0.01},
        'lira_turkey': {'slug': 'lira-turkey', 'margin_percent': 0.01},
        'yuan_china': {'slug': 'yuan-china', 'margin_percent': 0.01},
        'pound_uk': {'slug': 'pound-uk', 'margin_percent': 0.01},
        'dirham_uae': {'slug': 'dirham-uae', 'margin_percent': 0.01},
        
        # Coins - already have good margins, just fix slug
        'coin_full': {'slug': 'coin-full', 'margin_percent': None},
        'coin_half': {'slug': 'coin-half', 'margin_percent': None},
        'coin_quarter': {'slug': 'coin-quarter', 'margin_percent': None},
        
        # Gold - already has good margin, just fix slug  
        'gold_abshodeh': {'slug': 'gold-abshodeh', 'margin_percent': None},
    }
    
    for product_code, config in product_configs.items():
        try:
            product = Product.objects.get(product_code=product_code)
            
            print(f"📦 {product.name} ({product_code})")
            print(f"   Old slug: {product.slug}")
            
            # Fix slug
            product.slug = config['slug']
            print(f"   New slug: {product.slug}")
            
            # Fix margins if needed
            if config['margin_percent'] is not None:
                # Get current price or use default
                current_price = product.sell_price if product.sell_price > 0 else Decimal('100000')
                margin = (current_price * Decimal(str(config['margin_percent']))).quantize(Decimal('1'))
                
                # Ensure minimum margin of 500 Rials each (1000 total)
                if margin < 500:
                    margin = Decimal('500')
                
                product.buy_margin = margin
                product.sell_margin = margin
                
                # Also update the prices to be valid (buy < sell)
                # Set temporary prices that will be updated by API
                if product.buy_price == product.sell_price or product.buy_price >= product.sell_price:
                    # Fetch from API or use reasonable defaults
                    if product_code in ['dollar_usa', 'euro', 'pound_uk']:
                        base = Decimal('100000')  # Currencies ~ 100k
                    elif product_code in ['yuan_china', 'lira_turkey']:
                        base = Decimal('10000')  # Smaller currencies
                    elif product_code == 'dirham_uae':
                        base = Decimal('30000')
                    else:
                        base = current_price if current_price > 0 else Decimal('100000')
                    
                    product.buy_price = base - margin
                    product.sell_price = base + margin
                    print(f"   Prices set: buy={product.buy_price:,}, sell={product.sell_price:,}")
                
                print(f"   Margins set: {margin:,} Rials each ({config['margin_percent']*100}%)")
            else:
                print(f"   Keeping existing margins: buy={product.buy_margin:,}, sell={product.sell_margin:,}")
            
            # Save
            product.save()
            print(f"   ✅ Saved successfully")
            print()
            
        except Product.DoesNotExist:
            print(f"   ⚠️  Product not found: {product_code}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    print("=" * 60)
    print("✅ Product fix completed!")
    print()
    print("Next step: Run 'python manage.py update_prices'")
    print("=" * 60)


if __name__ == '__main__':
    fix_products()

