# notifications/util.py
from django.core.mail import send_mail
from django.conf import settings

def send_notification_email(to_user, subject, body):
    """to_user は auth.User インスタンス想定"""
    if not to_user.email:          # アドレス未登録なら送らない
        return
    send_mail(
        subject        = subject,
        message        = body,
        from_email     = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [to_user.email],
        fail_silently  = False,    # ↓開発中だけ True でも可
    )
