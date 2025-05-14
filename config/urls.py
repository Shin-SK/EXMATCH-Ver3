from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django_contact_form.views import ContactFormView
from core.forms_contact import ContactFormWithSubject

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('payments/', include('payments.urls')),
    path('accounts/', include('allauth.urls')),
    path("api/notifications/", include("notifications.urls")),
    path("contact/", ContactFormView.as_view(
            form_class=ContactFormWithSubject), name="contact"),
    ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)