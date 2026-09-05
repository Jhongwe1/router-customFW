# CORRECTIONS — Block 10, `R5-3b-1`, seating 13

**Written 2026-09-06, thirty-fifth segment, after the seating.**
Three power cycles, 59 captures, `check-predictions` **32 of 32**.
**Zero flash-write commands, zero `FLR`.** The bracket is unchanged at
1,024 / 4,194,304 = 0.0244 %.

`bench/2026-09-06/PREDICTIONS-B11-block10.md` was frozen when `SP-A` landed.
Everything below is a correction to it, or a reading it did not ask for.

Every number in this file is re-derived from the captures by
`derive.py`-style arithmetic on the parsed `/proc/rtl819x-timer` fields, not
transcribed from a terminal.

---

## 0. What the block set out to do, and whether it did it

`R5-2` proved the timer counts. `R5-3a` proved the interrupt is delivered.
Neither made the kernel *depend* on either. **This block made it depend, three
times, and then showed the dependence by breaking the timer on purpose.**

| | |
|---|---|
| handover | **n = 3**, `CE-7`, `P2-5`, `P3-5` — three independent cold boots |
| negative control | **n = 3**, `CE-5`, `P2-4`, `P3-4` — every one `ce_probe_mode_calls=0` |
| causal test | **6 rows, 4 distinct reloads (2000/4000/8000/20000), 1× to 10×**, every ratio to four decimals |
| lost ticks | **0** over 25,853 periods / 258.53 s |
| guards | `irq_spurious`, `irq_stuck`, `ce_badmode`, `ce_hw_bad`, `ce_next_calls`, `irq_preacked` — **max 0 across all 59 captures**; `tc0_undisturbed` **min 1** |

---

## 1. 🟢 The handover, and the three witnesses in increasing independence

The card's § 5.4 ordered these before the block ran, and the order held.

### 1.1 Kernel state, read through my own driver

```
CE-7   verdict=0 registered=1 live=1 mode=2 mode_calls=2 hw_bad=0 next=0 badmode=0
P2-5   verdict=0 registered=1 live=1 mode=2 mode_calls=2 hw_bad=0 next=0 badmode=0
P3-5   verdict=0 registered=1 live=1 mode=2 mode_calls=2 hw_bad=0 next=0 badmode=0
```

`ce_mode_calls=2` and not 1, three times. 讀 `kernel/time/clockevents.c`:
`clockevents_exchange_device()` shuts the new device down, then
`tick_setup_periodic()` starts it — SHUTDOWN then PERIODIC. The card predicted
2 from the source before the board was powered; the board printed 2.

### 1.2 An address out of this build's `System.map`, typed by nobody

```
CE-0 / P2-0 / P3-0   ce_handler=80036D50   ce_handler_is_noop=1
CE-7 / P2-5 / P3-5   ce_handler=80036FC4   ce_handler_is_noop=0
```

`80036d50 T clockevents_handle_noop`, `80036fc4 T tick_handle_periodic`, both
re-derived by `cardcheck numbers` from `r53b1.System.map`. **The pair is the
reading, not either half** — `CE-0` prints the other address from the same code
path on the same boot, so a driver that printed a constant is excluded by the
capture rather than by trust.

### 1.3 🟢 The causal test — the only witness that does not ask the kernel about itself

`ce_cycles` accumulates `reload` per delivered interrupt, so
`Δce_cycles / hz_used` is elapsed **real** seconds; `Δwall` is elapsed
**kernel** seconds. Their ratio is the error the kernel cannot see.

| cell | `reload` | Δwall | Δjiffies | Δce_cycles | **ratio** | card predicted |
|---|---|---|---|---|---|---|
| `CE-7`→`CE-8` | 2000 | 46.57 | 4,657 | 9,314,000 | **1.0000** | 1.00 |
| `CE-9` | 4000 | 5.02 | 502 | 2,008,000 | **2.0000** | 2.00 |
| `CE-10` | 2000 | 5.03 | 503 | 1,006,000 | **1.0000** | 1.00 |
| `P2-8` | 8000 | 5.01 | 501 | 4,008,000 | **4.0000** | 4.00 |
| `P2-9` | 2000 | 5.03 | 503 | 1,006,000 | **1.0000** | 1.00 |
| `P3-6` | 20000 | 5.01 | 501 | 10,020,000 | **10.0000** | 10.00 |

