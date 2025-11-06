# 🚀 Anigold Integration - Setup Instructions

## 📌 Quick Overview

Your trading system has been **successfully upgraded** to work with the Anigold API! 

**10 new products** are now available for trading:
- 6 Currencies (Dollar, Euro, Lira, Yuan, Pound, Dirham)
- 3 Coins (Full, Half, Quarter)
- 1 Gold (Molten Gold - 18k)

---

## ⚡ 3-Step Setup

### Step 1️⃣: Apply Migrations

```bash
python manage.py migrate
```

This creates the database structure for new products.

### Step 2️⃣: Create Products

```bash
python setup_anigold_products.py
```

This adds all 10 products with proper pricing configurations.

### Step 3️⃣: Update Prices

```bash
python manage.py update_prices --show-details
```

This fetches current prices from the Anigold API and calculates buy/sell prices.

---

## ✅ Verify Setup

### Check Admin Panel
1. Go to: `/admin/trading/product/`
2. You should see **10 active products**
3. Each should have current prices displayed

### Test Telegram Bot
1. Send `/start` to your bot
2. Click "📈 قیمت‌ها و معامله"
3. You should see all products listed
4. Try buying/selling different types

---

## 📊 Product Pricing

| Product Type | Margin | Calculation |
|-------------|--------|-------------|
| **Currencies** | ±1% | Dynamic (auto-calculated) |
| **Coins** | ±450,000 Toman | Fixed (4,500,000 Rials) |
| **Gold** | ±30,000 Toman | Fixed (300,000 Rials) |

---

## 🔄 Automatic Price Updates

### Setup Cron Job (Recommended)

```bash
# Edit crontab
crontab -e

# Add this line to update prices every 5 minutes
*/5 * * * * cd /path/to/project && python manage.py update_prices
```

### Manual Updates

```bash
# Simple update
python manage.py update_prices

# Detailed update with full output
python manage.py update_prices --show-details
```

---

## 🎯 Key Information

### API Configuration

- **Endpoint**: `POST http://api.anigoldbot.ir/store/prices/`
- **Auth Header**: `Authorization: 1a233fab-04d1-47b2-b732-813d93795c43`
- **Response Format**: JSON array with price data
- **Price Unit**: Tomans (auto-converted to Rials ×10)

### Product Codes

```python
# Currencies
'dollar_usa'    # دلار آمریکا
'euro'          # یورو
'lira_turkey'   # لیر ترکیه
'yuan_china'    # یوان چین
'pound_uk'      # پوند انگلیس
'dirham_uae'    # درهم امارات

# Coins
'coin_full'     # سکه غیربانکی
'coin_half'     # نیم سکه غیربانکی
'coin_quarter'  # ربع سکه غیربانکی

# Gold
'gold_abshodeh' # طلای آبشده
```

---

## 🔧 Common Tasks

### Add/Edit Product Margin

1. Go to Admin Panel → Products
2. Click on product name
3. Edit "Buy Margin" or "Sell Margin"
4. Save
5. Run: `python manage.py update_prices`

### Activate/Deactivate Product

1. Go to Admin Panel → Products
2. Check/uncheck "Active" checkbox
3. Save

### Switch API Provider

Edit `gold_shop/settings.py`:

```python
# Use Anigold (current)
PRICE_PROVIDER_TYPE = 'anigold'

# Or use Navasan (legacy)
PRICE_PROVIDER_TYPE = 'navasan'
```

---

## 📚 Documentation

Comprehensive guides available:

1. **`ANIGOLD_INTEGRATION_GUIDE.md`**
   - Complete integration guide
   - API documentation
   - Troubleshooting

2. **`QUICK_START_ANIGOLD.md`**
   - Quick setup instructions
   - Verification checklist

3. **`IMPLEMENTATION_SUMMARY.md`**
   - Technical implementation details
   - All changes documented

---

## 🐛 Troubleshooting

### Prices not updating?

```bash
# Test API connection
python -c "
from trading.price_providers import get_active_provider
provider = get_active_provider()
print(provider._fetch_all_prices())
"
```

### Products not showing in bot?

1. Check if products are **active** in admin
2. Run `python manage.py update_prices`
3. Restart Telegram bot

### Incorrect prices?

1. Check product margins in admin panel
2. Verify API is returning correct data
3. Check logs for errors

---

## 📞 Need Help?

Refer to the detailed documentation files:
- `ANIGOLD_INTEGRATION_GUIDE.md` - Full guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details

---

## 🎉 You're All Set!

Your trading system is now fully operational with Anigold API integration!

**Happy trading!** 💰✨
