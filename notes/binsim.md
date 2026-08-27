# `binsim` — the ruler, its calibration, and the floor the plan did not have

**`R2a/b/d-0`. Desk work, 2026-08-27. Nothing here was measured on the device.**
Every number below is *read out of a binary*: out of six vendor firmware trees,
one of which is this unit's own flash dump. What the silicon does is not in
scope and is not touched.

**This note owns the instrument.** The matrix appears here as the evidence that
the instrument discriminates at all, which is `R2a/b/d-0`'s definition of done.
*Reading* the matrix — which drop this firmware was built from, and which cell
replaced the plan's refuted `FLOOR` — is `R2a/b/d-1`, **`notes/which-drop.md`**,
and this note stops before it on purpose. Where a paragraph here has since been
narrowed or refuted by that reading it is marked 🔄 and points at it rather than
being rewritten in place.

## Why the question exists

`R2b` asks which GPL drop built this unit's firmware, and the plan's answer is
that the threshold must come out of the data rather than out of me:

```
BASE  = binsim(unit-2018, n200re-3.2.0)   same SDK, ten weeks apart, other product
FLOOR = binsim(unit-2018, v3.4.0)         same product, five years, SDK generation
pass    binsim(rebuild, unit-2018) >= BASE
void    the fifteen pairwise scores span < 5 percentage points
```

That last line is why the controls were written before any number was reported.
A similarity metric is the easiest instrument in this project to build so that
it cannot fail: almost any function of two MIPS binaries from one vendor returns
something near 0.8, and a matrix of numbers near 0.8 reads like a result.

## The instrument

```
binsim(A, B) = |G(A) & G(B)| / min(|G(A)|, |G(B)|)
```

where `G(X)` is the set of 64-bit FNV-1a hashes of every 7-gram of normalised
MIPS operation tokens over `X`'s code window. Jaccard — the same intersection
over the union — is printed beside it on every line, never instead of it.

**Thirty-five controls, and every invocation runs them before it reports
anything.** Twenty-four are synthetic and need no vendor binary at all, so a
fresh clone with no `$FWRE_WORK` still has a control on every part of the file;
eleven need the real six trees. They are defined in `tools/binsim.py`'s header —
one owner — and exercised by `tools/test-binsim.sh`, 96 cases of which 74 run on
a stock runner. What follows quotes only the ones that decided something.

🆕 **Three of them are `R2a/b/d-1`'s, and each covers something this note left
open.** That step replaced the plan's refuted `@floor`, so the real corpus
stopped taking the `REFUTED` branch — and that branch had no fixture anywhere
else. So the verdict became a function; **`D5`** drives it in both directions,
at the boundary, and with its second argument moved (an adversarial reviewer
built a mutant that ignored that argument and passed everything, which is `M12`
now); **`E7`** asserts the floor is the highest of a *population* at one
denominator rather than one pair's number; **`E8`** measures what a
compilation-model change alone costs. A verdict that has stopped firing is not
a verdict that has been satisfied; it is a verdict nobody is watching.

Four measurements forced that shape, and each is a way it could have been wrong.

**The code window cannot come from `.text`.** Four of the six `boa`
(`n200re-3.2.0`, `unit-2018`, `v3.4.0`, `n300rt-3.4.0`) have **no section header
table at all**; `objdump -d` on them emits nothing and reports 0 for every
mnemonic, which `notes/lwl-mystery.md` already had to learn. The window is
`[DT_INIT, DT_FINI)` out of `PT_DYNAMIC`, which all six have. On the two that
kept their section headers it reproduces `.init` through `.fini` exactly:

| tree | derived window | `.init` | `.fini` |
|---|---|---|---|
| `v2.1.2` | `[0x3f90, 0x657d0)` | `0x3f90` | `0x657d0` |
| `n300rt-2.1.6` | `[0x3f90, 0x66570)` | `0x3f90` | `0x66570` |

**Jaccard has a length term and containment does not**, and control `C6`
measures it rather than arguing it: delete a known 20 % of one file's tokens, and
containment holds at 0.998 while Jaccard falls to **exactly the ratio of the two
k-gram set sizes**, 0.797 against 0.800.

