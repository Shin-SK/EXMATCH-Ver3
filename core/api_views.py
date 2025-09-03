# core/api_views.py
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from math import cos, radians
from django.db.models import F, Value
from django.db.models.functions import Abs, Power

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (UserProfile,Match, Message, Block, Footprint, VerificationSubmission, ProfileField, ProfileFieldValue, Report, set_current_user,
)
from .api_serializers import (ProfileSerializer, ProfileUpdateSerializer, MatchSerializer, MessageSerializer, LikeReceivedSerializer, LikeSentSerializer, FootprintSerializer, UserBriefSerializer, ReportSerializer, VerificationSubmissionSerializer, ProfileFieldSerializer,
)

User = get_user_model()


class _Base(APIView):
    permission_classes = [IsAuthenticated]
    def initial(self, request, *args, **kwargs):
        # SafeUserManager のために現在ユーザーをセット
        set_current_user(request.user)
        return super().initial(request, *args, **kwargs)


class ProfilesAPI(_Base):
    """
    GET /api/profiles/?q=&gender=&has_image=&verified=&age_min=&age_max=&area=&plan=&radius=&lat=&lon=&two_way=1
    - デフォルトで「自分の sexual_object_pref に合う相手の gender」を適用
      ※ ただし ?gender=... が指定された場合はユーザー指定を優先（デフォルト絞り込みはスキップ）
    - ?two_way=1 で「相手の sexual_object_pref も自分の gender に合う」相互条件を追加
    """
    def get(self, request):
        # ─────────────────────────────────────────────────────────────
        # 0) 入力取得
        # ─────────────────────────────────────────────────────────────
        q = (request.GET.get("q") or "").strip()
        gender_param = request.GET.get("gender")
        two_way = (request.GET.get("two_way") or "").lower() in ("1", "true", "yes")

        # ─────────────────────────────────────────────────────────────
        # 1) ベースQS（自分自身とブロック相手を除外）
        # ─────────────────────────────────────────────────────────────
        blk_to = Block.objects.filter(blocker=request.user).values_list("blocked_id", flat=True)
        blk_from = Block.objects.filter(blocked=request.user).values_list("blocker_id", flat=True)
        qs = (UserProfile.objects
              .select_related("user")
              .exclude(user=request.user)
              .exclude(user_id__in=blk_to)
              .exclude(user_id__in=blk_from))

        # ─────────────────────────────────────────────────────────────
        # 2) デフォルト：自分の性指向で相手の gender を絞る
        #     - ?gender=... がある場合はユーザー指定を優先してスキップ
        # ─────────────────────────────────────────────────────────────
        if not gender_param:
            my_pref = getattr(request.user.userprofile, "sexual_object_pref", None)
            if my_pref:
                qs = qs.filter(gender=my_pref)

        # ─────────────────────────────────────────────────────────────
        # 3) 相互条件：相手の sexual_object_pref も自分の gender に合致（任意）
        #     - ?two_way=1 の時だけ適用
        # ─────────────────────────────────────────────────────────────
        if two_way:
            my_gender = getattr(request.user.userprofile, "gender", None)
            if my_gender:
                qs = qs.filter(sexual_object_pref=my_gender)

        # ─────────────────────────────────────────────────────────────
        # 4) キーワード検索（ニックネーム / 自己紹介 / 居住地）
        # ─────────────────────────────────────────────────────────────
        if q:
            qs = qs.filter(
                Q(nickname__icontains=q) |
                Q(bio__icontains=q) |
                Q(main_area__icontains=q)
            )

        # ─────────────────────────────────────────────────────────────
        # 5) 単項目フィルタ（gender/画像あり/本人確認/プラン/エリア）
        # ─────────────────────────────────────────────────────────────
        if gender_param in ("male", "female"):
            qs = qs.filter(gender=gender_param)

        if (request.GET.get("has_image") or "").lower() in ("1", "true", "yes"):
            qs = qs.filter(profile_image__isnull=False)

        if (request.GET.get("verified") or "").lower() in ("1", "true", "yes"):
            qs = qs.filter(
                Q(id_doc_verified=True) |
                Q(
                    user__verifications__doc_type=VerificationSubmission.DocType.IDENTIFY,
                    user__verifications__status=VerificationSubmission.Status.APPROVED
                )
            )

        plan = request.GET.get("plan")
        if plan in ("free", "standard"):
            qs = qs.filter(plan=plan)

        area = request.GET.get("area")
        if area:
            qs = qs.filter(main_area__icontains=area)

        # ─────────────────────────────────────────────────────────────
        # 6) 年齢フィルタ（生年月日から算出）
        # ─────────────────────────────────────────────────────────────
        today = date.today()

        def years_ago(n: int):
            # 例：年齢>=n → DOB <= years_ago(n)
            y = today.year - int(n)
            try:
                return date(y, today.month, today.day)
            except ValueError:
                # うるう日対策など
                return date(y, today.month, 28)

        age_min = request.GET.get("age_min")
        age_max = request.GET.get("age_max")
        if age_min:
            qs = qs.filter(date_of_birth__lte=years_ago(int(age_min)))
        if age_max:
            qs = qs.filter(date_of_birth__gte=years_ago(int(age_max)))

        # ─────────────────────────────────────────────────────────────
        # 7) 半径検索（km）
        #     - 与えられた中心座標に対してBBoxで荒く→円で厳密化→近い順
        # ─────────────────────────────────────────────────────────────
        near_sorted = False
        radius = (request.GET.get("radius") or "").strip()
        lat_s = (request.GET.get("lat") or "").strip()
        lon_s = (request.GET.get("lon") or "").strip()
        if radius and lat_s and lon_s:
            try:
                R = float(radius)
                lat0 = float(lat_s)
                lon0 = float(lon_s)

                # 緯度1度 ≒ 111.32 km、経度は緯度により収縮するので cos(lat) 補正
                lat_deg = R / 111.32
                lon_coef = max(0.1, cos(radians(lat0)))
                lon_deg = R / (111.32 * lon_coef)

                # ① BBox で荒く絞る
                qs = qs.filter(
                    latitude__isnull=False, longitude__isnull=False,
                    latitude__gte=lat0 - lat_deg, latitude__lte=lat0 + lat_deg,
                    longitude__gte=lon0 - lon_deg, longitude__lte=lon0 + lon_deg,
                )

                # ② 円で厳密化 & 近い順（距離² = dlat² + (dlon*cos(lat0))²）
                qs = qs.annotate(
                    _dlat=Abs(F('latitude') - Value(lat0)),
                    _dlon=Abs((F('longitude') - Value(lon0)) * Value(lon_coef)),
                ).annotate(
                    _d2=Power(F('_dlat'), 2) + Power(F('_dlon'), 2)
                ).filter(
                    _d2__lte=(lat_deg ** 2)
                ).order_by('_d2', '-id')

                near_sorted = True
            except ValueError:
                # パラメータが不正な場合は半径検索を無視
                pass

        # ─────────────────────────────────────────────────────────────
        # 8) ソート & distinct
        #     - 半径未指定時は新着順
        # ─────────────────────────────────────────────────────────────
        if not near_sorted:
            qs = qs.order_by('-id')
        qs = qs.distinct()

        # ─────────────────────────────────────────────────────────────
        # 9) ページング & レスポンス
        # ─────────────────────────────────────────────────────────────
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = ProfileSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)


