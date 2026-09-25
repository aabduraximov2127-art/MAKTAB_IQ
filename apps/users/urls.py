from django.urls import path
from rest_framework.routers import DefaultRouter

from .access_api import PermissionListView, RoleListView
from .views import (
    MeProfileView,
    MeView,
    ParentViewSet,
    SchoolHealthRecordViewSet,
    StudentDocumentViewSet,
    StudentTransferHistoryViewSet,
    StudentViewSet,
    TeacherViewSet,
    TelegramLinkCodeView,
    TelegramStatusView,
    TelegramUnlinkView,
    UserViewSet,
)

users_router = DefaultRouter()
users_router.register("", UserViewSet, basename="user")

students_router = DefaultRouter()
students_router.register("documents", StudentDocumentViewSet, basename="student-document")
students_router.register("health-records", SchoolHealthRecordViewSet, basename="student-health-record")
students_router.register("transfer-history", StudentTransferHistoryViewSet, basename="student-transfer-history")
students_router.register("", StudentViewSet, basename="student")

teachers_router = DefaultRouter()
teachers_router.register("", TeacherViewSet, basename="teacher")

parents_router = DefaultRouter()
parents_router.register("", ParentViewSet, basename="parent")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/profile/", MeProfileView.as_view(), name="me-profile"),
    path("me/telegram-link-code/", TelegramLinkCodeView.as_view(), name="telegram-link-code"),
    path("me/telegram-status/", TelegramStatusView.as_view(), name="telegram-status"),
    path("me/telegram-unlink/", TelegramUnlinkView.as_view(), name="telegram-unlink"),
] + users_router.urls
students_urlpatterns = students_router.urls
teachers_urlpatterns = teachers_router.urls
parents_urlpatterns = parents_router.urls
roles_urlpatterns = [path("", RoleListView.as_view(), name="role-list")]
permissions_urlpatterns = [path("", PermissionListView.as_view(), name="permission-list")]
