import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Article",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220)),
                ("slug", models.SlugField(max_length=230, unique=True)),
                ("section", models.CharField(choices=[("current_affairs", "Current Affairs"), ("editorial", "Editorial"), ("blog", "Blog")], default="current_affairs", max_length=20)),
                ("summary", models.CharField(max_length=350)),
                ("content", models.TextField()),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-published_at", "-id"]},
        ),
    ]
