# The three rsdk toolchains, and what each of them will and will not build

**Owner of: what the vendor toolchains are, what they enforce, what they inject,
and whether they can build this board.** Measured 2026-08-28, desk, no power, no
device reading. `SPEC.md` indexes the numbers; this file owns them.

Everything here is 讀 or 量-on-this-desk — read out of the vendor's own binaries
and build files, or measured by running them here. **量 in this file never means
what it means in `SPEC.md`**, where §0 defines it as *measured on this device*;
nothing below was measured on the device, and where a number needs that mark it
goes to `SPEC.md` as 讀. **Not one line of this file is a statement about
silicon.** Where a toolchain and this unit's own image agree, that is recorded as
an agreement between two readings, not as a measurement of the die.

> **Refutation conditions, written before the results.**
>
> **R1** — *"the whole binutils was down, not just `as`"* is refuted by any one of
> the programs §3 names starting on a machine with no i386 `libz.so.1`. §3 lists
> **fifteen program names plus the `rsdk-linux-*` symlinks onto them**, which is
> where the count of seventeen comes from; the first version of this condition
> said "seventeen named" and "each entry carries its own `ldd` line", and neither
> was true of the file. Corrected rather than removed: a condition that describes
> evidence the file does not hold is not a condition.
>
> **R2** — *"the wrapper enforces exactly one `-march`"* is refuted by any
> `-march` other than the configured one producing an object file. Six values were
> tried per toolchain and the exit status read on each; **§2's table publishes
> four of the six rows** and the remaining two (`5181`, `4281`) behaved like the
> other rejections. A single `rc=0` with a non-empty output file kills it.
>
> **R3** — *"`-march=4181` pads load delay slots and `-march=5281` does not"* is
> refuted by a corpus where the two produce the same nop-after-load rate. §5 uses
> the vendor's own `users/dhrystone`, three kernel objects, and — added after the
> first three were in — **two whole `vmlinux` built from one source**; any of them
> coming out equal refutes it. It is **not** refuted by the counts differing in
> size: the claim is about the presence of padding, not its amount.
>
> **R3a** — the derived claim, *"this unit's kernel was built on the padded side"*,
> is refuted by its nop rate or its violation count falling between the two builds
> rather than beside one of them. 量: 29.91 % against 28.77 % and 2.06 %, and 168
> violations against 256 and 36,264. **This condition had to be written after the
> fact and that is a defect in the writing, not in the result** — the first version
> of §5 stopped at three object files and had no whole-image comparison to state a
> condition about.
>
> **R4** — *"no drop's build system passes `-fuse-uls`"* is a zero, so it needs a
> control. §6 carries one: the same grep over the same corpus must find
> `CPU_HAS_ULS` and `march=5281`, and per drop it finds 48/41/41 and
> 1141/1143/1055 files. ⚠️ **`ffix-bdsl` was listed as a third column of that
> control and it is not one** — it hits the same two files as `fuse-uls`, on the
> same line of the same string, so it is the metric agreeing with itself. Kept in
> the table below, marked, rather than quietly dropped.
>
> 🔴 **The method is `grep -rlI`, and the `-I` is load-bearing.** Without it the
> corpus returns **22** per drop rather than 2. The twenty extras are all
> toolchain **binaries** — `cc1`, `cc1plus`, `mips-linux-c++`, `mips-linux-cpp` —
> i.e. the flag compiled into the compilers, which is §6's own conclusion and
> confirming rather than refuting. The zero is about **build inputs**, so it is
> refuted by any `grep -rlI` hit in a Makefile, `.config`, `config.*`, `*.mk` or
> package source outside the two files §6 names. **Stated because a reader running
> the obvious command gets 22 and concludes this condition has fired.**

---

## 1. What the three releases are, and what the numbers in their names mean

All three drops ship the same three releases. 量 2026-08-28: three drops ×
three releases = nine directories on disk, three distinct toolchains.

