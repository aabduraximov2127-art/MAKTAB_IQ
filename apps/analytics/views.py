from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.classes.models import ClassRoom
from apps.schools.models import School
from apps.users.models import StudentProfile
from common import access, rbac
from common.permissions import require
from common.rbac import (
    VIEW_ALL_GRADES,
    VIEW_ASSIGNED_GRADES,
    VIEW_CHILD_GRADES,
    VIEW_CLASS_REPORTS,
    VIEW_OWN_GRADES,
    VIEW_REPORTS,
)

from .serializers import AdminAnalyticsResponseSerializer, StudentProgressResponseSerializer
from .services import compute_admin_analytics, compute_student_progress

PROGRESS_PERMISSIONS = (VIEW_OWN_GRADES, VIEW_CHILD_GRADES, VIEW_ASSIGNED_GRADES, VIEW_CLASS_REPORTS, VIEW_ALL_GRADES)


class StudentProgressView(APIView):
    """One student's progress. The student must be someone the caller may open (themselves,
    their child, a pupil of their class, or — school-wide roles — anyone in their school)."""

    permission_classes = [require(*PROGRESS_PERMISSIONS)]
    serializer_class = StudentProgressResponseSerializer

    def get(self, request):
        student_id = request.query_params.get("student")

        if student_id:
            student = get_object_or_404(StudentProfile, pk=student_id)
        else:
            own = access.student_profile_of(request.user)
            if own is None:
                return Response(
                    {"success": False, "message": "student parametri kerak", "errors": {}}, status=400
                )
            student = own

        if not access.can_view_student(request.user, student):
            self.permission_denied(request)

        progress = compute_student_progress(student)
        return Response({"success": True, "student": student.id, **progress})


class AdminAnalyticsView(APIView):
    """School-level report: ``view_reports`` (admin, director, deputy director, superadmin).
    Everyone except SUPERADMIN gets their *own* school's numbers; only SUPERADMIN may pick
    another school with ``?school=``."""

    permission_classes = [require(VIEW_REPORTS)]
    serializer_class = AdminAnalyticsResponseSerializer

    def get(self, request):
        if rbac.is_global(request.user):
            school_id = request.query_params.get("school") or getattr(request.user, "school_id", None)
        else:
            school_id = getattr(request.user, "school_id", None)
        school = get_object_or_404(School, pk=school_id) if school_id else None
        data = compute_admin_analytics(school=school)
        return Response({"success": True, **data})


class ClassReportView(APIView):
    """Report for one class: every pupil's progress plus class averages.

    A class teacher (``view_class_reports``) may only ask for a class they curate; roles with
    ``view_reports`` may ask for any class of their school (SUPERADMIN: any class)."""

    permission_classes = [require(VIEW_CLASS_REPORTS, VIEW_REPORTS)]
    serializer_class = serializers.Serializer

    def get(self, request):
        class_id = request.query_params.get("class_room")
        if not class_id:
            return Response({"success": False, "message": "class_room parametri kerak", "errors": {}}, status=400)
        class_room = get_object_or_404(ClassRoom, pk=class_id)

        school_wide = rbac.has_perm(request.user, VIEW_REPORTS) and access.same_school(
            request.user, class_room.school_id
        )
        own_class = rbac.has_perm(request.user, VIEW_CLASS_REPORTS) and access.curates(request.user, class_room)
        if not (school_wide or own_class):
            self.permission_denied(request)

        students = StudentProfile.objects.filter(class_room=class_room).select_related("user").order_by("user__last_name")
        rows = [
            {
                "student": student.id,
                "name": student.user.get_full_name() or student.user.username,
                "student_code": student.student_code,
                **compute_student_progress(student),
            }
            for student in students
        ]

        def average(key):
            return round(sum(r[key] for r in rows) / len(rows), 2) if rows else 0

        return Response(
            {
                "success": True,
                "class_room": class_room.id,
                "class_name": class_room.name,
                "student_count": len(rows),
                "average_grade": average("average_grade"),
                "attendance_percentage": average("attendance_percentage"),
                "homework_completion": average("homework_completion"),
                "quiz_average": average("quiz_average"),
                "students": rows,
            }
        )
