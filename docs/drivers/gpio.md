# `rtl819x-gpio` — a gpiolib chip on the PABCD port

Source: [`rtl819x-gpio.c`](../../kernel/linux-2.6.30/drivers/gpio/rtl819x-gpio.c), version 1.1 ·
reasoning and every reading: [`notes/gpio-driver.md`](../../notes/gpio-driver.md)

## What it does

It registers a `gpio_chip`, `rtl819x-pabcd`, of 32 lines numbered by bit position,
because which of PABCD's four ports a bit belongs to has never been measured
(`GPIO-1`, declined). `.request` refuses every line except two that this project has watched on
this board: bit 5, the button, an input, active low (`BRD-05`); and bit 6, which drives
the second of the board's eight LEDs, active low (`BRD-13`). Only bit 6 may be an
output, and an unmodified upstream `leds-gpio` binds to it as `n150rt:green:led2`. Bit
5 stays refused as an output: it has a pull-up and a button to ground, so driving it
high while the button is held shorts the pad driver through the switch.

2.6.30's `gpio_chip.set` returns `void`, so the guard lives in `.request` and
`.direction_output`, and `.set` counts what it refuses. `/proc/rtl819x-gpio` prints the
block's registers, the driver's counters and a contention detector on bit 6.

## Registers

Through KSEG1 at `0xB8003500` (`MAP-09`: 文 · 量 for the block, 讀 for the names).
The values in `REG-26` and `REG-27` are the loader's. Under Linux the vendor's own
`rtl_gpio_init` rewrites both before this driver runs, and the live `CNR` reads
`FFFFFF8B` (`REG-35`; notes § 3.1).

| register | address | what the driver does | row · V · N |
|---|---|---|---|
| `PABCD_CNR` | `0xB8003500` | reads and compares; never writes | `REG-26` · 量 · 讀 |
| *(no name)* | `0xB8003504` | reads once, on the `probe04` verb: `0x00000000` | `REG-36` · 量 · — |
| `PABCD_DIR` | `0xB8003508` | sets bit 6 to an output, in `.direction_output` | `REG-27` · 量 · 讀 |
| `PABCD_DAT` | `0xB800350C` | reads bit 5; writes bit 6 | `REG-28` · 量 · 讀 |

## What holds on the silicon

- 量 the button is bit 5 and active low: `PABCD_DAT` reads `0000003C` released and
  `0000001C` held (`BRD-05`, `REG-28`).
- 量 bit 6 lights LED 2 of eight, active low, both levels seen with the other seven as
  the negative control (`BRD-13`, seating 19).
- 量 upstream `leds-gpio`, bound to this chip, lit LED 2 from a sysfs write; with the
  mask narrowed at run time the refusal came before the write, so the write counter did
  not move, and with it widened again the light went out (notes § 13.1, § 13.2,
  seating 20).
- 量 the vendor's `rtl_gpio_timer`, the other writer of bit 6, acts once per boot,
  started by the first hold over about 2 s (`FW-62`).

## Known limits

From notes § 11 and the source's own list unless marked.

- Which port letter bits 5 and 6 belong to (`GPIO-1`).
- Thirty of the thirty-two lines are refused, because nothing has shown them to be GPIOs.
- No interrupt: `.to_irq` is `NULL`. `arch/rlx` declares `gpio_to_irq()` outside the
  `CONFIG_GPIOLIB` guard and defines it nowhere, so turning `CONFIG_DEBUG_FS` on breaks
  the link.
- Nothing arbitrates between this driver and the vendor's on bit 6; the detector
  counts what it sees, and cannot time it (notes § 6, § 13.5). In the image `R5` ran,
  the vendor's `/proc/gpio` is also a path from userspace that writes `PABCD_CNR`,
  `DIR` and `DAT` (讀, `FW-65`).
- Seven functions in the image form `PABCD_DAT`'s address and have not been read
  (notes § 5). `0xB8003504` has a value and no name.

## Where else

- [`docs/drivers/keys.md`](keys.md) — the button, read through this chip.
- [`docs/driver-diff.md`](../driver-diff.md) — beside the two public ports.
- [`docs/blind-write-ledger.md`](../blind-write-ledger.md) § 4.9 — the one artefact
  reading of the vendor's GPIO code, which took this driver out of the blind section.
