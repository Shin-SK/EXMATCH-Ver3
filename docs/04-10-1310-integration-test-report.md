# EXMATCH Phase 1-3 総合テストレポート

**実施日:** 2026-04-10 13:10
**対象:** Phase 1-3 全修正後のコードベース
**方法:** 読解ベース（実行テストなし）
**目的:** 修正同士の干渉・副作用・退行バグの検出

---

## 1. テスト対象

Phase 1-3 で変更された全ファイル:
- `core/api_views.py` — ReportCreateAPI, MatchesAPI, LikesSentAPI, MeCustomFieldsAPI, MessagesAPI
- `core/models.py` — Report constraint (created_date)
- `core/api_serializers.py` — lat/lon 丸め
- `frontend/src/api.js` — sendMessage 構造化, fetchMatches/fetchLikesSent extra params
- `frontend/src/views/ChatRoom.vue` — ERR_MAP, readThread fire-and-forget
- `frontend/src/views/Search.vue` — Number()型統一, likingSet
- `frontend/src/views/UserProfileDetail.vue` — checkMatched/checkLiked 最適化, sendingLike/sendingBlock
- `frontend/src/views/Matches.vue` — partner() ヘルパー
- `frontend/src/views/Chats.vue` — partner() ヘルパー
- `frontend/src/views/ProfileEdit.vue` — checkbox安定化, saveAll エラー表示, verification再取得
- `frontend/src/stores/useUnread.js` — readThread エラーログ

---

## 2. 実施した主要シナリオ

### シナリオ1: 新規ユーザー → プロフ編集 → 検索 → いいね → マッチ → チャット
コード上の全フローを追跡。api.js → バックエンド API → serializer → レスポンス → フロント state 更新 の一連を確認。

### シナリオ2: ChatRoom でのエラー分岐全パターン
FIRST_MESSAGE_ONLY / BLOCKED / NG_WORD / TEXT_TOO_LONG / REQUIRED_TEXT / detail_code なし / ネットワークエラー のそれぞれで ERR_MAP のフォールバックを確認。

### シナリオ3: 通報 → 重複通報
ReportCreateAPI の constraint + IntegrityError → 409 の流れを確認。

### シナリオ4: like 連打 / block 連打
sendingLike / sendingBlock / likingSet のガードロジックと finally でのリセットを確認。

### シナリオ5: ProfileEdit 保存 → required チェック → checkbox 往復
MeCustomFieldsAPI.patch() のバリデーション → フロントの alert 表示を確認。

### シナリオ6: verification 画面復帰再取得
visibilitychange リスナーの登録・発火・再取得を確認。

---

## 3. 確認できた正常動作

### A. 認証・初期導線
- [x] api.js interceptor: 401 → localStorage.removeItem → /login リダイレクト — **正常**
- [x] Token ヘッダー付与: `Token ${t}` — **正常**
- [x] `_Base.initial()` で `set_current_user(request.user)` — SafeUserManager 動作 — **正常**

### B. プロフィール編集
- [x] `updateMe()` → `ProfileUpdateSerializer` — 固定項目更新 — **正常**
- [x] checkbox 初期化: 文字列→配列変換、空文字除去 — **正常**
- [x] checkbox 保存: 配列→CSV 変換時に `.filter(Boolean)` — **正常**、冪等性確保
- [x] `saveAll()` catch: `e.response.data.detail` を alert に表示 — **正常**
- [x] verification一覧: `listVerifications()` → `vMap` computed — **正常**

### C. Search / Like / Match
- [x] `like()`: `Number(uid)` で型統一 — **正常**
- [x] `likingSet` ガード: 先頭で `has()` チェック、finally で delete — **正常**、永久 disable にならない
- [x] `buildMatchedSet/buildLikedSet`: `Number(uid)` → Set — **正常**
- [x] `matchedSet.has(p.id)`: API から返る `p.id`(Number) と Set 内の Number が型一致 — **正常**
- [x] `buildMatchedSet` 内の `fetchMatches(p)`: extra={} デフォルト適用 — 既存呼び出し互換 **正常**
- [x] if (uid) ガード: undefined/null/0 は Set に入らない — NaN 混入なし — **正常**

