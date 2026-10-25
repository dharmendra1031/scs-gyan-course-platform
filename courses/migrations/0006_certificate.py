import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0005_seo")]

    operations = [
        migrations.CreateModel(
            name="CourseCertificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("issued_at", models.DateTimeField(auto_now_add=True)),
                ("enrollment", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="certificate", to="courses.enrollment",
                )),
            ],
            options={"ordering": ["-issued_at"]},
        ),
    ]
