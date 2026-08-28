# Rebuilding `boa` and `busybox`, and what the score against the shipped binary is actually measuring

**Owner of: the `R2a`/`R2b` rebuild comparison** — what was built, on what window it
was read, what each build factor is worth on `binsim`, and the toolchain reading
that falls out. Measured 2026-08-28, desk, no power, no device reading, zero
flash bytes.

Everything here is 讀 or 量-on-this-desk: read out of vendor binaries and build
files, or produced by running them on this machine. **量 in this file never means
what `SPEC.md` §0 means by it** — nothing below was measured on the device.
**Not one line of this file is a statement about silicon.**

The comparand is always `$FWRE_WORK/extracted/unit-2018/squashfs-root/bin/<prog>`,
the program cut out of **this machine's flash dump**. `plan/` puts that in a box
and `notes/which-drop.md` §6 calls it the easiest thing in this gate to get
wrong; `tools/rebuild-census.py` refuses rather than substituting another
comparand, and `A6` is the case that pins it.

---

> ## Refutation conditions
>
> **Which of these were written before the result, and which were not, is stated
> per condition.** Three were; one was not, and the one that was not is the
> headline, which is exactly the shape that needs saying out loud.
>
> **R1 — the synthesised cell.** Written into `r2ab-synth.sh`'s header **before
> it was run**, because that build is the whole argument of §4:
> **P1** `-fuse-uls` is passed, so `lwl+lwr+swl+swr` > 0.
> **P2** `-march` is on the padding side, so `hazlint` violations ≈ 0 and
> nop-after-load lands 15–30 %.
> **P3** the `DT_NEEDED` libgcc name is **UNKNOWN**, and both answers were
> written out with what each would mean.
> **P4** `binsim` against `unit-2018/boa` lands materially **above** the 0.2522
> the same source scored at `-march=5281`. **Refuted if ≤ 0.2522.**
>
> **R2 — sstrip.** Written into `r2ab-controls.sh`'s header before it ran:
> removing the section header table must leave the code channel at **exactly
> 1.0000**, because the window is `[DT_INIT, DT_FINI)` out of `PT_DYNAMIC` and
> the section table is not in it. Refuted by any other value.
> 🔴 **The second half of R2 was also written first and it is REFUTED**: it said
> *"the strings channel is predicted to move, because the section header string
> table is bytes a string scan can see."* It did not move — 1.0000 on both
> channels. §8 has the mechanism and it is a property of the instrument, not of
> the file.
>
> **R3 — channel 3's zero.** Every shipped image reports 0 load-delay
> violations. That number means nothing unless something in the same run, read
> through the same window by the same tool, reports a non-zero. Refuted — in the
> sense of *made void* — if nothing does. `tools/rebuild-census.py` prints which
> it is on every run rather than leaving it to the reader.
>
> ⚠️ **R4 — the calibration in §3 was NOT pre-registered.** No condition was
> written for it because I did not expect to need it: it came out of building
> the rebuild-versus-rebuild block to interpret a number I could not read. It is
> the most consequential thing in this file and it is a **post-hoc** reading.
> What can be said in its defence is only this: the two cells it turns on are
> single-variable by construction (§3), and the direction was not chosen — it
> is the opposite of what the plan assumed.

---

## 1. What was built: 3 sources × 3 toolchains, and seven of nine

Nine cells, one per (GPL drop × rsdk release), each a self-contained minimal SDK
top level copied out of `src-vendor/` — **the vendor trees are never built in**,
and every command ran under `tools/vendor-tripwire.sh` from a scratch directory.
Every invocation reported `VENDOR-TRIPWIRE: CLEAN`.

| source drop | `rsdk-1.3.6-4181` | `rsdk-1.3.6-5281` | `rsdk-1.5.5-5281` |
|---|---|---|---|
| `rtl819x-toolchain` (RTL8196E) | ✅ 506,532 | ✅ 481,332 | ✅ 363,608 |
| `saturn49-wecb` (RTL8198) | ✅ 777,552 | ✅ 744,784 | ❌ |
| `wecb-vz-gpl` (RTL8198) | ✅ 745,168 | ✅ 711,660 | ❌ |

**The two failures are a reading, not a defect in the harness.** Both are the
same diagnostic, from the same line of the same file:

    fmget.c:271: error: static declaration of 'convert_bin_to_str'
                 follows non-static declaration

