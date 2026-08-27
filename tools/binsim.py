#!/usr/bin/env python3
"""binsim -- how much code structure two builds share, with the length term measured.

Why this exists
---------------
`R2b` asks which GPL drop this unit's firmware was built from, and the plan's
answer is that the threshold has to come out of the data rather than out of me:

    BASE  = binsim(unit-2018, n200re-3.2.0)   same SDK, ten weeks apart, other product
    FLOOR = binsim(unit-2018, v3.4.0)         same product, five years, SDK generation
    pass    binsim(rebuild, unit-2018) >= BASE
    void    the fifteen pairwise scores span < 5 percentage points

The corpus refuted that `FLOOR` on `boa` and `R2a/b/d-1` replaced it with the
same two trees read on `busybox` -- see "R2a/b/d-1 named it" below.  The cell
lives in `tools/binsim-corpus.tsv`; nothing in this file chooses it.

That last line is why the controls in this file were written before any number
was reported.  A similarity metric is the easiest instrument in this project to
build so that it cannot fail: almost any function of two MIPS binaries from one
vendor returns something near 0.8, and a matrix of numbers near 0.8 reads like a
result.  So every invocation runs the controls first and refuses to print a
matrix if one of them does not hold.

What the score is
-----------------
    binsim(A, B) = |G(A) & G(B)| / min(|G(A)|, |G(B)|)

where G(X) is the set of hashed **7**-grams of normalised MIPS operation tokens
over X's code window.  Jaccard -- the same intersection over the union -- is
printed beside it on every line, never instead of it.

Four measurements forced that shape, and each one is a way this could have been
wrong:

  * **The code window cannot come from `.text`.**  Four of the six `boa` in the
    corpus have no section header table at all (`n200re-3.2.0`, `unit-2018`,
    `v3.4.0`, `n300rt-3.4.0`); `objdump -d` on them emits nothing and reports 0
    for every mnemonic, which `notes/lwl-mystery.md` already had to learn.  So
    the window is `[DT_INIT, DT_FINI)` out of `PT_DYNAMIC`, which all six have.
    The two that kept their section headers are then the parser's positive
    control: on those the derived window must equal `.init` through `.fini`.

  * **Jaccard has a length term and containment does not**, and `C6` measures
    it rather than arguing it: delete a known 20 % of one file's tokens, and
    containment holds at 0.998 while Jaccard falls to exactly the ratio of the
    two k-gram set sizes.  What this said first was that the corpus's 1.32x
    span in BYTES is what Jaccard's denominator carries, and that is wrong: the
    denominator is a k-gram union, `|G(7)|` spans only 1.169x, and it
    ANTI-correlates with file size (Pearson -0.78) because the two smallest
    `boa` carry the two largest feature sets.

  * **Registers and immediates are dropped.**  Every build relocates, so a token
    that carries an address or an offset makes the score a function of the
    linker's arithmetic.  What is left is the operation identity.

  * **`0x00000000` is `nop`, not `sll`, and a COP*z* `rs` field is a function
    selector, not a register.**  The second is 2026-08-27's COP3 correction
    (`SPEC.md` `TC-08`), reused here rather than made wrong a third time --
    `tools/hazlint` and `tools/opcount.py` both carried `0x13 = COP1X` until
    that day, and `hazlint`'s `reads()` reported hazards on registers the
    instruction never named because of it.

The negative controls, and why the obvious one is the weak one
--------------------------------------------------------------
The plan writes the negative control as *"a file against `/dev/urandom` of the
same length"*.  That control is real but it is the weakest of the three, because
random bytes differ from a MIPS binary in **byte frequency** as well as in
structure -- so a metric that had accidentally been measuring nothing but the
byte histogram would pass it.  Two stronger ones run beside it:

  * `C4` **byte-permutation** of the file itself: identical byte histogram, no
    structure.  A byte-frequency metric scores 1.0 here and is caught.
  * `C5` **word-permutation**: identical *instruction* multiset, order
    destroyed.  A pure opcode histogram scores 1.0 here.  Both halves of `C5`
    are asserted -- at `k = 1` the score must be ~1.0 and at `k = 4` it must
    collapse -- because the first half is what makes the second half mean
    something.  A metric that scored 0 on both would not be measuring order, it
    would be broken in a way that happens to look strict.

`/dev/urandom` is available as `--urandom`, but the default random control is a
seeded PRNG.  A control whose expected value moves on every run cannot be
pinned, and a control that cannot be pinned cannot go red for the reason you
wanted it to.

Choosing k, and why it is not 4
-------------------------------
k was NOT chosen by looking at the matrix.  The rule below was written down
first, it reads only anchors whose answer is known in advance, and `E6` re-runs
it on every corpus run rather than trusting this paragraph:

    NULL         the word-permutation of a corpus binary must score < 0.05 --
                 the same five percentage points the plan already calls
                 indistinguishable.  Lower bound on k.
    SENSITIVITY  a corpus binary with 1 % of its code words replaced at random
                 must still score >= 0.50.  Upper bound on k.
    IDENTITY     `acltd` across the six trees, and the byte-identical busybox
                 pair, must stay exactly 1.0 -- true at every k.
    k := the smallest value that satisfies all three for EVERY binary in the
    corpus.

`k = 4`, which is the value a reader would expect, **fails the null by a factor
of nine**: measured 2026-08-27 on `unit-2018/bin/boa`, a word-permutation --
the identical instruction multiset in a destroyed order -- still scores 0.4398
at k=4.  The mechanism is in the numbers: the token alphabet is 52, and 96,490
windows produce only 7,333 distinct 4-grams, so 4-grams are mostly shared
idioms and any two MIPS binaries from this vendor share about half of them.
The null falls 0.44 -> 0.16 -> 0.041 -> 0.0067 across k = 4, 6, 7, 8, and 7 is
the first value under 0.05 for every one of the twelve binaries; five shuffle
seeds put `unit-2018/bin/boa` in 0.0371-0.0415 there, and 0.1540-0.1599 at k=6.
Sensitivity costs almost nothing over that range (0.9832 at k=4, 0.9563 at k=7).

`--sweep` prints the whole curve, because a conclusion that only holds at one k
is a property of k.

What the corpus said about the plan's own FLOOR
-----------------------------------------------
The plan's decision rule is *pass at or above `BASE`, warn between, fail at or
below `FLOOR`*.  Measured, that middle band is not a band:

    BASE   binsim(unit-2018, n200re-3.2.0)          0.9818
    FLOOR  binsim(unit-2018, v3.4.0)                0.0650
    CROSS  binsim(unit-2018/boa, unit-2018/busybox) 0.1581   <- a DIFFERENT PROGRAM

`FLOOR` sits **below** `CROSS`.  This unit's `boa` shares fewer 7-grams with the
2020 `boa` than with the `busybox` sitting next to it on its own rootfs, so
"above FLOOR" is satisfied by a completely different program, and the warn band
swallows the whole no-evidence region.  The mechanism is named rather than
guessed: `boa` is `pic` through 2018 and not `pic` from 2019 (`SPEC.md`
`TC-04`), and dropping PIC rewrites every function's prologue and every call,
while `boa` and `busybox` on one rootfs share a compilation model.

**All of that is the code channel, and the strings channel reverses it.**
Measured, containment: `BASE` 0.9913, `FLOOR` **0.6629**, `CROSS` **0.0515** --
the ordering inverts by 13x, because the `FLOOR` pair is the *same program* and
shares two thirds of its strings while `CROSS` shares libc symbol names and
little else.  So this section is about the **code** channel and says so: the
`FLOOR` pair is not unrelated, it is one program whose code was rewritten
between SDK generations while its content survived.  An earlier draft wrote
"`FLOOR` is not a different SDK, it is no relationship", and the second channel
refuted it.  A single blended score would have averaged 0.065 and 0.663 into a
number describing neither, which is why the two are printed and never summed.

So the corpus supplies a floor the plan did not have, and `--corpus` reported
the plan's `FLOOR` as refuted rather than quietly using a better number, because
naming a floor was `R2a/b/d-1`'s decision and not this file's.

R2a/b/d-1 named it, 2026-08-27
------------------------------
    @floor  boa  unit-2018  busybox  unit-2018   = 0.1581

**The denominator is the whole story, and the first replacement got it wrong.**
That first attempt was `busybox unit-2018 v3.4.0` = 0.1646: the plan's own tree
pair, read on the one program whose source is held constant across it (讀,
`BusyBox v1.13.4` in all six trees), and 0.1646 clears `CROSS` 0.1581.  An
adversarial review killed it the same day.  Containment divides by the SMALLER
feature set; busybox's is 42,297 grams against boa's 28,887, a factor of 1.46,
so the two numbers were read at different denominators.  讀 at a matched one,
the ordering reverses:

    no shared source, same model, denominator = boa/unit-2018's 28,887 grams
      boa vs busybox 0.1581    boa vs pppd 0.1578    boa vs wscd 0.1551
    ONE upstream source, compilation model changed, denominator 28,601 grams
      pppd unit-2018 / v3.4.0  0.1212     <- BELOW the no-shared-source level

So at this scale the corpus holds no cell above the no-shared-source level and
below `BASE` that could serve as a floor, and the tightest correct floor IS that
level.  `@floor` names it.  `E7` asserts it is the highest of the three at that
denominator; `E8` measures what a model change alone costs, which is what makes
the rule's precondition (`VOID`, not `fail`) a reading rather than an argument.

    VOID   the compilation model differs -- check the container fingerprint
    fail   score <= FLOOR = 0.1581
    warn   FLOOR < score < BASE
    pass   score >= BASE  = 0.9818

`notes/which-drop.md` owns the reasoning, the rejected alternatives, and the
k sweep -- 讀, the named cell is the top of its population at every k from 2 to
14 and is overtaken at k = 1, where the reference itself flips.

The three anchors that come free with the corpus
------------------------------------------------
  * `bin/acltd` is **one sha256 in all six trees** -- 10,032 bytes, `.comment`
    `GCC: (GNU) 3.2.3-1.2.11`, a prebuilt blob carried unchanged across five
    years and three product lines.  It is a real-material identity anchor, and
    it is also the positive control on the plan's own void verdict: its fifteen
    cells span exactly zero, so the verdict must fire on it.  A verdict that
    never fires is not a verdict.
  * `v2.1.2` and `n300rt-2.1.6`'s `busybox` are the same size and **differ in
    eight bytes, all of them digits in the BusyBox banner's build date**
    (`LOG.md` 2026-08-27).  99.997 % identical, one build rebuilt on another
    day.  A metric that does not put that pair at the top of the busybox matrix
    is not measuring structure -- and one that puts everything there is not
    measuring anything.  `1 - that score` is this tool's own noise floor, and
    `BASE - FLOOR` has to clear it.
  * The container format partitions the corpus without any similarity metric at
    all: `EF_MIPS_PIC` and `DT_MIPS_PLTGOT` split it 4+2 (`SPEC.md` `TC-04`),
    and `notes/lwl-mystery.md`'s unaligned-instruction counts split it 2+2+2.
    Those are read by a different instrument from a different part of the file,
    so a matrix that contradicts them is the matrix that is wrong.  `--corpus`
    prints the partition beside the scores; it does not blend them.

The controls
------------
Every invocation runs `A`, `B`, `C` and `D` first and refuses to report if one
fails.  `--self-test` runs the twenty-four of them and nothing else; none needs
a vendor binary, so a fresh clone with no `$FWRE_WORK` still has a control on
every part of this file.

  A1  the code window of a synthetic ELF is exactly the one built into it
  A2  eight malformed inputs, each refused with its own reason and none scored
  A3  a code window shorter than k words is refused, not scored 0.0 or 1.0
  A4  `e_flags` decoding: `0x1007` carries `pic`, `0x1005` does not
  B1  token identities, including `nop` distinct from `sll` and `mfc3`/`mtc3`
      landing in COP3 function-selector slots rather than being read as registers
  B2  the token alphabet: every token < 256, and injective on B1's cases --
      a tokeniser that collapsed everything to one value passes B1 alone
  B3  the k-gram hash of a fixed token sequence equals a pinned constant
  C1  identity: a file against itself is exactly 1.0, both channels
  C2  disjoint: two streams sharing no k-gram are exactly 0.0
  C3  a seeded random stream of the same length scores < 0.02
  C4  a byte-permutation of the file scores < 0.02
  C5  a word-permutation over the whole k curve: 1.0 at k=1, strictly falling,
      and under 0.05 at k=7.  **Necessary and not sufficient** -- a 4,000-word
      fixture cannot reproduce the k-gram saturation that made k=4 fail on real
      material, and `E5`/`E6` are the two that constrain
  C6  the length term, as a mechanism rather than a number: delete a contiguous
      20 % of the tokens; containment must hold >= 0.99, and Jaccard must equal
      the ratio of the two k-gram set sizes to within 0.01 -- which is what
      "Jaccard carries a length term" means, stated so it can be checked
  C7  not saturated: streams sharing half their tokens land strictly inside
      (0.05, 0.95).  A metric returning only 0 and 1 passes C1 through C6
  C8  symmetry, both measures
  C9  the strings channel: known set, minimum length honoured
  D1  a manifest whose sha256 does not match the file is refused, not scored
  D2  the void verdict fires on a corpus of three identical trees
  D3  the void verdict does not fire on a corpus built to span more than 5 pp
  D4  `BASE`/`FLOOR` are read from the manifest's named cells, and a cell that
      is not in the matrix is refused rather than silently dropped
  D5  the floor verdict follows BOTH of its arguments -- below `CROSS`, at it,
      above it, and with `CROSS` itself moved under a fixed floor.  Until
      `R2a/b/d-1` replaced `@floor` the REFUTED branch fired only on the real
      six trees, so the day the corpus stopped refuting the floor that branch
      would have had no test anywhere.  The first version of this control
      passed the same `cross_v` three times, and a reviewer built a mutant that
      ignored the argument entirely and passed all 24 controls and all 74
      runner cases; `M12` is that mutant, kept.  `tools/test-binsim.sh` also
      drives the verdict end to end on two synthetic corpora, one on each side

And with `$FWRE_WORK` present, `--corpus` adds eleven that need the real material:

  E0  **every sample in the corpus is the same ISA.**  The corpus's membership
      rule, enforced instead of written in a comment.  The parser already
      refuses a little-endian or non-MIPS file -- 讀 2026-08-27 on TOTOLINK
      N350RT V9.3.5u, which is a **MediaTek MT7628**, little-endian MIPS32r2:
      `ELF data 1, not MSB`, exit 2.  What that does NOT catch is a big-endian
      MIPS32r2 part, which would parse, score, and quietly move `FLOOR`
  E1  the identity-role program: every cell exactly 1.0, and the void verdict
      fires on it
  E2  every pair whose code window is byte-identical scores exactly 1.0/1.0.
      Derived from the material rather than from a tree name written in here:
      `acltd` supplies fifteen such pairs and busybox supplies one
  E2b a pair with identical code windows and different FILES must score 1.0 on
      the code channel and less on the strings channel.  Two channels that never
      disagreed would be one channel counted twice
  E4  on the two trees that kept section headers, the derived window equals
      `.init` through `.fini`.  That is two files out of twelve, so:
  E4b **the window is code, by a decoding invariant**: every `j`/`jal` word in
      the window must target the executable segment, and the same window read
      from a 2-byte offset must not (< 0.30), which is the negative control on
      the control.  Measured 2026-08-27: 0.9997-1.0000 per file inside, 0.000-
      0.043 in the 4 KiB after, 0.000-0.098 misaligned; 48,709 of 48,713 words
      across the corpus.  The four that miss are `jal 0x0` in the two 3.4.0
      `busybox`, each behind a null guard -- an un-relocated call, not data.
      The assertion is >= 0.99 per file for that reason.
      **A frequency was tried first and withdrawn**: primary opcode `0x00` is
      SPECIAL, so a run of padding scores 100 % "code-like", and `acltd`'s
      `.rodata` read 0.816.  The common-opcode fraction is still computed and
      printed over NON-ZERO words, and it is not what this asserts.
      Without E4b the eight binaries with no section table have no check on
      their window at all, and a window that had drifted into `.rodata` would
      still have produced a full matrix of plausible numbers
  E5  C3/C4/C5 again, on `unit-2018/bin/boa` rather than on a fixture.  This is
      the version of those three that constrains anything, because a 4,000-word
      fixture cannot reproduce the k-gram saturation that made k=4 fail
  E6  the k-selection rule above, re-run: `DEFAULT_K`'s null must be under 0.05
      for every binary in the corpus, and the sensitivity anchor must hold
  E6b ... and no smaller k does.  Separate from `E6` because minimality is a
      claim only a corpus with enough structure can make, and asserting it
      unconditionally would turn a simpler corpus red for a property of the
      corpus rather than of the pin.  ⚠️ It measures the null at exactly ONE
      value, `k - 1`; "every k below the pin is excluded" is an extrapolation
      no control here makes
  E7  **`FLOOR` is the highest cell of a POPULATION at one denominator**, not
      one pair's number.  Containment divides by the smaller feature set, so a
      cross-program score is roughly (shared compiler idiom) / |G(smaller)| and
      is not a constant of the corpus: 讀 2026-08-27 inside `unit-2018`, 422 of
      the 630 cross-program cells over its 36 largest programs sit above
      0.1646, and the top of that list is two vendor tools that share their
      source.  So the population is restricted to programs at least as large as
      the floor's own reference, and `E7` asserts the named cell is its maximum
  E8  **one upstream source under two compilation models lands at or below
      `FLOOR`** -- the `@model` cell.  This is what makes the decision rule's
      precondition a reading rather than an argument: below the floor the code
      channel cannot tell "the same source built differently" from "a program
      that shares no source", so a comparison across a model change is VOID and
      not a fail

`CROSS` -- `boa` against `busybox` from the *same* tree -- is **reported and not
asserted**, and that is deliberate.  It is a property of the corpus, not of this
tool: turning it into a control would report a finding about the plan's
thresholds as a defect in the instrument.  It sets the exit code instead.

A control that cannot run on a given corpus prints `n-a` rather than `ok`.  A
green line for a check nobody ran is the failure the census job one level up
exists to catch.

What this cannot do, so a number is not read as more than it is
---------------------------------------------------------------
  * **One cell** cannot tell a toolchain difference from a config difference.
    The corpus is another matter, and `R2a/b/d-1` measured it: `busybox` holds
    one upstream source across all six trees, so its cells move only when the
    code generator's output does, and on the 2016 -> 2018 edge they do not
    (0.9995-0.9997) while `boa` falls to 0.877-0.895.  On that edge the two are
    separated; across the compilation-model change they are not.
    🔄 This bullet used to read "the corpus confounds date, product line and
    SDK generation, and no function of two binaries separates them -- `--corpus`
    says so in its own output".  Both halves were wrong.  **Product line is
    crossed with the clustering, not confounded with it** -- 讀 `/etc/version`,
    N150RT appears in all three clusters -- and `--corpus` never printed any
    such sentence.  `notes/which-drop.md` §2 and §3 own the corrections.
  * It does not disassemble.  The window is scanned linearly at 4-byte
    alignment, so literal pools and jump tables inside the window are tokenised
    as instructions.  That is a *superset*, it is the same trade `opcount.py`
    documents, and it biases both files in a pair the same way.
  * **Containment divides by the smaller feature set**, so a score is not
    comparable across pairs of different sizes and a threshold read at one
    denominator does not transfer to another.  `--corpus` prints the
    denominator beside every named cell for that reason.
  * A high score is evidence of shared source and toolchain together.  It cannot
    attribute the share to one of them.
  * `--corpus` reports the matrix.  Reading the clusters is `R2a/b/d-1`,
    `notes/which-drop.md`, and this file deliberately stops before it.

Exit codes
----------
    0  reported, and every control held
    1  reported, but a result is void -- the fifteen scores did not span 5 pp,
       or the named FLOOR sits below CROSS
    2  refused: a control failed, or an input could not be parsed
    3  usage error

Version 1.1, 2026-08-27.  The version number lives in `VERSION` below; this
line said 1.0 for one commit after the bump, which is the reason it now says
where the real one is.
"""

