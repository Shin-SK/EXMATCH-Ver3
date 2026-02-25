from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import (
    UserProfile, ProfileField, ProfileFieldValue,
    Block, VerificationSubmission,
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
