from datetime import UTC, datetime

from mochi_mcp.models import Card, Deck, Page

# Example payloads taken from https://mochi.cards/docs/api/

DECK_JSON = {
    "sort-by-direction": True,
    "name": "My new deck",
    "show-sides?": True,
    "cards-view": "list",
    "id": "RMb5BZ67",
    "review-reverse?": True,
    "parent-id": "HJBMBGBO",
    "sort-by": "lexicographically",
    "archived?": True,
    "sort": 1,
    "card-count": 24,
}

CARD_JSON = {
    "updated-at": {"date": "2021-09-11T14:23:53.250Z"},
    "tags": [],
    "content": "New card from API.",
    "name": None,
    "deck-id": "btmZUXWM",
    "pos": "00F",
    "references": [],
    "id": "QQJ8ssvL",
    "reviews": [
        {
            "date": {"date": "2025-12-12T00:00:00.000Z"},
            "due": {"date": "2025-12-13T00:00:00.000Z"},
            "remembered?": True,
            "duration": 8,
        }
    ],
    "created-at": {"date": "2021-09-10T01:29:49.879Z"},
    "new?": False,
    "archived?": True,
    "template-id": None,
    "fields": {"name": {"id": "name", "value": "Hello,"}},
}


def test_deck_parses_kebab_case_and_question_mark_keys():
    deck = Deck.model_validate(DECK_JSON)
    assert deck.id == "RMb5BZ67"
    assert deck.parent_id == "HJBMBGBO"
    assert deck.archived is True
    assert deck.show_sides is True
    assert deck.review_reverse is True
    assert deck.sort_by == "lexicographically"
    assert deck.cards_view == "list"
    assert deck.card_count == 24


def test_deck_from_list_endpoint_has_sensible_defaults():
    deck = Deck.model_validate({"id": "HJBMBGBO", "sort": 6, "name": "New Deck"})
    assert deck.archived is False
    assert deck.parent_id is None
    assert deck.card_count is None


def test_card_unwraps_timestamps_into_datetimes():
    card = Card.model_validate(CARD_JSON)
    assert card.created_at == datetime(2021, 9, 10, 1, 29, 49, 879000, tzinfo=UTC)
    assert card.updated_at == datetime(2021, 9, 11, 14, 23, 53, 250000, tzinfo=UTC)


def test_card_parses_reviews_and_fields():
    card = Card.model_validate(CARD_JSON)
    assert card.deck_id == "btmZUXWM"
    assert card.archived is True
    assert card.new is False
    [review] = card.reviews
    assert review.remembered is True
    assert review.duration == 8
    assert review.due == datetime(2025, 12, 13, tzinfo=UTC)
    assert card.fields["name"].value == "Hello,"


def test_review_duration_is_optional():
    card = Card.model_validate(
        {
            **CARD_JSON,
            "reviews": [
                {
                    "date": {"date": "2025-12-12T00:00:00.000Z"},
                    "due": {"date": "2025-12-13T00:00:00.000Z"},
                    "remembered?": False,
                }
            ],
        }
    )
    assert card.reviews[0].duration is None


def test_card_field_value_can_be_null():
    # Seen from the live API for template fields left empty; not in the docs.
    card = Card.model_validate(
        {**CARD_JSON, "fields": {"name": {"id": "name", "value": None}}}
    )
    assert card.fields["name"].value is None


def test_unknown_keys_are_preserved():
    deck = Deck.model_validate({"id": "d1", "name": "Spanish", "new-api-field": 1})
    assert deck.model_dump(by_alias=True)["new-api-field"] == 1


def test_models_serialize_to_python_field_names():
    dumped = Deck.model_validate(DECK_JSON).model_dump(mode="json", exclude_none=True)
    assert dumped["archived"] is True
    assert dumped["parent_id"] == "HJBMBGBO"
    assert "archived?" not in dumped
    assert "parent-id" not in dumped


def test_page_parses_bookmark_and_docs():
    page = Page[Deck].model_validate(
        {"bookmark": "abc", "docs": [{"id": "d1", "name": "Spanish"}]}
    )
    assert page.bookmark == "abc"
    assert page.docs == [Deck(id="d1", name="Spanish")]


def test_page_bookmark_and_docs_are_optional():
    page = Page[Card].model_validate({})
    assert page.bookmark is None
    assert page.docs == []
