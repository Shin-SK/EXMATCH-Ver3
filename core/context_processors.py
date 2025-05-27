# core/context_processors.py
from core.utils import get_matched_users
from .utils import unverified


def blur_flag(request):
    """
    template では {{ unverified }} という真偽値だけを使う。
    """
    return {"unverified": unverified(request.user)}


def matched_set(request):
    if request.user.is_authenticated:
        return {"matched_set": {u.id for u in get_matched_users(request.user)}}
    return {"matched_set": set()}