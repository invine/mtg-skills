#!/usr/bin/env python3
"""Bounded Limited arithmetic from explicit JSON assumptions; no card-text or strategy inference."""
import argparse
import itertools
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path


class Unsupported(ValueError):
    pass


def integer(value, name, minimum=0, maximum=1000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer between {minimum} and {maximum}")
    return value


def keys(data, allowed):
    unknown = set(data) - set(allowed)
    if unknown:
        raise Unsupported(f"Unsupported fields: {sorted(unknown)}")


def draw_probability(data):
    keys(data, {"kind", "model", "draws", "groups", "minimum"})
    if data.get("model") != "uniform_without_replacement":
        raise Unsupported("Specify uniform_without_replacement; Arena smoothing and mulligan policies are not modeled")
    groups, required = data["groups"], data["minimum"]
    if not groups or len(groups) > 16 or not required or len(required) > 8:
        raise Unsupported("Use 1–16 disjoint card groups and 1–8 required tags")
    for group in groups:
        keys(group, {"count", "tags"})
        integer(group["count"], "group count", 1, 250)
        if not isinstance(group["tags"], list) or any(not isinstance(t, str) for t in group["tags"]):
            raise ValueError("Each group needs string tags; put a dual source in one group with both tags")
    required = {k: integer(v, "required count", 0, 250) for k, v in required.items()}
    total = sum(g["count"] for g in groups)
    draws = integer(data["draws"], "draws", 0, min(total, 250))
    tags = sorted(required)
    # Counts of combinations, compressed by draws and capped goal counts.
    states = {(0, (0,) * len(tags)): 1}
    for group in groups:
        updated = {}
        for (seen, counts), ways in states.items():
            for take in range(min(group["count"], draws - seen) + 1):
                reached = tuple(min(required[t], counts[i] + (take if t in group["tags"] else 0))
                                for i, t in enumerate(tags))
                key = (seen + take, reached)
                updated[key] = updated.get(key, 0) + ways * math.comb(group["count"], take)
        if len(updated) > 200000:
            raise Unsupported("Probability state limit exceeded; simplify the groups/requirements")
        states = updated
    successes = states.get((draws, tuple(required[t] for t in tags)), 0)
    probability = Fraction(successes, math.comb(total, draws))
    return {"status": "calculated", "fraction": str(probability), "probability": float(probability),
            "population": total, "draws": draws, "model": data["model"],
            "interpretation": "Cards seen, not spell castability or a keep verdict."}


def parse_cost(cost):
    if not isinstance(cost, str):
        raise ValueError("Cost must use brace symbols, for example {1}{W}")
    symbols = re.findall(r"\{([^{}]+)\}", cost)
    if "".join("{" + s + "}" for s in symbols) != cost:
        raise ValueError("Malformed mana cost")
    generic, colored = 0, []
    for symbol in symbols:
        if symbol.isdigit():
            generic += int(symbol)
        elif re.fullmatch(r"[WUBRGC](?:/[WUBRG])?", symbol):
            colored.append(set(symbol.split("/")))
        else:
            raise Unsupported("Resolve X/Phyrexian/snow/alternative costs explicitly before calculating")
    return generic, colored


def mana_sequence(data):
    keys(data, {"kind", "assumptions_verified", "sources", "floating", "steps"})
    if data.get("assumptions_verified") is not True:
        raise Unsupported("Verify source restrictions, readiness, and effective costs for one priority window first")
    sources, steps = data["sources"], data["steps"]
    if len(sources) > 20 or not 1 <= len(steps) <= 10:
        raise Unsupported("Supports up to 20 one-mana sources and 1–10 actions")
    slots, ready = {}, set()
    for source in sources:
        keys(source, {"id", "produces", "ready"})
        sid, options = source["id"], source["produces"]
        if not isinstance(sid, str) or not sid or sid.startswith("floating:") or sid in slots:
            raise ValueError("Source IDs must be distinct nonempty strings, excluding floating:")
        if not isinstance(options, list) or not options or any(c not in "WUBRGC" or len(c) != 1 for c in options):
            raise Unsupported("Each source produces one mana of one listed color; normalize other abilities separately")
        if type(source["ready"]) is not bool:
            raise ValueError("Source readiness must be verified true/false")
        slots[sid] = options
        if source["ready"]:
            ready.add(sid)
    for i, color in enumerate(data.get("floating", [])):
        if color not in {"W", "U", "B", "R", "G", "C"}:
            raise ValueError("Unknown floating mana color")
        sid = f"floating:{i}"
        slots[sid], ready = [color], ready | {sid}
    if len(ready) > 24:
        raise Unsupported("At most 24 available mana units")
    parsed = []
    for step in steps:
        keys(step, {"cost", "tap_sources"})
        taps = step.get("tap_sources", [])
        if not isinstance(taps, list) or len(set(taps)) != len(taps) or any(t not in slots or t.startswith("floating:") for t in taps):
            raise ValueError("tap_sources must name distinct existing physical sources")
        parsed.append((*parse_cost(step["cost"]), set(taps)))
    visits = 0
    failed = set()

    def charge():
        nonlocal visits
        visits += 1
        if visits > 100000:
            raise Unsupported("Mana search limit reached; reduce sources or split the comparison")

    def payments(available, requirements, generic, chosen=()):
        charge()
        if len(available) < len(requirements) + generic:
            return
        if requirements:
            colors = requirements[0]
            for sid in sorted(available):
                options = colors & set(slots[sid])
                if options:
                    color = sorted(options)[0]
                    yield from payments(available - {sid}, requirements[1:], generic, chosen + ((sid, color),))
        else:
            for ids in itertools.combinations(sorted(available), generic):
                yield chosen + tuple((sid, slots[sid][0]) for sid in ids)

    def search(index, available):
        charge()
        if index == len(parsed):
            return [], available
        state = (index, tuple(sorted(available)))
        if state in failed:
            return None
        generic, colored, tapped = parsed[index]
        if tapped <= available:
            for payment in payments(available - tapped, colored, generic):
                result = search(index + 1, available - tapped - {sid for sid, _ in payment})
                if result is not None:
                    later, remaining = result
                    return [{"step": index + 1, "mana": [{"source": sid, "color": color} for sid, color in payment],
                             "tapped_for_activation": sorted(tapped)}] + later, remaining
        failed.add(state)
        return None

    result = search(0, ready)
    return {"status": "calculated", "feasible": result is not None,
            "payments": result[0] if result else [], "remaining": sorted(result[1]) if result else [],
            "interpretation": "Mana accounting for verified effective costs and one-mana sources in one window; other legality and strategy remain external."}


def combat_damage(data):
    keys(data, {"kind", "declarations_verified", "attackers", "blockers", "blocks"})
    if data.get("declarations_verified") is not True:
        raise Unsupported("Verify declarations, actual stats and absence of other damage modifiers/triggers first")
    attackers, blockers, blocks = data["attackers"], data["blockers"], data["blocks"]
    supported = {"flying", "reach", "vigilance", "haste", "trample", "deathtouch", "lifelink", "indestructible"}
    creatures = {}
    for creature in attackers + blockers:
        keys(creature, {"id", "power", "toughness", "damage", "keywords", "target", "blocked"})
        cid = creature["id"]
        if not isinstance(cid, str) or not cid or cid in creatures:
            raise ValueError("Creature IDs must be unique nonempty strings")
        for field, minimum in (("power", -1000), ("toughness", 1), ("damage", 0)):
            integer(creature.get(field, 0), field, minimum)
        keywords = set(creature.get("keywords", []))
        if keywords - supported:
            raise Unsupported(f"Unsupported combat mechanics: {sorted(keywords - supported)}")
        if "blocked" in creature and type(creature["blocked"]) is not bool:
            raise ValueError("blocked must be true/false")
        if not isinstance(creature.get("target", "opponent"), str):
            raise ValueError("Attack target must be a string ID")
        creatures[cid] = creature
    attack_ids, block_ids = {a["id"] for a in attackers}, {b["id"] for b in blockers}
    used = []
    for aid, bids in blocks.items():
        if aid not in attack_ids or not isinstance(bids, list) or any(b not in block_ids for b in bids):
            raise ValueError("Blocks must connect known attackers and blockers")
        if len(bids) > 1:
            raise Unsupported("Multiple blockers require explicit damage allocation; this calculator supports one per attacker")
        used.extend(bids)
    if len(used) != len(set(used)):
        raise Unsupported("A blocker assigned to multiple attackers is unsupported")
    damage, deathtouch, targets, life = {c: 0 for c in creatures}, set(), {}, {"attacking": 0, "defending": 0}
    for attacker in attackers:
        aid = attacker["id"]
        target = attacker.get("target", "opponent")
        targets.setdefault(target, 0)
        ak = set(attacker.get("keywords", []))
        power = max(0, attacker["power"])
        bids = blocks.get(aid, [])
        through = 0
        if bids:
            blocker = creatures[bids[0]]
            bid, bk = blocker["id"], set(blocker.get("keywords", []))
            if "flying" in ak and not bk & {"flying", "reach"}:
                raise ValueError("This blocker cannot block flying under the supplied mechanics")
            lethal = 1 if "deathtouch" in ak else max(0, blocker["toughness"] - blocker.get("damage", 0))
            dealt = min(power, lethal) if "trample" in ak else power
            damage[bid] += dealt
            damage[aid] += max(0, blocker["power"])
            if "deathtouch" in ak and dealt:
                deathtouch.add(bid)
            if "deathtouch" in bk and blocker["power"] > 0:
                deathtouch.add(aid)
            if "lifelink" in bk:
                life["defending"] += max(0, blocker["power"])
            if "trample" in ak:
                through = power - dealt
        elif not attacker.get("blocked") or "trample" in ak:
            through = power
        targets[target] += through
        if "lifelink" in ak and (bids or through):
            life["attacking"] += power
    dead = [cid for cid, creature in creatures.items() if "indestructible" not in creature.get("keywords", []) and
            (damage[cid] + creature.get("damage", 0) >= creature["toughness"] or cid in deathtouch)]
    return {"status": "calculated", "damage_to_targets": targets, "damage_to_creatures": damage,
            "dead": sorted(dead), "survivors": sorted(set(creatures) - set(dead)), "life_gained": life,
            "interpretation": "One normal simultaneous damage step, at most one blocker per attacker, no other modifiers or triggers. Trample assigns minimum lethal to its blocker."}


def calculate(data):
    try:
        if not isinstance(data, dict):
            raise ValueError("Input must be an object")
        if data.get("kind") == "draw":
            return draw_probability(data)
        if data.get("kind") == "mana":
            return mana_sequence(data)
        if data.get("kind") == "combat":
            return combat_damage(data)
        raise Unsupported("Supported kinds: draw, mana, combat")
    except Unsupported as exc:
        return {"status": "unsupported", "reason": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file, or - for stdin")
    args = parser.parse_args()
    try:
        data = json.loads(sys.stdin.read() if args.input == "-" else Path(args.input).read_text())
        result = calculate(data)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "calculated" else 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"status": "invalid_input", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
