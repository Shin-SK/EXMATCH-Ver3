# core/forms.py
from django import forms
from allauth.account.forms import SignupForm
from .models import (
    UserProfile,
    ProfileField,
    ProfileFieldValue,
)
from django.forms import FileInput, RadioSelect


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # 編集可能なフィールドを列挙
        fields = [
            'profile_image',
            'bio',
            'gender',
            'sexual_object_pref',
            'blood_type',
            'main_area',
            'lciq_score',
            'lciq_image',
            # 必要に応じて他の項目も
        ]
        labels = {
            "bio": "自己紹介",
            "blood_type": "血液型",
            "gender": "性別",
            "sexual_object_pref": "恋愛対象",
            "main_area": "メインエリア",
            "lciq_score": "LCIQスコア",
            "lciq_image": "LCIQ診断スクショ",
        }

        widgets = {
            "profile_image": FileInput(attrs={"class": "filepond"}),
            "blood_type":forms.RadioSelect,
            "gender":forms.RadioSelect,
            "sexual_object_pref":forms.RadioSelect,
            "lciq_image": FileInput(attrs={"class": "filepond"}),
        }


class RegisterRequiredForm(forms.ModelForm):
    class Meta:
        model  = UserProfile
        fields = [
            "nickname",
            "gender",
            "sexual_object_pref",
            "date_of_birth",
            "profile_image",
            "blood_type",
            "main_area",
        ]   


class DynamicProfileFieldForm(forms.Form):
    def __init__(self, *args, user_profile: UserProfile, **kwargs):
        self.user_profile = user_profile
        super().__init__(*args, **kwargs)

        can_use_plus = (
            user_profile.is_standard_plan() or
            user_profile.has_option()
        )

        # ① ここで初期化
        self.category_map = {}

        # 取得対象
        qs = ProfileField.objects.all()
        if not can_use_plus:
            qs = qs.filter(category='normal')

        for pf in qs:
            field_name = f"dynamic_{pf.field_key}"

            # ② カテゴリを記録
            self.category_map[field_name] = pf.category   # 'normal' / 'plus'

            # ------- 既存のフォームフィールド生成ロジック ---------
            existing_value = (
                ProfileFieldValue.objects
                .filter(user_profile=user_profile, field=pf)
                .values_list('value', flat=True)
                .first() or ""
            )
            existing_list = existing_value.split(",") if existing_value else []

            if pf.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=pf.field_label,
                    required=False,
                    initial=existing_value,
                )

            elif pf.field_type in ('select', 'radio'):
                choices = [(c.strip(), c.strip())
                           for c in pf.field_choices.splitlines() if c.strip()]
                widget = forms.RadioSelect if pf.field_type == 'radio' else None
                self.fields[field_name] = forms.ChoiceField(
                    label=pf.field_label,
                    choices=choices,
                    widget=widget,
                    required=False,
                    initial=existing_value,
                )

            elif pf.field_type == 'checkbox':
                choices = [(c.strip(), c.strip())
                           for c in pf.field_choices.splitlines() if c.strip()]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=pf.field_label,
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                    initial=existing_list,
                )


    # -------------------------------------------------
    # 保存ロジック
    # -------------------------------------------------
    def save(self):
        for field_name, value in self.cleaned_data.items():
            key = field_name.replace("dynamic_", "", 1)
            pf = ProfileField.objects.get(field_key=key)

            if pf.field_type == 'checkbox':
                value = ",".join(value)  # list → CSV

            pfv, _ = ProfileFieldValue.objects.get_or_create(
                user_profile=self.user_profile,
                field=pf
            )
            pfv.value = value
            pfv.save()



class CustomSignupForm(SignupForm):
    nickname = forms.CharField(label='ニックネーム', max_length=100)
    GENDER_CHOICES = (('male', '男性'), ('female', '女性'))
    gender = forms.ChoiceField(
        label='性別',
        choices=GENDER_CHOICES,
        widget=forms.RadioSelect
    )

    SEXUAL_OBJECT_CHOICES = (
        ('male', '男性'),
        ('female', '女性'),
    )
    sexual_object_pref = forms.ChoiceField(
        label='恋愛対象',
        choices=SEXUAL_OBJECT_CHOICES,
         widget=forms.RadioSelect
    )
    main_area = forms.CharField  (label='居住地', max_length=30)

    def save(self, request):
        # 1) allauth が User を生成
        user = super().save(request)

        # 2) UserProfile を作成 / 更新
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.gender    = self.cleaned_data['gender']
        profile.main_area = self.cleaned_data['main_area']
        profile.nickname = self.cleaned_data['nickname']
        profile.sexual_object_pref = self.cleaned_data['sexual_object_pref']

        profile.save()

        return user


class ContactForm(forms.Form):
    SUBJECT_CHOICES = (
        ("general",    "サービス全般について"),
        ("bug_report", "不具合報告"),
        ("payment",    "決済関連"),
        ("other",      "その他"),
    )

    subject = forms.ChoiceField(
        label="お問い合わせ種別",
        choices=SUBJECT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    email   = forms.EmailField(label="メールアドレス", max_length=255)
    name    = forms.CharField(label="お名前", max_length=50)
    message = forms.CharField(
        label="お問い合わせ内容",
        widget=forms.Textarea(attrs={"rows": 6})
    )

    @classmethod
    def for_user(cls, user):
        """
        ログインユーザの情報で初期値をセットしたフォームを返す。
        未ログインなら空フォーム。
        """
        if not user.is_authenticated:
            return cls()

        prof   = getattr(user, "userprofile", None)
        name   = getattr(prof, "nickname", "") or user.get_full_name() or user.username
        return cls(initial={
            "email": user.email,
            "name":  name,
        })