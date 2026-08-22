# Daily Brief — scheduled-task prompt

Give this to whatever runs your mornings (Claude Cowork scheduled task, a Hermes cron job, a
plain OS cron + agent). It is deliberately short: the spec is the source of truth, the prompt
just points at it.

---

Build YOUR_NAME's Daily Brief for today.

Read `~/YOUR_VAULT/Routines/daily-brief/SPEC.md` first and follow it exactly. It is the source
of truth for this task and it supersedes anything you might assume from the name. Also read
`content.schema.md` in the same folder before writing any content.

Short version so you know the shape before you read it: two phases in one run. Phase 1 is the
task sync that used to be its own job — work out the lookback window from the most recent brief
in `Work/Briefs/`, gather across Circleback, Gmail, Calendar, Jira, Slack, Intercom, GitHub and
Drive over that window, then update `TASKS.md` and `DELEGATED.md` and write the dated task-sync
note. On a Monday that window reaches back across the weekend, which is deliberate — do not skip
Friday evening or weekend traffic. Phase 2 renders the brief page from those freshly synced
files plus today's calendar.

Build the page with `Routines/daily-brief/build.py`, which takes a `content.json` you write and
outputs the HTML. Do not hand-write HTML or CSS and do not read `fraunces-600.b64` into context
— the script substitutes it. Screenshot the result with a headless Chromium and actually look at
the image before delivering; the script fails loudly on an unfilled slot but it cannot see a
layout problem.

Deliver to `~/YOUR_VAULT/Work/Briefs/brief-YYYY-MM-DD.html`. A new file every day. Never
overwrite an earlier brief and do not create or maintain `brief-today.html`.

Then send a push notification naming the file and the single sharpest thing in it, and reply
with two or three sentences: the filename, the sharpest item, and anything the sync could not
confirm. Do not recap the brief itself — YOUR_NAME is about to read it.

Nobody is watching when this fires, so do not ask questions. Where the spec leaves a judgment
call, make it, and note the call in your reply.
