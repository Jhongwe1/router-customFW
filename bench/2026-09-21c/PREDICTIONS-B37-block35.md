# PREDICTIONS — block 35, seating 33 (`NET-73`'s ⚠️, and nothing else)

Frozen before the image is uploaded. **declared date 2026-09-21** — the
directory is `bench/2026-09-21c` because `bench/2026-09-21` is seating 31's and
`bench/2026-09-21b` is seating 32's, and this seating begins on the same
calendar day at `2026-09-21T12:13` (量, three clocks agreed at the segment's
open: Git Bash `2026-09-21T12:13:03+08:00`, WSL `2026-09-21T12:13:06+08:00`,
Windows epoch `1789963986`).

Every number below is re-derived from a named file, not copied from a previous
card. Marks: 量 measured on this device · 讀 read out of code or a dump · 推
inferred, pending a measurement.

---

## § 0 What this block is, and the one sentence it exists to decide

`SPEC.md` `NET-73` says **the fault requires a TCP connection**, and it excluded
five other dimensions by measurement — frame size, in-flight depth, total
volume, direction, bulk transport — with three negative controls that carried no
TCP and did not wedge.

It carries exactly one ⚠️, and five committed files say the same thing about it:

> `iperf3` always opens a TCP control socket, so **"a TCP connection" and
> "the `iperf3` program" have not been separated here**. A raw TCP connection
> with no `iperf3` — `socat` from the host — separates them. **Not run; it is
> the first cell of the next seating.**

This block is that cell, and it is deliberately **not** anything else. It does
not attempt `D5`, it does not build an image, and it does not chase why the
engine pauses.

🔴 **One correction to the plan that produced this block, made before power.**
The five files all say *"`socat` from the host to any listening port"*. 量
2026-09-21 at the desk, `tools/appletcensus.py query`: this image has **no
`nc`, no `telnet`, no `httpd`, no `inetd`, no `wget`, no `netstat`** — and
`config/rlxfw-initramfs.tsv` declares **no `/dev/ptmx` and no `/dev/pts`**. So
*any listening port* was a guess, and the only socket-capable binary in the
image is `iperf3` itself. The ladder below is built around that measurement
rather than around the sentence.

---

## § 1 The image, and what is held constant

| | `s31L` |
|---|---|
| variant | **loud**, `CONFIG_PRINTK=y` |
| assembled `nfjrom` | **1,180,672 B** |
| sha256 | `a038044da964b8331b426fe5bd36f3956a014e1faef7bb09e6bb5c426b3cd7dc` |
| `RECIPE_ID` | `f179cf21` |
| uploaded before | **3 times, good** (seating 32) |

🔴 **`RECIPE_ID` cannot tell `s31L` from `s31b` (`FW-99`), so the discriminator
is `looprun --image-sha256` and nothing else.** Both cardnum rows below name the
assembled `nfjrom` under `imgwork`, never the vendor-prebuilt `nfjrom` under
`cells/`, which is byte-identical between the two variants and would "prove"
either image was the other.

**Why the loud image and not the quiet one.** `NET-75`, 量 seating 32: a wedged
board on a `PRINTK=y` image prints `Virtual device rlx0 asks to queue packet!`
every 1.06 s, ratelimited; on the quiet image the interface dies silently. So
the console is a second, independent wedge detector that costs nothing, and
every rung below gets read two ways — `tx_stopped` in `/proc/rtl819x-nic`, and
the console.

**The power budget is one cycle and it is already spent.** 量, the board has
been at a cold loader prompt since `2026-09-21T12:20:47+0800`
(`bench/2026-09-21c/S0-catch`, whose own metadata records
`cr.esc.prompt_seen: true`, 7,356 ESC writes over 150.019673 s). The loader's
banner in that capture carries `Booting...`, `ramSize: 32M` and **no**
`Reboot Result from Watchdog Timeout!`, which is the loader's own evidence that
this was a cold power-on and not a reset.