import hashlib
import os
import random
import struct
import sys

VERSION = "1.1"

# k is pinned, and E6 re-derives the pin from the corpus on every corpus run
# rather than trusting this comment.  See "Choosing k" in the docstring.
DEFAULT_K = 7
# Dense from 1 to 16.  It was (1,2,3,4,5,6,7,8,10,12,16) until 2026-08-27, and
# three committed files then said the floor verdict "holds for every k from 7 to
# 16" -- a universal over ten values from a grid that visited five of them.  The
# five unswept ones do hold (讀), which is why this is a gap in what was
# checked rather than a wrong number, and a dense grid costs about a second.
SWEEP_K = tuple(range(1, 17))
DEFAULT_MIN_STRING = 8
VOID_SPAN = 0.05          # the plan's five percentage points
NULL_MAX = 0.05           # ... and what the metric's own null has to be under
SENS_MIN = 0.50           # a 1 % edit must not destroy the score

# ---------------------------------------------------------------------------
# ELF, read straight out of the bytes.  No external module: this has to run on
# a stock runner with nothing but python3, and `readelf` cannot be asked about
# a file whose section headers are gone anyway.
# ---------------------------------------------------------------------------

PT_LOAD, PT_DYNAMIC, PT_INTERP, PT_NOTE = 1, 2, 3, 4
PF_X = 1

DT_NULL, DT_NEEDED, DT_STRTAB, DT_STRSZ = 0, 1, 5, 10
DT_INIT, DT_FINI = 12, 13
DT_MIPS_LOCAL_GOTNO = 0x7000000A
DT_MIPS_SYMTABNO = 0x70000011
DT_MIPS_GOTSYM = 0x70000013
DT_MIPS_PLTGOT = 0x70000032

EM_MIPS = 8

EF_MIPS = [
    (0x00000001, "noreorder"),
    (0x00000002, "pic"),
    (0x00000004, "cpic"),
    (0x00000008, "xgot"),
    (0x00000020, "abi2"),
    (0x00000100, "32bitmode"),
    (0x00000400, "nan2008"),
]
EF_MIPS_ABI_MASK = 0x0000F000
EF_MIPS_ABI_NAMES = {0x1000: "o32", 0x2000: "o64", 0x3000: "eabi32", 0x4000: "eabi64"}
EF_MIPS_ARCH_MASK = 0xF0000000
EF_MIPS_ARCH_NAMES = {
    0x00000000: "mips1", 0x10000000: "mips2", 0x20000000: "mips3",
    0x30000000: "mips4", 0x40000000: "mips5", 0x50000000: "mips32",
    0x60000000: "mips64", 0x70000000: "mips32r2", 0x80000000: "mips64r2",
}


class Refused(Exception):
    """The input could not be read as what it claims to be.  Exit 2, not a score."""


class Elf(object):
    def __init__(self, blob, name="<bytes>"):
        self.blob = blob
        self.name = name
        b = blob
        if len(b) < 52:
            raise Refused("%s: %d bytes, shorter than an ELF32 header" % (name, len(b)))
        if b[:4] != b"\x7fELF":
            raise Refused("%s: no ELF magic" % name)
        if b[4] != 1:
            raise Refused("%s: ELF class %d, not ELF32" % (name, b[4]))
        if b[5] != 2:
            raise Refused("%s: ELF data %d, not MSB (big-endian)" % (name, b[5]))
        (self.e_type, self.e_machine, self.e_version, self.e_entry, self.e_phoff,
         self.e_shoff, self.e_flags) = struct.unpack_from(">HHIIIII", b, 16)
        (self.e_ehsize, self.e_phentsize, self.e_phnum, self.e_shentsize,
         self.e_shnum, self.e_shstrndx) = struct.unpack_from(">6H", b, 40)
        if self.e_machine != EM_MIPS:
            raise Refused("%s: e_machine %d, not EM_MIPS" % (name, self.e_machine))
        self.phdrs = self._phdrs()
        self.dyn = self._dynamic()

    def _phdrs(self):
        b = self.blob
        out = []
        if self.e_phentsize < 32 or self.e_phnum == 0:
            raise Refused("%s: no program headers" % self.name)
        end = self.e_phoff + self.e_phnum * self.e_phentsize
        if end > len(b):
            raise Refused("%s: program header table runs past the end of the file "
                          "(needs 0x%x, file is 0x%x)" % (self.name, end, len(b)))
        for i in range(self.e_phnum):
            o = self.e_phoff + i * self.e_phentsize
            out.append(dict(zip(
                ("type", "offset", "vaddr", "paddr", "filesz", "memsz", "flags", "align"),
                struct.unpack_from(">8I", b, o))))
        if not [p for p in out if p["type"] == PT_LOAD]:
            raise Refused("%s: no PT_LOAD segment" % self.name)
        return out

    def _dynamic(self):
        segs = [p for p in self.phdrs if p["type"] == PT_DYNAMIC]
        if not segs:
            raise Refused("%s: no PT_DYNAMIC segment -- the code window is taken from "
                          "DT_INIT/DT_FINI, and this file has neither" % self.name)
        p = segs[0]
        b = self.blob
        if p["offset"] + p["filesz"] > len(b):
            raise Refused("%s: PT_DYNAMIC runs past the end of the file" % self.name)
        tags = []
        for o in range(p["offset"], p["offset"] + p["filesz"] - 7, 8):
            tag, val = struct.unpack_from(">II", b, o)
            tags.append((tag, val))
            if tag == DT_NULL:
                break
        return tags

    def dt(self, tag):
        for t, v in self.dyn:
            if t == tag:
                return v
        return None

    def dt_all(self, tag):
        return [v for t, v in self.dyn if t == tag]

    def v2o(self, vaddr):
        """File offset of a virtual address, via the PT_LOAD that contains it."""
        for p in self.phdrs:
            if p["type"] != PT_LOAD:
                continue
            if p["vaddr"] <= vaddr < p["vaddr"] + p["filesz"]:
                return p["offset"] + (vaddr - p["vaddr"])
        return None

    def cstr(self, off):
        b = self.blob
        e = b.find(b"\x00", off)
        return b[off:e if e >= 0 else len(b)].decode("latin-1")

    # -- the code window ----------------------------------------------------

    def code_window(self):
        """(file_offset, size, vaddr) of [DT_INIT, DT_FINI).

        Not `.text`: four of the six binaries this exists for have no section
        header table.  `.init` .. `.fini` is what the two that DO have one say
        this window is, and E4 checks that on them.
        """
        init, fini = self.dt(DT_INIT), self.dt(DT_FINI)
        if init is None:
            raise Refused("%s: no DT_INIT" % self.name)
        if fini is None:
            raise Refused("%s: no DT_FINI" % self.name)
        if fini <= init:
            raise Refused("%s: DT_FINI 0x%x is not above DT_INIT 0x%x"
                          % (self.name, fini, init))
        off = self.v2o(init)
        if off is None:
            raise Refused("%s: DT_INIT 0x%x is in no PT_LOAD" % (self.name, init))
        end = self.v2o(fini)
        if end is None:
            raise Refused("%s: DT_FINI 0x%x is in no PT_LOAD" % (self.name, fini))
        if end <= off:
            raise Refused("%s: the code window maps to a non-positive file range"
                          % self.name)
        size = (end - off) & ~3
        # Without this a file truncated in its BODY -- the commonest way a
        # manifest hash fails -- died inside `tokenize` with an uncaught
        # struct.error, which `main` does not catch and which therefore exited 1
        # instead of 2. Exit 1 is "reported, but a result is void", so a caller
        # could not tell a crashed parse from a legitimate void verdict.
        if off + size > len(self.blob):
            raise Refused("%s: the code window runs past the end of the file "
                          "(needs 0x%x, file is 0x%x)"
                          % (self.name, off + size, len(self.blob)))
        return off, size, init

    # -- sections, when the file still has them -----------------------------

    def sections(self):
        """[(name, addr, offset, size)] or [] when the table was stripped."""
        if self.e_shoff == 0 or self.e_shnum == 0 or self.e_shentsize < 40:
            return []
        b = self.blob
        if self.e_shoff + self.e_shnum * self.e_shentsize > len(b):
            return []
        raw = []
        for i in range(self.e_shnum):
            o = self.e_shoff + i * self.e_shentsize
            raw.append(struct.unpack_from(">10I", b, o))
        if self.e_shstrndx >= len(raw):
            return []
        strtab = raw[self.e_shstrndx][4]
        out = []
        for r in raw:
            e = b.find(b"\x00", strtab + r[0])
            nm = b[strtab + r[0]:e if e >= 0 else len(b)].decode("latin-1")
            out.append((nm, r[3], r[4], r[5]))
        return out

    # -- the categorical fingerprint ----------------------------------------

    def fingerprint(self):
        strtab = self.dt(DT_STRTAB)
        needed = []
        if strtab is not None:
            so = self.v2o(strtab)
            if so is not None:
                needed = sorted(self.cstr(so + v) for v in self.dt_all(DT_NEEDED))
        interp = ""
        for p in self.phdrs:
            if p["type"] == PT_INTERP and p["offset"] + p["filesz"] <= len(self.blob):
                interp = self.cstr(p["offset"])
        return {
            "e_flags": "0x%04x %s" % (self.e_flags, decode_eflags(self.e_flags)),
            "phnum": self.e_phnum,
            "sections": "yes" if self.e_shoff else "no",
            "notes": sum(1 for p in self.phdrs if p["type"] == PT_NOTE),
            "interp": interp,
            "needed": ",".join(needed),
            "local_gotno": self.dt(DT_MIPS_LOCAL_GOTNO),
            "symtabno": self.dt(DT_MIPS_SYMTABNO),
            "gotsym": self.dt(DT_MIPS_GOTSYM),
            "pltgot": "yes" if self.dt(DT_MIPS_PLTGOT) is not None else "no",
        }


