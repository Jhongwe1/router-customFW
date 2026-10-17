# `rtl819x-switch` — the switch core

Source: [`rtl819x-switch.c`](../../kernel/linux-2.6.30/drivers/net/rtl819x-switch.c), version 1.6,
with the read-only [`rtl819x-view.c`](../../kernel/linux-2.6.30/drivers/net/rtl819x-view.c) ·
reasoning and every reading: [`notes/switch-driver.md`](../../notes/switch-driver.md) ·
the file heads until 2026-10-18, verbatim: [`rtl819x-switch.c`](switch-history.md),
[`rtl819x-view.c`](view-history.md)

## What it does

It drives the switch core at `0xBB800000`. Nothing is written at boot by the driver
itself: every write sits behind a `/proc/rtl819x-switch` verb and a runtime unlock, so
`n_writes` on a boot capture is a reading. The standard `/init` types, in order,
`unlock i-mean-it`, `init`, `vlan` and `start` ([`notes/init.md`](../../notes/init.md)
§ 2), and only then does `rtl819x-nic` open `rlx0`.

- `init` (1.5) sets the five bits of the take-over that `R6b` measured
  ([`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 14); `reset` is refused while the
  CPU port's DMA engine runs (`NET-168`).
- `vlan` (1.6, `R6c`) writes the loader's single-VLAN layout: the VLAN and netif tables,
  through the table-access protocol, then `PVCR0`–`PVCR3` and `FFCR`, each only where
  it differs; `PVCR4`, `VCR0`, `PBVCR0` and `PLITIMR` are checked and never written, and
  a mismatch writes nothing (`NET-173`). The stock loader configures that group only on
  its prompt path, so a board booted from flash lacked it (`NET-171`).
- `start` sets `TRXRDY` in `SIRR`, which is necessary (`NET-52`).
- `phyif` (1.4) sets `EnablePHYIf`; the driver also registers an `mii_bus` for reading
  the five PHYs at MDIO addresses 0–4 (`NET-39`).

`/proc/rtl819x-view` prints registers, MIB counters and tables, and only reads.

## Registers

`SPEC.md` row, value mark (V) and name mark (N). The names come from the vendor's
header, and the draft datasheet's tables where it has them.

| register | address | what the driver does | row · V · N |
|---|---|---|---|
| `SIRR` | `0xBB804204` | `FULL_RST` (bit 2) on `reset`, `TRXRDY` (bit 0) on `start` | `NET-36` · 讀 · 讀; `NET-52` · 量 · 讀 |
| `PCRP0`–`PCRP4` | `0xBB804104`–`0xBB804114` | per-port control; `EnablePHYIf` (bit 0) on `phyif` | `REG-16` · 量 · 讀 |
| `PSRP0`–`PSRP4` | `0xBB804128`–`0xBB804138` | per-port status, read | `REG-17` · 量 · 讀 |
| `MSCR`, `SWTCR0`, `SWTCR1`, `VCR0`, `PVCR0`–`PVCR4` | `0xBB804410`–`0xBB804A18` | written by `dumb` (nine writes) and read in the four states the proof compares — the loader's, early kernel, after `FULL_RST`, after `dumb` | `NET-43`, `NET-44` · 量 · 讀 |
| `MDCIOCR`, `MDCIOSR` | `0xBB804004`, `0xBB804008` | MDIO commands and status, for the `mii_bus` | `NET-15` · 讀 · 讀 |

The VLAN layout `vlan` writes is slot 8, `00807E3F`: ports 0–5 members and untagged
(`NET-173`, `NET-174`).

## What holds on the silicon

- 量 `D2`: the dumb configuration differs from the state `FULL_RST` leaves, on two
  registers, because `FULL_RST` already leaves most of a dumb switch (`NET-44`).
- 量 `TRXRDY` is necessary: a one-variable A/B (`NET-52`).
- 量 with the standard `/init` typing `init`, `rlx0` pings both ways after a cold
  power-on and after `busybox reboot -f`, on an image with no vendor Ethernet code
  (`NET-167`).
- 量 booted from a flash slot, before `vlan` existed, every frame from the host died in
  the switch (`NET-172`); with it, `rlx0` pings both ways after a watchdog reset and after
  a cold power-on ([`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 22).

## Known limits

- rlxfw has no WAN: the layout puts ports 0–5 in one VLAN, and port 0 is the jack
  labelled WAN (`NET-174`).
- `vlan`'s write set is shown sufficient as a unit; which of its writes is necessary is
  not established, with no on/off control on one boot (entry 22).
- `R6b`'s pass rested on switch state the loader wrote (entry 14); `vlan` has since
  taken over the VLAN group, and EEE, the CPU queue count, the PHY patch and `LEDCREG`
  stay as the boot leaves them ([`docs/known-issues/v1.0.md`](../known-issues/v1.0.md)).
  How a frame for `rlx0` reaches the CPU is 推 on one source (`NET-169`).
- `FULL_RST` resets tables and queues; it is not shown equal to a power-on reset.
