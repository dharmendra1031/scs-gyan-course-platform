import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("pages", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="contactenquiry",
            name="status",
            field=models.CharField(
                max_length=16, default="new",
                choices=[("new", "New"), ("in_progress", "In progress"), ("resolved", "Resolved")],
            ),
        ),
        migrations.AddField(
            model_name="contactenquiry",
            name="internal_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="contactenquiry",
            name="follow_up_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contactenquiry",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