class MeAPI(_Base):
    """GET/PATCH /api/me/"""
    def get(self, request):
        prof = request.user.userprofile
        return Response(ProfileSerializer(prof, context={"request": request}).data)

    def patch(self, request):
        prof = request.user.userprofile
        ser = ProfileUpdateSerializer(prof, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        # 反映確認用にフルを返す
        return Response(ProfileSerializer(prof, context={"request": request}).data)


# ↓ どこでもOK：クラスを2つ追加
class LikeAPI(_Base):
    """POST /api/like/  { "user_id": 2 }"""
    def post(self, request):
        me = request.user
        try:
            target_id = int(request.data.get("user_id"))
        except (TypeError, ValueError):
            return Response({"detail": "user_idが不正です"}, status=400)
        if target_id == me.id:
            return Response({"detail": "自分にはいいねできません"}, status=400)

        target = get_object_or_404(User.objects.all(), id=target_id)
        # 自分→相手 を like（既存があればそのまま）
        m, _ = Match.objects.get_or_create(
            from_user=me, to_user=target, defaults={"status": "like"}
        )

        # 相手→自分 が既に like なら双方 matched
        matched = Match.objects.filter(
            from_user=target, to_user=me, status="like"
        ).exists()
        if matched:
            Match.objects.filter(
                Q(from_user=me, to_user=target) | Q(from_user=target, to_user=me)
            ).update(status="matched")

        return Response({"ok": True, "matched": matched})

class MatchesAPI(_Base):
    """GET /api/matches/?page=1"""
    def get(self, request):
        me = request.user
        qs = Match.objects.filter(status="matched").filter(
            Q(from_user=me) | Q(to_user=me)
        ).order_by("-id")

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = MatchSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)


class MessagesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        me = request.user
        other = get_object_or_404(User.objects.all(), id=user_id)

        # 閲覧ブロック
        if Block.objects.filter(blocker=me, blocked=other).exists() or \
           Block.objects.filter(blocker=other, blocked=me).exists():
            return Response({"detail": "ブロック中です", "detail_code": "BLOCKED"}, status=403)

        after = int(request.GET.get("after") or 0)
        qs = Message.objects.filter(
            Q(sender=me, receiver=other) | Q(sender=other, receiver=me)
        )
        if after:
            qs = qs.filter(id__gt=after)
        qs = qs.order_by("id")[:200]

        data = MessageSerializer(qs, many=True, context={"request": request}).data
        return Response({"items": data})

    def post(self, request, user_id):
        me = request.user
        other = get_object_or_404(User.objects.all(), id=user_id)

        # 送信権限（DEV/staffはバイパス）
        if not (settings.DEBUG or me.is_staff):
            if not me.userprofile.can_send_message_to(other):
                return Response(
                    {"detail": "送信上限（初回1通まで）", "detail_code": "FIRST_MESSAGE_ONLY"},
                    status=403
                )

        raw = request.data.get("text")
        txt  = "" if raw is None else str(raw)  # 絵文字/記号もそのまま
        if txt == "":
            return Response({"detail": "textは必須です", "detail_code": "REQUIRED_TEXT"}, status=400)

        # ブロック中は送信不可
        if Block.objects.filter(blocker=me, blocked=other).exists() or \
           Block.objects.filter(blocker=other, blocked=me).exists():
            return Response({"detail": "ブロック中です", "detail_code": "BLOCKED"}, status=403)

        # NGワード
        for ng in getattr(settings, "NG_WORDS", []):
            if ng and ng in txt:
                return Response({"detail": "不適切な表現が含まれています", "detail_code": "NG_WORD"}, status=400)

        # 保存（通知など下流で落ちてもAPIは成功にしたいのでtry保護）
        try:
            m = Message.objects.create(sender=me, receiver=other, text=txt)
        except Exception as e:
            if settings.DEBUG:
                return Response(
                    {"detail": "INTERNAL_ERROR", "detail_code": "EXCEPTION", "error": f"{e.__class__.__name__}: {e}"},
                    status=500
                )
            raise

        return Response(MessageSerializer(m, context={"request": request}).data, status=201)


class BlockToggleAPI(_Base):
    """POST /api/block/<user_id>/toggle/"""
    def post(self, request, user_id):
        me = request.user
        other = get_object_or_404(User.objects.all(), id=user_id)
        obj = Block.objects.filter(blocker=me, blocked=other).first()
        if obj:
            obj.delete()
            return Response({"ok": True, "blocked": False})
        Block.objects.create(blocker=me, blocked=other)
        return Response({"ok": True, "blocked": True})


# ↓ Likes受信一覧
class LikesReceivedAPI(_Base):
    """GET /api/likes/received/?page=1"""
    def get(self, request):
        me = request.user
        qs = (Match.objects
              .select_related("from_user", "from_user__userprofile")
              .filter(to_user=me, status="like")
              .order_by("-created_at"))
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = LikeReceivedSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

