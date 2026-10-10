#!/usr/bin/env python3
"""Fetch, cache, summarize, and inspect public 17Lands game evidence (Python standard library)."""
import argparse
import json
import sys
from pathlib import Path

from seventeenlands_io import EvidenceCache, decode_json, digest, retrieve, write_json
from seventeenlands_state import DECODER_VERSION, decode_history


def metadata(cache):
    cards, abilities = {}, {}
    for url in cache.manifest.get("cards_urls", []):
        cards.update({c["id"]: c for c in decode_json(cache.get(url))["cards"]})
    for url in cache.manifest.get("abilities_urls", []):
        abilities.update({a["id"]: a["text"] for a in decode_json(cache.get(url))["abilities"]})
    for game in cache.manifest.get("games", []):
        if game.get("status") == "downloaded":
            info = decode_json(cache.get(game["info_url"]))
            for key, card in info["deck_build"].get("cards", {}).items():
                cards[int(key)] = {**card, **cards.get(int(key), {})}
    for card in cards.values():
        for key, text in {**card.get("abilities", {}), **card.get("hidden_abilities", {})}.items():
            abilities[int(key)] = text
    return cards, abilities


def reconstruct(cache, game, cards, abilities, capture_event=None):
    history = decode_json(cache.get(game["history_url"]))
    report = decode_history(history, cards=cards, abilities=abilities,
        event_id=cache.manifest["event_id"], match_index=game["match_index"], game_index=game["game_index"],
        frontend_sha=cache.manifest.get("frontend", {}).get("sha256"), capture_event=capture_event)
    report.update(game=game["game"], match_index=game["match_index"], game_index=game["game_index"],
                  history_url=game["history_url"], history_sha256=cache.sources[game["history_url"]]["sha256"])
    return report


def build(cache):
    cards, abilities = metadata(cache)
    summary = {"event_id": cache.manifest["event_id"], "decoder_version": DECODER_VERSION,
               "frontend": cache.manifest.get("frontend"), "games": []}
    for game in cache.manifest.get("games", []):
        row = {k: game[k] for k in ("game", "match_index", "game_index")}
        row.update({k: game.get("result", {}).get(k) for k in
                    ("won", "on_play", "mulligans", "opponent_mulligans", "deck_index")})
        try:
            if game.get("status") != "downloaded":
                raise ValueError(game.get("error", "History unavailable"))
            report = reconstruct(cache, game, cards, abilities)
            info = decode_json(cache.get(game["info_url"]))
            groups = info["deck_build"].get("groups", [])
            row["deck_fingerprint"] = digest(json.dumps(groups, sort_keys=True).encode())
            report["played_deck"] = info["deck_build"]
            relative = f"derived/m{game['match_index']}-g{game['game_index']}.json"
            write_json(cache.directory / relative, report)
            row["derived_sha256"] = digest((cache.directory / relative).read_bytes())
            row.update(path=relative, **{k: report[k] for k in
                ("seat_id", "coverage", "event_count", "frame_count", "cast_counts", "warnings")})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            row.update(coverage="unavailable", error=str(exc))
        summary["games"].append(row)
    write_json(cache.directory / "summary.json", summary)
    return summary


def print_summary(summary):
    print(f"Event {summary['event_id']} | {summary['decoder_version']} | {len(summary['games'])} games")
    for row in summary["games"]:
        outcome = "W" if row.get("won") is True else "L" if row.get("won") is False else "?"
        if row["coverage"] == "unavailable":
            print(f"Game {row['game']} {outcome}: UNAVAILABLE — {row.get('error')}")
            continue
        counts = row["cast_counts"]
        print(f"Game {row['game']} {outcome} (match {row['match_index']}, game {row['game_index']}, "
              f"seat {row['seat_id']}): {row['event_count']} events / {row['frame_count']} frames; "
              f"{row['coverage']}; casts {counts}; {len(row['warnings'])} warnings")


def describe_snapshot(snapshot, seat):
    board = snapshot["zones"].get("Battlefield", [])
    hand = snapshot["zones"].get("Hand", [])
    def names(objects):
        return ", ".join(obj["name"] + (f" {obj['power']}/{obj['toughness']}" if "power" in obj else "") +
                         (" tapped" if obj.get("tapped") else "") for obj in objects) or "—"
    life = {k: p.get("lifeTotal") for k, p in snapshot["players"].items()}
    sources = snapshot["mana_source_candidates"]
    return (f"life {life}; hand: {names(o for o in hand if o['owner'] == seat)}\n"
            f"  own: {names(o for o in board if o['controller'] == seat)}\n"
            f"  opp: {names(o for o in board if o['controller'] != seat)}\n"
            f"  untapped source candidates: {names(o for o in sources if not o.get('tapped') and o['controller'] == seat)}")


