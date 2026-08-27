# Which drop built this firmware — reading the matrix, and the floor that replaced the plan's

**`R2a/b/d-1`. Desk work, 2026-08-27. Nothing here was measured on the device.**
Every number is **讀** — read out of six vendor firmware trees, one of which is
this unit's own flash dump — or **推**, and each is marked. Zero flash bytes,
zero power cycles, zero device readings.

**This note owns two things**: the *reading* of the matrix, and the *decision*
that replaced `plan/router-rebuild-plan.md:1128`'s `FLOOR`. The instrument
itself — what `binsim` is, how `k=7` was chosen, its thirty-five controls — is
`notes/binsim.md`'s and is not restated here. The cell lives in one place,
`tools/binsim-corpus.tsv`'s `@floor` row, and this note is why it is that cell.
Where a paragraph in the instrument note has been narrowed or refuted by this
reading it is marked 🔄 there and points here.

## Refutation conditions, written before the reading

> **The floor is wrong** if `CROSS >= FLOOR` at the pinned `k`, where `CROSS` is
> measured **at the same denominator** as the comparison the floor governs, or
> if the named cell stops being the top of that population as `k` moves through
> the range the metric's own null admits. Both are printed by `binsim --corpus`
> on every run; `E7` asserts the first and the `R` section of
> `tools/test-binsim.sh` — twenty-two cases against the real six trees — pins
> both.

> **The floor's premise is wrong** if the pair either side of the cell shares
> source. `boa` and `busybox` are separate upstream projects; the corroborating
> pairs are `boa` against `pppd` and `wscd`, and all three land within 0.3 pp
> of each other, which is what a shared-compiler-idiom level should look like
> and not what shared source would.

> **The precondition is unnecessary** if one upstream source, built under two
> compilation models, scores *above* the floor. `E8` measures exactly that and
> would go red.

> **The clusters are product lines, not build generations**, if the partition
> can be reproduced by sorting the six trees by product — each cluster one
> product, each product one cluster. Weaker but still fatal: if the highest
> same-product cell that crosses a cluster boundary were above the lowest cell
> inside a cluster, product would be explaining part of the partition and the
> reading would have to say how much.

> **The nearest-neighbour identification is wrong** if it moves with `k`
> anywhere above the null's cutoff, or if the gap to the second-nearest cell
> does not clear the metric's estimated reproducibility error.

> **`TC-02` cannot move here at all**, and saying so is part of the result: the
> corpus holds six *shipped images*, and not one of them is a GPL drop. A matrix
> over shipped images can exclude generations and set the bar; it cannot name
> the drop. Only `R2a/b/d-4` can.

---

## 1. The floor: which cell, and why that one

`R2a/b/d-0` refuted the plan's floor and stopped there on purpose. In one line:
the plan's `FLOOR` was `boa unit-2018 / v3.4.0` = **0.0650**, and the score two
programs reach when they share nothing but the compiler is **0.1581**. A floor
below that is cleared by a program with no shared source at all, so the warn
band above it carried no information.

### The first replacement was also wrong, and the record of it stays here

This step's first answer was **`busybox unit-2018 / v3.4.0` = 0.1646** — the
plan's own tree pair, read on the one program whose upstream version is
constant across it (讀, `BusyBox v1.13.4` in all six trees), clearing 0.1581 by
0.65 pp. The argument was that `boa` crosses a source rewrite on that step
(讀: −16.5 % of its bytes, `+libcjson`, `+libmtdapi`, strings containment
0.6629) while `busybox` does not, so `busybox` isolates the compilation-model
change.

It does isolate it. What it does not do is isolate it **at the denominator the
rule uses**, and an adversarial review killed it the same day.

> `binsim(A,B) = |G(A) ∩ G(B)| / min(|G(A)|, |G(B)|)`. **The denominator is the
> smaller feature set.** Two programs sharing nothing but a compiler have an
> intersection of about four and a half thousand grams whatever their sizes, so
> their containment is roughly `4500 / |G(smaller)|` — a property of the
> comparand's size before it is a property of the corpus.

`busybox unit-2018` carries 42,297 grams and `boa unit-2018` carries 28,887, a
factor of **1.46**. The floor was read on the first; the rule it governs divides
by the second. 讀 2026-08-27, at a matched denominator:

