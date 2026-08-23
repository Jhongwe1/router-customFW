# rlxfw

An independent firmware for the Realtek RTL8196E — a big-endian MIPS SoC with a
Lexra core — built from four vendors' GPL drops and one leaked draft register
manual, for a router whose vendor never released its source.

| | |
|---|---|
| **Target** | TOTOLINK N150RT · RTL8196E · Lexra-family core (RLX4181 or RLX5281, undetermined) · big-endian · 4 MiB SPI NOR · 32 MiB SDRAM · one unit, no spare |
| **Status** | Safety net and desk analysis done. **Nothing built, nothing flashed, zero bytes written to the device.** |
| **Read out of the code** | The loader's cache-management model, the SPI flash controller's register and command interface, and an instruction census across eight binaries — from this unit's own flash dump, cross-checked against vendor source |
| **Not measured** | **No claim in this repository has been observed on silicon.** Everything here is read out of binaries or vendor source. Nothing in this project has yet executed a single instruction on the device |
| **Baseline** | [`upstream/`](https://github.com/Jhongwe1/router-firmware-re) pinned at `4d3ff26`, read-only. The differential proof this project is built toward is only worth anything against a baseline it cannot edit |

The `Not measured` row is the important one. A binary that avoids an instruction
is evidence about the toolchain that compiled it, not about the hardware that
runs it, and this repository does not yet contain a single number taken from the
device.

## What is in here

**[`notes/lwl-mystery.md`](notes/lwl-mystery.md)** — MIPS Technologies sued
Lexra over the patent covering `lwl`/`lwr`/`swl`/`swr`, and Lexra's cores
implement MIPS I without them. This unit's `/bin/boa` contains 144. Its
bootcode, written by Realtek, contains none in 40 KiB of code — and neither does
the vendor's own `busybox`. Across six firmware builds `boa` carries 176, then
144, then zero from 2019 onward.

**[`notes/cache-model.md`](notes/cache-model.md)** — MIPS I has no `cache`
instruction. This core uses the R3000 model, `Status.IsC`/`SwC`, plus a
Lexra-defined CP0 register 20 that carries the invalidate and writeback
commands. Two sources agree on `0x002` (invalidate I-cache) and `0x200` (flush
D-cache); two further commands the bootloader issues at reset have one source
and no name, and are recorded as undetermined rather than guessed.

**[`docs/loader-flash-write.md`](docs/loader-flash-write.md)** — the SPI
controller at `0xb8001200`, its command set including `RDID`, and what the
vendor's own upgrade path checks before writing flash. It bounds the write at
the top, against chip capacity. It does not bound it at the bottom, and `boot`
is one of the eight image signatures it accepts.

## How to check it

Every instrument here is expected to be able to fail, and ships with the
controls that show it can:

```
tools/test-gitignore.sh    14 cases. Six of them are positive controls, because a
                           .gitignore of a single `*` would pass every negative one
tools/test-opcount.sh      15 cases. Two exist because a counter reading the wrong
                           endianness, or ignoring alignment, is still a counter
tools/fetch-sources.sh     hashes a known file, then a corrupted copy, and refuses
                           to trust its own verifier until the second one fails
tools/spec-check.py        seven checks over SPEC.md, and eight mutations that must
                           each produce a finding the file did not already have.
                           The controls run on every invocation, and a control that
                           fails stops the report rather than annotating it
tools/test-file-modes.sh   reads the index rather than the working tree, because the
                           working tree is what DrvFs lies about. Its control is a
                           synthetic repo carrying one violation in each direction
```

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
S0  safety net                       done
R0  vendor kernel booted from RAM    zero flash bytes written
R1  ISA / hazard / CP0 table         bare metal, positive and negative controls
R2  toolchain equivalence
R3  my kernel boots to a shell and pings
R4  edit-to-result under 90 s
R5  five drivers in tree
R6  my Ethernet driver
R7  my userspace
R8  signed update, survives power cuts
R9  three-column differential table, and the third column is not empty
```

`PROGRESS.md` is the only file that says where the work actually is. It also
carries a list of the places this project's own plan turned out to be wrong,
because a plan that records where it was wrong is more useful than one that
looks right.
