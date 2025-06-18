# --- core/views.py ---
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django.utils import timezone
from django.apps import apps
from django.db.models import CharField, TextField, FloatField, DateTimeField, Exists, OuterRef, Subquery
from django.contrib.contenttypes.models import ContentType
from core.mixins import identity_verified_required


from .filters import DynamicProfileFilter
from .forms import ProfileEditForm, DynamicProfileFieldForm
from .models import UserProfile, Match, Message, Footprint, ProfileFieldValue, ProfileField
from notifications.models import Notification
from core.utils import get_matched_users, attach_normal_pfv

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .forms import ContactForm
from django.template.loader import render_to_string


@login_required
def my_page(request):
    profile = request.user.userprofile

    # --- カスタムフィールド等のロジック ---
    profile_field_values = ProfileFieldValue.objects.filter(user_profile=profile)
    for pfv in profile_field_values:
        if pfv.field.field_type == 'checkbox':
            splitted = (pfv.value or "").split(",")
            pfv.split_list = splitted
        else:
            pfv.split_list = []

    # プロフィール充実度計算
    total_fields = ProfileField.objects.count()
    answered_count = ProfileFieldValue.objects.filter(
        user_profile=profile
    ).exclude(value='').count()
    if total_fields > 0:
        completeness_ratio = answered_count / total_fields
        completeness_percent = int(completeness_ratio * 100)
    else:
        completeness_percent = 0

    # --- 入力がんばれアラート ---

    #必須項目
    REQUIRED_FIXED = ["nickname", "gender", "main_area", "sexual_object_pref", "lciq_score", "date_of_birth"]

    # 固定：空欄を数える
    missing_fixed_cnt = sum(
        1 for key in REQUIRED_FIXED if not getattr(profile, key)
    )

    # カスタム： required=True なのに未回答な件数
    required_pf = ProfileField.objects.filter(required=True)

    pfv_sub = ProfileFieldValue.objects.filter(
        user_profile=profile,
        field=OuterRef("pk")
    ).exclude(value="")

    missing_custom_cnt = (
        required_pf
        .annotate(has_answer=Exists(pfv_sub))
        .filter(has_answer=False)
        .count()
    )

    missing_total = missing_fixed_cnt + missing_custom_cnt

    # --- いいね数をカウント ---
    like_count = Match.objects.filter(
        to_user=profile.user,  # ログインユーザーが「いいね」を受けた
        status='like'
    ).count()

    # 本人確認書類入った？
    id_verified = profile.is_verified

    # --- ② プロフィール全部埋まった？ ---
    all_filled = (missing_total == 0)

    # --- ③ スタンダード会員？ ---
    is_standard = profile.is_standard_plan()

    # --- ④ プラスプロフィールを書いた？ ---
    plus_filled = (
        ProfileFieldValue.objects
        .filter(user_profile=profile, field__category='plus')
        .exclude(value__in=["", None])
        .exists()
    )

    # --- lciqポイント取得 --- #
    lciq_value = profile.lciq_score or '0'

    # matched のレコードをまとめて取得
    matched_records = Match.objects.filter(
        Q(from_user=request.user, status='matched') |
        Q(to_user=request.user, status='matched')
    ).order_by('-created_at')

    # 実際の「相手ユーザー」を集める
    matched_users_list = []
    seen = set()
    for m in matched_records:
        partner = m.to_user if m.from_user == request.user else m.from_user
        if partner not in seen:
            matched_users_list.append(partner)
            seen.add(partner)

    # ★ ここで id だけ取り出す
    matched_ids = [u.id for u in matched_users_list]

    # Prefetch を付けた QuerySet を再取得
    matched_qs  = attach_normal_pfv(
                    get_user_model().objects.filter(id__in=matched_ids)
                )
    matched_users_list = list(matched_qs)

    # ───────── リスト取得 ─────────
    matched_qs = get_user_model().objects.filter(id__in=matched_ids)
    matched_qs = attach_normal_pfv(matched_qs)      # ← たった１行追加
    matched_users_list = list(matched_qs)           # あとは元と同じ


    # いいね「された」レコードを最新順で取得
    likes_received_qs = (
        Match.objects
        .filter(to_user=request.user, status='like')
        .select_related('from_user', 'from_user__userprofile')
        .order_by('-created_at')
    )

    likes_received_top = likes_received_qs[:5]   # ← 上位5件だけ
    liked_users = [lk.from_user for lk in likes_received_qs]

    return render(request, 'core/my_page.html', {
        'profile': profile,
        'profile_field_values': profile_field_values,
        'total_fields': total_fields,
        'answered_count': answered_count,
        'completeness_percent': completeness_percent,
        'like_count': like_count,  # テンプレートで表示
        'lciq_value': lciq_value,
        'matched_users': matched_users_list,
        'likes_received_top': likes_received_top,
        'liked_users': liked_users,
        "missing_total": missing_total,
        'id_verified': id_verified,
        "all_filled": all_filled,
        "is_standard": is_standard,
        "plus_filled": plus_filled,
    })

