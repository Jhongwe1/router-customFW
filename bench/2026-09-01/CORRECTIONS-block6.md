# CORRECTIONS — seating 9, blocks 5 and 6, 2026-09-01

Beside `PREDICTIONS-B7-block5.md` and `PREDICTIONS-B7-block6.md`, which are
frozen and were not touched after their first capture landed. Everything that
went differently from those two files is here.

---

## 1. `Y0-A` — cycle 1's cold boot opened 1.093 s late and is void

**What happened.** The first power-up of the seating was applied about half a
second before `console-capture` had the port. The capture's first byte is at
`t = 1.093 s` and it is `P0phymode=01, embedded phy` — the middle of the boot
text. `ramSize: 32M` is not in the file at all, so **the byte where `C-8`'s
cold/warm discriminator lives was never recorded**, and block 5's `Y-A` cell —
*a single space after `ramSize: 32M`* — could be neither confirmed nor refuted.

**What was done.** The board was power-cycled and `Y-A` retaken with the
capture opened first and the operator applying power on a signal. Cycle 1's
capture is kept under a name that is not any block's cell:

```
superseded-by: bench/2026-09-01/Y-A
superseded-cell: bench/2026-09-01/Y0-A
reason: capture opened 1.093 s after the board began printing; the
        `ramSize: 32M` line, and therefore `C-8`'s discriminator, is absent
```

🔴 **The `superseded-by:` line above is the format `PRED-1` names and nothing
in this repository had ever written.** `PRED-1`: of 34 cells with no capture,
**14** were voided at the bench and re-run under a new prefix, and *nothing
links a superseded cell to its replacement*, so `check-predictions`'s one
sentence is wrong for that third of them. This is the first link. It does not
close `PRED-1` — the fourteen earlier ones still have none, and no tool reads
this line yet.

**Why the power cycle was spent, at that moment and not later.** `Y-A` is the
**negative control for `Y-j1`**: without a same-seating cold boot showing the
single space, `Y-j1`'s discriminator rests on `C-8`'s three earlier instances
rather than on this seating. Nothing had been established yet, so the cycle
cost almost nothing then and would have cost the seating later.

🔴 **A rule this exposed, and it is not in the capture — it is in `CLK-18`.**
`SPEC.md` `CLK-18` excludes three captures because *the first byte arrived
within 0.02 s of the capture opening, so that is not the moment the line came
up*. `Y0-A`'s first byte is at **1.093 s** and passes that test, while being
demonstrably mid-boot. **The stated exclusion rule would not have caught it**;
what caught it is the value — `looptime` reads `first-><RealTek> = 0.064 s`,
far outside 2.176–2.636. The rule is weaker than it reads, and §4 below
replaces the quantity it was protecting.

---

## 2. 🔴 `Y-ab` — the prediction is refuted, the board is right, and the abort was overridden

**Block 5 §2** predicts `DW 8040D4A0 1` → `00000000` and **§5 makes it the
first abort condition**: *"reads anything but `00000000` → stop, nothing else
runs."*

**量**: `8040D4A0: 00000001`.

**The cell is wrong, and two committed sources already said so.**

| source | what it says | mark |
|---|---|---|
| `SPEC.md` `REG-23` | `0x8040D4A0` is `AUTOBURN`; **上電後 `1`** — auto-burn at the prompt is on by default — and **每一次重置都會把它打回 `1`** | 量 |
| `RUNSHEET` `B6` | `DW 8040D4A0 1` → word 1 = `00000001`. *"`AUTOBURN` defaults to ON. Its initialiser in the image is `1`."* | 量 |

**Every `00000000` reading in this repository is taken after
`console-dump.py rescue` has sent `AUTOBURN 0`** — that is what `AutoBurning=0`
in those transcripts is. Block 4's order is `K-A` → `K-0r` (rescue) → `K-P0`
(`00000000`); `L-0ab` follows `L-0r`. **Block 5 has no rescue step at all**,
because it uploads nothing — so it inherited the expectation without the step
that produces it.

**Proved on the wire the same power cycle, one command apart**: `T-0r` sends
`AUTOBURN 0`, `T-ab` then reads `8040D4A0: 00000000`. Same seating, same
register, the rescue between them.

🔴 **The abort was overridden, and this is the reasoning, written so it can be
disagreed with.** The guard exists to stop an upload reaching flash. Three
things decided it:

