"""
Business logic services for users app
"""
from typing import Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile


def get_or_create_profile_by_telegram(
    telegram_id: str,
    phone_number: str,
    first_name: str = "",
    last_name: str = "",
    telegram_username: Optional[str] = None
) -> Tuple[Profile, bool]:
    """
    دریافت یا ایجاد پروفایل کاربر بر اساس شناسه تلگرام
    
    Args:
        telegram_id: شناسه عددی تلگرام
        phone_number: شماره تماس کاربر
        first_name: نام کاربر
        last_name: نام خانوادگی کاربر
        telegram_username: نام کاربری تلگرام (اختیاری)
    
    Returns:
        Tuple[Profile, bool]: پروفایل و اینکه آیا جدید ایجاد شده یا خیر
    """
    try:
        # جستجو بر اساس telegram_id
        profile = Profile.objects.select_related('user').get(telegram_id=telegram_id)
        created = False
        
        # به‌روزرسانی نام کاربری تلگرام در صورت تغییر
        if telegram_username and profile.telegram_username != telegram_username:
            profile.telegram_username = telegram_username
            profile.save(update_fields=['telegram_username'])
            
    except Profile.DoesNotExist:
        # ایجاد کاربر و پروفایل جدید
        with transaction.atomic():
            # ایجاد username یکتا از روی telegram_id
            username = f"tg_{telegram_id}"
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            profile = Profile.objects.create(
                user=user,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                phone_number=phone_number
            )
            created = True
    
    return profile, created


def get_profile_by_telegram_id(telegram_id: str) -> Optional[Profile]:
    """
    دریافت پروفایل بر اساس شناسه تلگرام
    
    Args:
        telegram_id: شناسه عددی تلگرام
    
    Returns:
        Profile یا None
    """
    try:
        return Profile.objects.select_related('user').get(telegram_id=telegram_id)
    except Profile.DoesNotExist:
        return None


def is_user_approved(telegram_id: str) -> bool:
    """
    بررسی تایید شدن کاربر توسط ادمین
    
    Args:
        telegram_id: شناسه عددی تلگرام
    
    Returns:
        bool: آیا کاربر تایید شده است یا خیر
    """
    profile = get_profile_by_telegram_id(telegram_id)
    return profile.is_approved if profile else False


def update_user_balance(
    profile: Profile,
    rial_change: float = 0,
    gold_change: float = 0
) -> Profile:
    """
    به‌روزرسانی موجودی کاربر (باید در transaction استفاده شود)
    
    Args:
        profile: پروفایل کاربر
        rial_change: تغییر موجودی ریالی (مثبت یا منفی)
        gold_change: تغییر موجودی طلا (مثبت یا منفی)
    
    Returns:
        Profile: پروفایل به‌روزرسانی شده
    
    Raises:
        ValueError: اگر موجودی منفی شود
    """
    new_rial_balance = profile.rial_balance + rial_change
    new_gold_balance = profile.gold_balance_grams + gold_change
    
    if new_rial_balance < 0:
        raise ValueError("موجودی ریالی کافی نیست.")
    
    if new_gold_balance < 0:
        raise ValueError("موجودی طلا کافی نیست.")
    
    profile.rial_balance = new_rial_balance
    profile.gold_balance_grams = new_gold_balance
    profile.save(update_fields=['rial_balance', 'gold_balance_grams'])
    
    return profile


