# Trading UX Testing Guide

## Quick Start Testing

### Prerequisites
1. Bot is running and connected to Telegram
2. Test user account is approved
3. Test user has sufficient Rial balance for buying
4. Test user has products to sell

### Test Scenario 1: Buy Flow (Happy Path)

**Steps**:
1. Start bot: `/start`
2. Click main menu button: "🛒 خرید"
3. **Observe**: Product list appears with prices
4. Click any product (e.g., "طلا (5,000,000 ریال/گرم)")
5. **Expected**: Same message is edited to show method selection
6. Click "گرم" (Grams)
7. **Expected**: Same message is edited to show:
   - "Enter amount prompt" (directly, no confirmation message)
   - Cancel button
8. Type: `10` (10 grams)
9. **Expected**: 
   - Your message is deleted
   - Bot message is edited to show invoice
10. Click "✅ تایید" (Confirm)
11. **Expected**: Same message is edited to show success

**Success Criteria**:
- ✅ Only ONE bot message visible throughout entire flow
- ✅ Your input message is deleted after processing
- ✅ Each step replaces the previous message
- ✅ No extra confirmation messages (goes directly from method to amount prompt)

### Test Scenario 2: Sell Flow (Happy Path)

**Steps**:
1. Click: "💰 فروش" (Sell)
2. Click product you own
3. **Expected**: Message edited to method selection
4. Click "ریال" (Rial)
5. **Expected**: Message edited showing:
   - "Enter rial amount" (directly, no confirmation)
   - Your current balance
   - Cancel button
6. Type valid amount: `1000000`
7. **Expected**: Your message deleted, invoice shown
8. Click confirm
9. **Expected**: Success message replaces invoice

**Success Criteria**:
- ✅ Balance displayed correctly
- ✅ Messages replaced at each step
- ✅ User input cleaned up

### Test Scenario 3: Error Handling - Invalid Amount

**Steps**:
1. Start buy flow
2. Select product → Select method (grams)
3. Type: `abc` (invalid)
4. **Expected**:
   - Your "abc" message is deleted
   - Bot message edited to show:
     - "❌ مقدار نامعتبر..."
     - "💡 لطفاً مقدار صحیح وارد کنید"
     - Cancel button still present
5. Type: `10` (valid)
6. **Expected**: Flow continues normally

**Success Criteria**:
- ✅ Error shown in SAME message (not new)
- ✅ Invalid input deleted
- ✅ Can continue after error
- ✅ Cancel button remains functional

### Test Scenario 4: Error Handling - Insufficient Balance

**Steps**:
1. Start buy flow
2. Select product → Select "ریال"
3. Check your balance (e.g., 10,000,000 ریال)
4. Type amount > your balance: `99999999999`
5. **Expected**:
   - Your message deleted
   - Bot message edited to show:
     - "❌ موجودی ناکافی..."
     - Details about balance
   - Conversation ends

**Success Criteria**:
- ✅ Error shown in edited message
- ✅ Clear error message about balance
- ✅ Conversation ends gracefully
- ✅ No invoice shown

### Test Scenario 5: Main Menu Button During Amount Entry

**Steps**:
1. Start buy flow
2. Select product → Select method
3. Instead of typing amount, click main menu button (e.g., "💼 کیف پول")
4. **Expected**:
   - Bot message edited to show:
     - "⚠️ لطفاً عدد وارد کنید"
     - Reminder to type number
   - Your menu button press might be deleted (if permission available)
5. Type: `10` (valid amount)
6. **Expected**: Flow continues normally

**Success Criteria**:
- ✅ Helpful error without ending conversation
- ✅ Message edited (not new message)
- ✅ Can continue after mistake
- ✅ User is not confused

### Test Scenario 6: Cancel Operations

Test canceling at each step:

**Test 6a: Cancel at product selection**
1. Click "🛒 خرید"
2. Click "❌ لغو" at bottom
3. **Expected**: "❌ عملیات لغو شد"

**Test 6b: Cancel at method selection**
1. Select product
2. Click "❌ لغو" 
3. **Expected**: "❌ عملیات لغو شد"

**Test 6c: Cancel at amount entry**
1. Select product → method
2. Click "❌ لغو عملیات"
3. **Expected**: "❌ عملیات لغو شد"

**Test 6d: Cancel at confirmation**
1. Complete through invoice
2. Click "❌ لغو"
3. **Expected**: "❌ عملیات لغو شد"

**Success Criteria for All Cancel Tests**:
- ✅ Message edited (not new)
- ✅ Context cleared
- ✅ Can start new trade immediately

### Test Scenario 7: Coin/Dollar (Count-based)

