# Generated migration for wallet fields

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


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
                decimal_places=2,
                default=Decimal('0.00'),
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
                max_digits=12,
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
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی طلای مسدود شده'
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='frozen_coin_balance',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
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
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی دلار مسدود شده'
            ),
        ),
        # Create BankAccount model
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_holder_name', models.CharField(max_length=200, verbose_name='نام صاحب حساب')),
                ('bank_name', models.CharField(
                    max_length=50,
                    choices=[
                        ('ملی ایران', 'بانک ملی ایران'),
                        ('ملت', 'بانک ملت'),
                        ('تجارت', 'بانک تجارت'),
                        ('صادرات', 'بانک صادرات'),
                        ('سپه', 'بانک سپه'),
                        ('رفاه', 'بانک رفاه'),
                        ('پاسارگاد', 'بانک پاسارگاد'),
                        ('پارسیان', 'بانک پارسیان'),
                        ('اقتصاد نوین', 'بانک اقتصاد نوین'),
                        ('سامان', 'بانک سامان'),
                        ('سینا', 'بانک سینا'),
                        ('کارآفرین', 'بانک کارآفرین'),
                        ('آینده', 'بانک آینده'),
                        ('شهر', 'بانک شهر'),
                        ('دی', 'بانک دی'),
                        ('صنعت و معدن', 'بانک صنعت و معدن'),
                        ('توسعه تعاون', 'بانک توسعه تعاون'),
                        ('قوامین', 'بانک قوامین'),
                        ('مهر اقتصاد', 'بانک مهر اقتصاد'),
                        ('حکمت ایرانیان', 'بانک حکمت ایرانیان'),
                    ],
                    verbose_name='نام بانک'
                )),
                ('account_number', models.CharField(max_length=50, verbose_name='شماره حساب/کارت')),
                ('is_verified', models.BooleanField(default=False, verbose_name='تایید شده')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')),
                ('profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bank_accounts',
                    to='users.profile',
                    verbose_name='پروفایل'
                )),
            ],
            options={
                'verbose_name': 'حساب بانکی',
                'verbose_name_plural': 'حساب‌های بانکی',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='bankaccount',
            index=models.Index(fields=['profile', 'is_verified'], name='users_banka_profile_idx'),
        ),
        migrations.AddIndex(
            model_name='bankaccount',
            index=models.Index(fields=['is_verified', 'is_active'], name='users_banka_verified_idx'),
        ),
    ]
