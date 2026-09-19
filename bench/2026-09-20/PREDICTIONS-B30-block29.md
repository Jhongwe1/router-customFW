# Block 29 — `D5` and `D6` on a link that is now measured good, and three driver defects that block 28 found the hard way

**Frozen before these cells.** Seating 29, `bench/2026-09-20/`, second card.
**declared date 2026-09-20**. Image `r6if1`, `RECIPE_ID` `edc94765`.

🔴 **This card does NOT say "frozen before power".** The board has been powered
since 01:34:18 and is at the `<RealTek>` prompt after a `busybox reboot -f`
(`X27`, `Reboot Result from Watchdog Timeout!`, **no power press**). § 0.2 names
what block 28 already did and what may be concluded from it.

---

## 0. Why there is a second card

Block 28 ran and did not reach `D5` or `D6`. It did not fail: it found a fault
and measured it. **Its cells are spent** — `console-capture` refuses an existing
`--out` and a re-run under the same names would destroy the mtime evidence
`check-predictions` scores — so the `D5`/`D6` measurement needs its own card.
`bench/2026-09-17b` carried three cards on one seating for the same reason.

### 0.1 🟢 The link was physically faulty and is now measured good

The single most important input to this card, and it is a **single-variable**
result: **nothing was changed but the cable**, re-seated at both ends, and the
switch's own port-3 receive counters moved from frozen to counting.

| port 3 RX | before (`X17`) | after (`X20`) | |
|---|---|---|---|
| `Rcv` | 600 bytes | **2,124 bytes** | +1,524 |
| `Broadcast` | 0 | **15** | +15 |
| `Multicast` | 0 | **6** | +6 |
| **`CRCAlignErr`** | 6 | **6** | **+0 — not one new error** |
| `SymbolErr` | 5 | 6 | +1, the unplug transient |

🟢 **That counter is the SWITCH's, not the driver's**, so it answers *did
anything arrive on the wire* without passing through anything that was wedged.
Before the re-seat the host sent 6 ARP replies (host `tcpdump`, `X7`) and 3 ARP
broadcasts (`X16`) and port 3 counted **none of them, not even as errors**.

⚠️ **This re-attributes `NET-54`, and the re-attribution is 推.** *"A flood once
made the interface permanently deaf, below both drivers, and only a cold
power-on recovered it"* has the same shape as what block 28 saw, and a cold
power-on involves handling the board. **Refuted by** `NET-54` reproducing on
this seating with the cable untouched.

### 0.2 What block 28 established, and what each result may be used for

| | may be used for | may NOT be used for |
|---|---|---|
| `C2-BOOT` 1,874 bytes = predicted 1,874, `RLXFW-ID0=EDC94765` | that `r6if1` is the image running, and that `bootbytes`' model holds | anything about the NIC |
| `C3-NIC0`: `version rtl819x-nic 1.1`, `n_writes 0`, `boot_icr 00000000` | that `R6-4a` is present and wrote nothing at boot | — |
| `C7`/`C8`/`X2`/`X7` ping failures | **nothing about the driver** — the link was physically faulty throughout | any conclusion about RX correctness |
| `X18`: `n_tx_stop 2`, `n_tx_wake 0`, `tx_stopped 1` | § 1's defect ① | a throughput statement |
| `X12`: `down`/`up` emits `ENGOFF`/`NDSTOP`/`ENGON`/`NDOPEN` and **no `ALLOC`/`ARM`** | § 1's defect ③ | — |
| `X27` `reboot -f` → loader in one command | `FW-37` holds on this image | — |

---

## 1. Three defects block 28 measured, and what each does to THIS card

