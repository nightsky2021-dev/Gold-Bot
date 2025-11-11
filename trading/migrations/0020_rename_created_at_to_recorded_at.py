# Generated migration to fix PriceHistory created_at -> recorded_at

from django.db import migrations


def rename_column_forward(apps, schema_editor):
    """Rename created_at to recorded_at in the database."""
    with schema_editor.connection.cursor() as cursor:
        # SQLite doesn't support ALTER COLUMN RENAME directly in older versions
        # We need to check if the column exists first
        cursor.execute("PRAGMA table_info(trading_pricehistory)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'created_at' in columns and 'recorded_at' not in columns:
            # For SQLite, we need to rename using ALTER TABLE
            cursor.execute(
                "ALTER TABLE trading_pricehistory RENAME COLUMN created_at TO recorded_at"
            )


def rename_column_backward(apps, schema_editor):
    """Rename recorded_at back to created_at."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE trading_pricehistory RENAME COLUMN recorded_at TO created_at"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0019_rename_trading_pri_product_3d4e5f_idx_trading_pri_product_c49885_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(rename_column_forward, rename_column_backward),
    ]

