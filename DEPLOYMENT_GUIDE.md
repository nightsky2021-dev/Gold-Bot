# 🚀 Deployment Guide - Gold Shop Bot

## Quick Start (Development)

### 1. Clone & Setup
```bash
git clone <repository-url>
cd gold_shop
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Edit .env file with your settings
nano .env

# Required: Set your Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Create Sample Products
```bash
python manage.py shell
```

```python
from trading.models import Product

Product.objects.create(
    name="سکه بهار آزادی",
    buy_price=65000000,
    sell_price=68000000,
    is_active=True
)

Product.objects.create(
    name="طلای 18 عیار",
    buy_price=2500000,
    sell_price=2600000,
    is_active=True
)
exit()
```

### 8. Run Services

**Terminal 1 - Django Admin Panel:**
```bash
python manage.py runserver
# Admin at: http://localhost:8000/admin/
```

**Terminal 2 - Telegram Bot:**
```bash
python manage.py runbot
```

---

## 🐳 Docker Deployment

### Development with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### Production Docker Deployment

1. **Update docker-compose.yml for production:**
```yaml
# Change environment variables
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:secure_password@db:5432/gold_shop
```

2. **Use production-ready PostgreSQL:**
```bash
# Ensure strong database password
DB_PASSWORD=very_secure_password_here
```

3. **Add nginx reverse proxy (recommended):**
Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /app/staticfiles/;
    }
}
```

---

## 🖥️ VPS/Server Deployment

### Prerequisites
- Ubuntu 20.04+ or Debian 11+
- Python 3.10+
- PostgreSQL 13+
- Nginx
- Systemd

### Step-by-Step

#### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip postgresql nginx git -y
```

#### 2. Create PostgreSQL Database
```bash
sudo -u postgres psql

CREATE DATABASE gold_shop;
CREATE USER gold_shop_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE gold_shop TO gold_shop_user;
\q
```

#### 3. Clone Project
```bash
cd /opt
sudo git clone <repository-url> gold_shop
cd gold_shop
sudo chown -R $USER:$USER /opt/gold_shop
```

#### 4. Setup Python Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. Configure Production Settings
```bash
nano .env
```

```env
SECRET_KEY=generate_a_secure_random_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your.server.ip

DATABASE_URL=postgres://gold_shop_user:secure_password_here@localhost:5432/gold_shop

TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

TIME_ZONE=Asia/Tehran

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### 6. Run Migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

#### 7. Setup Systemd Services

**Django/Gunicorn Service:**
```bash
sudo nano /etc/systemd/system/goldshop-web.service
```

```ini
[Unit]
Description=Gold Shop Web Service
After=network.target postgresql.service

[Service]
Type=notify
User=your_username
Group=www-data
WorkingDirectory=/opt/gold_shop
Environment="PATH=/opt/gold_shop/venv/bin"
ExecStart=/opt/gold_shop/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/opt/gold_shop/goldshop.sock \
    --timeout 60 \
    --access-logfile /opt/gold_shop/logs/access.log \
    --error-logfile /opt/gold_shop/logs/error.log \
    gold_shop.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Telegram Bot Service:**
```bash
sudo nano /etc/systemd/system/goldshop-bot.service
```

```ini
[Unit]
Description=Gold Shop Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/gold_shop
Environment="PATH=/opt/gold_shop/venv/bin"
ExecStart=/opt/gold_shop/venv/bin/python manage.py runbot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Price Updater Service:**
```bash
sudo nano /etc/systemd/system/goldshop-prices.timer
```

```ini
[Unit]
Description=Gold Shop Price Update Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h

[Install]
WantedBy=timers.target
```

```bash
sudo nano /etc/systemd/system/goldshop-prices.service
```

```ini
[Unit]
Description=Gold Shop Price Update Service

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/opt/gold_shop
Environment="PATH=/opt/gold_shop/venv/bin"
ExecStart=/opt/gold_shop/venv/bin/python manage.py update_prices
```

#### 8. Setup Nginx
```bash
sudo nano /etc/nginx/sites-available/goldshop
```

