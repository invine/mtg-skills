"""Public contracts for repeatable review evidence, independent of coaching judgments."""
import json
import unittest
import tempfile
from pathlib import Path

from seventeenlands_state import decode_history
from test_extract_17lands import initial, message, annotation


class KnowledgeTests(unittest.TestCase):
    def test_gap_does_not_relearn_a_stale_revealed_hand(self):
        first = initial()
        first["gameStateMessage"].update(gameObjects=[{"instanceId": 90, "grpId": 900,
            "ownerSeatId": 2, "controllerSeatId": 2, "visibility": "Visibility_Public"}], zones=[
            {"zoneId": 35, "type": "ZoneType_Hand", "ownerSeatId": 2, "objectInstanceIds": [90]}])
        report = decode_history({"seat_id": 1, "opponent_seat_id": 2,
            "events": [first, message(7)]}, capture_event=1)
        self.assertEqual(report["state"]["hand_knowledge"]["1"], [])

    def test_public_return_is_known_to_opponent_but_private_draw_is_not(self):
        private = {"instanceId": 10, "grpId": 100, "ownerSeatId": 1, "controllerSeatId": 1,
                   "type": "GameObjectType_Card", "visibility": "Visibility_Private", "viewers": [1]}
        first = initial()
        first["gameStateMessage"].update(gameObjects=[private], zones=[
            {"zoneId": 31, "type": "ZoneType_Hand", "ownerSeatId": 1, "objectInstanceIds": [10]}])
        public = {**private, "visibility": "Visibility_Public"}
        cast = message(2, gameObjects=[public], zones=[
            {"zoneId": 31, "type": "ZoneType_Hand", "ownerSeatId": 1},
            {"zoneId": 28, "type": "ZoneType_Battlefield", "objectInstanceIds": [10]}])
        bounce = message(3, gameObjects=[{**private, "instanceId": 11}], zones=[
            {"zoneId": 28, "type": "ZoneType_Battlefield"},
            {"zoneId": 31, "type": "ZoneType_Hand", "ownerSeatId": 1, "objectInstanceIds": [11]}],
            annotations=[annotation("ObjectIdChanged", 10, [10], orig_id=10, new_id=11)])
        history = {"seat_id": 1, "opponent_seat_id": 2, "events": [first, cast, bounce]}
        early = decode_history(history, cards={100: {"name": "Protection"}}, capture_event=0)
        late = decode_history(history, cards={100: {"name": "Protection"}}, capture_event=2)
        self.assertEqual(early["state"]["hand_knowledge"]["2"], [])
        known = late["state"]["hand_knowledge"]["2"]
        self.assertEqual([(c["name"], c["owner"], c["instance_id"]) for c in known], [("Protection", 1, 11)])
        self.assertEqual(known[0]["learned_event"], 1)
        self.assertEqual(known[0]["hand_entry_event"], 2)
        history["events"].append(message(7))
        uncertain = decode_history(history, capture_event=3)
        self.assertEqual(uncertain["state"]["hand_knowledge"]["2"], [])


class WindowTests(unittest.TestCase):
    def test_combat_selection_is_not_committed_until_later_phase_and_cycles_follow_seats(self):
        creature = {"instanceId": 50, "grpId": 100, "ownerSeatId": 1, "controllerSeatId": 1,
                    "type": "GameObjectType_Card", "visibility": "Visibility_Public"}
        first = initial()
        first["gameStateMessage"].update(gameObjects=[creature], zones=[
            {"zoneId": 28, "type": "ZoneType_Battlefield", "objectInstanceIds": [50]}])
        attack = {**creature, "attackState": "AttackState_Attacking", "attackInfo": {"targetId": 2}}
        history = {"seat_id": 1, "opponent_seat_id": 2, "events": [first,
            message(2, gameObjects=[attack], turnInfo={"phase": "Phase_Combat", "step": "Step_DeclareAttack"}),
            message(3, gameObjects=[creature]),  # selection withdrawn
            message(4, turnInfo={"phase": "Phase_Main2"}),
            message(5, turnInfo={"turnNumber": 2, "activePlayer": 1, "phase": "Phase_Main1"}),  # extra turn
            message(6, gameObjects=[attack], turnInfo={"phase": "Phase_Combat", "step": "Step_DeclareAttack"}),
            message(7, turnInfo={"phase": "Phase_Combat", "step": "Step_DeclareBlock"}),
            message(8, turnInfo={"phase": "Phase_Main2"}),
            message(9, turnInfo={"turnNumber": 3, "activePlayer": 2, "phase": "Phase_Main1"}),
            message(10, turnInfo={"turnNumber": 4, "activePlayer": 1, "phase": "Phase_Main1"})]}
        report = decode_history(history)
        self.assertEqual([c["status"] for c in report["combats"]], ["passed", "committed"])
        self.assertEqual(report["combats"][0]["attackers"], [])
        self.assertEqual(report["combats"][1]["attackers"][0]["instance_id"], 50)
        self.assertEqual([c["global_turns"] for c in report["turn_cycles"]], [[1], [2, 3], [4]])
        self.assertFalse(report["turn_cycles"][-1]["closed_by_next_own_turn"])


