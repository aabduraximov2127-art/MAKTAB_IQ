from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers as drf_serializers, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from common import access, rbac
from common.permissions import require
from common.rbac import TAKE_QUIZ, VIEW_ALL_QUIZZES
from common.guards import ForbidOutOfScopeMixin, StudentParamGuardMixin

from .models import Question, Quiz, QuizAttempt
from .permissions import CanAccessQuiz, can_write_quiz
from .serializers import (
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizAttemptSubmitSerializer,
    QuizSerializer,
)


class QuizViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [CanAccessQuiz]
    filterset_fields = ["subject", "class_room", "teacher"]

    def get_queryset(self):
        qs = Quiz.objects.select_related("subject", "class_room", "teacher__user").prefetch_related("questions")
        return access.quizzes_scope(self.request.user, qs)

    def get_permissions(self):
        if self.action == "submit":
            return [permissions.IsAuthenticated(), require(TAKE_QUIZ)()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user
        class_room = serializer.validated_data["class_room"]
        subject = serializer.validated_data["subject"]
        # admin: own school; teacher: a class they are assigned to and a subject they teach
        if rbac.has_perm(user, VIEW_ALL_QUIZZES):
            allowed = access.same_school(user, class_room.school_id)
        else:
            allowed = access.assigned_to_class(user, class_room) and access.teaches_subject(user, subject)
        if not allowed:
            raise PermissionDenied("Bu sinf va fan uchun test yaratishga ruxsatingiz yo'q.")
        teacher_profile = getattr(user, "teacher_profile", None)
        if teacher_profile is None:
            raise drf_serializers.ValidationError({"teacher": "Test yaratish uchun o'qituvchi profili kerak."})
        serializer.save(teacher=teacher_profile)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, require(TAKE_QUIZ)])
    def submit(self, request, pk=None):
        quiz = get_object_or_404(Quiz, pk=pk)
        student_profile = getattr(request.user, "student_profile", None)
        if student_profile is None:
            return Response({"success": False, "message": "Student profile topilmadi", "errors": {}}, status=400)
        # a student may only take quizzes set for their own class
        if student_profile.class_room_id != quiz.class_room_id:
            self.permission_denied(request)

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


class QuestionViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    queryset = Question.objects.select_related("quiz")
    serializer_class = QuestionSerializer
    permission_classes = [CanAccessQuiz]
    filterset_fields = ["quiz"]

    def get_queryset(self):
        visible = access.quizzes_scope(self.request.user, Quiz.objects.all())
        return super().get_queryset().filter(quiz__in=visible)

    def perform_create(self, serializer):
        quiz = serializer.validated_data["quiz"]
        if not can_write_quiz(self.request.user, quiz):
            raise PermissionDenied("Bu testga savol qo'shishga ruxsatingiz yo'q.")
        serializer.save()


class QuizAttemptViewSet(StudentParamGuardMixin, ForbidOutOfScopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [CanAccessQuiz]
    filterset_fields = ["quiz", "student"]

    def get_queryset(self):
        qs = QuizAttempt.objects.select_related("quiz", "student__user")
        return access.quiz_attempts_scope(self.request.user, qs)
