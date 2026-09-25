from collections import defaultdict

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.subjects.models import Subject
from apps.users.models import StudentProfile
from common.audit import log_action
from common import access, rbac
from common.rbac import VIEW_ALL_GRADES
from common.guards import ForbidOutOfScopeMixin, StudentParamGuardMixin

from .models import Grade
from .permissions import CanManageGrade
from .serializers import GradeSerializer


class GradeViewSet(StudentParamGuardMixin, ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [CanManageGrade]
    filterset_fields = ["student", "subject", "quarter", "academic_year", "grade_type"]
    search_fields = ["student__user__first_name", "student__user__last_name"]

    def get_queryset(self):
        qs = Grade.objects.select_related("student__user", "subject", "teacher__user", "quarter")
        return access.grades_scope(self.request.user, qs)

    def perform_create(self, serializer):
        requester = self.request.user
        student = serializer.validated_data["student"]
        subject = serializer.validated_data["subject"]
        # admin: own school only. Teacher: the student's class must be one they teach or
        # curate, and the subject one they are assigned to.
        if not access.can_grade(requester, student, subject):
            raise PermissionDenied("Bu o'quvchiga shu fandan baho qo'yishga ruxsatingiz yo'q.")
        teacher_profile = getattr(requester, "teacher_profile", None)
        grade = serializer.save(teacher=teacher_profile)
        log_action(
            requester,
            "GRADE_CREATED",
            target=str(grade.student),
            description=f"{grade.subject}: {grade.value}",
            request=self.request,
        )
        from apps.notifications.tasks import notify_new_grade

        notify_new_grade.delay(grade.id)

    def perform_update(self, serializer):
        requester = self.request.user
        instance = serializer.instance
        # Re-pointing a grade at another student/subject is a new grade in disguise:
        # apply the same rules as creation to the new target.
        student = serializer.validated_data.get("student", instance.student)
        subject = serializer.validated_data.get("subject", instance.subject)
        if (student.pk != instance.student_id or subject.pk != instance.subject_id) and not access.can_grade(
            requester, student, subject
        ):
            raise PermissionDenied("Bahoni boshqa o'quvchi yoki fanga o'tkaza olmaysiz.")
        # A school-wide writer (admin) changing a grade they didn't originally set (e.g. a
        # teacher's entry) is a grade override — permission-gated to their own school
        # (CanManageGrade) and, like every grade change, audit-logged.
        is_override = rbac.has_perm(requester, VIEW_ALL_GRADES) and instance.teacher_id != getattr(
            getattr(requester, "teacher_profile", None), "id", None
        )
        grade = serializer.save()
        log_action(
            requester,
            "GRADE_OVERRIDE" if is_override else "GRADE_CHANGED",
            target=str(grade.student),
            description=f"{grade.subject}: {grade.value}",
            request=self.request,
        )

    @action(detail=False, methods=["get"])
    def annual(self, request):
        student_id = request.query_params.get("student")
        academic_year_id = request.query_params.get("academic_year")
        if not student_id or not academic_year_id:
            return Response(
                {"success": False, "message": "student va academic_year parametrlari kerak", "errors": {}},
                status=400,
            )

        student = get_object_or_404(StudentProfile, pk=student_id)
        grades = self.get_queryset().filter(student=student, academic_year_id=academic_year_id)

        by_subject = defaultdict(lambda: defaultdict(list))
        for grade in grades:
            by_subject[grade.subject_id][grade.quarter.number].append(grade.value)

        results = []
        for subject_id, quarters in by_subject.items():
            subject = Subject.objects.get(pk=subject_id)
            quarter_averages = {
                str(q_num): round(sum(values) / len(values), 2) for q_num, values in quarters.items()
            }
            annual_average = round(sum(quarter_averages.values()) / len(quarter_averages), 2)
            results.append(
                {
                    "subject": subject_id,
                    "subject_name": subject.name,
                    "quarter_averages": quarter_averages,
                    "annual_average": annual_average,
                }
            )

        return Response({"success": True, "results": results})
