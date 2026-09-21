from rest_framework.routers import DefaultRouter

from .views import LibraryMaterialViewSet

router = DefaultRouter()
router.register("", LibraryMaterialViewSet, basename="library-material")

urlpatterns = router.urls
