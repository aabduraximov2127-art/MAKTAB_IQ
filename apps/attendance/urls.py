from rest_framework.routers import DefaultRouter

from .views import AttendanceViewSet, TeacherAttendanceViewSet

router = DefaultRouter()
router.register("teacher-attendance", TeacherAttendanceViewSet, basename="teacher-attendance")
router.register("", AttendanceViewSet, basename="attendance")

urlpatterns = router.urls
