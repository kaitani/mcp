"""SoyShop MCP server スモークテスト。

実環境 (komodaru-ya.com) に対する疎通確認用。Keychain 'soyshop-bridge-komodaru' に
有効なAPIキーが入っている前提。CIでは skip される（Keychain無し環境）。
"""

from __future__ import annotations

import os
import sys

import pytest

# uvx 実行時 packageディレクトリ
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from soyshop_mcp.client import SoyShopClient
from soyshop_mcp.tools import version, search_items, list_categories


@pytest.fixture
def client():
    c = SoyShopClient()
    if not c.credentials:
        pytest.skip("Bridge credentials not available (Keychain entry missing)")
    yield c
    c.close()


def test_version(client):
    result = version.execute(client, {})
    assert "version" in result
    assert "soyshop" in result
    assert "soyshop_id" in result


def test_search_items_default(client):
    result = search_items.execute(client, {"limit": 3})
    assert "items" in result
    assert "total" in result
    assert isinstance(result["items"], list)


def test_list_categories(client):
    result = list_categories.execute(client, {})
    assert "items" in result
    assert isinstance(result["items"], list)
