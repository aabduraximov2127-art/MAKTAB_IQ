from rest_framework.routers import DefaultRouter

from .views import ChatRoomViewSet, MessageViewSet

router = DefaultRouter()
router.register("messages", MessageViewSet, basename="message")
router.register("", ChatRoomViewSet, basename="chatroom")

urlpatterns = router.urls
