import httpx

BASE_URL = "https://app.mochi.cards/api/"


class MochiClient:
    def __init__(self, api_key: str, transport: httpx.BaseTransport | None = None) -> None:
        self._http = httpx.Client(
            base_url=BASE_URL,
            auth=(api_key, ""),
            transport=transport,
        )

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            response = self._http.get(path, params=params or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Mochi API returned {e.response.status_code}: {e.response.text}"
            ) from e

    def get_deck(self, deck_id: str) -> dict:
        return self._get(f"decks/{deck_id}")

    def get_card(self, card_id: str) -> dict:
        return self._get(f"cards/{card_id}")

    def list_decks(self) -> list[dict]:
        raise NotImplementedError

    def list_cards(self, deck_id: str | None = None) -> list[dict]:
        raise NotImplementedError
