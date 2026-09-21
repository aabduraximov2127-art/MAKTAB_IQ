from django.contrib import admin

from .models import LibraryMaterial


@admin.register(LibraryMaterial)
class LibraryMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "material_type", "subject", "author", "uploaded_by")
    list_filter = ("material_type", "subject")
    search_fields = ("title", "author")