gcc 3.4.6 accepts that and gcc 4.4.5 rejects it. ⚠️ What that establishes is
exactly *"this source does not compile under 4.4.5 and does under 3.4.6"*;
calling it **gcc-3.x-era source** is a characterisation from one diagnostic in
one file, not a survey. `rtl819x-toolchain`'s compiles under both. **It was
not patched** — a one-line fix would complete the matrix and would make the cell
a different program, and the source axis is already covered at two toolchains.

**Two deviations from the vendor build route, both real.**

1. The vendor builds `boa` as `make -C users boa`, and `users/Makefile`'s
   `prepare` prerequisite runs `./configure` inside `iptables-1.4.4` and
   `zlib-1.2.5` first. Neither is staged. `boa` is therefore built by entering
   `users/boa` directly with the environment `users/Makefile` would have exported
   (`users/Makefile:107-116,122`), passed through the **environment** and not the
   command line — that is how `.EXPORT_ALL_VARIABLES` delivers it, so
   `boa/src/Makefile`'s `CFLAGS = -Os -pipe` still wins. A command-line `CFLAGS`
   would have silently discarded it.
   **What the deviation cannot reach**: `COMMON_CFLAGS`, the ~60 `-D` flags that
   decide what `boa` is, is computed inside `users/boa/Makefile` from the three
   `.config` files. `users/Makefile` contributes none of it.
   `CPP` is deliberately unset — make's builtin is `$(CC) -E`, which follows
   `CC` to the cross compiler, and that is why the vendor never sets it either.
2. 🔴 **The two Actiontec drops cannot be built without a customer profile, and
   the script that applies one is not in either drop.** `do_act_build` names
   `do_act_prepare.sh` and `do_act_merge.sh` and exports `ACT_MACRODEFINE`
   pointing at `customers/<C>/<P>/DEFINES` — 讀, **neither script exists in
   either tree**, and nothing else in either tree reads `DEFINES`. The mapping is
   reconstructed here: each `NAME=VAL` line is passed both as a make
   command-line variable (`src/Makefile` has `ifdef AEI_DATACENTER`, which selects
   `-I../../ctl/files/include` and `-ltr69c`) and as `-D` in `EXTRA_CFLAGS`
   (`defines.h:31` turns `AEI_WECB` into `ACTIONTEC_WCB`). **Reconstructed, not
   read.** Profiles used: `BASE/WCB3000` and `VERIZON/WCB3000V`.

⚠️ **And one error of my own, recorded because its shape is the one this project
keeps meeting.** The first harness removed only `src/boa` and
`apmib/libapmib.so` before a rebuild. A run that had failed **with the wrong
flags** left its `.o` files behind, `make` found them newer than their `.c`, and
the next run linked them: `nm fmget.o` had no `telus_langstat` because
`fmget.o` predated `-DAEI_WECB`. The same run also left a `.depend` generated by
the **host** preprocessor, and `src/Makefile` regenerates it only
`if [ ! -e ]`. `rm *.o` is not the fix either — `users/boa/src` ships three
prebuilt objects — so every build now re-stages the package from `src-vendor/`.
**A positive check that the fix took**, and 🔴 **its first version was scoped
wrong**: it read 389 files and said "across all cells", but it walked
`users/boa` only. The sweep over **everything** under `users/` in every cell:
**1,937 files, 1,708 ELF32 MSB MIPS, and 0 target-side objects that are
anything else.** The 229 that are not ELF32-MSB-MIPS are accounted for one by
one: **189 are `busybox`'s per-directory `built-in.o`, every one of them exactly
8 bytes — an empty `ar` archive, `!<arch>\n` and nothing after it**, so the
"0 members checked" this sweep reports is a property of the files and not of the
reader; **28 are host `kconfig` objects under `scripts/`** and are x86-64, which
is what a host tool should be; **12 are symlinks to prebuilt `libssl`/`libcrypto`
shipped inside the Actiontec drops**, which I did not build.

⚠️ **`busybox` needed one host flag and no cross-toolchain change.**
BusyBox 1.13's kconfig `#include`s `zconf.hash.c` into `zconf.tab.c` and relies
on gnu89 `extern inline` for `kconf_id_lookup`; under C99 inline the host tool
fails to link. `HOSTCFLAGS=-fgnu89-inline` fixes it. Same shape as the
`timeconst.pl` one-liner the kernel needed (`notes/vendor-toolchains.md` §4):
**the modern host is the problem, never the 2011 cross compiler.**

