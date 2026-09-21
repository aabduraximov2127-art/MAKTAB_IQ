from rest_framework.routers import DefaultRouter

from .views import AnnouncementViewSet, EmergencyAnnouncementViewSet, NotificationViewSet

router = DefaultRouter()
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("emergency-announcements", EmergencyAnnouncementViewSet, basename="emergency-announcement")
router.register("", NotificationViewSet, basename="notification")

urlpatterns = router.urls
