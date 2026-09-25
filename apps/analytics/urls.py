from django.urls import path

from .views import AdminAnalyticsView, ClassReportView, StudentProgressView, SystemAnalyticsView

urlpatterns = [
    path("progress/", StudentProgressView.as_view(), name="student-progress"),
    path("admin/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("system/", SystemAnalyticsView.as_view(), name="system-analytics"),
    path("class/", ClassReportView.as_view(), name="class-report"),
]
