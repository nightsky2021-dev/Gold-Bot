# Generated migration for adding product_code field to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='product_code',
            field=models.CharField(
                choices=[
                    ('gold', 'طلای آبشده'),
                    ('coin', 'سکه تمام'),
                    ('dollar', 'دلار آمریکا')
                ],
                db_index=True,
                default='gold',  # Temporary default for existing records
                help_text='کد یکتای محصول برای شناسایی',
                max_length=20,
                unique=True,
                verbose_name='کد محصول'
            ),
            preserve_default=False,
        ),
    ]
