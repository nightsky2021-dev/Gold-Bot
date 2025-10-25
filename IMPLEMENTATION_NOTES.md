# 📝 Implementation Notes & Next Steps

## ✅ What Has Been Completed

### 1. Database Layer (100% Complete)
- ✅ Profile model updated with multi-currency support
- ✅ BankAccount model created with verification workflow
- ✅ Transaction model for comprehensive tracking
- ✅ WithdrawRequest model with approval workflow
- ✅ TransferRequest model for peer-to-peer transfers
- ✅ Database migrations created and ready to apply

### 2. Business Logic Layer (100% Complete)
- ✅ BankAccountService - Bank account management
- ✅ WalletService - Balance operations with freezing/unfreezing
- ✅ TransactionService - Transaction tracking and management
- ✅ DepositService - Deposit request handling
- ✅ WithdrawService - Withdrawal request handling with frozen balance
- ✅ TransferService - Peer-to-peer money transfers

### 3. Admin Interface (100% Complete)
- ✅ ProfileAdmin updated with wallet fields
- ✅ BankAccountAdmin with verification actions
- ✅ TransactionAdmin with completion actions
- ✅ WithdrawRequestAdmin with approve/reject actions
- ✅ TransferRequestAdmin for monitoring transfers

### 4. Bot Constants (100% Complete)
- ✅ All conversation states defined
- ✅ Callback data constants
- ✅ Currency types and bank lists
- ✅ Message templates
- ✅ Main menu updated

## ⏳ What Needs to Be Implemented

### 1. Bot Conversation Handlers (Priority: HIGH)

The template file `bot/wallet_handlers_template.py` provides a starting point. You need to:

#### Account Menu Handler
```python
# In runbot.py, add:
application.add_handler(
    MessageHandler(filters.Regex(f"^{MENU_ACCOUNT}$"), account_menu)
)
application.add_handler(
    CallbackQueryHandler(account_callback_handler, pattern="^account_")
)
```

Features to implement:
- ✅ View profile (template provided)
- ✅ View bank accounts (template provided)
- ✅ View balances (template provided)
- ✅ View transaction history (template provided)
- ⏳ Remove bank account (needs implementation)

#### Wallet Menu Handler
```python
# In runbot.py, add:
application.add_handler(
    MessageHandler(filters.Regex(f"^{MENU_WALLET}$"), wallet_menu)
)
application.add_handler(
    CallbackQueryHandler(wallet_callback_handler, pattern="^wallet_")
)
```

Features to implement:
- ✅ View balances (template provided)
- ✅ View transactions (template provided)
- ⏳ Complete deposit flow
- ⏳ Complete withdraw flow
- ⏳ Complete transfer flow

#### Deposit Conversation Handler
Template provided in `wallet_handlers_template.py`. Steps:
1. ✅ Select currency (implemented)
2. ✅ Enter amount (implemented)
3. ✅ Select bank account (implemented)
4. ⏳ Optional: Upload receipt image (needs implementation)
5. ✅ Confirm and create (implemented)

#### Withdraw Conversation Handler
Similar to deposit. Steps:
1. ⏳ Select currency
2. ⏳ Check available balance
3. ⏳ Enter amount
4. ⏳ Select destination bank account
5. ⏳ Confirm and freeze balance
6. ⏳ Create withdraw request

Code structure (similar to deposit):
```python
async def withdraw_start(update, context):
    # Show currency selection
    pass

async def withdraw_currency_selected(update, context):
    # Check balance and ask for amount
    pass

async def withdraw_amount_entered(update, context):
    # Validate balance, show bank accounts
    pass

async def withdraw_bank_selected(update, context):
    # Show confirmation
    pass

async def withdraw_confirm(update, context):
    # Create withdraw request, freeze balance
    pass
```

#### Transfer Conversation Handler
Steps:
1. ⏳ Select currency
2. ⏳ Enter receiver phone number
3. ⏳ Search and confirm receiver
4. ⏳ Enter amount
5. ⏳ Optional: Enter description
6. ⏳ Confirm and process transfer

