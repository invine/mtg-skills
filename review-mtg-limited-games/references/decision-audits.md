# Before-action decision records

Use this contract for each requested review. The main skill defines the candidate order; this reference defines the evidence and executable checks. Keep records task-local, separate from the concise coaching answer.

## Freeze, analyze, attach

1. Initialize coverage using [review-automation.md](review-automation.md). For each relevant decision, locate the state immediately before the action. A turn-start state does not replace a later land or target decision after new information.
2. Generate a frozen view and template:

   ```bash
   python3 -B <skill-dir>/scripts/review_tools.py decision <evidence-dir> --game 3 --event 429 --kind lethal
   ```

   `snapshot` with the same game/event returns the view without a decision template. It excludes the library order, sideboard, later events, outcome and opponent hand identities not established to our viewer. Public zones and our hand are retained. Verify face-down/private-zone visibility and exact rules externally where the source is incomplete. A snapshot does not guarantee complete land-drop, used-loyalty or preparation status: establish these from earlier source events before using the resource. If only a position is supplied, make the affected line conditional or unresolved. Earlier sequencing corrections need their own earlier snapshot; they are not actions available now. `hand_count` is the combined source hand-zone count, not an inferred opponent identity list.
3. Copy `decision` into the ledger's `decisions` list. Preserve its `context` and `snapshot_sha256`. For a historical review, record `choice_event` later than `state_event`, or `window_end_event` for a passed window. For a position-only recommendation with no subsequent play supplied, omit those fields and set `actual:{"status":"not_supplied"}`; validation with `--position` accepts this without inventing later events. Evaluate candidates using the snapshot before comparing actual play. Record a new decision after a draw/reveal if that information changes the continuation. The initial plan remains independently reviewable.
4. Attach the decision's ID to each applicable coverage check's `decision_ids`. Required kinds are: opening → `opening`; own turn cycle or requested position → `lethal`, `development`, `land`, `targets`, `combat`, `interaction`; combat episode → `lethal`, `targets`, `combat`, `interaction`. Records may be shared across overlapping windows. A land mistake and a development mistake require separate records, even on the same turn.
5. Validate, resolve errors, then render findings as described in review-automation. Link each finding using `decision_id` at that same state. `ok:true, complete:false` is an explicit partial review, not full coverage.

## Record contract

Every record needs `status` and a decision-specific `note`. For `reviewed` or `not_applicable`, `basis` cites exact facts from its snapshot:

```json
[{"id":"290","field":"power","value":4},
 {"id":"player:1","field":"lifeTotal","value":12},
 {"id":"turn","field":"phase","value":"Phase_Beginning"}]
```

Object IDs are strings containing the source `instance_id`; player IDs use `player:<seat>`, and turn fields use `turn`. Cite facts that support this particular judgment. `not_applicable` needs a reason there is no meaningful choice, such as no legal land option; a source fact alone does not establish that reason. `insufficient_evidence` needs `missing` and `impact`. If the entire source window is unavailable, put those fields on its coverage check instead.

A `reviewed` record has at least two materially distinct `candidates` and a `selected` candidate ID. Include pass/hold or a smaller attack where relevant. Each candidate has:

```json
{
  "id":"hold-removal",
  "information":"known_at_snapshot",
  "line":"Play the black source, make the planned attack, retain removal.",
  "actions":[{"source":"218","action":"Play Swamp"}],
  "calculations":[
    {"input":{}, "bindings":{}, "result":{}}
  ],
  "next_opponent_turn":{
    "untapped_sources":["218"],
    "held_interaction":["164"],
    "exposed":[],
    "assessment":"Explain which response is castable, its target window, and the relevant opposing threat."
  },
  "tradeoff":"Explain what this line gains and gives up, including the cost of waiting."
}
```

The example is a shape, not a complete calculation or mana inventory. Fill all resulting untapped sources, held options and exposed permanents. Use empty `actions` for pass. Sourced actions and future-turn resources must identify objects available at the snapshot. For prepared spells or abilities, source the originating permanent/card and verify its usable status. Concrete newly drawn resources belong in a later decision. Discuss an unknown draw as a conditional continuation without adding its identity to baseline actions.

Each calculation stores the complete input and exact output of `limited_math.py`. `bindings` maps every calculator creature, mana source, effect, held interaction and non-player attack target to a source object ID. IDs can already be source IDs, in which case map each to itself. Bind a prepared effect to its source card. Verify the transformation from the snapshot's stats to the hypothetical branch: costs, counters, triggers, readiness, targets and once-per-turn limits. Bindings establish provenance, not effect legality. Hypothetical objects without a source identity and unsupported mechanics require manual analysis.

