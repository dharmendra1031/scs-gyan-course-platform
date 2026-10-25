from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0007_refund_reconciliation")]

    operations = [
        migrations.AddField(
            model_name="course", name="instructor_name",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="course", name="learning_outcomes",
            field=models.TextField(blank=True, help_text="One outcome per line"),
        ),
    ]