🔄 **The first draft of this paragraph got that term wrong, and the corpus says
so.** It read *"the corpus spans 400,424 to 526,732 bytes, a factor of 1.32, and
Jaccard's denominator carries that 31 %"*. Jaccard's denominator is a k-gram
**union**, not a byte count, and on this corpus the two point in opposite
directions: measured, `|G(7)|` spans 28,887–33,763, a factor of **1.169**, and it
**anti-correlates with file size** (Pearson **−0.78**) because the two *smallest*
`boa` carry the two *largest* feature sets — 400,424 B → 33,665 grams against
485,012 B → 28,887. Nor is that a window artefact: the windows span a factor of
1.301 and the smallest still carries the largest set. The mechanism is real and
`C6` demonstrates it; the arithmetic transfer from bytes to features was
invented.

**Registers and immediates are dropped.** Every build relocates, so a token
carrying an address makes the score a function of the linker's arithmetic. What
is left is the operation identity.

**`0x00000000` is `nop`, not `sll`, and a COP*z* `rs` field is a function
selector, not a register.** The second is 2026-08-27's COP3 correction
(`SPEC.md` `TC-08`), reused rather than made wrong a third time — `hazlint` and
`opcount.py` both carried `0x13 = COP1X` until that day.

## Choosing `k`, and why it is not 4

The rule was written before the numbers, reads only anchors whose answer is
known in advance, and is re-run by control `E6` on every corpus run rather than
trusted to this paragraph:

> **NULL** — the word-permutation of a corpus binary (the identical instruction
> multiset, in a destroyed order) must score **< 0.05**, the same five
> percentage points the plan already calls indistinguishable. *Lower bound.*
> **SENSITIVITY** — a corpus binary with 1 % of its code words replaced at
> random must still score **≥ 0.50**. *Upper bound.*
> **IDENTITY** — `acltd` across the six trees, and the byte-identical busybox
> pair, must stay exactly 1.0. *True at every k.*
> `k` := the smallest value satisfying all three for **every** binary in the
> corpus.

**`k = 4` — the value a reader would expect — fails the null by a factor of
nine.** Measured on `unit-2018/bin/boa`:

| k | null (word-permutation) | sensitivity (1 % replaced) |
|---:|---:|---:|
| 4 | **0.4398** | 0.9832 |
| 5 | 0.3393 | 0.9760 |
| 6 | 0.1594 | 0.9663 |
| **7** | **0.0414** | **0.9563** |
| 8 | 0.0067 | 0.9475 |
| 12 | 0.0000 | 0.9112 |

The mechanism is in the counts: the token alphabet is **52**, and 96,490
windows produce only **7,333 distinct 4-grams** (7.6 %) against **28,887
distinct 7-grams** (29.9 %). At k=4 the features are mostly shared compiler
idioms, so any two MIPS binaries from this vendor share about half of them.

The choice is stable. Over five shuffle seeds and eight of the twelve
binaries, the null at k=7 is **0.0023–0.0430** (every one under 0.05) and at
k=6 is **0.0252–0.1618** (several over it). The tool's own `E6`/`E6b` re-derive
it across all twelve at one seed: 0.0027–0.0418 at k=7, 0.0263–0.1580 at k=6.

**And the matrix's ordering is not stable at every k, which has to be said
rather than left for a reader to find.** `--corpus --sweep` prints the top cell
of the `boa` matrix at each k:

| k | span | lowest cell | top pair |
|---:|---:|---:|---|
| 1 | 0.040 | 0.960 | `v2.1.2`/`n300rt-2.1.6` 1.0000 |
| 3 | 0.444 | 0.550 | **`n300rt-3.4.0`/`v3.4.0`** 0.9938 |
| 4 | 0.596 | 0.394 | **`unit-2018`/`n200re-3.2.0`** 0.9905 |
| 5 | 0.754 | 0.236 | `v2.1.2`/`n300rt-2.1.6` 0.9894 |
| **7** | **0.928** | **0.058** | `v2.1.2`/`n300rt-2.1.6` 0.9863 |
| 16 | 0.964 | 0.005 | `v2.1.2`/`n300rt-2.1.6` 0.9693 |

