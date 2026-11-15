import unittest
from src.collector import extract_espn_events, normalize_name, normalize_profile


class CollectorTests(unittest.TestCase):
    def test_name_normalization(self):
        self.assertEqual(normalize_name("Ciryl  Gane"), "ciryl gane")
        self.assertEqual(normalize_name("José Aldo"), "jos aldo")

    def test_espn_event_mapping(self):
        payload = {"events": [{
            "id": "123", "name": "Fight Night",
            "date": "2026-11-15T20:00Z",
            "status": {"type": {"name": "STATUS_SCHEDULED"}},
            "competitions": [{"competitors": [
                {"athlete": {"id": "1", "displayName": "Fighter One"}},
                {"athlete": {"id": "2", "displayName": "Fighter Two"}}
            ]}]
        }]}
        result = extract_espn_events(payload)
        self.assertEqual(result[0]["espn_id"], "123")
        self.assertEqual(len(result[0]["competitors"]), 2)

    def test_profile_normalization_maps_documented_fields(self):
        profile = {
            "id": 42, "slug": "sample-fighter", "name": "Sample Fighter",
            "dob": "1990-01-02", "height_inches": 70, "reach_inches": 72,
            "weight_lbs": 170, "team": "Sample Team",
            "records": {"pro_mma": {
                "value": "10-2-0", "wins": 10, "losses": 2,
                "draws": 0, "no_contests": 0,
                "source": "public-records", "scope": "pro-mma"
            }},
            "images": [{
                "url": "https://commons.wikimedia.org/example.jpg",
                "artist": "Photographer", "license": "CC BY-SA 4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "source_page": "https://commons.wikimedia.org/wiki/File:Example"
            }],
            "stats": {"slpm": "3.0"},
            "career_stats": [{"scope": "pro-mma"}]
        }
        result = normalize_profile(profile, {"id": 42, "slug": "sample-fighter"})
        self.assertEqual(result["date_of_birth"], "1990-01-02")
        self.assertEqual(result["height_cm"], 177.8)
        self.assertEqual(result["reach_cm"], 182.9)
        self.assertEqual(result["weight_kg"], 77.1)
        self.assertEqual(result["record"]["value"], "10-2-0")
        self.assertEqual(result["image"]["artist"], "Photographer")
        self.assertEqual(result["image"]["license"], "CC BY-SA 4.0")
        self.assertTrue(result["source_provenance"]["image_license_credit_required"])
        self.assertNotIn("stats", result)
        self.assertNotIn("career_stats", result)


if __name__ == "__main__":
    unittest.main()