@login_required
def likes_received_list(request):
    likes_received = (
        Match.objects
        .filter(to_user=request.user, status='like')
        .select_related('from_user', 'from_user__userprofile')
        .order_by('-created_at')
    )
    return render(request, 'core/likes_received_list.html',
                  {'likes_received': likes_received})


@login_required
def profile_edit(request):
    profile = request.user.userprofile

    if request.method == 'POST':
        # 通常のUserProfile固定項目用 (bio, blood_typeなど)
        form_fixed = ProfileEditForm(request.POST, request.FILES, instance=profile)

        # 動的項目用
        form_dynamic = DynamicProfileFieldForm(request.POST, user_profile=profile)

        if form_fixed.is_valid() and form_dynamic.is_valid():
            form_fixed.save()
            form_dynamic.save()
            return redirect('my_page')
    else:
        form_fixed = ProfileEditForm(instance=profile)
        form_dynamic = DynamicProfileFieldForm(user_profile=profile)

    normal_fields = []
    plus_fields   = []

    for fname in form_dynamic.fields.keys():
        cat = form_dynamic.category_map.get(fname, 'normal')
        if cat == 'plus':
            plus_fields.append(form_dynamic[fname])
        else:
            normal_fields.append(form_dynamic[fname])

    return render(request, 'core/profile_edit.html', {
        'form_fixed': form_fixed,
        'form_dynamic': form_dynamic,
        'normal_fields'   : normal_fields,
        'plus_fields'     : plus_fields
    })



@login_required
def user_profile_detail(request, user_id):
    target_user = get_user_model().objects.select_related('userprofile').get(id=user_id)
    profile     = target_user.userprofile

    # 足あと
    if request.user != target_user:
        Footprint.objects.get_or_create(from_user=request.user, to_user=target_user)

    # ------------------------------------------------------------------
    # ① 固定項目 → fixed_pairs
    # ------------------------------------------------------------------
    fixed_pairs = []
    FIELD_LABEL_MAP = {
        "nickname": "ニックネーム",
        "bio":      "自己紹介",
        "blood_type": "血液型",
        "gender":   "性別",
        "main_area": "居住地",
    }

    for field in profile._meta.get_fields():
        if not isinstance(field, (CharField, TextField, FloatField, DateTimeField)):
            continue
        value = getattr(profile, field.name)
        if value in (None, "", []):
            continue
        if field.choices:
            value = dict(field.flatchoices).get(value, value)
        label = FIELD_LABEL_MAP.get(field.name, field.verbose_name.title())
        fixed_pairs.append((label, value))

    # ------------------------------------------------------------------
    # ② 動的項目 → normal_pairs / plus_pairs
    # ------------------------------------------------------------------
    pfvs = (
        ProfileFieldValue.objects
        .select_related('field')
        .filter(user_profile=profile)
        .exclude(value__in=["", None])
    )

    normal_pairs = [
        (pfv.field.field_label, pfv.value)
        for pfv in pfvs if pfv.field.category == "normal"
    ]
    plus_pairs = [
        (pfv.field.field_label, pfv.value)
        for pfv in pfvs if pfv.field.category == "plus"
    ]

    # プラス閲覧権を持つか？
    viewer    = request.user.userprofile
    show_plus = viewer.is_standard_plan() or viewer.has_option()

    # --- いいね / マッチ状態 ---
    is_liked = Match.objects.filter(
        from_user=request.user, to_user=target_user, status='like'
    ).exists()
    is_matched = Match.objects.filter(
        Q(from_user=request.user, to_user=target_user, status='matched') |
        Q(from_user=target_user, to_user=request.user, status='matched')
    ).exists()

    return render(request, 'core/user_profile_detail.html', {
        'profile':     profile,
        'fixed_pairs': fixed_pairs,
        'normal_pairs': normal_pairs,
        'plus_pairs':   plus_pairs,
        'show_plus':   show_plus,
        'is_liked':    is_liked,
        'is_matched':  is_matched,
    })


