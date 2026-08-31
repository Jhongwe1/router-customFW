# CORRECTIONS — block 4, `bench/2026-08-31c/`

**Opened 2026-08-31 20:07, during the seating, because the card froze the
moment `K-A.log` landed.** Everything here is a correction to, or a deviation
from, `PREDICTIONS-B6-block4.md`, which is not edited again.

---

## §1 The card's own date prediction was refuted, and the directory was renamed before power

The card was written on 2026-08-31 into `bench/2026-09-01/` — **a prediction of
the seating day**. 量 2026-08-31 19:31, `date` on the Windows host and in the
distro: the seating is the **same evening the card was written**.

The card names the slip direction only (*"if this one slips"*); what happened is
the opposite. The rule it states does not move — *a `bench/` directory carries
the day its captures were taken* — so, **before power and before the first
capture landed**:

* `bench/2026-09-01/` → **`bench/2026-08-31c/`** (`git mv`, 40 occurrences)
* `…/bench-only/b6-20260901` → **`b6-20260831c`** (6 occurrences)
* the bare `` `2026-09-01` `` on the card's own prediction line was **kept** —
  it is what was predicted, and a record edited to match today stops being one.

`check-predictions` read `0 of 25` after the edit, which is what says the edit
landed before a capture rather than after one.

⚠️ `LOG.md:10542` (2026-08-31, eighteenth session) says *"`bench/2026-09-01/` is
deliberately kept"*. That sentence was true when written and is left in place.

## §2 🔴 The card named a file to upload that did not exist

`K-1` uploads `…/b6-20260901/probe3.bin`. 量 19:33: **that directory was
empty.** It was created at 18:14 and `probe3` was rebuilt at 18:47; nothing ever
copied the binary in.

**The card's four before-power checks all read the artefact the *build*
produced. None of them read the file `K-1` names.** It would have failed after
`K-A` … `K-P3`, with the board powered.

Fixed before power, and fixed at the hole rather than at this instance: the
binary was staged, a **fifth before-power command** was added, and a
`probe3.staged.sha256` row went into § 9's fence — so `cardcheck numbers`
re-derives it. **13 of 13 → 14 of 14.**

## §3 Deviations from the card's § 0, all before power

| | |
|---|---|
| **`console-dump.py` and `loader-tftp.py` are not in `tools/`** | they are in **`upstream/tools/`**, the pinned submodule. Every other command on the card carries an explicit `tools/` prefix; these two are bare. 量: `tools/console-dump.py` does not exist and the run failed with `FileNotFoundError`. Block 0's card writes `/usr/bin/python3 upstream/tools/console-dump.py` in full — **block 4 lost the prefix in the copy**. `upstream/` was not modified (`git status` clean, both levels) |
| **§10b rebuild-on-the-day was run** | `rm -rf build/probe3`, `make … payload`, `make show`. It **compiled** (not `Nothing to be done`), and reproduced `fc7b21d4…` / 31,536 **byte-identically** (`cmp` against a copy taken before the `rm -rf`). ⚠️ `make` printed `Clock skew detected. Your build may be incomplete.` — a DrvFs mtime artefact; the byte-identical sha over an emptied build directory is its control |
| **the `flrbracket` dry run was RE-RUN** against the renamed paths rather than argued to transfer. Four windows, `rc=0` each | containment re-confirmed for the exact strings that were then used |
| **two extra cells, `K-guard600` / `K-guard700`** | see § 4 |

## §4 🔴 `K-P3` spans two `H601` destinations, and its output lands inside the repository

`K-P3` is `DW 80A00000 2000`, covering `0x80A00000`–`0x80A01F3F`, which
**contains `0x80A00600` and `0x80A00700`** — the destinations `K-flrh` and
`K-flrc` fill with `H601` content. `MEM-17` is *DRAM keeps a previous cycle's
`FLR` output across a power cycle*, and seating 7 wrote those two addresses.

**`K-P3` writes to `bench/`.** Had DRAM retained, this unit's MAC would have
entered the repository — the 2026-08-31 incident in a third shape. `flrbracket`
refuses it; a bare `DW` on the card does not, and **`flashwin` governs printing,
not where a capture lands**.

