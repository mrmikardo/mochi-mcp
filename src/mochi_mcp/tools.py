from fastmcp import FastMCP

from mochi_mcp.client import MochiClient
from mochi_mcp.models import Card, Deck


def register_tools(mcp: FastMCP, client: MochiClient) -> None:
    @mcp.tool
    def list_decks(include_archived: bool = False) -> list[Deck]:
        """
        List all Mochi decks.
        """
        return client.list_decks(include_archived=include_archived)

    @mcp.tool
    def get_deck(deck_id: str) -> Deck:
        """
        Get a single Mochi deck by ID.
        """
        return client.get_deck(deck_id)

    @mcp.tool
    def list_cards(deck_id: str | None = None) -> list[Card]:
        """
        List all Mochi cards, optionally filtered by deck ID.
        """
        return client.list_cards(deck_id=deck_id)

    @mcp.tool
    def get_card(card_id: str) -> Card:
        """
        Get a single Mochi card by ID.
        """
        return client.get_card(card_id)
