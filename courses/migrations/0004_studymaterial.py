import courses.storage
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0003_gateway")]

    operations = [
        migrations.CreateModel(
            name="StudyMaterial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("description", models.CharField(blank=True, max_length=350)),
                ("file", models.FileField(
                    storage=courses.storage.private_storage,
                    upload_to="course-materials/",
                    validators=[django.core.validators.FileExtensionValidator(["pdf"])],
                )),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="materials", to="courses.course",
                )),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
