# Specta Fight Data

A sport-agnostic data enrichment layer for Specta. ESPN can remain the primary event source while this project explores normalized fighter-profile data.

## Local UFC HTML parser (learning tool)

This parser reads **HTML files already saved on your device**. It makes no HTTP requests, does not crawl UFC.com, and does not bypass access controls.

It extracts only the selectors in the supplied walkthrough:
- `.hero__title` — fighter name
- `.hero__nickname` — nickname
- `.hero__record` — displayed record

The supplied walkthrough does not establish selectors for reach, stance, height, stats, portraits, or fight history, so those fields remain null/empty rather than being guessed.

### Run it

Requires Python 3.10+; no third-party packages.

```bash
python -m src.ufc_html_parser path/to/saved-athlete.html --output fighters.local.json
```

Or pass a directory containing saved `.html` files:

```bash
python -m src.ufc_html_parser ./saved-athlete-pages/ -o fighters.local.json
```

The output is a local JSON file. Review source terms before collecting or reusing any page content. Do not commit saved athlete-page HTML or copied provider records to this public repository.

### Tests

```bash
python -m unittest discover -s tests -v
```

## Other provider research

UFCalendar documents roster search, fighter profiles, career history, career statistics, rankings history, and comparison:
- API docs: https://api.ufcalendar.com/docs
- Terms: https://www.ufcalendar.com/developers/terms
- Base URL: https://api.ufcalendar.com/v1

Verify the quota shown by your own account. Keep API credentials out of Android clients and out of Git. Provider data and image assets remain subject to their respective terms and licenses.

## Architecture

ESPN remains the event/bout source. Provider adapters enrich fighter profiles into `schemas/fighter.schema.json`. Keep source provenance, treat unknown values as null, and never silently join ambiguous athlete matches.
