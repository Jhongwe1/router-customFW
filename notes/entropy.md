# entropy — why `/dev/random`'s pool is empty on this board, and rlxfw's source

`R7`, 2026-09-30. Owner of: the mechanism, the design, the credit policy and
the experiment. `SPEC.md` holds the numbers; this file holds the reasoning.

## 1. The defect, 量

Image `r6b8i` (recipe `3685a3a4`), over the console, 2026-09-30:

| reading | value | capture |
|---|---|---|
| `entropy_avail` at 768 s uptime | **0** | `bench/2026-09-30/SB-ENT.log` |
| `entropy_avail` at 1613 s uptime | **0** | `bench/2026-09-30/SB-RT1.log` |
| `poolsize` | 4096 | both |

And with a burst driven at it, uptime 3289–3437 s
(`bench/2026-09-30/ENT-B1`, `ENT-B2`, `ENT-C1`..`ENT-C6`, host output at
`$FWRE_WORK/rebuild/s118/bench/entctl2-ping.txt`):

| reading | value |
|---|---|
| 400 ICMP echoes to 10.1.1.3 | 400 transmitted, 400 received, 0 % loss; rtt min/avg/max/mdev **1.056/10.619/100.703/14.940 ms** |
| IRQ 12 (`rtl819x-nic`) | 279 → 294 → **1063** |
| IRQ 8 (`serial`) | 1048 → 1556 → **9320** |
| IRQ 13 / IRQ 25 (timers) | 329,105 → 345,257 / 329,077 → 345,229 |
| IRQ 2 (cascade), ER0/ER1/ER2 | 0 throughout |
| `entropy_avail` before / after each burst / after 30 s more idle | **0 / 0 / 0** |

The refutation was registered before the run — *if `entropy_avail` rose above 0
on the unmodified image while a burst of aperiodic interrupts demonstrably
landed, the premise below would be false and no kernel change would be needed*
— and it did not fire, with a positive control that passed. 🔴 Round 1 of that
control went **red** and is worth keeping: the host pinged 10.1.1.1 while
`rlx0` on this image carries **10.1.1.3/8**, so 300 frames arrived only as
broadcast ARP and IRQ 12 moved 15. No entropy figure from that round means
anything.

So: ~770 NIC interrupts and ~7,700 serial interrupts fired, 400 packets
round-tripped both ways, and not one bit was credited.

**Consequence.** `SPEC-R7` § 6 specifies the broker's LOGIN and PWSET
fail-closed: `NOENTROPY` until `entropy_avail >= 128` has been seen once. As
the kernel stands, rlxfw can never issue a session token or salt a password on
this board. The alternative — reading `/dev/urandom` anyway — is § 2.4.

## 2. The mechanism, 讀

All line numbers are in the tree that builds,
`src-vendor/rtl819x-toolchain/linux-2.6.30` (`2.6.30.9`), which
`tools/rlxfw-kbuild.sh` stages.

### 2.1 One writer, one caller

* `drivers/char/random.c:524` `credit_entropy_bits()` is the only function that
  **raises** `input_pool.entropy_count`, which is the variable
  `/proc/sys/kernel/random/entropy_avail` reads (`random.c:1288`, the sysctl
  table entry whose `.data` is `&input_pool.entropy_count`). `account()`
  (`:790`, `:792`) debits it and `init_std_data()` (`:937`) zeroes it — "only
  writer" would be wrong.
* Its callers are `:666` inside `add_timer_randomness()` (`:614`); `:753`
  inside `xfer_secondary_pool()`, which cannot credit `input_pool` because
  `input_pool` has no `.pull` (`:422-428`); and the two root-only ioctls
  `RNDADDTOENTCNT` (`:1127`) and `RNDADDENTROPY` (`:1142`). 🔴
  `RNDADDTOENTCNT` credits **with no data at all** for `CAP_SYS_ADMIN`, so
  `entropy_avail >= 128` is a claim about root's restraint as well as about
  hardware.
* Exactly three functions call `add_timer_randomness()`:
  `add_input_randomness()` (`:673`), `add_interrupt_randomness()` (`:689`) and
  `add_disk_randomness()` (`:703`, inside `#ifdef CONFIG_BLOCK`).

### 2.2 Why none of the three fires on an unattended boot

🔴 An earlier draft of this section said *there is no keyboard, no mouse and no
rotating disk*. **Both halves were wrong**, and the correct statement is
narrower: two of the three paths exist and are merely idle, which matters to
every experiment on this file.

