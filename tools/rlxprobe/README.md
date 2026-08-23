# `rlxprobe` — bare-metal probe payloads for the Lexra core in the RTL8196E

`DAY-ZERO` item 8. `R1` runs bare metal and not under Linux, because MIPS Linux
**emulates** `ll`/`sc` and the FPU in its Reserved Instruction handler — so
measuring the ISA under it returns false positives on exactly the two rows the
toolchain decision rests on (plan D15).

## The one thing to understand about the build

**`hazlint` is a gate, not a lint.** `probe0.bin` depends on `probe0.gate`, and
that file does not exist unless `tools/hazlint` exited 0. There is no target
that produces a runnable payload while skipping it.

That is layer two. Upstream's `P9-12` post-mortem ends on exactly this point:
adding two `nop`s made that day pass, and teaching the build to refuse is what
stops tomorrow's payload. Item 7 delivered the checker; this Makefile is the
half that makes it matter.

```
make               build, gated
make gate-check    prove the gate FAILS on a planted load-use hazard
make dis           disassemble what was actually emitted
make clean
```

Knobs: `LOADADDR=0x80500000`, `RESET=1`, `CROSS=mips-linux-gnu-`.

## What segment 0 is for

Every later segment of `R1` needs five things to work before any of its answers
mean anything: the toolchain emits code this core will run, the linker puts the
entry at offset 0, `LOADADDR`/TFTP/`J` delivers it, the UART routine talks, and
the board comes back afterwards. **`probe0` tests exactly those five**, so that
when `R1a`'s instruction sweep reports an absence, "the payload did not run" is
already excluded.

Four CP0 registers come free while it is there, and three of them are blanks in
`SPEC.md`:

| register | what it settles |
|---|---|
| `PRId` | `CPU-04` — RLX4181 or RLX5281. The project has written *undetermined* in every document since the beginning because `/proc/cpuinfo` printed a decimal number |
| `Config` | `Config.M == 0` proves this is not a MIPS32 core outright, and says whether `Config1` — cache geometry, FPU, MMU — exists at all (`CPU-25`) |
| `Status` | `CPU-27` — is `BEV` 0 at the prompt? `R1d` plans to install a handler at `0x80000180`, and that address is only right if it is. If `BEV` is 1 the vectors are in boot ROM and `R1d`'s first step changes |
| `Cause` | read for its own sake, and as the thing an exception would have written |

### The prediction for `PRId`, written before it runs

The vendor kernel on this unit prints `cpu model : 52481`, and `52481` is
`0xCD01`. Decompressed from `r0-vendor-kernel.bin` (LZMA at offset `0x2808`,
3,374,772 bytes, link base `0x80000000`), that kernel's format string is
`cpu model\t\t: %d\n` — **`%d`, not mainline's `%s V%d.%d`** — and its single
reference at `0x8000B2B4` passes `cpu_data[n] + 16`, with `sizeof` 96.

**So the hypothesis is `PRId == 0x0000CD01`**: company `0x00` (legacy, i.e. not
MIPS32-compliant, which agrees with the MIPS-I reading), implementation `0xCD`,
revision `0x01`.

It is a hypothesis and not a reading, because **this kernel's `struct
cpuinfo_mips` is not mainline's layout** — `udelay_val` is at offset 0 here, and
in mainline it is near the end — so "offset 16" cannot be mapped to a field name
from the GPL trees this repo holds.

* **Confirmed** if `prid=0000cd01`. Then `52481` is `PRId` and `0xCD` is the
  number to match against Lexra's core IDs.
* **Refuted** if it reads anything else. Then `52481` is some other field, and
  the bare-metal read is simply the only `PRId` this project has — which still
  answers `CPU-04`, it just costs the corroboration.
* **Refuted differently** if it reads `00000000` or `ffffffff`: `PRId` is not
  implemented, and `CPU-04` needs another route.

## What it deliberately does not do

* No instruction outside MIPS-I except one `mfc0` with a select field, and that
  one only after `Config` says the register exists. Verified on the built
  artefact: `hazlint --isa` reports **0 hits over 264 words**, under both the
  strict and the loose classifier.
* **No exception handler.** It runs under the loader's, which is already
  installed (`CPU-26`) — so a fault prints `Undefined Exception happen.` and
  `cp0_cause=%X, cp0_epc=%X` rather than vanishing. Installing one is `R1d` and
  needs the cache model first.
* **No hazard measurement and no timing.** Both need a handler and a controlled
  loop; a number produced without them would be a number. `hazlint --survey`
  reports **0** of every unestablished-hazard shape in this payload, so the only
  hazard class it can trip is the one that is measured and gated.
* No flash, no configuration, and no register write except `WDTCNR` at the end.

## Why it resets itself

One power cycle is the most expensive unit on this project and there is no spare
device. `rlx_reset` drains the UART (LSR `TEMT`, with the loader's own 6540
bound), waits out the CP2102's latency timer, then writes `WDTCNR = 0` and
spins — the loader's own idiom, copied verbatim from `0x804092E8` **including
what it does not do**: it masks nothing.

So a payload hands the board back to the loader prompt by itself. That is what
makes a second, third and fourth payload affordable in one seating. `RESET=0`
spins instead.

## Running it

`probe0.bin` is 1,248 bytes, linked at `0x80500000`, entry at byte 0.

> ⚠️ **`0x80500000` is where the loader stages the `cr6c` payload** (`C-16`,
> `RUNSHEET.md` `B4`/`G1`). Loading `probe0` there overwrites the staged vendor
> kernel, which costs nothing — zero flash bytes — but it destroys `G1`/`G6`'s
> reference copy. **Run `probe0` after `B3`, or build it with
> `LOADADDR=0x81000000`**, which is `§C`'s scratch region and clear of both.

The address is the one `P9-12` proved on this device, and keeping it means the
first `rlxprobe` payload differs from that one in what it does and not in where
it lands.
