# What a digest over this unit's flash may say, and over which bytes

Owner of one question: **`flashwin` refuses to print a sha256 over any window
overlapping `H601`, and `SPEC.md` `FLS-14` has printed a sha256 over the whole
4 MiB — which contains `H601` — since 2026-08-24.** Both cannot be right for
the same reason, and until 2026-09-07 nobody had asked which.

It was asked because `R5-5`'s DoD needs a digest. Everything here is desk work
on the committed record and on `$FWRE_WORK/dumps/flash-n150rt-console-2.bin`;
no power was used and no flash byte was written.

**Containment for this whole file: offsets and counts only, never a byte
value.** That is `FLS-21`'s discipline and `FLS-22`'s, and it is what makes the
answer writable down at all.

---

## 1. The rule, asked of the enforcer rather than of the prose

`tools/flashwin.py` withholds a digest for a window overlapping `FORBIDDEN`,
and states its reason in the code:

> A digest over a window whose only unknown is 24 bits of MAC is
> brute-forceable by anyone who knows the format, so publishing one publishes
> the address.

**量 2026-09-07**, by calling `flashwin.overlaps_forbidden()` on four windows
rather than reasoning about what it would say:

| window | bytes | verdict |
|---|---:|---|
| `0x000000` the whole image | 4,194,304 | **REFUSED** (`H601`) |
| `0x006000` the `FLS-20` window | 256 | **REFUSED** (`H601`) — the known-fires control |
| `0x008000` everything above `H601` | 4,161,536 | digest printed |
| `0x000000` the loader region alone | 24,576 | digest printed |

So the rule does fire on the whole image. The second row is the positive
control: a rule that refused nothing would make this table meaningless.

## 2. What is already committed

| where | form | bits |
|---|---|---:|
| `LOG.md:87` | full 64 hex | 256 |
| `tools/leakscan.py:137` | full 64 hex, split across two literals | 256 |
| `SPEC.md:178` (`FLS-14`) | `a800059a…10f37ea` | 60 |
| `RUNSHEET.md:13`, `:401`, `notes/leak-surface.md:79` | `a800059a` | 32 |
| `bench/2026-08-24c/PREDICTIONS-block5.md:39` | `a800059a9b8c414d` | 64 |

🔴 **Eliding is not mitigation.** `FLS-14`'s 60-bit form distinguishes a set of
2^24 candidates with a false-positive probability of 2^24 · 2^-60 = **2^-36**.
A truncated digest is the same verifier as a full one at these scales, so
"shorten it" is not one of the available repairs.

🔴 **And `flashwin scan` structurally cannot see any of this.** `scan` asks
whether a committed file contains *the bytes of* a forbidden window; a digest
contains none of them. 量 2026-09-07: `--sweep . --exclude upstream` reads
**2,497 files, 113 probes, CLEAN**, with `LOG.md` and `tools/leakscan.py` both
in the swept set. That is `scan` working correctly on the question it asks, and
it is a different question from the one this file is about.

## 3. Whether the reason transfers, and the honest answer

`flashwin`'s reason is a **conditional**, and its antecedent is *"with the rest
of the window known"*.

**At 256 bytes the antecedent holds.** The complement is 250 bytes of a page
that is 98.22 % one repeated value (量, re-derived below), and `FLS-22` measured
that at least 45 of `H601`'s 146 non-zero bytes are recoverable from the public
`upstream/` tree. So the rule is right, and its behaviour must not change.

**At 4 MiB the antecedent is undecided, and undecidable with one device.** The
complement is 4,186,112 bytes including the entire firmware region. Deciding
whether an attacker knows it would need a second unit's dump — and *one device,
no spare* is the first line of `CLAUDE.md`.

Widening a digest is monotone: every added byte is either known to the attacker
(adds nothing) or unknown (adds entropy), so

> H(4 MiB | attacker) ≥ H(256 B | attacker)

and a 4 MiB digest is **never easier** to brute-force than the 256-byte one.
⚠️ *Never easier* is not *hard*, and this file does not pretend otherwise.

**What actually makes `FLS-14` safe today is not width — it is `FLS-22`.** The
MAC's value is already public by an owner's decision taken 2026-08-30 and
re-affirmed 2026-09-02. A digest cannot publish an address that is already
published. 🔴 **That makes `FLS-14`'s printability conditional on `FLS-22`
standing, and before today neither row mentioned the other.** Both now do.

⚠️ **Two futures reopen it**, and they are written here so they are not
discovered later: `upstream/` going private, and `R9`'s differential proof
publishing enough to rebuild the firmware region byte-exactly. Either would
make a 2026-08-24 commit into a verifier retroactively.

## 4. The decision, and why the rule does not change

🟢 **`flashwin`'s behaviour is unchanged; its scope is written down.**

