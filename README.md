# rlxfw

An independent firmware for the Realtek RTL8196E — a big-endian MIPS SoC with a
Lexra core — built from four vendors' GPL drops and one leaked draft register
manual, for a router whose vendor never released its source.

| | |
|---|---|
| **Target** | TOTOLINK N150RT · RTL8196E · **Lexra RLX4181** (🆕 2026-08-27: named from a `PRId` assignment table in the vendor's own kernel source — `PRID_IMP_RLX4181 = 0xcd00` against a measured `PRId` of `0x0000CD01`; `RLX5281` is `0xdc01` and is now excluded rather than merely unproven) · big-endian · 4 MiB SPI NOR · 32 MiB SDRAM · one unit, no spare |
| **Status** | **`v0.0` — the instruments and the record exist; the firmware does not.** No kernel of mine has been built and no byte of mine has been written to flash |
| **Measured on the device** | The vendor's own kernel, delivered over TFTP and executed from RAM, reaching userspace and answering ping — 2026-08-24, gate `R0`. 81 captures across five power cycles, **no flash-write command issued in any of them**, and the loader head and `cr6c` image header byte-identical across three kernel executions and two uploads |
| **What that claim does *not* say** | *"zero flash bytes written"*. The evidence reaches **512 bytes of a 4,194,304-byte part** — the two regions read back — and no instrument here can establish more than that. `PROGRESS.md`'s `R0` row carries the wording and why it changed |
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
to fill a load delay slot, worth twelve live hazards — five of them in the
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

```
tools/hazlint              refuses a payload that reads a register in the load delay
                           slot. Eight controls run before it will report, including a
                           negative control that must produce exactly 2 violations at
                           two named addresses, and a population control over 1,474
                           loads of vendor code. A control that fails stops the run
tools/spec-check.py        eight checks over SPEC.md, and nine mutations that must
                           each produce a finding the file did not already have.
                           The eighth exists because one unescaped `|` had kept a
                           row outside two of the other checks since it was written
tools/console-capture.py   29 cases. Four of them exist because the ESC heartbeat is
                           the grid every interval is quantised to, so the period each
                           capture ACHIEVED is measured and recorded, not assumed
tools/check-predictions.py refuses to compare a prediction against a capture unless
                           the prediction file's mtime is earlier
tools/test-gitignore.sh    15 cases. Six are positive controls, because a .gitignore of
                           a single `*` would pass every negative one
tools/test-opcount.sh      15 cases. Two exist because a counter reading the wrong
                           endianness, or ignoring alignment, is still a counter
tools/test-file-modes.sh   reads the git index rather than the working tree, because the
                           working tree is what DrvFs lies about
tools/test-rlxprobe.sh     106 cases over the bare-metal payloads. Four of them are
                           mutations that BUILD a deliberately broken payload and run it
                           under qemu, because a suite that cannot tell a fixed payload
                           from a shipped one is not a suite. One of those four exists
                           because qemu cannot reach the state it tests at all
tools/reply-size.py        what the loader will send back, in bytes, before it sends it.
                           Twelve controls, and the model's constants were fitted from
                           121 captures rather than counted by hand -- which is the
                           error it was built to remove
tools/boot-timeline.py     the named intervals of a boot, with the anchor bytes stated.
                           It exists because two adjacent silences of the same length is
                           how a measurement ends up wearing another one's name
```

**CI runs what a runner can run, and says out loud what it cannot.**
`.github/workflows/ci.yml` executes the suites whose inputs are committed text,
and a census job fails the build if a check starts skipping for a reason that is
not on `tools/ci-expected.tsv`. The suites it cannot run are the ones whose
population control is a 56 KiB vendor bootloader that cannot be redistributed;
the count is printed on every build rather than left out of the total.

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
R1-gate   cache model + CP0 census         active — bare metal, on silicon
R2a/b/d   which GPL drop this was built from
R3        my kernel boots to a shell and pings
R5        six drivers in tree, each diffed against two public ports
R1-pub    ISA / hazard / Lexra-ASE table   runs alongside R5
R6        my Ethernet driver
R7        my userspace
R8        signed update, survives power cuts
R9        three-column differential table, and the third column is not empty
```

`PROGRESS.md` is the only file that says where the work actually is.
`CHANGELOG.md` says what each tag contains.
