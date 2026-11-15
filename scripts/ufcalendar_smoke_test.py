"""Small authenticated UFCalendar smoke test; prints no API key or raw response."""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://api.ufcalendar.com/v1"
KEY = os.getenv("UFCAL_KEY")
if not KEY:
    raise SystemExit("UFCAL_KEY secret is missing.")

def get(path):
    request = urllib.request.Request(
        f"{BASE}/{path}",
        headers={"Authorization": f"Bearer {KEY}", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read().decode("utf-8")), response.headers
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        try:
            detail = json.loads(body).get("error", {}).get("message", "request failed")
        except Exception:
            detail = "request failed"
        raise RuntimeError(f"HTTP {error.code}: {detail}") from error

usage, usage_headers = get("usage")
usage_data = usage.get("data") or {}
print("AUTHENTICATION: OK")
print("PLAN:", usage_data.get("tier", "not reported"))
print("MONTHLY REQUESTS USED:", usage_data.get("requests_used", "not reported"))
print("MONTHLY REQUEST LIMIT:", usage_data.get("requests_limit", "not reported"))
print("REQUESTS PER MINUTE:", usage_data.get("rpm_limit", "not reported"))

fighter, _ = get("fighters/ciryl-gane")
data = fighter.get("data") or {}
if not data:
    raise SystemExit("Fighter endpoint responded, but returned no data for the test slug.")
print("FIGHTER PROFILE: OK")
print("NAME:", data.get("name", "not reported"))
print("PROFILE FIELDS:", ", ".join(sorted(data.keys())))
print("SMOKE TEST: PASSED")
