# notifications/urls.py
from django.urls import path
from .views import (
    UnreadCountAPI, NotificationsListAPI,
    NotificationMarkReadAPI, NotificationReadAllAPI,
)

app_name = "notifications"

urlpatterns = [
    path("unread/", UnreadCountAPI.as_view(), name="unread_count"),
    path("",        NotificationsListAPI.as_view(), name="list"),
    path("<int:pk>/read/", NotificationMarkReadAPI.as_view(), name="mark_read"),
    path("read-all/",      NotificationReadAllAPI.as_view(),  name="read_all"),
]
