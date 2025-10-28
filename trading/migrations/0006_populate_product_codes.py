# Generated manually to populate product codes

from django.db import migrations


def populate_product_codes(apps, schema_editor):
    """
    Populate product_code for existing products based on their names.
    """
    Product = apps.get_model('trading', 'Product')
    
    # Mapping of product name patterns to product codes
    product_mappings = {
        'gold': ['طلا', 'gold'],
        'coin': ['سکه', 'coin'],
        'dollar': ['دلار', 'dollar'],
    }
    
    for product in Product.objects.filter(product_code__isnull=True):
        # Try to match product name to a product code
        assigned = False
        product_name_lower = product.name.lower()
        
        for code, keywords in product_mappings.items():
            if any(keyword in product_name_lower for keyword in keywords):
                product.product_code = code
                product.save()
                assigned = True
                break
        
        # If no match found, assign based on position (fallback)
        if not assigned:
            # Just assign 'gold' as a safe default
            product.product_code = 'gold'
            product.save()


def reverse_populate(apps, schema_editor):
    """
    Reverse migration - set product codes back to null.
    """
    Product = apps.get_model('trading', 'Product')
    Product.objects.all().update(product_code=None)


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0005_product_created_at'),
    ]

    operations = [
        migrations.RunPython(populate_product_codes, reverse_populate),
    ]

