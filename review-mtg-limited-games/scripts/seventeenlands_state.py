"""Arena full/diff reconstruction. Extract evidence; leave gameplay judgments to the reviewer."""
import copy
from collections import Counter

from cast_evidence import classify
from review_evidence import KnowledgeLedger, CombatLedger, turn_cycles

DECODER_VERSION = "arena-2026-10-10-v2"
# This exact bundle's route parser and visibleDiff rules were inspected, and 15
# positions in a nine-game run were checked against the rendered replay.
SUPPORTED_FRONTENDS = {"b0dc60fbe4e6ef29bf8f9043febe04e3faa4fdf3502dafed9d92a348ba690d9f"}


def details(annotation):
    return {item["key"]: next((v for k, v in item.items() if k.startswith("value")), [])
            for item in annotation.get("details", [])}


def scalar(values, key, default=None):
    value = values.get(key, [])
    return value[0] if value else default


class ReplayState:
    def __init__(self, seat, opponent, cards, abilities):
        self.seat, self.opponent = seat, opponent
        self.cards, self.abilities = cards, abilities
        self.objects, self.zones, self.players, self.turn = {}, {}, {}, {}
        self.persistent, self.counters, self.aliases, self.choices = {}, {}, {}, {}
        self.seen_annotations = set()
        self.known_cards = {}
        self.game_state_id = None
        self.warnings = []
        self.knowledge = KnowledgeLedger(seat, cards)

    def ids(self, zone_type):
        return [oid for zone in self.zones.values() if zone["type"] == "ZoneType_" + zone_type
                for oid in zone.get("objectInstanceIds", [])]

    def zone_of(self, oid):
        for zone in self.zones.values():
            if oid in zone.get("objectInstanceIds", []):
                return zone["type"]
        return None

    def renamed(self, oid):
        seen = set()
        while oid in self.aliases and oid not in seen:
            seen.add(oid)
            oid = self.aliases[oid]
        return oid

    def update(self, message, index):
        kind = message.get("type")
        if kind not in {"GameStateType_Full", "GameStateType_Diff"}:
            raise ValueError(f"event:{index}: unsupported state type {kind!r}")
        current = message.get("gameStateId")
        if current is None:
            raise ValueError(f"event:{index}: missing gameStateId")
        gap = self.game_state_id is not None and current > self.game_state_id + 1
        if gap:
            self.known_cards.clear()
            self.warnings.append({"event": index, "kind": "state_gap", "after": self.game_state_id,
                                  "before": current, "full_resynchronization": kind == "GameStateType_Full"})
        if kind == "GameStateType_Full":
            self.objects, self.zones, self.players, self.turn = {}, {}, {}, {}
            self.persistent, self.counters = {}, {}
        self.game_state_id = current
        visible = any(key in message for key in ("zones", "gameObjects", "persistentAnnotations"))
        for player in message.get("players", []):
            seat = player["systemSeatNumber"]
            old_life = self.players.get(seat, {}).get("lifeTotal")
            if old_life and old_life != player.get("lifeTotal", 0):
                visible = True
            self.players[seat] = copy.deepcopy(player)
        for obj in message.get("gameObjects", []):
            # Entries are replacement objects: omitted isTapped means false.
            self.objects[obj["instanceId"]] = copy.deepcopy(obj)
            if obj.get("grpId") and (obj.get("visibility") == "Visibility_Public" or
                                     self.seat in obj.get("viewers", [])):
                self.known_cards[obj["instanceId"]] = obj["grpId"]
        for zone in message.get("zones", []):
            self.zones[zone["zoneId"]] = copy.deepcopy(zone)
        annotations = message.get("annotations", [])
        renames = []
        for annotation in annotations:
            kinds, values = annotation.get("type", []), details(annotation)
            if "AnnotationType_Scry" in kinds:
                visible = True
            if "AnnotationType_ObjectIdChanged" in kinds:
                old, new = scalar(values, "orig_id"), scalar(values, "new_id")
                if old is not None and new is not None:
                    self.aliases[old] = new
                    renames.append((old, new))
                    if old in self.known_cards and new not in self.known_cards:
                        self.known_cards[new] = self.known_cards[old]
            if "AnnotationType_ChoiceResult" in kinds:
                self.choices[annotation.get("affectorId")] = values
            aid = annotation.get("id")
            if aid is not None and aid in self.seen_annotations:
                continue
            if aid is not None:
                self.seen_annotations.add(aid)
            for counter_kind, sign in [("CounterAdded", 1), ("CounterRemoved", -1)]:
                if "AnnotationType_" + counter_kind in kinds:
                    for oid in annotation.get("affectedIds", []):
                        counters = self.counters.setdefault(oid, {})
                        counter = scalar(values, "counter_type")
                        counters[counter] = counters.get(counter, 0) + sign * scalar(values, "transaction_amount", 0)
        for annotation in message.get("persistentAnnotations", []):
            self.persistent[annotation["id"]] = copy.deepcopy(annotation)
        for aid in message.get("diffDeletedPersistentAnnotationIds", []):
            self.persistent.pop(aid, None)
        for annotation in self.persistent.values():
            if "AnnotationType_Counter" in annotation.get("type", []):
                values = details(annotation)
                for oid in annotation.get("affectedIds", []):
                    self.counters.setdefault(oid, {})[scalar(values, "counter_type")] = scalar(values, "count", 0)
        turn = message.get("turnInfo", {})
        if turn.get("turnNumber") and turn["turnNumber"] != self.turn.get("turnNumber"):
            visible = True
        if turn.get("phase") and turn["phase"] != self.turn.get("phase"):
            self.turn.pop("step", None)
        self.turn.update(copy.deepcopy(turn))
        if message.get("gameInfo", {}).get("stage") == "GameStage_GameOver":
            visible = True
        # Internal IDs are not permission to track identities through hidden libraries.
        for oid in self.ids("Library"):
            if self.objects.get(oid, {}).get("visibility") != "Visibility_Public":
                self.known_cards.pop(oid, None)
        self.knowledge.observe(self.objects, self.zones, renames, index,
                               {o["instanceId"] for o in message.get("gameObjects", [])}, gap)
        return visible, gap

    def describe(self, oid):
        obj = self.objects.get(oid, {})
        result = {"instance_id": oid, "owner": obj.get("ownerSeatId"),
                  "controller": obj.get("controllerSeatId")}
        visible = obj.get("visibility") == "Visibility_Public" or self.seat in obj.get("viewers", [])
        gid = obj.get("grpId") if visible else None
        if not gid:
            gid = self.known_cards.get(oid)
            if gid and self.zone_of(oid) == "ZoneType_Hand":
                return {**result, "card_id": gid, "name": self.cards.get(gid, {}).get("name", f"Card {gid}"),
                        "identity_evidence": "previously visible; public zone change"}
            return {**result, "name": "Unknown card"}
        card = self.cards.get(gid, {})
        ability_ids = obj.get("abilities", []) + [a["grpId"] for a in obj.get("uniqueAbilities", [])]
        result.update(card_id=gid, name=card.get("name", self.abilities.get(gid, f"Card/ability {gid}")),
                      object_type=obj.get("type"), tapped=bool(obj.get("isTapped")),
                      card_types=obj.get("cardTypes", []), abilities=ability_ids,
                      ability_text=[self.abilities.get(a, str(a)) for a in ability_ids])
        for key in ("power", "toughness"):
            if key in obj:
                result[key] = obj[key].get("value", 0)
        for key in ("damage", "hasSummoningSickness", "isCopy", "parentId", "attackState", "attackInfo", "blockState", "blockInfo"):
            if key in obj:
                result[key] = copy.deepcopy(obj[key])
        result["counters"] = dict(self.counters.get(oid, {}))
        if oid in self.choices:
            result["choice"] = copy.deepcopy(self.choices[oid])
        for key in ("mana_cost", "cmc", "image_url"):
            if key in card:
                result[key] = card[key]
        return result

    def snapshot(self, index):
        zones, libraries = {}, {}
        for zone in self.zones.values():
            name = zone["type"].removeprefix("ZoneType_")
            ids = zone.get("objectInstanceIds", [])
            if name == "Library":
                libraries[str(zone.get("ownerSeatId"))] = len(ids)
            elif name != "Limbo":
                zones.setdefault(name, []).extend(self.describe(oid) for oid in ids)
        sources = [obj for obj in zones.get("Battlefield", [])
                   if "CardType_Land" in obj.get("card_types", []) or
                   any("Add " in text or "add " in text for text in obj.get("ability_text", []))]
        return {"event": index, "game_state_id": self.game_state_id, "turn": dict(self.turn),
                "players": copy.deepcopy(self.players), "zones": zones, "library_counts": libraries,
                "mana_source_candidates": sources,
                "hand_knowledge": self.knowledge.hands(),
                "persistent_annotations": copy.deepcopy(list(self.persistent.values()))}


