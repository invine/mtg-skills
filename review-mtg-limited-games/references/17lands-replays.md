# Replay evidence

## Retrieval and scope

Use the bundled [Python extraction workflow](17lands-extractor.md) first. Inspect its manifest, coverage, and selected states before writing new retrieval or parsing code. The checks below govern adapter changes and evidence verification; apply them directly when execution or a supported schema is unavailable.

For a 17Lands details, history, deck, or pool link, establish the event and the page's role before following associated links. Use the public page, exports, or publicly accessible page data. Follow access controls; if the required replay is unavailable, ask for a log, export, or screenshots and bound the review to available evidence.

Record match and game indices independently. A best-of-three match can contain several games; URLs may use zero-based indices while the user calls the first game “game 1.” Map each game to its actual deck version and player seat. Obtain the card details needed to interpret actions; metadata with a card name and mana value may omit decisive rules text.

If a card-text lookup fails, use the event's card identifiers to locate complete text or inspect the linked card image from a reliable source. Verify costs, static abilities, and relevant faces; ability metadata can be incomplete. Reuse a successful source once it resolves the question rather than repeating equivalent failed lookups. Record any remaining text gap explicitly.

Treat frontend routes and endpoint schemas as current-source lookups. Inspect the page's current data requests or source when necessary rather than assuming a remembered private API. Check response status, payload shape, null responses, and gzip compression before interpreting a failed decode as missing history.

## Evidence reuse

Keep a task-local evidence index keyed by event, match, game, seat, and deck version. Record each source URL, retrieval time, local path, content hash, and decoder/schema version or observed fields. Retain raw responses separately from summaries. Reuse valid downloaded histories and verified card text for follow-ups; fetch again when coverage is missing, the event has advanced, or the source or interpretation changed. Rebuild derived summaries after a decoder correction.

Build a compact timeline with global turn/phase, material committed actions, life and board changes, and raw-event/frame references. Scan every requested game, then inspect detailed states around consequential decisions and disputed claims. Keep a small ledger of verified findings, uncertainties, and withdrawn claims. Reopen source evidence for a new question rather than treating an earlier conclusion as a fresh fact.

For a new decoder, inspect the current payload's required fields and full/diff behavior before parsing. Stop at an unknown shape with a useful diagnostic; use an export or visible replay for the affected gap. Keep endpoint discovery separate from state reconstruction, so a changed route need not change game logic.

## Decision links

Make each highlighted decision independently inspectable:

1. Record its event, match/game indices, player seat, global turn, active player, phase, and raw event. Select the state immediately before the choice; use the opening-hand decision for a mulligan and the available action window for a passed attack or missed response. Link additional positions when a finding depends on separate windows, such as passing the main phase and then declining an end-step play.
2. Obtain the exact-position URL from the replay's current share/navigation controls or derive it from the current frontend's URL parsing and frame construction. Map the raw event to the displayed replay position explicitly: raw array indices, `gameStateId`, global turns, and UI frame indices may differ. Use observed URL syntax and preserve the correct match/game indices.
3. Open each distinct position URL and check that it lands on the intended turn, phase, and board or stack state. An HTTP success or a page that opens at the start of the game is not verification. If rendering is unavailable, verify both the URL parameter handling and the mapped replay state from current source and raw data; record that verification method in the evidence index. Reuse a verified mapping within the review.
4. Keep the URL, position locator, verification method, and supporting state with the finding. Check the final answer's links against this ledger, including brief positive examples and overview-table callouts.

If the source lacks exact-position links or neither verification route is available, document the specific limitation. Supply the nearest source link, match/game, whose turn, global turn, phase, action description, and a snapshot or short log excerpt that locates the decision. For screenshot or log-only reviews, cite the particular image or log location. Publish only verified position URLs; never invent an anchor to satisfy the output requirement.

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

Validate reconstructed states around proposed criticisms against visible replay snapshots when available and reconcile hand sizes, mana spent, damage, deaths, and triggers over adjacent raw states. Use browser interaction to resolve evidence gaps or verify where decision links land. If the visible replay is unavailable, establish the relevant facts directly from raw state and resolution evidence and identify remaining uncertainty. A parser's prose summary is a working aid, not independent evidence. An uncertain reconstruction supports a conditional observation, not a firm gameplay error.

## Cast confirmation

Treat selecting a spell, assigning targets, entering payment, and tentative stack movement as a casting attempt. Confirm commitment from a completed cast, resolution, countering, or priority passing after casting and payment finish. A rollback can restore the card and mana before commitment; exclude that attempt from spells cast, triggers, and mana spent. Scope evidence to one attempt and spell instance, so a later successful recast remains separate.

The bundled extractor already calls `scripts/cast_evidence.py` when emitting its cast timeline. For another decoder or a suspected canceled cast outside that output, run the helper before treating the attempt as a played action. Read [cast-evidence.md](cast-evidence.md) for normalization and source-reference requirements. This helper checks the normalized evidence boundary; verify the raw adapter's mapping against the source.

If evidence conflicts, inspect adjacent states and keep the action unresolved until reconciled. A countered spell was still cast; a canceled attempt was not. Preserve canceled attempts as optional context about deliberation, without evaluating them as executed plays.
