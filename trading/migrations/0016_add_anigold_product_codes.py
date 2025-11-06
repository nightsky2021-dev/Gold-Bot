# Generated migration for Anigold product codes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0015_product_base_price_api_product_buy_margin_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_code',
            field=models.CharField(
                choices=[
                    ('dollar_usa', 'دلار آمریکا'),
                    ('euro', 'یورو'),
                    ('lira_turkey', 'لیر ترکیه'),
                    ('yuan_china', 'یوان چین'),
                    ('pound_uk', 'پوند انگلیس'),
                    ('dirham_uae', 'درهم امارات'),
                    ('coin_full', 'سکه غیربانکی'),
                    ('coin_half', 'نیم سکه غیربانکی'),
                    ('coin_quarter', 'ربع سکه غیربانکی'),
                    ('gold_abshodeh', 'طلای آبشده'),
                ],
                db_index=True,
                help_text='کد یکتای محصول برای شناسایی',
                max_length=20,
                unique=True,
                verbose_name='کد محصول',
            ),
        ),
    ]
