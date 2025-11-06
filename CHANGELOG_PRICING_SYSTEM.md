# Changelog: Dynamic Pricing System

## Version 2.0 - November 2025

### 🎯 Major Changes

#### New Feature: Dynamic Margin-Based Pricing System

The pricing system has been completely redesigned to allow admins to configure **calculation parameters** instead of direct prices.

---

## 📝 Detailed Changes

### 1. Database Schema (trading/models.py)

#### Added Fields to `Product` Model:
```python
buy_margin          # Decimal - Margin to subtract from market price
sell_margin         # Decimal - Margin to add to market price  
weight_grams        # Decimal - Weight per unit (for coins)
base_price_api      # Decimal - Last API price received (nullable)
```

#### Updated Fields:
```python
buy_price           # Now auto-calculated (readonly in admin)
sell_price          # Now auto-calculated (readonly in admin)
```

#### New Methods:
```python
Product.calculate_prices_from_base(base_price)
    # Calculate buy/sell from base price using product's margins
    
Product.update_prices_from_api(api_base_price)
    # Update prices from API base price
    
Product.get_total_margin()
    # Get sum of buy + sell margins
    
Product.get_margin_info_display()
    # Get formatted margin info string
```

### 2. Admin Interface (trading/admin.py)

#### Updated `ProductAdmin` Class:

**List Display Changes:**
- ✅ Added: `margin_display` - Shows configured margins
- ✅ Added: `calculated_buy_price` - Shows calculated buy price
- ✅ Added: `calculated_sell_price` - Shows calculated sell price
- ✅ Added: `base_api_price_display` - Shows API base price
- ❌ Removed: Direct `buy_price`, `sell_price` columns
- ❌ Removed: Editable prices from list view

**Fieldsets Restructured:**
```
1. اطلاعات محصول (Product Info)
   - product_code, name, slug

2. ⚙️ تنظیمات محاسبه قیمت (Calculation Settings) - EDITABLE
   - buy_margin, sell_margin, weight_grams
   - Includes inline documentation

3. 📊 قیمت‌های محاسبه شده (Calculated Prices) - READONLY
   - calculated_price_preview (formula breakdown)
   - base_price_api, buy_price, sell_price

4. وضعیت (Status)
   - is_active

5. تاریخچه (History)
   - created_at, updated_at
```

**New Display Methods:**
```python
margin_display()              # Shows margins with icons
calculated_buy_price()        # Green colored buy price
calculated_sell_price()       # Red colored sell price
base_api_price_display()      # Blue API price
calculated_price_preview()    # Full calculation breakdown
```

### 3. Price Calculator (trading/price_calculator.py)

#### New Method:
```python
PriceCalculator.calculate_product_prices(product, api_base_price)
    # Uses product's own margins and weight for calculation
```

#### Deprecated Methods (kept for backward compatibility):
```python
calculate_gold_abshodeh_prices()   # [DEPRECATED]
calculate_coin_full_prices()       # [DEPRECATED]
calculate_dollar_prices()          # [DEPRECATED]
calculate_all_prices()             # [DEPRECATED]
```

**Note:** Old methods still work but are deprecated. New code should use `Product.calculate_prices_from_base()` directly.

### 4. Trading Service (trading/services.py)

#### Rewritten `TradingService.update_all_prices()`:

**Before:**
```python
# Hardcoded margins in PriceCalculator
# Product-specific logic for each type
# Used deprecated calculate_all_prices()
```

**After:**
```python
# Dynamic margins from Product model
# Generic loop over all products
# Uses Product.update_prices_from_api()
# Better logging with margin details
```

**New Logic:**
1. Fetch API prices (gold, dollar_buy, dollar_sell)
2. Map product_code to base price
3. For each product:
   - Get base price from map
   - Call `product.update_prices_from_api(base_price)`
   - Save updated product
4. Log detailed calculation info

### 5. Database Migration

**Migration File:** `trading/migrations/0015_product_base_price_api_product_buy_margin_and_more.py`

**Operations:**
1. Add `base_price_api` field
2. Add `buy_margin` field (default: 0)
3. Add `sell_margin` field (default: 0)
4. Add `weight_grams` field (default: 1)
5. Alter `buy_price` field (update help text)
6. Alter `sell_price` field (update help text)
7. Run data migration to set default margins:
   - Gold: 300,000 / 300,000
   - Coin: 4,500,000 / 4,500,000  
   - Dollar: 10,000 / 10,000

**Backward Compatible:** Includes reverse operation.

---

## 📚 Documentation Added

### New Files:
1. **ADMIN_PRICING_GUIDE.md**
   - Comprehensive guide for admins
   - Examples and scenarios
   - Step-by-step instructions

2. **MIGRATION_GUIDE_PRICING_SYSTEM.md**
   - Migration instructions
   - Rollback procedure
   - Troubleshooting guide