@login_required
def footprint_list(request):
    """
    自分(to_user=request.user) に対する足あとを時系列で表示
    """
    footprints = (
        Footprint.objects
        .filter(to_user=request.user)
        .select_related('from_user', 'from_user__userprofile')
        .order_by('-created_at')
    )

    # 既存パーシャルが users を期待しているので抽出して渡す
    users = [fp.from_user for fp in footprints]

    return render(
        request,
        'core/footprint_list.html',
        {
            'footprints': footprints,  # ← いつか時刻を使いたい用に残す
            'users': users             # ← パーシャル用
        }
    )


@login_required
def follow_list(request):
    """
    ログインユーザーが「いいね（フォロー）」した相手一覧を表示
    """
    my_follows = Match.objects.filter(from_user=request.user, status='like')
    return render(request, 'core/follow_list.html', {'my_follows': my_follows})

@login_required
def follow_user(request, user_id):
    """
    特定のユーザーをフォロー（いいね）する処理。
    すでに同じ (from_user, to_user) のレコードがある場合は何もしない。
    もし相手からの "like" が既にあれば両方 'matched' に更新。
    """
    target_user = get_user_model().objects.get(id=user_id)
    if target_user == request.user:
        return redirect('user_list')  # 自分自身にはいいねしない

    # 既存の from_user→to_user レコードがあるかチェック
    existing_match = Match.objects.filter(
        from_user=request.user,
        to_user=target_user
    ).first()

    if existing_match:
        # 既にいいね済み
        return redirect(request.GET.get("next", "userprofile_list"))

    # 新規に「いいね」を作成
    my_match = Match.objects.create(
        from_user=request.user,
        to_user=target_user,
        status='like'
    )

    # 相手→自分が "like" だったら、両方 matched に更新
    try:
        opposite_match = Match.objects.get(
            from_user=target_user,
            to_user=request.user,
            status='like'
        )
        # 相手からのいいねが既に存在する -> マッチ成立
        my_match.status = 'matched'
        my_match.save()
        opposite_match.status = 'matched'
        opposite_match.save()
    except Match.DoesNotExist:
        # 相手からまだいいねが来ていない
        pass

    return redirect(request.GET.get("next", "userprofile_list"))


@login_required
def matched_list(request):
    """
    ログインユーザーがマッチ済み('matched')になっているレコードを集める。
    from_user or to_user のどちらかが自分で status='matched' のもの。
    """
    matches = Match.objects.filter(
        Q(from_user=request.user, status='matched') |
        Q(to_user=request.user, status='matched')
    )
    return render(request, 'core/matched_list.html', {'matches': matches})

User = get_user_model()
def home(request):
    # ① 男女それぞれ UserProfile → user_id を抽出
    female_ids = (
        UserProfile.objects.filter(gender='female')
                           .order_by('-user__date_joined')[:10]
                           .values_list('user_id', flat=True)
    )
    male_ids = (
        UserProfile.objects.filter(gender='male')
                           .order_by('-user__date_joined')[:10]
                           .values_list('user_id', flat=True)
    )

    # ② その ID で User を取得して attach_normal_pfv
    latest_female = attach_normal_pfv(
        User.objects.filter(id__in=female_ids)
                    .select_related('userprofile')
    )
    latest_male = attach_normal_pfv(
        User.objects.filter(id__in=male_ids)
                    .select_related('userprofile')
    )

    if request.user.is_authenticated:
        return redirect('my_page')

    return render(request, 'core/home.html', {
        'female_profiles': latest_female,
        'male_profiles':   latest_male,
    })


@login_required
def user_list(request):
    User = get_user_model()
    all_users = attach_normal_pfv(          # ← ここで Prefetch
        User.objects.exclude(id=request.user.id)
        .select_related('userprofile')
    )
    return render(request, 'core/user_list.html', {
        'all_users': all_users
    })


