# core/admin.py
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import get_user_model
from .utils import geocode_address

from .models import (
    UserProfile, Match, Message,
    ProfileField, ProfileFieldValue,
    Footprint, VerificationSubmission, Report, Block,
    MatchingRuleSet, MatchingRule,
)

# === import-export ===
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats

User = get_user_model()


# ---------- Resources（フィールド定義）----------
# core/admin.py

class UserProfileResource(resources.ModelResource):
    user = fields.Field(
        column_name='username',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = UserProfile
        import_id_fields = ('user',)

        # 画像は除外のままでOK
        exclude = (
            'lciq_image',
            'id_doc_image',
        )

        # ここを追加：インポート対象の列を明示
        fields = (
            'user',                 # ← column_name が username になる
            'nickname',
            'blood_type',
            'gender',
            'sexual_object_pref',
            'plan',
            'lciq_score',
            'plan_expiry',
            'option_expiry',
            'date_of_birth',
            'main_area',
            'latitude',
            'longitude',
            'id_doc_verified',      # 使うなら（adminでexcludeしてるけどCSV入力は可にしたい場合）
        )
        export_order = fields

class ProfileFieldResource(resources.ModelResource):
    class Meta:
        model = ProfileField
        import_id_fields = ('field_key',)  # keyでupsert
        fields = ('id','field_key','field_label','field_type','category','required','field_choices')
        export_order = fields

class ProfileFieldValueResource(resources.ModelResource):
    # user_profile(FK) を username で紐づけ
    user_profile = fields.Field(
        column_name='username',
        attribute='user_profile',
        widget=ForeignKeyWidget(UserProfile, 'user__username')
    )
    # field(FK) を field_key で紐づけ
    field = fields.Field(
        column_name='field_key',
        attribute='field',
        widget=ForeignKeyWidget(ProfileField, 'field_key')
    )

    class Meta:
        model = ProfileFieldValue
        # (username, field_key) で upsert
        import_id_fields = ('user_profile','field')
        fields = ('id','user_profile','field','value')
        export_order = fields

# 以降は“ID主キー”でのupsert（必要に応じて拡張可）
class MatchResource(resources.ModelResource):
    from_user = fields.Field(column_name='from_username',
                             attribute='from_user',
                             widget=ForeignKeyWidget(User, 'username'))
    to_user   = fields.Field(column_name='to_username',
                             attribute='to_user',
                             widget=ForeignKeyWidget(User, 'username'))
    class Meta:
        model = Match
        import_id_fields = ('id',)
        fields = ('id','from_user','to_user','status','created_at')
        export_order = fields

class MessageResource(resources.ModelResource):
    sender   = fields.Field(column_name='from_username',
                            attribute='sender',
                            widget=ForeignKeyWidget(User, 'username'))
    receiver = fields.Field(column_name='to_username',
                            attribute='receiver',
                            widget=ForeignKeyWidget(User, 'username'))
    class Meta:
        model = Message
        import_id_fields = ('id',)
        fields = ('id','sender','receiver','text','created_at')
        export_order = fields

class FootprintResource(resources.ModelResource):
    from_user = fields.Field(column_name='from_username',
                             attribute='from_user',
                             widget=ForeignKeyWidget(User, 'username'))
    to_user   = fields.Field(column_name='to_username',
                             attribute='to_user',
                             widget=ForeignKeyWidget(User, 'username'))
    class Meta:
        model = Footprint
        import_id_fields = ('id',)
        fields = ('id','from_user','to_user','created_at')
        export_order = fields

class VerificationSubmissionResource(resources.ModelResource):
    user = fields.Field(column_name='username',
                        attribute='user',
                        widget=ForeignKeyWidget(User, 'username'))
    class Meta:
        model = VerificationSubmission
        import_id_fields = ('id',)
        fields = ('id','user','doc_type','status','submitted_at','reviewed_at')
        export_order = fields

class ReportResource(resources.ModelResource):
    reporter = fields.Field(column_name='reporter_username',
                            attribute='reporter',
                            widget=ForeignKeyWidget(User, 'username'))
    reported = fields.Field(column_name='reported_username',
                            attribute='reported',
                            widget=ForeignKeyWidget(User, 'username'))
    class Meta:
        model = Report
        import_id_fields = ('id',)
        fields = ('id','reported','reporter','reason','status','created_at')
        export_order = fields

class BlockResource(resources.ModelResource):
    blocker = fields.Field(column_name='blocker_username',
                           attribute='blocker',
                           widget=ForeignKeyWidget(User, 'username'))
    blocked = fields.Field(column_name='blocked_username',
                           attribute='blocked',
                           widget=ForeignKeyWidget(User, 'username'))
    class Meta:
        model = Block
        import_id_fields = ('id',)
        fields = ('id','blocker','blocked','created_at')
        export_order = fields


# ---------- Admin（右上ボタン・CSV限定）----------
class CSVOnlyAdmin(ImportExportModelAdmin):
    # 右上の Import / Export を CSV のみに制限
    def get_import_formats(self):
        return [base_formats.CSV]
    def get_export_formats(self):
        return [base_formats.CSV]


@admin.register(UserProfile)
class UserProfileAdmin(CSVOnlyAdmin):
    resource_classes = [UserProfileResource]
    # 旧項目は触らせない（混乱防止）
    exclude = ('id_doc_image', 'id_doc_verified',)
    list_display = (
        'user','nickname','gender','plan',
        'main_area','latitude','longitude',
        # 進捗が一目でわかるように追加
        'verification_count','verification_badge',
    )
    list_filter = ('gender','plan',)

    def save_model(self, request, obj, form, change):
        if obj.main_area:
            lat, lng = geocode_address(obj.main_area)
            obj.latitude = lat
            obj.longitude = lng
        super().save_model(request, obj, form, change)


@admin.register(ProfileField)
class ProfileFieldAdmin(CSVOnlyAdmin):
    resource_classes = [ProfileFieldResource]
    list_display = ('field_key','field_label','category','field_type')
    list_filter = ('field_type',)


@admin.register(ProfileFieldValue)
class ProfileFieldValueAdmin(CSVOnlyAdmin):
    resource_classes = [ProfileFieldValueResource]
    list_display = ('user_profile','field','value')
    list_filter = ('field',)


@admin.register(Match)
class MatchAdmin(CSVOnlyAdmin):
    resource_classes = [MatchResource]
    list_display = ('from_user','to_user','status','created_at')
    list_filter = ('status','created_at')


@admin.register(Message)
class MessageAdmin(CSVOnlyAdmin):
    resource_classes = [MessageResource]
    list_display = ('sender','receiver','text','created_at')
    list_filter = ('sender','receiver','created_at')


@admin.register(Footprint)
class FootprintAdmin(CSVOnlyAdmin):
    resource_classes = [FootprintResource]
    list_display = ('from_user','to_user','created_at')
    list_filter = ('created_at',)
    autocomplete_fields = ('from_user','to_user')
    readonly_fields = ('created_at',)


@admin.register(VerificationSubmission)
class VerificationSubmissionAdmin(CSVOnlyAdmin):
    resource_classes = [VerificationSubmissionResource]
    list_display = ('user','doc_type','status','submitted_at','reviewed_at')
    list_filter = ('doc_type','status')
    search_fields = ('user__username',)
    readonly_fields = ('submitted_at',)


@admin.register(Report)
class ReportAdmin(CSVOnlyAdmin):
    resource_classes = [ReportResource]
    list_display = ("reported","reporter","reason","status","created_at")


@admin.register(Block)
class BlockAdmin(CSVOnlyAdmin):
    resource_classes = [BlockResource]
    list_display = ('blocker','blocked','created_at')



class MatchingRuleResource(resources.ModelResource):
    field = fields.Field(
        column_name='field_key',
        attribute='field',
        widget=ForeignKeyWidget(ProfileField, 'field_key')
    )

    class Meta:
        model = MatchingRule
        import_id_fields = ('id',)
        fields = ('id', 'ruleset', 'field', 'mode', 'weight', 'desired_value', 'match_type', 'enabled')
        export_order = fields


class MatchingRuleInline(admin.TabularInline):
    model = MatchingRule
    extra = 1
    fields = ('field', 'mode', 'weight', 'desired_value', 'match_type', 'enabled')


@admin.register(MatchingRuleSet)
class MatchingRuleSetAdmin(CSVOnlyAdmin):
    list_display = ('name', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    inlines = [MatchingRuleInline]


@admin.register(MatchingRule)
class MatchingRuleAdmin(CSVOnlyAdmin):
    resource_classes = [MatchingRuleResource]
    list_display = ('ruleset', 'field', 'mode', 'weight', 'desired_value', 'match_type', 'enabled')
    list_filter = ('ruleset', 'mode', 'match_type', 'enabled')
