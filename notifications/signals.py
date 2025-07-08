from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from core.models import Match, Message, UserProfile
from notifications.models import Notification
from notifications.utils import send_notification_email


# 1) いいね！を受け取った通知
@receiver(post_save, sender=Match)
def notify_like(sender, instance, created, **kwargs):
	if not created or instance.status != "like":
		return

	Notification.objects.create(
		user=instance.to_user,
		target=instance,
		verb="like",
		text=f"{instance.from_user.username} さんから いいね！",
	)

	send_notification_email(
		user=instance.to_user,
		template="notify_like",
		context={
			"to_user":      instance.to_user,
			"from_user":    instance.from_user,
			"to_profile":   instance.to_user.userprofile,
			"from_profile": instance.from_user.userprofile,
			"now":          timezone.now(),
		},
	)


# 2) マッチ成立
@receiver(post_save, sender=Match)
def notify_match(sender, instance, created, **kwargs):
	if instance.status != "matched":
		return

	ct = ContentType.objects.get_for_model(Match)

	for u, other in (
		(instance.from_user, instance.to_user),
		(instance.to_user,   instance.from_user),
	):
		if Notification.objects.filter(
			user=u,
			content_type=ct,
			object_id=instance.id,
			verb="match",
		).exists():
			continue

		Notification.objects.create(
			user=u,
			content_type=ct,
			object_id=instance.id,
			verb="match",
			text=f"{other.userprofile.nickname or other.username} さんとマッチしました！",
		)

		send_notification_email(
			user=u,
			template="notify_match",
			context={
				"to_user":      u,
				"from_user":    other,
				"to_profile":   u.userprofile,
				"from_profile": other.userprofile,
				"now":          timezone.now(),
			},
		)


# 3) 新着メッセージ
@receiver(post_save, sender=Message)
def notify_message(sender, instance, created, **kwargs):
	if not created:
		return

	Notification.objects.create(
		user=instance.receiver,
		target=instance,
		verb="message",
		text=f"{instance.sender.username} さんから新しいメッセージ",
	)

	send_notification_email(
		user=instance.receiver,
		template="notify_message",
		context={
			"to_user":      instance.receiver,
			"from_user":    instance.sender,
			"to_profile":   instance.receiver.userprofile,
			"from_profile": instance.sender.userprofile,
			"snippet":      instance.text[:60],
			"now":          timezone.now(),
		},
	)


# 4) 本人確認関連
@receiver(post_save, sender=UserProfile)
def notify_id_doc_events(sender, instance, **kwargs):
	# 書類アップロード
	if instance.tracker.has_changed("id_doc_image") and instance.id_doc_image:
		Notification.objects.create(
			user=instance.user,
			target=instance,
			verb="id_doc_uploaded",
			text="本人確認書類を受け取りました",
		)
		send_notification_email(
			user=instance.user,
			template="id_doc_uploaded",
			context={
				"user":    instance.user,
				"profile": instance,
				"now":     timezone.now(),
			},
		)

	# 認証完了
	if instance.tracker.has_changed("id_doc_verified") and instance.id_doc_verified:
		Notification.objects.create(
			user=instance.user,
			target=instance,
			verb="id_doc_verified",
			text="本人確認が完了しました",
		)
		send_notification_email(
			user=instance.user,
			template="id_doc_verified",
			context={
				"user":    instance.user,
				"profile": instance,
				"now":     timezone.now(),
			},
		)