class ReviewValidationTests(unittest.TestCase):
    def test_position_review_does_not_require_a_whole_game_attestation(self):
        from review_tools import make_review, validate_review
        report = decode_history({"seat_id": 1, "opponent_seat_id": 2,
            "events": [initial(), message(2, gameObjects=[])]})
        report.update(game=1, history_sha256="history1")
        reports = {1: report}
        ledger = make_review(reports, positions=[(1, 1)])
        self.assertEqual([c["kind"] for c in ledger["checks"]], ["evidence", "position"])
        for item in ledger["checks"]:
            item.update(status="reviewed", note="Position evidence inspected.")
        self.assertTrue(validate_review(ledger, reports, {}, positions=[(1, 1)])["ok"])
        self.assertFalse(validate_review(ledger, reports, {})["ok"])

    def test_coverage_and_each_finding_must_match_source_and_position(self):
        from review_tools import make_review, validate_review, context
        report = decode_history({"seat_id": 1, "opponent_seat_id": 2, "events": [initial(),
            message(2, gameObjects=[], turnInfo={"phase": "Phase_Main2"})]},
            capture_event=1, event_id="a" * 32)
        report.update(game=1, history_sha256="history1")
        reports = {1: report}
        ledger = make_review(reports)
        self.assertFalse(validate_review(ledger, reports, {})["ok"])

        for item in ledger["checks"]:
            item.update(status="reviewed", note="Checked opening/resources against state; no finding.")
        self.assertTrue(validate_review(ledger, reports, {})["ok"])
        point = context(report, report["state"])
        finding = {"id": "F1", "game": 1, "label": "Game 1 — before passing", "analysis": "Test finding.",
            "state_event": 1, "window_end_event": 1, "context": point,
            "verification": {"method": "ui", "url": point["position"]["url"],
                             "checked": ["turn", "board", "stack"], "note": "Replay phase, board and empty stack matched."}}
        ledger["findings"].append(finding)
        states = {(1, 1): report["state"]}
        self.assertTrue(validate_review(ledger, reports, states)["ok"])
        finding["context"]["position"]["url"] += "0"
        self.assertFalse(validate_review(ledger, reports, states)["ok"])
        ledger["findings"] = []
        ledger["checks"] = []
        self.assertFalse(validate_review(ledger, reports, {})["ok"])


class CardReferenceTests(unittest.TestCase):
    def test_exact_printing_resolves_prepared_faces_and_rejects_wrong_identity(self):
        from card_reference import reference
        from seventeenlands_io import EvidenceCache
        uid = "7e5a640b-fd88-4b5a-9dfc-1d8f5a5cef41"
        card = {"id": 100, "name": "Semester Foreseer", "layout": "prepare",
                "image_url": f"https://cards.scryfall.io/large/front/7/e/{uid}.jpg"}
        full = {"id": uid, "name": "Semester Foreseer // Peer Review", "layout": "prepare",
            "card_faces": [{"name": "Semester Foreseer", "mana_cost": "{3}{U}", "oracle_text": "This creature enters prepared."},
                           {"name": "Peer Review", "mana_cost": "{2}{W/U}", "oracle_text": "Create a Cadet. Surveil 1."}]}
        with tempfile.TemporaryDirectory() as directory:
            cache = EvidenceCache(Path(directory), transport=lambda url: (json.dumps(full).encode(), {"status": 200}))
            result = reference(card, cache)
            self.assertEqual(result["status"], "complete_text")
            self.assertEqual(result["faces"][1]["name"], "Peer Review")
            cache.save()
            self.assertEqual(reference(card, EvidenceCache(Path(directory), offline=True))["faces"], result["faces"])
            wrong = {**card, "name": "A-Semester Foreseer"}
            self.assertEqual(reference(wrong, cache)["status"], "unresolved")

    def test_refresh_retains_previous_text_and_provenance(self):
        from card_reference import reference
        from seventeenlands_io import EvidenceCache
        uid = "7e5a640b-fd88-4b5a-9dfc-1d8f5a5cef41"
        card = {"id": 100, "name": "Example", "image_url": f"https://cards.scryfall.io/{uid}.jpg"}
        record = {"id": uid, "name": "Example", "mana_cost": "{U}", "oracle_text": "Original text."}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            transport = lambda url: (json.dumps(record).encode(), {"status": 200})
            cache = EvidenceCache(path, transport=transport)
            old = reference(card, cache); cache.save()
            record["oracle_text"] = "Updated text."
            new = reference(card, EvidenceCache(path, refresh=True, transport=transport))
            self.assertNotEqual(old["source"]["sha256"], new["source"]["sha256"])
            self.assertIn("Original text.", (path / old["source"]["path"]).read_text())


if __name__ == "__main__":
    unittest.main()
