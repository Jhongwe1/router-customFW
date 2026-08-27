# `lwl` / `lwr` / `swl` / `swr` — who uses them on this device, and who does not

**DAY-ZERO item 2a. Desk work, 2026-08-23. Nothing here was measured on the
device.** Every number below is *read out of a binary*: out of this unit's own
flash dump, or out of five vendor firmware images. What the silicon does is
still unmeasured, and R1a is what will measure it.

## Why the question exists

MIPS Technologies sued Lexra over US Patent 4,814,976, which covers the
unaligned load and store instructions `lwl`, `lwr`, `swl`, `swr`. Lexra's cores
implemented MIPS I *except* those four. An earlier 1998 trademark suit had
already been settled on the condition that Lexra describe its products as not
implementing unaligned loads and stores.

This board carries a Lexra-family core (RLX4181 or RLX5281, undetermined —
`refs/README.md` records why the datasheet's own claim is contested), and this
unit's `/bin/boa` contains 142 of those instructions by upstream's count. Either
the hardware has them, or something is emulating them.

## Instrument

`tools/opcount.py`. It reads a file as big-endian 32-bit words at every 4-byte
aligned offset and histograms the primary opcode. For an image loaded at a
4-byte aligned address, every instruction lies at an offset congruent to 0 mod
4, so the scan is a *superset* of the instructions: it can count data as code
but cannot miss an instruction. **Every count it prints is an upper bound, and
exactly one kind of result is rigorous — a zero.** That is the result this
question needs, which is why the cheap instrument is the right one here.

`objdump -d` was tried first and is useless on these binaries: `/bin/boa` has
had its section headers stripped, `-d` only disassembles sections, and so it
emits no disassembly at all and reports 0 for every mnemonic. A tool that cannot
see is still willing to report a number.

Controls, `tools/test-opcount.sh`, 15 cases:

| | |
|---|---|
| P1 | a fixture with known counts, reproduced exactly (3 `lwl`, 2 `lwr`, 1 `swl`, 4 `swr`, 1 each of `ll`/`sc`/`beql`/`pref`/`lwc1`, 2 `cache`, 1 `sync`) |
| N1 | the same bytes read little-endian must not give the same answer — it gives 0 |
| N2 | scanning from a 2-byte offset must not give the same answer — it gives 0 |
| — | when a MIPS cross-assembler is present, the hardcoded fixture is re-derived from source and compared |

Code regions were bounded from an independent signal — the fraction of words
whose four bytes are all printable ASCII, which separates `.text` from `.dynstr`
and `.rodata` — not by looking for a boundary that produced an expected number.

## Measured

### The loader, and two userspace programs from this unit

| binary | kind | code region | `lwl`+`lwr`+`swl`+`swr` |
|---|---|---|---:|
| `stage2.bin` (bootcode, Realtek) | **bare metal** | `0x80400000`–`0x8040a000` | **0** |
| `bin/busybox` (unit-2018) | userspace | `0x403000`–`0x43c000` | **0** |
| `bin/boa` (unit-2018) | userspace | `0x403c00`–`0x462000` | **144** |

Over `stage2`'s code region *every* ISA indicator is zero: no `cache`, no
`ll`/`sc`, no `sync`, no branch-likely, no SPECIAL2/SPECIAL3, no FPU, no MIPS16
`jalx`. The same is true of `busybox`. Both are strictly MIPS-I **minus the
unaligned load and store instructions** — which is precisely the subset Lexra
shipped.

### `boa` across six firmware builds

**Corrected 2026-08-27**: the `v2.1.2` row read `2015-08-25`, which is upstream's
*release* date for that firmware, in a column headed *build*. The image says
otherwise from two places that agree to within ten minutes — its BusyBox banner
reads `(2015-08-11 17:26:34 CST)` and every binary's mtime is `2015-08-11 17:36`.
The other five rows were already build dates. `SPEC.md` `FW-19` carried the same
mix and is corrected in the same commit.

| tree | build | `lwl` | `lwr` | `swl` | `swr` | total | ELF flags |
|---|---|---:|---:|---:|---:|---:|---|
| v2.1.2 | 2015-08-11 | 69 | 69 | 19 | 19 | **176** | `0x1007` … pic … mips1 |
| n300rt-2.1.6 | 2016-05-16 | 69 | 69 | 19 | 19 | **176** | `0x1007` … pic … mips1 |
| unit-2018 | 2018-01-10 | 53 | 53 | 19 | 19 | **144** | `0x1007` … pic … mips1 |
| n200re-3.2.0 | 2018-03-30 | 53 | 53 | 19 | 19 | **144** | `0x1007` … pic … mips1 |
| n300rt-3.4.0 | 2019-03-15 | 0 | 0 | 0 | 0 | **0** | `0x1005` … mips1 |
| v3.4.0 | 2020-10-30 | 0 | 0 | 0 | 0 | **0** | `0x1005` … mips1 |

`lwl` equals `lwr` and `swl` equals `swr` in all six rows. That is not a
coincidence to be explained away, it is the check: a compiler emitting an
unaligned access emits the pair, so exact pairing in six independently bounded
code regions is evidence that the bounds are right and that these are
instructions rather than data. Where the bounds are deliberately widened to the
whole executable segment, `.rodata` contributes 40 hits to `unit-2018` and the
pairing breaks — which is what a false positive looks like.

**Between 2018-03-30 and 2019-03-15, `boa` stopped containing these
instructions**, and its ELF flags lost `pic` in the same step.

🆕 **2026-08-27, later the same day — and `notes/which-drop.md` §3 says why this
table gets 2+2+2 while the same metric gets 4+2 on `busybox`.** The toolchain
axis is 4+2; `boa`'s extra split is `boa`'s own source revision plus a post-link
strip that changes no code byte. These counts are a `boa` reading, so they carry
the `boa` partition for the same reason.

**2026-08-27 — two more instruments give this table's 2+2+2 back.** The counts
above split the six as 176 / 144 / 0. `notes/binsim.md` gets the same split
twice more and from different bytes: from the container format alone
(`DT_MIPS_PLTGOT`, program-header count, `DT_NEEDED`, whether the section header
table survived — `SPEC.md` `TC-10`), and from the structural similarity of the
code windows (0.986 / 0.982 / 0.974 within the three groups, 0.058–0.068 across
the `pic` boundary). Three instruments reading three different parts of the same
files, agreeing on one partition.

⚠️ **They are not three independent confirmations, and saying so would be
wrong.** All three are downstream of the same build changes, so agreement is
what you would expect and it is not evidence three times over. What it rules out
is narrower, and is the thing worth having: **no single instrument's error
accounts for the split.** A miscounted code region in *this* scan would have to
coincide with a partition read out of ELF headers this scan never looks at.

### The three hits in `stage2.bin`, adjudicated

The whole-file scan of all 56,592 bytes returns 1, not 0. All three exotic hits
are outside the code region and all three are data:

| hit | word | what it is |
|---|---|---|
| `lwr` @ `0x8040d760` | `9a000000` | inside a table of small integers (`1`, `3`, `8`, `0x15`) and a self-pointer `8040acb0` |
| `cache` @ `0x8040d264` | `bc000312` | immediately after a `jr ra` / `addiu sp,sp,32` epilogue, followed by zero padding; decodes to `cache 0x0,786(zero)` — base `zero`, address 786, not a plausible instruction |
| `ll` @ `0x8040ab14` | `c0a80001` | **`192.168.0.1`**, four bytes before the string `"\nSwitch core initialization failed!\n"` |

A lone `lwr` with zero `lwl` cannot be code.

## What this establishes, and what it does not

**Established, read out of the binaries:** Realtek's own bootcode for this SoC
uses none of the four instructions in 40 KiB of code, and neither does the
vendor's `busybox`. `boa` used them until some point in 2018–2019 and then
stopped.

**Not established:** whether the silicon implements them. Nothing here is a
measurement on the device. A binary that avoids an instruction is evidence about
the toolchain that built it, not about the hardware that runs it.

**Refutation condition, written before the scan:** the claim "`stage2` contains
none of the four" is refuted by any 4-byte aligned word in the file whose
primary opcode is `0x22`, `0x26`, `0x2A` or `0x2E` and whose neighbourhood
decodes as code. One such word exists; it does not decode as code, and its
partner instruction is absent.

## Where DAY-ZERO's prediction was wrong

DAY-ZERO 2a predicted the split would be **bare metal versus userspace** — that
Realtek's bootcode authors knew not to use these instructions while userspace
took the toolchain default and let the kernel clean up.

The split is not there. `busybox` is userspace, on the same rootfs, on the same
unit, and it has none either. The split is **`boa` against everything else**,
and it closes in 2019. So the follow-up DAY-ZERO assigned to R2 — "what does the
vendor's rsdk do with `lwl`?" — is now a narrower and better question: *what was
different about how `boa` was built, and what changed in 2019?*

## Next measurements, in the order that would settle it

1. **Does the vendor kernel contain an unaligned-access emulation handler?**
   This is the discriminator. If it does, the hardware lacks the instructions and
   every one of `boa`'s 144 sites was a trap into the kernel. The kernel is not
   carved yet — `extracted/*/` holds only `rootfs.squashfs` and its expansion.
   (R2)
2. **R1a on the device, bare metal.** Execute one `lwl` under a Reserved
   Instruction handler. That is the only thing here that measures the silicon.
3. **Compile a program with unaligned struct access using the vendor rsdk and
   count.** Settles what the vendor toolchain emits, which is the other half of
   the 2019 change. (R2)
4. If the hardware does lack them: `boa` on this unit takes a kernel trap on
   every unaligned string access, and the cost is measurable. (P2)
