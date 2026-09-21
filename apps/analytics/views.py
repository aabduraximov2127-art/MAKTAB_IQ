from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import StudentProfile
from common.permissions import IsAdmin, user_role

from .serializers import AdminAnalyticsResponseSerializer, StudentProgressResponseSerializer
from .services import compute_admin_analytics, compute_student_progress


class StudentProgressView(APIView):
    serializer_class = StudentProgressResponseSerializer

    def get(self, request):
        student_id = request.query_params.get("student")
        role = user_role(request.user)

        if student_id:
            student = get_object_or_404(StudentProfile, pk=student_id)
        elif role == "STUDENT":
            student = get_object_or_404(StudentProfile, user=request.user)
        else:
            return Response(
                {"success": False, "message": "student parametri kerak", "errors": {}}, status=400
            )

        if role == "STUDENT" and student.user_id != request.user.id:
            self.permission_denied(request)
        if role == "PARENT" and not student.parent_links.filter(parent__user=request.user).exists():
            self.permission_denied(request)
        if role == "TEACHER" and not (
            student.class_room
            and (
                (student.class_room.curator_id and student.class_room.curator.user_id == request.user.id)
                or student.class_room.lessons.filter(teacher__user=request.user).exists()
            )
        ):
            self.permission_denied(request)

        progress = compute_student_progress(student)
        return Response({"success": True, "student": student.id, **progress})


class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminAnalyticsResponseSerializer

    def get(self, request):
        if user_role(request.user) == "ADMIN":
            # School Admin/Director statistics are always their own school's —
            # the ?school= override is a SUPERADMIN-only capability.
            school_id = getattr(request.user, "school_id", None)
        else:
            school_id = request.query_params.get("school") or getattr(request.user, "school_id", None)
        school = None
        if school_id:
            from apps.schools.models import School

            school = get_object_or_404(School, pk=school_id)
        data = compute_admin_analytics(school=school)
        return Response({"success": True, **data})
