#!/usr/bin/env python
"""List all registered users in the system."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from users.models import Profile

def list_users():
    """Display all registered users."""
    profiles = Profile.objects.select_related('user').all().order_by('-created_at')
    count = profiles.count()
    
    print("\n" + "="*80)
    print(f"REGISTERED USERS ({count})")
    print("="*80 + "\n")
    
    if count == 0:
        print("No users registered yet.\n")
        return
    
    for i, profile in enumerate(profiles, 1):
        status = "✅ Approved" if profile.is_approved else "⏳ Pending"
        username = f"@{profile.telegram_username}" if profile.telegram_username else "N/A"
        
        print(f"{i}. {profile.get_display_name()}")
        print(f"   Phone: {profile.phone_number}")
        print(f"   Telegram ID: {profile.telegram_id}")
        print(f"   Username: {username}")
        print(f"   Status: {status}")
        print(f"   Created: {profile.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()

if __name__ == '__main__':
    list_users()

