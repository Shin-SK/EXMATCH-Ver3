# core/signals_message.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from core.models import Message
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.create(
        user     = instance.receiver,
        content_type = ContentType.objects.get_for_model(Message),
        object_id    = instance.id,
        verb     = 'message',
        text     = f'{instance.sender.username} から新着メッセージ',
    )
