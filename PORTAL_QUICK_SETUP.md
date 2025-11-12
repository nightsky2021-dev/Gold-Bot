# User Transaction Portal - Quick Setup Guide

## 🚀 Quick Start

This guide will help you deploy the User Transaction Portal in your Gold Trading System.

---

## Prerequisites

- ✅ Django 5.1.3+
- ✅ python-telegram-bot installed
- ✅ PostgreSQL database
- ⚠️ WeasyPrint (optional, for PDF export)

---

## Installation Steps

### 1. Install Dependencies (Optional for PDF)

```bash
# For PDF export capability (optional)
pip install weasyprint
```

### 2. Run Migrations

```bash
python manage.py migrate
```

This will create the `PortalAccessToken` table in your database.

### 3. Update Django Settings

The settings have been enhanced to automatically support both local development and production environments.

**For Local Development:**

Add to your `.env` file:
```bash
PORTAL_BASE_URL=http://localhost:8000
# or
PORTAL_BASE_URL=http://127.0.0.1:8000
```

**For Production:**

Add to your `.env` file:
```bash
PORTAL_BASE_URL=https://yourdomain.com
```

**Note:** The `settings.py` already includes:
- Automatic CSRF_TRUSTED_ORIGINS configuration
- Session security settings (1 hour timeout)
- Portal token expiration (24 hours)
- Local development optimizations

You can customize token expiration by adding to `.env`:
```bash
PORTAL_TOKEN_EXPIRATION_HOURS=24
```

### 4. Update Bot Configuration

In your bot initialization file (e.g., `main.py` or `bot/__main__.py`), add:

```python
from bot.handlers.portal import portal_access, portal_refresh_callback, portal_info

# Register portal handlers
application.add_handler(CommandHandler('portal', portal_access))
application.add_handler(CommandHandler('portal_info', portal_info))
application.add_handler(CallbackQueryHandler(portal_refresh_callback, pattern='^portal_refresh$'))
```

### 5. Update Template URLs (Optional)

In `templates/portal/error.html` and `templates/portal/logged_out.html`, replace:

```html
<a href="https://t.me/YOUR_BOT_USERNAME" ...>
```

with your actual bot username:

```html
<a href="https://t.me/your_actual_bot_username" ...>
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Restart Bot and Web Server

```bash
# Restart your Telegram bot
# Restart Django (gunicorn/uwsgi/runserver)
```

---

## Testing

### Test Locally

1. Set environment variable in `.env`:
   ```bash
   PORTAL_BASE_URL=http://localhost:8000
   ```

2. Start Django server:
   ```bash
   python manage.py runserver
   ```

3. In Telegram bot, send `/portal` command

4. Click the generated link

5. Verify all pages load correctly

### Test Features

- ✅ Dashboard loads with correct data
- ✅ Transaction list shows your orders
- ✅ Filters work (product, date, type)
- ✅ P/L calculations are accurate
- ✅ Statement shows correct balances
- ✅ CSV export downloads
- ✅ PDF export works (if WeasyPrint installed)
- ✅ Mobile responsive (test on phone)

---

## Production Deployment

### 1. Configure Web Server (Nginx Example)

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /static/ {
        alias /path/to/your/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/your/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Update Environment Variables for Production

Add to your `.env` file:
```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
PORTAL_BASE_URL=https://yourdomain.com
```

**Note:** The settings.py automatically configures:
- `SESSION_COOKIE_SECURE` based on DEBUG mode
- `CSRF_TRUSTED_ORIGINS` based on PORTAL_BASE_URL
- `X_FRAME_OPTIONS` for security

### 3. Set Up HTTPS

Use Let's Encrypt for free SSL:

```bash
sudo certbot --nginx -d yourdomain.com
```

### 4. Update PORTAL_BASE_URL

```python
PORTAL_BASE_URL = 'https://yourdomain.com'
```

---

## Maintenance Tasks

### Cleanup Expired Tokens (Weekly)

Create a management command or cron job:

```python
# In Django shell or management command
from trading.portal_services import PortalTokenService
PortalTokenService.cleanup_expired_tokens()
```

Or add to crontab:

```bash
0 0 * * 0 cd /path/to/project && python manage.py shell -c "from trading.portal_services import PortalTokenService; PortalTokenService.cleanup_expired_tokens()"
```

### Monitor Logs

```bash
tail -f /var/log/django/portal.log
```

---

## Troubleshooting

### Issue: "Token invalid or expired"

**Solution:**
- Tokens expire after 24 hours
- User should request new link with `/portal` command

### Issue: Persian text shows as ????

**Solution:**
- Ensure UTF-8 encoding: `<meta charset="UTF-8">`
- Check Persian font CSS is loaded
- Verify database charset is UTF-8

### Issue: Mobile layout broken

**Solution:**
- Check viewport meta tag exists
- Clear browser cache
- Test in different browsers

### Issue: PDF export fails

**Solution:**
```bash
# Install WeasyPrint
pip install weasyprint

