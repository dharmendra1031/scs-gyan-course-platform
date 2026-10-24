from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0004_studymaterial")]

    operations = [
        migrations.AddField(
            model_name="course", name="seo_title",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="course", name="seo_description",
            field=models.CharField(blank=True, max_length=320),
        ),
    ]
