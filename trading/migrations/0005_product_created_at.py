# Generated migration to add created_at to Product

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0004_add_wallet_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now,
                verbose_name='تاریخ ایجاد'
            ),
            preserve_default=False,
        ),
    ]

