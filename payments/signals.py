# payments/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Payment, PlanOption
from core.models import UserProfile

@receiver(post_save, sender=Payment)
def update_user_profile_plan(sender, instance, created, **kwargs):
    if not created:
        return  # 新規作成時のみ

    user = instance.user
    if not hasattr(user, 'userprofile'):
        UserProfile.objects.create(user=user)

    profile = user.userprofile
    now = timezone.now()

    # 1) plan の日数計算
    if instance.plan:
        try:
            plan_obj = PlanOption.objects.get(category='plan', code=instance.plan)
            total_plan_days = plan_obj.base_days + plan_obj.extra_days
        except PlanOption.DoesNotExist:
            total_plan_days = 0

        # plan_expiry を更新
        if total_plan_days > 0:
            profile.plan_expiry = now + timedelta(days=total_plan_days)
            profile.plan = 'standard'  # ユーザーProfile上で"standard"扱い

    # 2) option の日数計算
    if instance.option:
        try:
            opt_obj = PlanOption.objects.get(category='option', code=instance.option)
            total_opt_days = opt_obj.base_days + opt_obj.extra_days
        except PlanOption.DoesNotExist:
            total_opt_days = 0

        if total_opt_days > 0:
            profile.option_expiry = now + timedelta(days=total_opt_days)

    profile.save()
