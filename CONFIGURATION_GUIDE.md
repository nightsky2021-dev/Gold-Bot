# Configuration Guide - Gold Trading Bot

## Required Configuration Changes

After the recent security improvements, you **must** configure the following before running the application.

---

## 1. API Key Configuration (CRITICAL ⚠️)

### Problem
Previously, the API key was hardcoded in the source code, which is a security risk. This has been fixed.

### Solution
You must now set the `NAVASAN_API_KEY` in your environment or Django settings.

### Option A: Environment Variable (Recommended)

**For Linux/Mac:**
```bash
export NAVASAN_API_KEY='your-api-key-here'
```

**For Windows:**
```cmd
set NAVASAN_API_KEY=your-api-key-here
```

**For Docker/docker-compose.yml:**
```yaml
services:
  web:
    environment:
      - NAVASAN_API_KEY=your-api-key-here
```

**For .env file (with python-decouple):**
```env
NAVASAN_API_KEY=your-api-key-here
```

Then in `settings.py`:
```python
from decouple import config

NAVASAN_API_KEY = config('NAVASAN_API_KEY')
```

### Option B: Django Settings (Less Secure)

Add to `gold_shop/settings.py`:
```python
# API Configuration
NAVASAN_API_KEY = 'your-api-key-here'  # WARNING: Don't commit this to git!
```

**⚠️ Important:** If using this method, add `settings.py` to `.gitignore` or use a separate `local_settings.py`.

---

## 2. Verify Configuration

### Test API Key is Set

Run this command to verify:

```bash
python manage.py shell
```

Then in the shell:
```python
from django.conf import settings
print(hasattr(settings, 'NAVASAN_API_KEY'))
# Should print: True

print(settings.NAVASAN_API_KEY)
# Should print your API key
```

### Test Price Updates

```bash
python manage.py update_prices
```

**Expected output:**
```
INFO: Fetching prices from API...
INFO: Updated طلای آبشده: Base=15,234,567, ...
INFO: Successfully updated 3 products
```

**Error if not configured:**
```
ImproperlyConfigured: NAVASAN_API_KEY is not set in Django settings.
Please set it in your settings.py or environment variables.
```

---

## 3. Cache Configuration (Required for Order Deduplication)

The order deduplication feature requires Django cache. The default in-memory cache is sufficient.

### Verify Cache is Configured

In `gold_shop/settings.py`, ensure you have:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### For Production (Recommended: Redis)

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

Install Redis support:
```bash
pip install django-redis
```

---

## 4. Database Migration

Run the new migration to add the PriceHistory table:

```bash
python manage.py migrate trading
```

**Expected output:**
```
Running migrations:
  Applying trading.0016_add_price_history... OK
```

---

## 5. Verification Checklist

Before going to production, verify:

- [ ] ✅ `NAVASAN_API_KEY` is set and accessible
- [ ] ✅ Price updates work: `python manage.py update_prices`
- [ ] ✅ Cache is configured (check settings.py)
- [ ] ✅ Migration applied: `python manage.py migrate`
- [ ] ✅ Admin panel accessible without errors
- [ ] ✅ Price history is being recorded
- [ ] ✅ Orders can be created successfully
- [ ] ✅ Duplicate orders are rejected within 10 seconds

---

## 6. Troubleshooting

### Error: "NAVASAN_API_KEY is not set"

**Solution:**
1. Check environment variable is set: `echo $NAVASAN_API_KEY`
2. If using .env file, ensure python-decouple is installed
3. Restart Django server after setting environment variable

### Error: "No module named 'django_redis'"

**Solution:**
```bash
pip install django-redis
```

Or use the default cache (locmem).

### Error: "django.core.exceptions.ValidationError: معامله تکراری"

**Solution:**
This is expected behavior. Wait 10 seconds between order submissions or clear the cache:
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Price history not showing in admin

**Solution:**
1. Verify migration was applied: `python manage.py showmigrations trading`
2. Check for migration 0016_add_price_history
3. Re-run migration if needed: `python manage.py migrate trading`

---

## 7. Security Best Practices

### DO ✅
- Store API keys in environment variables
- Use `.env` files (not committed to git)
- Add `.env` to `.gitignore`
- Use different keys for development and production
- Rotate API keys periodically

### DON'T ❌
- Hardcode API keys in source code
- Commit API keys to version control
- Share API keys in chat/email
- Use production keys in development
- Log API keys in debug output

---

## 8. Production Deployment Checklist

Before deploying to production:

- [ ] Set `NAVASAN_API_KEY` in production environment
- [ ] Configure Redis cache (for better performance)
- [ ] Run migrations: `python manage.py migrate`
- [ ] Set `DEBUG = False` in settings
- [ ] Configure proper logging
- [ ] Test price updates in production environment
- [ ] Monitor logs for any errors
- [ ] Set up automated price update cron job

### Example Cron Job for Price Updates

```bash
# Update prices every hour
0 * * * * cd /path/to/gold_shop && /path/to/venv/bin/python manage.py update_prices >> /var/log/price_updates.log 2>&1
```

---

## 9. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NAVASAN_API_KEY` | ✅ Yes | None | API key for Navasan price service |
| `DEBUG` | No | True | Django debug mode |
| `SECRET_KEY` | ✅ Yes | (auto-generated) | Django secret key |
| `DATABASE_URL` | No | SQLite | Database connection string |
| `REDIS_URL` | No | None | Redis connection for cache |

---

## 10. Support

If you continue to experience issues:

1. Check Django logs: `tail -f /var/log/django.log`
2. Enable debug mode temporarily: `DEBUG = True`
3. Verify all dependencies: `pip freeze > requirements.txt`
4. Check Django version compatibility
5. Restart all services

For questions or issues, please refer to:
- README.md - General project documentation
- ARCHITECTURE.md - System design and structure
- IMPLEMENTATION_SUMMARY.md - Recent changes

---

**Last Updated:** 2025-11-09
**Version:** 2.0.0
