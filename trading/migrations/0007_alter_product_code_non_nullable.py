# Generated manually to make product_code non-nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0006_populate_product_codes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_code',
            field=models.CharField(
                max_length=20,
                unique=True,
                choices=[
                    ('gold', 'طلای آبشده'),
                    ('coin', 'سکه تمام'),
                    ('dollar', 'دلار آمریکا'),
                ],
                verbose_name="کد محصول",
                help_text="کد یکتای محصول برای شناسایی",
                db_index=True
            ),
        ),
    ]

