# The 1.70 V — what the desk could settle, and what was deliberately not run

**`DAY-ZERO` item 5 / `S0b`. Desk work, 2026-08-23. The board was not touched.**

**Status: `⊘` — deliberately not done.** The reason and the category are in §4,
and the analysis that was written *before* that decision is kept above it,
because it is the part that survives the decision.

**§3 is the exception to that date.** Its `C-14` bullet was answered at the
bench on 2026-08-24 and the measurement is folded in under the two bullets.
Item 5 itself is still not done: the clip has not been on the flash since, and
no flash byte has been written.

---

## 1. What was already measured, and what it does not say

Upstream, `BENCH-LOG.md` `T-85` / `P9-5`. Clip on `U19`, USB in, ten seconds,
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
state) and the programmer's own regulator (an external injection held 3.3 V at
the injection point and the chip still sat at 1.70 V).

## 2. What re-reading those same numbers settles, with no bench time at all

**`WP#` and `HOLD#` are 90 mV *above* `VCC`.** On this part they are tied to
the supply rail, so the board's 3.3 V net is itself at about **1.79 V** and the
flash's `VCC` pin is 90 mV below it.

**So the missing 1.5 V is dropped between the injection point and the board's
rail, not inside the board.** That is one sentence, out of numbers that were
already on file, and it is most of what item 5 existed to produce.

It leaves exactly two hypotheses:

| | hypothesis | it predicts |
|---|---|---|
| **H1** | **current budget.** The board draws more than the source can supply and the source folds back | the drop is *at the source*: the regulator output is already low |
| **H2** | **series resistance.** The clip contact and ribbon are a few ohms, and the board's ordinary draw develops 1.5 V across them | the drop is *across the wiring*: the regulator output is still 3.3 V and the clip's board end is not |

**They are not separated, and this file does not claim they are.**

### And the datasheet says why H1 is plausible without measuring anything

**(`refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf`.)** §1: the part *"requires only a
3.3 V external power supply. The built-in SWR or LDO 3.3 V to 1.0 V can be used
for system core power."*

**There is one external rail.** Injecting through the flash's `VCC` pin
therefore supplies the SoC core, the SDRAM, the five-port switch and the WLAN —
all of it through one clip contact and one flash-pin trace. The hypothesis
`plan/DAY-ZERO.md` recorded as *"most likely"* now has a datasheet behind it
instead of intuition.

## 3. Two things about the pins that were never read out before

**(Same datasheet, §6 and §6.1.)** Both were found while checking whether item 5
could run as written, and both outlive the decision not to run it.

- **`RESET#` is pin 49, and it is multiplexed with `LED_PORT3` and
  `GPIOB[5]`.** So *"hold the SoC in reset"* is not obviously available on this
  design — the pin may be an LED driver here. Three absences pointed the other
  way: no rootfs binary names a reset button, the vendor kernel has no
  reset-button driver **while carrying 13 `gpio` strings as the control**, and
  **"this unit's loader polls only the UART" — which is wrong.** That third
  absence is refuted, first read out of this unit's own image and then measured
  on the device: the loader's init configures this pin as a GPIO input at
  `0x804083AC` and `0x80408DE4` reads it. **Three absences are not a wire**, and
  here one of the three was not an absence at all. Carried as `C-14`; answered
  2026-08-24, and the measurement closes this section.
- **`SF_CS0#` (pin 45) and `SF_SCK` (pin 48) are SoC outputs**, and nothing in
  the datasheet says they are tri-stated while `RESET#` is asserted. Meanwhile
  the power-on strap pins are the DRAM ones — `MA[10:8]` at 44/52/53 and
  `RAS#`/`CAS#` at 51 — **not** the `SF_*` pins, so an external master on the
  bus at power-up cannot change the strapped configuration.

The second bullet moves the risk in both directions at once, and the direction
that matters is the first half of it.

### Measured 2026-08-24: the button is a GPIO on `PABCD` bit 5, not `RESET#`

`bench/2026-08-24b/B7a`, `B7b`, `B7c`, one boot, 🔄 no flash-write command issued *(was “zero flash bytes”; no `FLR` bracket ran)*. Register
names are from the datasheet, §8.3 (`SPEC.md` `MAP-09`); the values are from the
device. `DW B8003500 1` prints w1 = `PABCD_CNR`, w3 = `PABCD_DIR`, w4 =
`PABCD_DAT`:

```
released  B8003500:  FFFFFFDF  00000000  FF000000  0000003C
held      B8003500:  FFFFFFDF  00000000  FF000000  0000001C
XOR                                                00000020   → bit 5 only
```

> **Measured on the device: the button is a GPIO on `PABCD` bit 5, active low
> with a pull-up. It is not `RESET#`.** `DIR` bit 5 is `0`, an input. `CNR` and
> `DIR` are byte-identical across the press, so the button drives one pin and
> does nothing else to this port. `B7c.log` contains no `Booting...` and no
> banner — the board did not reset while the button was held.

**Refuted by**, all three written down before the cell ran
(`bench/2026-08-24b/PREDICTIONS-block2.md`): w4 bit 5 still `1` — the button is
not on this pin and `B7a` measured something else; any *other* bit of w4 moving
— more than one thing sits on this port and "bit 5 is the button" is
under-determined; or no `B8003500:` line at all with `Booting...` and the banner
appearing in the ESC stream — it is `RESET#` after all. None of the three
happened.

