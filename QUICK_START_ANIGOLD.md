# 🚀 Quick Start - Anigold Integration

## ✅ What Has Been Implemented

### 1. **New Price Provider**
- ✅ Created `AnigoldPriceProvider` class in `trading/price_providers.py`
- ✅ Supports POST requests with Authorization header
- ✅ Fetches all 10 products from Anigold API
- ✅ Automatic Toman to Rial conversion
- ✅ Configurable via `settings.py`

### 2. **Product Models Updated**
- ✅ Added 10 new product codes to `trading/models.py`:
  - 6 Currencies: dollar_usa, euro, lira_turkey, yuan_china, pound_uk, dirham_uae
  - 3 Coins: coin_full, coin_half, coin_quarter
  - 1 Gold: gold_abshodeh
- ✅ Legacy code aliases for backward compatibility

### 3. **Pricing Logic**
- ✅ **Currencies**: ±1% dynamic margins (auto-calculated)
- ✅ **Coins**: ±4,500,000 Rials fixed margins
- ✅ **Gold**: ±300,000 Rials fixed margins
- ✅ Auto-calculation in `TradingService.update_all_prices()`

### 4. **Setup Script**
- ✅ Created `setup_anigold_products.py` to add all 10 products
- ✅ Proper weights configured for each coin type
- ✅ Margins set according to specifications

### 5. **Telegram Bot**
- ✅ Updated `bot/constants.py` with new product lists
- ✅ Updated `bot/handlers/trading.py` to support all products
- ✅ Currencies and coins use count-based calculation
- ✅ Gold uses weight-based calculation

### 6. **Admin Panel**
- ✅ Already supports all products dynamically
- ✅ Shows margin configuration and calculated prices
- ✅ Easy to add/edit/remove products

### 7. **Settings**
- ✅ Added Anigold API configuration to `gold_shop/settings.py`
- ✅ API key: `1a233fab-04d1-47b2-b732-813d93795c43`
- ✅ Provider type: `anigold` (default)
- ✅ Easy switching between providers

### 8. **Migration**
- ✅ Created migration `0016_add_anigold_product_codes.py`
- ✅ Updates product_code field choices

## 📋 Steps to Complete Setup

### Step 1: Apply Migrations
```bash
python manage.py migrate
```

### Step 2: Create Products
```bash
python setup_anigold_products.py
```

Expected output:
```
🚀 Starting Anigold products setup...

✅ Created: دلار آمریکا (dollar_usa)
✅ Created: یورو (euro)
✅ Created: لیر ترکیه (lira_turkey)
✅ Created: یوان چین (yuan_china)
✅ Created: پوند انگلیس (pound_uk)
✅ Created: درهم امارات (dirham_uae)
✅ Created: سکه غیربانکی (coin_full)
✅ Created: نیم سکه غیربانکی (coin_half)
✅ Created: ربع سکه غیربانکی (coin_quarter)
✅ Created: طلای آبشده (gold_abshodeh)

📊 Summary:
   ✅ Created: 10 products
   📦 Total: 10 products
```

### Step 3: Update Prices from API
```bash
python manage.py update_prices --show-details
```

Expected output:
```
🔄 شروع به‌روزرسانی قیمت‌ها از API...

📡 Fetching prices from API using AnigoldPriceProvider...
✅ Updated دلار آمریکا: Base=750,000, Margins=(7,500, 7,500), Buy=742,500, Sell=757,500
✅ Updated یورو: Base=800,000, Margins=(8,000, 8,000), Buy=792,000, Sell=808,000
... (all 10 products)

✅ قیمت‌ها با موفقیت به‌روزرسانی شد!
```

### Step 4: Verify in Admin Panel
1. Go to: `http://localhost:8000/admin/trading/product/`
2. You should see all 10 products with:
   - Current prices
   - Configured margins
   - Base API prices
   - Active status

### Step 5: Test in Telegram Bot
1. Send `/start` to your bot
2. Click "📈 قیمت‌ها و معامله"
3. You should see all 10 products listed
4. Test buy/sell for different product types:
   - Currency: Uses count/rial method
   - Coin: Uses count/rial method
   - Gold: Uses gram/rial method