Two extra cells were run first, **outside the repository**:
`K-guard600` / `K-guard700`, `DW` of both destinations, compared to the
expectation by count only. **0 of 64 words matched at each.** Not retained, so
`K-P3` was safe and was run as carded.

🔴 **The card is not what made that safe. The experiment coming out the expected
way is.** That is the containment defect the carried-forward row already names,
and it is still in the template.

## §5 🔴 `K-J` dropped `--esc-after`, and that is a regression from block 0

Card: `CAP OUT K-J --send 'J 80500000' --seconds 90`, expecting *"`rlxprobe:
end` and the loader prompt back (`RESET=1` arms the watchdog and hands it back
with no power cycle)"*.

Block 0's `Q-J` (2026-08-29), the only previous run of this payload:

```
CAP --out …/QJ --send 'J 80500000' --esc-after 60 --esc-period 0.002 --seconds 120
   -> "then a reboot into the ESC storm and a prompt"
```

**`--esc-after` is the mechanism that hands the prompt back.** The watchdog
resets the SoC; the loader then **auto-boots** unless something is streaming
ESC. Block 4 kept the consequence and dropped the mechanism — block 4 was
written by copying block 3, a kernel-boot card, where ESC after `J` is exactly
what must *not* be sent.

量: `K-J` ran to `rlxprobe: end` (135 lines, 8,002 bytes) and was followed by a
full vendor-firmware boot — `wan_disconnect: StartDnsSpoof`, `MiniIGD v1.09.1`,
`boa: starting server pid=350`. **`K-rb` and `K-rbp` could not run**, and the
retained bitmap's pattern — § 7.2's whole prediction — exists only in the
read-back.

**Consequence: `K-rb` and `K-rbp` did not run on power cycle 8 and are FAILs in
`check-predictions`.** They were taken on power cycle 9 as `K2-rb` / `K2-rbp`.
A cycle-9 capture may not carry the `K-` prefix; `K2-` follows block 3d's `X2-`.

## §6 Power cycle 9, and it was spent to recover § 5

**Not on the card.** Off ≈ 20:00, on 20:01:16 (first byte 5.685 s into
`K2-A`, capture started 20:01:10.651). Off duration ≈ **1–2 minutes**.

`DW 80A02000 16` came back **`524C5833`** — probe3's own magic — with the nonce,
`pc`, `flags`, `rb`, `install.changed` and `break.epc` all matching what the
UART printed on cycle 8.

🟢 **`MEM-17`, and it is a much stronger reading than the one that opened the
row.** The block survived, in one power-up, **all three** of: a watchdog reset,
a complete vendor-firmware Linux boot that then ran for ~2 minutes, and a power
cycle. ⚠️ And the same cycle shows the *other* direction: `0x80500000` no longer
holds `probe3` — the loader re-staged the vendor image over it during the
auto-boot, and **that** is what DRAM retained there.

🔴 **The 17.6-hour arm, which is the first upper bound this row has ever had.**
Power off ≈ 2026-08-31 02:00 (owner's reading), power on 19:43:07 (first byte
3.282 s into `K-A`, started 19:43:03.922) — **≈ **63,787 s = 17.72 h****.
`K-guard600` / `K-guard700`: **0 of 64** words retained at each. So:

> **retention ≥ one power cycle of ~1–2 min with a vendor boot inside it, and
> < 17.72 h.** Neither end was bounded before today.

## §7 🔴 The read-back's three channels do not all agree, and the experiment that separates the causes is written HERE, before it runs

`rbcheck bench/2026-08-31c/K2-rb.log --base 0x80A02000 --words 718 --uart
bench/2026-08-31c/K-J.log`: **33 controls pass**, and the block reports

```
UART sum   (1)  05D7AC1A
seal w717  (2)  05D7AC1A     <- (1) and (2) agree
corrected  (3)  05D8AC1A     <- +0x00010000 = 2^16 exactly
```

Established already, and neither needs the board:

* **`K2-rb` and `K2-rbp` agree word for word** — 720 addresses in both, **0
  differ**. The read-back is stable; this is not a capture artefact.
* 208 of the 717 summed words have bit 16 set, so the arithmetic alone cannot
  name which word it is.
* Four UART values occur nowhere in the block: `w.line0.fresh=0000000D`,
  `w.line.fresh=0000000B`, `s.bits=01010040`, `rb.words=000002CE`.

**Three hypotheses, and only one of them is about DRAM:**

| | |
|---|---|
| **H1 — a retained-DRAM bit changed** | the block was sealed correctly on cycle 8 and one bit went 0→1 while it sat through the reset, the vendor boot and the power cycle |
| **H2 — a word is written AFTER the seal is computed** | a payload defect, not a memory one. rbcheck already knows of exactly one such re-stamp (word 2, `P_RESTORED` → `P_SEALED`, the `−0x10`); a second one would look exactly like this |
| **H3 — `rbcheck`'s channel (3) is wrong for a 718-word block** | `C16`'s real fixture is a 641-word block; `C24`'s 718-word block is synthetic |

> ### 🔴 PREDICTED, written 2026-08-31 20:09, before the re-run
>
> **The payload is re-uploaded and re-run on the SAME power-up** (rescue → put →
> `J … --esc-after 60 --seconds 120`), producing a block sealed minutes ago
> rather than one that sat through a boot. Then `DW 80A02000 718` → `K2b-rb`.
>
> **PREDICTED under H1: the fresh block's three channels AGREE**
> (corrected re-sum == seal == UART sum), and comparing `K2b-rb` against
> `K2-rb` word for word, the **deterministic** words are identical except
> **exactly one, differing by `0x00010000`**. That word is then named, and H1
> is the reading.
>
> **REFUTATION — H2/H3: the fresh block shows the SAME `corrected − seal =
> +0x00010000`.** Then nothing about DRAM follows, the defect is in the payload
> or in `rbcheck`, and this section is a finding about my own instruments. **The
> `+0x10000` being reproducible on a block that never left the prompt is what
> would prove it.**
>
> **A third outcome that refutes both readings of the comparison: MANY
> non-timing words differ between the two blocks.** Then the retained block was
> more damaged than its checksum suggests — a sum catches the net, not the
> count — and neither `K2-rb` nor the pairing analysis on it is entitled to be
> quoted.
>
> ⚠️ **What the re-run costs and what it destroys:** it overwrites the retained
> block at `0x80A02000`. That is acceptable **only because `K2-rb` and
> `K2-rbp` are already on disk and byte-identical to each other** — the
> evidence is captured twice before it is overwritten once.
>
> ⚠️ **`f.win.*` is expected to REPLICATE**, not to be a new reading:
> `f.sfcr = 3fc00000`, `f.win.seq ≈ f.win.str ≈ 30,354`, `R ≈ 1.00`. A second
> run that disagrees with the first by more than the § 6.8.3 condition-4
> tolerance (10 %) refutes the instrument, not the window.

## §8 A second bracket, added on cycle 9, because the first one is on the wrong side of a vendor boot

🔴 **Cycle 8's bracket ran before `K-J`.** Its four windows were therefore
verified **before** the watchdog reset auto-booted the vendor firmware, which
then ran for ~2 minutes with `boa`, `MiniIGD` and `wan_disconnect:
StartDnsSpoof` on the console. **Nothing in this project has ever read flash
with a specific, observed vendor-firmware run bracketed on both sides.**

The loader is at the prompt on cycle 9 and no further `put` is needed, so
§ 5.3's ordering rule is satisfied and this costs **no power cycle**.

**Fresh RAM destinations, `0x80A00C00`–`0x80A00F00`.** Cycle 8's destinations
(`0x80A00400`–`0x80A00700`) hold cycle 8's own `FLR` output, and `MEM-17` — as
this seating has now measured twice — says DRAM keeps it. Reusing them is what
voided cycle 6's round. All four are below `0x80A02000`, so the result block
that § 7 depends on is not touched.

> ### 🔴 PREDICTED, written 2026-08-31 20:15, before the second bracket runs
>
> **PREDICTED: all four windows come back byte-identical to the same
> expectations cycle 8 matched** — `bench/2026-08-24d/G8a-rd0.log`,
> `G8a-rd6.log`, `expect-h601-6000.txt`, `expect-h601-6400.txt`. The vendor
> firmware's boot and its ~2 minutes of running wrote **none** of these 1,024
> bytes.
>
> **PREDICTED: all four pre-reads DIFFER from the expectation.** They are fresh
> addresses nobody has written this power-up, so they are uninitialised DRAM.
>
> **REFUTATION, and it is the interesting one:** any window differing from
> cycle 8's reading is a flash write by the vendor firmware, localised to
> within one power-up and one observed boot. 🔴 **For `0x006400` that is the
> canary page `FLS-21` measured moving**, and a difference there would be the
> first time this project has caught that page moving with the writer named.
>
> **REFUTATION of the round rather than of the finding:** any pre-read that
> matches the expectation means DRAM retention reached these addresses too, and
> that round is VOID — `MEM-17`, cycle 6's lesson, applied in advance.
>
> ⚠️ **What it still cannot say:** 1,024 of 4,194,304 bytes = 0.0244 %. It
> cannot see a write outside the four windows, and `RUNSHEET` `G8b` still
> forbids *"not one flash byte is written"* without a full re-dump. **This
> seating runs none, and the vendor firmware ran on it.**

---

# THE RESULTS

## §9 § 7's experiment ran, and it refuted two of its three hypotheses

`K2-0rescue` → `K2-1` (31,536 bytes, 62 blocks) → `K2-2b` (head identical to
`K-2b`) → `K2-J` with `--esc-after 60 --seconds 120` → `K2b-rb`.

🟢 **`--esc-after` is the mechanism, confirmed directly.** `K2-J` is 39,183
bytes, 135 `rlxprobe:` lines, `rlxprobe: end`, **zero** vendor-boot strings, and
the log ends at `<RealTek>`. § 5's diagnosis is a measurement now, not a
reading of block 0's card.

🟢 **The fresh block agrees on three channels.** `seal = corrected re-sum =
UART sum = 055B8159`, `rbcheck` exit 0.

> **H2 (a word written after the seal) and H3 (`rbcheck`'s channel (3) wrong
> for a 718-word block) are REFUTED.** Both predict the same `+0x10000` on a
> block that never left the prompt, and it is not there.

🔴 **H1 stands, and the word is named.** `K2-rb` against `K2b-rb`, word for
word: **18 of 718 differ**, and every one but three carries a UART name whose
value changed between the two runs (`t.live`, `t.sep.a/b`, `t.hit.warm`,
`t.hit.ks0`, `t.ovh.1`, `f.boot.*`, `f.dram.seq`, `f.win.seq2`,
`install.changed`, `sum`). Of the three that do not, `w102` and `w103` differ
by **+1,017,152** against `t.sep.a`/`t.sep.b`'s **+1,017,184** — the same
counter base, so they are timing words with no UART name. That leaves one:

| | |
|---|---|
| `w126` at `0x80A021F8` | retained `00010400`, fresh `00000400`, **xor `00010000` — one bit, bit 16** |
| retained block | corrected re-sum − seal = `00010000` |
| fresh block | corrected re-sum − seal = `00000000` |

🔴 **And the word has a name.** `w126` is block index 126; the header is 64
words, so it is **result index 62 = `R_W_SIZE + 10`** — point 5 of the `w-size`
sweep (`W_KIB` = 32 KiB), field `n_fresh`. The UART row agrees:
`w.size 00000020 n=00000400 fresh=00000400 other=00000000`, so the true value
is 1,024 and the point is **saturated** — every victim FRESH. Naming it matters
because a reader has to be able to ask *could this word legitimately differ
between two runs*, and this one cannot: it is a geometry result, and both runs
produced `00000400`.

**The argument closes**: the UART sum equals the seal, so the payload's
arithmetic matched its own memory at seal time; the read-back's re-sum exceeds
the seal by exactly `0x10000`; exactly one non-timing word exceeds its fresh
counterpart by exactly `0x10000`. **The bit went 0 → 1 after the block was
sealed.**

⚠️ **Ruled out, and by measurement rather than by argument**: it is not a
capture artefact — `K2-rb` and `K2-rbp` agree over **720 addresses, 0 differ**;
and it is not a stuck-at-1 cell — the same address reads `00000400` in
`K2b-rb`, `K2b-rbp`, `K3-rb` and `K3-rb2`.

🔴 **What the seal did, and it is the first time.** This is the first occasion
in this project on which the block's own checksum has caught anything. **A sum
catches the NET**: two flips that cancel would be invisible to it, and only the
word-for-word comparison against a second block bounds that — and only over the
~700 words that are not timing readings.

## §10 § 8's second bracket ran, and every prediction held

| | |
|---|---|
| `K2-rd0` / `K2-rd6` / `K2-rdh` / `K2-rdc` **vs the 2026-08-16 dump's expectations** | **64/64 each** |
| the same four **vs cycle 8's own readings** | **64/64 each** — this is the tight bracket |
| `K2-p0` / `K2-p6` / `K2-ph` / `K2-pc` vs their own read-backs | **0/64 each** — the `FLR` demonstrably wrote |

🟢 **A watchdog reset, a full vendor-firmware boot and ~2 minutes of that
firmware running changed none of those 1,024 bytes**, with both readings taken
on one seating and the run between them observed on the console. The canary
page `0x006400` did not move.

⚠️ 0.0244 % of the part. It cannot see a write outside the four windows.

## §11 Power cycle 10, and the retention is BIT-EXACT when no vendor firmware runs

Off **not recorded** (see § 13), on **20:23:50.0** (`K3-A` started
20:23:47.700, first byte 2.288 s in). `DW 80A02000 718` → `K3-rb`, and again →
`K3-rb2`.

```
K3-rb vs K3-rb2 (two reads, one power-up)  :  0 of 718 words differ
K2b-rb vs K3-rb (across the power cycle)   :  0 of 718 words differ
bits compared 718 x 32 = 22,976            :  0 changed   BIT-EXACT
```

`rbcheck` on `K3-rb`: three channels agree, exit 0.

| interval | what is inside it | flipped bits |
|---|---|---:|
| seal on cycle 8 → read on cycle 9 | watchdog reset, **a full vendor-firmware boot and ~2 min of it running**, a power cycle | **1** |
| seal on cycle 9 → read on cycle 10 | watchdog reset, ESC caught at the prompt, a power cycle | **0** of 22,976 |

🔴 **n = 1 on each side, and the off durations are NOT controlled** — see § 13.
The vendor-firmware run is the element unique to the flipping interval, but
duration is not excluded, because neither duration was written down.

⚠️ **推, and labelled — 🔴 and RETRACTED 90 minutes later by § 16.** It read:
*a single-bit 0 → 1 is a poor fit for the firmware wrote there … it fits a
marginal cell losing charge during the power-off, and DRAM retention is
strongly temperature-dependent: the flipping interval is the one where the die
had just run Linux for two minutes.* **Power cycle 11 measured the duration
term and it is enormous**, so one bit at ~2 minutes needs no thermal
explanation at all. The sentence is kept because it was written before the
measurement that killed it.

## §12 The two instruments `R3-9` carried forward both landed, and they are two independent routes

**① The `M(T)` ladder.** `w.assoc.mt = **09 05 03 03**`. Direct-mapped predicts
`09 05 03 02`; **the one byte that carries the whole difference came back
`03`**. `w.assoc.mtcap = 00000000` as predicted, `w.assoc.tm = 00002003` =
(8192, 3) and `w.assoc.capped = 00000000`, both agreeing with 量 2026-08-29.

**② The retained bitmap's pattern.** 20 FRESH, 492 STALE, **0 other** — the
population control, because a single-valued region makes any pattern claim
vacuous. Positions `{15, 16, 231…238, 271, 272, 487…494}`:

> **10 pairs `{k, k+256}`, 0 unpaired.** 15↔271, 16↔272, 231↔487 … 238↔494.
> **PURE PAIRING → two-way.** Direct-mapped predicts the same *count* as 20
> isolated singletons and is refuted by the *positions*.

🟢 **And the two blocks agree**: `K2-rb` and `K2b-rb` give the identical FRESH
set, so the pairing is confirmed on two independent runs and the `w126` flip
did not touch the region.

🔴 **This is now `rbcheck`'s, not a scratchpad script's.** `C33`…`C39` and
mutants `M35`…`M40`; `C36` is the population control and `C39` is this
capture. A headline that only a throwaway script can re-derive is not a
finding this repository is entitled to quote.

⚠️ **`CPU-25` does not become more certain.** 量 2026-08-29 already excluded
direct-mapped through `w.assoc.tm = (8192, 3)`. What changed is that a reader
can now check it in the block, by two routes, instead of following an argument
about a search's tie-breaking.

## §13 Group F, and the answer is in the band that closes `FW-34` — with two things that must be written as problems

```
f.sfcr = 3fc00000   f.alias = 00000000   f.live = 00000f0f   f.faults = 00000000
f.win.seq  30354   f.win.str  30354   ->  R      = 1.0000
f.boot.seq 30353   f.boot.str 30354   ->  R_boot = 1.0000
f.dram.seq  1799   f.dram.str  2347   ->  R_dram = 1.3046
f.win.seq2 30354   |seq2 - seq| = 0        (§ 6.8.3 (4) allows 10 %)
```

**`R = 1.0000` is in the `≤ 1.15` band: the window does not buffer a
single-word read, so § 19.7.2's `≤9×` is `9×` and `FW-34`'s last row
CLOSES.** § 6.8.3's asymmetry is honoured — this is the direction that closes
it, and it closes because an uncached instruction fetch *is* a single-word read
from this window.

🟢 **And `0xBFC00000` was compared to `0xBD000000` for the first time.**
`f.alias = 0` says they are one flash; `f.boot.*` matches `f.win.*` value for
value, so the two address decodes (`0x1FC00000` against `0x1D000000`) behave
alike. § 6.8.0 says nothing in this repository had ever compared them, and
§ 19.7.2's `≤9×` rests on stage 1 executing at `0xBFC001D0`.

**Refutation conditions (1), (2), (3), (4), (5) and (6) all pass**, and (4)
passes with **zero** of its 10 % tolerance used. (7) passes for every window
leg — the smallest is 30,353 against `f.dram.str`'s 2,347, and none is near
the ~5,000 wrap floor.

### 🔴 §13.1 The control on the verdict, as written, CANNOT BE SATISFIED in the branch that closes the row

§ 6.8.2: *"`f.dram.str / f.dram.seq` must be **strictly less** than `R`."*
Measured: **1.3046 against 1.0000** — it is *greater*.

**The guard is unsatisfiable whenever `R ≤ 1.15`**, because no ratio is below
1.0 unless the strided leg is *faster* than the sequential one. It was written
before the seating, so it counts, and it is a defect in the control rather than
a reading about the part.

**What the DRAM legs do establish, and it is not nothing:** the same loop, the
same N, the same 64 KiB mask produced a **1.30** stride effect on DRAM. So the
instrument is stride-sensitive, and `1.0000` on the window is not *the tool
cannot see a difference*. ⚠️ **That is a sensitivity control, it is not the
control § 6.8.2 asked for, and it was reached at the bench rather than
written first.** `docs/probe3-cells.md` § 6.8.2 has to be rewritten so the
guard is conditioned on the branch; until it is, this row's verdict rests on
the ratio plus a control nobody predicted.

### 🔴 §13.2 The absolute cross-check lands in "not attributable", and the predicted band is refuted

`f.win.str / 1024` = **29.64 ticks** = 2.075 µs = **103.7 SPI clocks** at DIV 4
/ 50.0 MHz. § 6.8.2's rows are **20.6 ± 15 %** (17.5–23.7), **≈ 82** and
**≈ 9**. It is in none of them: *not attributable*.

* **PREDICTED `f.win.str` ≈ 21,300–21,700 ticks (1.49–1.52 ms). Measured
  30,354 = 2.125 ms. REFUTED** — the band was written before the number and it
  did not contain it.
* The three-way identification *72 clocks · DIV 4 · the datasheet's `DRAM
  Clock` is `CLK-02`'s 200 MHz* is therefore **not established**;
  `notes/kernel-build.md` § 20.5 records that this was the first thing to test
  it, and it comes back **undetermined**.
* ⚠️ **None of this touches `R`.** A ratio of two legs of one loop is
  clock-independent; whatever the per-access cost is made of, it is the same in
  both legs.
* 推, and named as such: 103.7 rather than 72 clocks is ~1.44×. Candidates
  nothing here separates — per-transaction CS turnaround, more dummy cycles
  than the datasheet's `Fast Read`, or a `DRAM Clock` that is not 200 MHz.

🟢 **`f.sfcr` has a second source on the same power-up.** `K2-sfcr` reads
`SFCR = 3FC00000` at the prompt after the payload ran, matching the `3fc00000`
the payload read inside its own timed run. `SFCR2 = 0BA08000` carries `0x0B`,
`LDR-42`'s `Fast Read` opcode.

## §14 What did not run, and the off durations I did not record

**`K-rb` and `K-rbp` are FAILs in `check-predictions` and they are supposed to
be.** They are cells of power cycle 8 and power cycle 8 could not produce them
(§ 5). The readings exist as `K2-rb` / `K2-rbp` on cycle 9, and a cycle-9
capture may not wear the `K-` prefix. **23 of 25 cells ran.**

🔴 **The card carries a line reading `power off at __:__:__  power on at
__:__:__  seconds off: ____`, and I used it for cycle 8 and not for the two
cycles I added myself.**

🔴 **The three numbers in this table were WRONG until 21:30, and the root cause
of all three is one thing: I derived the bounds from when a chat message went
out, and a chat message is not in the record.** Re-derived from the captures'
own `started_wallclock` + `duration_s`, which is what this repository holds:
the last **proof** the board was powered on cycle 8 is `K-J` ending at
**19:53:52** (not a message at 19:58:30), and on cycle 9 it is `K2-yesc` ending
at **20:16:40**. The upper arm was arithmetic: 19:43:07.2 − 02:00:00 is
**63,787 s = 17.72 h**, not 63,400 s. ⚠️ **The correction makes the overlap
worse, not better** — cycle 8 → 9 widens from *0.7–2.8 min* to **0–7.4 min**,
which is the same bound as cycle 9 → 10's **0–7.2 min**, so the two intervals
are now indistinguishable rather than merely overlapping.

| cycle | power off | power on | off duration |
|---|---|---|---|
| 8 | ≈ **02:00** (owner's reading) | **19:43:07.2** | **≈ **63,787 s = 17.72 h**** |
| 9 | **not recorded**, bounded (19:53:52, 20:01:16) | **20:01:16.3** | 0–7.4 min |
| 10 | **not recorded**, bounded (20:16:40, 20:23:50) | **20:23:50.0** | 0–7.2 min |
| off | **20:29** (owner's reading) | — | — |

**The two bounds overlap, so duration is NOT controlled between § 11's two
intervals**, and an earlier draft of this file's § 11 claimed the bit-exact
cycle had the longer power-off. It cannot be known that it did. 🔴 `MEM-17`
exists *because* an off duration was not recorded; the card added a line for
it; I used the line once and then added two cycles without it. **The cheapest
control in this seating is the one that was skipped, and it was skipped by the
person who wrote the section complaining about it.**

## §15 The reference a future seating can read for free

The block is in DRAM at `0x80A02000` with the board powered down at 20:29.

```
718 words · magic 524C5833 · nonce 7E41C9D0 · seal w717 = 055B8159
sha256(K2b-rb.log)  61aa643bb831ed96f01cc77991fae7f5d19af3f902ee633139656368e63323ae
sha256(K2b-rbp.log) d6429e53fbce3319f4e3ed9538f0289dfb4cdc561c0f2aa45a151c6a69677ca9
```

**If the next seating's first command after the ESC catch is `DW 80A02000 718`,
it measures bit-exact retention over the whole intervening power-off**, against
a checksummed reference, for the price of one `DW` and no power cycle. It costs
nothing except not overwriting the block first — so `probe3` must not be `J`ed
before that read.

⚠️ **Superseded by § 16 for THIS block**: it was read at 35.1 minutes and is
2.6 % decayed, so `K2b-rb.log` is no longer the reference a longer interval can
be measured against. **`K4-rb.log` is** — it was read twice on one power-up and
the two agree word for word.

## §16 🔴 Power cycle 11 — the duration term, and it refutes § 11's 推

**Both ends timed, for the first time in this seating.** Power off **20:29**
(owner's reading), power on **21:04:07.2** (`K4-A` started 21:03:59.761, first
byte 7.478 s in) — **2,107 s = 35.1 minutes**. No upload, no `J`: ESC catch,
then `DW 80A02000 718` twice.

```
K4-rb vs K4-rb2 (two reads, one power-up)   :   0 of 718 words differ
K2b-rb vs K4-rb (across 35.1 min, no vendor):  411 of 718 words differ

