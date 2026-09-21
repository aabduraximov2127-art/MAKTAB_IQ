from django.contrib import admin

from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "quarter", "value", "grade_type", "teacher")
    list_filter = ("grade_type", "quarter", "academic_year")
    search_fields = ("student__user__first_name", "student__user__last_name")
