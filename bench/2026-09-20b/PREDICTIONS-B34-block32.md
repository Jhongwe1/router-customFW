# Block 34 — how many frames in one burst desynchronise the two RX rings

**Seating 30, **declared date 2026-09-20**, boot 2.** Reached by
`busybox reboot -f` — 量 `FW-37`, 2.407 s to the loader prompt — **not by a power
press**. Same image, `RECIPE_ID edc94765`.

---

## 0. What this block is aimed at

`CORRECTIONS-block31.md` § 2 closes eight of nine links of a chain: a multi-frame
burst raises `MBUF_RUNOUT`, the engine's two RX position registers desynchronise
by exactly 4, the driver indexes both rings with one variable, frames are then
delivered carrying another frame's length, and `ip_rcv` drops them as
`InTruncatedPkts` — a counter that is **not** in `/proc/net/snmp`, which is why
every visible drop counter read 0 while one fragment per datagram vanished.

量, the repair and its undoing, in one pair of reads:

| | `rp` idx | `rm` idx | Δ |
|---|---:|---:|---:|
| `Z7-nic`, before `arm` | 7 | 3 | **4** |
| `Z10-nic`, after `arm`, **no traffic** | 0 | 0 | **0** |
| `Z14-nic2`, after **one** 6-frame ping run | 0 | 4 | **4** |

**So the state is repairable and re-breakable and the trigger is a burst.** Two
things that closes are not:

1. **How big a burst.** Block 32 sampled 6 (clean) and 14 (broken) on the same
   boot and block 31's ladder had no baseline, so 7, 8, 9 and 10 are untested
   from a known-good state.
2. **Whether `arm` alone restores the SYMPTOM.** It does not: `Z11-f6` was
   **11 / 181** where the byte-identical `H4-f6` had been **20 / 20** an hour
   earlier on the same boot. Either something else accumulates, or the rings
   re-desynchronise inside the first few datagrams.

---

## 1. The design, and why it is not a ladder

Block 31's ladder failed because each rung inherited the previous rung's state.
This block makes every rung an **independent trial**:

> `arm` (Δ ← 0) → **one** datagram → read Δ.

`ping -c 1` emits one datagram, which the board reassembles and answers with one
burst of `ceil((S+8)/1480)` frames. One burst in, one burst out, one register
read. Nothing accumulates across rungs because every rung starts from a repaired
ring pair.

🟢 **The instrument is Δ, not packet loss.** Δ is a live read of two hardware
registers and is a state, not a count, so it needs no baseline arithmetic and
cannot be confounded by the host's `-c`/`-w` interaction. `seen_iisr` is a
sticky OR and is therefore **useless** per-rung once bit 16 has ever been set —
recorded here so that nobody later reads it as a per-rung signal.

### Predictions, written before the first packet

讀 `config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c:351`:
`NIC_RX_DESC` is **8**.

> **A burst of N frames desynchronises the rings for the first time at N = 9**,
> the first N greater than the ring depth.

| rung | `-s` | frames | Δ predicted |
|---|---:|---:|---:|
| `L1` | 1400 | 1 | 0 |
| `L2` | 8000 | 6 | 0 |
| `L3` | 10000 | 7 | 0 |
| `L4` | 11000 | 8 | 0 |
| `L5` | 12500 | **9** | **≠ 0** |
| `L6` | 14000 | 10 | ≠ 0 |
| `L7` | 20000 | 14 | ≠ 0 |

**What refutes it.** Δ ≠ 0 at 7 or 8 frames; or Δ = 0 at 9, 10 **and** 14, which
would mean one datagram is never enough and the trigger is cumulative; or Δ
taking a value other than 4, which would mean the offset is not a property of the
ring depth.

⚠️ **A negative at every rung is a result, not a failure.** It would say the
trigger needs sustained traffic rather than one burst, and the next block would
raise `-c` rather than `-s`.

### And one thing this block settles for free

