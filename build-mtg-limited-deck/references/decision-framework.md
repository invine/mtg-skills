# Deck decisions

## Strategic axes

Use the axes that explain a choice. Describe positions qualitatively and connect each to cards or play patterns; invented numerical ratings imply precision the evidence cannot support.

| Axis | Question to answer | Practical consequence |
| --- | --- | --- |
| Aggro / midrange / control | Who must shorten the game in this matchup, and when does that change? | Mulligans, racing, and trading priorities. |
| Tempo / card advantage | Does the deck profit more from converting mana and initiative into damage, or from accumulating usable resources? | Develop, remove, draw, or hold up interaction. |
| Small game / big game | Does it prefer both players reduced to few resources, or a developed battlefield with engines and mana sinks? | Whether exchanges improve the future position. This is distinct from mana curve or creature size. |
| Wide / tall | Does it win through multiple bodies or a concentrated threat? | Removal exposure, combat tricks, and blocker management. |
| Ground / evasion / reach | Which route actually delivers the final damage? | Which opposing permanents deserve removal. |
| Proactive / reactive | Does it dictate problems or need to answer them? | Threat-to-answer ratio and timing. |
| Synergy / standalone power | How much setup makes the cards functional? | Enabler density, weak draws, and package size. |
| Inevitability / urgency | Who improves as turns pass, assuming plausible opposing draws? | Whether a risky attack is preferable to giving another turn. |
| Resilience / fragility | How well does it recover after interaction or a stalled attack? | Threat redundancy, recursion, selection, and exposure to a single answer. |
| Consistency / ceiling | How much reliability is spent on the strongest draws? | Splash, curve, and narrow synergy decisions. |

Treat the axes as related questions, not mutually exclusive deck labels. A midrange deck can prefer a small game; an aggressive deck can spend removal to preserve a wide board. Reassess its role from the actual hand and matchup.

## Resource dependencies

Count functional roles alongside card types. Separate lasting attackers and blockers from bodies that usually leave play, shuffle away, or must be spent to obtain their value. Record unconditional draw, conditional draw, and selection separately; a creature that draws cards after connecting may supply little lasting pressure.

Group cards by shared failure conditions: connecting in combat, retaining a creature, stocking the graveyard, finding a partner, or leaving mana unused. Several cards that all need a successful attack do not provide independent ways to recover from a stalled board. Compare what each version can do from an empty board, through blockers, and after its best threat is removed.

Count competing uses of the same resource. Two granted loyalty abilities on one planeswalker compete for its activation that turn; landcycling spends both development mana and a future spell. Name the resource spent before counting the payoff. Treat alternate modes as flexibility, rather than assuming all modes contribute in the same sequence.

Evaluate the next draw spell by what the deck lacks after existing card flow resolves. Reliable draw can repair dependence on connecting in combat; another value engine may instead displace the lasting body needed to attack, block, or exploit a team pump. Compare the contested cards' marginal contribution to a winning route, including how newly drawn cards become castable threats. Having enough draw is a reason to examine threat density, not an automatic verdict against further draw.

## Cumulative swaps

Compare the current full list with the last complete recommendation. Recount lasting threats, meaningful early plays, interaction, independent card flow, curve, and colored requirements after all accepted changes together. Explain whether the winning route and common failure modes have changed.

Reopen the closest complete alternative when the original recommendation's reason has weakened. For example, replacing early bodies with selection and adding a double-pip draw spell can change both the need for a splash and its mana cost. Rank the resulting decks, then retain or reverse earlier swaps as warranted. Distinguish an explicit inclusion constraint from a user asking whether an inclusion would improve the deck.

## Synergy and opportunity cost

For a disputed package, record the base rate without support, the ordinary supported outcome, and the ceiling. Identify the required cards, sequencing, mana, and earliest useful payoff turn. Compare against the best available replacement and include every supporting slot, turn of exposure, and development or interaction play displaced by setup. Evaluate the interrupted position if an enabler is answered before the payoff.

