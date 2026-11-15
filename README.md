# Specta Fight Data

A sport-agnostic data enrichment layer for Specta. ESPN can remain the primary event source while this project explores a normalized fighter-profile schema for future fight sports.

## Initial provider research

UFCalendar documents roster search, fighter profiles, career history, career statistics, rankings history, and a two-fighter comparison endpoint:
- API docs: https://api.ufcalendar.com/docs
- Terms: https://www.ufcalendar.com/developers/terms
- Base URL: https://api.ufcalendar.com/v1

The documentation reports 100 requests/month for new free accounts (10/minute, no card). Accounts created before 11 November 2026 retain 1,000/month. Verify your account's actual quota before implementing automated refresh. Fighter image results are Creative Commons / public-domain Wikimedia images and require the artist and license credit to be displayed.

**Important usage constraint:** the provider's terms allow caching and serving selected/transformed fields inside your own app and to your own app's users. They prohibit turning provider records into a public third-party API, dump, or data feed. Do not enable public GitHub Pages for raw provider records. Keep provider credentials server-side and return only the fields needed by Specta through a deployment model permitted by the provider.

## API endpoints of interest

- `GET /v1/fighters?q=...` — roster search
- `GET /v1/fighters/{idOrSlug}` — fighter bio
- `GET /v1/fighters/{idOrSlug}/history` — multi-promotion career timeline
- `GET /v1/fighters/{idOrSlug}/stats` — career records/statistics
- `GET /v1/fighters/{idOrSlug}/rankings` — rankings history
- `GET /v1/compare?a=...&b=...` — tale of the tape

ESPN continues to own event schedules and event/bout status in the first integration. This service only enriches athlete profiles.

## Project status

Repository scaffold and provider research are in progress. No credentials are stored here. No fighter records are bundled in this repository.

## Next integration steps

1. Add your provider key as a repository secret named `UFCAL_KEY` (never commit it).
2. Confirm the response schema against a real fighter profile and validate nullable fields.
3. Add a private-cache sync workflow that requests only fighters participating in ESPN events Specta displays.
4. Have Specta fetch the normalized selected profile fields from your own app-controlled/private delivery path.
5. Add additional provider adapters behind the same normalized schema when needed.

Project code may use the MIT license. Upstream data and images remain subject to their respective terms and licenses.
