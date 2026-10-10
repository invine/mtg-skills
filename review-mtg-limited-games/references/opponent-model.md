# Opponent hands and best responses

## Infer a range from the preceding turns

Before judging a consequential decision, inspect the relevant earlier turns in this game. Start with cards legal in the format and plausible in the observed colors and plan. Filter named candidates by exact cost, timing, target restrictions, available colored mana, and public activation resources. Separate what they can cast now from expensive or color-stranded cards they may hold.

Track known cards, unknown hand size, draws, selection, discards, land drops, revealed spells, and mana use. Form a short ranked range of card classes, then name verified cards only where their different effects change the line. Use the following evidence to update the range:

| Observation | Update to consider | Check before relying on it |
| --- | --- | --- |
| Missed land drop with cards in hand | Increase the likelihood of spells, unaffordable plays, or missing-color requirements. | Confirm the land drop was available and useful. A deliberately held land remains possible. A spell-heavy hand need not contain interaction castable now. |
| Unprofitable-looking attack with open mana | Increase the likelihood of a trick or removal that converts blocks into value. | Calculate public activations first. Include attacks on planeswalkers, a race, bluffing, sacrifice value, and replacement threats as competing explanations. |
| Declining a comparable trade earlier | Give weight to preserving that creature or engine when ranking their next block. | Reassess life totals, combat stats, other blockers, and new cards. Earlier willingness to take damage supports a branch without guaranteeing it repeats. |
| Passing with mana open despite a development opportunity | Increase the likelihood of affordable instants, flash creatures, or reactive plans. | Check what could actually have been developed and whether cycling, preparation, or a mana sink explains the pass. Follow how the mana was eventually spent. |
| Passing a good removal opportunity | Reduce the likelihood of a usable answer to that target. Repeated clean opportunities can support a strong read. | Verify target legality, colors, timing, protection, the target's importance, and the benefit of acting then. Examine credible reasons to wait, such as a better target or holding up another response. |
| Using a removal spell earlier | Mark that copy spent and update remaining possibilities. | Check this game's history, possible additional copies, later draws, and available recursion. |
| Draws or selection after an earlier read | Reopen possibilities for the newly acquired cards. | Distinguish older held cards from new unknowns when the evidence supports it; avoid erasing or extending the earlier read indiscriminately. |

Give missed removal opportunities real weight. If the opponent repeatedly had correct mana, a legal high-value target, and a compelling reason to act, describe the relevant answer as unlikely and consider exploiting that read. Scope the conclusion to "unlikely to hold a castable answer to this threat," rather than every possible removal card. Conversely, a merely plausible removal opportunity is weak evidence when waiting advances their plan. Check those reasons rather than automatically excusing every pass.

Use qualitative rankings unless a defensible model supports numbers. Repeated observations about the same held cards are correlated evidence, not independent probability multipliers. Separate a card's likelihood of being held from the likelihood they choose to use it in this branch.

For reads that affect the verdict, record a compact working entry: **turn/action → hand hypothesis → competing explanation → confidence → effect on our decision**. State explicitly when the history gives little basis to narrow the range. Complete the read when it supports the decision comparison, rather than enumerating every legal trick in the set.

## Preserve each player's information

Use our hand and public history for our decision. Model the opponent as knowing their own hand and interpreting our public actions; include what our open mana and attack suggest about a trick or bluff. Keep our unrevealed removal and plans out of their assumed knowledge.

When explaining the opponent's actual choice retrospectively, a later reveal can establish that a particular card was already in their hand only if reliable draw/zone/object evidence proves its earlier presence. Label that evidence as opponent-private information at the decision time. It may explain their choice without becoming knowledge our player could have used. An untraceable later reveal is insufficient to place the card in the earlier hand.

## Compare best responses under uncertainty

1. For each candidate line, use the same plausible opponent hand classes and comparable future developments. Start with the most credible classes from the history, then test a materially dangerous alternative.
2. From each class, identify the opponent's strongest sensible response given what they know. Include declining a block, chumping elsewhere, taking damage, a cheaper activation, preserving an answer, or accepting a trade to enable their next play. Keep our later choices available, including whether and how to spend a combat trick after blocks.
3. Rank branches by incentives and evidence: **likely**, **plausible alternative**, or **requires an opponent mistake**, with a reason. An unlikely mistake contributes little to the recommended line's value. Treat the opponent as capable without assuming perfect play or knowledge of our hidden hand.
4. Compare the resulting chance to execute a winning plan: clocks, surviving threats, protected activations, mana, useful cards, and recovery after interaction. Value a token by its stats, counters, readiness, synergy, and replacement cost; value a spent spell's lost modes as well as its immediate effect.
5. Prefer the line with the stronger outcomes across the credible responses. State the main downside and which read would reverse the choice. If the ranking depends on unsupported hand frequencies, keep the verdict close or conditional. Avoid equating best-response analysis with playing around every imaginable card.

Recompute the opponent's choices whenever an alternative changes visible information. A counter that makes a trade unattractive can cause them to decline the block; the previous block is no longer a fixed outcome.

Account for selection in offered trades. An opponent may accept a creature-for-trick-and-token exchange chiefly when their hand contains a replacement threat or a payoff for consuming the trick. Evaluate that accepting hand class; the apparently favorable exchange is not a random sample of their range. A player can also block because they suspect a bluff even when the trick-resolves branch is unfavorable.

Practice cue: **What would make them choose this response, and does our line still work against that hand?**

## Deploying threats into removal or counterspells

Use the inferred hand range to compare deploying now, playing a different threat, holding up a response, and waiting for a specific later sequence. Name the exact payoff of waiting: protection mana, paying a tax counter, two useful spells in one turn, or an opponent's necessary tap-out. Charge the delay for lost attacks, blocks, engine activations, and opposing draws. Being ahead or holding a bomb does not by itself justify waiting; urgency can make exposure the best winning route.

Separate interaction by when it works and what survives:

| Response | Reconstruct |
| --- | --- |
| Counterspell | Verify spell type, mana-value restrictions, colored cost, and taxes or alternative payments. A countered creature supplies no entry trigger, though applicable cast triggers can remain. |
| Removal after resolution | Resolve entry/cast triggers and independent tokens under the actual rules. Count value already gained, what can still block or attack, and whether a response or activation is affordable. |
| Bounce, exile, or disabling effect | Price the affected token or permanent, replay cost, lost counters/abilities, and the zones from which available recursion can recover it. |
| No answer, or the opponent saves it | Retain the threat's actual clock and engine payoff. Let the opponent ignore bait, use a cheaper answer, or answer the second spell instead. |

Enumerate all opposing payment resources before calling a window safe. Rank the credible answer classes from earlier opportunities, mana held open, cards spent, and subsequent draws. A resolved earlier threat is weak evidence against a counter that cannot legally hit it. Conversely, repeated passed opportunities against comparable important threats can justify deploying into nominally open mana.

For a double-spell or bait line, pay both spells and any protection in the correct colors. Compare outcomes when either threat is answered and when the opponent declines the bait. Choose a lead spell that remains useful in those branches; explain why any tempo sacrificed improves the resulting board. Protection for a permanent on the battlefield generally does not answer a counterspell targeting the creature spell.

Carry each retained line through the opponent's next turn and our next conversion of resources into pressure or value. Include the replacement threat or recursion actually available. Judge a threat that dies by the exchange and follow-up, rather than its death alone. State the read or timing change that would reverse the recommendation.

Practice cue: **What do I gain if this resolves, what remains if they answer it, and what improves if I wait?**
