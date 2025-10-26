# Generated migration for wallet fields

from decimal import Decimal
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # Add new balance fields to Profile
        migrations.AddField(
            model_name='profile',
            name='coin_balance',
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal('0.0000'),
                help_text='موجودی سکه تمام کاربر',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی سکه'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='dollar_balance',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='موجودی دلار کاربر',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی دلار'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='frozen_rial_balance',
            field=models.DecimalField(
                decimal_places=0,
                default=0,
                help_text='موجودی ریالی مسدود شده برای تراکنش‌های در حال انجام',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی ریالی مسدود شده'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='frozen_gold_balance',
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal('0.0000'),
                help_text='موجودی طلای مسدود شده برای تراکنش‌های در حال انجام',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی طلای مسدود شده'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='frozen_coin_balance',
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal('0.0000'),
                help_text='موجودی سکه مسدود شده برای تراکنش‌های در حال انجام',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی سکه مسدود شده'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='frozen_dollar_balance',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='موجودی دلار مسدود شده برای تراکنش‌های در حال انجام',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی دلار مسدود شده'
            ),
        ),
        # Create BankAccount model
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_holder_name', models.CharField(help_text='نام صاحب حساب (باید با نام کاربر مطابقت داشته باشد)', max_length=200, verbose_name='نام صاحب حساب')),
                ('bank_name', models.CharField(choices=[('ملی ایران', 'ملی ایران'), ('ملت', 'ملت'), ('تجارت', 'تجارت'), ('صادرات', 'صادرات'), ('سپه', 'سپه'), ('رفاه', 'رفاه'), ('پاسارگاد', 'پاسارگاد'), ('پارسیان', 'پارسیان'), ('اقتصاد نوین', 'اقتصاد نوین'), ('سامان', 'سامان'), ('سینا', 'سینا'), ('کارآفرین', 'کارآفرین'), ('آینده', 'آینده'), ('شهر', 'شهر'), ('دی', 'دی'), ('صنعت و معدن', 'صنعت و معدن'), ('توسعه تعاون', 'توسعه تعاون'), ('قوامین', 'قوامین'), ('مهر اقتصاد', 'مهر اقتصاد'), ('حکمت ایرانیان', 'حکمت ایرانیان')], help_text='نام بانک', max_length=50, verbose_name='نام بانک')),
                ('account_number', models.CharField(help_text='شماره کارت 16 رقمی یا شماره شبا (IR + 24 رقم)', max_length=26, verbose_name='شماره حساب')),
                ('account_type', models.CharField(choices=[('CARD', 'کارت بانکی'), ('IBAN', 'شماره شبا')], help_text='نوع حساب: کارت بانکی یا شماره شبا', max_length=4, verbose_name='نوع حساب')),
                ('is_verified', models.BooleanField(db_index=True, default=False, help_text='آیا این حساب توسط ادمین تایید شده است؟', verbose_name='تایید شده')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='آیا این حساب برای واریز/برداشت فعال است؟', verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')),
                ('profile', models.ForeignKey(help_text='پروفایل صاحب حساب', on_delete=models.deletion.CASCADE, related_name='bank_accounts', to='users.profile', verbose_name='پروفایل')),
            ],
            options={
                'verbose_name': 'حساب بانکی',
                'verbose_name_plural': 'حساب‌های بانکی',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['profile', 'is_verified'], name='users_banka_profile_idx'),
                    models.Index(fields=['is_verified', 'is_active'], name='users_banka_is_verified_idx'),
                ],
            },
        ),
        migrations.AlterUniqueTogether(
            name='bankaccount',
            unique_together={('profile', 'account_number')},
        ),
    ]
