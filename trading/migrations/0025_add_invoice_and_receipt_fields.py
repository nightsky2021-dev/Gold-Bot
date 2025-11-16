# Generated manually for invoice and receipt system enhancement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0024_rename_trading_por_token_idx_trading_por_token_0db3f9_idx_and_more'),
    ]

    operations = [
        # Add invoice fields to Order
        migrations.AddField(
            model_name='order',
            name='invoice_number',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='شماره یکتای فاکتور (به صورت خودکار تولید می‌شود)',
                max_length=50,
                null=True,
                unique=True,
                verbose_name='شماره فاکتور'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_generated_at',
            field=models.DateTimeField(
                blank=True,
                help_text='زمان تولید فاکتور',
                null=True,
                verbose_name='زمان تولید فاکتور'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_hash',
            field=models.CharField(
                blank=True,
                help_text='هش برای تأیید صحت فاکتور',
                max_length=64,
                null=True,
                verbose_name='هش فاکتور'
            ),
        ),
        # Add receipt fields to Transaction
        migrations.AddField(
            model_name='transaction',
            name='receipt_status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'در انتظار بررسی'),
                    ('VERIFIED', 'تأیید شده'),
                    ('REJECTED', 'رد شده'),
                ],
                db_index=True,
                default='PENDING',
                help_text='وضعیت بررسی رسید',
                max_length=20,
                verbose_name='وضعیت رسید'
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='receipt_rejection_reason',
            field=models.TextField(
                blank=True,
                help_text='دلیل رد رسید (در صورت رد)',
                verbose_name='دلیل رد رسید'
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='receipt_verified_at',
            field=models.DateTimeField(
                blank=True,
                help_text='زمان تأیید رسید توسط مدیر',
                null=True,
                verbose_name='زمان تأیید رسید'
            ),
        ),
    ]