Six rows over four distinct reloads, spanning 1× to 10×, is a slope. ⚠️ **The card's own § 5.5 says "Five rows" and that is correct for the card** — its table omits `P2-9`, the restore after `P2-8`. Mine has it, so mine has six. This sentence read "Five rows" until the wrap-up audit, because it was re-quoted from the card rather than re-derived from the table above it. ⚠️ No single row is worth quoting
alone: `Δwall` is quantised at one jiffy because `CONFIG_GENERIC_TIME=y`
selects `clocksource_jiffies` (`CLK-20`, `CLK-21`), so each row carries ±1 % at
these lengths — which is why the block took six of them over four distinct
reloads and not one.

**`tc1data` followed on every armed dump**, `tc1data = period_cycles << 4`:

```
CS-1 / P3-1b  256   -> 00001000      CE-9   4000  -> 0000FA00
CE-1 / P2-2b  2000  -> 00007D00      P2-8   8000  -> 0001F400
                                     P3-6  20000  -> 0004E200
```

`CE-0` is the control on that rule and it does **not** follow it: `state=idle`,
`tc1data=00000000`, the register as init left it. The rule is about an armed
timer and the idle dump says so.

---

## 2. 🟢 `P3-7` — a cell that is not on the card, and it is the strongest reading of the seating

The card's § 5.4 states, before the block ran, that
`Δjiffies == Δ(line 25)` proves nothing, because my tick and the vendor's are
both 100 Hz and the vendor's keeps firing after the handover. That is correct
and it is a real limit on every cell the card contains.

**`P3-6` removes the limit for free**, and the card did not notice. With
`ce_reload=20000` my tick is 10 Hz while the vendor's TC0 is untouched at
100 Hz. One extra cell, 90 s, taken after `P3-6` and before power-off:

```
P3-7   cat /proc/interrupts ; cat /proc/rtl819x-timer ;
       sleep 3 ;
       cat /proc/interrupts ; cat /proc/rtl819x-timer
```

| | |
|---|---|
| Δ line 13, the vendor's `rlx timer` | **3,009** → 99.97 Hz |
| Δ line 25, `rtl819x-timer` | **301** → 10.00 Hz |
| **Δjiffies** | **301** |
| line 13 / line 25 | **9.9967** |
| **Δjiffies − Δ line 25** | **0** |
| Δce_cycles / `hz_used` | **30.10 real s** |
| Δwall | **3.01 kernel s** |

**In 30.1 real seconds the vendor's timer interrupt was delivered 3,009 times
and the kernel counted 301 jiffies.** The two lines are no longer the same
number, and `jiffies` tracks mine with zero residual. This says the system tick
is mine without quoting an address, without asking the tick core about itself,
and without the tautology the card correctly refused to rely on.

---

## 3. 🔴 Corrections to the card

### 3.1 `NB-0`: the card predicted a line that cannot exist yet

Card: *"lines for **2/8/12/13** only — no line 25"*. `NB-0` read:

```
  2:          0             RLX  cascade (0x0)
  8:        164        RLX LOPI  serial (0x20)
 13:       5682        RLX LOPI  rlx timer (0x620)
```

**No line 12.** Every interface in the same capture reports `Interrupt:12`,
because `ifconfig` prints `dev->irq`, which is set at probe. A line in
`/proc/interrupts` appears at `request_irq`, which this driver does at
`ndo_open`. With every interface DOWN there is no line 12.

🟢 **The refutation has its own positive control inside the seating.** `CE-4`,
after `NB-1` brought `eth4` up, reads:

```
 12:         25        RLX LOPI  eth4 (0x20)
```

So line 12 is the same three-state reading the card built the *line 25*
argument on, and the card got its own example wrong while getting the argument
right. The `NB-0` claim that matters — **no line 25 before `reqirq`** — holds.

### 3.2 🔴 `NET-14` does not reproduce

Card `NB-1`, 推: *"the seating-12 failure reproduces: `TX` non-zero, `RX 0`,
`LNK 0`, 100 % packet loss"*. Measured, first open of `eth4` on a cold boot
with `eth0` never touched:

```
4 packets transmitted, 4 packets received, 0% packet loss
eth4 ... RX packets:5 ... TX packets:5
```

The card's own stop-if is the instruction that was followed: *"4/4 replies →
`NET-14` does not reproduce, and the finding is that it was not deterministic.
Record and go on."* `NB-2` then re-opened `eth4` anyway and also got 4/4, with
RTTs `2020 / 1000 / 0 / 10 ms` — the two-second first packet is link
renegotiation after `ifconfig down`.

