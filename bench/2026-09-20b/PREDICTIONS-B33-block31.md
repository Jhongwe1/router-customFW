# Block 33 — why a 14-fragment datagram never gets a reply, and a 6-fragment one always does

**Seating 30, **declared date 2026-09-20**, still boot 1 of power cycle 1.** No
power press, no upload, no reboot: block 32's shell is alive (`X4-live`, 41 bytes,
prompt back) and this block runs in it.

Same image throughout: `RECIPE_ID edc94765`, `nfjrom` sha256 `89051d6a396c305b…`.

---

## 0. What block 32 established, and what it did not

Block 32's ladder refuted **all three** of its pre-registered hypotheses:

| hypothesis | pre-registered discriminator | reading | verdict |
|---|---|---|---|
| interrupt storm | `n_irq` explodes | 1,936 interrupts for 5,281 frames = **2.7 frames per interrupt** | **refuted** |
| TX-queue death (`§ 0.6`) | `tx_stopped` → 1 | **0** at every rung including 41 frames; `n_tx_stop 0`, `n_xmit_busy 0`, `n_skb_fail 0` | **refuted** |
| softirq livelock | `time_squeeze` explodes | `/proc/net/softnet_stat` col 3 = **`00000000`** | **refuted** |

🟢 And it produced a two-source agreement nobody asked for: the driver's `n_rx`
**5281** and `softnet_stat`'s processed column **`0x14a1` = 5281**, byte for byte,
from counters that share no code. The switch MIB makes it three —
port 3 `Unicast 5281 pkts`.

**What it found instead** — the boundary is sharp and it is in **IP reassembly**:

| `-s` | frames per datagram | datagrams sent | replies |
|---:|---:|---:|---:|
| 1400 | 1 | 20 | **20** |
| 4000 | 3 | 20 | **20** |
| 8000 | **6** | 20 | **20** |
| 20000 | **14** | 145 | **0** |
| 60000 | **41** | 74 | **0** |

量 `/proc/net/snmp` after the ladder, against predictions written before the read:

| | predicted | read |
|---|---:|---:|
| `ReasmFails` | ≈ 219 (145 + 74) | **218** |
| `ReasmOKs` | ≈ 41 (1 + 20 + 20) | **42** |

and `218 + 42 = 260 = 145 + 74 + 41`. Three further closures are exact rather
than approximate: `FragCreates` **183** = 3 + 60 + 120, the fragments of the 41
replies the board did send; `IcmpMsg InType8` **61** = 1 + 20 + 20 + 20 (H2's
1400-byte pings need no reassembly) with `OutType0` **61**; and `InType0`/
`OutType8` **4** each, which is `C7-PING`.

**So not one of the 219 large datagrams reached ICMP.** `ReasmTimeout` is **3**,
so ~215 of the 218 failures are not timeouts.

⚠️ **And the card's own packet arithmetic was wrong in a way the measurement
survived.** `ping -c 20 -w 15` sent **145** packets, not 20: iputils' man page
says that with a deadline *"ping does not stop after count packets are sent, it
waits either for deadline expire or until count probes are **answered**"*. 145 =
15.38 s ÷ 0.106 s and 74 = 15.25 s ÷ 0.206 s, both matching `-i` exactly, so the
instrument is understood rather than merely excused — and `n_rx` closes on the
larger number (145 × 14 = 2030 against +2032; 74 × 41 = 3034 against +3035).

---

## 1. The two mechanisms left, and the single variable that separates them

量 `X3-frag`: `ipfrag_high_thresh` **262144**, `ipfrag_low_thresh` **196608**,
`ipfrag_time` **30**.

* **M1 — the memory threshold.** 讀 `net/ipv4/ip_fragment.c`: `ip_evictor()` runs
  when `ip_frag_mem` exceeds `high_thresh` and increments `IPSTATS_MIB_REASMFAILS`
  for every queue it kills, which is a `ReasmFails` that is **not** a
  `ReasmTimeout` — the shape of the 215. Each queued fragment costs its skb's
  `truesize`, so a 14-fragment datagram holds ~28 KB and 256 KB is ~9 of them.
* **M2 — something per-datagram.** Whatever it is, it fails the *first*
  14-fragment datagram, because `ReasmOKs` 42 leaves at most one of the 219 to
  have succeeded.

🟢 **`ipfrag_high_thresh` is a sysctl. It can be written, it is RAM state, it is
reversible in one line, and it touches no flash.** Raising it 16× and re-running
the identical ping is a single-variable experiment with two outcomes and no third:

| `Y3-hi14` after `high_thresh ← 4194304` | conclusion |
|---|---|
| replies come back | **M1.** The cause is the threshold, `ReasmFails` stops rising, and the fault is a *tuning* property of this kernel rather than of this driver |
| still 100 % loss | **M1 refuted.** The cause is per-datagram and the search narrows to M2 with the biggest candidate eliminated |

⚠️ **A raised threshold is not a fix and this card does not present it as one.**
It is a probe. `Y7-revert` puts it back and `Y8-post` reads it back, because a
tunable left changed is a variable in every later cell of the seating.

