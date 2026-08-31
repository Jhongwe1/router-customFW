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

---

## 3. The reading, and what `P2`'s refutation changed

**量 2026-09-01, both controls fired first**: `rep8` against itself reports
**0** differing bytes; `rep8` against `quietmc` — a build that genuinely differs
— reports **3,291,832 of 3,935,472 (83.6 %)** in **1,964 runs**, **337 of which
land in `.text`**. So the mapping can report large, and it can place a
difference in `.text`.

**The 84 bytes are 28 runs of 3 bytes each.**

| | runs | bytes | section / symbol | what the bytes are |
|---|---:|---:|---|---|
| the kernel's build timestamp | **2** | **6** | `.rodata` `linux_banner+0x4b` (file `0x26c1ff`), `.data` `init_uts_ns+0xd9` (file `0x291449`) | `#1 Sun Aug 30 18:46:38 CST 2026` against `#1 Sun Aug 30 18:47:26 CST 2026` — **48 s** apart |
| `gen_init_cpio`'s clock | **26** | **78** | `.init.ramfs`, 26 cpio headers | `6A9409FC` against `6A940A1D` — 2026-08-30 **18:46:20** against **18:46:53**, **33 s** apart |

* **`P1` holds.** **Zero** differing bytes in `.text`. This gcc is deterministic
  on this tree, which is the expensive outcome to have had to fix and did not.
* **`P3` holds**, with one qualifier stated rather than glossed: the second pair
  is ASCII, but it is ASCII **hex of a Unix epoch** inside a cpio header, not a
  human-readable date. Both pairs are 2026-08-30 and both are under a minute.
* 🔴 **`P2` is REFUTED, and the direction it fails in is the useful part.** The
  prediction said the differing strings *"resolve to `linux_banner` and/or the
  `version` field of `init_uts_ns`"*. **Two of twenty-eight runs do. The other
  twenty-six are a different mechanism carrying 92.9 % of the bytes.**

**The mechanism is 讀 out of the vendor's source, and its count is derivable
rather than observed.** `usr/gen_init_cpio.c` takes `time_t mtime = time(NULL)`
in three functions — `cpio_mkslink` (:105), `cpio_mkgeneric` (:153, which is
what a `dir` row goes through) and `cpio_mknod` (:241) — and takes the **source
file's** `st_mtime` in `cpio_mkfile` (:344). `config/rlxfw-initramfs.tsv`
declares **13 slink + 8 dir + 5 nod + 5 file = 31**, and **13 + 8 + 5 = 26**.
The five `file` entries did not move. The arithmetic closes against the
measurement without having been fitted to it.

### 3.1 🔴 What this does to the decision the gate opened with

The tension this gate opened with was: *freezing `KBUILD_BUILD_TIMESTAMP` is the
standard fix, but that timestamp is one of the anti-DoD's three discriminating
strings.* The measurement re-scopes it.

* **`KBUILD_BUILD_TIMESTAMP` fixes 6 of 84 bytes — 7.1 %.** The tension is real
  and it is one fourteenth of the problem.
* **The other 78 bytes (92.9 %) are `gen_init_cpio`, and fixing them costs the
  anti-DoD nothing at all.**
* And the leg is not deleted by freezing. `PROGRESS.md` names it as
  「my build stamp `(key@K) … #1 Fri Aug 28 23:37:47 CST 2026`」 — **`(key@K)`
  is inside the named string** and no vendor image carries it. What freezing
  removes is the leg's *second* role: saying **which** of my builds is running.
  ⚠️ Nothing else in the image had that role — `RLXFW-B00`..`B10` are constants
  and `start address: 0x80003600` is a property of the link — so the role has to
  move somewhere rather than just be dropped. It moves to `ID0`, §5.1.

### 3.2 讀 — a third host-dependence the tension did not cover, and it is bigger

