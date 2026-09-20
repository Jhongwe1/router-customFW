# PREDICTIONS — block 33, seating 31 (`R6-5`'s third seating)

**declared date 2026-09-21** · one power cycle, already spent at 2026-09-20 22:29
(cold power-on, banner carries **no** `Reboot Result from Watchdog Timeout!`,
capture `/home/key/fwre-work/rebuild/seat31/BOOT0`). Every cell below reaches
the board by watchdog reset from the loader, not by a second press.

---

## § 0 What this block is, and the one sentence that frames it

`R6-5` has had two seatings and `D5`/`D6` were not obtained either time. The
second seating identified the blocker — `NET-61`, a burst desynchronises the
engine's two RX position registers and the driver then delivers frames carrying
another frame's length — and `PROGRESS.md:17` records that not measuring
throughput in that state is **deliberate**: *"在一個會把 frame 帶著別人的長度遞交
的狀態下量吞吐量，量到的是缺陷而不是路徑。"*

This block exists because an image now exists in which `arm` is not fatal, and
because a counter now exists that can see the fault the DoD's own instrument is
blind to.

🔴 **It does not claim to fix `NET-61`.** 量 `bench/2026-09-20b/Z10-nic`: `arm`
already zeroed both hardware positions **before** this change, and 量 `Z11-f6`
read **11/181 (93.9 % loss)** after exactly that repair, where a fresh boot
reads 20/20. The change makes `arm` **non-fatal**; a card that treats it as a
repair is refuted by a capture that already exists.

---

## § 1 The image, and what is held constant

| | `r6if1` (seating 30) | `s31b` (this block) |
|---|---|---|
| `recipe_id` | `edc94765` | **`f179cf21`** |
| `config_sha256` | `59efa73c9715…` | **identical** |
| `initramfs_sha256` | `7130245fbcd9…` | **identical** |
| `cflags_kernel` | `-fno-if-conversion` | identical |
| host-compat patches / marks | 6 / 25 | identical |
| `vmlinux` bytes | 4,464,774 | 4,465,171 |
| `nfjrom` sha256 | — | **`8275a0799abce5a1f17818790f8ee1caf5b263ad6c18f3ec90892190015c88c1`** |
| `nfjrom` bytes | — | 1,153,024 |

**The single differing input is `config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c`.**
Everything else in the manifest is byte-identical, which is why the
`config_sha256` row is in this table: it is the evidence that `--variant quiet`
was the right choice rather than a guess.

### The three changes

1. **`nic_do_arm()` re-establishes both rings and zeroes both indices**, under
   `nic_lock`, behind a hoisted unlock guard, counting the CPU-owned slots it
   discards into `n_arm_flush`.
2. **A desync detector** — `nic_dsync_check()`, called once per NAPI poll
   *before* the harvest, two KSEG1 loads, **observe-only**.
3. **`dsynctest <rp> <rm>` and `dsyncchk`** — the detector's positive control,
   touching no hardware.

### 🔴 Four defects this driver had before it was built, caught by an
adversarial read and fixed

Recorded here because the fixes are what the cells below test.

* **The refill loops sat above the write guard.** `nic_wr` returns `-EPERM`
  when locked, but `nic_re_set`/`nic_dw_set` do not go through `nic_wr` — so a
  **locked** driver would have flushed the whole ring and *then* returned, a
  refusal that had already done the thing it refused, leaving a fresh skew in
  the opposite direction. Reachable by typing `echo alloc ; echo arm` with no
  `unlock`. The guard is now hoisted and increments `n_refused`.
* **The loops took no lock.** `nic_do_engine(0)` does **not** call
  `napi_disable()`, so a poll scheduled before the mask cleared can still run
  `nic_napi_harvest` in softirq and write `nic_rx_idx` mid-loop. The vendor
  precedent the function cites has `local_irq_save`; it had been dropped.