**Steps**:
1. Start buy flow
2. Select "سکه" (Coin) or "دلار" (Dollar)
3. **Expected**: Method options show:
   - "تعداد" (Count)
   - "ریال" (Rial)
4. Click "تعداد"
5. Type: `5` (5 coins/dollars)
6. **Expected**: Invoice shows quantity as count (not grams)
7. Confirm
8. **Expected**: Success shows correct units

**Success Criteria**:
- ✅ Count method available for coins/dollars
- ✅ Count method NOT available for gold
- ✅ Invoice shows correct units
- ✅ Balance updated correctly

### Test Scenario 8: Rapid Clicking

**Steps**:
1. Start buy flow
2. Quickly click same product multiple times
3. **Expected**: Should handle gracefully
4. Continue normally through flow
5. **Expected**: Only one trade executed

**Success Criteria**:
- ✅ No duplicate trades
- ✅ No error messages
- ✅ Conversation state consistent

### Test Scenario 9: Concurrent Trades

**Steps**:
1. Open bot in two different devices/sessions
2. Start buy flow in both
3. Complete trade in first session
4. Try to complete trade in second session
5. **Expected**: Balance check should catch if insufficient

**Success Criteria**:
- ✅ Each session independent
- ✅ Balance validated at execution time
- ✅ No race conditions

### Test Scenario 10: Old Message Editing

**Steps**:
1. Start buy flow
2. Wait 48+ hours (or change system time for testing)
3. Try to click buttons
4. **Expected**: May fall back to reply (Telegram limitation)

**Success Criteria**:
- ✅ Falls back to reply gracefully
- ✅ No errors shown to user
- ✅ Functionality still works

## Edge Cases

### Edge Case 1: Bot Restarted Mid-Trade
1. Start trade
2. Restart bot
3. Try to continue
4. **Expected**: May need to start over

### Edge Case 2: Network Issues
1. Start trade
2. Simulate network interruption
3. **Expected**: Error logged, fallback to reply

### Edge Case 3: Permission Issues
1. Test in group chat (if applicable)
2. Bot without delete message permission
3. **Expected**: Still works, just doesn't delete user messages

## Performance Testing

### Load Test
- Have 10+ users start trades simultaneously
- **Expected**: All handle correctly, no timeouts

### Speed Test
- Measure time from "🛒 خرید" to success
- **Target**: < 30 seconds for normal flow

## Visual Inspection

Look for these UI improvements:

✅ **Good Signs**:
- Only one message at bottom of chat
- Smooth transitions (message content changes)
- Clean chat history
- Professional appearance
- Buttons remain clickable
- Emoji indicators clear

❌ **Bad Signs**:
- Multiple messages stacking up
- "Method selected" message separate from "Enter amount"
- User input messages remaining after processing
- Multiple confirmation messages

## Comparison Testing

### Before (for reference)
- Take screenshot of old flow
- Count messages
- Note user confusion points

### After
- Take screenshot of new flow
- Count messages (should be fewer)
- Note improvements

## Bug Tracking

If you find issues, document:
1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Screenshots**
5. **Error logs** (check `logs/gold_shop.log`)

## Log Inspection

Check logs for:
```bash
# Success pattern
INFO:bot.trading.shared:Method selected: grams
INFO:bot.trading.shared:Amount entered: 10
INFO:bot.trading.confirmation:Order created successfully

# Error pattern
ERROR:bot.trading.shared:Error editing message: ...
ERROR:bot.trading.shared:Error processing amount: ...
```

## Success Metrics

After testing, verify:
- ✅ Messages per trade: ~1-2 (vs 5-6 before)
- ✅ No stacked messages in chat
- ✅ User input cleaned up
- ✅ All error cases handled
- ✅ Cancel works at all steps
- ✅ Fallback works when editing fails

## Final Checklist

Before deploying to production:

- [ ] All test scenarios pass
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Edge cases handled
- [ ] Fallbacks work
- [ ] Visual appearance good
- [ ] User feedback positive
- [ ] Staging environment tested
- [ ] Database integrity verified
- [ ] Rollback plan ready

## Rollback Instructions

If issues found:
1. Stop bot: `systemctl stop goldbot` (or your command)
2. Git revert changes:
   ```bash
   git log --oneline  # Find commit hash
   git revert <commit-hash>
   ```
3. Restart bot
4. Verify old behavior restored

## Support

If you encounter issues:
1. Check `logs/gold_shop.log`
2. Search for error messages
3. Check Telegram Bot API status
4. Verify bot permissions
5. Test with different user accounts

---

**Testing Duration**: ~30 minutes for full test suite  
**Priority**: High (UX improvement)  
**Risk Level**: Low (has fallbacks)  
**Recommended**: Test in staging before production

