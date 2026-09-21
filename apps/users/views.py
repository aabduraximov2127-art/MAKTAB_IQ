from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework.exceptions import PermissionDenied

from common.audit import get_client_ip, log_action
from common.permissions import IsAdmin, IsAdminOrTeacher, IsStaff, user_role

from .models import (
    ParentProfile,
    SchoolHealthRecord,
    StudentDocument,
    StudentProfile,
    StudentTransferHistory,
    TeacherProfile,
)
from .permissions import (
    CanAccessStudentProfile,
    CanEditStudentProfile,
    CanTransferStudent,
    CanViewSensitiveStudentData,
    IsSelfOrAdmin,
)
from .serializers import (
    EmptySerializer,
    LogoutSerializer,
    ParentProfileSerializer,
    PasswordResetSerializer,
    RegisterStudentSerializer,
    SchoolHealthRecordSerializer,
    StudentDocumentSerializer,
    StudentProfileSerializer,
    StudentProfileUpdateSerializer,
    StudentTransferHistorySerializer,
    StudentTransferRequestSerializer,
    TeacherProfileSerializer,
    UserSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        username = request.data.get("username")
        success = response.status_code == 200
        user = User.objects.filter(username=username).first()
        if user is not None:
            from common.models import LoginHistory

            LoginHistory.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                success=success,
            )
        return response


class RefreshView(TokenRefreshView):
    pass


class LogoutView(APIView):
    serializer_class = LogoutSerializer

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": "Logged out"}, status=status.HTTP_205_RESET_CONTENT)


class RegisterStudentView(generics.CreateAPIView):
    serializer_class = RegisterStudentSerializer
    permission_classes = [IsAdminOrTeacher]

    def perform_create(self, serializer):
        requester = self.request.user
        if user_role(requester) == "ADMIN":
            # School Admin/Director may only ever create students inside their own
            # school — TEACHER's create flow (business logic unchanged) skips this.
            school = serializer.validated_data.get("school")
            if school is not None and school.id != requester.school_id:
                raise PermissionDenied("Boshqa maktab uchun student yarata olmaysiz.")
            class_room = serializer.validated_data.get("class_room")
            if class_room is not None and class_room.school_id != requester.school_id:
                raise PermissionDenied("Boshqa maktabning classiga student biriktira olmaysiz.")
            serializer.validated_data["school"] = requester.school
        user = serializer.save()
        log_action(
            self.request.user,
            action="STUDENT_REGISTERED",
            target=user.username,
            description="New student account created",
            request=self.request,
        )


def _deny_cross_school(request, target_user):
    """ADMIN may only manage accounts in their own school; SUPERADMIN is unrestricted."""
    if user_role(request.user) == "ADMIN" and target_user.school_id != request.user.school_id:
        raise PermissionDenied("Boshqa maktab foydalanuvchisini boshqara olmaysiz.")


class AccountActivateView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = EmptySerializer

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        _deny_cross_school(request, user)
        user.is_active = True
        user.is_deactivated = False
        user.save(update_fields=["is_active", "is_deactivated"])
        log_action(request.user, "USER_ACTIVATED", target=user.username, request=request)
        return Response({"success": True, "message": "Account activated"})


class AccountDeactivateView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = EmptySerializer

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        _deny_cross_school(request, user)
        user.is_active = False
        user.is_deactivated = True
        user.save(update_fields=["is_active", "is_deactivated"])
        log_action(request.user, "USER_DEACTIVATED", target=user.username, request=request)
        return Response({"success": True, "message": "Account deactivated"})


class PasswordResetView(APIView):
    """Admin resets another user's password. Students cannot change their own."""

    permission_classes = [IsAdmin]
    serializer_class = PasswordResetSerializer

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        _deny_cross_school(request, user)
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        log_action(request.user, "PASSWORD_RESET", target=user.username, request=request)
        return Response({"success": True, "message": "Password reset"})


