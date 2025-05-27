# notifications/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_notification_email(user, subject_tpl, body_tpl, ctx):
    """
    subject_tpl / body_tpl にはテンプレートファイル名（txt）
    ctx はテンプレートに流し込む context dict
    """
    subject = render_to_string(subject_tpl, ctx).strip()
    body    = render_to_string(body_tpl,    ctx)
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,   # 本番では True にしてもOK
    )