| what the pair is | cell | denominator | containment |
|---|---|---:|---:|
| no shared source, same model | `boa` / `busybox`, `unit-2018` | 28,887 | **0.1581** |
| no shared source, same model | `boa` / `pppd`, `unit-2018` | 28,887 | 0.1578 |
| no shared source, same model | `boa` / `wscd`, `unit-2018` | 28,887 | 0.1551 |
| **one upstream source, model changed** | `pppd` `unit-2018`/`v3.4.0` | 28,601 | **0.1212** |

**The ordering reverses.** At this scale a pair that shares its entire upstream
source and differs only in compilation model scores *below* a pair that shares
no source at all. The 0.65 pp the first answer rested on was the distance
between two denominators, and the family it claimed to bound sits under the
level it claimed to clear.

The same-source-across-the-model-change family, read across the whole tree pair
(讀; every one of these is one upstream version in both trees, and every one
crosses `0x1007`-with-`pic` → `0x1005`):

| program | version | denominator | containment |
|---|---|---:|---:|
| `busybox` | 1.13.4 | 42,297 | 0.1646 |
| `pppd` | 2.4.4 | 28,601 | 0.1212 |
| `iptables` | 1.4.4 | 23,547 | 0.1072 |
| `routed` | v1.0 | 5,876 | 0.1009 |
| `tc` | (iproute2) | 21,495 | 0.0935 |
| `dnrd` | 2.12.1 | 5,629 | 0.0853 |

It rises with size, because a larger program holds more long idiomatic runs that
survive a model change. The no-shared-source level *falls* with size, because a
roughly constant idiom set is divided by a larger denominator. **The two curves
cross**, which is exactly why a single scalar read at the wrong denominator
inverts the answer.

### The floor, and why it is the `CROSS` cell itself

```
@floor  boa  unit-2018  busybox  unit-2018     = 0.1581
```

At `boa`'s denominator the corpus holds **nothing** above the no-shared-source
level and below `BASE` that could serve as a floor — the same-source family sits
under it, and the next thing above it is 0.8768. So the tightest correct floor
*is* that level, and `@floor` names the cell that records it. The manifest's
`@floor` row grew a five-field form for this: it names a cell across programs,
which no matrix holds.

That makes the floor a **population**, not one pair's number, and `E7` asserts
it: the named cell must be the highest of every program in the reference's own
tree whose feature set is at least as large — 0.1581 against 0.1578 and 0.1551.
Programs *smaller* than the reference are excluded on purpose, and the reason is
measured rather than argued: 讀 2026-08-27 inside `unit-2018`, over its 36
programs with at least 2,000 code words, **422 of the 630 cross-program cells
sit above 0.1646**, and the top of that list is `sysconf`/`timelycheck` at
**0.9967** — two vendor tools that share their source. *"Two different
programs"* is not the same claim as *"two programs that share no source"*, and
only the second one is a floor.

> **At or below `FLOOR`, this metric is not saying "a different source". It is
> declining to say anything.** A pair that shares no source reaches it, and so
> does a pair that shares all of its source across a compilation-model change.

### The precondition that falls out of it

Because the same-source-model-changed family sits *below* the floor, a low score
across a model change is not evidence of a wrong drop — it is the channel
carrying nothing. `E8` is that reading, asserted rather than argued:
`pppd unit-2018 / v3.4.0` = 0.1212 at a denominator within 1 % of the floor's
own, against `FLOOR` 0.1581. So the rule gains a gate in front of it:

```
VOID   the compilation model differs -- the container fingerprint does not match
fail   score <= FLOOR = 0.1581
warn   FLOOR < score < BASE
pass   score >= BASE  = 0.9818
```

`BASE − FLOOR` is **0.8237**, which clears the estimated reproducibility error
by 1025×.

### Does the floor survive a change of `k`? — 讀

With `FLOOR` naming the `CROSS` cell the two are equal by construction at the
pinned `k`, so a "margin" would say nothing. What the sweep still measures, and
what `--corpus` now prints, is whether the **named cell stays the top of its
population** as `k` moves. If another program overtakes it, the floor is below
the no-shared-source level and the verdict fires.

