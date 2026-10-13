#!/usr/bin/env python3
"""Render the daily brief from content.json into a single self-contained HTML file.

  python3 build.py content.json /path/out/brief-YYYY-MM-DD.html

Design lives here and in shell.html. Content lives in content.json.
Never paste the font base64 into a prompt or read fraunces-600.b64 into context;
this script substitutes it from disk.
"""
import argparse, datetime, html, json, pathlib, re, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
SEED_BASE = "https://claude.ai/new?q="
SEED_TAIL = "&surface=cowork&composer=mini"

# ---------------------------------------------------------------- source icons
_S = 'xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"'
GLYPH = {
    "jira": f'<svg {_S}><path d="M11.53 2 3 10.33a.97.97 0 0 0 0 1.4l8.53 8.35a1.02 1.02 0 0 0 1.42 0l8.53-8.35a.97.97 0 0 0 0-1.4L12.95 2a1.02 1.02 0 0 0-1.42 0Z"/><circle cx="12" cy="11.5" r="3.4" fill="#fff"/></svg>',
    "gmail": f'<svg {_S}><rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="m2.5 7 9.5 6 9.5-6" fill="none" stroke="#fff" stroke-width="1.6"/></svg>',
    "intercom": f'<svg {_S}><rect x="2.5" y="4.5" width="19" height="15" rx="3"/><path d="M6 9h12M6 12.5h9" stroke="#fff" stroke-width="1.6"/></svg>',
    "slack": f'<svg {_S}><path d="M9 3.5a2 2 0 1 0-4 0v4a2 2 0 1 0 4 0zM15.5 3.5a2 2 0 1 0-4 0v9a2 2 0 1 0 4 0zM3.5 9a2 2 0 1 0 0 4h4a2 2 0 1 0 0-4zM3.5 15.5a2 2 0 1 0 4 0v-4a2 2 0 1 0-4 0z"/></svg>',
    "github": f'<svg {_S}><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.1.39-1.99 1.03-2.69-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.58 9.58 0 0 1 5 0c1.91-1.3 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.6 1.03 2.69 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85V21c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg>',
    "cal": f'<svg {_S}><rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9h18M8 2.5V6M16 2.5V6" stroke="#fff" stroke-width="1.6"/></svg>',
    "drive": f'<svg {_S}><path d="m12 2 8.5 14.75H3.5Z"/><path d="m8.5 16.75 3.5 5.5 7-5.5" fill="none" stroke="#fff" stroke-width="1.2"/></svg>',
    "circleback": f'<svg {_S}><path d="M4 4h13a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3Z"/><path d="M8 9h8M8 13h8M8 17h4" stroke="#fff" stroke-width="1.6"/></svg>',
    "obsidian": f'<svg {_S}><path d="M12 2c3 2.5 4 5.5 3.5 8-1 3.5-4.5 5-5 8.5-.5 3 1 4.5 1 4.5-4-1.5-6-5-5.5-9 .5-4 4-7 6-12Z"/></svg>',
}

# short label + glyph key + default deep link for each source
SRC = {
    "tasks": ("TASKS.md", "obsidian", "obsidian://open?vault={vault}&file=TASKS.md"),
    "delegated": ("DELEGATED.md", "obsidian", "obsidian://open?vault={vault}&file=DELEGATED.md"),
    "jira": ("Jira", "jira", "https://your-jira.atlassian.net/jira/your-work"),
    "gmail": ("Gmail", "gmail", "https://mail.google.com/mail/u/0/#inbox"),
    "intercom": ("Intercom", "intercom", "https://app.intercom.com/a/apps/your-app/inbox"),
    "slack": ("Slack", "slack", "https://app.slack.com/client"),
    "github": ("GitHub", "github", "https://github.com/pulls/review-requested"),
    "cal": ("Calendar", "cal", "https://calendar.google.com/calendar/r/day/{y}/{m}/{d}"),
    "drive": ("Drive", "drive", "https://drive.google.com/drive/recent"),
    "circleback": ("Circleback", "circleback", "https://app.circleback.ai/meetings"),
}


def e(s):
    """Escape gathered text. Everything from a tool result goes through this."""
    return html.escape(str(s or ""), quote=True)


def seed(text):
    return SEED_BASE + urllib.parse.quote(text or "", safe="") + SEED_TAIL


def _js(obj):
    """JSON for embedding inside a <script> element.

    Escapes the characters that can close the script block (<, >, &) and the JS
    line separators U+2028/U+2029, so gathered text can never break out.
    """
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


# ---------------------------------------------------------------- validation
REQUIRED_TOP = (
    "date", "title", "masthead", "marg_left", "marg_right", "standfirst", "push", "sections",
)
REQUIRED_PUSH = ("title", "body", "seed")
REQUIRED_ITEM = ("id", "act", "src", "title")
ALLOWED_ACT = ("done", "seen", "stale")


