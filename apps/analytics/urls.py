from django.urls import path

from .views import AdminAnalyticsView, StudentProgressView

urlpatterns = [
    path("progress/", StudentProgressView.as_view(), name="student-progress"),
    path("admin/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]
