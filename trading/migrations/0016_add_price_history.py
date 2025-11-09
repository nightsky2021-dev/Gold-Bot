# Generated manually for PriceHistory model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0015_product_base_price_api_product_buy_margin_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_price_api', models.DecimalField(decimal_places=0, help_text='قیمت دریافتی از API (ریال به ازای هر گرم)', max_digits=12, verbose_name='قیمت پایه API')),
                ('buy_price', models.DecimalField(decimal_places=0, help_text='قیمت خرید از مشتری (ریال)', max_digits=12, verbose_name='قیمت خرید')),
                ('sell_price', models.DecimalField(decimal_places=0, help_text='قیمت فروش به مشتری (ریال)', max_digits=12, verbose_name='قیمت فروش')),
                ('buy_margin', models.DecimalField(decimal_places=0, help_text='مارجین خرید در زمان ثبت قیمت', max_digits=12, verbose_name='مارجین خرید')),
                ('sell_margin', models.DecimalField(decimal_places=0, help_text='مارجین فروش در زمان ثبت قیمت', max_digits=12, verbose_name='مارجین فروش')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='زمان ثبت این قیمت', verbose_name='تاریخ ثبت')),
                ('product', models.ForeignKey(help_text='محصولی که قیمتش ثبت شده است', on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='trading.product', verbose_name='محصول')),
            ],
            options={
                'verbose_name': 'تاریخچه قیمت',
                'verbose_name_plural': 'تاریخچه قیمت\u200cها',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['product', '-created_at'], name='trading_pri_product_idx'),
                    models.Index(fields=['-created_at'], name='trading_pri_created_idx'),
                ],
            },
        ),
    ]
