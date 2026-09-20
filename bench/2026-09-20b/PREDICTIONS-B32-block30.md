# Block 32 — `R6-5`, second attempt: what `NET-59` actually is

**Seating 30, **declared date 2026-09-20**, boot 1 of power cycle 1.** The board
is already at the loader prompt (`PREDICTIONS-B31-postmortem.md` § 1); this block
uploads and boots and needs **no further power press** unless § 7 fires.

Image: `$FWRE_WORK/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom`,
**1,152,000 bytes**, sha256 `89051d6a396c305b…`, `RECIPE_ID edc94765` — the same
image seating 29 ran, unchanged and deliberately so: this block characterises a
fault and must not also change the thing it is characterising.

---

## 0. Why this block exists: `SPEC.md` `NET-59` is wrong in four places, and every refutation comes out of captures seating 29 itself committed

Nothing in this section was measured today. All of it was measured on
2026-09-20 between 02:27 and 03:26 and written up as something else.

### 0.1 "console 完全靜默" — refuted by the board's own echo

量 `bench/2026-09-20/X35-rebootry.log`: **7,489 bytes came back off the port**
while the board was supposedly wedged. Byte census: `busybox reboot -f\r\n`
(19 B) + `^` × 3,735 + `[` × 3,735 (7,470 B). 19 + 7,470 = 7,489, exactly.

`^[` is N_TTY's `ECHOCTL` rendering of ESC. 量: the log holds **zero** raw `0x1B`
bytes. So all 3,735 ESC characters were received by the board's Linux tty, passed
through the line discipline, rendered, and echoed back out the UART.

🟢 **The control is inside another capture from the same night.**
`bench/2026-09-20/X36-escwin2.log`: before the reset the ESC stream comes back as
`^[`; after `Booting...` the identical stream comes back as raw `\x1b` from the
loader. Same port, same tool, two renderings — so the `^[` is Linux's line
discipline and not an artefact of the instrument.

讀 `tools/console-capture.py:563`: `log.write(chunk)` writes only bytes `read()`
from the port, and `ser.write()` is a separate path. **Those bytes came off the
board.**

### 0.2 "`X34`: 100 秒不送任何東西, 0 bytes" — that is the instrument's own input

量 `X34-listen.meta.json`: `"sent": null`. The cell typed **nothing**. A capture
that sends nothing to a quiet board gets nothing back. The row quotes the
instrument's null as the board's behaviour.

### 0.3 "`CONFIG_RTL_WTDOG=n` 代表沒有上膛的看門狗" — refuted by the boot that hung

`CONFIG_RTL_WTDOG` is the **vendor's** watchdog. 量 `bench/2026-09-20/D2-BOOT.log`,
the boot that later hung: `RLXFW-W3=00000000` (BOOTGUARD entered, rc 0) and
**`RLXFW-W4=00240000`** — `WDTCNR` read back running at OVSEL 9, which 量 seating
18 rung 9 is **84,001 ms**. 量 `grep` over every `"sent"` in that seating's
`*.meta.json`: no watchdog verb was typed, so nothing disarmed it.

`D15-IP2` (02:58:30) to the operator's cold press (03:18:13) is **1,183 s = 14
consecutive missed 84 s deadlines and zero bites.** 量 `grep -c` for
`RealTek|Reboot Result|ramSize|Booting` over all nineteen captures `D15`…`X35`:
**0**. The kick is a `timer_list` in the timer softirq. **It never stopped, so the
kernel's timer wheel ran for the whole "hang".**

### 0.4 🔴🔴 And the title names an event that never happened

量, the complete set of what came back from every `iperf3` cell of that seating:

| cell | sent | bytes | what came back |
|---|---|---:|---|
| `D14-IP1` | `-t 10 -i 1 -f m -J` | 525 | a **complete** JSON ending `"error": "control socket has closed unexpectedly"`, then `# ` |
| `X44-l8k` | `-t 2 -f m -l 8K` | 134 | `Connecting to host 10.1.1.2, port 5201`, the same error, then `# ` |
| `X45-l32k` | `-t 2 -f m -l 32K` | 37 | the echo, and nothing else — not even `Connecting to host` |

**Every run died in the control exchange. Not one byte of bulk TCP has ever been
carried by this board.** The row's title — *一個真正的 TCP 負載會把整台板子掃住* —
names a load that was never applied.

The row's one controlled comparison goes with it: `X44` (`-l 8K`) lost its control
socket **before any stream object was created**, so no block of any size was
written in either run. `-l` is not what separates them; **49 seconds of board
state is.**

### 0.5 What the record does support

