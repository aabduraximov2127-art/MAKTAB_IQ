from django.db import models

from common.models import TimeStampedModel


class Subject(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name/emoji for frontend")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
