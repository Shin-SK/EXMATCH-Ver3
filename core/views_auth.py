# core/views_auth.py
from django.conf import settings
from django.shortcuts import redirect
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC

def confirm_email_and_redirect(request, key):
    try:
        confirmation = EmailConfirmationHMAC.from_key(key)
        if confirmation is None:
            confirmation = EmailConfirmation.objects.get(key=key)
        confirmation.confirm(request)
    except Exception:
        # 期限切れ/不正キーでも最終的にフロントへ戻す
        pass
    return redirect(f"{settings.FRONTEND_BASE_URL}/login?verified=1")