**① `ndo_tx_timeout` cannot fire on this platform.** 讀, three lines that close
it: `net/ethernet/eth.c:349-353` — Realtek's `ether_setup` sets
`dev->tx_queue_len = 0` under `CONFIG_RTL_819X`; `net/sched/sch_generic.c:589`
gives a zero-length device `&noqueue_qdisc`; `:605-606` sets `need_watchdog`
**only when the qdisc is not noqueue**, and `:630` is the only caller of
`dev_watchdog_up()`. ∴ the watchdog timer is never started, and `X18`'s
`n_tx_timeout 0` beside `tx_stopped 1` for minutes is that, measured.
**Consequence for this card: `n_tx_timeout` is NOT a usable reading.** Block
28's card made it § 7.7's central refutation; it can only ever read 0 here, and
**a control that cannot fire proves nothing**. § 3 replaces it.

**② `NETDEV_TX_BUSY` drops the frame on this platform; it does not requeue.**
讀 `rtl819x-nic.c:880-885`, the driver's own correctness argument:
*"qdisc_restart requeues the skb … so an un-stopped queue makes `__qdisc_run`
loop and re-offer the same skb"*. `noqueue_qdisc.enqueue` is **NULL**, so
`dev_queue_xmit` never reaches `qdisc_restart` and a `NETDEV_TX_BUSY` return
ends in `kfree_skb`. **The argument is correct in general Linux and false on
this part.** 推 — no cell has yet shown a frame being dropped this way.
**This card tests it**: § 4's load is the first thing that can fill the ring.

**③ A re-opened interface resumes the DMA engine at a stale position.**
量 `X12`: `ifconfig rlx0 down ; up` printed `ENGOFF`, `NDSTOP`, `ENGON`,
`NDOPEN` and **no `RLXFW-N-ALLOC` and no `RLXFW-N-ARM`** — `ndo_open` skips both
when `nic_allocated`/`nic_armed` are already set. 量 `X23`: with the engine on,
`rpdcr0_pos` advanced `A15B1C00` → `A15B1C64` while `rx_ring` is `A15B8000`.
**The engine was reading descriptors from outside the ring and writing frame
data wherever those words pointed.** `X25`'s `ifconfig down` stopped it
(`engine_on 0`, `now_icr 04000000`, both position registers frozen — `X26`).
**Consequence for this card: no cell may `down` and `up` the interface.** Every
cell below runs on ONE `ndo_open`, from a fresh boot.

---

## 2. The boot

Re-uploaded to RAM and entered with `J 80500000`; the burn flag is read
independently first and **`00000000` is required**. Same image, so the same
prediction:

**Boot capture: 1,874 bytes**, `RLXFW-ID0=EDC94765`, `version rtl819x-nic 1.1`,
`n_writes 0`, `boot_icr 00000000`. Block 28 measured all five; a different value
here means the upload or the image changed, not the board.

⚠️ The loader banner must carry **`Reboot Result from Watchdog Timeout!`** —
absent would mean a cold power-on happened, which would make `C1` a different
experiment.

---

## 3. `D5` — the number, its method, and its spread

Board is the **client**, host the **server** (`iperf3 3.16`, the board's 3.1.3;
量 at the desk today: four interop cases, all rc 0, UDP 0/444 lost). Numeric
addresses only — 量, this image has no `/etc/hosts` and no `/etc/resolv.conf`,
and iperf3 opens neither on the numeric path.

**Five forward runs and one reverse, 10 s each**, over switch port 3 (LAN3),
100 Mbit. **The number is an UNCACHED-RING number** — `rtl819x-nic.c:93-110`
pre-registers that rings, descriptors **and packet buffers** are all KSEG1.

| | predicted | refuted by |
|---|---|---|
| a number exists | `bits_per_second` present in all six `-J` documents | `unable to create a new stream` — which would be `/tmp` or ramfs `ftruncate`, **not** the driver |
| spread | the five forward runs' relative standard deviation is stated with the median, whatever it is | — |
| `Retr`/`Cwnd` | plausible: `Cwnd` a small multiple of the MSS, `Retr` small and non-decreasing | 🔴 a huge or negative `Retr`, or `Cwnd 0.00 Bytes`. 量 today under qemu the same binary printed `Retr 4290268386`, `Cwnd 1.98 GBytes`, `max_rtt 724226048` — **that is the instrument's signature and this is its reference value** |
| both directions | `-R` completes | RX and TX are different paths and one can be fine while the other is not |