---

## § 2 The four sub-hypotheses, and what separates them

`NET-73`'s wording — *a TCP connection* — is a disjunction that has never been
taken apart. Four readings of it survive seating 32's data, and they predict
different things here.

| id | reading | what would have to be true |
|---|---|---|
| **H-TX** | the board **transmitting any TCP segment at all** | a bare `RST` is enough |
| **H-EST** | an **established** connection existing | a handshake is enough; a refused connection is not |
| **H-ACK** | the board emitting a **sustained stream of small TCP segments** | `NET-67`'s own mechanism sentence — the frozen descriptors were bare ACKs at `len 82/74/82/74` |
| **H-IPERF** | something specific to the **`iperf3` program** | socket options, CPU load, or its bidirectional pattern — not TCP as such |

The ladder is ordered by how much TCP each rung carries, and the positive
control is last because it is the one rung expected to leave the board wedged.

---

## § 3 Standing instructions

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL with output to `<prefix>.log`.

* 🔴 **No flash write, no `FLR`, no `EW`/`EB`/`FLW`, no `AUTOBURN` write.** The
  bracket stays at 1,024 / 4,194,304 = 0.0244 %.
* 🔴 **No `echo write` to `/proc/rtl865x/memory`.** 讀 `rtl865x_proc_debug.c`:
  that write path has no range check and `MIB_CONTROL` (`0xBB801000`) is one hex
  digit from `MACCR` (`0xBB804000`). This block reads no vendor register at all,
  so the rule costs nothing here and is declared anyway.
* 🔴 **No `ifconfig rlx0 down`**, no `reset full`, no `restore 0`.
* Board-side `ping` ignores `-c` (`FW-46`), so **every ping in this block is
  host-side**, through `HOST`.
* An applet with no `/bin/` symlink must be typed `busybox <applet>` (`FW-96`).
  That is why `telnetd` is written `busybox telnetd`.
* Every `CAP` carries `--seconds`. A proc-read cell's window is **25 s** so that
  it also listens: on a wedged board `NET-75`'s line arrives every 1.06 s, so a
  wedge shows up as ~20 repetitions inside a cell whose job was to print a
  counter.

---

## § 4 The ladder, and the pre-registered prediction for every rung

**Every prediction below is written before the image is uploaded.** Where a rung
has no basis for a number, it says so rather than inventing one.

### 4.1 `T1` — one connection attempt, refused. No process on the board.

Host opens **one** TCP connection to port 9999 on the board. Nothing listens, so
the board's stack emits one `RST`. No `iperf3` anywhere; nothing is running on
the board but the shell.

* 推 **no wedge.** One small TX frame, against 2,450,389 the board transmitted
  in seating 32's flood without wedging.
* 🔴 **If it wedges**: `H-TX` is confirmed, `H-IPERF` is **refuted outright**,
  and `NET-73`'s headline is too weak — the factor is not *a connection* but
  *a TCP segment leaving the board*. That would be the strongest result this
  block can produce, and it costs one command.

### 4.2 `T2` — fifty refused attempts

* 推 **no wedge**, same ground.
* If `T1` did not wedge and `T2` does, the factor is **rate or count** of TCP
  TX frames, not their existence.

### 4.3 `T3` — thirty seconds of refused attempts at the highest rate the host can drive

This is the rung that matters most among the connectionless ones: it makes the
board emit a **sustained stream of small TCP segments** with **no connection and
no `iperf3`** — the same shape as `H-ACK` and none of its substance.

🔴 **Declared instrument change.** `socat` spawns one process per connection and
cannot reach a useful rate; `T3` therefore uses a host-side Python loop instead.
It is still *a pure TCP connection opened by the host with no `iperf3`*, which
is what the pre-registration asked for; the tool is named here so that the
departure from the word `socat` is on the record before it happens, not after.

