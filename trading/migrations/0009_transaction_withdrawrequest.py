# Generated migration for Transaction and WithdrawRequest models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_profile_options_and_more'),
        ('trading', '0008_remove_order_trading_ord_created_f24bb8_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'واریز'), ('WITHDRAW', 'برداشت'), ('BUY', 'خرید'), ('SELL', 'فروش'), ('ADJUSTMENT', 'تعدیل')], help_text='نوع عملیات انجام شده', max_length=15, verbose_name='نوع تراکنش')),
                ('currency', models.CharField(choices=[('RIAL', 'ریال'), ('GOLD', 'طلا'), ('COIN', 'سکه'), ('DOLLAR', 'دلار')], help_text='نوع ارز تراکنش', max_length=10, verbose_name='ارز')),
                ('amount', models.DecimalField(decimal_places=4, help_text='مقدار تراکنش', max_digits=15, verbose_name='مقدار')),
                ('status', models.CharField(choices=[('PENDING', 'در انتظار'), ('COMPLETED', 'تکمیل شده'), ('CANCELLED', 'لغو شده'), ('REJECTED', 'رد شده')], db_index=True, default='PENDING', help_text='وضعیت فعلی تراکنش', max_length=10, verbose_name='وضعیت')),
                ('receipt_image', models.ImageField(blank=True, help_text='تصویر رسید واریز (فقط برای واریز ریالی)', null=True, upload_to='receipts/%Y/%m/', verbose_name='تصویر رسید')),
                ('description', models.TextField(blank=True, help_text='توضیحات تراکنش', verbose_name='توضیحات')),
                ('admin_notes', models.TextField(blank=True, help_text='یادداشت\u200cهای داخلی برای مدیر', verbose_name='یادداشت\u200cهای مدیر')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به\u200cروزرسانی')),
                ('completed_at', models.DateTimeField(blank=True, help_text='زمان تکمیل تراکنش', null=True, verbose_name='تاریخ تکمیل')),
                ('bank_account', models.ForeignKey(blank=True, help_text='حساب بانکی مرتبط (برای واریز/برداشت)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='users.bankaccount', verbose_name='حساب بانکی')),
                ('profile', models.ForeignKey(help_text='کاربر مربوط به این تراکنش', on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='users.profile', verbose_name='پروفایل کاربر')),
                ('related_order', models.ForeignKey(blank=True, help_text='سفارش مرتبط (برای خرید/فروش)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='trading.order', verbose_name='سفارش مرتبط')),
            ],
            options={
                'verbose_name': 'تراکنش',
                'verbose_name_plural': 'تراکنش\u200cها',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['profile', '-created_at'], name='trading_tra_profile_idx'),
                    models.Index(fields=['status', '-created_at'], name='trading_tra_status_idx'),
                    models.Index(fields=['transaction_type', 'status'], name='trading_tra_transac_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='WithdrawRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(choices=[('RIAL', 'ریال'), ('GOLD', 'طلا'), ('COIN', 'سکه'), ('DOLLAR', 'دلار')], help_text='نوع ارز برداشت', max_length=10, verbose_name='ارز')),
                ('amount', models.DecimalField(decimal_places=4, help_text='مقدار برداشت', max_digits=15, verbose_name='مقدار')),
                ('status', models.CharField(choices=[('PENDING', 'در انتظار'), ('PROCESSING', 'در حال پردازش'), ('COMPLETED', 'تکمیل شده'), ('CANCELLED', 'لغو شده'), ('REJECTED', 'رد شده')], db_index=True, default='PENDING', help_text='وضعیت فعلی درخواست', max_length=15, verbose_name='وضعیت')),
                ('rejection_reason', models.TextField(blank=True, help_text='دلیل رد درخواست (در صورت رد)', verbose_name='دلیل رد')),
                ('admin_notes', models.TextField(blank=True, help_text='یادداشت\u200cهای داخلی برای مدیر', verbose_name='یادداشت\u200cهای مدیر')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='تاریخ ثبت')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به\u200cروزرسانی')),
                ('completed_at', models.DateTimeField(blank=True, help_text='زمان تکمیل درخواست', null=True, verbose_name='تاریخ تکمیل')),
                ('bank_account', models.ForeignKey(help_text='حساب بانکی که باید به آن واریز شود', on_delete=django.db.models.deletion.PROTECT, related_name='withdraw_requests', to='users.bankaccount', verbose_name='حساب بانکی مقصد')),
                ('profile', models.ForeignKey(help_text='کاربر درخواست\u200cکننده', on_delete=django.db.models.deletion.PROTECT, related_name='withdraw_requests', to='users.profile', verbose_name='پروفایل کاربر')),
                ('related_transaction', models.OneToOneField(blank=True, help_text='تراکنش ثبت شده برای این برداشت', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='withdraw_request', to='trading.transaction', verbose_name='تراکنش مرتبط')),
            ],
            options={
                'verbose_name': 'درخواست برداشت',
                'verbose_name_plural': 'درخواست\u200cهای برداشت',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['profile', '-created_at'], name='trading_wit_profile_idx'),
                    models.Index(fields=['status', '-created_at'], name='trading_wit_status_idx'),
                ],
            },
        ),
    ]
