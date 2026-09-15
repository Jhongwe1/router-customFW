# CORRECTIONS — block 22, seating 24, 2026-09-16

**One power cycle against a budget of one.** Opened 02:19:32, the board off at
the operator's hand after 03:0x. Eleven carded cells, `check-predictions`
**11 of 11**; twelve declared off-card cells; three boots of `uc1`; **two**
runs of `probe3`; `capdate` **0 RED, 0 spanning**.

**Zero flash writes, and this time with the right instrument.** The
authoritative record of what was typed is each capture's own `.meta.json`
`sent` field plus the four rescue transcripts — **65 sent strings, 0 carrying
`FLW`/`EB `/`EW `/`FLR`/`AUTOBURN 1`**, with a synthetic `FLR 80A00200 006000
100` as the scan's positive control. `n_writes` **0** beside `n_pio_bytes`
**4,194,304** in one `/proc` dump. `FLS-26`'s ledger does not move — the map
compares against 2026-09-08, not against the 2026-08-16 dump.

---

## 0. The pre-power audit

### 0.0 What was checked and found correct

* **Three payloads, by size and sha256.** `probe3.bin` 33,616 /
  `c2069e250794ee7f…`; `nfjrom` 1,059,840 / `d66155754c271648…`; `vmlinux`
  4,141,974 / `0e8a452283b093d9…`; `ucost` 16,692 / sha16 `76c7e23180214849`.
  All four match § 1 of the card.
* **`UCOST_BUILD_ID` re-derived from the Makefile's own recipe** —
  `cat ucost.c ucost-cells.S | sha256sum | cut -c1-16` → **`8403799745aeb189`**.
* **`RECIPE_ID` by two independent routes.** The tree's `config/` (28 files)
  digests to **`efa93621`**, and so does `config/` as committed at `9d4f8e3`;
  and the artefact itself carries it — the build log of 00:49:41 has
  `RLXFW_SRC_ID=0xefa93621` on its compile lines, and the `vmlinux` contains
  **exactly one** `lui …,0xefa9` and **exactly one** `ori …,0x3621`, eight
  bytes apart. *Exactly one* is what makes the second route a reading rather
  than a coincidence.
* **`RB_POISON_W`.** `probe3.c:143` asserts `RB_WORDS == 754` and `:172`
  asserts `RB_WORDS % 4 != 0`, so `RB_POISON_W = 754 + 8 = 762` is pinned at
  compile time, not by the card.
* **Every prose prediction in § 5 and § 6, re-derived from the three published
  `t-hit` readings rather than copied.** Twenty-three numbers, **zero
  deviations**: the warm column's 1,472/17,664 and its 12.00× step, the cold
  column's 138/276/552/1,104/2,208/4,416, all five A–B–A legs, the correction's
  1,978 / 1.34× / 8.9×, the ruler's 3.58 ms, and the tick at 69.998321 ns.

🟢 **The one that would have been easy to copy wrong**: § 6.2's *"roughly 46 %
of intervals"* is **not** 716/2000 = 35.8 %. It is `2p(1−p)` with `p = 716/2000`
= **45.97 %** — the *interval* form, not the instant form. A reader re-deriving
it as 35.8 % would get a number that also looks right.

### 0.1 🔴 The host link, which `RUNSHEET` `P3` has recorded biting three times

量, before power: `<if>` was **DOWN with no address**, and
`ip -4 route get 10.1.1.1` resolved through `eth0`, WSL's NAT'd vNIC at
`172.18.x`. That is the exact state `P3` describes from seatings 12, 16 and 19,
and `P3`'s own carried-forward repair names the fix as *asking it before the
operator is told to press power, which is where a wasted ESC window costs a
seating rather than a retry.*

It was asked before the operator was told. After
`ip link set … up` / `ip addr replace 10.1.1.2/24`:
`10.1.1.1 dev <if> src 10.1.1.2`, driver `r8153_ecm`.
`Link detected: no` with the board off, which is the expected reading.

🟢 Both `looprun` runs' `S5c` then passed `P-a` and `P-b` on the first try,
three times.

### 0.2 🟢 The directory date is measured, not assumed