bits compared 718 x 32 = 22,976
bits changed              598  = 2.603 %
   0 -> 1                 500      2.634 % of the 18,985 zero-bits
   1 -> 0                  98      2.456 % of the  3,991 one-bits
```

**The magic itself decayed**: `524C5833` → `564C5033`. 🟢 **`rbcheck` refused
rather than reporting**, and its first finding is the right one — *magic
564C5033 names no payload this tool has a progress ladder for, so "the run
completed" cannot be checked at all*. It did not read a rotted block as a
result block.

⚠️ **One thing it says that is wrong in cause**: it also reports *the run wrote
past its own block* for `w718`/`w719`, which are decayed poison (`DEAD40DE`,
`DEBDC0DE`) and not an over-run. **When the magic is unrecognised the margin
diagnosis is not reliable**, and the tool asserts a cause there rather than a
difference. Noted, not fixed tonight.

**The decay is close to symmetric** — 2.63 % of the zero-bits and 2.46 % of the
one-bits — which is what a true/anti-cell array gives, roughly half the cells
storing a logical 1 as charge. Roughly uniform across the block (50–70 bits per
2,048), with the last two chunks lower (32 and 10) and that is unexplained.

### 🔴 What this does to § 11

| off duration | vendor-firmware boot inside it | bits changed of 22,976 |
|---|---|---:|
| 0 – 7.2 min (cycle 9 → 10) | no | **0** |
| 0 – 7.4 min (cycle 8 → 9) | **yes** | **1** |
| **35.1 min** (cycle 10 → 11) | no | **598** |

**Duration is the dominant term by three orders of magnitude, and one bit at
~2 minutes is the weakest cell in the array rather than evidence of anything
thermal.** § 11's 推 is retracted: the vendor-firmware boot is no longer
*the element unique to the flipping interval* in any useful sense, because the
element that actually varies — time — was never controlled.

⚠️ **What is still not known**: where the knee is. `≤ 7.3 min → 0` and
`35.1 min → 598` are three orders apart and nothing sits between them. The
next seating's first `DW` gives an overnight point for free; a 10-minute point
costs a power cycle and was deliberately not spent tonight.

🔴 **And the ordering is still not established**: cycle 9 → 10's bound
(0 – 7.2 min, 0 bits) and cycle 8 → 9's (0 – 7.4 min, 1 bit) **overlap**, so
even the duration story cannot be checked against them. That is § 14's defect
doing its damage, one section later.

## §17 🔴 The suite that went red is the one nobody edited, and what it found is not a count

`tools/test-boot-timeline.sh` `B2` hardcodes the cold/warm census and it went
red — **the second seating in a row**, and both times it was the
whole-suite rule that caught it rather than `--only`. Isolation check, run
before the line was touched: every bench directory **except** `2026-08-31c`
still reports **14 cold, 9 warm**, and `2026-08-31c` alone reports **4 cold,
2 warm**. So the delta is exactly `+4 / +2` — the four ESC catches and the two
watchdog reboots inside `K-J` and `K2-J` — and nothing was reclassified.
Updated to **18 cold, 11 warm**.

🔴 **But the census also moved something a count cannot show, and it lands on
`SPEC.md`.** `CLK-15 cold/warm` records *cold 348.0–356.9 ms (n=7) against warm
338.2–347.6 ms (n=7)* — **two DISJOINT ranges**, which is what the claim *a cold
power-on is 4.5–14.5 ms slower than a warm reset* rests on. After this seating:

```
cold  n=18   325.9 .. 358.3 ms   mean 350.0   spread 9.2 %
warm  n=11   338.2 .. 357.2 ms   mean 343.6   spread 5.5 %
```

**They overlap.** The difference in MEANS survives at 6.4 ms; the per-sample
rule does not.

⚠️ **And the population was redefined rather than merely enlarged.** Three of
this seating's four colds are power-ons after an off of **minutes** — ~1–2,
0–7 and 35.1 — where every cold before them was a seating's first power-on,
hours or days after the last. 🔴 **There is no monotone relation either**: the
fastest cold in the whole population is `K-A` at **325.9 ms** after **17.72 h**
off, and the slowest of this seating's is `K4-A` at **355.4 ms** after
**35.1 min**. **This is not a clean refutation; it is a variable nobody had
separated**, and both `SPEC.md` rows now say so.
