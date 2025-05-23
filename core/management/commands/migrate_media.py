from pathlib import Path
from django.core.management.base import BaseCommand
from django.apps import apps
from cloudinary.uploader import upload

class Command(BaseCommand):
    help = "Upload local media files to Cloudinary and fix DB paths."

    def handle(self, *args, **kwargs):
        UserProfile = apps.get_model("core", "UserProfile")

        for p in UserProfile.objects.exclude(profile_image="").iterator():
            # 既に Cloudinary にある場合はスキップ
            if p.profile_image.name.startswith("http") or "res.cloudinary" in p.profile_image.url:
                continue

            local_path = Path(p.profile_image.path)
            if not local_path.exists():
                self.stdout.write(f"× File not found: {local_path}")
                continue

            res = upload(local_path, folder="profiles")
            # public_id + 拡張子を保存（CloudinaryStorage が自動で完全URLへ解決）
            p.profile_image.name = f"{res['public_id']}.{res['format']}"
            p.save(update_fields=["profile_image"])
            self.stdout.write(f"✓ {local_path.name} → {res['public_id']}")
