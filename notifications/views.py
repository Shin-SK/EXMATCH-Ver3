# notifications/views.py
from django.http import JsonResponse
from .models import Notification
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from core.models import Message

@login_required
def unread_count(request):
    # ------ チャットの Notification だけを対象にする ------
    msg_ct = ContentType.objects.get_for_model(Message)

    cnt = (Notification.objects
           .filter(user=request.user,
                   content_type=msg_ct,      # または verb="message"
                   is_read=False)
           .count())
    return JsonResponse({"unread": cnt})

def list_notifications(request):
    qs = Notification.objects.filter(user=request.user).values(
        'id', 'verb', 'text', 'created_at', 'is_read')
    return JsonResponse({'items': list(qs)})
