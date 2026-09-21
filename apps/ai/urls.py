from django.urls import path

from .views import AIAskView, WeakTopicsView

urlpatterns = [
    path("ask/", AIAskView.as_view(), name="ai-ask"),
    path("weak-topics/", WeakTopicsView.as_view(), name="ai-weak-topics"),
]