| function | the real gate | this board |
|---|---|---|
| `add_input_randomness` | reached from `drivers/input/input.c:308`, gated at `:305` on `is_event_supported`; the callee de-duplicates at `:679` | **live.** `drivers/input/keyboard/rtl819x-keys.c` registers a *polled* input device (`:774`) and calls `input_report_key()` (`:378`), so a **reset button press credits the pool** — human-timed and rare, but a path |
| `add_disk_randomness` | gated on `disk->random`, which `rand_initialize_disk()` sets **unconditionally** in `alloc_disk_node()` (`block/genhd.c:1157`) — there is no rotational test in this tree | **live but idle.** Any mtdblock request completion samples (`drivers/mtd/mtd_blkdevs.c:122` → `end_request` → `block/blk-core.c:2011`), with `CONFIG_BLOCK=y` and `CONFIG_MTD_BLOCK=y`. The image is quiet only because nothing issues mtdblock I/O; `/dev/mtdN` through mtdchar does not use the block layer |
| `add_interrupt_randomness` | `kernel/irq/handle.c:429`, gated at `:428` on `IRQF_SAMPLE_RANDOM` in `handle_IRQ_event()`; gated **again** in the callee on `desc->timer_rand_state`, which only `rand_initialize_irq()` allocates — from `kernel/irq/manage.c:542`, inside the same flag test in `__setup_irq()`. So setting the bit on an already-registered `irqaction` would not create the state | **dead. No handler in this image registers that flag** |

量, rlxfw's own drivers (`config/rlxfw-src/linux-2.6.30/`), every
`request_irq`/`setup_irq`/`request_threaded_irq` call site and its flags — 3
live sites, 0 `struct irqaction`:

| driver | site | flags |
|---|---|---|
| `rtl819x-nic` | `drivers/net/rtl819x-nic.c:1677`, `:2687` (IRQ 12) | `IRQF_DISABLED` |
| `rtl819x-timer` | `drivers/clocksource/rtl819x-timer.c:1824` (IRQ 25) | `IRQF_DISABLED` |

🔴 Those two numbers are unchanged by § 3's hook, and that is deliberate: the
hook is a **net-zero** edit (`FW-110`). It replaces the blank line after
`nic_n_irq++;` instead of inserting, and the `#include` goes into
`rtl819x-nic-tx.h`, which no file cites by line — because the first version
inserted 22 lines and moved 70 citations across six files. § 8 records it.
And every registration that is **compiled** in the image,
by two independent methods — a grep over the 617-source compiled list taken
from the kbuild `.cmd` files, and a `readelf -sW` sweep of 645 objects for an
undefined `request_threaded_irq`/`setup_irq`, whose control is that
`kernel/irq/manage.o` defines them and is not in the referencing set:

| site | flags |
|---|---|
| `boards/rtl8196e/bsp/irq.c:122` (cascade) | `irq_cascade` has no `.flags` → **0** |
| `arch/rlx/kernel/rlx-cevt.c:243` (vendor tick) | `IRQF_DISABLED\|IRQF_PERCPU\|IRQF_TIMER` = **0x620** |
| `drivers/serial/8250.c:767` (console, IRQ 8) | `IRQF_DISABLED` = **0x20** — *not* `IRQF_SHARED`, because `bsp/serial.c` sets `s.flags = UPF_SKIP_TEST` and `8250.c:731` picks SHARED only for `UPF_SHARE_IRQ` |
| `drivers/net/wireless/rtl8192cd/8192cd_osdep.c:4014` | `IRQF_DISABLED` |
| `drivers/net/phy/phy.c:596` | `IRQF_SHARED` |
| the three rlxfw sites above | `IRQF_DISABLED` |

So the count of `IRQF_SAMPLE_RANDOM` registrations in this image is **zero**,
and that zero is a claim. Its controls: 36 driver and arch call sites in the
drop *do* set the flag (3c527, tg3, macb, gpio_keys, omap_udc, …) and **not one
of them has an object in either built cell**; over the compiled-source list the
only three `SAMPLE_RANDOM` lines are `kernel/irq/handle.c:428` and
`kernel/irq/manage.c:533`, `:869` — the infrastructure, which is exactly what a
working sweep should find; and the same regex over the same paths returns 457
`IRQF_DISABLED` lines and 1,428 `request_irq(` lines. The object files agree:
`li a3,32` immediately precedes each `jal request_threaded_irq` in
`rtl819x-nic.o` and `rtl819x-timer.o`.

