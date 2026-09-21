from django.db import models

from common.models import TimeStampedModel


class School(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="schools/logos/", null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
