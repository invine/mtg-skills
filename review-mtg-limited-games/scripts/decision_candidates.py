"""Bounded candidate generation from verified normalized facts, never replay outcomes."""
import copy
import itertools

from limited_math import Unsupported, combat_damage, integer, keys, mana_sequence


def land_options(data):
    keys(data, {"kind", "assumptions_verified", "sources", "lands", "sequence", "interaction", "chosen"})
    if data.get("assumptions_verified") is not True:
        raise Unsupported("Verify unused land drop, legal land options, costs, and no mana/untap changes before the opponent window")
    if not 1 <= len(data["lands"]) <= 10 or len(data["interaction"]) > 10:
        raise Unsupported("Use 1–10 land choices and at most 10 interaction options")
    ids = [land["id"] for land in data["lands"]]
    if len(set(ids)) != len(ids) or data.get("chosen", ids[0]) not in ids:
        raise ValueError("Land IDs must be distinct; chosen must be a listed option")
    options = []
    for land in data["lands"]:
        base = {"kind": "mana", "assumptions_verified": True, "sources": data["sources"] + [land],
                "steps": data["sequence"] or [{"cost": "{0}"}]}
        result = mana_sequence(base)
        reserved = {}
        for spell in data["interaction"]:
            keys(spell, {"id", "cost"})
            if spell["id"] in reserved:
                raise ValueError("Interaction IDs must be distinct")
            reserved[spell["id"]] = mana_sequence({**base, "steps": base["steps"] + [{"cost": spell["cost"]}]})
        options.append({"land": land["id"], "sequence": result, "reserved": reserved,
                        "available_interaction": sorted(k for k, v in reserved.items() if v["feasible"])})
    chosen = next(o for o in options if o["land"] == data.get("chosen", ids[0]))
    gains = [{"land": o["land"], "adds": sorted(set(o["available_interaction"]) - set(chosen["available_interaction"]))}
             for o in options if o["sequence"]["feasible"] and
             set(o["available_interaction"]) > set(chosen["available_interaction"])]
    return {"status": "calculated", "options": options, "preserves_sequence_adds_interaction": gains,
            "interpretation": "Each response is separately affordable after the sequence, before our next untap; payment choices can differ between response branches. Verify the actual payment preserves the intended options. No floating mana crosses windows. Extra options flag a land comparison, not strategic dominance or a guaranteed legal target."}


def lethal_candidates(data):
    keys(data, {"kind", "assumptions_verified", "sources", "sequence", "attackers", "blockers", "effects", "life"})
    if data.get("assumptions_verified") is not True:
        raise Unsupported("Verify attack readiness, all legal blockers, effective pre-block effects/costs and no unmodeled triggers or responses")
    integer(data["life"], "opponent life", 1)
    attackers, blockers, effects = data["attackers"], data["blockers"], data.get("effects", [])
    if len(attackers) > 6 or len(blockers) > 5 or len(effects) > 4:
        raise Unsupported("Lethal search supports at most 6 attackers, 5 blockers and 4 independent effects")
    attack_ids = {a["id"] for a in attackers}
    if len({e["id"] for e in effects}) != len(effects):
        raise ValueError("Each resource/effect may appear only once; encode target choices under that effect")
    for effect in effects:
        keys(effect, {"id", "cost", "choices"})
        if not 1 <= len(effect["choices"]) <= 9:
            raise Unsupported("Use 1–9 alternative target choices per independently available effect")
        for choice in effect["choices"]:
            if not choice or len({d["target"] for d in choice}) != len(choice):
                raise ValueError("Each effect choice needs distinct target changes")
            for delta in choice:
                keys(delta, {"target", "power", "toughness", "keywords"})
                if delta["target"] not in attack_ids:
                    raise ValueError("Effect target is not a supplied attacker")
                integer(delta.get("power", 0), "power change", -1000)
                integer(delta.get("toughness", 0), "toughness change", -1000)
    # Validate all supplied mechanics, even branches not eventually chosen.
    combat_damage({"kind": "combat", "declarations_verified": True, "attackers": attackers,
                   "blockers": blockers, "blocks": {}})
    visits = 0
    for choices in itertools.product(*[[None] + list(range(len(e["choices"]))) for e in effects]):
        team = copy.deepcopy(attackers)
        by_id = {a["id"]: a for a in team}
        selected, steps = [], copy.deepcopy(data.get("sequence", []))
        for effect, choice in zip(effects, choices):
            if choice is None:
                continue
            selected.append({"effect": effect["id"], "choice": choice})
            steps.append({"cost": effect["cost"]})
            for delta in effect["choices"][choice]:
                creature = by_id[delta["target"]]
                creature["power"] += delta.get("power", 0)
                creature["toughness"] += delta.get("toughness", 0)
                creature["keywords"] = sorted(set(creature.get("keywords", [])) | set(delta.get("keywords", [])))
        payment = mana_sequence({"kind": "mana", "assumptions_verified": True, "sources": data["sources"],
                                 "steps": steps or [{"cost": "{0}"}]})
        if not payment["feasible"]:
            continue
        team = [a for a in team if a["toughness"] > 0]
        for size in range(1, len(team) + 1):
            for subset in itertools.combinations(team, size):
                options = [[None] + [a["id"] for a in subset if "flying" not in a.get("keywords", []) or
                           set(b.get("keywords", [])) & {"flying", "reach"}] for b in blockers]
                minimum, witness, witness_input = None, None, None
                for assignments in itertools.product(*options):
                    visits += 1
                    if visits > 50000:
                        raise Unsupported("Lethal search exceeded 50000 block branches; split effects/subsets and finish manually")
                    blocks = {}
                    for blocker, aid in zip(blockers, assignments):
                        if aid is not None:
                            blocks.setdefault(aid, []).append(blocker["id"])
                    branch = {"kind": "combat", "declarations_verified": True,
                              "attackers": list(subset), "blockers": blockers, "blocks": blocks}
                    result = combat_damage(branch)
                    damage = result["damage_to_targets"].get("opponent", 0) - result["life_gained"]["defending"]
                    if minimum is None or damage < minimum:
                        minimum, witness, witness_input = damage, result, branch
                    # One defending branch suffices to reject a guaranteed-lethal claim.
                    if damage < data["life"]:
                        break
                if minimum is not None and minimum >= data["life"]:
                    return {"status": "calculated", "lethal_found": True, "effects": selected,
                            "attackers": [a["id"] for a in subset], "minimum_net_damage": minimum,
                            "worst_block_input": witness_input, "worst_block_result": witness,
                            "payment": payment, "branches": visits,
                            "interpretation": "Lethal against all supplied legal block assignments under the fixed damage-allocation policy; verify hidden interaction, targets, triggers and effect normalization separately."}
    return {"status": "calculated", "lethal_found": False, "branches": visits,
            "interpretation": "No guaranteed lethal in supplied effects/subsets with this allocation policy. This does not rule out omitted abilities, other allocations, burn, removal or opponent mistakes."}
