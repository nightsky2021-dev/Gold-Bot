# Generated manually for dynamic wallet system

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0024_rename_trading_por_token_idx_trading_por_token_0db3f9_idx_and_more'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, help_text='کد یکتای ارز (مثل: RIAL, GOLD, COIN, DOLLAR)', max_length=20, unique=True, verbose_name='کد ارز')),
                ('name', models.CharField(help_text='نام فارسی ارز (مثل: ریال، طلا، سکه، دلار)', max_length=100, verbose_name='نام فارسی')),
                ('display_name', models.CharField(blank=True, help_text='نام نمایشی برای استفاده در رابط کاربری', max_length=100, verbose_name='نام نمایشی')),
                ('display_symbol', models.CharField(help_text='نماد نمایشی ارز (مثل: ریال، گرم، عدد، $)', max_length=20, verbose_name='نماد نمایشی')),
                ('decimal_places', models.IntegerField(default=0, help_text='تعداد اعشار برای نمایش (0 برای ریال/سکه، 4 برای طلا، 2 برای دلار)', verbose_name='تعداد اعشار')),
                ('display_order', models.IntegerField(default=0, help_text='ترتیب نمایش در لیست ارزها (عدد کمتر = اولویت بیشتر)', verbose_name='ترتیب نمایش')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='آیا این ارز فعال است و در کیف پول نمایش داده می‌شود؟', verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')),
            ],
            options={
                'verbose_name': 'ارز',
                'verbose_name_plural': 'ارزها',
                'ordering': ['display_order', 'code'],
            },
        ),
        migrations.CreateModel(
            name='ProductCurrencyMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_primary', models.BooleanField(default=True, help_text='آیا این ارز اصلی برای این محصول است؟ (هر محصول باید یک ارز اصلی داشته باشد)', verbose_name='ارز اصلی')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product_mappings', to='trading.currency', verbose_name='ارز')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currency_mappings', to='trading.product', verbose_name='محصول')),
            ],
            options={
                'verbose_name': 'نقشه\u200cبرداری محصول به ارز',
                'verbose_name_plural': 'نقشه\u200cبرداری\u200cهای محصول به ارز',
                'ordering': ['product', '-is_primary', 'currency'],
            },
        ),
        migrations.CreateModel(
            name='WalletBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('available_balance', models.DecimalField(decimal_places=4, default=Decimal('0.0000'), help_text='موجودی قابل استفاده (غیر مسدود)', max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='موجودی قابل استفاده')),
                ('frozen_balance', models.DecimalField(decimal_places=4, default=Decimal('0.0000'), help_text='موجودی مسدود شده (برای برداشت در انتظار)', max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='موجودی مسدود شده')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به\u200cروزرسانی')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='wallet_balances', to='trading.currency', verbose_name='ارز')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallet_balances', to='users.profile', verbose_name='پروفایل کاربر')),
            ],
            options={
                'verbose_name': 'موجودی کیف پول',
                'verbose_name_plural': 'موجودی\u200cهای کیف پول',
                'ordering': ['profile', 'currency'],
            },
        ),
        migrations.AddIndex(
            model_name='currency',
            index=models.Index(fields=['is_active', 'display_order'], name='trading_cur_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='currency',
            index=models.Index(fields=['code'], name='trading_cur_code_idx'),
        ),
        migrations.AddIndex(
            model_name='productcurrencymapping',
            index=models.Index(fields=['product', 'is_primary'], name='trading_pro_product_idx'),
        ),
        migrations.AddIndex(
            model_name='productcurrencymapping',
            index=models.Index(fields=['currency'], name='trading_pro_currency_idx'),
        ),
        migrations.AddIndex(
            model_name='walletbalance',
            index=models.Index(fields=['profile', 'currency'], name='trading_wal_profile_idx'),
        ),
        migrations.AddIndex(
            model_name='walletbalance',
            index=models.Index(fields=['currency'], name='trading_wal_currency_idx'),
        ),
        migrations.AddConstraint(
            model_name='productcurrencymapping',
            constraint=models.UniqueConstraint(fields=['product', 'currency'], name='unique_product_currency'),
        ),
        migrations.AddConstraint(
            model_name='walletbalance',
            constraint=models.UniqueConstraint(fields=['profile', 'currency'], name='unique_profile_currency'),
        ),
    ]
