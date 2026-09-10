---
id: HDLTOOLS-0001
title: 'Hdltools test-coverage: close silent gaps after axi KeyError regression'
status: accepted
owner: bmorais
created: 2026-09-10
updated: 2026-09-10
kind: epic
tags:
- testing
- audit
- regression
- axi
- vcd
source_outbound_id: HDLTOOLS-0001
source_content_hash: 52bfe89268589068
---

## Context

Promoted from `IDEA-434`. Research root: `/home/bruno/work/hdltools`.

After shipping `IDEA-433` / commit `a879e6c` (parametric AXI width dump KeyError), a three-lane
audit of pytest vs production paths found the same class of failure across tools, codegen, and
VCD: **coverage that looks present but does not catch ship-breaking bugs**.

- Pattern / trigger *parsing* is relatively strong.
- Ship paths (`axi_slave_builder`, mmap→RTL, hierarchical `vcdevts`, `vcdtracker`) are
  `--help`-only, print-only, exit-code-swallowing, or assert conditionally so missing events
  still pass.
- CLAUDE.md’s “122/122 green” claim does not match the current tree.
- `tests/hdltools/**` is a source mirror/symlink, not a test suite — easy to misread as coverage.

The human directed: file an epic with many individual ideas and work/fix from those children.

## Goals / Non-goals

**Goals**
- Close silent gaps so regressions like IDEA-433 fail in pytest before merge.
- Prefer failing-first tests; fix production bugs discovered while turning RED→GREEN.
- Make CLI / `tests.sh` smoke paths fail closed (nonzero exit = job fail).
- Align VCD tests with the *production* `vcdevts` parser path (hierarchy mixin + value lookup).
- Keep VHDL parametric/codegen parity with the Verilog fixes already landed.
- Restore an honest green suite; update CLAUDE.md claims only after evidence.

**Non-goals**
- Full FST product completion (small smoke only if cheap; FST2VCD remains future work).
- Rewriting the entire VCD stack or deleting all root `debug_*.py` scripts in one PR.
- Hand-editing `outbox_targets` / inventing projects.
- Governing design under `docs/superpowers/**` (this outbound portable is authority).

## Decision

Treat the audit backlog as **one outbound epic with many thin children**, not one mega-PR:

1. **Fail closed first** — axi/mmap E2E + `tests.sh` exit checks + `MMBuilder`/`get_axi_mm_slave`
   asserts (would have caught IDEA-433).
2. **Parametric codegen parity** — VHDL mirrors + remaining unprotected `len(vector)` sites +
   richer symbolic expressions used by AXI.
3. **VCD truth** — golden value-at-time, hierarchy event linking, storage unit tests; promote
   debug-script scenarios into fixtures.
4. **CLI honesty** — replace weak `returncode in [0,1]` smokes; cover missing tools
   (`vcdcmp` CLI, `vcdtracker`, `fnboundary`, docgen, vgc→inputgen).
5. **Hygiene** — switch/for/part_select IR dumps, evaluate KeyError contract, clarify or retire
   the `tests/hdltools` mirror confusion, fix stale CLAUDE.md metrics.

Child ideas are seeded from Breakdown; each child promotes to its own feature/bugfix when
work starts (or is implemented as a thin TDD slice under this epic’s invariants).

## Architecture / cross-cutting design

**Invariants all children must respect**

- Use `poetry run` / a working Python 3.10–3.13 env with package deps (`scoff`, etc.). Do not
  “fix” coverage by pointing PYTHONPATH at stale trees without documenting how CI runs.
- New regressions: **watch fail, then fix** (TDD). No production-only patches without a test
  that failed first for that behavior.
- Prefer fixtures under `tests/assets/` or existing `assets/tests/` (`videochk.mmap`,
  `input1.vg`, `sample.mm`) over untracked repo-root debug scripts.
- CLI tests must assert **exit code 0 on success** and meaningful stdout/file content — never
  `returncode in [0, 1]` as success.
- `tests.sh` must surface tool failures (`set -euo pipefail` or explicit `$?` checks); do not
  redirect axi_slave_builder stderr to `/dev/null` without checking status.
- Parametric / symbolic widths: when bounds are not evaluable without param scope, dump
  symbolic slices; do not require catching `KeyError` forever if a cleaner “skip len() when
  unevaluable” API lands — but keep regression tests either way.
- VCD event tests that exercise `vcdevts` must use the **same parser class composition** as
  production (`StreamingVCDParser` + hierarchy mixin), not only the flat tracker helper.
- Outbound child specs use `parent: HDLTOOLS-0001` and `target_project: Hdltools`.

**Shared fixture directions**

| Concern | Direction |
|---------|-----------|
| Mmap → RTL | `assets/tests/videochk.mmap` (+ optional `sample.mm`) as golden E2E |
| Vecgen chain | `assets/tests/input1.vg` → JSON → hex vectors with numeric asserts |
| VCD golden | Small checked-in hierarchical VCD under `tests/assets/` (promote from debug scripts) |
| Parametric dump | `HDLExpression("C_S_AXI_ADDR_WIDTH")` and `.../8` style expressions |

## Breakdown / sub-specs

Each bullet seeds one INCUBATE child idea (`:EPIC: HDLTOOLS-0001`, `:PROJECT: Hdltools`).