## 🔧 Configuration

### API Settings

File: `gold_shop/settings.py`

```python
# Current configuration (already set)
PRICE_PROVIDER_TYPE = 'anigold'
ANIGOLD_API_KEY = '1a233fab-04d1-47b2-b732-813d93795c43'
```

### Product Margins

To change margins, edit products in admin panel or directly in database:

**Via Admin Panel:**
1. Go to Products
2. Click on a product
3. Edit "Buy Margin" and "Sell Margin"
4. Save
5. Run `python manage.py update_prices`

**Via Script:**
Edit `setup_anigold_products.py` and run again.

## 📊 Product Summary

| # | Product | Code | Weight | Buy Margin | Sell Margin |
|---|---------|------|--------|------------|-------------|
| 1 | دلار آمریکا | `dollar_usa` | 1g | 1% | 1% |
| 2 | یورو | `euro` | 1g | 1% | 1% |
| 3 | لیر ترکیه | `lira_turkey` | 1g | 1% | 1% |
| 4 | یوان چین | `yuan_china` | 1g | 1% | 1% |
| 5 | پوند انگلیس | `pound_uk` | 1g | 1% | 1% |
| 6 | درهم امارات | `dirham_uae` | 1g | 1% | 1% |
| 7 | سکه غیربانکی | `coin_full` | 8.133g | 4,500,000 ریال | 4,500,000 ریال |
| 8 | نیم سکه | `coin_half` | 4.0665g | 2,250,000 ریال | 2,250,000 ریال |
| 9 | ربع سکه | `coin_quarter` | 2.03325g | 1,125,000 ریال | 1,125,000 ریال |
| 10 | طلای آبشده | `gold_abshodeh` | 1g | 300,000 ریال | 300,000 ریال |

## 🤖 Automatic Price Updates

Set up cron job for automatic updates:

```bash
# Update every 5 minutes
*/5 * * * * cd /path/to/project && python manage.py update_prices

# Update every 15 minutes with details logged
*/15 * * * * cd /path/to/project && python manage.py update_prices --show-details >> /var/log/anigold_prices.log 2>&1
```

## ✅ Verification Checklist

- [ ] Migrations applied: `python manage.py migrate`
- [ ] Products created: `python setup_anigold_products.py`
- [ ] Prices updated: `python manage.py update_prices`
- [ ] Admin panel shows 10 products
- [ ] All products have current prices
- [ ] Bot displays all products
- [ ] Buy transaction works for currency
- [ ] Buy transaction works for coin
- [ ] Buy transaction works for gold
- [ ] Sell transaction works for all types
- [ ] Margins calculate correctly (±1% for currencies)

## 🎯 Key Files Modified/Created

### Created Files:
- ✅ `trading/migrations/0016_add_anigold_product_codes.py`
- ✅ `setup_anigold_products.py`
- ✅ `ANIGOLD_INTEGRATION_GUIDE.md`
- ✅ `QUICK_START_ANIGOLD.md`

### Modified Files:
- ✅ `trading/price_providers.py` - Added AnigoldPriceProvider
- ✅ `trading/models.py` - Added 10 product codes
- ✅ `trading/services.py` - Updated price update logic
- ✅ `gold_shop/settings.py` - Added Anigold config
- ✅ `bot/constants.py` - Added product categories
- ✅ `bot/handlers/trading.py` - Updated for all products

## 🚨 Important Notes

1. **Currency Margins**: The 1% margin is calculated dynamically during price updates, not stored statically
2. **Product Codes**: Must match exactly with `PRODUCT_MAPPING` in `price_providers.py`
3. **API Format**: Prices come in Tomans, automatically converted to Rials (×10)
4. **Backward Compatibility**: Legacy product codes (gold, coin, dollar) still work

## 📞 Support

For detailed documentation, see:
- `ANIGOLD_INTEGRATION_GUIDE.md` - Complete integration guide
- `ARCHITECTURE.md` - System architecture
- `API_SETUP.md` - API configuration details

## ✨ Success!

Your system is now fully integrated with Anigold API! 

All 10 products are configured and ready for trading through both the admin panel and Telegram bot.

Happy trading! 🎉
