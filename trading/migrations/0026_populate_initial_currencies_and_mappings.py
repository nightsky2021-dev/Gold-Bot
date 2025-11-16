# Generated manually for dynamic wallet system - data migration

from django.db import migrations
from decimal import Decimal


def populate_currencies_and_mappings(apps, schema_editor):
    """Populate initial currencies and create product-to-currency mappings."""
    Currency = apps.get_model('trading', 'Currency')
    Product = apps.get_model('trading', 'Product')
    ProductCurrencyMapping = apps.get_model('trading', 'ProductCurrencyMapping')
    
    # Create initial currencies
    currencies_data = [
        {
            'code': 'RIAL',
            'name': 'ریال',
            'display_name': 'ریال',
            'display_symbol': 'ریال',
            'decimal_places': 0,
            'display_order': 1,
            'is_active': True,
        },
        {
            'code': 'GOLD',
            'name': 'طلا',
            'display_name': 'طلا',
            'display_symbol': 'گرم',
            'decimal_places': 4,
            'display_order': 2,
            'is_active': True,
        },
        {
            'code': 'COIN',
            'name': 'سکه',
            'display_name': 'سکه',
            'display_symbol': 'عدد',
            'decimal_places': 0,
            'display_order': 3,
            'is_active': True,
        },
        {
            'code': 'DOLLAR',
            'name': 'دلار',
            'display_name': 'دلار',
            'display_symbol': '$',
            'decimal_places': 2,
            'display_order': 4,
            'is_active': True,
        },
    ]
    
    created_currencies = {}
    for currency_data in currencies_data:
        currency, created = Currency.objects.get_or_create(
            code=currency_data['code'],
            defaults=currency_data
        )
        created_currencies[currency_data['code']] = currency
    
    # Create product-to-currency mappings based on existing product codes
    # This uses the same logic as OrderService.get_product_currency_type()
    product_code_to_currency = {
        'gold': 'GOLD',
        'coin': 'COIN',
        'dollar': 'DOLLAR',
    }
    
    # Map each product to its currency
    for product in Product.objects.all():
        currency_code = product_code_to_currency.get(product.product_code, 'GOLD')
        currency = created_currencies.get(currency_code)
        
        if currency:
            # Create primary mapping
            ProductCurrencyMapping.objects.get_or_create(
                product=product,
                currency=currency,
                defaults={'is_primary': True}
            )


def reverse_populate_currencies_and_mappings(apps, schema_editor):
    """Reverse migration - remove currencies and mappings."""
    Currency = apps.get_model('trading', 'Currency')
    ProductCurrencyMapping = apps.get_model('trading', 'ProductCurrencyMapping')
    
    # Delete all mappings
    ProductCurrencyMapping.objects.all().delete()
    
    # Delete all currencies
    Currency.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0025_add_dynamic_wallet_models'),
    ]

    operations = [
        migrations.RunPython(
            populate_currencies_and_mappings,
            reverse_populate_currencies_and_mappings
        ),
    ]
