# payments/models.py (例の一部)
from django.db import models
from django.conf import settings
from django.utils import timezone

# 既存 Payment 用
PLAN_CHOICES = (
    ('standard_1m', 'Standard 1ヶ月'),
    ('standard_3m', 'Standard 3ヶ月'),
    ('standard_6m', 'Standard 6ヶ月'),
    ('standard_12m', 'Standard 12ヶ月'),
)
OPTION_CHOICES = (
    ('plus_profile', 'プラスプロフィール'),
)

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, blank=True, null=True)
    option = models.CharField(max_length=20, choices=OPTION_CHOICES, blank=True, null=True)
    purchased_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - plan:{self.plan} / option:{self.option} ({self.purchased_at})"


# ★ 新規追加: PlanOption モデル
CATEGORY_CHOICES = (
    ('plan', 'プラン'),
    ('option', 'オプション'),
)

class PlanOption(models.Model):
    """
    プランとオプションをまとめて管理するモデル。
    category='plan' / code='standard_3m' などでプランを表す。
    category='option' / code='plus_profile' などでオプションを表す。

    base_days: 基本日数
    extra_days: キャンペーンなどで追加する日数
    """
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        help_text="plan or option"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Payment.plan や Payment.option に対応する文字列"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="表示用の名前"
    )
    base_days = models.IntegerField(
        default=0,
        help_text="基本日数(例: standard_3mなら90, plus_profileなら30)"
    )
    extra_days = models.IntegerField(
        default=0,
        help_text="キャンペーンなどでさらに延長する日数"
    )

    def __str__(self):
        return f"[{self.category}] {self.name or self.code}"
