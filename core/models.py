# core/models.py
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ---- 固定のChoice定義 (既存のまま) ----
BLOOD_TYPE_CHOICES = (
    ('A', 'A型'),
    ('B', 'B型'),
    ('O', 'O型'),
    ('AB', 'AB型'),
)


GENDER_CHOICES = (
    ('male', '男性'),
    ('female', '女性'),
)

SEXUAL_OBJECT_CHOICES = (
    ('male', '男性'),
    ('female', '女性'),
)

PLAN_CHOICES = (
    ('free', 'フリープラン'),
    ('standard', 'スタンダード'),
)


# ======================================================================
# 1) ユーザーのProfile。 ここには血液型・性別など”すでに確定しているカラム”が残る
# ======================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to='',   # アップロード先フォルダ
        blank=True, null=True
    )
    nickname = models.CharField(max_length=50, blank=True, null=True)
    blood_type = models.CharField(
        max_length=2,
        choices=BLOOD_TYPE_CHOICES,
        blank=True,
        null=True
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    sexual_object_pref = models.CharField(
        max_length=10,
        choices=SEXUAL_OBJECT_CHOICES,
        blank=True,
        null=True
    )
    plan = models.CharField(
        max_length=10,
        choices=PLAN_CHOICES,
        default='free'
    )
    lciq  = models.CharField(max_length=10, blank=True, null=True)
    plan_expiry = models.DateTimeField(blank=True, null=True)
    option_expiry = models.DateTimeField(blank=True, null=True)
    date_of_birth    = models.DateField(blank=True, null=True)
    main_area = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.user.username

    def has_option(self):
        if self.option_expiry:
            return self.option_expiry > timezone.now()
        return False

    def is_standard_plan(self):
        if self.plan == 'standard' and self.plan_expiry:
            return self.plan_expiry > timezone.now()
        return False

    def is_free_plan(self):
        if self.plan == 'free':
            return True
        if self.plan == 'standard' and (not self.plan_expiry or self.plan_expiry < timezone.now()):
            return True
        return False

    def has_lciq(self) -> bool:
        """
        LCIQ® が入力済みかどうか  
        （固定カラム lciq を使っている想定。動的フィールドの場合は
         profile.custom_values.get("lciq") で同じことが出来ます）
        """
        return bool(self.lciq)

    @property
    def custom_values(self):
        # 例) { 'age': '30', 'hobby': 'サウナ' } のようなdictを返す
        if not hasattr(self, '_cached_custom_values'):
            pfvs = self.profilefieldvalue_set.select_related('field')
            self._cached_custom_values = {
                pfv.field.field_key: pfv.value
                for pfv in pfvs
            }
        return self._cached_custom_values

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

# ======================================================================
# 2) 可変項目用: Adminで「ラジオ/セレクト/テキスト」項目を自由に追加
# ======================================================================
class ProfileField(models.Model):
    """
    管理画面から追加する「動的なフィールド定義」。
    例: field_key='favorite_color', field_label='好きな色', field_type='select'
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'テキスト'),
        ('select', 'セレクト'),
        ('radio', 'ラジオ'),
        ('checkbox', 'チェックボックス'),
    ]
    field_key = models.SlugField(unique=True)
    field_label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    field_choices = models.TextField(
        blank=True,
        help_text="セレクトやラジオの場合、改行区切りで選択肢を列挙"
    )
    # 表示順や必須フラグを入れたければ追加

    CATEGORY_CHOICES = [
        ('normal', '通常'),
        ('plus',   'プラス'),
    ]
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='normal',
    )
    required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.field_label} (key={self.field_key})"

# ======================================================================
# 3) ユーザー回答: user_profile + field でユニーク。 valueに実際の選択や入力を保存
# ======================================================================
class ProfileFieldValue(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    field = models.ForeignKey(ProfileField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user_profile', 'field')

    def __str__(self):
        return f"{self.user_profile} - {self.field.field_key} = {self.value}"


class Match(models.Model):
    """
    ここでは「フォロー状態（from_user → to_user）」を記録する例にしています。
    'like' 状態が両方向になったらマッチとみなす、などの拡張もOK。
    """
    STATUS_CHOICES = [
        ('like', 'Like'),
        ('matched', 'Matched'),
        ('unmatched', 'Unmatched'),
    ]
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='matches_sent'
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='matches_received'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_received')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



class Footprint(models.Model):
    """
    誰が(from_user) いつ(to_user) のプロフィールを見たかを記録するモデル
    """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='footprints_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='footprints_received')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user} viewed {self.to_user} at {self.created_at}"
