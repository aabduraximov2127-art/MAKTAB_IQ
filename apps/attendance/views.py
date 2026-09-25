import calendar as pycalendar

import django_filters
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from common.audit import log_action
from common import access
from common.guards import ForbidOutOfScopeMixin, StudentParamGuardMixin

from .models import Attendance, AttendanceStatus, TeacherAttendance
from .permissions import CanAccessTeacherAttendance, CanManageAttendance, CanSubmitParentReason
from .serializers import AttendanceSerializer, ParentReasonSerializer, TeacherAttendanceSerializer


class AttendanceFilterSet(django_filters.FilterSet):
    year = django_filters.NumberFilter(field_name="date", lookup_expr="year")
    month = django_filters.NumberFilter(field_name="date", lookup_expr="month")

    class Meta:
        model = Attendance
        fields = ["student", "class_room", "subject", "date", "status"]


class AttendanceViewSet(StudentParamGuardMixin, ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [CanManageAttendance]
    filterset_class = AttendanceFilterSet
    search_fields = ["student__user__first_name", "student__user__last_name"]

    def get_queryset(self):
        qs = Attendance.objects.select_related("student__user", "class_room", "subject")
        return access.attendance_scope(self.request.user, qs)

    def perform_create(self, serializer):
        class_room = serializer.validated_data.get("class_room")
        student = serializer.validated_data.get("student")
        # admin: own school; teacher: a class they are assigned to; class teacher: own class.
        if class_room is None or not access.can_mark_attendance(self.request.user, class_room):
            raise PermissionDenied("Bu sinf davomatini belgilashga ruxsatingiz yo'q.")
        if student is not None and student.class_room_id != class_room.id:
            raise PermissionDenied("Bu o'quvchi ko'rsatilgan sinfda o'qimaydi.")
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        attendance = serializer.save(marked_by=teacher_profile)
        log_action(
            self.request.user,
            "ATTENDANCE_MARKED",
            target=str(attendance.student),
            description=f"{attendance.date}: {attendance.status}",
            request=self.request,
        )
        if attendance.status == AttendanceStatus.ABSENT:
            from apps.notifications.tasks import notify_student_absence

            notify_student_absence.delay(attendance.id)

    def perform_update(self, serializer):
        instance = serializer.instance
        previous_status = instance.status
        class_room = serializer.validated_data.get("class_room", instance.class_room)
        student = serializer.validated_data.get("student", instance.student)
        # Re-pointing a record at another class/student is a new mark in disguise: the same
        # rules as creation apply to the new target.
        if class_room.pk != instance.class_room_id or student.pk != instance.student_id:
            if not access.can_mark_attendance(self.request.user, class_room):
                raise PermissionDenied("Bu sinf davomatini belgilashga ruxsatingiz yo'q.")
            if student.class_room_id != class_room.id:
                raise PermissionDenied("Bu o'quvchi ko'rsatilgan sinfda o'qimaydi.")
        attendance = serializer.save()
        log_action(
            self.request.user,
            "ATTENDANCE_CHANGED",
            target=str(attendance.student),
            description=f"{attendance.date}: {attendance.status}",
            request=self.request,
        )
        # Marking a pupil absent by *correcting* an earlier mark must tell the parents too.
        if attendance.status == AttendanceStatus.ABSENT and previous_status != AttendanceStatus.ABSENT:
            from apps.notifications.tasks import notify_student_absence

            notify_student_absence.delay(attendance.id)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        student_id = request.query_params.get("student")
        month = int(request.query_params.get("month", 0))
        year = int(request.query_params.get("year", 0))
        if not (student_id and month and year):
            return Response(
                {"success": False, "message": "student, month, year kerak", "errors": {}}, status=400
            )

        days_in_month = pycalendar.monthrange(year, month)[1]
        records = self.get_queryset().filter(
            student_id=student_id, date__year=year, date__month=month
        )
        status_by_day = {r.date.day: r.status for r in records}
        days = [{"day": day, "status": status_by_day.get(day)} for day in range(1, days_in_month + 1)]
        return Response({"success": True, "year": year, "month": month, "days": days})

    @action(detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated, CanSubmitParentReason])
    def submit_reason(self, request, pk=None):
        from django.utils import timezone

        attendance = get_object_or_404(Attendance, pk=pk)
        self.check_object_permissions(request, attendance)
        serializer = ParentReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance.parent_reason = serializer.validated_data["parent_reason"]
        attendance.parent_reason_submitted_at = timezone.now()
        attendance.save(update_fields=["parent_reason", "parent_reason_submitted_at"])
        return Response(AttendanceSerializer(attendance).data)


class TeacherAttendanceViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = TeacherAttendanceSerializer
    permission_classes = [CanAccessTeacherAttendance]
    filterset_fields = ["teacher", "date", "status"]

    def get_queryset(self):
        qs = TeacherAttendance.objects.select_related("teacher__user")
        return access.teacher_attendance_scope(self.request.user, qs)

    def _notify_if_absent(self, attendance):
        if attendance.status == AttendanceStatus.ABSENT:
            from apps.notifications.tasks import notify_teacher_absence

            notify_teacher_absence.delay(attendance.id)

    def perform_create(self, serializer):
        teacher = serializer.validated_data.get("teacher")
        if teacher is not None and not access.same_school_or_unassigned(self.request.user, teacher.school_id):
            raise PermissionDenied("Boshqa maktab o'qituvchisining davomatini boshqara olmaysiz.")
        attendance = serializer.save()
        log_action(
            self.request.user,
            "TEACHER_ATTENDANCE_MARKED",
            target=str(attendance.teacher),
            description=f"{attendance.date}: {attendance.status}",
            request=self.request,
        )
        self._notify_if_absent(attendance)

    def perform_update(self, serializer):
        attendance = serializer.save()
        log_action(
            self.request.user,
            "TEACHER_ATTENDANCE_CHANGED",
            target=str(attendance.teacher),
            description=f"{attendance.date}: {attendance.status}",
            request=self.request,
        )
        self._notify_if_absent(attendance)