- **Tutors:** count relevant targets, their independent strength, the extra mana and turn spent, and what happens after drawing the only target naturally. One searchable card is access, not sufficient justification for the tutor.
- **Engines:** count actual enablers and payoffs, estimate how often the engine activates before the game is decided, and distinguish generating resources from converting them into a win. Include bodies reserved to protect a planeswalker and mana needed to restore its abilities. A deck's sole loyalty payoff may matter more than a superficially efficient standalone spell.
- **Recursion:** enumerate legal target roles, including lands, cheap blockers, and noncreature permanents when the text permits them. Count recovery plus deployment mana, graveyard setup, and life gained or end-step timing benefits. Compare these ordinary uses with recycling the best threat. Distinguish recasting from returning directly: verify cast-dependent entry triggers and access to previously exiled cards. Test a missed-land or pressured-board hand to establish whether recovery helps before the late game. Price additional copies by useful targets and affordable follow-ups; several recovery cards can compete for the same material and mana.
- **Conditional curves:** evaluate a turn-two enabler into a turn-three payoff as one draw pattern. Assess the cards when drawn in reverse order, late, or without their partner. Use explicit draw assumptions for any frequency estimate.
- **Marginal benefit:** when an effect upgrades bodies already obtainable, compare the incremental benefit against its total setup cost. Account separately for tutor flexibility or repeatability if those are real benefits.
- **Filtering:** value selection more when the deck floods, lacks draw, or needs particular threats. Separate filtering from net card advantage and include the tempo cost of using it.
- **Ramp:** identify which meaningful plays arrive a turn sooner and whether the ramp card contributes afterward. Price its actual drawback, lost board presence, and possible opponent benefit against those gains.
- **Team pumps and tokens:** count bodies likely to remain and be ready for the relevant attack. Include trades, sacrifice costs, defensive duties, and lost triggers when replacing a body with card flow. Count which blockers the pump beats and whether the attack advances lethal.
- **Combat tricks and bait:** test the opponent's sensible choices, including declining the offered trade, taking damage, or using a cheaper public ability. Value a trick by its useful outcomes across those responses and the opportunity cost of spending its other modes. A line that needs an unfavorable opposing block provides little support for an inclusion unless the bluff or pressure makes that block credible. For a specific replay, use the game-review skill to infer their hand from prior actions.

Example from the discussion: Pia finding only Way of the Deathbringer calls for evaluating both cards' ordinary performance and the search cost. A missing Empower Jace cannot support the evaluation. Rat into Way may be a useful line, but its existence does not establish the package's reliability. Re-read current card text before applying this example to another pool.

## Mana and splashes

Make a small source table when mana is contested:

| Source class | Record |
| --- | --- |
| Unconditional lands | Colors produced and whether available untapped on the needed turn. |
| Conditional lands | Entry conditions and how often the deck can meet them. |
| Fetching / landcycling | Activation cost, available targets, and the development turn spent. |
| Ramp / treasures / filters | Prerequisite colors, timing, survival or attack requirements, and one-shot versus repeatable access. |

Count a dual toward each color it can produce, while retaining the total number of physical sources: it cannot pay both colors simultaneously. Treat a fixer requiring green as dependent on first finding green. A two-mana landcycler may fix a late splash reliably while conflicting with a turn-two creature. An off-color basic displaces a main-color source even when the splash card is absent.

Classify land recovery as conditional access: it requires a legal land already in the graveyard, recovery mana, and a usable land drop. Include credible ways to stock that land and the development cost. Keep it separate from an unconditional land source when auditing opening colors or deciding the land count.

When comparing another basic with relying on landcycling, identify the exact cut and price the extra land's flood risk against saved setup mana, earlier colored access, and retaining the cycler as a spell. Treat a preference to cast the cycler as a real benefit to evaluate, while checking whether the resulting land count and sinks support it.

Evaluate the splash in four comparisons:

1. **Need:** when must the spell be cast, how many colored pips does it require, and is it still strong late?
2. **Access:** how many sources work by that turn, and at what setup cost?
3. **Damage:** which main-color plays become less reliable or slower?
4. **Reward:** how much does the splash improve the games where it is cast over the best on-color card?

Five nominal black sources are evidence to examine, not a universal verdict for splashing Garruk. High impact and late usefulness can justify costs; early double-pip demands can make the same mana base too expensive. Report the actual balance.

For simple draw calculations, state deck size, source count, cards seen, and play/draw assumptions. A hypergeometric chance of seeing a source is not the chance of casting a spell: total lands, entry timing, prerequisite colors, and setup mana still matter.
