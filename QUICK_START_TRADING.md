# 🚀 Quick Start Guide - Trading System

## Get Started in 5 Minutes

---

## Step 1: Setup Test Data (30 seconds)

```bash
python setup_test_data.py
```

This creates:
- ✅ 3 Products (Gold, Coin, Dollar) with prices
- ✅ 2 Test users (rich & poor) with balances
- ✅ Verified bank accounts

---

## Step 2: Start the Bot (10 seconds)

```bash
python manage.py runbot
```

---

## Step 3: Test Buy Transaction (2 minutes)

### Using Telegram:

1. **Send `/start` to your bot**

2. **Click "📈 قیمت‌ها و معامله"**

3. **Select "🪙 طلای آبشده"**

4. **Click "🟢 خرید"** (Buy)

5. **Choose "⚖️ محاسبه بر اساس مقدار"**

6. **Type: `2`** (2 grams)

7. **You'll see detailed invoice:**
```
🧾 فاکتور خرید
═══════════════════════
📦 محصول: طلای آبشده
💎 قیمت هر گرم: 5,000,000 ریال
⚖️ مقدار: 2 گرم
💵 مبلغ کل: 10,000,000 ریال

💳 پرداخت: 10,000,000 ریال
📥 دریافت: 2 گرم

─────────────────────
💼 موجودی‌ها:

ریال:
  • فعلی: 100,000,000 ریال
  • پس از معامله: 90,000,000 ریال

طلای آبشده:
  • فعلی: 20 گرم
  • پس از معامله: 22 گرم
═══════════════════════

آیا از انجام این معامله مطمئن هستید؟
```

8. **Click "✨ تایید و ثبت سفارش ✨"**

9. **Success! You'll see:**
```
✅ خرید شما با موفقیت انجام شد!

🧾 شماره سفارش: #1
📦 محصول: طلای آبشده
⚖️ مقدار: 2 گرم
💵 مبلغ پرداختی: 10,000,000 ریال

═══════════════════════
💼 موجودی‌های جدید:
💰 ریال: 90,000,000 ریال
📦 طلای آبشده: 22 گرم
═══════════════════════

از خرید شما متشکریم! 🙏
```

---

## Step 4: Test Sell Transaction (2 minutes)

1. **Go back to "📈 قیمت‌ها و معامله"**

2. **Select "🪙 طلای آبشده"**

3. **Click "🔴 فروش"** (Sell)

4. **Type: `5`** (5 grams)

5. **See invoice, then confirm**

6. **Result:**
   - Gold: -5 grams
   - Rial: +22,500,000 (at 4.5M/gram buy price)

---

## Step 5: Test Error Handling (1 minute)

### Test Insufficient Balance:

1. **Try to buy 50 grams** (would cost 250M)

2. **You'll see error:**
```
❌ موجودی ریالی کافی نیست!

💼 موجودی فعلی: 90,000,000 ریال
💰 مورد نیاز: 250,000,000 ریال
⚠️ کمبود: 160,000,000 ریال

لطفاً ابتدا کیف پول خود را شارژ کنید.
```

---

## ✅ Verification

### Check in Django Shell:

```bash
python manage.py shell
```

```python
from users.models import Profile
from trading.models import Order

# Get your test user
profile = Profile.objects.get(telegram_id="123456789")

# Check balances
print(f"Rial: {profile.rial_balance:,}")
print(f"Gold: {profile.gold_balance_grams}")

# Check orders
orders = Order.objects.filter(profile=profile)
print(f"Total orders: {orders.count()}")
print(f"Completed: {orders.filter(status='COMPLETED').count()}")

# Last order
last = orders.order_by('-created_at').first()
print(f"\nLast order: {last.get_order_type_display()}")
print(f"Status: {last.get_status_display()}")
print(f"Amount: {last.total_amount:,}")
```

---

## 🎯 What Just Happened?

### Behind the Scenes:

1. **Balance Validation** ✓
   - Checked if you have enough Rial/Gold

2. **Invoice Generation** ✓
   - Showed detailed transaction preview

3. **Atomic Transaction** ✓
   - Created order + Updated balances in one operation

4. **Immediate Execution** ✓
   - No waiting for admin approval

5. **Success Confirmation** ✓
   - Showed updated balances instantly

---

## 📱 Available Products

| Product | Code | Buy Price* | Sell Price* | Unit |
|---------|------|-----------|-------------|------|
| 🪙 طلای آبشده | gold | 4.5M | 5M | گرم |
| 🥇 سکه تمام | coin | 19M | 20M | عدد |
| 💵 دلار | dollar | 450K | 500K | دلار |

*Buy Price = We buy from you | Sell Price = You buy from us

---

## 🧪 Test Scenarios

### ✅ Happy Path
- Buy with sufficient balance
- Sell with sufficient product
- Multiple transactions
- Different products

### ❌ Error Cases
- Buy without enough Rial
- Sell without owning product
- Invalid amounts (negative, zero)
- Cancel transaction

---

## 🔧 Troubleshooting

### Bot not responding?
```bash
# Check if bot is running
# Look for errors in terminal

# Restart bot
python manage.py runbot
```

### Balance not updating?
```python
# Check order status
from trading.models import Order
order = Order.objects.last()
print(order.status)  # Should be 'COMPLETED'
```

### Prices not showing?
```python
# Check products exist
from trading.models import Product
products = Product.objects.filter(is_active=True)
for p in products:
    print(f"{p.name}: {p.sell_price:,}")
```

---

## 📚 More Information

- **Full Testing Guide:** `TRADING_TESTING_GUIDE.md`
- **All Changes:** `TRADING_CHANGELOG.md`
- **Setup Script:** `setup_test_data.py`

---

## 🎓 Next Steps

1. ✅ **Test all scenarios** (10 minutes)
   - Follow `TRADING_TESTING_GUIDE.md`

2. ✅ **Customize prices** (2 minutes)
   ```bash
   python manage.py shell
   ```
   ```python
   from trading.models import Product
   gold = Product.objects.get(product_code='gold')
   gold.sell_price = 5500000  # New price
   gold.save()
   ```

3. ✅ **Add real users** (5 minutes)
   - Send bot link to users
   - They send /start
   - Approve them in Django admin

4. ✅ **Monitor orders** (ongoing)
   ```bash
   # Django admin
   http://localhost:8000/admin/trading/order/
   ```

---

## 🚀 Production Checklist

Before going live:

- [ ] Test all buy/sell scenarios
- [ ] Verify balance updates
- [ ] Check error messages
- [ ] Test with multiple users
- [ ] Update product prices
- [ ] Configure admin notifications
- [ ] Backup database
- [ ] Monitor logs

---

## 💡 Pro Tips

### Quick Price Update:
```python
from trading.models import Product
Product.objects.filter(product_code='gold').update(
    buy_price=4600000,
    sell_price=5100000
)
```

### Check User Balance:
```python
from users.models import Profile
p = Profile.objects.get(telegram_id="YOUR_USER_ID")
print(f"Rial: {p.rial_balance:,}")
print(f"Gold: {p.gold_balance_grams}")
```

### View Recent Orders:
```python
from trading.models import Order
Order.objects.order_by('-created_at')[:10]
```

---

## ✅ Success Indicators

You're ready when:
- ✅ Test buy works without errors
- ✅ Test sell works without errors
- ✅ Balances update immediately
- ✅ Error messages are clear
- ✅ Invoice shows correct info
- ✅ Orders saved as COMPLETED

---

**🎉 Congratulations! Your trading system is ready!**

**Need help?** Check `TRADING_TESTING_GUIDE.md` for detailed scenarios.

