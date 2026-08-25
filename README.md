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
| **Measured on the core** | 🆕 **2026-08-25, gate `R1`: 19,792 bytes of my own bare-metal code executed on this silicon and reported back on two channels that agree word for word.** The cache model is no longer read: the I-cache **does** hand back stale bytes with no flush (the negative control, on both victims of a pair 7 KiB apart, and it is the *opposite* of what qemu returned); the D-cache is **write-through**; **`CCTL 0x002` alone is sufficient**, so the vendor's flush-D-then-invalidate-I is unnecessary rather than wrong; and 🔴 **`Status.IsC` does not isolate on this part — its byte stores reach DRAM**, which is the path the vendor's Linux uses and this unit's own bootcode never does |
| **Not measured** | The rest of the **core**: `PRId`, `Status.BEV`, the CP0 census, the pipeline hazards and the cache geometry are still read out of binaries and vendor source. **Do not write `RLX5281`.** Those need a second payload, and it is not going to the bench until the four defects an independent audit found in it are fixed against the values the first seating measured |
| **Baseline** | [`upstream/`](https://github.com/Jhongwe1/router-firmware-re) pinned at `4d3ff26`, read-only. The differential proof this project is built toward is only worth anything against a baseline it cannot edit |

The last two rows are the ones to read. A binary that avoids an instruction is
evidence about the toolchain that compiled it, not about the hardware that runs
it, and every ISA claim in this repository is still of the first kind.

## What is in here

**[`notes/cache-model.md`](notes/cache-model.md)** — MIPS I has no `cache`
instruction. This core uses the R3000 model, `Status.IsC`/`SwC`, plus a
Lexra-defined CP0 register 20 that carries the invalidate and writeback
commands. Two sources agree on `0x002` (invalidate I-cache) and `0x200` (flush
D-cache); two further commands the bootloader issues at reset have one source
and no name, and are recorded as undetermined rather than guessed. The file also
carries a correction: the general exception vector on this core is `0x80000080`,
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
tools/spec-check.py        seven checks over SPEC.md, and eight mutations that must
                           each produce a finding the file did not already have
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