@login_required
# @identity_verified_required 
def chat_room(request, user_id):
    target_user = get_user_model().objects.get(id=user_id)

    # ここで必ず作っておく -------------
    me_profile = request.user.userprofile
    # ----------------------------------

    # 送信処理 ----------------------------------------------------
    if request.method == "POST":
        text = request.POST.get("text", "").strip()

        # ① マッチ判定
        if not is_matched(request.user, target_user):
            return redirect("chat_room", user_id=target_user.id)

        # ② 送信可否チェック
        if not me_profile.can_send_message_to(target_user):
            if not me_profile.is_standard_plan():
                messages.info(
                    request,
                    "フリープランでは初回メッセージのみ送信できます。"
                    "無制限に送信するにはスタンダードプランへアップグレードしてください。"
                )
                return redirect("plan_upgrade")

            # スタンダードだけど本人確認が未承認
            messages.warning(
                request,
                "2通目以降の送信には本人確認書類の承認が必要です。"
                "プロフィール編集から書類をアップロードしてください。"
            )
            return redirect("profile_edit")

        # ③ 送信
        if text:
            Message.objects.create(
                sender=request.user,
                receiver=target_user,
                text=text
            )
            return redirect("chat_room", user_id=target_user.id)

    # ----- GET: フォーム表示判定 ------------------------------
    can_send = me_profile.can_send_message_to(target_user)
    need_plan       = (not can_send) and (not me_profile.is_standard_plan())
    need_verify     = (not can_send) and me_profile.is_standard_plan() and (not me_profile.is_verified)

    # メッセージ一覧取得 …（以下そのまま） -----------------------
    messages_qs = Message.objects.filter(
        Q(sender=request.user, receiver=target_user) |
        Q(sender=target_user, receiver=request.user)
    ).order_by('created_at')

    msg_ct = ContentType.objects.get_for_model(Message)
    Notification.objects.filter(
        user=request.user,
        content_type=msg_ct,
        object_id__in=messages_qs.values_list('id', flat=True),
        is_read=False
    ).update(is_read=True)

    return render(request, "core/chat_room.html", {
        "target_user": target_user,
        "messages":    messages_qs,
        "can_send":    can_send,
        "need_plan":   need_plan,
        "need_verify": need_verify,
    })


def is_matched(userA, userB):
    # どちら向きでも 'matched' があるか
    return Match.objects.filter(
        Q(from_user=userA, to_user=userB, status='matched') |
        Q(from_user=userB, to_user=userA, status='matched')
    ).exists()

@login_required
def chat_index(request):
    me = request.user

    # list → idリスト
    matched_user_ids = [u.id for u in get_matched_users(me)]

    # id で絞った QuerySet に変換（profile画像もまとめて取得）
    matched_qs = (
        get_user_model().objects
        .filter(id__in=matched_user_ids)
        .select_related('userprofile')
    )

    # 最新メッセージ 1 件だけをサブクエリで取得
    latest_qs = (
        Message.objects
        .filter(
            Q(sender=me, receiver=OuterRef('pk')) |
            Q(sender=OuterRef('pk'), receiver=me)
        )
        .order_by('-id')
        .values('text')[:1]
    )

    users_with_last = matched_qs.annotate(last_msg=Subquery(latest_qs))

    # ── 未読数ロジックはそのまま ───────────────────
    msg_ct = ContentType.objects.get_for_model(Message)
    unread_map = (
        Notification.objects.filter(user=me, content_type=msg_ct, is_read=False)
        .values('object_id')
        .annotate(cnt=Count('id'))
        .values_list('object_id', 'cnt')
    )

    msg_to_user = (
        Message.objects.filter(id__in=[mid for mid, _ in unread_map])
        .values_list('id', 'sender_id')
    )
    id_user_map = {mid: uid for mid, uid in msg_to_user}
    unread_by_user = {}
    for mid, cnt in unread_map:
        uid = id_user_map.get(mid)
        unread_by_user[uid] = unread_by_user.get(uid, 0) + cnt

    return render(request, "core/chat_index.html", {
        "matched_users": users_with_last,
        "unread_by_user": unread_by_user,
    })


