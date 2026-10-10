"""Behavioral tests for downloaded evidence and reconstructed replay positions."""
import gzip
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from seventeenlands_io import EvidenceCache, decode_json, enumerate_games, parse_event_url, retrieve
from seventeenlands_state import decode_history, SUPPORTED_FRONTENDS


def message(number, **fields):
    return {"type": "GREMessageType_GameStateMessage", "gameStateMessage": {
        "type": "GameStateType_Diff", "gameStateId": number, **fields}}


def annotation(kind, source, targets, **details):
    return {"type": ["AnnotationType_" + kind], "affectorId": source,
            "affectedIds": targets, "details": [
                {"key": k, "valueInt32": [v]} for k, v in details.items()]}


def initial():
    return message(1, type="GameStateType_Full", players=[
        {"systemSeatNumber": 1, "lifeTotal": 20}, {"systemSeatNumber": 2, "lifeTotal": 20}],
        zones=[{"zoneId": 27, "type": "ZoneType_Stack"},
               {"zoneId": 30, "type": "ZoneType_Limbo"}],
        turnInfo={"turnNumber": 1, "activePlayer": 1, "phase": "Phase_Main1"})


class ReconstructionTests(unittest.TestCase):
    def test_known_proft_position_matches_the_rendered_replay(self):
        history = json.loads((Path(__file__).parent / "fixtures/game4-frame161.json").read_text())
        report = decode_history(history, frontend_sha=next(iter(SUPPORTED_FRONTENDS)),
                                event_id="e187816eba1f41c78c0d0c57aa13ce26", match_index=3)
        position = report["positions"][161]
        self.assertEqual(position["event"], 468)
        self.assertEqual(position["game_state_id"], 466)
        self.assertEqual(position["turn"]["turnNumber"], 17)
        self.assertEqual(position["turn"]["activePlayer"], 2)
        self.assertEqual(position["turn"]["step"], "Step_End")
        self.assertEqual(position["url"], history["provenance"]["source"])

    def test_hidden_identity_is_not_backfilled_and_replacement_objects_untap(self):
        hidden = {"instanceId": 40, "ownerSeatId": 2, "controllerSeatId": 2,
                  "type": "GameObjectType_Card", "grpId": 999, "visibility": "Visibility_Private", "viewers": [2]}
        creature = {"instanceId": 50, "ownerSeatId": 1, "controllerSeatId": 1,
                    "type": "GameObjectType_Card", "grpId": 100, "visibility": "Visibility_Public"}
        first = initial()
        first["gameStateMessage"].update(gameObjects=[hidden, {**creature, "isTapped": True}], zones=[
            {"zoneId": 35, "type": "ZoneType_Hand", "ownerSeatId": 2, "objectInstanceIds": [40]},
            {"zoneId": 28, "type": "ZoneType_Battlefield", "objectInstanceIds": [50]}])
        history = {"seat_id": 1, "opponent_seat_id": 2, "events": [first,
            message(2, gameObjects=[creature]),
            message(3, gameObjects=[{**hidden, "visibility": "Visibility_Public"}])]}
        report = decode_history(history, cards={999: {"name": "Future reveal"}}, capture_event=1)
        self.assertEqual(report["state"]["zones"]["Hand"][0]["name"], "Unknown card")
        self.assertFalse(report["state"]["zones"]["Battlefield"][0]["tapped"])

    def test_public_bounce_preserves_known_identity_but_hidden_library_breaks_tracking(self):
        card = {"instanceId": 50, "grpId": 100, "ownerSeatId": 2, "controllerSeatId": 2,
                "type": "GameObjectType_Card", "visibility": "Visibility_Public"}
        first = initial()
        first["gameStateMessage"].update(gameObjects=[card], zones=[
            {"zoneId": 28, "type": "ZoneType_Battlefield", "objectInstanceIds": [50]}])
        hidden = {"instanceId": 51, "ownerSeatId": 2, "controllerSeatId": 2,
                  "type": "GameObjectType_Card", "visibility": "Visibility_Hidden"}
        bounce = message(2, gameObjects=[hidden], zones=[
            {"zoneId": 28, "type": "ZoneType_Battlefield"},
            {"zoneId": 35, "type": "ZoneType_Hand", "ownerSeatId": 2, "objectInstanceIds": [51]}],
            annotations=[annotation("ObjectIdChanged", 50, [50], orig_id=50, new_id=51)])
        library = message(3, zones=[{"zoneId": 35, "type": "ZoneType_Hand", "ownerSeatId": 2},
            {"zoneId": 34, "type": "ZoneType_Library", "ownerSeatId": 2, "objectInstanceIds": [51]}])
        draw = message(4, zones=[{"zoneId": 34, "type": "ZoneType_Library", "ownerSeatId": 2},
            {"zoneId": 35, "type": "ZoneType_Hand", "ownerSeatId": 2, "objectInstanceIds": [51]}])
        history = {"seat_id": 1, "opponent_seat_id": 2, "events": [first, bounce, library, draw]}
        before = decode_history(history, cards={100: {"name": "Known threat"}}, capture_event=1)
        after = decode_history(history, cards={100: {"name": "Known threat"}}, capture_event=3)
        self.assertEqual(before["state"]["zones"]["Hand"][0]["name"], "Known threat")
        self.assertEqual(after["state"]["zones"]["Hand"][0]["name"], "Unknown card")

    def test_unknown_schema_is_rejected_and_event_gaps_are_reported(self):
        for malformed in [None, {"gameStateMessage": []}]:
            with self.subTest(malformed=malformed), self.assertRaisesRegex(ValueError, "event:0"):
                decode_history({"seat_id": 1, "opponent_seat_id": 2, "events": [malformed, initial()]})
        with self.assertRaisesRegex(ValueError, "full snapshot"):
            decode_history({"seat_id": 1, "opponent_seat_id": 2, "events": [message(1)]})
        report = decode_history({"seat_id": 1, "opponent_seat_id": 2,
                                 "events": [initial(), message(4, gameObjects=[])]})
        self.assertEqual(report["coverage"], "partial")
        self.assertTrue(any(w["kind"] == "state_gap" for w in report["warnings"]))

    def test_prepared_copy_resolution_is_a_cast_without_a_graveyard_card(self):
        spell = {"instanceId": 487, "grpId": 106266, "type": "GameObjectType_Card",
                 "zoneId": 27, "visibility": "Visibility_Public", "isCopy": True,
                 "ownerSeatId": 1, "controllerSeatId": 1, "cardTypes": ["CardType_Sorcery"]}
        history = {"seat_id": 1, "opponent_seat_id": 2, "events": [initial(),
            message(2, gameObjects=[spell], zones=[{"zoneId": 27, "type": "ZoneType_Stack",
                    "objectInstanceIds": [487]}], annotations=[annotation("ManaPaid", 475, [487], color=1)]),
            message(3, annotations=[annotation("MultistepEffectStarted", 487, [1], SubCategory=11)]),
            message(4, zones=[{"zoneId": 27, "type": "ZoneType_Stack"}],
                    annotations=[annotation("MultistepEffectComplete", 487, [1], SubCategory=11)])]}
        report = decode_history(history, cards={106266: {"name": "Peer Review"}}, capture_event=3)
        self.assertEqual(report["casts"][0]["status"], "committed")
        self.assertEqual(report["casts"][0]["card"], "Peer Review")
        self.assertEqual(report["state"]["zones"].get("Graveyard", []), [])
        self.assertEqual(report["casts"][0]["evidence"][-1]["source"], "event:3")

    def test_rollback_then_recast_keeps_attempts_separate(self):
        card = {"instanceId": 10, "grpId": 100, "type": "GameObjectType_Card", "zoneId": 31,
                "ownerSeatId": 1, "controllerSeatId": 1, "visibility": "Visibility_Private", "viewers": [1]}
        land = {"instanceId": 20, "grpId": 200, "type": "GameObjectType_Card", "zoneId": 28,
                "ownerSeatId": 1, "controllerSeatId": 1, "visibility": "Visibility_Public",
                "cardTypes": ["CardType_Land"]}
        hand = {"zoneId": 31, "type": "ZoneType_Hand", "ownerSeatId": 1, "objectInstanceIds": [10]}
        stack = {"zoneId": 27, "type": "ZoneType_Stack"}
        first = initial()
        first["gameStateMessage"].update(gameObjects=[card, land], zones=[hand, stack,
            {"zoneId": 28, "type": "ZoneType_Battlefield", "objectInstanceIds": [20]}])
        cast = message(2, gameObjects=[{**card, "zoneId": 27}, {**land, "isTapped": True}],
            zones=[{**hand, "objectInstanceIds": []}, {**stack, "objectInstanceIds": [10]}],
            annotations=[annotation("ManaPaid", 20, [10], color=2)])
        rollback = message(3, gameObjects=[card, land], zones=[hand, stack])
        recast = json.loads(json.dumps(cast)); recast["gameStateMessage"]["gameStateId"] = 4
        resolved = message(5, zones=[stack, {"zoneId": 29, "type": "ZoneType_Graveyard",
                                             "ownerSeatId": 1, "objectInstanceIds": [10]}])
        report = decode_history({"seat_id": 1, "opponent_seat_id": 2,
                                 "events": [first, cast, rollback, recast, resolved]})
        self.assertEqual([a["status"] for a in report["casts"]], ["canceled", "committed"])
        self.assertNotEqual(report["casts"][0]["attempt_id"], report["casts"][1]["attempt_id"])


