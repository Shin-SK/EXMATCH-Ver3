# notifications/views.py
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Notification
from core.models import Message


class UnreadCountAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        msg_ct = ContentType.objects.get_for_model(Message)
        cnt = Notification.objects.filter(
            user=request.user, content_type=msg_ct, is_read=False
        ).count()
        return Response({"unread": cnt})


class NotificationsListAPI(APIView):
    """GET /api/notifications/?page=1"""
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        items = [
            {
                "id": n.id,
                "verb": n.verb,
                "text": n.text,
                "is_read": n.is_read,
                "created_at": n.created_at,
            } for n in page
        ]
        return paginator.get_paginated_response(items)


class NotificationMarkReadAPI(APIView):
    """POST /api/notifications/<id>/read/"""
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        n = get_object_or_404(Notification, id=pk, user=request.user)
        if not n.is_read:
            n.is_read = True
            n.save(update_fields=["is_read"])
        return Response({"ok": True, "is_read": True})


class NotificationReadAllAPI(APIView):
    """POST /api/notifications/read-all/"""
    permission_classes = [IsAuthenticated]
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"ok": True})
