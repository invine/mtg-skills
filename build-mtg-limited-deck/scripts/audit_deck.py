#!/usr/bin/env python3
"""Audit a normalized Limited deck against its pool; see references/deck-audit.md."""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_BASICS = ["Plains", "Island", "Swamp", "Mountain", "Forest"]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def card_counts(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a card-name-to-count object")
    for name, count in value.items():
        if not isinstance(name, str) or not name or name != name.strip():
            raise ValueError(f"{label} has an empty or untrimmed card name")
        if type(count) is not int or count < 1:
            raise ValueError(f"{label}[{name}] must be a positive integer")
    return value


def names(value, label):
    if not isinstance(value, list) or any(
        not isinstance(name, str) or not name or name != name.strip() for name in value
    ):
        raise ValueError(f"{label} must be a list of exact card names")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} contains duplicate names")
    return set(value)


def audit(data):
    if not isinstance(data, dict):
        raise ValueError("Input must be an object")
    allowed = {"deck", "pool", "land_names", "previous", "size", "unlimited_basics"}
    if set(data) - allowed:
        raise ValueError(f"Unknown fields: {sorted(set(data) - allowed)}")
    for key in ("deck", "pool", "land_names"):
        if key not in data:
            raise ValueError(f"Missing field: {key}")
    deck = card_counts(data["deck"], "deck")
    pool = card_counts(data["pool"], "pool")
    lands = names(data["land_names"], "land_names")
    basics = names(data.get("unlimited_basics", DEFAULT_BASICS), "unlimited_basics")
    size = data.get("size", 40)
    if type(size) is not int or size < 1:
        raise ValueError("size must be a positive integer")
    errors = []
    total = sum(deck.values())
    if total != size:
        errors.append(f"Deck has {total} cards; expected {size}")
    for name in sorted(deck):
        if name in basics:
            if name not in lands:
                errors.append(f"Unlimited basic missing from land_names: {name}")
        elif deck[name] > pool.get(name, 0):
            errors.append(f"{name}: deck uses {deck[name]}, pool contains {pool.get(name, 0)}")
    land_count = sum(count for name, count in deck.items() if name in lands)
    result = {
        "ok": not errors,
        "total": total,
        "expected_size": size,
        "lands": land_count,
        "nonlands": total - land_count,
        "land_breakdown": {name: deck[name] for name in sorted(deck) if name in lands},
        "errors": errors,
    }
    if "previous" in data:
        previous = card_counts(data["previous"], "previous")
        delta = {name: deck.get(name, 0) - previous.get(name, 0)
                 for name in sorted(set(deck) | set(previous))}
        result["changes"] = {
            "added": {name: count for name, count in delta.items() if count > 0},
            "removed": {name: -count for name, count in delta.items() if count < 0},
            "net_cards": sum(delta.values()),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Normalized deck JSON file, or - for stdin")
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
