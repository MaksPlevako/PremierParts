from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="supplier_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                editable=False,
                max_digits=10,
                null=True,
                verbose_name="остання ціна постачальника, ₴",
            ),
        ),
    ]
