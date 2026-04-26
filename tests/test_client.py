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
