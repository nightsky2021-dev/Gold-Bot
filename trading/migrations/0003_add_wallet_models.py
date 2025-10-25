# Generated migration for wallet models

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0002_add_product_code'),
        ('users', '0002_add_wallet_fields'),
    ]

    operations = [
        # Create Transaction model
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_number', models.CharField(max_length=50, unique=True, verbose_name='شماره تراکنش')),
                ('transaction_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('DEPOSIT', 'واریز وجه'),
                        ('WITHDRAW', 'برداشت وجه'),
                        ('TRANSFER_SEND', 'انتقال ارسالی'),
                        ('TRANSFER_RECEIVE', 'انتقال دریافتی'),
                        ('BUY', 'خرید'),
                        ('SELL', 'فروش'),
                    ],
                    verbose_name='نوع تراکنش'
                )),
                ('currency_type', models.CharField(
                    max_length=10,
                    choices=[
                        ('RIAL', 'ریال'),
                        ('GOLD', 'طلا'),
                        ('COIN', 'سکه'),
                        ('DOLLAR', 'دلار'),
                    ],
                    verbose_name='نوع ارز'
                )),
                ('amount', models.DecimalField(
                    decimal_places=4,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='مقدار'
                )),
                ('balance_before', models.DecimalField(decimal_places=4, max_digits=15, verbose_name='موجودی قبل از تراکنش')),
                ('balance_after', models.DecimalField(decimal_places=4, max_digits=15, verbose_name='موجودی بعد از تراکنش')),
                ('status', models.CharField(
                    max_length=10,
                    choices=[
                        ('PENDING', 'در انتظار بررسی'),
                        ('COMPLETED', 'تکمیل شده'),
                        ('CANCELLED', 'لغو شده'),
                        ('FAILED', 'ناموفق'),
                    ],
                    default='PENDING',
                    verbose_name='وضعیت'
                )),
                ('admin_note', models.TextField(blank=True, verbose_name='یادداشت ادمین')),
                ('user_note', models.TextField(blank=True, verbose_name='یادداشت کاربر')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تکمیل')),
                ('profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='transactions',
                    to='users.profile',
                    verbose_name='پروفایل کاربر'
                )),
                ('related_bank_account', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transactions',
                    to='users.bankaccount',
                    verbose_name='حساب بانکی مرتبط'
                )),
                ('related_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='related_transactions',
                    to='users.profile',
                    verbose_name='کاربر مرتبط'
                )),
                ('related_order', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transactions',
                    to='trading.order',
                    verbose_name='سفارش مرتبط'
                )),
            ],
            options={
                'verbose_name': 'تراکنش',
                'verbose_name_plural': 'تراکنش‌ها',
                'ordering': ['-created_at'],
            },
        ),
        # Create WithdrawRequest model
        migrations.CreateModel(
            name='WithdrawRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_number', models.CharField(max_length=50, unique=True, verbose_name='شماره درخواست')),
                ('currency_type', models.CharField(
                    max_length=10,
                    choices=[
                        ('RIAL', 'ریال'),
                        ('GOLD', 'طلا'),
                        ('COIN', 'سکه'),
                        ('DOLLAR', 'دلار'),
                    ],
                    verbose_name='نوع ارز'
                )),
                ('amount', models.DecimalField(
                    decimal_places=4,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='مقدار درخواستی'
                )),
                ('status', models.CharField(
                    max_length=10,
                    choices=[
                        ('PENDING', 'در انتظار بررسی'),
                        ('APPROVED', 'تایید شده'),
                        ('REJECTED', 'رد شده'),
                        ('COMPLETED', 'تکمیل شده'),
                    ],
                    default='PENDING',
                    verbose_name='وضعیت'
                )),
                ('admin_note', models.TextField(blank=True, verbose_name='یادداشت ادمین')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ پردازش')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تکمیل')),
                ('profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='withdraw_requests',
                    to='users.profile',
                    verbose_name='پروفایل کاربر'
                )),
                ('bank_account', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='withdraw_requests',
                    to='users.bankaccount',
                    verbose_name='حساب بانکی مقصد'
                )),
                ('related_transaction', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='withdraw_request',
                    to='trading.transaction',
                    verbose_name='تراکنش مرتبط'
                )),
            ],
            options={
                'verbose_name': 'درخواست برداشت',
                'verbose_name_plural': 'درخواست‌های برداشت',
                'ordering': ['-created_at'],
            },
        ),
        # Create TransferRequest model
        migrations.CreateModel(
            name='TransferRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_number', models.CharField(max_length=50, unique=True, verbose_name='شماره درخواست')),
                ('receiver_phone', models.CharField(max_length=15, verbose_name='شماره تلفن گیرنده')),
                ('currency_type', models.CharField(
                    max_length=10,
                    choices=[
                        ('RIAL', 'ریال'),
                        ('GOLD', 'طلا'),
                        ('COIN', 'سکه'),
                        ('DOLLAR', 'دلار'),
                    ],
                    verbose_name='نوع ارز'
                )),
                ('amount', models.DecimalField(
                    decimal_places=4,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='مقدار'
                )),
                ('status', models.CharField(
                    max_length=10,
                    choices=[
                        ('PENDING', 'در انتظار بررسی'),
                        ('COMPLETED', 'تکمیل شده'),
                        ('CANCELLED', 'لغو شده'),
                    ],
                    default='PENDING',
                    verbose_name='وضعیت'
                )),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تکمیل')),
                ('sender_profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='sent_transfers',
                    to='users.profile',
                    verbose_name='فرستنده'
                )),
                ('receiver_profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='received_transfers',
                    to='users.profile',
                    verbose_name='گیرنده'
                )),
                ('sender_transaction', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transfer_send',
                    to='trading.transaction',
                    verbose_name='تراکنش فرستنده'
                )),
                ('receiver_transaction', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transfer_receive',
                    to='trading.transaction',
                    verbose_name='تراکنش گیرنده'
                )),
            ],
            options={
                'verbose_name': 'درخواست انتقال وجه',
                'verbose_name_plural': 'درخواست‌های انتقال وجه',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes for Transaction
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_number'], name='trading_tra_txn_num_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['profile', '-created_at'], name='trading_tra_profile_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['status', '-created_at'], name='trading_tra_status_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_type', 'currency_type'], name='trading_tra_type_idx'),
        ),
        # Add indexes for WithdrawRequest
        migrations.AddIndex(
            model_name='withdrawrequest',
            index=models.Index(fields=['status', '-created_at'], name='trading_wd_status_idx'),
        ),
        migrations.AddIndex(
            model_name='withdrawrequest',
            index=models.Index(fields=['profile', '-created_at'], name='trading_wd_profile_idx'),
        ),
        # Add indexes for TransferRequest
        migrations.AddIndex(
            model_name='transferrequest',
            index=models.Index(fields=['status', '-created_at'], name='trading_tr_status_idx'),
        ),
        migrations.AddIndex(
            model_name='transferrequest',
            index=models.Index(fields=['sender_profile', '-created_at'], name='trading_tr_sender_idx'),
        ),
        migrations.AddIndex(
            model_name='transferrequest',
            index=models.Index(fields=['receiver_profile', '-created_at'], name='trading_tr_receiver_idx'),
        ),
    ]
