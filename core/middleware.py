# core/middleware.py
import threading
from core.models import set_current_user

_local = threading.local()

def get_current_user():
    return getattr(_local, "user", None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            set_current_user(user)
        else:
            set_current_user(None)
        try:
            return self.get_response(request)
        finally:
            set_current_user(None)