* **A fabricated 量.** The first comment asserted as *measured* that the engine
  wrote slots 0..5 while `rx_idx` was 2. 量 `bench/2026-09-20b/R9-NB0`, the dump
  immediately before `A1`'s re-arm: `rx_idx 1`, `rpdcr0_pos A15B8004`,
  `rmdcr0_pos A15B8024`, **all eight ring words SWCORE-owned — the ring was
  clean**. 量 `N1`, after the arm and one ping: exactly **one** stale slot
  (`rxd0 A15B8050 len 1446`) and `seen_iisr 0000320E`, **bit 16 absent, no
  run-out**. So `arm` creates an *index skew* and the skew then manufactures
  the hole one frame at a time. The comment now says that.
* **`dsynctest` had no `nic_allocated` guard**, so the positive control could
  have passed against a ring base of zero. It now returns `-ENXIO`.

⚠️ **Consequence for cell order**: the detector's control must run **after**
bring-up, not at rest. That is why `B4`–`B6` sit where they do.

---

## § 2 Hypotheses, each with what refutes it

**H1 — the detector discriminates.** `dsynctest` returns 0 for two equal
offsets, 4 for two offsets four slots apart, 1 for one slot apart.
*Refuted by* any other value, or by `dsync_test_seen` staying 0.
🔴 **Nothing else in this block may be interpreted if H1 fails.** A detector
that has only ever reported 0 is a claim with no control, and every `n_dsync 0`
below would then be *"nobody looked"* rather than *"it never happened"*.

**H2 — `arm` leaves the driver and the hardware agreeing.** After
`engine off ; arm ; engine on`: `rx_idx 0`, `tx_idx 0`, Δ 0, and all eight
`rxd*` words carry OWN.
*Refuted by* a non-zero index, a non-zero Δ, or any `rxd*` with OWN clear.

**H3 — the burst threshold is the ring depth.** A single datagram of N frames
first drives Δ ≠ 0 at **N = 9**, the first N greater than `NIC_RX_DESC` = 8.
*Refuted by* Δ ≠ 0 at 7 or 8; or Δ = 0 at 9, 10 **and** 14, which would mean one
burst is never enough and the trigger is cumulative.
⚠️ **A negative at every rung is a result, not a failure** — it would say the
trigger needs sustained traffic, and the next block raises `-c` rather than `-s`.

**H4 — `n_arm_flush` is non-zero at least once.** If every `arm` in this block
discards nothing, the refill loop is dead code on this path and its cost is
unjustified — which is a result about the fix, and it is written down here so
it cannot be quietly absorbed.

**H5 (D5) — a throughput figure exists**, host → board, over five runs, with its
spread. **Pre-registered point estimate 25 Mbit/s, band 20–30**, derived below.

---

## § 3 🔴 STANDING INSTRUCTION — the `NET-64` contingency

**IF THE CONSOLE GOES SILENT AT ANY POINT, DO NOT POWER CYCLE.**
Run these three, in this order, from the host, before anything else:

```
ping -I 10.1.1.2 -c 4 -W 2 10.1.1.3
ip -4 neigh show 10.1.1.3
cat /sys/class/net/enxfc19286184c9/carrier
```

**Why this is worth more than the block it interrupts.** `NET-64`'s surviving
hypotheses are **H4** (the watchdog did not bite, so the CPU was running) and
**H6** (only the UART died and the kernel lived) — and *both contradict the
row's own headline of a hard hang*. H1 (`bf` bus hang) is withdrawn for want of
source support, H2 (the link) is closed by the `usbipd detach` test, H3 (it bit
and the board is in the loader) is refuted by absence — two ESC windows, one of
25 minutes at 500 ESC/s, returning 0 bytes against a loader measured to echo
77,655 raw ESC.

H6's own experiment ran on 2026-09-20 and **its answer was discarded** when the
DRAM-retention gate fired. That data is now unobtainable: the wedged kernel's
DRAM has been overwritten by three boots since (21:58, 22:04, 22:29). **A reply
from `10.1.1.3` while the console is dead answers H6 directly, with no DRAM
retention involved at all.** It costs one command and there is no other route
to it.

