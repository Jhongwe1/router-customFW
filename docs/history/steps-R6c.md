# `PROGRESS.md` § `R6c`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `R6c`'s closing commit on 2026-10-09, once its
rows were closed. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R6c`'s step list — ✅ CLOSED 2026-10-09, in four segments (127th, 128th, 129th, 130th)

**Gate:** rlxfw's Ethernet from a flash boot (§ Gate board, row `R6c`). **Opened**
2026-10-08 by the owner's decision, after `v1.0`'s qualification seating found that an
image booted from a slot through `rlxboot` receives no frame (`NET-171`): rlxfw leaves the
switch's VLAN group to the loader (`notes/switch-driver.md` § 16.8), and the loader
configures the switch only on its prompt path (`LDR-46`). The relaxed process continues;
the flash rules, `H601`, the power handshake and `NET-165` do not relax, and every flash
write is a separate dated yes for that exact payload (`FW-113`).

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R6c-0`** ✅ **2026-10-08** | desk | This list and the board row | the board row reads `~` and names this list | — |
| **`R6c-1`** ✅ **2026-10-08** | desk | what the loader's prompt-path Ethernet init writes to the switch — registers and ASIC tables, with values — from the bootcode in the tree that builds the loader and from `stage2.bin`'s disassembly | a table with both sources per row, each agreeing or recorded undetermined | a function in a drop that does not build this loader |
| **`R6c-2`** ✅ **2026-10-08** | desk | the takeover's design: the VLAN group as a unit (§ 16.8), in rlxfw's own switch driver or `/init`, each value with two sources; the blast radius — `RECIPE_ID`, the armed image, the release image | written, with where it will fail | a value with one source, taken because the loader's state worked |
| **`R6c-3`** ✅ **2026-10-08** | desk | the change through `config/rlxfw-src`, its desk tests with a mutation that turns them red, and the mainline and armed images built twice each | builds byte-equal; tests green and the mutation red | a RAM boot through the prompt broken by writing over the loader's state |
| **`R6c-4`** ✅ **2026-10-08** | bench | a RAM boot through the prompt that still pings; the rebuilt image signed by the owner as version 5 and installed in slot A (one write); flash boots after a watchdog reset and after a cold power-on that each ping both ways, with `rlx0`'s counters moving | each boot judged by `bootslot`, each ping read from both sides | a cold boot that differs from the warm one |
| **`R6c-5`** ✅ **2026-10-09** | desk | the result: a `docs/GATE-RESULTS.md` entry, `SPEC.md` rows, the `docs/KNOWN-ISSUES.md` entry of 2026-10-08 closed, and `v1.0`'s image re-pinned for `P4b` | `cfcensus` and `spec-check` green on the closing tree | — |
