# Replay evidence

## Retrieval and scope

For a 17Lands details, history, deck, or pool link, establish the event and the page's role before following associated links. Use the public page, exports, or publicly accessible page data. Follow access controls; if the required replay is unavailable, ask for a log, export, or screenshots and bound the review to available evidence.

Record match and game indices independently. A best-of-three match can contain several games; URLs may use zero-based indices while the user calls the first game “game 1.” Map each game to its actual deck version and player seat. Obtain the card details needed to interpret actions; metadata with a card name and mana value may omit decisive rules text.

If a card-text lookup fails, use the event's card identifiers to locate complete text or inspect the linked card image from a reliable source. Verify costs, static abilities, and relevant faces; ability metadata can be incomplete. Reuse a successful source once it resolves the question rather than repeating equivalent failed lookups. Record any remaining text gap explicitly.

Treat frontend routes and endpoint schemas as current-source lookups. Inspect the page's current data requests or source when necessary rather than assuming a remembered private API. Check response status, payload shape, null responses, and gzip compression before interpreting a failed decode as missing history.

## Evidence reuse

Keep a task-local evidence index keyed by event, match, game, seat, and deck version. Record each source URL, retrieval time, local path, content hash, and decoder/schema version or observed fields. Retain raw responses separately from summaries. Reuse valid downloaded histories and verified card text for follow-ups; fetch again when coverage is missing, the event has advanced, or the source or interpretation changed. Rebuild derived summaries after a decoder correction.

Build a compact timeline with global turn/phase, material committed actions, life and board changes, and raw-event/frame references. Scan every requested game, then inspect detailed states around consequential decisions and disputed claims. Keep a small ledger of verified findings, uncertainties, and withdrawn claims. Reopen source evidence for a new question rather than treating an earlier conclusion as a fresh fact.

For a new decoder, inspect the current payload's required fields and full/diff behavior before parsing. Stop at an unknown shape with a useful diagnostic; use an export or visible replay for the affected gap. Keep endpoint discovery separate from state reconstruction, so a changed route need not change game logic. Preserve a mapping from each cited decision to its raw event or replay frame; publish precise frame anchors only after verifying them.

## Raw Arena event interpretation

Apply these checks when reconstructing `gameStateMessage` or similar event streams:

- Establish whose seat is the player in each game. Seat assignment can change across games.
- Distinguish full snapshots from diffs. Inspect schema semantics before merging: replacement objects can reset omitted booleans; zone lists can replace their previous contents.
- Track zone changes and object-ID changes. A returned creature may acquire a new ID; a vanished token must leave the battlefield model.
- Count threshold and recursion targets from actual graveyard cards. A cast spell copy that ceases to exist contributes no lasting card; confirm how a prepared or generated spell is represented before adding it to the count.
- Track persistent annotations, their deletion, counters, continuous effects, and temporary modifiers. Retain multiple instances of an ability when they each trigger; a dictionary keyed only by ability ID can lose double prowess.
- Separate available `actions` from selected actions and committed actions. Apply the cast-confirmation rules below before counting a spell as cast.
- Distinguish tentative attack/block selections from committed combat. Use the final combat and damage state before judging trades.
- Resolve targets from actual target and resolution evidence. An annotation's affected ID can identify a spell or ability rather than its target.
- Advance phase, priority, life totals, hand counts, and mana even when an event has no visible narration.
- Keep hidden identities concealed until their reveal. An ID associated with a later revealed card does not make that identity known on an earlier turn.
- Label turn numbers accurately: a global turn counter advances on each player's turn, unlike “my turn five.”

Validate reconstructed states around proposed criticisms against visible replay snapshots when available and reconcile hand sizes, mana spent, damage, deaths, and triggers over adjacent raw states. Use browser interaction to resolve a specific evidence gap; reuse complete verified data rather than reopening the UI solely to create deeper links. If the visible replay is unavailable, establish the relevant facts directly from raw state and resolution evidence, identify remaining uncertainty, and omit unverified frame anchors. A parser's prose summary is a working aid, not independent evidence. An uncertain reconstruction supports a conditional observation, not a firm gameplay error.

## Cast confirmation

Treat selecting a spell, assigning targets, entering payment, and tentative stack movement as a casting attempt. Confirm commitment from a completed cast, resolution, countering, or priority passing after casting and payment finish. A rollback can restore the card and mana before commitment; exclude that attempt from spells cast, triggers, and mana spent. Scope evidence to one attempt and spell instance, so a later successful recast remains separate.

When emitting an automated cast timeline, or when a criticism depends on a suspected canceled cast, run `scripts/cast_evidence.py` before treating it as a played action. Read [cast-evidence.md](cast-evidence.md) for normalization and source-reference requirements. This helper checks the normalized evidence boundary; adapt the current upstream schema separately and verify its mapping against the source.

If evidence conflicts, inspect adjacent states and keep the action unresolved until reconciled. A countered spell was still cast; a canceled attempt was not. Preserve canceled attempts as optional context about deliberation, without evaluating them as executed plays.