```nginx
upstream goldshop {
    server unix:/opt/gold_shop/goldshop.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias /opt/gold_shop/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /opt/gold_shop/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://goldshop;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health checks
    location /health/ {
        proxy_pass http://goldshop;
        access_log off;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/goldshop /etc/nginx/sites-enabled/
sudo nginx -t
```

#### 9. Setup SSL with Let's Encrypt (Recommended)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 10. Start Services
```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable goldshop-web goldshop-bot goldshop-prices.timer
sudo systemctl start goldshop-web goldshop-bot goldshop-prices.timer

# Start nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status goldshop-web
sudo systemctl status goldshop-bot
sudo systemctl list-timers goldshop-prices.timer
```

#### 11. Monitor Logs
```bash
# Web service logs
sudo journalctl -u goldshop-web -f

# Bot logs
sudo journalctl -u goldshop-bot -f

# Application logs
tail -f /opt/gold_shop/logs/gold_shop.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 🔒 Security Checklist

### Before Going Live

- [ ] Change `SECRET_KEY` to a random secure key
- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use PostgreSQL, not SQLite
- [ ] Enable HTTPS/SSL
- [ ] Set secure cookie flags
- [ ] Configure firewall (UFW)
- [ ] Setup regular database backups
- [ ] Enable fail2ban
- [ ] Use strong database passwords
- [ ] Restrict database access to localhost
- [ ] Setup monitoring (optional: Sentry, DataDog)
- [ ] Enable HSTS headers
- [ ] Review Django security checklist

### Firewall Configuration
```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

---

## 📊 Monitoring & Maintenance

### Health Check Endpoints
```bash
# Basic health
curl https://yourdomain.com/health/

# Readiness check
curl https://yourdomain.com/ready/

# Metrics
curl https://yourdomain.com/metrics/
```

### Database Backups
```bash
# Create backup script
nano /opt/gold_shop/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/goldshop"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U gold_shop_user gold_shop | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

```bash
chmod +x /opt/gold_shop/backup.sh

# Add to crontab
crontab -e
0 2 * * * /opt/gold_shop/backup.sh
```

### Log Rotation
```bash
sudo nano /etc/logrotate.d/goldshop
```

```
/opt/gold_shop/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 your_username www-data
}
```

---

## 🐛 Troubleshooting

### Bot Not Starting
```bash
# Check logs
sudo journalctl -u goldshop-bot -n 100

# Common issues:
# 1. Invalid bot token
# 2. Database connection failed
# 3. Migration not run

# Restart bot
sudo systemctl restart goldshop-bot
```

### Web Service Issues
```bash
# Check gunicorn status
sudo systemctl status goldshop-web

# Test gunicorn directly
cd /opt/gold_shop
source venv/bin/activate
gunicorn gold_shop.wsgi:application --bind 0.0.0.0:8000

# Check nginx config
sudo nginx -t

# Check socket file
ls -la /opt/gold_shop/goldshop.sock
```

### Database Connection Errors
```bash
# Test database connection
psql -U gold_shop_user -d gold_shop -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

---

## 📈 Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_orders_status_created ON trading_order(status, created_at DESC);
CREATE INDEX idx_profile_telegram_id ON users_profile(telegram_id);

-- Analyze tables
ANALYZE trading_order;
ANALYZE users_profile;
ANALYZE trading_product;
```

### Caching (Optional)
Install Redis:
```bash
sudo apt install redis-server
pip install django-redis
```

Update settings.py:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## ✅ Post-Deployment Checklist

- [ ] Admin panel accessible and working
- [ ] Bot responds to /start command
- [ ] Users can register successfully
- [ ] Price display works correctly
- [ ] Order creation and processing works
- [ ] Admin can approve users
- [ ] Admin can complete orders
- [ ] Health endpoints responding
- [ ] SSL certificate valid
- [ ] Logs being written correctly
- [ ] Backups configured and tested
- [ ] Monitoring alerts setup (optional)

---

## 📞 Support

For deployment issues:
1. Check logs first (systemd journal and application logs)
2. Verify configuration files
3. Test database connectivity
4. Ensure all services are running
5. Check firewall rules

---

**Last Updated**: 2025-10-24
**Deployment Difficulty**: ⭐⭐⭐ (Intermediate)
**Estimated Setup Time**: 1-2 hours
