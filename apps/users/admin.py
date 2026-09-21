from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    ParentProfile,
    ParentStudent,
    SchoolHealthRecord,
    StudentDocument,
    StudentProfile,
    StudentTransferHistory,
    TeacherProfile,
    User,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "first_name", "last_name", "role", "school", "is_active")
    list_filter = ("role", "is_active", "school")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("MaktabIQ", {"fields": ("role", "phone", "school", "telegram_chat_id", "is_deactivated")}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_code", "user", "school", "class_room")
    search_fields = ("student_code", "user__first_name", "user__last_name")
    list_filter = ("school", "class_room")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("teacher_id", "user", "school", "experience_years")
    search_fields = ("teacher_id", "user__first_name", "user__last_name")


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)


admin.site.register(ParentStudent)
admin.site.register(StudentTransferHistory)
admin.site.register(StudentDocument)
admin.site.register(SchoolHealthRecord)