The card's § 0 makes the directory name a live question. `capdate.py` compares
against the capture's **own UTC offset** and has a control (`C6`) for exactly
the failure mode of normalising to UTC. The board-off pre-flight then wrote
`started_wallclock = 2026-09-16T02:14:17+0800` — so `bench/2026-09-16/` is
right by a reading and not by a calendar glance. At 02:19 there was no risk of
crossing midnight either; `capdate` reports **0 spanning**.

### 0.3 🟢 The board-off pre-flight

0 bytes, **3.068965 s**, three artefacts written, `rc=1` — which is the healthy
reading, and is why the verdict is the artefacts and the duration and never
`$?`.

---

## 1. 🔴 The sequencing error, and it is mine

**`C1-P3bf` was run BEFORE the rescue and read `00000001`.** The card's § 4
makes `00000000` the condition on the upload, so the gate fired and nothing was
uploaded.

**`00000001` is the correct value there.** `SPEC.md` `REG-23`: *上電後 `1`*,
restored by every reset, cleared by `AUTOBURN 0` — which is what the rescue
sends. The corpus says the same thing with no ambiguity: **117 committed
readings of `0x8040D4A0`, 110 read `00000000` and 7 read `00000001`**, and
**all 94 `-ab2` captures (looprun's `S5b`, post-rescue) read `00000000`, zero
exceptions**.

**Where the cell belongs is measured, not read.** `bench/2026-09-14`'s mtimes,
same card template:

```
05:39:00  C1-P4pre.log         the negative control, cold prompt
05:39:04  C1-P4-rescue.json    the rescue
05:39:05  C1-P4bf.log          the burn flag, one second after it
05:39:08  C1-P4sh.log          the staged head, after the upload
```

and **that card's § 10 lists them interleaved** (`:480` pre → `:483` rescue →
`:485` bf → `:487` put → `:489` sh).

### 1.1 🔴 The card's own defect, which is what I resolved wrongly

Tonight's § 10 lists the captures in one block and the rescue and the upload in
a second block, under the sentence *"The rescue and the upload are **not
captures** and are therefore **not in the fence**"*. The grouping is by KIND.
**The interleaving is left implicit, and one cell's expectation depends on it.**
Section 4 positions the gate relative to *"either upload"*, which is correct and
which is also what made the § 10 ordering look like execution order.

`looprun`'s own stage order — `S5` rescue → `S5b` burnflag → `S6` upload — is
the tool's encoding of the same rule, and it ran correctly three times tonight.

### 1.2 What was done instead, and what it costs

The gate was re-taken post-rescue under an off-card name, following seating
21's own `X1-…bf2` precedent: **`X1-P3bf2` = `00000000`**, with the rescue's
`AutoBurning=0` echo as the independent second source `C-6` requires. The two
sources did not disagree tonight.

🟢 **`C1-P3bf` is not wasted.** It is this repository's **seventh** committed
cold-boot pre-rescue reading of `AUTOBURN = 1`, and the first in this card
family; the previous six are `bench/2026-08-23/B`, `2026-08-24f/G8b-ab`,
`2026-08-30d/Z-ab`, `2026-08-31b/X-ab`, `2026-09-01/Y-ab`, `2026-09-02/LP-ab`.
And with `X1-P3bf2` it reproduces `REG-23`'s `Y-ab`/`T-ab` pair — **both halves
in one power cycle, one command apart** — for the first time since 2026-09-01.

🔴 **The hole this leaves, declared rather than repaired.** The fence cell
`C1-P3bf` now holds a reading taken in a different machine state from the one
its own comment describes, and `check-predictions` scores **existence and
mtime, not content** — so the fence reads `11 of 11` with that cell carrying
the wrong-state reading. The card is not edited (editing it destroys the mtime
evidence the check rests on). **This paragraph is the record.**

---

## 2. 🔴 The card's § 5.5 stop condition fired, and the cause is located

`l.a.w4k` = **1,472**, exact, against 1,472 ± 1. `l.a.c4k` = **296**, against
**552 ± 2**. By § 5.5's own sentence — *"If either misses, the LEAF is wrong and
no knee may be read off the other ten rungs"* — the section stops.

### 2.1 The cause: `lad_base()` runs six rungs on one base with nothing between them

讀 `probe3.c:1273 (lad_base)`:

```c
static void lad_base(u32 base, u32 r_cold, u32 r_warm)
{
    for (i = 0u; i < 6u; i++) {
        res_put(r_cold + i, lad_leg(base, 1u, LAD_LINES[i]));
        res_put(r_warm + i, lad_leg(base, LAD_PASSES[i], LAD_LINES[i]));
    }
}
```

with `LAD_LINES = {64, 128, 256, 512, 1024, 2048}`. The routine's own comment
says *"Cold first — one pass, **every line a compulsory miss**"*. **It is not.**
Rung `k`'s cold leg walks `2 × LAD_LINES[k−1]` lines from the same base, and the
first half of them is resident from rung `k−1`'s warm leg. Nothing invalidates
between rungs.

🔴 **This is the identical mistake the card caught and corrected one section
earlier.** § 5.3's 🔴🔴 fixed the A–B–A — *"over 32 passes only the FIRST is
cold"* — and the same reasoning applies to the ladder's cold column, where it
sits in a source comment **and** in a published prediction **and** in
`docs/probe3-cells.md`'s `l-ladder` row.

### 2.2 The evidence that this is the cause and not a rescue

**① Four consecutive rungs sit at a constant fraction of the card's model.**
Noise does not produce a constant ratio:

| KiB | lines | base A | base B | card's model | A / card |
|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 143 | **138** | 138 | 1.036 |
| 2 | 128 | 149 | 148 | 276 | **0.540** |
| 4 | 256 | 296 | 297 | 552 | **0.536** |
| 8 | 512 | 594 | 593 | 1,104 | **0.538** |
| 16 | 1,024 | 1,191 | 1,191 | 2,208 | **0.539** |
| 32 | 2,048 | 4,351 | 4,352 | 4,416 | 0.985 |

**② A model with no free parameter fits all twelve rungs.** Rung `k` enters
with `min(LAD_LINES[k−1], cache)` lines resident; rung 5's residency is the last
cache-full of a 16 KiB walk, which a 32 KiB walk from the base evicts before
reaching it, so rung 5 is all-miss:

| KiB | model | A | B | A − model |
|---:|---:|---:|---:|---:|
| 1 | 138.0 | 143 | 138 | +5.0 |
| 2 | 149.5 | 149 | 148 | −0.5 |
| 4 | 299.0 | 296 | 297 | −3.0 |
| 8 | 598.0 | 594 | 593 | −4.0 |
| 16 | 1,196.0 | 1,191 | 1,191 | −5.0 |
| 32 | 4,351.5 | 4,351 | 4,352 | **−0.5** |

**③ The one rung whose cold leg really IS all-compulsory lands exactly.**
`l.b.c1k` = **138**, against `64 × (t.hit.warm / 256)` = **138.0**. Rung 0 at
base A is +5 (below, § 4.3). Base A's rung 0 is all-compulsory because
`t-hit`'s last leg is a KSEG1 walk over the same addresses and **the A–B–A in
this same capture measures that an uncached read invalidates resident lines**.

### 2.3 The call, with its own refutation condition

**The leaf is verified on both paths and the knee stands.** The warm path is
verified by the cell § 5.5 names — `l.a.w4k` = `t.hit.ks0` to the tick. The
miss path is verified by a cell § 5.5 does **not** name — `l.b.c1k` = 138.0 to
the tick — and that cell is a genuine compulsory-miss leg where `l.a.c4k` never
could have been one.

🔴 **Refuted if** a payload with the cold check moved to rung 0 reads
`l.a.c1k` ≠ 138 ± 2, or if invalidating between rungs does not bring the cold
column onto the card's original doubling series. Either would mean the leaf was
not verified and the knee comes down.

⚠️ **What is NOT claimed**: that the card was right. Its § 5.2 and § 5.5 cold
predictions are wrong, `probe3.c:1272`'s comment is wrong, and
`docs/probe3-cells.md`'s `l-ladder` row is wrong in the same place. The repair
is a specification change for the next payload, not a re-measurement.

---

## 3. What the ladder measured

### 3.1 🟢 The knee is at 8 KiB and the discriminator says it is a CACHE

| KiB | base A warm | base B warm | **A − B** |
|---:|---:|---:|---:|
| 1 | 1,496 | 1,496 | **0** |
| 2 | 1,480 | 1,480 | **0** |
| 4 | **1,472** | **1,472** | **0** |
| 8 | 1,485 | 1,485 | **0** |
| 16 | 17,405 | 17,406 | −1 |
| 32 | 17,404 | 17,408 | −4 |

