from rest_framework.routers import DefaultRouter

from .views import HelpDeskTicketViewSet

router = DefaultRouter()
router.register("", HelpDeskTicketViewSet, basename="helpdesk-ticket")

urlpatterns = router.urls
