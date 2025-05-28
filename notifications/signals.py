from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from core.models import Match, Message
from notifications.models import Notification
from notifications.utils import send_notification_email


# --------------------------------------------------
# 1) いいね！を受け取った通知
# --------------------------------------------------
@receiver(post_save, sender=Match)
def notify_like(sender, instance, created, **kwargs):
    if not created or instance.status != "like":
        return

    # 通知レコード
    Notification.objects.create(
        user   = instance.to_user,
        target = instance,
        verb   = "like",
        text   = f"{instance.from_user.username} さんから いいね！",
    )

    # メール
    ctx = {
        "to_user":      instance.to_user,
        "from_user":    instance.from_user,
        "to_profile":   instance.to_user.userprofile,
        "from_profile": instance.from_user.userprofile,
        "now":          timezone.now(),
    }
    body = render_to_string("emails/notify_like.txt", ctx)

    send_notification_email(
        instance.to_user,
        subject="【EXMATCH】👍 いいね！が届きました",
        body=body,
    )


# --------------------------------------------------
# 2) マッチ成立
# --------------------------------------------------
@receiver(post_save, sender=Match)
def notify_match(sender, instance, created, **kwargs):
    # 「created 直後」または status を 'matched' に更新した直後の両方を拾う
    if instance.status != "matched":
        return

    ct = ContentType.objects.get_for_model(Match)

    for u, other in (
        (instance.from_user, instance.to_user),
        (instance.to_user,   instance.from_user),
    ):
        # すでに同一ユーザー宛の match 通知があれば skip
        already = Notification.objects.filter(
            user=u,
            content_type=ct,
            object_id=instance.id,
            verb="match",
        ).exists()
        if already:
            continue

        Notification.objects.create(
            user=u,
            content_type=ct,
            object_id=instance.id,
            verb="match",
            text=f"{other.userprofile.nickname or other.username} さんとマッチしました！",
        )

        ctx = {
            "to_user":      u,
            "from_user":    other,
            "to_profile":   u.userprofile,
            "from_profile": other.userprofile,
            "now":          timezone.now(),
        }
        body = render_to_string("emails/notify_match.txt", ctx)

        send_notification_email(
            u,
            subject="【EXMATCH】🎉 マッチ成立のお知らせ",
            body=body,
        )

# --------------------------------------------------
# 3) 新着メッセージ
# --------------------------------------------------
@receiver(post_save, sender=Message)
def notify_message(sender, instance, created, **kwargs):
    if not created:
        return

    # 通知レコード
    Notification.objects.create(
        user   = instance.receiver,
        target = instance,
        verb   = "message",
        text   = f"{instance.sender.username} さんから新しいメッセージ",
    )

    # メール
    ctx = {
        "to_user":      instance.receiver,
        "from_user":    instance.sender,
        "to_profile":   instance.receiver.userprofile,
        "from_profile": instance.sender.userprofile,
        "snippet":      instance.text[:60],
        "now":          timezone.now(),
    }
    body = render_to_string("emails/notify_message.txt", ctx)

    send_notification_email(
        instance.receiver,
        subject="【EXMATCH】📨 新着メッセージがあります",
        body=body,
    )
