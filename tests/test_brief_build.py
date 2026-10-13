"""Acceptance and regression tests for the standalone daily brief renderer.

Run: python3 -m unittest discover -s tests -v

The suite is offline and deterministic: it renders the shipped example and a few
hostile fixtures through brief/build.py and inspects the resulting HTML. It never
stubs the renderer, so each test fails if the behaviour it names breaks.
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "brief" / "build.py"
EXAMPLE = ROOT / "brief" / "examples" / "content.example.json"


def load_example():
    return json.loads(EXAMPLE.read_text())


def js_literal(rendered, name):
    """Decode `const <name> = ...;` from the rendered page's script block."""
    match = re.search(r"const %s = (.*?);\n" % name, rendered, re.DOTALL)
    if match is None:
        raise AssertionError("no %s literal in the rendered page" % name)
    return json.loads(match.group(1))


def run_build(content=None, argv=None):
    """Run build.py against a content dict (or extra argv); return (proc, rendered)."""
    with tempfile.TemporaryDirectory() as directory:
        directory = pathlib.Path(directory)
        out = directory / "brief.html"
        if argv is None:
            src = directory / "content.json"
            src.write_text(content if isinstance(content, str) else json.dumps(content))
            cmd = [sys.executable, str(BUILD), str(src), str(out)]
        else:
            cmd = [sys.executable, str(BUILD), *argv]
        proc = subprocess.run(cmd, cwd=directory, capture_output=True, text=True)
        rendered = out.read_text() if out.exists() else None
    return proc, rendered


class BriefBuildAcceptanceTest(unittest.TestCase):
    def test_renders_content_json_into_a_self_contained_html_brief(self):
        """renders content.json into a self-contained HTML brief"""
        # Render the shipped example exactly as a run would — no stubbing and no
        # fixture rewriting — so this observes the real renderer output.
        proc, rendered = run_build(load_example())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIsNotNone(rendered)
        content = load_example()

        # content.json shows up, escaped and rendered.
        self.assertIn(f"<title>{content['title']}</title>", rendered)
        self.assertIn(content["masthead"], rendered)
        self.assertIn(content["standfirst"], rendered)
        first = content["sections"][0]["items"][0]
        self.assertIn(first["title"], rendered)
        self.assertIn(first["body"], rendered)

        # Every slot was filled.
        self.assertNotIn("{{", rendered)
        self.assertNotIn("__FONT_B64__", rendered)
        self.assertIsNone(re.search(r"__[A-Z0-9_]+__", rendered))

        # Self-contained: styles, font and hero wash travel with the file.
        self.assertRegex(rendered, re.compile(r"<style\b[^>]*>.*?</style\s*>", re.DOTALL))
        self.assertIn("@font-face", rendered)
        self.assertIn("data:font/", rendered)
        self.assertIn("data:image/jpeg;base64,", rendered)

        # No external asset loads: CSS, fonts and scripts are inline. Content
        # hyperlinks and the hotlinked hero <img> are content, not page assets.
        self.assertIsNone(re.search(r"<link\b[^>]*href=\"https?://", rendered, re.I))
        self.assertIsNone(re.search(r"<script\b[^>]*\bsrc=\"https?://", rendered, re.I))
        self.assertIsNone(re.search(r"url\(\s*['\"]?https?://", rendered, re.I))

    def test_push_seed_link_is_well_formed(self):
        """The highest-leverage action on the page links to the full seed URL."""
        proc, rendered = run_build(load_example())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        match = re.search(r'<a class="cta"[^>]*\bhref="([^"]*)"', rendered)
        self.assertIsNotNone(match, "the Let's do it CTA has no href")
        href = html.unescape(match.group(1))
        self.assertTrue(href.startswith("https://claude.ai/new?q="), href)
        self.assertIn("&surface=cowork&composer=mini", href)

    def test_gathered_text_cannot_break_out_of_the_script_block(self):
        """A hostile meeting name or seed cannot terminate the data <script>."""
        content = load_example()
        payload = "</script><script>alert(1)</script>"
        content["day"][0]["n"] = payload
        content["day"][0]["h"] = payload
        content["push"]["seed"] = payload
        proc, rendered = run_build(content)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(payload, rendered)
        self.assertNotIn("<script>alert(1)", rendered)
        self.assertEqual(rendered.lower().count("<script"), 1)
        self.assertEqual(rendered.lower().count("</script>"), 1)

    def test_gathered_text_is_escaped_before_it_reaches_the_page(self):
        """Avatar names/URLs and day text are escaped at the build boundary."""
        content = load_example()
        injected = '<img src=x onerror=alert(1)>'
        content["day"][0]["n"] = injected
        content["day"][0]["who"] = [
            {"i": 'x" onmouseover="alert(1)', "url": 'x" onerror="alert(1)'}
        ]
        proc, rendered = run_build(content)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # Raw injected markup must not survive into the document.
        self.assertNotIn("<img src=x onerror=", rendered)
        self.assertNotIn('onmouseover="alert(1)', rendered)

        # The data the shell inserts with innerHTML is HTML-escaped.
        day = js_literal(rendered, "DAY")
        self.assertEqual(day[0]["n"], html.escape(injected))
        who_key = content["day"][0]["who"][0]["i"]
        registry = js_literal(rendered, "A")
        self.assertEqual(registry[who_key][0], html.escape(who_key))
        self.assertEqual(registry[who_key][2], html.escape('x" onerror="alert(1)'))

    def test_invalid_content_fails_loudly_without_a_traceback(self):
        """A missing or malformed field is reported by name, not as a traceback."""
        missing = load_example()
        del missing["title"]
        proc, rendered = run_build(missing)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIsNone(rendered)
        self.assertIn("title", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

        malformed = load_example()
        malformed["date"] = "21-08-2026"
        proc, rendered = run_build(malformed)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("date", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_cli_help_exits_zero(self):
        proc, _ = run_build(argv=["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("usage", proc.stdout.lower())

    def test_missing_input_file_fails_cleanly(self):
        proc, _ = run_build(argv=["does-not-exist.json", "brief.html"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
