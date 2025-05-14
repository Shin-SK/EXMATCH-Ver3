from .utils import unverified
def blur_flag(request):
    """
    template では {{ unverified }} という真偽値だけを使う。
    """
    return {"unverified": unverified(request.user)}