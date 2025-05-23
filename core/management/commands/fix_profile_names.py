# core/management/commands/fix_profile_names.py
from django.core.management.base import BaseCommand
from django.apps import apps
from cloudinary import api

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        UserProfile = apps.get_model("core", "UserProfile")
        qs = UserProfile.objects.filter(profile_image__startswith="profiles/")
        fixed = 0
        for p in qs.iterator():
            pid = p.profile_image.name.split("/")[-1]          # pj2rzkf…
            if "." in pid:          # すでに拡張子付きならスキップ
                continue
            meta = api.resource(f"profiles/{pid}")
            p.profile_image.name = f"profiles/{pid}.{meta['format']}"
            p.save(update_fields=["profile_image"])
            fixed += 1
        self.stdout.write(f"fixed {fixed} records")
