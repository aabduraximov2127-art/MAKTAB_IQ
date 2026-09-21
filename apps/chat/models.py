from django.db import models

from common.models import TimeStampedModel


class ChatRoom(TimeStampedModel):
    class RoomType(models.TextChoices):
        CLASS_GENERAL = "CLASS_GENERAL", "Class general chat"
        PRIVATE = "PRIVATE", "Private chat"
        TEACHER_STUDENT = "TEACHER_STUDENT", "Teacher-student chat"
        PARENT_TEACHER = "PARENT_TEACHER", "Parent-teacher chat"

    room_type = models.CharField(max_length=20, choices=RoomType.choices)
    name = models.CharField(max_length=255, blank=True)
    class_room = models.ForeignKey(
        "classes.ClassRoom", on_delete=models.CASCADE, null=True, blank=True, related_name="chat_rooms"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or f"{self.room_type} #{self.id}"


class ChatMember(TimeStampedModel):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="chat_memberships")

    class Meta:
        unique_together = ("chat_room", "user")

    def __str__(self):
        return f"{self.user} in {self.chat_room}"


class Message(TimeStampedModel):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="+")
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to="chat/attachments/", null=True, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["chat_room", "created_at"])]

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"
