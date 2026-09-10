# Consuming this spec — HDLTOOLS-0001

This spec was **exported** by `wt` (work-tracking), a separate tool's spec pipeline — it was
not authored in this repo. Treat it as an implementation brief / governing spec (if this repo
has its own spec-first workflow, fold it in per that workflow).

## How to treat it

- Prefer the global agent skill `/wt-implement-spec` (install via `wt skills install` on a
  machine that has `wt`) for the implement → test → done loop on this file.
- Read the whole spec before writing code — it is self-contained (Context / Decision / Design
  / Acceptance criteria / Test plan).
- **This portable file is your working copy** for build progress: update frontmatter `status`
  (`accepted` → `in-progress` → `done`) and check off Acceptance criteria as you go. There is
  no wt ledger in this repo.
- Close the loop: implement to the Acceptance criteria and execute the Test plan; don't mark
  anything done without doing so.
- If you deviate from the Design, record the deviation in the spec body (or your own PR) —
  don't diverge silently.
- The wt author can later run `wt spec pull-status HDLTOOLS-0001` to mirror this file's
  `status` back into their outbox — optional, not automatic.
- Do **not** run `wt spec generate` on this outbound id.

## Provenance

- Source: outbound spec `HDLTOOLS-0001` (project `Hdltools`), `wt`'s canonical copy at
  `/home/bruno/.local/share/wt/outbox/Hdltools/HDLTOOLS-0001-hdltools-test-coverage-close-silent-gaps-after.md`.
- Exported: 2026-09-10 14:49:45
- Portable spec: `HDLTOOLS-0001-hdltools-test-coverage-close-silent-gaps-after.md`
- Content hash: `52bfe89268589068`

This contract + the paired spec were file-dropped by `wt spec export` (SPEC-0015 / SPEC-0041).
There is no live sync back to the source `wt` — this is a point-in-time snapshot, not a
subscription.
