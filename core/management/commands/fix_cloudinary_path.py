from django.core.management.base import BaseCommand
from django.apps import apps
from cloudinary import api        # pip install cloudinary

PREFIX = "media/profiles/"        # いま DB に残っている頭

class Command(BaseCommand):
    help = "media/profiles/xxx → profiles/xxx.<ext> に修正して Cloudinary URL を有効化"

    def handle(self, *args, **kwargs):
        UserProfile = apps.get_model("core", "UserProfile")

        qs = UserProfile.objects.filter(profile_image__startswith=PREFIX)
        fixed = 0

        for p in qs.iterator():
            public_id = p.profile_image.name[len(PREFIX):]        # 例: pj2rzkf...
            meta = api.resource(f"profiles/{public_id}")          # Cloudinary から拡張子取得
            p.profile_image.name = f"profiles/{public_id}.{meta['format']}"
            p.save(update_fields=["profile_image"])
            fixed += 1

        self.stdout.write(self.style.SUCCESS(f"fixed {fixed} records"))
