# core/management/commands/fix_profile_path.py
from django.core.management.base import BaseCommand
from django.apps import apps

PREFIX = "media/"               # ← ここだけ合わせる

class Command(BaseCommand):
    help = "Remove old prefix from profile_image names."

    def handle(self, *args, **kwargs):
        UserProfile = apps.get_model("core", "UserProfile")
        qs = UserProfile.objects.filter(profile_image__startswith=PREFIX)
        for p in qs.iterator():
            p.profile_image.name = p.profile_image.name[len(PREFIX):]
            p.save(update_fields=["profile_image"])
        self.stdout.write(self.style.SUCCESS(f"fixed {qs.count()} records."))
