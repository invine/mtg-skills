#!/usr/bin/env python3
"""Look up exact printing text using the event's Scryfall image identity, with verified caching."""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from extract_17lands import metadata
from seventeenlands_io import EvidenceCache, decode_json, digest

UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def download_text(url):
    if not re.fullmatch(r"https://api\.scryfall\.com/cards/" + UUID, url):
        raise ValueError("Expected an exact Scryfall printing endpoint")
    request = urllib.request.Request(url, headers={"User-Agent": "MTG-Limited-Review/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.url != url:
            raise ValueError("Unexpected printing endpoint redirect")
        return response.read(), {"status": response.status, "content_type": response.headers.get("Content-Type")}


def archive_source(cache, url):
    source = cache.sources[url]
    path = (cache.directory / source["path"]).resolve()
    if not path.is_relative_to(cache.directory.resolve()):
        raise ValueError("Text cache path escaped its directory")
    raw = path.read_bytes()
    if digest(raw) != source["sha256"]:
        raise ValueError("Text cache hash mismatch")
    relative = "versions/" + source["sha256"] + ".bin"
    destination = cache.directory / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and digest(destination.read_bytes()) != source["sha256"]:
        raise ValueError("Archived text version hash mismatch")
    if not destination.exists():
        destination.write_bytes(raw)
    versions = cache.manifest.setdefault("text_versions", {}).setdefault(url, {})
    versions.setdefault(source["sha256"], {**source, "path": relative})
    return {"url": url, **versions[source["sha256"]]}


def reference(card, cache):
    result = {"arena_card_id": card["id"], "name": card["name"], "status": "unresolved",
              "metadata": {k: card.get(k) for k in ("mana_cost", "cmc", "layout", "abilities", "image_url")}}
    image = urllib.parse.urlsplit(card.get("image_url", ""))
    match = re.search(UUID, image.path)
    if image.hostname != "cards.scryfall.io" or not match:
        result["gap"] = "No exact printing identifier; supply a verified authoritative record instead of a name guess."
        return result
    uid = match.group()
    url = "https://api.scryfall.com/cards/" + uid
    try:
        if url in cache.sources:
            archive_source(cache, url)
        record = decode_json(cache.get(url))
        source = archive_source(cache, url)
        faces = record.get("card_faces", [record])
        names = {f.get("name") for f in faces} | {record.get("name")}
        if record.get("id") != uid or card["name"] not in names:
            raise ValueError("Printing name/version does not match the Arena record")
        if card.get("layout") == "prepare" and (record.get("layout") != "prepare" or len(faces) < 2):
            raise ValueError("Prepared spell text is missing")
        if any("oracle_text" not in face or "mana_cost" not in face for face in faces):
            raise ValueError("Incomplete face text or costs")
        result.update(status="complete_text", printing_id=uid, oracle_id=record.get("oracle_id"),
            faces=[{k: f[k] for k in ("name", "mana_cost", "type_line", "oracle_text", "power", "toughness", "loyalty") if k in f} for f in faces],
            related=record.get("all_parts", []), source=source,
            caveat="Exact printing text; verify format-specific modifications and decisive rules interactions separately.")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        result["gap"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Existing 17Lands evidence directory")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--id", type=int)
    selector.add_argument("--name", help="Exact name from the event; ambiguous versions are rejected")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    try:
        cards, _ = metadata(EvidenceCache(args.directory, offline=True))
        matches = [c for c in cards.values() if c["id"] == args.id or (args.name is not None and c["name"] == args.name)]
        if len(matches) != 1:
            raise ValueError("Card missing or ambiguous; select its exact Arena ID")
        cache = EvidenceCache(args.directory / "card_text", offline=args.offline,
                              refresh=args.refresh, transport=download_text)
        result = reference(matches[0], cache)
        cache.save()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "complete_text" else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
