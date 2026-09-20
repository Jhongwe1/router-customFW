# PREDICTIONS — block 34, seating 32 (`R6-5`'s fourth seating)

Frozen before power. **declared date 2026-09-21** — the directory is
`bench/2026-09-21b` because `bench/2026-09-21` is seating 31's and this seating
begins on the same calendar day, at `2026-09-21T01:09` (量, three clocks agreed
at the segment's open: Git Bash `1789923270`, Windows `1789923272`, WSL
`1789923301`).

Every number below is re-derived from a named file, not copied from a previous
card. Marks: 量 measured on this device · 讀 read out of code or a dump · 推
inferred, pending a measurement.

---

## § 0 What this block is, and the sentence that frames it

Three seatings have failed to obtain `D5`, and each blamed a different cause:
the `iperf3` control exchange (`NET-60`, seating 29), the RX ring desync
(`NET-61`, seating 30), and the TX descriptor wedge (`NET-67`, seating 31).
The first two are closed or excluded. This block does **not** set out to get
`D5` by defeating `NET-67`. It sets out to get `D5` **in a configuration
`NET-67` is not in**, and then — with the number already banked — to spend the
fault deliberately, on a board that can be recovered without a power press.

🔴 **The framing sentence, and it is a correction to this repository, not a
plan:** `NET-67`'s own residual says the engine-side TX register *"was not
read"*. It was read **six times**, by seating 31's own captures, and the value
is committed. See § 2.1. Nothing in this block needs a new image to see it.

**The power budget is one cycle and it is already spent** — the board has been
at a cold loader prompt since `2026-09-21T01:09` (量, `live1.log`,
`8040D4A0: 00000001`, the documented power-on default of `AUTOBURN`, `REG-23`).
Two images ride that one cycle, joined by `busybox reboot -f` (`FW-37`, 2.407 s
to the loader prompt, 量).

---

## § 1 The two images, and what is held constant

| | `s31b` | `s31L` |
|---|---|---|
| variant | quiet | **loud** |
| `CONFIG_PRINTK` | `# … is not set` | **`=y`** |
| `vmlinux` | 4,465,171 B | 4,572,087 B |
| assembled `nfjrom` | **1,153,024 B** | **1,180,672 B** |
| sha256 | `8275a0799abce5a1f17818790f8ee1caf5b263ad6c18f3ec90892190015c88c1` | `a038044da964b8331b426fe5bd36f3956a014e1faef7bb09e6bb5c426b3cd7dc` |
| `RECIPE_ID` | `f179cf21` | `f179cf21` |
| uploaded before | 4 times, good | **never** |

Δ`vmlinux` = 4,572,087 − 4,465,171 = **106,916 B**.
Δ`nfjrom` = 1,180,672 − 1,153,024 = **27,648 B**.

🔴 **`RECIPE_ID` cannot tell these two apart (`FW-99`), so the discriminator is
`looprun --image-sha256` and nothing else.** A card that asserts which image ran
from `RLXFW-ID0` would pass a good unit carrying the wrong image.

🔴 **And there are TWO files called `nfjrom` under a cell.** 量 2026-09-21:
`cells/s31b/top/linux-2.6.30/rtkload/nfjrom` and
`cells/s31L/top/linux-2.6.30/rtkload/nfjrom` are **byte-identical** — 854,016 B,
sha256 `5cc8d61d4b4e8914ef085d3ea09bbde5c2c5edc59e3ae21ba8004e88c9b3c8be` — and
neither is the uploadable image. The uploadable ones are under
`rebuild/imgwork/<cell>/<cell>/kroot/rtkload/nfjrom`, which is the path `S3`
writes and `S6` sends. **Hashing the wrong one would have "proved" the two
images are the same.** This block hashes only the `imgwork/` path.

Held constant across the whole block: one Ethernet cable, one port with link
(`NET-12`, 100 Mbit FD), host `10.1.1.2/24` on `enxfc19286184c9`, board
`10.1.1.3` on `rlx0`, loader `10.1.1.1`.

---

## § 2 `NET-67` as actually measured, and five hypotheses with their refutations

### 2.1 🔴 The correction that makes this block possible

`SPEC.md:751`, `docs/KNOWN-ISSUES.md:895` and `notes/nic-driver.md:1246` all say
the next step is to read `tpdcr0_pos` across a wedge and that *"neither was
read"*. **The first half is false.** `rtl819x-nic.c:1693-1694` prints
`tpdcr0_pos` on every `cat /proc/rtl819x-nic`, so seating 31 took the reading
six times without meaning to. 量, `tx_ring = A15B8040`, entries 4 bytes,
slot = `(pos − base) / 4`:

| capture | `n_tx` | `n_rx` | `tx_idx` | `tpdcr0_pos` | engine slot | `txd0..3` OWN |
|---|---:|---:|---:|---|---:|---|
| `W1-BEFORE` | 7 | 10 | 3 | `A15B804C` | **3** | 0,0,0,0 |
| `W3-DURING` | 23 | 19 | 3 | `A15B8048` | **2** | 0,0,**1**,0 |
| `W4-AFTER` | 26 | 23 | 2 | `A15B8048` | **2** | 1,1,1,1 |
| `W5-LATE` | 26 | 27 | 2 | `A15B8048` | **2** | 1,1,1,1 |
| `W6-TXD` | 26 | 35 | 2 | `A15B8048` | **2** | 1,1,1,1 |
| `W7-TXD2` | 26 | 38 | 2 | `A15B8048` | **2** | 1,1,1,1 |

**Why nobody saw it**: `bench/2026-09-21/wedgeprobe.sh` writes the full `/proc`
into the `.log` and shows the operator a filtered view, and its filter (`:32`)
names `rpdcr0_pos`, `rmdcr0_pos`, `rx_idx`, `tx_idx` — **and not
`tpdcr0_pos`**. 量: `grep -c tpdcr0_pos bench/2026-09-21/wedgeprobe.sh` → **0**.
The residual was written from the summary. The instrument hid its own reading,
and the gap it manufactured looked like honest work remaining.

