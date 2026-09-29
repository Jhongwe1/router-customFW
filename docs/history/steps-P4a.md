# `PROGRESS.md` § `P4a`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 1106–1119, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `P4a`'s step list — ✅ CLOSED 2026-09-01, in one desk segment

| step | | done |
|---|---|---|
| `P4a-1` ✅ **2026-09-01** | **explain the 84 bytes before fixing anything.** `P21-1` written and committed BEFORE the mapping ran (`cb56a59`), with what was already known stated so the prediction's worth is bounded: the count was measured first, the locations were not | ✅ 2026-09-01 |
| `P4a-2` ✅ **2026-09-01** | **the fixes, both declared.** `config/host-compat/0002` (cpio mtime from `RLXFW_CPIO_MTIME`) and `config/rlxfw-build-stamp` (one epoch, rendered by the driver above the stage under `LC_ALL=C TZ=UTC`) | ✅ 2026-09-01 |
| `P4a-3` ✅ **2026-09-01** | **the anti-DoD repair the freeze made necessary.** `ID0`, the twelfth row of `config/rlxfw-marks.tsv`, whose value is a sha256 over `config/` — a function of the declaration, so it moves when the recipe moves | ✅ 2026-09-01 |
| `P4a-4` ✅ **2026-09-01** | **the instrument, committed rather than described.** `tools/repdiff.py` (16 controls on synthetic ELF32BE, so nothing needs `$FWRE_WORK`) and `tools/test-repdiff-mutants.py` (12 mutants, `M0` first) | ✅ 2026-09-01 |
| `P4a-5` ✅ **2026-09-01** | **the controls, including one that predicts NO change.** `PC-1` and `PC-2`, and `PC-2`'s inversion after `ID0` | ✅ 2026-09-01 |

**Five of five.** 🔴 **And the gate closes with its own DoD refuted in one
clause** — *"changing one source byte changes it"* is false as written, which
`PC-2` measured rather than argued. `notes/reproducible-build.md` §7 reads the
DoD one row at a time and lists what the gate did NOT establish.