`R6-BASE` and `R8-B0` re-run the byte-identical `H4-f6` on a **fresh boot**. If
it is 20/20 again, the degradation is accumulated state that a boot clears and
`arm` does not — which is the open question `Z11-f6` created.

---

## 2. The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL, output to `<prefix>.log`.

```commands
#-- R0-REBOOT  busybox reboot -f.  FW-37: 2.407 s to the loader prompt, and it
#--            is a watchdog bite (FW-45), so the banner MUST carry
#--            'Reboot Result from Watchdog Timeout!'.  --esc-after catches the
#--            prompt; without it the loader auto-boots the VENDOR image, which
#--            a reset has re-staged at 0x80500000.
CAP --out bench/2026-09-20b/R0-REBOOT --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until 'RealTek>' --seconds 45
#-- R1-BURN    AFTER the rescue, never before: AUTOBURN powers on to 1 and a
#--            reset puts it back (CORRECTIONS-block30 section 0).  00000000.
CAP --out bench/2026-09-20b/R1-BURN --send 'DW 8040D4A0 1' --until 'RealTek>' --seconds 15
#-- R2-HEAD    the staged head after the upload.
CAP --out bench/2026-09-20b/R2-HEAD --send 'DW 80500000 8' --until 'RealTek>' --seconds 15
#-- R3-BOOT    1,874 bytes, RLXFW-ID0=EDC94765.
CAP --out bench/2026-09-20b/R3-BOOT --send 'J 80500000' --seconds 45
#-- R4-SW
CAP --out bench/2026-09-20b/R4-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 20
#-- R5-UP      N-ALLOC and N-ARM both required.
CAP --out bench/2026-09-20b/R5-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- R6-BASE    rp idx == rm idx == 0 on a fresh boot, seen_iisr WITHOUT bit 16.
CAP --out bench/2026-09-20b/R6-BASE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- R7-NET0    InTruncatedPkts baseline -- 0 on a fresh boot.
CAP --out bench/2026-09-20b/R7-NET0 --send 'cat /proc/net/netstat' --seconds 25
#-- R8-B0      THE FRESH-BOOT BASELINE, byte-identical to H4-f6 which was 20/20.
HOST bench/2026-09-20b/R8-B0 :: ping -I enxfc19286184c9 -c 20 -s 8000 -i 0.05 -w 10 -q 10.1.1.3
#-- R9-NB0     Delta after 20 six-frame datagrams.
CAP --out bench/2026-09-20b/R9-NB0 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A1         repair, then ONE 1-frame datagram.
CAP --out bench/2026-09-20b/A1 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L1 :: ping -I enxfc19286184c9 -c 1 -s 1400 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N1 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A2         6 frames.
CAP --out bench/2026-09-20b/A2 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L2 :: ping -I enxfc19286184c9 -c 1 -s 8000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N2 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A3         7 frames.
CAP --out bench/2026-09-20b/A3 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L3 :: ping -I enxfc19286184c9 -c 1 -s 10000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N3 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A4         8 frames -- the ring's own depth.
CAP --out bench/2026-09-20b/A4 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L4 :: ping -I enxfc19286184c9 -c 1 -s 11000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N4 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A5         9 frames -- THE PREDICTED FIRST FAILURE.
CAP --out bench/2026-09-20b/A5 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L5 :: ping -I enxfc19286184c9 -c 1 -s 12500 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N5 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A6         10 frames.
CAP --out bench/2026-09-20b/A6 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L6 :: ping -I enxfc19286184c9 -c 1 -s 14000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N6 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A7         14 frames -- block 32's H5, reduced to one datagram.
CAP --out bench/2026-09-20b/A7 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-20b/L7 :: ping -I enxfc19286184c9 -c 1 -s 20000 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-20b/N7 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- R10-NET1   InTruncatedPkts after the whole ladder.
CAP --out bench/2026-09-20b/R10-NET1 --send 'cat /proc/net/netstat' --seconds 25
#-- R11-LIVE
CAP --out bench/2026-09-20b/R11-LIVE --send 'echo RLXFW-LIVE-MARK' --seconds 12
```

