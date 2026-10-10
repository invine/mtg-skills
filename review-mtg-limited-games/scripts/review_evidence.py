"""Evidence ledgers. Observations and mechanical accounting, never strategic verdicts."""
import copy


class KnowledgeLedger:
    """Track justified identities per viewer, bounded by the replay player's information."""
    def __init__(self, replay_seat, cards):
        self.replay_seat, self.cards = replay_seat, cards
        self.known = {1: {}, 2: {}}
        self.events = []
        self.previous_hands = {1: {}, 2: {}}

    def observe(self, objects, zones, renames, index, observed_ids, gap=False):
        locations = {oid: zone["type"] for zone in zones.values()
                     for oid in zone.get("objectInstanceIds", []) if zone["type"] != "ZoneType_Limbo"}
        if gap:
            for viewer, entries in self.known.items():
                for oid, entry in entries.items():
                    self.events.append({**entry, "viewer": viewer, "instance_id": oid,
                                        "event": index, "kind": "tracking_lost", "reason": "state_gap"})
                entries.clear()
        for old, new in renames:
            for entries in self.known.values():
                if old in entries:
                    entries[new] = entries.pop(old)
        for viewer, entries in self.known.items():
            for oid in list(entries):
                obj = objects.get(oid, {})
                location = locations.get(oid)
                if location is None or (location == "ZoneType_Library" and
                                        obj.get("visibility") != "Visibility_Public"):
                    self.events.append({**entries.pop(oid), "viewer": viewer, "instance_id": oid,
                                        "event": index, "kind": "tracking_lost", "reason": "hidden_zone"})
            for oid, location in locations.items():
                if oid not in observed_ids:
                    continue
                obj = objects.get(oid, {})
                public = obj.get("visibility") == "Visibility_Public"
                viewers = obj.get("viewers", [])
                # Logs may contain private opponent IDs. They are not review evidence.
                permitted = public or self.replay_seat in viewers
                visible = public or viewer in viewers
                if not permitted or not visible or not obj.get("grpId") or location == "ZoneType_Library":
                    continue
                gid = obj["grpId"]
                if oid not in entries or entries[oid]["card_id"] != gid:
                    entries[oid] = {"card_id": gid, "name": self.cards.get(gid, {}).get("name", f"Card {gid}"),
                                    "owner": obj.get("ownerSeatId"), "learned_event": index,
                                    "reason": "public" if public else "explicit_viewer"}
                    self.events.append({**entries[oid], "viewer": viewer, "instance_id": oid,
                                        "event": index, "kind": "identity_seen"})
        for viewer, entries in self.known.items():
            current = {}
            for oid, entry in entries.items():
                if locations.get(oid) == "ZoneType_Hand":
                    if oid not in self.previous_hands[viewer] or "hand_entry_event" not in entry:
                        entry["hand_entry_event"] = index
                        self.events.append({**entry, "viewer": viewer, "instance_id": oid,
                                            "event": index, "kind": "known_hand_entry"})
                    current[oid] = copy.deepcopy(entry)
            for oid, entry in self.previous_hands[viewer].items():
                if oid not in current:
                    self.events.append({**entry, "viewer": viewer, "instance_id": oid,
                                        "event": index, "kind": "known_hand_exit"})
            self.previous_hands[viewer] = current

    def hands(self):
        return {str(viewer): [{**entry, "instance_id": oid} for oid, entry in sorted(entries.items())]
                for viewer, entries in self.previous_hands.items()}


def resources(snapshot, seat):
    sources = snapshot["mana_source_candidates"]
    return {"event": snapshot["event"], "turn": snapshot["turn"],
            "sources": [s for s in sources if s["controller"] == seat],
            "player": snapshot["players"].get(str(seat), snapshot["players"].get(seat, {})),
            "hand": [c for c in snapshot["zones"].get("Hand", []) if c["owner"] == seat]}