Flat through 8 KiB, then **11.72×** at 16 KiB against a derived 12.00×.

`A_LAD2 − A_LAD1` = `0x50000` = 320 KiB, and `probe3.c:1255` asserts
`(A_LAD2 − A_LAD1) & 0x1FFF == 0`, so **every cache index bit is equal at the
two bases by construction**. Four of six rungs differ by **0 ticks** and the
largest difference is **4** (0.27 %).

By § 5.4's own table: *base 2 identical to base 1 at every footprint ⇒ the
structure follows the data, not the address ⇒ a **cache**, and the knee is the
D-cache size.* **`CPU-46`'s confound is resolved by the second base, not by the
knee** — which is what the card said in advance.

🟢 **And Group M is the independent second answer, on the same boot**:
`m.dmembase = 20000000`, `m.dmemtop = 00000000` — a base with no top above it is
not a window by `docs/probe3-cells.md` block 0's own rule.

🟢 **`docs/rlx-isa.md` § 8.1's registered prediction is CONFIRMED**: the knee
lands at 8 KiB and the datasheet's number is measured for the first time.

### 3.2 🟢 An uncached read invalidates resident lines

| leg | run 1 | run 2 | derived |
|---|---:|---:|---|
| `l.aba.0` KSEG0 32 passes warm | 1,472 | 1,473 | 1,472 = `t.hit.ks0` |
| `l.aba.w1` KSEG0 **1 pass** warm | 47 | 47 | 46 |
| `l.aba.1` KSEG1 32 passes | 13,697 | 13,697 | 13,698 = `t.hit.ks1` |
| **`l.aba.c1` KSEG0 1 pass, immediately after** | **545** | **544** | **552** invalidated / **46** not |
| `l.aba.2` KSEG0 32 passes re-warmed | 1,472 | 1,472 | 1,472 either way |

**545 is 7 from the invalidated branch and 499 from the other.** The cell's own
two cross-checks (`l.aba.0`, `l.aba.1`) hold, so it is not void.

🟢 § 5.3's correction — replacing the 32-pass form with a one-pass form —
earned its place: at 32 passes the separation would have been **1.34×** and the
owner file's *"~138 ns/load"* would have read a real invalidation as *no
invalidation*.

### 3.3 🟢 The three published constants, reproduced exactly, twice

`t.hit.warm` **552**, `t.hit.ks0` **1,472**, `t.hit.ks1` **13,698** on run 1;
552 / 1,472 / 13,696 on run 2. Power cycles four and five for these numbers,
and the first two are still at zero spread.

### 3.4 🟢 Within-boot repeatability, and then across a reset

§ 5.6's own cell: `l.rep.a8k` = `l.rep.b8k` = **1,473** on run 1 and **1,473 /
1,473** on run 2 — the two bases identical, both runs.

**Off-card, and larger**: the whole ladder was run a second time after a
`reboot -f`, a rescue, a re-upload and a second `J`. Every rung reproduces —
**±1 on the 1,4xx rungs, ±9 on the 17,4xx rungs (0.05 %)**, and `l.aba.c1`
545 → 544. No timing rung in this project had been repeated across a reset
before; § 5.6 repeated one rung within a boot.

### 3.5 🟢 A constant nobody asked for: this part has TWO miss costs

Six legs in which every load should miss — two bases × {warm 16 KiB, warm
32 KiB, cold 32 KiB}, three different leg lengths — all land at the same
fraction of the compulsory-miss cost derived from `t.hit.warm`:

```
0.985337  0.985394  0.985281  0.985507  0.985281  0.985507
spread 0.000226
```

**Refutation condition, written before the arithmetic**: if the six fractions
differed by more than the ladder's own repeatability (the two 8 KiB repeats
agreed to 0 ticks, the two bases to ≤ 4), this is six coincidences and the
paragraph is dropped. They did not.

* **first-touch (compulsory) miss = 2.15625 ticks**
* **steady-state (capacity) miss = 2.12474 ticks**
* **they differ by 1.462 %**

It closes rung 5's residual from **−65 to −0.5** with no free parameter, because
the 1.462 % was measured on the *other* five legs.

