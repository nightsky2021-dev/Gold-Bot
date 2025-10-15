"""
Management command to update gold prices.

Run with: python manage.py update_prices

This command should be scheduled to run periodically (e.g., via cron job)
to fetch latest gold prices from an external API and update the database.
"""

import logging
from typing import Dict, Any, List
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from trading.models import Product

logger = logging.getLogger('trading')


class Command(BaseCommand):
    """
    Management command to update gold product prices.
    
    This is a template implementation. In production, you should:
    1. Integrate with a real gold price API (e.g., Tgju.org API for Iran)
    2. Handle API errors and retries
    3. Add validation for price changes (e.g., alert if price changes > X%)
    4. Log all price updates for audit trail
    """
    
    help = 'Updates gold prices from external API'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        
        parser.add_argument(
            '--source',
            type=str,
            default='mock',
            help='Price source: mock, tgju, or custom',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        dry_run = options['dry_run']
        source = options['source']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting price update from source: {source}')
        )
        
        try:
            # Fetch prices based on source
            if source == 'mock':
                prices = self.fetch_mock_prices()
            elif source == 'tgju':
                prices = self.fetch_tgju_prices()
            else:
                self.stdout.write(
                    self.style.ERROR(f'Unknown source: {source}')
                )
                return
            
            # Update prices
            updated_count = self.update_product_prices(prices, dry_run)
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'DRY RUN: Would have updated {updated_count} products'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated {updated_count} products'
                    )
                )
                
        except Exception as e:
            logger.error(f'Error updating prices: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            raise

    def fetch_mock_prices(self) -> Dict[str, Dict[str, Decimal]]:
        """
        Fetch mock prices for testing.
        
        Returns:
            Dictionary mapping product slugs to price dictionaries.
        """
        self.stdout.write('Fetching mock prices...')
        
        # These are example prices for testing
        # In production, replace with actual API calls
        return {
            'سکه-بهار-آزادی': {
                'buy_price': Decimal('65000000'),  # Price we buy from customer (per coin)
                'sell_price': Decimal('68000000'),  # Price we sell to customer (per coin)
            },
            'طلای-18-عیار': {
                'buy_price': Decimal('2500000'),  # Per gram
                'sell_price': Decimal('2600000'),  # Per gram
            },
            'طلای-24-عیار': {
                'buy_price': Decimal('3300000'),  # Per gram
                'sell_price': Decimal('3450000'),  # Per gram
            },
        }

    def fetch_tgju_prices(self) -> Dict[str, Dict[str, Decimal]]:
        """
        Fetch prices from Tgju.org API (Iranian gold price source).
        
        This is a placeholder. Implement actual API integration here.
        
        Example API endpoint: https://api.tgju.org/v1/market/indicator/summary-table-data/gold
        
        Returns:
            Dictionary mapping product slugs to price dictionaries.
        """
        self.stdout.write('Fetching prices from Tgju.org API...')
        
        # TODO: Implement actual API call
        # import requests
        # response = requests.get('https://api.tgju.org/v1/market/indicator/summary-table-data/gold')
        # data = response.json()
        # Parse and return prices
        
        # For now, return mock data
        self.stdout.write(
            self.style.WARNING('Tgju integration not implemented yet, using mock data')
        )
        return self.fetch_mock_prices()

    @transaction.atomic
    def update_product_prices(
        self,
        prices: Dict[str, Dict[str, Decimal]],
        dry_run: bool = False
    ) -> int:
        """
        Update product prices in the database.
        
        Args:
            prices: Dictionary of product prices
            dry_run: If True, don't actually save changes
            
        Returns:
            Number of products updated
        """
        updated_count = 0
        
        for slug, price_data in prices.items():
            try:
                # Try to find product by slug
                try:
                    product = Product.objects.get(slug=slug)
                except Product.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Product not found: {slug} - skipping'
                        )
                    )
                    continue
                
                old_buy = product.buy_price
                old_sell = product.sell_price
                new_buy = price_data['buy_price']
                new_sell = price_data['sell_price']
                
                # Calculate price change percentage
                buy_change_pct = self.calculate_change_percentage(old_buy, new_buy)
                sell_change_pct = self.calculate_change_percentage(old_sell, new_sell)
                
                # Log significant changes (> 5%)
                if abs(buy_change_pct) > 5 or abs(sell_change_pct) > 5:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Significant price change for {product.name}: '
                            f'Buy: {buy_change_pct:+.2f}%, Sell: {sell_change_pct:+.2f}%'
                        )
                    )
                
                if not dry_run:
                    product.buy_price = new_buy
                    product.sell_price = new_sell
                    product.save()
                    
                    logger.info(
                        f'Updated {product.name}: '
                        f'Buy: {old_buy} -> {new_buy}, '
                        f'Sell: {old_sell} -> {new_sell}'
                    )
                else:
                    self.stdout.write(
                        f'Would update {product.name}: '
                        f'Buy: {old_buy} -> {new_buy} ({buy_change_pct:+.2f}%), '
                        f'Sell: {old_sell} -> {new_sell} ({sell_change_pct:+.2f}%)'
                    )
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f'Error updating product {slug}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'Error updating {slug}: {str(e)}')
                )
                continue
        
        return updated_count

    @staticmethod
    def calculate_change_percentage(old_value: Decimal, new_value: Decimal) -> float:
        """Calculate percentage change between two values."""
        if old_value == 0:
            return 0.0
        return float((new_value - old_value) / old_value * 100)
