# The 98.9 % coverage that counted zeros

`FLS-22`, at the desk, 2026-08-30/31: how much of `H601` — the flash region holding this unit's
MAC and radio calibration — can be recovered from text in the public `upstream/` repository.
The row is in [`SPEC.md`][spec] ([how to read it](../spec/README.md)); its owner is
[`notes/leak-surface.md`](../../notes/leak-surface.md), whose § 4 holds this measurement. The
record is [`docs/log/2026-08.md`](../log/2026-08.md), the entry headed 2026-08-30/31, the 14th
segment, in Chinese and quoted here translated. Marks: 量 measured on the device, 讀 read out of
code, a dump or the history, 推 inferred. `FLS-22` marks its counts 量, but they were computed at
the desk from this unit's flash dump with no device reading (notes, header), so here they are 讀.

## Symptom

讀 The first version of the measurement reported 98.9 % of `H601` recoverable, and its own
positive control, `H1`, "passed" by covering 8,042 bytes with an eight-byte slice
([`FLS-22`][spec], notes § 4). The method: harvest every byte string a text line could encode
in three forms from the 261 readable files under `upstream/`, look each up inside `H601` in the
dump, and take the union of the offsets covered (notes § 4).

## First hypothesis, and why it was wrong

No record written before the cause was known survives. 讀 The figure enters the repository in
commit `74bc28f1`, the commit that calls it false; the tree before it holds neither the figure
nor the 8,042 (`git log -S`). The 14th segment's entry, written after the correction
(translated): *"I first measured this coverage as 98.9 %, and it was false."* So the 98.9 %
reading is known only from the record of its correction. Why it was false is the cause, below.

## The single-variable cut

None is recorded. The evidence was the control's own reading, and the entry says so (translated):
*"A control whose reading is absurd is still a reading, and it was the only thing that caught
this."* The correction then changed two things at once — constant-byte candidates dropped,
and only the 146 non-zero bytes scored (notes § 4) — and the record holds no run that made one
change without the other.

## Cause

讀 `H601` is 8,046 zero bytes out of 8,192, and an all-zero candidate matches everywhere
([`FLS-22`][spec]); only the non-zero bytes carry information about this unit (notes § 4).
讀 Scored on them, at least 45 of 146 are recovered, 30.8 % — a lower bound, not a figure for
the coverage: the harvester decodes three encodings and reads none of the 26 files a text
scanner cannot read ([`FLS-22`][spec]).

## Positive control

讀 After the correction the four controls, `H1`–`H4`, read green ([`FLS-22`][spec]). The
control that caught the defect was the positive one, `H1`, which "passed" by covering 8,042
bytes with an eight-byte slice (notes § 4); the record does not say what each control checks.

## The check left behind

None for this measurement. 讀 The harvester and its four controls are not in the repository:
the row's sources name a lookup run against the dump, and no tool under `tools/` computes the
coverage. Two committed tools apply a like rule — a byte string with too few distinct values
identifies nothing — and the record does not say either was written for this case:

- [`tools/leakscan.py`](../../tools/leakscan.py) classifies an all-zero or broadcast address
  as `TRIVIAL` before it looks the value up in the dump; the branch arrived in `74bc28f1`. CI
  runs `leakscan self-test` and `test-leakscan-mutants` (workflow `instruments`,
  [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), job `text`). 讀 The self-test's
  `L14` feeds both constant values but accepts any class, and no case or mutant names
  `TRIVIAL`; 推 so deleting the branch would turn neither step red.
- [`tools/flashwin.py`](../../tools/flashwin.py) `scan` does not search for a 16-byte window
  of the region holding fewer than `SCAN_MIN_DISTINCT` (4) distinct byte values. Its control
  `S4` requires a run of one repeated byte from inside the region to read CLEAN, and mutant
  `MS1`, which drops the filter, must be killed by `S4`. CI runs both in job `text`, steps
  `flashwin self-test` and `flashwin mutation suite`; 推 removing the filter would turn both red.

[spec]: ../../SPEC.md
