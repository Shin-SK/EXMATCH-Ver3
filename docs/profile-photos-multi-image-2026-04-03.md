# プロフィール画像 複数枚対応 改修報告書

**日付**: 2026-04-03
**ブランチ**: staging

---

## 変更概要

プロフィール画像を単一画像（`UserProfile.profile_image`）から複数枚管理（最大5枚）に改修。
既存の `profile_image` フィールドは後方互換のため残し、正本は新設の `ProfilePhoto` テーブルに移行。

---

## 変更ファイル一覧

### バックエンド
| ファイル | 変更内容 |
|---|---|
| `core/models.py` | `ProfilePhoto` モデル追加、`_profile_photo_path` 関数追加 |
| `core/api_serializers.py` | `ProfilePhotoSerializer` 追加、`ProfileSerializer` に `photos` フィールド追加、`profile_image_url` を ProfilePhoto 優先に変更 |
| `core/api_views.py` | `MePhotosAPI`, `MePhotoDeleteAPI`, `MePhotosReorderAPI` 追加、`MeAvatarAPI` を互換レイヤーに改修、アップロード上限を 10MB に変更 |
| `core/api_urls.py` | `/api/me/photos/`, `/api/me/photos/reorder/`, `/api/me/photos/<id>/` 追加 |
| `core/admin.py` | `ProfilePhotoAdmin` 追加 |
| `core/tests.py` | `ProfilePhotoTestCase` 追加（13テストケース） |
| `core/migrations/0030_profilephoto.py` | ProfilePhoto テーブル作成 |
| `core/migrations/0031_migrate_profile_images.py` | 既存 profile_image を ProfilePhoto に移行するデータマイグレーション |

### フロントエンド
| ファイル | 変更内容 |
|---|---|
| `frontend/src/api.js` | `fetchMyPhotos`, `uploadPhoto`, `deletePhoto`, `reorderPhotos` 追加 |
| `frontend/src/components/ImageCropModal.vue` | **新規**: 画像編集モーダル（crop/zoom/rotate） |
| `frontend/src/views/ProfileEdit.vue` | 複数画像グリッド表示、ドラッグ並び替え、画像編集モーダル連携 |
| `frontend/src/views/UserProfileDetail.vue` | Splide カルーセルによる複数画像スワイプ表示 |
| `frontend/src/utils/pickAvatar.js` | `photos` 配列対応 |

---

## モデル追加内容

### ProfilePhoto
| フィールド | 型 | 説明 |
|---|---|---|
| `id` | AutoField | PK |
| `user` | FK -> User | 所有者 |
| `image` | ImageField | 画像ファイル（Cloudinary 保存） |
| `order` | PositiveSmallIntegerField | 並び順（0始まり、最小がメイン） |
| `created_at` | DateTimeField | 作成日時 |
| `updated_at` | DateTimeField | 更新日時 |

インデックス: `(user, order)`

クラスメソッド:
- `reorder(user, ordered_ids)` — 指定順で order を詰め直す
- `compact_order(user)` — 隙間なく order を詰め直す
- `sync_main_to_profile(user)` — メイン画像を `UserProfile.profile_image` に同期

---

## API 一覧

| Method | Endpoint | 説明 |
|---|---|---|
| `GET` | `/api/me/photos/` | 自分の画像一覧 |
| `POST` | `/api/me/photos/` | 画像追加（multipart） |
| `DELETE` | `/api/me/photos/<id>/` | 画像削除 |
| `POST` | `/api/me/photos/reorder/` | 並び替え（`{"ordered_ids": [3,1,5]}`） |
| `POST` | `/api/me/avatar/` | **互換**: メイン画像を差し替え |
| `DELETE` | `/api/me/avatar/` | **互換**: メイン画像を削除 |

レスポンス形式（各画像）:
```json
{
  "id": 1,
  "image_url": "https://res.cloudinary.com/.../profiles/xxx.jpg",
  "order": 0
}
```

---

## 既存 avatar API との互換方針

- `/api/me/avatar/` POST → メイン画像（order 最小）があれば差し替え、なければ新規作成
- `/api/me/avatar/` DELETE → メイン画像を削除し、order を詰め直し
- `ProfileSerializer.profile_image_url` → `ProfilePhoto` を優先参照、なければ旧 `profile_image` にフォールバック
- `UserBriefSerializer.profile_image_url` → 同上
- `pickAvatar.js` → `photos` 配列の先頭を優先参照

---

## 画像編集UI

### 採用ライブラリ
- **vue-advanced-cropper** (v2.8.9) — 既にプロジェクトに導入済み

### 選定理由
- Vue 3 ネイティブ対応
- crop / zoom / rotate すべてサポート
- アスペクト比固定（1:1）に対応
- 軽量で依存少なめ
- 既に package.json に含まれていたため追加インストール不要

### 機能
- ファイル選択後に編集モーダルが開く
- 1:1 アスペクト比でクロップ
- ズームイン/アウト
- 左右回転（90度単位）
- 確定後に長辺 1600px に縮小 + JPEG 85% 圧縮してからアップロード

---

## カルーセルUI

### 採用ライブラリ
- **@splidejs/vue-splide** (v0.6.12) — 既にプロジェクトに導入済み

### 選定理由
- 軽量・高パフォーマンス
- スワイプ/タッチ操作対応
- ページネーション（ドット）表示
- 既に package.json に含まれていたため追加インストール不要

---

## 制限値

| 項目 | 値 |
|---|---|
| 最大枚数 | 5枚 |
| ファイルサイズ上限 | 10MB（サーバー側） |
| 許可MIMEタイプ | image/jpeg, image/png, image/webp |
| フロント圧縮 | 長辺1600px、JPEG 85% |
| レートリミット | upload スコープ（20回/時） |

---

## 既存データ移行の扱い

- `0031_migrate_profile_images.py` でデータマイグレーションを実装
- 既存の `UserProfile.profile_image` が存在するユーザーについて、`ProfilePhoto`（order=0）を自動作成
- 冪等性あり（既に ProfilePhoto がある場合はスキップ）
- `UserProfile.profile_image` フィールドは削除しない（後方互換）
- `sync_main_to_profile` で ProfilePhoto → profile_image の同期を維持

---

## 残課題

1. **N+1 問題**: `ProfileSerializer.get_profile_image_url` と `get_photos` で都度クエリが走る。一覧表示でパフォーマンスが気になる場合は `prefetch_related` や annotation で最適化する
2. **Cloudinary eager transformation**: アップロード時にサムネイルを事前生成する仕組みは未実装。表示時のオンデマンド変換で当面は十分
3. **`f_auto,q_auto` の配信URL付与**: `Avatar.vue` の Cloudinary URL 変換に `f_auto,q_auto` を追加すると転送量をさらに削減できる
4. **`UserProfile.profile_image` フィールドの完全廃止**: 十分に移行が進んだ段階で、マイグレーションで削除可能
5. **モバイル向けタッチ並び替え**: 現在はHTML5 Drag & Drop API使用。モバイルでの並び替えは長押し等のライブラリ（SortableJS等）導入を検討
