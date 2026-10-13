from dataclasses import dataclass, field
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from mochi_mcp.models import Card, Deck, Page

BASE_URL = "https://app.mochi.cards/api/"

M = TypeVar("M", bound=BaseModel)


class MochiClientException(Exception):
    pass


@dataclass
class DeckNode:
    id: str
    children: list["DeckNode"] = field(default_factory=list)


class MochiClient:
    _deck_tree: DeckNode | None

    def __init__(
        self, api_key: str, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._http = httpx.Client(
            base_url=BASE_URL,
            auth=(api_key, ""),
            transport=transport,
        )
        self._deck_tree = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._http.close()

    def _build_deck_tree(self, decks: list[Deck]) -> None:
        """
        TODO.
        """

        def build(node_id: str) -> DeckNode:
            parent_id = None if node_id == "ROOT" else node_id
            node = DeckNode(node_id)
            for inp in decks:
                if inp.parent_id == parent_id:
                    node.children.append(build(inp.id))
            return node

        self._deck_tree = build("ROOT")

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            response = self._http.get(path, params=params or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise MochiClientException(
                f"Mochi API returned {e.response.status_code}: {e.response.text}"
            ) from e

    def _get_model(self, path: str, model: type[M], params: dict | None = None) -> M:
        data = self._get(path, params=params)
        try:
            return model.model_validate(data)
        except ValidationError as e:
            raise MochiClientException(
                f"Unexpected response from Mochi API for {path}: {e}"
            ) from e

    def _paginate(
        self, path: str, model: type[M], params: dict | None = None
    ) -> list[M]:
        results: list[M] = []
        params = dict(params or {})
        while True:
            page = self._get_model(path, Page[model], params=params)
            results.extend(page.docs)
            if not page.docs or not page.bookmark:
                break
            params["bookmark"] = page.bookmark
        return results

    def get_deck(self, deck_id: str) -> Deck:
        """
        Get a single deck by ID.
        """
        return self._get_model(f"decks/{deck_id}", Deck)

    def get_card(self, card_id: str) -> Card:
        """
        Get a single card by ID.
        """
        return self._get_model(f"cards/{card_id}", Card)

    def list_decks(self, *, include_archived: bool = False) -> list[Deck]:
        """
        List all of a user's decks.

        Args:
            include_archived: whether to include archived decks in the returned set.
        """
        decks = self._paginate("decks", Deck)

        # TODO: an issue with this approach is that it will get stale.
        # I think that's fine for now as the client doesn't expose any
        # mechanisms to update decks, so staleness would only creep in
        # if a user is editing their decks via the Mochi app in the
        # background: nevertheless, this requires some thought.
        if not self._deck_tree:
            self._build_deck_tree(decks)

        if not include_archived:
            return [deck for deck in decks if not deck.archived]
        return decks

    def get_top_level_decks(self) -> list[Deck]:
        """
        Return all the decks which sit at the top level of the user's Mochi library.
        """
        return [deck for deck in self.list_decks() if deck.parent_id is None]

    def list_cards(self, deck_id: str | None = None) -> list[Card]:
        """
        List all of a user's cards, optionally filtered by deck.
        """
        params = {"deck-id": deck_id} if deck_id else {}
        return self._paginate("cards", Card, params=params)