🔴 **`n_tx_timeout` is not read as a verdict** (defect ①). The TX-path verdict on
this card is `n_tx_stop`, `n_tx_wake`, `n_tx_wake_race`, `n_xmit_busy` and
`tx_stopped`, which are the driver's own and do fire.

## 4. The curve, and whether the number is the DRIVER's or the SoC's

A bare throughput figure on this driver reports a **memory** limit while looking
like a **driver** limit, because every byte crosses `cached skb → uncached
KSEG1 buffer` and back. Three levers, each failing differently:

**① `/proc/stat`, before and after each run.** 量 today it exists:
`fs/proc/stat.c:154` registers it, and the staged `/init` mounts `/proc`. The
`cpu ` line has **nine** fields after **two** spaces — `user nice system idle
iowait irq softirq steal guest` — in clock ticks at `HZ=100`.
`idle_frac = Δidle / ΣΔ`.
⚠️ **`softirq` and `system` are read separately, not summed.** NIC RX runs in
softirq: 0 % idle with the time in `softirq` is a *driver* cost; 0 % idle with
it in `system` is the copy and the stack. A bare idle fraction throws that away.

**② `-Z` (zerocopy) — a controlled experiment, not an observation.** 量, the
binary advertises `sendfile / zerocopy`; `-Z` swaps `write()` for `sendfile()`
and removes `copy_from_user` entirely.
**`-Z` raises throughput ⇒ the copy was binding. `-Z` changes nothing ⇒ it was
not, and the limit is the driver or the link.** This *changes* the suspected
cause instead of measuring a correlate, which is why it outranks ①.

**③ A UDP offered-load ladder** at 5 / 10 / 20 / 50 M and unlimited: achieved
rate, loss, and the `/proc/stat` pair at each point.

🔴 **iperf3's own `cpu_utilization_percent` is NOT used as the discriminator.**
讀 `iperf_util.c` `cpu_util()`: it is `getrusage(RUSAGE_SELF)` plus `clock()`,
and **`RUSAGE_SELF` excludes softirq and hard-IRQ time**. It can read well under
100 % while the CPU is pinned. It is recorded beside `/proc/stat` because **the
gap between them is the interrupt and softirq cost**, which neither gives alone.

## 5. `D6` — 30 minutes of continuous flood

One 1,800 s TCP stream, `-i 10`, **straight to the console and NOT redirected
and NOT `-J`**.

🔴 **That is a correction to block 28's design, and the reason is measured.**
讀 `iperf_api.c:2631-2632`: the per-interval flush is `if (test->logfile)
iflush(test)` — **conditional on `--logfile`**, and 3.1.3 has no
`--forceflush`. 量 today, three regimes with a control: to a **file**, `size=0
lines=0` for eleven consecutive polls over 5.1 s and then 850 bytes in one step;
to a **tty**, lines arrive 1 s apart. **So `> file` on a 30-minute flood returns
an empty file if the board resets, and `-J` is worse — one document at exit.**
Block 28's `C31-FSTART` redirected to a file; this card does not.

`-i 10` and not `-i 1`: 180 lines instead of 1,800, and console writes are CPU
the measurement would otherwise absorb.