⚠️ `arch/rlx/bsp` is a symlink to `boards/rtl8196e/bsp`, which `grep -r` from
`linux-2.6.30` does not follow; every sweep above passed it explicitly.

The vendor's own NIC (`drivers/net/rtl819x/rtl_nic.c:4227`, `IRQF_DISABLED`)
is compiled only at `CONFIG_RTL_819X_SWCORE=y`, i.e. in `quiet-swcore`, and
sets no flag either.

🔴 **`/proc/interrupts` on this board prints the raw flags.**
`arch/rlx/kernel/irq.c:161` is
`seq_printf(p, "  %s (0x%lx)", action->name, action->flags);`, so `(0x60)`
would mean `IRQF_SAMPLE_RANDOM` is set and this build's actions must read
`0x0`, `0x20`, `0x80` or `0x620`. ⚠️ The `/proc/interrupts` lines quoted in
`bench/2026-09-30/SB-ENT.log` carry no parenthesised flags, so either that
quote is abridged or the print differs in the built image; § 5 has the card
read it rather than assume it.

### 2.3 🔴 And the flag alone would not have fixed it

`add_timer_randomness()` (`random.c:614-669`) builds its sample from
`get_cycles()` and `jiffies`, and derives the credit from **jiffies alone**:
the minimum of the first, second and third absolute differences of the jiffies
series, then `min_t(int, fls(delta>>1), 11)`.

`arch/rlx/include/asm/timex.h` defines, for this Lexra core:

```c
static inline cycles_t get_cycles(void)
{
	return 0;
}
```

So on this board the pool's high-resolution field would be a **constant**, and
the credit would come from a 100 Hz counter whose third-order minimum is 0 for
almost every pair of packets arriving faster than a jiffy. Setting
`IRQF_SAMPLE_RANDOM` would have produced a number, not entropy. This is why
the fix is not a one-flag change.

🔴 `get_cycles()` returning 0 is not by itself evidence about the die — but the
die was measured, and an earlier draft of this file wrongly called it 未定 and
asked for the measurement that already exists. 量 `CPU-42`, 2026-08-25b, bare
metal: CP0 rd 9 `Count` reads `00000000` before and after a 100,000-iteration
loop, delta 0, traps 0, with `nowrite` 0 on all 256 census rows so the zero is a
real zero, and CP0 rd 1 `Random` moving as the positive control. rd 11
`Compare` also reads 0. Two further 讀 readings agree that the port has no
counter: `arch/rlx/include/asm/cpu-features.h:84` is `#define cpu_has_counter 0`
and `arch/rlx/kernel/cpu-probe.c:30` never sets `MIPS_CPU_COUNTER`. Nothing in
`arch/rlx` calls `read_c0_count()`, which `rlxregs.h:273` does define.

⚠️ 殘留, narrower than 未定: a `Count` that exists but is **clock-gated** reads
and behaves identically to one that is absent
(`docs/rlx-cache-and-cp0.md:290-299`; `docs/rlx-isa.md:438` states it flatly as
"not implemented", which is stronger than that file allows). The experiment
that separates them is one `mtc0` to rd 9 and one `mfc0` back, and it has never
been run — `CPU-56` measured that `mtc0` to rd 14 does *not* write, so it is not
a formality. `rdhwr` is no escape: it traps `RI` on silicon (`CPU-57`, probed as
`rdhwr $2,$29`) and the kernel does not emulate it (`CPU-47`). § 7.

### 2.4 What `/dev/urandom` is worth with an empty pool

`urandom_read()` (`random.c:1050`) calls `extract_entropy_user(&nonblocking_pool, …)`
and **never blocks and never fails**. `extract_entropy()` (`random.c:850`)
reduces `r->entropy_count` toward 0 and then keeps hashing the pool state
regardless: `xfer_secondary_pool()` pulls from `input_pool` only what
`input_pool` has, and with 0 there it transfers nothing. The bytes that come
out are the SHA-1 output of the `nonblocking_pool` state, which on this board
is seeded only by `init_std_data()` (`random.c:947`) — `ktime_get_real()`,
`jiffies` and `utsname()`, mixed with a credit of **0 bits**.

