from django.urls import path

from .views import (
    AccountActivateView,
    AccountDeactivateView,
    LoginView,
    LogoutView,
    PasswordResetView,
    RefreshView,
    RegisterStudentView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("register/student/", RegisterStudentView.as_view(), name="auth-register-student"),
    path("users/<int:pk>/activate/", AccountActivateView.as_view(), name="auth-activate"),
    path("users/<int:pk>/deactivate/", AccountDeactivateView.as_view(), name="auth-deactivate"),
    path("users/<int:pk>/reset-password/", PasswordResetView.as_view(), name="auth-reset-password"),
]