class RetrievalTests(unittest.TestCase):
    def test_malformed_game_is_preserved_as_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            def transport(url):
                if "/details/" in url:
                    return b'<script src="/static/Routes.fixture.js"></script>', {"status": 200}
                if "/static/" in url:
                    return b'/data/event_details /data/history_info/ /data/history /data/cards /data/abilities', {"status": 200}
                if "/data/event_details" in url:
                    payload = {"details": {"match_results": [{"game_results": [{"won": True}]}]}}
                elif "/data/history_info/" in url:
                    payload = {"history_path": "test", "deck_build": {"groups": []}}
                else:
                    payload = {"seat_id": 1, "opponent_seat_id": 2, "events": [None]}
                return json.dumps(payload).encode(), {"status": 200}
            cache = EvidenceCache(Path(directory), transport=transport)
            report = retrieve("https://www.17lands.com/details/" + "a" * 32, cache)
            self.assertEqual(report["games"][0]["status"], "unavailable")
            self.assertIn("event", report["games"][0]["error"])

    def test_match_and_game_indices_remain_independent(self):
        event = {"details": {"match_results": [
            {"game_results": [{"deck_index": 0}, {"deck_index": 1}, {"deck_index": 2}]},
            {"game_results": [{"deck_index": 3}]}]}}
        entries = enumerate_games(event)
        self.assertEqual([(g["game"], g["match_index"], g["game_index"]) for g in entries],
                         [(1, 0, 0), (2, 0, 1), (3, 0, 2), (4, 1, 0)])

    def test_compressed_json_and_verified_offline_cache(self):
        body = gzip.compress(b'{"events": []}')
        with tempfile.TemporaryDirectory() as directory:
            calls = []

            def transport(url):
                calls.append(url)
                return body, {"status": 200, "content_type": "text/html"}

            cache = EvidenceCache(Path(directory), transport=transport)
            url = "https://www.17lands.com/data/history?history_path=example"
            self.assertEqual(decode_json(cache.get(url)), {"events": []})
            cache.save()
            offline = EvidenceCache(Path(directory), offline=True)
            self.assertEqual(decode_json(offline.get(url)), {"events": []})
            self.assertEqual(len(calls), 1)
            entry = next(iter(offline.sources.values()))
            (Path(directory) / entry["path"]).write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError, "hash"):
                offline.get(url)

    def test_command_rebuilds_and_queries_an_offline_game(self):
        with tempfile.TemporaryDirectory() as directory:
            event_id = "a" * 32
            history = {"seat_id": 1, "opponent_seat_id": 2,
                       "events": [initial(), message(2, gameObjects=[], turnInfo={"phase": "Phase_Main2"})]}
            history_url, info_url = "https://www.17lands.com/history-data", "https://www.17lands.com/info-data"
            bodies = {history_url: json.dumps(history).encode(), info_url: b'{"deck_build":{"groups":[],"cards":{}}}'}
            cache = EvidenceCache(Path(directory), transport=lambda url: (bodies[url], {"status": 200}))
            for url in bodies:
                cache.get(url)
            cache.manifest.update(event_id=event_id, games=[{"game": 1, "match_index": 0,
                "game_index": 0, "result": {"won": True}, "status": "downloaded",
                "history_url": history_url, "info_url": info_url}])
            cache.save()
            command = [sys.executable, "-B", str(Path(__file__).with_name("extract_17lands.py"))]
            built = subprocess.run(command + ["build", directory], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            state = subprocess.run(command + ["state", directory, "--game", "1", "--event", "1"],
                                   capture_output=True, text=True)
            self.assertEqual(state.returncode, 0, state.stderr)
            output = json.loads(state.stdout)
            self.assertEqual(output["state"]["turn"]["phase"], "Phase_Main2")
            self.assertEqual(output["position"]["verification"], "unverified_candidate")
            review_cli = [sys.executable, "-B", str(Path(__file__).with_name("review_tools.py"))]
            ledger_path = Path(directory) / "review.json"
            initialized = subprocess.run(review_cli + ["init", directory, "--out", str(ledger_path)], capture_output=True, text=True)
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            ledger = json.loads(ledger_path.read_text())
            ledger.update(games=[], provenance={}, checks=[], findings=[])
            ledger_path.write_text(json.dumps(ledger))
            validated = subprocess.run(review_cli + ["validate", directory, str(ledger_path)], capture_output=True, text=True)
            self.assertEqual(validated.returncode, 1, validated.stdout + validated.stderr)


if __name__ == "__main__":
    unittest.main()
