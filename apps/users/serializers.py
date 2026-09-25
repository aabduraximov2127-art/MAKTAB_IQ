from django.contrib.auth import password_validation
from django.db import transaction
from rest_framework import serializers

from apps.classes.models import ClassRoom
from apps.schools.models import School
from common import rbac
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


class MeSerializer(UserSerializer):
    """The signed-in user's own payload: ``UserSerializer`` plus everything the frontend needs
    to decide what to show — the *effective* roles (primary + extra + derived class teacher),
    the resulting permission codenames, and the classes they curate."""

    primary_role = serializers.CharField(source="role", read_only=True)
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    curated_classes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("primary_role", "roles", "permissions", "curated_classes")
        read_only_fields = fields

    def get_roles(self, obj):
        roles = rbac.effective_roles(obj)
        return [role for role in rbac.ALL_ROLES if role in roles]

    def get_permissions(self, obj):
        return sorted(rbac.user_permissions(obj))

    def get_curated_classes(self, obj):
        return list(ClassRoom.objects.filter(curator__user=obj).values("id", "name"))


class MeUpdateSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    """What a user may change about *themselves* (needs ``update_own_profile``): name, email
    and phone. Login, role, school and activity flags are never editable here."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")


class AdminAccountCreateSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    """The SuperAdmin creates an administrator account. An admin always belongs to a school."""

    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())

    class Meta:
        model = User
        fields = ("id", "username", "password", "first_name", "last_name", "email", "phone", "school")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.ADMIN, **validated_data)
        user.set_password(password)
        user.save()
        return user


class AdminAccountUpdateSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    """The SuperAdmin edits an administrator: name, contact details and the school they run.
    Login, role and password are not editable here (password reset has its own action)."""

    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), required=False)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "school")


class UserAdminSerializer(UserSerializer):
    """What an administrator sees in the users list: the stored roles (primary first, then
    extra ones held through groups) and any permissions granted to this one user."""

    roles = serializers.SerializerMethodField()
    extra_permissions = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("roles", "extra_permissions")
        read_only_fields = fields

    def get_roles(self, obj):
        extra = [g.name for g in obj.groups.all() if g.name in rbac.STORED_ROLES and g.name != obj.role]
        return [obj.role, *sorted(extra)]

    def get_extra_permissions(self, obj):
        return sorted(p.codename for p in obj.user_permissions.all() if p.codename in rbac.PERMISSIONS)


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
            can_see_sensitive = rbac.has_perm(request.user, rbac.VIEW_SENSITIVE_STUDENT_DATA) or request.user.has_perm(
                "users.view_sensitive_student_data"
            )
            if not can_see_sensitive:
                data.pop("passport_number", None)
        return data


class StudentProfileUpdateSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    """Used for PATCH/PUT by student administrators, the class teacher, a linked parent (or the
    student themself when ``update_own_profile`` was granted) — see CanEditStudentProfile.
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


def _next_teacher_id():
    """T-0001, T-0002, ... — the first free code."""
    number = TeacherProfile.objects.count() + 1
    while TeacherProfile.objects.filter(teacher_id=f"T-{number:04d}").exists():
        number += 1
    return f"T-{number:04d}"


class TeacherProfileSerializer(PhoneValidationMixin, serializers.ModelSerializer):
    """A teacher. Creating one also creates the login (``username`` + ``password`` + name);
    editing one may change the name and contact details, never the login or the password."""

    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False, max_length=150)
    password = serializers.CharField(write_only=True, required=False, validators=[password_validation.validate_password])
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20)
    teacher_id = serializers.CharField(required=False, max_length=30)  # generated when left out

    LOGIN_FIELDS = ("username", "password")
    CONTACT_FIELDS = ("first_name", "last_name", "email", "phone")

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
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
        )
        read_only_fields = ("id", "created_at")

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu login band.")
        User.username_validator(value)
        return value

    def validate_teacher_id(self, value):
        clash = TeacherProfile.objects.filter(teacher_id=value)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError("Bu o'qituvchi kodi band.")
        return value

    def validate(self, attrs):
        if self.instance is None:
            missing = [name for name in ("username", "password", "first_name") if not attrs.get(name)]
            if missing:
                raise serializers.ValidationError({name: "Bu maydon majburiy." for name in missing})
        else:
            forbidden = [name for name in self.LOGIN_FIELDS if name in attrs]
            if forbidden:
                raise serializers.ValidationError(
                    {name: "Login va parol bu yerda o'zgartirilmaydi (parolni tiklash alohida)." for name in forbidden}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        login = {name: validated_data.pop(name) for name in self.LOGIN_FIELDS}
        contact = {name: validated_data.pop(name) for name in self.CONTACT_FIELDS if name in validated_data}
        subjects = validated_data.pop("subjects", [])
        user = User(role=User.Role.TEACHER, school=validated_data.get("school"), username=login["username"], **contact)
        user.set_password(login["password"])
        user.save()
        validated_data.setdefault("teacher_id", _next_teacher_id())
        profile = TeacherProfile.objects.create(user=user, **validated_data)
        profile.subjects.set(subjects)
        return profile

    @transaction.atomic
    def update(self, instance, validated_data):
        contact = {name: validated_data.pop(name) for name in self.CONTACT_FIELDS if name in validated_data}
        if contact:
            for name, value in contact.items():
                setattr(instance.user, name, value)
            instance.user.save(update_fields=list(contact))
        return super().update(instance, validated_data)


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
