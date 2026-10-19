from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=130, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Course(models.Model):
    class Mode(models.TextChoices):
        RECORDED = "recorded", "Recorded"
        LIVE = "live", "Live Online"
        CLASSROOM = "classroom", "Classroom"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="courses")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.CharField(max_length=320)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to="courses/", blank=True)
    mode = models.CharField(max_length=12, choices=Mode.choices, default=Mode.RECORDED)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration = models.CharField(max_length=80, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=0), name="course_price_nonnegative")]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})
