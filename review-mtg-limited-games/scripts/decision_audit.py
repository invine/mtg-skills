"""Point-in-time review contracts. Calculations are checked; strategic completeness is not proved."""
import copy
import hashlib
import json

from limited_math import calculate

FACETS = {
    "opening": ("opening",),
    "turn_cycle": ("lethal", "development", "land", "targets", "combat", "interaction"),
    "combat": ("lethal", "targets", "combat", "interaction"),
    "position": ("lethal", "development", "land", "targets", "combat", "interaction"),
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def snapshot(state, seat):
    """Project only the reconstructed decision state, never a report's later events/results."""
    known = [c for c in state.get("hand_knowledge", {}).get(str(seat), [])
             if c.get("learned_event", state["event"]) <= state["event"]]
    zones = {zone: copy.deepcopy(state.get("zones", {}).get(zone, []))
             for zone in ("Battlefield", "Stack", "Graveyard", "Exile", "Command")}
    zones["Hand"] = [copy.deepcopy(c) for c in state.get("zones", {}).get("Hand", []) if c.get("owner") == seat]
    return {"event": state["event"], "seat": seat, "turn": copy.deepcopy(state["turn"]),
            "players": copy.deepcopy(state.get("players", {})), "zones": zones,
            "library_counts": copy.deepcopy(state.get("library_counts", {})),
            "known_opponent_hand": [copy.deepcopy(c) for c in known if c.get("owner") != seat],
            "hand_count": len(state.get("zones", {}).get("Hand", [])),
            "boundary": "Only this reconstructed state and previously established public knowledge. Future draws, hidden identities and game outcome are excluded."}


def objects(view):
    return {str(c["instance_id"]): c for cards in view["zones"].values() for c in cards if "instance_id" in c}


def decision_template(game, kind, point, view):
    if kind not in set().union(*map(set, FACETS.values())):
        raise ValueError("Unknown decision kind")
    return {"id": f"g{game}:e{view['event']}:{kind}", "game": game, "kind": kind,
            "state_event": view["event"], "context": point, "snapshot_sha256": fingerprint(view),
            "status": "unreviewed", "basis": [], "candidates": [], "selected": None,
            "actual": {}, "note": ""}


def calculation_ids(data):
    kind = data.get("kind")
    ids = set()
    for field in ({"combat": ("attackers", "blockers"), "mana": ("sources",),
                   "lethal": ("attackers", "blockers", "sources", "effects"),
                   "land_options": ("sources", "lands", "interaction")}.get(kind, ())):
        ids.update(c["id"] for c in data.get(field, []))
    if kind in {"combat", "lethal"}:
        ids.update(c["target"] for c in data.get("attackers", []) if c.get("target", "opponent") != "opponent")
    return ids


def validate_decision(record, report, state, point, position_only=False):
    errors, rid = [], record.get("id", "decision")

    def fail(message):
        errors.append(f"{rid}: {message}")

    view = snapshot(state, report["seat_id"])
    available = objects(view)
    own = {cid for cid, c in available.items() if c.get("controller", c.get("owner")) == report["seat_id"]}
    if record.get("context") != point or record.get("snapshot_sha256") != fingerprint(view):
        fail("before-action context or snapshot is stale")
    event = state["event"]
    choice, end = record.get("choice_event"), record.get("window_end_event")
    if not ((position_only and choice is None and end is None) or (type(choice) is int and event < choice < report["event_count"]) or
            (choice is None and type(end) is int and event <= end < report["event_count"])):
        fail("identify the later action or passed-window end")
    status = record.get("status")
    if status not in {"reviewed", "not_applicable", "insufficient_evidence"} or not str(record.get("note", "")).strip():
        fail("record a decision-specific status and judgment")
    if status == "insufficient_evidence":
        if not record.get("missing") or not record.get("impact"):
            fail("unresolved decision needs missing fact and effect on the verdict")
        return errors
    basis = record.get("basis", [])
    if not basis:
        fail("cite at least one exact state fact supporting this decision")
    for fact in basis:
        obj = (view["turn"] if fact.get("id") == "turn" else
               view["players"].get(fact.get("id", "").removeprefix("player:")) if
               fact.get("id", "").startswith("player:") else available.get(fact.get("id")))
        if obj is None or fact.get("field") not in obj or obj[fact["field"]] != fact.get("value"):
            fail("basis fact does not match the before-action state")
    if status == "not_applicable":
        return errors
    candidates = record.get("candidates", [])
    if len(candidates) < 2 or len({c.get("id") for c in candidates}) != len(candidates):
        fail("compare at least two distinct candidates, including pass/hold or an attack subset where relevant")
    if record.get("selected") not in {c.get("id") for c in candidates}:
        fail("select a candidate before comparing the actual line")
    actual = record.get("actual", {})
    if actual.get("status") == "not_supplied":
        if not position_only:
            fail("missing actual play is allowed only for a position-only recommendation")
    elif not all(actual.get(k) for k in ("line", "comparison")):
        fail("separately record actual play and comparison (or not_supplied for a position-only question)")
    required = {"lethal": {"lethal", "combat"}, "combat": {"combat", "lethal"},
                "land": {"land_options", "mana"}, "interaction": {"land_options", "mana"}}
    kinds = set()
    for candidate in candidates:
        cid = candidate.get("id", "candidate")
        if candidate.get("information") != "known_at_snapshot":
            fail(f"{cid}: baseline must use information known at this snapshot; branch after unknown draws")
        if not candidate.get("line") or not candidate.get("tradeoff") or not isinstance(candidate.get("actions"), list):
            fail(f"{cid}: needs a line, sourced actions (empty for pass) and tradeoff")
        for action in candidate.get("actions", []):
            if action.get("source") not in own or not action.get("action"):
                fail(f"{cid}: action uses an unavailable resource or lacks its action")
        after = candidate.get("next_opponent_turn", {})
        if not after.get("assessment"):
            fail(f"{cid}: evaluate resources and exposure through the next opponent turn")
        for field in ("untapped_sources", "held_interaction", "exposed"):
            if not isinstance(after.get(field), list) or any(i not in own for i in after.get(field, [])):
                fail(f"{cid}: {field} must identify known resources (use a new snapshot for a drawn card)")
        for calc in candidate.get("calculations", []):
            try:
                data = calc["input"]
                result = calculate(data)
                kinds.add(data.get("kind"))
                if calc.get("result") != result:
                    fail(f"{cid}: calculation result differs from recomputation")
                bindings = calc.get("bindings", {})
                if set(bindings) != calculation_ids(data) or any(v not in available for v in bindings.values()):
                    fail(f"{cid}: bind every calculator entity to an object at this snapshot")
                if result["status"] == "unsupported":
                    manual = calc.get("manual", {})
                    if not all(manual.get(k) for k in ("assumptions", "steps", "result", "conclusion")) or not isinstance(manual.get("uncertainties"), list):
                        fail(f"{cid}: unsupported calculation requires explicit manual steps, result and uncertainties")
                    if manual.get("applies_to") in required.get(record["kind"], set()):
                        kinds.add(manual["applies_to"])
            except (ValueError, TypeError, KeyError) as exc:
                fail(f"{cid}: invalid calculation: {exc}")
    if record["kind"] in required and not kinds & required[record["kind"]]:
        fail("this decision needs a supported calculation or documented unsupported/manual escalation")
    return errors


def validate_coverage(check, decisions, report, states):
    """Coverage is a set of independently evaluated facets, not a note or a finding count."""
    required = set(FACETS.get(check["kind"], ()))
    if not required:
        return []
    errors, linked = [], []
    refs = check.get("decision_ids", [])
    if len(set(refs)) != len(refs):
        errors.append(f"{check['id']}: duplicate decision reference")
    for rid in refs:
        record = decisions.get(rid)
        if not record or record.get("game") != check["game"]:
            errors.append(f"{check['id']}: missing or wrong-game decision {rid}")
            continue
        state = states.get((record["game"], record["state_event"]))
        event = record["state_event"]
        if check["kind"] in {"opening", "position"}:
            valid = event == check["event"]
        elif check["kind"] == "turn_cycle":
            cycle = next(c for c in report["turn_cycles"] if c["start_event"] == check["event"])
            valid = cycle["start_event"] <= event <= cycle["end_event"]
        else:
            combat = next(c for c in report["combats"] if c["start_event"] == check["event"])
            valid = bool(state) and state["turn"].get("turnNumber") == combat["global_turn"]
        if not valid:
            errors.append(f"{check['id']}: decision {rid} is outside this coverage window")
        linked.append(record)
    missing = required - {r["kind"] for r in linked}
    if missing:
        errors.append(f"{check['id']}: missing independent decisions: {', '.join(sorted(missing))}")
    if check.get("status") == "reviewed" and any(r.get("status") not in {"reviewed", "not_applicable"} for r in linked):
        errors.append(f"{check['id']}: unresolved decisions cannot mark the window reviewed")
    return errors
