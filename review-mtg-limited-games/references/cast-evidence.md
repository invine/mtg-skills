# Cast evidence helper

Run `python3 <skill-dir>/scripts/cast_evidence.py input.json` to check cast evidence used in a generated timeline. This standard-library helper classifies normalized evidence; it does not decode Arena logs or verify the referenced source by itself.

Supply an `attempts` list. Give each attempt a unique ID, the card name, an optional boolean `claimed_cast`, and chronological evidence records:

```json
{
  "attempts": [{
    "attempt_id": "g4-event120-123",
    "card": "Example Spell",
    "claimed_cast": false,
    "events": [
      {"kind": "selected", "source": "game4.json:event120"},
      {"kind": "stack_entered", "source": "game4.json:event121"},
      {"kind": "canceled", "source": "game4.json:event123"}
    ]
  }]
}
```

Normalize from the current schema or verified replay frames. Preserve the source location for each event. Separate repeated attempts at casting the same card. Restrict this helper to casts; activated abilities, copied spells, and creatures put directly onto the battlefield have different semantics.

| Evidence kind | Required observation |
| --- | --- |
| `selected`, `targets_selected`, `payment_started`, `stack_entered`, `costs_paid` | An intermediate step in the attempt; it establishes no final commitment alone. |
| `cast_completed` | The source establishes that all casting steps finished. |
| `priority_after_cast` | Casting and payment have finished and a player receives priority to respond to this spell. Mere phase or priority movement is insufficient. |
| `resolved`, `countered` | This spell instance resolves or is countered after being cast. |
| `canceled` | Explicit cancellation or a verified rollback before commitment, restoring the attempt's card and resources. A spell returned to hand after being cast is not cancellation. |

Read the resulting `status` (`committed`, `canceled`, or `unresolved`) and preserved evidence. Commitment plus cancellation within one attempt is conflicting evidence: split wrongly grouped attempts or repair the mapping. An incomplete attempt remains unresolved even if mana was tentatively tapped. Report a played spell only when status is `committed`.

`claimed_cast` audits an existing timeline: true requires committed evidence; false conflicts with committed evidence. Omit it when classifying evidence before constructing a timeline. Exit status is 0 when claims agree and evidence has no conflict, 1 for a claim mismatch or conflicting evidence, and 2 for malformed input or unknown evidence kinds. Status 0 can include unresolved attempts; inspect each status before narration.

When modifying the helper, run `python3 -m unittest discover -s <skill-dir>/scripts -p 'test_*.py'`. When adapting a raw decoder, add fixtures from its supported schema for cancellation, completed casts, recasts, and truncated evidence; verify that normalization preserves source references and produces the expected helper input.
