# Testing Guide: Trading Menu Feature

## Quick Start

### Running the Bot

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run the bot
python manage.py runbot
```

## Test Scenarios

### Scenario 1: Basic Product Selection ✅

**Steps:**
1. Start bot: `/start`
2. Click "📈 قیمتها و معامله" button
3. **Expected:** See product selection menu with:
   - 🪙 طلای آبشده (Gold)
   - 🥇 سکه تمام (Coin)
   - 💵 دلار (Dollar)
   - 📊 مشاهده همه قیمت‌ها (View All)

### Scenario 2: View Individual Product Price ✅

**Steps:**
1. From product menu, click "🪙 طلای آبشده"
2. **Expected:** See:
   - Product name
   - Buy price (you sell to us)
   - Sell price (you buy from us)
   - Timestamp of last update
   - Warning: "Valid for 1 minute"
   - Buttons: 🟢 Buy, 🔴 Sell, 🔄 Refresh, 🔙 Back

### Scenario 3: View All Products ✅

**Steps:**
1. From product menu, click "📊 مشاهده همه قیمت‌ها"
2. **Expected:** See:
   - All products listed with prices
   - Last update timestamp
   - Back button

### Scenario 4: Buy Within Timer (Success) ✅

**Steps:**
1. View product price (fresh)
2. **Immediately** click "🟢 خرید"
3. **Expected:**
   - Proceeds to calculation method selection
   - Shows: "بر اساس مقدار" and "بر اساس مبلغ"
4. Select method and continue with trade

### Scenario 5: Timer Expiration (After 1 Minute) ⏱️

**Steps:**
1. View product price
2. **Wait 61+ seconds**
3. Click "🟢 خرید" or "🔴 فروش"
4. **Expected:**
   - Message: "⚠️ قیمت منقضی شده است!"
   - "قیمت‌ها بیش از 1 دقیقه قدیمی هستند"
   - "لطفاً قیمت را بروزرسانی کنید"
   - Only refresh button available

### Scenario 6: Refresh Price ✅

**Steps:**
1. After price expires OR anytime
2. Click "🔄 بروزرسانی قیمت"
3. **Expected:**
   - Toast: "🔄 در حال بروزرسانی قیمت..."
   - Fresh prices displayed
   - New timestamp shown
   - Timer reset (can trade again)

### Scenario 7: Back Navigation ✅

**Steps:**
1. View product detail
2. Click "🔙 بازگشت"
3. **Expected:**
   - Returns to product selection menu
   - Can select different product

### Scenario 8: Complete Buy Flow ✅

**Steps:**
1. Click "📈 قیمتها و معامله"
2. Select product (e.g., Gold)
3. Click "🟢 خرید" (within 60 seconds)
4. Select calculation method (e.g., "بر اساس مقدار")
5. Enter amount (e.g., "2.5")
6. Review preview
7. Click "✨ تایید و ثبت سفارش ✨"
8. **Expected:** Order created successfully

### Scenario 9: Complete Sell Flow ✅

**Steps:**
1. Click "📈 قیمتها و معامله"
2. Select product (e.g., Gold)
3. Click "🔴 فروش" (within 60 seconds)
4. Select calculation method
5. Enter amount
6. Review preview
7. Confirm
8. **Expected:** Order created successfully

### Scenario 10: Cancel at Any Stage ✅

**Steps:**
1. Start any flow
2. Click cancel/back button at various stages
3. **Expected:**
   - Graceful exit
   - Message: "❌ سفارش لغو شد"
   - Returns to main menu

## Timer Behavior Tests

### Test 1: Exact Timing
- View price at time T
- Try to trade at:
  - T+30s → Should work ✅
  - T+59s → Should work ✅
  - T+61s → Should be expired ⏱️

### Test 2: Multiple Products
- View Gold price at T=0
- View Coin price at T=30
- At T=70:
  - Gold should be expired (70s old)
  - Coin should work (40s old)

### Test 3: Refresh Reset
- View price at T=0
- Wait 55 seconds
- Refresh at T=55
- Timer should reset → can trade for another 60s

## Error Cases to Test

### Case 1: User Not Approved
- Try accessing without admin approval
- **Expected:** "حساب شما هنوز تأیید نشده است"

### Case 2: No Active Products
- Deactivate all products in admin
- Try to view prices
- **Expected:** "متأسفانه در حال حاضر محصولی برای معامله موجود نیست"

### Case 3: Invalid Amount
- Enter negative number
- Enter non-numeric value
- Enter zero
- **Expected:** Validation error messages

### Case 4: Insufficient Balance (Sell)
- Try to sell more gold than balance
- **Expected:** Insufficient balance error

## Performance Tests

### Load Test 1: Rapid Clicking
- Quickly click through menus
- **Expected:** No crashes, smooth operation

### Load Test 2: Multiple Users
- Have multiple users access prices simultaneously
- **Expected:** Each user has independent timer

### Load Test 3: Long Session
- Keep bot session open for extended period
- Test timer accuracy over time
- **Expected:** Timer remains accurate

## UI/UX Checks

### Check 1: Button Labels
- ✅ All Persian text displays correctly
- ✅ Emojis render properly
- ✅ Button alignment is clean

### Check 2: Message Formatting
- ✅ Bold text works (`*text*`)
- ✅ Numbers formatted with commas
- ✅ Timestamps readable

### Check 3: Button States
- ✅ Active buttons are green/red
- ✅ Expired state shows only refresh
- ✅ All buttons clickable

### Check 4: Flow Consistency
- ✅ Back button always returns to previous screen
- ✅ Cancel always exits to main menu
- ✅ Confirmations require explicit action

## Integration Tests

### Test 1: Legacy Menu Compatibility
- Old "💰 خرید طلا" button still works
- Old "🛒 فروش طلا" button still works
- Both paths lead to same trade flow

### Test 2: Wallet Integration
- After trade, check wallet updates
- Verify balances are correct
- Test with multiple currencies

### Test 3: History Integration
- Complete trades appear in history
- Timestamps are accurate
- Status updates correctly

## Admin Panel Checks

### Check 1: Order Creation
- Orders appear in admin panel
- All fields populated correctly
- Timestamps accurate

### Check 2: Price Updates
- Run `python manage.py update_prices`
- Verify prices update in bot
- Check updated_at timestamps

### Check 3: Product Management
- Create/edit/delete products
- Verify changes reflect immediately
- Test active/inactive toggle

## Debugging Tips

### Enable Debug Logging
```python
# In runbot.py, set level to DEBUG
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed from INFO
)
```

### Check Context Data
```python
# Add to handlers for debugging:
logger.debug(f"Context data: {context.user_data}")
```

### Monitor Timer Values
```python
# In handle_trade_action:
logger.info(f"Current time: {current_time}")
logger.info(f"Price time: {price_time}")
logger.info(f"Elapsed: {current_time - price_time}s")
```

## Common Issues & Solutions

### Issue 1: Timer Not Working
**Symptom:** Can trade even after 60 seconds  
**Solution:** Check context.user_data is being set correctly

### Issue 2: Prices Not Updating
**Symptom:** Old prices shown after refresh  
**Solution:** Run `python manage.py update_prices` or check DB

### Issue 3: Buttons Not Responding
**Symptom:** Clicking buttons does nothing  
**Solution:** Check callback patterns match constants.py

### Issue 4: Persian Text Garbled
**Symptom:** Text shows as ???  
**Solution:** Ensure UTF-8 encoding, check terminal settings

## Success Criteria

All tests pass when:
- ✅ Product menu displays correctly
- ✅ Individual product prices show with timer
- ✅ Timer expires after 60 seconds
- ✅ Refresh resets timer
- ✅ Buy/Sell work within timer
- ✅ Expired state blocks trading
- ✅ Navigation works smoothly
- ✅ Orders created successfully
- ✅ No crashes or errors
- ✅ Legacy features still work

## Test Log Template

```
Date: ___________
Tester: ___________

[ ] Scenario 1: Product Selection
[ ] Scenario 2: View Product
[ ] Scenario 3: View All
[ ] Scenario 4: Buy Within Timer
[ ] Scenario 5: Timer Expiration
[ ] Scenario 6: Refresh Price
[ ] Scenario 7: Back Navigation
[ ] Scenario 8: Complete Buy
[ ] Scenario 9: Complete Sell
[ ] Scenario 10: Cancel Flow

Issues Found:
1. ________________
2. ________________
3. ________________

Notes:
_____________________
_____________________
_____________________
```

## Next Steps After Testing

1. Document any bugs found
2. Create GitHub issues for problems
3. Update user documentation
4. Train support staff
5. Prepare deployment
6. Monitor production logs

---

**Happy Testing! 🚀**