**`NET-14` therefore moves from *a failure* to *a non-deterministic failure
observed once*, and the isolation `NB-2` was built for has nothing to isolate.**
The host capture `SP-host.txt` holds both directions for both cells.

### 3.3 ⚠️ `CE-4`'s `irq_count`: the prediction was right and the number was not comparable

Card: *"`irq_count` **≈ 800** (8 s at 100 Hz)"*. Measured **1,170**.

The interval is not 8 s. `CE-3` runs `reqirq` and `CE-4` runs `sleep 8`, so the
elapsed time between the two dumps is the sleep **plus a capture teardown and
setup**: `Δwall = 11.69 s`, `Δirq_count = 1,168`, **99.91 Hz**.

🟢 **The seating contains its own control for this.** `P2-3` and `P3-3` put
`reqirq ; sleep 8 ; cat` in ONE cell, and both read **`irq_count = 803`** —
the same driver, the same rate, and the card's own number. **The difference
between 1,170 and 803 is entirely in how the card split the cells**, and a
future card that predicts a count must say which cell boundary the interval
runs between.

### 3.4 🔴 `P2-1a`, `P2-2a`, `P3-1a`, `P3-2a` carry expectations they cannot show

Each of these cells types only `echo` verbs and no `cat`. Their captures are
110–111 bytes: the echoed command line and the prompt.

```
P2-1a.log   111 bytes   "echo period 8 > ... ; echo arm > ... ; echo armirq > ..."  #
P2-2a.log   110 bytes
```

The card lists `state=armed`, `mask_bits=8`, `tcir_tc1ie=1` under `P2-1a`.
Those values are real and are in `P2-1b`'s dump — but **a cell's expectations
cannot be written on a cell that produces no reading**. Either the split cell
gets a `cat`, or its expectations belong to the cell that follows it.

### 3.5 🔴 `P2-7` names a precondition no cell on PC2 establishes

Card § 4.2: *"`NET-14`'s cells do **not** repeat: they are spent."* So nothing
on PC2 brings `eth4` up. Card `P2-7`: `ping -c 20 10.1.1.2`, expecting 20/20.

Run exactly as written:

```
PING 10.1.1.2 (10.1.1.2): 56 data bytes
ping: sendto: Network is unreachable
```

**The defect is measured rather than argued**, which is why the cell was run as
written before it was fixed. The cell's actual content — interrupt behaviour
under traffic — was then taken as two cells of mine:

| capture | typed | why |
|---|---|---|
| `P2-7a` | `ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up ; ifconfig eth4` | the precondition, and it prints its own evidence rather than being a silent setup cell (§ 3.4) |
| `P2-7b` | `ping -c 20 10.1.1.2 ; cat /proc/rtl819x-timer ; cat /proc/interrupts` | the cell |

`P2-7b`: 4/4, `irq_spurious=0`, `irq_stuck=0`, **`irq_preacked=0`** under
traffic — the § 5.2 comparison the cell exists for, and it agrees with `CE-4`.

### 3.6 🔴 PC3 is outside the card's own `cells` fence

`cardcheck`/`check-predictions` read the ```cells``` fence. It lists 32 entries,
all of PC1 and PC2. `P3-L` and `P3-6` have literal `CAP OUT` commands in § 4.3
and are **not** in the fence; `P3-0`…`P3-5` have no literal command at all,
only the sentence *"as `P2-0`…`P2-5` … capture names `P3-0`…`P3-5`"*.

Found at the desk before power, by generating the commands from the card and
sweeping **in both directions**: 34 commands emitted, 32 cells declared, the
two extras named. A generator that only checked *declared → command* would have
reported a clean 32.

**Consequence, stated rather than hidden:** `check-predictions` reads **32 of
32** for this seating, and that number does not include the ten PC3 captures.
The fence is a list of what the block *will* produce; PC3 is reserve, so
excluding it is defensible — but a reader must not read 32/32 as *the whole
seating was checked*.

### 3.7 🔴 The cold-boot banner was lost on PC2, and the fix has a control

`SP-A` (PC1) holds `Booting...`, `chipName: UNKNOWN`, `ramSize: 32M`,
`---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)`.

`SQ-A` (PC2) holds none of them. Its first bytes, at **t = 0.004 s**:

```
---Escape booting by user
P0phymode=01, embedded phy
---Ethernet init Okay!
<RealTek>
```

