from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from common import access, rbac
from common.audit import log_action
from common.permissions import require
from common.rbac import GRADE_SUBMISSIONS, MANAGE_CLASS_HOMEWORK, SUBMIT_HOMEWORK, VIEW_ALL_HOMEWORK
from common.guards import ForbidOutOfScopeMixin, StudentParamGuardMixin

from .models import Assignment, AssignmentSubmission
from .permissions import CanManageAssignment, can_write_assignment
from .serializers import (
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
    SubmissionGradeSerializer,
)


class AssignmentViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [CanManageAssignment]
    filterset_fields = ["lesson", "teacher"]

    def get_queryset(self):
        qs = Assignment.objects.select_related("lesson__class_room", "teacher__user")
        return access.assignments_scope(self.request.user, qs)

    def perform_create(self, serializer):
        lesson = serializer.validated_data["lesson"]
        # Homework hangs off a lesson: only that lesson's teacher, the class teacher of its
        # class, or an admin of the same school may add it.
        if not access.can_manage_lesson_homework(self.request.user, lesson):
            raise PermissionDenied("Bu dars uchun uy vazifasi yaratishga ruxsatingiz yo'q.")
        # An admin has no teacher profile: the homework is recorded under the lesson's teacher.
        teacher_profile = getattr(self.request.user, "teacher_profile", None) or lesson.teacher
        assignment = serializer.save(teacher=teacher_profile)
        log_action(self.request.user, "HOMEWORK_CREATED", target=assignment.title, request=self.request)

        from apps.notifications.tasks import notify_homework_created

        notify_homework_created.delay(assignment.id)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, require(SUBMIT_HOMEWORK)])
    def submit(self, request, pk=None):
        assignment = get_object_or_404(Assignment, pk=pk)
        student_profile = getattr(request.user, "student_profile", None)
        if student_profile is None:
            return Response(
                {"success": False, "message": "Student profile topilmadi", "errors": {}}, status=400
            )
        # a student may only hand in homework given to their own class
        if student_profile.class_room_id != assignment.lesson.class_room_id:
            self.permission_denied(request)

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


class AssignmentSubmissionViewSet(StudentParamGuardMixin, ForbidOutOfScopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [CanManageAssignment]
    filterset_fields = ["assignment", "student", "status"]

    def get_queryset(self):
        qs = AssignmentSubmission.objects.select_related("assignment__teacher__user", "student__user")
        return access.submissions_scope(self.request.user, qs)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, require(GRADE_SUBMISSIONS, MANAGE_CLASS_HOMEWORK)],
    )
    def grade(self, request, pk=None):
        submission = get_object_or_404(AssignmentSubmission, pk=pk)
        # same people who may edit the assignment: its teacher, the class teacher, or an
        # admin of the same school
        if not can_write_assignment(request.user, submission.assignment):
            self.permission_denied(request)

        serializer = SubmissionGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission.score = serializer.validated_data["score"]
        submission.status = AssignmentSubmission.Status.GRADED
        submission.save(update_fields=["score", "status"])
        return Response(AssignmentSubmissionSerializer(submission).data)
