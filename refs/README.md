# `refs/` — vendor documentation, deliberately not committed

This directory is empty in a fresh clone. That is on purpose, and it is the only
file in here that git tracks.

## What belongs here

Two Realtek datasheets, both obtained from a third-party mirror
(`github.com/libc0607/Realtek_switch_hacking`, branch `files`). Their URLs, sizes
and sha256s are in [`../SOURCES.json`](../SOURCES.json); `tools/fetch-sources.sh`
downloads and verifies them.

| file | what it is | usable how |
|---|---|---|
| `RTL8196E-VEx-CG_Datasheet_1.1.pdf` | 83 pages, **register-level programming manual**. Interrupt controller, timer/watchdog, GPIO, UART, SPI flash controller, switch core, PCIe, pin muxing, power-on strapping, EJTAG | text layer present; machine-readable |
| `RTL8196C-GR_Datasheet_0.7.pdf` | the sibling part | **scanned images** (11 `CCITTFaxDecode` streams, no text layer). Text extraction fails and reports that it failed. A human reads it |

## Why they are not committed

`RTL8196E-VEx-CG_Datasheet_1.1.pdf` is marked
**`CONFIDENTIAL: Development Partners Only`**. Reading a document that is already
publicly mirrored, and citing it, is one thing. Republishing it from this
repository is another, and this project does not do the second one. Recording the
URL and the hash gives a reader everything they need to obtain the identical file
themselves — which is the same treatment the upstream project gives vendor
firmware images.

The same `.gitignore` rule covers any flash dump or vendor binary that ends up
here by accident.

## Three limits that must travel with every citation

1. **It is a Draft.** `Rev. D1.1, 17 July 2013`. Draft and production silicon can
   differ.
2. **It is the `-VE1/2/3` variant**, which carries embedded DRAM by MCM.
   **This unit is not that part** — it has an external Winbond W9825G6KH SDRAM.
   The peripheral register map is very likely shared. That is an assumption, not
   a measurement.
3. **Its CPU claim is contested.** It says `Embedded RISC CPU, RLX4181` and
   `Supports MIPS-1 ISA, MIPS16 ISA`. That contradicts the common
   "RTL8196E = RLX5281" convention, *and* it sits badly beside the 142
   `lwl`/`lwr`/`swl`/`swr` instructions in this device's own `/bin/boa`.

Consequently: **no register value goes into code on this document's authority
alone.** Two independent sources, always — the datasheet, an SDK header, and a
`devmem` read on the device, of which at least two must agree. Where they do not,
the note records "undetermined" rather than picking one.

The tool that enforces this is `tools/regmap-check.py`.
