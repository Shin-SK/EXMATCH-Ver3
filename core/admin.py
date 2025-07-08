from django.contrib import admin
from .models import UserProfile, Match, Message, ProfileField, ProfileFieldValue, Footprint, VerificationSubmission
from django.utils import timezone    
from .utils import geocode_address

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'nickname',
        'sexual_object_pref',
        'gender',
        'plan_expiry',
        'option_expiry',
        'main_area',
        'latitude',
        'longitude'
    )
    list_filter = ('blood_type', 'plan_expiry', 'option_expiry')


    def save_model(self, request, obj, form, change):
        # メインエリアが入力されていればジオコーディング
        if obj.main_area:
            lat, lng = geocode_address(obj.main_area)
            obj.latitude = lat
            obj.longitude = lng
        super().save_model(request, obj, form, change)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status', 'created_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'text', 'created_at')
    list_filter = ('sender', 'receiver', 'created_at')


@admin.register(ProfileField)
class ProfileFieldAdmin(admin.ModelAdmin):
    list_display = ('field_key', 'field_label', 'category', 'field_type')
    list_filter = ('field_type',)


@admin.register(ProfileFieldValue)
class ProfileFieldValueAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'field', 'value')
    list_filter = ('field',)


# 追加：Footprint を管理画面に登録
@admin.register(Footprint)
class FootprintAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at')
    list_filter = ('created_at',)
    autocomplete_fields = ('from_user', 'to_user')
    readonly_fields = ('created_at',)         # 作成日時は自動付与  



@admin.register(VerificationSubmission)
class VerificationSubmissionAdmin(admin.ModelAdmin):
	list_display	= ('user', 'doc_type', 'status', 'submitted_at', 'reviewed_at')
	list_filter		= ('doc_type', 'status')
	search_fields	= ('user__username',)
	readonly_fields	= ('submitted_at',)