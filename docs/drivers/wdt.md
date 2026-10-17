# `rtl819x-wdt` — a `/dev/watchdog` on `WDTCNR`

Source: [`rtl819x-wdt.c`](../../kernel/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c), version 1.1 ·
reasoning and every reading: [`notes/watchdog-driver.md`](../../notes/watchdog-driver.md) ·
the file head until 2026-10-18, verbatim: [`rtl819x-wdt.c`](wdt-history.md)

## What it does

The vendor kernel arms the watchdog at `OVSEL` 3 and feeds it at 100 Hz from its tick,
and both halves sit under `CONFIG_RTL_WTDOG`. That symbol is `n` in every image that
carries this driver, so nothing else arms the dog (notes § 4). At `late_initcall` the
driver arms the hardware at `OVSEL` 9 and feeds it from a kernel timer every 250 ms
(state `BOOTGUARD`). Opening `/dev/watchdog` hands the feeding to userspace with a
60 s soft timeout in front of the hardware one (`WDT_USER`). `/proc/rtl819x-wdt`
prints the state, the register read at probe and the rate it derives, and takes verbs:
`bite`, `biteraw`, `kickms`, `ovsel` and others.

## Registers

`SPEC.md` row, value mark (V) and name mark (N).

| register | address | what the driver does | row · V · N |
|---|---|---|---|
| `WDTCNR` | `0xB800311C` | composes a whole word every time, never a read-modify-write: `WDTE` (bits 31:24) `0x00` to run and `0xA5` to stop, `WDTCLR` (bit 23) to kick, and the timeout in `OVSEL` | `REG-12` · 量 · 讀 |
| `OVSEL` in `WDTCNR` | bits 21, 22, 17, 18 | `OVSEL[0]`–`[3]`, a split field out of order; the driver encodes bits 21, 22 and 18 | `CLK-28` · 量＋讀 · 讀 |
| `TC0DATA`, `CDBR` | `0xB8003100`, `0xB8003118` | reads, to derive the counting rate under Linux: 200,000 Hz | `REG-05` · 量 · 量; `REG-11` · 量 · 讀 |

`WDTCNR` reads `0xA5000000` at power-on reset, a hardware default rather than a loader
write (`REG-12`). `OVSEL[2]` was placed at bit 17 by seating 18, after this version
was built (notes § 11.1).

## What holds on the silicon

- 量 the driver runs and bites, and `wdtcnr_at_probe` reads `A5000000`: with
  `CONFIG_RTL_WTDOG=n` nothing armed the register before it (`FW-52`, seating 17).
- 量 it is the only feeder: at `OVSEL` 0 with its own kicks slowed to 3 s the board
  reset, with the vendor's `wlan0` down and again after `ifconfig wlan0 up`
  (notes § 10.3).
- 量 bite times from `OVSEL` 0, 3, 8 and 9: 163.911, 1,340.982, 41,910.358 and
  84,001.412 ms (notes § 11.3, seating 18). A `bite` word carries `WDTCLR`; three
  bites at `OVSEL` 3 in seating 19 spread by 34.622 ms against their own ruler's
  1.867 ms, so the spread is the device's (`CLK-28`).
- 量 the user path: with `/dev/watchdog` held open and never written, the board reset
  143.563 s later, against 60 s plus `OVSEL` 9's 83.886 s derived (notes § 11.6).
- 量 `WDTCLR` does not read back on this die: the driver writes `0x00A40000` and
  reads `0x00240000` (notes § 10.1).

## Known limits

From notes § 7 and § 11 unless marked.

- Four of the ten `OVSEL` settings are refused: the driver lags the measurement that
  placed `OVSEL[2]`, and changing it is a behaviour change.
- `WDIOC_GETBOOTSTATUS` returns 0 always: `WDTIND` does not read back, so
  `WDIOF_CARDRESET` is not advertised.
- What the watchdog counts is open (`CLK-08b` 殘留). Under Linux it is near 200 kHz,
  not the loader's 14.965 MHz, and a linear model of the four rungs is undetermined:
  three of its residuals fall within `OVSEL` 3's own jitter (`CLK-28`).
- `RTL819X_WDT_HZ`, 14,965,000, and the µs table built from it are the loader's values,
  76× off under Linux, and are left so on purpose: `/proc` prints them beside the
  derived ones and cards predict against them (`CLAUDE.md` § At the bench).
- `biteraw` does not clear the counter, so a reading without a `kickms 5000` first
  carries an unknown deficit.
- Turning `CONFIG_RTL_WTDOG` off was predicted to leave two `WDTCNR` writers in the
  image; six remained, four of them in the vendor's WLAN driver (`FW-51`, notes § 4.4).
- It is a hand-rolled `miscdevice` on `WATCHDOG_MINOR`, not a `struct watchdog_device`
  ([`docs/bringup.md`](../bringup.md) § 3a).

## Where else

- [`docs/blind-write-ledger.md`](../blind-write-ledger.md) § 4.10 — the vendor's
  watchdog code was read in full, on purpose, so this driver's diff is informed
  contrast, not a blind one.
- `FW-37` — `busybox reboot -f` resets this board through a watchdog bite.
