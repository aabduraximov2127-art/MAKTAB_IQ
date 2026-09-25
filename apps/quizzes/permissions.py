from rest_framework.permissions import SAFE_METHODS, BasePermission

from common import access, rbac
from common.rbac import (
    MANAGE_QUIZZES,
    VIEW_ALL_QUIZZES,
    VIEW_ASSIGNED_QUIZZES,
    VIEW_CHILD_QUIZZES,
    VIEW_CLASS_REPORTS,
    VIEW_OWN_QUIZZES,
)

QUIZ_VIEW_PERMISSIONS = (
    VIEW_ALL_QUIZZES,
    VIEW_OWN_QUIZZES,
    VIEW_CHILD_QUIZZES,
    VIEW_ASSIGNED_QUIZZES,
    VIEW_CLASS_REPORTS,
)


def can_write_quiz(user, quiz) -> bool:
    """A quiz is changed by the teacher who made it, or by a school-wide writer (admin) of the
    same school."""
    if not rbac.has_perm(user, MANAGE_QUIZZES):
        return False
    if rbac.has_perm(user, VIEW_ALL_QUIZZES):
        return access.same_school(user, quiz.class_room.school_id)
    return quiz.teacher.user_id == user.id


class CanAccessQuiz(BasePermission):
    """Quizzes. SUPERADMIN doesn't need quizzes/tests at all (it holds no quiz permission).
    Reading: ``view_*_quizzes``; writing: ``manage_quizzes`` on the quiz's own teacher / an
    admin of the same school. Directors and deputy directors can read only."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return rbac.has_any_perm(user, *QUIZ_VIEW_PERMISSIONS)
        return rbac.has_perm(user, MANAGE_QUIZZES)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True  # rows are already limited by the view's queryset
        quiz = getattr(obj, "quiz", obj)  # Question -> its quiz
        return can_write_quiz(request.user, quiz)