---

## 2. Four channels, one window

`tools/rebuild-census.py` is the instrument. The point of it is not that it runs
three tools; it is that it **makes all three read the same bytes**.

The window is `binsim`'s `[DT_INIT, DT_FINI)` out of `PT_DYNAMIC`. Forced, not
chosen: four of the six shipped trees have no section header table — the vendor's
romfs step runs `rsdk-linux-lstrip` over the whole tree (`Makefile:160`) — so
`.text` cannot be asked for, and the executable `PT_LOAD` contains `.rodata`,
which a linear scanner reads as code. `binsim`'s `E4`/`E4b` already certify this
window.

| | channel | reads |
|---|---|---|
| 1 | `binsim` | 7-gram containment of normalised operation tokens |
| 2 | `opcount` | `lwl`+`lwr`+`swl`+`swr` — the `-fuse-uls` lever |
| 3 | `hazlint` | loads / nop-after-load / violations — the `-march` lever |
| 4 | ELF header | `e_flags`, `phnum`, `DT_NEEDED`, section-table survival |

Channels 2 and 3 read four bytes at a time, which is a **superset** of the
instruction stream: **a zero is rigorous, a non-zero is an upper bound.**

---

## 3. 🔴 What each factor is worth — and the plan had it backwards

This is the block that changes how every other number in this file reads. Each
cell is single-variable **by construction**, not by argument.

| what differs, and nothing else | containment | Jaccard | `\|G\|` ratio |
|---|---:|---:|---:|
| **`-march` alone** — one source, one `.config`, one gcc, one binutils; 4181 vs 5281 | **0.3360** | 0.2009 | 1.01× |
| **toolchain generation alone** — one source, both at `-march=5281`; 1.3.6 vs 1.5.5 | **0.2132** | 0.1149 | 1.07× |
| **source and config** — one toolchain; Realtek's 8196E `boa` against Actiontec's WCB3000 fork of it | **0.9359** | 0.6371 | 1.40× |
| two different Actiontec drops, one toolchain | 0.9830 | 0.9202 | 1.05× |

**Read the first and third rows together.** Changing one compiler flag costs
two-thirds of the shared 7-gram structure. Changing the program — a different
product, a different SoC, 28 more translation units, 271 KB more binary — costs
six percentage points.

🔴 **And the third row is weaker than "a different program" makes it sound, so
here is what the two sources actually are.** 量: `users/boa/src` in the two drops
shares **56 filenames — every `.c`/`.h` the 8196E drop has, the Actiontec one has
too — of which 29 are byte-identical**, and Actiontec adds 28 files of its own
(`act_*.c`, `ifaddrs.c`, `md5.c`). So this row is **one program against a
superset fork of itself**, not a replacement: 27 modified files and 28 new ones.
That is a real source change and it is not the largest one imaginable. **The
asymmetry survives it** — 0.064 lost to a fork that rewrites or adds half its
translation units, against 0.664 lost to one compiler flag — but the row is now
described by what was measured rather than by how it was first phrased.

> **At `k=7` on this material, `binsim` measures the code generator. It barely
> sees the program.**

⚠️ The 0.9359 is read at a 1.40× size ratio and containment divides by the
smaller feature set, so a small set inside a large one scores high; that is
`binsim`'s own caveat. Jaccard, which has no such asymmetry, still puts source
replacement (0.6371) three times above a `-march` change (0.2009). The direction
does not depend on the measure.

**Mechanism, and it is only a consistency check.** The 4181 build carries 6,051
loads followed by an explicit `nop` and the 5281 build carries 0. A `nop` is a
token, so each inserted one disturbs up to 7 gram *positions*: ≤ 42,357 of
~97,752, i.e. ≤ 43 %. Measured containment is 33.6 % — **lower than that bound**,
so padding alone does not account for it and the two code generators differ in
more than the padding. ⚠️ Gram *positions* and *distinct* grams are not the same
quantity; this is an order-of-magnitude check, not an accounting.

