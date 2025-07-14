# core/middleware.py
import threading

_local = threading.local()

def get_current_user():
    return getattr(_local, "user", None)

class CurrentUserMiddleware:
    """リクエスト毎に現在のユーザーを thread-local に保存"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, "user", None)
        response = self.get_response(request)
        return response
