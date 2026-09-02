# CORRECTIONS — seating 10, block 7, 2026-09-02

Beside `PREDICTIONS-B8-block7.md`, which was amended **twice before power and
before any capture existed** — both amendments are logged in the card's own text
with what they changed and what they did not — and was not touched after
`LP-A` landed at 12:13:16. Everything that went differently from that file is
here.

**One power cycle, 12:13:16 → 12:16:26.** Nine cells, **eight captured**, and
the ninth is the one the card said in advance would be served under another
name. Zero flash-write commands; the burn flag was read back out of memory
before the only upload, and it read `00000000`.

---

## 1. `LP-3` has no capture, and `looprun`'s `S7` is why — this was written before power

**What happened.** The card's cell list names `bench/2026-09-02/LP-3`, and the
seating ran `looprun --mode bench`, whose `S7` writes `LP-boot`. So
`check-predictions` reports **8 of 9** with `LP-3` absent.

**Why this is not a missed cell.** The card's second amendment says it, in the
file, before power:

> `S4` writes `LP-rz` where the hand row is `LP-e5`, and `S7` writes `LP-boot`
> where the hand row is `LP-3`. … **No expectation moves**: `S7`'s assertions
> are `LP-3`'s prediction verbatim — eleven marks in order,
> `RLXFW-ID0=B1434383`, a prompt — made by the tool instead of by eye.

`LP-3`'s prediction was therefore **tested and hit**, by `A1`, `A2`, `A3` and
`A4` over `LP-boot`, which is a stronger reading than the hand column's would
have been: nobody looked at the log and decided it was right.

```
superseded-by: bench/2026-09-02/LP-boot
superseded-cell: bench/2026-09-02/LP-3
reason: the seating ran the loop tool rather than the hand-typed column for
        S4-S7; `looprun`'s S7 writes `-boot`. Same wire command
        (`J 80500000`), same predictions, asserted by the tool
```

🔴 **What this exposes is a real defect and it is `NAME-1`-shaped**: the card's
command column and the runner's plan are said to come from one list, and they
do — but they render **different `--out` names for the same command**, so a
card cell and a runner stage that are the same thing cannot be matched by any
tool here. `check-predictions` has no way to know. The `superseded-by:` block
above is the only link and a human wrote it.

⚠️ **This is not the same as block 6's `Y0-A`.** That one was a capture that
should not be read. This one is a capture that exists under another name.

---

## 2. `Q1`–`Q7`, scored

| id | prediction | reading | |
|---|---|---|---|
| `Q1` | `LP-ab` reads `00000001` | `00000001` | 🟢 |
| `Q2` | `LP-ab2` reads `00000000` | `00000000` — read by `S5b`, which did not exist when the card was written | 🟢 |
| `Q3` | `LP-3` prints `RLXFW-ID0=B1434383` | `LP-boot` prints it, and `A3` says *board printed b1434383, build computed b1434383* | 🟢 |
| `Q4` | `entry` below 2.8 ms **and** the read cadence below 1 ms | `entry` **2.3 / 2.4 ms**; cadence **0.666 / 0.664 ms** | 🟢 |
| `Q5` | 猜: `entry` in 1.0–2.6 ms | 2.3 / 2.4 ms | 🟢, and it was a guess |
| `Q6` | `LP-wd` reads `A5000000` | `A5000000` | 🟢 |
| `Q7` | eleven marks in declaration order | `A1` all present, `A2` 11 in order | 🟢 |

**Seven of seven.** `Q4`'s refutation condition — *a cadence still ≥ 2 ms* —
did not fire.

---

## 3. 🔴 The ESC period floor is ADDITIVE, and the card's model implied a target it cannot reach

**What the card assumed.** `--esc-period 0.0005` was written as though the tool
would deliver 0.5 ms. It delivered **0.666 ms**.

**What was measured**, n = 4, two requested periods, one seating, out of
`console-capture`'s own `achieved_period_s` — which exists in the metadata
precisely so this is askable:

| capture | requested | writes | window | achieved | achieved − requested |
|---|---:|---:|---:|---:|---:|
| `LP-A` | 0.002 | 11,684 | 25.0006 s | 0.002140 | **140 µs** |
| `LP-rz` | 0.002 | 4,638 | 10.0012 s | 0.002156 | **156 µs** |
| `LP-e5` | 0.0005 | 15,010 | 10.0001 s | 0.000666 | **166 µs** |
| `LP-e5b` | 0.0005 | 15,057 | 10.0004 s | 0.000664 | **164 µs** |

🟢 **The overhead is additive, not multiplicative, and the two groups
discriminate between those two models.** A multiplicative floor fitted to the
0.002 group (1.07×) predicts **35 µs** of overhead at 0.0005; the reading is
**165 µs**. An additive floor of ~150 µs predicts the 0.0005 group to within
16 µs. ⚠️ The two groups still differ by ~15 µs and n = 4 cannot explain that,
so the model is *additive plus something small*, not *additive*.

**What it does not change.** `Q4` asked for a cadence below 1 ms and got one.
Nothing on this card depended on 0.5 ms exactly.

**What it does change.** Any future cell that writes `--esc-period X` and
reasons about X rather than about `achieved_period_s` is reasoning about a
number the instrument does not produce. The floor is **~150 µs per ESC write**,
量, n = 4.

