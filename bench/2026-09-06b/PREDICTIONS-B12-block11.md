# Block 11 — `R5-3b-2`: the tick is armed at boot, ten times

Seating 14, 2026-09-06 (the second seating of this calendar day; seating 13 is
`bench/2026-09-06/`). Gate `R5`, step `R5-3b-2`, the seventh of fourteen.

**Zero flash-write commands. Zero `FLR`.** Nothing in this card can issue one:
`cardcheck commands` reports the loader verbs it types, and the bracket stays at
**1,024 / 4,194,304 = 0.0244 %**.

---

## 0. What this block is, in one paragraph

`R5-3b-1` handed the system tick to `rtl819x-timer` from a `/proc` write, three
times, on three cold boots (seating 13). That handover happened **after
userspace existed**, by hand. This block does the same handover from inside the
kernel, before `/sbin/init` is executed, and asks whether it survives being
repeated. The driver did not gain a second implementation of anything: a
sequencer calls the same functions the `/proc` verbs call, in the order seating
13 typed them. What is new is a retry, a wait, an unwind — and ten marks that
go out through `prom_putchar`, so a boot that never reaches a shell still says
where it stopped.

---

## 1. The image, staged and pinned

| | |
|---|---|
| file | `$FWRE_WORK/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin` |
| bytes | **1,034,240** |
| sha256 | `23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5` |
| `RECIPE_ID` | **`0a3135af`** — the board must print `RLXFW-ID0=0A3135AF` |
| driver | `rtl819x-timer` **4.0** (3.0 was seating 13's, 2.0 seating 12's, 1.0 seating 11's) |
| `vmlinux` | 3,976,095 bytes, sha256 `2730a7321ba4a357…` |
| initramfs spec | `f1cee4484bc3da30…`, **byte-identical to seating 13's**, and REGENERATED from `config/rlxfw-initramfs.tsv` rather than copied |
| recipe | `--variant quiet`, `--marks`, `--jobs 4`, declared cflags and stamp — identical to `r53b1`'s manifest in every field but the driver source |

The previous image is `rlxfw-r53b1-20260906.bin`, 1,033,216 bytes,
`e160089ae8ea5952…`. **It is the recovery path**: if a boot with this image
wedges before a shell, the next cycle uploads that one instead, and the board
comes up on the vendor's tick with the `/proc` route available. Nothing here is
in flash — every boot is a TFTP upload into RAM — so a wedge costs exactly one
power cycle and can cost nothing else.

### 1.1 What the desk already proved about this image, before power

Four checks, all on the built artefact rather than on the tree:

1. **The ten mark strings are in the image**, each exactly once:
   `strings -a r53b2.vmlinux.elf | grep -c 'RLXFW-TA<n>='` → `1`, for `TA0`…`TA9`.
2. **The sequencer survived optimisation.** `rtl819x_boot_arm_early` is *not* a
   symbol — gcc inlined it into `rtl819x_timer_init` — so `strings` alone would
   not have settled it. Disassembled and resolved against this build's own
   `System.map`, `rtl819x_timer_init` calls `rlxfw_puts_hex` **5×**,
   `rtl819x_tc1_arm` 2×, `rtl819x_tc1_armirq` 2×, `rtl819x_tc1_disarm` 2×,
   and `set_period` / `ackip` / `set_mode_verb` / `reqirq` / `__udelay` once
   each; `rtl819x_boot_arm_late` calls `rlxfw_puts_hex` 5×, `get_jiffies_64`
   5×, `rtl819x_tc1_cevt_register` **2×** and `msleep` once. Every count
   matches the source.
3. **The diff is exactly the sequencer.** The same slice taken on seating 13's
   `r53b1` image lists five calls — `__div64_32` ×2, `clockevent_delta2ns` ×2,
   `rtl819x_derive_period`, `create_proc_entry`, `init_timer_key`. `r53b2` has
   all five unchanged plus the fifteen above. The difference contains no
   removals.
4. **Both initcalls are in the table**: `__initcall_rtl819x_timer_init3`
   (`arch_initcall`, level 3) and `__initcall_rtl819x_boot_arm_late7`
   (`late_initcall`, level 7), in `.initcall.init`.

⚠️ **A control caught a defect in check 2's own tooling.** The first run
resolved one call target to `update_curr_rt`; it is `init_timer_key`. `awk`
parses an address like `8001e714` as **scientific notation** — 8001×10⁷¹⁴ →
`inf` — so a numeric `$1 == t` made every such address equal to every other.
The comparison is `$1 "" == t ""` now. It was found by running the same slice
on the previous image and asking why a call neither version should have made
appeared in both.

### 1.2 The two addresses, out of this build, and nobody types them

`clockevents_handle_noop` = **`80036D50`**, `tick_handle_periodic` =
**`80036FC4`**. Both are `count` rows in the `cardnum` fence, re-derived from
`r53b2.System.map`. They are the same values seating 13 read — the symbols sit
in `kernel/time/`, which links before `drivers/`, so the 335 lines this
step added to the driver (2,384 → 2,719) did not move them. **That they did not move is a reading, not an
assumption**: the fence checks this build's map, not seating 13's.

---

## 2. The ten boots, and the branch that decides the seating's shape

The DoD is `R5-3b`'s, unchanged: *the board boots with my timer as the system
time base, ten times, no oops.*

Each boot is: **a reset to the loader prompt**, then
`looprun --mode bench --skip S2,S3,S4`, then one `/proc` read. The reset is the
only part that differs, and it is the whole cost question:

| reset | how | cost |
|---|---|---|
| **cold** | the operator presses power inside an open ESC window | ~200 s of window plus a message round-trip, **per boot** |
| **warm** | `busybox reboot` typed into the shell of the boot before it | ~30 s, **no operator** |

🔴 **`busybox reboot` and not `reboot`.** This image declares **eleven**
busybox symlinks — `sh ash cat echo ls mount ps ifconfig ping mkdir sleep` —
and `reboot` is not one of them, even though the applet is in the binary
(`notes/rootfs-census.md`: the vendor rootfs has fifty symlinks and `reboot` is
among them). That is exactly the population confusion `cardcheck commands`
exists for, and it would have cost a cell at the bench.

### 2.1 🔴 The branch, and both outcomes are results

`K2-A` is the decision cell. It types `busybox reboot` into `K1`'s shell.

* **It reaches `<RealTek>`** → boots 2…10 are warm, the seating needs **one**
  power press, and `NET-25` gets one sample instead of ten.
* **It does not** → boots 2…10 are cold, ten power presses, and `NET-25` gets
  ten cold first-opens. The reason it did not is itself recorded: no reset at
  all (the applet is not in this binary, or `machine_restart` does nothing),
  or a reset that ran past the ESC window.

🔴 **And there is a second question inside the first one, which is the reason a
warm boot is not merely cheaper.** `rtl819x_tc1_arm()` refuses with `-EBUSY`
when it finds `TCCNR`'s `TC1En` already set. On a **cold** boot that bit is
clear — 量 `SPEC.md` `REG-06/08/09`, `TCCNR = 0xC0000000` at the loader
prompt. On a **warm** boot the previous boot left TC1 running, and whether a
watchdog reset clears the timer block has never been measured on this part.

推, and marked as inference: a watchdog reset resets the peripheral block, so
`tccnr_at_init` reads `C0000000` and `RLXFW-TA1=00000000`.

**Refutation**: `RLXFW-TA1=FFFFFFF0` (`-EBUSY`) with `tccnr_at_init=F0000000`.
🟢 That outcome is not a failure of the driver — it is a **new reading about
this silicon**, self-evidencing in two places at once, and the board still
boots on the vendor's tick because the sequencer's failure path is soft. It
would mean warm boots do not count toward the ten and the rest must be cold.

### 2.2 What makes a boot count

A boot counts toward the ten if **all** of:

1. `Kn-boot.log` holds the eleven `RLXFW-B00`…`B10` marks in order;
2. it holds `RLXFW-ID0=0A3135AF`;
3. it holds `TA0`…`TA9` with **`TA1`=`TA3`=`TA4`=`TA7`=`TA8`=`00000000`** and
   **`TA9`=`00000003`**;
4. 🟢 **`TA8` occurs before `B10` in the same capture** — see §5.1;
5. the capture ends at a `#` prompt;
6. `Kn-P` reads `boot_done=1`, `boot_rc=0`, `ce_live=1`, `ce_mode=2`,
   `ce_mode_calls=2`, `ce_probe_registered=1`, `ce_probe_mode_calls=0`,
   `irq_stuck=0`, `irq_spurious=0`, `ce_hw_bad=0`, `ce_badmode=0`.

A boot that fails any of these is **recorded and does not count**. The count is
not reset by a failure; the failure is a finding and the ten are ten
successes. If two boots fail **at the same stage**, the block stops and goes
back to the desk — a repeated failure is a defect, not noise.

### 2.3 🔴 "No oops" is measurable here, and the instrument's liveness is free

`CONFIG_PRINTK` is not set in this build, so "no oops text" would normally be
an instrument that cannot fail. 讀 the vendor tree: `arch/rlx/kernel/traps.c:52`
and `kernel/panic.c:27` both carry `#define printk panic_printk`, so every
`printk` inside `die()`, `show_registers()` and `panic()` is
`panic_printk` — which is real in this configuration and reaches the wire once
a console is registered.

🟢 **The positive control is in every boot capture at no cost**: the fifteen
vendor lines between `B09` and `B10` (`Realtek WLAN driver driver version 1.6`,
`chip name: 8196C`, `Realtek FastPath:v1.03`) are `panic_printk` output. If
they are present, the channel an oops would use is up. **Absence of oops text
is evidence only in a capture that contains those lines**, and the DoD row
below says so.

---

## 3. Before power

1. `usbipd list`, attach **both** devices, and **re-read the listing** — 量
   2026-08-29, a deliberate detach and a real drop are indistinguishable in one
   reading. 量 today: CP2102 `1-1`, USB GbE **`2-4`** — seating 13 read `3-4`
   and `RUNSHEET` records `2-4`, so this is its third value and the re-read is
   why it is right.
2. a long-lived WSL process must be running, or `usbipd attach` has nothing to
   attach to. 量 today: `sleep 36000`, PID 316.
3. host NIC at `10.1.1.2/24` on the USB GbE; with the board **off**,
   `Link detected: no` is the correct control.
4. a 3-second capture with the board **off**: **0 bytes**, which separates the
   adapter, the port and the board before a cycle is spent.
5. `sha256sum` the image and compare with §1. The board is not powered yet.
6. every capture command below uses `/usr/bin/python3`, never `python3` —
   量 2026-09-02, the venv on `PATH` in a login shell has no `pyserial`.
7. 🔴 **the capture is opened BEFORE the operator touches power, and the
   operator waits ten seconds after being told.** Seating 13's `PC2` lost its
   banner to the other order, and `boot-timeline` detected it independently
   (three power-ups, two `cold` rows, `SQ-A.log -- boot text but no Booting
   anchor`).

---

## 4. The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
`OUT` = `--out bench/2026-09-06b/`. Every row carries a terminator. 🔴 **Rows
containing `sleep` use `--seconds` ALONE** — a `sleep` on the board is silence
and `--idle` would cut the capture inside the cell.

`LOOP` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir
bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image
$FWRE_WORK/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin
--image-sha256 23539da9…` with `--cell Kn`.

🔴 **`--skip S2,S3` is necessary and `--skip S4` is chosen.** `S3` assembles
from the tree `S2` stages and nothing carries the path when `S2` is skipped
(`notes/dev-loop.md` §10.3). `S4` is `J BFC00000` at the loader prompt; every
reset in this card happens *before* `looprun` starts — the operator's power
press, or `busybox reboot` — so an `S4` inside the loop would be a second reset
in the same cycle and would re-stage `0x80500000` from flash again for nothing.

### 4.1 The loop, run once per boot n = 1…10

| # | capture | typed | expect | 🔴 stop if |
|---|---|---|---|---|
| **`Kn-A`** cold | `CAP OUT Kn-A --esc 150 --esc-period 0.002 --seconds 165` | the operator presses power inside the window; the loader's banner, then `<RealTek>` | no `<RealTek>`: the ESC window was missed and the board is running the **vendor** firmware from flash. Not a fault — power-cycle and repeat the cell |
| **`Kn-A`** warm | `CAP OUT Kn-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35` | the command echo, a reset, then `<RealTek>` | `busybox: applet not found` → the applet is not in this binary; every remaining boot is cold. No `<RealTek>` and no echo → the shell is gone; power-cycle |
| **`Kn-*`** | `LOOP --cell Kn` | five stages, six assertions, `A3` requires the board to print `RLXFW-ID0=0A3135AF` | `S5b` reads anything but `00000000` at `0x8040D4A0` → **nothing is uploaded**, and that guard is not skippable. `S6b`'s head words ≠ the image → abort |
| **`Kn-P`** | `CAP OUT Kn-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20` | §2.2's eleven fields | `boot_rc` ≠ 0 → read which stage; the board is on the vendor's tick and is not wedged |

### 4.2 `K1` only — the cold boot that everything else is measured against

| # | capture | typed | expect | 🔴 stop if |
|---|---|---|---|---|
| **`K1-Q`** | `CAP OUT K1-Q --send 'sleep 10 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 45` | 🟢 `Δjiffies` = `Δirq_count` = `Δce_cycles ÷ 2000`, all ≈ **1000** across `K1-P`→`K1-Q`; a line **25** `ICTL rtl819x-timer`; `irq_stuck=0` | the three not agreeing → a lost tick, and §5.3 is the arithmetic |
| **`K1-N`** | `CAP OUT K1-N --send 'ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up ; ping 10.1.1.2 ; ifconfig eth4' --idle 4 --seconds 30` | 🔴 **`NET-25`'s reproduction condition**: the first open of `eth4` after power. Seating 12 lost every packet, seating 13 got 4/4. Either is a sample | — this cell cannot fail the block; it adds one point to an unisolated phenomenon |
| **`K1-D`** | `CAP OUT K1-D --send 'echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | 🔴 **`last_verdict=-16`** (`-EBUSY`), `state=armed` still, `ce_live=1` — **the refusal is the deliverable**, now reached from a boot-time registration instead of a `/proc` one | `last_verdict=0` → `disarm` ran under a registered clockevent and the board is about to lose its clock. **This is the one cell whose success is the bad outcome** |

🔴 **No `-c` on that `ping`.** `NET-26`, 量 seating 13: this image's `ping`
ignores `-c` and always sends four — five separate requests, including
`busybox ping -c 3`, all returned four. A card that writes `-c 4` is asking for
something it will not get and the number would read as if it had been chosen.

### 4.3 `K10` only — the long one, placed last on purpose

| # | capture | typed | expect |
|---|---|---|---|
| **`K10-L`** | `CAP OUT K10-L --send 'sleep 240 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 280` | 🟢 zero lost ticks over ~240 s: `Δjiffies` = `Δirq_count` = `Δce_cycles ÷ 2000` ≈ **24,000** against `K10-P`. Seating 13's `/proc`-route figure was 25,853 over 258.53 s |

It is last so that a failure in it cannot cost the ten boots, and it is a
different question from §4.2's ten seconds: a rate that is right for 10 s and
wrong for 240 s is a drift, and only the second window can see it.

### 4.4 The expansion — one line per cell, and it is what gets typed

The table above is the RULE; this is the rule applied. It exists
because a parameterised row hides from the checker: with §4.1 alone
`cardcheck commands` saw **6 commands for 24 cells**, which is seating
13's defect (3) approached from the other side — there, cells had no
declaration; here, cells would have had no visible command.

量, cross-checked in **both** directions against this card's own
`cells` fence: **24 cells in the expansion, 24 in the fence, neither
list has an entry the other lacks.** The expansion has **33** capture
lines for those 24 cells — 24 + the 9 duplicated `-A` forms below —
and the `cardnum` row counts LINES, which is the number a `grep` of
this file can actually produce. 23 `--send` strings, longest
**80** characters, **0** at or over `console-capture.py`'s 128-byte
refusal.

🔴 **Nine cells appear twice**, `K2-A`…`K10-A`, because §2.1's branch
chooses one of two forms for each. Exactly one of each pair is run.
That is the one place the mapping is not one-to-one and it is written
here rather than left to be noticed at the bench.

```
#-- boot 1, always cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K1 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K1-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K1-Q --send 'sleep 10 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 45
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K1-N --send 'ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up ; ping 10.1.1.2 ; ifconfig eth4' --idle 4 --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K1-D --send 'echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 2: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K2-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K2-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K2 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K2-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 3: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K3-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K3-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K3 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K3-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 4: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K4-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K4-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K4 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K4-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 5: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K5-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K5-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K5 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K5-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 6: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K6-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K6-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K6 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K6-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 7: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K7-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K7-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K7 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K7-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 8: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K8-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K8-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K8 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K8-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 9: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K9-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K9-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K9 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K9-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
#-- boot 10: EXACTLY ONE of the next two, per 2.1
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K10-A --send 'busybox reboot' --esc-after 20 --esc-period 0.002 --seconds 35
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K10-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell K10 --out-dir bench/2026-09-06b --skip S2,S3,S4 --recipe-override 0a3135af --image /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin --image-sha256 23539da92c66589e8c52029a8779bc043e3805b2fbf364fec4c8c3c380b6bdc5
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K10-P --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06b/K10-L --send 'sleep 240 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 280
```

---

## 5. The arithmetic, written before the board is powered

### 5.1 🟢 The headline is two marks in one capture, and it quotes no address

`TA8` is printed the instant `clockevents_register_device()` returns. `B10` is
`rlxfw_mark("B10")` immediately before `init_post()`'s branch into
`/sbin/init`. 讀 `init/main.c`: `do_basic_setup()` runs **every** initcall level
to completion, and only then does `kernel_init` call `init_post()`.

**So `TA8` before `B10`, in one capture, is the sentence "the system tick was
this driver's before userspace existed" — proved by ordering, with no address
quoted, no question asked of the tick core, and no shell required.**

Refutation: `TA8` after `B10`, or absent.

### 5.2 🟢 `TA6` is predicted to be zero, and the prediction was derived at the desk

The pre-check needs `RTL819X_CE_MIN_J` = **300** jiffies = 3.00 s of delivered
interrupts after `reqirq`. `reqirq` happens in the early half at
`arch_initcall` (level 3); the registration happens in the late half at
`late_initcall` (level 7). What is spent in between is every level-6 driver.

量, from seating 13's own three boot captures and their `.timing` sidecars,
recomputed after the instrument defect in the note below:

| | `SP` | `SQ` | `SR` |
|---|---|---|---|
| `B09` → the vendor's first line — **levels 0–5, where `arch_initcall` sits** | **0.631 s** | 0.628 s | 0.627 s |
| the vendor's first line → `B10` — level 6, then `late_initcall` | **5.361 s** | 5.337 s | 5.327 s |
| `B09` → `B10`, every initcall | 5.991 s | 5.965 s | 5.954 s |
| `B00` → `rlxfw: init running` | 6.054 s | 6.026 s | 6.015 s |

⚠️ **The first version of this table was wrong and a control caught it.**
讀 `console-capture.py:462`: a `.timing` row is written **before** its chunk is
appended, so `offset seconds` means *a read finished at `seconds` and the bytes
it delivered begin at `offset`*. The arrival of byte *b* is therefore the row
with the **largest offset ≤ b**, and the first draft took the first offset **≥
b** — the *next* read. Normally that is a millisecond. Here it is not: there is
a 0.63 s silence a few bytes after `B09`, and on `SR` the two rules disagree by
**0.622 s**. The first draft reported *levels 1–5 = 0.006 s* and a 0.67 s
"difference between images"; both were the instrument.

🟢 **And `FW-32`'s own six landmarks were audited rather than assumed
guilty.** `notes/kernel-build.md` §17.3 documents the fragile rule, so the
question was whether the numbers in `SPEC.md` moved. 量, on
`bench/2026-08-30c/V-3` — `quietm`'s own capture: all five landmarks give the
same value to **≤ 0.001 s** under both rules, because each fell on a read
boundary. **The method is fragile and its published numbers are right**, and
both halves of that sentence are now measurements.

`quietm`'s `B09` → `B10` is **6.046 s** against this recipe's 5.954–5.991 s.
The two recipes agree to within **0.09 s** and no claim is made that the
difference is real: the images differ in the driver, in `config/`, and in the
initramfs declaration.

**What follows for `TA6`.** `reqirq` — and therefore the start of the 300-jiffy
window — happens inside the 0.63 s of levels 0–5. `late_initcall` runs after
level 6, which is **at least 5.33 s** later. 5.33 s ≫ 3.00 s, so:

* **`RLXFW-TA6=00000000`** — the late half waits for nothing.
* **`TA5` − `TA0` = 540…600** jiffies. The width is real and it is the one
  thing here nothing has measured: **where inside that 0.63 s window level 3
  actually runs**. This seating's own `.timing` will place `TA0` in it, which
  is a reading no previous boot could produce because nothing printed there.
* **`B00` → `rlxfw: init running` = 6.05…6.25 s** — the sequencer's ~35 ms plus
  ~52 ms of mark bytes at 38400 8N1, on top of 6.015–6.054.

Refutation: `TA6` > 0 means level 6 was faster than 3 s on that boot, which
contradicts three consistent measurements. **`TA6=000001F4` (500) is the
ceiling** and means jiffies stopped advancing — the one outcome that would say
the wait loop saved the boot rather than being a formality.

### 5.3 The boot capture's size is predicted exactly

Seating 13's `Kn-boot`-equivalent captures are **869 bytes, three times
identically**. `rlxfw_puts_hex` emits `RLXFW-TAn=` (10) + eight hex digits +
`\r\n` = **20 bytes**, and there are ten of them whatever their values.

**Predicted: `Kn-boot.log` = 1,069 bytes.**

Refutation: any other number. A short capture says a mark is missing; a long
one says something printed that this card did not predict.

### 5.4 🟢 The in-seating discriminator: three of the ten marks carry a run-time value

A mark is a compiled-in string, and a string proves only that the image is
mine. `TA0` and `TA5` print `jiffies`, and `TA2` prints how many `ackip` calls
it took to catch `TC1IP` at 1 — a race against the vendor's tick handler
clearing `TCIR` every 10 ms.

**A constant cannot vary across boots.** If `TA2` reads the same value on all
ten boots, either the race is not a race or the value is not being read. 推:
`TA2` in **1…5**, since the duty cycle at an 8-bit period is 87.20 % (量
seating 12) and each try is 500 µs apart.

Refutation: `TA2=FFFFFFFF` — 64 tries and never a 1 → the write-1-to-clear
result does not hold at boot, and `cevt` will refuse with `-EPERM` at `TA7`.

### 5.5 The negative control, and it did not cost a power cycle

The rating-99 `clock_event_device` is registered at `TA7`, before the real one,
on every boot: `ce_probe_registered=1` with **`ce_probe_mode_calls=0`**. The
core accepts it onto the list and never calls it, because 99 < the vendor's
100. **Rating 300 winning means nothing without it.**

And the marks' own negative control is already in the repository: seating 13's
`bench/2026-09-06/SP-boot.log` is 869 bytes and contains **zero** `RLXFW-TA`
lines, from an image built from the same tree one driver version earlier.

### 5.6 Expected order inside `Kn-boot.log`

```
RLXFW-B00 / RLXFW-ID0=0A3135AF / RLXFW-B01 … RLXFW-B09
RLXFW-TA0=…   <- arch_initcall, level 3
RLXFW-TA1=00000000
RLXFW-TA2=0000000n
RLXFW-TA3=00000000
RLXFW-TA4=00000000
Realtek WLAN driver driver version 1.6 (2012-12-04)   <- level 6
… chip name: 8196C … eth0..eth5 … Realtek FastPath:v1.03
RLXFW-TA5=…   <- late_initcall, level 7
RLXFW-TA6=00000000
RLXFW-TA7=00000000
RLXFW-TA8=00000000
RLXFW-TA9=00000003
RLXFW-B10
rlxfw: init running, RLXFW-R3-RUNG1-OK
```

🔴 **The vendor's entire NIC bring-up sitting BETWEEN `TA4` and `TA5` is a
structural prediction, not decoration.** If `TA5` appears before
`Realtek WLAN driver`, the initcall-level model in §5.2 is wrong and the `TA6`
prediction has no basis.

---

## 6. Stop conditions

1. Two boots wedge **at the same `TA` stage** → stop the block, go to the desk.
   One is noise; two at the same place is a defect with an address.
2. `K1-D`'s `disarm` returns `0` → stop immediately.
3. Any `S5b` reading other than `00000000` → `looprun` aborts by itself and
   nothing is uploaded. Do not override it.
4. `TA8` returns `-ETIME` (`FFFFFFC2`) on three consecutive boots → the
   pre-check is refusing systematically; read `ce_check_dj`/`ce_check_dc` and
   stop. **The guard doing its job is a complete result.**
5. Any capture containing `Oops`, `Unable to handle kernel`, `Kernel panic` or
   `BUG:` → keep everything, stop, and do not power-cycle before the capture is
   saved.
6. The seating ends at ten counted boots, or when the operator says stop.
   **Nothing here needs a flash write and nothing here may make one.**

---

## 7. What this block cannot decide

* It cannot show the arm is safe on hardware other than this die.
* It cannot separate *the sequencer works* from *seating 13's verb order
  works*, because they are the same calls — that is deliberate, and it is why
  `R5-3b-1` had to come first.
* `NET-25` gets one cold sample if the warm branch is taken. That is a cost of
  the branch, stated rather than hidden, and the phenomenon stays unisolated.
* The clocksource half is untouched: `rating` stays **0** and the system's time
  base is still `jiffies`. Only the clockevent is this driver's.

---

```cardnum
img-bytes	1034240	size /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin
img-sha16	23539da92c66589e	sha256-16 /home/key/fwre-work/rebuild/bench-only/r53b2-20260906/rlxfw-r53b2-20260906.bin
vmlinux-bytes	3976095	size /home/key/fwre-work/rebuild/r3-4/out/r53b2.vmlinux.elf
vmlinux-sha16	2730a7321ba4a357	sha256-16 /home/key/fwre-work/rebuild/r3-4/out/r53b2.vmlinux.elf
prev-img-bytes	1033216	size /home/key/fwre-work/rebuild/bench-only/r53b1-20260906/rlxfw-r53b1-20260906.bin
prev-img-sha16	e160089ae8ea5952	sha256-16 /home/key/fwre-work/rebuild/bench-only/r53b1-20260906/rlxfw-r53b1-20260906.bin
spec-sha16	f1cee4484bc3da30	sha256-16 /home/key/fwre-work/rebuild/r53b2-spec/rlxfw-initramfs.spec
drv-lines	2719	lines config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c
proc-lines	98	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c scnprintf
drv-verbs	9	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c strcmp\(buf,
markx-calls	11	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c rlxfw_markx\("TA
boot-proc-lines	7	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c "boot_[a-z_]+=
map-noop	1	count /home/key/fwre-work/rebuild/r3-4/out/r53b2.System.map ^80036d50 T clockevents_handle_noop$
map-tick	1	count /home/key/fwre-work/rebuild/r3-4/out/r53b2.System.map ^80036fc4 T tick_handle_periodic$
map-late-initcall	1	count /home/key/fwre-work/rebuild/r3-4/out/r53b2.System.map ^[0-9a-f]{8} t rtl819x_boot_arm_late$
ce-rating-dflt	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_RATING_DFLT\s+300$
ce-rating-probe	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_RATING_PROBE\s+99$
ce-min-j	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_MIN_J\s+300$
ce-tol-permille	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_CE_TOL_PERMILLE\s+10$
boot-ack-tries	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_BOOT_ACK_TRIES\s+64$
boot-ack-us	1	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c ^#define RTL819X_BOOT_ACK_US\s+500$
prev-boot-bytes	869	size bench/2026-09-06/SP-boot.log
prev-boot-ta	0	count bench/2026-09-06/SP-boot.log RLXFW-TA
send-over-127	0	count bench/2026-09-06b/PREDICTIONS-B12-block11.md -{2}send '[^']{128,}'
expansion-cap-lines	33	count bench/2026-09-06b/PREDICTIONS-B12-block11.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-06b/K[0-9]+-[APQNDL] .*--(esc|send) 
expansion-loops	10	count bench/2026-09-06b/PREDICTIONS-B12-block11.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell K[0-9]+ 
expansion-warm	9	count bench/2026-09-06b/PREDICTIONS-B12-block11.md ^.*--out bench/2026-09-06b/K[0-9]+-A -{2}send 'busybox reboot'
expansion-cold	10	count bench/2026-09-06b/PREDICTIONS-B12-block11.md ^.*--out bench/2026-09-06b/K[0-9]+-A --esc 150 
```

```cells
bench/2026-09-06b/K1-A
bench/2026-09-06b/K1-P
bench/2026-09-06b/K1-Q
bench/2026-09-06b/K1-N
bench/2026-09-06b/K1-D
bench/2026-09-06b/K2-A
bench/2026-09-06b/K2-P
bench/2026-09-06b/K3-A
bench/2026-09-06b/K3-P
bench/2026-09-06b/K4-A
bench/2026-09-06b/K4-P
bench/2026-09-06b/K5-A
bench/2026-09-06b/K5-P
bench/2026-09-06b/K6-A
bench/2026-09-06b/K6-P
bench/2026-09-06b/K7-A
bench/2026-09-06b/K7-P
bench/2026-09-06b/K8-A
bench/2026-09-06b/K8-P
bench/2026-09-06b/K9-A
bench/2026-09-06b/K9-P
bench/2026-09-06b/K10-A
bench/2026-09-06b/K10-P
bench/2026-09-06b/K10-L
```
