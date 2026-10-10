"""Public 17Lands retrieval and a hash-checked, offline-readable evidence cache."""
import gzip
import hashlib
import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ORIGIN = "https://www.17lands.com"
CACHE_VERSION = 1
ROUTES = {"event": "/data/event_details", "info": "/data/history_info/", "history": "/data/history",
          "cards": "/data/cards", "abilities": "/data/abilities"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def decode_json(raw):
    if raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Expected JSON or gzip JSON; inspect the cached response") from exc


def parse_event_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc not in {"www.17lands.com", "17lands.com"}:
        raise ValueError("Use a public https://www.17lands.com event URL")
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2 or parts[0] not in {"details", "history", "deck", "pool", "draft", "picks"}:
        raise ValueError("Expected a details, history, deck, pool, draft, or picks URL")
    if not re.fullmatch(r"[0-9a-f]{32}", parts[1]):
        raise ValueError("Invalid event identifier")
    return parts[1]


def enumerate_games(event):
    details = event.get("details") if isinstance(event, dict) else None
    if not isinstance(details, dict) or not isinstance(details.get("match_results"), list):
        raise ValueError("Unsupported event schema: expected details.match_results")
    games = []
    for match_index, match in enumerate(details["match_results"]):
        if not isinstance(match, dict) or not isinstance(match.get("game_results"), list):
            raise ValueError(f"Unsupported match {match_index}: expected game_results")
        for game_index, game in enumerate(match["game_results"]):
            if not isinstance(game, dict):
                raise ValueError("A game result must be an object")
            games.append({"game": len(games) + 1, "match_index": match_index,
                          "game_index": game_index, "result": game})
    return games


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "MTG-Limited-Review/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if urllib.parse.urlsplit(response.url).netloc not in {"www.17lands.com", "17lands.com"}:
            raise ValueError("Unexpected redirect outside 17Lands")
        return response.read(), {"status": response.status,
                                 "content_type": response.headers.get("Content-Type"),
                                 "final_url": response.url}


def referenced_ids(history):
    cards, abilities = set(), set()
    for index, event in enumerate(history["events"]):
        try:
            if not isinstance(event, dict):
                raise ValueError("expected an event object")
            message = event.get("gameStateMessage", {})
            if not isinstance(message, dict) or not isinstance(message.get("gameObjects", []), list):
                raise ValueError("expected gameStateMessage.gameObjects list")
            for obj in message.get("gameObjects", []):
                if not isinstance(obj, dict):
                    raise ValueError("expected a game object")
                target = abilities if obj.get("type") == "GameObjectType_Ability" else cards
                if obj.get("grpId"):
                    target.add(obj["grpId"])
                if obj.get("objectSourceGrpId"):
                    cards.add(obj["objectSourceGrpId"])
                abilities.update(obj.get("abilities", []))
                abilities.update(a["grpId"] for a in obj.get("uniqueAbilities", []))
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"Unsupported history event:{index}: {exc}") from exc
    if any(type(value) is not int for value in cards | abilities):
        raise ValueError("Expected integer card and ability identifiers in history events")
    return cards, abilities


class EvidenceCache:
    def __init__(self, directory, *, offline=False, refresh=False, transport=download):
        self.directory = Path(directory)
        self.offline, self.refresh, self.transport = offline, refresh, transport
        path = self.directory / "manifest.json"
        self.manifest = json.loads(path.read_text()) if path.exists() else {
            "cache_version": CACHE_VERSION, "sources": {}}
        if self.manifest.get("cache_version") != CACHE_VERSION:
            raise ValueError("Unsupported cache version; preserve raw evidence and use a new directory")
        self.sources = self.manifest["sources"]
        self.retrieved_this_run = set()

    def get(self, url):
        source = self.sources.get(url)
        if source and (self.offline or not self.refresh or url in self.retrieved_this_run):
            path = (self.directory / source["path"]).resolve()
            if not path.is_relative_to(self.directory.resolve()):
                raise ValueError("Cache path must remain inside its directory")
            raw = path.read_bytes()
            if digest(raw) != source["sha256"]:
                raise ValueError(f"Cache hash mismatch: {source['path']}")
            return raw
        if self.offline:
            raise ValueError(f"Offline cache lacks {url}")
        raw, metadata = self.transport(url)
        relative = "raw/" + digest(url.encode()) + ".bin"
        path = self.directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.sources[url] = {"url": url, "path": relative, "sha256": digest(raw),
                             "retrieved_at": datetime.now(timezone.utc).isoformat(), **metadata}
        self.retrieved_this_run.add(url)
        return raw

    def json(self, route, **params):
        url = ORIGIN + route + "?" + urllib.parse.urlencode(params)
        return decode_json(self.get(url)), url

    def save(self):
        write_json(self.directory / "manifest.json", self.manifest)


