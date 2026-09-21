from rest_framework.routers import DefaultRouter

from .views import AcademicYearViewSet, ClassRoomViewSet, QuarterViewSet

router = DefaultRouter()
router.register("academic-years", AcademicYearViewSet, basename="academic-year")
router.register("quarters", QuarterViewSet, basename="quarter")
router.register("", ClassRoomViewSet, basename="classroom")

urlpatterns = router.urls