def timeline(report, turn=None, actor=None):
    for window in report["turns"]:
        global_turn = window["global_turn"]
        display_turn = (global_turn + 1) // 2
        whose = "player" if window["active_player"] == report["seat_id"] else "opponent"
        if turn is not None and display_turn != turn or actor and actor != whose:
            continue
        print(f"\n{whose.upper()} turn {display_turn} (global {global_turn})")
        snapshot = window.get("main1", window["start"])
        print(f"e{snapshot['event']}: " + describe_snapshot(snapshot, report["seat_id"]))
        for action in report["actions"]:
            if action["turn"].get("turnNumber", 0) != global_turn:
                continue
            payload = {k: v for k, v in action.items() if k not in {"event", "turn"}}
            if "object" in payload:
                payload["object"] = payload["object"]["name"]
            if "combat" in payload:
                payload["combat"] = [{"creature": item["object"]["name"],
                                      "instance": item["object"]["instance_id"],
                                      "attack": item["attack"], "block": item["block"]}
                                     for item in payload["combat"]]
            print(f"e{action['event']}: {json.dumps(payload, ensure_ascii=False)}")
        print(f"end e{window['end']['event']}: " + describe_snapshot(window["end"], report["seat_id"]))
    print("\nWarnings:", json.dumps(report["warnings"]))
    unresolved = [a for a in report["casts"] if a["status"] != "committed"]
    print("Uncommitted attempts:", json.dumps(unresolved, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Retrieve a whole event, then build derived evidence")
    fetch.add_argument("url")
    fetch.add_argument("--out", required=True, type=Path)
    mode = fetch.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="Refresh mutable event/source data and histories")
    mode.add_argument("--offline", action="store_true", help="Require every response in the verified cache")
    for name in ("build", "summary", "state", "timeline"):
        command = commands.add_parser(name)
        command.add_argument("directory", type=Path)
        if name in ("state", "timeline"):
            command.add_argument("--game", required=True, type=int, help="One-based game number across the event")
        if name == "state":
            command.add_argument("--event", required=True, type=int, help="Zero-based raw event index; state is after it")
        if name == "timeline":
            command.add_argument("--turn", type=int, help="Replay display turn number")
            command.add_argument("--actor", choices=("player", "opponent"))
    args = parser.parse_args()
    try:
        if args.command == "fetch":
            cache = EvidenceCache(args.out, offline=args.offline, refresh=args.refresh)
            retrieve(args.url, cache)
            # Processing always reads the bytes just retrieved; it does not refresh them twice.
            summary = build(EvidenceCache(args.out, offline=True))
            print_summary(summary)
            return 1 if any(g["coverage"] == "unavailable" for g in summary["games"]) else 0
        cache = EvidenceCache(args.directory, offline=True)
        if args.command == "build":
            summary = build(cache)
            print_summary(summary)
            return 1 if any(g["coverage"] == "unavailable" for g in summary["games"]) else 0
        if args.command == "summary":
            summary = json.loads((args.directory / "summary.json").read_text())
            if summary["decoder_version"] != DECODER_VERSION:
                raise ValueError("Derived evidence is stale; run build")
            print_summary(summary)
            return 0
        game = next((g for g in cache.manifest["games"] if g["game"] == args.game), None)
        if not game or game.get("status") != "downloaded":
            raise ValueError("Requested game is unavailable; inspect summary")
        cards, abilities = metadata(cache)
        report = reconstruct(cache, game, cards, abilities, args.event if args.command == "state" else None)
        if args.command == "timeline":
            timeline(report, args.turn, args.actor)
        else:
            position = next((p for p in reversed(report["positions"]) if p["event"] <= args.event), None)
            output = {"history_url": game["history_url"], "history_sha256": report["history_sha256"],
                      "position": position, "state": report["state"], "warnings": report["warnings"]}
            if position is None or position["event"] != args.event:
                output["position_note"] = "No distinct displayed frame for this event; position is the preceding visible frame. Compare phase and stack before citing."
            print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
