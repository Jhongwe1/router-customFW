# Corrections to block 30's card — written before the corrected cells ran

`PREDICTIONS-B32-block30.md` is frozen at `774b68b` and **is not edited**.
`tools/check-predictions.py` reads the card's mtime, and its own docstring says
fixing even a typo has to make the check fail. This file is the mechanism, and
§ 0 was written and this file saved **before** any cell named in it was run.

---

## 0. `C1-BURN` is ordered before the step that produces its expectation

### What happened

量 2026-09-20 19:20:43, `bench/2026-09-20b/C1-BURN.log`:

```
DW 8040D4A0 1
8040D4A0:	00000001	00000000	00000000	00000000
<RealTek>
```

The card predicts `00000000` and makes that the first abort condition, so the
runner stopped and **nothing was uploaded**.

### Why the board is right and the card is wrong

`RUNSHEET.md:140`, cell `B6`: `DW 8040D4A0 1` → word 1 = `00000001`, and the row
says why — 🔴 **`AUTOBURN` defaults to ON**, its initialiser in the loader image
is `1`. `PROGRESS.md:2340` records the same thing, read out of `stage2.bin`
before the first upload this project ever made. `AUTOBURN` is RAM state; a reset
puts it back to `1` (`RUNSHEET.md:571`, `G8a`).

So `00000000` is not a property of a healthy board. It is a property of a board
**after `console-dump.py rescue` has sent `AUTOBURN 0`**. `RUNSHEET.md:565`,
cell `G2`, gives the order literally: *"`console-dump.py rescue …`, then
`console-capture.py … --send 'DW 8040D4A0 1'`"*. The card has it the other way
round.

量, the whole corpus rather than an impression — every committed
`DW 8040D4A0` capture, 137 of them:

| value | count | when |
|---|---:|---|
| `00000000` | 129 | every one of them **after** a rescue on that power cycle |
| `00000001` | 8 | every one of them **before** one — `G8b-ab`, `Z-ab`, `X-ab`, `Y-ab`, `LP-ab`, `C1-P3bf`, `X2-autoburn`, `X3-live` |

No exceptions in either direction.

### 🔴 This is the third occurrence of one named defect

`docs/FINDINGS.md:158` already carries it, verbatim:

> **A card can inherit an expectation without the step that produces it, and the
> abort will fire on a healthy board.** `Y-ab` predicted `AUTOBURN` = `00000000`
> and made it the first abort condition; the board said `00000001`, which is the
> documented power-on default. Every `00000000` in this repository is read after
> a rescue has sent `AUTOBURN 0`, and the block has no rescue step because it
> uploads nothing. **The card written the same evening repeated it.**

That is `CARD-1`, `bench/2026-09-01/CORRECTIONS-block6.md` § 2 — occurrences one
and two. This card is the third, and it was written by someone who had read the
row. ⚠️ **Nothing in this repository checks it.** `cardcheck numbers` passed
`15 of 15` and could not: the expectation is prose in a `#--` comment, not a
`cardnum` row, and no tool relates a cell's expectation to the cell ordering that
produces it. That is a real gap and it is recorded rather than patched in a
seating.

### 🟢 And the reading is not waste — it is this guard's first refusal

The burn-flag read-back is the one thing standing between this project and a
flash write. `tools/looprun.py` carries it as `S5b` and **refuses `--skip S5b`**,
on the stated ground that a guard a flag can switch off is not a guard. But
every one of those 129 `00000000` readings is the guard *passing*, and **a guard
that has only ever been seen passing is a wall**.

`C1-BURN` is the first time in this project that the burn-flag abort has fired on
the live board, before an upload, and stopped a block. The same shape as seating
20's `lock 6` + `brightness ← 0`: a guard taken down and put back up is worth
more than one that was never tested.

It is also the ninth independent confirmation of `RUNSHEET` `B6` — on this die,
on this seating, at a cold power-on.

### The correction

**One new cell, and no number in the frozen card changes.**

```commands
#-- C1b-BURN  the SAME read, AFTER the rescue that sets the flag.  RUNSHEET G2's
#--           order.  word 1 REQUIRED 00000000.  If it is 00000001 here, the
#--           rescue's echo said AutoBurning=0 and the word the burn path reads
#--           says otherwise -- that is C-6's two-sources case coming out the bad
#--           way, and NOTHING IS UPLOADED.
CAP --out bench/2026-09-20b/C1b-BURN --send 'DW 8040D4A0 1' --until 'RealTek>' --seconds 15
```