So `/dev/urandom` on this board today returns bytes that are a deterministic
function of the boot time and the kernel version string, stirred by a counter
that advances predictably. They are **not secret**: an attacker who knows
approximately when the board booted can enumerate the state. Using them for a
session token or a password salt would mean predictable session tokens on a
router's admin interface. That is the honest statement, and it is why R7's
login is fail-closed rather than "read urandom and hope".

## 3. The design

One new rlxfw source file, one narrow vendor patch, one Kbuild row, one line in
an existing rlxfw driver. **No new kernel config symbol** — so
`config/rlxfw-kernel.delta` is unchanged and no variant (`quiet`, `loud`,
`quiet-swcore`) is affected by a config delta. `drivers/Makefile:26` is
`obj-y += char/`, a bare `obj-y`, so no plumbing is needed.

| file | what |
|---|---|
| `config/rlxfw-src/linux-2.6.30/drivers/char/rlxfw-entropy.c` | the source, the probe and the credit policy; `/proc/rlxfw-entropy` |
| `config/rlxfw-src/linux-2.6.30/include/linux/rlxfw-entropy.h` | the interface, and the mechanism above in short |
| `config/rlxfw-marks.tsv` `MK13` | `obj-y += rlxfw-entropy.o` into `drivers/char/Makefile`, anchored on the line that builds `random.o` |
| `config/host-compat/0009-random-rlxfw-input.patch` | adds `rlxfw_random_add()` to `random.c`; changes no existing line |
| `config/rlxfw-src/…/drivers/net/rtl819x-nic.c` | one call in `nic_isr()`, **replacing a blank line** so the file's 61 cited lines do not move (`FW-110`) |
| `config/rlxfw-src/…/drivers/net/rtl819x-nic-tx.h` | the `#include`, which lives here because no file cites this header by line |

### 3.1 The clock

The arrival phase of an aperiodic interrupt, read on **TC0CNT**
(`0xB8003108`, `SPEC.md` `REG-07`). TC0 is the vendor's clockevent on IRQ 13,
still running, although since `CLK-27` `jiffies` follows rlxfw's TC1 clockevent
on IRQ 25. 🔴 This file **never writes the block**: it reads four words —
`TC0CNT` per event, and `TCCNR`, `TC0DATA`, `CDBR` once at the probe — and
writes none, so it cannot disturb either tick.

🔴 **No new register value enters code.** Base `0x18003100`, offset `0x08` and
the bits-31:4 shift are the three that `rtl819x-timer.c:418`, `:474` already
carries on two sources (D 8.2.1 Table 19 and Table 22, plus read on this die),
and `REG-07` is 量: two reads of `0xB8003108` seconds apart gave 114,003 and
16,989 ticks. They are restated in the entropy file rather than shared so the
source does not depend on an optional driver being configured in.

🔴 **The rate is used by no decision** — as well, because the rate is 推.
`CLK-17`'s value mark is 推: 14,286,057 Hz is `CLK-04`'s tick × `REG-05`'s
142,858, not a frequency anyone measured. Under Linux `arch/rlx/bsp/timer.c`
reprograms `CDBR` from divisor 14 to 1000 and `TC0DATA` from 142,858 to 2,000
(量 seating 11, TM-1), so the live rate is ~200 kHz — also 推 — one period ≈
10 ms ≈ one jiffy, and the resolution ~5 µs over an ~11-bit range. What is 量
is the **ratio**: 2,000 counts per jiffy, residual exactly 0 over 140,693,532
counts (`CLK-23`). `CLAUDE.md` forbids predicting a Linux-state value from a loader
constant, so nothing is compiled in: the policy asks only whether the phase
series is *irregular*, and `/proc/rlxfw-entropy` prints `TC0DATA` and `CDBR`
raw so a reader derives the rate instead of trusting a comment.

### 3.2 The source, and the three that were rejected

**Accepted: `rtl819x-nic`'s ISR (IRQ 12).** Packet arrival is the only
genuinely aperiodic interrupt this image has. One call, at the top of
`nic_isr()` after the W1C ack.

**Rejected — the timer tick.** IRQ 13 and IRQ 25 are periodic by construction;
their phase against TC0CNT is the same number every tick. Sampling a clock
with itself measures nothing, and crediting it would raise `entropy_avail` on a
schedule — worse than 0, because 0 is honest and a scheduled number looks like
a measurement.

