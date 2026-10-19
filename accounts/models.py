from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.get_full_name() or self.username