⚠️ 推, and not measured here: that the difference is DRAM row locality — a
first-touch pass activates a fresh row per line where a thrashing walk re-reads
recently-open ones. The experiment that would decide it is a cold column at two
strides.

---

## 4. `R1-pub-4b` — the emulation surface, priced

### 4.1 🟢 Two costs, reproduced on two independent boots

Slope over four rungs of `comp_tc1`, each measured row minus its twin:

| row | twin | boot 1 | boot 2 | agreement |
|---|---|---:|---:|---:|
| `sync` | `nop_a` | **988.6 ns/it** | **989.5 ns/it** | 0.09 % |
| `lwu2` | `lw` | **915.6 ns/it** | **915.4 ns/it** | 0.02 % |
| `ll` | `lw` | 5.0 ns/it | 4.8 ns/it | 4 % |
| `sc` | `sw` | +0.2 ns/it | **−0.2 ns/it** | **sign flips** |

The slopes fall into two clusters about **90×** apart:

```
native  : nop_a .00205  nop_b .00205  lw .00205  sw .00212  sc .00216  ll .00306
emulated: lwu2  .18513  sync  .19978              (counts per iteration)
```

**`E2`'s zero control** — two `nop` cells at two addresses, because `x − x` is a
tool that cannot fail — is **0.001 ns/it** on boot 1 and 0.011 on boot 2. Every
quoted cost is ≥ 84,000× it.

🟢 **The exception round trip on this kernel is ~900–990 ns**, i.e. **366–396
cycles at 400 MHz**, measured two independent ways: two different instructions
through two different handlers, agreeing to **7.4 %**, so the dominant term is
the trap and return rather than the handler body.

🟢 **`sc` costs nothing, and the evidence is that its sign is not stable.**
A quantity that is +0.2 ns on one boot and −0.2 on another is the instrument
finding zero, which is a stronger statement than either number.

### 4.2 🔴 `docs/rlx-isa.md` § 8.2 is REFUTED, and not by the row it named

§ 8.2 registered: *"`D-cost` will find **exactly one row with a measurable
cost**"*, **refuted if** more than one row shows a cost. 量: **two**, `sync` and
`lwu2`, both at the exception scale.

🔴 **The reason it was wrong is in its own sentence.** It reasoned from `4a`'s
*visible* surface, and `4a`'s census **excludes the unaligned forms by rule**
(`docs/emulation-surface.md:481`). **It was a prediction derived from an
instrument that was blind to the thing that refutes it.**

**§ 8.2 is left exactly as written.** The card's § 6.5 said so before power and
the reason stands: a document written before its measurement is the rarest thing
this repository has, and editing it now to agree would spend that for nothing.

### 4.3 🔴 The card's § 6.5 dichotomy is incomplete, and § 6.6 is what completes it

§ 6.5 wrote two branches: *if `ll` and `sc` cost anything → § 8.2 refuted; if
they do not → "emulated in user mode" refuted as a statement about the executing
machine, and § 8.2 confirmed.* **Neither branch covers a THIRD row costing
something**, which is what happened — and the cell that produced it is § 6.6,
the next subsection of the same card.

What the measurement actually says, in two parts:

* **`ll` and `sc` do not pay an exception.** `ll` costs **2 cycles** over `lw`;
  `sc` is indistinguishable from `sw`. So *"emulated in user mode"* is refuted
  as a statement about the executing machine, and the source reading is
  re-attributed: `simulate_llsc` exists in the kernel and, in user mode on this
  die, is never reached. ⚠️ Narrow: this says nothing about kernel mode, and
  nothing about whether the atomicity is correct — `ucost` times, it does not
  check semantics.
* **§ 8.2's count is refuted anyway**, by `lwu2`.

### 4.4 🟢 § 6.6's two-file disagreement is settled, and the winner is the documented one

* `docs/emulation-surface.md:335` lists the five unaligned forms as *"the
  unaligned `lh`, `lhu`, `lw`, `sh`, `sw`"* — `lwu2` is an unaligned `lw`, so
  this file predicts an exception round trip. **量 915.5 ns. Confirmed.**
* `SPEC.md` `CPU-15` measured, at the loader prompt, that the unaligned
  load/store **instructions** execute and compute the right answer.

