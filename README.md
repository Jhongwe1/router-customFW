# rlxfw

An independent firmware for the Realtek RTL8196E — a big-endian MIPS SoC with a
Lexra core — built from four vendors' GPL drops and one leaked draft register
manual, for a router whose vendor never released its source.

🎬 **[60 seconds: a kernel of mine boots this device to a shell, and pings](https://youtu.be/7UjzFiAmzVs)**

⚠️ **It is a replay, not a recording of the board.** Seven committed serial
captures played back at true wire speed — every byte comes from a file under
[`bench/`](bench), and the command that produces it is
`tools/replay-capture.py reel config/r3-11-reel.tsv`, so anyone who clones this
repository can re-run it and get the same frames. A recording can only be
believed; this can be checked. **The last segment is a control**: the *vendor's*
own firmware booting on the same board, with `start address: 0x80003440` in its
header where the first segment shows `0x80003600` — because this loader
re-stages the vendor kernel on a watchdog reset, so *a banner appeared* is not
evidence that my image ran. The viewer's first objection is answered inside the
artefact rather than in prose beside it.

**Release: [`v0.2`](https://github.com/Jhongwe1/router-customFW/releases/tag/v0.2) · what it does not establish: [`docs/KNOWN-ISSUES.md`](docs/KNOWN-ISSUES.md).**

| | |
|---|---|
| **Target** | TOTOLINK N150RT · RTL8196E · **Lexra RLX4181** (🆕 2026-08-27: named from a `PRId` assignment table in the vendor's own kernel source — `PRID_IMP_RLX4181 = 0xcd00` against a measured `PRId` of `0x0000CD01`; `RLX5281` is `0xdc01` and is now excluded rather than merely unproven) · big-endian · 4 MiB SPI NOR · 32 MiB SDRAM · one unit, no spare |
| **Status** | 🔴 **`v0.2` — a kernel of mine boots on the device, to a shell that answers, and pings, and the tree that builds it builds it the same way twice. The firmware does not exist yet.** 🆕 **2026-09-01: `P4a` is closed at Level 1** — two builds of the declared recipe are byte-identical, and one byte of a string literal moves the sha256. ⚠️ **Level 1 is one machine**: this 2.6.30 has no `KBUILD_BUILD_USER`/`_HOST`, so the banner carries `whoami@hostname` and a third party rebuilding the published recipe does not match this hash. That, and everything else this release does not establish, is in [`docs/KNOWN-ISSUES.md`](docs/KNOWN-ISSUES.md). 🆕 **2026-08-31: the gate that claim belongs to (`R3`) is CLOSED** — twelve steps of twelve, D1–D5 all holding **in one boot** with the discriminator present, both decisions' refutation conditions unfired and all four stop-loss clauses unreached. 🔴 **And the write-up carries a section on what it did NOT establish**, because the gate closes anyway: the flash bracket reaches 0.0244 % of the part so `G8b`'s sentence is still unsayable, **there is still no driver of mine**, and `D3`'s own written observable (`MemTotal:`) is a string this kernel never prints — that row passed on a substitute and is recorded as a defect in the DoD. `notes/kernel-build.md` §21. 🆕 **2026-08-29**: `loudm` was delivered to RAM over TFTP and entered from the loader prompt; it printed all eleven of its boot marks, `cat /proc/version` returned **my** build stamp rather than the vendor's, and `ping -c 4` got 4 replies with the host's own capture holding request and reply. On the power cycle before it a bare-metal payload of mine measured this die's instruction cache — **16 KiB, 16-byte lines, two-way** — with the controls that would have voided the number firing in both directions. **No flash-write command was issued** — and that is deliberately weaker than "no byte of mine has been written to flash", which this project's own `G8b` row forbids without a full re-dump; no `FLR` bracket ran this seating, so the flash-byte count is **unmeasured**. There is still no driver of mine: the ping went out through the vendor's own driver in the vendor's own configuration. 🆕 **2026-08-30**: the same kernel built quiet (`quietm`) booted in **7.26 s**, and the seating spent its two power cycles on a flash bracket instead of on new firmware — three 256-byte windows, two rounds, **768 of 4,194,304 bytes byte-identical** (🔄 **2026-08-31: 1,024 = 0.0244 %, four windows, and the bracket now has a negative control — every destination read before its `FLR`, all eight pre-reads differing**) to the reference dump, **including `H601`**, which is the region a wrong write cannot be undone in and which no earlier bracket had ever read. 31 predicted cells, **30 matched and 1 refuted** — ⚠️ *(this row said “31 hit”, and `31 of 31` is not a hit rate: it is `check-predictions.py`'s **ordering** report, that no capture is older than the prediction naming it)*. The refuted one: `quietm` printed 849 bytes where 401 was predicted, all five predicted terms exact and a sixth asserted to be zero worth 448 — fifteen lines the vendor's driver routes through `panic_printk`, which `CONFIG_PRINTK=n` does not remove. *(Until 2026-08-29 23:09 this row read "**Nothing of mine has executed on the silicon**"; before that day it read "**No kernel of mine has been built**".)* 🆕 **2026-08-31 (seating 8), and it is `R3`'s last cell that needed power**: a bare-metal payload timed the memory-mapped SPI window at two strides and got the same number both ways (`R = 1.0000`), which closes the last open row of `FW-34` — the window does not buffer a single-word read. The same run put the **two-way** cache geometry on a second, independent footing: the victims that thrash at the boundary point arrive as **ten `{k, k+256}` pairs and no singleton**, a shape direct-mapped cannot produce although it predicts the same count. 🔴 **And the result block's own checksum caught a single DRAM bit that changed while the board was off** — after which a fourth power cycle measured the decay properly, **598 of 22,976 bits over 35.1 minutes**, and retracted the thermal explanation this session had written for it an hour earlier. The flash figure is unchanged at **1,024 bytes = 0.0244 %**, now with an observed vendor-firmware boot bracketed between two rounds of it. |
| **Measured on the device** | The vendor's own kernel, delivered over TFTP and executed from RAM, reaching userspace and answering ping — 2026-08-24, gate `R0`. 81 captures across five power cycles, **no flash-write command issued in any of them**, and the loader head and `cr6c` image header byte-identical across three kernel executions and two uploads |
| **What that claim does *not* say** | *"zero flash bytes written"*. The evidence reaches **1,024 bytes of a 4,194,304-byte part — 0.0244 %** — four windows read back across two power cycles, and no instrument here can establish more than that. 🔄 **2026-09-02: this read *512 bytes* and that was two errors in one clause.** 512 is `H601`'s own coverage (512 of its 8,192 = **6.25 %** exactly — written unrounded because 6.25 is a half-way value and `round()` and prose disagree about it), and pairing it with the whole part's 4,194,304 understates the real figure by half; the whole-part number has been 1,024 since seating 8 on 2026-08-31, and seating 9 re-read four windows on 2026-09-01 without moving it. Caught by re-deriving it against `CLAUDE.md` and `PROGRESS.md`, not by any checker — `CNT-1`'s class. `PROGRESS.md`'s `R0` row carries the wording and why it changed |
| **Measured on the core** | 🆕 **2026-08-25, gate `R1`: 19,792 bytes of my own bare-metal code executed on this silicon and reported back on two channels that agree word for word.** The cache model is no longer read: the I-cache **does** hand back stale bytes with no flush (the negative control, on both victims of a pair 7 KiB apart, and it is the *opposite* of what qemu returned); a cached store to a line the D-cache does **not** hold reaches memory unaided (🔄 **narrowed 2026-08-26 from *"the D-cache is write-through"*, which those two cells cannot distinguish from write-back-without-write-allocate**); **`CCTL 0x002` alone is sufficient** for the instruction side, so the vendor's flush-D-then-invalidate-I is unnecessary rather than wrong; and 🔴 **`Status.IsC` does not isolate on this part — its byte stores reach DRAM**, which is the path the vendor's Linux uses and this unit's own bootcode never does |
| **Measured on the core** 🆕 | 🔴 **2026-08-25, second seating: the CP0 census ran under an exception handler of my own, installed at `0x80000080` and read back word for word before it was trusted.** `Status.BEV = 0`, so the vectors are in RAM and **the core fetches there** — `break` trapped into my handler and returned. **`PRId = 0x0000CD01`**, predicted in writing before the run. **`Count` is not implemented**, so this SoC's timer driver is a prerequisite and not a bonus. **The CP0 ignores the select field.** **CP0 register 20 reads zero for real** — the census reads every register twice with two different primes, so *reads zero* and *the destination was never written* are different observations, and `nowrite` was 0 on all 256. `Config.M = 0`, so this is not a MIPS32 core |
| **Not measured** | 🔄 **The cache geometry, and the two routes to it are now measured shut rather than untried**: `Config` reads zero so there is no `Config1`, and the R3000 sizing walk needs cache isolation that this part does not implement, so it can only return its own *no answer* value. What is left is an eviction walk that needs no isolation. **The pipeline hazards**, which need a controlled loop and a timing harness. 🆕 🔴 **Whether a DMA write is visible to a cached CPU read** — nothing has been measured in that direction at all, and it is the one driver decision the cache gate closed without. 🆕 **Whether this silicon retires the `cache` instruction** — its own kernel contains 37, and none has been executed by anything of mine. 🔄 ~~And **what `0x0000CD01` is the part number of**~~ — **answered 2026-08-27 and it is still not a measurement**: the mapping comes from `arch/rlx/include/asm/cpu.h`, a header the port itself never reads, byte-identical across three drops. It is corroborated by this unit's kernel *behaving* like the RLX4181 column of the board configs — zero `ll`/`sc`/`sync` in 2.85 MB of text, where RLX5281 boards build with both — which is evidence of a different kind from a constant |
| **Baseline** | [`upstream/`](https://github.com/Jhongwe1/router-firmware-re) pinned at `4d3ff26`, read-only. The differential proof this project is built toward is only worth anything against a baseline it cannot edit |

The last two rows are the ones to read. A binary that avoids an instruction is
evidence about the toolchain that compiled it, not about the hardware that runs
it, and every ISA claim in this repository is still of the first kind.

🔄 **That was true of every ISA claim here until 2026-08-27. Two are now of the
second kind, and both are inferred.** The core is named `RLX4181` from a `PRId`
assignment table, and `lwl`/`lwr` are inferred present because this unit's own
kernel uses them in `memcpy` while its `do_ri` carries no emulation for them —
so either the core has them or the device would not boot, and it boots. Neither
is a measurement. `R1a` is one `lwl` under a bare-metal RI handler away from
converting the second.

⚠️ **The vendor toolchains were measured too, and the first answer was wrong.**
The emission of `lwl`/`lwr` is controlled by a build flag, `-fuse-uls`, that both
rsdk generations carry; only the default differs. An earlier version of this
paragraph reported that `-march` made no difference — that reading came from a
sweep whose exit status was never checked, in which four of five points did not
compile at all. `notes/vendor-kernel-isa.md` §2.3.

🔄 **2026-08-28 narrows that further, and it is the more useful statement.**
`-fuse-uls` is not in any of the three drops' build systems — it is **injected by
the rsdk-1.5.5 wrapper** and by neither 1.3.6 wrapper, so the flag separates
toolchain *generations* rather than releases.

🔴 **And the same day the vendor's toolchain said something about the core that
no binary of theirs could.** Their compiler pads load delay slots for
`-march=4180/4181/5181` and not for `5280/5281/4281`; their 1.5.5 assembler warns
about a load-use hazard on exactly the first set and is silent on the second;
the 1.3.6 assembler has no such checker at all. Two independent instruments, one
boundary, and it falls where this device's core does. **It is still a reading of
Realtek's tools, not of the die** — but it is the first ISA-adjacent statement
here that came from something other than counting instructions in an image.
`notes/vendor-toolchains.md` §5.

## What is in here

**[`config/`](config)** 🆕 — every input rlxfw's kernel build takes
that is not the pinned vendor drop, written down instead of remembered.
[`rlxfw-kernel.delta`](config/rlxfw-kernel.delta) is the configuration as 35
rules with a reason each — 14 that rlxfw sets, 21 that kconfig derives, and
the baseline named by **sha256** rather than by filename, because three of the
four GPL drops carry a file at that exact path and two of them differ from this
one on eight symbol lines. [`rlxfw-initramfs.tsv`](config/rlxfw-initramfs.tsv)
is the first boot's userspace, 29 entries, 24 of them this device's own binaries
unmodified and 5 named as mine. [`rlxfw-sdk.config`](config/rlxfw-sdk.config)
and [`host-compat/`](config/host-compat) are the two build inputs that were
undeclared until 2026-08-28 — one of them normally produced by a curses
program, which is not a step anyone else can reproduce.


**[`notes/incremental-build.md`](notes/incremental-build.md)** 🆕 — why a
`make` with nothing touched rebuilt all 599 objects, and what it cost to find
out. The answer is not the one the question was opened on: a patch written for
the stated cause froze both suspect timestamps and the rebuild stayed at 599.
kbuild's own `V=2` names the real one — 597 of the 599 `CC` lines say
`- due to command line change`, and the two strings being compared are
byte-identical until make truncates one of them at a bare `#`. 🔴 It also
carries what the fix does **not** buy: zero on this project's default path,
because a freshly staged tree has no object files to keep.

**[`notes/kernel-build.md`](notes/kernel-build.md)** 🆕 — how rlxfw's own kernel
is built, wrapped and reached: which toolchain (`rsdk-1.3.6-4181`, with the
condition that would refute the choice), what the configuration may differ by,
what the loadable image is made of, what the first boot mounts, and how far a
kernel for this board can be run at a desk. 🔴 **Three things in it were found by
reading material this project already had.** A control that separates `-march`
from the toolchain generation had been *built* on 2026-08-28 and never read — the
note that called it *not run* was committed 48 minutes later; read, it moves the
whole-image violation count from 4 to 20,201 on the `-march` change alone and by
4.9 % on the generation. Seven `arch/rlx` assembly files rely on the **assembler**
to fill a load delay slot, worth eleven live hazards — five of them in the
exception return path — and no compiler flag would fix them because there is no
compiler in that path. And `yes '' | make oldconfig` silently turned on a CPU
sleep option the vendor had turned off, so the kernel already on disk is not a
build of the vendor's configuration.

**[`notes/vendor-toolchains.md`](notes/vendor-toolchains.md)** 🆕 — what the three
rsdk releases are, what their wrapper enforces and silently injects, and whether
they can build this board. Ends with a complete `vmlinux` linked twice from the
vendor's own source, and with the measured cost of building a 4181 kernel with a
5281-configured toolchain.

**[`notes/rebuild-vs-shipped.md`](notes/rebuild-vs-shipped.md)** 🆕 — the vendor's
own `boa` and `busybox`, rebuilt ten ways and scored against the programs cut out
of this unit's flash dump. 🔴 **It refutes the premise the step was built on.**
Holding everything else fixed, changing `-march` alone costs containment
**0.3360** while changing the source costs **0.9359** — so at `k=7` on this
material the metric reads the *code generator*, and identifying a GPL drop
through it was the wrong axis. The best cell reaches 0.8255, which is `warn`, and
it scores *higher* against the 2015 image than against this one, so it identifies
an era and not a build. What the four channels do answer is the toolchain: every
one of them is consistent with a 1.5.5-generation rsdk driving a `-march` on the
padding side, and the strongest rival was built rather than argued away and dies
on three of them. Reconstructing a config would not have closed the gap — the
vendor's own five configs for this SoC span 0.9347–0.9976, at most 0.065 against
a 0.156 shortfall — and that is measured rather than assumed.

**[`notes/cache-model.md`](notes/cache-model.md)** — the R3000-class model plus a
Lexra-defined CP0 register 20 (`CCTL`) carrying the invalidate and writeback
commands, four of which now have a name from a source that states it. 🔄 **And a
correction the file makes against itself**: MIPS I has no `cache` instruction, but
**this unit's own kernel executes 37 of them** on the D cache — the scan that had
returned zero was run on the 56 KB loader and on nothing else, and the refutation
condition this file wrote for itself is therefore met. `Config.M = 0` is measured,
so it is still not a MIPS32 core; what changed is the sentence. Two commands the
bootloader issues at reset were unnamed in every source until 2026-08-26 — 🔴 **they are `IMEM0FILL` and `IMEM0OFF`, the lifecycle controls of a 16 KiB instruction scratchpad, and the file that names them was in the vendor tree this project already reads.** The fact was in the project and the search went elsewhere, for the second time. *(as written:)* and the only
instrument that could name them is one this project declines to run. It also
carries an older correction: the general exception vector here is `0x80000080`,
not MIPS32's `0x80000180`, and the wrong address had propagated into four files.

**[`notes/binsim.md`](notes/binsim.md)** — a structural similarity metric over
six vendor firmware trees, with thirty-five controls that run before any number
is reported, because almost any function of two MIPS binaries from one vendor
returns something near 0.8 and a matrix of numbers near 0.8 reads like a result.
`k` is 7 and not the 4 a reader would expect: a word-permutation — the identical
instruction multiset in a destroyed order — still scores **0.4398** at k=4. The
window cannot come from `.text`, because four of the six `boa` have no section
header table at all. 🔴 **It refuted the threshold the plan was going to decide
on**, and it prints `REFUTED` and exits 1 rather than substituting a better
number.

**[`notes/which-drop.md`](notes/which-drop.md)** — reading that matrix, and the
floor that replaced the plan's. 🔴 **Its own first answer was wrong and the
record of it is in the file**: a threshold that cleared the no-shared-source
level only because it was read on a feature set 1.46× larger, since containment
divides by the smaller of the two. At a matched denominator the ordering
reverses — a pair sharing its whole upstream source across a compilation-model
change scores *below* a pair sharing none — which is why the rule now has a
`VOID` precondition rather than a third band. It also refutes a sentence this
project had been carrying: **product line is crossed with the clustering, not
confounded with it.** And it does not identify a drop: six shipped images cannot
name a source release, so `TC-02` stays 推.

**[`notes/vendor-kernel-isa.md`](notes/vendor-kernel-isa.md)** 🆕 — what this
unit's *own* vendor kernel uses and what it emulates, read out of the
LZMA-decompressed image beside the three GPL drops, and kept apart from them
throughout because they disagree twice. `ll`/`sc` and `sync` are emulated; the
FPU is not emulated at all, which 🔴 **refutes half of the reason this project's
own bench rule gives** for never measuring the ISA under Linux. The cache
model is neither `r3k` nor `r4k` but a third one, and the `#ifdef` that selects
it is why an earlier scan found 37 `cache` instructions on the D side and none
on the I side. 🔴 **And the kernel contains MIPS16**, entered with `jalx`, which
breaks the superset claim two of this project's instruments were standing on —
so both were changed, after the twelve userland binaries were re-checked and
found clean.

**[`notes/lwl-mystery.md`](notes/lwl-mystery.md)** — MIPS Technologies sued
Lexra over the patent covering `lwl`/`lwr`/`swl`/`swr`, and Lexra's cores
implement MIPS I without them. This unit's `/bin/boa` contains 144. Its
bootcode, written by Realtek, contains none in 40 KiB of code — and neither does
the vendor's own `busybox`. Across six firmware builds `boa` carries 176, then
144, then zero from 2019 onward. 🔄 **2026-08-27: the discriminator this file
named came back pointing the other way** — the vendor kernel carries no
unaligned-instruction emulation, and its own `memcpy` uses `lwl`/`lwr`. The
question the file was really asking turns out to be about the toolchain, and
that half is now measured.

**[`docs/loader-flash-write.md`](docs/loader-flash-write.md)** — the SPI
controller at `0xb8001200`, its command set including `RDID`, and what the
vendor's own upgrade path checks before writing flash. It bounds the write at
the top, against chip capacity. It does not bound it at the bottom, and `boot`
is one of the eight image signatures it accepts.

**[`docs/loader-command-semantics.md`](docs/loader-command-semantics.md)** — the
loader's seventeen commands read to instruction level, including the four that
can write an arbitrary memory address, and the 128-byte console line buffer
whose `readline` writes its NUL only on the CR path.

**[`docs/rlx-cache-and-cp0.md`](docs/rlx-cache-and-cp0.md)** — what two bare-metal
payloads measured about the cache and the CP0 file, and the four driver decisions
each reading unblocks. Three of the four name a measurement; the fourth — whether
an Ethernet driver's descriptor rings need an uncached window — names none, and
the document is mostly about why the obvious answer is not one. Written closing a
gate, it also records that the gate's own *"the D-cache is write-through"* does
not follow from what was measured, and that a refutation condition this project
wrote for itself turned out to be met.

**[`tools/rlxprobe/`](tools/rlxprobe/)** — bare-metal payloads. The build is
gated: no payload exists unless `tools/hazlint` exited 0 on the linked image.

## How the work is recorded

Six files own six different things, and nothing restates what another owns.

| | |
|---|---|
| **`PROGRESS.md`** | *where the work is*: the active gate, its step list, what is blocked, and every open question with the gate that will close it. It also carries the list of places this project's own plan turned out to be wrong |
| **`SPEC.md`** | every number this project holds about the device — part numbers, register readings, addresses, budgets. Each row marks where the **value** came from separately from where its **name** came from, and links to the file that owns the finding. It is an index and owns nothing; a correction lands in the owning file and in `SPEC.md` in the same commit |
| **`RUNSHEET.md`** | what gets typed at the bench, with every cell's expected value and refutation condition **written before power is applied**, and the results beside them |
| **`bench/`** | the raw captures, unedited, with the prediction files that were written before them. `tools/check-predictions.py` is what makes *before* checkable rather than claimed |
| **`LOG.md`** | a dated entry per session, including desk-only days |
| **`docs/`, `notes/`** | one file per finding, each stating what it did **not** establish |

Three rules run through all of it:

- **Every sentence about this machine is marked** — *measured on the device*,
  *read out of the code or the dump*, or *inferred, pending a measurement*.
  Mixed together they are worth neither.
- **Nothing counts as a result until its refutation condition is written
  first** — what outcome would have proved it wrong.
- **A tool reporting `0` is making a claim.** Every sweep needs a positive
  control; a tool that cannot fail proves nothing.

## How to check it

Every instrument here is expected to be able to fail, and ships with the
controls that show it can:

⚠️ **This is a selection, not a census, and the numbers are derived rather
than counted by eye.** 量 2026-09-02, over `git ls-files tools/` (83 files),
taking those whose first two bytes are `#!` and excluding `tools/test-*`:
**35** programs, of which **19 are described below and 16 are not** —
`audit-bench-log`, `binsim`, `ci-census`, `fetch-sources`, `fsmanifest`,
`isa-probe`, `leakscan`, `opcount`, `rbcheck`, `rebuild-census`, `repdiff`,
`rlxfw-kbuild`, `rlxprobe/qemu-run`, `tc-smoke`, `vendor-tripwire` and
`verify-backup-copy`. Each has its own controls and `tools/ci-expected.tsv` is
the census; this list is prose and it has been behind for several sessions.
🔴 **The first version of this paragraph said 25 and 7**, which were
taken off a list written by hand rather than derived — `CNT-1`'s class, inside
a note about `CNT-1`'s class, caught by re-deriving it one line later. Said here
so that an absence below is not read as an instrument without controls.

```
tools/hazlint              refuses a payload that reads a register in the load delay
                           slot. Twenty controls run before it will report (seventeen on a clone, where the two population controls have no vendor material to read), including a
                           negative control that must produce exactly 2 violations at
                           two named addresses, and a population control over 1,474
                           loads of vendor code. A control that fails stops the run.
                           1.4 stopped bounding the scan below the first MIPS16 symbol
                           and started cutting MIPS16 out BY NAME: one 714-byte function
                           had been costing 900 KB of coverage. Removing the bound
                           exposed two things it was hiding -- .rodata was inside the
                           scan, and sys_call_table is a data table linked into .text
tools/kconfig-delta.py     answers one question: is every difference between the vendor's
                           board template and the .config THIS BUILD USED on the declared
                           list? Twenty-four controls, and C6 is the one it exists for -- it
                           feeds the gate the file that was copied in rather than the one
                           the compiler saw, and must refuse. `apply` and `check` read
                           the same delta file, so the generator and the auditor cannot
                           drift apart and both keep passing
tools/mkinitramfs.py       builds R3's initramfs from a declaration in which every entry
                           names its source and is tagged `unit` or `rlxfw` -- and the
                           tag is CHECKED against the path, not trusted. A declared
                           source that is not there is refused, never replaced with
                           something similar. THIRTY-FOUR controls, four of which exist
                           because the ceiling was being measured on the ELF FILE SIZE
                           rather than on the image the decompressor writes -- 495,729
                           bytes out, 75.7 % reported where the truth is 66.2 % -- and
                           EIGHT of which arrived on 2026-08-31 as the first this
                           tool's `verify` subcommand has ever had. Every one of the
                           other twenty-six is about the DECLARATION; `verify` is the
                           half that reads the built artefact, and it is the only one
                           that can catch a mark that compiled and is not in the image
tools/test-mkinitramfs-mutants.py
                           10 mutants, baseline first, and it is the answer to a debt
                           this repository carried for five sessions. It could not be
                           written earlier: with no control touching `verify`, every
                           mutation of it would have survived and said nothing. Two
                           rows found defects in the CONTROLS rather than in the tool
                           -- one case asserted `"dev" in <output>` where `dev` also
                           occurs in a heading three lines above, so deleting the
                           whole device-number comparison left it green; another named
                           a case that cannot see it, and the label followed the
                           measurement rather than the intent
tools/rlxfw-marks.py       the first tool here that edits somebody else's source, and it
                           is a TABLE rather than a patch: one row per insertion, each
                           naming the suspect it brackets. The anchor must occur EXACTLY
                           ONCE or it refuses. Eighteen controls, and the one that earns
                           its keep is `verify` -- `check` reads the staged tree and
                           answers "did the insertion happen", which a mark can pass
                           while being absent from the image; `verify` reads the BUILT
                           artefact and the vendor's, and refuses if `--absent` is not
                           given, because "present in mine" alone is a label. It caught
                           two real defects the day it was written
tools/spec-check.py        TWELVE checks and forty case lines. C1-C7 are about
                           SPEC.md; C8/C8b/C8c/C9 are about how EVERY tracked
                           `.md` renders -- 71 files, 620 tables, ~43,000 code
                           spans -- because that is not a property of one file.
                           C8 exists because one unescaped `|` had kept a row
                           outside two of the other checks since it was written;
                           generalising it on 2026-08-30 found eight ragged rows
                           where the census behind it had said six, and exposed
                           three shapes it could not see: a row split over more
                           than one physical line, a `|`-line belonging to no
                           table (nine of them on the findings page, stranded by
                           one blank line), and a code span whose whole content
                           is whitespace -- one of which had made a READING
                           wrong, not a rendering. Nine mutations of SPEC.md and
                           ten controls on a fixture built in the process, of
                           which T1 is positive and T5 is a control on T1.
                           C11 (2026-08-31) is the twelfth: a reference to a line
                           of a payload source must carry a TOKEN from that line,
                           and the token must still be within three lines of the
                           number. It exists because editing `probe3.c` had
                           invalidated fourteen such references at once and an
                           owner audit, not a check, is what found them -- the
                           line still exists, so `does this line exist` passes.
                           Ten more case lines, of which T20a and T20b are ONE
                           EDGE EACH of the tolerance (a single case at a
                           boundary passes whether the comparison is `<` or
                           `<=`) and T21/T22 are population controls on the real
                           tree. It went red twice on the day it was written:
                           on this format's own exemplar from the day before,
                           and on the sixteen references the next payload edit
                           moved
tools/console-capture.py   45 cases, 46 results (P3 checks two things). Four of them
                           exist because the ESC heartbeat is
                           the grid every interval is quantised to, so the period each
                           capture ACHIEVED is measured and recorded, not assumed.
                           Eleven more arrived on 2026-08-30 with the terminator
                           guard -- and then six more, because a mutation pass
                           over 25 edits of that guard found TEN of them alive
                           against all forty. The class the forty could not see:
                           a waiver on any flag the cases leave at default, and
                           `--esc 25` is A-catch's own shape.
                           🔴 This entry used to end "N21 ... pins the guard
                           between the two things it has to sit between, from one
                           command". It does not. N21 sends 127 characters, a
                           length `_check_send` ACCEPTS, so it passes whether or
                           not the guard sits above it; that side was held only
                           by three other cases happening to carry no terminator.
                           N29 sends 128 and requires the LENGTH refusal, which
                           is the assertion the sentence claimed
tools/test-console-capture-mutants.py
                           25 mutations of that guard, each run against the WHOLE
                           suite above, because "the committed cases catch it" is
                           the claim and a fast proxy for the suite would be a
                           different one. Anchors must occur EXACTLY ONCE and a
                           moved anchor is reported as a SURVIVOR rather than
                           skipped; it refuses outright if the unmutated baseline
                           is not green, since every mutation would then "kill" on
                           a suite that was already red. It exists because "ten
                           survived" was a sentence in LOG.md that nothing re-ran
tools/flashwin.py          27 cases (24 on a machine without this unit's dump,
                           plus one skip covering 3), and it exists for a
                           region whose reading can
                           never be published. It renders the loader's `DW` reply
                           for a window of flash out of this unit's own dump, so
                           that H601 -- the MAC and radio calibration, the one
                           region a wrong write cannot be undone in -- has an
                           expectation computed before the seating. Its control is
                           the argument: R1/R2 require the same renderer to
                           reproduce two captures taken off the device on
                           2026-08-24, byte for byte, so a reader who cannot see
                           the withheld rendering can see that the instrument that
                           produced it reproduces two readings they can. C6/C7/C8
                           drive the publication guard as a subprocess in all three
                           directions, including that no digest is printed for such
                           a window: with the rest of the 256 bytes known, a hash
                           is a 2^24 search for the address
tools/xcheck.py            asks whether two committed instruments agree about one
                           artefact, which nothing here asked before. `looptime` and
                           `boot-timeline` both parse a capture's `.timing`, both map a
                           byte offset to a time, and both publish an interval anchored
                           two bytes apart -- and on 2026-09-01 they disagreed about the
                           third while SPEC.md cited the one without the model. Three
                           identities, the third EXACT rather than tolerant: a tolerance
                           is where a 2 ms anchor error hides. 390 artefacts, 0
                           disagreements. Its three controls each document a real
                           divergence the corpus cannot reach -- one parser sorts and the
                           other does not, while the one that does not breaks its scan
                           early, which is correct only on sorted input -- and C4 is
                           their negative control, so it is not merely trigger-happy

tools/looprun.py           runs the whole edit->result iteration and asserts something
                           NOBODY TYPED: the build computes RLXFW_SRC_ID as a sha256 over
                           config/, the kernel prints it on the console, and the run
                           requires the board to say the id the build just produced. A
                           stale image, the vendor's firmware, and the loader's own
                           re-staging of 0x80500000 from flash after a watchdog reset are
                           then all red for the same reason. 23 controls, and N1..N7 each
                           require exactly ONE of the four assertions to fail: a control
                           set where one broken input trips every check cannot say which
                           check is load-bearing. Its first run found two defects in
                           itself and two wrong counts in its own docstring

tools/check-predictions.py refuses to compare a prediction against a capture unless
                           the prediction file's mtime is earlier. Six controls, four
                           of which must FAIL. Two of the six exist only because
                           `--sweep` deliberately disagrees with the per-file check
                           on one case — a predicted cell with no capture is a
                           violation there and is not one in the sweep, and without a
                           control pinning that they would drift into agreement
                           unnoticed. `--sweep bench` reads the whole committed
                           record as a CI gate — no count here, for the reason the
                           paragraph below this list gives
tools/flrbracket.py        50 controls, and its corpus is hardware: the nine `FLR`
                           echoes, eight replies to `Y` and one to `N` that seating 7
                           recorded. It answers one question -- should the operator
                           type `Y` -- with three outcomes rather than two, because
                           *the loader did not ask* must send nothing and *the loader
                           asked about something else* must send `N`. It exists
                           because the script that drove seating 7's bracket had been
                           shown to refuse a CORRECT echo and never to refuse a wrong
                           one. Seven of the 50 drive the containment guard as a
                           subprocess: the read-back of an `H601` window may not be
                           written inside this repository, and the PRE-READ may not be
                           written there for ANY window -- its content is decided by
                           --dst's history, and MEM-17 measured DRAM keeping a
                           previous cycle's FLR output across a power cycle, and `G3` is the control that says that is a
                           guard rather than a blanket refusal
tools/test-flrbracket-mutants.py
                           41 mutants plus `B0`, and `B0` is first and is not a
                           mutant: the unmutated tool must be green through the same
                           temp root or the run refuses to report kills. Every row
                           also NAMES the case it must turn red and is a kill only if
                           that case failed. Both controls exist because a pass over
                           `flashwin` reported 8 of 8 killed and every kill was
                           invalid
tools/cardcheck.py         27 controls, and it reads a card the way the DEVICE will.
                           `commands` checks every command a card types against what
                           the image DECLARES it can invoke; `numbers` re-derives every
                           number a card states from the artefact it names. It exists
                           because seating 7 typed `wc -lc < /dev/mtd0ro` and got
                           `wc: not found` — `wc` is one of this busybox's fifty
                           applets and is not one of the eleven symlinks the image
                           declares, and those are two populations nothing compared.
                           `A11` runs the whole committed block-3 card and requires
                           exactly the two cells that failed at the bench. `numbers`
                           REFUSES a card with no ```cardnum fence rather than
                           reporting `0 of 0`, which is why the five frozen blocks
                           come back refused and that is the correct output
tools/test-cardcheck-mutants.py
                           18 mutants, baseline first. Two survived the 23 controls
                           that existed when they were written, and neither was
                           visible to any card in the corpus — one of them exposed a
                           real defect, that `/proc` and `/sys` belong to the kernel
                           and were being reported as undeclared
tools/replay-capture.py    17 controls, and it turns a committed `.log` + `.timing`
                           back into the terminal it came from - so R3-11's
                           artefact is DERIVED from evidence rather than recorded
                           beside it, and anyone with a clone can re-run it.
                           `R4` is why it is worth a suite: `W-3`, `X-3`, `V-3`
                           and `T-3` are byte-identical across three power cycles
                           and three days, so four independent captures must give
                           identical data and different timing - 248 / 256 / 259 /
                           264 records - and both halves are asserted. `T-3` is
                           the one reached with the power switch never touched. `R12` hands the result to
                           `scriptreplay(1)` itself and compares byte for byte;
                           `R13` is its negative, because without a header line
                           `scriptreplay` silently eats the first ten bytes
tools/test-replay-capture-mutants.py
                           13 killed and one declared EQUIVALENT with a proof -
                           the byte-count reconciliation cannot fire, because the
                           three checks before it make the counts telescope. An
                           equivalent row is still run and is required to SURVIVE,
                           so an edit that makes the check reachable turns it red
                           in the other direction
tools/test-gitignore.sh    six of its cases are positive controls, because a .gitignore
                           of a single `*` would pass every negative one
tools/test-opcount.sh      two of its cases exist because a counter reading the wrong
                           endianness, or ignoring alignment, is still a counter
tools/test-file-modes.sh   reads the git index rather than the working tree, because the
                           working tree is what DrvFs lies about
tools/test-rlxprobe.sh     the bare-metal payloads. Four of its cases are mutations that
                           BUILD a deliberately broken payload and run it under qemu,
                           because a suite that cannot tell a fixed payload from a
                           shipped one is not a suite. One of those four exists because
                           qemu cannot reach the state it tests at all
tools/rtkimage.py          runs Realtek's own nfjrom pipeline and reads what it produced.
                           Its R1 control is the drop's OWN shipped nfjrom, re-parsed on
                           every invocation; R2 flips one bit and requires both the
                           checksum and the payload to notice. A truncated LZMA stream
                           decodes partially WITHOUT raising, so "smaller image" was a
                           thing this had to be stopped from printing
tools/hazlint-objs.py      hazlint over every object a kernel build produced under
                           arch/rlx -- following the symlink, because plain `find` misses
                           the six BSP objects and would sweep the architecture while
                           skipping the machine. Its Q5 control re-assembles the same
                           sources from the build's own recorded command line with one
                           token changed, and requires the eleven hazards to appear
tools/deskchan.py          runs an image under qemu and reads how far it got. C1 and C2
                           prove the emulated UART's two addresses separately, because
                           "the mark did not run" and "the instrument does not carry"
                           are the two answers a silent run has to be split into
tools/reply-size.py        what the loader will send back, in bytes, before it sends it.
                           Twelve controls, and the model's constants were fitted from
                           121 captures rather than counted by hand -- which is the
                           error it was built to remove
tools/boot-timeline.py     the named intervals of a boot, with the anchor bytes stated.
                           It exists because two adjacent silences of the same length is
                           how a measurement ends up wearing another one's name
tools/looptime.py          the wall clock of a development loop, out of its own artefacts.
                           Every capture already carried started_wallclock, duration_s and
                           a .timing; nothing had joined them, so the dead time in a
                           seating and the interval from power to a typeable prompt had
                           never been read.  Its overlap bound is DERIVED -- the wall
                           clock is truncated to the second and the duration is not
```

🔄 **2026-08-29: the case counts are gone from this list, and that is a repair
rather than a tidy-up.** Three of them were stale and nothing compared them —
`test-gitignore` read 15 against an actual **18**, `test-opcount` 15 against
**29**, `test-rlxprobe` 106 against **202**. `tools/ci-expected.tsv` is the owner
of every suite's bench total and `tools/ci-census.py` fails the build when one
drifts; a second copy on this page could only ever go stale quietly, which is the
same defect this repository has now found in four different files.

**CI runs what a runner can run, and says out loud what it cannot.**
`.github/workflows/ci.yml` executes the suites whose inputs are committed text,
and a census job fails the build if a check starts skipping for a reason that is
not on `tools/ci-expected.tsv`. The suites it cannot run are the ones whose
population control is a 56 KiB vendor bootloader that cannot be redistributed;
the count is printed on every build rather than left out of the total.

🆕 **2026-08-29, and the half that could not be built is the more useful
finding.** `tools/audit-bench-log.py` scans every committed capture for anything
that could identify this device, and runs every pattern against a synthetic
positive control first; it is a CI gate. 🔴 **2026-08-30: *every committed
capture* overstated it and the same sentence had to be corrected in `SPEC.md`
§18 on the same day.** 量: the gate globs `bench/**/*.log` — **240 files**,
where `git ls-files` returns **899**. The **658** tracked files it never reads,
plus `upstream/`'s **302** that a submodule hides from `git ls-files` entirely,
hold hits on the patterns that can identify a unit. `tools/leakscan.py`
is the instrument that says so, it never prints what matched, and only its
self-test and its mutation suite are gates. 🔄 **The count that stood here
was 100 and it was never a reading on any commit** — 量 on a clean `HEAD` it was
**99**, and after a ninth pattern and four more readable extensions went in it is
**161**. 🔴 **And the finding it was reporting was the wrong value**: the MAC it
flagged is the workstation's own USB adapter, on an OUI that belongs to Actions
Microelectronics rather than to this device's vendor. `leakscan --attribute` answers
*whose address is this* by looking the bytes up in this unit's own flash dump instead
of recognising a prefix, and its answer is that exactly one hit in the corpus is this
device's — in a public file, left in place as a recorded decision because the device
is end of life (`SPEC.md` `FLS-22`, `notes/leak-surface.md`). The verdict run is a desk
step: it needs the 4 MiB dump, which can never be committed. `tools/check-predictions.py --sweep
bench` checks that every capture named by a prediction file is **newer** than
the file naming it — and it **cannot** be a CI gate, because **git does not
store mtimes**. A checkout writes every file fresh, so on a clone of this
repository the sweep reads 128 of 156 cells as out of order; 量 twice. So *the
expectation was written first* is verifiable **on the machine that took the
captures and nowhere else**, which is a harder limit than the tool's own
docstring used to state, and it is stated there now. What CI runs is that tool's
fifteen controls — eight of which must fail, four of them driving the file as a
subprocess after a mutation pass found that six function-level controls killed
only 7 of 15 mutants. Both tools refuse rather than reporting green when they
find nothing to look at.

`tools/opcount.py` counts MIPS primary opcodes by linear scan rather than
disassembly, because for an image loaded at a 4-byte aligned address the scan is
a superset of the instructions: it can count data as code but cannot miss an
instruction. Every count it prints is an upper bound, and exactly one kind of
result is rigorous — a zero.

`tools/fsmanifest.py` records type, mode, uid, gid, size, mtime and digest for
every path, because a content hash alone is blind to 762 symlinks, 12 device
nodes and 294 setuid bits in the tree it protects.

## Getting the sources

None of the vendor material is committed here. `SOURCES.json` records every
external input with its URL and sha256, and `tools/fetch-sources.sh` obtains and
verifies them. Two Realtek datasheets are read and cited but not redistributed —
`refs/README.md` says why, and records the three limits that travel with every
citation from them.

The flash dump is not here either. It contains this unit's MAC addresses and
radio calibration; it identifies one physical device rather than a model.

## Where it is going

```
S0        safety net                       closed 2026-08-23
R0        vendor kernel booted from RAM    closed 2026-08-24
R1-gate   cache model + CP0 census         closed 2026-08-26
R2a/b/d   which GPL drop this was built from   closed 2026-08-28
R1h       cache geometry, D-side coherence, `cache` retirement   closed 2026-08-29
R3        my kernel boots to a shell and pings  closed 2026-08-31
P4a       reproducible build: same tree twice -> same image sha256  closed 2026-09-01
P4b-gate  the part of the release process that blocks tagging v0.2
R4        edit -> result in under 90 s
R5        six drivers in tree, each diffed against two public ports
R1-pub    ISA / hazard / Lexra-ASE table   runs alongside R5
R6        my Ethernet driver
R7        my userspace
R8        signed update, survives power cuts
R9        three-column differential table, and the third column is not empty
```

🔴 **Which gate is ACTIVE is not written here, and the word `active` was
removed from this list on 2026-08-31 rather than moved down it.** `PROGRESS.md`
is the sole owner of current position; a status word copied to a second place
goes stale there, and this one had: it said `R1-gate ... active` for five days
after `R1-gate` closed, through the closing of `R2a/b/d`, `R1h` and `R3`, and
neither of this project's two routine audits looks at this file. The closure
DATES stay, because a date something closed is a historical fact and not a
statement about where the work is now.

### Which gates make which version

**This table is the owner of version → contents.** Until 2026-09-01 that state
lived in two places — the project's planning material, which is not committed,
and a table in `PROGRESS.md` — and 量, they disagreed on **six of six** shared
rows and on four of the six week estimates beside them. A public reader could
follow neither, because the authoritative one was invisible. So it moved here,
and the other two now point at it.

| version | the gates that define it |
|---|---|
| `v0.0` | the instruments and the desk analysis |
| `v0.1` | `R0` + `rlxprobe` executing on the silicon + `R1-gate` |
| `v0.2` | `R3`, with a 60-second take + `P4a` |
| `v0.3` | `R4` + `R5` |
| `v0.4` | `R1-pub` + `P1` |
| `v0.5` | `R6` + `P2` |
| `v0.6` | `R7` |
| `v1.0` | `R8` + `R9` + `P3` + `P4b` |

⚠️ **These are the gates a version is *defined* by, not everything that landed
in it.** `v0.1` was never tagged, so the `v0.2` release spans `v0.0` → `v0.2`
and contains `R2a/b/d` and `R1h` as well; `CHANGELOG.md` is where what a
release actually shipped is written down.

⚠️ **No dates here.** Week targets are planning estimates about one person's
availability, they are uncalibrated, and this repository's own gate board
already carries the argument for keeping estimates out of a file that records
what has been done. They stay in the planning material.

`PROGRESS.md` is the only file that says where the work actually is, and its
Release clock is the only place that says which of these versions have shipped.
`CHANGELOG.md` says what each tag contains.
`docs/GATE-RESULTS.md` says, per gate, what it established and what it did not.