### 2.2 🔴 What that table refutes, and it is this block's own previous plan

At `W3-DURING` **exactly one** descriptor was engine-owned (slot 2), the
engine's pointer was on it, and the ring was **not full**. Between `W3` and
`W4` the driver filled three more (`n_tx` 23 → 26) and the engine's pointer did
not move. Had the engine consumed slot 2 after `W3` the pointer would have
advanced.

> **量: the engine stopped with ONE descriptor outstanding. The all-four-owned
> state arrived three transmits later and is a CONSEQUENCE, not the trigger.**

So `NIC_TX_DESC = 4`, and the missing "always keep one slot RISC-owned"
invariant the vendor enforces (讀 `rtl865xc_swNic.c:701-704`,
`if (next_index == txPktDoneDescIndex[…]) return -1;` — usable depth N−1, max
in flight 3 on a 4-entry ring), are a **second and independent defect**: they
are why an engine pause becomes a permanently dead interface here, where the
vendor's driver would have dropped packets and carried on (讀 `rtl_nic.c:5161-5171`,
a bounded spin then `kfree_skb` and return 0 — **the vendor never stops the
queue on ring-full**). They are not why the engine paused.

### 2.3 What the same captures already refute, for free

* 🔴 **`STOPTX` latched by the doorbell's read-modify-write — REFUTED.**
  `now_icr` reads **`C4000000`** in all five wedge captures. `C4000000` =
  bits 31 (`TXCMD`), 30 (`RXCMD`), 26 (`NIC_MBUF_2048`, `4u << 24`).
  `STOPTX` is bit 21 (讀 `rtl865xc_asicregs.h:540`) and
  `C4000000 & 00200000 = 0`. The engine is commanded to run.
* ⚠️ **The doorbell itself is NOT testable this way.** `TXFD` is a measured
  self-clearing bit (量, `notes/nic-driver.md:906-910`), so `now_icr` says
  nothing about whether a doorbell rang. Only `txstall off` can ask that; § 6.
* 🔴 **A transmitted frame looped back to the CPU port — REFUTED at the desk.**
  `nic_xmit` uses `portlist 0x3F` = bits 0–5. The CPU port is **6** in the
  `PORTID` namespace (讀 `rtl865x_asicL2.h` `enum PORTID{…CPU=6}`,
  `rtl865x_fdb.h:21` `RTL8651_CPU_PORTNUMBER=6`) and **7** in the
  TX-descriptor mask namespace (讀 `rtl865xc_swNic.h:155`). `0x3F` excludes
  both. ⚠️ **This leaves seating 31's own `n_rx` anomaly unexplained** —
  *"`n_rx` rose by more than the fragment count (+14 for a 9-fragment
  datagram)"* — and this block does not chase it.
* 🔴 **No error was reported by the engine.** `seen_iisr` reads `0000320E` in
  every wedge capture; `0x320E` = bits 1, 2 (`TX_ALL_DONE_IP0/1`), 3
  (`RX_DONE_IP0`), 9 (`TX_DONE_IP0`), 12, 13. **No `PKTHDR_RUNOUT` (bits
  17–22), no `MBUF_RUNOUT` (bit 16), no `TX_ERR` (bit 23).** ⚠️ Bits 12 and 13
  are set in the healthy state too and are **unnamed** in this driver's bit
  table — an open item this block records and does not chase.

### 2.4 The five live hypotheses, each with what refutes it

| id | hypothesis | instrument | 否證 |
|---|---|---|---|
| **H-POOL** | The ASIC's shared descriptor pool is exhausted, so the engine cannot accept the CPU-port frame and never retires its descriptor | `GDSR0` `0xBB806100`: `USEDDSC` bits 25:16, `MaxUsedDsc` bits 13:0, `DSCRUNOUT` bit 27, `SharedBufFCON_Flag` bit 14 — against `SBFCR0` `0xBB804500`'s `S_DSC_RUNOUT` threshold, bits 9:0 | `USEDDSC` well below the threshold **and** `DSCRUNOUT` = 0 **and** `SharedBufFCON_Flag` = 0 during the wedge |
| **H-FC** | The switch is applying flow control to the CPU port's egress path | `PCSR0` `0xBB806108` (P3 output-queue congestion, bits 30:24), `PCSR1` `0xBB80610C` (P6 = CPU port, bits 22:16), `asicCounter` port-3 Output `pause` | all congestion fields 0 during the wedge, and `pause` not advancing across it |
| **H-BELL** | The doorbell was lost; the engine is idle waiting to be told | `txstall off` — which writes `TXCMD` then `TXFD` and touches nothing else | `txstall off` does not restore transmit |
| **H-CMD** | The engine's command state is wrong in some way a full `CPUICR` rewrite fixes | `engine off ; engine on` (`CPUICR` written by plain `=`, `:1591`), no ring or base touched | it does not restore transmit either |
| **H-RING** | The descriptor contents or the ring bases are what is wrong | `engine off ; arm ; engine on` — the known-working recovery, which rewrites all four ring words AND `CPUTPDCR0` | it fails too, which would leave every hypothesis here refuted |

🔴 **`H-BELL`, `H-CMD` and `H-RING` are ordered as a bisection and the order is
the whole point.** The recovery used on seating 31 changed five things at once
(讀 `rtl819x-nic.c`: `CPUIIMR=0`; `CPUICR &= ~(TXCMD|RXCMD)`; all four
`tx_ring[i]` rewritten OWN-clear `:1356-1360`; `nic_rx_idx = nic_tx_idx = 0`
`:1362-1363`; `CPUTPDCR0 = nic_tx_ring`; `CPUICR = 0xC4000000` by plain `=`).
Each rung below changes strictly fewer.

⚠️ **`arm` is not separable from `CPUTPDCR0 = base` on this image** — no verb
writes one without the other. That separation needs a build and is not
attempted here.

