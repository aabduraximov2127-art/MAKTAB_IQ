from django.db import models

from common.models import TimeStampedModel
from common.validators import validate_file_size


class LibraryMaterial(TimeStampedModel):
    class MaterialType(models.TextChoices):
        BOOK = "BOOK", "Book"
        PDF = "PDF", "PDF"
        DOCUMENT = "DOCUMENT", "Document"
        LESSON_MATERIAL = "LESSON_MATERIAL", "Lesson material"
        VIDEO = "VIDEO", "Video"
        LINK = "LINK", "Link"

    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices)
    subject = models.ForeignKey(
        "subjects.Subject", on_delete=models.SET_NULL, null=True, blank=True, related_name="library_materials"
    )
    author = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="library/", null=True, blank=True, validators=[validate_file_size])
    link = models.URLField(blank=True)
    uploaded_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
