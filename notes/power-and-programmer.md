# The 1.70 V, and what would tell us why — S0b

**`DAY-ZERO` item 5. Part 1 was written at the desk on 2026-08-23, before the
board was touched. Part 2 is empty until the bench session.** That order is the
point: a result whose refutation condition was written afterwards is not a
result.

## What is already measured, and what it does not say

Upstream, `BENCH-LOG.md` `T-85`/`P9-5`. Clip on `U19`, USB in, ten seconds,
pin 4 as ground:

| flash pin | function (EN25QH32B) | reading |
|---|---|---|
| 1 | `CS#` | 1.65 V |
| 2 | `DO` | 0 V |
| 3 | `WP#` | **1.79 V** |
| 5 | `DI` | 0 V |
| 6 | `CLK` | 0 V |
| 7 | `HOLD#` | **1.79 V** |
| 8 | `VCC` | **1.70 V** |

Three supply configurations give the same chip-side number: the CH341A's own
3.3 V rail (and the programmer browns out with it), a rear motherboard USB 2.0
port, and an ESP8266's regulator injected into the CH341A's 3.3 V rail — the
last one **while its own supply side measured 3.3 V**.

Ruled out already: inrush (still 1.70 V after ten seconds, so it is steady
state) and the programmer's own regulator (the external injection kept 3.3 V at
the injection point and the chip still sat at 1.70 V).

**What the pin table adds, and it was not read out before.** `WP#` and `HOLD#`
are 90 mV *above* `VCC`. On this part they are tied to the supply rail, so the
board's 3.3 V net is itself sitting at about **1.79 V** and the flash's `VCC`
pin is 90 mV below it. So the 1.5 V that went missing is dropped **between the
injection point and the board's rail**, not inside the board.

That is one sentence and it splits the remaining hypotheses in two:

| | hypothesis | what it predicts |
|---|---|---|
| **H1** | **current budget.** The board draws more than the source can give, and the source folds back | the drop appears *at the source*: the CH341A's regulator output is already low |
| **H2** | **series resistance.** Clip contact and ribbon are a few ohms, and the board's ordinary draw develops 1.5 V across them | the drop appears *across the wiring*: the regulator output is 3.3 V and the clip's board end is not |

**The plan's experiment 2 tests H1 only.** It does not distinguish them, because
if H2 is true, holding the SoC in reset changes nothing and the experiment reads
as "H1 refuted" when it has not been tested. Part 1 below fixes that.

## What the datasheet says that changes the odds

**(D, `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf`.)**

- §1: the part "requires only a 3.3 V external power supply. The built-in SWR or
  LDO 3.3 V to 1.0 V can be used for system core power." **So there is one
  external rail.** Injecting through the flash's `VCC` pin supplies the SoC
  core, the SDRAM, the five-port switch and the WLAN — through one clip contact.
  The plan's hypothesis is no longer intuition; it has a datasheet behind it.
- §6: `SF_CS0#` = **pin 45, output**. `SF_SDIO[1:0]` = pins 46/47, I/O.
  `SF_SCK` = **pin 48, output**. `RESET#` = **pin 49, input, "System External
  Reset"** — and it is multiplexed with `LED_PORT3` and `GPIOB[5]`.
- §6.1: the power-on strap pins are `MA[10:8]` (44, 52, 53) and `RAS#`/`CAS#`
  (51) — the DRAM pins. **The `SF_*` pins are not strap pins**, and strap data
  latches 300 ms after the rail passes 0.7 V. So an external master on the SPI
  bus during power-up cannot change the SoC's strapped configuration. That
  removes one hazard from the in-system read.

## The thing that blocks two of the three experiments

The plan's experiments 2 and 3 both begin *"hold the SoC in reset (hold the
reset button, or find RST# and pull it low)"*. **Whether this board can do that
is not established.** `RESET#` shares pin 49 with `LED_PORT3` and `GPIOB[5]`, so
the pin may be an LED driver on this design and not a reset input at all.

What is known, all of it at the desk today:

| | finding | how |
|---|---|---|
| the board has a candidate | *"barrel jack at the board's top-left corner, **with a push button beside it**"* | upstream `notes/hardware-inspection.md` §7 |
| **no rootfs binary names a reset button** | 0 hits for `reset button` / `restore.*default` / `gpio.*button` across every executable in `bin`, `sbin`, `usr/bin`, `usr/sbin` | `strings` over `extracted/unit-2018/squashfs-root` |
| **the vendor kernel has no reset-button driver** | 0 hits for the same needles, **while 13 `gpio`/`GPIO` strings are present** — the scan can see GPIO code, there just is not any for a button | `strings` over the LZMA-decompressed kernel, 3,374,772 bytes |
| **this unit's loader polls only the UART** | `user_interrupt()` touches `0xB8002014` and `0xB8002000` and nothing else; the vendor's alternative `Get_GPIO_SW_IN()` path is `#else`-d out in B | `loader-unpack.py` `interrupt_wiring.console_input`, and `docs/loader-command-semantics.md` |

**Inferred, pending a measurement:** a push button that no software reads, on a
board whose SoC has a dedicated external reset input, is most likely wired to
`RESET#`. Three absences are not a wire. **E3 below settles it for free**, and
it has to run before E4 and E5 or those two are unrunnable.

---

## Part 1 — the experiments, in the order they should run

Every one is read-only or unpowered. **No write, at any voltage, at any point
in this section.**

### E3 first, because it is free and it gates two others

**Is the push button `RESET#` or a GPIO?**

Console attached, board running normally, press the button.