Refusing is never wrong — it is the conservative direction. And an enforcer
that had to evaluate *"is the complement known?"* would be an enforcer with a
judgement call inside it, which is the exact property that moving the `apt`
rule and the changepoint convention out of prose and into code was meant to
remove. `flashwin` governs **windows read at the bench**. The whole-image
digest is `FLS-14`'s, its precondition is `FLS-22`'s, and the two rows now
carry that coupling.

🔴 **What this repository still does not have**: anything that checks whether a
committed file contains a *digest of* a forbidden window. `scan` reads bytes,
`leakscan` reads address shapes, `audit-bench-log` reads topic keywords — all
three are blind to a hash. Carried forward as `FLW-1`, with its positive
control already fixed: **the instrument must report `LOG.md:87` on its first
run, and must not report the complement digest of §5.** An enforcer built in
the same hour as the decision it would have flagged has no independent control,
which is why it is not built today.

## 5. The digest `R5-5` can actually use

The complement of `H601` is two contiguous pieces, and `flashwin` prints a
digest for each of them (§1, rows 3 and 4 in spirit; measured directly as
`overlaps_forbidden` → `False` on both).

```
[0x000000, 0x006000) ∪ [0x008000, 0x400000)   4,186,112 bytes = 99.8047 %
sha256  a9916fd8…4ce3cba
```

**量 2026-09-07** on `flash-n150rt-console-2.bin`, whose whole-file sha256 was
re-derived in the same run and matches `FLS-14` exactly. The elided form is
deliberate and follows `FLS-14`'s own style; the full value is recomputable by
anyone holding the dump, which is the only place it can legitimately come from.

⚠️ **The 8,192 bytes this leaves out are 0.1953 % of the flash, and leaving
them out is a rule, not a failure.** Their verification stays where it already
is — the `FLR` bracket, which compares without printing, exactly as `flashwin`
prescribes: *"The verdict is what gets written down: this file against the
round-A file, cmp, same/differ."*

## 6. Re-derived, not requoted

`FLS-22` and `flashwin`'s comments both state figures about `H601`. 量
2026-09-07, computed from the dump in this session rather than read off those
rows:

| | this session | the row it agrees with |
|---|---|---|
| `H601` size | 8,192 bytes | — |
| non-zero bytes | **146** | `FLS-22` |
| distinct byte values | **40** | `flashwin` §probe-set comment |
| most common value's share | **98.22 %** | `flashwin` §probe-set comment |

Three independently stated numbers, three agreements. The point of re-deriving
is that a fourth reader should not have to trust the third.

## 7. Six re-reads of the two regions that may never be written

Found while asking §3's question: `$FWRE_WORK/dumps/` holds six files named
`config-region-*.bin`, and 🔴 **the name is wrong**. Every sidecar says
`"flash_offset": 0, "length": 65536`, so each is a re-read of
**`0x000000`–`0x00FFFF`** — the loader region, `H601`, and the first 32 KiB of
the firmware image. Two of them are byte-identical to the 2026-08-16 dump's
first 64 KiB, which means **two files named `config-region-*` hold this unit's
MAC**. They are outside this repository and stay there; the hazard recorded
here is that a hand reasoning from the filename would mishandle them.

量 2026-09-07 against `flash-n150rt-console-2.bin[0x000000..0x00FFFF]`, two
tools agreeing (`cmp -l | wc -l` and a Python byte loop):

| re-read | loader `0x0000`–`0x5FFF` | `H601` `0x6000`–`0x7FFF` | fw head `0x8000`–`0xFFFF` |
|---|---:|---:|---:|
| 2026-08-17 07:33 | 0 | 0 | 0 |
| 2026-08-17 11:02 | 0 | 0 | 0 |
| 2026-08-17 post | 0 | 0 | 14,068 |
| 2026-08-18 19:27 | 0 | 0 | 14,206 |
| 2026-08-19 02:30 | 0 | 0 | 54 |
| 2026-08-19 w07close | 0 | 0 | 14,104 |

🟢 **Neither protected region moved by one byte, and every changed byte landed
above `0x008000`.** ⚠️ *`CLAUDE.md` records two upstream flash writes in this
window; that count is quoted, not measured here.* What IS measured is that the
firmware head takes at least **three** distinct states against the reference —
0, ~14,100, and **54** — so the 2026-08-19 02:30 read had come back to within 54
bytes of the 2026-08-16 dump after differing by 14,206 the evening before. The
region was written and then largely restored, which a count of writes hides.

This is **full 8,192-byte** coverage of `H601`, six times. `CLAUDE.md` records
`upstream/BENCH-LOG.md` as holding *"seven baselines of `H601`'s first 4 KiB
across three days"* — this is a different artefact set, twice the width.

⚠️ **What it is not.** Six readings from one instrument (`console-dump.py`, one
port, one baud) are not six instruments. All six predate rlxfw's first
power-up, so this says nothing about any seating of this project, and it does
**not** move `FLS-19`/`FLS-20`'s bracket or make `G8b`'s sentence sayable:
those need a full re-dump, and none ran. What it does is bound where that era's
writes landed, which no row here had.

