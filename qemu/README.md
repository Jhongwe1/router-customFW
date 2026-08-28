# `qemu/` — captures from the emulator, and what they cannot show

**A capture in here is not a measurement of this device.** It is a recording of
what a payload did on `qemu-system-mips -M malta`, and that machine is a 24Kf —
a MIPS32 part with interlocks, a coherent I-cache as far as the guest can tell,
no D-cache modelled at all, and no `cache`-instruction op-field decoding. This
directory is separate from `bench/` for exactly that reason: `bench/` is silicon
and this is not, and a reader sweeping for readings must never have to work out
which is which from a filename.

**Written 2026-08-26, `R1h-1`.** Until that day this repository had never
committed a single qemu serial capture — `qemu-run.sh` wrote into a `mktemp -d` —
so every *"expected under qemu"* value in `docs/probe3-cells.md` rested on prose
plus one CI assertion, with no artefact behind it. That is what this directory
fixes.

## What a pass here means

The four things it demonstrates, and they are all about the payload rather than
about the silicon:

1. the image is linked where it thinks it is and the entry is its first byte;
2. the report is well formed and the run reaches its own end marker, so *"it
   stopped"* and *"it ended"* are different observations;
3. every self-gate fires in the direction it is written for — a group whose
   precondition fails reports **void with a reason** rather than a pass;
4. a mutation planted in one check makes that check, and only that check, fail.

## What it cannot show, stated so a clean run is not read as more than it is

- **qemu interlocks the load delay slot and this core does not.** That is `F46`,
  it is measured on this device, and it is the whole reason `tools/hazlint`
  exists as a build gate rather than as a lint.
- **The expectations are OPPOSITE, and that is the point.** TCG invalidates a
  translation block when a store lands on code it has already translated, keyed
  on the *physical* address — so both the KSEG0 and the KSEG1 window behave like
  a machine with a coherent I-cache, and every cache cell comes back FRESH.
  On silicon `probe1` cell 1 came back **`01` STALE** (量,
  `bench/2026-08-25/H1b.log:9`) where qemu said FRESH.
  **A qemu run that looks like the device is the run to distrust.**
- **An emulator kinder than the device certifies exactly the bugs the device
  rejects.** That is how upstream's `P9-12` was certified by its own simulator
  before it failed on this silicon.

## 🆕 2026-08-29: there are now TWO channels in here, and they disagree about the UART

Everything above and below was written for `tools/rlxprobe/qemu-run.sh`, which
runs a bare-metal payload. `tools/deskchan.py` runs a **kernel image**, and it
differs in every line that matters:

| | `qemu-run.sh` (`2026-08-26/`) | `deskchan.py` (`2026-08-29/`) |
|---|---|---|
| entry | `-kernel <elf>` | four-instruction `-bios` stub + `-device loader,addr=0` |
| CPU | malta's default, a **24Kf** | `-cpu 4Kc` (量: 4Kc, 24Kc and 24Kf give the same counts) |
| memory | `-m 32` | `-m 128` |
| UART | ISA COM1, `0xB80003F8` / `0xB80003FD`, `-serial` **0** | CBUS, `0xBF000900` / `0xBF000928`, `-serial` **2** |
| what changes in the image | three build constants, recompiled | two patches applied to the binary: four COP3 words → `nop`, five words in `prom_putchar` |

🔴 **And the UART row is a contradiction between two of this repository's own
measurements, which is why it is written out rather than smoothed over.**

* 量 2026-08-26, committed in `2026-08-26/probe3.txt`: a payload writing
  `0xB80003F8` under `-kernel` produced **5,893 bytes**. The ISA window works.
* 量 2026-08-29, `deskchan.py`'s `C1`: a `-bios`-only stub writing the same
  address, with the file chardev on `-serial` 0, produced **nothing**, and a
  poll of `0xB80003FD` read 0 forever.

**One variable differs and it is the entry mechanism.** With `-kernel`, qemu's
malta writes its own bootloader into the reset window and that code initialises
the board before jumping; with `-bios`, the four instructions that replace it
initialise nothing. **That the GT64120's PCI/ISA decoders are what is missing is
推, not measured** — it is the obvious candidate and no experiment here
separates it from the others. What IS measured is that the CBUS UART at
`0xBF000900` answers on both paths, which is why the kernel channel uses it.

**Neither capture is wrong and neither generalises.** A reader taking the UART
addresses out of the table below and using them under `-bios` gets silence, and
would read it as *the code never got there*.

## The build is not the same image

`qemu-run.sh` rebuilds with three constants changed and nothing else:

| | device | qemu | why |
|---|---|---|---|
| `UART_THR` / `UART_LSR` | `0xB8002000` / `0xB8002014` | `0xB80003F8` / `0xB80003FD` | this part's 16550 registers are four bytes apart; Malta's is an ordinary ISA one |
| `VEC_GENERAL` | `0x80000080` | `0x80000180` | R3000 layout vs MIPS32's |
| `CLEAR_BEV` | 0 | 1 | Malta comes out of `-kernel` with `Status.BEV` set, which is the one state the payload refuses to install into |
| `RET_ERET` | 0 | 1 | `rfe` is MIPS-I and a Reserved Instruction on a 24Kf; the handler would fault inside itself |

Each capture's `.build` file records both sets and the **device** image's
`sha256`, because the file next to it was produced by the other one.

## Layout

```
qemu/<date>/<payload>.txt      the serial capture, verbatim
qemu/<date>/<payload>.build    host, qemu version, toolchain, both builds,
                               the device image's sha256, and the capture's own
```

`tools/audit-bench-log.py` is run over this directory before anything in it is
pushed — the same scan `bench/` gets, with the same eight patterns and the same
synthetic positive control, because *"it is only an emulator log"* is not a
reason to skip the check that decides whether a file identifies this unit.

Captures are committed **only when they are evidence for a written expectation**.
`qemu-run.sh`'s default output goes to `tools/rlxprobe/build/qemu/`, which is
gitignored; putting one here is a deliberate act.