| release | gcc | binutils | configured for |
|---|---|---|---|
| `rsdk-1.3.6-4181-EB-2.6.30-0.9.30` | 3.4.6-1.3.6 | 2.16.94-1.3.6 20060612 | `-march=4181` |
| `rsdk-1.3.6-5281-EB-2.6.30-0.9.30` | 3.4.6-1.3.6 | 2.16.94-1.3.6 20060612 | `-march=5281` |
| `rsdk-1.5.5-5281-EB-2.6.30-0.9.30.3-110714` | 4.4.5-1.5.5p4 | 2.19.92.20091006 | `-march=5281` |

🔴 **The number in the directory name is not the compiler's default.** Both 1.3.6
releases' `mips-linux-gcc` report `_MIPS_ARCH "4180"` and
`-print-multi-directory` → `4180`; their multilib list is identical
(`5280 4180 5181 4181 5281 4281 el`) and their `mips-linux-as` is byte-identical
(same sha256). What differs is `mips-linux-gcc`, `cc1`, `mips-linux-ld` and the
uClibc built beside them.

**So `mips-linux-gcc` is the wrong thing to ask which core a toolchain is for.**
The right thing is `rsdk-linux-gcc`, and that is also what the kernel calls:
`arch/rlx/Makefile` sets `CROSS_COMPILE := rsdk-linux-`.

---

## 2. `rsdk-linux-gcc` is a wrapper, and it is the thing with an opinion

All three `rsdk-linux-gcc` are the **RSDK Wrapper version 2.0** (timestamp
1283844024 = 2010-09-07). On 1.5.5 it is a symlink to `mips-linux-gcc`; on 1.3.6
it is a separate binary and `mips-linux-gcc` beside it is the raw gcc driver.

It self-identifies. `rsdk-linux-wrapper --version`, 1.5.5:

    Realtek Semiconductor Corp.
    RSDK Wrapper version: 2.0
    RSDK Wrapper timestamp: 1283844024
    Configured for: -march=5281 -EB -msoft-float -fuse-uls -ffix-bdsl

⚠️ **It writes `offset.tmp` into the current working directory every time it
runs.** 量 2026-08-28: it did so into this repository's root. Run it from a
scratch directory.

### What it enforces

量 2026-08-28, six `-march` values per toolchain, exit status read on each and
the output file removed first:

| `-march` given | 1.3.6-4181 | 1.3.6-5281 | 1.5.5-5281 |
|---|---|---|---|
| `4180` | rejected | rejected | rejected |
| `4181` | **accepted** | rejected | rejected |
| `5281` | rejected | **accepted** | **accepted** |
| `mips1` | rejected | rejected | rejected |

Rejection is `FATAL: -march mismatch. RSDK is configured for -march=NNNN only`,
exit 1, **and no output file is written**. A sweep that does not read the exit
status reads the previous iteration's output instead; that is how a table of
four false zeros reached a commit on 2026-08-27.

🔴 **The only rsdk-1.5.5 on hand cannot build a 4181 target through its wrapper,
and `boards/rtl8196e/config.in` is `ARCH_CPU_RLX4181=y`.**

⚠️ **The wall is the wrapper, not the toolchain.** 量 2026-08-28:
`mips-linux-xgcc` — the real driver, wrapper bypassed — takes `-march=4181` on
1.5.5, compiles, links statically, and the result runs correctly under
`qemu-mips`. The `4181` multilib is present at
`lib/gcc/mips-linux/4.4.5-1.5.5p4/4181/`. ⚠️ **But `mips-linux/lib/` has no
`4181` variant**, so such a link mixes 4181 user code with a 5281-built uClibc.
量: that uClibc contains **0** `ll`, **0** `sc`, **0** `sync` (82,052
disassembled lines, and the same scan finds 3 `lwl` / 2 `lwr` / 3 `swl` in it, so
it is not a blind scan), which is the axis that would have made the mixture
unsafe **on that axis**. **推** that the mixture is harmless there; it has not
been run on the device and nothing here says it has.
🔴 **And §5 establishes a second axis that this mixture fails on.** A uClibc built
at `-march=5281` is built for a core with a load interlock, so it carries no
load-delay padding; linking it under a 4181 object puts exactly the code §5
measures as wrong for this core into every binary. **The mixture is not safe; it
is unexamined on the axis that matters most**, and the check is one `hazlint` run
over `mips-linux/lib/libc.a` that has not been done.