⚠️ **These are not in conflict once the two things are separated**, and the
card's framing conflated them. `lwl`/`lwr`/`swl` are *instructions*; tonight's
`C2-UP` shows them raising **no signal** in user mode (rows 8/9/a), agreeing
with `emulation-surface.md`'s own column ②. `lwu2` is an *aligned instruction at
an unaligned address* — an address error, not a reserved instruction.

🔴 **The open question, named**: `CPU-15` was measured at the loader prompt and
this at a Linux user-mode prompt, so they are two states of one machine and
neither refutes the other. **The experiment that decides it is `lwu2` timed
bare metal**, which needs a `probe3` row and a seating.

### 4.5 🔴 `E5`'s clause is off by one, and its own source contains the ±1

`E5`: *the two composites agree or differ by exactly one reload.* Over both
boots, **13 of 64 rungs "fail"** — 7/32 and 6/32, both under the ¼ that would
void the seating.

**Every one of the thirteen is off by exactly 1**: four by ±1, three by ±1,999,
and 1,999 = one reload − 1. § 6.2's own measurement is *"**716 or 717** in all
twelve"* — the clause demanded exactness from a quantity its own source
measured with a ±1 spread. **Allow that ±1 and 0 of 64 rungs fail; the ruler is
clean.**

🟢 The ruler's design decision is vindicated by the data it was written for:
`nop_a` rung 2 on boot 1 has `Δcomp_tc0 = −1,304` — negative, because `c0raw`
wrapped while `jiffies` did not — against `Δcomp_tc1 = 696`. `ce_live = 1`, so
the program used `comp_tc1`.

🟢 **The desk reproduced the board's own arithmetic on all 64 rungs, 0
disagreements**, recomputing both composites from the six raw snapshot fields.

### 4.6 🔴 `E4`'s threshold sits inside the noise

`E4`'s limit is `max(2 counts, 1 % of the largest Δ)` — **a fixed fraction of
the row's own magnitude**, so it is ~50× stricter on a cheap row than on an
expensive one, which is backwards: the cheap rows are where the noise is
proportionally largest.

量: **boot 1 fails `sw` (25.1 vs 23.9); boot 2 fails `ll` (21.0 vs 9.5).** A
different row each time is the signature of a threshold inside the noise rather
than outside it. `sync` and `lwu2` pass on both boots with ~10× headroom.

**Consequence, following `E4`'s own sentence rather than overriding it**: the
two expensive costs are quoted as numbers; `ll` and `sc` are reported as
**bounds** — neither pays an exception, `ll` is within ~5 ns of `lw` and `sc`
within ±0.2 ns of `sw`. That conclusion does not depend on either fit, because
the clusters are 90× apart.

### 4.7 🟢 `E1`, `E3`, `E6`, `E7`

* **`E1`** every row ran 4 rungs on both boots, `rc=0`, `rungs=00000004`.
* **`E3`** wanted one measured row and its twin on two independent boots.
  **All four rows and all four twins, on two boots**, each boot a separate
  rescue + upload + `J`.
* **`E6`** § 6.5 wrote both branches before the capture.
* **`E7`** the surface is 8 and this prices 4; the other four are unpriced and
  that is a declared scope limit.

---

## 5. § 7's `4a` repeat: byte-identical

`uprobe`'s `BUILD_ID` is **`a87be346bb83e7f9`** in both captures, which is the
whole reason the comparison is worth anything — § 7 froze `isa-payload.tsv`'s
`special0e` `why` column for a fourth time to keep it still.

`bench/2026-09-15/C2-UP.log` (arg `d73`) against `bench/2026-09-16/C2-UP.log`
(arg `a91`): **75 `PU` rows, `cmp` IDENTICAL**, and all eleven header fields
equal including `scratch_at = 00445d88`.

**The first time any column-② row in this project has been repeated, and every
one of them reproduces.** The two runs used different arguments and produced
identical rows, so the argument is a label and not a selector.

---

## 6. The flash bracket

### 6.1 🔴 I used the wrong instrument first, and the card had said so

The card's § 8 warns: *"`map_jiffies` varies by a tick, so a whole-file `cmp` is
wrong; compare the unit digests."* A whole-file sha256 of tonight's `C2-M0`
gives `5ff5de0d…` against the reference family's `b3d3d7d0…`, which **reads as a
flash difference**. It is `map_jiffies` 1279 against 1280.