Lethal/combat decisions need a `lethal` or `combat` calculation; land/interaction decisions need `land_options` or `mana`. Preserve calculations for every decisive branch, including the strongest opposing block. Development and target comparisons should reuse those calculations where they affect damage or castability. A calculator's favorable output alone does not justify a preference.

If a calculator returns `unsupported`, retain that output and add:

```json
{"manual":{"applies_to":"combat","assumptions":["Verified relevant rules"],
 "steps":["Explicit assignments, trigger resolution and deaths in order"],
 "result":{"damage_to_opponent":0,"survivors":[]},
 "uncertainties":[],"conclusion":"Explain the checked outcome and limits."}}
```

For mechanics entirely outside the supported inputs, use an input with `kind:"manual"` and a `mechanics` description; preserve the unsupported response. The validator checks the manual record's presence, not its arithmetic or strategic truth. If unresolved uncertainty could reverse the conclusion, use `insufficient_evidence` instead of `reviewed`.

When observed play is available, after establishing the candidates supply `actual:{"line":"Observed play","comparison":"How it compares with the selected candidate"}`. Keep outcome descriptions here, separate from the decision's known information. A failed attack need not invalidate the earlier development or counter-placement plan.

## Candidate inputs

Run `python3 -B <skill-dir>/scripts/limited_math.py <input.json>`. Inputs use verified effective costs and actual combat stats. Preserve relevant unmodeled rules in the manual analysis rather than silently deleting them to fit the tool.

### Lethal

`kind:"lethal"` takes `assumptions_verified:true`, opponent `life`, `sources`, optional fixed `sequence` of mana steps, eligible `attackers`, eligible `blockers`, and optional `effects`. Creatures use the combat format from review-automation. Only supply creatures legally able to attack/block; apply summoning sickness, tapped status and restrictions first. The tool explores attack subsets and all block assignments for its supported mechanics. For each tested block it uses the documented damage-allocation policy.

An effect is independently available once. Encode alternative targets under that single effect, not as multiple separately available copies:

```json
{"id":"known-pump-card","cost":"{1}{W}","choices":[
 [{"target":"attacker-a","power":2,"toughness":2,"keywords":["flying"]}],
 [{"target":"attacker-b","power":2,"toughness":2,"keywords":["flying"]}]
]}
```

A choice may change multiple creatures: a counter transfer can reduce the source's power/toughness while increasing the others. The tool considers skipping each effect, combines chosen effects in input order, checks mana, then searches attacks. A zero-toughness creature is removed before attacking. Normalize other consequences manually. Free effects use `{0}`; explicitly resolve X and all nonmana costs before encoding a choice. Effects must be independent except for shared mana: mutually exclusive loyalty abilities, effect-created resources, triggered draws and order-dependent legality need separate input branches or manual analysis. Do not spend a hypothetical draw.

`lethal_found:true` reports an attack subset, selected effects, minimum net damage across blocks, a worst-block witness and payments. Defending lifelink is deducted. This certifies the supplied model, not safety against every unknown trick. `lethal_found:false` rules out only the supplied transformations and allocation policy. Removal, burn, omitted abilities and unusual assignments still need review. Bounds: six attackers, five blockers, four independent effects, nine choices per effect and 50,000 block branches; exceeding them returns `unsupported`.

### Land options through the opponent turn

`kind:"land_options"` takes `assumptions_verified:true`, current `sources`, legal `lands`, a fixed `sequence` (possibly empty), `interaction` entries `{id,cost}`, and the `chosen` land ID. Sources and lands use the mana format `{id,produces:["B"],ready:true}`; `ready:false` covers tapped entry. Verify the unused land drop and that no additional untap, floating-mana carryover or source changes occur before the opposing response window.

The tool tries each land, pays the same planned sequence, then reserves each response **separately** before our next untap. `preserves_sequence_adds_interaction` flags choices that preserve the line and strictly expand the castable response set. Payment choices can differ between reserved-response branches; inspect the reported payments and verify that the chosen real payment retains all responses you intend to hold. Review source utility, future color requirements and target legality before judging the choice. A favorable option need not have been used in the actual opponent turn to have been available.

See `scripts/fixtures/review-regressions.json` for complete inputs and before-action fixtures. Tests cover concentrated first-strike blocks, pre-block evasion, colored removal access, false lethal/castability claims and later-draw contamination. Use these as maintenance regressions, not substitutes for reconstructing a new game.