### What it injects

`RSDK_LOGFILE=<path>` makes the wrapper write the command line it hands to
`mips-linux-xgcc`. 量 2026-08-28, 1.5.5, compiling one `.c`:

    -ffix-bdsl -fuse-uls -UCONFIG_CPU_HAS_ULS -DCONFIG_CPU_HAS_ULS
    -msoft-float -EB -march=5281 -O2

and 1.3.6-4181, the same file:

    -march=4181 -EB -O2

🔴 **Two things follow, and neither is in any drop's build system.**

1. **`-fuse-uls` is injected by the 1.5.5 wrapper and by nothing else.** §6.
2. **`-UCONFIG_CPU_HAS_ULS -DCONFIG_CPU_HAS_ULS` is emitted as a constant pair,
   in that order, under every flag combination tried** — default, `-fuse-uls`,
   `-fno-use-uls`. `-D` is last, so the macro is **always defined**. 量: on
   1.5.5 `CONFIG_CPU_HAS_ULS` is defined for all three; on both 1.3.6 releases it
   is never defined, at any `-march`, under any of the three.
   ⚠️ **Undetermined**: the wrapper plainly means to choose between `-U` and
   `-D`, and this measurement did not find the input that makes it choose. What
   is measured is only that the three obvious inputs do not.
   🔴 The consequence is real: `arch/rlx/Kconfig:87` makes `CONFIG_CPU_HAS_ULS`
   a kernel config symbol, and `arch/rlx/lib/memcpy.S` branches on it. Built with
   rsdk-1.5.5 the wrapper defines it on the command line **whatever the kernel's
   own `.config` says**.

⚠️ **`gcc -c foo.S` does not carry `-march` through to `as`.** 量 2026-08-28 on
1.3.6: assembling a `.S` containing `cache 0x11,0($4)` fails with
`Error: opcode not supported on this processor: lx4180 (lx4180)`, and
`-Wa,-march=4181` fixes it while saying
`Warning: A different -march was already specified`. So the driver hands `as` its
own default (`lx4180`) for hand-written assembly while giving `cc1` the
configured `4181`. This did not stop the kernel build in §4 — nothing in
`arch/rlx`'s `.S` files needs an instruction `lx4180` refuses — but it is a live
trap for anything that does.

---

## 3. The i386 dependency, and it was never only `as`

量 2026-08-28. rsdk-1.5.5's host programs are 32-bit i386 ELFs. `gcc`, `cpp`,
`xgcc` and the wrapper are **statically linked** and run anywhere; every
binutils program is **dynamically linked against `libz.so.1`**, which a 64-bit
Ubuntu 24.04 does not have in a 32-bit flavour by default.

Seventeen programs, each `ldd`-confirmed `libz.so.1 => not found`:

    addr2line  ar  as  c++filt  gprof  nm  objcopy  objdump  ranlib
    readelf  size  strings  strip  xld  ld  (and the rsdk-linux-* symlinks to them)

**This is why `--version` was a bad DoD.** The one program the old DoD ran is in
the group that works.

Still unresolved after the fix, and **not needed for a build**: `mips-linux-gdb`,
`mips-linux-gdbtui`, `mips-linux-insight` want `libX11.so.6`, `libncurses.so.5`
and `libexpat.so.0`. `libncurses.so.5` is not packaged for Ubuntu 24.04 at all.
Recorded here so that a future zero on those three reads as *known and not
needed* rather than as a new problem.

### Two recipes, and the order they were proved in matters

The hermetic route was done **first**, so its positive result could not have been
produced by the system package.

**Hermetic — no root, no system change.**

    apt-get download lib32z1                     # 1:1.3.dfsg-3.1ubuntu2.1, amd64
    #   .deb  sha256 91ab7d60f433561982ca2b7f47ab3e586706df961b0418098ae1201d9d13b4ca  57,380 bytes
    dpkg-deb -x lib32z1_*.deb $FWRE_WORK/rebuild/tc-deps/lib32z1
    export LD_LIBRARY_PATH=$FWRE_WORK/rebuild/tc-deps/lib32z1/usr/lib32
    #   libz.so.1 -> libz.so.1.3, i386 shared object
    #   sha256 0c10047944d94b3bfc014c76b1a4633fea9e155cf161a1eb7dd8cffa94ba160d

