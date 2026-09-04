# CORRECTIONS — block 9, `R5-3a`, seating 12

**Written after the seating, 2026-09-04 afternoon.**
`PREDICTIONS-B10-block9.md` is frozen and was not edited. Everything below is a
correction to it, a deviation from it, or an addition beside it — recorded here
because that is the only place any of the three may go once a capture has landed.

The seating: **one power cycle**, 2026-09-04, **13:55:58 → 14:27:39** — 量, the
first and last captures' own `started_wallclock` plus the last one's duration,
31.7 minutes. Zero `FLR`, zero
`EW`/`EB`/`FLW`, zero burn, zero upload beyond `S6`'s TFTP into RAM. The flash
bracket is untouched and stands at **1,024 of 4,194,304 = 0.0244 %**; *not one
flash byte is written* is exactly as unsayable as it was.

**Nine card cells ran and all nine landed.** Twenty off-card cells ran beside
them under the `EX-` stem, plus one abandoned `looprun` stage under `SN-`.
35 captures, 140,236 bytes.

---

## 1. 🔴 `TI-3` returned the `0 | 0` row, and it is NOT the finding the card assigned to that row

§ 5.3 assigns `tcir_tc1ip = 0, gisr_tc1ip = 0` to:

> § 3.2 is wrong **too**. `TCIR` bit 30 is not the remaining gate, and the block
> needs something not yet identified. **The most informative outcome of the block**

**The reading is correct and the assignment is wrong.** § 3.2 is right; `TCIR`
bit 30 *is* the remaining gate; and the thing not yet identified is neither a
gate nor in the timer block. It is the vendor's own tick handler.

### 1.1 What `TI-3` actually measured

量, `TI-3`, with everything recomputed from the capture by `tools/tcheck.py`:

| | |
|---|---|
| jiffies since `arm` | **8,714** = 87.14 s |
| that at `hz_used = 200,000` | 17,428,000 counts; `tc1_ext` read **17,431,137** (0.018 %) |
| periods elapsed | **16.62** of 1,048,576 counts |
| `tcir` | `C0000000` — `TC1IE` set, `TC1IP` **clear** |
| `gisr` | `88000004` — byte-identical to `TI-0`'s |

So the period elapsed sixteen times over with the timer-block enable set, and
the pending bit read 0. That excludes *"the period had not elapsed"* and it is
what makes the rest of this section necessary.

### 1.2 讀: the vendor erases it, 100 times a second

`arch/rlx/kernel/rlx-cevt.c:217`, inside `rlx_timer_interrupt()` — the handler
behind `13: RLX LOPI rlx timer`, which `EX-0` measured at 8,824 and `EX-19` at
162,380 — calls `bsp_timer_ack()`. 讀 `arch/rlx/bsp/timer.c:43-46`:

```c
void inline bsp_timer_ack(void)
{
    REG32(BSP_TCIR) |= BSP_TC0IP;
}
```

`|=` is a **read-modify-write**, and `TCIR`'s `IP` bits are **write-1-to-clear**
(`SPEC.md` `REG-10`, D Table 25 — and § 3 below turns that single source into a
measurement). The read returns every bit currently set, including a `TC1IP` that
belongs to a driver the vendor has never heard of, and the write-back puts a 1
there. **Every tick clears every pending bit in `TCIR`, not only TC0's.**

⚠️ **The file was already read and is already in this repository.** 
`docs/blind-write-ledger.md:247` records `bsp_timer_ack()` among
`arch/rlx/bsp/timer.c`'s writes, entered on 2026-09-04 by `R5-10` — one segment
before this one. What is new here is **the consequence**, which nothing had
drawn: 量, `git grep` over the whole tree with `upstream/` excluded finds no
sentence saying the vendor's ack clears a foreign pending bit. The reading was
banked and its implication was not, which is a different failure from not
having read the file.

### 1.3 So `TI-3` measured a duty cycle, not a hardware property

`TC1IP` is set at a TC1 timeout and cleared by the next vendor tick, ≤ 10 ms
later. A single `/proc` read catches it with probability

