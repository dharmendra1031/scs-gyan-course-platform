import courses.storage
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Chapter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("position", models.PositiveIntegerField(default=0)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chapters", to="courses.course")),
            ],
            options={"ordering": ["position", "id"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("position", models.PositiveIntegerField(default=0)),
                ("video_url", models.URLField(blank=True)),
                ("notes", models.FileField(blank=True, storage=courses.storage.private_storage, upload_to="lesson-notes/", validators=[django.core.validators.FileExtensionValidator(["pdf"])])),
                ("is_published", models.BooleanField(default=False)),
                ("chapter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="courses.chapter")),
            ],
            options={"ordering": ["position", "id"]},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="courses.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("cancelled", "Cancelled")], default="pending", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="courses.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="course_orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                ("enrollment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="completed_lessons", to="courses.enrollment")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="completions", to="courses.lesson")),
            ],
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(fields=["student", "course"], name="unique_course_enrollment"),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.UniqueConstraint(fields=["student", "course"], name="unique_student_course_order"),
        ),
        migrations.AddConstraint(
            model_name="lessonprogress",
            constraint=models.UniqueConstraint(fields=["enrollment", "lesson"], name="unique_lesson_completion"),
        ),
    ]
