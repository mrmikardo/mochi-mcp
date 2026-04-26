from unittest.mock import MagicMock
from mochi_mcp.client import MochiClient
from mochi_mcp.tools import register_tools


class CaptureMCP:
    """Fake FastMCP that records registered tools instead of registering them."""

    def __init__(self) -> None:
        self.tools: dict = {}

    def tool(self, fn):
        self.tools[fn.__name__] = fn
        return fn


def test_register_tools_registers_four_tools():
    mcp = CaptureMCP()
    register_tools(mcp, MagicMock(spec=MochiClient))
    assert set(mcp.tools.keys()) == {"list_decks", "get_deck", "list_cards", "get_card"}


def test_list_decks_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.list_decks.return_value = [{"id": "d1", "name": "Spanish"}]
    register_tools(mcp, client)
    result = mcp.tools["list_decks"]()
    assert result == [{"id": "d1", "name": "Spanish"}]
    client.list_decks.assert_called_once()


def test_get_deck_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.get_deck.return_value = {"id": "d1", "name": "Spanish"}
    register_tools(mcp, client)
    result = mcp.tools["get_deck"](deck_id="d1")
    assert result == {"id": "d1", "name": "Spanish"}
    client.get_deck.assert_called_once_with("d1")


def test_list_cards_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.list_cards.return_value = [{"id": "c1"}]
    register_tools(mcp, client)
    result = mcp.tools["list_cards"](deck_id="d1")
    assert result == [{"id": "c1"}]
    client.list_cards.assert_called_once_with(deck_id="d1")


def test_get_card_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.get_card.return_value = {"id": "c1", "content": "hola"}
    register_tools(mcp, client)
    result = mcp.tools["get_card"](card_id="c1")
    assert result == {"id": "c1", "content": "hola"}
    client.get_card.assert_called_once_with("c1")
