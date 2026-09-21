from django.contrib import admin

from .models import AcademicYear, ClassRoom, Quarter


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ("academic_year", "number", "start_date", "end_date")
    list_filter = ("academic_year", "number")


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "grade", "academic_year", "curator")
    list_filter = ("school", "grade", "academic_year")
    search_fields = ("name",)
