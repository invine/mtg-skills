---
name: review-mtg-limited-games
description: Review MTG Limited games from 17Lands histories, replays, logs, screenshots, or described positions. Assess mulligans, mana use, threat deployment, combat, and deck execution without hindsight.
---

# MTG Limited Game Review

Find decisions that plausibly improve the player's chance to win, prioritizing strategic judgment over a catalogue of mechanical errors. Evaluate the choice using information available at the time. Treat wins as reviewable and losses as compatible with good decisions.

## 1. Establish the evidence

Read the actual played list and game history. Track deck changes by game, format, play/draw, mulligans, and results. Separate the original pool, a recommended build, and the version actually played. For 17Lands links, run the bundled Python extractor using [17lands-extractor.md](references/17lands-extractor.md), then inspect every game's coverage and unresolved cast evidence. Reuse its cache and targeted state queries for follow-ups. Read [17lands-replays.md](references/17lands-replays.md) for raw-log interpretation, unsupported schemas, and decision-link verification.

For an automated cast timeline or a suspected canceled cast, use `scripts/cast_evidence.py` as described in [cast-evidence.md](references/cast-evidence.md). If execution is unavailable, apply its evidence categories manually and label unresolved attempts.

After extraction, use [review-automation.md](references/review-automation.md) to initialize an unreviewed coverage ledger, query turn cycles and combat episodes, and reuse exact-printing card text. For source-only or screenshot reviews, keep the same coverage and evidence distinctions manually.

Review all games requested, including wins. If only a position or subset is available, state that scope. Verify exact card versions and all decision-relevant rules using Savecraft, Scryfall or official sources, including prepared spells, activated costs, protection, alternative mana, tokens, and repeated triggered abilities.

Describe the deck's expected route to winning and its scarce resources. Use prior build analysis if available, checking it against the played list.

**Complete when:** each reviewed game is mapped to the correct deck and result, available history coverage is known, and the intended game plan is explicit.

## 2. Freeze the information available at the decision

For a full-game review, read [opening-and-mana.md](references/opening-and-mana.md). Review every available mulligan/keep and bottom decision, then audit mana use across every turn, including the opponent-turn windows before the next untap. Audit both players' combat windows, including wins and passed attacks. For a single position, apply only the relevant checks. Keep the coverage ledger compact and develop only material findings in the answer.

Before inspecting a decision's result, use `review_tools.py snapshot` at the before-action event. Read [decision-audits.md](references/decision-audits.md) for the record format and candidate tools. Capture the following facts from the snapshot and supporting source evidence:

- Both life totals; creatures and other permanents, actual stats, counters, damage, tapped status, summoning sickness, and planeswalker loyalty.
- Available mana of every color, nonland mana sources, floating mana, land drop, and activation resources.
- Own hand, relevant graveyard/exile/prepared resources, and remaining deck possibilities.
- Opponent hand count and public knowledge, revealed abilities, prior actions, and the current phase, priority, or committed combat state.

Verify exact card text and restrictions before normalizing calculator inputs. Label facts, inferences, and unknowns.

Verify land-drop availability, used loyalty activations and existing preparation from source evidence; an omitted status is unknown, not available. When a correction moves an action earlier, reconstruct and link that earlier state. Keep it separate from moves still legal at the supplied position.

Construct baseline lines from resources in that snapshot. A draw, reveal, selection or search creates a new information boundary: retain the pre-draw plan, then evaluate the continuation from a new snapshot. Unknown cards can be discussed as conditional possibilities; they cannot fund the baseline. A useful engine counter may justify a setup line even if its actual draw was poor or an attack later failed.

Before evaluating a material attack, block, response to interaction, or threat deployment, read [opponent-model.md](references/opponent-model.md). Use its hand-inference procedure to rank plausible holdings from earlier turns and draws up to the decision. When interaction challenges known protection, apply **Challenges to known protection** before judging whether to respond. For threat deployment, apply the deployment comparison, including the cost of waiting.

