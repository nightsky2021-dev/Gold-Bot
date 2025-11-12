"""
Management command to reset and clean all user data across the platform.

This command removes all user-related data from the database including:
- User profiles
- Bank accounts
- Orders and transactions
- Withdrawal requests
- Portal access tokens
- Django user accounts (except superusers by default)

Usage:
    python manage.py reset_user_data
    python manage.py reset_user_data --include-superusers
    python manage.py reset_user_data --no-input
    python manage.py reset_user_data --dry-run
"""

import logging
from decimal import Decimal
from typing import Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from users.models import Profile, BankAccount
from trading.models import (
    Order,
    Transaction,
    WithdrawRequest,
    PortalAccessToken,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to reset all user data."""
    
    help = 'Reset and clean all user data across bot, portal, and admin panel'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--include-superusers',
            action='store_true',
            help='Also delete superuser accounts (use with caution!)',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompts (dangerous!)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        include_superusers = options['include_superusers']
        no_input = options['no_input']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING(
            "\n" + "="*70 + "\n"
            "  USER DATA RESET UTILITY\n"
            "  This will delete ALL user data from the database!\n"
            "="*70 + "\n"
        ))
        
        # Get statistics before deletion
        stats = self._get_statistics(include_superusers)
        
        # Display what will be deleted
        self._display_statistics(stats)
        
        # Confirmation
        if not no_input and not dry_run:
            confirm = input("\nAre you sure you want to DELETE all this data? Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS("Operation cancelled."))
                return
            
            # Double confirmation for safety
            confirm2 = input("This action CANNOT be undone! Type 'DELETE ALL' to proceed: ")
            if confirm2 != 'DELETE ALL':
                self.stdout.write(self.style.SUCCESS("Operation cancelled."))
                return
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                "\n[DRY RUN] No data was actually deleted.\n"
            ))
            return
        
        # Perform the deletion
        try:
            with transaction.atomic():
                deleted_stats = self._delete_all_user_data(include_superusers)
                self._display_deletion_results(deleted_stats)
                
            self.stdout.write(self.style.SUCCESS(
                "\n" + "="*70 + "\n"
                "  ✓ All user data has been successfully deleted!\n"
                "="*70 + "\n"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n✗ Error during deletion: {str(e)}\n"
            ))
            raise CommandError(f"Failed to delete user data: {str(e)}")
    
    def _get_statistics(self, include_superusers: bool) -> Dict[str, int]:
        """Get statistics about data to be deleted."""
        
        # User queryset
        if include_superusers:
            users = User.objects.all()
        else:
            users = User.objects.filter(is_superuser=False)
        
        stats = {
            'users': users.count(),
            'superusers': User.objects.filter(is_superuser=True).count() if not include_superusers else 0,
            'profiles': Profile.objects.count(),
            'bank_accounts': BankAccount.objects.count(),
            'orders': Order.objects.count(),
            'transactions': Transaction.objects.count(),
            'withdraw_requests': WithdrawRequest.objects.count(),
            'portal_tokens': PortalAccessToken.objects.count(),
        }
        
        # Calculate financial statistics
        stats['total_rial_balance'] = sum(
            profile.rial_balance + profile.frozen_rial_balance 
            for profile in Profile.objects.all()
        )
        stats['total_gold_balance'] = sum(
            profile.gold_balance_grams + profile.frozen_gold_balance 
            for profile in Profile.objects.all()
        )
        stats['total_coin_balance'] = sum(
            profile.coin_balance + profile.frozen_coin_balance 
            for profile in Profile.objects.all()
        )
        stats['total_dollar_balance'] = sum(
            profile.dollar_balance + profile.frozen_dollar_balance 
            for profile in Profile.objects.all()
        )
        
        return stats
    
    def _display_statistics(self, stats: Dict[str, Any]) -> None:
        """Display statistics about what will be deleted."""
        self.stdout.write("\n" + self.style.WARNING("Data to be deleted:") + "\n")
        
        self.stdout.write(f"  👥 Users (Django accounts): {stats['users']}")
        if stats['superusers'] > 0:
            self.stdout.write(f"     ⚠️  Superusers will be PRESERVED: {stats['superusers']}")
        
        self.stdout.write(f"\n  📋 User Profiles: {stats['profiles']}")
        self.stdout.write(f"  🏦 Bank Accounts: {stats['bank_accounts']}")
        self.stdout.write(f"  📦 Orders: {stats['orders']}")
        self.stdout.write(f"  💳 Transactions: {stats['transactions']}")
        self.stdout.write(f"  💰 Withdraw Requests: {stats['withdraw_requests']}")
        self.stdout.write(f"  🔑 Portal Access Tokens: {stats['portal_tokens']}")
        
        self.stdout.write("\n" + self.style.WARNING("Financial Data to be Reset:") + "\n")
        self.stdout.write(f"  💵 Total Rial Balance: {stats['total_rial_balance']:,.0f} ریال")
        self.stdout.write(f"  🪙 Total Gold Balance: {stats['total_gold_balance']:,.4f} گرم")
        self.stdout.write(f"  🥇 Total Coin Balance: {stats['total_coin_balance']:,.0f} عدد")
        self.stdout.write(f"  💵 Total Dollar Balance: ${stats['total_dollar_balance']:,.2f}")
    
    def _delete_all_user_data(self, include_superusers: bool) -> Dict[str, int]:
        """Delete all user data from the database."""
        deleted_stats = {}
        
        self.stdout.write("\n" + self.style.WARNING("Starting deletion...") + "\n")
        
        # 1. Delete Portal Access Tokens
        self.stdout.write("  🔑 Deleting portal access tokens...")
        count = PortalAccessToken.objects.all().delete()[0]
        deleted_stats['portal_tokens'] = count
        self.stdout.write(self.style.SUCCESS(f"     ✓ Deleted {count} portal tokens"))
        
        # 2. Delete Withdraw Requests
        self.stdout.write("  💰 Deleting withdraw requests...")
        count = WithdrawRequest.objects.all().delete()[0]
        deleted_stats['withdraw_requests'] = count
        self.stdout.write(self.style.SUCCESS(f"     ✓ Deleted {count} withdraw requests"))
        
        # 3. Delete Transactions
        self.stdout.write("  💳 Deleting transactions...")
        # Delete receipt images first
        transactions = Transaction.objects.all()
        receipt_count = 0
        for txn in transactions:
            if txn.receipt_image:
                try:
                    txn.receipt_image.delete(save=False)
                    receipt_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete receipt image: {e}")
        
        count = transactions.delete()[0]
        deleted_stats['transactions'] = count
        self.stdout.write(self.style.SUCCESS(
            f"     ✓ Deleted {count} transactions ({receipt_count} receipt images)"
        ))
        
        # 4. Delete Orders
        self.stdout.write("  📦 Deleting orders...")
        count = Order.objects.all().delete()[0]
        deleted_stats['orders'] = count
        self.stdout.write(self.style.SUCCESS(f"     ✓ Deleted {count} orders"))
        
        # 5. Delete Bank Accounts
        self.stdout.write("  🏦 Deleting bank accounts...")
        count = BankAccount.objects.all().delete()[0]
        deleted_stats['bank_accounts'] = count
        self.stdout.write(self.style.SUCCESS(f"     ✓ Deleted {count} bank accounts"))
        
        # 6. Delete Profiles (this will cascade to related User objects)
        self.stdout.write("  📋 Deleting user profiles...")
        count = Profile.objects.all().delete()[0]
        deleted_stats['profiles'] = count
        self.stdout.write(self.style.SUCCESS(f"     ✓ Deleted {count} profiles"))
        
        # 7. Delete remaining User accounts (those without profiles)
        self.stdout.write("  👥 Deleting Django user accounts...")
        if include_superusers:
            users = User.objects.all()
        else:
            users = User.objects.filter(is_superuser=False)
        
        count = users.delete()[0]
        deleted_stats['users'] = count
        self.stdout.write(self.style.SUCCESS(f"     ✓ Deleted {count} user accounts"))
        
        return deleted_stats
    
    def _display_deletion_results(self, stats: Dict[str, int]) -> None:
        """Display results after deletion."""
        self.stdout.write("\n" + self.style.SUCCESS("Deletion Summary:") + "\n")
        
        total = sum(stats.values())
        self.stdout.write(f"  Total items deleted: {total}")
        self.stdout.write(f"    - Portal Tokens: {stats.get('portal_tokens', 0)}")
        self.stdout.write(f"    - Withdraw Requests: {stats.get('withdraw_requests', 0)}")
        self.stdout.write(f"    - Transactions: {stats.get('transactions', 0)}")
        self.stdout.write(f"    - Orders: {stats.get('orders', 0)}")
        self.stdout.write(f"    - Bank Accounts: {stats.get('bank_accounts', 0)}")
        self.stdout.write(f"    - Profiles: {stats.get('profiles', 0)}")
        self.stdout.write(f"    - User Accounts: {stats.get('users', 0)}")