def decode_eflags(f):
    bits = [nm for m, nm in EF_MIPS if f & m]
    abi = EF_MIPS_ABI_NAMES.get(f & EF_MIPS_ABI_MASK)
    if abi:
        bits.append(abi)
    arch = EF_MIPS_ARCH_NAMES.get(f & EF_MIPS_ARCH_MASK)
    bits.append(arch if arch else "arch?0x%x" % (f & EF_MIPS_ARCH_MASK))
    return ", ".join(bits)


# ---------------------------------------------------------------------------
# Tokens.  One byte each, so the k-gram hash is a plain FNV over bytes.
#
#   0          nop, i.e. the word 0x00000000
#   2 .. 63    a primary opcode that is not sub-decoded below
#   64 ..127   SPECIAL, by funct
#   128..159   REGIMM, by rt
#   160..195   COP0/1/2/3, by function selector -- NOT by register.  The rs
#              field of a COPz word selects MF/DMF/CF/MT/DMT/CT/BC/CO; reading
#              it as a source register is the defect corrected in hazlint and
#              opcount on 2026-08-27 (SPEC.md TC-08), and it is not repeated here.
#
# Slot 1 is unused: opcode 1 is REGIMM and is sub-decoded, and slot 0 belongs to
# nop.  Dropping nop into SPECIAL/funct 0 would merge it with every `sll`, and
# delay-slot padding is a large fraction of a MIPS image built `-fno-schedule`.
# ---------------------------------------------------------------------------

COPZ = (0x10, 0x11, 0x12, 0x13)

# The primary opcodes that dominate compiled MIPS code.  Used only by E4b, as an
# independent signal for "is this window code" -- the same list and the same
# purpose as `tools/opcount.py`'s COMMON, which `notes/lwl-mystery.md` used to
# bound code regions without looking for a boundary that gave a wanted answer.
COMMON_OPS = {0x00, 0x02, 0x03, 0x04, 0x05, 0x08, 0x09, 0x0C, 0x0D, 0x0E, 0x0F,
              0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B}

TOK_NOP = 0
TOK_SPECIAL = 64
TOK_REGIMM = 128
TOK_COPZ = 160


def token(w):
    if w == 0:
        return TOK_NOP
    op = w >> 26
    if op == 0:
        return TOK_SPECIAL + (w & 0x3F)
    if op == 1:
        return TOK_REGIMM + ((w >> 16) & 0x1F)
    if op in COPZ:
        rs = (w >> 21) & 0x1F
        fsel = rs if rs < 8 else (7 if rs == 8 else 8)
        return TOK_COPZ + (op & 3) * 9 + fsel
    return op


def tokenize(blob, off, size):
    out = []
    ap = out.append
    for i in range(off, off + size, 4):
        ap(token(struct.unpack_from(">I", blob, i)[0]))
    return out


MASK64 = (1 << 64) - 1
FNV_OFF = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3


def kgrams(toks, k):
    """Set of 64-bit FNV-1a hashes of every k-token window.

    Explicitly not `hash(tuple)`: that is an implementation detail of the
    interpreter, and B3 pins this one to a constant so a build where it changed
    would go red rather than quietly produce a different matrix.
    """
    if k < 1:
        raise Refused("k must be >= 1, got %d" % k)
    n = len(toks)
    if n < k:
        raise Refused("code window holds %d token(s), shorter than k=%d" % (n, k))
    out = set()
    add = out.add
    for i in range(n - k + 1):
        h = FNV_OFF
        for j in range(i, i + k):
            h = ((h ^ toks[j]) * FNV_PRIME) & MASK64
        add(h)
    return out


# ---------------------------------------------------------------------------
# The two measures.  Both are printed on every line, always.
# ---------------------------------------------------------------------------

def measures(a, b):
    """(containment, jaccard, |a|, |b|, |a&b|)."""
    if not a or not b:
        raise Refused("an empty feature set has no similarity; refusing to call it 0 or 1")
    inter = len(a & b)
    return (inter / min(len(a), len(b)),
            inter / (len(a) + len(b) - inter),
            len(a), len(b), inter)


def ascii_runs(blob, minlen):
    """Set of printable-ASCII runs of at least `minlen` bytes.

    The whole file, not the code window: what this channel is for is the
    configuration and the symbol names, which are the axis the code channel is
    deliberately blind to.  The two are reported side by side and never summed.
    """
    out = set()
    run = bytearray()
    for c in blob:
        if 0x20 <= c <= 0x7E:
            run.append(c)
        else:
            if len(run) >= minlen:
                out.add(bytes(run))
            del run[:]
    if len(run) >= minlen:
        out.add(bytes(run))
    return out


class Sample(object):
    """One binary, read once."""

    def __init__(self, path=None, blob=None, name=None, minstr=DEFAULT_MIN_STRING):
        if blob is None:
            with open(path, "rb") as fh:
                blob = fh.read()
        self.blob = blob
        self.path = path
        self.name = name or (path or "<bytes>")
        self.elf = Elf(blob, self.name)
        self.off, self.size, self.vaddr = self.elf.code_window()
        self.toks = tokenize(blob, self.off, self.size)
        self.strings = ascii_runs(blob, minstr)
        self._g = {}

    def grams(self, k):
        if k not in self._g:
            self._g[k] = kgrams(self.toks, k)
        return self._g[k]

    def sha256(self):
        return hashlib.sha256(self.blob).hexdigest()


def score(a, b, k=DEFAULT_K):
    return measures(a.grams(k), b.grams(k))


def score_strings(a, b):
    return measures(a.strings, b.strings)


# ---------------------------------------------------------------------------
# Controls.  Every invocation runs these before it reports anything.
# ---------------------------------------------------------------------------

class Controls(object):
    """ok / FAIL / n-a, and the third one is not a convenience.

    A control that cannot run on a given corpus -- `E4` where no file kept a
    section table, `E6b` where the corpus does not constrain k downward -- has
    to say so.  Printing it as `ok` would be a green line for a check nobody
    ran, which is the failure this project's census job exists to catch one
    level up.
    """

    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail):
        self.rows.append((name, bool(ok), detail))
        return ok

    def na(self, name, detail):
        self.rows.append((name, None, detail))
        return True

    @property
    def failed(self):
        return [r for r in self.rows if r[1] is False]

    @property
    def notrun(self):
        return [r for r in self.rows if r[1] is None]

    def report(self, out=sys.stdout):
        for name, ok, detail in self.rows:
            tag = "n-a" if ok is None else ("ok" if ok else "FAIL")
            out.write("  %-6s %-46s %s\n" % (tag, name, detail))
        line = "  %d control(s), %d failed" % (len(self.rows), len(self.failed))
        if self.notrun:
            line += ", %d not applicable to this corpus" % len(self.notrun)
        out.write(line + "\n")


# -- a synthetic ELF, so every control above runs without a vendor binary ----

SYN_BASE = 0x00400000
SYN_EHSIZE = 52
SYN_PHENT = 32


def synth_elf(words, nphdr_extra=0, machine=EM_MIPS, elfclass=1, data=2,
              want_dynamic=True, init_off=None, fini_off=None, flags=0x1007,
              tag=b""):
    """A loadable ELF32-BE MIPS executable wrapped round `words`.

    Layout: ehdr | phdrs | dynamic | code.  `init_off`/`fini_off` are offsets
    into the code array, so A1 knows the answer before it asks.
    """
    nph = 2 + nphdr_extra
    dyn_off = SYN_EHSIZE + nph * SYN_PHENT
    dyn = []
    code_off = dyn_off  # filled in once the dynamic table's size is known
    ndyn = 3 if want_dynamic else 0
    code_off = dyn_off + ndyn * 8
    # Four words of tail padding so that DT_FINI, which is an address INSIDE the
    # load in every real binary, is inside this one too when fini_off is the end
    # of the code array.  Without it the synthetic ELF is one word shorter than
    # the address it names, and the parser is right to refuse it.
    #
    # Then a `.rodata`-shaped tail, OUTSIDE the code window, derived from the
    # words so that two fixtures built from different code carry different
    # strings.  Without it the strings channel has no fixture at all and C1/C8
    # would be asserting something about an empty set.
    #
    # `tag` goes in that tail, OUTSIDE the code window, so a caller can build
    # two files with identical code and different bytes -- which is the shape
    # the eight-byte busybox pair has and the only way a synthetic corpus can
    # exercise E2b.
    tail = (b"".join(b"binsim-fixture-%08x\x00" % w for w in sorted(set(words))[:64])
            + tag)
    code = (b"".join(struct.pack(">I", w) for w in words) + b"\x00" * 16 + tail)
    i0 = 0 if init_off is None else init_off
    i1 = len(words) if fini_off is None else fini_off
    if want_dynamic:
        dyn = [(DT_INIT, SYN_BASE + code_off + i0 * 4),
               (DT_FINI, SYN_BASE + code_off + i1 * 4),
               (DT_NULL, 0)]
    total = code_off + len(code)

    ident = bytearray(16)
    ident[0:4] = b"\x7fELF"
    ident[4] = elfclass
    ident[5] = data
    ident[6] = 1
    eh = bytes(ident) + struct.pack(
        ">HHIIIII6H", 2, machine, 1, SYN_BASE + code_off, SYN_EHSIZE,
        0, flags, SYN_EHSIZE, SYN_PHENT, nph, 0, 0, 0)

    ph = struct.pack(">8I", PT_LOAD, 0, SYN_BASE, SYN_BASE, total, total,
                     4 | PF_X, 0x10000)
    if want_dynamic:
        ph += struct.pack(">8I", PT_DYNAMIC, dyn_off, SYN_BASE + dyn_off,
                          SYN_BASE + dyn_off, ndyn * 8, ndyn * 8, 4 | 2, 4)
    else:
        ph += struct.pack(">8I", PT_NOTE, dyn_off, SYN_BASE + dyn_off,
                          SYN_BASE + dyn_off, 0, 0, 4, 4)
    for _ in range(nphdr_extra):
        ph += struct.pack(">8I", PT_NOTE, 0, 0, 0, 0, 0, 4, 4)

    dynb = b"".join(struct.pack(">II", t, v) for t, v in dyn)
    return eh + ph + dynb + code


# Roughly the instruction mix of compiled MIPS-I, with the common forms repeated
# so the fixture's token distribution is skewed the way real code's is.  The
# multiplicities are from what a compiler emits, not from the corpus -- tuning a
# fixture on the material it is meant to be an independent check of is how a
# control stops being one.
_POOL = (
    [0x8C620000] * 9 + [0xAC620000] * 6 + [0x24420001] * 6 + [0x00000000] * 6 +
    [0x00431021] * 4 + [0x3C021234] * 3 + [0x34420001] * 3 + [0x1443FFFE] * 3 +
    [0x1043FFFE] * 3 + [0x0C100000] * 3 + [0x03E00008] * 2 + [0x27BDFFE0] * 2 +
    [0xAFBF001C] * 2 + [0x8FBF001C] * 2 + [0x00021080] * 2 + [0x90620000] * 2 +
    [0xA0620000] * 2 + [0x30420001] * 2 + [0x0043102A] * 2 + [0x00431023] +
    [0x00431025] + [0x00431024] + [0x00431026] + [0x00021083] + [0x00021082] +
    [0x0043001B] + [0x00001012] + [0x00001010] + [0x00430019] + [0x84620000] +
    [0x94620000] + [0xA4620000] + [0x80620000] + [0x08100000] + [0x18400002] +
    [0x1C400002] + [0x04410002] + [0x04400002] + [0x28420001] + [0x2C420001] +
    [0x38420001] + [0x88620000] + [0x98620003] + [0xA8620000] + [0xB8620003] +
    [0x40026000] + [0x40826000] + [0x0060F809] + [0x0000000D] + [0x0000000C] +
    [0x00431027] + [0x00622004] + [0x00622006] + [0x00622007] + [0x00430018] +
    [0x00400011] + [0x00400013] + [0x04110002]
)


