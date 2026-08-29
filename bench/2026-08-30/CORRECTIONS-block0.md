# CORRECTIONS — `PREDICTIONS-B5-block0.md`, after the seating

**Written 2026-08-29 after power cycle 1.** The block is frozen and is not
edited — it says so in its own second paragraph, and editing it would move the
mtime and make `check-predictions.py` fail correctly. This is the list of what
it says that the seating showed to be wrong, in the shape §B5-c12 established
for block 1.

**The block's own gate passed**: `13 of 13 captures came after the prediction, 0
did not`. Nine of the thirteen cells matched byte for byte. What is below is the
residue, and two of the nine items are defects in *instructions* rather than in
predictions — those are the expensive kind.

---

## 1. 🔴 `Q-A` as written never returns, and the same defect is on §B5's card

🔄 **The count in this section's original heading — *twelve times* — is wrong; it is **14 of 15**, and §*Corrections to this file* at the bottom has the enumeration and three more errors of mine.**

**§0's `Q-A` row is `CAP --out …/A-catch --esc 25 --esc-period 0.002` — no
`--seconds` and no `--idle`.** 量, `tools/console-capture.py:699-700`: both
default to `0.0`, and the capture's final loop (`:543-551`) breaks on **neither**.
量, `timeout -s TERM 8` against a board-off port: `rc=124`. It had to be killed.

**What a kill costs is `.meta.json`**, which is written only at the end
(`:578-583`). The `.log` and `.timing` survive because they are flushed per
chunk (`:380-382`). So this does not lose the boot bytes and does not by itself
cost a power cycle. **What could cost the cold-boot reading is the recovery**:
the tool refuses to overwrite an existing `.log` (`:296-297`), and the way past
that refusal is `--force`, which would replace a cold capture with a warm one.

量 over all **eight** committed `A-catch` captures: every one passed
`--seconds` — `esc 25 → 40`, `esc 45 → 65`, `esc 180 → 200`. **Not one was ever
run the way the cards write it**, so this is a defect of the cards and not of
past practice.

**Scope, and the pattern in it** 🔄 **(counts corrected 2026-08-30 — see §*Corrections to this file* below)**: block 0 carries `--seconds` on **12 of 13**
rows and omits it only here. `RUNSHEET` §B5's card carries it on **1 of 13** —
only `L-3`, the one row whose window someone actually reasoned about. The
terminator was written wherever a number was being thought about and dropped
wherever it looked obvious, which is exactly where the tool supplies no default.

**What was run**: `--esc 180 --esc-period 0.002 --seconds 200`, the operator's
choice between two windows with committed precedent. The long window is
measured-compatible with this cell rather than assumed to be —
`bench/2026-08-25` and `bench/2026-08-25b` both used `esc 180 → seconds 200` and
both produced the canonical 181-byte slice.

⚠️ **Not fixed in the tool today, deliberately.** A refusal when neither
terminator is given is a three-line change to the one instrument the whole
seating runs through, and `test-console-capture.sh` would have to be re-run and
probably amended. Changing it between the desk validation and the bench is the
shape `P7` exists to prevent. Carried forward.

## 2. 🔴 §4's `^[` prefix rule watches for the wrong bytes, and today produced the negative control it lacked

§4: *"those bytes are `0x5E 0x5B` repeated — the literal two characters `^[` …
printed by the **loader's own readline** as it echoes the stream `--esc` is
sending"*, and the rule built on it: *"Any run of `0x5E 0x5B` means a loader was
already answering."*

**The first half is right about those files and the attribution is wrong.** 量
across all nine `A-catch*.log` plus today's two:

| capture | prefix | raw `0x1B` | `0x5E 0x5B` |
|---|---:|---:|---:|
| `2026-08-24d` | 2,814 | **0** | 1,407 |
| `2026-08-24e` | 4,424 | **0** | 2,211 |
| `2026-08-24f` | 2,810 | **0** | 1,405 |
| **`2026-08-30`** (cycle 1) | 0 | 0 | 0 |
| **`2026-08-30b`** (cycle 2) | **117** | **117** | **0** |

Today's cycle 2 opened its capture while **the loader from cycle 1 was still at
its prompt** — the literal condition the rule names — and the prefix is 117
**raw `0x1B`** bytes with zero caret pairs. **The rule would not have fired on
the case it exists to catch.** The whole-file counts say the same thing at scale:
cycle 1 holds 81,457 raw `0x1B` and 0 caret pairs, in runs of 128 followed by
`Unknown command !` — the 128-byte `readline` cliff, 637 times.

**So the loader echoes raw ESC.** What produces `^[` is a **Linux tty** with
`echoctl`, and `24d`/`24e`/`24f` are the later cycles of 2026-08-24 — the day
the vendor kernel was booted to userspace in `24c`. That attribution is 推: the
encoding difference is 量 in both directions, but nothing here reads the vendor
tty's termios settings.

**The rule is strictly more useful once corrected**, which is why it is worth
the row: the prefix does not merely say *not cold*, it says **which of the two
was answering**.

## 3. 🔴 §12's cross-check table pairs `tmpl` with the wrong word, and the mechanical check could not have caught it

§12: *"All 25 pairings resolve, and every one of the 45 defined header words is
`rb_put()` somewhere in the source — checked mechanically."*

Run against the seating, 24 of 25 agreed and `tmpl` did not: the UART printed
`tmpl=03e00008`, the block's word 19 held `80500ED0`.

讀, `probe3.c`:

* `:1047` — `rb_put(H_TMPL, (u32)rlx_vic_template)` → word 19 is the template
  **address**
* `:1063` — `field("tmpl", rd_unc((u32)&rlx_vic_template[0]))` → the UART line is
  the guard **word**
* the guard word is in the block at **word 20**, `H_TMPL_W0`

量: word 20 = `03E00008`. With the pairing corrected the table is **25 of 25**.

🔴 **The mechanical check that was run is not the check that was needed.** *Every
header word is written somewhere* cannot detect a UART line and a block word
sharing a name while carrying different quantities. `H_TMPL_W0`'s own comment
says what it is — *"the guard word AS ASSEMBLED, read back through KSEG1"* — so
the source distinguishes them and the table did not.

## 4. `break.epc` — refuted, and the reasoning was the wrong shape

§10 predicted *"an address inside the image, **not** `probe2`'s `80500270`
— different build, different offset. Only its range is predicted."*

量: **`break.epc=80500270`**. Exactly `probe2`'s value. The prediction that the
two builds must differ here was an inference from the builds differing
elsewhere; the `break` site's offset happens to coincide.

## 5. `install.changed` — the value withdrawn yesterday was correct, and withdrawing it was still right

§10 recorded `0000002b` (43) as **withdrawn**: it had rested on *"probe2, with
the identical handler"*, and 量 showed `exc.S` was committed four hours after
`H2a`'s seating with the 22 emitted words hashing differently between the two
builds. The block predicted only *"non-zero, and ≤ 44"*.

量: **`install.changed=0000002b`** — 43.

**The withdrawal was methodologically right and the number was right.** The
stated reason for the prediction was false, so the prediction was not supported
even though its value was true. Recorded because the tempting lesson — *"you
withdrew a correct prediction"* — is the wrong one: a prediction that is right
for a refuted reason is not evidence, and 43 is now 量 rather than a guess that
got lucky twice.

## 6. §7's pointer-shape refutation condition fires on noise

§7 lists as a refutation *"any aligned pointer-shaped word `80xxxxxx` /
`81xxxxxx` / `A0xxxxxx` / `B8xxxxxx`"*, quoting `G0` verbatim as *"any one
pointer-shaped word and the address is re-picked"*.

量, across the four windows (64 words): **two words carry a listed prefix** —
`813515F5` and `81771575` — and **neither is 4-byte aligned**. Under the
verbatim quotation the arena would have been re-picked; under the word
*aligned*, which the block also uses, nothing fires.

**Neither reading is a good discriminator.** For uniform random words the loose
form fires with probability `1 − (63/64)^64` = **63.6 %** on any 64-word sample,
and the aligned form at **22.2 %**. A condition that fires on two thirds of
random samples is not a refutation condition; it needs a rate, not a
presence test. This was its first run.

**What the other five shapes did**: none fired, and the one with real power was
*any two of the four windows byte-identical* — measured at **0 of 16 words equal**
for all six pairs, which is what a live read path looks like.

## 7. The `--seconds` sizing section: the observation holds, the explanation is backwards

§0's rate box reads *"the **longer** reply is the slower one so it is the first
line's fixed cost rather than a per-byte overhead."*

`Q-3` adds a third point at 2.4× the largest reply this device had executed:

| capture | bytes | window | B/s |
|---|---:|---:|---:|
| `H1c` | 1,667 | 0.447 s | 3,726 |
| `H2g` | 9,660 | 2.688 s | 3,594 |
| **`Q-3`** | **23,523** | **6.697 s** | **3,512** |

A fixed startup cost is `T = F + N/r`, whose rate `N/(F + N/r)` **rises** toward
`r` as `N` grows. It cannot produce a rate that falls with size. Fitting
`T = a + b·N` over the three points gives a **negative** intercept
(−0.03 to −0.11 s), which is the signature of the clock starting at the **first
read** rather than at the first byte: `console-capture.py` drains on a 50 ms
grid, so a short reply has a larger fraction already buffered when timing begins.

**The marginal (slope) rate is 3,458–3,497 B/s, and that is the conservative
figure for sizing a window** — not 3,594. Every margin on this card was still
comfortable: `Q-3` finished in 6.71 s of a 15 s window (2.24×) and `Q-5` in
1.98 s (7.6×).

## 8. §3's `carrier` warning was right, and it is now a measurement

§3: *"`carrier` on `enxfc19286184c9` reads `1` with the board unpowered … if it
is `1` both times, it is a cell that cannot fail."* 量 today: **`1` with the
board off and `1` with the board on.** It carries no information about the board
on this path and should not appear in a preflight as though it did.

## 9. The report-length model, for the record

§10 predicted **5,728** bytes for the branch *"`c-A` negative, Group V stays
void"*, which is the branch that ran. 量: **5,642** bytes to `rlxprobe: end`,
including the `J` echo and the jump line. **−86, or 1.5 %.** The line-length
model is good to that; recorded rather than corrected.

---

## What the block got right, because a corrections file that lists only errors misreports the block

* **`Q-4` byte for byte**, and it is the only upload check this block has:
  `0x80500000` = `3C1D8051`, `0x8050000C` = `250871A0` → `_bss_start` =
  `0x80500000 + 29,088`, with `_bss_end − _bss_start` = 752 = the `.bss` the
  build printed. Three numbers from three places.
* **Every `reply-size.py` byte count exactly**: 71, 71, 71, 213 ×4, 23,527, 71,
  118, 7,593. Including 23,527 at a scale the model had never been used at.
* **`pc=80502c74`**, computed from today's ELF before the run.
* **`flags=50010002`**, derived from the Makefile's own expression, and it is
  the device-build discriminator: qemu's is `50070002`.
* `status=1000fc00`, `handler_words=00000016`, `install.bad=00000000`,
  `kseg0=00000001`, `break.count`/`break.cause`, `arena=80a10000`, no
  `CLEAR_BEV` warning, `rb=` in lower case.
* **The `A-catch` slice**: `f5287ff9f64b1035…`, the eighth agreeing capture, and
  §4's honesty about it stands — it is a consistency reading with no
  demonstrated negative, and it is still that.
* **`Q-0ab` / `Q-0ab2` as a bracket**: `00000000` at both ends, over six
  commands, which is the reading the second read was added to produce.
* **The free over-run control**: `w641`/`w642`/`w643` all `DEADC0DE`, on the
  seal's own reply line, costing no command — exactly as §12 worked out the day
  before.
* **The three-way seal**, now `tools/rbcheck.py`: `C93E60B5` on all three
  channels with the `− 0x10` derived rather than assumed.


---

## 🔴 Corrections to this file, 2026-08-30, from the adversarial pass

This file was itself put to four hostile readers. Three of its own numbers were
wrong and one of its severity claims was inverted. The findings survive; the
arithmetic did not.

### §1's count is wrong in both numerator and denominator

*"Twelve of `RUNSHEET` §B5's thirteen card rows omit it."* 量: §B5's card is
**18 rows**, of which **15 are `console-capture.py` invocations** — `L-0r` is
`console-dump.py`, `L-1` is `loader-tftp.py`, and the `host` row is `tcpdump`.
Only `L-3` carries a terminator. **The number is 14 of 15.**

And §B5-c13's own remediation table **drops `L-6c` and `L-7b`**, both of which
issue a `--send`. Worse, that table then assigns `--seconds 20` to *"`L-7a` and
the `L-7b…e` sweep"* — **fixing a row it did not count as defective**.
Conditionality is not the exclusion rule either: `L-8` is equally conditional
and *is* counted. `L-6c` still gets neither a count nor a number, so a literal
reader hangs there.

### §1's severity is inverted, and the danger path runs the wrong way

量, on a pty: **`SIGINT` writes a complete `.meta.json`** (`rc=1`, not the `rc=0` the reviewer reported — I measured it) —
`stop_reason='interrupted'`, the CR record intact, via the handler at
`console-capture.py:552`. **Only `SIGTERM` loses it.** `timeout -s TERM` is a
harness artefact; **a bench operator presses Ctrl-C and loses nothing.**

And 量: `console-capture.py report` on a `SIGTERM`-killed capture returns
`rc=0` — the `.log` is complete and usable without its metadata. **So `--force`
is never the correct recovery**, and §1 framed the overwrite refusal as the
obstacle when it is the safety feature. On `L-A` specifically the ESC window is
already on disk before a hang is even noticeable, so a `--force` re-run
*destroys* a good capture rather than recovering one. Reaching the danger needs
two compounded operator errors, not one.

### 🔴 And the census was an inference, which is a larger defect than the one §1 found

*"量 over all eight committed `A-catch` captures: every one passed
`--seconds`."* **That is not a measurement of what was passed.** 讀,
`console-capture.py:302-333`: the metadata records `esc_seconds`,
`esc_after_seconds`, `esc_period_requested_s` and `cr_settle_s` — **and neither
`seconds` nor `idle`.** The census reads it out of the `stop_reason` string,
which is one-directional: it can prove `--seconds` *was* passed and can never
prove it was not.

**So the instrument does not record its own terminator**, in the tool whose own
comment at `:217-219` says *"what the instrument did to produce it is part of
the reading"*. That is the defect to fix first, and it is a bigger one than the
missing card rows. Carried forward.

⚠️ Also: the census said **eight**; the index now holds **ten**, because today's
two `A-catch` captures are themselves committed. Both passed `--seconds` (200
and 40), so n=10 does not move the conclusion — but the sweep excluded the very
captures the next paragraph describes.

### §6's probability arithmetic is wrong three ways, and the conclusion still holds

* `1 − (63/64)^64` = **0.635013**, i.e. **63.50 %**, not 63.6 %. 63.6 % would
  need n = 64.17.
* **The condition is `G0`'s, and `G0`'s own sample is 12 words**, not 64 —
  three `DW … 1` reads, rounded up by `LDR-07` to four words each. At `G0`'s own
  n the loose form fires at **17.2 %**. Charging `G0` with a rate computed on a
  sample 5.3× its own is not fair to `G0`; the 64-word figure belongs to `P2`,
  which *inherited* the condition.
* **Uniform random is the wrong null and this project already says so.**
  `MEM-16` records this board's uninitialised DRAM as 89.5 % reproducible
  against a *measured* null of 55.98 %, with a 1 KiB period — and `MEM-16`'s
  owner is `RUNSHEET`'s `G0`, the same cell. Fitting the position-wise model to
  the 64 words actually captured gives P(top byte in the set) = **0.00849** per
  word against uniform's 0.015625, so uniform is **1.84× too generous** and the
  honest figure is **42.0 %**, not 63.5 %.
* And independence fails on the data itself: the two hits, `813515F5` and
  `81771575`, sit at **the same word offset `0x34`** in windows 0xE0000 bytes
  apart — ~1/16 under independence, and expected under `MEM-16`'s 1 KiB
  periodicity. A binomial over 64 iid draws is the wrong shape at any p.

**The conclusion survives all four errors**: at the correctly fitted 42 % a
presence test still fires on two fifths of null samples, so *"it needs a rate,
not a presence test"* stands. Right answer, wrong numbers.