**Rejected — the console (IRQ 8).** Genuinely aperiodic, and 量 above it fires
~7,700 times in a burst. But reaching it needs a patch to the vendor's
`drivers/serial/8250.c:767` registration (which is `IRQF_DISABLED` here, not
shared: `bsp/serial.c` sets `UPF_SKIP_TEST`), and an unattended boot produces no
keystrokes, so it cannot be
the source that makes a login possible. It would add risk to the path that must
work and bits to the case that does not need them. The hook is one call if a
later gate wants it.

**Rejected — `IRQF_SAMPLE_RANDOM` on the NIC.** It would route the same
interrupt through `add_timer_randomness()`, which credits from jiffies deltas
and mixes a constant `get_cycles()`, **on top of** this file's credit for the
same event. Two estimators on one event is over-crediting, which is the one
error here that is a security defect rather than a slow boot.

## 4. The credit policy

Per event, in `rlxfw_entropy_event()`:

1. Read TC0CNT → `phase`. **Before** taking the lock, so the sample is the
   arrival phase and not the phase after a fixed instruction sequence.
2. Mix 12 bytes unconditionally: `phase`, `jiffies`, `(src << 16 | seq)`.
   Mixing makes no claim and cannot lower the pool's quality.
3. Compute `d1`, `d2`, `d3` — the first, second and third differences of the
   phase series — and `m = min(|d1|, |d2|, |d3|)`. The event **qualifies** iff
   `m != 0`. Bucket `fls(m)` into `dist[]`.
4. Credit **1 bit per 16 qualifying events**, and **never more than 1 bit per
   jiffy**.

### 4.1 Why third-order and not "the phase moved"

🔴 This file's first draft qualified on `phase != last_phase`, and that is a
test that cannot fail on a regular source. A host sending one packet every
7.1 ms against a ~10 ms counter period walks the phase by a **constant** ~1,420
counts each time: the phase differs every event, so a first-order test
qualifies all of them and credits a stream with no jitter in it at all. The
first difference of a constant-rate walk is constant, so `d2` is 0 and the
event does not qualify. Third order costs nothing and refuses a
constant-acceleration walk too. It is also exactly the shape `random.c:637-660`
uses on jiffies, so a reviewer recognises it.

It is the liveness test as well: a mis-addressed, frozen or powered-down
register gives every phase equal, `d1 = 0`, `m = 0`, and **nothing is ever
credited**. A broken source cannot manufacture bits here; it can only fail to
produce them, and the failure is a pool that stays at 0 — the state today,
which R7 treats as fail-closed.

### 4.2 Why 16, stated as a derating and not as a measurement

The observable is an ~11-bit phase at ~5 µs. Take the pessimistic floor at
**1 bit of unpredictability per qualifying event** — pessimistic because it
assumes an attacker who sends every packet and lands it within one counter
tick, far better than anything measured here. This policy claims **1/16** of
that floor. The kernel's own estimator on the same data would be between 1×
and 176× more generous (`fls(m>>1)` capped at 11).

🔴 **What an attacker controls, with the ratio 量.** From § 1: 300 broadcast
frames moved IRQ 12 by 15; 400 round-tripping echoes moved it by 769. So the
interrupt count is **not** the packet count — anywhere from ~1/20 to ~2
interrupts per frame — and an attacker who can put frames on the LAN chooses
how many events this file sees, across more than an order of magnitude. The
policy is therefore written so the **event count buys as little as possible**
and the **wall clock is the binding constraint**. What the attacker cannot
choose is the phase: the same burst showed rtt mdev 14.940 ms and max
100.703 ms — milliseconds of spread against a 5 µs tick — and the part of that
spread contributed by the board's own bus, DRAM refresh and cache state is not
reachable from the wire at all.

### 4.3 Why the one-bit-per-jiffy clamp

It bounds what a flood buys. At `CONFIG_HZ` = 100 the pool cannot gain more
than **100 bits/s** from this source however many packets arrive, so R7's
128-bit threshold needs ≥ 1.28 s of wall clock **and** ≥ 2,048 qualifying
events, whichever is slower. Without the clamp a 100 kpps flood at ~1
interrupt per frame would credit ~6,250 bits/s and fill the 4,096-bit pool in
0.65 s — a number pretending to be a measurement.

### 4.4 The probe is a positive control on the address

