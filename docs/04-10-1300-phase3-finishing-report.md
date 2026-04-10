# EXMATCH Phase 3 仕上げレポート

**実施日:** 2026-04-10 13:00
**対象:** UX-001, UX-002, L-002, SUSP-003
**方針:** diff のみ / 変更最小 / 破壊的変更なし / WebSocket 実装なし

---

## 1. UX-001: detail_code の構造化

### 問題
`sendMessage` の catch で `Error.message` に `[DETAIL_CODE]` を文字列連結し、ChatRoom 側で `.includes()` でパースしていた。拡張しづらく、誤マッチのリスクがあった。

### 修正内容

**api.js**
- `sendMessage` の catch で、`detail_code` がある 403/400 レスポンスの場合、`Error` オブジェクトに `detail_code` と `status` プロパティを直接付与して throw。
- 既存の `message` プロパティも維持（`data.detail` をそのまま使用）。

**ChatRoom.vue**
- `doSend` の catch を `e.detail_code` ベースの `ERR_MAP` ルックアップに変更。
- `.includes()` による文字列パースを廃止。
- マップに無いコードはフォールバックで `e.message || '送信に失敗しました'` を表示。

### 効果
- 新しい detail_code が追加されても `ERR_MAP` に1行追加するだけで対応可能。
- 文字列の部分一致による誤マッチが起きない。

---

## 2. UX-002: sending/busy フラグによる二重送信防止

### 問題
like / block 操作中にボタンが有効なまま残り、連打で二重リクエストが発生する可能性があった。

### 修正内容

**UserProfileDetail.vue**
- `sendingLike` / `sendingBlock` ref を追加。
- `doLike()`: 先頭でガード、finally でリセット。ボタンに `:disabled="sendingLike"` + テキスト切替。
- `doToggleBlock()`: 同様にガード + `:disabled="sendingBlock"`。

**Search.vue**
- `likingSet` (Set) を追加。いいね通信中のユーザー ID を保持。
- `like()`: 先頭で `likingSet.has(id)` ガード。finally で除去。
- UserCard の like イベントは呼び出し元でガードされるため、テンプレート変更不要。

**ChatRoom.vue**
- 既に `sending` フラグが実装済み。変更なし。

### 効果
- 全ての書き込み系操作で二重送信が防止される。
- 通信中はボタンが disabled になり、ユーザーに状態が伝わる。

---

## 3. L-002: ProfileField required バリデーション実装

### 問題
`ProfileField.required = True` のフィールドが定義されていても、`MeCustomFieldsAPI.patch()` で未入力チェックがなく、空値で保存できた。

### 修正内容

**バックエンド (core/api_views.py) — MeCustomFieldsAPI.patch()**
- `transaction.atomic()` の前に required チェックを追加。
- 送信されたフィールドが空の場合 → missing に追加。
- 送信されていないフィールド → 既存の DB 値を確認し、空なら missing に追加。
- missing がある場合、400 レスポンスを返す:
  ```json
  {
    "detail": "必須項目が未入力です: フィールド名1, フィールド名2",
    "detail_code": "REQUIRED_FIELDS_MISSING",
    "missing_fields": ["フィールド名1", "フィールド名2"]
  }
  ```

**フロントエンド (ProfileEdit.vue)**
- `saveAll()` の catch で `e.response.data.detail` を alert に表示。
- サーバーから返る「必須項目が未入力です: ...」がそのままユーザーに見える。

### 効果
- required な custom field を空で保存しようとすると 400 で拒否される。
- エラーメッセージに未入力フィールド名が表示される。

---

## 4. SUSP-003: Verification 承認ステータスの画面復帰時再取得

### 問題
本人確認書類を提出後、管理画面で承認されても ProfileEdit 画面では pending のまま表示され続けた。定期同期もリアルタイム通知もなかった。

### 修正内容

**ProfileEdit.vue**
- `visibilitychange` イベントリスナーを追加。画面がフォアグラウンドに戻った時に `listVerifications()` を再取得。
- `onActivated` フックでも再取得（keep-alive 環境での復帰対応）。
- 既にデータがある場合のみ再取得し、通信過多を防止。

### 効果
- ユーザーが別タブ/別アプリから戻った時に最新の承認ステータスが反映される。
- WebSocket 不要で、必要最小限の通信で済む。

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `frontend/src/api.js` | sendMessage で detail_code を Error オブジェクトに構造化付与 |
| `frontend/src/views/ChatRoom.vue` | doSend を ERR_MAP ルックアップに変更 |
| `frontend/src/views/UserProfileDetail.vue` | sendingLike / sendingBlock ガード + ボタン disabled |
| `frontend/src/views/Search.vue` | likingSet による like 二重送信防止 |
| `core/api_views.py` | MeCustomFieldsAPI.patch() に required バリデーション追加 |
| `frontend/src/views/ProfileEdit.vue` | saveAll エラー表示改善 + verification 画面復帰時再取得 |

---

## 手動確認チェックリスト

- [ ] ChatRoom で FIRST_MESSAGE_ONLY が構造化された分岐で正しく表示される
- [ ] like / send を連打しても二重実行されない
- [ ] required な custom field を空で保存 → エラーが出て保存されない
- [ ] 本人確認を管理画面で承認後、ProfileEdit でタブ復帰すると状態が更新される

---

## Phase 1〜3 完了後の残存技術負債

| ID | 内容 | 備考 |
|----|------|------|
| BUG-002 | ProfilePhoto 正本化 | 現時点では互換運用中。実害再現が取れた場合に検討 |
| SUSP-003+ | Verification リアルタイム通知 | 現状は画面復帰時再取得で対応。WebSocket は将来検討 |
| UX-003 | チャット WebSocket 化 | 現状4秒ポーリングで動作中。モバイル最適化は将来課題 |
