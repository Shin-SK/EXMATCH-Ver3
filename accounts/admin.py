from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import User


class UserResource(resources.ModelResource):
	class Meta:
		model = User
		import_id_fields = ("username",)  # ← usernameで照合
		exclude = ("id",)  # idは衝突の元になるため除外


@admin.register(User)
class MyUserAdmin(ImportExportModelAdmin, UserAdmin):
	resource_class = UserResource
	search_fields = ('username', 'email', 'first_name', 'last_name')
