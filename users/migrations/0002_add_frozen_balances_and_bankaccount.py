# Generated migration for adding frozen balances and BankAccount model

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='frozen_rial_balance',
            field=models.DecimalField(
                decimal_places=0,
                default=0,
                help_text='موجودی ریالی که به دلیل برداشت در انتظار مسدود شده',
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
                help_text='موجودی طلا که به دلیل برداشت در انتظار مسدود شده',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='موجودی طلای مسدود شده'
            ),
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(help_text='نام بانک (مثل: ملی، ملت، سپه)', max_length=100, verbose_name='نام بانک')),
                ('account_holder_name', models.CharField(help_text='نام کامل صاحب حساب', max_length=200, verbose_name='نام صاحب حساب')),
                ('account_number', models.CharField(help_text='شماره حساب 16 رقمی', max_length=16, verbose_name='شماره حساب')),
                ('iban', models.CharField(blank=True, help_text='شماره شبای 26 رقمی (اختیاری)', max_length=26, verbose_name='شماره شبا')),
                ('account_type', models.CharField(choices=[('SAVINGS', 'حساب پس\u200cانداز'), ('CURRENT', 'حساب جاری')], default='SAVINGS', help_text='نوع حساب بانکی', max_length=10, verbose_name='نوع حساب')),
                ('is_verified', models.BooleanField(db_index=True, default=False, help_text='آیا این حساب توسط ادمین تأیید شده است؟', verbose_name='تأیید شده')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین به\u200cروزرسانی')),
                ('profile', models.ForeignKey(help_text='کاربری که این حساب متعلق به اوست', on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts', to='users.profile', verbose_name='پروفایل کاربر')),
            ],
            options={
                'verbose_name': 'حساب بانکی',
                'verbose_name_plural': 'حساب\u200cهای بانکی',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['profile', 'is_verified'], name='users_banka_profile_idx'),
                    models.Index(fields=['account_number'], name='users_banka_account_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='bankaccount',
            constraint=models.UniqueConstraint(fields=('profile', 'account_number'), name='unique_profile_account'),
        ),
    ]
