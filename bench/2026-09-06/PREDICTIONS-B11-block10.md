# Block 10 — `R5-3b-1`: the system tick, handed over and taken back

**Written 2026-09-06, thirty-fourth segment, at the desk, before power.**
Gate `R5`, step `R5-3b-1`. Three power cycles. Nothing here writes flash.

> **Frozen when the first capture lands.** Until then this file may be edited;
> after, corrections go in `bench/2026-09-06/CORRECTIONS-block10.md` and this
> file is not touched, so that what was predicted stays legible beside what
> happened.

---

## 0. What this block is, in one paragraph

`R5-2` proved my timer counts. `R5-3a` proved my interrupt is delivered —
119,818 times, `irq_spurious` 0. Neither made the kernel *depend* on either:
the clocksource ran at rating 0 so nothing would select it, and the interrupt
went to a handler that did nothing but count. **This block is where the
dependence starts.** It registers a `clock_event_device` at a rating above the
vendor's, the tick core exchanges the devices, and from that instant `jiffies`
advances because of an interrupt this repository's own source produced. It is
the first step of `R5` that can leave the board unable to reach a prompt.

---

## 1. The image, staged and pinned

| | |
|---|---|
| file | `$FWRE_WORK/rebuild/bench-only/r53b1-20260906/rlxfw-r53b1-20260906.bin` |
| bytes | **1,033,216** |
| sha256 | `e160089ae8ea59523c97af289887e0dd12286cc1fcc2ead5875d5fa5afb671b3` |
| `RECIPE_ID` | **`93e1c9c7`** — the board must print `RLXFW-ID0=93E1C9C7` |
| driver | `rtl819x-timer` **3.0** (2.0 was seating 12's, 1.0 seating 11's) |
| `vmlinux` | 3,975,506 bytes, sha256 `e9fcf3d52767c32e…` |
| recipe | `--variant quiet`, `--marks`, `--jobs 4`, declared cflags and stamp — **identical to `r53b`'s manifest in every field but the driver source** |

**Gates run at the desk, all three green:**

* `rlxfw-marks verify` — 12 marks present once in my image, **0** in the
  vendor's `ctl-vendor/kroot/vmlinux`; 2 witnesses.
  ⚠️ **`MK2`'s witness count moved 1 → 2 and the reason is this block's own
  edit**: the negative-control device is named `"rtl819x-tc1-probe"`, which
  *contains* the witness string `rtl819x-tc1`. 讀 `tools/rlxfw-marks.py:568`,
  a `str:` witness passes on `got >= 1`, so this is a pass by the rule and not
  by luck — but a reader diffing against seating 12's run would otherwise find
  an unexplained 2.
* `hazlint-objs --also drivers/clocksource` — **0 violations in 1,986 loads**
  across 61 leaf objects, with `Q5` firing (11 violations for the same sources
  at `-march=5281`), so the sweep can fail.
* the build log names `rtl819x-timer.c` in **0** diagnostics, and the control
  that this means anything is line 441, `CC drivers/clocksource/rtl819x-timer.o`
  — the file was compiled.

⚠️ **This is the third build of this driver today and the first two are not
the image above.** `93434ca3` was 3.0 without `cereload`; `a63f318c` was 3.0
with it and with the stale `period_jiffies` that `notes/timer-driver.md`
§ 11.6 6 assigns to this step; `93e1c9c7` is the one that fixes it. **The
sha256 in the row above is the only identity that matters** — 量 today, all
three images are 1,033,216 bytes.

### 1.1 Two addresses out of this build, and nobody types them

`RLXFW-ID0` is this project's existing "the board printed the id the build
computed". This block adds a second quantity of the same kind, and it is the
one that answers the block's whole question:

```
80036d50 T clockevents_handle_noop      <- ce_handler BEFORE the handover
80036fc4 T tick_handle_periodic         <- ce_handler AFTER  it
```

Both from `r53b1.System.map`, both re-derived by `cardcheck numbers` from that
file. The driver prints `ce_handler=%08lX` out of its own
`clock_event_device.event_handler`. **A capture reading `80036FC4` is the tick
core having installed its periodic handler on my device**, and there is no
other code path in this kernel that writes that field.

---

## 2. The three power cycles, and what each one is the only one that can do

