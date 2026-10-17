# `rtl819x-keys` — the board's button, polled, as an input device

Source: [`rtl819x-keys.c`](../../kernel/linux-2.6.30/drivers/input/keyboard/rtl819x-keys.c), version 1.0 ·
reasoning and every reading: [`notes/gpio-driver.md`](../../notes/gpio-driver.md) § 10, § 12
and § 13 · the board's description of the button:
[`rlxfw-devices.c`](../../kernel/linux-2.6.30/arch/rlx/kernel/rlxfw-devices.c)

## What it does

It reports the button as a key through the input core, polling it with upstream's
`input_polled_dev` and reading it through `rtl819x-gpio`'s chip by gpiolib. The board
file describes the button in upstream's own `gpio_keys_platform_data`, so the
description is one an unmodified `gpio_keys` would accept.

`gpio_keys` itself cannot drive this board: it needs `gpio_to_irq()` at six sites, and
`arch/rlx` declared that function and defined it nowhere, so `CONFIG_KEYBOARD_GPIO=y`
failed at link. `config/host-compat/0006` aliases it to gpiolib's `__gpio_to_irq`,
which returns `-ENXIO` because `rtl819x-gpio` has no `.to_irq`: the failure moves from
link time to probe time, with the value produced by the data structure rather than
typed (`FW-56`; notes § 12.1). The polled variant upstream later added is not in this
drop (notes § 10).

Polling starts only when a handler opens the device. The image carries `evdev` and
`/dev/input/event0`; `evbug`, which opens every device at registration, was rejected
because it would make the polling unconditional. `/proc/rtl819x-keys` prints the open
and poll counters, the debouncer's state and a ring of raw edges stamped in jiffies.
A non-zero `wakeup` in the board file is refused at probe, not ignored.

## Registers

None of its own. It reads `PABCD_DAT` bit 5 through gpiolib; the register and its
sources are on [the gpio page](gpio.md), and the button's polarity is `BRD-05` (量,
active low). The driver writes nothing.

## What holds on the silicon

From notes § 13.3 and § 13.6, seating 20, 2026-09-10.

- 量 the polling is caused by the open: the three-state control reads (0, 0) → (1, 60)
  → (2, 120) → (2, 120) — sixty polls per three-second open at 50 ms, twice, and flat
  across a sleep that carries no open.
- 量 at 10, 50 and 200 ms the span from first to last poll is exactly (polls − 1) ×
  the period, with no remainder at any of the three.
- 量 at 200 ms the ring held six edges for three presses with two counted: the 0.20 s
  press, one poll period, was seen and refused by the debouncer rather than lost.
- 量 the driver's own `gpio_to_irq()` call reads `-ENXIO` (`RLXFW-K4 = FFFFFFFA`).

## Known limits

From the source's own list and notes § 13.6.

- No GPIO interrupt exists on this arch, so the button is polled.
- Which port of PABCD the button is on is unknown (`GPIO-1`, declined).
- A press reaching userspace is not established: `n_report` counts
  `input_report_key()` calls and is an upper bound, and nothing in the image decodes
  `/dev/input/event0`.
- The vendor's reset path is not out of the way: its `rtl_gpio_timer` polls the same
  button once a second (`FW-40`), and both drivers read the pin with no arbitration.
- Bounce: `b0_n_bounce` read 0 on every carded rung, which means bounce is below 10 ms
  or falls between polls, not that the button does not bounce.

## Where else

- [`docs/drivers/gpio.md`](gpio.md) — the chip this driver reads through.
- [`docs/blind-write-ledger.md`](../blind-write-ledger.md) § 4.1 — this driver is one of
  the two still in the blind section.