讀, dense over `k` = 1…16: the named cell is the top at **every `k` from 2 to
14**, and is overtaken at **`k` = 1** by `pppd` — where the reference itself
flips, because at `k` = 1 `busybox` carries the smaller feature set. At `k` = 15
and 16 the reference flips again for the same reason and the verdict still
stands. So the choice is not a property of the pin.

⚠️ `k <= 6` is excluded by the metric's own null, but state that precisely:
`E6b` measures the null at exactly **one** value, `k − 1` = 6, where eight of
twelve binaries sit at or above 0.05. *"Every `k` below the pin is excluded"* is
an extrapolation from that one reading, and no control here makes it.

### The alternatives, and why they were rejected

**`busybox unit-2018 / v3.4.0` (0.1646)** — this step's own first answer.
Rejected on the denominator, above.

**`boa unit-2018 / v2.1.2` (0.8860)**, the lowest cell in this unit's own
cluster. Tempting because it is the lowest *populated* cell above the mush.
Wrong for one reason: it is not a floor, it is a different threshold. A rebuild
scoring 0.5 would be called *no evidence* when 0.5 is three times anything a
pair with no shared source has reached in this corpus at that denominator.
**A floor marks where the metric stops carrying information, and 0.886 is a
score carrying a great deal of it.** (It is also not the lowest such cell —
0.8768 and 0.8848 are lower.)

⚠️ **What is NOT true, and an earlier draft of this note said it was: the warn
band is not empty.** With `FLOOR` = 0.1581 and `BASE` = 0.9818, thirteen of the
corpus's forty-five code-channel cells fall inside it — five on `boa` (0.8768,
0.8848, 0.8860, 0.8951, 0.9740) and all eight `busybox` cells that cross the
generation (0.1646–0.1695). The true statement is about a **gap**, and only on
`boa`: **nothing in the `boa` matrix lands between 0.0681 and 0.8768.**

### Caveats that belong to the choice

* **`BASE` and `FLOOR` share a denominator** — 28,887, this unit's own `boa`,
  which is the smaller set in every comparison the rule governs. That is now
  printed beside both and pinned by a case, because a threshold read at one
  denominator and applied at another is exactly what sank the first answer.
* The floor cell and its population share one binary, `boa/unit-2018`. That is
  deliberate — it is the denominator — but it means the three cells are not
  three independent measurements of one quantity.
* **"One upstream source" is a banner, not a diff.** `pppd` reports 2.4.4 in
  both trees (讀), and that the vendor applied the same patches to it is 推.
  The same caveat sank the busybox premise harder than it looked: 讀
  2026-08-27, `v3.4.0`'s busybox carries `awk`, `md5sum` and `passwd` where
  this unit's carries `traceroute`, `ping6`, `chroot`, `uptime` and `nice`, and
  the rootfs holds 50 busybox symlinks against `v3.4.0`'s 54. So the applet set
  moved even where the version string did not, and `E8`'s reading is *one
  upstream version under two models, up to a build-config delta*.
* **The reproducibility error is the smallest of three candidates**, not the
  only one: 讀, `binsim` finds `busybox n300rt-2.1.6/unit-2018` and
  `v2.1.2/unit-2018` at 8.04e-4 and `n300rt-3.4.0/v3.4.0` at 4.28e-3. The tool
  prints the range now. The tightest is the harder bar for `BASE − FLOOR` to
  clear, which is why it is the one the guard uses.

---

## 2. The corpus is crossed, not confounded — and that refutes the sentence this gate was carrying

`PROGRESS.md`, `notes/binsim.md`, `LOG.md` and `binsim.py`'s own docstring all
carried some form of *"date, product line and SDK generation are completely
collinear in this corpus and no function of two binaries can separate them"*,
and the step list named *"reading a cluster as a toolchain when it is a product
line"* as the most likely way this step would go wrong. **讀 2026-08-27, from
`/etc/version` in each tree: product line is crossed with the clustering, and is
refuted as an explanation of it.**