🔴 **The handover is one-way inside a boot.** 讀 `kernel/time/tick-common.c`:
`tick_cpu_device` is a static per-cpu variable and `tick_device_lock` a static
spinlock, neither exported, and `clockevents.c` has no unregister. So a
clockevent that stops delivering is a board whose `jiffies` has stopped, and
`R4`'s scripted reset cannot help — `J BFC00000` is a **loader** command and
there is no loader prompt under Linux. **Recovery is the operator's hand on the
power.**

That is why the block is three cycles and not one, and each has a reason that
is not "be careful":

| cycle | what only it can do |
|---|---|
| **PC1** | `NET-14` needs a **cold** boot with `eth0` never touched — a warm one carries the previous boot's interface state, which is the confound. And it is the first handover, so everything after `CE-7` is at risk. |
| **PC2** | the long measurement **after** a handover already known to work. Running it on PC1 would mean designing a 10-minute cell whose first 30 seconds decide whether the rest exists. |
| **PC3** | reserve, and it is not slack: `n = 1` is not a result. PC3 repeats the handover from a cold boot, and if PC1 and PC2 both completed it takes the loader-side cells instead. |

---

## 3. Before power

1. `usbipd list`, attach, and **re-read the listing** — 量 2026-08-29, a
   deliberate detach and a real drop are indistinguishable in one reading.
2. a 3-second capture with the board **off**: 0 bytes, which separates the
   adapter, the port and the board before a cycle is spent.
3. `sha256sum` the image and compare with §1. The board is not powered yet.
4. every capture command below uses `/usr/bin/python3`, never `python3`.

---

## 4. The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
`OUT` = `--out bench/2026-09-06/`. Every row carries a terminator. 🔴 **Rows
containing `sleep` use `--seconds` ALONE** — a `sleep` on the board is silence
and `--idle` would cut the capture inside the cell.

🔴 **The first draft of this card had two `--send` strings over 128 bytes**
(`P2-1` at 175, `P2-2` at 165) **and a sentence claiming the longest was 104.**
`console-capture.py` refuses at 128 and both cells would have been refused at
the bench. They are split below, and the claim is now a `cardnum` row
(`send-over-127 = 0`) re-derived from this file rather than a sentence: 量,
the longest is `NB-2` at **106**. No `$` appears in any `--send`.

🔴 **And the guard's first version broke the OTHER checker.** `cardcheck
commands` finds cells with the regex `--send\s+'([^']*)'`, so a `cardnum`
row that spelled `--send '` literally was read as a cell typing `[^`. The
row now writes `-{2}send`, which `re` compiles to the same thing and a
scanner reading this file as text does not see. **A checker that is visible
to another checker is a population error**, and it is the same shape as
`CLAUDE.md`'s `c-apt-ure`: a pattern matching more than it names.

### 4.1 PC1 — cold boot. `NET-14`, then the interrupt proof, then the handover

