from django.contrib import admin

from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("class_room", "subject", "teacher", "room", "date", "start_time", "end_time")
    list_filter = ("date", "class_room")
