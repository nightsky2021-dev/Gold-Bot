# Anigold API Integration Guide

## Overview

This guide explains the new Anigold API integration that replaces the previous Navasan API. The system now supports 10 tradeable products with dynamic pricing and flexible margin configuration.

## ✨ New Features

### 10 Tradeable Products

1. **Currencies** (6 products):
   - دلار آمریکا (US Dollar)
   - یورو (Euro)
   - لیر ترکیه (Turkish Lira)
   - یوان چین (Chinese Yuan)
   - پوند انگلیس (British Pound)
   - درهم امارات (UAE Dirham)

2. **Coins** (3 products):
   - سکه غیربانکی (Full Coin - Non-Bank)
   - نیم سکه غیربانکی (Half Coin - Non-Bank)
   - ربع سکه غیربانکی (Quarter Coin - Non-Bank)

3. **Gold** (1 product):
   - طلای آبشده (Molten Gold - 18 karat)

### Pricing Strategy

#### Currencies (±1%)
- **Buy Price**: Market Price - 1%
- **Sell Price**: Market Price + 1%
- Margins are calculated dynamically based on current market prices

#### Coins (±450,000 Toman)
- **Buy Price**: Market Price - 4,500,000 Rials
- **Sell Price**: Market Price + 4,500,000 Rials
- Fixed margins for stability

#### Gold (±30,000 Toman)
- **Buy Price**: Market Price - 300,000 Rials
- **Sell Price**: Market Price + 300,000 Rials
- Per gram pricing

## 🚀 Quick Start

### Step 1: Run Migrations

```bash
python manage.py migrate
```

### Step 2: Setup Products

```bash
python setup_anigold_products.py
```

This script will:
- Create all 10 products with proper configurations
- Set appropriate margins for each product category
- Configure weight parameters for coins

### Step 3: Update Prices

```bash
python manage.py update_prices --show-details
```

This command will:
- Fetch current prices from Anigold API
- Calculate 1% margins for currencies dynamically
- Update all product prices
- Display detailed price information

## 📡 API Configuration

### API Details

- **Endpoint**: `POST http://api.anigoldbot.ir/store/prices/`
- **Authentication**: Header `Authorization: {API_KEY}`
- **API Key**: `1a233fab-04d1-47b2-b732-813d93795c43`

### Changing API Provider

The system supports multiple API providers. To switch between them:

**Edit `gold_shop/settings.py`:**

```python
# Use Anigold (default)
PRICE_PROVIDER_TYPE = 'anigold'
ANIGOLD_API_KEY = '1a233fab-04d1-47b2-b732-813d93795c43'

# Or use Navasan (legacy)
PRICE_PROVIDER_TYPE = 'navasan'
NAVASAN_API_KEY = 'your-navasan-key'
```

### Response Format

The API returns an array of price objects:

```json
[
  {
    "fa_slug": "دلار آمریکا",
    "en_slug": "price_usd",
    "price": "75000",
    "buyprice": "75000",
    "maxPrice": "75500",
    "minPrice": "74500",
    "diff": "500",
    "diff_percent": "0.67",
    "dir": "up",
    "last_update": "2025-11-06T16:19:51.903"
  },
  ...
]
```

**Note**: Prices are in **Tomans** and automatically converted to Rials (×10).

## 🛠️ Admin Panel Usage

### Managing Products

1. Navigate to **Admin Panel** → **Trading** → **Products**

2. Each product shows:
   - Current buy/sell prices
   - Configured margins
   - Base API price
   - Last update time

3. To modify a product:
   - Edit **Buy Margin** (خرید از مشتری)
   - Edit **Sell Margin** (فروش به مشتری)
   - Edit **Weight** (وزن واحد) for coins
   - Click **Save**

4. Run `python manage.py update_prices` after changes

### Product Fields Explained

| Field | Description | Example |
|-------|-------------|---------|
| **Product Code** | Unique identifier | `dollar_usa` |
| **Name** | Persian display name | دلار آمریکا |
| **Weight (grams)** | Unit weight | `1` for currencies, `8.133` for full coin |
| **Buy Margin** | Amount subtracted from market price | 750,000 Rials |
| **Sell Margin** | Amount added to market price | 750,000 Rials |
| **Base Price API** | Last price from API | 750,000,000 Rials |
| **Buy Price** | Calculated: Base - Buy Margin | 749,250,000 Rials |
| **Sell Price** | Calculated: Base + Sell Margin | 750,750,000 Rials |

### Adding New Products

To add a new tradeable product:

1. **Create Product via Admin**:
   - Go to Products → Add Product
   - Set product code (must match API)
   - Set name (Persian)
   - Configure margins
   - Set weight

2. **Update Price Provider** (if needed):
   Edit `trading/price_providers.py`:
   
   ```python
   PRODUCT_MAPPING = {
       # ... existing products ...
       'new_product': 'price_api_field',
   }
   ```

3. **Run Price Update**:
   ```bash
   python manage.py update_prices
   ```

## 🤖 Telegram Bot Integration

The Telegram bot automatically supports all active products:

### User Experience

1. **View Prices**: Users see all active products with live prices
2. **Select Product**: Choose from any available product
3. **Choose Method**: 
   - **Currencies/Coins**: Count or Rial
   - **Gold**: Gram or Rial
