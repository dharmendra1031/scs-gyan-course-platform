from django.urls import reverse

from .models import StudentNotification


def notify(student, event_key, title, message, url_name="dashboard", args=None):
    return StudentNotification.objects.get_or_create(
        student=student,
        event_key=event_key,
        defaults={
            "title": title,
            "message": message,
            "link": reverse(url_name, args=args),
        },
    )