class WalletService:
    """
    Service for wallet operations including balance display,
    freezing/unfreezing balances, and formatting wallet information.
    """
    
    @staticmethod
    def format_wallet_display(profile: Profile) -> str:
        """
        Format complete wallet display with all balances.
        
        Args:
            profile: User profile
            
        Returns:
            Formatted wallet string with all currencies
        """
        rial_available = profile.get_available_rial_balance()
        rial_frozen = profile.frozen_rial_balance
        
        gold_available = profile.get_available_gold_balance()
        gold_frozen = profile.frozen_gold_balance
        
        wallet_text = "💼 *کیف پول شما:*\n\n"
        
        # Rial balance
        wallet_text += f"💰 *ریال:*\n"
        wallet_text += f"   موجودی کل: {profile.rial_balance:,.0f} ریال\n"
        wallet_text += f"   قابل استفاده: {rial_available:,.0f} ریال\n"
        if rial_frozen > 0:
            wallet_text += f"   مسدود شده: {rial_frozen:,.0f} ریال\n"
        wallet_text += "\n"
        
        # Gold balance
        wallet_text += f"🪙 *طلا:*\n"
        wallet_text += f"   موجودی کل: {profile.gold_balance_grams} گرم\n"
        wallet_text += f"   قابل استفاده: {gold_available} گرم\n"
        if gold_frozen > 0:
            wallet_text += f"   مسدود شده: {gold_frozen} گرم\n"
        
        return wallet_text
    
    @staticmethod
    def freeze_balance(
        profile: Profile,
        currency: str,
        amount: float
    ) -> None:
        """
        Freeze balance for pending withdrawal.
        
        Args:
            profile: User profile
            currency: Currency type ('RIAL', 'GOLD', 'COIN', 'DOLLAR')
            amount: Amount to freeze
            
        Raises:
            ValueError: If insufficient available balance
        """
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            # Refresh from database to avoid race conditions
            profile.refresh_from_db()
            
            if currency == 'RIAL':
                if not profile.has_sufficient_available_rial(amount):
                    raise ValueError("موجودی ریالی قابل برداشت کافی نیست.")
                profile.frozen_rial_balance += amount
                profile.save(update_fields=['frozen_rial_balance'])
                
            elif currency in ['GOLD', 'COIN']:
                if not profile.has_sufficient_available_gold(amount):
                    raise ValueError("موجودی طلای قابل برداشت کافی نیست.")
                profile.frozen_gold_balance += amount
                profile.save(update_fields=['frozen_gold_balance'])
            
            else:
                raise ValueError(f"ارز {currency} پشتیبانی نمی‌شود.")
    
    @staticmethod
    def unfreeze_balance(
        profile: Profile,
        currency: str,
        amount: float
    ) -> None:
        """
        Unfreeze balance (e.g., when withdrawal is cancelled).
        
        Args:
            profile: User profile
            currency: Currency type
            amount: Amount to unfreeze
        """
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            profile.refresh_from_db()
            
            if currency == 'RIAL':
                profile.frozen_rial_balance = max(0, profile.frozen_rial_balance - amount)
                profile.save(update_fields=['frozen_rial_balance'])
                
            elif currency in ['GOLD', 'COIN']:
                profile.frozen_gold_balance = max(0, profile.frozen_gold_balance - amount)
                profile.save(update_fields=['frozen_gold_balance'])
    
    @staticmethod
    def process_withdrawal(
        profile: Profile,
        currency: str,
        amount: float
    ) -> None:
        """
        Process withdrawal by deducting from both frozen and total balance.
        
        Args:
            profile: User profile
            currency: Currency type
            amount: Amount to withdraw
        """
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            profile.refresh_from_db()
            
            if currency == 'RIAL':
                profile.rial_balance -= amount
                profile.frozen_rial_balance -= amount
                profile.save(update_fields=['rial_balance', 'frozen_rial_balance'])
                
            elif currency in ['GOLD', 'COIN']:
                profile.gold_balance_grams -= amount
                profile.frozen_gold_balance -= amount
                profile.save(update_fields=['gold_balance_grams', 'frozen_gold_balance'])
    
    @staticmethod
    def add_balance(
        profile: Profile,
        currency: str,
        amount: float
    ) -> None:
        """
        Add balance to user's wallet (e.g., after deposit approval).
        
        Args:
            profile: User profile
            currency: Currency type
            amount: Amount to add
        """
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            profile.refresh_from_db()
            
            if currency == 'RIAL':
                profile.rial_balance += amount
                profile.save(update_fields=['rial_balance'])
                
            elif currency in ['GOLD', 'COIN']:
                profile.gold_balance_grams += amount
                profile.save(update_fields=['gold_balance_grams'])
    
    @staticmethod
    def get_currency_display_name(currency: str) -> str:
        """Get Persian display name for currency."""
        currency_names = {
            'RIAL': 'ریال',
            'GOLD': 'طلا',
            'COIN': 'سکه',
            'DOLLAR': 'دلار'
        }
        return currency_names.get(currency, currency)
