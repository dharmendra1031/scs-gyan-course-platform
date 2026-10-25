from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("articles", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="article", name="seo_title",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="article", name="seo_description",
            field=models.CharField(blank=True, max_length=320),
        ),
    ]
