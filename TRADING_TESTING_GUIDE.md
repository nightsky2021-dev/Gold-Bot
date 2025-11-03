# 🧪 Trading System Testing Guide

## Overview
This guide provides comprehensive test scenarios for the enhanced trading system with real-time balance validation and immediate transaction execution.

---

## 🎯 Test Prerequisites

### 1. Database Setup
Ensure you have:
- ✅ At least one approved user profile
- ✅ Active products (Gold, Coin, Dollar) with prices set
- ✅ Test user with varying balance scenarios

### 2. Create Test User with Balance
```python
# Run in Django shell: python manage.py shell
from users.models import Profile
from django.contrib.auth.models import User

# Get or create test user
user = User.objects.get(username="tg_123456789")  # Your test user
profile = user.profile

# Set test balances
profile.rial_balance = 50000000  # 50 million Rial
profile.gold_balance_grams = 10.0  # 10 grams
profile.coin_balance = 5  # 5 coins
profile.dollar_balance = 100  # 100 dollars
profile.save()

print(f"✅ Test user ready: {profile.get_display_name()}")
print(f"💰 Rial: {profile.rial_balance:,}")
print(f"🪙 Gold: {profile.gold_balance_grams}")
```

---

## 📋 Test Scenarios

### Scenario 1: Successful Buy Transaction ✅

**Setup:**
- User has: 50,000,000 Rial
- Product: Gold at 5,000,000 Rial/gram

**Steps:**
1. Open bot and navigate to "📈 قیمت‌ها و معامله"
2. Select "🪙 طلای آبشده"
3. Click "🟢 خرید" (Buy)
4. Select "⚖️ محاسبه بر اساس مقدار (گرم/عدد)"
5. Enter: `5` (5 grams)
6. Verify invoice shows:
   - ✓ Product: طلای آبشده
   - ✓ Quantity: 5 گرم
   - ✓ Total: 25,000,000 ریال
   - ✓ Current Rial: 50,000,000
   - ✓ After Rial: 25,000,000
   - ✓ Current Gold: 10.0 گرم
   - ✓ After Gold: 15.0 گرم
7. Click "✨ تایید و ثبت سفارش ✨"
8. Verify success message with:
   - ✓ Order number
   - ✓ Updated balances shown

**Expected Result:** ✅
- Rial deducted: -25,000,000
- Gold added: +5 grams
- Order status: COMPLETED
- User sees updated balances immediately

---

### Scenario 2: Buy with Insufficient Balance ❌

**Setup:**
- User has: 10,000,000 Rial
- Product: Gold at 5,000,000 Rial/gram

**Steps:**
1. Navigate to Gold product
2. Click "🟢 خرید"
3. Select amount calculation method
4. Enter: `5` (5 grams = 25M Rial needed)
5. **Expected:** Error message appears:

```
❌ موجودی ریالی کافی نیست!

💼 موجودی فعلی: 10,000,000 ریال
💰 مورد نیاز: 25,000,000 ریال
⚠️ کمبود: 15,000,000 ریال

لطفاً ابتدا کیف پول خود را شارژ کنید.
```

**Expected Result:** ✅
- Transaction blocked
- Clear error with shortage amount
- Balance unchanged
- Conversation ends

---

### Scenario 3: Successful Sell Transaction ✅

**Setup:**
- User has: 10.0 grams Gold
- Product: Gold buy price 4,500,000 Rial/gram

**Steps:**
1. Navigate to Gold product
2. Click "🔴 فروش" (Sell)
3. Select "⚖️ محاسبه بر اساس مقدار"
4. Enter: `3` (3 grams)
5. Verify invoice shows:
   - ✓ Current Gold: 10.0 گرم
   - ✓ After Gold: 7.0 گرم
   - ✓ Receive: 13,500,000 ریال
6. Confirm transaction

**Expected Result:** ✅
- Gold deducted: -3 grams
- Rial added: +13,500,000
- Order status: COMPLETED

---

### Scenario 4: Sell with Insufficient Product ❌

**Setup:**
- User has: 2.0 grams Gold

**Steps:**
1. Try to sell: `5` grams
2. **Expected:** Error message:

```
❌ موجودی طلای آبشده کافی نیست!

💼 موجودی فعلی: 2.0 گرم
📤 مورد نیاز: 5.0 گرم
⚠️ کمبود: 3.0 گرم

شما نمی‌توانید بیشتر از موجودی خود بفروشید.
```

**Expected Result:** ✅
- Transaction blocked
- Clear error message
- Balance unchanged

---

### Scenario 5: Buy Using Rial Amount 💰

**Setup:**
- User has: 50,000,000 Rial
- Gold price: 5,000,000 Rial/gram

**Steps:**
1. Select Gold → Buy
2. Choose "💰 محاسبه بر اساس مبلغ (ریال)"
3. Enter: `10000000` (10 million Rial)
4. Verify invoice shows:
   - ✓ Quantity: 2.0 گرم (calculated)
   - ✓ Total: 10,000,000 ریال
5. Confirm

**Expected Result:** ✅
- Deduct: 10M Rial
- Add: 2.0 grams Gold

---

### Scenario 6: Multi-Product Testing (Coin) 🥇