At `k ≤ 4` the top pair moves; from `k ≥ 5` it does not. That instability sits
**entirely inside the region the null already excludes** — at k=4 a
word-permutation still scores 0.44, so the metric there is not ranking by
structure and its ranking should not be expected to hold. The two facts agree,
and the agreement was not arranged: the null was measured before the sweep was
run. But "the conclusion does not depend on k" is only true above the value the
null picked, and stating it unqualified would be wrong.

The `lowest cell` column is the saturation made visible: at k=1 the *least*
similar pair in the corpus still scores 0.96.

## Is the window actually code?

`E4` covers only the ten files that kept a section table. For the other eight
the check is a **decoding invariant, not a frequency**: MIPS `j`/`jal` carry a
26-bit word target, so a random word points somewhere in a 256 MiB range and has
about a 0.2 % chance of landing in a 500 KiB segment. In code essentially all of
them do.

| region | `j`/`jal` words | fraction targeting the executable segment |
|---|---:|---:|
| inside the window (12 files) | 529 – 13,239 | **0.99973 – 1.00000** |
| the 4 KiB after it | 11 – 45 | 0.000 – 0.043 |
| the same window read 2 bytes misaligned | 3 – 806 | 0.000 – 0.098 |

🔄 **Not 1.000 — 48,709 of 48,713.** The four exceptions are all the same word,
`0x0c000000` = `jal 0x0`, two each in `n300rt-3.4.0` and `v3.4.0`'s `busybox`,
at `0x403c80`/`0x403ccc` and `0x403cd0`/`0x403d1c`. They are **instructions, not
data** — each has a live delay slot and sits behind a `lui`/`addiu`/`beqz` null
guard, which is the shape of a weak symbol that was never relocated. So the
per-file assertion is `>= 0.99` rather than equality, and the reason is named
rather than the threshold being loosened until it passed.

The misaligned read is the negative control on the control: without it the
invariant would be a check nobody had shown could fail. Every file in the
corpus is covered by `E4` or `E4b`, and the tool asserts that rather than
leaving it to be counted by hand.

## The three anchors that came free with the corpus

**`bin/acltd` is one sha256 in all six trees** — 10,032 bytes, `.comment`
`GCC: (GNU) 3.2.3-1.2.11` and `3.3.2`, a prebuilt blob carried unchanged across
five years and three product lines. It is a real-material identity anchor, and
it is also the positive control on the plan's own void verdict: its fifteen
cells span exactly zero, so the verdict **must** fire on it. A verdict that
never fires is not a verdict.

⚠️ It is also the trap in this corpus. `grep 'GCC: (GNU)' unit-2018/` answers
**3.2.3-1.2.11**, and that is `acltd`'s compiler, not this unit's. Of the six
trees only the two from 2015 and 2016 still carry a `.comment` for their own
`boa`, and it reads **`GCC: (GNU) 4.4.5-1.5.5p2`** — the same value `TC-01`
already holds from the kernel banner, now from a second artefact. The other four
were stripped of section headers and lost it.

**The eight-byte busybox pair.** `v2.1.2` and `n300rt-2.1.6`'s `busybox` differ
in exactly eight bytes, all of them digits in the BusyBox banner's build date
(`LOG.md` 2026-08-27). Their **code windows are byte-identical** — 238,144
bytes, sha256 `c17788fdb20ba0b9…` both — and the banner is in `.rodata`, outside
the window. So the code channel says **1.0000** and the strings channel says
**0.9972**, and that split is control `E2b`: two channels that never disagreed
would be one channel counted twice.

**The container format**, which partitions the corpus with no similarity metric
at all:

| group | trees | `e_flags` | phdrs | `DT_MIPS_PLTGOT` | section table | `DT_NEEDED` |
|---|---|---|---:|---|---|---|
| 1 | `v2.1.2`, `n300rt-2.1.6` | `0x1007` … **pic** … | 8 | no | **yes** | 3 |
| 2 | `unit-2018`, `n200re-3.2.0` | `0x1007` … **pic** … | 8 | no | no | 3 |
| 3 | `n300rt-3.4.0`, `v3.4.0` | `0x1005` (no pic) | 10 | **yes** | no | 5 (+`libcjson`, `libmtdapi`) |

That is **2+2+2**, read by a different instrument from a different part of the
file, and it is the same 2+2+2 `notes/lwl-mystery.md` gets from unaligned
instruction counts (176 / 144 / 0). `SPEC.md` `TC-04` already held the `e_flags`
half of it.