def decode_history(history, *, cards=None, abilities=None, event_id=None,
                   match_index=0, game_index=0, frontend_sha=None, capture_event=None):
    if not isinstance(history, dict) or not isinstance(history.get("events"), list):
        raise ValueError("Expected a history object with events")
    seat, opponent = history.get("seat_id"), history.get("opponent_seat_id")
    if seat not in (1, 2) or opponent not in (1, 2) or seat == opponent:
        raise ValueError("Expected distinct player and opponent seats 1 and 2")
    events = history["events"]
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"event:{index}: expected an object")
        if "gameStateMessage" in event and not isinstance(event["gameStateMessage"], dict):
            raise ValueError(f"event:{index}: expected gameStateMessage object")
    start = next((i for i, e in enumerate(events) if
                  e.get("gameStateMessage", {}).get("type") == "GameStateType_Full"), None)
    if start is None:
        raise ValueError("History has no full snapshot; reconstruction is unavailable")
    if capture_event is not None and not start <= capture_event < len(events):
        raise ValueError("Requested event is outside reconstructable history")
    state = ReplayState(seat, opponent, cards or {}, abilities or {})
    report = {"decoder_version": DECODER_VERSION, "seat_id": seat, "opponent_seat_id": opponent,
              "event_count": len(events), "positions": [], "turns": [], "openings": [],
              "actions": [], "casts": [], "payments": [], "warnings": state.warnings}
    combat_ledger, payment_ids = CombatLedger(), set()
    attempts, active_attempts = [], {}
    previous_stack, previous_board, previous_life = set(), set(), {}
    previous_combat = None
    previous_snapshot, previous_turn = None, None
    opening_hands = set()
    if start:
        state.warnings.append({"kind": "unreconstructable_prefix", "events": start})
    if frontend_sha not in SUPPORTED_FRONTENDS:
        state.warnings.append({"kind": "unverified_frontend", "sha256": frontend_sha})

    def action(index, kind, **fields):
        report["actions"].append({"event": index, "turn": dict(state.turn), "kind": kind, **fields})

    def evidence(attempt, index, kind):
        item = {"kind": kind, "source": f"event:{index}"}
        if item not in attempt["events"]:
            attempt["events"].append(item)

    for index in range(start, len(events)):
        event = events[index]
        if not isinstance(event, dict):
            raise ValueError(f"event:{index}: expected an object")
        message = event.get("gameStateMessage")
        before_objects, before_zones = state.objects.copy(), copy.deepcopy(state.zones)
        visible, gap = False, False
        if message is not None:
            visible, gap = state.update(message, index)
        elif event.get("type") == "ClientMessageType_SelectNResp":
            visible = event.get("optionContext") == "OptionContext_Resolution" and "ids" in event.get("selectNResp", {})
        elif event.get("type") not in {"GREMessageType_UIMessage", "ClientMessageType_UIMessage"}:
            state.warnings.append({"event": index, "kind": "unsupported_event", "type": event.get("type")})
        if index > start and visible:
            frame = len(report["positions"])
            supported = frontend_sha in SUPPORTED_FRONTENDS
            report["positions"].append({"frame": frame, "event": index,
                "game_state_id": state.game_state_id, "turn": dict(state.turn),
                "url": f"https://www.17lands.com/history/{event_id}/{match_index}/{game_index}/{frame}" if event_id else None,
                "verification": "source_mapping" if supported else "unverified_candidate"})
        stack, board = set(state.ids("Stack")), set(state.ids("Battlefield"))
        annotations = (message or {}).get("annotations", [])
        new_ids = {scalar(details(a), "new_id"): scalar(details(a), "orig_id") for a in annotations
                   if "AnnotationType_ObjectIdChanged" in a.get("type", [])}
        for oid in sorted(stack - previous_stack):
            obj = state.objects.get(oid, {})
            if index == start or (message or {}).get("type") == "GameStateType_Full":
                if obj.get("type") in {"GameObjectType_Card", "GameObjectType_PreparedCard"} and oid not in active_attempts:
                    state.warnings.append({"event": index, "kind": "unobserved_stack_entry", "object_id": oid})
                continue  # A resynchronization observes a stack; it does not prove an entry.
            if obj.get("type") == "GameObjectType_Ability":
                action(index, "ability_on_stack", object=state.describe(oid))
                continue
            if obj.get("type") not in {"GameObjectType_Card", "GameObjectType_PreparedCard"}:
                continue
            old_id = new_ids.get(oid)
            old_obj = before_objects.get(old_id, state.objects.get(old_id, {}))
            prepared = bool(old_obj.get("parentId")) and any(
                "AnnotationType_LoseDesignation" in a.get("type", []) and
                scalar(details(a), "DesignationType") == 24 for a in annotations)
            attempt = {"attempt_id": f"event-{index}-object-{oid}", "card": state.describe(oid)["name"],
                       "events": [], "object_id": oid, "start": index,
                       "copy": bool(obj.get("isCopy")), "prepared": prepared,
                       "controller": obj.get("controllerSeatId"),
                       "paid": False, "paid_sources": set(), "gap": False,
                       "before_stack": set(previous_stack), "before_zones": before_zones,
                       "before_objects": before_objects, "origin_id": old_id if old_id is not None else oid,
                       "turn": dict(state.turn), "response_seen": False}
            evidence(attempt, index, "stack_entered")
            attempts.append(attempt)
            active_attempts[oid] = attempt
        for attempt in active_attempts.values():
            attempt["gap"] |= gap
            if stack - attempt["before_stack"] - {attempt["object_id"]}:
                attempt["response_seen"] = True
        for annotation in annotations:
            kinds = annotation.get("type", [])
            if "AnnotationType_ManaPaid" in kinds:
                payment_key = annotation.get("id", repr(annotation))
                if payment_key not in payment_ids:
                    payment_ids.add(payment_key)
                    report["payments"].append({"event": index, "source": state.describe(annotation.get("affectorId")),
                        "targets": annotation.get("affectedIds", []), "details": details(annotation)})
            for oid in annotation.get("affectedIds", []):
                attempt = active_attempts.get(oid)
                if attempt and "AnnotationType_ManaPaid" in kinds:
                    attempt["paid"] = True
                    attempt["paid_sources"].add(annotation.get("affectorId"))
                    evidence(attempt, index, "costs_paid")
            attempt = active_attempts.get(annotation.get("affectorId"))
            if attempt and "AnnotationType_MultistepEffectComplete" in kinds:
                if not attempt["copy"] or attempt["paid"] or attempt["prepared"]:
                    evidence(attempt, index, "resolved")
        for oid, attempt in list(active_attempts.items()):
            if oid in stack:
                continue
            destination = state.zone_of(state.renamed(oid))
            returned_origin = any(attempt["origin_id"] in z.get("objectInstanceIds", [])
                                  for z in attempt["before_zones"].values() if z["type"] == "ZoneType_Hand")
            restored_sources = bool(attempt["paid_sources"]) and all(
                source in state.ids("Battlefield") and source in attempt["before_objects"] and
                not state.objects.get(source, {}).get("isTapped") and
                not attempt["before_objects"][source].get("isTapped")
                for source in attempt["paid_sources"])
            if (destination == "ZoneType_Hand" and returned_origin and restored_sources and
                    not attempt["gap"] and not attempt["response_seen"] and
                    state.turn == attempt["turn"] and stack == attempt["before_stack"] and
                    not any(e["kind"] == "resolved" for e in attempt["events"])):
                evidence(attempt, index, "canceled")
            if not attempt["gap"] and destination in {"ZoneType_Battlefield", "ZoneType_Graveyard", "ZoneType_Exile"}:
                if not attempt["copy"] or attempt["paid"] or attempt["prepared"]:
                    evidence(attempt, index, "cast_completed")
            normalized = {k: attempt[k] for k in ("attempt_id", "card", "events")}
            result = classify(normalized)
            action_kind = {"committed": "cast", "canceled": "canceled_cast", "unresolved": "unresolved_stack_departure"}
            action(index, action_kind[result["status"]],
                   card=attempt["card"], attempt_id=attempt["attempt_id"])
            del active_attempts[oid]
        for oid in sorted(board - previous_board):
            action(index, "entered_battlefield", object=state.describe(oid))
        for oid in sorted(previous_board - board):
            action(index, "left_battlefield", object_id=oid)
        life = {key: value.get("lifeTotal") for key, value in state.players.items()}
        if previous_life and life != previous_life:
            action(index, "life", values=life)
        combat = [{"object": state.describe(oid), "attack": state.objects[oid].get("attackInfo"),
                   "block": state.objects[oid].get("blockInfo")} for oid in sorted(board)
                  if state.objects.get(oid, {}).get("attackState") == "AttackState_Attacking" or
                  state.objects.get(oid, {}).get("blockState") == "BlockState_Blocking"]
        if combat and combat != previous_combat:
            action(index, "combat_observation", combat=combat,
                   verification="Check subsequent phase/damage state before treating selections as committed")
        previous_combat = combat
        turn_number = state.turn.get("turnNumber", 0)
        snapshot = None
        if turn_number != previous_turn:
            if previous_snapshot:
                report["turns"][-1]["end"] = previous_snapshot
            snapshot = state.snapshot(index)
            report["turns"].append({"global_turn": turn_number, "active_player": state.turn.get("activePlayer"),
                                    "start": snapshot})
            previous_turn = turn_number
        if state.turn.get("phase") == "Phase_Main1" and "main1" not in report["turns"][-1]:
            snapshot = snapshot or state.snapshot(index)
            report["turns"][-1]["main1"] = snapshot
        if not turn_number:
            hand = tuple(oid for oid in state.ids("Hand") if state.objects.get(oid, {}).get("ownerSeatId") == seat)
            if hand and hand not in opening_hands:
                opening_hands.add(hand)
                report["openings"].append({"event": index, "hand": [state.describe(oid) for oid in hand]})
        previous_snapshot = snapshot or state.snapshot(index)
        combat_ledger.observe(previous_snapshot, gap)
        if index == capture_event:
            report["state"] = copy.deepcopy(previous_snapshot)
        previous_stack, previous_board, previous_life = stack, board, life
    if report["turns"]:
        report["turns"][-1]["end"] = previous_snapshot
    for attempt in attempts:
        result = classify({k: attempt[k] for k in ("attempt_id", "card", "events")})
        result.update(start_event=attempt["start"], is_copy=attempt["copy"],
                      object_id=attempt["object_id"], controller=attempt["controller"],
                      last_evidence_event=max(int(e["source"].split(":")[1]) for e in attempt["events"]))
        report["casts"].append(result)
    report["cast_counts"] = dict(Counter(item["status"] for item in report["casts"]))
    report["knowledge_events"] = state.knowledge.events
    for payment in report["payments"]:
        attempts_here = [c for c in report["casts"] if c["object_id"] in payment["targets"] and
                         c["start_event"] <= payment["event"] <= c["last_evidence_event"]]
        payment["cast_status"] = attempts_here[0]["status"] if len(attempts_here) == 1 else "unresolved_or_activation"
    combat_ledger.finish(len(events) - 1, ended=True)
    report["combats"] = combat_ledger.episodes
    report["turn_cycles"] = turn_cycles(report)
    report["cast_evidence_complete"] = all(item["status"] != "unresolved" for item in report["casts"])
    report["frame_count"] = len(report["positions"])
    report["coverage"] = "partial" if any(w["kind"] != "unverified_frontend" for w in state.warnings) else "complete"
    return report