* 推 **no wedge**, and this is the prediction this block is least sure of. Its
  basis is that all three of `NET-73`'s negative controls moved far more frames
  than this will.
* 🔴 **If it wedges**: `H-ACK` is confirmed in its protocol-shaped form and
  `H-EST`/`H-IPERF` are both refuted — a wedge with no connection in existence.

### 4.4 `T4` — an established connection, held open, carrying nothing

Board runs `busybox telnetd -p 9999`; host connects with `socat` and holds for
20 s, sending nothing.

* ⚠️ **This rung may not be runnable, and that is stated before it is tried.**
  讀 `config/rlxfw-initramfs.tsv`: there is no `/dev/ptmx` and no `/dev/pts`, so
  `telnetd` is expected to accept the TCP connection and then fail to allocate a
  pty. **The handshake completing is the whole requirement here** — `NET-73`
  already records that one wedge (`H5-D5r1`) happened with an *incomplete*
  control connection, so the handshake is inside the triggering window.
* 推 **no wedge** if the connection is idle after the handshake.
* 🔴 **If it wedges**: `H-EST` is confirmed and `H-IPERF` is refuted — an
  established connection with no `iperf3` in the process table.
* If `telnetd` does not start or the connection is not accepted, `T4` and `T5`
  are **NOT RUN** and that is recorded as a reading, not retried into existence.

### 4.5 `T5` — the same connection, carrying bulk host → board

The host pushes bytes into that socket for 20 s. The board's stack acknowledges
them. This is `NET-67`'s mechanism — *the board emitting bare ACKs
continuously* — reproduced with **no `iperf3`**.

* ⚠️ **Bounded, and the bound is stated first.** With nothing on the board
  reading the socket, the receive window closes after roughly one window's worth
  of data and the ACK stream stops. So `T5` is a **short** ACK burst, not a
  sustained one, and a no-wedge here is correspondingly weak evidence. It is run
  because it is free and because it is the closest available approach to
  `H-ACK`.
* 推 **wedge**, but with low confidence for the reason just given.
* 🔴 **If `T5` wedges**: `H-ACK` is confirmed and `H-IPERF` is refuted. That is
  the result that makes `s32a` the right next image, because a deeper ring plus
  the vendor's N−1 invariant turns *interface permanently dead* into *packets
  dropped, link alive*.

### 4.6 `T6` — the positive control, and it is the reason any of the above means anything

Board runs `iperf3 -c 10.1.1.2 -t 10` against a host-side `iperf3 -s`.

* 推 **wedge.** 量 seating 32: five `iperf3` invocations, five wedges.
* 🔴 **If `T6` does not wedge, every no-wedge reading in `T1`–`T5` is VOID** —
  the board was simply not in the state in which the fault occurs, and this
  block establishes nothing. This is written here, before power, because a
  ladder of negatives with no positive control is the shape this project keeps
  finding in its own work.

---

## § 5 `NET-73` is VOID, not "unchanged", if any of these

1. `A4-PING` is not 4/4. Nothing below a dead link is interpretable.
2. `T6` does not wedge (§ 4.6).
3. `A3-BASE` does not read all four `txd` OWN bits clear with `tx_stopped 0`.
   A board that begins the ladder already wedged cannot be wedged by a rung.
4. The board wedges at a rung and a later rung is then read **without a
   recovery in between**. `NET-68`: a new `arm` reclaims the stuck ring, so
   recovery costs a command and not a power press — but a rung run on an
   unrecovered board is contaminated and is recorded as such.

---

## § 6 The cells

