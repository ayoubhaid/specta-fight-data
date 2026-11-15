"""Build a private/local Specta fight-data cache from ESPN events + UFCalendar profiles.

No UFC website scraping. No odds, picks, predictions, or betting fields are requested.
"""
from __future__ import annotations

import json
import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UF_BASE = "https://api.ufcalendar.com/v1"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
USER_AGENT = "SpectaFightData/0.1 (personal project)"
CACHE_PATH = Path(os.getenv("FIGHT_DATA_CACHE", "data/cache/fight-data.json"))
TARGETS_PATH = Path(os.getenv("FIGHT_DATA_TARGETS", "data/targets.json"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_name(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def request_json(url: str, api_key: str | None = None, etag: str | None = None) -> tuple[Any, dict[str, str], int]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if etag:
        headers["If-None-Match"] = etag
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")), dict(response.headers.items()), response.status
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return None, dict(exc.headers.items()), 304
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"HTTP {exc.code} for {url}: {detail}") from exc


def read_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {"schema_version": 1, "generated_at": None, "events": [], "fighters": {}}


def write_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = CACHE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(CACHE_PATH)


def extract_espn_events(payload: dict) -> list[dict]:
    """Extract event and competitor identities from ESPN's public scoreboard JSON."""
    events = []
    for event in payload.get("events", []):
        competitions = event.get("competitions") or []
        competition = competitions[0] if competitions else {}
        competitors = []
        for item in competition.get("competitors", []):
            athlete = item.get("athlete") or {}
            name = athlete.get("displayName") or athlete.get("fullName") or item.get("displayName")
            if name:
                competitors.append({
                    "espn_id": str(athlete.get("id") or item.get("id") or ""),
                    "name": name,
                    "abbreviation": athlete.get("shortName"),
                    "winner": item.get("winner"),
                    "home_away": item.get("homeAway")
                })
        events.append({
            "espn_id": str(event.get("id") or ""),
            "name": event.get("name") or event.get("shortName") or "UFC event",
            "date": event.get("date"),
            "status": ((event.get("status") or {}).get("type") or {}).get("name"),
            "competitors": competitors
        })
    return events


def fetch_espn_events() -> list[dict]:
    url = os.getenv("ESPN_MMA_SCOREBOARD_URL", ESPN_BASE)
    payload, _, _ = request_json(url)
    if not isinstance(payload, dict):
        raise RuntimeError("ESPN scoreboard response was not a JSON object")
    return extract_espn_events(payload)


def uf_get(path: str, api_key: str, params: dict | None = None) -> dict:
    query = urllib.parse.urlencode(params or {})
    url = f"{UF_BASE}/{path.lstrip('/')}" + (f"?{query}" if query else "")
    payload, _, status = request_json(url, api_key=api_key)
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected UFCalendar response for {path}")
    if "error" in payload:
        raise RuntimeError(f"UFCalendar error: {payload['error']}")
    return payload


def find_fighter(name: str, api_key: str) -> dict | None:
    result = uf_get("fighters", api_key, {"q": name, "org": "ufc", "limit": 10})
    rows = result.get("data") or []
    target = normalize_name(name)
    exact = [row for row in rows if normalize_name(row.get("name")) == target]
    if len(exact) == 1:
        return exact[0]
    # Never auto-join ambiguous or fuzzy name matches.
    return None


def normalize_profile(profile: dict, fighter_ref: dict) -> dict:
    """Keep a stable Specta DTO while retaining source fields for future schema growth."""
    records = profile.get("records") or {}
    stats = profile.get("stats")
    image = profile.get("image")
    if isinstance(image, dict):
        normalized_image = {
            "url": image.get("url"),
            "artist": image.get("artist"),
            "license": image.get("license"),
            "attribution_url": image.get("attribution_url") or image.get("source_url")
        }
    else:
        normalized_image = None

    return {
        "schema_version": 1,
        "provider": "ufcalendar",
        "provider_id": str(profile.get("id") or fighter_ref.get("id")),
        "slug": profile.get("slug") or fighter_ref.get("slug"),
        "name": profile.get("name") or fighter_ref.get("name"),
        "nickname": profile.get("nickname"),
        "nationality": profile.get("nationality") or fighter_ref.get("nationality"),
        "country_code": profile.get("country_code") or fighter_ref.get("country_code"),
        "date_of_birth": profile.get("date_of_birth"),
        "age": profile.get("age"),
        "height_cm": profile.get("height_cm"),
        "reach_cm": profile.get("reach_cm"),
        "stance": profile.get("stance"),
        "division": profile.get("division"),
        "record": records.get("pro_mma") if isinstance(records, dict) else None,
        "promotion_records": records,
        "career_stats": stats if stats is not None else profile.get("career_stats"),
        "image": normalized_image,
        "source_provenance": {
            "profile": "UFCalendar Fight API",
            "image_license_credit_required": bool(normalized_image and normalized_image.get("url"))
        },
        "retrieved_at": utc_now()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-history", action="store_true", help="Fetch full career timelines for newly discovered fighters (one extra API request each).")
    parser.add_argument("--include-rankings", action="store_true", help="Fetch ranking history for newly discovered fighters (one extra API request each).")
    args = parser.parse_args()
    api_key = os.getenv("UFCAL_KEY")
    if not api_key:
        print("Missing UFCAL_KEY. Add it as an environment variable; never commit it.", file=sys.stderr)
        return 2

    cache = read_cache()
    try:
        events = fetch_espn_events()
    except Exception as exc:
        print(f"ESPN fetch failed: {exc}", file=sys.stderr)
        return 1

    existing = cache.get("fighters") or {}
    names = sorted({
        competitor["name"]
        for event in events
        for competitor in event.get("competitors", [])
        if competitor.get("name")
    })
    # Stay within the free quota: profile requests are made only for newly seen fighters.
    for name in names:
        key = normalize_name(name)
        if key in existing and existing[key].get("provider_id"):
            continue
        try:
            ref = find_fighter(name, api_key)
            if not ref:
                print(f"UNMATCHED/AMBIGUOUS: {name}")
                continue
            profile_response = uf_get(f"fighters/{urllib.parse.quote(str(ref.get('slug') or ref.get('id')), safe='')}", api_key)
            profile = profile_response.get("data") or {}
            normalized = normalize_profile(profile, ref)
            # History and rankings are opt-in to protect the small free monthly quota.
            if args.include_history:
                normalized["history"] = (uf_get(
                    f"fighters/{urllib.parse.quote(str(ref.get('slug') or ref.get('id')), safe='')}/history",
                    api_key
                ).get("data") or [])
                time.sleep(6.2)
            else:
                normalized["history"] = []
            if args.include_rankings:
                normalized["rankings_history"] = (uf_get(
                    f"fighters/{urllib.parse.quote(str(ref.get('slug') or ref.get('id')), safe='')}/rankings",
                    api_key
                ).get("data") or [])
                time.sleep(6.2)
            else:
                normalized["rankings_history"] = []
            existing[key] = normalized
            print(f"ADDED: {name}")
            # Keep request rate below the documented 10/minute cap.
            time.sleep(6.2)
        except Exception as exc:
            print(f"PROFILE ERROR {name}: {exc}", file=sys.stderr)

    cache.update({
        "schema_version": 1,
        "generated_at": utc_now(),
        "event_source": "ESPN public scoreboard",
        "fighter_source": "UFCalendar Fight API",
        "events": events,
        "fighters": existing
    })
    write_cache(cache)
    print(f"Saved {len(events)} ESPN events and {len(existing)} cached fighter profiles to {CACHE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
