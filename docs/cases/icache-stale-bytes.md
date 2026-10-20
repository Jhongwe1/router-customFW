# The I-cache handing back stale bytes

`R1g-4a`, one power cycle on 2026-08-25, under `R1-gate`. Rows of [`SPEC.md`][spec]
([how to read one](../spec/README.md)): [`CPU-19`][spec] and [`CPU-20`][spec], owned by
[`notes/cache-model.md`](../../notes/cache-model.md) and
[`docs/rlx-cache-and-cp0.md`](../rlx-cache-and-cp0.md), and [`CPU-35`][spec], closed. The record is
[`docs/log/2026-08.md`](../log/2026-08.md), in Chinese: the entries of 2026-08-23 (`DAY-ZERO` 2b
and 2c, quoted here translated) and 2026-08-25 (the bench, `R1g-4a`). Marks: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred.

## Symptom

讀 The payload `probe1` calls a small function in RAM, rewrites one immediate field of it, then
calls it again ([`probe1.c`](../../tools/rlxprobe/probe1.c); [`CPU-19`][spec]).
量 In cell 1 — the store through the cached window, no treatment — both victims executed the
old constant while memory read back the new one, `vd=00000001`, STALE ([`CPU-19`][spec];
[`bench/2026-08-25/H1b.log`](../../bench/2026-08-25/H1b.log)). Under qemu, at the desk and not
on the device, the same cell reads FRESH ([`probe1.c`](../../tools/rlxprobe/probe1.c), header).

## First hypothesis, and why it was wrong

The stale bytes were predicted. The run sheet, written before power, made cell 1 the negative
control — *"It must read `01` STALE"* — and if it read FRESH the other five cells had passed
untested ([`docs/history/runsheet-2026-09-27.md`](../history/runsheet-2026-09-27.md), § H1).
Two records written before the bench had the remedy's mechanism wrong. The entry of
2026-08-23, on the cache-management model, read the vendor kernel's `c-r3k.c`, which uses
`ST0_ISC`/`ST0_SWC` and flushes the D-cache before invalidating the I-cache, and concluded
(translated): *"So the model is R3000's; CP0 register 20 is a Lexra extension layered on top,
not a replacement."* `R1-gate`'s stop-loss, written before the work, priced the fallback for a
cell 1 that would not hold as *"flush D-then-I through `CCTL` **and** take the `Status.IsC` path"*
([`docs/history/steps-R1-gate.md`](../history/steps-R1-gate.md), *Stop-loss, written now*).
量 Why it was wrong: the R3000's isolation, the `Status.IsC` path, does not isolate on this
core; in cell 4 its byte stores reached DRAM and both victims read `07` CORRUPT ([`CPU-19`][spec],
[`CPU-35`][spec]), though 量 the CP0 itself is R3000-class ([`CPU-19`][spec]). qemu had shown the
same failure before power (run sheet, § H1). 讀 The vendor kernel's cache code is neither r3k nor
r4k: `arch/rlx/mm/cache.c` calls `rlx_cache_init()` unconditionally ([`CPU-19`][spec], 2026-08-27).

## The single-variable cut

讀 Cells 1 and 5 differ in the store's path — cell 1 through the cached window, cell 5
through KSEG1, uncached — and in their victim pair; neither applies a treatment
([`probe1.c`](../../tools/rlxprobe/probe1.c), `CELLS`; the run sheet's four-way table, written
before the run). 量 Both read STALE with the new word, `240222b2`, in memory: the store reached
RAM either way, and the old constant ran from the I-cache ([`CPU-19`][spec]; `H1b.log`).
量 Adding the I-cache invalidate alone, `CCTL 0x002`, to either path — cells 2 and 6 — turned
every victim FRESH ([`CPU-19`][spec]; the command's name is 讀, [`CPU-20`][spec]).

## Cause

量 This core's I-cache hands back stale bytes after a store to RAM, and invalidating it with
`CCTL 0x002` alone is enough for these stores ([`CPU-19`][spec]); for them the vendor's D-side
write-back first is unnecessary rather than wrong (`notes/cache-model.md`, *Measured on the device,
2026-08-25*). What the cut cannot separate: 推 both stores hit lines the D-cache did not
hold, so a write-through D-cache and a write-back one that does not allocate on a write miss
read the same; the first write-up's *"the D-cache is write-through"* was narrowed on
2026-08-26, and the question is ⊘ with a reopening condition ([`CPU-19`][spec] and its 殘留).

## Positive control

量 The same run read FRESH wherever a treatment took — cells 2, 3 and 6 — so this instrument
can report FRESH on this die ([`CPU-19`][spec]; `H1b.log`). 量 The UART report and the RAM
block read back with `DW` agree 104 of 104 words ([`CPU-19`][spec];
[`H1c.log`](../../bench/2026-08-25/H1c.log)). 量 `probe2` measured the remedy again on another
address range and store path ([`CPU-19`][spec]; [`H2a.log`](../../bench/2026-08-25b/H2a.log)).

## The check left behind

None that CI exercises. [`tools/test-rlxprobe.sh`](../../tools/test-rlxprobe.sh) builds `probe1`
and runs it under qemu, where cell 1 must read FRESH; STALE there would mean the harness is
broken. CI runs it as step `test-rlxprobe` (workflow `instruments`,
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), job `instruments`), but the
runner has no `mips-linux-gnu-gcc`, by design, and the suite skips everything
([`tools/ci-expected.tsv`](../../tools/ci-expected.tsv), row `test-rlxprobe`); at a desk with the
cross compiler, qemu and `hazlint`'s `stage2.bin` it turns red when cell 1's first victim is not
FRESH. Nor is the finding's consumer checked: `rlxboot` writes back D and invalidates I through
KSEG1 before it jumps and links no `Status.IsC` path ([`src/rlxboot/main.c`](../../src/rlxboot/main.c),
`boot_verified`), no test asserts those calls, and rlxboot's qemu test runs the `CCTL` writes
as plain instructions ([`run-qemu-payload.sh`](../../src/rlxboot/test/run-qemu-payload.sh)).

[spec]: ../../SPEC.md