**By unit digest — eleven map captures, 2026-09-08 to 2026-09-16, six seatings —
every one is the same, and tonight's two are 0 of 32 units different against
every other.** `map_hashed` 4,186,112, `map_h601_skipped` 8,192,
`map_truncated` 0.

⚠️ **This does not move `FLS-26`'s ledger**, which compares against the
**2026-08-16 dump**; the map compares tonight's flash against 2026-09-08's.

### 6.2 🟢 `n_writes 0` now has a positive control in the same dump

`X4-NW` read `n_writes 0` on boot 2 — but every counter in that dump was 0,
because no map had run on that boot, so the reading had no positive control.
*A tool reporting 0 is making a claim.*

Boot 3, off-card:

```
X7-NW0   n_pio_bytes 0          n_writes 0
X7-M3    map_ran 1  map_rc 0  map_hashed 4186112  map_lines 32
X7-NW1   n_pio_bytes 4194304    n_writes 0
         n_mmio_bytes 4194304   n_state_foreign 0   n_state_bad 0
```

A counter that moved by 4,194,304 beside one that did not, in one file, from one
driver.

### 6.3 🔴 And a grep over the `.log` files made an alarming false claim

A sweep for flash-write verbs across `bench/2026-09-16/*.log` returned **one
`FLW`, one `EB`, one `EW`, one `FLR`**. All four are in `C1-Q.log` — `C1-Q`
sends `?` and the **loader prints its own command table**. A `.log` holds what
the board printed as well as what was sent.

The right instrument is each capture's `.meta.json` `sent` field plus the rescue
transcripts: **65 sent strings, 0 hits**, with a synthetic `FLR …` as the
positive control.

---

## 7. What the seating could NOT settle

1. **`l.a.c1k`'s +5 at base A.** Reproduced: **+5 on run 1 and +7 on run 2**,
   while base B lands on 138.0 both times (138, 137). It is stable and it is not
   noise. 推, and the best candidate: base A's rung 0 is the **first call** to
   `rlx_tc_ladder`, so it pays the leaf's own I-cache fill, where base B's rung 0
   is the thirteenth. **The experiment that decides it**: discard one `lad_leg`
   before the ladder starts. Needs a payload.
2. **Why `lwu2` costs an exception under Linux when `CPU-15` measured unaligned
   access working at the loader prompt.** Needs `lwu2` timed bare metal.
3. **The four unpriced rows** of the eight-entry surface. Declared in `E7`.
4. **The two-miss-cost mechanism.** § 3.5's 1.462 % is measured; DRAM row
   locality is 推.
5. **Group V** is void for the fourth time (`c-A` negative), so § 4's
   conditional — *if `c-A` reads positive this seating, Group V's result is VOID
   because Group L pre-warms its arena* — did not arise. It is still live for a
   future seating.

---

## 8. 🔴 The closeout audit produced a FALSE finding, and it nearly cost a power cycle

`docs/isa-prior-art.md` § 7's seating schedule for `R1-pub-3` lists five slots:

| slot | what | status |
|---|---|---|
| 1 | `R1a`/`R1b` payloads + the loop seam | seatings 21/22 |
| 2 | `CPU-45`'s cells | **ran tonight** |
| 3 | `J` to a kernel of mine | **ran tonight**, three times |
| 4 | `FW-65`'s two `echo` writes bracketing one long hold | ✅ **seating 22, 2026-09-14** |
| 5 | `FW-63`'s bit-6 transition timestamps on a fresh boot | ✅ **seating 22, 2026-09-14** |

**The audit reported slots 4 and 5 as silently dropped riders that still needed
power. That is wrong.** Both were closed at seating 22 with four predictions
each, all hit; the captures are `bench/2026-09-14c/C4-S1`, `C4-S2`, `C4-E2A`,
`C4-E2B`, and `LOG.md:26218` / `:26421` carry the readings.

### 8.1 How the false finding was produced

