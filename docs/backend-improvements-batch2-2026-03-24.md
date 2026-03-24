# EXMATCH バックエンド改善 第2弾 報告書

**実施日**: 2026-03-24
**対象**: Django バックエンド（セキュリティ・課金・通報・認証・パフォーマンス・退会）

---

## 変更概要

| # | 項目 | 内容 |
|---|------|------|
| P1 | Stripe webhook 冪等性 | 処理済みイベント記録 + atomic で二重課金を防止 |
| P2 | セキュリティテスト追加 | レートリミット・アップロード制限・メッセージ制限・座標丸め等の回帰テスト |
| P3 | Report/Ban 原子性 | transaction.atomic + select_for_update でレース防止 |
| P4 | N+1 クエリ解消 | verification_count の annotate 化、MatchesAPI の select_related 追加 |
| P5 | print 文除去・logging 化 | payments/views.py, core/filters.py の print を logging に置換 |
| P6 | トークン失効設計 | パスワード変更時・BAN時・退会時にトークン自動失効 |
| P7 | セキュリティヘッダー | HSTS, nosniff, Referrer-Policy, X-Frame-Options 等を追加 |
| P8 | ソフトデリート・退会設計 | deleted_at フィールド + 退会API + 個人情報匿名化 |

---

## 変更ファイル一覧

### 変更
- `payments/views.py` — webhook冪等性 + logging化
- `payments/models.py` — ProcessedWebhookEvent モデル追加
- `payments/tests.py` — webhook冪等性テスト追加
- `notifications/signals.py` — Report/Ban 原子性 + BAN時トークン失効
- `core/api_views.py` — N+1 annotate、MatchesAPI select_related、退会API、deleted_at/is_active フィルタ
- `core/api_serializers.py` — verification_count の annotate キャッシュ対応
- `core/api_urls.py` — MeDeactivateAPI エンドポイント追加
- `core/filters.py` — print → logging
- `core/models.py` — deleted_at フィールド、is_deleted プロパティ
- `core/tests.py` — SecurityTestCase 追加
- `config/settings.py` — セキュリティヘッダー、AccountsConfig 切替
- `accounts/apps.py` — ready() でシグナル登録
- `accounts/signals.py` — パスワード変更時トークン失効（新規）

### 新規ファイル
- `accounts/signals.py`
- `payments/migrations/0004_processedwebhookevent.py`
- `core/migrations/0029_userprofile_deleted_at.py`

---

## 追加した Model / Migration / Setting

### Model
- `payments.ProcessedWebhookEvent` — webhook冪等性用。event_id (unique), event_type, processed_at

### Migration
- `payments/0004_processedwebhookevent.py` — ProcessedWebhookEvent テーブル作成
- `core/0029_userprofile_deleted_at.py` — UserProfile.deleted_at カラム追加

### Setting
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"`
- `X_FRAME_OPTIONS = "DENY"`
- 本番時 (DEBUG=False):
  - `SECURE_HSTS_SECONDS = 31536000`
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - `SECURE_HSTS_PRELOAD = True`
  - `SECURE_SSL_REDIRECT = True`
  - `SECURE_PROXY_SSL_HEADER`
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`

---

## テスト内容

### core/tests.py — SecurityTestCase
| テスト | 検証内容 |
|--------|----------|
| `test_contact_api_throttled` | ContactAPI のレートリミットが効く |
| `test_upload_over_5mb_rejected` | 5MB超のアップロードが 400 |
| `test_upload_invalid_mime_rejected` | 非許可MIMEが 400 |
| `test_message_over_2000_chars_rejected` | 2000字超メッセージが 400 |
| `test_free_user_limited_to_one_message` | フリーユーザーの送信制限 |
| `test_staff_bypasses_message_limit` | staff バイパス |
| `test_lat_lon_rounded_in_response` | 座標が小数第1位に丸められる |
| `test_deactivated_user_hidden_from_profiles` | 退会ユーザーが一覧非表示 |

### payments/tests.py — WebhookIdempotencyTestCase
| テスト | 検証内容 |
|--------|----------|
| `test_duplicate_event_id_rejected` | 同一 event_id は get_or_create で created=False |
| `test_unique_constraint_on_event_id` | unique 制約で IntegrityError |

---

## 影響範囲

- **課金フロー**: webhook が冪等になった。既存の正常フローには影響なし
- **通報/BAN**: 並行通報時の整合性改善。二重BANが起きなくなった
- **プロフィール一覧**: N+1 改善でパフォーマンス向上。レスポンス形式は変更なし
- **認証**: パスワード変更時・BAN時・退会時にトークンが失効。再ログインが必要
- **セキュリティヘッダー**: ブラウザ側の防御が強化。本番でのみ SSL 系が有効
- **退会**: 新API `/api/me/deactivate/` 追加。個人情報を匿名化しつつレコードは残す
- **ログ**: print が消え、logging に統一。本番でのログ追跡が可能に

---

## 残課題

1. **CSP ヘッダー**: Cloudinary 等の外部リソース指定が必要なため今回見送り。フロント確認後に追加推奨
2. **トークン有効期限**: 現行 TokenAuthentication は期限なし。将来的に JWT + refresh token 移行を推奨
3. **退会からの復帰フロー**: 管理画面からの手動復帰は可能だが、ユーザー自身での復帰UIは未実装
4. **ChatThreadsAPI の N+1**: Python 側でループ集約しているため、根本的な改善にはクエリ設計変更が必要
5. **webhook の古いイベントレコード削除**: ProcessedWebhookEvent が無限に増えるため、定期削除ジョブの追加を推奨
6. **ソフトデリート後のデータ完全削除**: GDPR 等に対応するなら一定期間後の物理削除バッチが必要