🔴 **What this does to `R2b` as the plan wrote it.** The plan's premise was that
`boa`'s similarity to the shipped binary identifies the **drop**. On this
corpus, at this `k`, it identifies the **toolchain**. A drop test built on this
channel is measuring the wrong axis, and `notes/which-drop.md` §3's reading of
`boa`'s 0.877–0.895 across ①↔② as a *source* move now has to sit beside a
measurement saying that a total source replacement is worth only 0.06.

---

## 4. The tenth cell: `rsdk-1.5.5` driving `-march=4181`

Four channels pointed at a toolchain that is **1.5.5-generation and configured
for 4181**, and no drop ships one. All three drops' `users/Makefile` carries a
branch keyed on the exact release name
**`rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225`** (`users/Makefile:89-91` in each),
and two more on `rsdk-1.5.0-4181-EB-2.6.30-0.9.30.{2,3}`
(`users/Makefile`, `users/rc/Makefile`, `users/auth/src/dlisten/Makefile`).
**None of the six names is on any of the three disks.**

⚠️ **And the obvious second reading of that is wrong, so it is written down
before it is used.** The drops' `Kconfig` offers exactly the three toolchains
they ship — which says nothing, because `Kconfig` is *generated*:
`Makefile:108` is `@config/genconfig > Kconfig`, and `config/genconfig:123` is
`find toolchain -type d -name 'rsdk-*' -maxdepth 1`. The Kconfig is a directory
listing. The **hand-written Makefile branches** are the only signal, and what
they support is 推: *these Makefiles were written against an SDK line in which
those releases existed*. They do not establish what any of them contains.

The 1.5.5 wrapper on disk refuses `-march=4181` outright (`FATAL: -march
mismatch`), so the question can only be asked by bypassing it and driving
`mips-linux-xgcc` with the flag set the wrapper is **measured** to inject
(`RSDK_LOGFILE`, this session): `-ffix-bdsl -fuse-uls -msoft-float -EB -march=`,
with `5281` replaced by `4181`. **A reconstruction of what a 1.5.5-4181 wrapper
would do, not a reading of one.**

| | R1's prediction | measured | |
|---|---|---|---|
| **P1** | `lwl+lwr+swl+swr` > 0 | **32** (14/14/2/2) | ✅ |
| **P2** | violations ≈ 0, nop 15–30 % | **3** violations, **18.85 %** | ✅ with a caveat, below |
| **P3** | libgcc name unknown; both branches written out | **plain `libgcc_s.so.1`** | ✅ and it killed an inference of mine |
| **P4** | > 0.2522 against `unit-2018/boa` | **0.8255** (Jaccard 0.5889) | ✅ |

**P4 is a 3.3× move from changing one flag on one otherwise identical build.**

**P3 went against me and the record of that stays.** Before this cell ran, the
1.3.6 cells' `libgcc_s_4181.so.1` / `libgcc_s_5281.so.1` against every shipped
image's plain `libgcc_s.so.1` looked like evidence for a genuinely 4181-*configured*
release. It is not: 讀, `rsdk-1.5.5` ships **no `libgcc_s_*.so.1` at all**, only
`lib/libgcc_s.so.1`, so a 4181 build on it gets the plain name for a reason that
has nothing to do with which core it targets. What survives is weaker and still
useful, **once it is scoped by a second measurement**: 量, both 1.3.6 releases
ship a plain `lib/libgcc_s.so.1` **as well as** the suffixed one, and both report
`-print-multi-directory` = `4180`. So the suffix is not a property of the
release's contents — it appears because the wrapper forces a **non-default**
`-march` and the link then selects a non-default multilib. **The correct claim is
about builds, not tarballs: any build driven through either 1.3.6 wrapper gets a
suffixed soname, and that is every build the SDK is able to perform.** All six
shipped images carry the plain one.

🔴 **P2's three violations are not noise and they are a safety finding.** They sit
at `0x004039b8`, `0x00403a04`, `0x00403a14` — 讀 the section table, inside
`.init` (`0x0040394c`, 0x78 bytes) and the first 0x44 bytes of `.text`.

**That they are crt code and not `boa` code is carried by a control, and the
first thing I tried was the wrong instrument.** Searching the toolchain's own
`crti.o`/`crt1.o` for those three words finds nothing, and cannot: two of them
are `gp`-relative with link-time offsets, so the bytes in the object are not the
bytes in the image. The measurement that does settle it is a **5,462-byte
hello-world** built with the identical command line — no `boa` source in it at
all — which reports **exactly three violations of exactly the same shapes**:
`lw ra,28(sp)` in `.init`, and two `lw …(gp)` in the first instructions of
`.text`. 量: 31 loads, 12 nop (38.71 %), 3 violations.

