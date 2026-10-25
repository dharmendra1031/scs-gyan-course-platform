from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("exams", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="assessment", name="kind",
            field=models.CharField(choices=[
                ("quiz", "Quiz"), ("test", "Test Series"), ("daily", "Daily Quiz"),
            ], default="quiz", max_length=5),
        ),
        migrations.AddField(
            model_name="assessment", name="daily_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="question", name="explanation",
            field=models.TextField(blank=True),
        ),
    ]