```
period 20 : 1,048,576 counts / 200,000 Hz = 5,242.88 ms  ->  10/5242.88 = 0.19 %
period  8 :       256 counts / 200,000 Hz =     1.28 ms  ->  (10-1.28)/10 = 87.20 %
```

**The 0.19 % was written down before the experiment, and so was the 87.20 %.**
`EX-3`, at period 8, read `tcir_tc1ip = 1` and `gisr_tc1ip = 1`. Both numbers
are recomputed from the captures by the summary pass, not typed.

🔴 **The refutation condition, stated before `EX-1` ran**: if period 8 also read
`0 | 0`, then 16 wraps at 5.24 s *and* ~6,000 wraps at 1.28 ms would both have
produced nothing, and § 5.3's assignment would have stood. It did not happen.

---

## 2. 🔴 DEVIATION: `TI-4`…`TI-7` ran with their precondition established at period 8, not by `TI-3` at period 20

The card's `TI-4` precondition is literally *"`TI-3` read `tcir_tc1ip=1`"*.
`TI-3` read 0. Three off-card cells established the same **substantive**
precondition — `TC1IP` latched, right now — at a period where it is observable:

| cell | typed | what it established |
|---|---|---|
| `EX-1` | `disarm` ; `period 8` ; dump | the unwind, banked before any new path; `mask_bits=8` |
| `EX-2` | `arm` ; `armirq` ; dump | `tcir` `80000000` → **`D0000000`**, `gisr` `88000004` → **`88000204`** |
| `EX-3` | `sleep 2` ; dump | the same two words 2 s later — latched and stable, not a transient |

`TI-4`…`TI-7` then ran **exactly as the card writes them**. The deviation is
recorded here rather than hidden, and it is visible in the data as well as in
this file: the per-cell table shows `TI-4`…`TI-7` at `mask_bits = 8` where
`TI-1`…`TI-3` are at 20.

**What the deviation costs**: `TI-6`'s `irq_count` and the rate below are at a
period 4,096× shorter than the card's, so any claim of the form *"the card's
period was delivered"* is not available. What is available — delivery, and
delivery at the rate the driver programmed — is stronger and is § 4.

---

## 3. 🟢 `TI-4`: D Table 25's write-1-to-clear claim is no longer single-source

| | |
|---|---|
| `ackip_before` | **1** |
| `ackip_after` | **0** |
| `ack_proven` | **1** |

Both are read inside one `spin_lock_irqsave`, immediately either side of the
write, so the ~1.28 ms until the next TC1 timeout cannot forge the transition.
The driver sets `ack_proven` **only** on a 1 → 0 it watched itself.

🔴 **`SPEC.md` `REG-10`'s closing clause is refuted by this cell.** It read:

> write-1-to-clear 這條主張**依然只有 D 一個來源**,而且現在是量出來的無法測試

The *first* half survives as history and the *second* is now false: it became
testable the moment something set `TCIR` bit 30, which is `armirq`, which is
`R5-3a`. ⚠️ And `REG-10`'s other sentence — *"`TC1IE` 清空時 `TC1IP` 根本不會
latch"* — is **not** refuted: its condition is `TC1IE` clear, and every cell
here that saw a latch had `TC1IE` set. It is superseded, not corrected.

⚠️ `ack_proven` is **n = 1** per the card's own § 2, and this seating did not
improve that: the flag is sticky (量, `git grep` finds one `= 1` and no `= 0`
in the driver), so the later `reqirq` at `EX-5` and `EX-17` did not re-prove it.

---

## 4. 🟢 `TI-5`/`TI-6`: the first interrupt this project has had delivered, and it arrives at the rate the driver programmed

`TI-5` — `reqirq`:

```
gimr  00209100 -> 00209300      bit 9, set by bsp_ictl_irq_unmask through
                                request_irq; this driver never writes GIMR
irq_requested=1  irq_count=8  irq_spurious=0  irq_stuck=0
irq_last_tcir=C0000000          the ISR's own read-back, TC1IP cleared
```

`irq_count = 8` between `reqirq` returning and the `cat` is 10.2 ms at 781.25 Hz
— the shell's own latency, measured by the interrupt counter.

`TI-6` — `/proc/interrupts`:

```
 25:      29602            ICTL  rtl819x-timer (0x20)
```

The driver's own counter reads **29,592** in the same capture — a difference
of **10**, which is 12.8 ms at 781.25 Hz: the gap between the two `cat`s.
At period 12 the same pair reads 113,223 and 113,223, because 12.8 ms at
48.83 Hz is 0.6. **The disagreement between the two counters is itself a rate
measurement, and its disappearance at the slower period is the control.**

🟢 **`EX-0` is what makes that a discriminator rather than a count.** It ran
before `reqirq` and read the same file: lines **2, 8, 13 and no 25**. `EX-19`,
after the final `disarm`, reads lines **2, 8, 12, 13 and no 25** again. Three
states — absent, present with a count, absent — so the line was installed by
this driver's `request_irq` and removed by its `free_irq`, rather than being
found already there.

### 4.1 The rate, at two periods, computed by program

`tools/tcheck.py rate`, over pairs the tool refuses unless `period_cycles`
match on both sides:

| pair | period | predicted /jiffy | measured /jiffy | error | context |
|---|---|---|---|---|---|
| `TI-5`→`TI-6` | 256 | 7.812500 | **7.814052** | 0.0199 % | idle |
| `EX-5`→`EX-6` | 4096 | 0.488281 | **0.488766** | 0.0994 % | idle |
| `EX-17`→`EX-18` | 4096 | 0.488281 | **0.488382** | 0.0206 % | NIC up, 4 pings in flight |

Predicted is `hz_used / period_cycles / hz_kernel` — three integers the driver
reports and none of them truncated. **Measured ratio between the two periods:
15.9873 against a predicted 16.0000, 0.079 %.** A source that was not this
timer would not shrink by 16× when this timer's period grew by 16×, so the
second point is what turns a ratio into a slope.

🔴 This closes the card's own § 7.4 — *"`irq_count` ≥ 1 shows delivery, not
correctness … this block does not measure a rate"* — by addition rather than by
editing the frozen card.

### 4.2 A prediction that did not come true, and it was written before the cell

Before `TI-5` ran, this was written down: at period 8 the vendor's ack could
land between the ICTL latching and the ISR reading `TCIR`, the ISR would see
`TC1IP = 0`, return `IRQ_NONE`, and `irq_spurious` would rise — where the card
predicts 0. **量: `irq_spurious = 0` at every one of the eighteen dumps, over
119,818 delivered interrupts.** The mechanism is real and its rate is below
1/119,818; the card's expectation was right and the addition was wrong.

---

## 5. 🟢 `TI-7`, and two more unwinds beside it

| | `TI-7` | `EX-7` | `EX-19` |
|---|---|---|---|
| `tccnr` vs `tccnr_at_init` | `C0000000` = | = | = |
| `tcir` vs `tcir_at_init` | `80000000` = | = | = |
| `gimr` vs `gimr_at_init` | `00209100` = | = | = |
| `irq_requested` / `tc1ie_ours` | 0 / 0 | 0 / 0 | 0 / 0 |

Three complete unwinds, two of them from a **live** interrupt. ⚠️ 量, and stated because the phrasing is easy to read one way too many: there were **four** arm/disarm cycles on this seating and **three** of them delivered — the first, at period 2²⁰, armed a counter and never installed a handler, which is `TI-1`…`TI-3` and is the whole point of § 1. Final counters:
`irq_count` **119,818**, `irq_spurious` **0**, `irq_stuck` **0**,
`tc0_undisturbed` **1** — the vendor's tick was never disturbed, across the
whole seating.

---

## 6. 🟢 The seven gates of § 3.1 are now all measured

`docs/interrupt-map.md` § 3.1's table had three gates unread and one inferred.