### D. UserProfileDetail
- [x] `checkMatched(userId)`: `fetchMatches(1, { partner_id: userId })` — 1回で判定 — **正常**
- [x] `checkLiked(userId)`: `fetchLikesSent(1, { to_user_id: userId })` — 1回で判定 — **正常**
- [x] `partner_id` は文字列(route param)だが Django が int に自動変換 — **正常**
- [x] `sendingLike.value` / `sendingBlock.value`: finally でリセット — **正常**、永久 disable にならない
- [x] テンプレートの `:disabled="sendingLike"` / `:disabled="sendingBlock"` — **正常**

### E. Chat / Messages
- [x] `sendMessage` catch: 403+detail_code → Error に `detail_code` プロパティ付与 — **正常**
- [x] `sendMessage` catch: 400+detail_code → 同上 — **正常**
- [x] `sendMessage` catch: detail_code なし → 元の Axios エラーを re-throw — **正常**
- [x] ChatRoom `doSend`: `ERR_MAP[code]` ルックアップ — 未知のコードは `e.message` フォールバック — **正常**
- [x] ChatRoom `loadNew`: readThread fire-and-forget、catch でログ出力 — **正常**
- [x] readThread 失敗時: メッセージ表示・スクロールに影響なし — **正常**
- [x] `sending` フラグ: textarea disabled + ボタン disabled — **正常**（Phase 1 から既存）

### F. 通報 / ブロック
- [x] Report constraint: `created_date` (DateField) で同一日判定 — **正常**
- [x] IntegrityError → 409 + `DUPLICATE_REPORT` — **正常**
- [x] `transaction.atomic()` で包んでいる — **正常**
- [x] BlockToggleAPI: toggle ロジック — **正常**（Phase 1-3 で変更なし）

### G. partner/user 参照統一
- [x] Matches.vue: `partner(m)` ヘルパー — `m.partner || m.user || {}` — **正常**
- [x] Chats.vue: `partner(t)` ヘルパー — `t.partner || t.user || {}` — **正常**
- [x] `partner(x).id` が undefined の場合: `unread.of(undefined)` → `this.map?.[undefined] || 0` → 0 — 表示崩れなし — **正常**
- [x] ChatThreadsAPI は `partner` キーで返す — Chats.vue の `partner(t)` で即取得 — **正常**
- [x] MatchSerializer は `partner` キーで返す — Matches.vue の `partner(m)` で即取得 — **正常**

---

## 4. 確認できた不具合

### BUG-P3-001: ProfileEdit.vue の visibilitychange リスナーが解除されない

**分類:** 確認できた不具合
**導入フェーズ:** Phase 3
**優先度:** MEDIUM

**症状:** ProfileEdit 画面を開いて離脱するたびに `visibilitychange` リスナーが蓄積する。タブ切替のたびに `listVerifications()` が蓄積分だけ重複発火する。

**発生条件:** ProfileEdit → 別画面 → ProfileEdit → 別画面 … を繰り返す

**再現手順:**
1. ProfileEdit を開く → `onMounted` で `addEventListener('visibilitychange', onVisibilityChange)` が登録
2. 別画面に遷移（vue-router push）
3. ProfileEdit を再度開く → 同じ関数が再度登録（2個目）
4. タブ切替 → `onVisibilityChange` が2回発火 → `listVerifications()` が2回呼ばれる
5. N回繰り返すと N重取得になる

**原因候補:**
`frontend/src/views/ProfileEdit.vue` L125 で `addEventListener` しているが、`onBeforeUnmount` / `onUnmounted` での `removeEventListener` がない。

**影響範囲:** 
- 通常利用では数回程度の蓄積なので実害は小さい
- ただし SPA で長時間使うユーザーでは通信増加

**修正方針:**
`onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVisibilityChange))` を追加。

---

## 5. 強く疑われる不具合

### SUSP-P3-001: required custom field + コメントアウトされた UI の組み合わせ

**分類:** 強く疑われる不具合（条件付き）
**導入フェーズ:** Phase 3
**優先度:** LOW（現時点で required=True の ProfileField が存在しなければ発火しない）

