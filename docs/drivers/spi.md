# `rtl819x-spi` — the SPI flash, read by programmed I/O

Source: [`rtl819x-spi.c`](../../kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c), version 1.2,
with [`rtl819x-spi-write.c`](../../kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-write.c),
[`rtl819x-spi-wrpolicy.h`](../../kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h) and
[`rtl819x-spi-install.h`](../../kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h) ·
reasoning and every reading: [`notes/spi-mtd-driver.md`](../../notes/spi-mtd-driver.md) ·
the flash rule: [ADR-006](../decisions/ADR-006-flash-write-rule.md) ·
the file heads until 2026-10-18, verbatim: [`rtl819x-spi-write.c`](spi-write-history.md)

## What it does

It registers a read-only MTD device, `rtl819x-spi-pio`, that reads the 4 MiB SPI NOR
through the controller's command and data registers, as the vendor's MTD path does
(notes § 1). It coexists with the vendor's flash driver, which is still in the image
and holds no lock: every transaction saves `SFCR`, `SFCR2` and `SFCSR`, restores them
and reads them back, and two counters record a transaction that began from a state
not its own, with a `wedge` verb as their positive control (notes § 4).
`/proc/rtl819x-spi` takes `verify` and `map`, which digest the flash through this path
and through the memory-mapped window and compare the two; both skip `H601`
(`0x006000`–`0x007FFF`) by rule.

Writing is refused three ways in every committed image: the write path is a separate
translation unit that is not compiled (`CONFIG_MTD_RTL819X_WRITE=n`), `mtd->write` and
`mtd->erase` are stubs that return `-EOPNOTSUPP`, and `mtd->flags` is `MTD_CAP_ROM`
(notes § 5, § 12). Only an armed image, RAM-booted through the loader for `R8b`, built
the slot install path, which takes region names compiled in, never an address.

## Registers

`SPEC.md` row, value mark (V) and name mark (N). The values in `REG-13` were read at
the loader prompt; Linux reprograms the controller (`REG-38`).

| register | address | what the driver does | row · V · N |
|---|---|---|---|
| `SFCR`, `SFCR2`, `SFCSR`, `SFDR` | `0xB8001200`–`0xB800120C` | `SFCSR` frames each command and `SFDR` carries it and its data; `SFCR`, `SFCR2` and `SFCSR` are saved and restored, and `SFDR` never is, because writing it issues an SPI command | `REG-13` · 量 ×2 · 讀 |
| `SPI_RDY` | `0xB8001208` bit 27 | polled with a bound: a controller that never raises it gives `-ETIMEDOUT` and a count, where the vendor's spin has no bound | `REG-14` · — · 讀+ |
| the window | `0xBD000000` | read, as the second path the digests compare against | `MAP-12` · 量 · 讀 |

量 under Linux, seating 16: `SFCR` `FFC00000` (clock divisor 16, the loader's is 4),
`SFCR2` `0BA08000`, `SFCSR` `C8000000` (notes § 3.1). The chip's JEDEC ID is
`0x1C7016` (`FLS-04`).

## What holds on the silicon

- 量 the two read paths agree: `PIO==MMIO` on all 32 units, over every hashed byte —
  4,186,112, all but `H601` (`FLS-26`).
- 量 eleven flash maps over six seatings and nine days, every unit digest the same
  (`FLS-27`).
- 量 `R8b`, armed image only: one `SE` erases 4,096 bytes, bounded from both sides
  (`FW-244`); a 64 KiB block installs in 0.48–0.51 s and a slot in 10.26–11.24 s
  (`FW-246`).

## Known limits

- The vendor's flash-write path is in the image: `mtd_spi_write` and `mtd_spi_erase`
  are installed unconditionally, and what keeps them unreached is the userspace
  surface ([known issue 08](../known-issues/08-a-flash-write-path-not-mine.md), `FW-44`).
- `n_writes` reads 0 in every committed version because none increments it, so a 0
  carries no information about writes (`FW-142`).
- An unaligned read is refused with `-EINVAL` rather than served by an untested
  partial-word path (notes § 8).
- The map shows that the flash matches the 2026-08-16 dump except in two 4 KiB units,
  `0x9000` and `0xD000`, whose cause is undetermined (`FLS-26`); a digest cannot see
  two writes that cancel.

## Where else

- [`notes/flash-digest-scope.md`](../../notes/flash-digest-scope.md) — what the digests
  cover.
- [`docs/blind-write-ledger.md`](../blind-write-ledger.md) § 4.5 — the vendor's MTD map
  was read, so this driver's diff is not a blind one.
