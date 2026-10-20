from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0002_learning")]

    operations = [
        migrations.AddField(
            model_name="order", name="gateway_order_id",
            field=models.CharField(max_length=70, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="order", name="gateway_payment_id",
            field=models.CharField(max_length=70, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="order", name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
