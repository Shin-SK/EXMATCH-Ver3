# core/api_views_csrf.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.middleware.csrf import get_token

class CsrfAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # csrftokenクッキーも同時に送られる
        return Response({"csrfToken": get_token(request)})