| tree | `/etc/version` | product | marketing version | build date | cluster |
|---|---|---|---|---|---|
| `v2.1.2` | `TOTOLINK-N150RT-V2.1.2` | **N150RT** | V2.1.2 | 2015-08-11 | ① |
| `n300rt-2.1.6` | `TOTOLINK-N300RT-V2.1.6` | N300RT | **V2.1.6** | 2016-05-16 | ① |
| `unit-2018` ← this unit | `TOTOLINK-CX-N150RT-V2.1.6-B20171121.1002` | **N150RT** | **V2.1.6** | 2018-01-10 | ② |
| `n200re-3.2.0` | `TOTOLINK-N200RE-V3.2.0-B20180330.1757` | N200RE | V3.2.0 | 2018-03-30 | ② |
| `n300rt-3.4.0` | `TOTOLINK-N300RT-V3.4.0-B20190315.1747` | N300RT | V3.4.0 | 2019-03-15 | ③ |
| `v3.4.0` | `TOTOLINK-N150RT-V3.4.0-B20201030.1142` | **N150RT** | V3.4.0 | 2020-10-30 | ③ |

* **The similarity partition separates cleanly and product line is orthogonal to
  it.** The lowest *within*-cluster cell is **0.9740** and the highest
  *between*-cluster cell is **0.8951** — no overlap, on `boa`, over all fifteen
  cells. Product does not line up with that: **N150RT appears in all three
  clusters** and N300RT in two, so two builds of *one product* score **0.8860**
  (`v2.1.2`/`unit-2018`, ①↔②) and **0.0650** (`unit-2018`/`v3.4.0`, ②↔③), while
  two *different products* inside one cluster score **0.9863** and **0.9818**.
  Both same-product cross-cluster numbers are quoted, including the high one:
  0.8860 is the strongest case product line has anywhere in this corpus, and it
  is still below every within-cluster cell.
* **The vendor's own version number is refuted too.** `n300rt-2.1.6` and this
  unit are both stamped **V2.1.6** and land in different clusters — their cell
  is **0.8951**, the highest between-cluster cell there is, and still below the
  lowest within-cluster one. `unit-2018` (V2.1.6) and `n200re-3.2.0` (V3.2.0)
  land together at 0.9818. The marketing string does not track the build.

**What remains collinear is date and SDK generation**, and that is a tautology
rather than a confound — an SDK generation *is* a stretch of time. The sentence
that has to be corrected is the one about product line, and it is corrected in
`notes/binsim.md`, `tools/binsim.py` and `SPEC.md` in the same commit as this
note.

⚠️ Two smaller things read out of the same trees, neither load-bearing. This
unit's `/etc/version` is stamped `B20171121` while its BusyBox banner and **every
binary's mtime** say 2018-01-10 — 50 days apart. The universal has to be
restricted to binaries and the exception is worth more than the rule: 讀, 14 of
the 267 in-image files carry other mtimes, thirteen of them an SDK-vintage
residue (2014-03-19, 2014-05-08, 2014-11-05) that recurs byte-for-byte in four
of the six trees, and the fourteenth is `/etc/inittab` at **2017-11-08** —
byte-identical across those four trees yet re-stamped in each, thirteen days
before this unit's `B20171121`. So the version stamp tracks the source checkout
and the binaries track the build. And the `CX` in `TOTOLINK-CX-N150RT` is
unexplained; it is in no other tree. Recorded, not interpreted.

---

## 3. `busybox` is a toolchain tracer, and on one edge it separates the two halves

The standing caveat is that a high score proves *source and toolchain were the
same together* and cannot say which half. That is true of any single cell. It is
not true of the corpus, because the corpus contains a program whose upstream
version is constant: **BusyBox 1.13.4, in all six trees** (讀). Its cells
therefore move only when the code generator's output does.

Reading the two programs side by side, per edge of the partition — all 讀,
`binsim --corpus`:

| edge | `busybox` code | `boa` code | `boa` strings | container fingerprint | reading |
|---|---:|---:|---:|---|---|
| inside ① | 1.0000 | 0.9863 | 0.9783 | identical | one code generator, one `boa` revision |
| inside ② | 1.0000 | 0.9818 | 0.9913 | identical | one code generator, one `boa` revision |
| **① ↔ ②** | **0.9995–0.9997** | **0.8768–0.8951** | 0.9263–0.9387 | only the section header table is gone | **the code generator's output did not move; `boa`'s source did** |
| ①② ↔ ③ | 0.1646–0.1695 | 0.0584–0.0681 | 0.6629–0.7026 | pic → no pic, +`PLTGOT`, 8→10 phdrs, +2 libs | both moved; not separable |
| inside ③ | 0.9994 | 0.9740 | 0.9766 | identical | one code generator, one `boa` revision |