# ---------------------------------------------------------------------------
# Users / profiles
# ---------------------------------------------------------------------------
class MeView(APIView):
    serializer_class = UserSerializer

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class TelegramLinkCodeView(APIView):
    """Generates a short-lived code the user sends to the Telegram bot as `/link <code>`
    to bind their Telegram account for notifications."""

    serializer_class = EmptySerializer

    def post(self, request):
        import random

        from django.core.cache import cache

        code = f"{random.randint(0, 999999):06d}"
        cache.set(f"telegram_link:{code}", request.user.id, timeout=600)
        return Response({"success": True, "code": code, "expires_in": 600})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    search_fields = ["username", "first_name", "last_name", "email"]
    filterset_fields = ["role", "school", "is_active"]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        if user_role(self.request.user) == "ADMIN":
            return qs.filter(school=self.request.user.school)
        return qs


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditStudentProfile]
    search_fields = ["user__first_name", "user__last_name", "student_code"]
    filterset_fields = ["class_room", "school"]

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return StudentProfileUpdateSerializer
        return StudentProfileSerializer

    def get_queryset(self):
        qs = StudentProfile.objects.select_related("user", "class_room", "school")
        if self.action != "list":
            # Detail actions rely on object-level permission checks (CanAccessStudentProfile)
            # so that unauthorized access returns 403 instead of leaking existence via 404.
            return qs

        user = self.request.user
        role = user_role(user)

        if role == "SUPERADMIN":
            return qs
        if role == "ADMIN":
            return qs.filter(school=user.school)
        if role == "STUDENT":
            # A student may browse their own classmates (needed to start a class chat),
            # but object-level retrieve (CanAccessStudentProfile) still stays self-only.
            class_room_id = getattr(getattr(user, "student_profile", None), "class_room_id", None)
            if class_room_id:
                return qs.filter(class_room_id=class_room_id)
            return qs.filter(user=user)
        if role == "PARENT":
            return qs.filter(parent_links__parent__user=user).distinct()
        if role == "TEACHER":
            return (
                qs.filter(class_room__lessons__teacher__user=user) | qs.filter(class_room__curator__user=user)
            ).distinct()
        return qs.none()

    def get_permissions(self):
        if self.action in {"retrieve", "list", "me"}:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        if not CanAccessStudentProfile().has_object_permission(self.request, self, obj):
            self.permission_denied(self.request)
        return obj

    @action(detail=False, methods=["get"])
    def me(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        return Response(self.get_serializer(profile).data)

    @action(detail=True, methods=["post"], permission_classes=[CanTransferStudent])
    def transfer(self, request, pk=None):
        student = get_object_or_404(StudentProfile, pk=pk)
        serializer = StudentTransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_class = serializer.validated_data["new_class"]
        old_class = student.class_room

        if user_role(request.user) == "ADMIN":
            # School Admin/Director may only transfer their own school's students,
            # and only into a class that also belongs to their own school.
            admin_school_id = request.user.school_id
            if student.school_id != admin_school_id or new_class.school_id != admin_school_id:
                self.permission_denied(request)

        student.class_room = new_class
        student.save(update_fields=["class_room"])

        history = StudentTransferHistory.objects.create(
            student=student,
            old_class=old_class,
            new_class=new_class,
            reason=serializer.validated_data.get("reason", ""),
            transferred_by=request.user,
        )
        log_action(
            request.user,
            "STUDENT_TRANSFER",
            target=student.student_code,
            description=f"{old_class} -> {new_class}",
            request=request,
        )
        return Response(StudentTransferHistorySerializer(history).data, status=status.HTTP_201_CREATED)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.select_related("user", "school").prefetch_related("subjects")
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["user__first_name", "user__last_name", "teacher_id"]
    filterset_fields = ["school", "subjects"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = user_role(self.request.user)
        # STUDENT only sees teachers actually teaching their class (subject teachers
        # or curator). Every other role keeps the existing unrestricted behavior.
        if role == "STUDENT":
            student_profile = getattr(self.request.user, "student_profile", None)
            class_room_id = getattr(student_profile, "class_room_id", None)
            if class_room_id is None:
                return qs.none()
            return (
                qs.filter(lessons__class_room_id=class_room_id)
                | qs.filter(curated_classes__id=class_room_id)
            ).distinct()
        # ADMIN (School Admin/Director) is confined to their own school; SUPERADMIN,
        # TEACHER and PARENT keep the existing unrestricted behavior.
        if role == "ADMIN":
            return qs.filter(school=self.request.user.school)
        return qs

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        profile = get_object_or_404(TeacherProfile, user=request.user)
        return Response(self.get_serializer(profile).data)


class ParentViewSet(viewsets.ModelViewSet):
    queryset = ParentProfile.objects.select_related("user")
    serializer_class = ParentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        role = user_role(self.request.user)
        if role == "SUPERADMIN":
            return super().get_queryset()
        if role == "ADMIN":
            return super().get_queryset().filter(user__school=self.request.user.school)
        if role == "PARENT":
            return super().get_queryset().filter(user=self.request.user)
        return ParentProfile.objects.none()

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        profile = get_object_or_404(ParentProfile, user=request.user)
        return Response(self.get_serializer(profile).data)


class StudentTransferHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentTransferHistorySerializer
    permission_classes = [IsAdminOrTeacher]
    filterset_fields = ["student"]

    def get_queryset(self):
        return StudentTransferHistory.objects.select_related("student", "old_class", "new_class")


class StudentDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["student", "document_type"]

    def get_queryset(self):
        role = user_role(self.request.user)
        qs = StudentDocument.objects.select_related("student__user")
        if role in {"ADMIN", "SUPERADMIN"}:
            return qs
        if role == "STUDENT":
            return qs.filter(student__user=self.request.user)
        if role == "PARENT":
            return qs.filter(student__parent_links__parent__user=self.request.user)
        return qs.none()

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class SchoolHealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolHealthRecordSerializer
    permission_classes = [CanViewSensitiveStudentData]
    filterset_fields = ["student"]

    def get_queryset(self):
        return SchoolHealthRecord.objects.select_related("student__user")

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