**Setup:**
- User has: 5 coins
- Coin sell price: 20,000,000 Rial/coin

**Steps:**
1. Navigate to "🥇 سکه تمام"
2. Click "🔴 فروش"
3. Enter: `2` (2 coins)
4. Verify invoice shows correct units (عدد)
5. Confirm

**Expected Result:** ✅
- Coins deducted: -2 عدد
- Rial added: +40,000,000

---

### Scenario 7: Multi-Product Testing (Dollar) 💵

**Setup:**
- User has: 20,000,000 Rial
- Dollar sell price: 500,000 Rial/dollar

**Steps:**
1. Navigate to "💵 دلار"
2. Click "🟢 خرید"
3. Enter: `10` (10 dollars)
4. Verify total: 5,000,000 Rial
5. Confirm

**Expected Result:** ✅
- Rial deducted: -5,000,000
- Dollar added: +10 دلار

---

### Scenario 8: Edge Cases 🔬

#### 8.1: Very Small Amount
- Try buying: `0.01` grams
- **Expected:** Should work if within MIN_ORDER_GRAMS

#### 8.2: Decimal Amounts
- Try buying: `2.5` grams
- **Expected:** Works correctly

#### 8.3: Cancel During Transaction
- Start buy process
- Click "🔙 انصراف" at invoice stage
- **Expected:** Transaction cancelled, no changes

#### 8.4: Expired Price (if implemented)
- View product price
- Wait > 60 seconds
- Try to trade
- **Expected:** Price refresh required

---

## 🔍 Verification Checklist

After each transaction, verify:

### Database Check
```python
# In Django shell
from users.models import Profile
from trading.models import Order

profile = Profile.objects.get(telegram_id="YOUR_TEST_USER_ID")

# Check balances
print(f"Rial: {profile.rial_balance:,}")
print(f"Gold: {profile.gold_balance_grams}")
print(f"Coin: {profile.coin_balance}")
print(f"Dollar: {profile.dollar_balance}")

# Check last order
last_order = Order.objects.filter(profile=profile).order_by('-created_at').first()
print(f"Order #{last_order.id}: {last_order.get_order_type_display()}")
print(f"Status: {last_order.get_status_display()}")
print(f"Amount: {last_order.total_amount:,} Rial")
```

### User Experience Check
- ✅ Messages are clear and in Persian
- ✅ Numbers formatted with commas
- ✅ Emojis display correctly
- ✅ Invoice is readable and organized
- ✅ Error messages are helpful
- ✅ Balance updates shown immediately

---

## 🚨 Common Issues & Solutions

### Issue 1: "موجودی کافی نیست" but user has balance
**Solution:**
- Check frozen balances: `profile.frozen_rial_balance`
- Check if profile is approved: `profile.is_approved`

### Issue 2: Order created but balance not updated
**Solution:**
- Check order status: Should be "COMPLETED"
- Look for errors in logs: `python manage.py runbot` output
- Verify `complete_order()` was called

### Issue 3: Wrong product balance updated
**Solution:**
- Verify product.product_code matches constants (PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR)
- Check Product table in admin

---

## 📊 Test Results Template

```
Test Date: _____________
Tester: _____________

| Scenario | Status | Notes |
|----------|--------|-------|
| Buy with sufficient balance | ✅/❌ | |
| Buy with insufficient balance | ✅/❌ | |
| Sell with sufficient product | ✅/❌ | |
| Sell with insufficient product | ✅/❌ | |
| Buy using Rial amount | ✅/❌ | |
| Coin transactions | ✅/❌ | |
| Dollar transactions | ✅/❌ | |
| Invoice display | ✅/❌ | |
| Error messages | ✅/❌ | |
| Balance updates | ✅/❌ | |

Overall Result: ✅/❌
```

---

## 🎓 Advanced Testing

### Concurrent Transactions
Test multiple users trading simultaneously:
```bash
# Terminal 1
python manage.py shell
# Execute trades for User A

# Terminal 2
python manage.py shell
# Execute trades for User B at same time
```

### Load Testing
```python
# Create multiple test orders rapidly
from trading.services import OrderService
from trading.models import Product
from users.models import Profile

profile = Profile.objects.first()
product = Product.objects.first()

for i in range(10):
    order = OrderService.create_order(
        profile=profile,
        product=product,
        order_type='BUY',
        quantity_grams=1,
        price_per_gram=product.sell_price,
        total_amount=product.sell_price
    )
    OrderService.complete_order(order, execute_immediately=True)
```

---

## ✅ Final Checklist

Before going live:
- [ ] All test scenarios pass
- [ ] Error messages are clear
- [ ] Balances update correctly
- [ ] Orders saved with COMPLETED status
- [ ] Invoice format is professional
- [ ] Multi-product support works
- [ ] Persian text displays correctly
- [ ] No console errors
- [ ] Database transactions are atomic
- [ ] Concurrent transactions work
- [ ] Admin can view orders

---

## 📞 Support

If you encounter issues:
1. Check bot logs: `python manage.py runbot`
2. Check Django admin: `/admin/trading/order/`
3. Verify database directly
4. Test with fresh user profile

---

**Happy Testing! 🚀**

