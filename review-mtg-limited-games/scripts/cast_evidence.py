#!/usr/bin/env python3
"""Check normalized casting evidence; see references/cast-evidence.md."""
import argparse
import json
import sys
from pathlib import Path

INTERMEDIATE = {"selected", "targets_selected", "payment_started", "stack_entered", "costs_paid"}
COMMITTED = {"cast_completed", "priority_after_cast", "resolved", "countered"}
KNOWN = INTERMEDIATE | COMMITTED | {"canceled"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def classify(attempt):
    if not isinstance(attempt, dict):
        raise ValueError("Each attempt must be an object")
    if set(attempt) - {"attempt_id", "card", "claimed_cast", "events"}:
        raise ValueError("Unknown attempt fields")
    for field in ("attempt_id", "card"):
        if not isinstance(attempt.get(field), str) or not attempt[field].strip():
            raise ValueError(f"Each attempt needs a nonempty {field}")
    if "claimed_cast" in attempt and type(attempt["claimed_cast"]) is not bool:
        raise ValueError("claimed_cast must be a boolean")
    events = attempt.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a chronological list")
    kinds = set()
    for event in events:
        if not isinstance(event, dict) or set(event) != {"kind", "source"}:
            raise ValueError("Each evidence event needs exactly kind and source")
        if not isinstance(event["kind"], str) or event["kind"] not in KNOWN:
            raise ValueError(f"Unknown evidence kind: {event['kind']}")
        if not isinstance(event["source"], str) or not event["source"].strip():
            raise ValueError("Each evidence event needs a source location")
        kinds.add(event["kind"])
    committed = bool(kinds & COMMITTED)
    canceled = "canceled" in kinds
    issues = []
    if committed and canceled:
        status = "unresolved"
        issues.append("Conflicting commitment and cancellation; inspect attempt boundaries and mapping")
    elif committed:
        status = "committed"
    elif canceled:
        status = "canceled"
    else:
        status = "unresolved"
    claimed = attempt.get("claimed_cast")
    if claimed is True and status != "committed":
        issues.append("Timeline claims a cast without confirmed commitment")
    elif claimed is False and status == "committed":
        issues.append("Timeline excludes a confirmed cast")
    return {"attempt_id": attempt["attempt_id"], "card": attempt["card"],
            "status": status, "issues": issues, "evidence": events}


def audit(data):
    if not isinstance(data, dict) or set(data) != {"attempts"}:
        raise ValueError("Input must contain exactly an attempts list")
    if not isinstance(data["attempts"], list):
        raise ValueError("attempts must be a list")
    results = []
    seen = set()
    for attempt in data["attempts"]:
        result = classify(attempt)
        if result["attempt_id"] in seen:
            raise ValueError(f"Duplicate attempt_id: {result['attempt_id']}")
        seen.add(result["attempt_id"])
        results.append(result)
    return {"ok": all(not result["issues"] for result in results), "attempts": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Normalized cast evidence JSON file, or - for stdin")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
        result = audit(json.loads(raw, object_pairs_hook=unique_object))
    except (ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
