from io import BytesIO
from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    UserProfile, ProfilePhoto, ProfileField, ProfileFieldValue,
    Block, Message, VerificationSubmission,
    MatchingRuleSet, MatchingRule,
)
from core.compat import score_candidate

User = get_user_model()


def _make_ruleset():
    """テスト用デフォルトルールセットを返す（なければ作成）"""
    ruleset, _ = MatchingRuleSet.objects.get_or_create(
        name="default", defaults={"is_active": True}
    )
    return ruleset


class GlobalRulesCompatTestCase(TestCase):
    """score_candidate（グローバルルール方式）と /api/recommendations/ の最小テスト"""

    def setUp(self):
        # UserProfile は post_save シグナルで自動作成される
        self.viewer_user = User.objects.create_user(username="viewer", password="pass")
        self.viewer_profile = self.viewer_user.userprofile

        self.cand_user = User.objects.create_user(username="cand1", password="pass")
        self.cand_profile = self.cand_user.userprofile

        self.ruleset = _make_ruleset()

        self.field = ProfileField.objects.create(
            field_key="hobby", field_label="趣味", field_type="select"
        )

    # ------------------------------------------------------------------ #
    # 1) ルールなしでも /api/recommendations/ が 200 で items を返す
    # ------------------------------------------------------------------ #
    def test_recommendations_api_no_rules_returns_200(self):
        client = APIClient()
        client.force_authenticate(user=self.viewer_user)
        response = client.get("/api/recommendations/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.data)

    # ------------------------------------------------------------------ #
    # 2) mustルール不一致で除外される
    # ------------------------------------------------------------------ #
    def test_must_rule_mismatch_excludes_candidate(self):
        rule = MatchingRule.objects.create(
            ruleset=self.ruleset,
            field=self.field,
            mode="must",
            desired_value="サウナ",
            match_type="eq",
        )
        rules = [rule]
        # cand_profile に hobby の値なし → 除外
        result = score_candidate(self.viewer_profile, self.cand_profile, rules)
        self.assertFalse(result["eligible"])

    # ------------------------------------------------------------------ #
    # 3) bonus一致で加点される
    # ------------------------------------------------------------------ #
    def test_bonus_match_adds_score(self):
        rule = MatchingRule.objects.create(
            ruleset=self.ruleset,
            field=self.field,
            mode="bonus",
            weight=20,
            desired_value="サウナ",
            match_type="eq",
        )
        ProfileFieldValue.objects.create(
            user_profile=self.cand_profile,
            field=self.field,
            value="サウナ",
        )
        rules = [rule]
        result = score_candidate(self.viewer_profile, self.cand_profile, rules)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["score"], 20)
        self.assertEqual(len(result["reasons"]), 1)
        self.assertEqual(result["reasons"][0]["label"], "趣味")

    # ------------------------------------------------------------------ #
    # 4) ブロック双方向で除外される
    # ------------------------------------------------------------------ #
    def test_block_from_viewer_excludes_candidate(self):
        Block.objects.create(blocker=self.viewer_user, blocked=self.cand_user)
        result = score_candidate(self.viewer_profile, self.cand_profile, [])
        self.assertFalse(result["eligible"])

    def test_block_from_candidate_excludes_candidate(self):
        Block.objects.create(blocker=self.cand_user, blocked=self.viewer_user)
        result = score_candidate(self.viewer_profile, self.cand_profile, [])
        self.assertFalse(result["eligible"])

    # ------------------------------------------------------------------ #
    # 5) sexual_object_pref がある場合 gender が一致しないと除外される
    # ------------------------------------------------------------------ #
    def test_sexual_object_pref_excludes_wrong_gender(self):
        self.viewer_profile.sexual_object_pref = "female"
        self.viewer_profile.save()
        self.cand_profile.gender = "male"
        self.cand_profile.save()
        result = score_candidate(self.viewer_profile, self.cand_profile, [])
        self.assertFalse(result["eligible"])

    def test_sexual_object_pref_allows_correct_gender(self):
        self.viewer_profile.sexual_object_pref = "female"
        self.viewer_profile.save()
        self.cand_profile.gender = "female"
        self.cand_profile.save()
        result = score_candidate(self.viewer_profile, self.cand_profile, [])
        self.assertTrue(result["eligible"])

    # ------------------------------------------------------------------ #
    # 6) /api/me/preference/ は 410 を返す（廃止済み）
    # ------------------------------------------------------------------ #
    def test_me_preference_api_returns_410(self):
        client = APIClient()
        client.force_authenticate(user=self.viewer_user)
        for method in ("get", "patch"):
            response = getattr(client, method)("/api/me/preference/")
            self.assertEqual(response.status_code, 410, f"{method} should return 410")