1. **Block 5 uploads nothing.** Its cells are `DW` reads and `J BFC00000`.
   `AUTOBURN` gates the TFTP *receive* path and nothing else.
2. 讀 `docs/loader-command-semantics.md` §c: *"`AUTOBURN` is read at exactly one
   instruction"*, with `0x80409944` the only writer. `FLR` is at `0x804099AC`
   and moves flash → RAM. **No command on either block between that reading and
   the upload can burn anything.**
3. **The guard that protects the upload is `T-ab`, and it ran** — after the
   rescue, requiring `00000000`, before `T-1`.

**What would have made this unnecessary**: a cell whose expectation names the
state it is asserting about. `Y-ab`'s expectation is right for *after a rescue*
and wrong for *at a fresh prompt*, and the cell says neither.

---

## 3. `T-ab` and `T-0r` ran in the opposite order to the one block 6 lists

Block 6 §4's table lists `T-rz` → `T-ab` → `T-0r` → `T-0t` → `T-1`. **`T-ab`
requires `00000000` and `T-0r` is what produces it**, so as written the guard
fires on every run — the identical defect to §2, in a file written by someone
who had just read block 5's version of it and did not see it.

**Run order was `T-rz` → `T-0r` → `T-ab` → `T-0t` → `T-1`.** Both cells ran,
both names stand, both are in the block's `cells` fence and both resolved. The
swap is recorded here rather than by editing a frozen file.

It was caught by reading, before power — but only *after* the board had already
refuted the same expectation in `Y-ab`. **The board found it first.**

---

## 4. `CLK-18`'s two groups are the instrument, and the carried-forward hypothesis is refuted

The zero-cost experiment `R4-2` carried: apply `C-8`'s cold/warm discriminator
to the fourteen captures whose to-prompt values split 9/5 with a 165 ms gap.

**Result ①, the hypothesis is refuted.** All fourteen are **cold** — every one
prints a single space after `ramSize: 32M`. The split was never cold-vs-warm.

**Result ②, the split is in the measurement.** `looptime.to_prompt` sets
`first_byte = rows[0][1]`: the first read, whatever byte it carried. 量 over
the fifteen cold captures (the fourteen plus tonight's `Y-A`), **six open on a
line-transition byte** — `0x00`, `0xFC` or `0xFF` — that precedes `Booting` by
**0.321–0.350 s**; the other nine start within 0.002 s of it.

| origin | n | min | max | range | largest gap |
|---|---:|---:|---:|---:|---:|
| `rows[0]` → `<RealTek>` (as measured until tonight) | 15 | 2.171 | 2.636 | 0.465 | **0.165** |
| `Booting` → `<RealTek>` | 15 | 2.095 | 2.315 | **0.220** | **0.075** |

**The 165 ms gap is not in the board.** Corrected, the population is unimodal.

**Result ③, an independent population agrees.** Seating 9's twenty-one warm
boots, one power cycle: `Booting` → `<RealTek>` = 2.104–2.365 s, n = 21, range
0.261 s, largest gap 0.053 s. Also unimodal, and overlapping the cold range —
consistent with `CLK-15`'s measured cold/warm difference of +4.5 and +14.5 ms.

**The instrument was changed, not just the table.** `tools/looptime.py`
`to_prompt` now reports a second interval from `Booting`, and **absent rather
than defaulted** when `Booting` is not in the capture before the marker — a
fallback would make the two agree exactly when the correction matters least.
Controls `P7`, `N11`, `N10` and `A2`; 22 → **26**, mutants 20/20.

---

## 5. What did NOT need correcting

Recorded because a corrections file listing only failures reads as if the card
were mostly wrong, and it was mostly right.

* 22 of block 5's 24 cells hit as written, including all nineteen repeats.
* `Y-j1`'s three refutation directions: none fired.
* §2.1's timing cell came out as the **third** pre-registered outcome — 0.5 ms,
  at the instrument's floor — which the block wrote down in advance as a real
  answer rather than a miss.
* All eighteen of block 6's cells hit, including the four-window bracket's
  fourteen comparisons and `T-3`'s byte-identity.
* Every terminator held: no capture ended on `--idle` with its predicted string
  missing, which is §1's own refutation condition and it did not fire.