量 `X18-nic` (02:27:30) against `X21-nic` (02:41:01) — 13 min 31 s apart, same
boot, nothing typed between them but three reads:

| field | `X18` | `X21` |
|---|---|---|
| `n_irq` | 30 | **30** |
| `n_tx` | 27 | 27 |
| `n_rx` | 7 | 7 |
| `n_tx_stop` | 2 | 2 |
| `n_tx_wake` | **0** | **0** |
| `n_tx_timeout` | 0 | 0 |
| `tx_stopped` | **1** | **1** |
| `now_iimr` | 007E0FFE | 007E0FFE |
| `now_iisr` | 00000000 | **80000008** |
| `rpdcr0_pos` | A15B1C00 | **A15B1C54** |

🔴 **`n_irq` is a constant across 13.5 minutes. The interrupt-storm hypothesis is
refuted by a capture taken before the hypothesis was written down.**

🔴 `tx_stopped` was 1 for 13.5 minutes with `n_tx_wake` 0. 讀 `rtl819x-nic.c:726`:
the only live call to `nic_tx_try_wake()` is inside the ISR. 讀 `NET-57`:
`ndo_tx_timeout` is unreachable because `net/ethernet/eth.c:349` sets
`tx_queue_len = 0` under `CONFIG_RTL_819X`, so `dev_watchdog_up()` is never
called. **A stopped queue with no interrupt coming has nothing that can restart
it.**

🔴 `now_iisr 80000008`, bit 3 set *and unmasked* in `now_iimr 007E0FFE`, while
`n_irq` did not move: a pending, enabled cause that produced no interrupt.

⚠️ **Marked honestly: `X18`/`X21` are 30 minutes BEFORE the first `iperf3` cell**,
and that boot carried the `NET-56` cable fault and `NET-58`'s loose engine
(`tpdcr0_pos A1FD1400` against `tx_ring A15B8040` — 4.3 MB outside the ring). So
the table is evidence about *a* stopped-TX state, not about the iperf3 event. It
is the strongest thing in the record and it is still not the measurement this
block has to take.

### 0.6 The replacement hypothesis, stated so it can be killed

> 推 — **the board does not hang.** `rlx0`'s transmit queue stops
> (`nic_xmit:847-888` → `netif_stop_queue()` + `NETDEV_TX_BUSY`), the only thing
> that can restart it is an interrupt, and `ndo_tx_timeout` cannot fire. With the
> queue stopped and no further interrupt, TX is dead; `tcp_sendmsg` blocks in
> `sk_stream_wait_memory()` **with no timeout**; the foreground process never
> returns; the shell never returns to its prompt; and everything typed afterwards
> is echoed by the line discipline into a canonical buffer nobody reads.
>
> 推 — the variable is **how many frames the stack hands to `ndo_start_xmit`
> back-to-back** against a **4**-entry TX ring, not how many bytes move.

---

## 1. Why the first rung is not `iperf3`

The carried-forward plan is `iperf3 -c 10.1.1.2 -n 64K`, doubling. It stays frozen
as `SPEC.md:265` wrote it and is **not** edited here. Three measured reasons it is
the wrong *first* rung:

1. 量 on the artefact: `-n 64K` **transfers 1,310,720 bytes, not 65,536** —
   `iperf_api.c:1853` sends `multisend = 10` blocks per bound check and the
   `break` leaves the stream loop, not the multisend loop. At the default
   `-l 128K` that is ten 128 KiB writes: **`D14`'s exact configuration**, one of
   the two that ended the last seating. (`-b` anything sets `multisend = 1` and
   makes `-n` exact: `-n 64K -l 1K -b 100M` moves exactly 65,536 bytes in 64
   writes of 1,024.)
2. 量 `IEENDCONDITIONS`: `-t` and `-n` are mutually exclusive, so an `-n` run has
   **no wall-clock cap** and a board that stops sending hangs the client forever.
3. § 0.4: every `iperf3` run so far died in the control exchange, so an `iperf3`
   rung measures the control exchange and not the load.

**Rung 1 is a burst-depth ladder driven from the host.** A fragmented ICMP echo
makes the board reassemble and then emit `ceil((S + 8) / 1480)` frames
back-to-back from **one** egress call — the same shape as a TCP write, with an
exact frame count, no control protocol, nothing board-side, and a generator on a
machine that cannot hang. 量: the host's `ping` is iputils 20240117 and honours
`-c`; **the board's busybox `ping` ignores it** (`NET-26`), which is exactly why
the generator must be the host.