def retrieve(url, cache):
    """Fetch the whole event; preserve failed games as explicit coverage entries."""
    event_id = parse_event_url(url)
    old_id = cache.manifest.get("event_id")
    if old_id and old_id != event_id:
        raise ValueError("Cache belongs to a different event; select another output directory")
    cache.manifest["event_id"] = event_id
    try:
        page_url = ORIGIN + "/details/" + event_id
        html = cache.get(page_url).decode("utf-8")
        match = re.search(r'src=[\"\'](/static/Routes\.[^\"\']+\.js)[\"\']', html)
        if not match:
            raise ValueError("Frontend Routes bundle not found; inspect current public page source")
        frontend_url = ORIGIN + match.group(1)
        frontend = cache.get(frontend_url)
        if any(route.encode() not in frontend for route in ROUTES.values()):
            raise ValueError("Frontend endpoint contract changed; inspect source before adapting retrieval")
        cache.manifest["frontend"] = {"url": frontend_url, "sha256": digest(frontend)}
        event, event_url = cache.json(ROUTES["event"], draft_id=event_id)
        games = enumerate_games(event)
        cache.manifest.update(event_url=event_url, games=games)

        def fetch_game(entry):
            entry = dict(entry)
            try:
                info, info_url = cache.json(ROUTES["info"], draft_id=event_id,
                                           match_index=entry["match_index"], game_index=entry["game_index"])
                entry["info_url"] = info_url
                if not isinstance(info, dict) or not isinstance(info.get("history_path"), str):
                    raise ValueError("Missing history_path; replay may be unavailable")
                if not isinstance(info.get("deck_build"), dict):
                    raise ValueError("Missing played deck_build")
                history, history_url = cache.json(ROUTES["history"], history_path=info["history_path"])
                entry["history_url"] = history_url
                if not isinstance(history, dict) or not isinstance(history.get("events"), list):
                    raise ValueError("Missing history events")
                card_ids, ability_ids = referenced_ids(history)
                entry.update(card_ids=sorted(card_ids), ability_ids=sorted(ability_ids))
                entry["status"] = "downloaded"
            except (ValueError, OSError) as exc:
                entry.update(status="unavailable", error=str(exc))
            return entry

        with ThreadPoolExecutor(max_workers=3) as executor:
            games = list(executor.map(fetch_game, games))
        cache.manifest["games"] = games
        card_ids, ability_ids = set(), set()
        for game in games:
            if game["status"] != "downloaded":
                continue
            info = decode_json(cache.get(game["info_url"]))
            for group in info["deck_build"].get("groups", []):
                card_ids.update(group.get("cards", []))
            card_ids.update(game["card_ids"])
            ability_ids.update(game["ability_ids"])
        for key, ids, route in [("cards", card_ids, ROUTES["cards"]), ("abilities", ability_ids, ROUTES["abilities"])]:
            urls = []
            for offset in range(0, len(ids), 150):
                data, source_url = cache.json(route, ids=",".join(map(str, sorted(ids)[offset:offset + 150])))
                if not isinstance(data, dict) or not isinstance(data.get(key), list):
                    raise ValueError(f"Unsupported {key} response")
                urls.append(source_url)
            cache.manifest[key + "_urls"] = urls
        return cache.manifest
    finally:
        cache.save()
