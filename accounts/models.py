from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.get_full_name() or self.username


class StudentNotification(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    event_key = models.CharField(max_length=120)
    title = models.CharField(max_length=180)
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=300, default="/account/dashboard/")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["student", "event_key"], name="unique_student_notification_event"),
        ]