---

## § 3 Standing instructions

1. 🔴 **A liveness probe between every cell.** `docs/KNOWN-ISSUES.md`: block 29
   lost **fourteen** carded cells by typing them into a shell that was already
   dead, and `check-predictions` scores existence and mtime, never content, so
   the seating would have reported green. Every script in this block re-reads
   its precondition **at the point of use**, not at the point of start
   (`FW-100`).
2. 🔴 **`/proc/rtl865x/memory` is READ-ONLY in this block. No `write`, ever.**
   讀 `rtl865x_proc_debug.c:4115-4178`: there is no range, alignment or
   allow-list check, and `MIB_CONTROL` (`0xBB801000`) sits **one hex digit**
   from `MACCR` (`0xBB804000`). A stray write there is not a brick; it is a
   silent, unrecoverable loss of the baseline of the instrument this block
   depends on. ⚠️ The handler also has a one-byte stack overflow at exactly
   `len == 64`; every payload written here is **≤ 20 bytes**.
3. 🔴 **Every `--send` line is ≤ 127 characters** (`_check_send` refuses 128,
   `N29`), and 🔴 **no line uses shell substitution or quoting.** The first
   draft of this card read the seven registers with one
   `for a in … ; do echo read 0x$a 4 >… ; done` at 120 characters, and
   `cardcheck --self-test`'s control **`B9`** — *no committed card needs shell
   quoting or substitution* — **fired on it**, correctly: a command carrying
   `$a` cannot be checked against the image's declared applet set, which is the
   whole reason `cardcheck commands` exists. The loop is gone. Each register
   read is literal, **two per line at 91 characters**
   (`44 + 3 + 44`), and the register sweep therefore costs four cells instead
   of one.
4. ⚠️ **`--seconds` is measured from `t0`, not from the end of `--esc`**
   (讀 `console-capture.py:657`, `:783`). No cell here uses `--esc`.
5. ⚠️ **`FW-49`**: ash wraps the *echo* of any line ≥ 80 characters with
   `\r\r\n`. Output is never wrapped. The § 7 sweep's echo will be wrapped and
   that is not a fault.
6. ⚠️ **`FW-64`**: one `cat` is **two** `read_proc` invocations, so every
   `cat /proc/rtl819x-nic` adds **12** to `n_reads` (six `nic_rd()` per
   invocation). Any identity over `n_reads` carries that factor.
7. 🔴 **This image's `ping` ignores `-c`** (`FW-46` family) — every `ping` in
   this block is **host-side**.
8. 🔴 **If the console goes silent at any point, DO NOT POWER CYCLE.** Take a
   30 s read-only capture with `sent: null` first; `NET-64` was refuted by
   exactly that (the board was mute, not hung).

---

## § 4 Cells — § A and § B, image `s31b`

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL with output to `<prefix>.log`.

🔴 **`--skip S2,S3,S4`**: the tree is built and the image assembled, and the
board is at a **cold** loader prompt, where `S4`'s abort condition
(`Reboot Result from Watchdog Timeout!`) is correctly absent. `S5b` is **not**
skipped and cannot be — it reads `0x8040D4A0` back after the rescue and aborts
on anything but `00000000`.

```
#-- A0    looprun: rescue -> burnflag -> hostlink -> upload -> staged -> boot -> assert
#--       --skip S2,S3,S4 --recipe-override f179cf21
#--       --image  <imgwork>/s31b/s31b/kroot/rtkload/nfjrom
#--       --image-sha256 8275a0799abce5a1f17818790f8ee1caf5b263ad6c18f3ec90892190015c88c1
#-- B1-SW   the switch first. Without SIRR's TRXRDY the ping is 100 % loss and
#--         reads as a driver fault.
CAP --out bench/2026-09-21b/B1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
#-- B2-UP   bring rlx0 up. ndo_open does alloc, arm, request_irq, engine on.
CAP --out bench/2026-09-21b/B2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- B3-BASE at rest. RECORDS tx_ring. Every slot arithmetic below is VOID if
#--         this does not read A15B8040.
CAP --out bench/2026-09-21b/B3-BASE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B4-PING baseline. If this is not 4/4 nothing below is interpretable.
HOST bench/2026-09-21b/B4-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- B5-REGa..d the engine-side registers AT REST. This is the control for
#--         § 6's wedge read; without it a number there means nothing.
#--         a = GDSR0 + GDSR1    b = PCSR0 + PCSR1
#--         c = P6_DCR0 + SBFCR0 d = CPUTPDCR0 + CPUICR
CAP --out bench/2026-09-21b/B5-REGa --send 'echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806104 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/B5-REGb --send 'echo read 0xBB806108 4 >/proc/rtl865x/memory ; echo read 0xBB80610C 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/B5-REGc --send 'echo read 0xBB806170 4 >/proc/rtl865x/memory ; echo read 0xBB804500 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/B5-REGd --send 'echo read 0xB8010020 4 >/proc/rtl865x/memory ; echo read 0xB8010000 4 >/proc/rtl865x/memory' --seconds 25
#-- B6-REGa2 GDSR0 a SECOND time, immediately. MaxUsedDsc is a history field
#--         and may be clear-on-read; two reads a few seconds apart is the
#--         only way to find out before the number is used as evidence.
CAP --out bench/2026-09-21b/B6-REGa2 --send 'echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806104 4 >/proc/rtl865x/memory' --seconds 25
#-- B7-ASICC clear the ASIC counters. 讀 rtl865x_proc_debug.c:4416-4540. The
#--         64-bit byte counters on this part are low + (high << 22), so the
#--         low word wraps at 4,194,304 bytes -- ~34 s at 1 Mbit/s and about
#--         1.7 s at 20 Mbit/s. Differencing without clearing reads a wrap as
#--         a stall. Absolute counts from zero remove the hazard.
CAP --out bench/2026-09-21b/B7-ASICC --send 'echo clear > /proc/rtl865x/asicCounter ; echo dump port 6 > /proc/rtl865x/asicCounter' --seconds 30
```