# ↓ 足跡一覧
class FootprintsAPI(_Base):
    """GET /api/footprints/?page=1"""
    def get(self, request):
        me = request.user
        qs = (Footprint.objects
              .select_related("from_user", "from_user__userprofile")
              .filter(to_user=me)
              .order_by("-created_at"))
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = FootprintSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)


# --- プロフィール単体 ---
class ProfileDetailAPI(_Base):
    """GET /api/profiles/<user_id>/"""
    def get(self, request, user_id):
        user = get_object_or_404(User.objects.all(), id=user_id)
        prof = user.userprofile
        return Response(ProfileSerializer(prof, context={"request": request}).data)

# --- チャット一覧（相手 × 最終メッセージ） ---
class ChatThreadsAPI(_Base):
    """GET /api/chats/?page=1"""
    def get(self, request):
        me = request.user
        msgs = (Message.objects
                .filter(Q(sender=me) | Q(receiver=me))
                .select_related('sender', 'receiver', 'sender__userprofile', 'receiver__userprofile')
                .order_by('-id'))

        seen = set()
        items = []
        for m in msgs:
            partner = m.receiver if m.sender_id == me.id else m.sender
            pid = partner.id
            if pid in seen:
                continue
            seen.add(pid)
            items.append({
                "partner": UserBriefSerializer(partner, context={"request": request}).data,
                "last_message": MessageSerializer(m, context={"request": request}).data,
            })
            if len(items) >= 200:
                break

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(items, request)
        return paginator.get_paginated_response(page)

# --- ブロック一覧（自分がブロックしている相手） ---
class BlocksAPI(_Base):
    """GET /api/blocks/?page=1"""
    def get(self, request):
        me = request.user
        qs = (Block.objects
              .select_related("blocked", "blocked__userprofile")
              .filter(blocker=me)
              .order_by("-created_at"))

        items = [{
            "user": UserBriefSerializer(b.blocked, context={"request": request}).data,
            "created_at": b.created_at,
        } for b in qs]

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(items, request)
        return paginator.get_paginated_response(page)



# --- 通報作成 ---
class ReportCreateAPI(_Base):
    """POST /api/reports/  {reported_id, reason, comment?, anonymous?}"""
    def post(self, request):
        me = request.user
        data = request.data or {}
        try:
            reported_id = int(data.get("reported_id"))
        except (TypeError, ValueError):
            return Response({"detail":"reported_idが不正です"}, status=400)

        # 理由の妥当性
        valid_reasons = {k for k,_ in getattr(settings, "REPORT_REASONS", [])}
        reason = data.get("reason")
        if reason not in valid_reasons:
            return Response({"detail": f"reasonは{sorted(valid_reasons)}から選択してください"}, status=400)

        reported = get_object_or_404(User._base_manager, id=reported_id)
        anonymous = bool(data.get("anonymous", False))

        obj = Report.objects.create(
            reporter = None if anonymous else me,
            reported = reported,
            reason   = reason,
            comment  = data.get("comment","").strip()
        )
        return Response(ReportSerializer(obj, context={"request": request}).data, status=201)

# --- 自分が出した通報一覧 ---
class ReportsSentAPI(_Base):
    """GET /api/reports/sent/?page=1"""
    def get(self, request):
        me = request.user
        qs = (Report.objects
              .select_related("reporter","reported","reported__userprofile")
              .filter(reporter=me)
              .order_by("-created_at"))
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = ReportSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

# --- 自分が通報された一覧（必要ならUIに表示） ---
class ReportsReceivedAPI(_Base):
    """GET /api/reports/received/?page=1"""
    def get(self, request):
        me = request.user
        qs = (Report.objects
              .select_related("reporter","reported","reporter__userprofile")
              .filter(reported=me)
              .order_by("-created_at"))
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = ReportSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)





# ---- 可変項目: 定義一覧 ----
class ProfileFieldsAPI(_Base):
    """GET /api/profile-fields/"""
    def get(self, request):
        qs = ProfileField.objects.all().order_by("id")
        data = ProfileFieldSerializer(qs, many=True).data
        return Response({"items": data})