On this cell that code comes from the **5281-built** uClibc, because
`mips-linux/lib/` has no 4181 variant. `notes/vendor-toolchains.md` §2 recorded
that mixture as *"not safe; unexamined on the axis that matters most"*. It is now
examined: **it puts three unpadded load-use pairs into the first instructions the
program executes**, and it does so in every program built this way, not just in
`boa`. The 1.3.6-4181 cell, whose crt comes from a 4181-built uClibc, has 0.

### Specificity, and it does not say what a careless reading would

| the synth cell against | containment |
|---|---:|
| `v2.1.2` (2015-08-11) | **0.8584** |
| `n300rt-2.1.6` (2016-05-16) | 0.8527 |
| `n200re-3.2.0` (2018-03-30) | 0.8293 |
| **`unit-2018` (2018-01-10)** | **0.8255** |
| `n300rt-3.4.0` (2019-03-15) | 0.0613 |
| `v3.4.0` (2020-10-30) | 0.0602 |

🔴 **This unit is the *lowest* of the four, not the highest.** The rebuild is
closest to the 2015 image — which is what a `.config` generated 2013-06-29 should
be. So the cell identifies a **generation**, not a build: 0.826–0.858 against the
whole PIC-era group and 0.060–0.061 across the group boundary, a 14× step. **It
does not pick this unit out of its own group and this file does not claim it
does.**

---

## 5. `R2a`: `busybox`, the toolchain test

`notes/which-drop.md` §6 called this the cleaner test — one upstream source
(`BusyBox v1.13.4`, 讀, in all six trees), so it moves only when the code
generator's output does — and predicted *"a rebuild that does not land in the
high 0.99s against this unit's means the toolchain is wrong."*

| build | code-C | vs `unit-2018/busybox` |
|---|---:|---|
| 1.5.5 at `-march=4181` (synth) | **0.9729** | container VOID, see below |
| 1.5.5 at `-march=5281` | 0.3743 | warn |
| 1.3.6 at `-march=4181` | 0.1788 | VOID |
| 1.3.6 at `-march=5281` | 0.0803 | VOID |

Same ordering as `boa`, on a program whose source is held constant across the
whole corpus. Two programs, one answer.

🔴 **The `busybox` synth cell is VOID under §6's rule and the rule is applied as
written.** Its container differs on `phnum` (8 against 7) and `DT_NEEDED` (no
`libgcc_s.so.1`). ⚠️ **That difference is my harness, not the toolchain**:
`busybox` links through `$(CC)`, and the wrapper's link stage — 讀 from
`RSDK_LOGFILE` — supplies `-nostdlib` with explicit `crt1.o crti.o crtbeginS.o`
from the toolchain's own `lib/`, plus a `-Wl,--start-group … -lc -lgcc` group,
none of which a bare `mips-linux-xgcc` link reproduces. Adding `-shared-libgcc`
changed nothing. **So 0.9729 is reported and is not admissible under the rule**,
and the fix is to make the harness reproduce the link, not to weaken the rule.
`boa`'s synth cell, which satisfies the precondition on all four fields, is the
admissible one.

---

## 6. What the four channels say together about the toolchain

Read down the columns for this unit's `boa`, and against the ground truth the
seven rebuilds supply:

| channel | this unit's `boa` | 1.3.6@4181 | 1.3.6@5281 | 1.5.5@5281 | 1.5.5@4181 |
|---|---|---|---|---|---|
| 2 unaligned | **144** | 0 | 0 | 26 | 32 |
| 3 violations | **0** | 0 | 7,656 | 5,224 | 3 (crt) |
| 3 nop-after-load | **19.71 %** | 21.03 % | 0.00 % | 0.00 % | 18.85 % |
| 4 libgcc soname | **plain** | `_4181` | `_5281` | plain | plain |
| 4 `phnum` | **8** | 7 | 7 | 8 | 8 |
| 1 containment | — | 0.2401 | 0.1033 | 0.2522 | **0.8255** |

