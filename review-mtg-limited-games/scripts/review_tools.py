#!/usr/bin/env python3
"""Prepare and validate review evidence. Read --help for commands; all review data stays task-local."""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

from extract_17lands import metadata, reconstruct
from seventeenlands_io import EvidenceCache, digest, write_json
from seventeenlands_state import DECODER_VERSION


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def context(report, state):
    position = next((p for p in reversed(report["positions"]) if p["event"] <= state["event"]), None)
    return {"history_sha256": report["history_sha256"], "decoder_version": report["decoder_version"],
            "state_sha256": fingerprint(state), "event": state["event"], "seat": report["seat_id"],
            "game_state_id": state["game_state_id"], "turn": state["turn"], "position": copy.deepcopy(position),
            "exact_frame": bool(position and position["event"] == state["event"])}


def make_review(reports, positions=None):
    positions = sorted(positions or [])
    if len(set(positions)) != len(positions):
        raise ValueError("Duplicate requested positions")
    for game, event in positions:
        if game not in reports or type(event) is not int or event < 0 or (
                reports[game].get("coverage") != "unavailable" and event >= reports[game]["event_count"]):
            raise ValueError("Requested position is outside the available history")
    checks, provenance = [], {}
    for game, report in sorted(reports.items()):
        provenance[str(game)] = {k: report.get(k) for k in ("history_sha256", "history_url", "decoder_version",
            "coverage", "derived_sha256", "deck_fingerprint", "match_index", "game_index")}
        entries = [("evidence", None)]
        if positions:
            entries += [("position", event) for g, event in positions if g == game]
        else:
            entries += [("opening", o["event"]) for o in report.get("openings", [])]
            entries += [("turn_cycle", o["start_event"]) for o in report.get("turn_cycles", [])]
            entries += [("combat", o["start_event"]) for o in report.get("combats", [])]
        for kind, event in entries:
            checks.append({"id": f"g{game}:{kind}:{event}", "game": game, "kind": kind, "event": event,
                           "status": "unreviewed", "note": ""})
    return {"schema": 1, "games": sorted(reports), "positions": [list(p) for p in positions], "provenance": provenance,
            "checks": checks, "findings": [], "withdrawn": []}


def validate_review(ledger, reports, states, answer=None, positions=None):
    expected, errors = make_review(reports, positions), []
    if not reports:
        errors.append("Requested review scope must contain at least one game.")
    if any(ledger.get(key) != expected[key] for key in ("schema", "games", "positions", "provenance")):
        errors.append("Review scope/provenance is stale or changed; regenerate and reconcile the ledger.")
    actual = ledger.get("checks", [])
    by_id = {c.get("id"): c for c in actual}
    if len(by_id) != len(actual) or set(by_id) != {c["id"] for c in expected["checks"]}:
        errors.append("Coverage checks missing, duplicated, or outside the requested scope.")
    for check in expected["checks"]:
        item = by_id.get(check["id"], {})
        if any(item.get(k) != check[k] for k in ("game", "kind", "event")):
            errors.append(f"{check['id']}: source locator changed.")
        if item.get("status") not in {"reviewed", "insufficient_evidence"} or not str(item.get("note", "")).strip():
            errors.append(f"{check['id']}: needs a reviewer status and note.")
        if reports[check["game"]].get("coverage") == "unavailable" and item.get("status") != "insufficient_evidence":
            errors.append(f"{check['id']}: unavailable history cannot be marked reviewed.")
    ids = set()
    for finding in ledger.get("findings", []):
        fid = finding.get("id", "")
        if not re.fullmatch(r"F[1-9][0-9]*", fid) or fid in ids:
            errors.append(f"Invalid or duplicate finding ID: {fid}")
        ids.add(fid)
        game, event = finding.get("game"), finding.get("state_event")
        if positions and (game, event) not in positions:
            errors.append(f"{fid}: finding is outside the requested positions.")
        report, state = reports.get(game), states.get((game, event))
        if report is None or state is None:
            errors.append(f"{fid}: missing before-action source state.")
            continue
        point = context(report, state)
        if finding.get("context") != point:
            errors.append(f"{fid}: context/URL does not match the reconstructed state.")
        choice, end = finding.get("choice_event"), finding.get("window_end_event")
        if not ((type(choice) is int and event < choice < report["event_count"]) or
                (choice is None and type(end) is int and event <= end < report["event_count"])):
            errors.append(f"{fid}: identify a later action or the end of a passed-action window.")
        verification = finding.get("verification", {})
        method = verification.get("method")
        if method == "unavailable":
            if not all(str(verification.get(k, "")).strip() for k in ("reason", "source_url", "locator", "excerpt")):
                errors.append(f"{fid}: fallback needs reason, closest source URL, locator and excerpt.")
        else:
            position = point["position"] or {}
            if not point["exact_frame"]:
                errors.append(f"{fid}: preceding frame needs an explicit unavailable-link fallback.")
            if method not in {"ui", "source_and_state"} or verification.get("url") != position.get("url"):
                errors.append(f"{fid}: missing verification for this exact URL.")
            if method == "source_and_state" and position.get("verification") != "source_mapping":
                errors.append(f"{fid}: unrecognized frontend requires UI verification or fallback.")
            if set(verification.get("checked", [])) != {"turn", "board", "stack"} or not verification.get("note"):
                errors.append(f"{fid}: record turn, board and stack checks and their supporting note.")
        if not finding.get("label") or not finding.get("analysis"):
            errors.append(f"{fid}: label and analysis are required.")
    if answer is not None:
        blocks = re.findall(r"<!-- finding:(F\d+) -->\s*(.*?)\s*<!-- /finding -->", answer, re.S)
        if len(blocks) != len(ids) or {k for k, _ in blocks} != ids:
            errors.append("Rendered answer must contain one marked block for each retained finding.")
        rendered = dict(blocks)
        for finding in ledger.get("findings", []):
            if finding.get("id") in rendered and render_finding(finding).strip() not in answer:
                errors.append(f"{finding['id']}: rendered finding differs from its verified ledger entry.")
    return {"ok": not errors, "errors": errors, "checks": len(expected["checks"]), "findings": len(ids),
            "limitations": "Validates recorded coverage and evidence consistency, not the truth of reviewer attestations or strategic judgments."}