def validate(content):
    """Return a list of human-readable problems with content.json (empty = ok).

    Mirrors brief/content.schema.md so a broken run fails loudly with the field
    that is wrong, instead of a KeyError traceback.
    """
    if not isinstance(content, dict):
        return ["top level must be a JSON object"]
    problems = []
    for key in REQUIRED_TOP:
        if key not in content:
            problems.append("missing required field: %s" % key)
    if "date" in content:
        date = content["date"]
        if not isinstance(date, str):
            problems.append("date must be a string in YYYY-MM-DD form")
        else:
            try:
                datetime.date.fromisoformat(date)
            except ValueError:
                problems.append("date must be YYYY-MM-DD, got %r" % date)
    if "push" in content:
        push = content["push"]
        if not isinstance(push, dict):
            problems.append("push must be an object")
        else:
            for key in REQUIRED_PUSH:
                if key not in push:
                    problems.append("missing required field: push.%s" % key)
    if "sections" in content:
        sections = content["sections"]
        if not isinstance(sections, list):
            problems.append("sections must be an array")
        else:
            for i, sec in enumerate(sections):
                if not isinstance(sec, dict):
                    problems.append("sections[%d] must be an object" % i)
                    continue
                if "label" not in sec:
                    problems.append("missing required field: sections[%d].label" % i)
                items = sec.get("items")
                if not isinstance(items, list):
                    problems.append("sections[%d].items must be an array" % i)
                    continue
                for j, item in enumerate(items):
                    where = "sections[%d].items[%d]" % (i, j)
                    if not isinstance(item, dict):
                        problems.append("%s must be an object" % where)
                        continue
                    for key in REQUIRED_ITEM:
                        if key not in item:
                            problems.append("missing required field: %s.%s" % (where, key))
                    if "act" in item and item["act"] not in ALLOWED_ACT:
                        problems.append(
                            "%s.act must be one of %s" % (where, ", ".join(ALLOWED_ACT))
                        )
    return problems


# ---------------------------------------------------------------- components
def srcs(keys, ctx):
    if not keys:
        return ""
    out = []
    for k in keys:
        if k not in SRC:
            continue
        label, glyph, href = SRC[k]
        href = href.format(vault=ctx["vault"], y=ctx["y"], m=ctx["m"], d=ctx["d"])
        out.append(f'<a href="{e(href)}">{GLYPH[glyph]}{label}</a>')
    return '<span class="srcs">' + "".join(out) + "</span>"


def avatar(a):
    tint = " b" if a.get("tint") else ""
    img = f'<img src="{e(a["url"])}" alt="" onerror="this.remove()">' if a.get("url") else ""
    return f'<span class="ava{tint}" data-i="{e(a.get("i", ""))}">{img}</span>'


def glyphs(keys):
    if not keys:
        return ""
    return '<span class="glyphs">' + "".join(GLYPH[k] for k in keys if k in GLYPH) + "</span>"


def title_html(it):
    t = e(it["title"])
    if it.get("href"):
        t = f'<a href="{e(it["href"])}">{t}</a>'
    tag = f' <span class="tag">{e(it["tag"])}</span>' if it.get("tag") else ""
    return t + tag + glyphs(it.get("glyphs")) + "".join(avatar(a) for a in it.get("avatars", []))


def body_html(it):
    """Body text with [label](url) turned into links. Text is escaped first."""
    txt = e(it.get("body", ""))
    txt = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+|obsidian://[^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
        txt,
    )
    txt = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", txt)
    return txt


def row(it):
    return (
        f'<div class="row" data-id="{e(it["id"])}" data-act="{e(it["act"])}" '
        f'data-src="{e(it["src"])}" data-ref="{e(it.get("ref", ""))}">'
        '<input class="chk" type="checkbox" aria-label="tick">'
        f'<div><p class="it-title">{title_html(it)}</p>'
        f'<p class="it-body">{body_html(it)}</p></div></div>'
    )


def feedback(sec, placeholder):
    return (
        f'<div class="fb" data-sec="{e(sec)}">'
        '<span class="fbt"><span class="pm">+</span>Add feedback</span>'
        f'<textarea placeholder="{e(placeholder)}"></textarea></div>'
    )


def section(s, ctx):
    label = (
        f'<div class="slabel">{e(s["label"])}'
        f'<span class="sub">{e(s.get("sub", ""))}</span>{srcs(s.get("srcs"), ctx)}</div>'
    )
    rows = "".join(row(i) for i in s.get("items", []))
    if not s.get("items"):
        rows = '<p class="it-body" style="padding-bottom:6px">Nothing here today.</p>'
    fb = feedback(s["label"], s.get("feedback_hint", "Anything I got wrong, or should have caught."))
    return f"  <section>\n    {label}\n    <div>{rows}{fb}</div>\n  </section>\n"


def push_body(p):
    return (
        '<div class="pushbody">'
        f'<p class="title">{e(p["title"])}</p>'
        f"<p>{body_html(p)}</p>"
        + feedback("Push your work forward", p.get("feedback_hint", "Wrong call? Different owner? Say so and I will redo the hand-off."))
        + "</div>"
    )


