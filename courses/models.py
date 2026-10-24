from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from .storage import private_storage


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
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)
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


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=180)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=180)
    position = models.PositiveIntegerField(default=0)
    video_url = models.URLField(blank=True)
    notes = models.FileField(
        upload_to="lesson-notes/",
        storage=private_storage,
        blank=True,
        validators=[FileExtensionValidator(["pdf"])],
    )
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.title


class StudyMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=180)
    description = models.CharField(max_length=350, blank=True)
    file = models.FileField(
        upload_to="course-materials/",
        storage=private_storage,
        validators=[FileExtensionValidator(["pdf"])],
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    student = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="course_orders")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="orders")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    gateway_order_id = models.CharField(max_length=70, blank=True, null=True, unique=True)
    gateway_payment_id = models.CharField(max_length=70, blank=True, null=True, unique=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="unique_student_course_order")]

    def __str__(self):
        return f"Order #{self.pk} - {self.course.title}"


class Enrollment(models.Model):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="enrollments")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="unique_course_enrollment")]

    def __str__(self):
        return f"{self.student} - {self.course}"


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="completed_lessons")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["enrollment", "lesson"], name="unique_lesson_completion")]

    def __str__(self):
        return f"{self.enrollment} - {self.lesson}"