```
#-- A0    looprun: rescue -> burnflag -> hostlink -> upload -> staged -> boot -> assert
#--       --skip S2,S3,S4 --recipe-override f179cf21
#--       --image  <imgwork>/s31L/s31L/kroot/rtkload/nfjrom
#--       --image-sha256 a038044da964b8331b426fe5bd36f3956a014e1faef7bb09e6bb5c426b3cd7dc
#-- A1-SW   the switch first. Without SIRR's TRXRDY the ping is 100 % loss and
#--         reads as a driver fault.
CAP --out bench/2026-09-21c/A1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
#-- A2-UP   bring rlx0 up. ndo_open does alloc, arm, request_irq, engine on.
CAP --out bench/2026-09-21c/A2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- A3-BASE at rest. § 5 clause 3 reads THIS cell. Four txd OWN clear,
#--         tx_stopped 0, n_tx_stop 0, or the whole ladder is void.
CAP --out bench/2026-09-21c/A3-BASE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- A4-PING baseline. § 5 clause 1 reads THIS cell.
HOST bench/2026-09-21c/A4-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- A5-SNMP the whole /proc/net/snmp, fetched WHOLE and compared at the desk.
#--         NET-76's residual names this reading and says busybox grep has no
#--         /bin/ symlink (FW-96) so it cannot be filtered on the board. It has
#--         never been fetched whole. This is the healthy-state baseline for it.
CAP --out bench/2026-09-21c/A5-SNMP --send 'cat /proc/net/snmp' --seconds 25
#-- T1     one refused connection. § 4.1
HOST bench/2026-09-21c/T1-SYN1 :: socat -T2 STDIO TCP:10.1.1.3:9999
CAP --out bench/2026-09-21c/T1-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21c/T1-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- T2     fifty refused connections. § 4.2
HOST bench/2026-09-21c/T2-SYN50 :: bash bench/2026-09-21c/t2-syn50.sh
CAP --out bench/2026-09-21c/T2-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21c/T2-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- T3     30 s of refused connections at rate. § 4.3, declared instrument change
HOST bench/2026-09-21c/T3-SYNRATE :: /usr/bin/python3 bench/2026-09-21c/t3-synrate.py
CAP --out bench/2026-09-21c/T3-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21c/T3-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- T4     an established connection, idle. § 4.4. May be NOT RUN.
CAP --out bench/2026-09-21c/T4-LISTEN --send 'busybox telnetd -p 9999 ; sleep 2 ; busybox ps' --seconds 25
HOST bench/2026-09-21c/T4-CONN :: socat -T20 STDIO TCP:10.1.1.3:9999
CAP --out bench/2026-09-21c/T4-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21c/T4-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- T5     the same connection, carrying bulk host -> board. § 4.5
HOST bench/2026-09-21c/T5-BULK :: bash bench/2026-09-21c/t5-bulk.sh
CAP --out bench/2026-09-21c/T5-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21c/T5-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- T6     THE POSITIVE CONTROL. § 4.6. Expected to leave the board wedged.
CAP --out bench/2026-09-21c/T6-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m' --seconds 45
CAP --out bench/2026-09-21c/T6-PROC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21c/T6-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- T7-SNMP the same whole file again, in whatever state T6 left the board.
#--         Paired with A5-SNMP this is NET-76's residual read from one route;
#--         the host-side tcpdump is the other half and is off-card.
CAP --out bench/2026-09-21c/T7-SNMP --send 'cat /proc/net/snmp' --seconds 25
```

---

## § 7 What this block does NOT establish

* **Why the engine pauses.** `NET-67`'s residual is untouched: the engine sits
  on a descriptor it owns, at its own position pointer, short of nothing, and
  does not consume it. Nothing here reads a vendor register.
* **`D5`.** No throughput number is sought and none may be quoted from `T6`,
  which is run to break the board and not to measure it.
* **`H-ACK` in its sustained form.** § 4.5 states the receive-window bound.
  Establishing `H-ACK` properly needs a board-side reader, which needs a binary
  this image does not have, which needs a build.
* **Whether the vendor's driver survives this.** Still 推. `ifconfig eth4 up`
  returns `Device or resource busy` because this driver holds a non-shared
  `request_irq(12)`, 量 seating 29.