### The rate axis, which separates M1 from M2 a second time and independently

M1 is a *rate* mechanism: fragments pile up because they arrive faster than
datagrams complete. M2 is not. So the same 14-fragment datagram at one twentieth
of the rate is a second, independent separator that changes no tunable at all.

| `Y1-slow14` (`-i 1.0`, 5 datagrams) | conclusion |
|---|---|
| 5/5 replies | M1 — with a 1 s gap nothing can accumulate |
| 0/5 | M2 — one datagram at a time still fails |

🔴 **Running `Y1-slow14` before `Y3-hi14` matters**: if the slow rate already
works, the threshold write is unnecessary and is not performed. Cells are
one-shot, and the cheaper separator goes first.

### The fragment-count ladder, and the number it is aimed at

讀 `config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c`: `NIC_RX_DESC` is
**8**. 6 fragments fit inside one ring's worth and 14 do not, so the ring depth is
the obvious candidate for the boundary.

**Prediction, written before the rungs run: if the RX ring depth is the cause the
boundary sits between 8 and 9 fragments.** Rungs at 7, 8, 9 and 10 bracket it. If
the boundary is anywhere else — or if it moves when the rate changes — the ring
depth is refuted, and a boundary that moves with rate is M1 by yet another route.

`frames = ceil((S + 8) / 1480)`:

| `-s` | frames |
|---:|---:|
| 10000 | 7 |
| 11000 | 8 |
| 12500 | 9 |
| 14000 | 10 |

### What each `/proc/net/snmp` read is for

`ping`'s own loss figure cannot say *why*. `ReasmOKs` and `ReasmFails` **deltas**
across one rung give the exact count of datagrams that assembled and of queues
that died, and `ReasmTimeout` separates eviction from expiry. That is why every
rung is bracketed by a `snmp` read rather than scored on the host's summary.

---

## 2. The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL and writes its output to
`<prefix>.log`.

```commands
#-- Y0-snmp0  the baseline every delta below is taken against.
CAP --out bench/2026-09-20b/Y0-snmp0 --send 'cat /proc/net/snmp' --seconds 25
#-- Y1-slow14 THE RATE SEPARATOR.  14 frames per datagram, one per second.
#--           M1 predicts 5/5.  M2 predicts 0/5.
HOST bench/2026-09-20b/Y1-slow14 :: ping -I enxfc19286184c9 -c 5 -s 20000 -i 1.0 -w 10 -q 10.1.1.3
#-- Y2-snmp1  ReasmOKs delta 5 (M1) or 0 (M2); ReasmFails the complement.
CAP --out bench/2026-09-20b/Y2-snmp1 --send 'cat /proc/net/snmp' --seconds 25
#-- Y3-hi     raise the threshold 16x.  RAM state, reversible, no flash.
CAP --out bench/2026-09-20b/Y3-hi --send 'echo 4194304 > /proc/sys/net/ipv4/ipfrag_high_thresh ; cat /proc/sys/net/ipv4/ipfrag_high_thresh' --seconds 20
#-- Y4-hi14   the SAME ping that lost 100 % in block 32's H5, one variable moved.
HOST bench/2026-09-20b/Y4-hi14 :: ping -I enxfc19286184c9 -c 20 -s 20000 -i 0.1 -w 15 -q 10.1.1.3
#-- Y5-snmp2  the decisive delta.
CAP --out bench/2026-09-20b/Y5-snmp2 --send 'cat /proc/net/snmp' --seconds 25
#-- Y6-nic    tx_stopped must still be 0; if it is not, block 32's refutation of
#--           section 0.6 was load-dependent and that is a finding of its own.
CAP --out bench/2026-09-20b/Y6-nic --send 'cat /proc/rtl819x-nic' --seconds 25
#-- Y7-revert put the tunable back BEFORE the ladder, so the ladder is run at
#--           the kernel's own setting and not at this card's.
CAP --out bench/2026-09-20b/Y7-revert --send 'echo 262144 > /proc/sys/net/ipv4/ipfrag_high_thresh ; cat /proc/sys/net/ipv4/ipfrag_high_thresh' --seconds 20
#-- Y8-f7     7 frames.  Predicted to pass if the boundary is the 8-entry ring.
HOST bench/2026-09-20b/Y8-f7 :: ping -I enxfc19286184c9 -c 20 -s 10000 -i 0.05 -w 10 -q 10.1.1.3
#-- Y9-snmp3
CAP --out bench/2026-09-20b/Y9-snmp3 --send 'cat /proc/net/snmp' --seconds 25
#-- Y10-f8    8 frames.  The ring's own depth.
HOST bench/2026-09-20b/Y10-f8 :: ping -I enxfc19286184c9 -c 20 -s 11000 -i 0.05 -w 10 -q 10.1.1.3
#-- Y11-snmp4
CAP --out bench/2026-09-20b/Y11-snmp4 --send 'cat /proc/net/snmp' --seconds 25
#-- Y12-f9    9 frames.  One past the ring.
HOST bench/2026-09-20b/Y12-f9 :: ping -I enxfc19286184c9 -c 20 -s 12500 -i 0.05 -w 10 -q 10.1.1.3
#-- Y13-snmp5
CAP --out bench/2026-09-20b/Y13-snmp5 --send 'cat /proc/net/snmp' --seconds 25
#-- Y14-f10   10 frames.
HOST bench/2026-09-20b/Y14-f10 :: ping -I enxfc19286184c9 -c 20 -s 14000 -i 0.05 -w 10 -q 10.1.1.3
#-- Y15-snmp6
CAP --out bench/2026-09-20b/Y15-snmp6 --send 'cat /proc/net/snmp' --seconds 25
#-- Y16-live  41 bytes.  The shell has to have survived all of it.
CAP --out bench/2026-09-20b/Y16-live --send 'echo RLXFW-LIVE-MARK' --seconds 12
#-- Y17-soft  time_squeeze must still be 0 -- the livelock hypothesis is refuted
#--           at block 32's load and this extends the refutation to this one.
CAP --out bench/2026-09-20b/Y17-soft --send 'cat /proc/net/softnet_stat' --seconds 20
#-- Y18-asic  port 3 pause frames again: 1456 was the reading after block 32.
CAP --out bench/2026-09-20b/Y18-asic --send 'cat /proc/rtl865x/asicCounter' --seconds 35
```