| | predicted | refuted by |
|---|---|---|
| drops | `nd_stats drop 0/0`, `n_skb_fail 0`, `n_irq_spurious 0` | any non-zero — `D6` fails and is reported failed |
| **defect ②** | 🔴 **`n_xmit_busy` and `n_tx_stop` are expected to MOVE.** This is the first load with a real window; seating 28's floods were ping-bound and read `n_xmit_busy 0` | staying 0 ⇒ the stop path is still unreached and `R6-4a` is untested under load — **a narrower result, not a pass** |
| **the wake** | `n_tx_wake + n_tx_wake_race >= n_tx_stop`, and the stream still running at the end | `n_tx_stop > 0` with both wake counters 0 ⇒ the wake site is wrong. **This is the refutation that replaces `n_tx_timeout`**, because ① makes that one unable to fire |
| oops | **zero, and it is evidenceable**: `arch/rlx/kernel/traps.c:52` is `#define printk panic_printk` with `CONFIG_PANIC_PRINTK=y`, so `die()` reaches the console even at `CONFIG_PRINTK=n`; and `CONFIG_RTL_WTDOG=n` means `is_fault` is never set, so a panic **prints and stays** instead of truncating at ~46 characters | any `die`/register dump in the capture |
| kernel log | **whole** — every cell is an ungrepped console capture, and on this image the console *is* the log | — |
| two sources | `Σ Δnd_stats tx_bytes` (wrap-corrected) against `Δ asicCounter Snd` | disagreement ⇒ § 6 ②'s `<< 22` is the first suspect |

Counters are sampled at ~180 s, **below the 343.6 s wrap** of the 32-bit
`nd_stats` byte counters, so every interval is unambiguous without knowing the
rate first — and no console gap approaches `C-19`'s 7 min 24 s.

## 6. Hazards carried forward from block 28

**① No `ifconfig down`/`up` anywhere on this card** — defect ③.
**② `asicCounter`'s "64-bit" value is `lo + (hi << 22)`**, 讀
`rtl865x_asicCom.c:1500-1510`, the `CONFIG_RTL_8196E` branch. 推 that the low
register holds 22 valid bits. 🟢 **It is NOT read-to-clear** — 讀 three ways, and
量 across block 28's six reads the counters accumulated monotonically. **No
`clear` is issued.**
**③ `cat /proc/rtl865x/asicCounter > file` gives a ZERO-BYTE file** — the
handler returns `len = 0` and writes to the console. Every such cell uses
`--until CpuEvent`.
**④ `ping` ignores `-c` and always sends four** (`NET-26`).
**⑤ `TRXRDY` is cleared by a link event.** 量 `X19`: `SSIR` read `00000000`
after the cable re-seat, having read `00000001` before. `C3` re-asserts it after
the boot and `C4` reads it back.
**⑥ No `$`, `"`, backtick or `sh -c` in any `--send`** — `cardcheck`'s `B9`
sweeps the whole corpus.
**⑦ No cell carries `--idle`.** Ten begin with a `sleep`.

---

## 7. What this block does NOT claim

1. It does not isolate why the cable failed. It measures that it did and that
   re-seating fixed it.
2. It does not fix defects ①–③. It measures around them and states which
   readings they invalidate.
3. It does not measure the vendor driver's throughput — `eth4` cannot open
   while my driver holds a non-shared `request_irq(12)` (量 `X9`:
   `SIOCSIFFLAGS: Device or resource busy`), so there is no contrast number.
4. It does not attribute the CPU cost to the KSEG1 copy. `-Z` bounds it; a
   cached-buffer build would attribute it, and that is a different image.
5. `ph_queueId`'s layout is still inherited from a declaration nothing has
   executed. These frames are default-MTU.

---

## 8. The cells

`CAP` expands to
`/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.

```
#-- 1. the burn flag, independently of the rescue transcript.  00000000 REQUIRED.
CAP --out bench/2026-09-20/D1-BURN --send 'DW 8040D4A0 1' --until 'RealTek>' --seconds 15

#-- 2. the boot.  1874 bytes, RLXFW-ID0=EDC94765, and the banner must say Watchdog.
CAP --out bench/2026-09-20/D2-BOOT --send 'J 80500000' --seconds 45

#-- 3. TRXRDY.  Hazard 5: a link event clears it and X19 measured that.
CAP --out bench/2026-09-20/D3-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 30

#-- 4. read it back.  SSIR bit 0 must be 1.
CAP --out bench/2026-09-20/D4-SWRB --send 'cat /proc/rtl819x-switch' --seconds 30

