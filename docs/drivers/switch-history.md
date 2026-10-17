# `rtl819x-switch.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/net/rtl819x-switch.c`](../../kernel/linux-2.6.30/drivers/net/rtl819x-switch.c)
until 2026-10-18 — lines 1–102 at commit `9ec29f8c` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [switch](switch.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-switch.c` counts the file's lines at `9ec29f8c`.

```c
/*
 * rtl819x-switch.c -- rlxfw's switch-core driver for the RTL8196E.
 *
 * R6-2: "the switch to a dumb state from my code -- all ports one VLAN, no
 * acceleration", whose DoD is *a register read-back whose value differs from
 * RESET*, and whose named failure mode is *that a dumb switch looks identical
 * to a switch nobody configured*.
 *
 * ======================================================================
 * WHY THIS DRIVER EXISTS IN THIS SHAPE, WHICH IS A MEASUREMENT PROBLEM
 * BEFORE IT IS A CONFIGURATION PROBLEM
 * ======================================================================
 *
 * 🔴 `bench/2026-09-17b/PREDICTIONS-B25-block24.md:96` recorded, before this
 * driver existed, that the DoD is *"not satisfiable today: none of the eight
 * has a known reset value"*.  That sentence was true of the method available
 * on 2026-09-17 morning and it is not true of this part.
 *
 * 讀 `rtl865xc_asicregs.h:1399-1446`: `SSIR` (alias `SIRR`) at
 * `SWMISC_BASE + 0x04` = `0xBB804204` carries `SwitchFullRst = (1<<2)`,
 * commented *"Reset all tables & queues"*, and `TRXRDY = (1<<0)`,
 * *"Start normal TX and RX"*.  讀 `rtl865x_asicCom.c:2002-2040`: the vendor's
 * own bring-up asserts it.  So the reset state is not a documentary gap --
 * it is a state this driver can ENTER and then read, on this die.
 *
 * That turns `D2` from a substitution into a measurement, and it makes the
 * proof four-cornered rather than two:
 *
 *   S0   the loader's state          -- 量 already, bench/2026-09-17b block 24
 *   S0'  after early kernel init,    -- latched by this driver at
 *        before the vendor NIC          subsys_initcall.  NOBODY HAS EVER
 *        driver runs                    MEASURED THIS STATE.
 *   S1   after FULL_RST              -- `reset` verb.  The reset baseline.
 *   S3   this driver's dumb config   -- `dumb` verb.
 *
 * `D2` is then **S3 != S1**, register by register, with:
 *
 *   - a POSITIVE control on the reset: at least one register must satisfy
 *     S1 != S0'.  If `FULL_RST` moves nothing, the write did nothing and the
 *     whole block is void.  That is the refutation condition, written here
 *     before the verb was run once.
 *   - a NEGATIVE control on the writes: a register this driver never writes
 *     must satisfy S3 == S1.  If everything moves, something other than this
 *     driver is moving it.
 *   - a ROUND TRIP: restore S0' and read again.  If a register does not come
 *     back, it is not a plain read/write cell and a read-back is not the
 *     proof `D2` assumes it is.  This part has one such register already --
 *     `WDTCLR` does not read back (`SPEC.md` `FW-52`) -- so this is a
 *     measured hazard and not a hypothetical one.
 *
 * ⚠️ THE LIMIT, STATED HERE RATHER THAN LEFT TO BE FOUND.  `FULL_RST` is a
 * SOFT reset of "tables & queues".  It is NOT proven identical to a power-on
 * reset.  What this driver can support is *differs from the state this part's
 * own documented full reset leaves it in* -- strictly stronger than "differs
 * from loader-state", strictly weaker than "differs from the power-on
 * default".  The gap is named, not hidden.
 *
 * 🟢 And there is an independent check available on exactly one register.
 * The draft datasheet's Table 64 gives per-bit defaults for `PCRP0`-`PCRP4`
 * which assemble to `0x007F....`, and this unit reads `PCRP0 = 0x007F0039`.
 * So after `FULL_RST`, `PCRP0`'s top half is PREDICTED to be `0x007F`.  If it
 * is, the "full reset as a reset baseline" method is validated against a
 * documentary source on the one register that has one.  If it is not, the
 * method is refuted -- which is also a result, and is why the prediction is
 * written down here.
 *
 * ======================================================================
 * WHY `MSCR` AND `VCR0` ARE IN THE TABLE THOUGH NOTHING HAS EVER READ THEM
 * ======================================================================
 *
 * 🔴🔴 `SPEC.md` `NET-21` derives this project's switch-register population
 * from 48 `lui ...,0xbb80` sites in the LOADER, converging on 13 addresses.
 * That is *what one agent touched*.  It is not *what configures the switch*.
 * 量 2026-09-17 (`tools/hdrcensus.py`): of the 21 addresses the vendor header
 * declares in the ALE block, NINETEEN have never been printed by this
 * repository -- and `MSCR`, the switch's operation-layer mode register, is
 * one of them.  `VCR0`, which holds the 802.1Q-unaware bit, is another.
 *
 * A census whose population is one agent's behaviour is blind to everything
 * that agent ignores.  Both registers are the direct object of R6-2's own
 * one-line definition, and neither was in the census that was supposed to
 * load it.
 *
 * ======================================================================
 * WHAT THIS DRIVER DOES NOT DO
 * ======================================================================
 *
 * 1. It does not touch the CPU-port DMA rings, the interrupt, or any
 *    `net_device`.  That is R6-3 and it is a different driver.
 * 2. It writes NOTHING at boot.  Every write is behind a verb AND behind an
 *    explicit runtime unlock, so a boot of this image is read-only by
 *    construction and `n_writes` reads 0 on a capture that proves it.
 * 3. It writes a table in one verb only: 1.6's `vlan` (R6c, at the end of
 *    this file) writes the VLAN and netif tables through the TACI block
 *    (`SWTACR`/`SWTAA`/`TCR0`-`TCR7`), a protocol and not a register write.
 *    `dumb` leaves every table alone: 推 that `En1QtagVIDignore` makes the
 *    table irrelevant for a dumb switch, and that 推 is still untested.
 * 4. It says nothing about whether the silicon agrees with the header.  This
 *    project has one measured counter-example already: the header names
 *    `PCRP5` at `0xBB804118` and the die reads `00000000` where every
 *    neighbour reads `xx7F00xx`.
 */
```
