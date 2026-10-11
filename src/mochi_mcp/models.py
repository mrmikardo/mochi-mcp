"""
Pydantic models for values returned by the Mochi API.

See https://mochi.cards/docs/api/ for the upstream reference. Mochi uses
Clojure-style keys (kebab-case, with a trailing `?` on booleans), so every
such field declares an alias; models accept either the alias or the Python
field name, and serialize back to the API's keys.

The docs are incomplete in places, so unknown keys are kept rather than
rejected, and most fields are optional.
"""

from datetime import datetime
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _unwrap_date(value: Any) -> Any:
    # Mochi wraps timestamps as {"date": "2021-09-10T01:29:49.879Z"}.
    if isinstance(value, dict) and "date" in value:
        return value["date"]
    return value


MochiDateTime = Annotated[datetime, BeforeValidator(_unwrap_date)]

T = TypeVar("T")


class MochiModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )


class Deck(MochiModel):
    id: str
    name: str
    parent_id: str | None = Field(default=None, alias="parent-id")
    sort: int | None = None
    archived: bool = Field(default=False, alias="archived?")
    trashed: MochiDateTime | None = Field(default=None, alias="trashed?")
    sort_by: str | None = Field(default=None, alias="sort-by")
    sort_by_direction: bool | None = Field(default=None, alias="sort-by-direction")
    cards_view: str | None = Field(default=None, alias="cards-view")
    show_sides: bool | None = Field(default=None, alias="show-sides?")
    review_reverse: bool | None = Field(default=None, alias="review-reverse?")
    card_count: int | None = Field(
        default=None,
        alias="card-count",
        description="Only returned when fetching a single deck; excludes nested decks.",
    )


class Review(MochiModel):
    date: MochiDateTime
    due: MochiDateTime
    remembered: bool = Field(alias="remembered?")
    duration: int | None = Field(
        default=None,
        description="Seconds spent on the review; missing on older reviews.",
    )


class CardField(MochiModel):
    id: str
    value: str


class Card(MochiModel):
    id: str
    content: str
    deck_id: str = Field(alias="deck-id")
    name: str | None = None
    template_id: str | None = Field(default=None, alias="template-id")
    pos: str | None = None
    tags: list[str] = Field(default_factory=list)
    fields: dict[str, CardField] = Field(default_factory=dict)
    references: list[Any] = Field(default_factory=list)
    reviews: list[Review] = Field(default_factory=list)
    archived: bool = Field(default=False, alias="archived?")
    new: bool | None = Field(default=None, alias="new?")
    created_at: MochiDateTime | None = Field(default=None, alias="created-at")
    updated_at: MochiDateTime | None = Field(default=None, alias="updated-at")


class Page(MochiModel, Generic[T]):
    """One page of a paginated list response."""

    bookmark: str | None = None
    docs: list[T] = Field(default_factory=list)