| observation | reading |
|---|---|
| the console prints `Booting...` and the full stage-1 banner | **it is `RESET#`.** E4 and E5 can run |
| nothing, or a userspace message, or a reboot without the stage-1 lines | **it is a GPIO or it is not a button at all.** E4 and E5 cannot run as written, and the section stops after E2 |

**Refutation of the desk inference:** anything other than a stage-1 cold boot.

Costs no power cycle that is not already happening, and it is the answer to a
question the plan assumed.

### E0 — does the clip make contact at all?

Board on **its own adapter**, running. **CH341A unplugged from USB.** Measure at
the far end of the clip's pin-8 wire, at the programmer's header.

| reading | meaning |
|---|---|
| ≈ 3.3 V | the contact is good, and the board's own rail proves it |
| much less, or nothing | **the clip is not making contact**, and every other experiment in this file would have failed for a reason that has nothing to do with the SoC |

This is not in the plan and it should be. A dead contact and a current-starved
board look identical from the chip side.

> ⚠️ The clip's other five wires are on a live SPI bus while the board runs.
> That is fine as long as the programmer is unpowered and driving nothing —
> which is why the CH341A must be **out of USB** for this one.

### E1 — the IR-drop walk: where does the 1.5 V go?

Board unpowered and unplugged. CH341A on USB. Clip on. Measure, in this order,
against the board's ground:

1. the CH341A's USB 5 V
2. the CH341A's 3.3 V regulator output
3. the programmer-side end of the clip's pin-8 wire
4. the flash's pin 8 (`VCC`)
5. the flash's pin 7 (`HOLD#`) — the board rail

**The largest single step is the answer.**

| where the step is | verdict |
|---|---|
| 1 → 2 | the programmer's regulator is folding back. **H1** |
| 2 → 3 or 3 → 4 | clip contact and ribbon resistance. **H2** |
| no big step; 2, 3, 4, 5 all low together | the source is being pulled down by the load, i.e. USB current limit upstream. **H1** |

This replaces the plan's binary "did it climb above 3.0 V" with a location.
Same meter, same five minutes.

### E2 — do the flash and the SoC share a rail?

Board unpowered, nothing plugged in, meter in resistance/continuity mode.
Flash pin 8 against the board's 3.3 V bulk capacitor and against the SoC's
`VDD33` pins.

**Predicted: yes, they are the same net.** The datasheet says the part takes
only a 3.3 V supply and generates its own 1.0 V core, so there is one rail to
share. **This is now a confirmation, not a discovery** — run it anyway, because
a prediction that is never checked is an assumption wearing a result's clothes.

**Refutation:** a separate flash rail would mean the 1.70 V has a different
cause entirely, and H1 collapses.

### E4 — hold the SoC in reset, then repeat E1

**Only if E3 said `RESET#`.** Button held down (or `RESET#` pulled low), clip on,
USB in.

| observation | verdict |
|---|---|
| the chip-side `VCC` climbs above 3.0 V | **H1 confirmed.** The board's running draw was the problem, and it is a current-budget finding with a number attached |
| it does not move from 1.70 V | **H1 refuted, H2 stands.** The drop is in the wiring, and a better clip or shorter leads would fix it — which is a different and cheaper conclusion |

### E5 — the in-system read, and it is the one worth the session

**Only if E3 said `RESET#`.** Board on its own adapter. Clip on, **with the
`VCC` wire disconnected** — `CLK`, `MISO`, `MOSI`, `CS#`, `GND` only. SoC held
in reset. `flashrom -r`.

Success means a **second recovery path that does not depend on the boot loader
being intact.** Today the entire recovery story for a device with no spare is
"the loader's TFTP rescue still answers". That is one path, and it runs on the
thing most likely to be damaged.

> 🔴 **The risk this carries, stated because the datasheet does not rule it
> out.** `SF_CS0#` (pin 45) and `SF_SCK` (pin 48) are SoC **outputs**. Nothing
> in `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` says they are tri-stated while
> `RESET#` is asserted. If they are not, the programmer drives against the SoC's
> push-pull outputs. **Abort conditions:**
>
> - E3 did not return a stage-1 cold boot → do not run E5 at all.
> - Holding the button does not visibly stop the board (LEDs, console) → the SoC
>   is not actually held; stop.
> - `flashrom` reports a chip it cannot identify, or an ID that is not the one
>   `docs/loader-flash-write.md` predicts → stop, do not retry, do not `-r`
>   again.
> - Anything gets warm. Stop.
>
> **What would make this safe rather than merely careful** is a measurement the
> desk cannot supply: whether the SoC releases those two pins in reset. If E5 is
> not worth that risk today, E0–E4 still close S0b, and E5 can wait for a
> logic-analyser session that watches `CS#` and `CLK` while reset is held —
> which observes the answer instead of assuming it.

### Never, in this section

| | why |
|---|---|
| run `probe` or `read` while the chip sits at 1.70 V | 1.70 V is outside this part's operating range. A read that **looks** right at an undervoltage is worse than one that fails, and it would poison a dump this project cannot re-take cheaply |
| write anything, at any voltage | mainline is zero-write through R9, and `flashguard` does not exist yet |
| connect the programmer's `VCC` while the board is on its own adapter | two sources on one rail |
| leave the CH341A in USB during E0 | same reason |

---

## Part 2 — results

*Empty. To be filled at the bench, with the reading beside each row and the
verdict written even when it is the boring one — both directions are a result.*

| # | what was done | reading | verdict |
|---|---|---|---|
| E3 | | | |
| E0 | | | |
| E1 | | | |
| E2 | | | |
| E4 | | | |
| E5 | | | |

**The one-sentence judgement goes here**, and `PROGRESS.md`'s S0 row closes when
it does.
