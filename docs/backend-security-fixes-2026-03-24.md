# EXMATCH バックエンド セキュリティ修正レポート

**実施日**: 2026-03-24
**対象**: Django バックエンド（`config/`, `core/`, `payments/`）
**ステータス**: 修正完了（優先度1〜5）

---

## 概要

EXMATCH バックエンド（Django 5.2 + DRF）を調査し、手書き実装由来のセキュリティ課題を5件特定・修正しました。

---

## 修正内容

### 1. APIレートリミットの追加

**問題**: 全APIエンドポイントにレート制限が一切なく、ブルートフォース攻撃・スパム・DoSに対して無防備だった。お問い合わせフォーム（`ContactAPI`）は `AllowAny` で認証不要のまま無制限にリクエスト可能だった。

**修正箇所**:
- `config/settings.py` — `REST_FRAMEWORK` に `DEFAULT_THROTTLE_CLASSES` と `DEFAULT_THROTTLE_RATES` を追加
- `core/api_contact.py` — `throttle_scope = "contact"` を有効化
- `core/api_views.py` — `LikeAPI`, `MessagesAPI`, `MeAvatarAPI`, `MeLciqImageAPI`, `VerificationsAPI` に個別スコープを設定

**設定値**:

| スコープ | レート | 対象 |
|----------|--------|------|
| `anon` | 30/分 | 未認証ユーザー全般 |
| `user` | 120/分 | 認証済みユーザー全般 |
| `contact` | 5/時間 | お問い合わせフォーム |
| `like` | 60/分 | いいね送信 |
| `message` | 30/分 | メッセージ送受信 |
| `upload` | 20/時間 | 画像アップロード（アバター・LCIQ・本人確認書類） |

---

### 2. ファイルアップロードのバリデーション追加

**問題**: アバター、LCIQ画像、本人確認書類のアップロードに**サイズ制限もMIMEタイプチェックもなかった**。巨大ファイルによるDoS攻撃や、不正なファイル形式のアップロードが可能だった。

**修正箇所**: `core/api_views.py`

**修正内容**:
- `_validate_image()` ヘルパー関数を追加
- 許可MIMEタイプ: `image/jpeg`, `image/png`, `image/webp`
- 最大サイズ: **5MB**
- 以下の3エンドポイントに適用:
  - `POST /api/me/avatar/` （MeAvatarAPI）
  - `POST /api/me/lciq-image/` （MeLciqImageAPI）
  - `POST /api/verifications/` （VerificationsAPI）

---

### 3. 位置情報（緯度・経度）のAPI露出を制限

**問題**: `ProfileSerializer` がユーザーの緯度・経度を**生の値のまま**APIレスポンスに含めていた。マッチングサイトで正確な位置情報を公開することは、ストーキングや住所特定のリスクに直結する。

**修正箇所**: `core/api_serializers.py`

**修正内容**:
- `latitude` / `longitude` フィールドを `SerializerMethodField` に変更
- 値を**小数第1位に丸める**（`round(float(value), 1)`）
- これにより精度は約**10km**となり、おおまかなエリアは分かるが住所特定は不可能になる
- DB保存値（検索用）は元のまま保持 — 半径検索のロジックに影響なし
- `ProfileUpdateSerializer`（自分のプロフィール更新）は従来通り正確な値を受け取り保存可能

---

### 4. メッセージテキストの長さ制限追加

**問題**: `MessagesAPI.post` でメッセージ本文の長さチェックが一切なかった。悪意あるユーザーが数MB単位の巨大テキストを送信でき、DB容量圧迫やレンダリング負荷の原因になり得た。

**修正箇所**: `core/api_views.py` — `MessagesAPI.post`

**修正内容**:
- テキストが **2000文字** を超えた場合、`400 Bad Request` を返す
- エラーコード: `TEXT_TOO_LONG`

---

### 5. DEBUGモードによるメッセージ送信制限バイパスの除去

**問題**: メッセージ送信の権限チェックに `settings.DEBUG` による分岐があった:

```python
# 修正前（危険）
if not (settings.DEBUG or me.is_staff):
    if not me.userprofile.can_send_message_to(other):
        ...
```

本番環境で誤って `DEBUG=True` が設定された場合、**全ユーザーがプラン未加入でも無制限にメッセージを送信可能**になる致命的なリスクがあった。

**修正箇所**: `core/api_views.py` — `MessagesAPI.post`

**修正内容**:
```python
# 修正後（staffのみバイパス）
if not me.is_staff:
    if not me.userprofile.can_send_message_to(other):
        ...
```

- `settings.DEBUG` 条件を完全に除去
- `is_staff`（管理者）のみバイパスを許可

---

## 未対応の推奨事項（次回以降）

以下は今回のスコープ外だが、対応を推奨する:

| 優先度 | 項目 | 概要 |
|--------|------|------|
| 高 | print文の除去 | `payments/views.py`, `core/filters.py` に本番不要のprint文が残存 |
| 高 | Webhook冪等性 | Stripe webhookでセッションIDの重複チェックがない |
| 高 | N+1クエリ | ProfileSerializerの `verification_count` 等がプロパティ経由でDBアクセス |
| 中 | トークン有効期限 | TokenAuthに期限設定がない。JWT移行を検討 |
| 中 | セキュリティヘッダー | CSP / HSTS が未設定 |
| 中 | Report処理の原子性 | バン判定が非アトミック（レースコンディション） |
| 低 | GDPR対応 | データエクスポート・削除APIが未実装 |
| 低 | NGワード強化 | Unicode変種でバイパス可能 |
| 低 | テスト | テストファイルがほぼ空 |
| 低 | ソフトデリート | ユーザー削除がカスケード。休止機能なし |

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `config/settings.py` | DRFスロットリング設定を追加 |
| `core/api_views.py` | レートスコープ設定、画像バリデーション関数追加、メッセージ長制限、DEBUGバイパス除去 |
| `core/api_serializers.py` | 緯度経度を丸めるSerializerMethodField化 |
| `core/api_contact.py` | throttle_scope有効化 |