def _plausible_code(n, seed=1):
    """n words that tokenize the way real MIPS code does, deterministically."""
    rnd = random.Random(seed)
    return [_POOL[rnd.randrange(len(_POOL))] for _ in range(n)]


def _sample_from_words(words, name, minstr=DEFAULT_MIN_STRING):
    return Sample(blob=synth_elf(words), name=name, minstr=minstr)


def run_controls(k=DEFAULT_K, urandom=False):
    c = Controls()

    # --- A: the container ---------------------------------------------------
    words = _plausible_code(400)
    blob = synth_elf(words, init_off=8, fini_off=360)
    try:
        e = Elf(blob, "A1")
        off, size, va = e.code_window()
        toks = tokenize(blob, off, size)
        want = (360 - 8)
        ok = size == want * 4 and len(toks) == want and toks == [token(w) for w in words[8:360]]
        c.add("A1  code window is [DT_INIT, DT_FINI)", ok,
              "%d words at file 0x%x, vaddr 0x%x" % (len(toks), off, va))
    except Refused as ex:
        c.add("A1  code window is [DT_INIT, DT_FINI)", False, "refused: %s" % ex)

    bad = [
        ("not an ELF", b"MZ" + b"\x00" * 200, "no ELF magic"),
        ("ELF64", synth_elf(words, elfclass=2), "not ELF32"),
        ("little-endian", synth_elf(words, data=1), "not MSB"),
        ("not MIPS", synth_elf(words, machine=40), "not EM_MIPS"),
        ("truncated header", b"\x7fELF\x01\x02\x01" + b"\x00" * 20, "shorter than an ELF32 header"),
        ("phdrs past EOF", synth_elf(words)[:60], "past the end of the file"),
        ("no PT_DYNAMIC", synth_elf(words, want_dynamic=False), "no PT_DYNAMIC"),
        ("DT_FINI <= DT_INIT", synth_elf(words, init_off=300, fini_off=10),
         "is not above DT_INIT"),
    ]
    seen, why = 0, []
    for label, b, expect in bad:
        try:
            s = Elf(b, label)
            s.code_window()
            why.append("%s: NOT refused" % label)
        except Refused as ex:
            if expect in str(ex):
                seen += 1
            else:
                why.append("%s: wrong reason (%s)" % (label, ex))
        except Exception as ex:                                # noqa: BLE001
            why.append("%s: raised %s, not Refused" % (label, type(ex).__name__))
    c.add("A2  eight malformed inputs, each refused by reason", seen == len(bad),
          "%d/%d" % (seen, len(bad)) + ("  " + "; ".join(why) if why else ""))

    tiny = synth_elf(_plausible_code(2), init_off=0, fini_off=2)
    try:
        Sample(blob=tiny, name="A3").grams(k)
        c.add("A3  a window shorter than k words is refused", False, "scored it instead")
    except Refused as ex:
        c.add("A3  a window shorter than k words is refused", "shorter than k" in str(ex),
              str(ex))

    f7, f5 = decode_eflags(0x1007), decode_eflags(0x1005)
    c.add("A4  e_flags decoding separates 0x1007 from 0x1005",
          "pic" in f7.split(", ") and "pic" not in f5.split(", ") and f7 != f5,
          "0x1007 %s | 0x1005 %s" % (f7, f5))

    # --- B: the tokeniser ---------------------------------------------------
    cases = [
        (0x00000000, TOK_NOP, "nop"),
        (0x00021080, TOK_SPECIAL + 0x00, "sll, and not nop"),
        (0x00431021, TOK_SPECIAL + 0x21, "addu"),
        (0x03E00008, TOK_SPECIAL + 0x08, "jr"),
        (0x0441FFFF, TOK_REGIMM + 1, "bgez -- REGIMM is keyed on rt, not rs"),
        (0x0442FFFF, TOK_REGIMM + 2, "bltzl -- same rs, different instruction"),
        (0x8C620000, 0x23, "lw"),
        (0x4C020000, TOK_COPZ + 3 * 9 + 0, "mfc3 -- selector MF, not register v0"),
        (0x4C880000, TOK_COPZ + 3 * 9 + 4, "mtc3 -- selector MT, not register t0"),
        (0x4D010003, TOK_COPZ + 3 * 9 + 7, "bc3t -- selector BC"),
        (0x4DF46783, TOK_COPZ + 3 * 9 + 8, "COP3 CO form, the kernel word from 2026-08-27"),
        (0x40800000, TOK_COPZ + 0 * 9 + 4, "mtc0"),
        (0xCC820000, 0x33, "lwc3"),
    ]
    badtok = [w for w, t, _ in cases if token(w) != t]
    c.add("B1  token identities, %d hand-encoded words" % len(cases), not badtok,
          "0 wrong" if not badtok else "wrong: " + " ".join("0x%08x" % w for w in badtok))

    alpha = set()
    for w in range(0, 1 << 32, 0x00010007):        # a stride that visits every opcode
        alpha.add(token(w))
    for w, _, _ in cases:
        alpha.add(token(w))
    inj = len({token(w) for w, _, _ in cases}) == len({t for _, t, _ in cases})
    c.add("B2  alphabet fits one byte and is injective on B1",
          max(alpha) < 256 and min(alpha) >= 0 and inj and len(alpha) > 40,
          "%d distinct tokens, max %d" % (len(alpha), max(alpha)))

    pinned = 0xBE7A5E775165785D
    got = list(kgrams([1, 2, 3, 4], 4))[0]
    c.add("B3  the k-gram hash is pinned, not the interpreter's",
          got == pinned, "0x%016X" % got)

    # --- C: the metric ------------------------------------------------------
    base_words = _plausible_code(4000, seed=7)
    A = _sample_from_words(base_words, "C-A")

    con, jac, _, _, _ = score(A, A, k)
    sc, sj, _, _, _ = score_strings(A, A)
    c.add("C1  identity is exactly 1.0, both channels",
          con == 1.0 and jac == 1.0 and sc == 1.0 and sj == 1.0,
          "code %.6f/%.6f  strings %.6f/%.6f" % (con, jac, sc, sj))

    # Two streams with no shared k-gram: build them from disjoint token pools.
    p1 = [0x8C620000, 0x24420001, 0x00431021]           # lw, addiu, addu
    p2 = [0xAC620000, 0x30420001, 0x00431023]           # sw, andi, subu
    d1 = _sample_from_words([p1[i % 3] for i in range(2000)], "C2-a")
    d2 = _sample_from_words([p2[i % 3] for i in range(2000)], "C2-b")
    con2, jac2, _, _, inter2 = score(d1, d2, k)
    c.add("C2  two streams sharing no k-gram are exactly 0.0",
          con2 == 0.0 and jac2 == 0.0 and inter2 == 0,
          "%.6f / %.6f, intersection %d" % (con2, jac2, inter2))

    nb = len(base_words) * 4
    if urandom:
        rb = os.urandom(nb)
        rlabel = "/dev/urandom"
    else:
        rb = bytes(random.Random(20260827).randrange(256) for _ in range(nb))
        rlabel = "seeded PRNG"
    R = _sample_from_words(list(struct.unpack(">%dI" % len(base_words), rb)), "C3")
    con3, jac3, _, _, _ = score(R, A, k)
    c.add("C3  random bytes of the same length score near zero",
          con3 < 0.02, "%.6f containment (%s)" % (con3, rlabel))

    raw = b"".join(struct.pack(">I", w) for w in base_words)
    bs = bytearray(raw)
    random.Random(11).shuffle(bs)
    B4 = _sample_from_words(list(struct.unpack(">%dI" % len(base_words), bytes(bs))), "C4")
    con4, _, _, _, _ = score(B4, A, k)
    same_hist = sorted(bs) == sorted(raw)
    c.add("C4  a byte-permutation, same byte histogram, scores near zero",
          con4 < 0.02 and same_hist,
          "%.6f containment, histogram identical: %s" % (con4, same_hist))

    shuf = list(base_words)
    random.Random(12).shuffle(shuf)
    W = _sample_from_words(shuf, "C5")
    curve = [(kk, score(W, A, kk)[0]) for kk in (1, 2, 3, 4, k)]
    falling = all(curve[i][1] >= curve[i + 1][1] for i in range(len(curve) - 1))
    c.add("C5  word-permutation: 1.0 at k=1, falling, < %.2f at k=%d" % (NULL_MAX, k),
          curve[0][1] > 0.99 and falling and curve[-1][1] < NULL_MAX,
          "  ".join("k=%d %.4f" % (kk, v) for kk, v in curve)
          + "   (fixture; E5/E6 are the binding ones)")

    cut_lo, cut_hi = 1000, 1800                       # 800 of 4000 tokens = 20 %
    T = _sample_from_words(base_words[:cut_lo] + base_words[cut_hi:], "C6")
    con6, jac6, na, nbg, _ = score(T, A, k)
    ratio = na / nbg
    c.add("C6  the length term: delete 20 % of the tokens",
          con6 >= 0.99 and abs(jac6 - ratio) <= 0.01 and 0.70 <= ratio <= 0.90,
          "containment %.4f holds; jaccard %.4f == the k-gram size ratio %.4f "
          "to %.4f" % (con6, jac6, ratio, abs(jac6 - ratio)))

    half = base_words[:2000] + _plausible_code(2000, seed=99)
    H = _sample_from_words(half, "C7")
    con7, jac7, _, _, _ = score(H, A, k)
    c.add("C7  half-shared streams land strictly inside (0.05, 0.95)",
          0.05 < con7 < 0.95 and 0.05 < jac7 < 0.95,
          "containment %.4f  jaccard %.4f" % (con7, jac7))

    # A against T, not A against H: A and H have the SAME number of distinct
    # k-grams, so an asymmetric containment -- inter/|a| instead of
    # inter/min -- is invisible between them and this control could not fail.
    # That is what the M9 mutation found the first time it was run.
    ab, ba = score(A, T, k), score(T, A, k)
    sab, sba = score_strings(A, T), score_strings(T, A)
    c.add("C8  both measures are symmetric",
          ab[0] == ba[0] and ab[1] == ba[1] and sab[0] == sba[0] and sab[1] == sba[1]
          and ab[2] != ab[3],
          "%.6f/%.6f both ways, over sets of %d and %d -- unequal, or an "
          "asymmetric measure would look symmetric" % (ab[0], ab[1], ab[2], ab[3]))

    fixture = b"\x00\x01" + b"hello world" + b"\x00" + b"shortie" + b"\x00" + b"a" * 8
    got = ascii_runs(fixture, 8)
    c.add("C9  strings channel honours the minimum length",
          got == {b"hello world", b"a" * 8},
          "%d run(s); 'shortie' (7) absent: %s" % (len(got), b"shortie" not in got))

    # C10-C12 exist because three mutants survived the first suite. Each of them
    # was a real defect that every one of the then twenty controls and sixty-five
    # cases passed over.

    # C10. C6 asserts a jaccard VALUE, so a wrong jaccard formula that happens to
    # land on the same value passes it -- `inter/max` does, on C6's fixture.
    # This checks the two measures against their own definitions, from the counts
    # the function itself returns, which no formula change can survive.
    # A against T, not A against H: A and H carry the same number of distinct
    # k-grams, so `na10 != nb10` would be false and this control would refuse
    # itself. That is the same trap C8 fell into, found the same way.
    con10, jac10, na10, nb10, in10 = score(A, T, k)
    ok10 = (abs(con10 - in10 / min(na10, nb10)) < 1e-12
            and abs(jac10 - in10 / (na10 + nb10 - in10)) < 1e-12
            and na10 != nb10)
    c.add("C10 each measure equals its own definition, from the returned counts",
          ok10, "containment %.6f == %d/%d, jaccard %.6f == %d/%d, over unequal sets"
          % (con10, in10, min(na10, nb10), jac10, in10, na10 + nb10 - in10))

    # C11. `_perturbation` is the SENSITIVITY anchor of the k-selection rule. A
    # version of it that changed nothing would make the anchor read 1.0 and E6
    # would still pass -- so the perturbation itself needs a control.
    pn = _perturbation(A, 4242, frac=0.01)
    diff = sum(1 for x, y in zip(pn.toks, A.toks) if x != y)
    want = max(1, int(len(A.toks) * 0.01))
    sc11 = score(pn, A, k)[0]
    c.add("C11 the sensitivity anchor is a real edit, not a no-op",
          0 < diff <= want and sc11 < 1.0 and len(pn.toks) == len(A.toks),
          "%d of %d token(s) changed (<= %d requested), and the score moved off "
          "1.0 to %.4f" % (diff, len(A.toks), want, sc11))

    # C12. Nothing outside the bench asserted the value of k. Changing
    # DEFAULT_K to 4 -- the value the note says fails the null ninefold -- left
    # every CI-visible case green. Sufficiency is checkable here; MINIMALITY is
    # not, because this fixture is already under the null at k=4, and that gap
    # is named rather than papered over.
    nullk = score(W, A, DEFAULT_K)[0]
    c.add("C12 DEFAULT_K is pinned and satisfies the null on the fixture",
          DEFAULT_K == 7 and nullk < NULL_MAX,
          "k=%d, fixture null %.4f < %.2f. Minimality is E6b's, and E6b needs the "
          "corpus: this fixture is already under the null at k=4" % (DEFAULT_K, nullk,
                                                                     NULL_MAX))

    # --- D: the corpus machinery, on a synthetic corpus ----------------------
    d = _corpus_controls(k)
    for row in d.rows:
        c.rows.append(row)
    return c


