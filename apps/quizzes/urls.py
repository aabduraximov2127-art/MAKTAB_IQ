from rest_framework.routers import DefaultRouter

from .views import QuestionViewSet, QuizAttemptViewSet, QuizViewSet

router = DefaultRouter()
router.register("questions", QuestionViewSet, basename="question")
router.register("attempts", QuizAttemptViewSet, basename="quiz-attempt")
router.register("", QuizViewSet, basename="quiz")

urlpatterns = router.urls