A power cycle destroys the evidence. Ask before pressing.

---

## § 4 Cells — block 33, image `s31b`

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL with output to `<prefix>.log`.

Preamble is `tools/looprun.py --mode bench`, which carries its own abort gates:
`S4` requires `Reboot Result from Watchdog Timeout!`; **`S5b` requires the word
at `0x8040D4A0` to read `00000000`** and cannot be skipped; `S5c` uses ARP and
not ICMP; `S6b` requires the staged head to be the image `S6` sent.

```
#-- A0         looprun: reset -> rescue -> burnflag -> hostlink -> upload -> staged -> boot -> assert
#--            --image .../imgwork/s31b/s31b/kroot/rtkload/nfjrom
#--            --image-sha256 8275a0799abce5a1f17818790f8ee1caf5b263ad6c18f3ec90892190015c88c1
#--            --recipe-override f179cf21
#-- B1-SW      the switch first. PROGRESS.md:19: without SIRR's TRXRDY the ping is
#--            100 % loss and looks like a driver fault.
CAP --out bench/2026-09-21/B1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
#-- B2-UP      bring rlx0 up. ndo_open does alloc then arm then request_irq then engine on.
CAP --out bench/2026-09-21/B2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- B3-BASE    at rest. RECORDS rx_ring and mb_ring -- B4..B6's arguments are
#--            predicted from A15B8000/A15B8020 and are VOID if this reads otherwise.
CAP --out bench/2026-09-21/B3-BASE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B4-T0      detector control, negative side
CAP --out bench/2026-09-21/B4-T0 --send 'echo dsynctest A15B8000 A15B8020 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- B5-T4      detector control, positive side -- reproduces C16's measured rp6/rm2 shape
CAP --out bench/2026-09-21/B5-T4 --send 'echo dsynctest A15B8010 A15B8020 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- B6-T1      a value that is neither 0 nor 4, so the control is not a two-state coincidence
CAP --out bench/2026-09-21/B6-T1 --send 'echo dsynctest A15B8004 A15B8020 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- B7-PING    baseline. If this is not 4/4 nothing below is interpretable.
HOST bench/2026-09-21/B7-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- B8-ARM     the re-establishing arm. N-ARM and N-ARMR must BOTH appear.
CAP --out bench/2026-09-21/B8-ARM --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
#-- B9-POST    H2. rx_idx 0, tx_idx 0, delta 0, every rxd OWN set.
CAP --out bench/2026-09-21/B9-POST --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B10-PING   the arm did not break the path
HOST bench/2026-09-21/B10-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

### The ladder — `NET-61` 殘留's five remaining rungs

Every rung is `arm` (Δ ← 0) → **one** datagram → read Δ. The frame counts are
re-derived here rather than copied: `ceil((S + 8) / 1480)` for `-s S`.

| rung | `-s` | frames | Δ predicted |
|---|---:|---:|---:|
| `C1` | 10000 | 7 | 0 |
| `C2` | 11000 | 8 | 0 |
| `C3` | 12500 | **9** | **≠ 0** |
| `C4` | 14000 | 10 | ≠ 0 |
| `C5` | 20000 | 14 | ≠ 0 |

```
#-- C1a/C1b/C1c   7 frames
CAP --out bench/2026-09-21/C1a --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21/C1b :: ping -I 10.1.1.2 -c 1 -s 10000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21/C1c --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C2a/C2b/C2c   8 frames -- the ring's own depth
CAP --out bench/2026-09-21/C2a --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21/C2b :: ping -I 10.1.1.2 -c 1 -s 11000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21/C2c --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C3a/C3b/C3c   9 frames -- THE PREDICTED FIRST FAILURE
CAP --out bench/2026-09-21/C3a --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21/C3b :: ping -I 10.1.1.2 -c 1 -s 12500 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21/C3c --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C4a/C4b/C4c   10 frames
CAP --out bench/2026-09-21/C4a --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21/C4b :: ping -I 10.1.1.2 -c 1 -s 14000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21/C4c --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C5a/C5b/C5c   14 frames
CAP --out bench/2026-09-21/C5a --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21/C5b :: ping -I 10.1.1.2 -c 1 -s 20000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21/C5c --send 'cat /proc/rtl819x-nic' --seconds 25
```

⚠️ **`FW-97` applies to the host cells and is why every rung is `-c 1` with no
`-w`**: `ping -c N -w D` does not send N packets under loss. One datagram, no
deadline, so the count is not a function of the loss.

⚠️ **`FW-96`/`FW-46`**: the board's own `ping` ignores `-c` entirely. Every ping
in this block is therefore run from the **host**, where `-c` works.

---

## § 5 D5 — the throughput number

**Roles: host = server, board = client.** 量 today, reproducing
`notes/iperf3-port.md:200-205`: `qemu-mips-static ./iperf3 -s -B 10.1.1.2` binds
the real interface and `ss -ltnp` shows `LISTEN 10.1.1.2:5201`.

🔴 **Both ends must be 3.1.3.** The host's own `/usr/bin/iperf3` is **3.16**,
which is the version `NET-60` measured failing on a real 1500-byte path, and it
must not be used. The MIPS 3.1.3 at `/home/key/fwre-work/iperf3-port/iperf3` is
byte-identical to the copy in the image.

🔴 **`-b` is deliberately absent from the measurement runs.** `FW-98`'s `-b`
clause exists to make `-n` exact; D5 uses `-t`, because `-t` and `-n` are
mutually exclusive and an `-n` run has **no wall-clock bound**. `-b` appears
once, as a declared control, because on TCP it is itself a potential limiter.

**Five runs per direction, not three.** Three points cannot distinguish a spread
from one outlier. The spread is reported as min / median / max and
`(max − min) / median`, computed on the **receiver's** byte figure, and the two
directions are **never pooled**.

### 🔴 Pre-registered prediction, written before the run

Two models from the same measured saturation point
(`bench/2026-09-19b/L2-after`: 7,466 frames and 10,755,068 bytes each way in
5.79 s, re-derived here rather than copied → 1.857 MB/s each way, 2,579 fps):

* **per-byte** → ~2,410 segments/s × 1448 B = 3.49 MB/s = **27.9 Mbit/s**
* **per-packet** → 1.5 D = 2,579 → D = 1,719 fps × 1448 B = **19.9 Mbit/s**

**Host → board, single TCP stream: 20–30 Mbit/s, point estimate 25.**
**Board → host: substantially lower, 5–15 Mbit/s**, with `n_tx_stop` and
`n_xmit_busy` in the thousands — grounds: `NIC_TX_DESC` = 4, `NET-57`'s
`tx_queue_len = 0` making a stopped queue a **drop**, and `NET-63`'s measured
~3.05 fragments before the queue stops.

⚠️ The 1.88 MB/s figure in `notes/nic-driver.md` § 6 is **not** a copy rate and
is disowned as one in three places in that file. It is used here as a
*saturation point*, which is a different quantity.

**The discriminator between the two models costs two minutes**: one leg at
`mtu 600`. If Mbit/s falls with the MTU the limit is per-packet; if it holds,
per-byte.

### D5 is VOID, not "low", if any of these

1. `n_dsync > 0` at any sample — the engine desynchronised and the number
   measures `NET-61`. This is `PROGRESS.md:129`'s own stated reason.
2. `n_dsync_chk == 0` — the detector never ran.
3. `dsync_test_seen == 0`, or either control in `B4`/`B5` misses.
4. `seen_iisr` gains bit 16 or 17 — the ring starved.
5. `ΔIpExt:InTruncatedPkts > 0` — `NET-62`'s signature.
6. Any run prints `control socket has closed unexpectedly`, or the host log
   prints `WARNING: Size of data read does not correspond to offered length` —
   `NET-60`, and every number in the seating is void.
7. The figure lands within 2 % of 100 Mbit/s or of any `-b` in use — the
   instrument is the limiter.
8. `> 60 Mbit/s` — suspect a loopback short-circuit or a `-R` that did not
   reverse.
9. `(max − min) / median > 20 %` with no identified cause.
10. `unable to create a new stream` — that is the ramfs `/tmp` precondition
    (no `CONFIG_TMPFS`, no `CONFIG_SHMEM`), **not** the driver. Misattributing
    it to the driver is the specific error this condition exists to prevent.

---

## § 6 D6 — and the reason it needs a different image

🔴🔴 **`D6` cannot be met on this image, and that is a property of the image
rather than of the board.** The row asks for *zero oops* and *kernel log
captured whole*. 讀 `config/rlxfw-kernel.delta:138`:
`set@loud CONFIG_PRINTK n y`. **The quiet image has `PRINTK=n`, so `die()`
prints nothing and there is no kernel log at all.** Every image this project has
put on the silicon is the quiet one.

So D6 runs on **`s31L`**, built `--variant loud` from the same `config/`.

⚠️ **`RECIPE_ID` cannot tell the two apart** — it is a digest over `config/`
only, and the variant is not in `config/`. Both images print the same
`RLXFW-ID0`. **The discriminator is the assembled image's sha256**, asserted
through `looprun --image-sha256`, and the boot capture's length, which the loud
image changes substantially.

The flood rate is a **derived** quantity and is deliberately not a number here:

> flood rate = 60–70 % of D5's measured host → board figure, **capped at
> 18.5 Mbit/s**.

🔴 The cap is arithmetic, not taste. 讀 `netdevice.h:135-138`: `rx_bytes` is
`unsigned long` = **32 bits**, wrapping at 4,294,967,296. At `-l 1400` the
counted frame is 1442 B, so 4.295e9 / 1800 s = 2.386 MB/s = **18.5 Mbit/s**.
Above that, `rx_bytes` wraps inside the window and every before/after byte
figure is wrong by 4.295 GB, silently. Three in-band samples at 880 s make a
wrap visible and recoverable instead.

🔴 **`-l 1400`, never the 3.1.3 UDP default of 8192.** One datagram = one frame,
zero IP fragmentation, so the loss count is a pure frame count. 8192 is six
fragments per datagram — which is `H4-f6`, the rung sitting on the measured
failure boundary.

**Eight loss lines, of which the DoD's own instrument is line 2:**

```
wire loss        = sent_h - A_rx                        (ASIC port N, vendor code)
driver loss      = A_rx  - Dn_rx                        <- the DoD's own instrument
stack loss       = Dn_rx - I_rx - ARP                   (/proc/net/snmp)
truncation       = D IpExt:InTruncatedPkts              <- NET-62, invisible to the driver
socket loss      = D Udp:RcvbufErrors + InErrors
application loss = U_rx - app_rx                        (iperf3's own sequence numbers)
backlog loss     = softnet_stat col 2
CAUSE            = n_dsync, with n_dsync_chk >> 0
```

⚠️ **Unmeasured precondition, settled in the first two cells**: whether
`/proc/rtl865x/asicCounter` is clear-on-read. Two back-to-back reads with no
traffic between. If it is, the "before" sample destroys the baseline and the
protocol becomes one read at the end only.

---

## § 7 R6-6 — what one endpoint can and cannot establish

`PROGRESS.md:111`, verbatim: *"Two ports on different VLANs cannot `ping` each
other while each reaches the CPU port; **positive control**: restoring one VLAN
table restores connectivity"*.

🔴 **Two of its three clauses cannot be met tonight, for two different reasons,
and neither is procedural.**

| clause | verdict |
|---|---|
| "two ports cannot ping each other" | 🔴 **Structurally unreachable.** It needs two hosts on two jacks *simultaneously*. One cable = one port with `LinkUp` — 量, thirteen reads, thirteen times exactly one. Moving the cable tests two ports at two *times*, and the claim is about one moment. No amount of cable-moving closes it. |
| "while each reaches the CPU port" | 🟡 **Meetable sequentially, and the weakening is written down.** Port identity is read from `PSRP` on both sides of every move. |
| "restoring one VLAN **table**" | 🔴 **Unreachable for a second, independent reason: rlxfw cannot write the VLAN table at all.** 讀 `rtl819x-switch.c:88-92` — the table is reached indirectly through the TACI block, which is a protocol and not a register write. What gets restored is the **PVID register**. The *control* survives; the *object named in the DoD* does not. |

**The claim this block can actually establish**, and the one that goes in the
write-up:

> On this part, the per-port PVID field at `0xBB804A08 + (port*2 & ~3)` selects
> whether that physical port's ingress traffic reaches the CPU port, measured by
> ping in both directions with the port identity read from `PSRP` on both sides
> of every cable move; and writing the original word back restores it.

🔴 **Blast radius, and the hazard is the instrument rather than the semantics.**
讀 `rtl865x_proc_debug.c:4115-4163`: `proc_mem_write()` does
`WRITE_MEM32(mem_addr, mem_data)` with **no range check, no alignment check, no
allow-list**, and `simple_strtol` on garbage yields 0 silently. A mistyped
address is an arbitrary 32-bit store anywhere in the physical map.
**Mitigation, in every write cell**: an `echo read` of the *same* address in the
*same* cell, with the address literal appearing identically in both. Keep every
payload well under 64 characters — `tmpbuf[64]` with `tmpbuf[len]='\0'` is a
one-byte stack overflow at exactly 64.

🔴 **Stay inside `PVCR0`–`PVCR3`.** Those four are rewritten to `0x00080008` by
the loader on every boot path, so they self-heal. `VCR0`, `SWTCR1` and `PVCR4`
have no self-healing evidence and none of them is needed.
🔴 **Do not run `reset full`** anywhere: after `FULL_RST` the `PVCR`s already
read `00010001`, so a write becomes a no-op and the block reports nothing while
looking like it worked.
🔴 **Do not use `restore 0`**: slot 0 is `S0′`, latched before the vendor driver
configured the switch — **it was never a working configuration**, and 量 seating
27 it left the network dead. `snap 1` at a shell first, restore **that**.
🔴 **Budget one cold power press.** `NET-54` measured a flood-induced *ingress*
wedge surviving a watchdog reset, cleared only by a cold power-on.

### 🟢 One result this block banks at the desk, for zero power

`SPEC.md:734` `NET-10 殘留` asks which of `PSRP6`/`PSRP7` is the CPU port, and
names the experiment. Both halves are now done, 讀:
`rtl865x_asicL2.h:77-89` — `enum PORTID { PHY0=0 … PHY5=5, **CPU=6**, … }`; and
`port_status_read()` loops `port=PHY0; port<=CPU` printing `CPUPort` at
`port==CPU`. Second, independent define: `rtl865x_fdb.h:21`,
`RTL8651_CPU_PORTNUMBER = RTL8651_MAC_NUMBER = 6`.
**So `PSRP6` (`0xBB804140`) is the CPU port and `PSRP7` is not.**
⚠️ Carried, not resolved: `rtl865xc_swNic.h:155` defines `RTL8651_CPU_PORT 0x07`
— a **mask** in the TX-descriptor namespace, not a `PORTID`. Two constants with
similar names and different values; a cell must not quote the wrong one.

🔴 **And rlxfw's own switch `/proc` cannot be used to find the cable.** 量
`rtl819x-switch.c:209-213`: the census carries `PSRP0`, `PSRP3`, `PSRP5`,
`PSRP6`, `PSRP7` only — **`PSRP1`, `PSRP2`, `PSRP4` are absent**, i.e. LAN1,
LAN2 and LAN4 are invisible to it. Use `cat /proc/rtl865x/port_status`, with
`echo read 0xBB804128 36 > /proc/rtl865x/memory` as the independent second
source.

---

## § 8 What this block does NOT establish

* It does not fix `NET-61`. See § 0.
* It does not explain `NET-64`. The refutation condition is written before
  power: **if the patched image re-arms and the board still goes silent, the
  index skew was not the cause.**
* It does not close `NET-61`'s *other* residual — **which** ring leads. On an
  8-slot ring 4 is its own negative, and `nic_dsync_calc` reports how far apart,
  never which one is ahead. That is stated in the function's own comment.
* `n_dsync_chk` is ~2 × `n_napi_poll`, so `n_reads` stops being the small
  auditable number it was. 量, six consecutive dumps on the previous image:
  `n_reads` advanced by exactly **12** per `cat` (38/50/62/74/86) — six register
  reads × `FW-64`'s two `read_proc` invocations. If it moves by 6 on this
  image, every delta derived here must be re-derived.
* The detector watches the **NAPI path only**. `nic_harvest()` — the `rx` and
  `poll` verbs — is not instrumented, so a seating driven entirely through
  `/proc` would read `n_dsync_chk 0`. `dsyncchk` covers it and must be typed.
* **Zero flash-write commands, zero `FLR`.** `n_writes` on the SPI driver is
  expected 0 at every rest. The bracket stays at 0.0244 %.

---

## § 9 The cells

```cells
bench/2026-09-21/A0-rz
bench/2026-09-21/A0-ab2
bench/2026-09-21/A0-2a
bench/2026-09-21/A0-boot
bench/2026-09-21/B1-SW
bench/2026-09-21/B2-UP
bench/2026-09-21/B3-BASE
bench/2026-09-21/B4-T0
bench/2026-09-21/B5-T4
bench/2026-09-21/B6-T1
bench/2026-09-21/B7-PING
bench/2026-09-21/B8-ARM
bench/2026-09-21/B9-POST
bench/2026-09-21/B10-PING
bench/2026-09-21/C1a
bench/2026-09-21/C1b
bench/2026-09-21/C1c
bench/2026-09-21/C2a
bench/2026-09-21/C2b
bench/2026-09-21/C2c
bench/2026-09-21/C3a
bench/2026-09-21/C3b
bench/2026-09-21/C3c
bench/2026-09-21/C4a
bench/2026-09-21/C4b
bench/2026-09-21/C4c
bench/2026-09-21/C5a
bench/2026-09-21/C5b
bench/2026-09-21/C5c
```

## § 10 The numbers, every one re-derived from a file

The two image rows are the reason this fence exists: they re-derive the
digests in § 1 **from the artefacts themselves**, so a card quoting an image
that was rebuilt after the card was written cannot pass.

```cardnum
cells-fence	29	count bench/2026-09-21/PREDICTIONS-B35-block33.md ^bench/2026-09-21/(A0-[a-z0-9]+|B[0-9]+-[A-Z0-9]+|C[0-9][abc])$
declared-date	1	count bench/2026-09-21/PREDICTIONS-B35-block33.md [*][*]declared date 2026-09-21[*][*]
send-over-127	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*' -{2}idle
no-shell-subst	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*[$`]
no-ifdown	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*ifconfig rlx0 down
no-reset-full	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*reset full
no-restore-zero	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*restore 0
no-ping-dash-c-board	0	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send '[^']*ping -c
arm-cells	6	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send 'echo engine off > /proc/rtl819x-nic ; echo arm
host-cells	7	count bench/2026-09-21/PREDICTIONS-B35-block33.md ^HOST bench/2026-09-21/
dsynctest-cells	3	count bench/2026-09-21/PREDICTIONS-B35-block33.md -{2}send 'echo dsynctest
nfjrom-bytes	1153024	size /home/key/fwre-work/rebuild/imgwork/s31b/s31b/kroot/rtkload/nfjrom
nfjrom-sha256	8275a0799abce5a1	sha256-16 /home/key/fwre-work/rebuild/imgwork/s31b/s31b/kroot/rtkload/nfjrom
loud-nfjrom-bytes	1180672	size /home/key/fwre-work/rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom
loud-nfjrom-sha256	a038044da964b833	sha256-16 /home/key/fwre-work/rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom
```