# ---- 可変項目: 自分の値 取得/一括更新 ----
class MeCustomFieldsAPI(_Base):
    """
    GET  /api/me/custom-fields/      -> { values: {<field_key>: <value>, ...} }
    PATCH /api/me/custom-fields/     -> body: {<field_key>: <value>, ...}
    """
    def get(self, request):
        prof = request.user.userprofile
        pfvs = (ProfileFieldValue.objects
                .select_related("field")
                .filter(user_profile=prof))
        values = {pfv.field.field_key: (pfv.value or "") for pfv in pfvs}
        return Response({"values": values})

    def patch(self, request):
        prof = request.user.userprofile
        body = request.data or {}
        if not isinstance(body, dict):
            return Response({"detail": "JSONオブジェクトで送ってください"}, status=400)

        # 既存の定義だけを対象にする
        fields = {f.field_key: f for f in ProfileField.objects.all()}
        updates = {k: (v if v is not None else "") for k,v in body.items() if k in fields}

        if not updates:
            return Response({"detail": "更新対象がありません"}, status=400)

        with transaction.atomic():
            for key, val in updates.items():
                field = fields[key]
                obj, _ = ProfileFieldValue.objects.get_or_create(
                    user_profile=prof, field=field, defaults={"value": str(val)}
                )
                if obj.value != str(val):
                    obj.value = str(val)
                    obj.save(update_fields=["value"])

        # 反映後を返す
        pfvs = (ProfileFieldValue.objects
                .select_related("field")
                .filter(user_profile=prof))
        values = {pfv.field.field_key: (pfv.value or "") for pfv in pfvs}
        return Response({"values": values})



class VerificationsAPI(_Base):
    """GET/POST /api/verifications/"""
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        me = request.user
        qs = (VerificationSubmission.objects
              .filter(user=me)
              .order_by("-submitted_at"))
        status_q = request.GET.get("status")
        if status_q:
            qs = qs.filter(status=status_q)
        dt_q = request.GET.get("doc_type")
        if dt_q:
            qs = qs.filter(doc_type=dt_q)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = VerificationSubmissionSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

    def post(self, request):
        me = request.user
        doc_type = (request.data.get("doc_type") or "").strip()
        valid = {c for c,_ in VerificationSubmission.DocType.choices}
        if doc_type not in valid:
            return Response({"detail": f"doc_typeは{sorted(valid)}から選んでください"}, status=400)
        if VerificationSubmission.objects.filter(user=me, doc_type=doc_type).exists():
            return Response({"detail": "この種類は既に提出済みです"}, status=400)

        f = request.FILES.get("image")
        if not f:
            return Response({"detail":"imageは必須です"}, status=400)

        obj = VerificationSubmission.objects.create(user=me, doc_type=doc_type, image=f)
        return Response(VerificationSubmissionSerializer(obj, context={"request": request}).data, status=201)


# 本人確認: 削除（自分の & 未審査のみ）
class VerificationDeleteAPI(_Base):
    """DELETE /api/verifications/<int:pk>/"""
    def delete(self, request, pk):
        me = request.user
        obj = get_object_or_404(VerificationSubmission.objects.filter(user=me, id=pk))
        if obj.status != VerificationSubmission.Status.PENDING:
            return Response({"detail":"審査中/承認済みは削除できません"}, status=400)
        obj.delete()
        return Response({"ok": True})


class MeAvatarAPI(_Base):
    """POST/DELETE /api/me/avatar/  (multipart: image)"""
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        f = request.FILES.get('image')
        if not f:
            return Response({"detail":"imageは必須です"}, status=400)
        prof = request.user.userprofile
        prof.profile_image = f
        prof.save(update_fields=["profile_image"])
        return Response(ProfileSerializer(prof, context={"request": request}).data, status=201)

    def delete(self, request):
        prof = request.user.userprofile
        if prof.profile_image:
            # Cloudinary等の実体はストレージ側で消える
            prof.profile_image.delete(save=False)
            prof.profile_image = None
            prof.save(update_fields=["profile_image"])
        return Response({"ok": True})


