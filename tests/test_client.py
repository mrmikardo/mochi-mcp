import base64
import httpx
import pytest
from mochi_mcp.client import MochiClient


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
    deck = {"id": "deck-1", "name": "Spanish"}
    client, _ = make_client([{"json": deck}])
    assert client.get_deck("deck-1") == deck


def test_get_card_returns_card():
    card = {"id": "card-1", "content": "hola", "deck-id": "deck-1"}
    client, _ = make_client([{"json": card}])
    assert client.get_card("card-1") == card


def test_auth_header_uses_api_key_as_basic_username():
    client, transport = make_client([{"json": {"id": "d1", "name": "Test"}}])
    client.get_deck("d1")
    auth = transport.requests[0].headers.get("authorization", "")
    expected = "Basic " + base64.b64encode(b"test-key:").decode()
    assert auth == expected


def test_list_decks_returns_all_decks_single_page():
    decks = [{"id": "d1", "name": "Spanish"}, {"id": "d2", "name": "French"}]
    client, _ = make_client([{"json": {"docs": decks}}])
    assert client.list_decks() == decks


def test_list_decks_paginates_through_all_pages():
    client, _ = make_client(
        [
            {"json": {"docs": [{"id": "d1"}], "bookmark": "cursor1"}},
            {"json": {"docs": [{"id": "d2"}], "bookmark": "cursor2"}},
            {"json": {"docs": [{"id": "d3"}]}},
        ]
    )
    assert client.list_decks() == [{"id": "d1"}, {"id": "d2"}, {"id": "d3"}]


def test_list_cards_returns_all_cards():
    cards = [{"id": "c1", "content": "hola"}]
    client, _ = make_client([{"json": {"docs": cards}}])
    assert client.list_cards() == cards


def test_list_cards_passes_deck_id_filter():
    client, transport = make_client([{"json": {"docs": []}}])
    client.list_cards(deck_id="deck-1")
    assert transport.requests[0].url.params.get("deck-id") == "deck-1"


def test_list_cards_paginates_with_deck_filter_preserved():
    client, transport = make_client(
        [
            {"json": {"docs": [{"id": "c1"}], "bookmark": "cursor1"}},
            {"json": {"docs": [{"id": "c2"}]}},
        ]
    )
    result = client.list_cards(deck_id="deck-1")
    assert result == [{"id": "c1"}, {"id": "c2"}]
    assert transport.requests[1].url.params.get("deck-id") == "deck-1"
    assert transport.requests[1].url.params.get("bookmark") == "cursor1"


def test_http_error_raises_readable_exception():
    client, _ = make_client([{"status_code": 401, "json": {"error": "Unauthorized"}}])
    with pytest.raises(Exception, match="Mochi API returned 401"):
        client.get_deck("d1")