⚠️ And it is **not** an answer to §3 either. That the firmware region is
mutable on this unit does not show its state on 2026-08-16 was unguessable —
the factory image is publicly downloadable. The antecedent stays undecided.

---

## 8. The digest was finally used, and it refuted — `FLS-26`

*2026-09-08, seating 16. §5 wrote down the digest `R5-5` could use. This is what
happened when `R5-5` used it.*

### 8.1 The reading, and why it is not the instrument

`rtl819x-spi`'s `verify` traversed all 4,194,304 bytes on the silicon and
reported `digest_bytes 4186112`, `h601_skipped 8192`, `h601_hashed 0`, and

```
d1_sha256 a16735789a3301a1a65201b912d2c42e19f1685469bd5a0adcfa55e7100d49eb
```

against §5's `a9916fd8…4ce3cba`. Three instruments could have been lying and all
three are closed by measurement rather than by argument:

1. **The constant.** The complement was recomputed at the desk from **both**
   dump files (`flash-n150rt-console-1.bin`, `-2.bin`), by an independent
   implementation, over the same scope the driver uses. Both give
   `a9916fd86adb49ff0a4f53d49bc377ca5c54321dcff02bdb55e7b4ab64ce3cba`, equal to
   §5 and to the value compiled into `rtl819x-spi.c`.
2. **The driver's digest engine and its scope.** `verify 4096`'s own digest is
   `e7d529d2…9697647d`; the dump's first 4,096 bytes digest to exactly that. The
   engine reproduces an independent implementation on real device bytes.
3. **A digest that cannot fail.** `C1-NG` injected one changed byte at 1,048,576
   and the 4 MiB digest moved to `1682557547a05ef1…`. And `C1-VF` and `C1-NF`
   are two independent full traversals returning the **identical** digest, so
   the reading is n=2.

⚠️ **The `d1_match` field has no positive control here.** It read `0` in every
cell of the seating, so nothing shows it can read `1`. The refutation rests on
the three items above, not on that flag.

### 8.2 The bisection, and the limit that comes with it

`verify <n>` hashes `[0, min(n,0x6000))` and `[0x8000, n)`, rounding `n` down to
`RTL819X_SPI_CHUNK` = 4096 (`rtl819x-spi.c:765`, `limit &= ~(CHUNK-1u)`). Nine
rungs, each compared against the dump computed to the same scope:

| `verify n` | hashed | verdict |
|---|---|---|
| 8192 … 24576 | 8192 … 24576 | SAME |
| **32768** | **24576** | **SAME** — exactly `[0, 0x6000)` |
| **36864** | **28672** | **SAME** |
| **40960** | **32768** | **DIFFERS** |
| 49152, 57344, 65536, all | | DIFFERS |

🟢 **`verify 32768` covers the whole loader region and it is byte-identical to
2026-08-16 over all 24,576 bytes.** §7's six re-reads and every `FLR` bracket in
this project combined had sampled 256 of them.

🔴 **The first difference is `[0x9000, 0xA000)` — 4,096 bytes, exactly one erase
sector**, in `mtd0`'s `"boot+cfg+linux"` immediately above `H601`.

🔴 **A prefix digest finds the FIRST difference and nothing past it.** Everything
above `0xA000` is undetermined, and this image cannot narrow it: `verify` takes a
limit and no offset, and `FW-46` measured that this image's busybox has neither
`dd` nor `md5sum`, so there is no second path. `SPEC.md` §17 owns the exit.

⚠️ **A guard earned its place here.** Nine of the finer rungs came back
`SCOPE?` rather than a verdict, because the driver's rounding made
`digest_bytes` disagree with what the desk had hashed. Comparing two digests over
different byte counts would have printed a confident `DIFFER` that meant nothing.
**The comparison refuses when the scopes differ**, and that is why the four-rung
answer above is trustworthy.

### 8.3 What this does and does not say about writes

It says flash content moved between 2026-08-16 and 2026-09-08 00:15, in at least
one erase sector, and that the loader region is not where it moved.

It does **not** say who wrote it. Not tonight: the loader entered this image
directly on all ten boots, the vendor firmware did not execute, `n_writes` read 0
in every dump, and no `FLW`/`EW`/`EB`/burn command was issued. The vendor
firmware *has* run on this part since the dump, and `[0x9000,0xA000)` is where a
vendor firmware saves configuration — **that is a hypothesis with a mechanism and
it is recorded as one, not as a reading.**

🔴 **And it moves the forbidden sentence in the harder direction.** *"Not one
flash byte is written"* was previously unmeasured; it is now **known false for the
device** over some interval, with the write unattributed. What is measured is
narrower and better: rlxfw's own driver counted zero writes, and the loader
region is intact over all of it.
