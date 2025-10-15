# 🚀 راهنمای استقرار (Deployment Guide)

این راهنما نحوه استقرار حرفه‌ای پروژه Gold Shop را در محیط تولید (Production) توضیح می‌دهد.

## 📋 پیش‌نیازهای Production

- ✅ سرور لینوکس (Ubuntu 20.04+ توصیه می‌شود)
- ✅ PostgreSQL 13+
- ✅ Python 3.10+
- ✅ Nginx (برای Reverse Proxy)
- ✅ دامنه و SSL Certificate (Let's Encrypt)
- ✅ حداقل 2GB RAM و 20GB فضای دیسک

## روش 1: استقرار با Docker (توصیه شده)

### مزایا:
- ✅ راه‌اندازی سریع
- ✅ ایزوله بودن محیط
- ✅ قابلیت مقیاس‌پذیری آسان
- ✅ سازگاری بالا

### مراحل:

#### 1. نصب Docker و Docker Compose
```bash
# نصب Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. کلون پروژه
```bash
git clone <your-repo-url> gold_shop
cd gold_shop
```

#### 3. تنظیم متغیرهای محیطی
```bash
cp .env.example .env
nano .env
```

تنظیمات ضروری `.env`:
```env
# Django
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DATABASE_URL=postgres://gold_shop_user:your-strong-password@db:5432/gold_shop
DB_PASSWORD=your-strong-password

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# Time Zone
TIME_ZONE=Asia/Tehran
```

#### 4. ساخت و اجرای Container ها
```bash
# ساخت images
docker-compose build

# اجرای migrations
docker-compose run --rm web python manage.py migrate

# ایجاد superuser
docker-compose run --rm web python manage.py createsuperuser

# افزودن داده نمونه
docker-compose run --rm web python setup_sample_data.py

# اجرای تمام سرویس‌ها
docker-compose up -d
```

#### 5. بررسی وضعیت
```bash
# مشاهده لاگ‌ها
docker-compose logs -f

# مشاهده وضعیت سرویس‌ها
docker-compose ps

# تست ربات
# به ربات تلگرام خود پیام /start بدهید
```

#### 6. پیکربندی Nginx (Reverse Proxy)
```bash
sudo nano /etc/nginx/sites-available/goldshop
```

محتوای فایل:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/gold_shop/staticfiles/;
    }

    location /media/ {
        alias /path/to/gold_shop/media/;
    }
}
```

فعال‌سازی:
```bash
sudo ln -s /etc/nginx/sites-available/goldshop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. نصب SSL با Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## روش 2: استقرار Manual (بدون Docker)

### 1. نصب Dependencies
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx
```

### 2. راه‌اندازی PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE gold_shop;
CREATE USER gold_shop_user WITH PASSWORD 'your-strong-password';
ALTER ROLE gold_shop_user SET client_encoding TO 'utf8';
ALTER ROLE gold_shop_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE gold_shop_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE gold_shop TO gold_shop_user;
\q
```

### 3. کلون و راه‌اندازی پروژه
```bash
cd /opt
sudo git clone <your-repo-url> gold_shop
sudo chown -R $USER:$USER /opt/gold_shop
cd gold_shop

# ایجاد virtual environment
python3.10 -m venv venv
source venv/bin/activate

# نصب dependencies
pip install -r requirements.txt
```

### 4. پیکربندی
```bash
cp .env.example .env
nano .env
```

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://gold_shop_user:your-password@localhost:5432/gold_shop
TELEGRAM_BOT_TOKEN=your-token
```

### 5. Django Setup
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python setup_sample_data.py
```

### 6. Gunicorn (WSGI Server)
```bash
pip install gunicorn

# تست
gunicorn gold_shop.wsgi:application --bind 0.0.0.0:8000
```

### 7. Systemd Service برای Django
```bash
sudo nano /etc/systemd/system/goldshop-web.service
```

محتوا:
```ini
[Unit]
Description=Gold Shop Django Web Application
After=network.target postgresql.service

[Service]
Type=notify
User=your-user
Group=www-data
WorkingDirectory=/opt/gold_shop
Environment="PATH=/opt/gold_shop/venv/bin"
ExecStart=/opt/gold_shop/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/opt/gold_shop/goldshop.sock \
    gold_shop.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 8. Systemd Service برای Bot
```bash
sudo nano /etc/systemd/system/goldshop-bot.service
```

محتوا:
```ini
[Unit]
Description=Gold Shop Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/gold_shop
Environment="PATH=/opt/gold_shop/venv/bin"
ExecStart=/opt/gold_shop/venv/bin/python manage.py runbot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9. فعال‌سازی و اجرای Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable goldshop-web goldshop-bot
sudo systemctl start goldshop-web goldshop-bot

# بررسی وضعیت
sudo systemctl status goldshop-web
sudo systemctl status goldshop-bot
```

### 10. Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/goldshop
```

```nginx
upstream goldshop_app {
    server unix:/opt/gold_shop/goldshop.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 4G;

    location /static/ {
        alias /opt/gold_shop/staticfiles/;
    }

    location /media/ {
        alias /opt/gold_shop/media/;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://goldshop_app;
    }

    # Logging
    access_log /var/log/nginx/goldshop_access.log;
    error_log /var/log/nginx/goldshop_error.log;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/goldshop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 11. SSL با Let's Encrypt
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🔄 به‌روزرسانی خودکار قیمت‌ها (Cron Job)

### برای Docker:
در `docker-compose.yml` سرویس `price_updater` وجود دارد که خودکار کار می‌کند.

### برای Manual:
```bash
crontab -e
```

افزودن این خط (هر ساعت):
```cron
0 * * * * cd /opt/gold_shop && /opt/gold_shop/venv/bin/python manage.py update_prices >> /var/log/goldshop-prices.log 2>&1
```

---

## 🔒 بهترین شیوه‌های امنیتی

### 1. تنظیمات Django
```python
# در settings.py

# SECURITY
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2. دیتابیس
- ✅ از رمز عبور قوی استفاده کنید
- ✅ فقط از localhost دسترسی داشته باشد
- ✅ Backup های منظم

### 3. فایروال
```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### 4. Backup خودکار
```bash
# اسکریپت backup
nano /opt/backup-goldshop.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/goldshop"

mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U gold_shop_user gold_shop | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# حذف backup های قدیمی (بیش از 30 روز)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x /opt/backup-goldshop.sh

# افزودن به cron (هر روز ساعت 2 بامداد)
crontab -e
0 2 * * * /opt/backup-goldshop.sh >> /var/log/goldshop-backup.log 2>&1
```

---

## 📊 مانیتورینگ و لاگ‌ها

### مشاهده لاگ‌ها (Docker)
```bash
docker-compose logs -f web
docker-compose logs -f bot
docker-compose logs -f price_updater
```

### مشاهده لاگ‌ها (Manual)
```bash
sudo journalctl -u goldshop-web -f
sudo journalctl -u goldshop-bot -f
tail -f /opt/gold_shop/logs/gold_shop.log
```

### نصب Monitoring Tools (اختیاری)
```bash
# Prometheus + Grafana
# Sentry for error tracking
# Uptime monitoring (UptimeRobot, etc.)
```

---

## 🔧 مشکلات رایج

### ربات Crash می‌کند
```bash
# بررسی لاگ‌ها
docker-compose logs bot

# Restart
docker-compose restart bot
```

### خطای Database Connection
```bash
# بررسی وضعیت PostgreSQL
docker-compose ps db

# بررسی credentials در .env
```

### Static Files نمایش داده نمی‌شوند
```bash
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data /opt/gold_shop/staticfiles
```

---

## 📈 Scale کردن

### افزایش Workers
```yaml
# در docker-compose.yml
web:
  deploy:
    replicas: 3
```

### استفاده از Load Balancer
- Nginx load balancing
- HAProxy
- Cloud load balancers (AWS ELB, etc.)

### استفاده از Redis (Cache)
```bash
pip install redis django-redis

# در settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

---

## ✅ Checklist نهایی قبل از Production

- [ ] DEBUG=False
- [ ] SECRET_KEY تغییر کرده
- [ ] ALLOWED_HOSTS تنظیم شده
- [ ] از PostgreSQL استفاده می‌شود
- [ ] SSL نصب شده
- [ ] Firewall پیکربندی شده
- [ ] Backup خودکار فعال است
- [ ] Monitoring راه‌اندازی شده
- [ ] لاگ‌ها قابل دسترسی هستند
- [ ] ربات تست شده
- [ ] سفارشات تست شده
- [ ] پنل ادمین قابل دسترسی است

---

## 🆘 پشتیبانی

برای مشکلات Production:
1. لاگ‌ها را بررسی کنید
2. GitHub Issues را چک کنید
3. یک Issue جدید باز کنید

---

**نکته مهم**: این راهنما یک پیکربندی پایه است. برای سیستم‌های بزرگ، مشاوره با یک DevOps Engineer توصیه می‌شود.
