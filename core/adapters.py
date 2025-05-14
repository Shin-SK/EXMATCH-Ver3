# core/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):
    """メール確認フローのリダイレクト先を制御"""

    # 確認リンクをクリックした直後（GET）のリダイレクト
    def get_email_confirmation_redirect_url(self, request, confirmation):
        if request.user.is_authenticated:
            return reverse("profile_first_edit")   # /signup/profile/
        return super().get_email_confirmation_redirect_url(request, confirmation)

    # 「確認する」ボタンを押したあと complete_signup() で呼ばれる
    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_authenticated:
            profile = getattr(user, "userprofile", None)
            if profile and not getattr(profile, "finished_first_edit", False):
                return reverse("profile_first_edit")
        return super().get_login_redirect_url(request)
