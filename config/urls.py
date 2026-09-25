from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.assignments import urls as assignments_urls  # noqa: E402
from apps.users import urls as users_urls  # noqa: E402

api_v1_patterns = [
    path("auth/", include("apps.users.auth_urls")),
    path("users/", include((users_urls.urlpatterns, "users"))),
    path("students/", include((users_urls.students_urlpatterns, "students"))),
    path("teachers/", include((users_urls.teachers_urlpatterns, "teachers"))),
    path("parents/", include((users_urls.parents_urlpatterns, "parents"))),
    path("roles/", include((users_urls.roles_urlpatterns, "roles"))),
    path("permissions/", include((users_urls.permissions_urlpatterns, "permissions"))),
    path("schools/", include("apps.schools.urls")),
    path("classes/", include("apps.classes.urls")),
    path("subjects/", include("apps.subjects.urls")),
    path("lessons/", include("apps.lessons.urls")),
    path("assignments/", include((assignments_urls.urlpatterns, "assignments"))),
    path("submissions/", include((assignments_urls.submissions_urlpatterns, "submissions"))),
    path("grades/", include("apps.grades.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("chat/", include("apps.chat.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("library/", include("apps.library.urls")),
    path("quizzes/", include("apps.quizzes.urls")),
    path("helpdesk/", include("apps.helpdesk.urls")),
    path("ai/", include("apps.ai.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
