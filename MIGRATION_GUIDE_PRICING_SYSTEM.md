# Migration Guide: New Pricing System

## 🎯 Overview

This guide explains how to migrate from the old hardcoded pricing system to the new dynamic margin-based pricing system.

## 📋 What Changed?

### Before (Old System):
- ❌ Margins were hardcoded in `PriceCalculator` class
- ❌ Admins had to directly edit buy/sell prices
- ❌ Prices needed manual updates
- ❌ No flexibility per product

### After (New System):
- ✅ Margins are configurable per product in admin panel
- ✅ Admins configure calculation parameters (margins, weights)
- ✅ Prices auto-calculated from API + margins
- ✅ Each product can have unique margins

## 🔄 Migration Steps

### Step 1: Run Database Migration

```bash
python manage.py migrate trading
```

This will:
- Add `buy_margin`, `sell_margin`, `weight_grams` fields to Product model
- Add `base_price_api` field to track API prices
- Set default margins based on old hardcoded values:
  - Gold: 300,000 Rials for both buy and sell
  - Coin: 4,500,000 Rials for both buy and sell
  - Dollar: 10,000 Rials for both buy and sell

### Step 2: Verify Products in Admin

1. Go to Django Admin → Products
2. Check each product has proper margin values
3. Verify weight values:
   - Gold: 1 gram
   - Dollar: 1 unit
   - Coin: 8.133 grams (or your actual coin weight)

### Step 3: Update Prices

```bash
python manage.py update_prices --show-details
```

This will:
- Fetch latest prices from API
- Calculate buy/sell prices using new margin system
- Update all products

### Step 4: Verify Calculations

Check that prices match expected values:
- Old system: `API_price ± fixed_margin`
- New system: `(API_price × weight) ± product_margin`

## 🎨 Admin Panel Changes

### Product List View
**New columns:**
- `مارجین‌ها`: Shows buy/sell margins and total
- `💰 قیمت خرید`: Calculated buy price (readonly)
- `💵 قیمت فروش`: Calculated sell price (readonly)
- `📡 قیمت API`: Base price from API

**Changed:**
- Buy/Sell prices are now **readonly** (auto-calculated)
- Only `is_active` remains editable in list view

### Product Edit View
**New section: "⚙️ تنظیمات محاسبه قیمت"**
- `buy_margin`: Margin deducted from market price for buying from customer
- `sell_margin`: Margin added to market price for selling to customer
- `weight_grams`: Weight per unit (1 for gold/dollar, actual weight for coins)

**New section: "📊 قیمت‌های محاسبه شده"**
- Shows calculation preview with formula
- Displays base API price, calculated prices
- All fields are readonly

## 🔧 Customization After Migration

### Adjusting Margins

To change profit margins for a product:

1. Go to Admin → Products → Select product
2. In "⚙️ تنظیمات محاسبه قیمت":
   - Adjust `buy_margin` (amount to subtract from market price)
   - Adjust `sell_margin` (amount to add to market price)
3. Save
4. Run: `python manage.py update_prices`

### Adding New Products

For new products (e.g., half coin, quarter coin):

1. Create product in admin
2. Set appropriate `product_code`
3. Configure margins and weight:
   ```
   Example for Half Coin:
   - weight_grams: 4.066
   - buy_margin: 2,250,000 (half of full coin)
   - sell_margin: 2,250,000
   ```
4. Run `update_prices`

## 📊 Calculation Examples

### Gold (per gram):
```
API Price: 10,000,000 Rials
Weight: 1 gram
Buy Margin: 300,000 Rials
Sell Margin: 300,000 Rials

Adjusted Base = 10,000,000 × 1 = 10,000,000
Buy Price = 10,000,000 - 300,000 = 9,700,000 Rials
Sell Price = 10,000,000 + 300,000 = 10,300,000 Rials
Profit = 600,000 Rials
```

### Coin (per coin):
```
API Price (gold): 10,000,000 Rials/gram
Weight: 8.133 grams
Buy Margin: 4,500,000 Rials
Sell Margin: 4,500,000 Rials

Adjusted Base = 10,000,000 × 8.133 = 81,330,000
Buy Price = 81,330,000 - 4,500,000 = 76,830,000 Rials
Sell Price = 81,330,000 + 4,500,000 = 85,830,000 Rials
Profit = 9,000,000 Rials
```

## 🚨 Important Notes

### ✅ Safe Operations:
- Adjusting margins in admin panel
- Running `update_prices` command
- Viewing price calculations

### ⚠️ Handle with Care:
- Changing `weight_grams` (affects all calculations)
- Large margin changes (verify profit/loss first)
- Modifying `product_code` (used for API price mapping)

### ❌ Avoid:
- Directly editing `buy_price` or `sell_price` in database
- Manually overriding calculated prices
- Deleting migration files

## 🔄 Rollback Plan

If you need to rollback:

```bash
# Rollback migration
python manage.py migrate trading 0014_rename_trading_tra_status_b8c123_idx_trading_tra_status_6fc988_idx_and_more

# This will remove the new fields and revert to old system
```

**Note:** After rollback, you'll need to use the old hardcoded margin system in `PriceCalculator`.

## 📚 Related Documentation

- **Admin Guide**: `ADMIN_PRICING_GUIDE.md` - Detailed pricing guide for admins
- **README**: `README.md` - General project documentation
- **Architecture**: `ARCHITECTURE.md` - System architecture

## ✅ Post-Migration Checklist

- [ ] Migration completed successfully
- [ ] All products have correct margin values
- [ ] Prices updated via `update_prices` command
- [ ] Calculations verified in admin panel
- [ ] Admins trained on new system
- [ ] Cron job updated (if needed)
- [ ] Backup created before migration
- [ ] Tested on staging environment first

## 🆘 Troubleshooting

### Problem: Prices not updating
**Solution:** Run `python manage.py update_prices` manually

### Problem: Incorrect calculations
**Solution:** 
1. Check margin values in admin
2. Verify weight_grams is correct
3. Check `base_price_api` field has value

### Problem: Migration fails
**Solution:**
1. Check database connectivity
2. Ensure no conflicting migrations
3. Review error logs
4. Try `python manage.py migrate --fake trading 0015` (as last resort)

## 📞 Support

If you encounter issues:
1. Check logs: `logs/` directory
2. Review this guide
3. Consult `ADMIN_PRICING_GUIDE.md`
4. Contact system administrator

---

**Migration Date**: November 2025  
**Migration Version**: 0015_product_base_price_api_product_buy_margin_and_more  
**Status**: ✅ Ready for Production

