# mcp

櫂谷家の自作 MCP（Model Context Protocol）サーバ群。

## サーバ一覧

| パッケージ     | 説明                                                     | リンク                             |
| -------------- | -------------------------------------------------------- | ---------------------------------- |
| `soycms-eleve` | SOY CMS (eleve-organic.jp) を read + draft-write するMCP | [README](./soycms-eleve/README.md) |

各パッケージの使い方・認証設定は個別のREADMEを参照。

## 設計方針

- **モノレポ**: 1リポジトリに複数MCPを並べる。`<package>/pyproject.toml` で個別パッケージ化
- **`uvx` 直接実行前提**: `uvx --from git+...#subdirectory=<package>` で clone不要起動
- **秘密情報を持たない**: APIキーは利用側の環境変数 / Keychain / Codespace Secrets から取得
- **Public OK**: コードに秘密情報がないので Public リポジトリで運用可

## 新しいMCPを追加するとき

```
mcp/
├── README.md
└── <new-mcp>/
    ├── pyproject.toml
    ├── README.md
    ├── src/<package_name>/
    └── tests/
```

`pyproject.toml` の `[project.scripts]` に CLI エントリを定義し、`uvx --from git+...#subdirectory=<new-mcp> <command>` で起動できるようにする。
