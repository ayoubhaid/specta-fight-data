import unittest

from src.ufc_html_parser import parse_athlete_html


class ParserTests(unittest.TestCase):
    def test_extracts_walkthrough_fields(self):
        html = """
        <main>
          <h1 class="hero__title">Sample Athlete</h1>
          <div class="hero__nickname">The Example</div>
          <div class="hero__record"><span>20</span>-<span>4</span>-<span>1</span></div>
        </main>
        """
        result = parse_athlete_html(html, "sample-athlete.html")
        self.assertEqual(result["name"], "Sample Athlete")
        self.assertEqual(result["nickname"], "The Example")
        self.assertEqual(result["record"]["display"], "20 - 4 - 1")
        self.assertEqual(result["provider"], "ufc_html_local_sample")

    def test_missing_name_fails_loudly(self):
        with self.assertRaises(ValueError):
            parse_athlete_html("<div class='hero__record'>1-0</div>")


if __name__ == "__main__":
    unittest.main()