| gate | seating 11 | this seating |
|---|---|---|
| `L1` counter enable | 🟢 set | 🟢 `C0000000` → `F0000000` |
| `L2` period loaded | 🟢 `80000000` | 🟢 `tc1data` `00001000` (period 8) and `00010000` (period 12) — `(mask+1) ≪ 4` at two points |
| `L3` timer-block IE | 🔴 clear, nobody wrote it | 🟢 **`armirq` writes it**: `80000000` → `C0000000` |
| `L4` controller mask | 🔴 clear | 🟢 `request_irq` sets, `free_irq` clears, three times each |
| `L5` routing | **未讀 under Linux** | 🟢 `irr1 = C222FA2D`, `irr1_tc1_rs = 2` |
| `L6` cascade `Status.IM2` | 未讀 | 🟢 `status = 10000401`, `im2 = 1` |
| `L7` `Status.IEc`/`BEV` | 推 | 🟢 `iec = 1`, `bev = 0` |

And an **eighth** thing the table does not have, because it is not a gate to
delivery: the vendor's ack, § 1.2, which gates only *observation* of the flag.

---

## 7. 🟢 `TI-L` and `TI-0`: the routing registers, and `IRQ-07`'s undetermined encoding

`TI-L`, at the loader prompt, `DW B8003008 4` — 71 bytes, and `RUNSHEET` `A0`'s
structural constant predicts `13 + 2 + 47×1 + 9 = 71` exactly, so the reply is
complete rather than cut:

```
B8003008:  00000000  30050004  00000000  00000000
           IRR0      IRR1      IRR2      IRR3
```

* `IRR1 = 30050004` **reproduces `SPEC.md` `REG-03` byte for byte**, eleven days
  and an unknown number of power cycles later. `REG-03` was n = 1; it is n = 2.
* `IRR0`, `IRR2`, `IRR3` had **never been read on this die** in either state.
  At the loader prompt all three are zero.

`TI-0`, under Linux, all four as `bspchip.h`'s own macros predict:
`22222222 / C222FA2D / 2EB29F22 / 22222022`, with `irr1_tc0_rs = 13` and
`irr1_tc1_rs = 2`. Not one nibble of `IRR1` agrees with the loader's, as
`REG-03` predicted.

🟢 **`IRQ-07`'s open question is answered, and by two independent sources in the
same capture.** It asked what the `_RS` fields encode, and named the deciding
experiment as *"read `0xB8003008` under Linux"*. That read gives
`irr1_tc0_rs = 13`; `EX-0`'s `/proc/interrupts` — a different file, produced by
a different subsystem — lists the vendor's tick as **`13: RLX LOPI rlx timer`**.
**The field is the destination IRQ line.** `irr1_tc1_rs = 2` is
`BSP_IRQ_CASCADE`, and TC1 duly arrives as ICTL IRQ 25.

⚠️ What this does **not** settle is the loader's `4` in the same field, which
`IRQ-07` says fits neither reading. Nothing here touched it.

---

## 8. 🔴 An inference of mine, made mid-seating and refuted by the same register twenty minutes later

`EX-0` read `2: 0 RLX cascade (0x0)` and I wrote that no ICTL interrupt had ever
been delivered on this kernel. **`TI-6` delivered 29,602 of them and the cascade
still reads 0** — and `EX-19`, after 119,818, still reads 0. A chained cascade
does not increment its own count.

The narrow claim survives and is the one § 4 uses: **before `TI-5` there was no
line 25 at all.** The wide one was an inference from an absence, which is the
shape this repository's own rule warns about, made by the same person who wrote
the rule into the card.

---

## 9. Additions beside the card (`EX-*`), and why they are not edits

The card owns the `TI-` stem. Every off-card cell took `EX-`, so
`check-predictions` sees exactly the nine cells the card declares and the
population is not quietly widened. Twenty ran:

| | |
|---|---|
| `EX-0` | `/proc/interrupts` **before** anything — § 4's discriminator |
| `EX-1`–`EX-3` | § 2's precondition branch |
| `EX-4`–`EX-7` | second rate point at period 12, then unwind |
| `EX-8`–`EX-15` | the network survival check, § 10 |
| `EX-16`–`EX-19` | interrupts re-armed **with the NIC up**, ping under load, final unwind |

---

## 10. 🔴 The survival ping refuted its own first attempt, and the cause is not the interrupt work

`EX-9` brought `eth4` up at `10.1.1.10` — the interface `RUNSHEET` § D5 measured
as the one the cable is on — and `EX-10` pinged the workstation. The board's
side showed only `PING 10.1.1.2 …` and no replies. The host capture shows why,
and it is the reason `arp` is in that filter:

```
00:12:34:56:78:94 > ff:ff:ff:ff:ff:ff  ARP Request who-has 10.1.1.2 tell 10.1.1.10
fc:19:28:61:84:c9 > 00:12:34:56:78:94  ARP Reply 10.1.1.2 is-at fc:19:28:61:84:c9
                                       (six times, 20 µs apart each time)
```

**The board transmits; the host answers; the board does not receive.** `EX-11`:
`eth4` `TX packets:6 RX packets:0`, driver counters `SW:6 TX:6 RX:0 LNK:0 ERR:6`.

**`LNK: 0` is the reading that matters** — the driver had never seen a link
event. After `EX-12`/`EX-14` brought `eth0` up and down and re-opened `eth4`,
`EX-15` read `LNK: 3`, `RX packets:5`, and **4/4, 0 % packet loss**, with the
host capture holding four ICMP echo requests, four replies, and — the strongest
line of the three — an **ARP request from the host that the board answered**,
which is RX working independently of anything the board initiated.

### 10.1 Two things this does NOT show

1. ⚠️ **It does not isolate the cause.** Between the failing and the working
   ping, two things changed: `eth4` was closed and re-opened, and `eth0` was
   brought up and down in between. This data cannot separate them.
2. 🔴 **It is not a regression against `R3`, and it is not the interrupt work.**
   `RUNSHEET` § D5's 4/4 was taken after bringing up `eth0`…`eth3` *and then*
   `eth4` — so R3's own procedure contained the step that this seating had to
   discover. And `EX-7` measured `gimr = 00209100 = gimr_at_init` **before** the
   NIC was opened at all, so the controller mask was handed back clean; `EX-11`
   then measured the NIC's own interrupt as `12: RLX LOPI eth4`, a **LOPI** line
   that does not pass through the controller this seating touched.

**Carried forward**: a single first open of `eth4` does not receive, and what
makes the difference is unidentified. It costs one power cycle to isolate and
none was spent on it.

---

## 11. Defects found in this session's own instruments

| | |
|---|---|
| 🔴 the analysis tool derived `period_jiffies` on an idle dump | the driver computes it inside `arm()`, so 0 is correct there; the tool reported the **driver** red on `TI-0`. `tcheck.py` `T6` |
| 🔴 it did not model `arm()`'s `ext_interval_j ≥ 1` clamp | red on every period-8 dump. `T7` |
| 🔴 `rate` would score a pair spanning a re-arm against the second period alone | found while writing the control, not while using the tool. `T8` |
| 🔴 the CI step-timing script scored `apt` by substring | `c-apt-ure` contains `apt`, so `test-console-capture-mutants`' 361 s was billed to package installation and `instruments`' 537 s of execution was reported as 92 s |
| 🔴 a control that could not fail | the first `T12` asserted the counter mask and `mask_bits` disagree *somewhere in range*. They cannot: `mult ≤ 2³²−1` always binds first while mask < 2³¹. Rewritten to prove the identity, with `T12b` at 32 bits so it is not vacuous |
| 🔴 two controls passing for the wrong reason | `test-tcheck` `M5` and `M9` survived the first run: `T9` was refused by a different guard than the one it named, and `T5` passed against a hardcoded `exact = True` |

---

## 12. What this seating did not do

1. **No clockevent, no rating change.** `rating` read **0** in all eighteen
   dumps. The system time base was `jiffies` throughout. That is `R5-3b`.
2. **`ESTATUS` is still unread.** `L6`/`L7` are 量 for `Status` only.
3. **`ack_proven` is still n = 1.**
4. **The rate is measured against `jiffies`, which descends from TC0, which
   shares `CDBR` with TC1.** It is a ratio between two dividers fed by one
   crystal, not an absolute frequency — the same limitation `SPEC.md` `CLK-22`
   carries for `R5-2`.
5. **Zero flash bytes are still unmeasured.** No `FLR`, no re-dump; the bracket
   is 0.0244 % and this block added nothing to it, as § 0 of the card said it
   would not.