def render_finding(finding):
    verification = finding["verification"]
    url = verification.get("url", verification.get("source_url"))
    fallback = (f" Exact-position link unavailable: {verification['reason']}. "
                f"Locator: {verification['locator']}. Evidence: {verification['excerpt']}\n"
                if verification["method"] == "unavailable" else "")
    return (f"<!-- finding:{finding['id']} -->\n[{finding['label']}]({url})\n\n"
            f"{finding['analysis']}\n{fallback}<!-- /finding -->")


def load_reports(directory, games=None):
    cache = EvidenceCache(directory, offline=True)
    summary = json.loads((directory / "summary.json").read_text())
    if summary.get("decoder_version") != DECODER_VERSION:
        raise ValueError("Derived data is stale; run extract_17lands.py build first")
    reports = {}
    for row in summary["games"]:
        game = row["game"]
        if games is not None and game not in games:
            continue
        if row["coverage"] == "unavailable":
            reports[game] = row
        else:
            data = (directory / row["path"]).read_bytes()
            if digest(data) != row.get("derived_sha256"):
                raise ValueError(f"Game {game}: derived file hash mismatch; rebuild")
            report = json.loads(data)
            if digest(cache.get(report["history_url"])) != report["history_sha256"]:
                raise ValueError(f"Game {game}: raw history changed; rebuild")
            report.update(derived_sha256=row["derived_sha256"], deck_fingerprint=row["deck_fingerprint"])
            reports[game] = report
    if games is not None and set(reports) != set(games):
        raise ValueError("Requested game is outside this event")
    return cache, reports


def parse_position(value):
    if not re.fullmatch(r"[1-9][0-9]*:(?:0|[1-9][0-9]*)", value):
        raise argparse.ArgumentTypeError("Use GAME:EVENT, for example 4:468")
    return tuple(int(part) for part in value.split(":"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "validate", "render", "context", "knowledge", "cycles", "combats"):
        command = sub.add_parser(name)
        command.add_argument("directory", type=Path)
        if name in {"init", "validate", "render"}:
            scope = command.add_mutually_exclusive_group()
            scope.add_argument("--games", type=int, nargs="+", help="Requested scope; default all event games")
            scope.add_argument("--position", action="append", type=parse_position, help="Position-only scope GAME:EVENT; repeat for several positions")
        if name == "init":
            command.add_argument("--out", required=True, type=Path)
        elif name in {"validate", "render"}:
            command.add_argument("ledger", type=Path)
            command.add_argument("--answer", type=Path, help="Check marked finding blocks in an existing answer")
        else:
            command.add_argument("--game", required=True, type=int)
            if name in {"context", "knowledge"}:
                command.add_argument("--event", required=True, type=int, help="State AFTER event; choose before the action")
            else:
                command.add_argument("--global-turn", type=int)
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text()) if hasattr(args, "ledger") else None
        games = getattr(args, "games", None)
        positions = getattr(args, "position", None)
        if positions:
            games = sorted({g for g, _ in positions})
        if hasattr(args, "game"):
            games = [args.game]
        cache, reports = load_reports(args.directory, games)
        if args.command == "init":
            if args.out.exists():
                raise ValueError("Ledger already exists; preserve review notes and reconcile it explicitly")
            write_json(args.out, make_review(reports, positions))
            print(json.dumps({"ledger": str(args.out), "games": sorted(reports), "status": "unreviewed"}))
            return 0
        if args.command in {"validate", "render", "context", "knowledge"}:
            cards, abilities = metadata(cache)
            requests = {(f["game"], f["state_event"]) for f in ledger["findings"]} if ledger else {(args.game, args.event)}
            states = {}
            for game, event in requests:
                entry = next(g for g in cache.manifest["games"] if g["game"] == game)
                states[game, event] = reconstruct(cache, entry, cards, abilities, event)["state"]
            if ledger is not None:
                result = validate_review(ledger, reports, states, args.answer.read_text() if args.answer else None, positions)
                if args.command == "render" and result["ok"]:
                    print("\n\n".join(render_finding(f) for f in ledger["findings"]))
                else:
                    print(json.dumps(result, indent=2))
                return 0 if result["ok"] else 1
            state = states[args.game, args.event]
            output = context(reports[args.game], state)
            if args.command == "knowledge":
                output["hand_knowledge"] = state["hand_knowledge"]
                output["events"] = [e for e in reports[args.game]["knowledge_events"] if e["event"] <= args.event]
        else:
            key = "turn_cycles" if args.command == "cycles" else "combats"
            output = [item for item in reports[args.game][key] if args.global_turn is None or
                      args.global_turn in item.get("global_turns", [item.get("global_turn")])]
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