Code structure:
```python
async def transfer_start(update, context):
    # Show currency selection
    pass

async def transfer_currency_selected(update, context):
    # Ask for receiver phone
    pass

async def transfer_receiver_entered(update, context):
    # Search receiver, show profile, ask for amount
    pass

async def transfer_amount_entered(update, context):
    # Check balance, ask for description
    pass

async def transfer_description_entered(update, context):
    # Show confirmation
    pass

async def transfer_confirm(update, context):
    # Process transfer
    pass
```

#### Add Bank Account Conversation Handler
Steps:
1. ⏳ Ask for bank name
2. ⏳ Validate against IRANIAN_BANKS list
3. ⏳ Ask for account number
4. ⏳ Validate format (16 digits or IBAN)
5. ⏳ Ask for account holder name
6. ⏳ Validate match with user's name
7. ⏳ Confirm and create

Code structure:
```python
async def add_bank_start(update, context):
    # Ask for bank name
    pass

async def bank_name_entered(update, context):
    # Validate, ask for account number
    pass

async def account_number_entered(update, context):
    # Validate, ask for holder name
    pass

async def holder_name_entered(update, context):
    # Validate, show confirmation
    pass

async def add_bank_confirm(update, context):
    # Create bank account
    pass
```

### 2. Notifications (Priority: MEDIUM)

#### User Notifications
Send Telegram messages when:
- ⏳ Bank account verified
- ⏳ Deposit approved/rejected
- ⏳ Withdraw approved/rejected
- ⏳ Transfer received
- ⏳ Order completed

Example implementation:
```python
async def notify_user(profile, message):
    """Send notification to user via Telegram."""
    bot = context.bot  # Get bot instance
    await bot.send_message(
        chat_id=profile.telegram_id,
        text=message,
        parse_mode='Markdown'
    )
```

Integrate in services:
```python
# In DepositService.approve_deposit():
await notify_user(txn.profile, MSG_DEPOSIT_APPROVED)

# In WithdrawService.approve_withdraw():
await notify_user(wd.profile, MSG_WITHDRAW_APPROVED)
```

#### Admin Notifications
Send notifications to admin Telegram channel when:
- ⏳ New bank account pending verification
- ⏳ New deposit request
- ⏳ New withdraw request

### 3. Additional Features (Priority: LOW)

#### Rate Limiting
Implement in services:
```python
def check_withdraw_limits(profile, amount, currency):
    """Check daily withdrawal limits."""
    today_start = timezone.now().replace(hour=0, minute=0, second=0)
    today_withdraws = WithdrawRequest.objects.filter(
        profile=profile,
        currency_type=currency,
        created_at__gte=today_start,
        status__in=['PENDING', 'COMPLETED']
    )
    
    total = sum(w.amount for w in today_withdraws)
    
    MAX_DAILY_WITHDRAW = {
        'RIAL': Decimal('100000000'),  # 100M Rial
        'GOLD': Decimal('100'),  # 100 grams
        'COIN': Decimal('10'),  # 10 coins
        'DOLLAR': Decimal('1000'),  # $1000
    }
    
    if total + amount > MAX_DAILY_WITHDRAW[currency]:
        raise ValidationError("محدودیت برداشت روزانه")
```

#### Receipt Upload
For deposits:
```python
# In deposit flow, add state for photo upload:
async def deposit_receipt_upload(update, context):
    """Handle receipt photo upload."""
    photo = update.message.photo[-1]  # Get largest size
    file = await photo.get_file()
    
    # Save to media directory
    filename = f"receipt_{profile.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"
    filepath = os.path.join(settings.MEDIA_ROOT, 'receipts', filename)
    await file.download_to_drive(filepath)
    
    # Store path in context
    context.user_data['receipt_path'] = filepath
```

#### Transaction Report Export
Add admin action:
```python
def export_transactions_csv(modeladmin, request, queryset):
    """Export selected transactions to CSV."""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Transaction Number', 'User', 'Type', 'Currency', 'Amount', 'Status', 'Date'])
    
    for txn in queryset:
        writer.writerow([
            txn.transaction_number,
            txn.profile.get_display_name(),
            txn.get_transaction_type_display(),
            txn.get_currency_type_display(),
            str(txn.amount),
            txn.get_status_display(),
            txn.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response
```

## 🚀 Quick Start Guide

