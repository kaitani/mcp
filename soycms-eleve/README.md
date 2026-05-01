# soycms-eleve MCP

Claude Code から SOY CMS (eleve-organic.jp) を read + draft-write するMCPサーバ。

## 提供ツール

| Tool                               | データソース                                     | 認証 |
| ---------------------------------- | ------------------------------------------------ | ---- |
| `soy_list_blog_entries`            | `output_blog_entries_json` プラグイン (公開JSON) | 不要 |
| `soy_get_entry_by_alias`           | Bridge API（フォールバック: 公開JSON）           | 推奨 |
| `soy_compare_markdown_with_soycms` | 公開JSON                                         | 不要 |
| `soy_create_draft`                 | Bridge API                                       | 必須 |

## 使い方（推奨: `uvx` で git 直接実行）

cloneせず、Mac / GitHub Codespace どちらからでも同じ設定で動きます。

`.mcp.json`（プロジェクト直下）または `~/.claude.json`：

```json
{
  "mcpServers": {
    "soycms-eleve": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kaitani/mcp.git#subdirectory=soycms-eleve",
        "soycms-mcp"
      ],
      "env": {
        "SOYCMS_BASE_URL": "https://eleve-organic.jp",
        "SOYCMS_BLOG_PAGE_ID": "5",
        "SOYCMS_TIMEOUT": "10"
      }
    }
  }
}
```

`uv` 未インストールなら：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Claude Code 再起動 → `/mcp` で `soycms-eleve` が **connected** になればOK。

## 認証（`soy_create_draft` を使う場合のみ必要）

`auth.py` は以下の順で API キーを探します：

1. 環境変数 `SOYCMS_BRIDGE_API_KEY`（最優先）
2. macOS Keychain（service: `soycms-eleve-bridge`, account: `$USER`）

### Mac（Keychain）

```bash
security add-generic-password -s soycms-eleve-bridge -a "$USER" -w '<key_id>.<secret>'
```

### GitHub Codespaces

リポジトリ Settings → Codespaces → Codespaces secrets に登録：

- Name: `SOYCMS_BRIDGE_API_KEY`
- Value: `<key_id>.<secret>`
- Repository access: Codespace を起動するリポジトリを選択

Codespace 再起動で環境変数として自動注入されます。

### キー発行元

Bridge plugin の管理画面（eleve-organic.jp 側）で発行。

## ローカル開発

```bash
git clone https://github.com/kaitani/mcp.git
cd mcp/soycms-eleve
uv venv
source .venv/bin/activate
uv pip install -e .
uv run pytest
```

## 動作確認

```bash
# 公開JSON経由（認証不要）
SOYCMS_BLOG_PAGE_ID=5 uv run python -c "
from soycms_mcp.client import SoyCmsClient
with SoyCmsClient() as c:
    r = c.read_public_entries(limit=5)
    print(r.get('total'), len(r.get('entries', [])))
"

# Bridge版（要認証）
uv run python -c "
from soycms_mcp.client import SoyCmsClient
with SoyCmsClient() as c:
    r = c.bridge_get('/version')
    print(r)
"
```

## 環境変数

| Var                     | デフォルト                 | 用途                                      |
| ----------------------- | -------------------------- | ----------------------------------------- |
| `SOYCMS_BASE_URL`       | `https://eleve-organic.jp` | サイトのドメイン                          |
| `SOYCMS_BLOG_PAGE_ID`   | `5`                        | output_blog_entries_json のブログページID |
| `SOYCMS_TIMEOUT`        | `10`                       | HTTP タイムアウト秒                       |
| `SOYCMS_BRIDGE_API_KEY` | -                          | Keychain未使用時のfallback／Codespace用   |

## 設計上の制約（厳守）

- このMCPサーバは記事の**ステータスを進めない**（`status: ready` 等の変更はGitHub frontmatterで人間が編集）
- `soy_create_draft` は **下書きのみ**作成。**公開・削除はBridge側で永久禁止**
- 公開ボタンは管理画面で人間（櫂谷）が押す

## 関連

- Bridge plugin (Xserver側): `kaitani/cc-company` リポジトリ `060-systems/eleve-content-lab/eleve-bridge-plugin/`
- 設計書: `kaitani/cc-company` リポジトリ `060-systems/eleve-content-lab/docs/soycms-mcp-design.md`
- Issue: cc-company #94, #95
