# core/api_serializers.py
from datetime import date
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (UserProfile, Match, Message, Footprint, Report, ProfileField, VerificationSubmission,
)
from .utils import geocode_address


User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")

class ProfileSerializer(serializers.ModelSerializer):
    id                  = serializers.SerializerMethodField()   # user.id を返す
    username            = serializers.SerializerMethodField()
    profile_image_url   = serializers.SerializerMethodField()
    lciq_image_url      = serializers.SerializerMethodField()
    age                 = serializers.SerializerMethodField()
    verification_badge  = serializers.SerializerMethodField()
    verification_count  = serializers.SerializerMethodField()
    is_profile_complete = serializers.SerializerMethodField()   # ★追加
    latitude            = serializers.SerializerMethodField()
    longitude           = serializers.SerializerMethodField()

    class Meta:
        model  = UserProfile
        fields = (
            "id","username",
            "nickname","bio","main_area","date_of_birth",
            "age","profile_image_url","lciq_image_url",
            "blood_type","gender","sexual_object_pref",
            "plan","plan_expiry","option_expiry",
            "lciq_score","id_doc_verified",
            "latitude","longitude",
            "verification_badge","verification_count",
            "is_profile_complete",                           # ★追加
        )

    # ------- 既存のユーティリティ（抜粋） -------
    def _abs_url(self, url):
        req = self.context.get("request")
        return req.build_absolute_uri(url) if (req and url) else url

    def get_id(self, obj):
        return obj.user_id

    def get_username(self, obj):
        return getattr(obj.user, "username", None)

    def get_profile_image_url(self, obj):
        f = getattr(obj, "profile_image", None)
        if f and getattr(f, "name", ""):
            return self._abs_url(f.url)
        return None

    def get_lciq_image_url(self, obj):
        f = getattr(obj, "lciq_image", None)
        if f and getattr(f, "name", ""):
            return self._abs_url(f.url)
        return None

    def get_age(self, obj):
        from datetime import date
        if not obj.date_of_birth:
            return None
        d, t = obj.date_of_birth, date.today()
        return t.year - d.year - ((t.month, t.day) < (d.month, d.day))

    def get_latitude(self, obj):
        """住所特定防止のため小数第1位に丸める（約10km精度）"""
        if obj.latitude is None:
            return None
        return round(float(obj.latitude), 1)

    def get_longitude(self, obj):
        if obj.longitude is None:
            return None
        return round(float(obj.longitude), 1)

    def get_verification_badge(self, obj):
        cnt = self.get_verification_count(obj)
        if cnt == 0:
            return None
        return {1: 'blue', 2: 'pink', 3: 'silver'}.get(cnt, 'gold')

    def get_verification_count(self, obj):
        # annotate 済みなら DB アクセスしない
        if hasattr(obj, '_verification_count'):
            return obj._verification_count
        return obj.verification_count

    # ------- ここが肝：必須項目の充足で判定 -------
    def get_is_profile_complete(self, obj):
        ok_nickname  = bool(obj.nickname and obj.nickname.strip())
        ok_avatar    = bool(getattr(obj, "profile_image", None) and getattr(obj.profile_image, "name", ""))
        ok_blood     = bool(obj.blood_type)
        ok_gender    = bool(obj.gender)
        ok_pref      = bool(obj.sexual_object_pref)
        ok_dob       = bool(obj.date_of_birth)
        ok_main_area = bool(obj.main_area)
        return all([ok_nickname, ok_avatar, ok_blood, ok_gender, ok_pref, ok_dob, ok_main_area])



class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "nickname","bio","main_area","date_of_birth",
            "blood_type","gender","sexual_object_pref",
            "latitude","longitude",
            "lciq_score",                     # ★任意を保存できるように追加
        )

    def update(self, instance, validated_data):
        old_area = instance.main_area
        res = super().update(instance, validated_data)

        # main_area 変更 & 緯度経度未指定なら自動ジオコード（既存動作）
        from .utils import geocode_address
        area_changed = "main_area" in validated_data and (validated_data["main_area"] or "") != (old_area or "")
        lat_given    = "latitude" in validated_data
        lon_given    = "longitude" in validated_data
        if area_changed and not (lat_given and lon_given):
            lat, lon = geocode_address(validated_data["main_area"])
            if lat is not None and lon is not None:
                instance.latitude  = lat
                instance.longitude = lon
                instance.save(update_fields=["latitude","longitude"])
        return res
    


class MatchSerializer(serializers.ModelSerializer):
    partner = serializers.SerializerMethodField()
    class Meta:
        model  = Match
        fields = ("id","status","created_at","partner")
    def get_partner(self, obj):
        me = self.context["request"].user
        other = obj.to_user if obj.from_user_id == me.id else obj.from_user
        return ProfileSerializer(other.userprofile, context=self.context).data
    



class MessageSerializer(serializers.ModelSerializer):
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model  = Message
        fields = ("id", "text", "is_mine", "created_at", "sender", "receiver")
        extra_kwargs = {
            "text": {"trim_whitespace": False},  # 末尾の全角/半角記号も保持
        }

    def get_is_mine(self, obj):
        req = self.context.get("request")
        return bool(req and getattr(req, "user", None) and obj.sender_id == req.user.id)


class UserBriefSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    main_area = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    lciq_score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "nickname", "profile_image_url", "main_area", "age", "lciq_score")

    def get_nickname(self, obj):
        prof = getattr(obj, "userprofile", None)
        return getattr(prof, "nickname", None)

    def get_profile_image_url(self, obj):
        prof = getattr(obj, "userprofile", None)
        if prof and prof.profile_image and hasattr(prof.profile_image, "url"):
            req = self.context.get("request")
            url = prof.profile_image.url
            return req.build_absolute_uri(url) if req else url
        return None

    def get_main_area(self, obj):
        prof = getattr(obj, "userprofile", None)
        return getattr(prof, "main_area", None)

    def get_age(self, obj):
        prof = getattr(obj, "userprofile", None)
        dob = getattr(prof, "date_of_birth", None) if prof else None
        if not dob: return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_lciq_score(self, obj):
        prof = getattr(obj, "userprofile", None)
        return getattr(prof, "lciq_score", None)


class LikeReceivedSerializer(serializers.ModelSerializer):
    from_user = ProfileSerializer(source="from_user.userprofile", read_only=True)
    class Meta:
        model = Match
        fields = ("id","from_user","created_at")



class FootprintSerializer(serializers.ModelSerializer):
    from_user = UserBriefSerializer()

    class Meta:
        model = Footprint
        fields = ("id", "from_user", "created_at")




class ReportSerializer(serializers.ModelSerializer):
    reporter = UserBriefSerializer(read_only=True)
    reported = UserBriefSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ("id", "reporter", "reported", "reason", "comment", "status", "created_at")
        read_only_fields = ("id", "reporter", "status", "created_at")
        

class ProfileFieldSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = ProfileField
        fields = ("field_key","field_label","field_type","category","required","choices","field_choices")
        read_only_fields = ("field_choices",)

    def get_choices(self, obj):
        if not obj.field_choices:
            return []
        return [s.strip() for s in obj.field_choices.splitlines() if s.strip()]


class VerificationSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationSubmission
        fields = ("id","doc_type","status","submitted_at","reviewed_at","image")
        read_only_fields = fields


class LikeSentSerializer(serializers.ModelSerializer):
    to_user = ProfileSerializer(source="to_user.userprofile", read_only=True)
    class Meta:
        model = Match
        fields = ("id","to_user","created_at")



