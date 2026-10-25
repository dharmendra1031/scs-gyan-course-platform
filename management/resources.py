from dataclasses import dataclass

from articles.models import Article
from courses.models import Category, Chapter, Course, Lesson, StudyMaterial
from exams.models import Assessment, Choice, Question

from .forms import (
    ArticleForm, AssessmentForm, CategoryForm, ChapterForm, ChoiceForm,
    CourseForm, LessonForm, MaterialForm, QuestionForm,
)


@dataclass(frozen=True)
class Resource:
    label: str
    model: type
    form: type
    search: tuple[str, ...]
    related: tuple[str, ...] = ()


RESOURCES = {
    "categories": Resource("Categories", Category, CategoryForm, ("name",)),
    "courses": Resource("Courses", Course, CourseForm, ("title", "summary"), ("category",)),
    "chapters": Resource("Chapters", Chapter, ChapterForm, ("title", "course__title"), ("course",)),
    "lessons": Resource("Lessons", Lesson, LessonForm, ("title", "chapter__title"), ("chapter__course",)),
    "materials": Resource("Study Materials", StudyMaterial, MaterialForm, ("title", "course__title"), ("course",)),
    "articles": Resource("Articles", Article, ArticleForm, ("title", "summary")),
    "assessments": Resource("Quizzes & Tests", Assessment, AssessmentForm, ("title", "course__title"), ("course",)),
    "questions": Resource("Questions", Question, QuestionForm, ("text", "assessment__title"), ("assessment",)),
    "choices": Resource("Answer Choices", Choice, ChoiceForm, ("text", "question__text"), ("question__assessment",)),
}