| capture | cell | typed | **precondition** | expect | 🔴 stop if |
|---|---|---|---|---|---|
| **`NB-0`** | `NET-14` | `CAP OUT NB-0 --send 'cat /proc/interrupts ; ifconfig -a' --idle 3 --seconds 20` | at a shell, **cold boot, no network command has been typed this cycle** | lines for 2/8/12/13 only — **no line 25**, which is `EX-0`'s three-state reading taken again; `eth0` and `eth4` both DOWN | a line 25 before `reqirq` → something other than this driver owns IRQ 25 and the whole block's attribution is wrong |
| **`NB-1`** | `NET-14` | `CAP OUT NB-1 --send 'ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up ; ping -c 4 10.1.1.2 ; ifconfig eth4'  --idle 4 --seconds 30` | `NB-0` shows `eth0` DOWN | 推 **the seating-12 failure reproduces**: `TX` non-zero, `RX 0`, `LNK 0`, 100 % packet loss | 4/4 replies → **`NET-14` does not reproduce, and the finding is that it was not deterministic.** Record and go on; the isolation below then has nothing to isolate |
| **`NB-2`** | `NET-14` | `CAP OUT NB-2 --send 'ifconfig eth4 down ; ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up ; ping -c 4 10.1.1.2 ; ifconfig eth4' --idle 4 --seconds 30` | `NB-1` failed, and **`eth0` has not been touched** | 🟢 4/4 → **re-opening `eth4` alone is sufficient and `eth0` is excluded.** `NET-14` becomes a one-variable statement | still 0 replies → the `eth4` re-open is **not** sufficient, so seating 12's recovery needed the `eth0` leg. That is the other half of the same isolation and it is equally a result |
| **`CE-0`** | baseline | `CAP OUT CE-0 --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20` | any | `driver=rtl819x-timer 3.0`, `state=idle`, `mode=cs`, `ce_reload=2000`, `ce_reload_hz=2000`, `ce_reload_exact=1`, `ce_rating=300`, `ce_registered=0`, `ce_probe_registered=0`, `ce_live=0`, `ce_mode=-1`, `ce_mode_calls=0`, `ce_next_calls=0`, `ce_badmode=0`, **`ce_handler=80036D50`**, `ce_handler_is_noop=1`, `irq_preacked=0`, and 🆕 **`period_jiffies=67108`** — `(2^27 x 100) / 200000` in integer arithmetic, derived at init so that the very first dump describes the period the driver is configured for rather than two zeros | `ce_reload_exact=0` → `hz_used` does not divide by `HZ` and every later cell is void. `ce_handler` ≠ `80036D50` → the image is not the one §1 names |
| **`CS-1`** | `I1` | `CAP OUT CS-1 --send 'echo period 8 > /proc/rtl819x-timer ; echo arm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 25` | `CE-0` read `gimr_tc1ie=0` and `tc0_undisturbed=1` | `state=armed`, `last_verdict=0`, `mode=cs`, `mask_bits=8`, `period_cycles=256`, `tccnr=F0000000`, `tc0_undisturbed=1`, `arm_delta_100us` in **18…24** | `-EIO` or `tc0_undisturbed=0` → disarm, end the block |
| **`CS-2`** | `I2` | `CAP OUT CS-2 --send 'echo armirq > /proc/rtl819x-timer ; sleep 3 ; cat /proc/rtl819x-timer' --seconds 30` | `CS-1` returned `state=armed` | `tcir_tc1ie=1`, `tc1ie_ours=1`, and 🟢 **`tcir_tc1ip=1`** — 87.20 % duty at this period, 量 seating 12 `EX-2`/`EX-3` | `tcir_tc1ip=0` → §5.1's phase argument is wrong at 2⁸ as well as at 2¹¹, and `CS-3` has nothing to clear |
| **`CS-3`** | `I3` | `CAP OUT CS-3 --send 'echo ackip > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `CS-2` read `tcir_tc1ip=1` | `ackip_before=1`, `ackip_after=0`, **`ack_proven=1`** | `ackip_after=1` → `TC1IP` is not write-1-to-clear, D Table 25 is refuted, and `cevt` will refuse. **End the block; that is a complete result** |
| **`CS-4`** | unwind | `CAP OUT CS-4 --send 'echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `CS-3` read `ack_proven=1` | `state=idle`, `tc1ie_ours=0`, `tccnr` = `tccnr_at_init` = `C0000000`, `tcir` = `tcir_at_init` = `80000000`, and **`ack_proven` still 1** — it is not reset by disarm, which is what lets `CE-3` use it. 🆕 **`mask_bits=8` beside `period_jiffies=0`**, not 524: `notes/timer-driver.md` § 11.6 6, fixed in 3.0. **The 0 is correct and is why `tc1_ext_trusted` reads 0 at this period** — `256 x 100 / 200000` truncates, and § 11.6 5 recorded that guard firing before the field followed it | `ack_proven=0` → the flag is reset somewhere and `CE-3` will refuse; that is a driver defect and the block stops |
| **`CE-1`** | mode | `CAP OUT CE-1 --send 'echo mode ce > /proc/rtl819x-timer ; echo arm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 25` | `CS-4` returned `state=idle` | `mode=ce`, `state=armed`, **`period_cycles=2000`**, **`tc1data=00007D00`** — byte-identical to `tc0data`, and that is the point — `period_jiffies=1`, `tccnr=F0000000`, and every `tc1_ext_*` line **0** | `-ERANGE` → `ce_reload_exact` was 0. `period_cycles` ≠ 2000 → `rtl819x_tc1_reload()` did not follow the mode |
| **`CE-2`** | `I2` | `CAP OUT CE-2 --send 'echo armirq > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `CE-1` returned `state=armed` | `tcir_tc1ie=1`, `tc1ie_ours=1`, `gimr_tc1ie=0` | `gimr_tc1ie=1` here → something else moved it; disarm and stop |
| **`CE-3`** | `I4` | `CAP OUT CE-3 --send 'echo reqirq > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `CE-2` returned `tcir_tc1ie=1` and `CS-3` returned `ack_proven=1` | `last_verdict=0`, `irq_requested=1`, 🔴 **`gimr_tc1ie=1`** — set by `bsp_ictl_irq_unmask` through `request_irq`, never by this driver | `-EPERM` → `ack_proven` was 0, which is the guard working and not a failure |
| **`CE-4`** | pre-check | `CAP OUT CE-4 --send 'sleep 8 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 40` | `CE-3` returned `irq_requested=1` | 🟢 `irq_count` **≈ 800** (8 s at 100 Hz), `irq_spurious=0`, `irq_stuck=0`, a line **25** in `/proc/interrupts`, and `irq_preacked` — see §5.2, **the number this cell exists for** | `irq_count=0` with the board alive → the interrupt does not arrive at this period and the handover must not be attempted. **`irq_stuck` ≥ 1 → the guard fired; stop** |
| **`CE-5`** | 🟢 **negative control** | `CAP OUT CE-5 --send 'echo cevtprobe > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `CE-4` returned `irq_count` > 0 | `last_verdict=0`, `ce_probe_registered=1`, and 🔴 **`ce_probe_mode_calls=0`, `ce_probe_mode=-1`, `ce_live=0`, `ce_handler=80036D50`** — a registration the core declined | `ce_probe_mode_calls` > 0 → the core took a rating-**99** device over the vendor's 100, and `tick_check_new_device`'s inequality does not mean what §5.3 says. **The board is now running on a clockevent whose `set_mode` is real, so it is not wedged — but stop and record** |
| **`CE-6`** | rating | `CAP OUT CE-6 --send 'echo rating 300 > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `CE-5` returned `ce_live=0` | `last_verdict=0`, `ce_rating=300` | `-EBUSY` → the real device is already registered, which contradicts `CE-0` |
| **`CE-7`** | 🔴 **THE HANDOVER** | `CAP OUT CE-7 --send 'echo cevt > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 5 --seconds 30` | `CE-6` returned `ce_rating=300`; `CE-5` returned `ce_probe_mode_calls=0` | 🟢 `last_verdict=0`, `ce_registered=1`, **`ce_mode=2`**, **`ce_mode_calls=2`**, **`ce_live=1`**, **`ce_handler=80036FC4`**, `ce_handler_is_noop=0`, `ce_hw_bad=0`, `ce_next_calls=0`, `ce_badmode=0`, `ce_check_dj` ≥ 300, `ce_check_dc` within 1 % of it | `-ETIME` → the pre-check refused; read `ce_check_dc`/`ce_check_dj` and **stop, the guard did its job**. **No output at all → the board is wedged: power-cycle, and PC2 starts at `CE-0`** |
| **`CE-8`** | alive | `CAP OUT CE-8 --send 'sleep 10 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 45` | `CE-7` returned `ce_live=1` | 🟢 the board answers at all, `Δjiffies` ≈ 1000 across `CE-7`→`CE-8`, line 25 rising, `irq_stuck=0`, `ce_hw_bad=0`. **§5.4 is the arithmetic** | silence → wedged after the handover; power-cycle |
| **`CE-9`** | 🟢 **the causal test** | `CAP OUT CE-9 --send 'echo cereload 4000 > /proc/rtl819x-timer ; cat /proc/rtl819x-timer ; sleep 5 ; cat /proc/rtl819x-timer' --seconds 45` | `CE-8` showed the board alive | `ce_reload=4000`, `ce_reload_hz=2000`, `ce_reload_writes=1`, and between the two dumps: **`Δwall` ≈ 5.0 s, `Δjiffies` ≈ 500, `Δce_cycles` ≈ 2,000,000** — §5.5, where the last one says the real elapsed time was **10 s** | `Δce_cycles / 200000` ≈ `Δwall` → the reload did not take effect, and `cereload` writes a register the hardware ignores mid-period |
| **`CE-10`** | restore | `CAP OUT CE-10 --send 'echo cereload 2000 > /proc/rtl819x-timer ; cat /proc/rtl819x-timer ; sleep 5 ; cat /proc/rtl819x-timer' --seconds 45` | `CE-9` completed | `ce_reload=2000`, `ce_reload_writes=2`, and the ratio in §5.5 back to **1.00** | the ratio not returning → the effect is not the reload |
| **`CE-11`** | one-way | `CAP OUT CE-11 --send 'echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | any | 🔴 **`last_verdict=-16`** (`-EBUSY`), `state=armed` still, `ce_live=1` — **the refusal is the deliverable**, not a failure | `last_verdict=0` → `disarm` ran under a registered clockevent, the tick source is gone, and the board is about to stop. **This is the one cell whose success would be the bad outcome** |
| **`CE-12`** | the NIC | `CAP OUT CE-12 --send 'ping -c 4 10.1.1.2 ; cat /proc/interrupts' --idle 4 --seconds 30` | `NB-1` or `NB-2` left `eth4` up and pinging | 4/4, and line 25 still rising. **A network stack whose every timeout is in `jiffies`, running on my tick** | loss → a finding about the tick under load; keep the capture and the host-side one |

### 4.2 PC2 — the handover again, and the long measurement

Runs after a power cycle. `NET-14`'s cells do **not** repeat: they are spent.

| capture | cell | typed | expect |
|---|---|---|---|
| **`P2-0`** | baseline | `CAP OUT P2-0 --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20` | as `CE-0`, and `ce_handler=80036D50` again from a fresh boot |
| **`P2-1a`** | `I1`/`I2` | `CAP OUT P2-1a --send 'echo period 8 > /proc/rtl819x-timer ; echo arm > /proc/rtl819x-timer ; echo armirq > /proc/rtl819x-timer' --idle 4 --seconds 25` | `state=armed`, `mask_bits=8`, `tcir_tc1ie=1` |
| **`P2-1b`** | `I3` | `CAP OUT P2-1b --send 'sleep 3 ; echo ackip > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --seconds 30` | `ack_proven=1` |
| **`P2-2a`** | to `ce` | `CAP OUT P2-2a --send 'echo disarm > /proc/rtl819x-timer ; echo mode ce > /proc/rtl819x-timer ; echo arm > /proc/rtl819x-timer' --idle 4 --seconds 30` | `mode=ce`, `period_cycles=2000` |
| **`P2-2b`** | `I2` | `CAP OUT P2-2b --send 'echo armirq > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `tcir_tc1ie=1`, `tc1ie_ours=1` |
| **`P2-3`** | `I4` | `CAP OUT P2-3 --send 'echo reqirq > /proc/rtl819x-timer ; sleep 8 ; cat /proc/rtl819x-timer' --seconds 40` | `irq_count` ≈ 800, `gimr_tc1ie=1` |
| **`P2-4`** | control | `CAP OUT P2-4 --send 'echo cevtprobe > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `ce_probe_mode_calls=0` — **the negative control taken twice** |
| **`P2-5`** | handover | `CAP OUT P2-5 --send 'echo cevt > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 5 --seconds 30` | `ce_mode=2`, `ce_handler=80036FC4` — **n = 2** |
| **`P2-6`** | 🟢 **the long one** | `CAP OUT P2-6 --send 'sleep 240 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 300` | four minutes on my tick: `Δjiffies` ≈ 24,000, line 25 ≈ +24,000, `irq_spurious` and `irq_stuck` still **0**, `ce_hw_bad=0`, and §5.6's drift number |
| **`P2-7`** | load | `CAP OUT P2-7 --send 'ping -c 20 10.1.1.2 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 60` | 20/20, and `irq_preacked` compared against `CE-4`'s — §5.2 under traffic |
| **`P2-8`** | 3× | `CAP OUT P2-8 --send 'echo cereload 8000 > /proc/rtl819x-timer ; cat /proc/rtl819x-timer ; sleep 5 ; cat /proc/rtl819x-timer' --seconds 60` | ratio **4.00**, not 2.00 — §5.5 is a slope if it has two points |
| **`P2-9`** | restore | `CAP OUT P2-9 --send 'echo cereload 2000 > /proc/rtl819x-timer ; cat /proc/rtl819x-timer ; sleep 5 ; cat /proc/rtl819x-timer' --seconds 45` | ratio 1.00 |