The operator reached the power switch before the capture opened the port, so
stage-1's banner went to a port nobody was listening on.

🟢 **The cold boot is still attested, by the capture's own shape.**
`---Escape booting by user` is printed by stage-1's boot-delay loop when it
sees an ESC; a board already sitting at `<RealTek>` answers an ESC with
`Unknown command !`. `SQ-A` holds the first line once and the second ~1,700
times. **The transition proves the capture began inside the boot's ESC
window**, which a board that was already at the prompt cannot produce.

🟢 **The fix was then run as a controlled experiment.** For PC3 the operator
was asked to wait ten seconds after replying before touching power. `SR-A`
holds the full banner. **Three power cycles, one variable, and the outcome
followed it** — so this is a procedural finding with a control and not an
apology.

🟢 **A second instrument measured the same thing, and it had never heard of the
procedure.** `tools/boot-timeline.py` classifies a capture cold or warm from
the loader's own line. Over the whole tree it moves **22/37 → 24/37** for this
seating — **three power-ons and two cold rows** — and it names the missing one
itself:

```
bench/2026-09-06/SQ-A.log -- boot text but no `Booting` anchor
                          -- the capture opened after the board started
```

`SQ-A` is the `1 of them hold boot text` in that directory's NOT CLASSIFIED
line. The isolation check the convention requires: every directory except
`2026-09-06` still reports 22 cold / 37 warm, and `2026-09-06` alone reports
2 cold / 0 warm, so the delta is exactly **+2 / +0** and nothing was
reclassified. **The zero warm rows are also a reading** -- `looprun` ran with
`--skip S2,S3,S4` on all three cycles, so its own `J BFC00000` never fired, and
this is the first seating since 2026-09-02 to add no warm row at all.
`tools/test-boot-timeline.sh` `B2` carries the numbers and the reasoning.

---

## 4. 🔴 A finding with reach beyond this block: `ping -c` does nothing

`P2-7b` asked for `-c 20` and the board sent 4. Five requests were then put to
it, in three cells:

| capture | asked | transmitted |
|---|---|---|
| `NB-1`, `CE-12` | `-c 4` | 4 |
| `P2-7b` | `-c 20` | 4 |
| `P2-7c` | `-c 2`, then `-c 7` | 4, 4 |
| `P2-7d` | `-c20` (attached), then `busybox ping -c 3` | 4, 4 |

The echoed command line is intact in every capture, so the shell received what
was typed. Both the spaced and attached option forms, and the explicit
`busybox ping` invocation, give 4.

**This image's `ping` ignores `-c` and always sends exactly four packets.**

⚠️ **What that does and does not do to the record.** It invalidates nothing:
four replies is four replies, and every past `ping -c 4` cell got what it
asked for by coincidence rather than by request. What it does is remove a
degree of freedom nobody knew was missing — **a card cannot ask this image for
a ping count other than 4**, and `P2-7`'s "20/20" was unreachable for a second
reason on top of § 3.5. The binary behind the applet is a desk question;
`config/rlxfw-initramfs.tsv` is where it starts.

---

## 5. 🟢 Everything else the block predicted, and hit

* `CE-0` / `P2-0` / `P3-0`: eighteen fields each, including the 3.0-only
  `period_jiffies=67108` — `(2²⁷ × 100) / 200000` in integer arithmetic —
  and `ce_reload_exact=1`, the gate every later cell depends on.
* `CS-1`: `arm_delta_100us=20`, card band **18…24**, and the same 20 on all
  three cycles. `period_jiffies=0` beside `mask_bits=8`, which is
  `notes/timer-driver.md` § 11.6 6 fixed in 3.0 — `256 × 100 / 200000`
  truncates, and `tc1_ext_trusted` follows it to 0.
* `CS-2`: `tcir_tc1ip=1` at 87.20 % duty, **and `gisr_tc1ip=1` with
  `gimr_tc1ie=0`** — the masked-observation strategy confirmed again, on
  every cycle.
* `CS-3` / `P2-1b` / `P3-1b`: `ackip_before=1 → ackip_after=0 → ack_proven=1`,
  three times. D Table 25's write-1-to-clear holds on this die.
* `CS-4`: full unwind, `tccnr` and `tcir` back to their `_at_init` values, and
  `ack_proven` **still 1** — not reset by `disarm`, which is what lets `CE-3`
  run.