### Step 1: Apply Migrations
```bash
python manage.py migrate users
python manage.py migrate trading
```

### Step 2: Test Admin Interface
1. Run development server: `python manage.py runserver`
2. Access admin: `http://localhost:8000/admin/`
3. Test creating:
   - Bank accounts
   - Transactions
   - Withdraw requests
4. Test bulk actions:
   - Approve bank accounts
   - Approve deposits
   - Approve/reject withdrawals

### Step 3: Implement Bot Handlers
1. Copy relevant handlers from `bot/wallet_handlers_template.py` to `bot/management/commands/runbot.py`
2. Add conversation handlers to application
3. Test each flow:
   - Start bot: `python manage.py runbot`
   - Test account menu
   - Test wallet menu
   - Test deposit flow
   - Test withdraw flow
   - Test transfer flow

### Step 4: Add Notifications
1. Integrate notification calls in services
2. Test notifications when:
   - Admin approves bank account
   - Admin approves deposit
   - Admin approves withdrawal
   - Transfer is completed

### Step 5: Production Deployment
1. Review security settings
2. Set up proper database (PostgreSQL)
3. Configure ALLOWED_HOSTS
4. Set up static/media file serving
5. Configure proper logging
6. Set up monitoring (Sentry)
7. Run migrations on production database
8. Start bot process
9. Monitor logs for errors

## 🐛 Testing Checklist

### Database Models
- [ ] Create profile with all balance fields
- [ ] Create bank account and verify it
- [ ] Create transaction and complete it
- [ ] Create withdraw request and approve it
- [ ] Create transfer request and complete it
- [ ] Test frozen balance operations
- [ ] Test atomic operations (concurrent updates)

### Services
- [ ] Test WalletService.freeze_balance()
- [ ] Test WalletService.unfreeze_balance()
- [ ] Test DepositService.approve_deposit()
- [ ] Test WithdrawService.approve_withdraw()
- [ ] Test WithdrawService.reject_withdraw()
- [ ] Test TransferService.create_transfer_request()
- [ ] Test balance validations
- [ ] Test error handling

### Admin Interface
- [ ] Test bank account verification
- [ ] Test deposit approval
- [ ] Test withdraw approval/rejection
- [ ] Test bulk actions
- [ ] Test filtering and searching
- [ ] Test readonly fields

### Bot Handlers
- [ ] Test account menu navigation
- [ ] Test wallet menu navigation
- [ ] Test deposit flow end-to-end
- [ ] Test withdraw flow end-to-end
- [ ] Test transfer flow end-to-end
- [ ] Test bank account addition
- [ ] Test error messages
- [ ] Test input validation
- [ ] Test conversation cancellation

## 📚 Additional Resources

### Useful Django Commands
```bash
# Create superuser for admin
python manage.py createsuperuser

# Check for issues
python manage.py check

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver

# Run bot
python manage.py runbot
```

### Useful Queries
```python
# Get user's available balance
profile.get_available_balance('RIAL')

# Get pending withdrawals
WithdrawRequest.objects.filter(status='PENDING')

# Get today's transactions
from django.utils import timezone
today = timezone.now().date()
Transaction.objects.filter(created_at__date=today)

# Get user's transaction history
profile.transactions.all().order_by('-created_at')[:10]
```

### Common Issues & Solutions

**Issue**: Migration conflicts
**Solution**: Delete migration files and recreate them

**Issue**: Frozen balance becomes negative
**Solution**: Check for race conditions, ensure proper use of `select_for_update()`

**Issue**: Bot not receiving updates
**Solution**: Check bot token, internet connection, Telegram API status

**Issue**: Admin can't approve requests
**Solution**: Check service method calls, database permissions

## 📧 Support

For questions or issues with this implementation:
1. Check the comprehensive docstrings in service methods
2. Review the workflow diagrams in `WALLET_IMPLEMENTATION_SUMMARY.md`
3. Examine the template code in `bot/wallet_handlers_template.py`
4. Test services in Django shell: `python manage.py shell`

---

**Last Updated**: 2025-10-25  
**Status**: Core system complete, bot handlers need implementation  
**Priority**: Implement deposit, withdraw, and transfer conversation handlers