### 4.3 PC3 — reserve, and what it does if nothing was lost

| capture | cell | typed | expect |
|---|---|---|---|
| **`P3-L`** | free, loader | `CAP OUT P3-L --send 'DW B8003008 4' --idle 2 --seconds 8` | at the loader prompt: `IRR0`–`IRR3` as the loader left them. `REG-03` predicts `IRR1` = `30050004`; a third reading of it |
| **`P3-0`** | third handover | as `P2-0`…`P2-5` (with `P2-1`/`P2-2` split the same way), capture names `P3-0`…`P3-5` | **n = 3**, and `ce_handler=80036FC4` on a third independent boot |
| **`P3-6`** | 🔴 the destructive one, **last** | `CAP OUT P3-6 --send 'echo cereload 20000 > /proc/rtl819x-timer ; cat /proc/rtl819x-timer ; sleep 5 ; cat /proc/rtl819x-timer' --seconds 180` | the extreme of §5.5: **10 Hz**, ratio 10.00. Every kernel timeout runs ten times slow; the shell still answers. **This is the last cell of the seating** |

---

## 5. Predictions, with refutation conditions

### 5.1 🔴 Why `I2`/`I3` are proved at period 2⁸ and not at the clockevent's own period

`SPEC.md` `IRQ-09`: the vendor's `bsp_timer_ack()` is `REG32(BSP_TCIR) |=
BSP_TC0IP`, a read-modify-write on a register whose `IP` bits are
write-1-to-clear, run every 10 ms. So `TC1IP` is erased 100 times a second by
code that has never heard of this driver.

**In clockevent mode my period is also 10 ms, and that makes the flag's
visibility a CONSTANT rather than a probability.** TC1 wraps at some fixed
phase φ inside the vendor's tick, so `TC1IP` is up for `(10 ms − φ)` of every
10 ms — and φ is decided by when `arm` ran and does not drift, because both
timers divide the same `CDBR`. Sampling five times in a row would sample the
same φ five times. At period 2⁸ (1.28 ms) the duty cycle is **87.20 %**,
量 seating 12, and `ackip` is a near-certainty.

🟢 **And the proof transfers.** `ackip` establishes that writing 1 to `TCIR`
bit 28 clears it — a property of the register, not of the period. `reqirq`'s
refusal exists because a handler that cannot clear its own pending bit loops
the board through `handle_level_irq`'s unmask; that is equally true at either
period.

⚠️ **What is NOT established by this route**: that `TC1IP` is *observable* at
the clockevent's period. `CE-4`'s `irq_preacked` measures the consequence
instead, which is the thing that actually matters.

### 5.2 🟢 `irq_preacked` is a number this project has never had

New in 3.0 and separated from `irq_spurious` on purpose. It counts ISR entries
that found `TC1IP` already clear — which under `IRQ-09` has a cause that has
nothing to do with ownership. In clockevent mode the ISR does **not** return
`IRQ_NONE` on it: 讀 `arch/rlx/bsp/irq.c`, `bsp_ictl_irq_dispatch()` reaches
`do_IRQ(BSP_TC1_IRQ)` only when `GIMR & GISR` has bit 9 set, so the dispatcher
has already proved the interrupt is TC1's and the `TCIR` read is a second,
weaker witness. Dropping a system tick to honour it would be a bug.

**Prediction, written before the cell**: seating 12 measured `irq_spurious = 0`
in 119,818 deliveries at 781 Hz and 48.8 Hz. At 100 Hz, with my wrap and the
vendor's ack at the *same* rate and a fixed phase, the collision is either
never or always. So `irq_preacked` after `CE-4` is 推 **either ≈ 0 or ≈
`irq_count`** — and a value in between would refute the fixed-phase model in
§5.1. **All three outcomes are readings.**

### 5.3 The three source facts the handover rests on, and where each is written

讀 `kernel/time/tick-common.c` and `kernel/time/clockevents.c`, 2.6.30, from
the drop this image was built from:

| | |
|---|---|
| `tick_check_new_device()` keeps the incumbent unless `curdev->rating >= newdev->rating` is false | so 300 takes over from 100, and **99 cannot** — that is `CE-5` |
| `tick_setup_device()` sets the **old** device's `event_handler` to `clockevents_handle_noop` | so the vendor's TC0 interrupt keeps firing at 100 Hz, keeps petting the watchdog (`CONFIG_RTL_WTDOG=y`), keeps running `bsp_timer_ack()`, and stops advancing `jiffies`. **Nothing double-counts and nothing stops** |
| `clockevents_exchange_device()` shuts the new device down, then `tick_setup_periodic()` starts it | two `set_mode` calls, SHUTDOWN then PERIODIC, which is why `CE-7` predicts `ce_mode_calls=2` and not 1 |

The vendor's own side, 讀 `arch/rlx/kernel/rlx-cevt.c`: `cd->rating = 100`
(line 234) and `.features = CLOCK_EVT_FEAT_PERIODIC` (line 140) — one flag,
and `set_mode`/`set_next_event` are stubs that return immediately. Both are
re-derived by `cardcheck numbers` from that file.

### 5.4 🔴 `Δjiffies == Δ(line 25)` is NOT evidence, and this block says so before it runs

My tick is 100 Hz. The vendor's is 100 Hz. After the handover **both**
`/proc/interrupts` lines advance at ≈ 100 per second and both match `Δjiffies`
— so the obvious reading proves nothing at all, and a card that quoted it
would be quoting a tautology.

**What does distinguish them**, in increasing order of independence:

1. `ce_mode=2` and `ce_mode_calls=2` — the tick core called *my* `set_mode`.
   Kernel state, read through my own driver.
2. **`ce_handler=80036FC4`** — the core installed `tick_handle_periodic` on
   *my* `clock_event_device`. Same kind of evidence, but the value comes from
   this build's `System.map` and cannot be produced by any other write in the
   image.
3. **§5.5** — the causal one, and the only one that does not ask the kernel
   about itself.

### 5.5 🟢 The causal test: make my timer wrong and watch the clock follow

`cereload 4000` doubles TC1's period. If the tick is mine, the kernel now gets
50 interrupts a second while still believing `HZ = 100`, so **every kernel
clock runs at half speed** and nothing in the kernel can notice.

Two references, and neither is the kernel's own clock:

* **on the board**: `ce_cycles` accumulates `reload` per delivered interrupt,
  i.e. real TC1 counts. `Δce_cycles / hz_used` is elapsed **real** seconds.
  `Δwall` is elapsed **kernel** seconds. Their ratio is the error.
* **off the board**: the capture's `.timing` file, host-side. ⚠️ `R5-2` found
  the host timing disagreeing with itself by 17× its own floor, so it is
  useless at ppm — and this effect is **2×**, six orders of magnitude above
  that floor.

| cell | `reload` | `Δwall` | `Δjiffies` | `Δce_cycles` | `Δce_cycles / 200000 / Δwall` |
|---|---|---|---|---|---|
| `CE-8` (before) | 2000 | ≈ 10 s | ≈ 1000 | — | **1.00** |
| `CE-9` | 4000 | ≈ 5 s | ≈ 500 | ≈ 2,000,000 | **2.00** |
| `CE-10` | 2000 | ≈ 5 s | ≈ 500 | ≈ 1,000,000 | **1.00** |
| `P2-8` | 8000 | ≈ 5 s | ≈ 500 | ≈ 4,000,000 | **4.00** |
| `P3-6` | 20000 | ≈ 5 s | ≈ 500 | ≈ 10,000,000 | **10.00** |

🔴 **Refuted by** a ratio that stays at 1.00 after `cereload`: then either the
reload write does nothing (a finding about `TC1DATA`) or the tick is not mine
(a finding about the handover) — and `ce_handler` says which.

⚠️ **Not a frequency measurement.** `Δwall` is quantised at one jiffy because
`CONFIG_GENERIC_TIME=y` selects `clocksource_jiffies` (`CLK-20`, `CLK-21`), so
each row carries ±1 % at these lengths. Five rows spanning 1× to 10× is a
slope; no single row is worth quoting alone.

### 5.6 The four-minute cell, and what it can and cannot show

`P2-6` is 240 s under my tick. It shows the board still answering and
`irq_stuck` still 0. **It does not measure frequency** — `Δjiffies` and
`Δirq_count` are the same clock counted twice, and the only independent
reference at that length is the host `.timing`, whose floor §5.5 already
states. What it can bound is **lost ticks**: `Δce_cycles / 2000` is how many
periods TC1 actually completed and `Δjiffies` is how many the kernel counted.
Their difference is ticks the kernel did not get, which is the quantity §5.1's
`IRQ-09` hazard would produce if it produced anything.

推 the difference is **0**. Refuted by any non-zero value, which would be the
first measurement of interrupt loss on this part.

---

## 6. Abort conditions for the block as a whole

1. 🔴 **`irq_stuck` ≥ 1 at any point** → the ISR's clear did not take, the
   guard has disabled line 25, and after `CE-7` that means the tick is gone.
   Stop; the capture is the result.
2. 🔴 **`CE-5` shows `ce_probe_mode_calls` > 0** → the core's inequality does
   not mean what §5.3 says. Do not run `CE-7`.
3. 🔴 **`CE-7` produces no output** → wedged. Power-cycle. PC2 begins.
4. 🔴 **`tc0_undisturbed=0` anywhere** → this driver has touched the vendor's
   timer bits. Stop the block, whatever else is pending.
5. **No flash-write command may be typed.** No `EW`, `EB`, `FLW`, `FLR` or
   burn appears anywhere above; `AUTOBURN` is not read because nothing is
   uploaded after the first boot of each cycle.

---

## 7. What this block cannot tell you, stated before it runs

* **It is not `R5-3b`'s DoD.** That DoD is *the board boots with my timer as
  the system time base, ten times*. Every handover here is from a `/proc`
  write on a board that already reached a shell. Boot-time arming is
  `R5-3b-2`, it needs a different image, and building that image before this
  block runs would be building on an assumption.
* **It says nothing about a clocksource.** `mode ce` unregisters nothing and
  registers nothing on that side; `tc1_ext_*` reads 0 throughout and the
  reason is in the driver's header, not in the numbers.
* **It cannot see a handover that works for four minutes and fails at forty.**
  `P2-6` is the longest window in the block and it is 240 s.
* **`ce_handler` is read through the driver's own `/proc`.** A driver that
  printed a constant would produce the same line. What makes it evidence is
  that `CE-0` prints the *other* address from the same code path on the same
  boot — the pair is the reading, not either half.
* **The `>=` boundary itself is untested.** `CE-5` runs a rating strictly
  below the vendor's (99 < 100) because a control that depends on reading one
  comparison operator correctly is weaker than one decided by arithmetic. A
  tie at exactly 100 is never registered by this block.

---

## 8. The machine-readable halves

Both fences are read by `tools/cardcheck.py`. Every number is re-derived from a
file on disk; nothing here is typed twice.

```cardnum
img-bytes	1033216	size /home/key/fwre-work/rebuild/bench-only/r53b1-20260906/rlxfw-r53b1-20260906.bin
img-sha16	e160089ae8ea5952	sha256-16 /home/key/fwre-work/rebuild/bench-only/r53b1-20260906/rlxfw-r53b1-20260906.bin
vmlinux-bytes	3975506	size /home/key/fwre-work/rebuild/r3-4/out/r53b1.vmlinux.elf
vmlinux-sha16	e9fcf3d52767c32e	sha256-16 /home/key/fwre-work/rebuild/r3-4/out/r53b1.vmlinux.elf
prev-img-sha16	b1273e55552603bf	sha256-16 /home/key/fwre-work/rebuild/bench-only/r53b-20260904/rlxfw-r53b-20260904.bin
drv-lines	2384	lines config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c
proc-lines	91	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c scnprintf
drv-verbs	9	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c strcmp\(buf,
map-noop	1	count /home/key/fwre-work/rebuild/r3-4/out/r53b1.System.map ^80036d50 T clockevents_handle_noop$
map-tick	1	count /home/key/fwre-work/rebuild/r3-4/out/r53b1.System.map ^80036fc4 T tick_handle_periodic$
vendor-rating-100	1	count /home/key/fwre-work/rebuild/src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/kernel/rlx-cevt.c cd->rating = 100;
vendor-periodic-only	1	count /home/key/fwre-work/rebuild/src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/kernel/rlx-cevt.c CLOCK_EVT_FEAT_PERIODIC,$
ce-rating-dflt	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_RATING_DFLT\s+300$
ce-rating-probe	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_RATING_PROBE\s+99$
ce-min-j	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_MIN_J\s+300$
ce-tol-permille	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_TOL_PERMILLE\s+10$
send-over-127	0	count bench/2026-09-06/PREDICTIONS-B11-block10.md -{2}send '[^']{128,}'
```

```cells
bench/2026-09-06/NB-0
bench/2026-09-06/NB-1
bench/2026-09-06/NB-2
bench/2026-09-06/CE-0
bench/2026-09-06/CS-1
bench/2026-09-06/CS-2
bench/2026-09-06/CS-3
bench/2026-09-06/CS-4
bench/2026-09-06/CE-1
bench/2026-09-06/CE-2
bench/2026-09-06/CE-3
bench/2026-09-06/CE-4
bench/2026-09-06/CE-5
bench/2026-09-06/CE-6
bench/2026-09-06/CE-7
bench/2026-09-06/CE-8
bench/2026-09-06/CE-9
bench/2026-09-06/CE-10
bench/2026-09-06/CE-11
bench/2026-09-06/CE-12
bench/2026-09-06/P2-0
bench/2026-09-06/P2-1a
bench/2026-09-06/P2-1b
bench/2026-09-06/P2-2a
bench/2026-09-06/P2-2b
bench/2026-09-06/P2-3
bench/2026-09-06/P2-4
bench/2026-09-06/P2-5
bench/2026-09-06/P2-6
bench/2026-09-06/P2-7
bench/2026-09-06/P2-8
bench/2026-09-06/P2-9
```