**症状:** 管理画面で `required=True` の ProfileField を新規追加した場合、既存ユーザーが ProfileEdit で保存しようとすると、必須項目未入力エラーで保存が拒否される。ただしカスタム項目の入力 UI はテンプレートでコメントアウトされているため、ユーザーが入力する手段がない。

**発生条件:**
1. ProfileField に `required=True` のレコードが存在する
2. `ProfileEdit.vue` のカスタム項目セクション（L409-519）がコメントアウトのまま
3. 既存ユーザーが saveAll() を実行

**コード上の根拠:**
- `MeCustomFieldsAPI.patch()` L568-587: 全 `required` フィールドをチェック
- `saveAll()` L140-149: `fields.value` をイテレートして payload を構築。コメントアウトされた UI から値は入力されないが、`fetchMyCustomFields()` で取得した既存値は `customVals.value` に入っている
- 新規追加された required フィールドは既存値がないため `customVals.value[k]` が `undefined` → `payload[k]` が `''` → required チェックで拒否

**影響範囲:**
- 現時点でカスタム項目 UI が無効なので、required field を追加しなければ問題なし
- カスタム項目 UI を有効化すれば解消される

**修正方針:**
- カスタム項目 UI をアンコメントするか
- `required` バリデーションを「リクエストに含まれたフィールドのみ」に限定する

---

## 6. 副作用・退行バグの有無

### detail_code 構造化の副作用
- `sendMessage` は ChatRoom.vue からのみ呼ばれる。他のファイルでは import されていない — **副作用なし**
- `detail_code` がないエラー（例: 500、ネットワークエラー）では元の Axios エラーがそのまま throw される。ChatRoom の `ERR_MAP[undefined]` は undefined を返し、`e.message` にフォールバック — **副作用なし**
- Error オブジェクトの `message` プロパティは `data.detail || 'Forbidden'` で設定。従来の `${data.detail} [${data.detail_code}]` 連結形式から変更されたが、ChatRoom は `ERR_MAP` で分岐するため `message` を直接参照しない — **副作用なし**

### required バリデーションの副作用
- バリデーションは `MeCustomFieldsAPI.patch()` のみに追加。GET は影響なし — **副作用なし**
- `updates` が空の場合（`if not updates`）は required チェックの前に 400 で返る。required チェックが不要な空リクエストをブロックすることはない — **副作用なし**
- SUSP-P3-001 として記載した条件付きの問題あり

### verification 再取得の副作用
- BUG-P3-001 として記載（リスナー未解除）
- `onActivated` は keep-alive 環境でのみ発火。現時点で ProfileEdit が keep-alive 内で使われているかは不明だが、keep-alive 外なら `onActivated` は無視される — **実害なし（keep-alive 未使用の場合）**

### like / sending ガードの副作用
- 全て `finally` でリセット — **永久 disable にならない。副作用なし**
- 例外が throw されても `finally` は実行される — **正常**

### Search の型統一修正の副作用
- `Number()` は `if (uid)` ガードの後に呼ばれるため、undefined/null/0 は Set に入らない — **NaN 混入なし。副作用なし**

### fetchMatches / fetchLikesSent の extra パラメータ追加の副作用
- デフォルト `extra={}` のため、既存の `fetchMatches(p)` 呼び出し（Search.vue, Matches.vue 等）は `params: { page: p }` のまま — **互換性維持。副作用なし**

---

## 7. 優先度順の修正候補

| # | ID | 内容 | 優先度 | 工数 | 備考 |
|---|-----|------|--------|------|------|
| 1 | BUG-P3-001 | ProfileEdit visibilitychange リスナー未解除 | MEDIUM | 極小 | 1行追加で修正 |
| 2 | SUSP-P3-001 | required field + UI コメントアウトの矛盾 | LOW | 小 | 条件付き。現時点では発火しない可能性大 |

---

## 8. いますぐ直すべきもの TOP5

**今回は TOP5 に該当する緊急修正はありません。**

確認できた不具合は1件（BUG-P3-001）で、影響は「通信の軽微な重複」に留まります。
強く疑われる不具合は1件（SUSP-P3-001）で、条件付きかつ現時点では発火しない可能性が高いです。

修正自体は簡単（1行追加）なので、次の実装サイクルの冒頭で直すのが適切です。

---

