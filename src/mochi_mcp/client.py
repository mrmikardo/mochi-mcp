import httpx

BASE_URL = "https://app.mochi.cards/api/"


class MochiClient:
    def __init__(self, api_key: str, transport: httpx.BaseTransport | None = None) -> None:
        self._http = httpx.Client(
            base_url=BASE_URL,
            auth=(api_key, ""),
            transport=transport,
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._http.close()

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
        results: list[dict] = []
        params: dict = {}
        while True:
            data = self._get("decks", params=params)
            docs = data.get("docs", [])
            results.extend(docs)
            bookmark = data.get("bookmark")
            if not docs or not bookmark:
                break
            params = {"bookmark": bookmark}
        return results

    def list_cards(self, deck_id: str | None = None) -> list[dict]:
        results: list[dict] = []
        params: dict = {}
        if deck_id:
            params["deck-id"] = deck_id
        while True:
            data = self._get("cards", params=params)
            docs = data.get("docs", [])
            results.extend(docs)
            bookmark = data.get("bookmark")
            if not docs or not bookmark:
                break
            params = {**params, "bookmark": bookmark}
        return results