* **`NET-76`'s residual.** `A5-SNMP`/`T7-SNMP` are read in the *wedge* state,
  not in the post-flood state the residual describes. They are a first whole
  reading of a file this project has never fetched whole, and they are not that
  residual's answer.

---

## § 8 The cells

```cells
bench/2026-09-21c/A0-ab2
bench/2026-09-21c/A0-2a
bench/2026-09-21c/A0-boot
bench/2026-09-21c/A1-SW
bench/2026-09-21c/A2-UP
bench/2026-09-21c/A3-BASE
bench/2026-09-21c/A4-PING
bench/2026-09-21c/A5-SNMP
bench/2026-09-21c/T1-SYN1
bench/2026-09-21c/T1-PROC
bench/2026-09-21c/T1-PING
bench/2026-09-21c/T2-SYN50
bench/2026-09-21c/T2-PROC
bench/2026-09-21c/T2-PING
bench/2026-09-21c/T3-SYNRATE
bench/2026-09-21c/T3-PROC
bench/2026-09-21c/T3-PING
bench/2026-09-21c/T4-LISTEN
bench/2026-09-21c/T4-CONN
bench/2026-09-21c/T4-PROC
bench/2026-09-21c/T4-PING
bench/2026-09-21c/T5-BULK
bench/2026-09-21c/T5-PROC
bench/2026-09-21c/T5-PING
bench/2026-09-21c/T6-IPERF
bench/2026-09-21c/T6-PROC
bench/2026-09-21c/T6-PING
bench/2026-09-21c/T7-SNMP
```

---

## § 9 Every number in this card, re-derived from a file

| number | where it came from |
|---|---|
| `s31L` `nfjrom` 1,180,672 B / `a038044d…` | `size` and `sha256-16` on `imgwork/s31L/s31L/kroot/rtkload/nfjrom`, both in § 10 |
| `RECIPE_ID f179cf21` | seating 32's frozen card, § 1; not re-derivable here without a rebuild, and this block does not rebuild |
| 2,450,389 TX frames | `SPEC.md` `NET-76`, `nd_stats tx 2450389/3533309070` |
| 1.06 s wedge line period | `SPEC.md` `NET-75` |
| `S0-catch` 7,356 ESC writes / 150.019673 s | `bench/2026-09-21c/S0-catch.meta.json`, `esc.esc.writes` and `esc.esc.window_s` |
| three clocks at the open | § 0 of this card; Git Bash and WSL `date -Is`, Windows `[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()` |

---

## § 10 The machine-checkable declaration

`cardcheck numbers` re-derives each of these from the artefact named on its
line. The `no-*` rows turn every prose safety claim in § 3 into a re-derived
`0`, so a cell that grew one by accident is caught before the port is opened.

```cardnum
cells-fence	28	count bench/2026-09-21c/PREDICTIONS-B37-block35.md ^bench/2026-09-21c/[AT][0-9]
declared-date	1	count bench/2026-09-21c/PREDICTIONS-B37-block35.md [*][*]declared date 2026-09-21[*][*]
cap-cells	13	count bench/2026-09-21c/PREDICTIONS-B37-block35.md ^CAP -{2}out
host-cells	12	count bench/2026-09-21c/PREDICTIONS-B37-block35.md ^HOST bench/2026-09-21c/
send-over-127	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*' -{2}idle
no-ifdown	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*ifconfig rlx0 down
no-reset-full	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*reset full
no-restore-zero	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*restore 0
no-ping-dash-c-board	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*ping -c
no-memory-write	0	count bench/2026-09-21c/PREDICTIONS-B37-block35.md -{2}send '[^']*echo write
loud-nfjrom-bytes	1180672	size /home/key/fwre-work/rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom
loud-nfjrom-sha256	a038044da964b833	sha256-16 /home/key/fwre-work/rebuild/imgwork/s31L/s31L/kroot/rtkload/nfjrom
catch-bytes	4837	size bench/2026-09-21c/S0-catch.log
```
