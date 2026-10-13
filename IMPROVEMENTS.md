# Improvement list — authoritative implementation scope

This is the actionable improvement list the daily-brief run asked for. No shared
improvement list or defining issue/PR existed in the repo, so this document is the
scope of record for the implementation step (`.pi-tasks/TASK_0002.md`, plan key `P02`).
Each item is small, in-repo, and independently verifiable; together they harden the
`content.json` → self-contained HTML path without changing the content contract.

Status key: **✅ done** in this change set — see `git diff` and `tests/test_brief_build.py`.

| ID | Improvement | Why it matters | Verification |
|----|-------------|----------------|--------------|
| **IMP-1** | ✅ Fix the broken *Let's do it* push link. `{{PUSH_SEED}}` is HTML-attribute-escaped instead of `json.dumps`-quoted. | The rendered button shipped as `href=""https://claude.ai/new?q=…""` — an empty `href`, so the single highest-leverage action on the page did nothing. | `test_push_seed_link_is_well_formed` parses the `href` and asserts it is the full `claude.ai/new?q=…&surface=cowork&composer=mini` URL. |
| **IMP-2** | ✅ Validate `content.json` in `build.py` and fail with a readable, itemised error before rendering. | Missing/mistyped fields produced raw `KeyError`/`ValueError` tracebacks; SPEC promises the build "fails loudly … rather than shipping a broken page". | `test_invalid_content_fails_loudly_without_a_traceback` (missing `title`, bad `date`). |
| **IMP-3** | ✅ Escape HTML-significant characters when embedding content-derived JSON in the page `<script>` (block `</script>` breakout). | Meeting names, push seeds and avatar ids come from email/Slack/Jira; an unescaped `</script>` could terminate the data block and inject script. | `test_gathered_text_cannot_break_out_of_the_script_block` (asserts exactly one `<script>` element survives a hostile payload). |
| **IMP-4** | ✅ HTML-escape content-derived display strings at the build boundary (avatar `title`/`src`, day-rail time/name/hover) and insert them directly. | The shell previously only stripped `<`; a `"` in an avatar name or URL allowed attribute injection. | `test_gathered_text_is_escaped_before_it_reaches_the_page`. |
| **IMP-5** | ✅ Give `build.py` a real CLI (`argparse`): `-h/--help` exits 0, usage errors are clear, a missing/invalid JSON input yields a one-line message. | The documented verification calls `python3 brief/build.py --help`; it used to print the docstring and exit 1. | `test_cli_help_exits_zero`, `test_missing_input_file_fails_cleanly`. |
| **IMP-6** | ✅ Rewrite the acceptance test to render the shipped example unmodified and assert the self-contained-HTML contract end to end, titled *renders content.json into a self-contained HTML brief*. | The previous test mutated the fixture and its title did not match the acceptance criterion, so the gate reported the behaviour as untested. | `python3 -m unittest discover -s tests -v` — the test named in the criterion. |
| **IMP-7** | ✅ Add regression tests for IMP-1…IMP-5. | Locks the new behaviour so it cannot silently regress. | Same suite, all green. |

## Out of scope

- Changing `brief/content.schema.md`'s contract or the `brief/SPEC.md` run behaviour —
  both are preserved; only a validation note was added.
- `scripts/build_manifest.py` and `paintings.json` (optional NGA tooling).
- Anything requiring network access or a browser (the suite is offline and deterministic).