### Predictions for § B

| cell | prediction | what refutes it |
|---|---|---|
| `A0` | eleven boot marks, `RLXFW-ID0=F179CF21`, a prompt | any of the three missing |
| `B3-BASE` | `tx_ring A15B8040`, `tx_idx 0`, `now_icr C4000000`, `tpdcr0_pos A15B8040`, `n_tx_stop 0`, `tx_stopped 0` | `tx_ring` ≠ `A15B8040` **voids § 2.1's slot arithmetic and § 6's predictions** |
| `B4-PING` | 4/4 | anything less stops the block |
| `B5-REGa..d` | eight `cmd read` lines and eight values. **`GDSR0`'s `USEDDSC` (bits 25:16) LOW at rest; `DSCRUNOUT` 0; `SharedBufFCON_Flag` 0** | no output at all → the vendor `/proc` does not print under `PRINTK=n`. 量 `bench/2026-09-17b/X28-LX28.log` on image `p11e` (`# CONFIG_PRINTK is not set`) shows `cmd read` + `bb804128:  000000E0`, so that outcome is already refuted by precedent |
| `B5-REGd` | `b8010020` equals `B3-BASE`'s `tpdcr0_pos`, **two sources agreeing** — all 88 existing readings of that register come from `nic_rd()` alone, and this is the first through the vendor's handler, sharing no code | a disagreement is a finding about the instrument, not about the board |
| `B6-REGa2` | identical to `B5-REGa` | any field differing with the board at rest means that field is clear-on-read or free-running, and every later use of it as evidence has to say which |
| `B7-ASICC` | a CPU-port block ~13 lines, all counters at or near 0 | `dump port 6` not recognised → fall back to a bare `cat` |

---

## § 5 `D5` — the `iperf3` number, in the configuration `NET-67` is not in

### 5.1 What `D5` actually asks for

Verbatim, `PROGRESS.md:128`:

> an `iperf3` number exists, with the method that produced it and its spread
> over at least three runs.

🔴 It names the **instrument** and nothing else. 量: the strings "TCP", "UDP",
"bits/s", "bytes/s" and every direction word are **absent** from `D5`, from the
`R6-5` step cell (`PROGRESS.md:110`), from the gate board (`:1804`) and from
the plan's 通過 row (`plan/router-rebuild-plan.md:1414`). A `ping`-derived
figure fails `D5`'s **tool** clause; an `iperf3 -u` figure does not.

⚠️ **This block does not read that as a licence.** The number is reported with
the transport, the direction and the fault beside it, because a receive-side
UDP figure quoted as "the throughput of this driver" would be an overclaim a
hostile reader would take apart in one question.

### 5.2 Why this direction

量 (agent-independent, re-derived here from the captures):

| workload | board TX | `n_xmit_busy` | `txd0..3` | outcome |
|---|---:|---:|---|---|
| host flood ping, `bench/2026-09-19b/L2-after` | **7,466** frames, len 1446 | **0** | `D0 E8 0200 021A` — OWN all **clear** | no wedge |
| TCP `-R -b 1M`, `bench/2026-09-21/W6-TXD` | **26** frames, len 82/74 | 1 | `D1 E9 8201 821B` — OWN all **set** | wedge |

🔴 **In every wedge this project has recorded, the board was the TCP
RECEIVER** — 讀 `iperf_api.c:370-379` (`role=='c'` ⇒ `sender=1`, then
`if (reverse) sender = !sender`), and 量 every one of `V1`, `F1M`, `W2-START`
and `bwladder.sh:48` carries `-R` and prints
`Reverse mode, remote host 10.1.1.2 is sending`. Its TX was ACKs. **7,466
large frames went through and 26 ACK-sized ones did not**, so neither TX volume
nor frame size is the trigger on the evidence available.

`iperf3 -u -R` makes the board a **UDP receiver**, which transmits nothing at
all during the test: 讀 `iperf_udp.c:55-125`, `iperf_udp_recv()` is `Nread` plus
counters plus `return r` — no `sendto`, no ACK. (⚠️ Not literally zero: the
connect handshake is one datagram, and the TCP control socket carries state
bytes and the end-of-test results.)

🔴 **`-l 1400`, never the 3.1.3 UDP default of `-l 8192`.** 讀
`iperf_api.h:42` `DEFAULT_UDP_BLKSIZE 8192`: at an MTU of 1500 that is
`ceil((8192 + 8) / 1480)` = **6** IP fragments per datagram, which sits on the
measured fragment-ladder failure boundary (量 seating 31: 7 ✓, 8 ✓, **9 ✗**,
10 ✓, 14 ✗ — non-monotone). All four UDP attempts in the record used the
default.

🔴 **`-i 1`, never `-i 0`.** 讀 `iperf_api.c:698-699`, `:1839`. With `-i 1` the
board prints a receiver interval line per second **as it happens**, which
`console-capture` records regardless of whether the run ever reaches its
end-of-test exchange over the control socket. Every seating-31 run used `-i 0`
and a run that wedges therefore loses its own number.

### 5.3 The ladder, and the pre-registered prediction

Four rungs × three runs, 10 s each. Rungs **2M / 10M / 30M / 60M**, chosen so
that the ping-derived bracket is spanned on both sides: re-derived here from
`bench/2026-09-21/C1b`, `C2b`, `C4b` pairwise (`2·ΔS / Δrtt`), **24.7 –
33.1 Mbit/s**, three slopes disagreeing by about 30 %.

> **Pre-registered, written before the run:**
> 1. At `-b 2M` and `-b 10M`: loss **< 1 %**, received rate within 2 % of
>    offered.
> 2. The knee — the highest rung whose loss is **< 5 %** — is at **10M or
>    30M**. 推.
> 3. At `-b 60M`: loss **> 40 %**, received rate **15–40 Mbit/s**. 推.
> 4. **No rung wedges the board.** `n_tx_stop` and `tx_stopped` read **0** in
>    the `/proc` read after every rung.
>
> **否證 of (4), which is the one that matters:** if a UDP receive rung wedges
> the board, then board-side TX is not necessary for `NET-67` and every
> attribution in § 2 — including this block's own — is about the wrong half of
> the path. That outcome is more valuable than the number and the block does
> not treat it as a failure.