⚠️ **The matching partition is `boa`'s, and stating it unscoped would be wrong.**
On `busybox` — the corpus's other subject — `binsim` gives **4+2**, not 2+2+2:
groups ① and ② merge at containment 0.9995–1.0000 against 0.165 to group ③,
because BusyBox 1.13.4 was rebuilt from the same source with the same toolchain
across 2015, 2016 and 2018. That is not two instruments disagreeing; it is a
fact about the two programs. `boa` was maintained across those years and
`busybox` was not.

🆕 **`R2a/b/d-1` turns that from two numbers into one mechanism.** The toolchain
axis is 4+2 — `busybox` says so, and so does `G(boa_t) & G(busybox_t)` compared
between trees, which attenuates the same-program comparison rather than being
free of it -- `notes/which-drop.md` §3 owns that correction.
`boa`'s extra split is `boa`'s own source revision plus a post-link strip of the
section header table, which changes no code byte. So 2+2+2 and 4+2 are one
partition seen through a program that changed inside the era and one that did
not. `notes/which-drop.md` §3.

⚠️ **What that agreement is worth, stated narrowly.** These three are not
independent *evidence*: they are three consequences of the same build changes,
so of course they line up, and nothing here is three separate confirmations of
one fact. What the agreement does buy is the thing this step needs — **no single
instrument's error explains the partition.** If `binsim`'s window were drifting
into `.rodata`, or its tokens were collapsing, the clusters it produced would
have to coincide with a partition read from ELF headers it never touches. So the
clustering is not an artefact of the metric. That is a claim about instrument
error, not about the world, and it is the only one the agreement supports.

## What does not go in the corpus, and why the rule is now machine-checkable

The corpus had six trees and no stated membership rule, which is fine until
someone offers a seventh. One was offered the same day:
`TOTOLINK-N350RT_V9.3.5u.6466_B20250825`, a 2025 release, neighbouring model
number, and on its face an attractive sample — a fourth product line and five
years past the newest tree, which is exactly the axis this corpus is short of.

量 2026-08-27, and it is not the same machine:

| | this unit | N350RT V9.3.5u |
|---|---|---|
| container | Realtek loader image | **U-Boot uImage** (`27051956`), name `C8351R-6466` |
| SoC | Realtek RTL8196E, Lexra-family core | **MediaTek MT7628** |
| `/bin/busybox` | ELF32 **MSB**, MIPS-I, `e_flags 0x1007` | ELF32 **LSB**, **MIPS32 rel2**, `0x70001007` |
| kernel | Linux 2.6.30.9, gcc 4.4.5-1.5.5p2 | Linux 3.4.113, gcc 4.4.7 |
| libc | uClibc 0.9.30.3 | uClibc 0.9.33.2 |
| web server | `boa` | **lighttpd** — there is no `boa` in it |

Different endianness, different ISA level, different SoC vendor, different
bootloader, different kernel line, and no comparable program. `binsim.py`
refuses it before scoring — `ELF data 1, not MSB (big-endian)`, exit 2 — which
is the `A2` refusal path exercised on real material for the first time.

**The useful part is what it changed.** The parser's endianness check happens to
catch this one, but it would *not* catch a **big-endian MIPS32r2** part, which
would parse, score, and quietly move `FLOOR`. So the membership rule is now
control `E0`: every sample in the corpus must carry the same `EF_MIPS_ARCH`
field, and a mixed corpus is refused with the odd one named. The rule lives in
the tool instead of in someone's memory, and `tools/test-binsim.sh` builds a
deliberately mixed corpus to show `E0` going red.

Recorded rather than discarded: *"we looked and it is a different part"* is a
result, and the model numbering does not imply a shared platform.

## Measured — the instrument's discrimination

`binsim`, containment of code 7-grams, `boa`, six trees ordered by build date:

|  | v2.1.2 | n300rt-2.1.6 | unit-2018 | n200re-3.2.0 | n300rt-3.4.0 | v3.4.0 |
|---|---|---|---|---|---|---|
| **v2.1.2** | — | 0.986 | 0.886 | 0.877 | 0.060 | 0.058 |
| **n300rt-2.1.6** | 0.986 | — | 0.895 | 0.885 | 0.060 | 0.059 |
| **unit-2018** | 0.886 | 0.895 | — | **0.982** | 0.066 | **0.065** |
| **n200re-3.2.0** | 0.877 | 0.885 | 0.982 | — | 0.068 | 0.067 |
| **n300rt-3.4.0** | 0.060 | 0.060 | 0.066 | 0.068 | — | 0.974 |
| **v3.4.0** | 0.058 | 0.059 | 0.065 | 0.067 | 0.974 | — |

| | span of the 15 cells | verdict |
|---|---|---|
| `boa` | **0.9279** (92.8 pp) | discriminates |
| `busybox` | **0.8354** (83.5 pp) | discriminates |
| `acltd` | **0.0000** | **void — and that is the control** |

**Reproducibility error: 8.0e-4, estimated — and the first version of this
paragraph was circular.** It read *"noise floor 0.0000: sixteen pairs have
byte-identical code windows and every one scores exactly 1.000, so the
reproducibility error is zero, not small"*. Those pairs are **selected by**
byte-equality of the very window that is then scored, so 1.000 is arithmetic and
not a reading — forced for any deterministic set-valued metric at any `k`. The
control that asserted it could not fail, and the guard it fed (`BASE − FLOOR`
must exceed the noise) had its bar pinned at zero.

Two things replace it. The falsifiable half of `E2` is now the **converse**: no
pair whose windows *differ* may reach Jaccard 1.0 — which a collapsed tokeniser
or a saturating `k` would break. And measuring reproducibility needs two builds
of one source whose windows are **not** identical. The tightest the corpus has
is `busybox` `n300rt-2.1.6` against `unit-2018`, same BusyBox 1.13.4, windows
two words apart, **Jaccard 0.999196**.
🔄 **"The corpus has one" was wrong, and the code never agreed with it.**
`report_corpus` collects every non-identical same-program pair at Jaccard ≥ 0.99
and takes the **minimum**; 讀, that set has **three** members and they run
8.04e-4 to 4.28e-3 — a factor of 5.3. Taking the minimum is the anti-conservative
end of an error bar, so the tool prints the whole range now and the guard still
uses the tightest, which is the harder bar for `BASE − FLOOR` to clear (1025×
against the floor `R2a/b/d-1` named).
⚠️ Calling those two "one source" is **推**, inferred from the banner and the
window length; it is not 量, and the tool prints it as an estimate.

⚠️ **And containment saturates.** Seventeen cells reach containment exactly
1.000 while only sixteen pairs are byte-identical. The extra one is `busybox`
`unit-2018`/`n200re-3.2.0`: n200re's 40,915 7-grams are a strict subset of
unit-2018's 42,297, Jaccard 0.9673. **Containment 1.000 does not mean
identical** — the second time in this file that `min()` in the denominator has
turned out to be doing something worth naming.

### A second implementation, sharing no code with the first

Twenty-nine controls check that `binsim` is self-consistent. None of them can
say whether the whole file is wrong in one direction. So the headline numbers
were recomputed by a second program that shares nothing with it: the code window
comes from parsing `readelf -dW`/`-lW` **text** rather than from unpacking the
program headers; k-grams are Python tuples in a set rather than 64-bit FNV
hashes; and the tokeniser was written again from the MIPS encoding.

| | second implementation | `tools/binsim.py` |
|---|---|---|
| `BASE` / `FLOOR` / `CROSS` | 0.9818 / 0.0650 / 0.1581 | identical |
| span, `boa` / `busybox` / `acltd` | 0.9279 / 0.8354 / 0.000000 | identical |
| null at k=7, three seeds | 0.0405 – 0.0416 | 0.0414, inside it |
| null at k=4 | 0.4330 – 0.4398 | 0.4398 |
| alphabet / distinct 4-grams / 7-grams | 52 / 7,333 / 28,887 | identical |

Not committed — it is a throwaway written to disagree, and its value was in the
disagreeing. It did not.

The three container groups are the three clusters, and the clustering agrees
with two instruments that are not this one. **Which of them this firmware was
built from is `R2a/b/d-1`** — `notes/which-drop.md`, done the same day.