---

## 4. 🟢 `entry` is a property of the board, and this seating separated it from the instrument for the first time

**The 2026-09-01 problem.** `boot-timeline`'s `entry` is *the largest gap
between two reads that returned data, from the capture's start to the first
boot byte*. Its floor is therefore one read period. Over 21 resets at
`--esc-period 0.002` it read 1.7–2.8 ms, mean 2.4 — and the read cadence was
2.088–2.126 ms. **`entry` was sitting at ~1.1 read periods, which is the
instrument's floor**, so the two were not separable and `ESC-1` was opened.

**What this seating did.** Two resets at a **3.2× finer** cadence, and — the
part that matters — **one reset at the coarse cadence in the same power cycle**,
so the comparison is not across days or across board states.

| capture | achieved cadence | `entry` | `entry` in read periods |
|---|---:|---:|---:|
| `LP-e5` | 0.666 ms | **2.3 ms** | ≈ 3.5 |
| `LP-e5b` | 0.664 ms | **2.4 ms** | ≈ 3.6 |
| `LP-rz` | 2.156 ms | **2.3 ms** | ≈ 1.1 |

🟢 **The ruler got 3.2× finer and the number did not move.** Had `entry` been
the read floor, it would have fallen to ~0.7 ms. It did not. So **2.3–2.4 ms is
a silence on the board**, 量, and `ESC-1`'s question is answered.

⚠️ **What it is NOT.** `entry` is not the watchdog timeout. It spans the
timeout **plus** the reset **plus** the time to the first boot byte, so it is an
**upper bound**: the timeout is ≤ 2.3 ms. `R4`'s inherited 推 value, halved down
from the measured 557.583 ms at `OVSEL=1000`, is **2.184 ms**, which sits under
that bound. Consistent, not confirmed — and the card said so
(`Q5` is 猜, and it is recorded as one).

---

## 5. 🔴 `C-6` reproduced itself inside this seating's own rescue transcript

Not predicted, and it is the measurement that the morning's `S5b` was built on.
`LP-rescue.json`, verbatim:

```
sent "AUTOBURN: 0"      reply "Unknown command !"
sent "AUTOBURN 0"       reply "AutoBurning=0"
sent "LOADADDR: 80500000"  reply "Unknown command !"
sent "LOADADDR 80500000"   reply "Set TFTP Load Addr 0x80500000"
sent "IPCONFIG:10.1.1.1"   reply "Unknown command !"
sent "IPCONFIG 10.1.1.1"   reply "Now your Target IP is 10.1.1.1"
```

`console-dump.py rescue` sends both forms deliberately, so the colon form's
failure is on the record for all three commands, on this board, today.

🔴 **And it sharpens what `loader-tftp.py`'s guard actually is.** That tool's
check is `"AutoBurning=0" in replies` — a **substring test over a transcript
that also contains `Unknown command !`**. It passes here because the second
form worked. It is a statement that *the string appeared*, not that *the
loader's burn flag is zero*. `S5b` read `00000000` out of `0x8040D4A0`, which
is the word the one instruction at `0x80401B9C` will read, and those are two
sources rather than one.

---

## 6. 🔴 `--iterations` is a flag that cannot do what it says, 讀

Not a correction to a cell; found at the bench while deciding whether anything
else was worth the live board, and settled **by reading, without spending it**.

`--iterations N` calls `loop_once` N times. `loop_once` begins at `S4`,
`J BFC00000`, which is a **loader** command — and iteration 1 ends with Linux
running and the loader gone. So iteration 2 sends a loader command to a busybox
shell.

🔴 **And it fails earlier than that, for a worse reason.** Every capture stage
renders `--out` from `--cell` with no iteration index, and `console-capture.py`
refuses to overwrite an existing capture. So iteration 2 dies at `S4` on *the
output file exists*, **before** it reaches the reason that matters. A run that
fails on a filename teaches nothing about the loop.

**What was done today**: `looprun` now **refuses** `--iterations > 1` with the
reason, rather than accepting a number it cannot honour. Making it actually
iterate needs a way back from Linux to the loader and per-iteration output
names, and that is `R4` work with a design decision in it, not a patch.

---

## 7. What did NOT need correcting

* Every command on the card ran as written. `cardcheck commands` had said all
  seven were invocable; nothing was mistyped at the bench.
* All nine `cardnum` values re-derived before power and none moved.
* `LP-A` opened **before** the board spoke — block 6's `Y0-A` failure did not
  repeat. `ramSize: 32M` and the single space after it are both in the file.
* `LP-ab`'s precondition column did its job: the card predicted `00000001`
  *because* no rescue had run, and the board agreed. This is the cell block 5
  got wrong and `CARD-1` exists for.
* `audit-bench-log` over all ten logs: **0 hits**. `flashwin scan --sweep` over
  the directory: 32 files, **CLEAN**. `leakscan` on the card: byte-identical
  hit counts before and after both amendments.
* 🔴 **No `FLR` ran, and that was decided in the card before power rather than
  omitted.** The flash bracket therefore stands exactly where it did:
  **1,024 of 4,194,304 bytes = 0.0244 %**, and *not one flash byte is written*
  remains unsayable.