### 5.4 `D5` is VOID, not "low", if any of these

* the host listener is not on `10.1.1.2:5201` at the moment the board dials
  (re-read `ss` per run — `FW-100`);
* the two ends are not both 3.1.3 (the host's own `/usr/bin/iperf3` is **3.16**
  and must not be used; the MIPS binary is
  `/home/key/fwre-work/iperf3-port/iperf3`, 252,644 B, run under
  `qemu-mips-static`);
* fewer than three completed runs exist at the quoted rung;
* the `/proc` read bracketing a rung shows `n_tx_stop` non-zero — the number
  then measures the defect, not the path;
* a rung's board-side output is absent and only the host's summary survives.

### 5.5 Cells

```
#-- C0-SRV  host: start the 3.1.3 MIPS server under qemu, and LEAVE IT RUNNING.
#--         Verified at the point of use by every rung, never once at the start.
#-- C1..C4  the ladder. bench/2026-09-21b/s93udp.sh drives it: per rung, a
#--         liveness ping, an `ss` re-read, three 10 s runs, a /proc read
#--         after each, and a post-rung liveness ping.
HOST bench/2026-09-21b/C-LADDER :: bash bench/2026-09-21b/s93udp.sh
#-- C5-PROC the state after the whole ladder
CAP --out bench/2026-09-21b/C5-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C6-ASIC what the ASIC counted, absolute from B7-ASICC's clear
CAP --out bench/2026-09-21b/C6-ASIC --send 'echo dump port 6 > /proc/rtl865x/asicCounter' --seconds 40
#-- C7-PING the ladder did not break the path
HOST bench/2026-09-21b/C7-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

---

## § 6 The recovery bisection — the mechanism, on a board that can be recovered

Run **after** `D5`'s number is banked, because it deliberately breaks the board.

```
#-- D0-WEDGE reproduce it. The trigger of record: TCP, board as receiver, -b 1M.
#--          BACKGROUNDED with `&` -- seating 31's one methodological win. The
#--          shell stays free and /proc can be read DURING the fault.
CAP --out bench/2026-09-21b/D0-WEDGE --send 'iperf3 -c 10.1.1.2 -p 5201 -t 30 -i 1 -f m -R -b 1M > /dev/null 2>&1 &' --seconds 20
#-- D1-DUR   the driver's side, during
CAP --out bench/2026-09-21b/D1-DUR --send 'cat /proc/rtl819x-nic' --seconds 25
#-- D2-REGa..d 🔴 THE CELLS THIS BLOCK EXISTS FOR. The engine's side, DURING.
#--          Same four lines as B5, so the comparison is line-for-line.
CAP --out bench/2026-09-21b/D2-REGa --send 'echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806104 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/D2-REGb --send 'echo read 0xBB806108 4 >/proc/rtl865x/memory ; echo read 0xBB80610C 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/D2-REGc --send 'echo read 0xBB806170 4 >/proc/rtl865x/memory ; echo read 0xBB804500 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/D2-REGd --send 'echo read 0xB8010020 4 >/proc/rtl865x/memory ; echo read 0xB8010000 4 >/proc/rtl865x/memory' --seconds 25
#-- D3-DUR2  one second later. Two identical dumps while n_rx moves is the
#--          proof that the ENGINE is not retiring, not that a consumer index
#--          stopped moving -- this driver has no consumer index, it reads the
#--          descriptor words themselves.
CAP --out bench/2026-09-21b/D3-DUR2 --send 'sleep 1 ; cat /proc/rtl819x-nic' --seconds 25
#-- D4-ASICW what the ASIC counted across the wedge
CAP --out bench/2026-09-21b/D4-ASICW --send 'echo dump port 6 > /proc/rtl865x/asicCounter' --seconds 40
#-- D5-BELL  rung 1: TXCMD + doorbell ALONE. Touches no descriptor, no ring
#--          base, no index. The source carries its own refutation condition
#--          at rtl819x-nic.c:1899-1907.
CAP --out bench/2026-09-21b/D5-BELL --send 'echo txstall off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- D6-P1    did rung 1 restore transmit?
HOST bench/2026-09-21b/D6-P1 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- D7-CMD   rung 2: a full CPUICR rewrite. Still no descriptor, no base.
CAP --out bench/2026-09-21b/D7-CMD --send 'echo engine off > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- D8-P2
HOST bench/2026-09-21b/D8-P2 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- D9-RING  rung 3: the known recovery. Rewrites all four ring words AND
#--          CPUTPDCR0 AND both indices.
CAP --out bench/2026-09-21b/D9-RING --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
#-- D10-P3
HOST bench/2026-09-21b/D10-P3 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- D11-REGa/b the engine's side AFTER recovery -- the third leg, and the one
#--          that says whether whatever D2 showed went away.
CAP --out bench/2026-09-21b/D11-REGa --send 'echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806104 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/D11-REGb --send 'echo read 0xBB806108 4 >/proc/rtl865x/memory ; echo read 0xBB80610C 4 >/proc/rtl865x/memory' --seconds 25
```

### Pre-registered predictions for § 6

| cell | prediction | 否證 |
|---|---|---|
| `D1-DUR` | `n_tx_stop ≥ 1`, `tx_stopped 1`, `n_tx_wake 0`, all four `txd` OWN set, `tpdcr0_pos` frozen on one slot, `now_icr C4000000` | `now_icr` ≠ `C4000000` would be the first non-`C4000000` reading in the record and re-opens `STOPTX` |
| `D3-DUR2` | byte-identical to `D1-DUR` **except** `n_rx`, `n_napi_poll`, `n_irq`, `n_reads`, `j_now` | any `txd` or `tpdcr0_pos` moving refutes "the engine is not retiring" |
| `D2-REGa..d` vs `B5-REGa..d` | **H-POOL** predicts `GDSR0`'s `USEDDSC` high, at or near `SBFCR0`'s `S_DSC_RUNOUT`, and/or `DSCRUNOUT`/`SharedBufFCON_Flag` set. **H-FC** predicts `PCSR0`'s P3 or `PCSR1`'s P6 congestion field non-zero. `D2-REGd`'s `b8010020` equals `D1-DUR`'s frozen `tpdcr0_pos` | all eight fields equal to the at-rest values refutes **both** and leaves the engine stopping for a reason none of the five hypotheses names — which this block would then report as its result |
| `D5-BELL` → `D6-P1` | 推 **does not recover**. If it does, **H-BELL** is confirmed and the fix is a shadow-write doorbell | recovery here makes `arm` unnecessary and rewrites `NET-68` |
| `D7-CMD` → `D8-P2` | 推 does not recover | — |
| `D9-RING` → `D10-P3` | recovers, ping ≥ 2/4 (量 seating 31: `arm` alone left ping 0/4 and one `ifconfig` cycle reached 2/4; this block does **not** predict 4/4) | no recovery at all refutes every hypothesis in § 2.4 and the block reports that |

⚠️ **`arm` is not a repair and says so in its own comment** (`:1382-1389`): 量
`Z11-f6` read 11/181 after exactly that recovery where a fresh boot reads
20/20.

---

## § 7 The direction never tried — board as bulk UDP **sender**

```
#-- E1-TXUDP no -R. The board generates. This is the direction D5 most wants
#--          and the one no seating has ever run.
CAP --out bench/2026-09-21b/E1-TXUDP --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m -u -l 1400 -b 20M' --until 'iperf Done|error|refused|unable' --seconds 45
#-- E2-PROC
CAP --out bench/2026-09-21b/E2-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- E3-REGa/b
CAP --out bench/2026-09-21b/E3-REGa --send 'echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806104 4 >/proc/rtl865x/memory' --seconds 25
CAP --out bench/2026-09-21b/E3-REGb --send 'echo read 0xBB806108 4 >/proc/rtl865x/memory ; echo read 0xBB80610C 4 >/proc/rtl865x/memory' --seconds 25
#-- E4-PING
HOST bench/2026-09-21b/E4-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

