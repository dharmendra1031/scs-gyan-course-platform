import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=130, unique=True)),
            ],
            options={"verbose_name_plural": "Categories", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("summary", models.CharField(max_length=320)),
                ("description", models.TextField()),
                ("thumbnail", models.ImageField(blank=True, upload_to="courses/")),
                ("mode", models.CharField(choices=[("recorded", "Recorded"), ("live", "Live Online"), ("classroom", "Classroom")], default="recorded", max_length=12)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ("duration", models.CharField(blank=True, max_length=80)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="courses", to="courses.category")),
            ],
            options={"ordering": ["-created_at"], "constraints": [models.CheckConstraint(condition=models.Q(price__gte=0), name="course_price_nonnegative")]},
        ),
    ]
