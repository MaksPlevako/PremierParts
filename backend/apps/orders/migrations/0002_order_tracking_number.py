from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='order', name='tracking_number',
            field=models.CharField(blank=True, max_length=80, verbose_name='номер ТТН'),
        ),
    ]