| `-s` | frames the board emits back-to-back |
|---:|---:|
| 1400 | 1 |
| 4000 | 3 |
| 8000 | 6 |
| 20000 | 14 |
| 60000 | 41 |

### Predictions, written before the first packet

| | prediction | what refutes it |
|---|---|---|
| `H1-frag1` (`-c 1 -s 4000`) | reply returns, `tx_stopped 0` | no reply ⇒ **IP reassembly**, not TX; the ladder is then void rather than reinterpreted. This rung exists to find that out before it contaminates anything |
| 1 and 3 frames | survive, `n_tx_stop` unchanged | — |
| **6, 14, 41** frames | 推 `tx_stopped` → **1**, `n_tx_stop` increments | if 41 frames survives, **burst depth is not the variable** and § 0.6 is refuted |
| `n_irq` at every rung | rises **in proportion to frames**, never explodes | an explosion revives the interrupt-storm hypothesis |
| `time_squeeze` | unchanged | an explosion ⇒ softirq livelock, a different fault |

### The three-way separator, written before the reads

讀 `kernel/softirq.c:197-201` — 量 `CONFIG_RTL_819X=y`, so `MAX_SOFTIRQ_RESTART`
is **2000** where mainline is 10 — and `:646-650`, `ksoftirqd` runs at
`set_user_nice(current, -20)`. 讀 `net/core/dev.c:1977`: `netdev_budget` is
**128** where mainline is 300.

| | `n_irq` | `tx_stopped` | `time_squeeze` |
|---|---|---|---|
| interrupt storm | explodes | — | may rise |
| **TX-queue death (§ 0.6)** | **stops** | **1** | unchanged |
| softirq livelock | rises with packets | — | **explodes** |

🔴 **`/proc/net/softnet_stat` has never been read on this board.** It is the only
one of the three with no reading at all, and it costs one `cat`.

---

## 2. The cells, as literal command lines

