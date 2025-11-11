# Generated migration for PriceHistory model

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0015_product_base_price_api_product_buy_margin_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_price_api', models.DecimalField(decimal_places=0, help_text='قیمت دریافتی از API', max_digits=12, verbose_name='قیمت پایه API')),
                ('buy_price', models.DecimalField(decimal_places=0, help_text='قیمت خرید از مشتری', max_digits=12, verbose_name='قیمت خرید')),
                ('sell_price', models.DecimalField(decimal_places=0, help_text='قیمت فروش به مشتری', max_digits=12, verbose_name='قیمت فروش')),
                ('buy_margin', models.DecimalField(decimal_places=0, help_text='مارجین خرید در زمان ثبت', max_digits=12, verbose_name='مارجین خرید')),
                ('sell_margin', models.DecimalField(decimal_places=0, help_text='مارجین فروش در زمان ثبت', max_digits=12, verbose_name='مارجین فروش')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='زمان ثبت این قیمت', verbose_name='زمان ثبت')),
                ('product', models.ForeignKey(help_text='محصول مربوطه', on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='trading.product', verbose_name='محصول')),
            ],
            options={
                'verbose_name': 'تاریخچه قیمت',
                'verbose_name_plural': 'تاریخچه قیمت\u200cها',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.AddIndex(
            model_name='pricehistory',
            index=models.Index(fields=['product', '-recorded_at'], name='trading_pri_product_3d4e5f_idx'),
        ),
        migrations.AddIndex(
            model_name='pricehistory',
            index=models.Index(fields=['-recorded_at'], name='trading_pri_recorde_7f8a9b_idx'),
        ),
    ]
