# notifications/utils.py
import logging
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from post_office import mail

logger = logging.getLogger(__name__)

def send_notification_email(
    *,
    user=None,
    to=None,
    subject="",
    message="",
    template=None,
    context=None,
    language: str = "",
    priority: str = "now",
    cc=None,
    bcc=None,
):
    """
    絵文字/UTF-8安全・失敗しても例外を外へ投げない安全送信。
    - 宛先は user か to（どちらでもOK）
    - template 指定があればテンプレート送信、無ければ subject/message 送信
    - 送信失敗/不正メールはログに残して False を返す
    """
    # 宛先抽出
    recipients = []
    if to:
        recipients = [to] if isinstance(to, str) else [x for x in to if x]
    elif user is not None:
        email = (getattr(user, "email", "") or "").strip()
        if email:
            recipients = [email]

    # 検証
    valid = []
    for addr in recipients:
        try:
            validate_email(addr)
            valid.append(addr)
        except ValidationError:
            logger.warning("notify skipped: invalid email '%s' (user=%s, template=%s)", addr, getattr(user, "pk", None), template)

    if not valid:
        logger.info("notify skipped: no valid recipients (user=%s, template=%s)", getattr(user, "pk", None), template)
        return False

    # 送信（post_office）
    try:
        if template:
            mail.send(
                recipients=valid,
                template=template,
                context=context or {},
                language=language or "",
                priority=priority or "now",
                cc=cc, bcc=bcc,
            )
        else:
            mail.send(
                recipients=valid,
                subject=force_str(subject or ""),
                message=force_str(message or ""),
                priority=priority or "now",
                cc=cc, bcc=bcc,
            )
        return True
    except Exception as e:
        logger.exception("notify mail failed (user=%s, template=%s): %s", getattr(user, "pk", None), template, e)
        return False
