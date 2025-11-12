# User Data Reset Guide

## Overview

This guide explains how to use the `reset_user_data` management command to completely remove and clean all user data from the Gold Trading Bot platform across all interfaces (Telegram Bot, Web Portal, and Admin Panel).

## ⚠️ IMPORTANT WARNING

**THIS COMMAND WILL PERMANENTLY DELETE ALL USER DATA!**

- This action **CANNOT BE UNDONE**
- All user balances will be lost
- All transaction history will be deleted
- All orders and withdrawals will be removed
- Users will need to re-register

**Always backup your database before running this command!**

## What Gets Deleted

The command removes all user-related data from the following models:

### User Data
- ✓ User accounts (Django User model)
- ✓ User profiles (Profile model)
- ✓ Bank accounts (BankAccount model)

### Transaction Data
- ✓ Orders (Order model)
- ✓ Transactions (Transaction model)
- ✓ Withdrawal requests (WithdrawRequest model)
- ✓ Portal access tokens (PortalAccessToken model)

### Financial Data
- ✓ All Rial balances (available + frozen)
- ✓ All Gold balances (available + frozen)
- ✓ All Coin balances (available + frozen)
- ✓ All Dollar balances (available + frozen)

### What is NOT Deleted
- ✗ Products (Product model)
- ✗ Price history (PriceHistory model)
- ✗ Superuser accounts (unless --include-superusers flag is used)
- ✗ Admin configurations

## Usage

### Basic Usage

```bash
python manage.py reset_user_data
```

This will:
1. Show statistics about data to be deleted
2. Ask for confirmation (requires typing "yes")
3. Ask for double confirmation (requires typing "DELETE ALL")
4. Delete all user data
5. Show deletion summary

### Command Options

#### 1. Dry Run (Recommended First)

```bash
python manage.py reset_user_data --dry-run
```

**Use this first!** Shows what would be deleted without actually deleting anything.

#### 2. No Input (Automated/Scripted)

```bash
python manage.py reset_user_data --no-input
```

⚠️ **DANGEROUS!** Skips all confirmation prompts. Use only in automated scripts where you're absolutely sure.

#### 3. Include Superusers

```bash
python manage.py reset_user_data --include-superusers
```

⚠️ **EXTREMELY DANGEROUS!** Also deletes superuser accounts. Use with extreme caution!

### Combining Options

```bash
# Dry run with superusers included
python manage.py reset_user_data --dry-run --include-superusers

# Automated deletion (no prompts)
python manage.py reset_user_data --no-input

# Automated deletion including superusers
python manage.py reset_user_data --no-input --include-superusers
```

## Step-by-Step Guide

### Step 1: Backup Your Database

**CRITICAL: Always backup first!**

For SQLite:
```bash
# Copy the database file
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

For PostgreSQL:
```bash
# Dump the database
pg_dump -U your_username your_database > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Run Dry Run

```bash
python manage.py reset_user_data --dry-run
```

Review the output carefully. Make sure you understand what will be deleted.

### Step 3: Execute the Reset

```bash
python manage.py reset_user_data
```

Follow the prompts:
1. Type `yes` when asked for first confirmation
2. Type `DELETE ALL` when asked for second confirmation

### Step 4: Verify the Reset

Check that users have been deleted:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from users.models import Profile
from trading.models import Order, Transaction

# Check counts
print(f"Users: {User.objects.count()}")
print(f"Profiles: {Profile.objects.count()}")
print(f"Orders: {Order.objects.count()}")
print(f"Transactions: {Transaction.objects.count()}")
```

## Example Output

### Dry Run Output

```
======================================================================
  USER DATA RESET UTILITY
  This will delete ALL user data from the database!
======================================================================

Data to be deleted:
  👥 Users (Django accounts): 15
     ⚠️  Superusers will be PRESERVED: 2

  📋 User Profiles: 15
  🏦 Bank Accounts: 8
  📦 Orders: 145
  💳 Transactions: 89
  💰 Withdraw Requests: 5
  🔑 Portal Access Tokens: 23

Financial Data to be Reset:
  💵 Total Rial Balance: 50,000,000 ریال
  🪙 Total Gold Balance: 125.5000 گرم
  🥇 Total Coin Balance: 10 عدد
  💵 Total Dollar Balance: $500.00

