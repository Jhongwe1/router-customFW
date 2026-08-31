# `P4a` — the reproducible build, and the row of its own DoD that is already refuted

**Owner of: `P4a`** — what "same tree built twice → same image sha256" is
measured on, which artefacts satisfy it today, which do not, and what each
non-reproducible byte turns out to be. Opened **2026-09-01** (twenty-first
session), the day after `R3` closed.

Everything in this file is 讀 or 量-**on this desk**: read out of build files
and ELF images, or produced by running a build on this workstation. **量 in this
file never means what `SPEC.md` §0 means by it** — not one line below is a
statement about silicon, and nothing here consumed a power cycle.

`P4a`'s gate-board definition, verbatim, because the rest of this file is read
against it: *reproducible build: same tree built twice → same image sha256, with
the positive control that changing one source byte changes it.*

---

## 1. What this gate inherits, and the two halves point opposite ways

**Two artefacts in this repository have been built twice. One is reproducible
and the other is not, and the gate's DoD is one sentence covering both.**

| artefact | built by | evidence | verdict |
|---|---|---|---|
| `rlxprobe` (bare metal, host gcc 12.4.0) | `tools/rlxprobe/Makefile` | 量 2026-08-25: `git archive 2db12bb` into a clean directory, rebuilt — `fbac7d60…`, byte-identical to the artefact `R1d` was measured on. `RUNSHEET.md` §「a `sha256` that is not one of these」 | 🟢 reproducible **across a checkout** |
| the kernel `vmlinux` (rsdk 1.3.6-4181, vendor tree) | `tools/rlxfw-kbuild.sh` | 量 2026-08-30, `r3-9/determinism.log`: `rep8` and `rep4`, the **same** `.config` file (`quietm.config-installed`, sha256 `c11d5b5f67e5b86d`), the same initramfs spec (`f1cee4484bc3da30`), the same 15 marks, differing only in `-j8` against `-j4`. Both **3,935,472 bytes**, both `.text` **2,427,448** — and sha256 `ebaeeb99252e3798…` against `9ac8374098cdcbc8…` | 🔴 **NOT reproducible** |

🔴 **So `P4a`'s positive claim is refuted before the gate opens, on the artefact
that matters** — the kernel is what v0.2 ships and what a GPL reader would try
to rebuild. The `rlxprobe` row is real and it is four gates early, but it is a
120 KB bare-metal object built by a Makefile of mine with a modern host
toolchain; it does not carry the vendor tree's 599 translation units, its
generated headers, or its 2009 kbuild.

⚠️ **`-j` is excluded as the variable and that had to be done first**, because
this build's Makefile rewrites its own headers before compiling and a `-j` race
was the obvious suspect: 量, `rep8` and `rep4` produce the **same** `.text`
size and the **same** file size, so whatever differs is not a scheduling race
that would move code.

### 1.1 What this gate does NOT inherit, because it was already closed

**The largest reproducibility defect this project has found is not open.**
量 2026-08-30 (`notes/kernel-build.md` §18.5): the image that booted on the
silicon could not be rebuilt from its own recorded configuration, and the whole
difference was one compiler flag — `-fno-if-conversion`, `SPEC.md` `TC-25` —
which lived nowhere except the operator's command line. It is now
`config/rlxfw-cflags`, an empty flag set is refused rather than silently
accepted, and `tools/test-kbuild-cflags.sh` is the gate. **That is a
reproducibility finding, and `P4a` must not re-claim it.**

---

## 2. The 84 bytes, and the prediction written before they were mapped

### 2.1 What was known when this prediction was written

**Stated because it bounds what the prediction is worth.** At the moment §2.2
was committed, three things had been measured and no more:

* both files are **3,935,472** bytes (量, `stat`);
* their sha256 are `ebaeeb99252e3798e39d3a217effc193c7ea075c751c6a0f55a125ca51499e94`
  (`rep8`) and `9ac8374098cdcbc85131d48cfeae7226b39ce25b1e521f9872be3825465ef587`
  (`rep4`) — the first sixteen hex digits of each match what `determinism.log`
  recorded on 2026-08-30, so nothing on disk has moved since;
* `cmp -l` counts **84** differing bytes out of 3,935,472 = **0.00213 %**.

🔴 **The count was known and the LOCATIONS were not.** A prediction written
after the count is weaker than one written before it, and saying so is cheaper
than pretending otherwise: 84 is already enough to exclude "a whole section
moved", so §2.2's first clause is partly bought rather than earned. The clauses
that are *not* bought are which sections, which symbols, and what the bytes say.

### 2.2 `P21-1`, written before `repdiff.py` was run

**Hypothesis (推).** The difference is the kernel's build timestamp. `rep8`'s
cell ran `2026-08-30T18:45:59` → `18:46:39` and `rep4`'s `18:46:39` →
`18:47:28` (讀, `r3-9/determinism.log`), so the two builds' `mkcompile_h`
moments are **under one minute apart** and differ only in the minutes-and-seconds
field of a `Sun Aug 30 18:4x:yy CST 2026` string.

* **P1** — **zero** differing bytes lie inside `.text`.
* **P2** — every differing byte lies inside a string that contains a date or a
  time, and those strings resolve to `linux_banner` and/or the `version` field
  of `init_uts_ns` (2.6.30 puts the same `UTS_VERSION` in both).
* **P3** — the differing bytes, read as ASCII, are two timestamps **less than
  10 minutes apart**, both on 2026-08-30.

**Refutation, written now:**

* **P1 is refuted by one differing byte in `.text`.** That outcome would mean
  the compiler itself is non-deterministic on this tree, which is a different
  and much more expensive gate than a timestamp.
* **P2 is refuted by any differing byte outside a timestamp-bearing string** —
  a differing pointer in `.data`, a differing symbol table entry, a differing
  `.init.ramfs` byte. Any of those adds a second cause, and a fix that freezes
  only the timestamp would then be a fix that leaves the gate open while
  appearing to close it.
* **P3 is refuted by the runs not decoding to ASCII, or decoding to times more
  than 10 minutes apart** — the second would mean the stamp is taken somewhere
  other than where `determinism.log` timed.

**Positive control**, because a mapping tool that reports "small and in strings"
for every input proves nothing: the same tool run on `rep8` against `quietmc` —
a build that genuinely differs, `.text` 2,427,448 against 2,432,392 — must
report a difference count in the **hundreds of thousands** and must place some
of it in `.text`. **Negative control**: `rep8` against itself must report **0**.

⚠️ **What this experiment cannot decide, whatever it returns.** It compares two
builds **49 seconds apart on one machine with one tree staged from one pinned
drop**. It says nothing about a different host, a different `$PWD`, a different
user, a different filesystem order, or a different day — and three of those are
known kbuild reproducibility hazards in 2009-era trees. A green result here
narrows `P4a`'s first cell and does not close the gate.
