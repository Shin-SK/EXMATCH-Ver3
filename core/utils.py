# core/utils.py
import math, requests
from django.db.models import Q, Prefetch
from core.models import Match, ProfileFieldValue, ProfileField
import re
import unicodedata
from django.conf import settings
from django.contrib.auth import get_user_model 

from django.db.models import Q, Count, Case, When, Value, IntegerField
from .models import UserProfile, VerificationSubmission


def get_matched_users(user):
    """
    ログインユーザーと 'matched' 状態の相手ユーザーをリストで返す
    """
    records = Match.objects.filter(
        Q(from_user=user, status='matched') |
        Q(to_user=user,   status='matched')
    ).select_related('from_user', 'to_user').order_by('-created_at')

    seen, users = set(), []
    for m in records:
        partner = m.to_user if m.from_user == user else m.from_user
        if partner.id not in seen:
            users.append(partner)
            seen.add(partner.id)
    return users


def geocode_address(address):
    api_key = "AIzaSyCnyO6_HZoOw-DZrE3D_6vZjTV_6J-l16I"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    resp = requests.get(url)
    data = resp.json()
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return (location['lat'], location['lng'])
    return (None, None)


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # 地球の半径(km)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def unverified(user):
    """ログイン済み & LCIQ入力済みなら False → ぼかさない"""
    return (not user.is_authenticated) or not getattr(user.userprofile, "lciq", "")




def attach_normal_pfv(user_qs):
    normal_pfv = Prefetch(
        "userprofile__profilefieldvalue_set",
        queryset=ProfileFieldValue.objects
                 .select_related("field")
                 .filter(field__category="normal"),
        to_attr="normal_pfvs"
    )
    return user_qs.prefetch_related(normal_pfv)


#誹謗中傷ワード系

# ひらがな⇔カタカナ変換用
_kana_table = str.maketrans(
    "ぁあぃいぅうぇえぉおゃやゅゆょよっゎわゐゑゕゖゔ",
    "ァアィイゥウェエォオャヤュユョヨッヮワヰヱヵヶヴ"
)

def _normalize(text: str) -> str:
    # 半角→全角・大文字小文字統一など
    text = unicodedata.normalize('NFKC', text)
    # カタカナをひらがなに寄せる（or 逆でも可）
    text = text.translate(_kana_table)
    return text.lower()

NG_PATTERNS = [re.compile(re.escape(_normalize(w))) for w in settings.NG_WORDS]

def contains_ng(text: str) -> bool:
    norm = _normalize(text)
    return any(p.search(norm) for p in NG_PATTERNS)




def order_by_quality(user_ids):
    profiles = (
        UserProfile.objects
        .filter(user_id__in=user_ids)
        .annotate(
            has_lciq=Case(
                When(lciq_image__isnull=False, then=Value(1)),
                default=Value(0), output_field=IntegerField()),
            verified_docs=Count(
                'user__verifications__doc_type',
                filter=Q(user__verifications__status=
                         VerificationSubmission.Status.APPROVED),
                distinct=True)
        )
        .order_by('-has_lciq', '-verified_docs', '-user__last_login')
    )
    ordered_ids = list(profiles.values_list('user_id', flat=True))
    when = [When(id=pk, then=pos) for pos, pk in enumerate(ordered_ids)]
    return attach_normal_pfv(
        get_user_model().objects
        .filter(id__in=ordered_ids)
        .annotate(_o=Case(*when, output_field=IntegerField()))
        .order_by('_o')
    )