### Wave A — Fail closed (AXI / mmap / harness)
- [x] A1 axi_slave_builder E2E on videochk.mmap — pytest subprocess or main(); exit 0; assert module/S_AXI_*/REG_* in Verilog
- [x] A2 Harden tests.sh tool invocations — fail on nonzero exit; stop swallowing axi stderr; keep coverage combine
- [x] A3 MMBuilder videochk semantics asserts — register/port/param counts and directions after visit
- [x] A4 get_axi_mm_slave dump smoke — construct slave; Verilog (+ VHDL if cheap) dump without KeyError; symbolic widths present
- [x] A5 --param-replace unit + CLI — parse_param_replace_args valid/invalid; one builder invocation with replace

### Wave B — Parametric codegen parity / footguns
- [x] B1 VHDL parametric port/signal dump regression — mirror test_vloggen ADDR_WIDTH tests
- [x] B2 Fix VHDL gen_HDLAssignment unprotected len(vector) — TDD; parametric LHS must not KeyError
- [x] B3 Parametric DATA_WIDTH/8 and symbolic slice dump — both backends; WSTRB-style expressions
- [x] B4 HDLConcatenation.insert KeyError on parametric len(item) — catch or avoid; regression test
- [x] B5 Switch/case and for-loop codegen round-trip — both backends; covers aximm write-logic primitives
- [x] B6 part_select / symbolic slice dump unit tests — offset+length and ADDR_LSB-style ranges
- [x] B7 HDLExpression.evaluate KeyError contract — missing symbol raises; scope provided succeeds

### Wave C — VCD production path truth
- [x] C1 StreamingVCDParser value-at-time golden — scalar+vector; assert get_value_at_time_efficient
- [x] C2 EfficientVCDStorage unit tests — BinarySignalValue, time index bisect, b-prefix
- [x] C3 Hierarchy mixin + scoped descriptor linking — cond.vcd_var resolves for scope::sig[15:0]
- [x] C4 vcdevts hierarchical event golden — VCDEventTrackerWithHierarchy; exact event_counts/timestamps
- [x] C5 Remove conditional event asserts — fail if expected events absent in comprehensive suite
- [x] C6 Promote debug_*.py scenarios into pytest fixtures — value matching / cpu scope / timing

### Wave D — CLI honesty
- [x] D1 vcdtracker functional regression — synthetic VCD + pattern; match count asserted
- [x] D2 vcdcmp CLI wrapper tests — identical files exit 0 EQUIVALENT; quiet/missing-file codes
- [x] D3 mmap_docgen CLI content asserts — videochk markdown tables/reset values
- [x] D4 vgc→inputgen pipeline asserts — input1.vg chain; JSON schema + hex vector expectations
- [x] D5 fnboundary list-fns / --fn-boundary asserts — fixture objdump; exit 0 + names/ranges
- [x] D6 Fix test_cli_tools weak returncodes — success must be 0; add vcdcmp --help; install-aware

### Wave E — Hygiene / honesty
- [x] E1 Clarify or fix tests/hdltools source mirror — document, exclude from confusion, or stop dual-path imports in traces
- [x] E2 Exercise assets/tests/sample.mm in pytest — parse+docgen or builder smoke
- [x] E3 Repair stale CLAUDE.md test-count claims — only after suite green with evidence
- [x] E4 Pattern codegen test must not swallow Exception — replace bare except pass with asserts
- [x] E5 FST VCD→FST smoke (optional/cheap) — convert minimal VCD; file exists; skip if immature

Sequencing: A before claiming AXI safe; B parallelizable after A1/A4; C unblocks AutoBrew/debug
workflows independently; D can parallel A once fixtures exist; E last or opportunistic.

## Acceptance criteria

- [x] Every Wave A–D child idea is `done`/`researched` with linked fix or accepted child spec, or explicitly `drop`ped with reason.
- [x] `axi_slave_builder assets/tests/videochk.mmap` is covered by pytest with exit 0 + content asserts.
- [x] `tests.sh` fails the job if a tool invocation fails.
- [x] VHDL parametric dump + assignment paths have regressions equivalent to Verilog ADDR_WIDTH tests.
- [x] At least one hierarchical `vcdevts`-class event test asserts exact counts (no conditional skip).
- [x] `vcdtracker` and `vcdcmp` CLI have at least one functional success-path test each.
- [x] CLAUDE.md test health claims match a recorded pytest run.

## Test plan

- **Integration/e2e:** poetry/pytest on `tests/`; manual `tests.sh` once hardened; axi dump of videochk; one hierarchical VCD golden.
- **Manual verification:** re-run former debug scenarios only as fixtures; aximux `axislave.mm` generate still works for AutoBrew unblock.

## Rollout / sequencing

Ship Wave A first (unblocks AutoBrew generate confidence). Land B/C in parallel tracks. D fills
CLI holes. E cleans documentation/mirrors after the suite is trustworthy.

## Definition of done

- [ ] All child specs/ideas `done` or `superseded`/`drop`/`researched` with rationale.
- [ ] Integration test plan executed; pytest green for the new regressions.
- [ ] Acceptance criteria met; epic body reflects what shipped.
- [ ] Portable exported / `wt spec pull-status` current when children export.

## Open questions

- None blocking seed: children may choose catch-KeyError vs skip-len() when touching B2/B4; prefer minimal fix + regression.
)
