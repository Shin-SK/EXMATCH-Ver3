# core/utils.py
import math, requests
from django.db.models import Q
from core.models import Match

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