🔄 **The sentence that used to close this paragraph was wrong, and the corpus
refutes it.** It read *"date, product line and SDK generation are confounded in
this corpus in a way no function of two binaries can separate"*. 讀 2026-08-27
from `/etc/version` in each tree: **product line is crossed with the clustering,
not confounded with it.** N150RT appears in all three clusters and N300RT in
two; two *different products* inside one cluster score 0.9863 and 0.9818, while
two builds of *the same product* across clusters score 0.0650. The vendor's own
version number is refuted the same way — this unit and `n300rt-2.1.6` are both
stamped V2.1.6 and land in different clusters: their cell is 0.8951, the highest
between-cluster cell there is, and still below the lowest within-cluster one. What remains collinear is date and SDK
generation, which is a tautology rather than a confound. `notes/which-drop.md`
§2 owns that reading.

## What it refuted: the plan's own `FLOOR`

```
BASE   binsim(unit-2018, n200re-3.2.0)          0.9818
FLOOR  binsim(unit-2018, v3.4.0)                0.0650
CROSS  binsim(unit-2018/boa, unit-2018/busybox) 0.1581   <- a DIFFERENT PROGRAM
```

**`FLOOR` sits below `CROSS`.** This unit's `boa` shares fewer 7-grams with the
2020 `boa` than with the `busybox` on its own rootfs. The plan's rule is *pass
at or above `BASE`, warn between, fail at or below `FLOOR`* — so a rebuild
scoring anywhere in `[0.0650, 0.1581)` would be "warn" while being less like
this unit's `boa` than a completely different program is. The warn band swallows
the whole no-evidence region.

`CROSS` is 0.1132–0.1581 across all six trees, so it is a property of the
corpus and not of one pair.

The mechanism is named rather than guessed: `boa` is `pic` through 2018 and not
`pic` from 2019 (`TC-04`), and dropping PIC rewrites every function prologue and
every call in the image, while `boa` and `busybox` on one rootfs share a
compilation model.

🔴 **All of that holds on the code channel, and the second channel reverses it —
which is the strongest thing this corpus says about keeping the two apart.**
Measured, containment on both:

| | code | strings |
|---|---:|---:|
| `BASE` unit-2018 / n200re-3.2.0 | 0.9818 | 0.9913 |
| `FLOOR` unit-2018 / v3.4.0 | **0.0650** | **0.6629** |
| `CROSS` unit-2018 boa / busybox | **0.1581** | **0.0515** |

On strings the ordering inverts by a factor of **13**: the `FLOOR` pair shares
two thirds of its strings — it is the *same program*, `boa`'s own HTML and error
text — while `CROSS` shares 5 %, which is libc symbol names and little else. So
the first draft's summary, *"`FLOOR` is not 'a different SDK'; it is 'no
relationship'"*, is **wrong**. The accurate statement is narrower and more
useful: **on the code channel the `FLOOR` pair scores below an unrelated
program, so the plan's warn band carries no information** — and the pair is not
unrelated, it is one program whose code was rewritten between SDK generations
while its content survived. A single blended score would have averaged 0.065 and
0.663 into a number describing neither.

`tools/binsim.py --corpus` printed this as `REFUTED` and exited 1 rather than
quietly substituting a better number, because naming a replacement floor was
`R2a/b/d-1`'s decision.

🆕 **`R2a/b/d-1` named it the same day, and its first answer was wrong too:**
`@floor busybox unit-2018 v3.4.0` = 0.1646, clearing `CROSS` 0.1581 by 0.65 pp.
An adversarial review killed it. **Containment divides by the smaller feature
set** — busybox's is 42,297 grams against boa's 28,887 — so the two numbers were
read at different denominators, and 讀 at a matched one the ordering reverses:
a pair sharing its whole upstream source across the model change scores 0.1212,
*below* the 0.1551–0.1581 a pair sharing no source reaches. The floor is now the
`CROSS` cell itself, `@floor boa unit-2018 busybox unit-2018` = 0.1581, in a
five-field cross-program form the manifest grew for it.
**`notes/which-drop.md` owns the decision, the alternatives it rejected, the
`VOID` precondition that falls out of it, and what it makes `R2a/b/d-4` do; the
cell itself lives in `tools/binsim-corpus.tsv`.** This note stops at "the plan's
floor was refuted", which is what it measured.

