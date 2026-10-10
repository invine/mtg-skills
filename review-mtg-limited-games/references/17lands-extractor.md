# Python extraction

## Run and inspect

Use the standard-library CLI at `scripts/extract_17lands.py` for public 17Lands event links. Resolve the script relative to this skill's directory. Keep downloaded evidence in a task-local directory outside the skill repository.

```bash
python3 -B <skill-dir>/scripts/extract_17lands.py fetch <17lands-url> --out <evidence-dir>
python3 -B <skill-dir>/scripts/extract_17lands.py summary <evidence-dir>
python3 -B <skill-dir>/scripts/extract_17lands.py timeline <evidence-dir> --game 4
python3 -B <skill-dir>/scripts/extract_17lands.py state <evidence-dir> --game 4 --event 468
```

`fetch` processes the whole event, including every game within a best-of-three match. For a request restricted to one game, restrict the review to that game. `--game` is one-based across the event; stored match/game indices are independently zero-based. `state --event` is the state **after** that zero-based raw event. To inspect a decision, select the event before the action, then verify its phase and stack. `timeline --turn 9 --actor player` narrows output using the replay's displayed turn number; global turn and active seat remain authoritative, especially with extra turns.

Read every game's summary before reviewing plays. A successful exit can include state gaps, an unverified frontend, or unresolved casts. Inspect those entries in `summary.json` and the game's derived JSON. `coverage` describes stream reconstruction, while `cast_evidence_complete` and `casts` describe action evidence. An unavailable game remains in the manifest and summary; report partial scope rather than silently excluding it. Unknown essential schemas fail with diagnostics and retain already-downloaded evidence.

**Complete when:** requested games, actual decks, seats, results, openings, and coverage are accounted for; gaps that might change a verdict have a raw-state or visible-replay check.

## Reuse evidence

The manifest stores source URLs, response hashes, retrieval times, frontend identity, and independent match/game indices. Raw responses retain their downloaded bytes, including gzip; decoding uses byte signatures instead of trusting the content-type header. Card metadata is supplemented with the played deck's mana costs. Inspect linked card images or another authoritative text source for missing faces or decisive rules.

Reuse the same directory for follow-ups. `fetch --offline` requires cached responses; `build <evidence-dir>` rebuilds derived output without network access after a decoder change. `fetch --refresh` refreshes the event and current frontend when an event has advanced or sources may have changed. Hash mismatches stop cache reuse. Read `--help` for the current interface rather than reconstructing commands from memory.

The main outputs are `manifest.json`, `raw/`, `summary.json`, and one `derived/m<match>-g<game>.json` per reconstructable game. Each game includes the actual deck, opening observations, turn start/main/end states, action evidence, cast statuses, and frame positions. Start with the compact CLI timeline, then query selected raw events. Preserve raw evidence separately from conclusions; avoid loading all histories into the conversation.

The derived report also supplies per-viewer knowledge events, observed mana payments, combat episodes and turn cycles. Use [review-automation.md](review-automation.md) for concise queries, coverage tracking, card references and finding validation; reuse this derived data instead of writing another ad hoc ledger generator.

## Use positions and uncertainty

The frame mapper implements the inspected frontend's default `visibleDiff` behavior. A recognized exact bundle hash produces `source_mapping` positions; an unfamiliar hash produces `unverified_candidate` positions. Endpoint discovery is independent: changed frontend routes stop retrieval for inspection, while changed frame logic need not prevent analysis of cached raw states. Update the supported fingerprint only after inspecting the new route/frame code and checking regression positions.

For each highlighted decision, apply the verification procedure in [17lands-replays.md](17lands-replays.md). Compare the returned position's event, turn, board, and stack with the requested state. Some raw events produce no new displayed frame: the CLI labels the preceding visible frame explicitly. Such a link may show an earlier phase or stack and needs verification or the documented fallback. A source mapping is not a claim that the URL has been opened in the browser.

The decoder preserves point-in-time visibility, replacement-object semantics, zone membership, object-ID changes, counters, persistent annotations, raw combat fields, and public/own-hand information. It summarizes libraries by count rather than exposing hidden order. Sources with an `Add` ability are **mana-source candidates**: verify colors, restrictions, floating mana, tap/sacrifice costs, summoning sickness, and activations before proposing a sequence. The decoder does not implement the Magic rules engine or decide strategic advantage.

Cast reports pass normalized evidence through `cast_evidence.py`. Prepared copies can resolve without becoming graveyard cards. Casting payment alone remains intermediate evidence; incomplete and unsupported departures remain unresolved. A narrowly verified card-and-mana rollback is canceled, and a later recast is a separate attempt. Spell copies put directly onto the stack are not assumed cast. Combat observations retain selections and subsequent changes; verify final combat and damage before narrating an attack or block as committed.

**Complete when:** retained findings cite verified positions, unresolved attempts remain distinct from played spells, and proposed lines use checked resources rather than source counts alone.

## Maintain the adapter

Keep retrieval/cache code in `seventeenlands_io.py`, reconstruction in `seventeenlands_state.py`, and presentation in `extract_17lands.py`. Test at the public CLI and decode boundaries. Run `python3 -B <skill-dir>/scripts/validate_extractor.py` after changes; it compiles Python sources and runs the bundled regression suite without network access or bytecode artifacts.

Regression coverage includes gzip/cache integrity, offline CLI operation, best-of-three indexing, prepared-copy resolution, cancellation/recast boundaries, visibility, object replacement, missing states, and a replay position independently checked in the UI. Expand fixtures when adapting a new upstream shape. Run a live fetch and an offline rebuild on an accessible real event when changing retrieval; compare consequential states with raw evidence or the replay. Keep a changed decoder version with regenerated derived output.

When changing these tools, enable the automatic outgoing-revision guard described in [review-automation.md](review-automation.md#maintenance-checks); it preserves existing hooks and runs both MTG skills' available regression suites.
