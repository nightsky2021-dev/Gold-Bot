
Based on my review, here's a **complete Product Requirements Document (PRD)** for implementing the Standard E-Commerce Structure (Option A):

---

# 📋 Product Requirements Document: Bot Menu Reorganization
## Option A: Standard E-Commerce Structure

### 🎯 Executive Summary

**Objective:** Reorganize the Telegram bot's main menu from 5 buttons to 4 buttons, eliminating redundancy and enhancing user experience with a standard e-commerce structure.

**Timeline:** 3 development phases (Quick Win → Core Enhancement → Advanced Features)

**Impact:** 
- Reduce button count from 5 to 4 (20% reduction)
- Eliminate 80% functionality overlap between Portfolio and Wallet
- Enable deposit/withdraw functionality (currently unused despite models existing)
- Improve user task completion rate

---

## 📐 Current vs. Target State

### Current Structure (5 Buttons)
```
Row 1: 📈 قیمت‌ها
Row 2: 💳 کیف پول | 🏦 حساب‌های بانکی
Row 3: 📊 پورتفولیو | 📜 تاریخچه
```

### Target Structure (4 Buttons)
```
Row 1: 📈 قیمت‌ها
Row 2: 💼 کیف پول
Row 3: 📋 تاریخچه | ⚙️ تنظیمات
```

---

## 🎨 Detailed Button Specifications

### **Button 1: 📈 قیمت‌ها (Prices & Trade)**

**Status:** NO CHANGES REQUIRED ✅ only change the name to قیمتها و معامله

**Current Functionality:**
- Display inline menu with product options (Gold, Coin, Dollar)
- Show individual product prices with buy/sell buttons
- Automatic price expiration after 60 seconds
- Direct transition to buy/sell conversation flow

**Keep as is:** This button is well-implemented and follows best practices.

---

### **Button 2: 💼 کیف پول (Wallet) - ENHANCE**

**Current State:**
- Only displays balance information (read-only)
- Shows: Rial, Gold, Coin, Dollar balances
- Shows: Available vs. Frozen balances
- No interaction capability

**Target State:**
- Interactive wallet hub with action buttons
- Full transaction management

**Required Features:**

#### 2.1 Enhanced Balance Display
- Display current balances (all 4 currencies)
- Show available vs. frozen amounts
- Display last update timestamp
- Add total portfolio value estimation (optional Phase 3)

#### 2.2 Inline Action Buttons
Add inline keyboard with three action buttons:

