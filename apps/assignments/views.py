from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.audit import log_action
from common.permissions import IsStudent, user_role


def _same_school_or_denied(request, view, school_id):
    role = user_role(request.user)
    if role == "ADMIN" and (not request.user.school_id or request.user.school_id != school_id):
        view.permission_denied(request)

from .models import Assignment, AssignmentSubmission
from .permissions import CanManageAssignment
from .serializers import (
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
    SubmissionGradeSerializer,
)


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [CanManageAssignment]
    filterset_fields = ["lesson", "teacher"]

    def get_queryset(self):
        qs = Assignment.objects.select_related("lesson__class_room", "teacher__user")
        role = user_role(self.request.user)
        user = self.request.user

        if role == "ADMIN":
            return qs.filter(lesson__class_room__school=user.school)
        if role == "TEACHER":
            return qs.filter(teacher__user=user)
        if role == "STUDENT":
            return qs.filter(lesson__class_room__students__user=user)
        if role == "PARENT":
            return qs.filter(lesson__class_room__students__parent_links__parent__user=user)
        return qs.none()

    def perform_create(self, serializer):
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        assignment = serializer.save(teacher=teacher_profile)
        log_action(self.request.user, "HOMEWORK_CREATED", target=assignment.title, request=self.request)

        from apps.notifications.tasks import notify_homework_created

        notify_homework_created.delay(assignment.id)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsStudent])
    def submit(self, request, pk=None):
        assignment = get_object_or_404(Assignment, pk=pk)
        student_profile = getattr(request.user, "student_profile", None)
        if student_profile is None:
            return Response(
                {"success": False, "message": "Student profile topilmadi", "errors": {}}, status=400
            )

        is_late = timezone.now() > assignment.deadline
        submission, _created = AssignmentSubmission.objects.update_or_create(
            assignment=assignment,
            student=student_profile,
            defaults={
                "answer": request.data.get("answer", ""),
                "attachment": request.data.get("attachment"),
                "status": AssignmentSubmission.Status.LATE if is_late else AssignmentSubmission.Status.SUBMITTED,
            },
        )
        return Response(AssignmentSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class AssignmentSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [CanManageAssignment]
    filterset_fields = ["assignment", "student", "status"]

    def get_queryset(self):
        qs = AssignmentSubmission.objects.select_related("assignment__teacher__user", "student__user")
        role = user_role(self.request.user)
        user = self.request.user

        if role == "ADMIN":
            return qs.filter(assignment__lesson__class_room__school=user.school)
        if role == "TEACHER":
            return qs.filter(assignment__teacher__user=user)
        if role == "STUDENT":
            return qs.filter(student__user=user)
        if role == "PARENT":
            return qs.filter(student__parent_links__parent__user=user)
        return qs.none()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def grade(self, request, pk=None):
        submission = get_object_or_404(AssignmentSubmission, pk=pk)
        role = user_role(request.user)
        if role == "ADMIN":
            _same_school_or_denied(request, self, submission.assignment.lesson.class_room.school_id)
        elif submission.assignment.teacher.user_id != request.user.id:
            self.permission_denied(request)

        serializer = SubmissionGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission.score = serializer.validated_data["score"]
        submission.status = AssignmentSubmission.Status.GRADED
        submission.save(update_fields=["score", "status"])
        return Response(AssignmentSubmissionSerializer(submission).data)
