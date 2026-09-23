from django.contrib.auth import password_validation
from rest_framework import serializers

from apps.classes.models import ClassRoom
from apps.schools.models import School
from common.permissions import user_role
from common.validators import normalize_uz_phone

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


class PhoneValidationMixin:
    """Stores phone numbers in the canonical +998XXXXXXXXX form."""

    def validate_phone(self, value):
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            return normalize_uz_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class UserSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    telegram_linked = serializers.SerializerMethodField()

    def get_telegram_linked(self, obj):
        return bool(obj.telegram_chat_id)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "school",
            "is_active",
            "is_deactivated",
            "date_joined",
            "telegram_linked",
        )
        read_only_fields = ("id", "role", "is_deactivated", "date_joined", "telegram_linked")


class RegisterStudentSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    age = serializers.IntegerField(write_only=True, required=False)
    passport_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    photo = serializers.ImageField(write_only=True, required=False)
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(), write_only=True, required=False
    )
    class_room = serializers.PrimaryKeyRelatedField(
        queryset=ClassRoom.objects.all(), write_only=True, required=False
    )
    student_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "age",
            "passport_number",
            "photo",
            "school",
            "class_room",
            "student_code",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        profile_fields = {
            "age": validated_data.pop("age", None),
            "passport_number": validated_data.pop("passport_number", ""),
            "photo": validated_data.pop("photo", None),
            "school": validated_data.pop("school", None),
            "class_room": validated_data.pop("class_room", None),
            "student_code": validated_data.pop("student_code"),
        }
        password = validated_data.pop("password")
        user = User(role=User.Role.STUDENT, **validated_data)
        user.set_password(password)
        user.save()
        StudentProfile.objects.create(user=user, **profile_fields)
        return user


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class_room_name = serializers.CharField(source="class_room.name", read_only=True, default=None)

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "user",
            "school",
            "class_room",
            "class_room_name",
            "age",
            "passport_number",
            "photo",
            "student_code",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request is not None:
            role = user_role(request.user)
            can_see_sensitive = role in {"ADMIN", "SUPERADMIN"} or request.user.has_perm(
                "users.view_sensitive_student_data"
            )
            if not can_see_sensitive:
                data.pop("passport_number", None)
        return data


class StudentProfileUpdateSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    """Used for PATCH/PUT by ADMIN/SUPERADMIN/TEACHER/PARENT (see CanEditStudentProfile).
    Deliberately excludes school/class_room/student_code/passport_number — class changes
    only ever happen through the `transfer` action, and identifiers stay admin-managed."""

    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    phone = serializers.CharField(source="user.phone", required=False, allow_blank=True)

    class Meta:
        model = StudentProfile
        fields = ("id", "first_name", "last_name", "phone", "age", "photo")
        read_only_fields = ("id",)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save(update_fields=list(user_data.keys()))
        return super().update(instance, validated_data)


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = (
            "id",
            "user",
            "school",
            "teacher_id",
            "subjects",
            "experience_years",
            "avatar",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ParentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = ParentProfile
        fields = ("id", "user", "children", "created_at")
        read_only_fields = ("id", "created_at")

    def get_children(self, obj):
        links = obj.children_links.select_related("student__user")
        return StudentProfileSerializer(
            [link.student for link in links], many=True, context=self.context
        ).data


class ParentStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentStudent
        fields = ("id", "parent", "student", "relation", "created_at")
        read_only_fields = ("id", "created_at")


class StudentTransferHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentTransferHistory
        fields = (
            "id",
            "student",
            "old_class",
            "new_class",
            "reason",
            "transferred_by",
            "transferred_at",
        )
        read_only_fields = ("id", "transferred_by", "transferred_at")


class StudentTransferRequestSerializer(serializers.Serializer):
    new_class = serializers.PrimaryKeyRelatedField(queryset=ClassRoom.objects.all())
    reason = serializers.CharField(required=False, allow_blank=True)


class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = ("id", "student", "document_type", "file", "uploaded_by", "created_at")
        read_only_fields = ("id", "uploaded_by", "created_at")


class SchoolHealthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolHealthRecord
        fields = (
            "id",
            "student",
            "blood_type",
            "allergies",
            "chronic_conditions",
            "notes",
            "updated_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "updated_by", "created_at", "updated_at")


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class EmptySerializer(serializers.Serializer):
    """Used for endpoints that take no request body (Swagger documentation only)."""
