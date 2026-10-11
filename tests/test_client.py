import base64

import httpx
import pytest

from mochi_mcp.client import MochiClient, MochiClientException
from mochi_mcp.models import Card, Deck


class MockTransport(httpx.BaseTransport):
    def __init__(self, responses: list[dict]) -> None:
        self._responses = responses
        self._index = 0
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        data = self._responses[self._index]
        self._index += 1
        return httpx.Response(
            data.get("status_code", 200),
            json=data.get("json"),
            request=request,
        )


def make_client(responses: list[dict]) -> tuple[MochiClient, MockTransport]:
    transport = MockTransport(responses)
    client = MochiClient(api_key="test-key", transport=transport)
    return client, transport


def test_get_deck_returns_deck():
    client, _ = make_client([{"json": {"id": "deck-1", "name": "Spanish"}}])
    assert client.get_deck("deck-1") == Deck(id="deck-1", name="Spanish")


def test_get_card_returns_card():
    card = {"id": "card-1", "content": "hola", "deck-id": "deck-1"}
    client, _ = make_client([{"json": card}])
    assert client.get_card("card-1") == Card(
        id="card-1", content="hola", deck_id="deck-1"
    )


def test_auth_header_uses_api_key_as_basic_username():
    client, transport = make_client([{"json": {"id": "d1", "name": "Test"}}])
    client.get_deck("d1")
    auth = transport.requests[0].headers.get("authorization", "")
    expected = "Basic " + base64.b64encode(b"test-key:").decode()
    assert auth == expected


def test_list_decks_returns_all_decks_single_page():
    decks = [{"id": "d1", "name": "Spanish"}, {"id": "d2", "name": "French"}]
    client, _ = make_client([{"json": {"docs": decks}}])
    assert client.list_decks() == [
        Deck(id="d1", name="Spanish"),
        Deck(id="d2", name="French"),
    ]


def test_list_decks_paginates_through_all_pages():
    client, _ = make_client(
        [
            {"json": {"docs": [{"id": "d1", "name": "A"}], "bookmark": "cursor1"}},
            {"json": {"docs": [{"id": "d2", "name": "B"}], "bookmark": "cursor2"}},
            {"json": {"docs": [{"id": "d3", "name": "C"}]}},
        ]
    )
    assert [d.id for d in client.list_decks()] == ["d1", "d2", "d3"]


def test_list_cards_returns_all_cards():
    cards = [{"id": "c1", "content": "hola", "deck-id": "d1"}]
    client, _ = make_client([{"json": {"docs": cards}}])
    assert client.list_cards() == [Card(id="c1", content="hola", deck_id="d1")]


def test_list_cards_passes_deck_id_filter():
    client, transport = make_client([{"json": {"docs": []}}])
    client.list_cards(deck_id="deck-1")
    assert transport.requests[0].url.params.get("deck-id") == "deck-1"


CARD_C1 = {"id": "c1", "content": "uno", "deck-id": "deck-1"}
CARD_C2 = {"id": "c2", "content": "dos", "deck-id": "deck-1"}


def test_list_cards_paginates_with_deck_filter_preserved():
    client, transport = make_client(
        [
            {"json": {"docs": [CARD_C1], "bookmark": "cursor1"}},
            {"json": {"docs": [CARD_C2]}},
        ]
    )
    result = client.list_cards(deck_id="deck-1")
    assert [c.id for c in result] == ["c1", "c2"]
    assert transport.requests[1].url.params.get("deck-id") == "deck-1"
    assert transport.requests[1].url.params.get("bookmark") == "cursor1"


def test_http_error_raises_readable_exception():
    client, _ = make_client([{"status_code": 401, "json": {"error": "Unauthorized"}}])
    with pytest.raises(Exception, match="Mochi API returned 401"):
        client.get_deck("d1")


ARCHIVE_DECKS = [
    {"id": "d1", "name": "Active"},
    {"id": "d2", "name": "Explicitly active", "archived?": False},
    {"id": "d3", "name": "Archived", "archived?": True},
]


def test_list_decks_excludes_archived_by_default():
    client, _ = make_client([{"json": {"docs": ARCHIVE_DECKS}}])
    assert [d.id for d in client.list_decks()] == ["d1", "d2"]


def test_list_decks_can_include_archived():
    client, _ = make_client([{"json": {"docs": ARCHIVE_DECKS}}])
    assert [d.id for d in client.list_decks(include_archived=True)] == [
        "d1",
        "d2",
        "d3",
    ]


def test_get_top_level_decks_excludes_nested_decks():
    decks = [
        {"id": "d1", "name": "Languages"},
        {"id": "d2", "name": "Spanish", "parent-id": "d1"},
    ]
    client, _ = make_client([{"json": {"docs": decks}}])
    assert [d.id for d in client.get_top_level_decks()] == ["d1"]


def test_malformed_response_raises_client_exception():
    client, _ = make_client([{"json": {"name": "no id"}}])
    with pytest.raises(MochiClientException, match="Unexpected response"):
        client.get_deck("d1")