`CAP` expands to
`/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL and writes its combined output to
`<prefix>.log`.

🔴 **The runner parses this block; it does not restate it.** A sweep that
reconstructs the command it runs will eventually run a broken one and report it as
a broken subject — `CLAUDE.md`, measured 2026-09-02.

```commands
#-- C1-BURN  the burn flag, independently of the rescue transcript (C-6).
#--          word 1 REQUIRED 00000000, or nothing is uploaded.  71 bytes.
CAP --out bench/2026-09-20b/C1-BURN --send 'DW 8040D4A0 1' --until 'RealTek>' --seconds 15
#-- C2-HEAD  the staged head, read back after the upload.  8 words; words 7-8
#--          carry __vmlinux_end, so this identifies WHICH image landed.
CAP --out bench/2026-09-20b/C2-HEAD --send 'DW 80500000 8' --until 'RealTek>' --seconds 15
#-- C3-BOOT  1,874 bytes.  Derived by tools/bootbytes.py predict:
#--          710 const + 1,164 marks (71 marks).  RLXFW-ID0=EDC94765.
CAP --out bench/2026-09-20b/C3-BOOT --send 'J 80500000' --seconds 45
#-- C4-LIVE  41 bytes = the shell is alive (X39-live, X43-live).  22 = wedged.
CAP --out bench/2026-09-20b/C4-LIVE --send 'echo RLXFW-LIVE-MARK' --seconds 12
#-- C5-SW    TRXRDY must be set or RX never reaches the CPU port (NET-52).
CAP --out bench/2026-09-20b/C5-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 20
#-- C6-UP    N-ALLOC=A15B8000 and N-ARM=A15B8000 must BOTH appear.  Their
#--          absence is NET-58 and the whole ladder would be void.
CAP --out bench/2026-09-20b/C6-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- C7-PING  4/4.  Four packets whatever -c says (NET-26), so -c is not typed.
CAP --out bench/2026-09-20b/C7-PING --send 'ping 10.1.1.2' --seconds 30
#-- C8-BASE  baseline: tx_stopped 0, n_tx_stop 0, n_tx_wake 0, n_writes 0.
CAP --out bench/2026-09-20b/C8-BASE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C9-SOFT  FIRST READING IN THIS PROJECT.  col 3 is time_squeeze.
CAP --out bench/2026-09-20b/C9-SOFT --send 'cat /proc/net/softnet_stat' --seconds 20
#-- C10-IRQ  line 12 RLX LOPI rtl819x-nic, line 25 ICTL rtl819x-timer.
CAP --out bench/2026-09-20b/C10-IRQ --send 'cat /proc/interrupts' --seconds 20
#-- H1-frag1 THE REASSEMBLY CONTROL.  1 received, or the ladder is VOID.
HOST bench/2026-09-20b/H1-frag1 :: ping -I enxfc19286184c9 -c 1 -s 4000 -W 3 -q 10.1.1.3
#-- C11-frag1 tx_stopped 0.
CAP --out bench/2026-09-20b/C11-frag1 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- H2-f1    20 replies, 1 frame each.  n_tx +20.
HOST bench/2026-09-20b/H2-f1 :: ping -I enxfc19286184c9 -c 20 -s 1400 -i 0.05 -w 10 -q 10.1.1.3
#-- C12-f1
CAP --out bench/2026-09-20b/C12-f1 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- H3-f3    20 replies, 3 frames each.  n_tx +60.
HOST bench/2026-09-20b/H3-f3 :: ping -I enxfc19286184c9 -c 20 -s 4000 -i 0.05 -w 10 -q 10.1.1.3
#-- C13-f3
CAP --out bench/2026-09-20b/C13-f3 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- H4-f6    THE FIRST RUNG ABOVE THE RING DEPTH.  6 frames per reply, ring is 4.
HOST bench/2026-09-20b/H4-f6 :: ping -I enxfc19286184c9 -c 20 -s 8000 -i 0.05 -w 10 -q 10.1.1.3
#-- C14-f6   PREDICTION: tx_stopped 1.
CAP --out bench/2026-09-20b/C14-f6 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C15-live6 41 while ping loss is 100 % kills "the board hangs" on its own.
CAP --out bench/2026-09-20b/C15-live6 --send 'echo RLXFW-LIVE-MARK' --seconds 12
#-- H5-f14   14 frames per reply.
HOST bench/2026-09-20b/H5-f14 :: ping -I enxfc19286184c9 -c 20 -s 20000 -i 0.1 -w 15 -q 10.1.1.3
#-- C16-f14
CAP --out bench/2026-09-20b/C16-f14 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- H6-f41   41 frames per reply from ONE egress call.
HOST bench/2026-09-20b/H6-f41 :: ping -I enxfc19286184c9 -c 10 -s 60000 -i 0.2 -w 15 -q 10.1.1.3
#-- C17-f41
CAP --out bench/2026-09-20b/C17-f41 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C18-live41
CAP --out bench/2026-09-20b/C18-live41 --send 'echo RLXFW-LIVE-MARK' --seconds 12
#-- C19-soft compare against C9-SOFT.  col 3 is the whole point.
CAP --out bench/2026-09-20b/C19-soft --send 'cat /proc/net/softnet_stat' --seconds 20
#-- C20-irq  compare against C10-IRQ.
CAP --out bench/2026-09-20b/C20-irq --send 'cat /proc/interrupts' --seconds 20
```

Two stages are **off-card** and named here rather than left to be inferred,
because they are `looprun`'s and not this card's:

```
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-20b/C0-rescue.json
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom --filename r6if1 --rescue-report bench/2026-09-20b/C0-rescue.json --expect-load 80500000 --yes
```

🔴 `--filename` must not contain `nfjrom` or `boot.img`: 讀 this unit's
`stage2.bin` at `0x80401208`, `nfjrom` sets the auto-execute flag at `0x8040D390`.
🔴 `--load-addr` is `int(s, 0)` and `--expect-load` is `int(s, 16)` — opposite hex
conventions in two commands on the same line.

⚠️ The six `H*` cells write a `.log` and **no `.meta.json`**, because they are not
console captures and nothing may claim to be one. `check-predictions` scores the
`.log`; `capdate` globs `*.meta.json` and therefore does not count them, which is
the behaviour the corpus already contains (`bench/2026-09-20/D27-U50`).

No `--idle` anywhere. No `$`, `"`, backtick or `sh -c` in any `--send`. No `FLR`,
`EW`, `EB`, `FLW` or burn verb. **No `ifconfig rlx0 down`** — `NET-58` says a
re-open leaves the engine loose.

---

## 3. The gate between every cell

Seating 29 put **fourteen frozen cells into a dead shell** because nothing checked
between them, and `check-predictions` scores existence and mtime rather than
content, so a 39-byte empty capture scored the same as a success. The runner for
this block stops on the first cell whose capture does not carry the echo of what
was sent plus the evidence the cell exists to produce.

量, the two outcomes of the liveness payload: `echo RLXFW-LIVE-MARK` returns
**41 bytes** alive (`X39-live`, `X43-live`, `X44-l8k-live`) and **22 bytes** not
(`X45-l32k-live`). The gate counts `RLXFW-LIVE-MARK` in the **raw bytes**: every
line ends `\r\n`, and `tools/capfield.py` refuses any name beginning `RLXFW-`, so
this is counted in Python and never by `grep`.

