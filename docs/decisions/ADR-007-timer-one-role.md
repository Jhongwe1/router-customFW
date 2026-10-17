# ADR-007: The timer driver is a clocksource or a clockevent device, not both

## Context
CP0's `Count` reads 0 and does not move on this core (量, `CPU-42`), so a clocksource has to come out of the SoC timer block. Its two timers are the same block twice. TC0 is the vendor kernel's tick, and its ISR read-modify-writes `TCIR`, whose pending bits are write-1-to-clear, a hundred times a second (量, `IRQ-09`); its period under Linux, 2,000 counts, is not a power of two (量, `REG-05`). `rtl819x-timer` runs beside that kernel, so it has TC1, which has one reload register (`notes/timer-driver.md` § 1).
## Decision
TC1 is either a clocksource or a clockevent device, chosen with `mode cs` or `mode ce`; `arm()` writes a different `TC1DATA` under each. The recorded reason is arithmetic: a clocksource needs a power-of-two period, because the core computes `(now - last) & mask`, and a 100 Hz clockevent needs 2,000 counts — "`2,000 = 2^4 × 125`. No power of two at or above this driver's floor of `2^8` divides it, so the two requirements have no common solution." (`notes/timer-driver.md` § 12.1). Since version 4.1 the driver arms itself at boot as a clockevent at rating 300, strictly above the vendor's 100.
## Alternatives considered
- **A software-extended clocksource beside the tick**: the ISR adds a period to a 64-bit accumulator, and its one race needs a wrap-pending test. Refuted on this part: because of `IRQ-09`, a pending bit lives at most one 10 ms tick, and a clocksource that is right most of the time hands the core a backwards step (`notes/timer-driver.md` § 12.2).
- **One timer per role, as both public ports do** (`shibajee`: TC0 clocksource, TC1 clockevent; `ggbruno` the reverse): they replace the vendor's tick; rlxfw coexists with it, "so TC1 is not a choice: it is the only timer available" (`docs/driver-diff.md` § 3.4.1).
- **TC0 extended in software**, by a wrap correction or by `jiffies` × period + count: the first is correct only if the counter is read more often than once per wrap, which nothing in this kernel guarantees; the second is circular for the measurement `R5-2` exists to take (`notes/timer-driver.md` § 1).
## Consequences
- In clockevent mode there is no clocksource of the driver's: the system's time source stays `jiffies`, and only the tick is the driver's; its clocksource registers at rating 0, below `jiffies`, so the kernel never switches to it (`notes/timer-driver.md` § 14.5; `docs/driver-diff.md` § 3.4.1).
- The handover is one-way inside a boot: the 2.6.30 tick core has no unregister, so `disarm` returns `-EBUSY` once a device is registered, and a wedge needs a power cycle (`notes/timer-driver.md` § 12.8).
- After the handover the vendor's TC0 still interrupts at 100 Hz, still pets the watchdog, and no longer advances `jiffies` (讀, § 12.3). 量 seating 13: the tick is the driver's, shown causally, with zero lost ticks (§ 13).
## Evidence
[`notes/timer-driver.md`](../../notes/timer-driver.md) § 1, § 12, § 13 and § 14; [`docs/driver-diff.md`](../driver-diff.md) § 3.4; [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 8 (`R5`); [`SPEC.md`](../../SPEC.md) `CPU-42`, `IRQ-09`, `REG-05`. Decided 2026-09-06, in `R5-3b-1` (version 3.0); armed at boot 2026-09-06, version 4.1.
## Status
In force: the driver in the tree is version 4.1.
