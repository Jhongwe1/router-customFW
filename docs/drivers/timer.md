# `rtl819x-timer` — Timer/Counter 1 as the system tick

Source: [`rtl819x-timer.c`](../../kernel/linux-2.6.30/drivers/clocksource/rtl819x-timer.c), version 4.1 ·
reasoning and every reading: [`notes/timer-driver.md`](../../notes/timer-driver.md) ·
the decision: [ADR-007](../decisions/ADR-007-timer-one-role.md) ·
the file head until 2026-10-18, verbatim: [`rtl819x-timer.c`](timer-history.md)

## What it does

TC1 is a clockevent device or a clocksource, never both: its one reload register cannot
hold a power-of-two period and a 2,000-count tick at once (`CLK-25`). At boot the driver
arms itself as a clockevent at rating 300; the tick core hands the system tick over from
the vendor's TC0 device, rating 100, and TC0 keeps interrupting at 100 Hz with its handler
set to a no-op (notes § 12.3, § 14). Its clocksource registers at rating 0, below
`jiffies`, so the kernel never switches to it (`CLK-21`).

`/proc/rtl819x-timer` prints the registers and the driver's counters and takes verbs —
`mode`, `arm`, `armirq`, `ackip`, `cevt`, `disarm` and others. `disarm` refuses with
`-EBUSY` once a device is registered, because 2.6.30's tick core has no unregister
(notes § 12.8).

## Registers

Through KSEG1 at `0xB8003000`. Each row cites its `SPEC.md` row and that row's two
marks: where the value came from (V) and where the name came from (N); D is the draft
datasheet.

| register | address | what the driver does | row · V · N |
|---|---|---|---|
| `TC1DATA` | `0xB8003104` | writes the reload: `0x00007D00`, 2,000 counts, in clockevent mode — byte for byte `TC0DATA` under Linux; a power of two in clocksource mode | `REG-06` · 量 · 讀 + 量 (D Table 21) |
| `TC1CNT` | `0xB800310C` | reads, as the clocksource's counter | `REG-08` · 量 · 讀 |
| `TCCNR` | `0xB8003110` | ORs `TC1EN` (bit 29) and `TC1MODE` (bit 28) into the word it read, and reads it back; TC0's bits stay as found | `REG-09` · 量 · 讀 (D Table 24) |
| `TCIR` | `0xB8003114` | sets `TC1IE` (bit 30); acknowledges `TC1IP` (bit 28, write-1-to-clear) by writing the two enable bits back with it | `REG-10` · 量 · 讀 (D Table 25) |
| `TC0DATA`, `CDBR` | `0xB8003100`, `0xB8003118` | reads, to derive the rate. Under Linux they hold 2,000 ≪ 4 and divisor 1000, not the loader's values | `REG-05` · 量 · 量; `REG-11` · 量 · 讀 |
| `GIMR`, `GISR`, `IRR0`–`IRR3` | `0xB8003000`–`0xB8003014` | reads and prints; never writes `GIMR` | `REG-01`, `REG-02`, `REG-32`, `REG-03`, `REG-04`, `REG-33` |

TC1's interrupt is Linux IRQ 25: `TCIR` bit 30, then bit 9 of `GISR` and `GIMR`, then
`IRR1`, then the CPU's `IP2` (`IRQ-06`).

## What holds on the silicon

- 量 TC1 and the vendor's TC0 count from one divider: ΔTC1 / ΔTC0_total = 1, residual
  exactly zero, over three intervals (`CLK-23`, seating 11).
- 量 the first interrupt delivery: 119,818 deliveries, none spurious, none stuck
  (`IRQ-08`, seating 12).
- 量 after the handover the two interrupt lines advance at different rates and `jiffies`
  follows TC1's, with zero lost ticks (`IRQ-12`, seating 13).
- 量 the system tick is the driver's before userspace exists, on ten boots without an
  oops (`CLK-27`, seating 14).

## Known limits

From notes § 14.5 unless marked.

- In clockevent mode the system's time source is still `jiffies`; only the tick is this
  driver's.
- `set_next_event` is a stub, and this build has no oneshot tick at all.
- The longest window measured is 654.76 s, so a handover that fails after an hour is not
  excluded; the ten counted boots were warm resets.
- The negative control is a device at rating 99, so the `>=` boundary at 100 is untested.
- Whether IRQ 13, the vendor's tick, and IRQ 25 are one source divided twice is open:
  they agree to 8 ppm, which shows only that both are 100 Hz (`FW-190` 殘留).

## Where else

- [`docs/driver-diff.md`](../driver-diff.md) § 3.4 — its decisions beside the two public
  ports'.
- [`docs/interrupt-map.md`](../interrupt-map.md) — the layers a timer interrupt crosses.
- [`docs/blind-write-ledger.md`](../blind-write-ledger.md) § 4.3 — what was read of other
  implementations before it was written.