**The ① ↔ ② row is the separation.** Same upstream BusyBox, built by four
different trees over two years and seven months, scoring 0.9995–1.0000 — while
`boa` over the same edge falls from its within-cluster 0.9863/0.9818 to
0.8768–0.8951, **a drop of 8.7 to 11.0 points**. If the code generator had
changed, `busybox` would have moved with it.

The sharpest single reading is not the near-1.0 pair but the pair that is
*deliberately different* (inside ②, not across the edge): **`n200re-3.2.0`'s
`busybox` has 1,869 fewer code words than this unit's (57,669 against 59,538)
and all 40,915 of its 7-grams are a strict subset of this unit's 42,297** —
containment exactly 1.0000, Jaccard 0.9673. A different config, and not one gram
of new structure. That is what one code generator looks like when the recipe
changes and the compiler does not.

### A third instrument, which attenuates the same-program objection

The reading above still puts two builds of `busybox` side by side. A read of the
toolchain axis that leans on that far less is available for free: for each tree
take

    IDIOM(t) = G(boa_t) ∩ G(busybox_t)

— the 7-grams shared by two programs with no source in common. Whatever is in
there is a property of how the tree was compiled. Comparing `IDIOM` *between*
trees is then a toolchain read. 讀:

| | `v2.1.2` | `n300rt-2.1.6` | `unit-2018` | `n200re-3.2.0` | `n300rt-3.4.0` | `v3.4.0` |
|---|---|---|---|---|---|---|
| `v2.1.2` | — | 0.993 | 0.939 | 0.932 | 0.099 | 0.099 |
| `n300rt-2.1.6` | 0.993 | — | 0.945 | 0.937 | 0.101 | 0.101 |
| `unit-2018` | 0.939 | 0.945 | — | 0.969 | 0.100 | 0.099 |
| `n200re-3.2.0` | 0.932 | 0.937 | 0.969 | — | 0.103 | 0.102 |
| `n300rt-3.4.0` | 0.099 | 0.101 | 0.100 | 0.103 | — | 0.980 |
| `v3.4.0` | 0.099 | 0.101 | 0.099 | 0.102 | 0.980 | — |

*(containment; |IDIOM| runs 3,814–4,651 grams, 11.3–15.8 % of each tree's `boa`)*

**4+2, with a ninefold gap.** This unit's row: 0.939 / 0.945 / 0.969 against the
other three PIC-era trees and 0.099 / 0.100 against the 2019/2020 pair.

⚠️ **It does not "never compare a program with itself", and an earlier draft of
this note claimed it did.** Expand the cell:

    IDIOM(t1) ∩ IDIOM(t2) = (G(boa_t1) ∩ G(boa_t2)) ∩ (G(bb_t1) ∩ G(bb_t2))

— two builds of `boa` are in that numerator, and two builds of `busybox` are
too. What the construction does is **attenuate** the same-program signal: a gram
survives only if it is in all four sets, so a run of `boa` source that both
`boa` builds share but neither `busybox` has is discarded. That is worth
something and it is not immunity.

⚠️ `IDIOM(t)` is also defined through `boa`, so it moves when `boa`'s source
moves. The weak ①/② structure inside the PIC block (0.932–0.945 across, 0.969
and 0.993 within) is what a `boa` source change produces and is **not** evidence
of a toolchain change.

⚠️ **"Toolchain" is doing more work in this section than the measurement
supports, and the exact reading is narrower.** What is 讀 is that *the code
generator's output* did not move across ① ↔ ②: one upstream source in,
essentially one binary out. That is compiler *and* flags together. Nothing here
separates "a different compiler" from "the same compiler invoked differently".

⚠️ And the transfer from `busybox`'s toolchain to `boa`'s is **推**. It assumes
one toolchain per tree. Two things make that assumption cheap rather than free:
the `IDIOM` table is built out of `boa` and agrees, and every tree's `boa` and
`busybox` carry identical `e_flags`. A compiler change too small to move 7-gram
structure would be invisible to all three instruments, and "the same `rsdk`
build" is a stronger claim than any of them supports.

### So the 2+2+2 and the 4+2 are one fact, not two

`notes/binsim.md` records that `boa` partitions 2+2+2 and `busybox` 4+2, and
scopes the 2+2+2 to `boa` rather than leaving it unqualified. The mechanism is
now readable:

* **The toolchain axis is 4+2** — `busybox` says so, the `IDIOM` table says so,
  and the parts of the container fingerprint a compiler controls (`pic`,
  `DT_MIPS_PLTGOT`, phdr count) say so.
* **`boa`'s extra split, ① against ②, is `boa`'s own source revision**, plus a
  post-link strip of the section header table that changes no code byte.
* `notes/lwl-mystery.md`'s unaligned-instruction counts — 176 / 144 / 0 — are a
  `boa` reading, so they carry the same 2+2+2 for the same reason.

The identity anchor makes the same point from the other side: `bin/acltd` is one
sha256 in all six trees and still carries `e_flags 0x1007` **with `pic`** inside
the 2019 and 2020 images, where everything that was actually rebuilt is `0x1005`.
It was never rebuilt, so it never crossed the generation.

---

## 4. Where this unit sits

**Nearest neighbour: `n200re-3.2.0`, `boa` containment 0.9818** (讀). Second
nearest is `n300rt-2.1.6` at 0.8951 — a gap of **8.67 pp**, about 108× the
estimated reproducibility error. The ranking is stable: `n200re-3.2.0` is this
unit's top cell at **every `k` from 2 to 16** (讀, and at `k = 1` three cells tie
at 1.0000, which is saturation, not a tie in the data).