Running order for the rest of the block, unchanged except that `C1b-BURN` and the
rescue are inserted where the card put `C1-BURN`:

1. `C0-rescue` (off-card, already named in the card's § 2)
2. **`C1b-BURN`** — `00000000` required
3. upload (off-card, already named)
4. `C2-HEAD` onwards, exactly as the card has them

`C1b-BURN` is **outside** the `cells` fence, deliberately: the fence is frozen and
a cell added to it after the block began would be a card edit wearing a different
name. It is declared here instead, which is the same treatment
`bench/2026-09-20`'s forty-three `X*` cells got.

### Rejected alternatives, recorded because the choice mattered

* **Edit the card so `C1-BURN` comes after the rescue.** Rejected: the block has
  run, `C1-BURN.log` exists, and moving the card's mtime past it turns a real
  reading into a `check-predictions` regression. The frozen artefact is the
  evidence.
* **Re-run `C1-BURN` with `--force` after the rescue.** Rejected: `--force`
  overwrites the capture, and the capture is the measurement that makes this
  section a finding rather than an apology.
* **Widen the gate to accept `00000000` or `00000001`.** Rejected outright. That
  is repairing the instrument to agree with the experiment, and the instrument in
  question is the only thing between this project and a flash write. Seating 14
  made the same choice the same way: *the tolerance was not widened; the window
  was moved.*

---

## 1. The runner's gate compared a literal echo, and `FW-47` says it cannot

### What happened

`C5-SW` **passed on the board and the runner called it a STOP**, at 19:24.
量 `bench/2026-09-20b/C5-SW.log`:

```
echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl81R9LxX-FswWi-tSW
-cUhN
LOCK
RLXFW-SW-START
#
```

`R9LxX-FswWi-tSW` is `RLXFW-SW` and `9x-swit` woven together one character at a
time, and `-cUhN` / `LOCK` completes `-ch` and `UNLOCK`. The board emitted
`RLXFW-SW-UNLOCK`, then `RLXFW-SW-START`, then the prompt. **The cell did exactly
what it was written to do.**

### Why the gate was wrong

`SPEC.md` `FW-47` (and `FW-41` before it): `rlxfw_mark()` writes to the console
character by character and interleaves with busybox ash's echo of the line that
caused it. The repository's own conclusion from that is *gate on FIELDS, never on
MARKS* — and a gate that requires the **echo** to be present verbatim is the same
error one layer out, because the echo is the other half of the same interleave.

⚠️ It only bites on a long line: the echo of a 77-character command takes ~20 ms
at 38400, and the first mark prints inside that window. `C4-LIVE` (20 characters)
was unaffected, which is why the defect survived four cells.

### The replacement, and it is strictly better

**The universal gate is now *the prompt came back*, not *the echo is present*.**

An echo proves only that the line discipline ran — § 0.1 of the card is the whole
reason that is not enough, because seating 29's wedged board echoed 3,735
characters. A **prompt** proves the shell read the line, ran it and returned.
That is the same quantity `X44-l8k-live` (41 B, prompt) and `X45-l32k-live`
(22 B, echo only, no prompt) differ in, so the gate is now measuring exactly what
§ 0.6 is about.

Where a specific mark still has to be checked, the test is a **subsequence**
rather than a substring — interleaving preserves order, so a subsequence sees a
mark that `in` cannot. `RLXFW-SW-UNLOCK` and `N-ALLOC=A15B8000` are both checked
that way now.

### 🔴 Both of this block's instrument defects were documented traps, and both failed safe

`§ 0` walked into `CARD-1` and this one walked into `FW-47`, on the same block,
within four minutes, in a repository that records both. What is worth keeping is
the direction: **each one refused a healthy board rather than passing a sick
one.** The burn-flag gate refused before an upload; the echo gate refused before
spending the next cell. A pair of instrument defects that can only fail toward
STOP is a different thing from the composition `CLAUDE.md` records for 2026-09-17,
where two harmless defects composed into a green that hid a red.

⚠️ Neither cell is re-run. `C1-BURN` and `C5-SW` keep their captures, because
both captures are the evidence.
