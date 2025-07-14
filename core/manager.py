from django.db import models
from django.conf import settings

class UserQuerySet(models.QuerySet):
    def exclude_blocked_for(self, user):
        from core.models import Block
        blocked_ids = Block.objects.filter(blocker=user)\
                                   .values_list('blocked_id', flat=True)
        blockers_ids = Block.objects.filter(blocked=user)\
                                    .values_list('blocker_id', flat=True)
        return self.exclude(id__in=blocked_ids).exclude(id__in=blockers_ids)