🔴 **A confound named before the run, not after.** 讀 `NET-57`:
`tx_queue_len = 0` makes `rlx0` a `noqueue` device, so `noqueue_qdisc.enqueue`
is NULL and every `NETDEV_TX_BUSY` becomes a `kfree_skb` — a **silent** local
drop. 量 `NET-63`: `n_xmit_busy 19`, `n_tx_stop 19`, `ΔFragFails +19`,
`ΔOutDiscards +19`. **So `iperf3`'s loss column here conflates local TX drop
with network loss**, and the only way to separate them is `n_xmit_busy` and
`n_tx_stop` from `E2-PROC`. The number is reported with them beside it or not
at all.

> **Pre-registered:** 推 this wedges the board, because it is sustained
> board-side TX. If it does **not** wedge — 7,466 flood-ping frames did not
> either — then TX alone is not sufficient and the trigger involves the
> **concurrent** RX load, which is what every wedge in the record had and the
> flood ping did not.

---

## § 8 `D6` — image `s31L`, and why it needs a different image

Verbatim, `PROGRESS.md:130`: **"30 minutes of continuous flood: zero drops by
the driver's own counters, zero oops, kernel log captured whole"**, sharpened at
`:110` to *"continuous traffic — not a 2.4 s loop"* and *"captured whole rather
than grepped"*. **Three** conjuncts. The protocol is **unspecified**.

讀 `config/rlxfw-kernel.delta:138`, `set@loud CONFIG_PRINTK n y`: under
`PRINTK=n` an oops prints nothing and there is no kernel log, so **two of the
three conjuncts are unobservable on every image this project has ever run**.
`s31L` is the first loud one.

⚠️ **And the first conjunct is known to be blind here.** 量 seating 30: the
driver's `n_rx` counted every one of 5,281 frames while 218 datagrams died
above it (`NET-62`). *Zero drops by the driver's own counters* can be true and
meaningless. It is reported as measured, with that sentence attached.

**The flood chosen is a host-side `ping -f`**, because it is the only
continuous workload this board is measured to survive at length (量 7,466
frames, `n_xmit_busy 0`), and because it exercises RX **and** TX where
`iperf3 -u -R` exercises only RX.

