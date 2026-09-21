from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import TimeStampedModel
from common.validators import validate_document_extension, validate_file_size


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadmin"
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        PARENT = "PARENT", "Parent"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    school = models.ForeignKey(
        "schools.School", on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )
    telegram_chat_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    is_deactivated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class StudentProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    school = models.ForeignKey("schools.School", on_delete=models.SET_NULL, null=True, related_name="students")
    class_room = models.ForeignKey(
        "classes.ClassRoom", on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to="students/photos/", null=True, blank=True)
    student_code = models.CharField(max_length=30, unique=True)

    class Meta:
        indexes = [models.Index(fields=["student_code"])]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_code})"


class TeacherProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    school = models.ForeignKey("schools.School", on_delete=models.SET_NULL, null=True, related_name="teachers")
    teacher_id = models.CharField(max_length=30, unique=True)
    subjects = models.ManyToManyField("subjects.Subject", related_name="teachers", blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    avatar = models.ImageField(upload_to="teachers/avatars/", null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.teacher_id})"


class ParentProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")

    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"


class ParentStudent(TimeStampedModel):
    class Relation(models.TextChoices):
        FATHER = "FATHER", "Father"
        MOTHER = "MOTHER", "Mother"
        GUARDIAN = "GUARDIAN", "Guardian"

    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name="children_links")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="parent_links")
    relation = models.CharField(max_length=20, choices=Relation.choices, default=Relation.GUARDIAN)

    class Meta:
        unique_together = ("parent", "student")

    def __str__(self):
        return f"{self.parent} -> {self.student}"


class StudentTransferHistory(TimeStampedModel):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="transfer_history")
    old_class = models.ForeignKey(
        "classes.ClassRoom", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    new_class = models.ForeignKey(
        "classes.ClassRoom", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    reason = models.TextField(blank=True)
    transferred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transferred_at"]

    def __str__(self):
        return f"{self.student} : {self.old_class} -> {self.new_class}"


class StudentDocument(TimeStampedModel):
    class DocumentType(models.TextChoices):
        SCHOOL_DOCUMENT = "SCHOOL_DOCUMENT", "School document"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        REGISTRATION = "REGISTRATION", "Registration document"
        OTHER = "OTHER", "Other"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DocumentType.choices, default=DocumentType.OTHER)
    file = models.FileField(
        upload_to="students/documents/", validators=[validate_file_size, validate_document_extension]
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    def __str__(self):
        return f"{self.student} - {self.document_type}"


class SchoolHealthRecord(TimeStampedModel):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name="health_record")
    blood_type = models.CharField(max_length=10, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")

    def __str__(self):
        return f"Health record: {self.student}"