What that supports, stated narrowly:

* **讀** — this unit's `boa` and `n200re-3.2.0`'s `boa` share 98.18 % of the
  smaller 7-gram set, and their container fingerprints are identical field for
  field. **推** — that this means one source revision, one toolchain and one set
  of flags, 79 days apart, for two different products. The score is the reading;
  "same source revision" is the interpretation, and the corpus holds no pair
  that could calibrate how far apart two revisions can be and still score 0.98.
* **讀** — 526 of this unit's 28,887 7-grams (1.8 %) are not in `n200re`'s. That
  is the size of *whatever* differs between the two builds; calling it
  per-product configuration is **推**.
* **讀** — this unit is on the PIC side of the compilation-model boundary, which
  falls between 2018-03-30 and 2019-03-15.
* **讀** — the 2019 and 2020 images were built with a different compilation
  model: `0x1005` without `pic`, `DT_MIPS_PLTGOT` present, ten program headers,
  two extra libraries, and 0.0650/0.0664 on the code channel. **推** — that the
  *toolchain* changed rather than only its flags; nothing here separates a new
  compiler from the same compiler invoked differently. Either way, any GPL drop
  published for those images is excluded as this unit's builder, because the
  binaries it produced do not have this unit's shape.
* **推** — the toolchain that built this unit is the one whose banner `TC-01`
  already holds from the kernel, `gcc 4.4.5-1.5.5p2` / uClibc 0.9.30.3. That
  value is 量 from this unit's kernel banner and 讀 from the `.comment` the two
  2015/2016 trees still carry for their own `boa` (`TC-09`) — but those two
  trees are in cluster ①, and the transfer across the ①/② edge rests on §3's
  toolchain-tracer reading, which is 推.

**What it does not support.** It does not identify a drop. `n200re-3.2.0` is a
shipped image, not a source release, and "built by the same thing as N200RE
V3.2.0" is not a name.

---

## 5. `TC-02` — it stays **推**, and that is the answer, not a deferral

`TC-02` names a candidate: `rtl819x-toolchain`'s
`rsdk-1.5.5-5281-EB-2.6.30-0.9.30.3-110714`, on the grounds that every field of
its name matches `TC-01`'s banner. **Nothing in this matrix touches it**, and
the reason is structural rather than a shortage of work: the corpus is six
shipped firmware images and a GPL drop is a source and toolchain release. A
similarity matrix over images can place this unit in a build generation. It
cannot tell you what was on the build machine.

What did move around it:

| | |
|---|---|
| excluded | the 2019/2020 SDK generation, on two independent instruments |
| narrowed | this unit's builder is whatever built `n200re-3.2.0` 79 days later |
| corroborated | the code generator's output did not change across 2015-08 → 2018-03 (§3), so a drop dated 2011 being in use in 2018 is not the anomaly it looks like. Weak, and 推 |
| unchanged | `TC-02` itself. **推** |