## Refutation conditions, written before the run

> **The metric has no discrimination** if the fifteen pairwise scores span less
> than five percentage points. Measured: 92.8 pp on `boa`, 83.5 pp on `busybox`
> — and **0.0 pp on `acltd`**, where it correctly fires.

> **The metric is not measuring structure** if it does not put the
> byte-identical pair at exactly 1.0, or if a byte-permutation or a
> word-permutation of a real binary scores above the null. Measured: 1.000,
> 0.0000, 0.0414.

> **The metric is measuring "is a MIPS binary from this vendor"** if two
> different programs from one tree score as high as two builds of one program.
> Measured: `CROSS` 0.158 against `BASE` 0.982 — but **also against `FLOOR`
> 0.065, which it exceeds**, and that half is the one that came out wrong.

## What this establishes, and what it does not

**Established, read out of the binaries.** A metric exists whose null is under
5 pp, whose identity anchors are exactly 1.0, whose length term is measured
rather than assumed, and which reproduces a 2+2+2 partition that two other
instruments already give. The plan's `FLOOR` is below the score of an unrelated
program and cannot carry the decision rule built on it.

**Not established.** Which drop built this firmware — that is `R2a/b/d-1`,
`notes/which-drop.md`, and its answer is that a matrix over six *shipped images*
cannot name a *source and toolchain release* at all: `TC-02` stays **推**.
Whether a *rebuild* clears `BASE` — that is `R2a/b/d-4`, and it needs the
container in `R2a/b/d-3` first. And nothing **in a single cell** separates
toolchain from config: a high score is evidence of shared source **and**
toolchain together and cannot attribute the share to one of them.

🔄 **That last sentence was stated too broadly, and the corpus is what narrows
it.** It is a property of one cell, not of the corpus. `busybox` is one upstream
source held constant across all six trees (讀), so its cells move only when the
toolchain does — and on the ① ↔ ② edge they do not move (0.9995–1.0000) while
`boa` drops eleven points (0.877–0.895). On that edge the two halves *are*
separated, and the answer is that `boa`'s source moved and the toolchain did
not. On the ② ↔ ③ edge both move together and nothing separates them.
`notes/which-drop.md` §3 owns that, including the third instrument it turns on —
`G(boa_t) & G(busybox_t)`, which reads the toolchain axis without putting two
builds of one program side by side, and gives the same 4+2 with a ninefold gap.

**A caveat that belongs to the instrument.** The window is scanned linearly at
4-byte alignment, so literal pools and jump tables inside it are tokenised as
instructions. That is a superset, it is the same trade `opcount.py` documents,
and it biases both files of a pair the same way.

## Where the first version was wrong

Six, and every one of them was caught by a control rather than by reading:

1. **`k` defaulted to 4**, which fails the null by a factor of nine. The
   word-permutation control is what said so; nothing in the matrix looked wrong.
2. **The window-is-code control counted zero words as instructions.** Primary
   opcode `0x00` is `SPECIAL`, so a run of padding scored 100 % "code-like" and
   `acltd`'s `.rodata` read 0.816. Replaced with the `j`/`jal` target invariant,
   which has a twentyfold margin instead of a marginal one.
3. **The symmetry control could not fail.** Its two fixtures had the *same*
   number of distinct k-grams, so an asymmetric containment was invisible
   between them. The M9 mutation found it; the control now uses two fixtures of
   deliberately unequal size and asserts they are unequal.
4. **`E2` asserted the eight-byte pair was "the top busybox cell"** — undefined,
   because several cells are 1.0000. Restated as a property derived from the
   material: every pair with byte-identical code windows must score exactly 1.0.
5. **The suite's skip label said 7 cases where the section had 8.** The census
   arithmetic caught it — 48 + 7 ≠ 56 — which is the failure mode `ci-census.py`
   exists for, on its first exposure to a new suite.
6. **The plan's `/dev/urandom` negative control is the weak one**, because
   random bytes differ from a MIPS binary in *byte frequency* as well as in
   structure. It is kept, under `--urandom`, beside two stronger ones.

### And then the whole day went to an adversarial review, which took twelve more

Six lenses over the diff, each finding handed to a dedicated skeptic told to
refute it: **30 agents, 24 findings raised, 22 survived their refuter.** Every
one below was reproduced here before it was acted on, and two of the three
biggest are things this note *asserted*.