Off-card, between `R0-REBOOT` and `R1-BURN`, exactly as block 30 declared them:

```
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-20b/R0-rescue.json
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom --filename r6if1 --rescue-report bench/2026-09-20b/R0-rescue.json --expect-load 80500000 --yes
```

No `--idle`. No `$`, `"`, backtick or `sh -c`. No `FLR`, `EW`, `EB`, `FLW`, no
burn verb, no `iperf3`, no `ifconfig rlx0 down`. **Zero flash-write commands.**

---

## 3. The gate

The prompt coming back, as `CORRECTIONS-block30.md` § 1 established. An `A*` cell
must additionally emit `RLXFW-N-ARM=A15B8000` (subsequence test, `FW-47`), an
`N*` cell must carry `rpdcr0_pos`, and `R3-BOOT` must be 1,874 bytes with
`RLXFW-ID0=EDC94765`.

## 4. What this block cannot say

* It cannot say *why* the offset is 4 rather than some other number. That is
  a property of the engine's mbuf allocation and is not read here.
* It cannot separate "the mbuf ring runs out" from "the packet-header ring runs
  out" — `NIC_IE_PKTHDR_RUNOUT` is bits 17–22 and `seen_iisr` carries
  `0001320E`, whose bit 16 is the mbuf side, but a per-rung reading of the
  *other* side is not taken.
* It says nothing about TCP or about `NET-59`'s `iperf3` control exchange.
* It does not fix anything. **A fix belongs in a different image from the
  measurement that characterises the fault.**

## 5. Stop-loss

If `R8-B0` is not 20/20 on a fresh boot, the "accumulated state" reading is
refuted, the ladder is still run because Δ does not depend on it, and the seating
stops afterwards rather than opening a third front.

```cells
bench/2026-09-20b/R0-REBOOT
bench/2026-09-20b/R1-BURN
bench/2026-09-20b/R2-HEAD
bench/2026-09-20b/R3-BOOT
bench/2026-09-20b/R4-SW
bench/2026-09-20b/R5-UP
bench/2026-09-20b/R6-BASE
bench/2026-09-20b/R7-NET0
bench/2026-09-20b/R8-B0
bench/2026-09-20b/R9-NB0
bench/2026-09-20b/A1
bench/2026-09-20b/L1
bench/2026-09-20b/N1
bench/2026-09-20b/A2
bench/2026-09-20b/L2
bench/2026-09-20b/N2
bench/2026-09-20b/A3
bench/2026-09-20b/L3
bench/2026-09-20b/N3
bench/2026-09-20b/A4
bench/2026-09-20b/L4
bench/2026-09-20b/N4
bench/2026-09-20b/A5
bench/2026-09-20b/L5
bench/2026-09-20b/N5
bench/2026-09-20b/A6
bench/2026-09-20b/L6
bench/2026-09-20b/N6
bench/2026-09-20b/A7
bench/2026-09-20b/L7
bench/2026-09-20b/N7
bench/2026-09-20b/R10-NET1
bench/2026-09-20b/R11-LIVE
```

```cardnum
cells-fence	33	count bench/2026-09-20b/PREDICTIONS-B34-block32.md ^bench/2026-09-20b/([ANLR][0-9]+|R[0-9]+-[A-Za-z0-9_]+)$
declared-date	1	count bench/2026-09-20b/PREDICTIONS-B34-block32.md [*][*]declared date 2026-09-20[*][*]
send-over-127	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*' -{2}idle
no-shell-subst	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*[$`]
no-ifdown	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*ifconfig rlx0 down
no-iperf3	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*iperf3
no-ping-dash-c	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send '[^']*ping -c
no-sysctl	0	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send 'echo [0-9]+ > /proc/sys
arm-cells	7	count bench/2026-09-20b/PREDICTIONS-B34-block32.md -{2}send 'echo engine off > /proc/rtl819x-nic ; echo arm
host-cells	8	count bench/2026-09-20b/PREDICTIONS-B34-block32.md ^HOST bench/2026-09-20b/[LR][0-9]
```