**推 — and it is a claim about the toolchain, not about the drop: the userspace
on this unit was built by a 1.5.5-generation rsdk driving a `-march` on the
`{4180, 4181, 5181, mips1}` side.**

🔴 **"Nothing else on hand fits" was an assertion until the rival was built, so
it was built.** The strongest one is `rsdk-1.3.6-4181` with `-fuse-uls` passed by
hand: that is the one other combination available here that gets both the
unaligned instructions and the load-delay padding. 量, same source, same
`.config`:

| | this unit's `boa` | 1.3.6-4181 **+ `-fuse-uls`** | 1.5.5 at 4181 |
|---|---|---|---|
| channel 2, unaligned | 144 | **3,798** | 32 |
| channel 4, libgcc soname | plain | `_4181` | plain |
| channel 4, `phnum` | 8 | 7 | 8 |
| channel 1, containment | — | 0.2462 (**VOID**) | **0.8255** |
| channel 3, violations / nop | 0 / 19.71 % | 0 / 20.93 % | 3 / 18.85 % |

**It dies on channels 1, 2 and 4** — and the 3,798 is the sharp one: gcc 3.4.6
with `-fuse-uls` emits unaligned accesses at **26×** the rate the shipped image
has, where gcc 4.4.5 emits them at a quarter of it. ⚠️ **Channel 3 does not
distinguish it at all** (0 violations, 20.93 %), which is worth saying plainly:
the `-march` channel establishes the *side* and cannot establish the
*generation*. The generation is carried by channels 1, 2 and 4. `TC-01`'s kernel banner —
`gcc version 4.4.5-1.5.5p2`, 量 — is a fifth reading of the same generation from
a sixth part of the image.

**The one release name that would satisfy all of it is
`rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225`**, which all three drops' Makefiles
name and none of them ships. ⚠️ **推, and weakly**: nothing here reads that
tarball. That its date code (`110225`, before the `110714` on the 5281 release we
have) would fit a `p2` patch level below the `p4` we have is **a guess about a
naming convention and nothing more.**

🔴 **A separate reading, and this one is 讀 rather than 推: every shipped
userspace binary in all six trees was built for the padding side.**

| | `boa` nop % | `busybox` nop % | violations |
|---|---:|---:|---:|
| `v2.1.2` / `n300rt-2.1.6` / `unit-2018` / `n200re-3.2.0` | 19.98 / 20.01 / 19.71 / 20.00 | 26.21 / 26.21 / 26.21 / 26.48 | **0** in all eight |
| `n300rt-3.4.0` / `v3.4.0` | 28.71 / 28.54 | 27.03 / 27.00 | **0** in all four |

**And the zero has its positive control in the same table, read through the same
window by the same tool**: the `-march=5281` rebuilds return 5,224–10,494. Twelve
shipped binaries at 0 is a reading, not a blind scan.

---

## 7. What this says about which drop: nothing new

**`TC-02` stays 推.** Everything above is about the **toolchain**. The drop
question is untouched, and §3 makes it worse rather than better: the channel
`R2b` was going to answer it on is dominated by the code generator, and a total
source replacement moves it by 0.06. The best cell reaches **warn**, not pass —
`FLOOR` 0.1581 < 0.8255 < `BASE` 0.9818 — and §4's specificity table shows the
score is a property of the era, not of the build.

---

## 8. The controls

| | | |
|---|---|---|
| **sstrip** | the winning cell against its own `rsdk-linux-sstrip`ped self: 376,484 → 363,728 bytes, 12,756 removed, section table gone | **code channel C = J = 1.0000**, and its score against `unit-2018/boa` is 0.8255 before and after. **The sstrip confound is dead**, and every rebuild-versus-shipped number in this file is clean of it |
| **strings channel, same pair** | predicted to move; **1.0000** | 🔴 **The prediction was wrong.** `binsim`'s `DEFAULT_MIN_STRING = 8` and section names (`.text`, `.data`, `.bss`) are shorter, so the string scan never saw the table that was removed. A property of the instrument, not of the file |
| **build determinism** | baseline against `-UCONFIG_IPV6`, a macro this cell's config never defined | **3 bytes differ**, all of them digits at file offset ~352,837 — `timestamp.c`'s build stamp — and both channels read 1.0000. Free, and the same shape as the corpus's own `v2.1.2`/`n300rt-2.1.6` `busybox` anchor (8 bytes, all digits in the BusyBox banner) |
| **channel 3's zero** | needs something that fires | the `-march=5281` cells: 5,224 / 7,656 / 10,266 / 10,494 |
| **cross-build sanity** | 389 `.o`/`.so` across all cells | **0 not big-endian MIPS** |
| **tripwire** | every vendor-binary invocation | `CLEAN` on all of them |