**System — one amd64 package, no foreign architecture.**

    sudo apt-get install ./lib32z1_1%3a1.3.dfsg-3.1ubuntu2.1_amd64.deb

`lib32z1` installs `/usr/lib32/libz.so.1`, and `/usr/lib32` is already on the
loader path via `/etc/ld.so.conf.d/zz_i386-biarch-compat.conf`. This is the same
mechanism that put the 32-bit libc there: `/lib32/libc.so.6` comes from
`libc6-i386`, also an amd64 package. **`dpkg --add-architecture i386` is not
required**, and `plan/`'s Dockerfile sketch (`zlib1g:i386`) asks for more than
the job needs.

量, in this order:

| step | `mips-linux-as --version` |
|---|---|
| before anything | rc=127, `error while loading shared libraries: libz.so.1` |
| `LD_LIBRARY_PATH=<hermetic>` | **rc=0**, `GNU assembler (GNU Binutils) 2.19.92.20091006` |
| env var removed again | rc=127 — the negative control between the two routes |
| `lib32z1` installed, `env -u LD_LIBRARY_PATH` | **rc=0**, same banner |

After the fix: 27 of the 30 ELF programs in that `bin/` resolve; the 3 that do
not are the debuggers above.

---

## 4. The ladder, and a complete kernel at the top of it

`tools/tc-smoke.sh` is the instrument. 量 2026-08-28, all three releases reach
L4: binutils start; `.c → .s → .o →` statically linked 32-bit MSB MIPS `EXEC`;
the nine instructions `arch/rlx` is made of assemble to the same 48 bytes
(sha256 `298d5f2a…`) from all three; and the linked program runs under
`qemu-mips` and prints the number it computed.

Above the ladder, three real builds:

| build | 1.3.6-4181 | 1.3.6-5281 | 1.5.5-5281 |
|---|---|---|---|
| `users/dhrystone`, the vendor's own package and Makefile | `make` rc=0, dynamic **and** static, runs under `qemu-mips`, **every internal self-check value matches its expected constant** | same | same |
| `arch/rlx/{lib/memcpy,kernel/traps,mm/cache,bsp/setup}.o` | rc=0, 4/4 | *not run* | rc=0, 4/4 |
| **complete `vmlinux`**, 724 objects | **rc=0, 3,340,287 bytes**, text 2,656,040, entry `0x80003600` | *not run* | **rc=0, 3,166,710 bytes**, text 2,497,352, entry `0x80003420` |

⚠️ **The empty column is the control that was not run, and it is the interesting
one.** `rsdk-1.3.6-5281` is the same gcc and the same binutils as the 4181
release with a different `-march` forced by its wrapper. Building the kernel with
it would separate *the toolchain generation* from *the `-march`* in §5's kernel
rows, which currently vary both at once. Cheap, and not done.

Both `vmlinux` are `ELF 32-bit MSB executable, MIPS, MIPS-I, statically linked`,
`Machine: MIPS R3000`, `Flags: 0x1001, noreorder, o32, mips1`.

**What it took, and what it did not.** The kernel is not built in the vendor
tree — the tree is a pinned clone and `tools/vendor-tripwire.sh` guards it. The
minimal top-level layout has to be reconstructed, because `arch/rlx/bsp` is a
symlink to `../../../target/bsp` and `target` is a symlink to
`boards/rtl8196e`; and `DIR_ROOT` / `DIR_LINUX` / `DIR_BOARD` / `DIR_RSDK` must
be exported, because `boards/rtl8196e/bsp/Makefile:10` is
`include $(DIR_LINUX)/.config`.

**One patch, and it is a host-tool patch.** `kernel/timeconst.pl:373` uses
`defined(@val)`, removed from Perl in 5.22; this host runs 5.38.2. One line.
🔴 **Nothing about the cross toolchain needed changing** — which is the answer
to the plan's `R-6` risk (*"2.6.30 will not build on a modern host"*): it does,
and the single thing in the way is a Perl idiom, not a compiler.