For claims about a known hand, query the knowledge ledger at the before-action event and select the relevant viewer seat. Use the bounded calculators in [review-automation.md](references/review-automation.md#bounded-calculators) for repeated draw, colored-mana and damage arithmetic after verifying their inputs and supported mechanics.

**Complete when:** each available opening decision and turn's mana use has been considered; each decision has a reproducible before-action context; the actual line and proposed alternatives are legal; opponent reads that could change the verdict have evidence and stated uncertainty; and every continuation using newly learned information has its own boundary. If a missing fact could reverse the evaluation, present conditional branches or leave the decision unresolved and explain the effect.

## 3. Generate alternatives, then compare the played line

Identify who benefits from time and which resource currently limits winning: threats, answers, cards, mana, life, or an attack window. Before judging a consequential risk, apply [Risk when ahead or behind](references/strategic-patterns.md#risk-when-ahead-or-behind) to establish whether the current advantage is durable and what can reverse it. Compare the played line with the strongest plausible alternative, including the opponent's sensible responses and the following turn.

For each own turn or requested position, keep **lethal, development/spell order, land choice, targets/counters, combat, and reserved interaction** as separate decisions. For combat windows, cover lethal, targets, combat and interaction. One finding completes only its own decision. Share a decision record across overlapping windows when its source state and analysis cover both.

Evaluate candidates in this order, before explaining the actual outcome:

1. **Immediate win.** Test known evasion, pump, counter transfers, removal, burn and abilities before committing mana or attackers. Run the bounded lethal scan for supported effects; calculate unsupported routes manually. Consider smaller attack subsets and attacks at the opponent versus planeswalkers.
2. **Precombat development.** Compare the strongest materially different deployments already available, including cheaper combinations, engines, hasty threats, planeswalkers and holding mana. A different development line changes the combat input; calculate it separately.
3. **Targets and combat.** Compare counter/spell targets, partial attacks and no attack. Check creatures reserved to block and whether offered trades are necessary. For each serious line, test the opponent's strongest sensible response, including concentrated double/triple blocks, declining the trade, or preserving an engine. Resolve first strike, deaths, normal damage, target damage and survivors. Check the resulting crack-back and planeswalker exposure. Compare attacking now with waiting over the same relevant turns, using damage through credible blocks. Use the bounded combat calculator where supported.
4. **Land and opponent-turn resources.** Compare land options against both the chosen sequence and held responses before the next untap. Run the land-options calculator when color access differs. Finding a spell-order error does not resolve the independent land choice or whether removal stayed available.
5. **Actual play and strategic preference.** Compare the played line with the candidates just established. Record the advantage, retained resources, cost of waiting and condition that reverses the preference. Reopen the search if a user supplies a missed alternative.

Read the relevant procedure in [strategic-patterns.md](references/strategic-patterns.md) for multi-action sequences, combat/clock comparisons, interaction resolution, expiring answers, removal versus trades, value versus development, hidden interaction, concessions or a challenged finding. Apply the best-response procedure in [opponent-model.md](references/opponent-model.md) to each candidate line. Explain why an acceptable trade is better than waiting for the known follow-up before preferring it.

Execute each alternative action by action through the opponent's next turn. Update colored mana, land drops, activation availability, attackers and blockers, planeswalker exposure, triggers, and draw/mill/shuffle order after each action. Compare immediate damage, retained resources, engine development, vulnerability to interaction, and resulting clocks. Choose lines for their contribution to winning from this position. Abstract card advantage, mana efficiency, and the deck's archetype label are evidence, not verdicts.

For a survival or stabilization line, continue to the next meaningful attack or resource conversion: identify what can win, the required time and resources, and how the opponent can disrupt it. If the line only delays defeat, label it accordingly; weigh a riskier credible route to victory against that outcome.

Store candidate actions with source-object identities, checked calculation inputs/results, and resources/exposure through the next opponent turn. The validator recomputes supported arithmetic and rejects unavailable baseline resources. For unsupported mechanics retain the tool result and explicit manual steps; use `insufficient_evidence` when they cannot be resolved. Use `not_applicable` only with a state fact and a reason that this particular decision has no meaningful choice.

Prioritize role assignment, preserving pressure, target and mode selection, trades, development versus removal, risk tolerance, mulligans, and timing of engines or finishers. Report decisions whose alternatives materially change the winning route. Keep acknowledged sequencing mistakes brief unless their underlying strategic cause remains useful.

Classify findings as **clear error**, **preferred line**, **close choice**, **good play**, or **insufficient evidence**. Match confidence to legality, information quality, and how robust the advantage is across responses. Distinguish a defensible setup from a subsequent bad attack, an improved chance from a guaranteed win, and a close preference from a mistake. Numerical win probabilities require a defensible model.

**Complete when:** every required decision is independently accounted for, and later draws have not supplied baseline actions. Each retained criticism compares the played line with the strongest alternative, explains the alternative's advantage under credible responses, and states its downside, branch likelihood, and a condition that could reverse the preference. For a consequential risk, name the losing route it closes or the winning route it opens, including the cost of waiting. Support combat preferences with damage reaching the intended targets and the resulting board in the decisive branches. Claim a protected planeswalker, available counterspell, or improved clock only when the resulting resources support it. Drop criticisms that fail this comparison; zero strategic mistakes is a valid finding. A reviewed status or generic note alone cannot complete coverage.

## 4. Separate deck behavior from pilot decisions

Compare observed games with the expected plan: early development, color access, pressure, removal use, card flow, and ability to finish. Distinguish a structural weakness repeated across plausible draws from a single flood, screw, bad matchup, or decision error. Report what a short run supports without treating its win record as proof of deck quality.

Separate uncastable hands or repeated curve gaps from choosing low-impact activations over useful spells. Credit deliberately reserved mana when the threatened response or end-step use justifies it. Check whether a threat's removal was an acceptable exchange or preventable exposure before attributing the loss to insufficient threat quality.

Recommend a deck change only when the evidence identifies a role or mana problem and the replacement is available in the pool. Otherwise frame it as a hypothesis to test. Keep the full rebuild separate unless the user requests one.

**Complete when:** deck construction, execution, and variance have distinct explanations supported by specific games.

## 5. Deliver actionable coaching

Lead with whether the deck played as expected and the most important strategic lesson. Give a compact per-game overview when reviewing a run, then develop the few decisions with the greatest impact or learning value.

For each developed finding provide: **game/turn and state → relevant opponent read → played line versus strongest alternative → likely response and meaningful downside → winning route → confidence → reusable cue**. Surface only the hand hypotheses and branches that affect the recommendation. Distinguish your turn count from the replay's global turn count. Explain at least one meaningful good decision when supported by the games.

Attach a clickable link to the exact decision position beside every highlighted play, including good plays, mulligans, and plays mentioned in overview tables. Use a descriptive label such as “Game 2 — your turn 8, before combat.” A game-level link serves run navigation only; it does not satisfy this requirement. For replay links, follow [Decision links](references/17lands-replays.md#decision-links) to obtain and verify the position. When exact linking is unavailable after checking the source, state the limitation beside that finding and provide the closest source link plus a precise position locator and supporting snapshot or log excerpt. Keep this exception explicit rather than silently substituting a game link.

End with a small number of concrete habits to practice, such as counting remaining threats before trading or checking which player benefits from another untap. Answer the user's disputed point directly before broadening the review.

When challenged, reopen the card text and before-action state, test both lines, and state which conclusion survives and why. Explicitly withdraw an incorrect claim and retain supported ones. Carry accepted corrections forward so later summaries do not revive a disproven criticism.

Before delivering a 17Lands review, validate its coverage and finding ledger using [review-automation.md](references/review-automation.md#coverage-and-findings), then render highlighted plays from the verified entries. Resolve failures or retain explicit insufficient-evidence/link fallbacks. Validate assembled answer blocks when producing an answer file.

**Complete when:** every highlighted play has a verified decision-position link or the explicit unavailable-link fallback, each link identifies the state used in the analysis, and the user has a practical decision rule, not merely a result-based verdict.
