# rlxfw

An independent firmware for the Realtek RTL8196E — a big-endian MIPS SoC with a
Lexra core — built from four vendors' GPL drops and one leaked draft register
manual, for a router whose vendor never released its source.

| | |
|---|---|
| **Target** | TOTOLINK N150RT · RTL8196E · Lexra-family core (RLX4181 or RLX5281, undetermined) · big-endian · 4 MiB SPI NOR · 32 MiB SDRAM · one unit, no spare |
| **Status** | **`v0.0` — the instruments and the record exist; the firmware does not.** No kernel of mine has been built and no byte of mine has been written to flash |
| **Measured on the device** | The vendor's own kernel, delivered over TFTP and executed from RAM, reaching userspace and answering ping — 2026-08-24, gate `R0`. 81 captures across five power cycles, **no flash-write command issued in any of them**, and the loader head and `cr6c` image header byte-identical across three kernel executions and two uploads |
| **What that claim does *not* say** | *"zero flash bytes written"*. The evidence reaches **512 bytes of a 4,194,304-byte part** — the two regions read back — and no instrument here can establish more than that. `PROGRESS.md`'s `R0` row carries the wording and why it changed |
| **Measured on the core** | 🆕 **2026-08-25, gate `R1`: 19,792 bytes of my own bare-metal code executed on this silicon and reported back on two channels that agree word for word.** The cache model is no longer read: the I-cache **does** hand back stale bytes with no flush (the negative control, on both victims of a pair 7 KiB apart, and it is the *opposite* of what qemu returned); a cached store to a line the D-cache does **not** hold reaches memory unaided (🔄 **narrowed 2026-08-26 from *"the D-cache is write-through"*, which those two cells cannot distinguish from write-back-without-write-allocate**); **`CCTL 0x002` alone is sufficient** for the instruction side, so the vendor's flush-D-then-invalidate-I is unnecessary rather than wrong; and 🔴 **`Status.IsC` does not isolate on this part — its byte stores reach DRAM**, which is the path the vendor's Linux uses and this unit's own bootcode never does |
| **Measured on the core** 🆕 | 🔴 **2026-08-25, second seating: the CP0 census ran under an exception handler of my own, installed at `0x80000080` and read back word for word before it was trusted.** `Status.BEV = 0`, so the vectors are in RAM and **the core fetches there** — `break` trapped into my handler and returned. **`PRId = 0x0000CD01`**, predicted in writing before the run. **`Count` is not implemented**, so this SoC's timer driver is a prerequisite and not a bonus. **The CP0 ignores the select field.** **CP0 register 20 reads zero for real** — the census reads every register twice with two different primes, so *reads zero* and *the destination was never written* are different observations, and `nowrite` was 0 on all 256. `Config.M = 0`, so this is not a MIPS32 core |
| **Not measured** | 🔄 **The cache geometry, and the two routes to it are now measured shut rather than untried**: `Config` reads zero so there is no `Config1`, and the R3000 sizing walk needs cache isolation that this part does not implement, so it can only return its own *no answer* value. What is left is an eviction walk that needs no isolation. **The pipeline hazards**, which need a controlled loop and a timing harness. 🆕 🔴 **Whether a DMA write is visible to a cached CPU read** — nothing has been measured in that direction at all, and it is the one driver decision the cache gate closed without. 🆕 **Whether this silicon retires the `cache` instruction** — its own kernel contains 37, and none has been executed by anything of mine. And 🔴 **what `0x0000CD01` is the part number of** — the value is measured, the mapping to a Lexra model number is not, so **`RLX5281` stays unwritable, and so does `RLX4181`** |
| **Baseline** | [`upstream/`](https://github.com/Jhongwe1/router-firmware-re) pinned at `4d3ff26`, read-only. The differential proof this project is built toward is only worth anything against a baseline it cannot edit |

The last two rows are the ones to read. A binary that avoids an instruction is
evidence about the toolchain that compiled it, not about the hardware that runs
it, and every ISA claim in this repository is still of the first kind.

## What is in here

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

**[`notes/lwl-mystery.md`](notes/lwl-mystery.md)** — MIPS Technologies sued
Lexra over the patent covering `lwl`/`lwr`/`swl`/`swr`, and Lexra's cores
implement MIPS I without them. This unit's `/bin/boa` contains 144. Its
bootcode, written by Realtek, contains none in 40 KiB of code — and neither does
the vendor's own `busybox`. Across six firmware builds `boa` carries 176, then
144, then zero from 2019 onward.

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
