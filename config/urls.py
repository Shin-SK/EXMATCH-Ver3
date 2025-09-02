#config/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django_contact_form.views import ContactFormView
from core.forms_contact import ContactFormWithSubject
from core.api_views_csrf import CsrfAPI
from core.views_auth import confirm_email_and_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('payments/', include('payments.urls')),
    path('accounts/', include('allauth.urls')),
    path("api/notifications/", include("notifications.urls")),
    path("contact/", ContactFormView.as_view(
            form_class=ContactFormWithSubject), name="contact"),
    path("__reload__/", include("django_browser_reload.urls")),
    path('api/csrf/', CsrfAPI.as_view(), name='api_csrf'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path("api/auth/registration/account-confirm-email/<str:key>/",confirm_email_and_redirect,name="account_confirm_email_redirect",),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/', include('core.api_urls')),
    ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)