`scripts/mkcompile_h` in this drop has **no** `KBUILD_BUILD_USER` and no
`KBUILD_BUILD_HOST`; it writes `LINUX_COMPILE_BY` from `` `whoami` `` and
`LINUX_COMPILE_HOST` from `` `hostname` `` (:65-66). Those symbols arrived in
mainline after 2.6.30. So **`(key@K)` is this workstation's, and a third party
rebuilding this repository's declared recipe gets a different `vmlinux` sha256
whatever is done about the clock.**

🔴 **That splits `P4a` into two gates wearing one sentence.** The gate board says
*same tree built twice → same image sha256* (one machine); `study/20260831-study7.md`
gives the purpose as 「二進位檔真的來自我發布的原始碼」 (any machine). **Owner's
decision, 2026-09-01: Level 1 now, Level 2 recorded as this gate's residual**,
§6. ⚠️ `LINUX_COMPILE_TIME` is a third `mkcompile_h` output and it is **not** a
hazard: 讀, it is referenced nowhere in the tree's `.c`, `.h` or `.S`, which is
why there are two non-initramfs runs rather than three.

---

## 4. `P21-2`, the two fixes, written before they were built

**Fix A — the initramfs.** `config/host-compat/0002-gen-init-cpio-declared-mtime.patch`
takes every cpio mtime from `RLXFW_CPIO_MTIME` instead of from the clock.
**Fix B — the kernel stamp.** `config/rlxfw-build-stamp` declares one Unix
epoch; `tools/rlxfw-kbuild.sh` renders it into `KBUILD_BUILD_TIMESTAMP` under
`LC_ALL=C TZ=UTC` and passes the same epoch as `RLXFW_CPIO_MTIME`, so the two
cannot drift apart.

* **P1** two builds of the declared recipe, minutes apart, are **byte-identical**.
* **P2** the banner reads `#1 Tue Sep 1 00:00:00 UTC 2026` and every cpio mtime
  field reads `6A961580` (= 1788220800).

**Refuted by** any differing byte, or by a stamp that renders with a local
timezone name.

### 4.1 🟢 量 2026-09-01 — P1 and P2 both hold

Two cells, `p4a1` (01:25:46 → 01:26:30) and `p4a2` (01:26:30 → 01:27:08), the
same declaration, `-j4` both:

```
c956c5b7543748439c5b8ea3238cccaa2cff52e0dd80d575274a01304454b97a  p4a1 vmlinux
c956c5b7543748439c5b8ea3238cccaa2cff52e0dd80d575274a01304454b97a  p4a2 vmlinux
cmp rc=0    3,968,240 bytes    0 differing bytes
```

Banner: `Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Tue Sep 1
00:00:00 UTC 2026`. cpio headers end `…0000026A961580`. ⚠️ The rendered stamp is
`Tue Sep  1` with two spaces and the banner shows one — `mkcompile_h` passes
`UTS_VERSION` through an unquoted `echo`, which collapses runs of whitespace.
Cosmetic, and recorded so that the string is not later "corrected" into
something the build does not emit.

---

## 5. `P21-3`, two controls, and one of them is a control on the DoD's wording

**The gate board's positive control is *"changing one source byte changes it"*.
Read literally that is false, and this pair is what says so.**

* **`PC-1` — a byte that reaches the image.** One character of the string
  literal `"0123456789ABCDEF"` in `config/rlxfw-src/…/rlxfw_mark.c`.
  **Prediction: the sha256 CHANGES.** Refuted by an identical image, which would
  mean the build is not reading my staged source at all.
* **`PC-2` — a byte that does not.** One character inside a **comment** in the
  same file. **Prediction: the sha256 is UNCHANGED**, because a comment reaches
  no instruction and no string. Refuted by a different image — which would mean
  something in the build is hashing my source text, and at this point in the
  session nothing is.

🔴 **`PC-2` predicting *no change* is deliberate.** A control that can only come
out one way is not a control, and "one source byte" in the DoD needs the
qualifier *that reaches the image* or the gate is asserting something false.
⚠️ **`PC-2`'s answer is expected to INVERT once `ID0` lands**, because `ID0` is
computed from the declaration files as bytes, comments included. That inversion
is itself a check on `ID0`.
