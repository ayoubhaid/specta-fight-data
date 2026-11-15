# Provider notes

## UFCalendar

Official docs: https://api.ufcalendar.com/docs

Documented fighter endpoints include search, profile, career history, career statistics, rankings history, and comparison. Responses use a `data` and `meta` envelope. The provider documents 100 monthly requests for new free accounts, 10 requests/minute, and a no-card free tier. Older accounts created before 11 November 2026 retain 1,000 monthly requests.

Use conditional GET support (ETag) where possible, cache successful results, and do not poll individual fighters on every app launch. Do not expose the upstream API key in Android. Terms allow selected/transformed fields to be served by your own backend to your own app/users, but prohibit redistribution as a public data API or downloadable dataset.

Fighter portraits are sourced from Wikimedia Commons / Creative Commons; show the returned artist and license credit whenever an image is rendered.

## ESPN

Retain the existing ESPN integration for event scheduling and bouts. Match athletes by a stable ID where available; use conservative name normalization only as a fallback. Never silently join ambiguous matches.

## Normalized fighter fields

Suggested optional fields:
- identity: provider id, slug, display name, nickname
- profile: nationality/country code, date of birth, age, hometown
- physical: height, reach, stance, division
- record: wins, losses, draws, no contests, display record
- statistics: striking, takedown, submission metrics with source scope
- image: URL, artist, license, attribution URL
- career: history rows with opponent, event, date, outcome, method, round and time
- provenance: source, retrieval timestamp, confidence where supplied

Treat unknown values as null, not zero. Stats scoped to different promotions must not be mixed.
