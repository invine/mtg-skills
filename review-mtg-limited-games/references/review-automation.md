# Deterministic review tools

## Coverage and findings

After extracting a run, initialize its review ledger. Resolve scripts relative to this skill; store outputs beside the event evidence, outside the skill directory.

```bash
python3 -B <skill-dir>/scripts/review_tools.py init <evidence-dir> --out <evidence-dir>/review.json
python3 -B <skill-dir>/scripts/review_tools.py cycles <evidence-dir> --game 4 --global-turn 17
python3 -B <skill-dir>/scripts/review_tools.py combats <evidence-dir> --game 4 --global-turn 17
python3 -B <skill-dir>/scripts/review_tools.py knowledge <evidence-dir> --game 4 --event 468
python3 -B <skill-dir>/scripts/review_tools.py context <evidence-dir> --game 4 --event 468
```

For whole-game subsets, give `--games 4` or the requested game numbers. For a position-only question, use `--position 4:468` (repeat for multiple positions); this creates evidence and position checks instead of requiring a full-game review. Supply the same scope flags to `init`, `validate` and `render`. Validation defaults to all event games independently of the editable ledger, so deleting its game list cannot silently narrow the request. Initialization preserves unavailable games and starts every check as `unreviewed`. Keep an existing ledger for follow-ups; initialization refuses to overwrite it. Schema 2 requires linked decision records, not just coverage notes. Follow [decision-audits.md](decision-audits.md) to freeze snapshots, compare candidates and attach `decision_ids`. Mark a check `reviewed` only when its required facets are complete. For `insufficient_evidence`, fill `missing`, `impact` and `note`; the validator reports `complete:false`. Generated coverage measures observations, not completed reasoning. Preserve a schema-1 ledger as historical evidence and reconcile its findings into a freshly initialized schema-2 ledger; changing its version number does not complete the new checks. Inspect the evidence check for each game for missing openings, unresolved casts and history gaps.

The knowledge query returns point-in-time `hand_knowledge` by **viewer seat**, including the card owner, first observed event and known hand-entry event. Use the opponent's viewer seat to establish what they knew about our hand. Source visibility and public identity changes support knowledge; later reveals cannot backfill it. Hidden-library transitions or gaps break tracking. An empty list means no established known identity, not that the opponent knows nothing through unrecorded information. Rank their intentions with [opponent-model.md](opponent-model.md).

Turn cycles follow actual active-player transitions, so extra turns do not shift the pairing. Their windows contain our main-phase resources and resources remaining after each following opponent turn. `payments` are observed mana annotations, labeled with a cast status when attributable; `canceled` payments are restored attempts, and `unresolved_or_activation` needs an adjacent-state check. These annotations are not a complete mana-spent total. Source candidates require checked colors, restrictions, readiness and costs. A final cycle without the next own turn is explicitly incomplete.

Combat episodes preserve selection changes, commit evidence, passed windows and incomplete windows. `committed` establishes observed attackers after declaration; it does not imply that all later blockers or damage are known. Inspect `block_commit_event`, `complete_window`, gaps and adjacent states. `life_before`/`life_after` can include spells and triggers; attribute damage from the actual sequence. A passed attack with no combat phase in the stream remains part of the turn-cycle audit.

For every highlighted play, including positives and overview callouts, add a finding to `review.json`. Copy the `context` command's JSON unchanged, then supply:

```json
{
  "id": "F1", "game": 4, "state_event": 468, "choice_event": 469,
  "decision_id": "g4:e468:interaction",
  "label": "Game 4 — your turn 9, responding to Unsummon",
  "context": {},
  "analysis": "State, opponent read, played line and strongest alternative, response, downside, winning route, confidence and reusable cue.",
  "verification": {
    "method": "source_and_state", "url": "<exact context position URL>",
    "checked": ["turn", "board", "stack"],
    "note": "Record the actual state comparison and evidence supporting it."
  }
}
```