def _corpus_controls(k):
    """D1-D4: the manifest, the void verdict, and the named cells.

    These build a corpus in memory rather than on disk, so the code path that
    reads a manifest and decides `void` has a control on a stock runner with no
    $FWRE_WORK -- which is the half of this tool that would otherwise only ever
    have run here.
    """
    c = Controls()

    ident = _plausible_code(3000, seed=5)
    trees_same = {"t1": ident, "t2": ident, "t3": ident}
    samples = {n: _sample_from_words(w, n) for n, w in trees_same.items()}

    # D1 -- integrity, against the function `load_corpus` itself calls.
    s = samples["t1"]
    got = s.sha256()
    outcomes = []
    for label, nb, sh in (("matching", len(s.blob), got),
                          ("wrong sha", len(s.blob), "0" * 64),
                          ("wrong size", len(s.blob) - 1, got)):
        try:
            check_integrity("t1", s.blob, nb, sh)
            outcomes.append((label, "accepted"))
        except Refused as ex:
            outcomes.append((label, "refused: " + str(ex).split(":")[1].strip()[:24]))
    c.add("D1  the integrity check load_corpus calls, all three ways",
          [o[1] for o in outcomes] == ["accepted"] + [o[1] for o in outcomes[1:]]
          and outcomes[0][1] == "accepted"
          and all(o[1].startswith("refused") for o in outcomes[1:]),
          "; ".join("%s -> %s" % o for o in outcomes))

    m = matrix(samples, ["t1", "t2", "t3"], k)
    sp = span(m)
    c.add("D2  the void verdict fires on three identical trees",
          sp is not None and sp < VOID_SPAN and all(v[0] == 1.0 for v in m.values()),
          "span %.4f over %d cell(s), all at 1.0" % (sp, len(m)))

    trees_wide = {"t1": ident,
                  "t2": ident[:1500] + _plausible_code(1500, seed=6),
                  "t3": _plausible_code(3000, seed=8)}
    sw = {n: _sample_from_words(w, n) for n, w in trees_wide.items()}
    mw = matrix(sw, ["t1", "t2", "t3"], k)
    spw = span(mw)
    c.add("D3  the void verdict does not fire on a corpus that spans", spw >= VOID_SPAN,
          "span %.4f over %d cell(s)" % (spw, len(mw)))

    ok_named = named_cell(mw, "t1", "t2") is not None
    missing = named_cell(mw, "t1", "nope")
    c.add("D4  a named cell that is not in the matrix is refused",
          ok_named and missing is None, "t1/t2 found, t1/nope refused")

    # D5 -- the floor verdict, in both directions, at the boundary, AND with
    # cross_v varied.  The last part is the one that took a second attempt: the
    # first version passed the same 0.1581 in all three cases, so it pinned the
    # verdict only as a function of floor_v and a mutant that ignored cross_v
    # and hard-coded 0.1581 passed every control and all 69 runner cases.  A
    # control blind to one of its two arguments is the shape M9 already found
    # once in this file.
    d5 = [floor_verdict(0.0650, 0.1581),      # the plan's floor: refuted
          floor_verdict(0.1581, 0.1581),      # equal: the tightest correct floor
          floor_verdict(0.1646, 0.1581),      # above: stands
          floor_verdict(0.1646, 0.2000),      # cross moved up under it: refuted
          floor_verdict(0.1581, 0.0650)]      # cross moved down: stands
    c.add("D5  the floor verdict follows BOTH of its arguments",
          d5 == [True, False, False, True, False],
          "0.0650/0.1581 REFUTED; equal stands; 0.1646/0.1581 stands; "
          "0.1646/0.2000 REFUTED; 0.1581/0.0650 stands")
    return c


def check_integrity(path, blob, want_bytes, want_sha):
    """Refuse bytes that are not the ones the manifest names.

    A free function, and `load_corpus` calls exactly this, because the first
    version had the check inline and D1 asserting a *separate* two-line helper
    that no production path touched -- a control on code nobody runs.
    """
    if len(blob) != want_bytes:
        raise Refused("%s: manifest says %d bytes, file is %d"
                      % (path, want_bytes, len(blob)))
    got = hashlib.sha256(blob).hexdigest()
    if got != want_sha:
        raise Refused("%s: manifest sha256 %s..., file is %s..."
                      % (path, want_sha[:16], got[:16]))


def window_stats(blob, off, size, vaddr, lo, hi):
    """(common-opcode fraction over NON-ZERO words, zero fraction, n_jal, in-range).

    `in-range` is the fraction of `j`/`jal` words whose computed target lands
    inside the executable segment, and it is the sharp one.  MIPS `j`/`jal`
    carry a 26-bit word target, so a random word points somewhere in a 256 MiB
    range and has about a 0.2 % chance of landing in a 500 KiB segment.  In
    code every one of them must land there.  Measured 2026-08-27 across the
    corpus: 1.000 inside every window, 0.000-0.043 in the 4 KiB after it, and
    0.000-0.098 over the same window read from a 2-byte offset.

    The common-opcode fraction is printed beside it and is NOT what the control
    asserts: `0x00000000` has primary opcode SPECIAL, so a run of padding scores
    as 100 % "common", and counting a zero word as an instruction is the kind of
    claim this project does not make.  Zero words are excluded and reported
    separately; the first version of this control counted them and read 0.816
    on `acltd`'s `.rodata`.
    """
    n = size // 4
    if n <= 0:
        return (0.0, 0.0, 0, None)
    z = com = nz = njal = jin = 0
    for idx in range(n):
        w = struct.unpack_from(">I", blob, off + idx * 4)[0]
        if w == 0:
            z += 1
            continue
        nz += 1
        if (w >> 26) in COMMON_OPS:
            com += 1
        if (w >> 26) in (0x02, 0x03):
            njal += 1
            pc = vaddr + idx * 4
            if lo <= ((pc & 0xF0000000) | ((w & 0x03FFFFFF) << 2)) < hi:
                jin += 1
    return (com / nz if nz else 0.0, z / n, njal, (jin / njal) if njal else None)


