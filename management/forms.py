from django import forms
from django.utils.text import slugify

from articles.models import Article
from courses.models import Category, Chapter, Course, Lesson, StudyMaterial
from exams.models import Assessment, Choice, Question


class AutomaticSlugForm(forms.ModelForm):
    """Fill missing slugs without modifying explicitly chosen URL slugs."""

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("slug") and cleaned.get("title", cleaned.get("name")):
            cleaned["slug"] = slugify(cleaned.get("title") or cleaned["name"])
        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug")


class CourseForm(forms.ModelForm):
    slug = forms.SlugField(max_length=220, required=False)

    class Meta:
        model = Course
        fields = (
            "category", "title", "slug", "summary", "description",
            "instructor_name", "learning_outcomes", "thumbnail",
            "mode", "duration", "price", "seo_title", "seo_description",
            "is_published",
        )

    def clean_slug(self):
        slug = self.cleaned_data["slug"] or slugify(self.data.get("title", ""))
        if not slug:
            raise forms.ValidationError("Enter a title or course slug.")
        return slug


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ("course", "title", "position")


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("chapter", "title", "position", "video_url", "notes", "is_published")


class MaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ("course", "title", "description", "file", "is_published")


class ArticleForm(forms.ModelForm):
    slug = forms.SlugField(max_length=230, required=False)

    class Meta:
        model = Article
        fields = (
            "title", "slug", "section", "summary", "content",
            "published_at", "seo_title", "seo_description", "is_published",
        )
        widgets = {"published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")}

    def clean_slug(self):
        slug = self.cleaned_data["slug"] or slugify(self.data.get("title", ""))
        if not slug:
            raise forms.ValidationError("Enter a title or article slug.")
        return slug


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ("course", "title", "kind", "daily_date", "duration_minutes", "is_published")
        widgets = {"daily_date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        data = super().clean()
        if data.get("kind") == Assessment.Kind.DAILY and not data.get("daily_date"):
            self.add_error("daily_date", "Daily quizzes require a date.")
        if data.get("is_published"):
            if not self.instance.pk:
                self.add_error("is_published", "Save the draft, add questions, then publish.")
            else:
                questions = self.instance.questions.prefetch_related("choices")
                if not questions.exists():
                    self.add_error("is_published", "Add questions before publishing.")
                for question in questions:
                    answers = list(question.choices.all())
                    if len(answers) < 2 or sum(a.is_correct for a in answers) != 1:
                        self.add_error(
                            "is_published", "Every question needs at least two choices and exactly one correct answer."
                        )
                        break
        return data


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("assessment", "text", "position", "marks", "explanation")

    def clean_marks(self):
        marks = self.cleaned_data["marks"]
        if marks < 1:
            raise forms.ValidationError("Marks must be at least one.")
        return marks


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ("question", "text", "is_correct")

    def clean(self):
        data = super().clean()
        question = data.get("question")
        if question and question.assessment.is_published:
            raise forms.ValidationError("Unpublish the assessment before editing its answers.")
        if question and data.get("is_correct"):
            others = Choice.objects.filter(question=question, is_correct=True)
            if self.instance.pk:
                others = others.exclude(pk=self.instance.pk)
            if others.exists():
                self.add_error("is_correct", "Unmark the existing correct choice first.")
        return data