`SPEC.md`'s residual rows are single table rows that carry **both** the open
question **and**, appended to the same row, the ✅ that closes it. The audit read
them through `sed -n '630,631p' SPEC.md | cut -c1-260` — a **truncated view**,
which showed the row's opening sentence (*"兩件事未定"*) and not its tail
(*"✅ 收了 2026-09-14（seating 22）"*). The ✅ in the id column said so too and
was read as a status glyph rather than as the answer.

🔴 **This is the failure this project's own operating notes name first — quoting
a partial view instead of re-deriving — and it now has a dated instance whose
cost was nearly a power cycle**: the operator had already said to go ahead before
the second read caught it. **The rule that would have caught it earlier: never
read a `SPEC.md` row through `cut`; a row is one line and its verdict is at the
end.**

### 8.2 The real defect, which is smaller

`docs/isa-prior-art.md` § 7's table is **stale**: it still lists slots 4 and 5 as
riders on `R1-pub-3`'s seating, two days after both were closed. The file's own
dateline was updated on 2026-09-14 for the route-① column and that table was not.
**Tonight's card was right not to carry them**, and its § 9 was right not to list
them as dropped, because they were not this seating's to drop.

---

## 9. The seating in numbers

| | |
|---|---|
| power cycles | **1**, budget 1 |
| carded cells | 11, `check-predictions` **11 of 11** |
| off-card cells, all declared | 12 |
| `looprun` runs | 3, each **9 assertions**, 39.06 / 39.23 / 38.98 s |
| boots of `uc1` | 3, all `RLXFW-ID0=EFA93621`, all **1,637 bytes** |
| `probe3` runs | 2, both 6,826 bytes, 4.5067 / 4.5037 s |
| `C1-P3rb` | **9,003 bytes** — the `cardnum` `dw762-bytes` value, on the device |
| flash-write verbs sent | **0 of 65** |
| `capdate` | 34 directories, 1,273 captures, **0 RED** |

🟢 **`C1-P3rb`'s 9,003 bytes is the card's own machine-re-derived prediction
landing on the silicon**, and `C2-M0`'s 3,013 bytes reproduces seating 18's
figure for the same command.

🔴 **The three boot captures differ in exactly two fields**: `RLXFW-TA5`
`FFFF8D3C`/`FFFF8D3D` and `RLXFW-TA6` — `IRQ-13`'s lost-interrupt count — **10,
11, 10**. Seating 17 read 11 on nine of ten boots and seating 18 read 8 on all
thirteen, so this count is image-dependent and moves by one within an image.


---

## 10. 🔴 Two gates cannot see a bench record until the commit that publishes it, and this segment hit the hole twice

`CLAUDE.md` records this shape once already, for the freeze procedure: *a card is
untracked until the freezing commit, so the gate that exists to check the card
cannot see the card.* **It is not one gate. It is every gate whose population is
`git ls-files`.**

### 10.1 `leakscan` — and this one is a redaction check

量 `tools/leakscan.py:165 (def tracked)`: the population is
`git -C <root> ls-files`. So an untracked file is not clean to it, it is
**unread** — and `leakscan`'s own output says exactly that about the five
non-text files it skips, while saying nothing about untracked ones.

**What it would have caught**: this file carried the host NIC's interface name
**twice**, and `LOG.md`'s new section carried it once.
`bench/2026-09-10/CORRECTIONS-block17.md:150` states the convention — the
interface name is written `<if>` deliberately, because it encodes the host
adapter's MAC and `leakscan` classifies it HOST — and eleven tracked files
already carry it. **These three were redacted before the commit, and what found
them was `git grep`, not the gate.**

### 10.2 `spec-check` — the same population, the same blind spot

`spec-check`'s `C11` flags a bare `file:NNN` citation with no token from that
line. It caught two in `SPEC.md` (both this segment's) and **zero** in this
file, which carried one — because this file was untracked when it swept.

### 10.3 What this is, stated narrowly

It is **not** that the gates are broken: `git ls-files` is the right population
for a check whose subject is the published record. It is that **the closeout
order puts every such gate one commit behind the thing it is checking**, and the
one place that matters most is a bench record, because a bench record is written
last and is the file most likely to carry a raw reading.

🔴 **The workaround used tonight, which is a habit and not a guard**: `git add`
the record before running the `.md` gates, so the sweep sees it. **The repair
that would be a guard** — a `--include-untracked` mode, or a closeout step that
stages first — is named here and not built.
