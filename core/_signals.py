# --- core/signals.py ---
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get("raw", False):   # ← ★これを追加
        return                     #    fixture 読み込み時はスキップ
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    ユーザーが保存されるたびにUserProfileも保存する。
    """
    if kwargs.get("raw", False):      # ← ★ ここにも
        return
    instance.userprofile.save()
