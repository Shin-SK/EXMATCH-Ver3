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
        pass
    # ★ signup後の導線：ログイン画面へ。成功時 next=/onboarding に流す
    return redirect(f"{settings.FRONTEND_BASE_URL}/login?verified=1&next=/onboarding")