* `CE-3`: `gimr_tc1ie=1`, set by `bsp_ictl_irq_unmask` through `request_irq`
  and never by this driver.
* `CE-11`: **`last_verdict=-16` (`-EBUSY`)**, `state=armed`, `ce_live=1`. The
  refusal is the deliverable. This is the one cell whose success would have
  been the bad outcome, and it refused.
* `CE-12`: 4/4 with line 25 still rising — a network stack whose every timeout
  is in `jiffies`, running on my tick.
* `P2-6`: **0 lost ticks** over 258.53 s. `Δjiffies`, `Δirq_count` and
  `Δce_cycles / reload` are **25,853, 25,853, 25,853**. The card wrote
  推 0 and *"refuted by any non-zero value"*.
* `P3-L`: `B8003008: 00000000 30050004 00000000 00000000` — `IRR1 = 30050004`,
  `REG-03`'s third reading, reproduced byte for byte at the loader prompt.
  Under Linux the same register reads `C222FA2D` (`CE-0`), because Linux
  reprograms the routing; both readings match what each context predicts.
* Three `looprun` boots, six assertions each: `AUTOBURN` `00000000`, eight
  staged head words derived from the image, eleven marks in declaration order,
  **`RLXFW-ID0`: board printed `93e1c9c7`, build computed `93e1c9c7`**, a
  reachable prompt. Machine totals **21.77 / 21.68 / 21.71 s** — range 0.09 s,
  0.41 %.

---

## 6. What this seating did NOT establish

* **It is not `R5-3b`'s DoD.** That DoD is *the board boots with my timer as the
  system time base, ten times*. Every handover here came from a `/proc` write
  on a board that had already reached a shell. Boot-time arming is `R5-3b-2`
  and it needs a different image.
* **Nothing was measured about a clocksource.** `mode ce` registers and
  unregisters nothing on that side; `rating` read **0** in every dump and
  `tc1_ext_*` read 0 throughout.
* **The longest window is 258.53 s.** A handover that works for four minutes
  and fails at forty is not excluded.
* **The `>=` boundary is still untested.** `CE-5`/`P2-4`/`P3-4` run rating 99
  against the vendor's 100; a tie at exactly 100 was never registered.
* **`irq_preacked=0` everywhere** is one of the two outcomes § 5.2 predicted,
  so the fixed-phase model of § 5.1 survives — but *survives* is not
  *confirmed*: the other predicted outcome was `≈ irq_count`, and only a value
  strictly between the two would have refuted it.
* **The flash sentence has not moved.** No `FLR` ran, no full re-dump ran, and
  the bracket stands at **1,024 of 4,194,304 = 0.0244 %**. *Not one flash byte
  is written* remains unsayable, exactly as it was.

---

## 7. The captures

| prefix | what |
|---|---|
| `SP-*`, `SQ-*`, `SR-*` | the three `looprun` boots: `-A` cold catch, `-rescue.json`, `-ab2` burn flag, `-2a` staged head, `-boot` |
| `SP-host.txt`, `SQ-host.txt`, `SR-host.txt` | host-side `tcpdump -e -n 'icmp or arp'`, one per power cycle |
| `NB-*`, `CS-*`, `CE-*` | PC1, 20 cells |
| `P2-*` | PC2, 12 card cells + `P2-7a`/`P2-7b`/`P2-7c`/`P2-7d` (mine) |
| `P3-*` | PC3, `P3-L` + `P3-0`…`P3-5` + `P3-6` + `P3-7` (mine) |

⚠️ **The host captures were written outside the repository first and moved in
only after their MAC survey was read.** The board's `eth4` is
`00:12:34:56:78:94` and the loader's synthesised address is
`56:0a:01:01:01:e8`; neither is `H601`'s. **A containment rule whose
correctness depends on the experiment coming out the expected way is not a
containment rule**, so the order was: capture to the scratchpad, read the MACs,
then decide.

🟢 That survey also turned a *read* claim into a *measured* one. `RUNSHEET` § G3
says the loader *"synthesises its MAC from that address"*. `56:0a:01:01:01:e8`
carries `0a:01:01:01` = **10.1.1.1** in bytes 2–5. It had never been checked.

⚠️ And the board's own ping RTT is quantisation, not latency: `CE-12` reports
`time=10.000 ms` four times, while `SP-host.txt` timestamps the request and its
reply **20 µs** apart. One jiffy at `HZ=100` is 10 ms and
`clocksource_jiffies` cannot resolve below it.
