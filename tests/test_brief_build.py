"""Acceptance tests for the standalone daily brief renderer."""
import json
import pathlib
import re
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "brief" / "build.py"


class BriefBuildAcceptanceTest(unittest.TestCase):
    def test_build_py_renders_content_json_into_a_self_contained_html_brief(self):
        """Invoke brief/build.py with content.json and verify rendered HTML."""
        with __import__("tempfile").TemporaryDirectory() as directory:
            tmp_path = pathlib.Path(directory)
            content = json.loads((ROOT / "brief" / "examples" / "content.example.json").read_text())
            # Replace the example's intentional remote artwork so this checks all
            # loaded assets rather than content URLs chosen by the fixture.
            content["hero"] = {"svg": '<svg aria-label="test artwork"></svg>'}
            content["credit"] = []
            for section in content.get("sections", []):
                for item in section.get("items", []):
                    for avatar in item.get("avatars", []):
                        avatar.pop("url", None)
            for event in content.get("day", []):
                event.pop("seed", None)
                for avatar in event.get("who", []):
                    avatar.pop("url", None)
            content["title"] = "Renderer acceptance test title"
            content["push"]["seed"] = ""
            content["push"]["srcs"] = []
            content["day_srcs"] = []
            content["standfirst"] = "Renderer acceptance test standfirst"
            fixture = tmp_path / "content.json"
            fixture.write_text(json.dumps(content))
            output = tmp_path / "brief.html"

            subprocess.run(
                [sys.executable, str(BUILD), str(fixture), str(output)],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            rendered = output.read_text()

            self.assertIn("<title>Renderer acceptance test title</title>", rendered)
            self.assertIn("Renderer acceptance test title", rendered)
            self.assertIn("Renderer acceptance test standfirst", rendered)
            self.assertIn("Sign the Q3 scope change before standup", rendered)
            self.assertNotIn("{{", rendered)
            self.assertNotIn("__FONT_B64__", rendered)
            self.assertRegex(rendered, re.compile(r"<style\b[^>]*>.*?</style\s*>", re.DOTALL))
            self.assertRegex(rendered, re.compile(r"<script\b[^>]*>.*?</script\s*>", re.DOTALL))
            self.assertIn("data:image/jpeg;base64,", rendered)
            self.assertTrue("data:font/" in rendered or "data:application/font-woff" in rendered)
            # Hyperlinks in content are expected; externally loaded assets are not.
            self.assertIsNone(re.search(
                r"<(?:script|link|img)\b[^>]*(?:src|href)=\"https?://",
                rendered,
                re.IGNORECASE,
            ))


if __name__ == "__main__":
    unittest.main()