**Answered by a bit that moved, not by an absence.** `RUNSHEET.md` `D3` — press
the button, expect a stage-1 cold boot — could only ever have produced an
absence on the GPIO branch, and *nothing happened* does not separate a GPIO from
a `RESET#` that is not wired to this button from a press that never registered.
Reading the port block makes the negative branch decidable.

**The corroboration is what makes it hard to argue with.** `PABCD_CNR` reads
`FFFFFFDF`: **bit 5 is the only cleared bit in the whole 32-bit word.** Read out
of this unit's image, `0x804083AC` — called unconditionally from `main` at
`0x80406778` — clears bit 5 of `0xB8003500` and `0xB8003508`. One bit named by
the disassembly, exactly that one bit clear on silicon. Refuted by w1 or w3
bit 5 reading `1`, which would have meant that routine did not run on this boot
and w4 is not the button.

**And the loader reads this pin, not a copy of it.** Read out of the image:
`0x80408DE4` takes the button state from a RAM structure at `[0x8040DD4C]+0x44`
instead of the port block when `(0xB800000C & 0xF) == 13`. Measured (`B7b`,
`DW B8000000 1`, w4): that nibble is `0xF`. The multiplex is not taken, so the
GPIO `B7a`/`B7c` read is the one the loader reads. Refuted by that nibble
reading 13.

**What is true instead of "polls only the UART".** Read out of the image: the
loader reads this pin only inside the boot ESC window. Consistent with the
device — the button was held while `B7c` ran at the `<RealTek>` prompt, and
nothing happened beyond the command's own reply and the ESC stream's. A hold at
the prompt drives the pin and reaches nothing that is looking.

**Reconciled with the ten-second factory reset.** That holding the button for
about ten seconds resets the unit to defaults is *reported at the bench, not
measured here*. It is the vendor kernel timing a GPIO: a hardware `RESET#`
cannot carry a hold-duration semantic, because the SoC is in reset from the
moment the pin is asserted and nothing is left running to count the seconds.
Both observations are of the same pin, and they differ only in which software is
awake to read it.

**The cell was made safe, not assumed safe.** `B7c` was sent inside
`--esc-after 20 --seconds 35`, so the branch it did not expect — the board
resetting under the press — would have been caught by the ESC stream in the same
capture, costing a prompt rather than a power cycle. The ESC accounting came back
as predicted: 985 bytes = 7 × 128 + 89, seven `Unknown command !`, and
`flush-b7c` consumed the residue.

**Consequence, recorded here because this file owns the button.** `RUNSHEET.md`
`D3` will not produce a cold boot; the question it existed to answer is answered
already, and at no power cycle. `D2b`'s refutation condition — *after the button,
a cold boot, the same read must come back changed* — assumed the press **was** a
cold boot, so it is unavailable as written and has to come from a power cycle
instead.

---

## 4. The decision, and why it is the right one

**Not done. Category: blocked on instrumentation** (`plan/` §17, item 5), with a
voluntary-risk component that is stated rather than folded in.

Two reasons, in the order that matters:

1. **The one variant that had never been tried cannot be tried with this
   harness.** The industry-standard in-system read is *board on its own supply,
   programmer's `VCC` line not connected*. **This SOIC-8 clip's far end is
   soldered, so its `VCC` line cannot be opened.** Insulating the clip's pin-8
   contact would open it mechanically — and it would not touch reason 2, which
   is the one that decides.
2. **The remaining risk is to the only device.** With the board powered and the
   programmer driving `CLK` and `CS#`, those two pins are SoC **outputs**, and
   the datasheet does not say reset releases them. That is an output-against-
   output contention that no amount of care removes, only a measurement would —
   and the measurement needs a logic analyser watching `CS#` and `CLK` while
   reset is held, which is a different session with different equipment.

**One device, no spare.** A recovery path that might cost the device is not a
recovery path.

The remaining experiments — a contact check, an IR-drop walk, a continuity
check — are all zero-risk, and they were dropped with the rest because
**mainline does not need in-circuit programming at any point through R9**, and
because §2 above already produced the explanation that item 5 existed to
produce. What they would have added is the H1/H2 separation, and that is now
recorded as unmeasured rather than guessed.

### What this costs, stated plainly

| | |
|---|---|
| **`plan/` §17 item 5** — an independent second instrument for the flash dump — **stays open**, and what it is missing is now named precisely: a clip harness whose `VCC` line can be opened, **and** a measurement that the SoC releases `SF_CS0#`/`SF_SCK` in reset | it was already open; nothing regressed |
| **H1 against H2 is undetermined** | it was undetermined before, and this file no longer implies otherwise |
| the recovery story is still one path — the loader's TFTP rescue | **unchanged, and it is the reason R8's rescue drill is a hard precondition rather than a nicety** |

**What is *not* a cost**: the mainline. R0 through R9 write zero flash bytes and
reach the flash only through the loader, which does not need any of this.

---

## 5. If it ever comes back

Not a plan, a note for whoever reads this next. It comes back only if **both**
of these are true:

1. a clip harness exists whose `VCC` line can be opened without unsoldering — or
   a second unit exists, at which point the question stops being interesting;
2. `SF_CS0#` and `SF_SCK` have been **observed** to float while `RESET#` is
   asserted, on a logic analyser, rather than assumed to.

Condition 2 is the one that matters, and it is an observation, not an argument.