4. **Enter Amount**: Type the amount to buy/sell
5. **Confirm**: Review and confirm transaction

### Bot Constants

The bot uses product categories for logic:

```python
# bot/constants.py
CURRENCY_PRODUCTS = [
    'dollar_usa', 'euro', 'lira_turkey',
    'yuan_china', 'pound_uk', 'dirham_uae'
]

COIN_PRODUCTS = [
    'coin_full', 'coin_half', 'coin_quarter'
]

GOLD_PRODUCTS = [
    'gold_abshodeh'
]
```

## 📊 Price Update System

### Automatic Price Updates

Set up a cron job for automatic updates:

```bash
# Update prices every 5 minutes
*/5 * * * * cd /path/to/project && python manage.py update_prices >> /var/log/prices.log 2>&1
```

### Manual Updates

```bash
# Basic update
python manage.py update_prices

# Detailed update with full price display
python manage.py update_prices --show-details
```

### Update Process

1. **Fetch Prices**: Connect to Anigold API
2. **Parse Response**: Extract price data for each product
3. **Calculate Margins**:
   - Currencies: Calculate 1% dynamically
   - Coins: Apply fixed margins
   - Gold: Apply fixed margin
4. **Update Database**: Save new prices
5. **Log Results**: Record success/failure

## 🔧 Advanced Configuration

### Custom Margin Calculation

Edit `trading/services.py` → `TradingService.update_all_prices()`:

```python
# For currencies, dynamically calculate 1% margin
if product.product_code in CURRENCY_PRODUCTS:
    calculated_margin = (base_price * Decimal('0.01')).quantize(Decimal('1'))
    product.buy_margin = calculated_margin
    product.sell_margin = calculated_margin
```

### Product-Specific Logic

Add custom logic in `trading/models.py` → `Product` class:

```python
def calculate_prices_from_base(self, base_price: Decimal) -> tuple[Decimal, Decimal]:
    # Custom logic per product
    adjusted_base = base_price * self.weight_grams
    buy_price = (adjusted_base - self.buy_margin).quantize(Decimal('1'))
    sell_price = (adjusted_base + self.sell_margin).quantize(Decimal('1'))
    return buy_price, sell_price
```

## 📈 Monitoring & Reports

### Admin Dashboard

Access reports at: **Admin Panel** → **Dashboard**

Shows:
- Total trade volume
- Product performance
- User activity
- Profit margins

### Database Queries

```python
# Get top products by volume
from trading.models import Order, Product
from django.db.models import Sum

top_products = Product.objects.annotate(
    volume=Sum('orders__total_amount')
).order_by('-volume')[:10]
```

## 🐛 Troubleshooting

### Prices Not Updating

1. **Check API Connection**:
   ```bash
   python -c "
   from trading.price_providers import get_active_provider
   p = get_active_provider()
   print(p._fetch_all_prices())
   "
   ```

2. **Verify API Key**:
   ```bash
   grep ANIGOLD_API_KEY gold_shop/settings.py
   ```

3. **Check Logs**:
   ```bash
   tail -f /var/log/django.log
   ```

### Product Not Appearing in Bot

1. Ensure product is **active** in admin
2. Run price update
3. Restart bot if needed

### Incorrect Margins

1. Check product configuration in admin
2. Verify margin calculation logic
3. Run `update_prices` with `--show-details`

## 📝 API Field Mapping

| Product | API Field | Product Code |
|---------|-----------|--------------|
| دلار آمریکا | `price_usd` | `dollar_usa` |
| یورو | `price_eur` | `euro` |
| لیر ترکیه | `price_try` | `lira_turkey` |
| یوان چین | `price_cny` | `yuan_china` |
| پوند انگلیس | `price_gbp` | `pound_uk` |
| درهم امارات | `price_aed` | `dirham_uae` |
| سکه غیربانکی | `price_sekeb` | `coin_full` |
| نیم سکه | `price_nim` | `coin_half` |
| ربع سکه | `price_rob` | `coin_quarter` |
| طلای آبشده | `price_geram18` | `gold_abshodeh` |

## 🔐 Security Notes

1. **API Key Protection**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` file for sensitive data
3. **Rate Limiting**: API has no documented limits, but use reasonable intervals
4. **Error Handling**: All API calls have retry logic and fallback

## 📚 Additional Resources

- **Architecture**: See `ARCHITECTURE.md`
- **API Setup**: See `API_SETUP.md`
- **Admin Guide**: See `ADMIN_ARCHITECTURE.md`
- **Price Providers**: `trading/price_providers.py`
- **Services**: `trading/services.py`

## ✅ Testing Checklist

- [ ] Migrations applied successfully
- [ ] All 10 products created
- [ ] Prices update from API
- [ ] Bot shows all products
- [ ] Buy/sell transactions work
- [ ] Margins calculate correctly
- [ ] Admin panel displays properly

## 🎉 Success!

Your system is now configured with Anigold API integration. All products are tradeable through both the admin panel and Telegram bot with dynamic pricing and flexible margin configuration.

For support or questions, refer to the project documentation or contact the development team.