class SecurityTestCase(TestCase):
    """セキュリティ修正の回帰テスト"""

    def setUp(self):
        self.user = User.objects.create_user(username="secuser", password="pass", email="sec@test.com")
        self.user.userprofile.gender = "male"
        self.user.userprofile.sexual_object_pref = "female"
        self.user.userprofile.date_of_birth = date(1990, 1, 1)
        self.user.userprofile.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # --- ContactAPI レートリミット ---
    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.TokenAuthentication",),
            "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
            "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
            "DEFAULT_THROTTLE_RATES": {"contact": "2/hour"},
        }
    )
    def test_contact_api_throttled(self):
        data = {"name": "test", "email": "a@b.com", "subject": "abuse", "message": "test msg"}
        for _ in range(3):
            resp = self.client.post("/api/contact/", data, format="json")
        self.assertEqual(resp.status_code, 429)

    # --- 10MB超の画像アップロードが拒否される ---
    def test_upload_over_10mb_rejected(self):
        big_file = SimpleUploadedFile("big.jpg", b"\x00" * (10 * 1024 * 1024 + 1), content_type="image/jpeg")
        resp = self.client.post("/api/me/avatar/", {"image": big_file}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ファイルサイズ", resp.data.get("detail", ""))

    # --- 非許可MIMEタイプが拒否される ---
    def test_upload_invalid_mime_rejected(self):
        svg_file = SimpleUploadedFile("test.svg", b"<svg></svg>", content_type="image/svg+xml")
        resp = self.client.post("/api/me/avatar/", {"image": svg_file}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("JPEG", resp.data.get("detail", ""))

    # --- 2000文字超メッセージが拒否される ---
    def test_message_over_2000_chars_rejected(self):
        other = User.objects.create_user(username="other", password="pass")
        long_text = "あ" * 2001
        resp = self.client.post(f"/api/chats/{other.id}/messages/", {"text": long_text}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("2000", resp.data.get("detail", ""))

    # --- 非課金ユーザーの送信制限 ---
    def test_free_user_limited_to_one_message(self):
        other = User.objects.create_user(username="other2", password="pass")
        resp1 = self.client.post(f"/api/chats/{other.id}/messages/", {"text": "hello"}, format="json")
        self.assertEqual(resp1.status_code, 201)
        resp2 = self.client.post(f"/api/chats/{other.id}/messages/", {"text": "second"}, format="json")
        self.assertEqual(resp2.status_code, 403)
        self.assertIn("FIRST_MESSAGE_ONLY", resp2.data.get("detail_code", ""))

    # --- staff は送信制限をバイパスできる ---
    def test_staff_bypasses_message_limit(self):
        staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        other = User.objects.create_user(username="other3", password="pass")
        client = APIClient()
        client.force_authenticate(user=staff)
        for i in range(3):
            resp = client.post(f"/api/chats/{other.id}/messages/", {"text": f"msg{i}"}, format="json")
            self.assertEqual(resp.status_code, 201)

    # --- 緯度経度が丸められて返る ---
    def test_lat_lon_rounded_in_response(self):
        prof = self.user.userprofile
        prof.latitude = 35.6812
        prof.longitude = 139.7671
        prof.save(update_fields=["latitude", "longitude"])
        resp = self.client.get("/api/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["latitude"], 35.7)
        self.assertEqual(resp.data["longitude"], 139.8)

    # --- 退会済みユーザーが一覧に出ない ---
    def test_deactivated_user_hidden_from_profiles(self):
        other = User.objects.create_user(username="deleted_user", password="pass")
        other.userprofile.gender = "female"
        other.userprofile.deleted_at = timezone.now()
        other.userprofile.save()
        resp = self.client.get("/api/profiles/")
        self.assertEqual(resp.status_code, 200)
        user_ids = [p["id"] for p in resp.data["results"]]
        self.assertNotIn(other.id, user_ids)


class ProfilePhotoTestCase(TestCase):
    """ProfilePhoto 複数画像 API のテスト"""

    def setUp(self):
        self.user = User.objects.create_user(username="photouser", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _make_image(self, name="test.jpg", size=100, content_type="image/jpeg"):
        return SimpleUploadedFile(name, b"\xff\xd8\xff\xe0" + b"\x00" * size, content_type=content_type)

    # --- 画像追加 ---
    def test_add_photo(self):
        resp = self.client.post("/api/me/photos/", {"image": self._make_image()}, format="multipart")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["order"], 0)
        self.assertEqual(ProfilePhoto.objects.filter(user=self.user).count(), 1)

    # --- 画像一覧取得 ---
    def test_list_photos(self):
        ProfilePhoto.objects.create(user=self.user, image="profiles/a.jpg", order=0)
        ProfilePhoto.objects.create(user=self.user, image="profiles/b.jpg", order=1)
        resp = self.client.get("/api/me/photos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]["order"], 0)
        self.assertEqual(resp.data[1]["order"], 1)

    # --- 5枚上限 ---
    def test_max_5_photos(self):
        for i in range(5):
            ProfilePhoto.objects.create(user=self.user, image=f"profiles/{i}.jpg", order=i)
        resp = self.client.post("/api/me/photos/", {"image": self._make_image()}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("最大", resp.data["detail"])

    # --- 削除後にorderが詰まる ---
    def test_delete_compacts_order(self):
        p0 = ProfilePhoto.objects.create(user=self.user, image="profiles/a.jpg", order=0)
        p1 = ProfilePhoto.objects.create(user=self.user, image="profiles/b.jpg", order=1)
        p2 = ProfilePhoto.objects.create(user=self.user, image="profiles/c.jpg", order=2)
        self.client.delete(f"/api/me/photos/{p1.id}/")
        remaining = list(ProfilePhoto.objects.filter(user=self.user).order_by("order"))
        self.assertEqual(len(remaining), 2)
        self.assertEqual(remaining[0].order, 0)
        self.assertEqual(remaining[1].order, 1)

    # --- reorder API ---
    def test_reorder(self):
        p0 = ProfilePhoto.objects.create(user=self.user, image="profiles/a.jpg", order=0)
        p1 = ProfilePhoto.objects.create(user=self.user, image="profiles/b.jpg", order=1)
        p2 = ProfilePhoto.objects.create(user=self.user, image="profiles/c.jpg", order=2)
        resp = self.client.post(
            "/api/me/photos/reorder/",
            {"ordered_ids": [p2.id, p0.id, p1.id]},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["id"], p2.id)
        self.assertEqual(resp.data[0]["order"], 0)

    # --- reorder: 不正なID ---
    def test_reorder_invalid_ids(self):
        p0 = ProfilePhoto.objects.create(user=self.user, image="profiles/a.jpg", order=0)
        resp = self.client.post(
            "/api/me/photos/reorder/",
            {"ordered_ids": [p0.id, 9999]},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    # --- 0枚でもAPIが壊れない ---
    def test_zero_photos_ok(self):
        resp = self.client.get("/api/me/photos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])

    # --- 詳細APIにphotosが返る ---
    def test_profile_detail_includes_photos(self):
        other = User.objects.create_user(username="other_photo", password="pass")
        other.userprofile.gender = "female"
        other.userprofile.save()
        ProfilePhoto.objects.create(user=other, image="profiles/x.jpg", order=0)
        resp = self.client.get(f"/api/profiles/{other.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("photos", resp.data)
        self.assertEqual(len(resp.data["photos"]), 1)

    # --- avatar API 後方互換 ---
    def test_avatar_api_compat_post(self):
        resp = self.client.post("/api/me/avatar/", {"image": self._make_image()}, format="multipart")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(ProfilePhoto.objects.filter(user=self.user).count(), 1)

    def test_avatar_api_compat_delete(self):
        ProfilePhoto.objects.create(user=self.user, image="profiles/a.jpg", order=0)
        resp = self.client.delete("/api/me/avatar/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ProfilePhoto.objects.filter(user=self.user).count(), 0)

    # --- MIME制限 ---
    def test_invalid_mime_rejected(self):
        svg = SimpleUploadedFile("test.svg", b"<svg></svg>", content_type="image/svg+xml")
        resp = self.client.post("/api/me/photos/", {"image": svg}, format="multipart")
        self.assertEqual(resp.status_code, 400)

    # --- サイズ制限 (10MB超) ---
    def test_oversize_rejected(self):
        big = SimpleUploadedFile("big.jpg", b"\x00" * (10 * 1024 * 1024 + 1), content_type="image/jpeg")
        resp = self.client.post("/api/me/photos/", {"image": big}, format="multipart")
        self.assertEqual(resp.status_code, 400)

    # --- 他人の画像は削除できない ---
    def test_cannot_delete_others_photo(self):
        other = User.objects.create_user(username="other2", password="pass")
        p = ProfilePhoto.objects.create(user=other, image="profiles/x.jpg", order=0)
        resp = self.client.delete(f"/api/me/photos/{p.id}/")
        self.assertEqual(resp.status_code, 404)
