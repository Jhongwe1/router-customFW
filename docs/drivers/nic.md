# `rtl819x-nic` — the switch core's CPU port, as `rlx0`

Source: [`rtl819x-nic.c`](../../kernel/linux-2.6.30/drivers/net/rtl819x-nic.c), version 1.6, with
[`rtl819x-nic-tx.h`](../../kernel/linux-2.6.30/drivers/net/rtl819x-nic-tx.h) ·
reasoning and every reading: [`notes/nic-driver.md`](../../notes/nic-driver.md) ·
against the vendor's driver, field by field: [`docs/nic-vendor-diff.md`](../nic-vendor-diff.md) ·
the file heads until 2026-10-18, verbatim: [`rtl819x-nic.c`](nic-history.md),
[`rlxfw-seam.c`](seam-history.md)

## What it does

It owns the CPU port's DMA engine: four TX descriptor rings, six RX packet-header rings
and one RX buffer ring, an interrupt on LOPI line 12, a NAPI poll, and a `net_device`
called `rlx0` (notes § 0). It ships inert: every hardware write sits behind a `/proc`
verb and a runtime unlock, and the standard `/init` writes `unlock` and `netdev on` at
boot, after the switch driver's verbs ([`notes/init.md`](../../notes/init.md) § 2).

Since `R6b-8` the mainline image carries no vendor Ethernet code
(`CONFIG_RTL_819X_SWCORE=n`, [known issue 19](../known-issues/19-no-vendor-ethernet-driver.md)).
The loader leaves this engine running, with rings in memory the kernel will reuse;
without the vendor's probe, [`rlxfw-seam.c`](../../kernel/linux-2.6.30/drivers/net/rlxfw-seam.c)
makes the vendor's two disarm writes from `bsp_setup()`, before any allocator exists.
Since 1.6 the TX descriptor lengths follow the vendor's convention by default — `m_len` =
`m_extsize` = `ph_len` — which is the fix for `rlx0`'s transmit loss (notes § 29).

## Registers

The CPU interface block at `0xB8010000` is the system block, not the switch core at
`0xBB800000`. Its names rest on one Realtek header copied into all three drops; the draft
datasheet has none of them, so every value here was read on the die (notes § 2).

| register | offset | what the driver does | row · V · N |
|---|---|---|---|
| `CPUICR` | `+0x000` | starts and stops TX and RX DMA; the loader leaves `C4000000` | `NET-48` · 量 · 讀 |
| `CPURPDCR0`, `CPURMDCR0` | `+0x004`, `+0x01C` | the RX ring bases, pointed at rings the driver allocates | `NET-48` · 量 · 讀 |
| `CPUTPDCR0`–`3` | `+0x020`, `+0x024`, `+0x060`, `+0x064` | the TX ring bases; not contiguous, so the header's indexed macro would land on `CPUIIMR` and `CPUIISR` | `NET-48` · 量 · 讀 |
| `CPUIIMR` | `+0x028` | the interrupt mask: `0x7FE`, the loader's `0x7F8` plus the ring-drained bits | `NET-48` · 量 · 讀 |
| `CPUIISR` | `+0x02C` | acknowledged by writing 1s; two reads in a row change nothing | `NET-48` · 量 · 讀 |

The control bits of `CPUICR` are `NET-38` (讀 · 讀); its `SOFTRST` clears itself and
`TXCMD`/`RXCMD` with it (`NET-100`). The descriptor layout was closed at the loader
prompt before any driver ran (`NET-49`).

## What holds on the silicon

- 量 `rlx0` pings both ways, and the driver's counters match the bytes (`NET-51`).
- 量 `R6`: 17.03, 17.76 and 17.09 Mbit/s of bulk TCP (n = 4, one collapse) with a
  recovery verb armed by hand (`NET-107`), and 31.66 minutes of flood with `drop 0/0`
  ([`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 12).
- 量 `R6b`: with the vendor's length convention, 220 of 220 exchanges answered on two
  boots where 1.4's answered 145 of 1,327 and 144 of 1,189, and a sweep over every
  length from 60 to 1,514 moved `JabberErr` by 0 (entry 14); 31 minutes and 2,363,511
  frames fired no recovery while 1.4 fired 12 times in two minutes (`NET-141`).
- 量 `R6c`: booted from a flash slot, `rlx0` pings both ways after a watchdog reset and
  after a cold power-on (entry 22; what made it work is the switch driver's `vlan`,
  [the switch page](switch.md)).

## Known limits

- Why the engine stopped reclaiming TX descriptors under 1.4's lengths is not
  established: the fix removes the bad lengths and the stalls together (`NET-67`
  殘留, `NET-78` 殘留, both declined).
- The register names have one source, a header copied three times; the values have
  the die.
- `CPUIISR` is shown stable across two reads at the values the die held, not free of
  read side effects at every value.
- Every reading of the release image is one unit and one boot per path
  ([`docs/known-issues/v1.0.md`](../known-issues/v1.0.md)).
