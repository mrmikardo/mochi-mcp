import asyncio
from unittest.mock import MagicMock

from fastmcp import Client, FastMCP

from mochi_mcp.client import MochiClient
from mochi_mcp.models import Card, Deck
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
    client.list_decks.return_value = [Deck(id="d1", name="Spanish")]
    register_tools(mcp, client)
    result = mcp.tools["list_decks"]()
    assert result == [Deck(id="d1", name="Spanish")]
    client.list_decks.assert_called_once()


def test_get_deck_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.get_deck.return_value = Deck(id="d1", name="Spanish")
    register_tools(mcp, client)
    result = mcp.tools["get_deck"](deck_id="d1")
    assert result == Deck(id="d1", name="Spanish")
    client.get_deck.assert_called_once_with("d1")


def test_list_cards_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.list_cards.return_value = [Card(id="c1", content="hola", deck_id="d1")]
    register_tools(mcp, client)
    result = mcp.tools["list_cards"](deck_id="d1")
    assert result == [Card(id="c1", content="hola", deck_id="d1")]
    client.list_cards.assert_called_once_with(deck_id="d1")


def test_get_card_tool_delegates_to_client():
    mcp = CaptureMCP()
    client = MagicMock(spec=MochiClient)
    client.get_card.return_value = Card(id="c1", content="hola", deck_id="d1")
    register_tools(mcp, client)
    result = mcp.tools["get_card"](card_id="c1")
    assert result == Card(id="c1", content="hola", deck_id="d1")
    client.get_card.assert_called_once_with("c1")


def test_tools_return_api_keys_to_mcp_clients():
    mcp = FastMCP("test")
    client = MagicMock(spec=MochiClient)
    client.get_deck.return_value = Deck.model_validate(
        {"id": "d1", "name": "Spanish", "archived?": True, "parent-id": "d0"}
    )
    register_tools(mcp, client)

    async def call():
        async with Client(mcp) as mcp_client:
            return await mcp_client.call_tool("get_deck", {"deck_id": "d1"})

    result = asyncio.run(call())
    assert result.structured_content["archived?"] is True
    assert result.structured_content["parent-id"] == "d0"
