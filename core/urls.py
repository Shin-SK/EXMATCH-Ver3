# --- core/urls.py ---
from django.urls import path
from . import views
from django.views.generic import TemplateView
from .views import UserProfileListView, my_page, profile_edit


urlpatterns = [
    path('', views.home, name='home'),
    path('user_list/', views.user_list, name='user_list'),  # 追加
    path('follow_list/', views.follow_list, name='follow_list'),
    path('follow_user/<int:user_id>/', views.follow_user, name='follow_user'),
    path('matched_list/', views.matched_list, name='matched_list'),
    path('chat/<int:user_id>/', views.chat_room, name='chat_room'),
    path("chat/api/<int:user_id>/", views.chat_api, name="chat_api"),
    path('chat/', views.chat_index, name='chat_index'),         # 一覧
    path('search/', UserProfileListView.as_view(), name='userprofile_list'),
    path('mypage/', views.my_page, name='my_page'),
    path('profile_edit/', views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', views.user_profile_detail, name='user_profile_detail'),
    path('footprints/', views.footprint_list, name='footprint_list'),
    path('likes_received/', views.likes_received_list, name='likes_received_list'),
    path("contact/", views.contact_view, name="contact"),
    path("contact/sent/", views.contact_done, name="contact_done"),
    path("how-to-lciq/", TemplateView.as_view(template_name="core/h2lciq.html"),name="h2lciq"),
    path("reports/create/", views.create_report, name="create_report"),
    path("block/<int:user_id>/", views.toggle_block, name="toggle_block"),
]