# kenshu-manage

製造部門向けの検収管理Webアプリです。発注履歴CSVをアップロードし、今月の未検収案件を一覧表示して、担当者がコメントを入力することで上司が検収状況をリアルタイムに把握できます。

-----

## 機能

- **CSVアップロード**：発注履歴CSV（cp932）をブラウザからアップロード
- **月タブ / 回数タブ**：`yyyy年mm月` の月タブと、その月内のアップロード回数タブで履歴を管理
- **自動引き継ぎ**：同月2回目のアップロード時、管理ナンバーをキーに前回のコメントを自動引き継ぎ。前回から消えた行（検収済み）は自動的に非表示
- **ハイライト表示**：コメントあり=緑 / 今月納期・未コメント=黄 / 納期超過・未コメント=赤
- **コメント入力**：`空欄` / `今月検収` / `来月以降に検収（仕入先と合意済み）` の3択セレクト
- **フィルタ・ソート**：各列ごとのテキストフィルタ、列ヘッダークリックでソート
- **表示切替**：今月案件のみ表示 / 全件表示をワンクリックで切替
- **列名の柔軟対応**：キー列名（管理ナンバー・納期）はフロント・バックエンドそれぞれ1行の変更で対応可能

-----

## 技術スタック

|層       |技術                                   |
|--------|-------------------------------------|
|バックエンド  |Python / FastAPI / uvicorn           |
|フロントエンド |Vite + React 18 + TypeScript         |
|データ保存   |SQLite3（`backend/data/kenshu.db`、標準ライブラリ使用）|
|CSV文字コード|cp932（Shift-JIS）                     |

-----

## ディレクトリ構成

```
kenshu-manage/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── upload.py
│   │   └── sessions.py
│   ├── constants.py           # 定数定義
│   ├── database.py            # SQLite3接続設定
│   ├── migrate.py             # JSONからSQLiteへのデータ移行スクリプト
│   ├── data/                  # SQLite3 DBファイル（kenshu.db）自動生成（Git管理外）
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── index.css
    │   ├── types/index.ts
    │   └── components/
    │       ├── TabBar.tsx
    │       ├── DataTable.tsx
    │       ├── FilterBar.tsx
    │       └── CommentModal.tsx
    ├── index.html
    ├── vite.config.ts
    └── package.json
```

-----

## セットアップ

### 前提

- Python 3.11 以上
- Node.js 20 LTS 以上（フロントのビルドに必要）

### バックエンド

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### フロントエンド（開発用）

```bash
cd frontend
npm install
npm run dev
```

ブラウザで `http://localhost:5173` を開く。

-----

## 本番デプロイ（社内サーバー向け）

フロントをビルドし、FastAPIに静的ファイルとして配信させます。サーバー側にNode.jsは不要です。

```bash
# ビルド（Node.jsがある開発PCで実行）
cd frontend
npm run build
# frontend/dist/ が生成される
```

`frontend/dist/` と `backend/` をまとめてサーバーに配置し、以下で起動します。

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

`backend/main.py` でdistフォルダを静的ファイルとしてマウントしているため、ブラウザから `http://サーバーIP:8000` でアクセスできます。

-----

## 運用フロー

月末の2回チェックを想定した運用手順です。

```
1回目（月末5日前）
  担当者がシステムからCSVをエクスポート
    → ブラウザでアップロード
    → 今月納期・未検収案件にコメント入力

2回目（月末2日前）
  担当者が再度CSVをエクスポート
    → ブラウザでアップロード
    → 前回コメントが自動引き継ぎ
    → 検収済み（CSVから消えた案件）は自動非表示
    → 新規発生案件はコメントなしで追加表示
```

-----

## データ保存形式

`backend/data/kenshu.db` にSQLite形式で保存されます。

主なテーブル構造：
- **`sessions`:**
  - `id` (主キー: セッションID、例 `20260426_143022`)
  - `month` (月、例 `2026-04`)
  - `uploaded_at` (アップロード日時)
  - `round` (その月の何回目のアップロードか)
- **`records`:**
  - `id` (主キー)
  - `session_id` (外部キー: `sessions.id`)
  - `management_number` (管理ナンバー)
  - `comment` (担当者のコメント)
  - `checked` (真偽値: コメントありか否か)
  - `updated_at` (コメント更新日時)
  - `data` (JSON形式。管理ナンバー以外のCSV列データを格納)

WAL（Write-Ahead Logging）モードやロックタイムアウトを利用しており、多人数（50人規模）による同時コメント保存のロストアップデートを安全に防止しています。

-----

## 列名のカスタマイズ

CSVの列名が変わった場合、以下の1行ずつを変更してください。

|変更箇所                               |対象キー                                  |
|-----------------------------------|--------------------------------------|
|`backend/constants.py` の定数  |`COL_MANAGEMENT_NUMBER`（管理ナンバー）、`COL_DELIVERY_DATE`（納期）|
|`frontend/src/types/index.ts` の先頭定数|`KEY_COLUMN`、`DATE_COLUMN`            |

-----

## ライセンス

社内利用を目的として開発されたツールです。
