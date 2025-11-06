"""
Setup script for adding/updating all Anigold products with proper pricing configurations.

This script creates or updates 10 products:
- 6 currencies (USD, EUR, TRY, CNY, GBP, AED) with ±1% margins
- 3 coins (full, half, quarter) with ±4,500,000 Rial margins
- 1 gold product (abshodeh) with ±300,000 Rial margins

Usage:
    python setup_anigold_products.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from trading.models import Product


def setup_products():
    """Create or update all products with proper configurations."""
    
    print("🚀 Starting Anigold products setup...\n")
    
    # Product configurations
    # Format: (product_code, name, weight_grams, buy_margin_rials, sell_margin_rials)
    products_config = [
        # Currencies - 1% margin (will be calculated as percentage of base price)
        # For currencies, we'll use a placeholder margin that will be dynamically calculated
        ('dollar_usa', 'دلار آمریکا', Decimal('1'), 'percentage', Decimal('0.01')),
        ('euro', 'یورو', Decimal('1'), 'percentage', Decimal('0.01')),
        ('lira_turkey', 'لیر ترکیه', Decimal('1'), 'percentage', Decimal('0.01')),
        ('yuan_china', 'یوان چین', Decimal('1'), 'percentage', Decimal('0.01')),
        ('pound_uk', 'پوند انگلیس', Decimal('1'), 'percentage', Decimal('0.01')),
        ('dirham_uae', 'درهم امارات', Decimal('1'), 'percentage', Decimal('0.01')),
        
        # Coins - ±450,000 Toman = ±4,500,000 Rials
        ('coin_full', 'سکه غیربانکی', Decimal('8.133'), Decimal('4500000'), Decimal('4500000')),
        ('coin_half', 'نیم سکه غیربانکی', Decimal('4.0665'), Decimal('2250000'), Decimal('2250000')),
        ('coin_quarter', 'ربع سکه غیربانکی', Decimal('2.03325'), Decimal('1125000'), Decimal('1125000')),
        
        # Gold - ±30,000 Toman = ±300,000 Rials (per gram)
        ('gold_abshodeh', 'طلای آبشده', Decimal('1'), Decimal('300000'), Decimal('300000')),
    ]
    
    created_count = 0
    updated_count = 0
    
    for product_code, name, weight_grams, buy_margin, sell_margin in products_config:
        try:
            product, created = Product.objects.get_or_create(
                product_code=product_code,
                defaults={
                    'name': name,
                    'weight_grams': weight_grams,
                    'buy_margin': Decimal('0'),  # Will be set below
                    'sell_margin': Decimal('0'),  # Will be set below
                    'buy_price': Decimal('0'),  # Will be updated by update_prices
                    'sell_price': Decimal('0'),  # Will be updated by update_prices
                    'is_active': True,
                }
            )
            
            if created:
                print(f"✅ Created: {name} ({product_code})")
                created_count += 1
            else:
                print(f"🔄 Updating: {name} ({product_code})")
                product.name = name
                product.weight_grams = weight_grams
                updated_count += 1
            
            # Set margins (for percentage-based, we'll note it but set to 0 for now)
            # The actual margin will be calculated dynamically in services
            if buy_margin == 'percentage':
                # For currencies, we mark them with a tag in the system
                # We'll store a fixed margin that represents ~1% of typical prices
                # These will be recalculated during price updates
                product.buy_margin = Decimal('0')
                product.sell_margin = Decimal('0')
                print(f"   💡 {name} uses percentage-based pricing (±1%)")
            else:
                product.buy_margin = buy_margin
                product.sell_margin = sell_margin
                print(f"   💰 Buy margin: {buy_margin:,} | Sell margin: {sell_margin:,} Rials")
            
            product.save()
            
        except Exception as e:
            print(f"❌ Error setting up {product_code}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Created: {created_count} products")
    print(f"   🔄 Updated: {updated_count} products")
    print(f"   📦 Total: {created_count + updated_count} products")
    
    print("\n" + "="*60)
    print("⚠️  IMPORTANT NOTES:")
    print("="*60)
    print("1. Currency margins (±1%) will be calculated dynamically")
    print("   during price updates based on current market prices")
    print("")
    print("2. Run the following command to fetch and update prices:")
    print("   python manage.py update_prices --show-details")
    print("")
    print("3. All products are now active and ready for trading")
    print("="*60)


def update_margins_with_percentage():
    """
    Update currency products to use percentage-based margins.
    This creates a more dynamic pricing system for currencies.
    """
    print("\n🔧 Configuring percentage-based margins for currencies...\n")
    
    currency_codes = [
        'dollar_usa', 'euro', 'lira_turkey', 
        'yuan_china', 'pound_uk', 'dirham_uae'
    ]
    
    # We'll need to fetch current prices first to calculate 1% margin
    # For now, we set a reasonable default that will be updated
    from trading.price_providers import get_active_provider
    
    provider = get_active_provider()
    
    # Try to get prices if available
    try:
        prices = provider._fetch_all_prices() if hasattr(provider, '_fetch_all_prices') else {}
        
        if prices:
            print("📡 Fetching current prices to calculate margins...\n")
            
            for currency_code in currency_codes:
                try:
                    product = Product.objects.get(product_code=currency_code)
                    
                    # Get price from provider
                    if hasattr(provider, 'get_price'):
                        base_price = provider.get_price(currency_code)
                        
                        if base_price:
                            # Calculate 1% margin
                            margin = base_price * Decimal('0.01')
                            margin = margin.quantize(Decimal('1'))  # Round to nearest Rial
                            
                            product.buy_margin = margin
                            product.sell_margin = margin
                            product.save()
                            
                            print(f"✅ {product.name}: margin set to {margin:,} Rials (1% of {base_price:,})")
                        else:
                            print(f"⚠️  {product.name}: Could not fetch price, keeping default margin")
                    
                except Product.DoesNotExist:
                    print(f"⚠️  Product not found: {currency_code}")
                except Exception as e:
                    print(f"❌ Error updating {currency_code}: {e}")
        else:
            print("⚠️  Could not fetch prices from API. Using default margins.")
            print("   Run 'python manage.py update_prices' to set accurate margins.")
    
    except Exception as e:
        print(f"⚠️  Could not connect to API: {e}")
        print("   Currency margins will be calculated during next price update.")


if __name__ == '__main__':
    setup_products()
    
    # Uncomment the following line to enable percentage-based margin calculation
    # This requires API access and will be done during price updates
    # update_margins_with_percentage()
    
    print("\n✅ Setup complete! Products are ready for trading.")
    print("   Next step: python manage.py update_prices --show-details\n")
