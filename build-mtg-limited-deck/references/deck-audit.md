# Deck audit

Run `python3 <skill-dir>/scripts/audit_deck.py input.json` before delivering a complete list. Use `--help` for command options. The standard-library script checks arithmetic and inventory; strategic roles, card text, and colored access still require judgment.

Supply one JSON object:

```json
{
  "deck": {"Island": 8, "Mountain": 9, "Example Spell": 23},
  "pool": {"Example Spell": 23},
  "land_names": ["Island", "Mountain"],
  "previous": {"Island": 9, "Mountain": 8, "Example Spell": 23},
  "size": 40
}
```

Replace the example with the verified full list and pool. Use exact names and positive integer quantities. Include every land in `land_names`, using verified card types; a landcycling spell remains a nonland. For modal double-faced cards, use the front face for the reported land count and assess the land face separately as conditional mana access.

`previous` is optional and produces the exact additions and removals, including basics. `size` defaults to 40. The five ordinary basic lands are unlimited by default; override `unlimited_basics` with the exact permitted names when the format differs. Snow basics, Wastes, and nonbasic lands require pool copies unless the format explicitly permits unlimited copies. Include all unlimited basics used by the deck in `land_names`.

Read `errors` and `ok`, plus total cards, lands, nonlands, and changes. Exit status is 0 for a passed audit, 1 for a failed count/copy/land audit, and 2 for malformed input. Correct the source list and rerun after any changes. If inventory is incomplete, report the unresolved copy check rather than inventing pool quantities to make it pass.

When modifying the helper, run `python3 -m unittest discover -s <skill-dir>/scripts -p 'test_*.py'`.
