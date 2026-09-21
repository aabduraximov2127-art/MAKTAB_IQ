from django.contrib import admin

from .models import Attendance, TeacherAttendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "class_room", "date", "status")
    list_filter = ("status", "date")
    search_fields = ("student__user__first_name", "student__user__last_name")


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ("teacher", "date", "status")
    list_filter = ("status", "date")