class UserProfileListView(LoginRequiredMixin, FilterView):
    model = UserProfile
    filterset_class = DynamicProfileFilter
    template_name = 'core/userprofile_list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        # ログインユーザー自身を除外
        qs = qs.exclude(user=self.request.user)

        # 自分の性別設定を読み込む
        me = self.request.user.userprofile
        # "相手の gender == 自分の sexual_object_pref" で絞り込み
        # (ここでは空欄を考慮しない前提なので、必須入力とする)
        if me.sexual_object_pref:
            qs = qs.filter(gender=me.sexual_object_pref)

        return qs

    def get_filterset(self, filterset_class=None):
        """
        1) request=self.request を渡して、Filterで self.request が使えるようにする
        2) 課金オプションを持たないユーザーからは 'sexual_pref' を削除
        """
        if filterset_class is None:
            filterset_class = self.get_filterset_class()

        fs = filterset_class(
            data=self.request.GET,
            queryset=self.get_queryset(),
            request=self.request,  # ★重要
        )

        # --- オプション制御ロジック ---
        profile = self.request.user.userprofile
        has_option = (profile.option_expiry and profile.option_expiry > timezone.now())
        if not has_option:
            option_fields = getattr(filterset_class, 'option_fields', [])
            for f in option_fields:
                if f in fs.form.fields:
                    del fs.form.fields[f]

        return fs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ↓ ① 検索結果 (UserProfile QS) を取得
        profiles = self.filterset.qs

        # ↓ ② そこから user_id を抽出
        user_ids = profiles.values_list('user_id', flat=True)

        # ↓ ③ attach_normal_pfv で normal_pfvs を事前取得
        users_qs = attach_normal_pfv(
            get_user_model()
            .objects.filter(id__in=user_ids)
            .select_related('userprofile')
        )

        context["users"] = users_qs   # ← 置き換え
        return context


def chat_api(request, user_id):
    """相手との新着メッセージだけ JSON で返す"""
    last_id = int(request.GET.get("after", 0))
    target  = get_object_or_404(get_user_model(), id=user_id)

    qs = Message.objects.filter(
        Q(sender=request.user, receiver=target) |
        Q(sender=target, receiver=request.user),
        id__gt=last_id          # ← ここが新着フィルタ
    ).order_by("id")

    data = [{
        "id": m.id,
        "sender": m.sender.username,
        "avatar":  (m.sender.userprofile.profile_image.url
                    if m.sender.userprofile.profile_image
                    else static("img/user-unset.webp")),
        "text": m.text,
        "created": m.created_at.strftime("%H:%M"),
    } for m in qs]

    return JsonResponse({"messages": data})




def contact_view(request):
    if request.method == "GET":
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
            # ニックネーム → フルネーム → ユーザ名 の順で埋める例
            prof = getattr(request.user, "userprofile", None)
            initial["name"] = (
                getattr(prof, "nickname", "") or
                request.user.get_full_name() or
                request.user.username
            )
        form = ContactForm(initial=initial)
    else:
        form = ContactForm(request.POST)

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        context = {
            **cd,
            "subject_label": dict(ContactForm.SUBJECT_CHOICES).get(cd["subject"]),
            "now": timezone.now(),
        }

        body_admin = render_to_string("emails/contact_admin.txt", context)
        body_user  = render_to_string("emails/contact_user.txt", context)

        # ────────── 管理者宛メール ──────────
        email_admin = EmailMessage(
            subject=f"[問い合わせ] {context['subject_label']}",
            body    =body_admin,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to      =[settings.CONTACT_EMAIL],
            reply_to=[cd["email"]],          # ★ ここが欲しいので EmailMessage を使用
        )
        email_admin.send()                   # ← send_mail ではなく send()

        # ────────── ユーザー宛自動返信 ────────
        email_user = EmailMessage(
            subject="【EXMATCH】お問い合わせ受付いたしました。",
            body    =body_user,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to      =[cd["email"]],
        )
        email_user.send()
        
        # フラッシュメッセージ & リダイレクト
        messages.success(request, "お問い合わせを送信しました。ありがとうございました。")
        return redirect("contact_done")

    return render(request, "core/contact.html", {"form": form})

def contact_done(request):
    """送信完了ページ（テンプレートは簡単に）"""
    return render(request, "core/contact_done.html")