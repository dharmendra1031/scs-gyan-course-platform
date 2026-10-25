import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("courses", "0003_gateway"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Assessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("kind", models.CharField(choices=[("quiz", "Quiz"), ("test", "Test Series")], default="quiz", max_length=4)),
                ("duration_minutes", models.PositiveSmallIntegerField(default=30)),
                ("is_published", models.BooleanField(default=False)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assessments", to="courses.course")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("position", models.PositiveIntegerField(default=0)),
                ("marks", models.PositiveSmallIntegerField(default=1)),
                ("assessment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="exams.assessment")),
            ],
            options={"ordering": ["position", "id"]},
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=500)),
                ("is_correct", models.BooleanField(default=False)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="exams.question")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Attempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("score", models.PositiveIntegerField(default=0)),
                ("total_marks", models.PositiveIntegerField(default=0)),
                ("assessment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attempts", to="exams.assessment")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-started_at"],
                "constraints": [models.UniqueConstraint(fields=("assessment", "student"), name="unique_student_assessment_attempt")],
            },
        ),
        migrations.CreateModel(
            name="AttemptAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="exams.attempt")),
                ("choice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="exams.choice")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="exams.question")),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("attempt", "question"), name="unique_attempt_question_answer")],
            },
        ),
    ]
