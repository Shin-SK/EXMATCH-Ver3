import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(pre_save, sender=User)
def invalidate_token_on_password_change(sender, instance, **kwargs):
    """パスワード変更時に既存トークンを失効させる"""
    if not instance.pk:
        return
    try:
        old = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if old.password != instance.password:
        from rest_framework.authtoken.models import Token
        deleted, _ = Token.objects.filter(user=instance).delete()
        if deleted:
            logger.info("Token invalidated for user %s on password change", instance.pk)