[DRY RUN] No data was actually deleted.
```

### Actual Deletion Output

```
Starting deletion...
  🔑 Deleting portal access tokens...
     ✓ Deleted 23 portal tokens
  💰 Deleting withdraw requests...
     ✓ Deleted 5 withdraw requests
  💳 Deleting transactions...
     ✓ Deleted 89 transactions (12 receipt images)
  📦 Deleting orders...
     ✓ Deleted 145 orders
  🏦 Deleting bank accounts...
     ✓ Deleted 8 bank accounts
  📋 Deleting user profiles...
     ✓ Deleted 15 profiles
  👥 Deleting Django user accounts...
     ✓ Deleted 15 user accounts

Deletion Summary:
  Total items deleted: 300
    - Portal Tokens: 23
    - Withdraw Requests: 5
    - Transactions: 89
    - Orders: 145
    - Bank Accounts: 8
    - Profiles: 15
    - User Accounts: 15

======================================================================
  ✓ All user data has been successfully deleted!
======================================================================
```

## Use Cases

### Development Environment Reset

```bash
# Quick reset for development
python manage.py reset_user_data --dry-run
python manage.py reset_user_data --no-input
```

### Production Cleanup (Use with Extreme Caution!)

```bash
# 1. Stop all services
sudo systemctl stop gold_bot_web
sudo systemctl stop gold_bot_telegram

# 2. Backup database
pg_dump -U gold_bot gold_bot_db > backup_before_reset.sql

# 3. Run dry run
python manage.py reset_user_data --dry-run

# 4. Execute reset
python manage.py reset_user_data

# 5. Restart services
sudo systemctl start gold_bot_web
sudo systemctl start gold_bot_telegram
```

### Testing Environment

```bash
# Reset test database
python manage.py reset_user_data --no-input --settings=gold_shop.settings_test
```

## Safety Features

The command includes multiple safety features:

1. **Dry Run Mode**: Test without deleting
2. **Double Confirmation**: Requires two confirmations
3. **Superuser Protection**: Superusers are preserved by default
4. **Transaction Atomicity**: All deletions in a single transaction (all-or-nothing)
5. **Cascade Handling**: Properly handles foreign key relationships
6. **File Cleanup**: Removes uploaded receipt images

## Troubleshooting

### Error: Foreign Key Constraint

If you get foreign key constraint errors:
```bash
# Try with cascade delete in the correct order
# The command handles this automatically, but if you see errors,
# check for custom foreign keys that might need manual handling
```

### Error: Permission Denied

```bash
# Run with proper Python environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

python manage.py reset_user_data
```

### Database Locked (SQLite)

```bash
# Stop all services accessing the database
sudo systemctl stop gold_bot_web
sudo systemctl stop gold_bot_telegram

# Then run the command
python manage.py reset_user_data
```

## Best Practices

1. **Always run dry-run first**
   ```bash
   python manage.py reset_user_data --dry-run
   ```

2. **Always backup before deletion**
   - Use database backups
   - Keep multiple backup versions
   - Test backup restoration

3. **Stop all services before reset**
   - Stop Telegram bot
   - Stop web server
   - Prevent new data during deletion

4. **Verify after reset**
   - Check database counts
   - Test user registration
   - Ensure products still exist

5. **Document the reset**
   - Record why reset was needed
   - Document what was deleted
   - Note any issues encountered

## Alternative: Selective Deletion

If you need to delete specific users instead of all users, use the Django shell:

```bash
python manage.py shell
```

```python
from users.models import Profile
from django.db import transaction

# Delete a specific user
with transaction.atomic():
    profile = Profile.objects.get(phone_number='09123456789')
    profile.user.delete()  # Cascades to profile and related data
```

## Recovery

If you accidentally deleted data and have a backup:

### SQLite Recovery

```bash
# Stop services
sudo systemctl stop gold_bot_web gold_bot_telegram

# Restore backup
cp db.sqlite3.backup_YYYYMMDD_HHMMSS db.sqlite3

# Restart services
sudo systemctl start gold_bot_web gold_bot_telegram
```

### PostgreSQL Recovery

```bash
# Stop services
sudo systemctl stop gold_bot_web gold_bot_telegram

# Drop and recreate database
dropdb gold_bot_db
createdb gold_bot_db

# Restore backup
psql -U gold_bot gold_bot_db < backup_before_reset.sql

# Restart services
sudo systemctl start gold_bot_web gold_bot_telegram
```

## Support

For issues or questions:
- Check Django logs: `logs/gold_shop.log`
- Review command help: `python manage.py reset_user_data --help`
- Check database integrity after reset
- Test all platforms (bot, portal, admin) after reset

## Related Commands

- `python manage.py seed_products` - Recreate product data
- `python manage.py update_prices` - Update product prices
- `python manage.py createsuperuser` - Create new admin user

## Conclusion

The `reset_user_data` command is a powerful tool for cleaning user data across all platforms. Use it responsibly and always with proper backups!

