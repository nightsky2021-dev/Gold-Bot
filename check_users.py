#!/usr/bin/env python
"""Check all users and profiles in the system."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from users.models import Profile
from django.contrib.auth.models import User

print("\n" + "="*80)
print("DATABASE CHECK")
print("="*80 + "\n")

# Check Django Users
users = User.objects.all()
print(f"Total Django Users: {users.count()}")
if users.count() > 0:
    print("\nDjango Users:")
    for user in users:
        print(f"  - {user.username} (ID: {user.id}, Email: {user.email or 'N/A'})")

print()

# Check Profiles
profiles = Profile.objects.select_related('user').all().order_by('-created_at')
print(f"Total Profiles: {profiles.count()}")

if profiles.count() == 0:
    print("\n⚠️  No users registered yet.")
    print("\nTo register users:")
    print("1. Start the bot: python manage.py runbot")
    print("2. In Telegram, send /start to the bot")
    print("3. Share your contact when prompted")
    print("4. Admin needs to approve the user in Django admin panel")
else:
    print("\nRegistered Profiles:")
    print("-" * 80)
    for i, profile in enumerate(profiles, 1):
        status = "✅ Approved" if profile.is_approved else "⏳ Pending"
        username = f"@{profile.telegram_username}" if profile.telegram_username else "N/A"
        
        print(f"\n{i}. {profile.get_display_name()}")
        print(f"   Phone: {profile.phone_number}")
        print(f"   Telegram ID: {profile.telegram_id}")
        print(f"   Username: {username}")
        print(f"   Status: {status}")
        print(f"   Django User: {profile.user.username}")
        print(f"   Created: {profile.created_at.strftime('%Y-%m-%d %H:%M')}")

print("\n" + "="*80 + "\n")