Replace the illustrative event numbers with the actual decision. The state is **after** `state_event`; `choice_event` must be later. For a passed-action window use `window_end_event` instead of `choice_event`. Verify positions using [17lands-replays.md](17lands-replays.md#decision-links). Choose `ui` for an opened and checked replay or `source_and_state` for checked source mapping plus raw state. A known frontend fingerprint supports mapping; the reviewer still checks the relevant board and stack. For a preceding frame, unsupported mapping, or unavailable exact link, set verification to `{"method":"unavailable","reason":"...","source_url":"...","locator":"...","excerpt":"..."}`. The renderer exposes that fallback beside the finding.

```bash
python3 -B <skill-dir>/scripts/review_tools.py validate <evidence-dir> <evidence-dir>/review.json
python3 -B <skill-dir>/scripts/review_tools.py render <evidence-dir> <evidence-dir>/review.json
```

Render retained finding blocks from the validated ledger and use them in the answer, including the same link when mentioning that play in an overview. If assembling an answer file, keep the invisible `finding:F1` comment markers and run `validate ... --answer <answer-file>` to check those blocks against the ledger. Validation checks declared scope, source/decoder freshness, independent decision coverage, before-action facts, baseline resource identities, recomputed calculations, finding-to-decision links, exact URLs and verification records. It cannot prove that all effects were normalized correctly, that candidates cover every legal option, or that prose judgments follow from the evidence. It also cannot prove the order in which the reviewer reasoned. Review those limitations explicitly rather than calling a passing ledger proof of strategic correctness. Zero findings is valid. Retain withdrawn claims with their reasons in `withdrawn`; do not reintroduce them without new evidence.

## Card references

```bash
python3 -B <skill-dir>/scripts/card_reference.py <evidence-dir> --name "Semester Foreseer"
python3 -B <skill-dir>/scripts/card_reference.py <evidence-dir> --id 106265 --offline
```

The lookup reuses event metadata and the Scryfall printing ID in its image URL. It verifies the returned printing/name, returns all faces (including prepared spells), and caches raw text with source URL, retrieval time and hash under `card_text/`. Immutable content-hash files under `card_text/versions/` preserve earlier text and provenance across refreshes. Use the Arena ID for ambiguous names. Reuse `--offline` for follow-ups; use `--refresh` when text may have changed. `complete_text` means the exact record has its required text fields, not that every interaction or format modification is resolved. An unresolved result preserves metadata and identifies the gap; use another authoritative source or the card image for that gap. Check digital/rebalanced names exactly.

## Bounded calculators

Run `python3 -B <skill-dir>/scripts/limited_math.py <input.json>`; `-` reads stdin. The same script can support deck building. Results are `calculated`, `unsupported`, or invalid input. Enter normalized, verified facts. Preserve assumptions with the resulting comparison.

**Draws:** use disjoint groups of physical cards; one dual land belongs to one group with both color tags. Specify the population remaining at the decision and the number of future cards seen. This exact finite-sampling model omits Arena opening smoothing, selection effects, mulligan policies and casting costs.

```json
{"kind":"draw","model":"uniform_without_replacement","draws":2,"groups":[{"count":8,"tags":["blue","land"]},{"count":7,"tags":["white","land"]},{"count":18,"tags":[]}],"minimum":{"blue":1}}
```

**Mana:** supports a sequence in one window, one mana per ready source, colored/colorless/generic costs and color/color hybrid pips. Apply verified discounts to input costs. Choose X explicitly. State source restrictions/readiness, sacrifice costs, summoning sickness, alternative payments and floating-mana expiry outside the calculator. `tap_sources` spends that physical source on the activation before paying its mana cost. Search preserves colors needed by later steps rather than greedily spending a dual first. Search limits yield `unsupported`, never a false impossibility verdict.

```json
{"kind":"mana","assumptions_verified":true,"sources":[{"id":"dual","produces":["W","U"],"ready":true},{"id":"island","produces":["U"],"ready":true}],"floating":[],"steps":[{"cost":"{U}"},{"cost":"{W}"}]}
```

**Combat:** supports multiple blockers, first/double strike, marked damage, flying/reach, vigilance, haste, trample, deathtouch, lifelink and indestructible. It removes dead creatures between damage steps and preserves blocked status if blockers leave. Default damage allocation assigns lethal successively in the supplied blocker list, then excess to the last blocker or through trample. This is a chosen legal policy, not an optimal assignment or a rule requiring blocker order. To choose another split, supply `allocations`, for example `{"normal":{"a":{"blockers":{"b":1,"c":2},"target":0}}}`; phase keys are `first` and `normal`. Current rules permit a legal split without killing either blocker. See [Foundations rules changes](https://magic.wizards.com/en/news/announcements/foundations-update-bulletin).

```json
{"kind":"combat","declarations_verified":true,"attackers":[{"id":"a","power":3,"toughness":3,"keywords":["first strike"],"target":"opponent"}],"blockers":[{"id":"b","power":2,"toughness":3},{"id":"c","power":2,"toughness":3},{"id":"d","power":2,"toughness":3}],"blocks":{"a":["b","c","d"]}}
```

The output includes each damage step, target damage, deaths, survivors and lifegain. Unmodeled triggers, prevention/replacement, protection, changing abilities between steps, or one blocker blocking multiple attackers require explicit manual analysis. `declarations_verified:true` attests that omitted mechanics do not change this branch; it does not remove them from the real game.

**Lethal and land candidates:** [decision-audits.md](decision-audits.md#candidate-inputs) defines the `lethal` and `land_options` inputs. Use them during candidate generation, not only after spotting an error. Preserve the exact inputs/results and resource bindings in the decision ledger. Search bounds return `unsupported`, never a claim that no winning line exists.

## Maintenance checks

Run `scripts/validate_extractor.py` after changes. To enable automatic validation in a checkout, run `python3 -B <skill-dir>/scripts/validation_guard.py install <skills-repository>`. The local pre-push guard checks the actual outgoing revisions' MTG test suites in temporary snapshots and chains the existing hooks, including Git LFS. It leaves their original files intact. Install once in each new checkout, or reinstall if its hook configuration changes; skill files cannot configure hooks in another environment automatically. Preserve source provenance and increment the decoder version when derived semantics change.