3. **CHANGELOG_PRICING_SYSTEM.md** (this file)
   - Complete change log
   - Technical details

---

## 🔄 API/Interface Changes

### Breaking Changes:
❌ None - Fully backward compatible

### Deprecated:
⚠️ `PriceCalculator.calculate_gold_abshodeh_prices()` - Use `Product.calculate_prices_from_base()`
⚠️ `PriceCalculator.calculate_coin_full_prices()` - Use `Product.calculate_prices_from_base()`
⚠️ `PriceCalculator.calculate_dollar_prices()` - Use `Product.calculate_prices_from_base()`
⚠️ `PriceCalculator.calculate_all_prices()` - Not needed anymore

### New Public API:
```python
# Product model methods
Product.calculate_prices_from_base(base_price) -> (buy, sell)
Product.update_prices_from_api(api_base_price) -> None
Product.get_total_margin() -> Decimal
Product.get_margin_info_display() -> str

# Fields
Product.buy_margin: Decimal
Product.sell_margin: Decimal
Product.weight_grams: Decimal
Product.base_price_api: Decimal | None

# Calculator
PriceCalculator.calculate_product_prices(product, api_price) -> ProductPrices
```

---

## 🎨 UI/UX Improvements

### Admin Panel:
✅ Rich help text with HTML formatting
✅ Color-coded price displays (green buy, red sell, blue API)
✅ Inline calculation preview showing formula
✅ Margin summary in list view
✅ Warning messages for missing API prices
✅ Better field organization with emoji icons
✅ Clearer distinction between editable and readonly fields

### Command Line:
✅ Enhanced logging in `update_prices` with margin details
✅ Better error messages
✅ Calculation details in logs

---

## 🧪 Testing Recommendations

### Manual Testing Checklist:
- [ ] Create new product with custom margins
- [ ] Edit existing product margins
- [ ] Run `update_prices` command
- [ ] Verify calculations in admin panel
- [ ] Check calculation preview display
- [ ] Test with different weight values
- [ ] Verify API price tracking
- [ ] Test backward compatibility with old code

### Automated Tests Needed:
```python
# tests/test_product_pricing.py
- test_calculate_prices_from_base()
- test_update_prices_from_api()
- test_get_total_margin()
- test_margin_calculations_gold()
- test_margin_calculations_coin()
- test_weight_multiplication()
```

---

## 📊 Performance Impact

### Positive:
✅ Simplified price update logic
✅ Reduced hardcoded values
✅ Better maintainability

### Neutral:
➖ No significant performance change
➖ Same number of database queries

### Migration:
⚠️ One-time migration adds 4 fields per product (minimal impact)

---

## 🔐 Security Considerations

### No Security Impact:
- No authentication/authorization changes
- No exposure of sensitive data
- Margin values are admin-only (already protected)

### Admin Panel:
✅ Prices readonly prevents accidental manual edits
✅ Calculation transparency helps catch errors

---

## 🚀 Deployment Instructions

### Pre-Deployment:
1. Backup database
2. Test migration on staging
3. Train admins on new system

### Deployment:
```bash
# 1. Pull latest code
git pull origin main

# 2. Run migration
python manage.py migrate trading

# 3. Update prices
python manage.py update_prices --show-details

# 4. Verify in admin panel
# Check Products → verify margins are set
```

### Post-Deployment:
1. Monitor logs for any errors
2. Verify prices are calculating correctly
3. Check admin panel accessibility
4. Update cron jobs if needed

---

## 🐛 Known Issues

### None at release time

---

## 💡 Future Enhancements

### Possible Improvements:
1. **Percentage-based margins**: Allow margins as % instead of fixed amounts
2. **Time-based margins**: Different margins for different times/days
3. **Volume-based margins**: Reduced margins for large orders
4. **Margin presets**: Quick templates for common scenarios
5. **Margin history**: Track margin changes over time
6. **Automated margin optimization**: ML-based margin suggestions
7. **Multi-currency support**: More sophisticated currency handling
8. **Real-time price updates**: WebSocket-based live price feeds

---

## 📞 Support & Contact

**For Questions:**
- Technical: Review code comments and docstrings
- Admin Usage: See `ADMIN_PRICING_GUIDE.md`
- Migration: See `MIGRATION_GUIDE_PRICING_SYSTEM.md`

**For Issues:**
- Check logs in `logs/` directory
- Review Django admin error messages
- Consult troubleshooting sections in guides

---

## ✅ Sign-off

**Developed By:** AI Assistant  
**Reviewed By:** _[Pending]_  
**Tested By:** _[Pending]_  
**Approved By:** _[Pending]_  
**Deployment Date:** _[Pending]_  

**Status:** ✅ Ready for Review & Testing

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Nov 2025 | Initial release of dynamic pricing system |
| 1.0 | Oct 2025 | Original hardcoded pricing system |