### Config sensitivity — the number that says whether reconstructing a config would help

The question is not *"is my config right"*. It is *"how much of a score can
config explain at all"* — because without that, a rebuild at 0.83 is
uninterpretable and any attempt to close the gap by adjusting `.config` is
fitting the model to the test set.

`boards/rtl8196e` ships **five complete config triples**, one per model, all for
this SoC and all against the same `boa` source. Building the same source at the
same toolchain under each is a real config delta the vendor shipped, and it needs
no invention:

| | bytes | vs `88E_GW` | vs `unit-2018` |
|---|---:|---:|---:|
| `RTL8196E_88E_GW` (the drop's own) | 376,484 | — | 0.8255 |
| `RTL8196E_92C_GW` | 362,588 | 0.9856 | 0.8228 |
| `RTL8196E_92D_GW` | 369,696 | 0.9596 | 0.8039 |
| `RTL8196E_MP` | 345,884 | 0.9829 | 0.8295 |
| `RTL8196E_88E_ULINKER` | 394,944 | 0.9347 | 0.7607 |

**Ten config-only pairs: 0.9347 to 0.9976, median 0.9869.**

> **A config difference between two real vendor configurations of one program at
> one toolchain is worth at most about 0.065 of containment.** The gap between
> the best rebuild (0.8255) and `BASE` (0.9818) is 0.156. **Config cannot close
> it**, and reconstructing one would buy at most 40 % of the shortfall while
> costing the comparison its independence. So it was not done.

⚠️ **What that bound is over, stated because the sentence above does not say it
by itself.** The five are Realtek's own reference configs for one SoC family, and
their spread is what *those five* cost. TOTOLINK's config is not in the set and
nothing here bounds how far outside it can lie. What the measurement does
establish is narrower and still enough for the decision it was made for: on the
vendor's own configurations of this program, config is a small term, so
**assuming** the shortfall is config would have been assuming something this
corpus does not support.

⚠️ A weaker second form was run first and is kept because it is the honest half:
ten single feature macros turned off with `-U`. Seven built; the code channel
moved by ≤ 0.0001 on all seven, and the four whose macro this config never
defined changed **nothing at all**, which is the harness demonstrating it does
not manufacture motion. `-U` is a **lower bound** — it cannot add or remove a
`.c` file from `SOURCES`, and three of the ten macros make `boa` fail to compile
when removed, so the sample is biased toward macros that do little. The
five-config form has none of those problems, which is why it is the one quoted.

---

## 9. What could still be wrong

* **§3's calibration was not pre-registered.** It is the load-bearing reading in
  this file and it came out of the data. R4 says so.
* **`n = 1` on the source axis at each toolchain.** "Source replacement is worth
  0.06" rests on Realtek-8196E-`boa` against Actiontec-WCB3000-`boa`, twice. Two
  forks of one upstream Boa 0.94 are more related than the row's framing suggests;
  a genuinely unrelated program would score lower and is not in the block.
* **The synthesised cell is a reconstruction.** Its flag set is read out of the
  1.5.5 wrapper's own log; that a real `rsdk-1.5.5-4181` would inject the same
  set with `4181` substituted is 推, and its uClibc/crt objects are demonstrably
  from the wrong side.
* **The Actiontec cells' `-D` set is invented.** `do_act_prepare.sh` is not in
  either drop; the `DEFINES`-to-build mapping is mine.
* **`k = 7` is where all of this is read.** §3's inversion is a statement about
  this metric at this `k` on this material. A sweep is not in this file.
* **Nothing here was run.** Not on the device, not in an emulator. Seven ELF
  files that link and have the right shape, and one of them is measured to have
  three load-use violations in its entry path.
* **One source (B) for the toolchain half**, three drops from one vendor, plus
  this desk. `SPEC.md` §0's two-source rule is not satisfied by any of §6's
  channels on their own; what is claimed there is agreement among four readings
  of one vendor's tools, not corroboration by a second party.
