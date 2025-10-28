# Generated migration for wallet models

from decimal import Decimal
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0003_order_invoice_number'),
        ('users', '0003_add_wallet_fields'),
    ]

    operations = [
        # Create Transaction model
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_number', models.CharField(db_index=True, help_text='شماره یونیک تراکنش', max_length=50, unique=True, verbose_name='شماره تراکنش')),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'واریز'), ('WITHDRAW', 'برداشت'), ('TRANSFER_SEND', 'انتقال - ارسال'), ('TRANSFER_RECEIVE', 'انتقال - دریافت'), ('BUY', 'خرید'), ('SELL', 'فروش')], db_index=True, help_text='نوع تراکنش', max_length=20, verbose_name='نوع تراکنش')),
                ('currency_type', models.CharField(choices=[('RIAL', 'ریال'), ('GOLD', 'طلا'), ('COIN', 'سکه'), ('DOLLAR', 'دلار')], db_index=True, help_text='نوع ارز', max_length=10, verbose_name='نوع ارز')),
                ('amount', models.DecimalField(decimal_places=4, help_text='مقدار تراکنش', max_digits=20, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='مقدار')),
                ('balance_before', models.DecimalField(decimal_places=4, help_text='موجودی قبل از تراکنش', max_digits=20, verbose_name='موجودی قبل')),
                ('balance_after', models.DecimalField(decimal_places=4, help_text='موجودی بعد از تراکنش', max_digits=20, verbose_name='موجودی بعد')),
                ('status', models.CharField(choices=[('PENDING', 'در انتظار'), ('COMPLETED', 'تکمیل شده'), ('CANCELLED', 'لغو شده'), ('FAILED', 'ناموفق')], db_index=True, default='PENDING', help_text='وضعیت تراکنش', max_length=10, verbose_name='وضعیت')),
                ('admin_note', models.TextField(blank=True, help_text='یادداشت داخلی ادمین', verbose_name='یادداشت ادمین')),
                ('user_note', models.TextField(blank=True, help_text='یادداشت کاربر', verbose_name='یادداشت کاربر')),
                ('receipt_image', models.ImageField(blank=True, help_text='تصویر رسید (برای واریز)', null=True, upload_to='transaction_receipts/%Y/%m/', verbose_name='تصویر رسید')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='تاریخ ایجاد')),
                ('completed_at', models.DateTimeField(blank=True, help_text='زمان تکمیل تراکنش', null=True, verbose_name='تاریخ تکمیل')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')),
                ('profile', models.ForeignKey(help_text='کاربر صاحب تراکنش', on_delete=models.deletion.PROTECT, related_name='transactions', to='users.profile', verbose_name='پروفایل')),
                ('related_bank_account', models.ForeignKey(blank=True, help_text='حساب بانکی مرتبط (برای واریز/برداشت)', null=True, on_delete=models.deletion.SET_NULL, related_name='transactions', to='users.bankaccount', verbose_name='حساب بانکی مرتبط')),
                ('related_order', models.ForeignKey(blank=True, help_text='سفارش مرتبط (برای خرید/فروش)', null=True, on_delete=models.deletion.SET_NULL, related_name='transactions', to='trading.order', verbose_name='سفارش مرتبط')),
            ],
            options={
                'verbose_name': 'تراکنش',
                'verbose_name_plural': 'تراکنش‌ها',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['profile', '-created_at'], name='trading_tra_profile_idx'),
                    models.Index(fields=['transaction_type', 'status'], name='trading_tra_trans_type_idx'),
                    models.Index(fields=['currency_type', '-created_at'], name='trading_tra_currency_idx'),
                    models.Index(fields=['status', '-created_at'], name='trading_tra_status_idx'),
                ],
            },
        ),
        # Create WithdrawRequest model
        migrations.CreateModel(
            name='WithdrawRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_number', models.CharField(db_index=True, help_text='شماره یونیک درخواست', max_length=50, unique=True, verbose_name='شماره درخواست')),
                ('currency_type', models.CharField(choices=[('RIAL', 'ریال'), ('GOLD', 'طلا'), ('COIN', 'سکه'), ('DOLLAR', 'دلار')], db_index=True, help_text='نوع ارز', max_length=10, verbose_name='نوع ارز')),
                ('amount', models.DecimalField(decimal_places=4, help_text='مقدار درخواستی', max_digits=20, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='مقدار')),
                ('status', models.CharField(choices=[('PENDING', 'در انتظار بررسی'), ('APPROVED', 'تایید شده'), ('REJECTED', 'رد شده'), ('COMPLETED', 'تکمیل شده')], db_index=True, default='PENDING', help_text='وضعیت درخواست', max_length=10, verbose_name='وضعیت')),
                ('admin_note', models.TextField(blank=True, help_text='دلیل رد یا توضیحات ادمین', verbose_name='یادداشت ادمین')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='تاریخ ایجاد')),
                ('processed_at', models.DateTimeField(blank=True, help_text='زمان پردازش توسط ادمین', null=True, verbose_name='تاریخ پردازش')),
                ('completed_at', models.DateTimeField(blank=True, help_text='زمان تکمیل نهایی', null=True, verbose_name='تاریخ تکمیل')),
                ('bank_account', models.ForeignKey(help_text='حساب بانکی مقصد برای واریز', on_delete=models.deletion.PROTECT, related_name='withdraw_requests', to='users.bankaccount', verbose_name='حساب بانکی مقصد')),
                ('profile', models.ForeignKey(help_text='کاربر درخواست‌کننده', on_delete=models.deletion.PROTECT, related_name='withdraw_requests', to='users.profile', verbose_name='پروفایل')),
                ('related_transaction', models.OneToOneField(blank=True, help_text='تراکنش مرتبط با این درخواست', null=True, on_delete=models.deletion.SET_NULL, related_name='withdraw_request', to='trading.transaction', verbose_name='تراکنش مرتبط')),
            ],
            options={
                'verbose_name': 'درخواست برداشت',
                'verbose_name_plural': 'درخواست‌های برداشت',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['profile', '-created_at'], name='trading_wit_profile_idx'),
                    models.Index(fields=['status', '-created_at'], name='trading_wit_status_idx'),
                    models.Index(fields=['currency_type', 'status'], name='trading_wit_currency_idx'),
                ],
            },
        ),
    ]

