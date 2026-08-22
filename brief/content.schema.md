# content.schema.md — the contract for `content.json`

`build.py` renders `content.json` → a self-contained HTML brief. This file is the contract
between the agent that writes content and the script that renders it. Validate against the
example (`examples/content.example.json`) before running.

All text fields are plain strings. `build.py` escapes everything — pass raw text, never HTML.
Links are written as `[label](https://...)` and **bold** as `**text**`; the script converts
them.

## Top level

| Field | Type | Required | Notes |
|---|---|---|---|
| `date` | string | ✅ | `YYYY-MM-DD`. Drives calendar deep links and the archive filename. |
| `title` | string | ✅ | Browser tab title. e.g. `The Friday Brief · 21 Aug 2026` |
| `masthead` | string | ✅ | The big serif title. e.g. `The Friday Brief` |
| `marg_left` | string | ✅ | Left marginalia, top of the page. |
| `marg_right` | string | ✅ | Right marginalia. |
| `standfirst` | string | ✅ | One line (~25 words) that reads the shape of the day. |
| `credit` | array<string> | optional | Hero credit lines, one per element (artist, title, year, source). |
| `vault` | string | optional | Obsidian vault name for `obsidian://` source links. Default `YOUR_VAULT_NAME`. |
| `hero` | object | optional | See below. Omit for a plain tinted header. |
| `push` | object | ✅ | The *Push your work forward* block. See below. |
| `sections` | array<object> | ✅ | The five list sections. See below. |
| `day_srcs` | array<string> | optional | Source chips for the day rail. Default `["cal"]`. |
| `day` | array<object> | optional | The *Your day* calendar rail. See below. |

## `hero`

| Field | Type | Notes |
|---|---|---|
| `src` | string | Image URL (e.g. an NGA IIIF URL). Hotlinked; `fallback_src` covers failure. |
| `fallback_src` | string | Tried once if `src` fails, then the wash. |
| `svg` | string | Inline SVG for `HERO=drawing` mode (used when `src` is empty). |
| `bg_b64` | string | Base64 JPEG wash overriding `hero-fallback.b64`. |
| `bg_tint` | string | CSS color under the wash. Default `#3A4942`. |

## `push`

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | ✅ | The one move. ≤ 10 words. |
| `body` | string | ✅ | ~50 words. What, why now, who it unblocks. |
| `seed` | string | ✅ | Raw text of the *Let's do it* work order (see SPEC → Seeds). |
| `srcs` | array<string> | optional | Source chips. Default `["delegated", "jira"]`. |
| `feedback_hint` | string | optional | Placeholder for the feedback box. |

## `sections[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `label` | string | ✅ | Kicker, e.g. `Top to-dos`. |
| `sub` | string | optional | Small subtitle, e.g. `Act before noon`. |
| `srcs` | array<string> | optional | Source chips. |
| `feedback_hint` | string | optional | Feedback placeholder. |
| `items` | array<object> | ✅ | Empty array → *Nothing here today.* Never pad. |

### `sections[].items[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | ✅ | Stable id within the day, e.g. `t1`. |
| `act` | string | ✅ | What a tick means: `done` · `seen` · `stale`. |
| `src` | string | ✅ | Source key — `tasks` · `delegated` · `jira` · `gmail` · `intercom` · `slack` · `github` · `cal` · `drive` · `circleback`. Drives the copy-for-Claude file mapping. |
| `ref` | string | optional | File/ticket reference for the copy output, e.g. `D1–D4`. |
| `title` | string | ✅ | ≤ 10 words, your own words, never a subject line. |
| `href` | string | optional | Deep link for the title. |
| `tag` | string | optional | Small tag chip, e.g. `D-2`. |
| `glyphs` | array<string> | optional | Source glyph keys shown inline. |
| `avatars` | array<object> | optional | `{i, tint?, url?}` — `i` id, `tint` = darker ring, `url` = image. |
| `body` | string | optional | 25–30 words, 2–3 rendered lines. |

## `day[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `t` | string | ✅ | Time, e.g. `09:30`. |
| `n` | string | ✅ | Meeting name. |
| `soft` | boolean | optional | True → optional/unanswered; dashed border. |
| `who` | array<object> | optional | Same shape as item avatars. |
| `h` | string | ✅ | Hover summary, ~25 words. |
| `p` | string | optional | Prep paragraph folded into the *Prep me* seed. |
| `seed` | string | optional | Full *Prep me* work order. Omit → no button. |

## Source keys

`tasks` · `delegated` · `jira` · `gmail` · `intercom` · `slack` · `github` · `cal` · `drive` ·
`circleback` — used in `srcs`, `glyphs`, and item `src`. Unknown keys are ignored.

## Copy-for-Claude semantics

| `act` | Tick means | Copy heading |
|---|---|---|
| `done` | Done | `Done` |
| `seen` | Already knew this | `Already knew this` |
| `stale` | No longer relevant | `No longer relevant` |

The copy groups ticked items by `act` and by the file implied by `src`, appending `ref` when
present. Feedback text goes under `## Notes`, quoted per section.