class CombatLedger:
    """Group combat windows by transitions, including extra combats in the same turn."""
    def __init__(self):
        self.episodes, self.current, self.previous = [], None, None

    def observe(self, snapshot, gap=False):
        turn = snapshot["turn"]
        in_combat = turn.get("phase") == "Phase_Combat"
        if self.current and (not in_combat or turn.get("turnNumber") != self.current["global_turn"]):
            self.finish(snapshot["event"], gap=gap)
        if in_combat:
            if self.current is None:
                self.current = {"start_event": snapshot["event"], "global_turn": turn.get("turnNumber"),
                    "active_player": turn.get("activePlayer"), "status": "unresolved", "attackers": [],
                    "blockers": [], "observations": [], "gap": gap,
                    "start_observed": turn.get("step") in {"Step_BeginCombat", "Step_DeclareAttack"},
                    "life_before": {str(k): v.get("lifeTotal") for k, v in snapshot["players"].items()}}
            self.current["gap"] |= gap
            board = snapshot["zones"].get("Battlefield", [])
            attack = [c for c in board if c.get("attackState") == "AttackState_Attacking"]
            block = [c for c in board if c.get("blockState") == "BlockState_Blocking"]
            observation = {"event": snapshot["event"], "step": turn.get("step"),
                           "attackers": attack, "blockers": block}
            previous = self.current["observations"][-1] if self.current["observations"] else None
            if previous is None or any(observation[k] != previous[k] for k in ("step", "attackers", "blockers")):
                self.current["observations"].append(observation)
            if turn.get("step") in {"Step_DeclareBlock", "Step_FirstStrikeDamage", "Step_CombatDamage"}:
                if attack and not self.current["attackers"]:
                    self.current["attackers"] = copy.deepcopy(attack)
                    self.current["attack_commit_event"] = snapshot["event"]
            if turn.get("step") in {"Step_FirstStrikeDamage", "Step_CombatDamage"}:
                if "block_commit_event" not in self.current:
                    self.current["blockers"] = copy.deepcopy(block)
                    self.current["block_commit_event"] = snapshot["event"]
            self.current["last_event"] = snapshot["event"]
            self.current["life_after"] = {str(k): v.get("lifeTotal") for k, v in snapshot["players"].items()}
            self.current["last_board"] = copy.deepcopy(board)
        self.previous = snapshot

    def finish(self, end_event, gap=False, ended=False):
        if not self.current:
            return
        episode = self.current
        episode["end_event"] = end_event
        episode["gap"] |= gap
        if episode["attackers"] and not episode["gap"]:
            episode["status"] = "committed"
        elif (episode["start_observed"] and not episode["gap"] and not ended and
              not episode["observations"][-1]["attackers"]):
            episode["status"] = "passed"
        episode["complete_window"] = not ended and not episode["gap"]
        episode["damage_note"] = "Life/board changes may include spells or triggers; inspect observations before attributing damage."
        self.episodes.append(episode)
        self.current = None


def turn_cycles(report):
    """Pair windows by active seat, never by odd/even turn assumptions."""
    cycles, current = [], None
    for turn in report["turns"]:
        if not turn["global_turn"]:
            continue
        if turn["active_player"] == report["seat_id"]:
            if current:
                current["closed_by_next_own_turn"] = True
                cycles.append(current)
            current = {"start_event": turn["start"]["event"], "global_turns": [],
                       "windows": [], "closed_by_next_own_turn": False}
        if current:
            current["global_turns"].append(turn["global_turn"])
            current["windows"].append({"active_player": turn["active_player"],
                "main": resources(turn.get("main1", turn["start"]), report["seat_id"]),
                "end": resources(turn["end"], report["seat_id"])})
            current["end_event"] = turn["end"]["event"]
    if current:
        cycles.append(current)
    for cycle in cycles:
        start, end = cycle["start_event"], cycle["end_event"]
        cycle["payments"] = [p for p in report["payments"] if start <= p["event"] <= end]
        cycle["committed_casts"] = [c for c in report["casts"] if c["status"] == "committed" and
                                   c["controller"] == report["seat_id"] and start <= c["start_event"] <= end]
        cycle["warnings"] = [w for w in report["warnings"] if start <= w.get("event", -1) <= end]
        cycle["interpretation"] = "Observed resource windows; source candidates and held mana require rules and strategic review."
    return cycles
