# core/templatetags/profile_extras.py
from django import template
register = template.Library()

@register.filter
def pfv_value(pfvs, lookup_key):          # ‹lookup_key 例: 'age'
    """
    normal_pfvs の中から field.field_key == lookup_key の value を返す
    無ければ '' を返す
    """
    for pfv in pfvs:
        if pfv.field.field_key == lookup_key:     # ← ここを field_key に
            return pfv.value
    return ''