## 9. 今回は問題なしと判断した項目

以下は明示的に確認し、問題なしと判断した項目です。

| 確認項目 | 結果 | 根拠 |
|---------|------|------|
| detail_code なしのエラーで ChatRoom が壊れないか | 問題なし | ERR_MAP[undefined] → undefined → e.message フォールバック |
| sendMessage の message プロパティが消えていないか | 問題なし | `new Error(data.detail \|\| 'Forbidden')` で設定済み |
| like ボタンが永久に disabled にならないか | 問題なし | 全て finally でリセット |
| block ボタンが永久に disabled にならないか | 問題なし | 全て finally でリセット |
| Number() で id 比較が壊れないか | 問題なし | if (uid) ガードで falsy 値を除外 |
| partner() ヘルパーで表示が崩れないか | 問題なし | 空オブジェクト {} へのフォールバック |
| fetchMatches extra パラメータで既存呼び出しが壊れないか | 問題なし | デフォルト {} で互換 |
| MatchesAPI partner_id フィルタで通常一覧が壊れないか | 問題なし | パラメータ未指定時はフィルタ適用なし |
| readThread 失敗で unread バッジが勝手に減らないか | 問題なし | useUnread.readThread は API 成功後にのみ count を減算 |
| Report constraint が正しく機能するか | 問題なし | created_date (DateField) で同一日判定 |
| Stripe webhook | 確認対象外 | 一次確認で実装済みと確定。Phase 1-3 で変更なし |
| throttle_scope | 確認対象外 | Phase 1-3 で変更なし。settings 側の確認が必要だが今回のスコープ外 |

---

## 10. まとめ

### Phase 1-3 の修正で安定化した点

1. **Report 重複通報**: created_at → created_date に変更し、同一日 constraint が正しく機能するようになった
2. **UserProfileDetail の API 効率**: 最大10回 → 2回に削減。partner_id / to_user_id フィルタは安全に動作
3. **Search の like 即時反映**: Number() 型統一で Set.has() が確実に動作
4. **ChatRoom のエラー表示**: 文字列パース → ERR_MAP ルックアップに変更。拡張性・安全性向上
5. **ChatRoom の readThread**: fire-and-forget 化でメッセージ表示がブロックされなくなった
6. **partner/user 参照**: ヘルパー関数で一元管理。空オブジェクトフォールバックで表示崩れ防止
7. **like/block 二重送信**: sending ガードが全箇所で正しく動作
8. **checkbox カスタム項目**: filter(Boolean) で空要素を除去。保存→再表示の冪等性確保

### まだ本番運用上不安が残る点

1. **BUG-P3-001**: ProfileEdit の visibilitychange リスナー未解除（軽微だが修正すべき）
2. **カスタム項目 UI がコメントアウト中**: required バリデーションは実装済みだが、入力 UI がない状態。UI を有効化するか、required field を追加しないかの判断が必要
3. **WebSocket 未導入**: チャットは4秒ポーリング、verification は画面復帰時再取得。リアルタイム性は限定的

### 次の1手として何をやるべきか

1. **BUG-P3-001 を修正**（1行追加: onBeforeUnmount で removeEventListener）
2. **カスタム項目 UI の有効化判断** — コメントアウトを外すかどうかをプロダクト側で決定
3. **手動動作確認** — 読解テストでは拾えないランタイム固有の問題（CSS 崩れ、タイミング依存バグ等）を実機で確認

---

## 結論

**Phase 1-3 の修正は全体として安定しています。**

修正間の干渉・副作用は確認されませんでした。確認できた不具合は1件（リスナー未解除）のみで、影響は軽微です。

前回の監査で誤検知があった領域（Stripe webhook、throttle、partner/user）については:
- Stripe webhook: Phase 1-3 で変更なし。一次確認済みのため問題なし
- throttle: Phase 1-3 で変更なし。settings 側の確認は別途必要
- partner/user: ヘルパー関数で吸収済み。空オブジェクトフォールバックで安全

**本番リリースに向けて、BUG-P3-001 の1行修正を実施すれば、読解ベースでは blocking issue はありません。**

---

**報告日:** 2026-04-10 13:10
**調査者:** Claude Code（読解ベース）
