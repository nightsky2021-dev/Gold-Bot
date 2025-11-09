"""Script to start bot with fresh bytecode cache."""
import os
import sys
import shutil
from pathlib import Path

print("🔧 Preparing to start bot with fresh code...")
print()

# Clear all __pycache__ directories
cache_dirs = list(Path('.').rglob('__pycache__'))
print(f"Found {len(cache_dirs)} cache directories")

for cache_dir in cache_dirs:
    try:
        shutil.rmtree(cache_dir)
        print(f"  ✅ Cleared: {cache_dir}")
    except Exception as e:
        print(f"  ⚠️  Could not clear: {cache_dir} ({e})")

print()
print("✅ Cache cleared!")
print()
print("🚀 Starting bot...")
print("="*60)
print()

# Start the bot
os.system("python manage.py runbot")

