---
name: mochi-drill
description: Run an interactive flashcard drill over the user's Mochi decks via the Mochi MCP, showing each card's face either verbatim or reworded, then grading the user's typed answers. Use this whenever the user wants to drill, quiz, test or revise their Mochi cards or decks, practise a specific deck ("drill my Italian vocab", "test me on the Codebase facts deck", "quiz me on my poems"), or asks Claude to reword their flashcards so they can't just pattern-match, even if they don't say "drill" or "Mochi" explicitly but refer to their flashcards or spaced-repetition decks.
compatibility: Requires the Mochi MCP (list_decks, list_cards, get_card; get_deck optional). On surfaces where tools are deferred, load them with tool_search first.
---

# Mochi drill

Drill the user on cards from one of their Mochi decks, one card at a time. The user types an answer, you grade it against the back of the card, and you finish with a summary.

The Mochi MCP is **read-only**: it can list and read cards but cannot record reviews. A drill here does not update the user's Mochi schedule. Never say or imply that it does. The end-of-session summary exists so the user can act on the results in Mochi themselves.

## Workflow

### 1. Find the deck

1. Call `list_decks`. Build the deck tree from `parent-id` so you can show each deck's full path (e.g. `CS › Tools › Git`).
2. Ignore decks with a `trashed?` key. Keep archived decks (`archived?: true`), because users still drill those deliberately, but label them "(archived)".
3. Match the user's description to a deck by name, case-insensitively and allowing for loose wording.
   - **One clear match:** confirm it in passing ("Drilling **Italian › Vocabulary**.") and move on.
   - **Several matches:** show the candidates with their full paths and ask which one. Real decks often reuse names such as "Grammar", "Vocabulary" or "Consumer app".
   - **No match, or no deck named:** show the top-level decks, plus children of any deck the user seems to mean, and ask.

### 2. Set up the session

Ask the setup questions together in one go, using a tappable-options tool if one is available and plain text otherwise. Skip any question that doesn't apply.

1. **Sub-decks.** Ask only if the chosen deck has child decks: "Include its sub-decks?" (Yes / No).
2. **Which cards:**
   - due or overdue cards
   - weakest cards (most lapses)
   - new cards (never reviewed)
   - all cards, shuffled

   Also ask how many, defaulting to 20.
3. **Reword faces?** Yes / No. If YES, you present each card's face with the same meaning but different wording. If NO, you present it exactly as written.

For sequence decks (see "Card types" below), skip question 3. Tell the user that rewording is off for that deck because the exact wording is what's being learnt.

### 3. Fetch and prepare the cards

1. Call `list_cards` with each `deck_id` in scope (the chosen deck, plus its descendants if included).
2. **Large decks:** if a result is too large and gets saved to a file, parse that file with a short script rather than reading it into context. The file is a JSON list whose first item's `text` is the JSON array of cards. If even a single deck is too large to fetch, tell the user and suggest a sub-deck.
3. **Drop these cards:**
   - cards with `trashed?` or `archived?`
   - cards with empty `content`

   If `template-id` is set and `content` is empty, the card's text may live in template fields. Try `get_card`, and skip the card if it's still empty.
4. **Split each card** into face and back on the first line that is exactly `---`. Ignore any further `---` separators.
5. **Derive review stats** from `reviews`:
   - due date: the last review's `due.date`
   - lapses: the count of reviews with `remembered?: false`
   - never reviewed: `new?: true` or no reviews
6. **Select cards:**
   - due/overdue: due ≤ today, most overdue first
   - weakest: sort by lapses, highest first
   - new: never reviewed
   - all: shuffle

   Then trim to the requested number. If fewer cards qualify than were asked for, say so and drill what there is.
7. **Duplicate pairs.** Some users keep the same question as both a `[cloze]` card and a `[test]` card. If both of a pair are selected, drill only one of them.

### 4. Drill loop

Present **one card per message** and then stop and wait. Never show the next card, or the answer, before the user has replied.

Format each card like this:

```
**Card 3 of 20** · Italian › Vocabulary

<face, reworded or verbatim>
```

When the user replies, grade the answer:

- **✅ Correct**: the key facts all match.
- **🟡 Partly right**: some key facts are present but some are missing or wrong. Name which ones.
- **❌ Not quite**: the answer is wrong, or the user said they don't know.

Then show the back of the card exactly as written as the reference answer, followed by at most one or two sentences on why the answer was or wasn't right. If the face was reworded, also show the card's original face in a single line under the grading, so the user sees the card as it actually appears in Mochi. End by presenting the next card in the same message, so the session flows.

#### Grading principles

- Judge meaning, not wording. A paraphrase that captures the facts is correct.
- Be strict about anything that has to be exact:
  - identifiers, function, class and module names, and fully-qualified paths (`a.b.c` vs `a.b` matters)
  - numbers, dates and counts
  - spellings of foreign-language vocabulary
  - the exact next line in a sequence deck