```
#-- F0-RB   back to the loader with NO power press. FW-37: `busybox reboot`
#--         signals PID 1 and this image's PID 1 is a shell script; `-f` is a
#--         watchdog bite, 2.407 s to the prompt.
CAP --out bench/2026-09-21b/F0-RB --send 'busybox reboot -f' --esc-after 12 --esc-period 0.002 --seconds 30
#-- F1     looprun with the LOUD image. --image-sha256 is the only discriminator.
#--        --skip S2,S3,S4 --recipe-override f179cf21
#--        --image-sha256 a038044da964b8331b426fe5bd36f3956a014e1faef7bb09e6bb5c426b3cd7dc
#-- F2-SW
CAP --out bench/2026-09-21b/F2-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
#-- F3-UP
CAP --out bench/2026-09-21b/F3-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- F4-PRE
CAP --out bench/2026-09-21b/F4-PRE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- F5-FLOOD 🔴 THE CONSOLE IS CAPTURED FOR THE WHOLE 30 MINUTES AND NOT
#--          GREPPED. 1,860 s of --seconds with no --until and no --idle.
CAP --out bench/2026-09-21b/F5-FLOOD --seconds 1860
HOST bench/2026-09-21b/F5-HOSTFLOOD :: sudo ping -f -w 1800 -s 1400 -I 10.1.1.2 10.1.1.3
#-- F6-POST
CAP --out bench/2026-09-21b/F6-POST --send 'cat /proc/rtl819x-nic' --seconds 25
#-- F7-REGa  GDSR0 after 30 minutes. MaxUsedDsc (bits 13:0) is a HIGH-WATER
#--          HISTORY field, so this one read says how close the pool came to
#--          its threshold over the whole flood -- which no per-moment read can.
CAP --out bench/2026-09-21b/F7-REGa --send 'echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806104 4 >/proc/rtl865x/memory' --seconds 25
#-- F8-PING
HOST bench/2026-09-21b/F8-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

🔴 **`F5-FLOOD` carries no `--send`.** It is a pure read-only capture running
concurrently with the host-side flood, so the board's console is recorded whole
for the full 30 minutes with nothing typed into it. That is what *"captured
whole rather than grepped"* requires, and it also means the capture is a valid
reading whether the board stays up or dies at minute 3.

⚠️ **`F5-FLOOD` and `F5-HOSTFLOOD` must start in that order** and the capture's
`--seconds 1860` is 60 s longer than the flood's `-w 1800`, so the capture
outlives the flood and records whatever the board says afterwards.

> **Pre-registered:** 推 `s31L` boots; its boot capture is **longer** than
> `s31b`'s because `PRINTK=y` restores `printk` output. **No byte-count
> prediction is made for it**, because no loud image has ever booted on this
> die and a number invented here would be a guess wearing a prediction's
> clothes. What **is** predicted: `RLXFW-ID0=F179CF21` (the same id as `s31b` —
> `FW-99`), the eleven boot marks, and a prompt.

---

## § 9 What this block does NOT establish

* **Why the engine stops**, if `D2-REGW` comes back equal to `B5-REG0`. The
  block would then have refuted five hypotheses and named none.
* **`H-BELL` vs `H-CMD` cleanly**, if `D5-BELL` recovers — `txstall off`
  writes `TXCMD` *and* the doorbell, so a recovery there does not say which.
* **`arm`'s ring rewrite vs its `CPUTPDCR0` rewrite.** Not separable on this
  image; needs a build.
* **`R6-6`.** Not attempted. Two of its three DoD clauses were established
  unreachable before power on the previous card
  (`bench/2026-09-21/PREDICTIONS-B35-block33.md:356-377`): two ports need two
  simultaneous endpoints (thirteen reads, exactly one `LinkUp` each time), and
  rlxfw cannot write the VLAN **table** at all (讀 `rtl819x-switch.c:88-92`,
  the indirect TACI path) — what a restore restores is the PVID register.
* **The `n_rx` anomaly** of § 2.3 — `n_rx` rising by more than the fragment
  count — which the loopback refutation leaves unexplained.
* **`seen_iisr` bits 12 and 13**, set in health and in fault, unnamed in this
  driver's bit table.
* **Zero flash writes.** No `FLW`/`EW`/`EB`/burn is issued, `AUTOBURN` is read
  back by `S5b` before each of the two uploads, and both uploads land at
  `0x80500000`, which is RAM. 🔴 **That is not the same sentence as "not one
  flash byte is written"** — no `FLR` bracket runs in this block, so the
  bracket stands where it stood, at **1,024 of 4,194,304 = 0.0244 %**, and
  `FLS-26`'s ledger does not move.

---

## § 10 The cells

```cells
bench/2026-09-21b/A0-ab2
bench/2026-09-21b/A0-2a
bench/2026-09-21b/A0-boot
bench/2026-09-21b/B1-SW
bench/2026-09-21b/B2-UP
bench/2026-09-21b/B3-BASE
bench/2026-09-21b/B4-PING
bench/2026-09-21b/B5-REGa
bench/2026-09-21b/B5-REGb
bench/2026-09-21b/B5-REGc
bench/2026-09-21b/B5-REGd
bench/2026-09-21b/B6-REGa2
bench/2026-09-21b/B7-ASICC
bench/2026-09-21b/C-LADDER
bench/2026-09-21b/C5-PROC
bench/2026-09-21b/C6-ASIC
bench/2026-09-21b/C7-PING
bench/2026-09-21b/D0-WEDGE
bench/2026-09-21b/D1-DUR
bench/2026-09-21b/D2-REGa
bench/2026-09-21b/D2-REGb
bench/2026-09-21b/D2-REGc
bench/2026-09-21b/D2-REGd
bench/2026-09-21b/D3-DUR2
bench/2026-09-21b/D4-ASICW
bench/2026-09-21b/D5-BELL
bench/2026-09-21b/D6-P1
bench/2026-09-21b/D7-CMD
bench/2026-09-21b/D8-P2
bench/2026-09-21b/D9-RING
bench/2026-09-21b/D10-P3
bench/2026-09-21b/D11-REGa
bench/2026-09-21b/D11-REGb
bench/2026-09-21b/E1-TXUDP
bench/2026-09-21b/E2-PROC
bench/2026-09-21b/E3-REGa
bench/2026-09-21b/E3-REGb
bench/2026-09-21b/E4-PING
bench/2026-09-21b/F0-RB
bench/2026-09-21b/F1-ab2
bench/2026-09-21b/F1-2a
bench/2026-09-21b/F1-boot
bench/2026-09-21b/F2-SW
bench/2026-09-21b/F3-UP
bench/2026-09-21b/F4-PRE
bench/2026-09-21b/F5-FLOOD
bench/2026-09-21b/F5-HOSTFLOOD
bench/2026-09-21b/F6-POST
bench/2026-09-21b/F7-REGa
bench/2026-09-21b/F8-PING
```

---

## § 11 Every number in this card, re-derived from a file

| number | how it was derived here | file |
|---|---|---|
| `s31b` nfjrom 1,153,024 B / `8275a079…` | `stat -c %s` and `sha256sum` on the `imgwork/` path, 2026-09-21 | `rebuild/imgwork/s31b/s31b/kroot/rtkload/nfjrom` |
| `s31L` nfjrom 1,180,672 B / `a038044d…` | same | `rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom` |
| Δ`nfjrom` 27,648 B | 1,180,672 − 1,153,024 | — |
| Δ`vmlinux` 106,916 B | 4,572,087 − 4,465,171, both `stat`ed | `cells/s31{b,L}/top/linux-2.6.30/vmlinux` |
| `GDSR0` `0xBB806100` | `SWCORE_BASE 0xBB800000` (`:147`) + `SWCORECNR 0x6000` (`:674`) + `DESCDIAG_BASE 0x0100` (`:699`) + `0x000` (`:700`) | `rtl865xc_asicregs.h` |
| `PCSR0` `0xBB806108`, `PCSR1` `0xBB80610C` | `DESCDIAG_BASE` + `0x008` / `0x00c` (`:702-703`) | same |
| `P6_DCR0` `0xBB806170` | `DESCDIAG_BASE` + `0x070` (`:728`) | same |
| `SBFCR0` `0xBB804500` | `SBFCTR = 0x4500 + SWCORE_BASE` (`:1673`) + `0x000` (`:1674`) | same |
| `CPUTPDCR0` `0xB8010020` | `0x18010000` + `0x020` (`rtl819x-nic.c:219`, `:224`), KSEG1 | `rtl819x-nic.c` |
| `USEDDSC` bits 25:16 | `(0x3ff<<16)` (`:765`) | `rtl865xc_asicregs.h` |
| `MaxUsedDsc` bits 13:0 | `(0x3fff<<0)` (`:768`) | same |
| `DSCRUNOUT` bit 27, `SharedBufFCON_Flag` bit 14 | `(1<<27)` (`:762`), `(1<<14)` (`:766`) | same |
| `S_DSC_RUNOUT` bits 9:0 | `(0x3FF<<0)` (`:1735`) | same |
| `STOPTX` bit 21 | `(1<<21)` (`:540`); `C4000000 & 00200000 = 0` | same |
| `C4000000` = bits 31, 30, 26 | `0xC4000000` = `1100 0100 …`; `NIC_MBUF_2048` is `4u<<24` = bit 26 | `rtl819x-nic.c:241-244` |
| `0000320E` = bits 1,2,3,9,12,13 | `0x320E` = `0x0E` (1,2,3) + `0x200` (9) + `0x3000` (12,13) | — |
| slot = `(pos − A15B8040)/4` | `0x4C→3`, `0x48→2`, `0x44→1`, `0x40→0` | `W1`…`W7` |
| 6 fragments at `-l 8192` | `ceil((8192 + 8) / 1480)` = `ceil(5.54)` = 6 | `iperf_api.h:42` |
| 24.7–33.1 Mbit/s | pairwise `2·ΔS/Δrtt` over `-s` 10000/11000/14000 at 4.747/5.231/7.178 ms | `bench/2026-09-21/C1b`, `C2b`, `C4b` |
| byte-counter wrap 4,194,304 B | `low + (high << 22)`; `2^22` = 4,194,304 | `rtl865x_asicCom.c:1504-1508` |
| 34 s at 1 Mbit/s | 4,194,304 B ÷ 125,000 B/s = 33.55 s | — |
| 1.7 s at 20 Mbit/s | 4,194,304 B ÷ 2,500,000 B/s = 1.678 s | — |
| register-read line = 91 chars | `echo read 0xBB806100 4 >/proc/rtl865x/memory` = `12 + 8 + 4 + 20` = 44; two joined by ` ; ` = `44 + 3 + 44` = **91**; three would be **134** and `_check_send` refuses 128 | counted in this card |
| bracket unchanged 0.0244 % | 1,024 ÷ 4,194,304 = 0.0244 % | `SPEC.md` `FLS-20` |

---

## § 12 The machine-checkable declaration

`cardcheck numbers` re-derives each of these from the artefact named on its
line. Scraping numbers out of prose was the other design and it is worse than
nothing: it checks what it happens to recognise and stays quiet about the rest.

```cardnum
cells-fence	50	count bench/2026-09-21b/PREDICTIONS-B36-block34.md ^bench/2026-09-21b/[A-F][0-9]*[a-z0-9]*-?[A-Za-z0-9]*$
declared-date	1	count bench/2026-09-21b/PREDICTIONS-B36-block34.md [*][*]declared date 2026-09-21[*][*]
cap-cells	35	count bench/2026-09-21b/PREDICTIONS-B36-block34.md ^CAP -{2}out
host-cells	9	count bench/2026-09-21b/PREDICTIONS-B36-block34.md ^HOST bench/2026-09-21b/
regread-cells	14	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send 'echo read 0x
arm-cells	1	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send 'echo engine off > /proc/rtl819x-nic ; echo arm
send-over-127	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*[$`]
no-flr	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*' -{2}idle
no-ifdown	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*ifconfig rlx0 down
no-reset-full	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*reset full
no-restore-zero	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*restore 0
no-ping-dash-c-board	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*ping -c
no-memory-write	0	count bench/2026-09-21b/PREDICTIONS-B36-block34.md -{2}send '[^']*echo write
nfjrom-bytes	1153024	size /home/key/fwre-work/rebuild/imgwork/s31b/s31b/kroot/rtkload/nfjrom
nfjrom-sha256	8275a0799abce5a1	sha256-16 /home/key/fwre-work/rebuild/imgwork/s31b/s31b/kroot/rtkload/nfjrom
loud-nfjrom-bytes	1180672	size /home/key/fwre-work/rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom
loud-nfjrom-sha256	a038044da964b833	sha256-16 /home/key/fwre-work/rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom
```

🔴 **`no-memory-write` is the one that guards the device**, not the seating:
`/proc/rtl865x/memory`'s write path has no range check and `MIB_CONTROL`
(`0xBB801000`) is one hex digit from `MACCR` (`0xBB804000`). A card that grew
an `echo write` by accident would be caught here before the port is opened.
