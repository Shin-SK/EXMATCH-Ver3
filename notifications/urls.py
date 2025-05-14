from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("unread/", views.unread_count, name="unread_count"),
]
