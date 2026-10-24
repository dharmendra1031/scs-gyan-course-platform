from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    dependencies = [("courses", "0006_certificate")]

    operations = [
        migrations.AddField(
            model_name="order", name="refunded_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order", name="refund_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(refunded_amount__gte=0), name="order_refund_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(refunded_amount__lte=F("amount")), name="order_refund_lte_amount",
            ),
        ),
    ]
