# notifications/views.py
from django.http import JsonResponse
from .models import Notification
from django.contrib.auth.decorators import login_required

@login_required  
def unread_count(request):
    cnt = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread': cnt})

def list_notifications(request):
    qs = Notification.objects.filter(user=request.user).values(
        'id', 'verb', 'text', 'created_at', 'is_read')
    return JsonResponse({'items': list(qs)})
