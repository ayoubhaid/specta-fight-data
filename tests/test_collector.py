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

    def test_profile_normalization_preserves_image_credit(self):
        profile = {
            "id": 42, "slug": "sample-fighter", "name": "Sample Fighter",
            "records": {"pro_mma": {"value": "10-2-0"}},
            "image": {"url": "https://commons.wikimedia.org/example.jpg",
                      "artist": "Photographer", "license": "CC BY-SA 4.0",
                      "attribution_url": "https://commons.wikimedia.org/wiki/File:Example"}
        }
        result = normalize_profile(profile, {"id": 42, "slug": "sample-fighter"})
        self.assertEqual(result["record"]["value"], "10-2-0")
        self.assertEqual(result["image"]["artist"], "Photographer")
        self.assertTrue(result["source_provenance"]["image_license_credit_required"])


if __name__ == "__main__":
    unittest.main()