#-- 5. ONE ndo_open for the whole card.  Defect 3: no down/up anywhere below.
CAP --out bench/2026-09-20/D5-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 35

#-- 6. cold ARP: n_tx 5 (one ARP + four ICMP).  The link is now measured good.
CAP --out bench/2026-09-20/D6-PING1 --send 'ping 10.1.1.2' --seconds 25

#-- 7. warm ARP: n_tx 4.  Two pings, because the ring is four deep.
CAP --out bench/2026-09-20/D7-PING2 --send 'ping 10.1.1.2' --seconds 25

#-- 8. the baseline for every delta on this card.
CAP --out bench/2026-09-20/D8-BASE --send 'cat /proc/rtl819x-nic' --seconds 25

#-- 9. the txstall positive control.  n_tx_stop must move; n_tx_timeout may NOT
#--    be read as a verdict (defect 1 -- the watchdog timer never starts here).
CAP --out bench/2026-09-20/D9-STALL --send 'echo txstall on > /proc/rtl819x-nic ; ping 10.1.1.2 ; ping 10.1.1.2 ; cat /proc/rtl819x-nic' --seconds 45

#-- 10. two writes: restore TXCMD and ring TXFD.  now_icr back to C4000000.
CAP --out bench/2026-09-20/D10-OFF --send 'echo txstall off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 30

#-- 11. txstall's OWN refutation: no recovery here and the control is VOID.
CAP --out bench/2026-09-20/D11-RECOV --send 'ping 10.1.1.2 ; cat /proc/rtl819x-nic' --seconds 35

#-- 12. asicCounter zero point.  --until CpuEvent: the handler returns len 0.
CAP --out bench/2026-09-20/D12-AC0 --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40

#-- 13,14. D5.  /proc/stat brackets every run; iperf3's own cpu number is NOT
#--         the discriminator (getrusage excludes softirq).
CAP --out bench/2026-09-20/D13-ST0 --send 'cat /proc/stat' --seconds 25
CAP --out bench/2026-09-20/D14-IP1 --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J' --seconds 50

#-- 15..20. four more forward runs and the reverse, each bracketed by /proc/stat.
CAP --out bench/2026-09-20/D15-IP2 --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J' --seconds 50
CAP --out bench/2026-09-20/D16-IP3 --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J' --seconds 50
CAP --out bench/2026-09-20/D17-IP4 --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J' --seconds 50
CAP --out bench/2026-09-20/D18-IP5 --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J' --seconds 50
CAP --out bench/2026-09-20/D19-ST1 --send 'cat /proc/stat' --seconds 25
CAP --out bench/2026-09-20/D20-IPR --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J -R' --seconds 50

#-- 21..23. the controlled experiment: -Z removes copy_from_user entirely.
#--         Higher => the copy was binding.  Unchanged => it was not.
CAP --out bench/2026-09-20/D21-ST2 --send 'cat /proc/stat' --seconds 25
CAP --out bench/2026-09-20/D22-IPZ --send 'iperf3 -c 10.1.1.2 -t 10 -i 1 -f m -J -Z' --seconds 50
CAP --out bench/2026-09-20/D23-ST3 --send 'cat /proc/stat' --seconds 25

#-- 24..28. the offered-load ladder.
CAP --out bench/2026-09-20/D24-U5 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 5M -f m -J' --seconds 50
CAP --out bench/2026-09-20/D25-U10 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 10M -f m -J' --seconds 50
CAP --out bench/2026-09-20/D26-U20 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 20M -f m -J' --seconds 50
CAP --out bench/2026-09-20/D27-U50 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 50M -f m -J' --seconds 50
CAP --out bench/2026-09-20/D28-U0 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 0 -f m -J' --seconds 50