- Small typos in a long identifier are "Partly right" at most. Name the typo.
- For list answers, count how many items the user got and grade proportionally. Order matters only if the card implies it.
- Don't be swayed by confident phrasing, and don't argue. If the user disputes a grade, note their reasoning and move on.

#### In-session commands

Mention these once, at the start of the first card. Accept them in natural phrasing.

- **hint**: give a nudge that narrows the answer without revealing it, such as a first letter, the category or the number of items.
- **skip**: show the answer and count the card as skipped, not wrong.
- **original**: show the verbatim face of the current card without revealing the answer.
- **stop**: end the session and go straight to the summary.

### 5. Summary

When the cards run out or the user stops, give:

- the score: correct, partly right, wrong and skipped
- the cards that were partly right, wrong or skipped, each as `<card name> (id <card id>) · <deck path>`, so the user can find them in Mochi
- a reminder, in one line, that results weren't saved to Mochi
- an offer to re-drill just the missed cards straight away

## Rewording faces

The aim of rewording is to make the user retrieve the fact, not recognise the card. A good rewording asks for exactly the same answer, at the same difficulty, in different words.

**Rules:**

- **Keep the meaning and the answer identical.** If someone could correctly answer the reworded face with something other than the card's back, the rewording has drifted.
- **Change the wording substantively.** Use a different sentence structure, different verbs and a different framing. Swapping one synonym is not enough.
- **Preserve exactly:** code, identifiers, file paths, setting keys, URLs, numbers, proper nouns, foreign-language terms being tested, and anything in backticks or code blocks. Reword the prose around them.
- **Keep the question type.** "Name the function that…" must still ask for a name, and "How many…" must still ask for a count.
- **Never leak the answer.** Don't add hints the original didn't have, and don't drop qualifiers that make the question answerable (e.g. "in the staging environment").
- **Keep emphasis on the deciding word.** If the original bolds or italicises the word that disambiguates the question, keep that word emphasised.
- **Very short faces** still get rephrased. For example, "Define **monostich**" becomes "What does the term **monostich** mean?"

Reword each card at the moment you present it, not all up front.

**Examples:**

| Original face | Reworded face |
|---|---|
| In what module is `create_specialist_clean_job()` defined? | Which module would you open to find the definition of `create_specialist_clean_job()`? |
| How many possible **job states** are there? | A job can be in one of a fixed set of **states**. What's the size of that set? |
| Over what period is the worker fulfilment score measured? | The worker fulfilment score looks back over a window of time. How long is it? |
| What gates access to the Wagtail admin UI? | Which flag decides whether a user can get into the Wagtail admin at all? |

## Card types

Detect these from the content and handle them as follows.

- **Basic**: the face is above `---` and the answer is below it.
- **Reverse-review** (`review-reverse?: true`): the card is meant to be learnt in both directions. For each one, randomly choose the direction:
  - forward: present the face and grade against the back
  - reverse: present the back as the prompt and grade against the face

  Say "(reverse)" next to the card header when drilling in reverse. Many such cards phrase the back as a question, which makes this natural.
- **Cloze**: the content contains `{{…}}`.
  - If the cloze markers are in the face, show the face with each `{{…}}` replaced by `[…]`. The answer is the hidden text.
  - If the face is an ordinary question and the cloze markers are only in the back, treat the card as basic and use the back, with braces removed, as the answer.
  - When rewording, never reword the hidden parts.
- **Images** (`![…](…)` with `attachments`): the image usually won't be available to you. Tell the user the card has an image you can't display, and give its filename. Ask whether to attempt the card from the text alone or skip it, unless the text is answerable on its own.
- **Sequence decks**: these are decks for memorising passages line by line, such as poems or speeches. You can recognise them by a card whose face is `_First line_` (any case) and one whose back is `_End_` or `_Last line_`, with each card's back being the next card's face.
  - Turn rewording off. The verbatim line is the cue.
  - With "all cards", drill in passage order from the first line rather than shuffling, unless the user asks for random order.
  - Grade strictly on the exact line, but treat punctuation differences as minor.
  - If two adjacent cards disagree, mention it once as a likely card error. For example, card N's back differs from card N+1's face.
- **Code answers**: when the back is a code block, accept the identifier without backticks or a code block. Grade only the code itself.

## Edge cases

- **Mochi tools not available:** say the Mochi connector needs to be connected, and stop.
- **The user switches deck mid-session:** give a summary of the cards drilled so far, then restart at step 2 for the new deck.
- **The user asks to edit a card** (e.g. they spot an error): explain that the connector can't edit cards. Note the card name and id, and the suggested fix, in the final summary.
