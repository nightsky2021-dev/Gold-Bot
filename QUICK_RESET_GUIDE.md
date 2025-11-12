# Quick Reset User Data Guide

## ⚠️ WARNING: THIS PERMANENTLY DELETES ALL USER DATA!

## Quick Steps

### 1. Backup First (REQUIRED!)
```bash
# SQLite
cp db.sqlite3 db.sqlite3.backup

# PostgreSQL
pg_dump -U username database_name > backup.sql
```

### 2. Check What Will Be Deleted
```bash
python manage.py reset_user_data --dry-run
```

### 3. Reset User Data
```bash
python manage.py reset_user_data
```
- Type `yes` when prompted
- Type `DELETE ALL` for final confirmation

## Command Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without deleting |
| `--no-input` | Skip confirmations (dangerous!) |
| `--include-superusers` | Also delete admin accounts (very dangerous!) |

## What Gets Deleted

✓ All user accounts (except superusers)
✓ All profiles
✓ All bank accounts
✓ All orders
✓ All transactions
✓ All withdrawals
✓ All balances (Rial, Gold, Coin, Dollar)
✓ All portal tokens

## What is NOT Deleted

✗ Products
✗ Price history
✗ Superuser accounts (unless --include-superusers)

## Example Usage

```bash
# Safe way (recommended)
python manage.py reset_user_data --dry-run  # Check first
python manage.py reset_user_data             # Then execute

# Quick way (for dev only)
python manage.py reset_user_data --no-input

# Nuclear option (use with extreme caution!)
python manage.py reset_user_data --include-superusers --no-input
```

## After Reset

Verify everything is clean:
```bash
python manage.py shell -c "from users.models import Profile; print(f'Profiles: {Profile.objects.count()}')"
```

Test user registration works through:
- Telegram Bot
- Web Portal
- Admin Panel

## Recovery

If you made a mistake:
```bash
# SQLite
cp db.sqlite3.backup db.sqlite3

# PostgreSQL
psql -U username database_name < backup.sql
```

## Full Documentation

See `RESET_USER_DATA_GUIDE.md` for complete documentation.

