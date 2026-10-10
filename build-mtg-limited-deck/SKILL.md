---
name: build-mtg-limited-deck
description: Build MTG Limited decks from pools or 17Lands links; compare builds, evaluate splashes and card swaps, tune mana bases, and explain mulligans, mana use, and threat deployment.
---

# MTG Limited Deck Builder

Choose the strongest coherent deck available in the actual pool. Optimize expected game performance, including consistency and realistic play patterns. Treat explicit requirements to play a card as constraints; treat questions about a card as requests to evaluate it. Recommend against a proposed inclusion when the deck is stronger without it.

For follow-ups, reuse the verified pool, card text, and current list. Track accepted swaps from the last complete build. After several swaps, or one that changes the plan or mana requirements, reassess the whole resulting deck before recommending another change. Give the updated full list when requested or materially changed.

## 1. Establish the pool

Read the supplied pool, deck export, screenshots, or 17Lands page. For a 17Lands link, distinguish the complete pool from a saved deck and its sideboard; use event metadata to establish Draft/Sealed, format, and best-of-one/three. Use available public exports or page data when the rendered page is incomplete. If retrieval fails, identify the missing information and request an export while completing any analysis the available data supports.

Inventory exact card names and quantities, nonbasic lands, and permitted basics. Verify decision-relevant card text using Scryfall or official card/rules sources, including costs, both faces, prepared spells, activated abilities, and digital/rebalanced versions. Resolve the actual printing before relying on a familiar name. Derive playable colors from costs and abilities: color identity alone can include an optional off-color ability.

**Complete when:** the available copies and format are established; every card or interaction that could change the build is verified or explicitly marked unresolved. Keep recommendations provisional where unresolved text matters.

## 2. Compare coherent candidates

Identify the strongest plausible plans, usually two or three candidates: different base colors, a splash versus two colors, or an aggressive versus a more resource-intensive version. For each, identify:

- How it establishes a board and wins; what role it takes against faster and slower opponents.
- Threat density, meaningful early plays, evasion, interaction, card flow, engines, and mana sinks.
- Which resource is scarce and which draws fail: missing colors, too many expensive cards, removal without threats, or payoffs without enablers.

Read [decision-framework.md](references/decision-framework.md) when assessing strategic axes, resource dependencies, a splash, recursion, a synergy package, combat-dependent value, or cumulative swaps. Compare packages by their floor, normal outcome, ceiling, setup frequency, and displaced cards. Count only support present in this pool.

Use current format statistics only as supporting evidence. State the relevant population and sample limitations when stats drive a close choice; card win rates alone do not establish the best fit in this deck.

**Complete when:** one candidate leads for explicit reasons and the closest alternative has a concrete advantage, cost, and condition that would reverse the choice. A disputed synergy's payoff is feasible at the proposed mana and timing, with its setup exposure accounted for. For a narrow swap request, compare the affected versions rather than rebuilding unrelated options.

## 3. Build and audit the mana base

Build the full list before declaring a splash worthwhile. Count actual sources by color and availability turn, separating unconditional lands from delayed or conditional access. Read the mana section of [decision-framework.md](references/decision-framework.md) for splash or fixing decisions.

Match early requirements and double pips to the mana base; distinguish a late splash from an on-curve requirement. Account for tapped lands, utility lands, landcycling costs, ramp prerequisites, and competition between fixing and board development. Price mana failures against the splash's incremental value over the best replacement.

For each complete candidate, read [opening-and-deployment.md](references/opening-and-deployment.md). Test representative opening hands and useful spending sequences through the early turns and first expensive payoff. Include development with interaction available and the position after a key threat is answered. For a narrow swap, repeat only the tests that the change affects.

Choose the land count from the curve, sinks, card flow, and format. Start from 17 as a comparison point; justify moving to 16 or 18. Include all basics and nonbasics in the final count. Quantify draw probabilities only with an explicit model, keeping land draws, colored access, and castability distinct.

Before presenting a complete build or revised list, run `scripts/audit_deck.py` using the verified inventory. Read [deck-audit.md](references/deck-audit.md) for its input contract. Resolve count, copy-limit, and land-classification issues; use its delta to confirm that only the intended changes were made. Evaluate colored access separately from these mechanical counts.

**Complete when:** the mana supports the intended early turns and splash timing at an acknowledged cost; representative hands have a keep/mulligan rationale and a feasible spending plan; the audited list totals 40 cards and every nonbasic card is within the pool's copy count. Use a different size only when the user or format requires it and explain why. If the helper cannot run, perform and label the same checks manually.

## 4. Explain the deck as a plan

Lead with the chosen colors, role, and decisive reason. Provide:

1. The complete list with quantities, separated into nonlands and lands, with totals; use an importable text block when useful.
2. The mana source counts and the important tradeoff behind the split.
3. Typical early turns, the midgame transition, how to finish through a stalled board, and concrete keep/mulligan examples with a bottom-card plan when relevant.
4. The decision-relevant strategic axes from the framework, tied to actual cards and matchups.
5. The closest cuts or substitutions and what would make them preferable; include sideboarding when the format or request calls for it.

Explain why each contested card advances the plan. Give concrete common lines for a card the user questions, including the likely opposing response and what remains if the key interaction is disrupted. Preserve requested inclusions in the constrained build; label any stronger unconstrained alternative separately. Prefer a decisive recommendation with bounded uncertainty over a menu of unranked decks.

Explain when to deploy the main threats, when to reserve interaction, and when mana sinks or draw should use the remaining mana. Ground removal and counterspell considerations in verified format options and actual costs; use the game-review skill for reads from a particular opponent's history.

**Complete when:** the answer contains the verified playable list, its winning route and common failure modes, and concrete reasons for the important inclusions and exclusions.
