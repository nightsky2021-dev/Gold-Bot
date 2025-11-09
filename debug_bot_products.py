#!/usr/bin/env python
"""Debug script to check exactly what the bot sees."""
import os
import django
import asyncio
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('debug')

# Now import models and services
from asgiref.sync import sync_to_async
from trading.services import ProductService
from trading.models import Product

async def debug_products():
    """Debug product fetching exactly as bot does."""
    
    # Test 1: Direct query
    print("=" * 60)
    print("TEST 1: Direct Product.objects query")
    print("=" * 60)
    all_products = await sync_to_async(lambda: list(Product.objects.all()))()
    print(f"Total products in database: {len(all_products)}")
    for p in all_products:
        print(f"  - {p.name}: is_active={p.is_active}, product_code={p.product_code}")
    
    # Test 2: Filter by is_active
    print("\n" + "=" * 60)
    print("TEST 2: Products with is_active=True")
    print("=" * 60)
    active_products = await sync_to_async(lambda: list(Product.objects.filter(is_active=True)))()
    print(f"Active products: {len(active_products)}")
    for p in active_products:
        print(f"  - {p.name}")
    
    # Test 3: Using ProductService (exactly what bot uses)
    print("\n" + "=" * 60)
    print("TEST 3: ProductService.get_active_products() (what bot uses)")
    print("=" * 60)
    service_products = await sync_to_async(ProductService.get_active_products)()
    print(f"Products from service: {len(service_products) if service_products else 0}")
    
    if not service_products:
        print("❌ BUG FOUND: ProductService returns empty!")
    else:
        for p in service_products:
            print(f"  ✅ {p.name}")
    
    # Test 4: Check the actual service implementation
    print("\n" + "=" * 60)
    print("TEST 4: Checking ProductService implementation")
    print("=" * 60)
    
    # Call it synchronously to see actual results
    sync_products = ProductService.get_active_products()
    print(f"Sync call result type: {type(sync_products)}")
    print(f"Sync call result: {sync_products}")
    print(f"Is it a list? {isinstance(sync_products, list)}")
    print(f"Length: {len(sync_products) if sync_products else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(debug_products())

