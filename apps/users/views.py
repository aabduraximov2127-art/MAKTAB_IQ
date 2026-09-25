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

from common import access, rbac
from common.audit import get_client_ip, log_action
from common.permissions import RBACPermission, require
from common.rbac import (
    MANAGE_STUDENTS,
    MANAGE_TEACHERS,
    MANAGE_USERS,
    VIEW_ALL_STUDENTS,
    VIEW_ASSIGNED_STUDENTS,
    VIEW_CLASS_STUDENTS,
    VIEW_OWN_PROFILE,
)

from .models import (
    ParentProfile,
    SchoolHealthRecord,
    StudentDocument,
    StudentProfile,
    StudentTransferHistory,
    TeacherProfile,
)
from .access_api import UserAccessMixin
from .permissions import (
    STUDENT_LIST_PERMISSIONS,
    CanAccessStudentProfile,
    CanEditStudentProfile,
    CanTransferStudent,
    CanViewSensitiveStudentData,
    can_manage_user,
)
from .serializers import (
    EmptySerializer,
    LogoutSerializer,
    MeSerializer,
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
    UserAdminSerializer,
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
    permission_classes = [require(MANAGE_STUDENTS)]

    def perform_create(self, serializer):
        requester = self.request.user
        if not rbac.is_global(requester):
            # Every school-bound account (admin) may only ever create students inside its
            # own school; only a global SUPERADMIN can choose any school.
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
    """School-bound admins may only manage accounts of their own school (and never a
    SUPERADMIN); a global SUPERADMIN is unrestricted."""
    if not can_manage_user(request.user, target_user):
        raise PermissionDenied("Bu foydalanuvchini boshqara olmaysiz.")


class AccountActivateView(APIView):
    permission_classes = [require(MANAGE_USERS)]
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
    permission_classes = [require(MANAGE_USERS)]
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

    permission_classes = [require(MANAGE_USERS)]
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
    serializer_class = MeSerializer

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class TelegramLinkCodeView(APIView):
    """Issues a short-lived code the user sends to the Telegram bot (``/link <code>``, or just
    the code) to bind their Telegram account for notifications."""

    serializer_class = EmptySerializer

    def post(self, request):
        from .telegram_link import CODE_TTL, issue_code

        code = issue_code(request.user)
        return Response({"success": True, "code": code, "expires_in": CODE_TTL})


class TelegramStatusView(APIView):
    """Whether the current user's account is connected to Telegram (polled by the website
    while it waits for the user to send the code to the bot)."""

    serializer_class = EmptySerializer

    def get(self, request):
        return Response({"linked": bool(request.user.telegram_chat_id)})


class TelegramUnlinkView(APIView):
    serializer_class = EmptySerializer

    def post(self, request):
        from .telegram_link import unlink_user

        unlink_user(request.user)
        return Response({"success": True, "linked": False})


# ---------------------------------------------------------------------------
# Telegram Mini App auth — Telegram signs `initData` with the bot token, proving which
# Telegram account opened the app. See apps/users/telegram_webapp.py for the signature
# check and apps/users/telegram_link.py for how a chat gets bound to a MaktabIQ account.
# ---------------------------------------------------------------------------
class TelegramAuthView(APIView):
    """Silent sign-in: if this Telegram account is already linked to a MaktabIQ user,
    exchange the (Telegram-signed) initData for that user's JWT — no password needed,
    Telegram already proved who is opening the app. Used every time the Mini App opens."""

    serializer_class = EmptySerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .telegram_webapp import telegram_chat_id_from, verify_init_data

        verified = verify_init_data(request.data.get("init_data", ""))
        if verified is None:
            return Response({"success": False, "message": "initData tasdiqlanmadi"}, status=400)

        chat_id = telegram_chat_id_from(verified)
        user = User.objects.filter(telegram_chat_id=chat_id).first() if chat_id else None
        if user is None or not user.is_active or user.is_deactivated:
            return Response({"linked": False})

        refresh = RefreshToken.for_user(user)
        return Response({"linked": True, "access": str(refresh.access_token), "refresh": str(refresh)})


class TelegramWebAppLoginView(APIView):
    """First-time Mini App sign-in: verifies the initData (proves the Telegram identity)
    *and* a MaktabIQ username/password (proves the account), links the two, and issues
    that user's JWT — after this, TelegramAuthView signs the same chat in silently."""

    serializer_class = EmptySerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        from .telegram_link import bind_chat_id, notify_linked
        from .telegram_webapp import telegram_chat_id_from, verify_init_data

        verified = verify_init_data(request.data.get("init_data", ""))
        if verified is None:
            return Response({"success": False, "message": "initData tasdiqlanmadi"}, status=400)

        chat_id = telegram_chat_id_from(verified)
        if not chat_id:
            return Response({"success": False, "message": "Telegram foydalanuvchisi aniqlanmadi"}, status=400)

        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)

        existing = user or User.objects.filter(username=username).first()
        if existing is not None:
            from common.models import LoginHistory

            LoginHistory.objects.create(
                user=existing,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                success=user is not None,
            )

        if user is None:
            return Response({"success": False, "message": "Login yoki parol xato"}, status=400)
        if not user.is_active or user.is_deactivated:
            return Response({"success": False, "message": "Hisob faol emas"}, status=400)

        already_linked = user.telegram_chat_id == chat_id
        bind_chat_id(user, chat_id)
        if not already_linked:
            notify_linked(user)

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class UserViewSet(UserAccessMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only user directory for user administrators (``manage_users``). Roles and
    permissions are changed through the dedicated actions in ``access_api.py`` — there is
    deliberately no PATCH/PUT that accepts a ``role`` field."""

    serializer_class = UserAdminSerializer
    permission_classes = [require(MANAGE_USERS)]
    search_fields = ["username", "first_name", "last_name", "email"]
    filterset_fields = ["role", "school", "is_active"]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined").prefetch_related("groups", "user_permissions")
        if rbac.is_global(self.request.user):
            return qs
        if not self.request.user.school_id:
            return qs.none()
        # school-bound admins: their own school only, and never SUPERADMIN accounts
        return qs.filter(school=self.request.user.school).exclude(role=rbac.SUPERADMIN)


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
        return access.students_scope(self.request.user, qs)

    def get_permissions(self):
        if self.action == "list":
            return [require(*STUDENT_LIST_PERMISSIONS)()]
        if self.action in {"retrieve", "me"}:
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

        # transfer_students + the right relation to *this* student (own school for admin /
        # director, own class for a class teacher, assigned pupils for a teacher who was
        # explicitly granted the permission) and a destination in the same school.
        if not access.can_transfer_student(request.user, student, new_class):
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
        # Who sees which teachers: administrators/supervisors their school's; a student the
        # teachers of their own class; a parent their children's teachers; a class teacher the
        # teachers of their class; a teacher themself. See common.access.teachers_scope.
        return access.teachers_scope(self.request.user, super().get_queryset())

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_TEACHERS)()]
        return [permissions.IsAuthenticated()]

    def _enforce_own_school(self, serializer):
        school = serializer.validated_data.get("school")
        if not rbac.is_global(self.request.user) and school is not None and school.id != self.request.user.school_id:
            raise PermissionDenied("Boshqa maktab uchun o'qituvchi yarata/o'zgartira olmaysiz.")

    def perform_create(self, serializer):
        self._enforce_own_school(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._enforce_own_school(serializer)
        serializer.save()

    @action(detail=False, methods=["get"])
    def me(self, request):
        profile = get_object_or_404(TeacherProfile, user=request.user)
        return Response(self.get_serializer(profile).data)


class ParentViewSet(viewsets.ModelViewSet):
    queryset = ParentProfile.objects.select_related("user")
    serializer_class = ParentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return access.parents_scope(self.request.user, super().get_queryset())

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_USERS)()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        profile = get_object_or_404(ParentProfile, user=request.user)
        return Response(self.get_serializer(profile).data)


class StudentTransferHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Class-transfer log. Staff only, and only for students the user may open."""

    serializer_class = StudentTransferHistorySerializer
    permission_classes = [require(VIEW_ALL_STUDENTS, VIEW_ASSIGNED_STUDENTS, VIEW_CLASS_STUDENTS)]
    filterset_fields = ["student"]

    def get_queryset(self):
        qs = StudentTransferHistory.objects.select_related("student", "old_class", "new_class")
        return access.transfer_history_scope(self.request.user, qs)


class StudentDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["student", "document_type"]

    def get_queryset(self):
        qs = StudentDocument.objects.select_related("student__user")
        return access.student_documents_scope(self.request.user, qs)

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_STUDENTS)()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        student = serializer.validated_data.get("student")
        if student is not None and not access.can_edit_student(self.request.user, student):
            raise PermissionDenied("Bu o'quvchi uchun hujjat yuklay olmaysiz.")
        serializer.save(uploaded_by=self.request.user)


class SchoolHealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolHealthRecordSerializer
    permission_classes = [CanViewSensitiveStudentData]
    filterset_fields = ["student"]

    def get_queryset(self):
        return access.health_records_scope(
            self.request.user, SchoolHealthRecord.objects.select_related("student__user")
        )

    def _check_student(self, serializer):
        student = serializer.validated_data.get("student")
        if student is not None and not access.can_view_student(self.request.user, student):
            raise PermissionDenied("Bu o'quvchining sog'liq ma'lumotlarini boshqara olmaysiz.")

    def perform_create(self, serializer):
        self._check_student(serializer)
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):
        self._check_student(serializer)
        serializer.save(updated_by=self.request.user)
