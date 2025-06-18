# core/mixins.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

# --- クラスベースビュー用 -----------------------
class IdentityVerifiedRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.userprofile.is_verified:
            return redirect('my_page')          # マイページへ戻す
        return super().dispatch(request, *args, **kwargs)

# --- 関数ビュー用 -------------------------------
def identity_verified_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if (request.user.is_authenticated and
                not request.user.userprofile.is_verified):
            return redirect('my_page')
        return view_func(request, *args, **kwargs)
    return _wrapped