| | what the first version got wrong | how it was caught |
|:-:|---|---|
| 7 | **"Noise floor 0.0000"** was circular — see above. The control feeding it could not fail and the guard it fed had its bar pinned at zero | a reviewer noticing that `E2` selects its pairs *by* the equality it then asserts |
| 8 | **"`FLOOR` is not 'a different SDK'; it is 'no relationship'"** — refuted by this tool's own second channel, 0.6629 against `CROSS` 0.0515 | running the strings channel on the pair the note never quoted it for |
| 9 | **The `j`/`jal` table said 1.000.** It is 48,709 of 48,713 | counting them instead of reading the summary |
| 10 | **"Jaccard's denominator carries that 31 %"** transferred a *byte* span onto *feature-set* sizes, which anti-correlate with it (r = −0.78) | measuring `|G(7)|` instead of assuming it tracked file size |
| 11 | **"2+2+2" was stated unscoped.** It is `boa`'s partition; on `busybox` this metric gives 4+2 | running the same clustering on the corpus's other subject |
| 12 | **Three mutants survived all 65 cases**: `_perturbation` could be a no-op and the sensitivity anchor would still read green; `C6` could not tell Jaccard from overlap-over-max; and `DEFAULT_K` could be set to 4 — the value declared to fail the null ninefold — with every CI-visible case still passing. `C10`, `C11`, `C12` are the three controls that now fail | a reviewer asked to *build* a surviving mutant rather than to reason about one |
| 13 | **A blank line in `SPEC.md` put `TC-09`/`TC-10`/`TC-11` outside the table**, so `spec-check.py` never parsed them — 300 rows where there are 303 — and reported green | mutating a new row and watching the tool stay silent |
| 14 | **The manifest hash ran *after* the ELF had been parsed**, while `binsim-corpus.tsv` told the reader the opposite; and a corpus file truncated in its **body** died inside `tokenize` with an uncaught `struct.error`, exiting 1 — the code reserved for "reported, but a result is void" | reading the order rather than the comment |
| 15 | **`D1` guarded a two-line helper no production path called.** The real check was inline and untested by any control | `grep` for the helper's only other caller |
| 16 | **`tools/binsim-corpus.tsv` was opened by no code path a runner could reach.** `@floor` could have been misspelled for months | asking which committed file CI actually parses |
| 17 | **`--fingerprint` had no case at all**, and printed `squashfs-root` as the label for every row of the corpus | opening the mode and looking at it |
| 18 | **"within ten minutes of every binary's mtime in all six trees"** — it is 2m02s to 1h48m02s; `v3.4.0` is the outlier | measuring all six instead of the one that prompted the sentence |

Two findings were refuted and are recorded because they were: that `E6` checks
its sensitivity leg on one binary of eighteen (it does, and that is the anchor's
definition, not a gap), and that `CROSS` is not the corpus's highest
cross-program score (a third program reaches higher, but it is the identity
anchor, which cannot be a comparand).

**One finding is acknowledged and not fixed.** `tools/ci-expected.tsv` allow-lists
two skips whose own reason column says they must not appear on a runner
(`test-opcount`'s fixture, `test-gitignore`'s symlink). The census credits them
anyway, so a silently missing apt package would keep the badge green. That is a
pre-existing property of a file this step did not set out to change, it needs
its own `must-not-appear` column in `ci-census.py`, and inventing one at the end
of an unrelated session is how a gate acquires a rule nobody remembers. It is on
the list in `PROGRESS.md` § Next after this.

And one defect this work found in a neighbouring tool: `ci-census.py`'s case
regexes were anchored `^\s*`, so a tool a suite *invokes* had its control lines
counted as the outer suite's cases. `test-rlxprobe.sh` re-indents `hazlint`'s
twelve controls into its stdout, and with the cross compiler present the census
read 116 ok / 107 FAIL against a bench total of 202 and reported cases as
missing. It never fired in CI, which does not install that compiler — so the
101/101 configuration `ci-expected.tsv` documents in that suite's own row was a
number the census could not reproduce. Anchored at exactly two spaces now, with
`C11`/`C11b` as the control; the census reads 101 + 101 = 202 there.