class MeLciqImageAPI(_Base):
    """POST/DELETE /api/me/lciq-image/  (multipart: image)"""
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        f = request.FILES.get('image')
        if not f:
            return Response({"detail":"imageは必須です"}, status=400)
        prof = request.user.userprofile
        prof.lciq_image = f
        prof.save(update_fields=["lciq_image"])
        return Response(ProfileSerializer(prof, context={"request": request}).data, status=201)

    def delete(self, request):
        prof = request.user.userprofile
        if prof.lciq_image:
            prof.lciq_image.delete(save=False)
            prof.lciq_image = None
            prof.save(update_fields=["lciq_image"])
        return Response({"ok": True})

# 送信したLike一覧
class LikesSentAPI(_Base):
    """GET /api/likes/sent/?page=1"""
    def get(self, request):
        me = request.user
        qs = (Match.objects
              .select_related("to_user", "to_user__userprofile")
              .filter(from_user=me, status="like")
              .order_by("-created_at"))
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        data = LikeSentSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

# 足跡記録（プロフィール閲覧時に叩く想定）
class FootprintTouchAPI(_Base):
    """POST /api/footprints/<user_id>/touch/"""
    def post(self, request, user_id):
        me = request.user
        other = get_object_or_404(User._base_manager, id=user_id)
        if other.id == me.id:
            return Response({"detail": "自分自身です"}, status=400)
        # ブロック中は記録しない
        if Block.objects.filter(blocker=me, blocked=other).exists() or \
           Block.objects.filter(blocker=other, blocked=me).exists():
            return Response({"detail": "ブロック中です"}, status=403)

        # 直近10分以内に同一足跡があれば重複作成しない
        since = timezone.now() - timedelta(minutes=10)
        exists = Footprint.objects.filter(from_user=me, to_user=other, created_at__gt=since).exists()
        if exists:
            return Response({"ok": True, "created": False})  # 200

        fp = Footprint.objects.create(from_user=me, to_user=other)
        return Response({"ok": True, "created": True, "id": fp.id}, status=201)

# アンマッチ / いいね取消（双方向を unmatched に）
class UnmatchAPI(_Base):
    """POST /api/unmatch/<user_id>/"""
    def post(self, request, user_id):
        me = request.user
        other = get_object_or_404(User._base_manager, id=user_id)
        qs = Match.objects.filter(
            Q(from_user=me, to_user=other) | Q(from_user=other, to_user=me)
        )
        if not qs.exists():
            return Response({"ok": False, "changed": 0}, status=404)
        changed = qs.update(status="unmatched")
        return Response({"ok": True, "changed": changed})


class ChatUnreadMapAPI(_Base):
    """
    GET /api/chats/unread-map/
    -> {"count": 3, "by_sender": {"6":2, "9":1}}
    """
    def get(self, request):
        me = request.user
        ct = ContentType.objects.get_for_model(Message)

        unread_mids = Notification.objects.filter(
            user=me, content_type=ct, verb='message', is_read=False
        ).values_list('object_id', flat=True)

        if not unread_mids:
            return Response({"count": 0, "by_sender": {}})

        rows = (Message.objects
                .filter(id__in=list(unread_mids))
                .values('sender_id')
                .annotate(cnt=Count('id')))

        by = {str(r['sender_id']): r['cnt'] for r in rows}
        return Response({"count": sum(by.values()), "by_sender": by})


class ChatThreadReadAPI(_Base):
    """
    POST /api/chats/<user_id>/read/
    -> その人からの未読メッセージのみ既読化
    """
    def post(self, request, user_id):
        me = request.user
        ct = ContentType.objects.get_for_model(Message)
        mids = list(Message.objects.filter(
            sender_id=user_id, receiver_id=me.id
        ).values_list('id', flat=True))
        if not mids:
            return Response({"ok": True, "changed": 0})
        changed = Notification.objects.filter(
            user=me, content_type=ct, object_id__in=mids, is_read=False
        ).update(is_read=True)
        return Response({"ok": True, "changed": changed})



