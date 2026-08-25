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
make                  build every payload, gated
make P=probe1         build one
make gate-check       prove the gate FAILS on a planted load-use hazard
make dis   P=probe1   disassemble what was actually emitted
make show  P=probe1   the numbers that go in the runsheet cell
make qemu  P=probe1   run it under qemu-system-mips -- HARNESS ONLY
make clean
```

Knobs: `LOADADDR=0x80500000`, `RESET=1`, `CROSS=mips-linux-gnu-`, and for the
later payloads `RESULT_BASE`, `GEOM`, `GEOM_BASE`. 🔄 **`FLUSH_ISC` was removed on 2026-08-25** — `probe1` cell 4 measured that `Status.IsC` does not isolate on this core and that its byte stores reach DRAM, so the knob stopped being a knob rather than gaining a danger note. What replaced it is `ISC`, which is set per payload in the `Makefile` with `override` and is 1 only for `probe1`, whose cell 4 IS that measurement.

🔴 **Three more knobs exist only because qemu has no MIPS-I core**, and every one
of them produces an image that looks right and is wrong for the device:
`UART_THR`/`UART_LSR` (qemu's 16550 is at `0xB80003F8`, one-byte spacing, where
this part's is at `0xB8002000` with four), `VEC_GENERAL` (qemu's Malta is a 24Kf,
a MIPS32 part, so its general exception vector is `0x80000180` where this core's
is `0x80000080`), and `CLEAR_BEV`/`RET_ERET`. `make show` prints
`*** NOT A DEVICE BUILD ***` when any of them is off its default, and
`tools/test-rlxprobe.sh` carries a pair of cases guarding that warning itself.
`qemu-run.sh` is the only caller that sets them.

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
| `Config` | `Config.M == 0` proves this is not a MIPS32 core outright, and says whether `Config1` — cache geometry, FPU, MMU — exists at all (`CPU-25`). ✅ **Answered 2026-08-25b: `Config` reads `00000000` and `nowrite = 0` proves the destination WAS written, so `Config.M = 0` and there is no `Config1`. `CPU-25` cannot come out of CP0 on this part** |
| `Status` | `CPU-27` — is `BEV` 0 at the prompt? `R1d` installs a handler at **`0x80000080`**, and that address is only right if it is. 🔴 **`0x80000080`, not `0x80000180`** — this is an R3000-class CP0, `0x80000000` is the UTLB refill vector and `0x80000080` is the general one. Corrected 2026-08-25; `notes/cache-model.md` carries the three sources |
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

`probe0.bin` is linked at `0x80500000` with its entry at byte 0; `make show`
prints the size and sha256 that go in the capture's metadata.

> ⚠️ **`0x80500000` is where the loader stages the `cr6c` payload** (`C-16`,
> `RUNSHEET.md` `B4`/`G1`). Loading `probe0` there overwrites the staged vendor
> kernel, which costs nothing — zero flash bytes — but it destroys `G1`/`G6`'s
> reference copy. **Run `probe0` after `B3`, or build it with
> `LOADADDR=0x81000000`**, which is `§C`'s scratch region and clear of both.

The address is the one `P9-12` proved on this device, and keeping it means the
first `rlxprobe` payload differs from that one in what it does and not in where
it lands.


## The payloads

| | what it decides | state |
|---|---|---|
| **`probe0`** | the chain: the toolchain emits code this core runs, the entry is byte 0, `LOADADDR`/TFTP/`J` delivers, the UART talks, the board comes back. Plus `PRId`, `Config`, `Config1`, `Status`, `Cause` | written, gated, runs to its end marker under qemu. **Not yet run on the device** |
| **`probe1`** | `R1d`. Six cells that decide **which cache-management sequence makes this core see an instruction just written into RAM** — no flush, `CCTL 0x002` alone, the vendor's `0x200`-then-`0x002`, the `Status.IsC`/`SwC` path `c-r3k.c` uses, an uncached store, and the recipe `notes/cache-model.md` recommends. Plus `CPU-25`'s geometry behind `GEOM=1` | ✅ **RAN 2026-08-25 and `R1d` closed with it.** Six cells, both victims each, `bench/2026-08-25/H1b.log`. The negative control held — cell 1 came back STALE, the **opposite** of qemu. `CCTL 0x002` alone is sufficient, a cached store to a line the D-cache does not hold reaches memory unaided (🔄 **narrowed 2026-08-26 from *"the D-cache is write-through"*** — both cells store to a line the cache does not hold, so that reading and *write-back without write-allocate* are indistinguishable), and cell 4 measured `Status.IsC` **failing to isolate**: its byte stores reached DRAM. 🔄 The source moved on 2026-08-25 (`rlx_call0_primed`, `SAFE_A0` in `uart.S`), so **the binary that ran is the tree at commit `2db12bb`**, sha256 `fbac7d60…`, and that rebuild is checked |
| **`probe2`** | `R1e`. A handler of our own at `0x80000080` **and** `0x80000000`, **read back through KSEG1 before anything dares fault**, a `break` positive control, then all 32 CP0 registers across all 8 select values **read TWICE with two different primes**, then `Count`/`Compare`. Restores both vectors and checks the restore in both directions | 🔄 **rewritten 2026-08-25 against `docs/rlxprobe-audit-2026-08-25.md` § Must-fix.** Written, gated, its 512-read census runs under qemu, and four mutations — one per must-fix — build deliberately broken payloads and require the checks to fire. One binary, 9,392 bytes. ✅ **RAN 2026-08-25b and `R1e` closed with it.** `bench/2026-08-25b/H2a.log` and `H2g.log`, two channels agreeing on all 40 header words, on the seal and on every spot-checked census row. `BEV = 0`, `PRId = 0000CD01`, `Count` not implemented, the select field ignored, `nowrite = 0` on all 256 rows, both vectors restored. 🔴 **The block command is `DW <base> 817`, not `809`** — `RB_POISON_W` is `RB_WORDS + 8`, and `LDR-07` rounds `809` up to 812 printed words, which shows only three of the eight margin words and nothing past the poison loop's own end |

`RUNSHEET.md` § Session B4 is the sheet that runs `probe1` and `probe2`, with
every expected value and refutation condition written before power is applied.

## What a qemu pass means, and it is less than it looks

qemu interlocks the load delay slot. This core does not — that is `F46`, it is
measured, and it is why `hazlint` exists. So a payload that produces the right
value under qemu has shown its **control flow** is right and **nothing** about
the silicon.

For `probe1` the gap is sharper and it is worth stating before anyone reads a
qemu run as a result: TCG invalidates a translation block when a store lands on
code it has already translated, so **qemu behaves like a machine with a coherent
I-cache**. Cells 1 and 5 — the two with no treatment at all — come back FRESH
under qemu, which is exactly the answer that would make the whole experiment
vacuous on the device. **A device run that looks like the qemu run is the run
that refutes the experiment, not the one that confirms it.**

That is not a defect in qemu, and it is the reason a qemu run is still worth its
minute: it is where `probe1`'s cell 4 was caught **destroying its own victim**.
`rlx_isc_inv` byte-stores zeros, which writes cache tags only if `Status.IsC`
isolates; on qemu's 24Kf it does not, so `03e00008` (`jr ra`) became `00e00008`
(`jr $7`) and the payload jumped into the weeds with no guest exception logged.
This unit's own bootcode never uses `IsC` either, so it was exactly as
unestablished on the device. There is now a guard, and `V_CORRUPT` is a
first-class verdict meaning *the treatment wrote memory where it was supposed to
write cache tags*.