🔴 **The gate's own refutation condition ⓐ did not fire and `TC-02` still does
not move.** The fifteen scores span 92.8 pp against a 5 pp bar. A refutation
condition that is satisfied and still leaves the answer undetermined is telling
you it was not the binding constraint; the binding one was never written down
and is now: *a similarity matrix over shipped images cannot name a source
release, whatever it scores.* The thing that would move `TC-02` is
`R2a/b/d-4`, and it needs `R2a/b/d-3`'s container first.

---

## 6. What `R2a/b/d-4` must do — written now, while nothing depends on it

The plan's rule was *pass at or above `BASE`, warn between, fail at or below
`FLOOR`*. It needs a gate in front of it, and each line has to name the program
it governs — `R2a/b/d-4` rebuilds **two** of them, and their fingerprints are
not the same.

**For `R2b`, the `boa` rebuild — the drop test:**

```
PRECONDITION   the rebuilt boa's container fingerprint must match unit-2018's
               boa: e_flags 0x1007 with pic, 8 program headers, no
               DT_MIPS_PLTGOT, DT_NEEDED = {libapmib, libc, libgcc_s}.
               If it does not, the comparison is VOID, not "fail" -- 讀, with
               the model changed one upstream source scores 0.1212, BELOW the
               floor, so the channel is not carrying source information at all.

pass           binsim(rebuild, unit-2018/boa) >= BASE  = 0.9818
warn           FLOOR < score < BASE
fail           score <= FLOOR                          = 0.1581
```

**For `R2a`, the `busybox` rebuild — the toolchain test:** the same shape, but
unit-2018's `busybox` is **7 program headers and `DT_NEEDED = {libc, libgcc_s}`
with no `libapmib`** (讀), so the fingerprint it must match is its own. And its
bar is not `BASE`: 讀, BusyBox 1.13.4 scores 0.9995–1.0000 across all four
PIC-era trees, so a rebuild that does not land in the high 0.99s against this
unit's means the toolchain is wrong.

Three more things this step hands `-4`:

1. **`R2a` cannot discriminate between drops of the PIC era** — `busybox` is
   essentially one binary across all four of those trees. That is exactly what
   makes it a clean toolchain test, and the answer arrives before any `boa`
   source question is asked. **Do it first, and read it as a toolchain result.**
2. **`R2b` is the drop test.** `boa` is the only program in the corpus whose
   source moved *inside* a toolchain generation (0.8768–0.8951 across ① ↔ ②),
   so it is the only one that can distinguish drops of the same era.
3. **The comparand is this machine's binary.** `$FWRE_WORK/extracted/unit-2018`
   is the flash dump's rootfs; the plan puts this in a box and it is the easiest
   thing in this gate to get wrong.

---

## What could still be wrong

* **The floor is now equal to `CROSS` by construction**, so the verdict that
  guards it can only fire if the corpus changes — a seventh program at that
  denominator scoring higher, or a `k` where the named cell is overtaken. `E7`
  and the sweep are what would catch either, and both are checked on every bench
  run. Nothing checks them on a runner, by construction.
* **The population is three programs.** `boa` against `busybox`, `pppd` and
  `wscd`, spread over 0.1551–0.1581. Three is enough to show the level is not
  one pair's number and not enough to put an error bar on it.
* **The transfer of `E8`'s reading from `pppd` to `boa` is 推.** It is the
  closest denominator the corpus offers (28,601 against 28,887, within 1 %) and
  it is still a different program.
* **The toolchain transfer from `busybox` to `boa` is 推** (§3), and all three
  instruments would miss a compiler change too small to move 7-gram structure.
* **Six trees is a small corpus**, and every cluster has exactly two members.
  What makes the partition a claim is that three instruments reading different
  parts of the file agree on it, and that a fourth explanation — product line —
  was tried and refuted.
* **Nothing here has been run against a rebuild.** Every threshold in §6 is a
  prediction. The honest possibility is that a correct rebuild lands at 0.95 for
  reasons that have nothing to do with the drop — a different `-O` level, a
  different uClibc point release, a different `strip`. That would not refute the
  identification; it would mean `BASE` is the wrong bar, and the way to find out
  is `-4`.