def _words_sample(raw, name):
    """Wrap a run of code bytes back into a scoreable ELF."""
    return Sample(blob=synth_elf(list(struct.unpack(">%dI" % (len(raw) // 4), raw))),
                  name=name)


def _word_permutation(sample, seed):
    """The same instruction multiset, in a destroyed order."""
    ws = list(struct.unpack(">%dI" % len(sample.toks),
                            sample.blob[sample.off:sample.off + sample.size]))
    random.Random(seed).shuffle(ws)
    return Sample(blob=synth_elf(ws), name="perm(%s)" % sample.name)


def _perturbation(sample, seed, frac=0.01):
    """The same code with `frac` of its words replaced at random."""
    ws = list(struct.unpack(">%dI" % len(sample.toks),
                            sample.blob[sample.off:sample.off + sample.size]))
    rnd = random.Random(seed)
    for i in rnd.sample(range(len(ws)), max(1, int(len(ws) * frac))):
        ws[i] = rnd.randrange(1 << 32)
    return Sample(blob=synth_elf(ws), name="perturbed(%s)" % sample.name)


# ---------------------------------------------------------------------------
# Matrices
# ---------------------------------------------------------------------------

def matrix(samples, order, k):
    """{(a, b): (containment, jaccard, na, nb, inter)} for every unordered pair."""
    out = {}
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a, b = order[i], order[j]
            out[(a, b)] = score(samples[a], samples[b], k)
    return out


def string_matrix(samples, order):
    out = {}
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a, b = order[i], order[j]
            out[(a, b)] = score_strings(samples[a], samples[b])
    return out


def span(m, idx=0):
    if not m:
        return None
    vals = [v[idx] for v in m.values()]
    return max(vals) - min(vals)


def named_cell(m, a, b):
    return m.get((a, b)) or m.get((b, a))


def cross_population(man, loaded, spec, k):
    """The no-shared-source level, measured at ONE denominator.

    `([(containment, program, tree, shared, |G(other)|)], reference, name)`,
    highest first.

    The reference is whichever half of `spec` carries the SMALLER feature set --
    the one that supplies containment's denominator.  The population is every
    other program in the reference's own tree whose feature set is at least as
    large, so that the reference keeps supplying the denominator throughout.
    Programs smaller than the reference are excluded on purpose: they divide
    the same few thousand grams of shared compiler idiom by a smaller number
    and score higher for that reason alone.  量 2026-08-27 inside `unit-2018`,
    over the 36 programs with at least 2,000 code words: 422 of the 630
    cross-program cells sit above 0.1646, and the top of the list is
    `sysconf`/`timelycheck` at 0.9967 -- two vendor tools that share their
    source.  "Two different programs" is not the same claim as "two programs
    that share no source", and only the second one is a floor.
    """
    pa, ta, pb, tb = spec
    a, b = loaded[pa][0][ta], loaded[pb][0][tb]
    if len(a.grams(k)) <= len(b.grams(k)):
        ref, refprog, reftree = a, pa, ta
    else:
        ref, refprog, reftree = b, pb, tb
    nref = len(ref.grams(k))
    pop = []
    for prog in man.programs():
        if prog == refprog:
            continue
        samples, _ = loaded[prog]
        if reftree not in samples:
            continue
        other = samples[reftree]
        if len(other.grams(k)) < nref:
            continue
        m = score(ref, other, k)
        pop.append((m[0], prog, reftree, m[4], len(other.grams(k))))
    pop.sort(reverse=True)
    return pop, ref, "%s/%s" % (refprog, reftree)


def resolve_cell(man, loaded, spec, k, label):
    """(containment, denominator) for a `@base`/`@floor` spec.

    Returns the denominator -- `min(|G(A)|, |G(B)|)` -- beside the score,
    because containment divides by the SMALLER feature set and a threshold is
    only meaningful at the denominator of the comparison it governs.  Leaving
    that number unprinted is how `R2a/b/d-1`'s first floor came to be compared
    against a `CROSS` measured on a set 1.46x smaller.
    """
    pa, ta, pb, tb = spec
    for prog in (pa, pb):
        if prog not in loaded:
            raise Refused("@%s names program %s, which is not in the corpus"
                          % (label.lower(), prog))
    for prog, tree in ((pa, ta), (pb, tb)):
        if tree not in loaded[prog][0]:
            raise Refused("@%s names %s/%s, which is not in the corpus"
                          % (label.lower(), prog, tree))
    a, b = loaded[pa][0][ta], loaded[pb][0][tb]
    m = score(a, b, k)
    return m[0], min(m[2], m[3])


def floor_verdict(floor_v, cross_v):
    """True when the corpus refutes the named `@floor` cell.

    Refuted means the floor sits STRICTLY BELOW `CROSS` -- the highest score
    reached by a pair that shares no source, measured at a denominator no
    smaller than the one the floor's own comparison uses.  A floor below that
    is satisfied by a pair with no shared source at all, so the warn band above
    it carries no information.  That is what happened to
    `plan/router-rebuild-plan.md:1128`'s floor: 0.0650 against 0.1581.

    **Equality is not refuted, and that changed on 2026-08-27.**  The first
    version returned `floor_v <= cross_v`, on the argument that "a floor exactly
    at the cross-program score separates nothing from nothing".  That argument
    is wrong: a floor AT the no-shared-source level is the tightest correct one
    there is -- everything at or below it is reachable by an unrelated program,
    so `fail score <= FLOOR` is exactly the claim the corpus supports.  The
    corpus turned out to hold no cell above that level that could serve, for a
    reason `notes/which-drop.md` §1 owns, so `@floor` names the `CROSS` cell
    itself and equality is the normal case rather than an edge one.

    This is a function and not an `if` inside `report_corpus` because the branch
    it picks is a verdict, and a verdict nobody has seen fire is not a verdict.
    `D5` drives it in both directions AND varies `cross_v`, on a runner with no
    vendor byte present; `tools/test-binsim.sh` drives both ends to end on two
    synthetic corpora built to land on either side, and `M11` inverts it.
    """
    return floor_v < cross_v


def print_matrix(m, order, idx, title, out=sys.stdout):
    out.write("\n  %s\n" % title)
    w = max(len(x) for x in order)
    out.write("  %-*s  %s\n" % (w, "", "  ".join("%6s" % t[:6] for t in order)))
    for i, a in enumerate(order):
        cells = []
        for j, b in enumerate(order):
            if i == j:
                cells.append("%6s" % "-")
            else:
                v = named_cell(m, a, b)
                cells.append("%6.3f" % v[idx] if v else "%6s" % "?")
        out.write("  %-*s  %s\n" % (w, a, "  ".join(cells)))


# ---------------------------------------------------------------------------
# The corpus manifest
# ---------------------------------------------------------------------------

class Manifest(object):
    def __init__(self, path):
        self.path = path
        self.rows = []            # (tree, date, program, relpath, bytes, sha, role)
        self.base = None          # (progA, treeA, progB, treeB)
        self.floor = None
        self.model = None         # one source, two compilation models
        with open(path, encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                f = [p.strip() for p in line.split("\t") if p.strip() != ""]
                if f[0] in ("@base", "@floor", "@model"):
                    # Four fields name a cell of ONE program's matrix:
                    #     @base   program  treeA  treeB
                    # Five name a cell ACROSS programs, which the matrices do
                    # not hold and which `R2a/b/d-1` needed for the floor:
                    #     @floor  progA  treeA  progB  treeB
                    # Both are stored as (progA, treeA, progB, treeB).
                    if len(f) == 4:
                        spec = (f[1], f[2], f[1], f[3])
                    elif len(f) == 5:
                        spec = (f[1], f[2], f[3], f[4])
                    else:
                        raise Refused("%s:%d: %s takes program, treeA, treeB "
                                      "or progA, treeA, progB, treeB"
                                      % (path, lineno, f[0]))
                    if spec[0] == spec[2] and spec[1] == spec[3]:
                        raise Refused("%s:%d: %s names one binary against itself"
                                      % (path, lineno, f[0]))
                    setattr(self, f[0][1:], spec)
                    continue
                if len(f) != 7:
                    raise Refused("%s:%d: need tree/date/program/relpath/bytes/sha256/role, "
                                  "tab separated, got %d field(s)" % (path, lineno, len(f)))
                self.rows.append((f[0], f[1], f[2], f[3], int(f[4]), f[5], f[6]))
        if not self.rows:
            raise Refused("%s: no rows" % path)

    def programs(self):
        seen = []
        for r in self.rows:
            if r[2] not in seen:
                seen.append(r[2])
        return seen

    def trees_for(self, program):
        rows = [r for r in self.rows if r[2] == program]
        rows.sort(key=lambda r: r[1])          # by build date
        return rows

    def role(self, program):
        roles = {r[6] for r in self.rows if r[2] == program}
        if len(roles) != 1:
            raise Refused("%s: program %s carries %d roles" % (self.path, program, len(roles)))
        return roles.pop()


def load_corpus(man, root, program, minstr):
    """{tree: Sample}, with size and sha256 checked BEFORE anything is parsed.

    The order is the point.  The first version constructed the `Sample` -- which
    parses the ELF, derives the window and tokenises it -- and compared the hash
    afterwards, while `tools/binsim-corpus.tsv` told the reader the opposite.
    """
    samples, order = {}, []
    for tree, date, prog, rel, nbytes, sha, role in man.trees_for(program):
        path = os.path.join(root, tree, "squashfs-root", rel)
        if not os.path.exists(path):
            raise Refused("corpus file missing: %s" % path)
        with open(path, "rb") as fh:
            blob = fh.read()
        check_integrity(path, blob, nbytes, sha)
        samples[tree] = Sample(blob=blob, path=path, name=tree, minstr=minstr)
        order.append(tree)
    return samples, order


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def report_pair(pa, pb, k, minstr, sweep, out=sys.stdout):
    a = Sample(path=pa, name=os.path.basename(pa), minstr=minstr)
    b = Sample(path=pb, name=os.path.basename(pb), minstr=minstr)
    out.write("\nA  %s\n   %d bytes, sha256 %s\n" % (pa, len(a.blob), a.sha256()[:32]))
    out.write("   code window file[0x%x .. 0x%x)  vaddr 0x%x  %d words\n"
              % (a.off, a.off + a.size, a.vaddr, len(a.toks)))
    out.write("B  %s\n   %d bytes, sha256 %s\n" % (pb, len(b.blob), b.sha256()[:32]))
    out.write("   code window file[0x%x .. 0x%x)  vaddr 0x%x  %d words\n"
              % (b.off, b.off + b.size, b.vaddr, len(b.toks)))

    out.write("\n  %-10s %10s %10s %10s %10s %10s\n"
              % ("channel", "contain", "jaccard", "|A|", "|B|", "|A&B|"))
    con, jac, na, nb, inter = score(a, b, k)
    out.write("  %-10s %10.4f %10.4f %10d %10d %10d   <- binsim, k=%d\n"
              % ("code", con, jac, na, nb, inter, k))
    sc, sj, sa, sb, si = score_strings(a, b)
    out.write("  %-10s %10.4f %10.4f %10d %10d %10d   config, not toolchain\n"
              % ("strings", sc, sj, sa, sb, si))

    if sweep:
        out.write("\n  k sweep -- the conclusion should not depend on k\n")
        out.write("  %6s %10s %10s\n" % ("k", "contain", "jaccard"))
        for kk in SWEEP_K:
            try:
                cc, jj, _, _, _ = score(a, b, kk)
                out.write("  %6d %10.4f %10.4f\n" % (kk, cc, jj))
            except Refused as ex:
                out.write("  %6d  refused: %s\n" % (kk, ex))

    fa, fb = a.elf.fingerprint(), b.elf.fingerprint()
    out.write("\n  container fingerprint -- read by a different instrument, "
              "from a different part of the file\n")
    for key in sorted(fa):
        mark = " " if fa[key] == fb[key] else "*"
        out.write("  %s %-13s %-38s %s\n" % (mark, key, str(fa[key])[:38], str(fb[key])[:38]))
    ndiff = sum(1 for key in fa if fa[key] != fb[key])
    out.write("  %d of %d fingerprint field(s) differ\n" % (ndiff, len(fa)))
    return 0


def corpus_label(path):
    """`<root>/<tree>/squashfs-root/bin/boa` -> `<tree>/boa`; else the basename.

    The first version printed `os.path.basename(os.path.dirname(os.path.dirname(
    path)))`, which is `squashfs-root` for every file in the corpus -- a table of
    six rows all labelled the same.
    """
    parts = os.path.normpath(path).replace("\\", "/").split("/")
    if len(parts) >= 4 and parts[-3] == "squashfs-root":
        return parts[-4] + "/" + parts[-1]
    return parts[-1]


def report_manifest(man, out=sys.stdout):
    """Parse and validate the manifest WITHOUT touching a single vendor byte.

    `tools/binsim-corpus.tsv` names `BASE`, `FLOOR` and eighteen sha256 rows, and
    until this mode existed it was opened by no code path a CI runner could
    reach: the only reader was `--corpus`, which needs the six trees. So a typo
    in `@floor`, a row with a missing field, or a `@base` naming a tree that is
    not in the corpus would have been found on one machine, by one person, on
    the day it next ran.
    """
    progs = man.programs()
    out.write("\n  %s\n  %d row(s), %d program(s)\n" % (man.path, len(man.rows), len(progs)))
    for p in progs:
        rows = man.trees_for(p)
        out.write("    %-10s role %-9s %d tree(s): %s\n"
                  % (p, man.role(p), len(rows), ", ".join(r[0] for r in rows)))
    bad = []
    for label, spec in (("@base", man.base), ("@floor", man.floor)):
        if spec is None:
            bad.append("%s is not declared" % label)
            continue
        pa, ta, pb, tb = spec
        for prog, tree in ((pa, ta), (pb, tb)):
            if prog not in progs:
                bad.append("%s names program %s, which is not in the manifest"
                           % (label, prog))
                continue
            if tree not in [r[0] for r in man.trees_for(prog)]:
                bad.append("%s names tree %s, which %s does not have"
                           % (label, tree, prog))
        if pa == pb and ta == tb:
            bad.append("%s names one binary against itself" % label)
        if pa == pb:
            out.write("  %-6s %s: %s vs %s\n" % (label, pa, ta, tb))
        else:
            out.write("  %-6s %s/%s vs %s/%s  (across programs)\n"
                      % (label, pa, ta, pb, tb))
    for tree, date, prog, rel, nbytes, sha, role in man.rows:
        if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
            bad.append("%s/%s: sha256 is not 64 hex characters" % (tree, prog))
        if nbytes <= 0:
            bad.append("%s/%s: byte count %d" % (tree, prog, nbytes))
    if bad:
        raise Refused("%s: %s" % (man.path, "; ".join(bad)))
    out.write("  every @base/@floor cell names a tree the manifest carries; "
              "all %d sha256 fields well-formed\n" % len(man.rows))
    return 0


def report_fingerprints(paths, out=sys.stdout):
    """One row per field, one column per file.

    Transposed because the fields are wide and of wildly different widths -- a
    `DT_NEEDED` list beside a one-digit `phnum` -- and a row-per-file table of
    them cannot be read, which is what the first version produced.
    """
    fps = []
    for p in paths:
        with open(p, "rb") as fh:
            fps.append((corpus_label(p), Elf(fh.read(), corpus_label(p)).fingerprint()))
    keys = sorted(fps[0][1])
    kw = max(len(k) for k in keys)
    cols = [max(len(lbl), *(len(str(f[k])) for k in keys)) for lbl, f in fps]
    out.write("\n  %-*s  %s\n" % (kw, "field",
                                  "  ".join("%-*s" % (w, lbl)
                                            for (lbl, _), w in zip(fps, cols))))
    for k in keys:
        vals = [str(f[k]) for _, f in fps]
        mark = " " if len(set(vals)) == 1 else "*"
        out.write("%s %-*s  %s\n" % (mark, kw, k,
                                     "  ".join("%-*s" % (w, v)
                                               for v, w in zip(vals, cols))))
    ndiff = sum(1 for k in keys if len({str(f[k]) for _, f in fps}) != 1)
    out.write("  %d of %d field(s) differ across %d file(s); `*` marks them\n"
              % (ndiff, len(keys), len(fps)))
    return 0


def report_corpus(man, root, k, minstr, sweep, urandom, out=sys.stdout):
    """The corpus controls, then the matrices.  In that order, and it stops if
    a control fails."""
    rc = 0
    ec = Controls()
    loaded = {}
    for prog in man.programs():
        loaded[prog] = load_corpus(man, root, prog, minstr)

    # -- E0: one corpus, one ISA --------------------------------------------
    # The ELF parser already refuses a little-endian or non-MIPS file, so an
    # MT7628 image cannot get in (讀 2026-08-27 on TOTOLINK N350RT V9.3.5u:
    # `ELF data 1, not MSB`, exit 2). What it does NOT catch is a big-endian
    # MIPS32r2 part, which would parse, score, and quietly move FLOOR. The
    # corpus's membership rule is "the same ISA", and this is where it is
    # enforced rather than left in a comment.
    arches = {}
    for prog, (samples, order) in loaded.items():
        for tree in order:
            f = samples[tree].elf.e_flags
            arches.setdefault(EF_MIPS_ARCH_NAMES.get(f & EF_MIPS_ARCH_MASK,
                                                     "arch?0x%x" % (f & EF_MIPS_ARCH_MASK)),
                              []).append("%s/%s" % (prog, tree))
    ec.add("E0  every sample in the corpus is the same ISA", len(arches) == 1,
           "; ".join("%s: %d file(s)%s" % (a, len(v), "" if len(arches) == 1
                                           else " (" + ", ".join(v) + ")")
                     for a, v in sorted(arches.items())))

    # -- E1: the identity anchor ---------------------------------------------
    for prog in man.programs():
        if man.role(prog) != "identity":
            continue
        samples, order = loaded[prog]
        m = matrix(samples, order, k)
        sp = span(m)
        allone = all(v[0] == 1.0 and v[1] == 1.0 for v in m.values())
        ec.add("E1  %s: %d cells at exactly 1.0, and void fires" % (prog, len(m)),
               allone and sp < VOID_SPAN,
               "span %.4f -- one sha256 in %d trees, so this is what a metric "
               "with nothing to measure must look like" % (sp, len(order)))

    # -- E4: the code window against the section table, where one survives ----
    checked, bad = 0, []
    for prog, (samples, order) in loaded.items():
        for tree in order:
            s = samples[tree]
            secs = s.elf.sections()
            if not secs:
                continue
            byname = {n: (a, o, sz) for n, a, o, sz in secs}
            if ".init" not in byname or ".fini" not in byname:
                continue
            checked += 1
            want_off = byname[".init"][1]
            want_end = byname[".fini"][1]
            if s.off != want_off or s.off + s.size != want_end:
                bad.append("%s/%s: window [0x%x,0x%x) vs .init/.fini [0x%x,0x%x)"
                           % (prog, tree, s.off, s.off + s.size, want_off, want_end))
    if checked == 0:
        ec.na("E4  DT window equals .init..fini where sections survive",
              "no file in this corpus kept a section table; E4b carries the whole "
              "window check here")
    else:
        ec.add("E4  DT window equals .init..fini where sections survive", not bad,
               "%d file(s) still have a section table" % checked
               + ("; " + "; ".join(bad) if bad else ""))

    # -- E4b: the window is code, by a decoding invariant rather than a
    # frequency, on the eight files E4 cannot reach because their section
    # header table is gone.
    MIN_JAL = 32
    ins, aft, mis, bad4b, na, covered = [], [], [], [], [], set()
    thin, total = [], []
    for prog, (samples, order) in loaded.items():
        for tree in order:
            s = samples[tree]
            total.append((prog, tree))
            if s.elf.sections():
                covered.add((prog, tree))          # E4 has it
            lo = hi = None
            for ph in s.elf.phdrs:
                if ph["type"] == PT_LOAD and (ph["flags"] & PF_X):
                    lo, hi = ph["vaddr"], ph["vaddr"] + ph["filesz"]
            a = window_stats(s.blob, s.off, s.size, s.vaddr, lo, hi)
            nafter = min(4096, len(s.blob) - s.off - s.size)
            b = window_stats(s.blob, s.off + s.size, nafter, s.vaddr + s.size, lo, hi)
            # the negative control on this control: the same bytes, misaligned
            d = window_stats(s.blob, s.off + 2, s.size - 4, s.vaddr, lo, hi)
            if a[2] < MIN_JAL:
                na.append("%s/%s (%d j/jal)" % (prog, tree, a[2]))
                continue
            covered.add((prog, tree))
            ins.append(a[3])
            # The `after` and `misaligned` figures are the negative controls'
            # descriptive range, and a ratio over three words is not a range.
            # 讀 2026-08-27, when pppd/v3.4.0 joined the corpus as a baseline:
            # ONE j/jal word sits in the 4 KiB after its window, it happens to
            # land in the executable segment, and the summary line went from
            # "after 0.000-0.043" to "after 0.000-1.000" on a sample of one.
            # The assertion never moved -- it is on `ins` and `mis` -- but the
            # printed range is what a reader checks, so it is gated too.
            if b[3] is not None and b[2] >= MIN_JAL:
                aft.append(b[3])
            elif b[3] is not None:
                thin.append(b[2])
            if d[3] is not None:
                mis.append(d[3])
            if a[3] < 0.99:
                bad4b.append("%s/%s inside %.3f" % (prog, tree, a[3]))
            if d[3] is not None and d[3] >= 0.30:
                bad4b.append("%s/%s misaligned %.3f -- the control cannot fail"
                             % (prog, tree, d[3]))
    ec.add("E4b every j/jal in the window targets the executable segment",
           ins and not bad4b and set(total) == covered,
           "%d file(s): in-window %.3f-%.3f, after %.3f-%.3f over %d file(s) with "
           ">= %d j/jal there%s, misaligned %.3f-%.3f; n/a %s; every file covered "
           "by E4 or E4b: %s"
           % (len(ins), min(ins), max(ins), min(aft or [0]), max(aft or [0]),
              len(aft), MIN_JAL,
              (", %d file(s) too thin to summarise there (%d-%d j/jal)"
               % (len(thin), min(thin), max(thin))) if thin else "",
              min(mis or [0]), max(mis or [0]),
              ", ".join(na) or "none", set(total) == covered)
           + ("; " + "; ".join(bad4b) if bad4b else ""))

    # -- E2: every pair whose code window is byte-identical must be exactly 1.0
    # Derived from the material rather than from a tree name written into this
    # file: `acltd` supplies fifteen such pairs and busybox supplies one, and a
    # metric that does not return exactly 1.0 for them is not measuring code.
    same, notone = [], []
    for prog, (samples, order) in loaded.items():
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                a, b = samples[order[i]], samples[order[j]]
                if a.blob[a.off:a.off + a.size] != b.blob[b.off:b.off + b.size]:
                    continue
                same.append((prog, order[i], order[j], a.sha256() == b.sha256()))
                v = score(a, b, k)
                if v[0] != 1.0 or v[1] != 1.0:
                    notone.append("%s %s/%s -> %.6f/%.6f"
                                  % (prog, order[i], order[j], v[0], v[1]))
    # The half that CAN fail. Asserting that byte-identical windows score 1.0 is
    # f(x) == f(x): forced for any deterministic set-valued metric at any k, and
    # green under every mutation this suite has. What is falsifiable is the
    # converse -- a tokeniser that collapsed its alphabet, or a k short enough to
    # saturate, would put pairs that are NOT identical at Jaccard 1.0 too.
    #
    # Containment does saturate, and it is measured rather than argued: 讀
    # 2026-08-27 there are 16 byte-identical pairs and **17** cells at
    # containment exactly 1.000. The extra one is busybox unit-2018 /
    # n200re-3.2.0, whose smaller 7-gram set is a strict subset of the larger --
    # Jaccard 0.9673. So containment 1.000 does not mean identical, and only
    # Jaccard can carry this control.
    satur = []
    for prog, (samples, order) in loaded.items():
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                a, b = samples[order[i]], samples[order[j]]
                if a.blob[a.off:a.off + a.size] == b.blob[b.off:b.off + b.size]:
                    continue
                v = score(a, b, k)
                if v[1] == 1.0:
                    notone.append("%s %s/%s: NOT identical yet jaccard 1.0"
                                  % (prog, order[i], order[j]))
                if v[0] == 1.0:
                    satur.append("%s %s/%s (jaccard %.4f)"
                                 % (prog, order[i], order[j], v[1]))
    ec.add("E2  identical windows are 1.0, and only identical ones reach jaccard 1.0",
           len(same) > 0 and not notone,
           "%d byte-identical pair(s), all 1.0/1.0 -- which is forced, not "
           "evidence; the falsifiable half is that no OTHER pair reaches "
           "jaccard 1.0, and none does. Containment saturates on %d of them: %s"
           % (len(same), len(satur), "; ".join(satur) or "none")
           + ("; " + "; ".join(notone) if notone else ""))

    # -- E2b: the two channels are not the same measurement -------------------
    # The eight-byte busybox pair differs ONLY in the digits of the BusyBox
    # banner's build date, which is in .rodata and outside the code window.  So
    # the code channel must say 1.0 and the strings channel must not.
    split = []
    for prog, ta, tb, samefile in same:
        if samefile:
            continue
        sa, sb = loaded[prog][0][ta], loaded[prog][0][tb]
        cj = score(sa, sb, k)[1]
        sj = score_strings(sa, sb)[1]
        split.append((prog, ta, tb, cj, sj))
    if not split:
        ec.na("E2b a pair with identical code and different files splits the channels",
              "no pair in this corpus has identical code windows and different files, "
              "so nothing here can separate the two channels")
    else:
        ec.add("E2b a pair with identical code and different files splits the channels",
               all(cj == 1.0 and sj < 1.0 for _, _, _, cj, sj in split),
               "; ".join("%s %s/%s code %.4f strings %.4f" % s for s in split))

    subjects = [p for p in man.programs() if man.role(p) == "subject"]

    # -- the metric's reproducibility, and it is NOT zero -------------------
    # The first version set `noise = 0.0` as a literal, gated on E2 passing, and
    # printed it as though it had been measured. It had not: the pairs E2
    # selects are chosen BY byte-equality of the window it then scores, so 1.0
    # is arithmetic, not a reading.
    #
    # A reproducibility error needs two builds of the same source whose windows
    # are NOT identical. This corpus has such pairs on the busybox side, and
    # calling them "the same source" is 推 -- inferred from BusyBox 1.13.4's
    # banner and a window differing by two words -- not 讀. So the number below
    # is an estimate with a stated inference in it, and it is reported that way.
    noise, noise_from = None, ""
    cands = []
    for prog, (samples, order) in loaded.items():
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                a, b = samples[order[i]], samples[order[j]]
                if a.blob[a.off:a.off + a.size] == b.blob[b.off:b.off + b.size]:
                    continue
                v = score(a, b, k)
                if v[1] >= 0.99:
                    cands.append((1.0 - v[1], prog, order[i], order[j], v[1]))
    if cands:
        cands.sort()
        noise = cands[0][0]
        # The MINIMUM of a set, and the set has to be named. Until 2026-08-27
        # this printed one pair and `notes/binsim.md` said "The corpus has one",
        # which the code did not agree with: on the real corpus `cands` holds
        # three, and the largest is 5.3x the smallest. For an error bar the
        # minimum is the anti-conservative end, so the whole range is printed
        # and the guard below still uses the tightest of them -- which is the
        # harder bar for `BASE - FLOOR` to clear.
        noise_from = "%s %s/%s, jaccard %.6f" % (cands[0][1], cands[0][2],
                                                 cands[0][3], cands[0][4])
        if len(cands) > 1:
            noise_from += ("; the SMALLEST of %d candidate pair(s), which run "
                           "%.2e-%.2e (%s %s/%s is the largest)"
                           % (len(cands), cands[0][0], cands[-1][0],
                              cands[-1][1], cands[-1][2], cands[-1][3]))

    # -- E5: C3/C4/C5 again, on real material rather than on a fixture -------
    # The fixture cannot reproduce the k-gram saturation that made k=4 fail, so
    # this is the version of those three that constrains anything. It used to be
    # printed and not asserted, which is a number nobody checks.
    ref5 = None
    for prog in subjects:
        for tree, s in loaded[prog][0].items():
            if tree == "unit-2018" and ref5 is None:
                ref5 = s
    if ref5 is None and subjects:
        ref5 = loaded[subjects[0]][0][loaded[subjects[0]][1][0]]
    e5 = {}
    if ref5 is not None:
        nb5 = len(ref5.toks) * 4
        rb5 = (os.urandom(nb5) if urandom else
               bytes(random.Random(20260827).randrange(256) for _ in range(nb5)))
        raw5 = ref5.blob[ref5.off:ref5.off + ref5.size]
        bs5 = bytearray(raw5)
        random.Random(11).shuffle(bs5)
        e5["random"] = score(_words_sample(rb5, "rand"), ref5, k)[0]
        e5["bytes"] = score(_words_sample(bytes(bs5), "byte"), ref5, k)[0]
        perm5 = _word_permutation(ref5, 12)
        e5["words_k"] = score(perm5, ref5, k)[0]
        e5["words_1"] = score(perm5, ref5, 1)[0]
        ec.add("E5  the three negative controls, on %s/%s" % (subjects[0], ref5.name),
               e5["random"] < 0.02 and e5["bytes"] < 0.02
               and e5["words_k"] < NULL_MAX and e5["words_1"] > 0.99,
               "random %.4f, byte-permutation %.4f, word-permutation %.4f at k=%d "
               "and %.4f at k=1 -- the last pair is one control: k=1 near 1.0 is "
               "what makes k=%d mean order" % (e5["random"], e5["bytes"],
                                               e5["words_k"], k, e5["words_1"], k))

    # -- E6: the k-selection rule, re-run rather than remembered --------------
    nulls, sens = {}, None
    for prog in subjects:
        samples, order = loaded[prog]
        for tree in order:
            s = samples[tree]
            for kk in (k - 1, k):
                if kk < 1:
                    continue
                nulls[(prog, tree, kk)] = score(_word_permutation(s, 1200 + kk), s, kk)[0]
    ref = None
    for prog in subjects:
        for tree, s in loaded[prog][0].items():
            if tree == "unit-2018" and ref is None:
                ref = s
    if ref is None:
        ref = loaded[subjects[0]][0][loaded[subjects[0]][1][0]]
    sens = score(_perturbation(ref, 4242), ref, k)[0]
    at_k = [v for kk, v in ((key[2], v) for key, v in nulls.items()) if kk == k]
    at_km1 = [v for kk, v in ((key[2], v) for key, v in nulls.items()) if kk == k - 1]
    ec.add("E6  k=%d satisfies the pre-registered rule on this corpus" % k,
           all(v < NULL_MAX for v in at_k) and sens >= SENS_MIN,
           "null at k=%d is %.4f-%.4f over %d binaries (all < %.2f); "
           "sensitivity %.4f >= %.2f" % (k, min(at_k), max(at_k), len(at_k),
                                         NULL_MAX, sens, SENS_MIN))
    # Minimality is a separate claim, and it is one only a corpus with enough
    # structure can make.  Asserting it unconditionally would turn every
    # simpler corpus red for a property of the corpus rather than of the pin.
    if at_km1 and any(v >= NULL_MAX for v in at_km1):
        ec.add("E6b ... and no smaller k does", True,
               "at k=%d the null is %.4f-%.4f, and %d of %d binaries are at or "
               "above %.2f" % (k - 1, min(at_km1), max(at_km1),
                               sum(1 for v in at_km1 if v >= NULL_MAX),
                               len(at_km1), NULL_MAX))
    else:
        ec.na("E6b ... and no smaller k does",
              "k=%d already satisfies the null here (%.4f-%.4f), so this corpus "
              "shows k=%d sufficient but not minimal"
              % (k - 1, min(at_km1 or [0]), max(at_km1 or [0]), k))

    # -- E7/E8: the floor and the precondition it implies --------------------
    # These are computed HERE, with the other corpus controls, and not down
    # beside the section that prints them. The first version added them after
    # `ec.report()` had already run, so they were silently never reported --
    # which is the same shape as E5 printing a number nobody asserted.
    fpop, fref, frefname, fval, mval = [], None, "", None, None
    if man.floor:
        try:
            fval = resolve_cell(man, loaded, man.floor, k, "floor")[0]
            fpop, fref, frefname = cross_population(man, loaded, man.floor, k)
        except Refused as ex:
            ec.add("E7  FLOOR is the highest denominator-matched no-shared-source cell",
                   False, "refused: %s" % ex)
    if fval is not None and len(fpop) >= 2:
        top = fpop[0]
        ec.add("E7  FLOOR is the highest denominator-matched no-shared-source cell",
               abs(fval - top[0]) < 1e-12,
               "%.6f at %d grams over %d program(s): %s"
               % (fval, len(fref.grams(k)), len(fpop),
                  ", ".join("%s %.4f" % (p, v) for v, p, _, _, _ in fpop)))
    elif man.floor:
        ec.na("E7  FLOOR is the highest denominator-matched no-shared-source cell",
              "this corpus holds %d program(s) at or above the reference's feature-set "
              "size, so there is no population to take a maximum over" % len(fpop))
    if man.model:
        try:
            mval = resolve_cell(man, loaded, man.model, k, "model")[0]
        except Refused as ex:
            ec.add("E8  one source under two compilation models lands at or below FLOOR",
                   False, "refused: %s" % ex)
    if mval is not None and fval is not None:
        ec.add("E8  one source under two compilation models lands at or below FLOOR",
               mval <= fval,
               "%s %s/%s = %.4f against FLOOR %.4f -- this is what makes a model "
               "mismatch VOID rather than a fail"
               % (man.model[0], man.model[1], man.model[3], mval, fval))
    else:
        ec.na("E8  one source under two compilation models lands at or below FLOOR",
              "the manifest names no @model pair, so this corpus cannot say what a "
              "compilation-model change alone costs")

    cross = []
    if len(subjects) >= 2:
        pa, pb = subjects[0], subjects[1]
        common = [t for t in loaded[pa][1] if t in loaded[pb][0]]
        for t in common:
            cc = score(loaded[pa][0][t], loaded[pb][0][t], k)
            cross.append((t, cc[0]))

    if ec.failed:
        ec.report(out)
        out.write("\nREFUSED: %d corpus control(s) failed; no matrix printed.\n"
                  % len(ec.failed))
        return 2

    ec.report(out)

    # -- the container partition, before any score ---------------------------
    out.write("\n=== container fingerprint: what a different instrument already says ===\n")
    prog0 = subjects[0] if subjects else man.programs()[0]
    samples, order = loaded[prog0]
    groups = {}
    for t in order:
        f = samples[t].elf.fingerprint()
        key = (f["e_flags"], f["phnum"], f["pltgot"], f["needed"], f["sections"])
        groups.setdefault(key, []).append(t)
    out.write("  %s: %d group(s) over %d trees\n" % (prog0, len(groups), len(order)))
    for key, ts in groups.items():
        out.write("    %-34s %s\n" % (", ".join(ts), key[0]))
        out.write("    %-34s phdrs %s, pltgot %s, sections %s\n"
                  % ("", key[1], key[2], key[4]))
        out.write("    %-34s needed %s\n" % ("", key[3]))

    # -- the matrices --------------------------------------------------------
    for prog in man.programs():
        samples, order = loaded[prog]
        role = man.role(prog)
        m = matrix(samples, order, k)
        sm = string_matrix(samples, order)
        out.write("\n=== %s -- %d trees, %d pairwise cells (%s) ===\n"
                  % (prog, len(order), len(m), role))
        out.write("  %-14s %10s %10s %10s %s\n"
                  % ("tree", "bytes", "code words", "|G(%d)|" % k, "date"))
        for tree, date, _, _, nbytes, _, _ in man.trees_for(prog):
            out.write("  %-14s %10d %10d %10d %s\n"
                      % (tree, nbytes, len(samples[tree].toks),
                         len(samples[tree].grams(k)), date))
        # A `baseline` program is in the corpus to supply a denominator-matched
        # comparand, not to be clustered. It has as few as one tree, so it has
        # no matrix and the void verdict -- which is a statement about a
        # SUBJECT's fifteen cells -- does not apply to it.
        if role == "baseline":
            out.write("  (%s is a baseline: it is scored against the FLOOR cell's\n"
                      "  reference and is not matrixed, so the void verdict is not "
                      "its verdict)\n" % prog)
            if len(m) == 1:
                cell = list(m.values())[0]
                out.write("  its one cell: containment %.4f, jaccard %.4f\n"
                          % (cell[0], cell[1]))
            continue
        print_matrix(m, order, 0, "binsim -- containment of code %d-grams" % k, out)
        print_matrix(m, order, 1, "jaccard of the same sets (carries the length term)", out)
        print_matrix(sm, order, 0, "strings -- containment (config, not toolchain)", out)

        sp = span(m)
        spj = span(m, 1)
        out.write("\n  span of the %d cells: containment %.4f, jaccard %.4f\n"
                  % (len(m), sp, spj))
        if role == "subject":
            if sp < VOID_SPAN:
                out.write("  VOID  the plan's failure condition fired: the %d scores span "
                          "%.1f pp, under %.1f. No drop is identified from %s.\n"
                          % (len(m), sp * 100, VOID_SPAN * 100, prog))
                rc = max(rc, 1)
            else:
                out.write("  the metric discriminates on %s: %.1f pp > %.1f pp\n"
                          % (prog, sp * 100, VOID_SPAN * 100))
        else:
            out.write("  (%s is the identity anchor; a span of 0 here is the control, "
                      "not a result)\n" % prog)

        if sweep:
            out.write("\n  k sweep on this matrix's span -- if the ordering moves with k,\n"
                      "  the ordering is a property of k and not of the corpus\n")
            out.write("  %6s %10s %10s %s\n" % ("k", "span", "min", "top pair"))
            for kk in SWEEP_K:
                try:
                    mk = matrix(samples, order, kk)
                    tp = max(mk.items(), key=lambda kv: kv[1][0])
                    out.write("  %6d %10.4f %10.4f %s/%s %.4f\n"
                              % (kk, span(mk), min(v[0] for v in mk.values()),
                                 tp[0][0], tp[0][1], tp[1][0]))
                except Refused as ex:
                    out.write("  %6d  refused: %s\n" % (kk, ex))

    # -- BASE and FLOOR, which are named cells and not thresholds I chose -----
    out.write("\n=== BASE and FLOOR -- named cells of the matrix above ===\n")
    if not man.base or not man.floor:
        out.write("  the manifest names neither; nothing to report\n")
        return max(rc, 2)
    vals, dens = {}, {}
    for label, spec in (("BASE", man.base), ("FLOOR", man.floor)):
        cell, den = resolve_cell(man, loaded, spec, k, label)
        vals[label] = cell
        dens[label] = den
        pa, ta, pb, tb = spec
        if pa == pb:
            out.write("  %-6s binsim(%s, %s) on %s = %.4f   denominator %d grams\n"
                      % (label, ta, tb, pa, cell, den))
        else:
            out.write("  %-6s binsim(%s/%s, %s/%s) = %.4f   denominator %d grams\n"
                      % (label, pa, ta, pb, tb, cell, den))

    gap = vals["BASE"] - vals["FLOOR"]
    out.write("  BASE - FLOOR = %.4f (%.1f pp)\n" % (gap, gap * 100))
    if noise is not None:
        out.write("  reproducibility error, ESTIMATED, not measured = %.2e\n"
                  "         from %s\n"
                  "         Two builds whose windows are byte-identical score 1.000 by\n"
                  "         arithmetic, so they cannot measure this. The pair above is\n"
                  "         the nearest thing the corpus has: same program, windows two\n"
                  "         words apart. Calling it one source is inferred, not read.\n"
                  % (noise, noise_from))
        if gap <= noise:
            out.write("  VOID  BASE and FLOOR are not separated by more than the "
                      "estimated reproducibility error.\n")
            rc = max(rc, 1)
        else:
            out.write("  BASE - FLOOR clears it by %.0fx\n" % (gap / noise))
    else:
        out.write("  reproducibility error: UNDETERMINED on this corpus -- it holds no\n"
                  "         pair of builds from one source whose code windows differ,\n"
                  "         and identical windows score 1.000 by arithmetic\n")

    # -- CROSS, at the denominator of the comparison the floor governs -------
    pop, ref, refname = cross_population(man, loaded, man.floor, k)
    if pop:
        out.write("\n=== CROSS -- what a pair with NO SHARED SOURCE reaches ===\n")
        out.write(
            "  Containment divides by the SMALLER feature set, so this level is not a\n"
            "  constant of the corpus: it is roughly (shared compiler idiom) over\n"
            "  |G(smaller)|. A threshold is only meaningful at the denominator of the\n"
            "  comparison it governs, which is why these are the pairs where the FLOOR\n"
            "  cell's own reference binary supplies it -- everything else in the tree is\n"
            "  smaller, and would divide the same idiom by a smaller number.\n")
        out.write("  reference %s, %d grams\n" % (refname, len(ref.grams(k))))
        for v, prog, tree, inter, ng in pop:
            out.write("    vs %-10s %-14s %.4f   %5d shared   (%d grams)\n"
                      % (prog, tree, v, inter, ng))
        worst = pop[0][0]
        out.write("  CROSS  = %.4f (the highest of %d, at this denominator)\n"
                  % (worst, len(pop)))
        out.write("  FLOOR  = %.4f\n" % vals["FLOOR"])

        if floor_verdict(vals["FLOOR"], worst):
            out.write("""
  REFUTED: FLOOR is below CROSS, so the rule built on it has a band that carries
  no information. `plan/router-rebuild-plan.md:1128` reads

      pass    binsim(rebuild, unit-2018) >= BASE
      warn    between FLOOR and BASE
      fail    <= FLOOR

  and a rebuild scoring anywhere in [%.4f, %.4f) would be "warn" while being
  LESS like the reference than a program that shares no source with it is. The
  band that carries evidence starts at CROSS, not below it. Which cell FLOOR is
  and why is `notes/which-drop.md`'s to say, so this exits 1 rather than quietly
  substituting a number of its own.
""" % (vals["FLOOR"], worst))
            rc = max(rc, 1)
        elif abs(vals["FLOOR"] - worst) < 1e-12:
            out.write("  FLOOR is the CROSS cell itself -- the tightest floor the corpus\n"
                      "  supports. Everything at or below it is reachable by a pair that\n"
                      "  shares no source, so `fail score <= FLOOR` is exactly the claim\n"
                      "  the material makes, and nothing weaker would be.\n")
        else:
            marg = vals["FLOOR"] - worst
            out.write("  FLOOR is above CROSS by %.4f (%.2f pp), so it is narrower than\n"
                      "  'both were built by this toolchain'.\n" % (marg, marg * 100))

        # Now that FLOOR names the CROSS cell, the two are equal by
        # construction at the pinned k and a "margin" says nothing. What the
        # sweep still measures, and what it is now written to show, is whether
        # the NAMED cell stays the top of its population as k moves: if some
        # other program overtakes it, the named floor is below the level a
        # pair with no shared source reaches, and the verdict fires.
        out.write("\n  Does the named cell stay the top of that population as k moves?\n"
                  "  If another program overtakes it, FLOOR is below the no-shared-source\n"
                  "  level and the verdict fires. The pinned k is %d; E6/E6b are what\n"
                  "  admit or exclude a value of k, and they are re-run above.\n" % k)
        out.write("  %6s %10s %10s  %-18s %-10s %s\n"
                  % ("k", "FLOOR", "CROSS", "reference", "top of pop", ""))
        for kk in SWEEP_K:
            try:
                fv = resolve_cell(man, loaded, man.floor, kk, "floor")[0]
                kpop, _, kref = cross_population(man, loaded, man.floor, kk)
                if not kpop:
                    # A row that vanishes silently is the failure this project
                    # keeps finding, so say why rather than skipping.
                    out.write("  %6d  no population: at this k nothing in the tree is "
                              "at least as large as %s\n" % (kk, kref))
                    continue
                cv, cp = kpop[0][0], kpop[0][1]
            except Refused as ex:
                out.write("  %6d  refused: %s\n" % (kk, ex))
                continue
            out.write("  %6d %10.4f %10.4f  %-18s %-10s %s%s\n"
                      % (kk, fv, cv, kref, cp,
                         "REFUTED" if floor_verdict(fv, cv) else "stands",
                         "" if kk >= k else "   (below the pinned k)"))
        out.write("  The reference is whichever half of the FLOOR cell carries the\n"
                  "  SMALLER feature set, so it can change with k -- 讀, it does at\n"
                  "  k=16 on this corpus. A row whose reference is not the pinned k's\n"
                  "  is answering a different question and is marked by that column.\n")

    # -- the precondition the floor implies, measured rather than argued -----
    if man.model:
        mv, mden = resolve_cell(man, loaded, man.model, k, "model")
        pa, ta, pb, tb = man.model
        out.write("\n=== the compilation-model precondition ===\n")
        out.write("  One upstream source, built under two compilation models, at a\n"
                  "  denominator comparable to the floor's reference:\n")
        out.write("    %s %s / %s = %.4f   denominator %d grams\n"
                  % (pa, ta, tb, mv, mden))
        if pop and mv <= vals["FLOOR"]:
            out.write("  That is AT OR BELOW the floor. So at this scale the code channel\n"
                      "  cannot tell 'the same source built differently' from 'a program\n"
                      "  that shares no source': a comparison across a compilation-model\n"
                      "  change is VOID, not a fail, and the container fingerprint has to\n"
                      "  be checked before the score is read at all.\n")
        else:
            out.write("  That is ABOVE the floor, so a model change alone does not sink a\n"
                      "  comparison on this corpus and the precondition below is not\n"
                      "  derived from this reading.\n")
        # The assertion itself is E8, registered with the other corpus controls
        # above so that it is reported rather than added after ec.report() has
        # already run. This block only prints what E8 checked.
    else:
        out.write("\n=== the compilation-model precondition ===\n")
        out.write("  UNDETERMINED: the manifest names no `@model` pair, so this corpus\n"
                  "  cannot say what a model change alone costs.\n")

    if cross:
        out.write("\n  For context, and NOT the number the verdict used: %s against %s\n"
                  "  inside each tree, where each tree's own %s supplies the denominator,\n"
                  "  runs %.4f-%.4f. So the level is a property of the corpus rather than\n"
                  "  of one pair -- but the six values are six different denominators.\n"
                  % (subjects[0], subjects[1], subjects[0],
                     min(v for _, v in cross), max(v for _, v in cross)))

    # -- E5's numbers, printed beside the verdict they already produced ------
    if e5:
        out.write("\n=== E5: the negative controls, on real material (%s/%s, %d code "
                  "words) ===\n" % (subjects[0], ref5.name, len(ref5.toks)))
        out.write("  %-44s %.4f  (%s)\n"
                  % ("random bytes", e5["random"],
                     "/dev/urandom" if urandom else "seeded PRNG"))
        out.write("  %-44s %.4f\n" % ("byte-permutation, same byte histogram",
                                      e5["bytes"]))
        out.write("  %-44s %.4f   and %.4f at k=1\n"
                  % ("word-permutation, same instruction multiset",
                     e5["words_k"], e5["words_1"]))
        out.write("  k=1 on the word-permutation is ~1.0 by construction -- it is the\n"
                  "  same instruction multiset. That is what makes the k=%d number mean\n"
                  "  order rather than composition.\n" % k)
    return rc


# ---------------------------------------------------------------------------

def die(msg, code=3):
    sys.stderr.write("binsim: %s\n" % msg)
    raise SystemExit(code)


def main(argv):
    mode = "pair"
    k = DEFAULT_K
    minstr = DEFAULT_MIN_STRING
    sweep = False
    urandom = False
    manifest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binsim-corpus.tsv")
    root = os.path.join(os.environ.get("FWRE_WORK", "/home/key/fwre-work"), "extracted")
    files = []

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--self-test":
            mode = "self-test"; i += 1
        elif a == "--corpus":
            mode = "corpus"; i += 1
            if i < len(argv) and not argv[i].startswith("-"):
                manifest = argv[i]; i += 1
        elif a == "--check-manifest":
            mode = "check-manifest"; i += 1
            if i < len(argv) and not argv[i].startswith("-"):
                manifest = argv[i]; i += 1
        elif a == "--fingerprint":
            mode = "fingerprint"; i += 1
        elif a == "--root":
            root = argv[i + 1]; i += 2
        elif a == "-k":
            k = int(argv[i + 1]); i += 2
        elif a == "--min-string":
            minstr = int(argv[i + 1]); i += 2
        elif a == "--sweep":
            sweep = True; i += 1
        elif a == "--urandom":
            urandom = True; i += 1
        elif a in ("-h", "--help"):
            sys.stdout.write(__doc__)
            return 0
        elif a.startswith("-"):
            die("unknown argument %s" % a)
        else:
            files.append(a); i += 1

    if k < 1:
        die("-k must be >= 1")

    sys.stdout.write("binsim %s -- controls first, results after\n" % VERSION)
    try:
        c = run_controls(k=k, urandom=urandom)
    except Refused as ex:
        die("a control refused: %s" % ex, 2)
    c.report()
    nfail = len(c.failed)
    if nfail:
        sys.stdout.write("\nREFUSED: a control failed, so nothing is reported.\n")
        return 2

    if mode == "self-test":
        return 0

    try:
        if mode == "check-manifest":
            return report_manifest(Manifest(manifest))
        if mode == "fingerprint":
            if not files:
                die("--fingerprint takes one or more files")
            return report_fingerprints(files)
        if mode == "corpus":
            man = Manifest(manifest)
            return report_corpus(man, root, k, minstr, sweep, urandom)
        if len(files) != 2:
            die("give two files, or --corpus, or --self-test")
        return report_pair(files[0], files[1], k, minstr, sweep)
    except Refused as ex:
        sys.stderr.write("binsim: refused: %s\n" % ex)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
