from rest_framework.routers import DefaultRouter

from .views import AssignmentSubmissionViewSet, AssignmentViewSet

assignments_router = DefaultRouter()
assignments_router.register("", AssignmentViewSet, basename="assignment")

submissions_router = DefaultRouter()
submissions_router.register("", AssignmentSubmissionViewSet, basename="submission")

urlpatterns = assignments_router.urls
submissions_urlpatterns = submissions_router.urls
