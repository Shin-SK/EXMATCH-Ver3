# EXMATCH Phase 2 バグ修正レポート

**実施日:** 2026-04-10 12:51
**対象:** bug-audit-2026-04-09.md で検出された BUG-003, SUSP-001, BUG-004, SUSP-004, F-002
**方針:** diff のみ / 変更最小 / API キー名の破壊的変更なし

---

## 1. BUG-003: UserProfileDetail checkMatched/checkLiked 多重取得の改善

### 問題
プロフィール詳細画面の初回表示で、マッチ済み/いいね済み判定のために全ページ(最大5ページ)をループ取得していた。

### 修正内容

**バックエンド (core/api_views.py)**
- `MatchesAPI` に `partner_id` クエリパラメータを追加。指定時は該当ユーザーとのマッチのみに絞り込み。
- `LikesSentAPI` に `to_user_id` クエリパラメータを追加。指定時は該当ユーザーへのいいねのみに絞り込み。
- 既存の呼び出し元(Matches.vue, Search.vue 等)はパラメータ未指定のため影響なし。

**フロントエンド (api.js)**
- `fetchMatches(page, extra)` / `fetchLikesSent(page, extra)` に第2引数 `extra` を追加(デフォルト空オブジェクト)。既存呼び出しは互換。

**フロントエンド (UserProfileDetail.vue)**
- `checkMatched()`: ループ廃止 → `fetchMatches(1, { partner_id })` の1回で判定。
- `checkLiked()`: ループ廃止 → `fetchLikesSent(1, { to_user_id })` の1回で判定。

### 効果
- 初回表示の API コール: 最大10回 → 2回に削減。

---

## 2. SUSP-001: Search で like 後に一覧の該当アイテム状態が即時更新されない問題

### 問題
`like()` で `matchedSet` / `likedSet` を更新しているが、型(Number vs String)の不一致により `Set.has()` が false を返す可能性があった。

### 修正内容

**フロントエンド (Search.vue)**
- `like(uid)`: 受け取った uid を `Number()` で正規化してから Set に追加。
- `buildMatchedSet()`: Set への追加時に `Number(uid)` で統一。
- `buildLikedSet()`: 同上。

### 効果
- `matchedSet.has(p.id)` / `likedSet.has(p.id)` が型一致で確実に動作。
- いいね後、即座にカード上のボタンが「いいねしました！」または「メッセージ」に切り替わる。

---

## 3. BUG-004: ChatRoom 既読化エラーハンドリング改善

### 問題
- `loadNew()` 内の `unread.readThread()` が await されており、失敗時にメッセージ表示処理自体がブロックされるリスクがあった。
- エラーログが出力されず、既読化失敗の原因追跡が困難だった。

### 修正内容

**フロントエンド (ChatRoom.vue)**
- `loadNew()` 内: `readThread()` を fire-and-forget に変更。`.catch()` でステータスコード・レスポンスデータをログ出力。
- `onMounted()` 内: 同様に fire-and-forget + catch ログ。
- メッセージの表示・スクロールは `readThread()` の成否に依存しない。

### 効果
- 既読化 API が失敗してもチャット表示は正常動作。
- 失敗時に `[ChatRoom] readThread failed` + ステータスコードがコンソールに出力され、原因追跡が可能。

---

## 4. SUSP-004: Match / ChatThread 系の partner/user 参照ゆれ整理

### 問題
`Matches.vue` と `Chats.vue` のテンプレートで `m.partner?.id || m.user?.id` のような fallback パターンが散在し、可読性が低く参照漏れのリスクがあった。

### 修正内容

**フロントエンド (Matches.vue)**
- `partner(m)` ヘルパー関数を追加: `m.partner || m.user || {}`
- テンプレート内の全ての `(m.partner || m.user)` / `m.partner?.id || m.user?.id` を `partner(m)` に統一。
- `doUnmatch()` のフィルター条件も統一。

**フロントエンド (Chats.vue)**
- 同様に `partner(t)` ヘルパー関数を追加。
- テンプレート内の全参照を統一。

### 効果
- partner キーが undefined でも空オブジェクトにフォールバックし、表示崩れを防止。
- サーバー側のキー名変更なし（破壊的変更なし）。

---

## 5. F-002: checkbox カスタム項目の保存/再表示安定化

### 問題
- 初期化時: 文字列 → 配列変換で空文字が混入する可能性。
- 保存時: `Array.join(',')` で空要素が含まれると `,,,` のような不正な CSV になる可能性。
- 再読込時にパース結果が変わり、チェック状態がずれる。

### 修正内容

**フロントエンド (ProfileEdit.vue)**
- 初期化時: 既に配列の場合も `.filter(Boolean)` で空要素を除去。
- 保存時: 配列 → CSV 変換前に `.filter(Boolean)` で空要素除去。文字列が来た場合も一度 split → trim → filter → join で正規化。

### 効果
- `["a", "", "b"]` → `"a,b"` のように安定した CSV を生成。
- 保存 → 再読込 → 再表示で冪等性が保たれる。

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `core/api_views.py` | MatchesAPI に partner_id フィルタ追加、LikesSentAPI に to_user_id フィルタ追加 |
| `frontend/src/api.js` | fetchMatches / fetchLikesSent に extra パラメータ追加 |
| `frontend/src/views/UserProfileDetail.vue` | checkMatched / checkLiked を1回呼び出しに簡略化 |
| `frontend/src/views/Search.vue` | like / buildMatchedSet / buildLikedSet で Number() 型統一 |
| `frontend/src/views/ChatRoom.vue` | readThread を fire-and-forget 化 + エラーログ追加 |
| `frontend/src/views/Matches.vue` | partner() ヘルパー追加、テンプレート参照統一 |
| `frontend/src/views/Chats.vue` | partner() ヘルパー追加、テンプレート参照統一 |
| `frontend/src/views/ProfileEdit.vue` | checkbox 初期化・保存時の空要素除去 |

---

## 手動確認チェックリスト

- [ ] 詳細画面の初回表示で不要な多重 API が減っている（DevTools Network タブで確認）
- [ ] Search で like 後に一覧状態が即時変わる
- [ ] Matches / Chats で相手情報が欠けない
- [ ] 既読化失敗時に黙って壊れない（DevTools Console で `readThread failed` が出ること）
- [ ] checkbox カスタム項目が保存後に崩れない

---

## Phase 3 に残す技術負債

| ID | 内容 | 備考 |
|----|------|------|
| BUG-002 | ProfilePhoto 正本化 | 現時点では互換運用中。実害再現が取れた場合に正本化を検討 |
| SUSP-003 | Verification 承認ステータスの自動同期 | WebSocket or ポーリング設計が必要 |
| L-002 | ProfileField required バリデーション未実装 | API 仕様変更を伴う |
| UX-001 | エラーメッセージの詳細化（全画面） | 全画面横断の改善 |

**除外:** SUSP-002 (Stripe webhook) は一次確認で実装済みと確定。追加改善が必要な場合は冪等性/運用監査として別途扱う。
