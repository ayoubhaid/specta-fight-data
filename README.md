# Specta Fight Data

Sport-agnostic enrichment service for Specta. Current adapters: ESPN event scoreboard + UFCalendar fighter profiles. No UFC.com crawler is included.

## Providers

- **ESPN** supplies event schedule and competitor identities from its public MMA scoreboard JSON. Override the URL with `ESPN_MMA_SCOREBOARD_URL` if ESPN changes its route.
- **UFCalendar** enriches only fighters found in ESPN event cards. Profile payloads include bio, records, career statistics, and Wikimedia Commons/CC portraits with required artist/license credit.
- **Wikimedia Commons** is the image provenance represented by UFCalendar's returned image metadata. The app must show the artist and license whenever it displays a portrait.

The collector intentionally does not request odds, odds history, pick'em, predictions, or any betting-related fields.

## Run locally

Python 3.10+; standard library only.

```bash
export UFCAL_KEY="your-key"
python -m src.collector
```

Windows PowerShell:

```powershell
$env:UFCAL_KEY="your-key"
python -m src.collector
```

Optional:
- `ESPN_MMA_SCOREBOARD_URL`
- `FIGHT_DATA_CACHE` (default `data/cache/fight-data.json`)

The local cache is git-ignored. Do not commit provider records or API keys. The UFCalendar free quota for new accounts is currently 100 requests/month, so the collector only looks up previously unseen ESPN competitors and caches profiles. Each new profile costs a roster search + profile request. Do not schedule frequent full refreshes.

## Output shape

`data/cache/fight-data.json` contains:
- `events[]`: ESPN event + competitor rows
- `fighters{}`: normalized profile keyed by normalized name
- `image`: URL + artist + license + attribution URL

Unknown fields stay null. Name joins are exact only; ambiguous matches are skipped.

## Terms / delivery

UFCalendar permits showing its facts in your own app and storing them in your own systems, but prohibits exposing its records as a third-party API or public downloadable data dump. This repository is public, so the generated cache is not committed or published through GitHub Pages. Keep it private/local or use a delivery path that serves data only to Specta and its users, consistent with the provider terms.

UFCalendar docs: https://api.ufcalendar.com/docs
UFCalendar terms: https://www.ufcalendar.com/developers/terms

## Tests

```bash
python -m unittest discover -s tests -v
```
