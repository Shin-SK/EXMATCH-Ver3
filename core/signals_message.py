# core/signals_message.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str

from core.models import Message
from notifications.models import Notification
from notifications.utils import send_notification_email

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message, dispatch_uid="notify_on_message")
def create_message_notification(sender, instance: Message, created: bool, **kwargs):
    if not created:
        return

    # 1) アプリ内通知（DB）…失敗しても握りつぶす
    try:
        Notification.objects.create(
            user=instance.receiver,
            content_type=ContentType.objects.get_for_model(Message),
            object_id=instance.id,
            verb='message',
            text=f'{instance.sender.username} から新着メッセージ',
        )
    except Exception as e:
        logger.exception("notification row failed: %s", e)

    # 2) メール通知…失敗しても握りつぶす（絵文字OK）
    try:
        send_notification_email(
            user=instance.receiver,
            subject=force_str("新着メッセージ"),
            message=force_str(instance.text[:120]),
        )
    except Exception as e:
        logger.exception("email notify failed: %s", e)
