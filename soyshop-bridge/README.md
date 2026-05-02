# soyshop-mcp

> MCP server for SoyShop catalog operations via the **soyshop_bridge** plugin.
> Reads, draft creates, updates, and toggles publish/unpublish for SoyShop items.
> **Does not** touch carts, orders, payments, stock, prices, or item deletion (those live in Easy My Shop).

This is a sibling of `soycms-eleve` MCP. Same authentication scheme (HMAC-SHA256), same Keychain-based credential loading, just for SoyShop instead of SOY CMS.

---

## Architecture

```
Claude Code  ──stdio──>  soyshop-mcp (this package)
                              │
                              │ HMAC-SHA256 auth
                              ▼
                  https://komodaru-ya.com/soyshop_bridge/...
                              │
                              ▼
                  SoyShop  ──ItemLogic──>  MySQL (item master)
                  └── (Easy My Shop は SoyShop の item_code で外部紐付け)
```

---

## Installation

### From local clone (during development)

```bash
cd ~/work/mcp/soyshop-bridge
uv sync
uv run soyshop-mcp  # stdio mode, will block waiting for MCP client
```

### From git (production)

```bash
uvx --from git+https://github.com/kaitani/mcp.git#subdirectory=soyshop-bridge soyshop-mcp
```

---

## Credentials

Keychain サービス名（macOS）:

- デフォルト: `soyshop-bridge-komodaru`
- 切替: 環境変数 `SOYSHOP_BRIDGE_KEYCHAIN_SERVICE`

```bash
# komodaru-ya.com 用キーを保存
security add-generic-password -s soyshop-bridge-komodaru -a "$USER" -w '<key_id>.<secret>'

# 別サイト用キー（例: IT'S ESHOP リニューアル後）
security add-generic-password -s soyshop-bridge-its-eshop -a "$USER" -w '<key_id>.<secret>'
```

フォールバック: 環境変数 `SOYSHOP_BRIDGE_API_KEY`

---

## MCP 登録例（`.mcp.json`）

```json
{
  "mcpServers": {
    "soyshop-komodaru": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kaitani/mcp.git#subdirectory=soyshop-bridge",
        "soyshop-mcp"
      ],
      "env": {
        "SOYSHOP_BRIDGE_BASE_URL": "https://komodaru-ya.com",
        "SOYSHOP_BRIDGE_KEYCHAIN_SERVICE": "soyshop-bridge-komodaru"
      }
    }
  }
}
```

複数SoyShopサイトを並行運用する場合は `mcpServers` に `soyshop-its-eshop` 等を追加し、`base_url` と `keychain_service` を切替えれば1MCPサーバ実装で複数サイト対応できる。

---

## Tools

| Tool                        | 用途                                                                        |
| --------------------------- | --------------------------------------------------------------------------- |
| `soyshop_version`           | Bridge疎通確認（バージョン・サイトID取得）                                  |
| `soyshop_search_items`      | 商品検索（q / code / open でフィルタ、ページング）                          |
| `soyshop_get_item`          | 商品詳細（id か code で取得）                                               |
| `soyshop_create_draft_item` | 新規商品 draft 作成（**is_open=0 強制**、価格・在庫は触らない）             |
| `soyshop_update_item`       | 商品更新（限定フィールド: name/code/subtitle/alias/description/categories） |
| `soyshop_change_open`       | 公開非公開一括切替（最大500件、ids/codesどちらでも指定可）                  |
| `soyshop_list_categories`   | カテゴリ一覧（read-only）                                                   |

### 永久禁止（実装無し）

- 商品削除（is_disabled の操作）
- 価格・在庫・購入価格・割引フィールドの書き込み
- 受注・カート・決済関連
- ユーザー（顧客）情報の操作
- 任意SQL・テンプレート操作・キャッシュクリア

---

## 想定使用例

### 売り切れ連動

```
Claude: Easy My Shop で売り切れた SKU 一覧を取得 → soyshop_change_open でSoyShopも一括非公開
```

### CSV移行（IT'S ESHOPからのデータ移行時）

```
Claude: CSV1行ずつ → soyshop_create_draft_item({code, name, description, categories})
日次create上限はBridge設定画面でキー単位に上書き可能（デフォルト200/day）
```

### 商品説明の一括更新

```
Claude: 「自然食品で〇〇産タグの商品の説明文に注意書きを追加」
→ soyshop_search_items → soyshop_update_item by-code でループ
```

---

## Sibling project

- `soycms-eleve/`: 同じパターンでSOY CMS（記事ブログ）向け
- 共通設計: `eleve-content-lab/eleve-bridge-plugin/` の認証・Rate Limit・Audit Log を踏襲

---

## Development

```bash
uv sync
uv run pytest               # スモークテスト（Keychain無し環境ではskip）
uv run soyshop-mcp           # stdio で起動（Ctrl+C で停止）
```
