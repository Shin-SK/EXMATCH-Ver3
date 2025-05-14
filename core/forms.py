# core/forms.py
from django import forms
from allauth.account.forms import SignupForm
from .models import (
    UserProfile,
    ProfileField,
    ProfileFieldValue,
)


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
            # 必要に応じて他の項目も
        ]


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
    """
    通常フィールド + プラスフィールド をまとめて動的生成するフォーム
    - プラスフィールド(category='plus') は
      user_profile.is_standard_plan() or user_profile.has_option() が True のときだけ表示
    """

    def __init__(self, *args, user_profile: UserProfile, **kwargs):
        self.user_profile = user_profile
        super().__init__(*args, **kwargs)

        # -------------------------------------------------
        # 権限判定：プラスプロフィールを編集できるか？
        # -------------------------------------------------
        can_use_plus = (
            user_profile.is_standard_plan() or
            user_profile.has_option()
        )

        # 取得対象
        qs = ProfileField.objects.all()
        if not can_use_plus:
            qs = qs.filter(category='normal')   # plus は除外

        for pf in qs:
            field_name = f"dynamic_{pf.field_key}"

            # 既存値を取得
            existing_value = (
                ProfileFieldValue.objects
                .filter(user_profile=user_profile, field=pf)
                .values_list('value', flat=True)
                .first() or ""
            )
            existing_list = existing_value.split(",") if existing_value else []

            # -------------------------------------------------
            # フィールド種別ごとのフォームフィールド生成
            # -------------------------------------------------
            if pf.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=pf.field_label,
                    required=False,
                    initial=existing_value
                )

            elif pf.field_type in ('select', 'radio'):
                choices = [
                    (c.strip(), c.strip())
                    for c in pf.field_choices.splitlines()
                    if c.strip()
                ]
                widget = forms.RadioSelect if pf.field_type == 'radio' else None
                self.fields[field_name] = forms.ChoiceField(
                    label=pf.field_label,
                    choices=choices,
                    widget=widget,
                    required=False,
                    initial=existing_value
                )

            elif pf.field_type == 'checkbox':
                choices = [
                    (c.strip(), c.strip())
                    for c in pf.field_choices.splitlines()
                    if c.strip()
                ]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=pf.field_label,
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                    initial=existing_list
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
    gender = forms.ChoiceField(label='性別', choices=GENDER_CHOICES)
    SEXUAL_OBJECT_CHOICES = (
        ('male', '男性'),
        ('female', '女性'),
    )
    sexual_object_pref = forms.ChoiceField(label='恋愛対象', choices=SEXUAL_OBJECT_CHOICES)
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
