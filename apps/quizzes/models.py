from django.db import models

from common.models import TimeStampedModel


class Quiz(TimeStampedModel):
    title = models.CharField(max_length=255)
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="quizzes")
    class_room = models.ForeignKey("classes.ClassRoom", on_delete=models.CASCADE, related_name="quizzes")
    teacher = models.ForeignKey("users.TeacherProfile", on_delete=models.CASCADE, related_name="quizzes")
    deadline = models.DateTimeField()
    time_limit_minutes = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_points(self):
        return sum(self.questions.values_list("points", flat=True))


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    options = models.JSONField(help_text='["variant A", "variant B", ...]')
    correct_answer = models.PositiveSmallIntegerField(help_text="Index of correct option in `options`")
    points = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.question[:50]


class QuizAttempt(TimeStampedModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey("users.StudentProfile", on_delete=models.CASCADE, related_name="quiz_attempts")
    answers = models.JSONField(help_text='{"<question_id>": <selected_index>}')
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("quiz", "student")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} - {self.quiz}: {self.score}/{self.max_score}"
