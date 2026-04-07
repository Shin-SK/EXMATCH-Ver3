"""
既存の UserProfile.profile_image を ProfilePhoto に移行するデータマイグレーション。
- 画像がある各ユーザーについて、order=0 で ProfilePhoto を1件作成
- 元の profile_image フィールドはそのまま残す（後方互換）
"""
from django.db import migrations


def forward(apps, schema_editor):
    UserProfile = apps.get_model('core', 'UserProfile')
    ProfilePhoto = apps.get_model('core', 'ProfilePhoto')

    profiles = UserProfile.objects.exclude(
        profile_image__isnull=True
    ).exclude(
        profile_image=''
    ).select_related('user')

    to_create = []
    for prof in profiles:
        # 既に ProfilePhoto がある場合はスキップ（冪等性）
        if ProfilePhoto.objects.filter(user=prof.user).exists():
            continue
        to_create.append(ProfilePhoto(
            user=prof.user,
            image=prof.profile_image.name,
            order=0,
        ))

    if to_create:
        ProfilePhoto.objects.bulk_create(to_create)


def backward(apps, schema_editor):
    # backward は何もしない（profile_image は残っているので安全）
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_profilephoto'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