#-- 29,30,31. the flood's zero points, then D6 itself: ONE 1800 s stream, to the
#--           tty, NOT redirected and NOT -J, because a redirect is block-buffered.
CAP --out bench/2026-09-20/D29-F0 --send 'cat /proc/rtl819x-nic' --seconds 25
CAP --out bench/2026-09-20/D30-FST --send 'cat /proc/stat' --seconds 25
CAP --out bench/2026-09-20/D31-FLOOD --send 'iperf3 -c 10.1.1.2 -t 1800 -i 10 -f m' --seconds 1860

#-- 32..35. the flood's end points, and the NET-54 liveness check.
CAP --out bench/2026-09-20/D32-FNIC --send 'cat /proc/rtl819x-nic' --seconds 25
CAP --out bench/2026-09-20/D33-FST1 --send 'cat /proc/stat' --seconds 25
CAP --out bench/2026-09-20/D34-FAC --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
CAP --out bench/2026-09-20/D35-FPING --send 'ping 10.1.1.2' --seconds 25

#-- 36. errors:N here is not a hardware error -- but defect 1 means ndo_tx_timeout
#--     cannot have incremented it, so a non-zero errors count is a DIFFERENT cause.
CAP --out bench/2026-09-20/D36-FIFC --send 'ifconfig rlx0' --seconds 25
```

### 8.1 The numbers this card states, and where each is re-derived FROM

```cardnum
cells-fence	36	count bench/2026-09-20/PREDICTIONS-B30-block29.md ^bench/2026-09-20/D[0-9]+-[A-Za-z0-9_]+$
image-bytes	1152000	size /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom
image-sha16	89051d6a396c305b	sha256-16 /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom
iperf3-bytes	252644	size build/rlxfw-user/iperf3/iperf3
declared-date	1	count bench/2026-09-20/PREDICTIONS-B30-block29.md [*][*]declared date 2026-09-20[*][*]
send-over-127	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*' -{2}idle
no-shell-subst	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*[$`]
no-asic-clear	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*echo clear
no-ping-dash-c	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*ping -c
no-ifdown	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*ifconfig rlx0 down
no-redirect-flood	0	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*iperf3[^']*>
iperf-cells	13	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send '[^']*iperf3 -c
procstat-cells	6	count bench/2026-09-20/PREDICTIONS-B30-block29.md -{2}send 'cat /proc/stat'
```

**`no-ifdown` and `no-redirect-flood` are new**, and each is a block-28 defect
turned into arithmetic: defect ③ says no cell may re-open the interface, and
§ 5's buffering measurement says the flood may not be redirected. A guard the
card can check beats a guard the card promises.

## 9. The fence

```cells
bench/2026-09-20/D1-BURN
bench/2026-09-20/D2-BOOT
bench/2026-09-20/D3-SW
bench/2026-09-20/D4-SWRB
bench/2026-09-20/D5-UP
bench/2026-09-20/D6-PING1
bench/2026-09-20/D7-PING2
bench/2026-09-20/D8-BASE
bench/2026-09-20/D9-STALL
bench/2026-09-20/D10-OFF
bench/2026-09-20/D11-RECOV
bench/2026-09-20/D12-AC0
bench/2026-09-20/D13-ST0
bench/2026-09-20/D14-IP1
bench/2026-09-20/D15-IP2
bench/2026-09-20/D16-IP3
bench/2026-09-20/D17-IP4
bench/2026-09-20/D18-IP5
bench/2026-09-20/D19-ST1
bench/2026-09-20/D20-IPR
bench/2026-09-20/D21-ST2
bench/2026-09-20/D22-IPZ
bench/2026-09-20/D23-ST3
bench/2026-09-20/D24-U5
bench/2026-09-20/D25-U10
bench/2026-09-20/D26-U20
bench/2026-09-20/D27-U50
bench/2026-09-20/D28-U0
bench/2026-09-20/D29-F0
bench/2026-09-20/D30-FST
bench/2026-09-20/D31-FLOOD
bench/2026-09-20/D32-FNIC
bench/2026-09-20/D33-FST1
bench/2026-09-20/D34-FAC
bench/2026-09-20/D35-FPING
bench/2026-09-20/D36-FIFC
```
