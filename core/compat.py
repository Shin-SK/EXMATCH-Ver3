# core/compat.py
"""
相性スコア計算ユーティリティ。
運営が管理画面で定義した「グローバル採点ルール（MatchingRule リスト）」と
候補者プロフィールを照合してスコアを算出する。
"""
from core.models import Block


def _matches(candidate_val: str, desired_val: str, match_type: str) -> bool:
    """候補者の値と希望値が条件に合致するか判定する。"""
    if match_type == "eq":
        return candidate_val == desired_val
    elif match_type == "contains":
        return desired_val in candidate_val
    return False


def score_candidate(viewer_profile, candidate_profile, rules) -> dict:
    """
    グローバル採点ルール rules に対して candidate_profile の相性スコアを計算する。

    引数:
        viewer_profile   : UserProfile（閲覧者）
        candidate_profile: UserProfile（候補者）
        rules            : MatchingRule のイテラブル（enabled=True かつ desired_value 非空のみ渡す想定）

    返却形式:
    {
        "eligible": bool,
        "score": int,
        "reasons": [{"label": str, "detail": str, "points": int}, ...]
    }
    """
    _ineligible = {"eligible": False, "score": 0, "reasons": []}

    # 1) ブロック関係（双方向）
    if Block.objects.filter(
        blocker=viewer_profile.user, blocked=candidate_profile.user
    ).exists():
        return _ineligible
    if Block.objects.filter(
        blocker=candidate_profile.user, blocked=viewer_profile.user
    ).exists():
        return _ineligible

    # 2) 性指向フォールバック（ProfilesAPI と同等）
    my_sexual_pref = getattr(viewer_profile, "sexual_object_pref", None)
    if my_sexual_pref and candidate_profile.gender != my_sexual_pref:
        return _ineligible

    # 3) mode="must" ルール評価（1つでも不一致なら除外）
    custom_vals = candidate_profile.custom_values
    rules = list(rules)

    for rule in rules:
        if rule.mode == "must":
            candidate_val = custom_vals.get(rule.field.field_key, "")
            if not _matches(candidate_val, rule.desired_value, rule.match_type):
                return _ineligible

    # eligible 確定 → bonus 加点
    score = 0
    reasons = []
    for rule in rules:
        if rule.mode == "bonus":
            candidate_val = custom_vals.get(rule.field.field_key, "")
            if _matches(candidate_val, rule.desired_value, rule.match_type):
                score += rule.weight
                reasons.append({
                    "label": rule.field.field_label,
                    "detail": "一致",
                    "points": rule.weight,
                })

    # points 降順で上位3件のみ返す
    reasons.sort(key=lambda r: r["points"], reverse=True)
    reasons = reasons[:3]

    return {"eligible": True, "score": score, "reasons": reasons}