---

## 5. The load delay slot, read out of the vendor's own compiler

🔴 **This is the finding with the widest reach. Two instruments inside the vendor
toolchain agree on it, and they are independent in implementation and not in
provenance** — §8 says so and the headline is written to match it rather than to
run ahead of it. Both are consumers of the same thing: whatever table assigns an
ISA level to each `-march` name in Realtek's binutils/gcc lineage. **What that
buys is a check against one of them being misread, not a second witness.**

**The compiler**, and it is **`mips-linux-gcc`, not `rsdk-linux-gcc`** — §2's own
point is that the wrapper accepts exactly one `-march`, so four of the six columns
below cannot be reached through it at all. The raw driver is the only way to ask
the question, and it means these rows are a property of the **code generator**,
not of a build anyone could perform with the wrapper in place. Same source, same
`-O2`, exit status read at every point, output removed first. `users/dhrystone/dhry_1.c`, every column from
`tools/hazlint` so the whole section is one instrument:

| toolchain | `-march` | loads | nop after load | violations |
|---|---|---:|---:|---:|
| 1.3.6 | `4180` / `4181` / `5181` | 421 | 121 (28.74 %) | **0** |
| 1.3.6 | `5280` | 425 | 0 (0.00 %) | **107** |
| 1.3.6 | `5281` / `4281` | 425 | 0 (0.00 %) | **162** |
| 1.5.5 | `4180` / `4181` | 388 | 90 (23.20 %) | **0** |
| 1.5.5 | `5181` | 384 | 91 (23.70 %) | **0** |
| 1.5.5 | `5280` / `5281` / `4281` | 390 | 1 (0.26 %) | **134** |

🔴 **The violations column is the sharper half and it was not in the first
version of this table.** The padding is a habit; the violation is the defect the
padding prevents. Zero on one side of the partition and 107–162 on the other,
from one C file, in both toolchain generations.

**The assembler.** rsdk-1.5.5's `as` carries a load-use checker — the strings
`possible LOAD-USE: regno=%d`, `warn-possible-load-use`, `load_delay_nop`,
`reg_needs_delay` are in the binary. 1.3.6's `as` has **none of those strings**
— and see the correction below, which is that it has the behaviour anyway, so
the strings measure a *diagnostic*, not a model. Fed
`lw $31,0($4)` / `jr $31` under `.set noreorder`:

| `-march` | 1.5.5 `as` | 1.3.6 `as` |
|---|---|---|
| `4180` `4181` `5181` `mips1` | **warns** | silent (no checker) |
| `5280` `5281` `4281` `mips2` | silent | silent |

**The partition is identical: `{4180, 4181, 5181, mips1}` expose the load delay
slot; `{5280, 5281, 4281, mips2}` do not.** Two instruments, two toolchain
generations, one boundary — and it falls exactly where MIPS-I / MIPS-II falls.

⚠️ **Under `.set noreorder` the assembler only warns; it does not insert the
`nop`.** The object contains `lw ra,28(sp)` immediately followed by `jr ra`.

🔄 **2026-08-28, from review: that sentence was written from a `.set noreorder`
test file and is false under gas's default `.set reorder` — and the correction is
a THIRD reading of the same partition, stronger than the one it replaces.** 量,
the same two instructions under each directive:

| toolchain | `-march` | `.set noreorder` | `.set reorder` (gas's default) |
|---|---|---|---|
| 1.3.6 | `4181` | `lw` `jr` `nop` — untouched, silent | **`lw` `nop` `jr` — gas inserted it** |
| 1.3.6 | `5281` | `lw` `jr` `nop` | `lw` `jr` `nop` — no insertion |
| 1.5.5 | `4181` | `lw` `jr` `nop`, **and it warns** | **`lw` `nop` `jr` — inserted, and the warning is gone** |
| 1.5.5 | `5281` | `lw` `jr` `nop` | `lw` `jr` `nop` — no insertion |

🔴 **So both assemblers carry a per-core load-delay model and both act on it,
and the older one has no warning strings only because it fixes silently.**
"1.3.6's `as` has none of them" is true of the strings and false of the
behaviour. **The `noreorder`-only probe had no positive control** — it is the one
mode in which a checkerless assembler and a silent-fixing one look identical —
and that is the same false zero this repository keeps cataloguing.

⚠️ **And it is reachable in the real build.** Not every `.S` under `arch/rlx`
sets `.set noreorder`, and `asm/stackframe.h` sets `.set reorder` outright, so
some hand-written kernel assembly is assembled in the mode where gas fixes the
hazard for you. Which files, and whether any of them relies on it, is **not
looked at here**.

**Net: the partition survives on three readings, not two, and the claim that dies
is the one that said the assembler leaves the hazard in place.**

### What that does to a kernel built with the wrong rsdk

Same source, same `.config`, `tools/hazlint`:

| object | 1.3.6-4181 (`-march=4181`) | 1.5.5-5281 (`-march=5281`) |
|---|---|---|
| `arch/rlx/kernel/traps.o` | 134 loads, 30 nop (22.4 %), **0 violations** | 150 loads, 0 nop, **28 violations** |
| `arch/rlx/mm/cache.o` | 33 loads, 14 nop (42.4 %), **0 violations** | 33 loads, 0 nop, **16 violations** |
| `arch/rlx/bsp/setup.o` | 7 loads, 4 nop (57.1 %), **0 violations** | 6 loads, 0 nop, **5 violations** |

🔴 **Forty-nine load-delay violations in three files, and two of the three are the
exception handler and the cache management code.** This is not a statement that
rsdk-1.5.5 is broken. It is a statement that **a 5281-configured rsdk must not be
used to build a 4181 kernel**, and that is the only 1.5.5 on hand.

### And what it says about the image on this unit — at whole-kernel scale

The three objects above are three files. The comparison that matters is whole
images, and today produced two of them from one source. All three rows below are
the same instrument, and the range is **bounded below the MIPS16**, which is the
reading `hazlint` will certify without an override. The lowest symbol marked
`[MIPS16]` is `0x8016c844` in the 4181 build and `0x8015c200` in the 5281 one, so
`[0x80000000, 0x80158000)` is 32-bit code in all three artefacts and the same
bound serves all three:

| artefact | loads | nop after load | violations |
|---|---:|---:|---:|
| `vmlinux` built here, `-march=4181` | 61,568 | 17,423 (**28.30 %**) | **4** |
| `vmlinux` built here, `-march=5281` | 65,740 | 117 (**0.18 %**) | **21,185** |
| **this unit's own decompressed kernel** | 63,298 | 19,419 (**30.68 %**) | **0** |

🔄 **This table was published first over the whole image with `--allow-mips16`,
and that was worse in every way.** Those numbers are kept because negative
results stay: 117,759/33,878/**256**, 118,406/2,437/**36,264**,
143,555/42,932/**168**. They were run in a mode `hazlint` itself calls *not a
conservative answer, it is no answer*, and the reason given for using it — *"a
bounded range would not be the same range in each"* — **is false**: one bound
serves all three, and `hazlint` accepts it with no override at all. The bounded
reading is sharper on every axis, and **this unit's kernel goes to zero**.

🔴 **This unit's kernel sits on the 4181 side by both measures at once**: its nop
rate is within 2.4 pp of the 4181 build and 170× the 5281 build's, and it carries
**zero** violations against the 5281 build's 21,185. Two builds of the same
source, differing in which rsdk drove them, and the shipped image is not near the
midpoint of anything.

**推, and it is a much stronger 推 than a nop rate alone**: the firmware on this
unit was built by a toolchain in the load-delay-exposed class.

⚠️ **Do not mix these numbers with `hazlint`'s `K4b` control**, which reads the
same kernel over a different range (bounded below `0x802B8000`) and reports
128,440 loads / 40,182 nop (31.28 %) / 58 violations. Both are right for their
ranges; the three rows above are comparable to each other.

⚠️ **The 4 are not explained.** They are four sites in 61,568 loads and nothing
here says what they are. The 21,185 are not explained either, beyond being what a
toolchain that does not pad produces.

⚠️ **And the discarded whole-image numbers are a warning about method, not just a
superseded table**: 168 for this unit's kernel and 256 for the 4181 build were
both mostly *data read as code*, because a `vmlinux`'s single executable
`PT_LOAD` contains `__ex_table`, `.rodata` and `.data`. The bounded range removes
that and takes this unit to zero. **A wider scan is not a more conservative
scan.**

⚠️ **This is a reading of two compilers, not of the die.** Whether the silicon
has the interlock is `R1a` / `CPU-14`, and nothing here moves it.

---

## 6. `-fuse-uls`: it is in no drop's build system

The question was how each of the three drops passes `-fuse-uls`. 量 2026-08-28:
**none of them does.** In every drop, exactly two files mention it, and both are
inside the rsdk-1.5.5 toolchain's own uClibc configuration:

    toolchain/rsdk-1.5.5-.../include/bits/uClibc_config.h:179
    toolchain/rsdk-1.5.5-.../config/uclibc/config/default:194
      UCLIBC_EXTRA_CFLAGS="-march=5281 -EB -fuse-uls -msoft-float -ffix-bdsl"

`-fno-use-uls` appears **zero** times in any drop. `boa`'s own Makefile sets
`export CC = rsdk-linux-gcc` and `CFLAGS = -Os -pipe` and no `-march`, no
`-fuse-uls`. The kernel's Makefiles mention neither.

**Control for that zero** — the same grep over the same corpus, per drop:

| drop | `fuse-uls` | `CPU_HAS_ULS` | `march=5281` | `ffix-bdsl` ⚠️ |
|---|---|---|---|---|
| `rtl819x-toolchain` | 2 | 48 | 1141 | 2 |
| `saturn49-wecb` | 2 | 41 | 1143 | 2 |
| `wecb-vz-gpl` | 2 | 41 | 1055 | 2 |

⚠️ **The `ffix-bdsl` column is not an independent control** — it matches the same
two files, on the same line of the same `UCLIBC_EXTRA_CFLAGS=` string, as
`fuse-uls` itself. Two of the three columns are controls; the third is the
measurement wearing a control's hat, which is the defect commit `55bc7c1`
recorded for the noise floor and it recurred here.

**Method**: `grep -rlI ... --exclude-dir=.git`. Without `-I` every column grows by
the toolchain binaries that carry the flag compiled in (22 for `fuse-uls`).

🔴 **So the switch is the toolchain, not the source.** A build that goes through
the 1.5.5 wrapper gets `-fuse-uls` and emits `lwl`/`lwr`; a build that goes
through either 1.3.6 wrapper does not. 量, same C, same `-O2`, `-S` so `as` is
not in the path, `lwl+lwr+swl+swr`:

| toolchain | default | `-fuse-uls` | `-fno-use-uls` |
|---|---|---|---|
| 1.3.6-4181 (at 4180 **and** at 4181) | 0 | 4 | 0 |
| 1.3.6-5281 | 0 | 4 | 0 |
| 1.5.5-5281 | **4** | 4 | 0 |

⚠️ **The sentence to retire is "compiler-emitted `lwl` dates a binary's
toolchain".** It dates the **rsdk generation whose wrapper built it** — which is
a coarser and more useful thing than a version number, and it is why
`notes/lwl-mystery.md`'s 2019 drop to zero needs no exotic explanation.

---

## 7. What this says about which drop, and it is a new discriminator

Each drop ships its own top-level `.config`, generated by the vendor, naming the
toolchain **that drop is configured to build with**:

| drop | generated | board | rsdk selected | model |
|---|---|---|---|---|
| `rtl819x-toolchain` | 2013-06-29 | **rtl8196e** | `rsdk-1.3.6-4181` | `RTL8196E_88E_GW` |
| `saturn49-wecb` | 2012-08-15 | rtl8198 | `rsdk-1.3.6-5281` | `RTL8198_SPI_SQUASHFS` |
| `wecb-vz-gpl` | 2012-08-15 | rtl8198 | `rsdk-1.3.6-5281` | `RTL8198_SPI_SQUASHFS` |

Control: each file carries three `CONFIG_RSDK_*` lines and exactly one is `=y`.

🔴 **Not one of the three selects a 1.5.5 toolchain, and this unit's kernel
banner is `gcc version 4.4.5-1.5.5p2`.** That is the **second** surviving
discriminator saying the drops on hand, as configured, did not build this image —
beside the `IMEM0_SIZE` mismatch in `notes/vendor-kernel-isa.md` §4.1. There were
three; the MIPS16 one died today (§4.2 of that file), which is why this is second
and not third.

⚠️ **It is a discriminator about configuration, not about capability.** A drop's
`.config` can be changed; what it cannot do is produce a toolchain it does not
ship, and none of the three ships a 1.5.5p2, nor any 1.5.5 configured for 4181.

⚠️ **Two of the three drops are for a different SoC** (RTL8198). Only
`rtl819x-toolchain` is an RTL8196E drop, and it is the one whose `target` symlink
already points at `boards/rtl8196e`.

### The `.comment` toolchain stamp, and why it is mostly not there

An ELF's `.comment` records the gcc that produced each object.

**Control first — can the scan see anything at all?** Per tree, ELF files that
still have section headers:

| tree | ELF files | keep section headers | verdict |
|---|---|---|---|
| `unit-2018` | 55 | **1** | blind |
| `n200re-3.2.0` | 62 | **1** | blind |
| `n300rt-2.1.6` | 63 | **63** | scannable |
| `v2.1.2` | 64 | **64** | scannable |
| `v3.4.0` | 50 | **1** | blind |
| `n300rt-3.4.0` | 50 | **1** | blind |

Four of six trees, **including this unit's**, are `sstrip`ped — the vendor ships
`rsdk-linux-sstrip` and it removes the section headers outright. On those four a
`.comment` scan means **not looked for**, never *not there*.

Where it can be read: `n300rt-2.1.6` and `v2.1.2`, in `bin/boa` and
`lib/libapmib.so`, `.comment` = `GCC: (GNU) 3.3.2` **and**
`GCC: (GNU) 4.4.5-1.5.5p2` — the same version string as this unit's 2018 kernel
banner.

The single file that survives in each blind tree is `/bin/acltd`, and it is
**byte-identical across all six trees** (established when the similarity metric
was built), carrying `GCC: (GNU) 3.2.3-1.2.11` and `GCC: (GNU) 3.3.2`. It dates
a prebuilt blob's original build and says nothing about any of the six builds.

⚠️ **Two readelf disagreed here and one of them was not answering the question.**
The vendor's `mips-linux-readelf` (binutils 2.16.94) has **no `-p` option at
all** — it prints a usage message — and a pipeline that greps its output records
that as "no `.comment` section". Both tools agree the section exists when asked
with `-S`. Use the host `readelf`.

---

## 8. What could still be wrong

- **Everything here is one source: the vendor's own toolchain.** By `SPEC.md`'s
  own rule that is a **B** source and a single one, so every number in this file
  is a reading of what Realtek's tools believe. Where a row in `SPEC.md` rests on
  this file alone it is marked accordingly.
- **The `-U`/`-D` pair in §2 is undetermined**, not explained. The wrapper
  evidently intends a choice and this measurement did not find the input that
  makes it.
- **§5's partition comes from two instruments that ship in the same tarball.**
  They are independent in implementation (a compiler scheduler and an assembler
  checker, one of which does not exist in the older generation) but not in
  provenance. A third source would have to be the die.
- **The `vmlinux` built here has not been run**, on the device or in an
  emulator. It links and it is the right shape; that is all.
- **The 4181-at-1.5.5 route in §2 mixes a 4181 object with a 5281 uClibc.** The
  one axis checked was `ll`/`sc`/`sync`. It is not a proof of safety.
- **`tools/tc-smoke.sh` certifies that a toolchain can build, and nothing about
  whether what it builds is right for this core.** `-march=5281` passes every
  rung and §5 is the reason that matters.