def js_data(content):
    """Avatar registry + the Your day rail, as JS literals.

    Display strings are HTML-escaped here, at the trust boundary, so the shell can
    insert them with innerHTML without re-escaping. Seeds stay raw (they are
    percent-encoded into a URL at runtime) but the JSON is escaped for the script.
    """
    A, seen = {}, {}

    def key(a):
        k = (a.get("i", "") or "x").lower()
        seen[k] = a
        return k

    day = []
    for d in content["day"]:
        who = [key(a) for a in d.get("who", [])]
        day.append(
            {
                "t": e(d.get("t", "")),
                "n": e(d.get("n", "")),
                "soft": bool(d.get("soft")),
                "who": who,
                "h": e(d.get("h", "")),
                "p": e(d.get("p", "")),
                "seed": d.get("seed"),
            }
        )
    for k, a in seen.items():
        A[k] = [e(a.get("i", "")), "b" if a.get("tint") else "", e(a.get("url", ""))]
    return "const A = " + _js(A) + ";\nconst DAY = " + _js(day) + ";"


# ---------------------------------------------------------------- main
def build(content):
    problems = validate(content)
    if problems:
        raise SystemExit("content.json is not valid:\n  - " + "\n  - ".join(problems))
    ctx = {"vault": content.get("vault", "YOUR_VAULT_NAME")}
    y, m, d = content["date"].split("-")
    ctx.update(y=int(y), m=int(m), d=int(d))

    shell = (HERE / "shell.html").read_text()
    font = (HERE / "fraunces-600.b64").read_text().strip()

    hero = content.get("hero") or {}
    if hero.get("src"):
        fb_src = hero.get("fallback_src") or ""
        onerr = (
            f"if(!this.dataset.f){{this.dataset.f=1;this.src='{fb_src}'}}else{{this.remove()}}"
            if fb_src
            else "this.remove()"
        )
        hero_img = (
            f'<img src="{e(hero["src"])}" alt="Painted scene for today\'s brief" '
            f'onerror="{onerr}">'
        )
    else:
        hero_img = hero.get("svg", "")
    wash = hero.get("bg_b64")
    if not wash:
        wf = HERE / "hero-fallback.b64"
        wash = wf.read_text().strip() if wf.exists() else ""
    tint = hero.get("bg_tint", "#3A4942")
    bg = f"{tint} url(data:image/jpeg;base64,{wash})" if wash else tint

    slots = {
        "{{TITLE}}": e(content["title"]),
        "{{MARG_L}}": e(content["marg_left"]),
        "{{MARG_R}}": e(content["marg_right"]),
        "{{MASTHEAD}}": e(content["masthead"]),
        "{{HERO_BG_CSS}}": bg,
        "{{HERO_IMG}}": hero_img,
        "{{STANDFIRST}}": e(content["standfirst"]),
        "{{CREDIT}}": "<br>".join(e(l) for l in content.get("credit", [])),
        "{{PUSH_BODY}}": push_body(content["push"]),
        "{{PUSH_SRCS}}": srcs(content["push"].get("srcs", ["delegated", "jira"]), ctx),
        "{{PUSH_SEED}}": e(seed(content["push"].get("seed", ""))),
        "{{SECTIONS}}": "".join(section(s, ctx) for s in content["sections"]),
        "{{DAY_SRCS}}": srcs(content.get("day_srcs", ["cal"]), ctx),
        "{{JS_DATA}}": js_data(content),
        "{{DATE}}": content["date"],
    }
    for k, v in slots.items():
        shell = shell.replace(k, v)
    shell = shell.replace("__FONT_B64__", font)
    alias = {"obsidian": "OBS", "circleback": "CB"}
    for k, v in GLYPH.items():
        shell = shell.replace("__G_%s__" % k.upper(), v)
        if k in alias:
            shell = shell.replace("__G_%s__" % alias[k], v)

    leftover = re.findall(r"\{\{[A-Z_]+\}\}|__[A-Z0-9_]+__", shell)
    if leftover:
        raise SystemExit("unfilled slots: %s" % sorted(set(leftover)))
    return shell


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="Render the daily brief from content.json into a single self-contained HTML file.",
        epilog="Design lives in shell.html; content lives in content.json. "
        "The font and hero wash are read from disk and never belong in a prompt.",
    )
    parser.add_argument("content", type=pathlib.Path, help="path to content.json")
    parser.add_argument("output", type=pathlib.Path, help="path to write the rendered HTML brief")
    args = parser.parse_args(argv)
    try:
        content = json.loads(args.content.read_text())
    except FileNotFoundError:
        raise SystemExit("no such file: %s" % args.content)
    except json.JSONDecodeError as exc:
        raise SystemExit("%s is not valid JSON: %s" % (args.content, exc))
    html_out = build(content)
    args.output.write_text(html_out)
    print("wrote %s (%d bytes)" % (args.output, len(html_out)))


if __name__ == "__main__":
    main()



