from rest_framework.permissions import SAFE_METHODS, BasePermission

from common.permissions import user_role


class CanAccessQuiz(BasePermission):
    """SUPERADMIN doesn't need quizzes/tests at all."""

    def has_permission(self, request, view):
        role = user_role(request.user)
        if role == "SUPERADMIN":
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in {"ADMIN", "TEACHER"}
