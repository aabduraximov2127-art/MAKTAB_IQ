from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsStudent, user_role

from .models import Question, Quiz, QuizAttempt
from .permissions import CanAccessQuiz
from .serializers import (
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizAttemptSubmitSerializer,
    QuizSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [CanAccessQuiz]
    filterset_fields = ["subject", "class_room", "teacher"]

    def get_queryset(self):
        qs = Quiz.objects.select_related("subject", "class_room", "teacher__user").prefetch_related("questions")
        role = user_role(self.request.user)
        user = self.request.user

        if role == "ADMIN":
            return qs
        if role == "TEACHER":
            return qs.filter(teacher__user=user)
        if role == "STUDENT":
            return qs.filter(class_room__students__user=user)
        if role == "PARENT":
            return qs.filter(class_room__students__parent_links__parent__user=user)
        return qs.none()

    def get_permissions(self):
        if self.action == "submit":
            return [permissions.IsAuthenticated(), IsStudent()]
        return super().get_permissions()

    def perform_create(self, serializer):
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        serializer.save(teacher=teacher_profile)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsStudent])
    def submit(self, request, pk=None):
        quiz = get_object_or_404(Quiz, pk=pk)
        student_profile = getattr(request.user, "student_profile", None)
        if student_profile is None:
            return Response({"success": False, "message": "Student profile topilmadi", "errors": {}}, status=400)

        serializer = QuizAttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]

        questions = {q.id: q for q in quiz.questions.all()}
        score = 0
        max_score = sum(q.points for q in questions.values())
        for question_id, selected_index in answers.items():
            question = questions.get(int(question_id))
            if question and question.correct_answer == selected_index:
                score += question.points

        attempt, _created = QuizAttempt.objects.update_or_create(
            quiz=quiz,
            student=student_profile,
            defaults={
                "answers": answers,
                "score": score,
                "max_score": max_score,
                "submitted_at": timezone.now(),
            },
        )
        return Response(QuizAttemptSerializer(attempt).data, status=201)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related("quiz")
    serializer_class = QuestionSerializer
    permission_classes = [CanAccessQuiz]
    filterset_fields = ["quiz"]


class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [CanAccessQuiz]
    filterset_fields = ["quiz", "student"]

    def get_queryset(self):
        qs = QuizAttempt.objects.select_related("quiz", "student__user")
        role = user_role(self.request.user)
        user = self.request.user

        if role == "ADMIN":
            return qs
        if role == "TEACHER":
            return qs.filter(quiz__teacher__user=user)
        if role == "STUDENT":
            return qs.filter(student__user=user)
        if role == "PARENT":
            return qs.filter(student__parent_links__parent__user=user)
        return qs.none()
