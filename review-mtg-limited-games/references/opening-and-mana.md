# Opening decisions and mana use

## Mulligans without hindsight

Audit the initial hand, each available redraw, the final keep, and any bottom choices in wins and losses. Record play/draw, hand size, prior mulligans, applicable rules, actual deck version, and matchup information available then. Treat missing opening or bottom evidence as a coverage limit.

Write the hand's first meaningful plays using actual colors and entry timing. Identify required land or spell draws, their deadlines, and what happens if they arrive a turn late. Separate castable selection or landcycling from spells stranded behind the missing color, and pay the fixing cost before claiming an on-curve creature. Count a functional opening, not simply two or three lands.

Compare keeping with taking another mulligan: lost card, expected access to a functional start, threat/answer balance, and the deck's capacity to recover. For a London mulligan, assess the seven seen and the legal bottom choice together; compare alternative bottoms by the resulting plan. Evaluate an unknown redraw by the remaining deck's plausible hands rather than assuming it contains the missing land or best curve. Further mulligans need their own cost comparison.

Use the extra cards seen on the draw and the opponent's initiative together. A marginal hand can be preferable to going to five; a seven-card hand needing an immediate off-color source can still deserve a mulligan. Price low-land, high-land, and engine-only hands through their castable early actions and next useful plays. Use known matchup demands when available.

Keep later topdecks and the game result out of the verdict. Mention a fortunate draw only to separate recovery from keep quality. For probabilities, state deck/source counts, cards seen, timing, and hand-generation assumptions, including uncertainty about Arena smoothing. Source-hit probability alone does not establish a keep threshold or castability.

Retain a compact judgment: **hand and play/draw → first plays and required draws → keep versus smaller-hand cost → preferred keep/bottom/mulligan and confidence**. Report consequential decisions rather than padding the review with routine keeps.

## Audit each turn's mana

Track a turn from the player's untap through the opponent's turn before the next untap. Record the available land drop, source colors, tapped/conditional sources, nonland and floating mana, committed payments, and useful response windows. Count each source once when tapped; count a utility land committed to its own activation as unavailable for producing mana. Reconcile newly generated mana and changed discounts before the next action. Exclude canceled payments using the cast-evidence procedure.

Use the [decision record](decision-audits.md) to track each land choice, development sequence and reserved interaction independently: usable sources, planned payments, alternatives and resources through the next opponent turn. Compare color access even when the planned line spends no mana; a land can strand a held answer without affecting the immediate play. The ledger is coverage evidence, not a mandatory final table. Distinguish mana that could have been spent at different windows from mana simultaneously available for one sequence.

Review three cases separately:

| Case | Comparison |
| --- | --- |
| Mana expires unused | Was there a useful legal play? Was reserving a response correct at the decision time? Once the opponent passed, was an end-step sink or spell still available? |
| All mana is spent but the board stagnates | Did draw, filtering, pings, or engine setup displace a stronger threat, blocker, or answer already in hand? When can the new resources affect the game? |
| A small action consumes the last relevant mana | Does omitting or reordering it permit threat plus removal/protection, a second spell, or a decisive activation? Price its lost damage or value against that option. |

Start alternatives from the verified hand and use the strategic-patterns sequence procedure. Compare development, interaction, draw, and sinks through the next meaningful opposing play and our next attack or activation. For recovery spells or graveyard activations, apply the recursion comparison below. Check land-before/after-spell order, discounts enabled by the first permanent, once-per-turn loyalty choices, and precombat triggers or hasty tokens. A tap-out line should also pass the opponent-model threat-deployment comparison.

Rank mana by its contribution to winning: relevant board, pressure, answer windows, or a realizable engine payoff. Credit holding mana for a sufficiently likely threat even if that threat never appears. Charge holding mana when it gives up development without a supported read or later use. Prefer using leftover mana when the opportunity cost is low; acknowledge cases where every available activation would damage the plan.

Compare who benefits from another untap. Establish the clock, blockers, or recurring value gained by deploying now, and the concrete benefit purchased by waiting. An existing hand full of useful spells raises the opportunity cost of expensive draw; a missing land or answer can reverse that preference. Judge using the information then available, not the eventual card drawn.

**Complete when:** every available opening decision and turn has been checked; retained findings identify a legal alternative, its useful payoff, response exposure, and downside. A full mana bar, unused mana, or a resolved bomb alone establishes no error.

## Recursion as current development

Enumerate legal targets by what they enable now: a land drop, an affordable blocker, removal, a combat trick, or a later finisher. Compare these with saving the recovery spell. For a land, verify that it is already in the graveyard, the land drop remains, and its entry timing and color support the follow-up. Include the blocker lost when a mana creature must tap.

Check instant-speed recovery before unused mana expires. Compare recovery before untapping plus next-turn deployment with paying both costs next turn. Price life gained by whether it buys a useful action or changes lethal, while retaining the cost of spending a flexible recovery card. Publicly returning a trick changes the opponent's block options; use the opponent-model comparison for that branch.

When a hand spell and a graveyard activation recover the same creature, compare total recovery-and-deployment cost, life gained, resources exiled, and the future targets each option preserves. Keep card flexibility and immediate survival in the same comparison. Prefer a small target when its feasible follow-up improves the winning route more than waiting for a bomb.
