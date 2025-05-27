# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from core.models import Match, Message
from .models import Notification
from .utils import send_notification_email

# --- いいね or マッチ -------------------------------------------------
@receiver(post_save, sender=Match)
def notify_match_like(sender, instance, created, **kwargs):
    # 相手への「いいね」が新規作成されたら
    if created and instance.status == "like":
        _create_and_email(
            user=instance.to_user,
            target=instance,
            verb="like",
            text=f"{instance.from_user.userprofile.nickname or instance.from_user.username} さんから いいね！が来ました"
        )

    # どちらかが matched に更新された瞬間（1 度だけ飛ばす）
    if not created and instance.status == "matched" and not instance.to_user.notifications.filter(
        verb="matched", object_id=instance.id
    ).exists():
        # 両者に通知
        _create_and_email(
            user=instance.to_user,
            target=instance,
            verb="matched",
            text="マッチ成立！メッセージを送ってみましょう"
        )
        _create_and_email(
            user=instance.from_user,
            target=instance,
            verb="matched",
            text="マッチ成立！メッセージを送ってみましょう"
        )

# --- メッセージ ------------------------------------------------------
@receiver(post_save, sender=Message)
def notify_message(sender, instance, created, **kwargs):
    if created:
        _create_and_email(
            user=instance.receiver,
            target=instance,
            verb="message",
            text=f"{instance.sender.userprofile.nickname or instance.sender.username} さんからメッセージが届きました"
        )

# --------------------------------------------------------------------
def _create_and_email(*, user, target, verb, text):
    # 1) Notification レコード
    Notification.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(target.__class__),
        object_id=target.id,
        verb=verb,
        text=text
    )
    # 2) メール送信
    subject_tpl = f"email/{verb}_subject.txt"
    body_tpl    = f"email/{verb}_body.txt"
    send_notification_email(user, subject_tpl, body_tpl, {"user": user, "target": target})
