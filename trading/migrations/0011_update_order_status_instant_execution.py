# Generated migration for instant order execution system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0010_rename_trading_tra_profile_idx_trading_tra_profile_9314fb_idx_and_more'),
    ]

    operations = [
        # First, update all existing PENDING orders to COMPLETED
        # This is a data migration to handle existing orders
        migrations.RunSQL(
            sql="UPDATE trading_order SET status = 'COMPLETED', completed_at = NOW() WHERE status = 'PENDING';",
            reverse_sql="UPDATE trading_order SET status = 'PENDING', completed_at = NULL WHERE status = 'COMPLETED' AND completed_at IS NOT NULL;",
        ),
        
        # Update the status field choices (remove PENDING, add REJECTED)
        # Remove the default value for status field
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('COMPLETED', 'تکمیل شده'),
                    ('CANCELLED', 'لغو شده'),
                    ('REJECTED', 'رد شده')
                ],
                db_index=True,
                help_text='وضعیت فعلی سفارش',
                max_length=10,
                verbose_name='وضعیت'
            ),
        ),
    ]