**📥 واریز (Deposit)**
- Opens deposit workflow
- Currency selection (Rial, Gold, Coin, Dollar)
- Amount input
- Bank account selection (from user's registered accounts)
- Receipt upload for Rial deposits
- Generates pending transaction record
- Admin notification for approval

**📤 برداشت (Withdraw)**
- Opens withdrawal workflow
- Currency selection (only from available balance)
- Amount validation (check sufficient balance)
- Bank account selection (verified accounts only)
- Confirmation step with details
- Generates WithdrawRequest record
- Admin notification for processing

**📊 تراکنش‌ها (Transaction History)**
- Display last 20 transactions
- Show: Type, Currency, Amount, Status, Date
- Filter options: All / Pending / Completed / Cancelled
- Pagination support (10 per page)
- Transaction detail view on selection

**Technical Notes:**
- Use existing `Transaction` model in `trading/models.py`
- Use existing `WithdrawRequest` model in `trading/models.py`
- Leverage `WalletService` in `users/wallet_services.py`
- Conversation states already defined in `bot/constants.py` (DEPOSIT_*, WITHDRAW_*)

---

### **Button 3: 📋 تاریخچه (History) - ENHANCE**

**Current State:**
- Shows only last 5 orders
- No filtering or pagination
- Order-only (no transaction history)

**Target State:**
- Comprehensive history viewer with tabs

**Required Features:**

#### 3.1 Enhanced Order History
- Display last 10-20 orders (increase from 5)
- Show order details:
  - Order ID
  - Product name
  - Buy/Sell indicator
  - Quantity
  - Total amount
  - Status (Pending/Completed/Cancelled)
  - Creation date
- Pagination support (10 per page)
- Order detail view with full invoice

#### 3.2 Filter Options (Inline Buttons)
Add inline keyboard:
- **🛒 سفارشات** (Orders) - Current functionality
- **💳 تراکنش‌ها** (Transactions) - Links to wallet transaction history

**Note:** Transaction history will be accessed via Wallet button primarily, this is a secondary access point for user convenience.

---

### **Button 4: ⚙️ تنظیمات (Settings) - NEW**

**Purpose:** Consolidate user profile, account management, and statistics

**Required Features:**

#### 4.1 Profile Section (👤 پروفایل من)
Display user information:
- Full name
- Phone number
- Telegram username
- Registration date
- Verification status
- National code (if available)

**Actions:**
- View only (no editing)
- Display formatted in Persian

#### 4.2 Bank Account Management (🏦 حساب‌های بانکی)

**Functionality:**

**📋 List Bank Accounts:**
- Display all registered bank accounts
- Show: Bank name, Account holder, Account number (masked), Verification status
- Verified accounts marked with ✅
- Pending accounts marked with ⏳
- Empty state message if no accounts

**➕ Add Bank Account:**
- Conversation flow to add new account
- Fields required:
  1. Bank name (select from predefined list - `IRANIAN_BANKS` in constants)
  2. Account holder name
  3. Account number (16 digits)
  4. Account type (savings/current)
- Validation on all fields
- Auto-generates verification request
- Notifies admin for verification

**🗑️ Remove Bank Account:**
- Select from list
- Confirmation dialog
- Only allow removal of unverified accounts
- Block removal if account has pending transactions

**Technical Notes:**
- Use existing `BankAccount` model in `users/models.py`
- Conversation states already defined: `ACCOUNT_ADD_BANK`, etc.

#### 4.3 Statistics Dashboard (📊 آمار من)
Consolidate information from old Portfolio button:

**Display Metrics:**
- Total orders count
- Completed orders
- Pending orders
- Cancelled orders
- Total trade volume (in Rial)
- Favorite product (most traded)
- Member since date
- Account status

**Layout:** Single formatted message with all statistics

---

## 🗑️ Buttons to Remove

### **Portfolio Button - REMOVE**
**Reason:** 80% redundancy with Wallet and Settings

**Migration Plan:**
- Balance information → Already in Wallet ✅
- User information → Move to Settings > Profile ✅
- Order statistics → Move to Settings > Statistics ✅
- Account status → Move to Settings > Profile ✅

### **Bank Accounts Button - REMOVE**
**Reason:** Low usage frequency, better as submenu

**Migration Plan:**
- Bank account list → Move to Settings > Bank Accounts ✅
- Add/Edit functionality → Implement in Settings ✅

---

## 📝 User Stories & Acceptance Criteria

### Epic 1: Wallet Enhancement

**User Story 1.1: Deposit Money**
```
As a user
I want to deposit money into my wallet
So that I can buy gold/coin/dollar

Acceptance Criteria:
✓ User can select currency type (Rial/Gold/Coin/Dollar)
✓ User can enter amount with validation
✓ User can select destination bank account
✓ User can upload payment receipt (for Rial)
✓ System creates pending transaction record
✓ User receives confirmation message with transaction number
✓ Admin receives notification for approval
✓ User can view transaction in history
```

**User Story 1.2: Withdraw Money**
```
As a user
I want to withdraw money from my wallet
So that I can receive cash/assets

Acceptance Criteria:
✓ User can only withdraw from available balance
✓ System validates sufficient balance before proceeding
✓ User can select verified bank account only
✓ System shows withdrawal details for confirmation
✓ System creates WithdrawRequest record
✓ Balance is frozen until admin processes
✓ User receives confirmation with request number
✓ Admin receives notification
```

**User Story 1.3: View Transaction History**
```
As a user
I want to view my transaction history
So that I can track my financial activities

Acceptance Criteria:
✓ User sees last 20 transactions
✓ Each transaction shows: type, currency, amount, status, date
✓ User can filter by status
✓ User can paginate through history
✓ User can tap transaction for details
```

### Epic 2: Settings Menu

**User Story 2.1: View Profile**
```
As a user
I want to view my profile information
So that I can verify my details

Acceptance Criteria:
✓ User sees complete profile information
✓ All fields displayed in Persian
✓ Dates formatted correctly (Jalali calendar)
✓ Verification status clearly indicated
```

**User Story 2.2: Manage Bank Accounts**
```
As a user
I want to add and manage my bank accounts
So that I can deposit and withdraw funds

Acceptance Criteria:
✓ User can view list of registered accounts
✓ User can add new bank account through guided flow
✓ System validates all account details
✓ User can remove unverified accounts
✓ System prevents removal of accounts with pending transactions
✓ User sees verification status for each account
```

**User Story 2.3: View Statistics**
```
As a user
I want to view my trading statistics
So that I can track my activity

Acceptance Criteria:
✓ User sees total order count by status
✓ User sees total trade volume
✓ User sees favorite product
✓ User sees membership duration
✓ All numbers formatted properly in Persian
```

### Epic 3: History Enhancement

**User Story 3.1: Enhanced Order History**
```
As a user
I want to see more orders in my history
So that I can review past transactions

Acceptance Criteria:
✓ User sees last 10-20 orders (increased from 5)
✓ Orders displayed with complete information
✓ User can paginate through history
✓ User can tap order for full invoice details
```

---

## 🔧 Technical Implementation Guidelines

### Phase 1: Quick Wins 
**Goal:** Restructure menu, remove redundancy

**Tasks:**
1. Update `bot/keyboards.py`:
   - Modify `get_main_menu_keyboard()` function
   - Change from 5 buttons to 4 buttons layout
   - Update button constants if needed

2. Remove handlers in `bot/management/commands/runbot.py`:
   - Remove or comment out Portfolio button handler
   - Remove or comment out Bank Accounts button handler

3. Add Settings button handler:
   - Create `show_settings()` function
   - Display inline keyboard with 3 options (Profile, Bank Accounts, Statistics)
   - Implement basic display for each submenu

4. Update `bot/constants.py`:
   - Add new menu button constant: `MENU_SETTINGS`
   - Add callback constants for settings submenus

**Testing Checklist:**
- [ ] Menu displays with 4 buttons correctly
- [ ] Each button responds when clicked
- [ ] Settings submenu appears with 3 options
- [ ] Profile display shows user information
- [ ] Bank accounts display shows list
- [ ] Statistics display shows consolidated info from old Portfolio

---

### Phase 2: Wallet Enhancement 
**Goal:** Make wallet interactive

**Tasks:**

#### 2.1 Update Wallet Display
1. Modify `show_wallet()` function in `runbot.py`
2. Add inline keyboard with 3 action buttons (Deposit, Withdraw, Transactions)
3. Keep existing balance display from `WalletService.format_wallet_display()`

#### 2.2 Implement Transaction History Viewer
1. Create callback handler: `show_wallet_transactions()`
2. Query last 20 transactions from database
3. Format display with pagination support
4. Add filter buttons (All, Pending, Completed, Cancelled)
5. Implement transaction detail view

#### 2.3 Implement Deposit Workflow
1. Create conversation handler for deposit
2. Use existing states: `DEPOSIT_SELECT_CURRENCY`, `DEPOSIT_ENTER_AMOUNT`, etc.
3. Implement handlers:
   - `deposit_select_currency()` - Show currency options
   - `deposit_enter_amount()` - Validate amount input
   - `deposit_select_bank()` - Show user's bank accounts
   - `deposit_upload_receipt()` - Handle photo upload (Rial only)
   - `deposit_confirm()` - Create Transaction record
4. Generate transaction number
5. Send admin notification

#### 2.4 Implement Withdrawal Workflow
1. Create conversation handler for withdrawal
2. Use existing states: `WITHDRAW_SELECT_CURRENCY`, `WITHDRAW_ENTER_AMOUNT`, etc.
3. Implement handlers:
   - `withdraw_select_currency()` - Show available currencies
   - `withdraw_enter_amount()` - Validate against available balance
   - `withdraw_select_bank()` - Show verified bank accounts only
   - `withdraw_confirm()` - Create WithdrawRequest record
4. Freeze balance using `WalletService.freeze_balance()`
5. Generate request number
6. Send admin notification

**Integration Points:**
- Use `WalletService` for all balance operations
- Use `Transaction` model for deposit tracking
- Use `WithdrawRequest` model for withdrawal tracking
- Reference `BankAccount` model for account selection

**Testing Checklist:**
- [ ] Wallet displays with 3 action buttons
- [ ] Transaction history loads and displays correctly
- [ ] Pagination works in transaction history
- [ ] Deposit workflow completes successfully
- [ ] Transaction record created correctly
- [ ] Withdrawal workflow validates balance
- [ ] WithdrawRequest record created correctly
- [ ] Balance frozen after withdrawal request
- [ ] Admin notifications sent
- [ ] Error handling works for invalid inputs

---

### Phase 3: Bank Account Management 
**Goal:** Enable users to manage bank accounts

**Tasks:**

#### 3.1 Display Bank Accounts
1. Implement `show_bank_accounts()` function
2. Query user's bank accounts from database
3. Format list with status indicators
4. Add action buttons: Add Account, Remove Account

#### 3.2 Add Bank Account Workflow
1. Create conversation handler
2. Use state: `ACCOUNT_ADD_BANK`
3. Implement handlers:
   - `account_add_bank_select_bank()` - Show bank list from `IRANIAN_BANKS`
   - `account_add_bank_holder_name()` - Get account holder name
   - `account_add_bank_number()` - Validate 16-digit account number
   - `account_add_bank_type()` - Select savings/current
   - `account_add_bank_confirm()` - Create BankAccount record
4. Set `is_verified=False` by default
5. Notify admin for verification

#### 3.3 Remove Bank Account
1. Implement `remove_bank_account()` callback handler
2. Show confirmation dialog
3. Validate no pending transactions
4. Delete record if allowed
5. Show error if not allowed (pending transactions exist)

**Integration Points:**
- Use `BankAccount` model in `users/models.py`
- Check against `Transaction` and `WithdrawRequest` before deletion
- Use `IRANIAN_BANKS` constant for bank selection

**Testing Checklist:**
- [ ] Bank account list displays correctly
- [ ] Add account workflow completes successfully
- [ ] BankAccount record created with correct data
- [ ] Validation works for account number format
- [ ] Remove account works for unverified accounts
- [ ] Remove blocked for accounts with pending transactions
- [ ] Admin notification sent for new accounts

---

### Phase 4: History Enhancement 
**Goal:** Improve order history display

**Tasks:**
1. Modify `show_history()` function in `runbot.py`
2. Increase limit from 5 to 10 orders
3. Add pagination support (optional)
4. Add inline keyboard with filter options (optional)
5. Improve order detail formatting

**Testing Checklist:**
- [ ] History shows 10 orders instead of 5
- [ ] Order information displayed clearly
- [ ] Pagination works if implemented

---

## 🎨 UI/UX Specifications

### Design Principles
1. **Consistency:** Use same emoji style across all buttons
2. **Clarity:** Clear labeling in Persian
3. **Feedback:** Immediate response to all user actions
4. **Error Handling:** Friendly error messages in Persian
5. **Confirmation:** Require confirmation for financial actions

### Message Formatting Standards
- Use Markdown for emphasis
- Format numbers with Persian separators: `{number:,.0f}`
- Use consistent emoji indicators:
  - ✅ Success/Verified
  - ⏳ Pending
  - ❌ Failed/Cancelled
  - 💰 Money/Rial
  - 🪙 Gold
  - 🥇 Coin
  - 💵 Dollar
  - 📥 Deposit
  - 📤 Withdraw

### Timeout Handling
- Financial conversations: 5 minutes max
- After timeout: Clear user_data and return to main menu
- Show friendly timeout message

---

## 🔒 Security & Validation

### Input Validation
1. **Amount Fields:**
   - Must be positive numbers
   - Must be within min/max limits
   - Decimal validation based on currency type

2. **Bank Account Number:**
   - Must be exactly 16 digits
   - Must be numeric only
   - No special characters

3. **Balance Checks:**
   - Always validate sufficient balance before proceeding
   - Check available balance (not frozen)
   - Prevent negative balances

### Transaction Safety
1. Use `@transaction.atomic` for all financial operations
2. Freeze balance before processing withdrawals
3. Log all balance changes
4. Generate unique transaction/request numbers
5. Admin approval required for deposits and withdrawals

---

## 📊 Success Metrics

### Primary KPIs
- **Menu Clarity:** Button count reduced from 5 to 4 ✓
- **Feature Utilization:** Deposit/Withdraw features available ✓
- **Redundancy:** Eliminated 80% overlap between Portfolio/Wallet ✓

### Secondary KPIs (Track after launch)
- Wallet interaction rate (target: 30% of users)
- Deposit request completion rate (target: >80%)
- Bank account addition rate (target: 50% of active users)
- Settings menu utilization (target: >20%)
- Support tickets reduction (target: 15% decrease)

---

## 📅 Implementation Timeline

### Week 1
- Phase 1: Menu restructuring (Days 1-2)
- Phase 2: Wallet enhancement start (Days 3-5)

### Week 2
- Phase 2: Complete wallet features (Days 1-3)
- Phase 3: Bank account management (Days 4-5)

### Week 3
- Phase 4: History enhancement (Day 1)
- Testing and bug fixes (Days 2-4)
- Documentation update (Day 5)

**Total Estimate:** 15 working days (3 weeks)

---

## 🧪 Testing Requirements

### Unit Tests Required
- `WalletService` methods
- Balance validation functions
- Transaction number generation
- Amount parsing and validation

### Integration Tests Required
- Deposit workflow end-to-end
- Withdrawal workflow end-to-end
- Bank account addition flow
- Transaction history retrieval

### Manual Testing Checklist
- [ ] All 4 main menu buttons work
- [ ] Prices button unchanged and working
- [ ] Wallet shows inline actions
- [ ] Deposit completes successfully
- [ ] Withdrawal validates balance
- [ ] Transaction history displays
- [ ] Settings shows all 3 submenus
- [ ] Profile displays correctly
- [ ] Bank accounts can be added
- [ ] Bank accounts can be removed
- [ ] Statistics show correct data
- [ ] History shows 10 orders
- [ ] All error messages in Persian
- [ ] All timeout handling works
- [ ] Admin notifications sent
- [ ] Database records created correctly

---

## 📚 Documentation Updates Required

### User Documentation
- Update bot usage guide with new menu structure
- Create deposit tutorial
- Create withdrawal tutorial
- Update bank account management guide

### Developer Documentation
- Update `ARCHITECTURE.md` with new structure
- Document new conversation handlers
- Update `PROJECT_STRUCTURE.md`
- Add inline comments to new functions

### Admin Documentation
- Update admin panel guide for deposit approvals
- Update withdrawal processing guide
- Document bank account verification process

---

## 🚀 Deployment Plan

### Pre-Deployment
1. Complete all phases
2. Pass all tests
3. Update documentation
4. Backup database
5. Test on staging bot

### Deployment Steps
1. Stop current bot process
2. Pull latest code
3. Run database migrations (if any)
4. Update requirements.txt dependencies (if any)
5. Restart bot process
6. Monitor logs for errors
7. Test all buttons in production

### Rollback Plan
1. Stop bot process
2. Revert to previous code version
3. Restore database if needed
4. Restart bot
5. Verify functionality

---

## ⚠️ Risks & Mitigation

### Risk 1: User Confusion
**Mitigation:** 
- Send broadcast message announcing changes
- Provide clear labels on all buttons
- Add help text in Settings

### Risk 2: Transaction Errors
**Mitigation:**
- Extensive testing before deployment
- Use database transactions (atomic)
- Add comprehensive error logging
- Admin approval layer for all financial operations

### Risk 3: Performance Issues
**Mitigation:**
- Optimize database queries
- Add pagination to long lists
- Cache frequently accessed data
- Monitor bot response times

---

## 💡 Future Enhancements (Post-Launch)

### Phase 5 (Optional)
- Portfolio value tracker (total worth in Rial)
- Price alerts/notifications
- Recurring deposits
- Export transaction history (PDF/Excel)
- Multi-language support
- Dark mode for messages
- Transaction search functionality

---

## ✅ Definition of Done

A feature is considered complete when:
- ✓ Code implemented and follows project standards
- ✓ All acceptance criteria met
- ✓ Unit tests written and passing
- ✓ Integration tests passing
- ✓ Error handling implemented
- ✓ Persian translations correct
- ✓ Admin panel integration complete (if applicable)
- ✓ Documentation updated
- ✓ Code reviewed and approved
- ✓ Tested on staging environment
- ✓ No critical bugs remaining

---

## 📞 Stakeholder Sign-Off

This PRD requires approval from:
- [ ] Product Owner
- [ ] Technical Lead
- [ ] UX Designer
- [ ] QA Lead

---

**Document Version:** 1.0  
**Last Updated:** 2024-11-02  
**Status:** Ready for Development  
**Priority:** High