from django.urls import path
from .api_views import (
    ProfilesAPI, MeAPI, LikeAPI, MatchesAPI,
    MessagesAPI, BlockToggleAPI, ChatThreadsAPI, ProfileDetailAPI, BlocksAPI,
    ReportCreateAPI, ReportsSentAPI, ReportsReceivedAPI,
    ProfileFieldsAPI, MeCustomFieldsAPI, MeAvatarAPI, MeLciqImageAPI,  # ★追加
    VerificationsAPI, VerificationDeleteAPI,
    LikesSentAPI, FootprintTouchAPI, UnmatchAPI, LikesReceivedAPI, FootprintsAPI,
    ChatUnreadMapAPI, ChatThreadReadAPI
)
from payments.api_views import PaymentsCheckoutAPI
from core.api_contact import ContactAPI

urlpatterns = [
    path("profiles/", ProfilesAPI.as_view(), name="api_profiles"),
    path("profiles/<int:user_id>/", ProfileDetailAPI.as_view(), name="api_profile_detail"),
    path("me/",       MeAPI.as_view(),       name="api_me"),
    path("like/",     LikeAPI.as_view(),     name="api_like"),
    path("matches/",  MatchesAPI.as_view(),  name="api_matches"),
    path("chats/",    ChatThreadsAPI.as_view(), name="api_chat_threads"),
    path("chats/<int:user_id>/messages/", MessagesAPI.as_view(), name="api_messages"),
    path("block/<int:user_id>/toggle/",   BlockToggleAPI.as_view(), name="api_block_toggle"),
    path("blocks/",   BlocksAPI.as_view(), name="api_blocks"),
    path("reports/",            ReportCreateAPI.as_view(),   name="api_reports_create"),
    path("reports/sent/",       ReportsSentAPI.as_view(),    name="api_reports_sent"),
    path("reports/received/",   ReportsReceivedAPI.as_view(),name="api_reports_received"),
    path("profile-fields/",       ProfileFieldsAPI.as_view(),   name="api_profile_fields"),
    path("me/custom-fields/",     MeCustomFieldsAPI.as_view(),  name="api_me_custom_fields"),
    path("me/avatar/",      MeAvatarAPI.as_view(),     name="api_me_avatar"),
    path("me/lciq-image/",  MeLciqImageAPI.as_view(),  name="api_me_lciq_image"),  # ★追加
    path("verifications/", VerificationsAPI.as_view(), name="api_verifications"),
    path("verifications/<int:pk>/", VerificationDeleteAPI.as_view(), name="api_verification_delete"),
    path("likes/sent/", LikesSentAPI.as_view(), name="api_likes_sent"),
    path("footprints/<int:user_id>/touch/", FootprintTouchAPI.as_view(), name="api_footprint_touch"),
    path("unmatch/<int:user_id>/", UnmatchAPI.as_view(), name="api_unmatch"),
    path("likes/received/", LikesReceivedAPI.as_view(), name="api_likes_received"),
    path("footprints/",     FootprintsAPI.as_view(),   name="api_footprints"),
    path("chats/unread-map/", ChatUnreadMapAPI.as_view(), name="api_chat_unread_map"),
    path("chats/<int:user_id>/read/", ChatThreadReadAPI.as_view(), name="api_chat_read_thread"),
    path("payments/checkout/", PaymentsCheckoutAPI.as_view(), name="api_payments_checkout"),
    path("contact/", ContactAPI.as_view(), name="api_contact"),
]
