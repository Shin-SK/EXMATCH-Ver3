from django import template
from django.db.models import Q
from core.models import Match

register = template.Library()

@register.filter
def is_matched(target, me):
    return Match.objects.filter(
        Q(from_user=me, to_user=target, status='matched') |
        Q(from_user=target, to_user=me, status='matched')
    ).exists()