`rlxfw_entropy_init()` (a `device_initcall`, level 6, so it is in place before
`rtl819x-nic`'s `late_initcall` 7) refuses to set `alive` unless all three
hold:

1. `TCCNR`'s `TC0En` (bit 31) is set — 量 `REG-09`, this unit reads
   `0xC0000000`. With TC0 disabled the phase would be meaningless.
2. `TC0DATA`'s low nibble is zero (D Table 20 reserves bits 3:0) and its count
   field is non-zero. A wrong address is far likelier to read something with
   bits set there.
3. `TC0CNT` **changes** within 65,536 reads. `probe_reads` reports how many
   were used, so "a few hundred" is falsifiable rather than asserted.

Any one failing leaves `alive 0`, credits nothing for the rest of the boot, and
says so in `/proc`. It does not print (`CONFIG_PRINTK` is `n` in `quiet`) and
does not fail the initcall: an entropy source that is not there must not stop
the boot.

## 5. The experiment — a card the main session can type

Board is **10.1.1.3/8** on `rlx0` (`量` § 1 round 1: assuming 10.1.1.1 is what
made that round void). Host is 10.1.1.2 on `enxfc19286184c9`. 🔴 `grep` is not
on the board's `PATH` (量: `/bin/sh: grep: not found`); it exists only as a
busybox applet, so every board cell below is a plain `cat` and the parsing is
the host's. No `dd`, no `md5sum`, and this image's `ping` ignores `-c` — no
board cell uses any of them. Every `--send` is ≤ 127 characters.

Identify the booted image by the tool comparing `RLXFW-ID0` against the build's
digest, never by a typed value.

🔴 **Three things must not happen during this card, because each credits the
pool for a reason that is not this driver** (§ 2.2):

1. **No reset-button press, at any point in the seating.** `rtl819x-keys`
   reports a key event, which reaches `add_input_randomness()`. A press between
   `E1` and `E9` breaks the attribution completely, and `CLK-28`/`FW-63`
   episodes must be kept to a different boot.
2. **Nothing may mount or read an mtdblock device**, or
   `add_disk_randomness()` credits. `/dev/mtdN` through mtdchar is safe.
3. **No `RNDADDTOENTCNT`/`RNDADDENTROPY` ioctl**, which no cell here issues,
   and no userspace that does — so no `brokerd` on this boot.

None of the three is visible in `/proc/rlxfw-entropy`, so none of them is
checkable after the fact. Criterion 6 of § 5.2 (`entropy_avail` == `bits`) is
the only thing that would catch 1 or 3; nothing catches 2.

| cell | where | command | ≤127 |
|---|---|---|---|
| `E0` | board | `cat /proc/rlxfw-entropy` | 23 |
| `E1` | board | `cat /proc/uptime /proc/sys/kernel/random/entropy_avail /proc/sys/kernel/random/poolsize` | 88 |
| `E2` | board | `cat /proc/interrupts` | 20 |
| `E3` | board | `ifconfig rlx0` | 13 |
| `E4` | board | `sleep 30` | 8 |
| `E5` | board | `E1` again — the idle control |  |
| `E6` | **host, off-card** | `sudo ping -q -c 4000 -i 0.0071 -s 64 10.1.1.3` | |
| `E7` | board | `E0`, `E1`, `E2`, `E3` |  |
| `E8` | **host, off-card** | `sudo ping -q -f -c 8000 -s 64 10.1.1.3` | |
| `E9` | board | `E0`, `E1`, `E2`, `E3` |  |

Order: `E0`, `E1`, `E2`, `E3`, `E4`, `E5`, `E6`, `E7`, `E8`, `E9`.

`-i 0.0071` is deliberate: 7.1 ms is not a divisor or a multiple of the ~10 ms
counter period, so the phase does not resonate with it. `E8`'s flood is the
clamp's test, not the mechanism's.

### 5.1 Telling *running* from *never started*

* `E0` prints **`No such file or directory`** → the driver is not in this
  image. The round is **void**, not failed; check which image booted.
* `E0` prints the node with `alive 0` → the driver ran and the **probe
  refused**. See § 4.4 for which of the three readings to look at
  (`tc0data`, `tccnr`, `probe_reads`).
* `E0` prints `alive 1` with `ev_nic 0` → running, no NIC interrupt has
  reached it yet. `nseen` < 3 says the warm-up has not finished.
* `probe_reads 0` is impossible by construction; if it appears, the instrument
  is wrong, not the board.

### 5.2 Pre-registered pass criteria — all of them

Let Δ be `E7` minus `E1`/`E2`/`E0` readings, and Δ' be `E9` minus `E7`.

1. `alive 1`, `1 ≤ probe_reads ≤ 65536`.
2. `E5` − `E1`: `entropy_avail` **unchanged** over 30 s of idle. Traffic, not
   uptime, is what credits.
3. Δ`ev_nic` ≥ 1,000, and |Δ(IRQ 12) − Δ`ev_nic`| ≤ 8. Two counters over the
   same events, one of them written by the kernel's IRQ core and not by rlxfw.
   ⚠️ This is a **wiring** control, not an entropy control: two counters
   agreeing while they count the same thing is evidence that the hook is
   called, and nothing more.
3b. Every action's flags in `E2` read `0x0`, `0x20`, `0x80` or `0x620` — no
   `0x40` bit anywhere. `arch/rlx/kernel/irq.c:161` prints them, so this is a
   direct reading of § 2.2's zero **on the running image**, and it is what
   would catch a future change that turned `IRQF_SAMPLE_RANDOM` on and started
   double-counting. If `E2` shows no parenthesised flags at all, this criterion
   is **not met and not failed** — record that the print is absent and say so,
   rather than reading the absence as a pass.
4. Δ`qualifying` ≥ 0.5 × Δ`ev_nic`.
5. Δ`bits` ≥ 128 **and** `entropy_avail` ≥ 128 at `E7`.
6. `entropy_avail` at `E7` **equals** `bits` at `E7`. Both start at 0, all
   credit goes to `input_pool`, and nothing in R7 drains it yet, so an
   inequality means something else credited or something consumed.
7. `dist` has ≥ 4 non-empty buckets and no single bucket holds > 80 % of
   `qualifying`. A near-single-bucket histogram is a phase walking
   deterministically and § 4.2's derating is not enough.
8. Δ'`bits` ÷ Δ'`uptime` ≤ 101 per second, across `E8`'s flood.

Prediction, from § 1's measured 1.92 interrupts per round-tripped echo: `E6`'s
4,000 echoes → Δ`ev_nic` ≈ 7,700 (range 4,000–16,000; the ratio is 量 at one
operating point only), Δ`qualifying` most of it, Δ`bits` ≈ 480 (≥ 128 even at
25 % qualifying), `entropy_avail` ≈ 480. `E6` takes 28.4 s, so the clamp's
2,840-bit ceiling is not binding.

### 5.3 What refutes the fix

| # | reading | refutes |
|---|---|---|
| `R1` | `alive 0` | the register model: TC0 disabled, `TC0DATA` reserved nibble set, or TC0CNT static in 65,536 reads |
| `R2` | Δ(IRQ 12) ≥ 1,000 while Δ`ev_nic` = 0 | the wiring — the hook is not on the ISR path |
| `R3` | Δ`ev_nic` ≥ 1,000 while Δ`qualifying` = 0 | the clock choice: the counter is read but the phase is regular to third order at event granularity. § 7's finer-clock row becomes the fix |
| `R4` | Δ`bits` ≥ 128 while `entropy_avail` still 0 | the mixing path — `config/host-compat/0009` or `credit_entropy_bits` |
| `R5` | criterion 8 fails | the clamp. **A security defect**: over-crediting under a flood |
| `R6` | criterion 7 fails | the credit policy, not the mechanism. `RLXFW_ENT_PER_BIT` must be re-derived from the histogram before R7's login trusts it |
| `R7` | criterion 2 fails (idle raises the pool) | the source claim — something periodic is crediting |

### 5.4 The control reading — the same card without the change

Already taken, § 1, on `r6b8i`: `E0` prints *No such file or directory*;
`entropy_avail` reads **0** at `E1`, **0** after 30 s idle, **0** after a burst
of 400 round-tripped echoes and ~770 NIC interrupts; IRQ 12 rises normally.
That is the comparison the change's number is against, and it means the rise is
attributable to this change and not to the burst.

## 6. What a pass does **not** establish

* **Not that the bits are cryptographically strong.** `entropy_avail` is an
  accounting variable that `rlxfw_random_add()` writes; a pass shows the
  accounting works and the source is alive, not that the source has the
  min-entropy claimed. Establishing that needs raw samples off the board and an
  SP 800-90B style estimate. `dist` is where that would start; it is not the
  answer.
* **Not that the source resists an on-path attacker.** § 4.2's 16× derating and
  § 4.3's clamp are arguments, not measurements.
* **Not TC0's rate under Linux.** No reading here measures it, `CLK-17` and the
  ~200 kHz figure are both 推 (only the 2,000-per-jiffy ratio is 量, `CLK-23`),
  and `/proc` prints `TC0DATA` and `CDBR` raw precisely so no reader takes a
  rate from this work.
* **Not that RLX4181 has no cycle counter.** `CPU-42` measured that `Count`
  reads 0 and does not move; clock-gated and absent are indistinguishable from
  that reading (§ 2.3, § 7).
* **Not that nothing else credited the pool.** Criterion 6 catches a reset-button
  press or an ioctl; nothing catches mtdblock I/O. § 5's three prohibitions are
  procedure, not instrumentation.
* **Not that any other consumer of randomness changed.**
  `secure_tcp_sequence_number()` has its own hash and is unaffected.
* **Not that the pool stays ≥ 128.** Readers consume it. R7's rule is *seen
  once*, which this satisfies.
* **Not anything about `loud` or `quiet-swcore`.** Only `quiet` was built.
* **Not that the image boots.** § 8 is a compile-and-link result; no line of
  this has run on silicon.

## 7. Open — 未定

| what | settled by |
|---|---|
| 殘留 of `CPU-42` — whether CP0 `Count` is absent or present-but-clock-gated. Not 未定: the read was taken (§ 2.3), and either way it is unusable today | one `mtc0` to CP0 rd 9 followed by one `mfc0`, bare metal. `CPU-56` measured that `mtc0` to rd 14 does not write, so a write-readback is a real experiment, not a formality. No `mtc0 …,$9` exists anywhere in `tools/`, `docs/` or `notes/` |
| whether the Lexra `lxc0` register file holds a counter | `docs/interrupt-map.md:758` — that file has never been probed, and the vendor header names only `$0` `ESTATUS`, `$1` `ECAUSE`, `$2` `INTVEC`, `$20` `CCTL`. So a Lexra-specific counter is not excluded by any measurement |
| the real min-entropy per qualifying event on this board | raw `dist` (and ideally raw phase samples) off the board, then an SP 800-90B style estimate. Until then `RLXFW_ENT_PER_BIT` = 16 is a derating, not a measurement |
| whether the console (IRQ 8) should be a second source | a seating in which the operator's keystrokes are the only traffic, which § 3.2's reasoning says is not the case that needs bits |

## 8. Build result

| cell | tree | recipe | vmlinux | `.text` | `kconfig-delta check` | `rlxfw-marks verify` |
|---|---|---|---|---|---|---|
| `entq0` (control, HEAD) | base clone | `8b5ae480` | 4,256,456 B | 3,582,908 | green `[quiet]` | green, 12 marks, **11** witnesses |
| `entq1` (this change) | this patch | `ad494952` | 4,257,403 B | 3,584,644 | green `[quiet]` | green, 12 marks, **12** witnesses |

`--variant quiet --marks --jobs 4`, with the declared initramfs spec `r6b8i`
was built from (spec sha256 `128d9c9f3e34fc06`). Cost: **+947 bytes** of
vmlinux, +1,736 of `.text`, +4 of `.data`, +208 of `.bss`. `random.o`'s `.text`
goes 6,708 → 6,804 (+96, the whole of `0009`); `rtl819x-nic.o` 69,592 → 69,668;
`rlxfw-entropy.o` is 5,460 bytes of object. Zero compiler warnings from any of
the three files.

Second, independent reading that the code linked and is not merely a string in
`.rodata`: `System.map` in `entq1` carries `rlxfw_random_add` (`T`),
`rlxfw_entropy_event` (`T`), `rlxfw_entropy_init` and
`__initcall_rlxfw_entropy_init6` — the `6` confirming `device_initcall` — and
18 `rlxfw_ent_*` objects; the same grep on `entq0`'s `System.map` returns
**0**, with ` add_interrupt_randomness` present in both as the positive
control. `nm` on `rlxfw-entropy.o` shows `rlxfw_random_add` as `U`, so it is
resolved from `random.o` and not from anywhere else. The witness string
`rlxfw-entropy` occurs 3× in `entq1`'s vmlinux and **0×** in `entq0`'s, with
`rtl819x-nic` at 5× in both as that grep's positive control.

⚠️ The first run of this build failed **in both arms identically**, at
`usr/initramfs_data.cpio`, because `--initramfs` was omitted and
`CONFIG_INITRAMFS_SOURCE` names `usr/rlxfw-initramfs.spec`. The control failing
the same way is what identified it as an invocation error rather than a defect
in this change.