No `--idle`. No `$`, `"`, backtick or `sh -c`. No `FLR`, `EW`, `EB`, `FLW`, no
burn verb, no `iperf3`, no `ifconfig rlx0 down`. The only write to the board is
the `ipfrag_high_thresh` sysctl, twice, and `Y7-revert` reads back the original
value.

---

## 3. The gate

Unchanged from block 32 after `CORRECTIONS-block30.md` § 1: **the prompt coming
back is the gate**, not the echo, because `FW-47` interleaves a mark with the
echo of the line that caused it and because a blocked shell echoes anyway
(`NET-59`, § 0.1 of block 32's card). A `snmp` cell must additionally carry an
`Ip:` line, and a host cell a `packets transmitted` line.

## 4. What this block cannot say

* It says nothing about **TCP**. `NET-59`'s subject is an `iperf3` control
  exchange and this block does not run one.
* It cannot distinguish *where* inside reassembly a queue dies. `ReasmFails`
  minus `ReasmTimeout` is eviction-or-error, and this block does not separate
  those two.
* `NIC_RX_DESC = 8` is 讀 from the driver source. Whether the hardware retires
  descriptors faster than the driver copies them is not measured here, and
  `pause 1456` on the switch's port 3 is the only evidence that anything was ever
  behind.
* **Zero flash-write commands, zero `FLR`.** `n_writes` was **14** at every read
  of block 32 and is expected to stay there: a sysctl write is not a driver write.

## 5. Stop-loss

If `Y16-live` is not 41 bytes, the ladder stops there and the seating goes to
`CORRECTIONS-block30.md` § 7's order — liveness, then `0x03`, then a ≤ 5 s power
press with the post-mortem reads of `PREDICTIONS-B31-postmortem.md`, which at that
interval are valid.

```cells
bench/2026-09-20b/Y0-snmp0
bench/2026-09-20b/Y1-slow14
bench/2026-09-20b/Y2-snmp1
bench/2026-09-20b/Y3-hi
bench/2026-09-20b/Y4-hi14
bench/2026-09-20b/Y5-snmp2
bench/2026-09-20b/Y6-nic
bench/2026-09-20b/Y7-revert
bench/2026-09-20b/Y8-f7
bench/2026-09-20b/Y9-snmp3
bench/2026-09-20b/Y10-f8
bench/2026-09-20b/Y11-snmp4
bench/2026-09-20b/Y12-f9
bench/2026-09-20b/Y13-snmp5
bench/2026-09-20b/Y14-f10
bench/2026-09-20b/Y15-snmp6
bench/2026-09-20b/Y16-live
bench/2026-09-20b/Y17-soft
bench/2026-09-20b/Y18-asic
```

```cardnum
cells-fence	19	count bench/2026-09-20b/PREDICTIONS-B33-block31.md ^bench/2026-09-20b/Y[0-9]+-[A-Za-z0-9_]+$
declared-date	1	count bench/2026-09-20b/PREDICTIONS-B33-block31.md [*][*]declared date 2026-09-20[*][*]
send-over-127	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*' -{2}idle
no-shell-subst	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*[$`]
no-ifdown	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*ifconfig rlx0 down
no-iperf3	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*iperf3
no-ping-dash-c	0	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send '[^']*ping -c
sysctl-writes	2	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send 'echo [0-9]+ > /proc/sys
snmp-cells	7	count bench/2026-09-20b/PREDICTIONS-B33-block31.md -{2}send 'cat /proc/net/snmp'
host-cells	6	count bench/2026-09-20b/PREDICTIONS-B33-block31.md ^HOST bench/2026-09-20b/Y[0-9]
```
