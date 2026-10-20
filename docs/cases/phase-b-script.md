# The phase-B script's two latent defects

`v1.0`'s release, 2026-10-09. Phase B builds and checks a release's artefacts at the desk,
before phase C's outward acts ([`docs/release-process.md`](../release-process.md)). Nothing
on this page is about the device: it is about a script run at the desk, so no sentence carries
量; 讀 marks what is read out of code and 推 what is inferred. The record is [`LOG.md`](../../LOG.md),
in Chinese and quoted here translated: the entries of 2026-10-08 (the 130th segment) and
2026-10-09 (the 131st segment, and its part two).

## Symptom

At the desk, the first run of the phase-B script, `phaseb.sh`, from 06:23:31 to 06:31:41:
A1, A2, B1, B2 and B4 passed and the two builds' twelve files were identical, and then it
stopped on `PHASE-B FAIL: manifest recipe`. The 131st segment's part two (translated):
*"What was stopped was the script, not the product."* The manifest carried
`recipe_id 9bb2bec7`, a CLEAN `h601_scan` and no "NOT this archive".

## First hypothesis, and why it was wrong

No record states a hypothesis about the failure before its cause was found: the entry that
reports the `FAIL` reports its cause in the same paragraph. What the records written before
the run held is that phase B had been rehearsed. The 130th segment's entry (translated):
*"`P4b`'s phases A–B were rehearsed on a clone of `28a490c7`; every step passed (an agent; …)"*,
B3 among them with *"`verify` rc 0 (the control that changes one character: rc 1)"*. The `P4b`
entry of [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md), committed in `2eb1a3d6` at 05:01:55, before
the run, calls phase B "rehearsed on `28a490c7` and owed again on this commit", and names that
rehearsal its weakest thing because the archive's digests move with the commit; it names no doubt
about the script.

Why it was wrong, in the 131st segment's part two (translated): *"These two lines [the
manifest checks] were copied verbatim from the 130th segment's `s130/phaseb.sh`; the 130th
segment's rehearsal was one script per step (`s130/p4b/scripts/`), and `phaseb.sh` never ran
from start to end."*

## The single-variable cut

Defect 1, the separator. 讀 [`tools/srcarchive.py`](../../tools/srcarchive.py) writes the
manifest's header fields separated by tabs (`# recipe_id<TAB>…`); the script matched them
with spaces. Against the same real manifest, the corrected check read rc 0
and the 130th segment's space-separated pattern rc 1.

Defect 2, the row the control flips, found by reading the half that had not run, before the
second run. 讀 `srcarchive.py verify --sums` reads only the archive's own row of
`SHA256SUMS` (`listed.get(os.path.basename(archive))` in `verify()`), and the script's control
flipped a digit in the first row, the `iperf3` licence file's: 推 it would have read rc 0 and
stopped the script at "verify control". 讀 The 130th segment's per-step script flipped the
archive's own row, so its rc 1 had been a correct control.

## Cause

Both were carried over as if the script had run (translated): *"I copied the 130th segment's
`phaseb.sh` as something that had run, without first reading it against the tool's real
output format: the first was hit by running, the second was seen by reading before the
rerun."* The first-row version of the control appeared only when `phaseb.sh` was assembled.

## Positive control

The manifest's three conditions moved into a check of their own with six
controls: the real manifest rc 0; the 130th segment's space-separated pattern rc 1; and rc 1
each for the recipe changed to `6a11de02`, an `h601_scan` that is not CLEAN, a `# cell` line
carrying "NOT this archive", and no file. On the second run, from 06:34:25
to 06:44:34, the control that flips one byte in the archive's own row read rc 1,
`sha256sum -c` over the sums file read rc 0, and the script ended `PHASE-B OK`, rc 0. The
record holds no run of the whole corrected script against a broken input.

## The check left behind

None. The script and its controls stayed in the session's working directory and were never
committed: at `85350a89`, `git log --all` finds no path matching `*phaseb*` or
`*mancheck*`. `CLAUDE.md` gained no rule for it: the lines it gained after the case are about
other things, and its nearest rule, "A guard is shown permitting as well as refusing", dates
from 2026-09-23. Phase B as written in [`docs/release-process.md`](../release-process.md)
passes B3 on `verify` rc 0 and asks for no control. CI's `srcarchive self-test` step
(workflow `instruments`, [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), job
`text`) tests the tool's `verify` (its cases S8 and S34), and nothing that drives it.
