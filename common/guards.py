"""View mixins that turn "you may not look at that" into an honest ``403 Forbidden``.

Out of the box DRF answers ``404`` when an object is filtered out of ``get_queryset()`` and
``200`` with an empty list when a filter such as ``?student=<someone else>`` matches nothing.
Both hide the fact that access was *refused*. The permission spec asks for ``403`` whenever a
user targets data that is not theirs (Student A -> Student B's grades, Parent A -> Parent B's
child, Teacher A -> Teacher B's class ...), so views mix these in:

* :class:`ForbidOutOfScopeMixin`  - ``GET/PATCH/DELETE /x/{id}/`` on an existing object outside
  the caller's scope is 403 (a truly non-existent id is still 404);
* :class:`StudentParamGuardMixin` - any request carrying ``?student=<id>`` for a student the
  caller may not open is 403 (covers list filters, ``annual``, ``calendar`` ...).
"""

from django.core.exceptions import ValidationError
from django.http import Http404

from . import access

DENIED_MESSAGE = "Bu ma'lumotga kirishga ruxsatingiz yo'q."


class ForbidOutOfScopeMixin:
    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            model = self.get_queryset().model
            lookup = self.lookup_url_kwarg or self.lookup_field
            value = self.kwargs.get(lookup)
            if value is not None:
                try:
                    exists = model._default_manager.filter(**{self.lookup_field: value}).exists()
                except (ValueError, TypeError, ValidationError):
                    exists = False
                if exists:
                    self.permission_denied(self.request, message=DENIED_MESSAGE)
            raise


class StudentParamGuardMixin:
    """Refuse ``?student=<id>`` for a student the caller is not allowed to open."""

    student_param = "student"

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # authentication + permission classes first
        raw = request.query_params.get(self.student_param)
        if raw and raw.isdigit():
            from apps.users.models import StudentProfile

            student = StudentProfile.objects.select_related("class_room").filter(pk=int(raw)).first()
            if student is not None and not access.can_view_student(request.user, student):
                self.permission_denied(request, message=DENIED_MESSAGE)
