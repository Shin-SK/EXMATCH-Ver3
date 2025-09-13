# accounts/models.py
from django.contrib.auth.models import AbstractUser, UserManager

class User(AbstractUser):
	# まずは既存の機能そのまま。必要なら後でフィールド追加OK
	objects = UserManager()

	class Meta:
		db_table = 'auth_user'          # ★既存テーブルをそのまま使う
		verbose_name = 'ユーザー'
		verbose_name_plural = 'ユーザー'
