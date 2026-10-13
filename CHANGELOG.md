# Changelog

All notable changes to **daily-brief** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Dates use the
`YYYY-MM-DD` of the change.

## [v0.1.0] - 2026-10-13

First release: the self-contained daily briefing pipeline, plus a hardening pass over the
renderer and the first definition of the implementation scope (`IMPROVEMENTS.md`,
IMP-1…IMP-7). No change to the `content.json` contract or the `brief/SPEC.md` run behaviour.

### Added

- **`brief/build.py`** — renders `content.json` into a single self-contained HTML newspaper
  (CSS, embedded font and hero wash inlined); fails loudly on an unfilled template slot or on
  content that violates the schema.
- **`brief/shell.html`** — the page: all CSS, layout and the client-side *Copy for Claude*
  loop (tick semantics, feedback boxes, day rail, copy-to-Markdown).
- **`brief/SPEC.md`** and **`brief/content.schema.md`** — the run spec (switches, Phase 1
  task sync, Phase 2 content selection, seeds, voice, build & deliver) and the `content.json`
  contract.
- **NGA hero paintings.** `brief/paintings.json` is a curated manifest of public-domain
  paintings with IIIF URLs and real artist/year credit lines; `hero-fallback.b64` covers any
  network failure. `scripts/build_manifest.py` regenerates the manifest from
  [NGA Open Data](https://github.com/NationalGalleryOfArt/opendata) (CC0).
- **Embedded masthead font.** Fraunces (OFL) is baked in as base64 so the brief works
  offline (`fraunces-600.b64`).
- **Vault integration.** Reads `TASKS.md`/`DELEGATED.md`, so *Owed to you* (passed chase
  dates) and *Gone quiet* (unchased commitments) work from your own files.
- **Scheduler materials.** `task/scheduler-prompt.md` (works with Claude Cowork, Hermes cron,
  or plain OS cron) and `task/brief.css`, an optional editor/console preview theme.
- **`IMPROVEMENTS.md`** — the authoritative scope of record (IMP-1…IMP-7), each item small,
  in-repo and independently verifiable.
- **`content.json` validation.** `build.py` checks input against `brief/content.schema.md`
  and exits non-zero naming the offending field (e.g.
  `sections[2].items[0].act must be one of done, seen, stale`) instead of raising a
  `KeyError`/`ValueError` traceback (IMP-2).
- **A real command-line interface.** `build.py` uses `argparse`; `python3 brief/build.py
  --help` exits `0` with usage, and a missing or malformed JSON input fails with a one-line
  message rather than a traceback (IMP-5).
- **A test suite that actually observes the renderer.** `tests/test_brief_build.py` renders
  the shipped example unmodified under the acceptance criterion title *renders content.json
  into a self-contained HTML brief*, plus regression tests for IMP-1…IMP-5 (IMP-6, IMP-7).
- **`LICENSE`** (MIT) and **`CHANGELOG.md`**.

### Fixed

- **The *Let's do it* button was a dead link.** `{{PUSH_SEED}}` was passed through
  `json.dumps`, so the anchor rendered as `href=""https://claude.ai/new?q=…""` — an empty
  `href`. It is now HTML-attribute-escaped and links to the full
  `https://claude.ai/new?q=…&surface=cowork&composer=mini` work order (IMP-1).
- **Untrusted text could close the data `<script>` block.** Content-derived JSON embedded in
  the page now escapes `<`, `>`, `&` and the U+2028/U+2029 line separators, so a meeting
  name, push seed or avatar id such as `</script><script>…` cannot inject markup (IMP-3).
- **Untrusted text could inject attributes.** Avatar `title`/`src` and the day-rail
  time/name/hover text are HTML-escaped at the build boundary instead of only having `<`
  stripped, closing `"`-based attribute injection (IMP-4).
- **Missing shell template** (`d66d7a2`, 2026-08-27) — `brief/shell.html` was absent from the
  repository, so `build.py` could not find its template and the build failed. The template is
  now included.

### Changed

- `brief/content.schema.md` gains a **Validation** section; `brief/SPEC.md`'s build step
  notes that the build also fails loudly on contract-violating content.

[v0.1.0]: https://github.com/kawaiier/daily-brief/releases/tag/v0.1.0