# For system dependencies (Ubuntu/Debian):
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
```

### Issue: Can't access portal after clicking link

**Solution:**
- Check `PORTAL_BASE_URL` is correct
- Verify Django server is running
- Check firewall/port settings
- Verify SSL certificate if using HTTPS

---

## Security Checklist

- ✅ HTTPS enabled in production
- ✅ `DEBUG = False` in production
- ✅ Strong `SECRET_KEY` configured
- ✅ `ALLOWED_HOSTS` properly set
- ✅ CSRF protection enabled
- ✅ Session cookies secured
- ✅ Token expiration set to 24 hours
- ✅ Session timeout set to 1 hour

---

## Performance Optimization (Optional)

### Add Redis Caching

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Cache prices for 5 minutes
from django.core.cache import cache
prices = cache.get('product_prices')
if not prices:
    prices = Product.objects.filter(is_active=True)
    cache.set('product_prices', prices, 300)
```

### Database Indexes

Migrations already include indexes, but verify:

```sql
-- Check indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'trading_portalaccesstoken';
```

---

## Feature Flags (Optional)

To enable/disable features:

```python
# settings.py
PORTAL_FEATURES = {
    'PDF_EXPORT': True,  # Set to False if WeasyPrint not installed
    'CSV_EXPORT': True,
    'AUTO_REFRESH': False,  # Auto-refresh prices
    'CHARTS': False,  # Phase 2 feature
}
```

---

## Monitoring & Analytics

### Track Portal Usage

```python
# In views, add logging
logger.info(f"Portal accessed by {profile.get_display_name()}")
```

### Add Analytics (Optional)

```html
<!-- In base.html, before </head> -->
<!-- Google Analytics or similar -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

---

## Next Steps

### Phase 2 Enhancements (Future)

1. **Charts & Visualizations**
   - Install Chart.js or ApexCharts
   - Add P/L trend charts
   - Portfolio allocation pie chart

2. **Advanced Search**
   - Full-text search in transactions
   - Search by amount range
   - Multi-select filters

3. **Email Reports**
   - Schedule weekly/monthly reports
   - Email PDF statements
   - Alerts for significant P/L changes

4. **Mobile App**
   - Progressive Web App (PWA)
   - Push notifications
   - Offline capability

---

## Support

For issues:

1. Check `USER_PORTAL_IMPLEMENTATION.md` for detailed docs
2. Review Django logs: `python manage.py check --deploy`
3. Test in staging before production
4. Contact development team

---

## Success Checklist

Before going live:

- [ ] Migrations applied successfully
- [ ] Bot handlers registered
- [ ] PORTAL_BASE_URL configured
- [ ] HTTPS enabled
- [ ] Static files collected
- [ ] All templates render correctly
- [ ] Filters work as expected
- [ ] CSV export downloads successfully
- [ ] PDF export works (if enabled)
- [ ] Mobile responsive on real devices
- [ ] Security settings verified
- [ ] Backup created
- [ ] Tested with real user accounts
- [ ] Monitoring/logging in place
- [ ] Documentation updated

---

**Ready to Go! 🎉**

After completing these steps, users can access the portal via:
1. Open Telegram bot
2. Send `/portal` command
3. Click the generated link
4. Enjoy the full-featured transaction portal!

---

*Last Updated: November 12, 2024*
