---
name: review-mtg-limited-games
description: Review MTG Limited games from 17Lands histories, replays, logs, screenshots, or described positions. Assess mulligans, mana use, threat deployment, combat, and deck execution without hindsight.
---

# MTG Limited Game Review

Find decisions that plausibly improve the player's chance to win, prioritizing strategic judgment over a catalogue of mechanical errors. Evaluate the choice using information available at the time. Treat wins as reviewable and losses as compatible with good decisions.

## 1. Establish the evidence

Read the actual played list and game history. Track deck changes by game, format, play/draw, mulligans, and results. Separate the original pool, a recommended build, and the version actually played. For 17Lands or raw Arena data, read [17lands-replays.md](references/17lands-replays.md) before retrieval or reconstruction; it covers evidence reuse, coverage, and cast confirmation.

For an automated cast timeline or a suspected canceled cast, use `scripts/cast_evidence.py` as described in [cast-evidence.md](references/cast-evidence.md). If execution is unavailable, apply its evidence categories manually and label unresolved attempts.

Review all games requested, including wins. If only a position or subset is available, state that scope. Verify exact card versions and all decision-relevant rules using Savecraft, Scryfall or official sources, including prepared spells, activated costs, protection, alternative mana, tokens, and repeated triggered abilities.

Describe the deck's expected route to winning and its scarce resources. Use prior build analysis if available, checking it against the played list.

**Complete when:** each reviewed game is mapped to the correct deck and result, available history coverage is known, and the intended game plan is explicit.

## 2. Reconstruct before judging

For a full-game review, read [opening-and-mana.md](references/opening-and-mana.md). Review every available mulligan/keep and bottom decision, then audit mana use across every turn, including the opponent-turn windows before the next untap. For a single position, apply only the relevant checks. Keep the coverage ledger compact and develop only material findings in the answer.

For each potentially material decision, capture the state immediately before the action:

- Both life totals; creatures and other permanents, actual stats, counters, damage, tapped status, summoning sickness, and planeswalker loyalty.
- Available mana of every color, nonland mana sources, floating mana, land drop, and activation resources.
- Own hand, relevant graveyard/exile/prepared resources, and remaining deck possibilities.
- Opponent hand count and public knowledge, revealed abilities, prior actions, and the current phase, priority, or committed combat state.

Label facts, inferences, and unknowns. Keep later draws and revealed cards outside the information available to the decision-maker; they may illustrate the actual result separately. Read the relevant section of [strategic-patterns.md](references/strategic-patterns.md) for interaction resolution, combat audits, multi-action sequences, expiring removal windows, removal versus trades, development versus value, hidden interaction, concessions, or a challenged finding.

Before evaluating a material attack, block, bait, or threat deployment, read [opponent-model.md](references/opponent-model.md). Use its hand-inference procedure to rank the opponent's plausible holdings from earlier turns and update the read for subsequent draws. For threats facing possible removal or counterspells, apply its deployment comparison, including the cost of waiting.

**Complete when:** each available opening decision and turn's mana use has been considered; the actual line and proposed alternatives are legal; opponent reads that could change the verdict have evidence and stated uncertainty. If a missing fact could reverse the evaluation, present conditional branches or leave the decision unresolved.

## 3. Compare winning routes

Identify who benefits from time and which resource currently limits winning: threats, answers, cards, mana, life, or an attack window. Compare the played line with the strongest plausible alternative, including the opponent's sensible responses and the following turn.

For a combat review, audit attacks and blocks across every requested game, including passed attacks and wins. Check attacker selection, attack targets, creatures reserved to block, and the necessity of offered trades. Use the combat and clock procedures in [strategic-patterns.md](references/strategic-patterns.md) to calculate damage through likely blocks and compare attacking now with waiting. Report only decisions whose alternatives materially change the winning route.

Apply the best-response procedure in [opponent-model.md](references/opponent-model.md) to each candidate line. Explain why an acceptable trade is better than waiting for the known follow-up before preferring it.

Execute each alternative action by action through the opponent's next turn. Update colored mana, land drops, activation availability, attackers and blockers, planeswalker exposure, triggers, and draw/mill/shuffle order after each action. Compare immediate damage, retained resources, engine development, vulnerability to interaction, and resulting clocks. Choose lines for their contribution to winning from this position. Abstract card advantage, mana efficiency, and the deck's archetype label are evidence, not verdicts.

For a survival or stabilization line, continue to the next meaningful attack or resource conversion: identify what can win, the required time and resources, and how the opponent can disrupt it. If the line only delays defeat, label it accordingly; weigh a riskier credible route to victory against that outcome.

Prioritize role assignment, preserving pressure, target and mode selection, trades, development versus removal, risk tolerance, mulligans, and timing of engines or finishers. Keep acknowledged sequencing mistakes brief unless their underlying strategic cause remains useful.

Classify each candidate finding as **clear error**, **preferred line**, **close choice**, **good play**, or **insufficient evidence**. Match confidence to legality, information quality, and how robust the advantage is across responses. Treat improved chances and a guaranteed win as separate claims. Use numerical win probabilities only when backed by an explicit defensible model.

**Complete when:** each retained criticism compares the played line with the strongest alternative, explains the alternative's advantage under credible responses, and states its downside, branch likelihood, and a condition that could reverse the preference. Support combat preferences with damage reaching the intended targets and the resulting board in the decisive branches. Claim a protected planeswalker, available counterspell, or improved clock only when the resulting resources support it. Drop criticisms that fail this comparison; zero strategic mistakes is a valid finding.

## 4. Separate deck behavior from pilot decisions

Compare observed games with the expected plan: early development, color access, pressure, removal use, card flow, and ability to finish. Distinguish a structural weakness repeated across plausible draws from a single flood, screw, bad matchup, or decision error. Report what a short run supports without treating its win record as proof of deck quality.

Separate uncastable hands or repeated curve gaps from choosing low-impact activations over useful spells. Credit deliberately reserved mana when the threatened response or end-step use justifies it. Check whether a threat's removal was an acceptable exchange or preventable exposure before attributing the loss to insufficient threat quality.

Recommend a deck change only when the evidence identifies a role or mana problem and the replacement is available in the pool. Otherwise frame it as a hypothesis to test. Keep the full rebuild separate unless the user requests one.

**Complete when:** deck construction, execution, and variance have distinct explanations supported by specific games.

## 5. Deliver actionable coaching

Lead with whether the deck played as expected and the most important strategic lesson. Give a compact per-game overview when reviewing a run, then develop the few decisions with the greatest impact or learning value.

For each developed finding provide: **game/turn and state → relevant opponent read → played line versus strongest alternative → likely response and meaningful downside → winning route → confidence → reusable cue**. Surface only the hand hypotheses and branches that affect the recommendation. Link the replay or source when available; distinguish your turn count from the replay's global turn count. Explain at least one meaningful good decision when supported by the games.

End with a small number of concrete habits to practice, such as counting remaining threats before trading or checking which player benefits from another untap. Answer the user's disputed point directly before broadening the review.

When challenged, reopen the card text and before-action state, test both lines, and state which conclusion survives and why. Explicitly withdraw an incorrect claim and retain supported ones. Carry accepted corrections forward so later summaries do not revive a disproven criticism.

**Complete when:** every criticism is traceable to a position and the user has a practical decision rule, not merely a result-based verdict.