---

## 4. What this block cannot say

* It cannot attribute the *first* hang (`D15`…`D26`). That boot carried the
  `NET-56` cable fault and `NET-58`'s loose engine and nothing separates them.
* A fragmented ping adds the board's **IP reassembly** as a variable. `H1-frag1`
  bounds it, and if `H1` fails the ladder is void rather than reinterpreted.
* `ceil((S+8)/1480)` is 推 about the *board's* fragmentation of its own reply. It
  is checkable on the host with `tcpdump` and that is an off-card reading, not a
  claim of this card.
* It says nothing about throughput. `D5` needs a number with a spread and this
  block produces none.
* **Zero flash-write commands, zero `FLR`.**

## 5. Stop-loss

If `C14-f6` and `C17-f41` both read `tx_stopped 0` and `n_tx_stop 0`, burst depth
is refuted as the variable; the ladder stops there and the rest of the seating
goes to § 6 rather than to doubling `-s`.

## 6. If the ladder refutes § 0.6

`/proc/net/softnet_stat` col 3 is the next axis — 讀 `net/core/dev.c:2954`, it is
incremented exactly where `net_rx_action` breaks on its 2-jiffy limit, and `:3185`
prints it. `C9-SOFT`/`C19-soft` bracket the whole ladder, so that reading exists
whatever the ladder does.

## 7. If the board stops answering

🔴 **Do not press power immediately.** The order is:

1. `echo RLXFW-LIVE-MARK` — 41 or 22 decides everything after it.
2. If 22: send a bare **`0x03`** (Ctrl-C) as `--send`. 量
   `console-capture.py:253-297`: `_check_send` refuses leading/trailing
   whitespace, `\r`, `\n`, non-ASCII and length ≥ 128, and `\x03` is none of
   those; passing it through `subprocess` argv means no shell quoting layer
   touches it. **If the prompt comes back, the kernel was healthy and a
   foreground process was blocked** — § 0.6's strongest single confirmation.
3. Only then a power press, and **≤ 5 s**, because at that interval `MEM-17` puts
   retention at 1 bit in 22,976 and `PREDICTIONS-B31-postmortem.md`'s reads become
   valid. 量 today at ~14.5 h they are not: Hamming distance from the written
   content **47.66 / 52.15 / 53.91 %**, i.e. complete loss.

```cells
bench/2026-09-20b/C1-BURN
bench/2026-09-20b/C2-HEAD
bench/2026-09-20b/C3-BOOT
bench/2026-09-20b/C4-LIVE
bench/2026-09-20b/C5-SW
bench/2026-09-20b/C6-UP
bench/2026-09-20b/C7-PING
bench/2026-09-20b/C8-BASE
bench/2026-09-20b/C9-SOFT
bench/2026-09-20b/C10-IRQ
bench/2026-09-20b/H1-frag1
bench/2026-09-20b/C11-frag1
bench/2026-09-20b/H2-f1
bench/2026-09-20b/C12-f1
bench/2026-09-20b/H3-f3
bench/2026-09-20b/C13-f3
bench/2026-09-20b/H4-f6
bench/2026-09-20b/C14-f6
bench/2026-09-20b/C15-live6
bench/2026-09-20b/H5-f14
bench/2026-09-20b/C16-f14
bench/2026-09-20b/H6-f41
bench/2026-09-20b/C17-f41
bench/2026-09-20b/C18-live41
bench/2026-09-20b/C19-soft
bench/2026-09-20b/C20-irq
```

```cardnum
cells-fence	26	count bench/2026-09-20b/PREDICTIONS-B32-block30.md ^bench/2026-09-20b/[CH][0-9]+-[A-Za-z0-9_]+$
image-bytes	1152000	size /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom
image-sha16	89051d6a396c305b	sha256-16 /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom
declared-date	1	count bench/2026-09-20b/PREDICTIONS-B32-block30.md [*][*]declared date 2026-09-20[*][*]
send-over-127	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*' -{2}idle
no-shell-subst	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*[$`]
no-ifdown	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*ifconfig rlx0 down
no-iperf3	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*iperf3
no-ping-dash-c	0	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send '[^']*ping -c
live-cells	3	count bench/2026-09-20b/PREDICTIONS-B32-block30.md -{2}send 'echo RLXFW-LIVE-MARK'
host-cells	6	count bench/2026-09-20b/PREDICTIONS-B32-block30.md ^HOST bench/2026-09-20b/H[0-9]
```
