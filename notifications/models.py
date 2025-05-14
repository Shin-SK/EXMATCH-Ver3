# notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Notification(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    # 何のイベントかを汎用に紐付け
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id    = models.PositiveIntegerField()
    target       = GenericForeignKey('content_type', 'object_id')

    verb        = models.CharField(max_length=50)     # 'message', 'match' など
    text        = models.CharField(max_length=255)    # 一覧に表示する文
    created_at  = models.DateTimeField(auto_now_add=True)
    is_read     = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
