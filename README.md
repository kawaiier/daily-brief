# The Daily Brief

A self-contained daily briefing — the one page you open before deciding what to work on.

This project rebuilds the *Dia* browser's Daily Briefing as a **plain, local, tool-agnostic
pipeline**: a scheduled task gathers your work stream (email, calendar, tickets, chat, notes),
writes one `content.json`, and a tiny Python script renders it into a single self-contained
HTML newspaper. No browser, no cloud service, no vendor lock-in — the design lives in the repo,
the content lives in your vault.

The design is adapted from a [Reddit post](https://www.reddit.com/r/diabrowser/comments/1vuqdcp/i_recreated_the_daily_briefing_in_claude_cowork/)
by a Claude Cowork user who rebuilt Dia's Daily Briefing as a scheduled task. This version
keeps the original architecture (SPEC → content → build → HTML) and generalizes it so you can
run it with **any** agent or scheduler you already use.

## Why

Dia's briefing is a nice idea — but it's tied to a browser, a $20–$100/mo tier, and a fixed set
of connectors. The version in this repo:

- **Runs anywhere.** A scheduled task on Claude Cowork, a cron job on your own Hermes setup, a
  plain `launchd`/Task Scheduler entry. The pipeline is just Python + JSON + HTML.
- **Knows what no browser extension can.** It reads your own `TASKS.md` and `DELEGATED.md`
  files, so sections like *Owed to you* (chase dates you've let slip) and *Gone quiet*
  (commitments nobody is chasing) actually work.
- **Closes the loop.** Every row has a checkbox and every section a feedback box. One
  *Copy for Claude* button bundles what you ticked into structured Markdown you can paste back
  into a chat to update your files and tickets.
- **Ships as a single file.** The daily HTML is fully self-contained — CSS, embedded font,
  base64 hero image. Archive it, open it offline, it just works.

## What it looks like

A newspaper, not a dashboard:

- **Masthead** — the day's name ("The Friday Brief"), built per run.
- **Hero** — a public-domain painting from the National Gallery of Art, cropped behind the
  title, exactly like Dia's briefing. No AI image costs, no prompt drift — just a curated
  manifest of beautiful paintings. (See [Hero images](#hero-images).)
- **Standfirst** — one line that reads the shape of the day.
- **Push your work forward** — the single highest-leverage thing available today, with a
  **Let's do it** button that opens a fresh chat pre-loaded with a full work order.
- **Top to-dos** — three of them; ticking saves in the browser.
- **New updates** — things that moved without you.
- **Owed to you** — read straight out of `DELEGATED.md`; passed chase dates and never-handed
  over items.
- **Gone quiet** — open items nobody is chasing you on.
- **Your day** — the calendar rail with a hover summary per meeting and a **Prep me** button
  on each.

## Repository layout

```
daily-brief/
├── README.md               # this file
├── LICENSE                 # MIT
├── brief/
│   ├── SPEC.md             # what a run does — edit this, not the task prompt
│   ├── content.schema.md   # the contract for content.json
│   ├── build.py            # renders content.json -> self-contained HTML
│   ├── shell.html          # the page: all CSS and layout lives here
│   ├── fraunces-600.b64    # embedded masthead font (base64, never read into context)
│   ├── hero-fallback.b64   # blurred wash so a failed image isn't a hole
│   ├── paintings.json      # NGA manifest: public-domain paintings for the hero
│   └── examples/
│       └── content.example.json   # a known-good content.json to diff against
├── task/
│   ├── scheduler-prompt.md # the ~8-line prompt you give your scheduler
│   └── brief.css           # editor/console theme for the example (optional)
└── scripts/
    └── build_manifest.py   # rebuild paintings.json from NGA open data (optional)
```

## Quick start

```bash
# 1. Clone
git clone https://github.com/kawaiier/daily-brief.git
cd daily-brief

# 2. Render the example brief
python3 brief/build.py brief/examples/content.example.json /tmp/brief-2026-08-21.html

# 3. Open it
open /tmp/brief-2026-08-21.html
```

That's it. The example brief builds with zero external dependencies — the painting and the
font are already baked in.

## Making it yours

1. **Copy the `brief/` package** into your vault (e.g. `Routines/daily-brief/`) or anywhere
   your scheduler can read it.
2. **Edit `brief/SPEC.md`** — the switch table at the top (hero mode, max items per section,
   notify policy) is the only thing you should ever need to change.
3. **Write your daily content** as `content.json` per `content.schema.md`, or let your agent
   do it.
4. **Run** `python3 brief/build.py content.json brief-2026-08-21.html`.
5. **Schedule it** with the prompt in `task/scheduler-prompt.md` — it works with Claude
   Cowork scheduled tasks, a Hermes cron job, or a plain OS cron.

The day's file is named `brief-YYYY-MM-DD.html`. **Never overwrite yesterday** — you're
building an archive.

## Hero images

The original project generated a fresh AI painting every morning (Higgsfield MCP, a few
credits a day). This version instead uses **real public-domain paintings from the National
Gallery of Art** — the same source Dia's briefing draws from.

- `brief/paintings.json` is a curated manifest of ~100 paintings (impressionist / post-
  impressionist / modern, muted palettes), each with its IIIF image URL, artist, title, year
  and NGA object page.
- The hero is picked per run (see the `HERO_PAINTING` switch in `SPEC.md`), and the credit
  line names the actual artist and year — no invented painters.
- Images are hotlinked from `api.nga.gov/iiif/...` (public domain, no key). The bundled
  `hero-fallback.b64` covers any network failure.
- `scripts/build_manifest.py` regenerates `paintings.json` from the official
  [NGA Open Data](https://github.com/NationalGalleryOfArt/opendata) release, so the manifest
  stays fresh and you can tune the filter (medium, era, palette) yourself.

## The copy-for-Claude loop

Every row has a checkbox, and it means different things per section:

| Section | A tick means |
|---|---|
| Top to-dos | Done |
| Owed to you / Gone quiet | No longer relevant |
| New updates | Already knew this |

The **Copy for Claude** button at the bottom bundles everything you ticked plus your notes into
structured Markdown — grouped by what the tick meant and which file needs the edit — ready to
paste into a chat that updates `TASKS.md`, `DELEGATED.md` and the relevant tickets.

## Credits

- Original concept & architecture: the [Reddit post](https://www.reddit.com/r/diabrowser/comments/1vuqdcp/i_recreated_the_daily_briefing_in_claude_cowork/)
  in r/diabrowser — *"I recreated the Daily Briefing in Claude Cowork so I could plug in my own
  tools"*.
- Paintings: [National Gallery of Art](https://www.nga.gov/), public domain via their
  [Open Data program](https://github.com/NationalGalleryOfArt/opendata) (CC0).
- Masthead font: [Fraunces](https://github.com/undercasetype/Fraunces) (OFL) — embedded as
  base64 so the brief is fully self-contained.

## License

MIT. The font is OFL-licensed; the painting metadata is CC0 (NGA Open Data). See `LICENSE`.
