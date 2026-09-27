# PREDICTIONS — block 50, seating 43's second press (card B: `D3`'s second boot, `NET-131`'s deciding bracket, `D3-MISS` ② at the fix, `D6`'s arm P, `R6b-4`'s `D4`)

**declared date 2026-09-27** — **one power press, the second of seating 43**; its catch window
opens no later than 23:14 that day (every trial at its timeout, every block that can be cut
cut); at the estimate, by 22:26 for `R6b-4` to run and by 22:26 for nothing to be cut (`CUT-4`
binds; § 6). § 6's cut points decide, from the wall clock, what runs after `I-D3`.
Card A — seating 43's first press, on `p2q` (`D3-MISS` ① and ②'s vendor and 1.4 series) — comes
before this card in the same seating and is frozen as
`bench/2026-09-27/PREDICTIONS-B51-block49.md` (`cc5e39d`); this card depends on it only through
the shared classifier `s1class.py` and card A's series reader `rttseries.py` (both pinned by
digest in `R0-SUM`), and card A's series plan (`011001100110`) and text capture (`TDT`), which
two cardnum rows (`m2-plan-card-a`, `m2-tdt-card-a`) read from that frozen card. Block 48
(`bench/2026-09-26b/PREDICTIONS-B50-block48.md`, recorded in `e922066`, `notes/nic-driver.md`
§ 27) is the last press read; this card was drafted after its record and follows it.

Marks: **量** measured on the device · **讀** read out of code or a dump · **推** inferred,
pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① What this press is, and the owner's decisions of 2026-09-26 it carries.** One press of
`r6b6q` (recipe `acf8ed3d`). Seating 43 is two presses, card A then this card. The owner
accepted: `R6b-4`'s 31-minute `ping -f` flood (`NET-76`'s own stimulus) at the fix and a
two-minute load at 1.4 bounded by `timeout`; `D3`'s second boot on this image, the card stating
now what a pass and a failure mean (P5); `R6b-6`'s B1 dropped (the datasheet has no PHY MII
register map, so `BMCR` bit 9 has one source, and the ruling drops B1 without it); arm P (the
owner pulls and re-plugs the cable, each by ⑩'s five steps, inside a window of 100 s) kept as
`get_link`'s positive control; `D3-MISS` ②'s vendor series (`eth4`, the vendor's driver; a
vendor-firmware series is ⊘, the owner's decision of 2026-09-26) on card A, not here. On
2026-09-27 the owner stated the handshake (⑩) and accepted a press of up to 85 minutes for this
card (`CUT-4`'s source, § 6 S6). Priority, decided before any sizing: `D3`'s twelve and their
1.4 control are never cut; then arm P, `D3-MISS` ②, `NET-131`, the `R6b-4` block, `D4`'s 1.4
arm and the TCP tail, cut in that order reversed (§ 6, S6). **`R6b-4`'s slack**: at the
estimate `CUT-4` is reached 5.7 min inside its 44-min rule (derived from the press's length the
owner accepted on 2026-09-27, § 6 S6), so an S1 (its read set and, in branch b, the re-attach:
推 several minutes, each of its lines after the 90-s hold of § 6) or the owner's replies in arm
P taking longer than the estimate's 30 s each can use it, and then `CUT-4` refuses and `R6b-4`
does not run on this press.

| conjunct | carried here | not here |
|---|---|---|
| `D3`, `NET-111`'s twelve at the fix, two boots | boot 2 (`I-D3`), on this image (P5 names the image variable) | — |
| `D3`'s positive control, 1.4 on the same boot | `LUR1` and `LUS1`, each on its own re-armed ring (block 48 ran `LUS1` on `LUR1`'s stalled ring) | — |
| `NET-117` 殘留 ② (the ~64 datagrams) | the receive buffer's size (`B-RMEM`) and two reads of the server's queue inside each UDP receive trial's data phase (P8) | ① (the host's own frames) and ③ (`-b` halved, a larger buffer): each changes the trial's shape |
| `NET-131` 殘留, the deciding bracket | six two-request brackets at 1.4 (61, 62, 63, twice each) on re-armed rings, under a capture read by record order (P9) | — |
| `D3-MISS` ②, the capture's effect on `rlx0`'s rtt | card A's twelve series, ABBA, at the fix (P10) | the vendor's (`eth4`) and 1.4's series: card A (card A skipped or voided: § 7) |
| `D6`, the `ethtool` ops on the board with a positive control; `MT-PORT` naming the driver | `linkprobe get` with its in-call controls (P3); arm P's pull and re-plug with `linkprobe watch` across both (P11); `mfgtest` 1.1 with the cable out and back (P11) | `MT-PORT`'s source outliving `R6b-8` (a fixture until `R6b-8` boots) |
| `NET-30` 殘留 (where a latched link-down comes from) | `DW BB804134 1` at the caught prompt, the boot's `SW7`, the opening page's `lde0` (P2) | the reads after `IPCONFIG` and after the upload: `looprun` does not stop there |
| `NET-30` 殘留 ② (a link event made at this desk) | arm N, H1 (`ip link set`), H2 (`ethtool -r`) (P4, P12) | B1 (dropped); H3 (the re-attach, `R6b-3`'s card by the coordinator's ruling) |
| `D4` (`NET-67` 殘留), `R6b-4` | the flood at the fix beside every stack length, 31 min (P13); the same load at 1.4, 2 min (P16) | — |
| `NET-68` 殘留 (does a recovery persist under continued traffic) | a reading from P16's cells: 1.4's fires and recoveries under the 120-s load, and the load answered around them (P16) | the manual `arm` against `ifconfig down/up` (`NET-72` closed that half); persistence at the fix, where no recovery is predicted (§ 7) |
| `NET-76` 殘留, `NET-78` 殘留 | after the flood, before any re-arm (P14); `cn` at both settings (P13, P16) | — |

**② The image variable, named before power.** `r6b6q` is not the image blocks 47 and 48 booted
(`r6b2q`). 量 at the desk (`$FWRE_WORK/rebuild/s113/plan43/`): the two build cells'
`rtl819x-nic.o` are byte-identical (`cmp`), their `.config` and kernel `cflags` the same; four
objects differ — `rtl819x-switch.o` (switch driver 1.1 → 1.2: every `PSRP` read counts the bit
8 it consumes, three more `PSRP` reads at `subsys_initcall`, a `/proc` page up to 438 B
longer), `init/main.o` and `rtl819x-spi.o` (by the recipe id only: `objdiff43b.out`, a cardnum
row) and `vmlinux.o`; the initramfs adds `/bin/linkprobe` and replaces `mfgtest` 1.0 with 1.1.
So a `D3` pass here is boot 2 of *driver 1.5 at `txlen vendor`*, the NIC object the same and
the image not; a `D3` failure is *`D3` not met on this boot*, recorded with the image variable
beside it (P5).

**③ Block 48's lessons, each applied here.**
* *`D3-LUS1-L` failed after 1.4's `LUR1` stalled the ring* (`notes/nic-driver.md` § 27.9):
  every 1.4 arm and trial here begins and ends with a re-arm before the next liveness gate (S2,
  which the generator checks on every § 6 path), `LUS1` runs on its own re-armed ring (`D3-Y`),
  and `D3-Z-SW` re-arms at the fix after it.
* *The read set ran after the board's own recovery and before the host's only*: a failed
  liveness is now classified from the board before the host is touched (`s1class.py`, S1), and
  the re-attach runs only in branch b or when branch a fails twice.
* *The re-attach restarted the host adapter's `rx_packets`* (§ 27.5 (b)): declared now — at the
  pair spanning a re-attach, P0 (b) is void, never refuted.
* *`D3`'s trials ran uncaptured and the socket was the place* (§ 27.8): kept uncaptured;
  `NET-117` 殘留's `~64` now gets its deciding read (P8).
* *Record lessons*: every invocation's exit code is written to a file by the wrapper that runs
  it (`inv43b.sh` appends `INVOCATION <name> rc=<n>` to
  `/home/key/fwre-work/rebuild/s113/run43b/rc.tsv`), and so is every declared X-cell's
  (`inv43b.sh --x`, `XCELL <name> rc=<n>`, § 6) and every hold's (`inv43b.sh --hold`,
  `HOLD <cell> rc=<n>`), and an off-card cell's time is its capture's `meta.json`, never a
  transcript line typed by hand.

**④ The host is restarted before this press**, as block 48's was: between card A's power-off
and this card's `I-0`, `wsl --shutdown`, a fresh keeper, the kernel-log follower into a new
file (`/home/key/fwre-work/rebuild/s113/host43b/dmesg-w43b.log`), and both USB devices attached
with the board off. `R0-DW0` refuses power unless that log reads `bug_preempt 0`,
`usbnet_xmit 0` and `call_trace 0`. The GbE adapter attached there, before this press's power,
and untouched after, is also `NET-30` 殘留's condition (P2); `R0-CW` reads its carrier 0 with the
board off — the positive control of the carrier watcher arm P's windows use.

**⑤ Containment, which does not depend on any outcome.**
* **Frames at 1.4's settings are bounded by construction.** The `D3` control is two `iperf3`
  trials (`NET-111`'s stimulus, run at 1.4 on seatings 39, 40 and 42). `NET-131`'s six runs are
  two requests each on a re-armed ring (12 frames at a faulty length). `D4`'s 1.4 arm is
  `d4load.sh --seconds 120`, whose flood runs under `timeout -s INT 125` (shown ending a flood
  whose `-w` was ten times too long at the desk, `d4rehearse/`), its length loop stopping with
  it. No sweep, no `tx` verb, no held ring (cardnum rows count zero).
* **The flood at the fix** is `NET-76`'s own stimulus (`ping -f -l 32 -s 1400`), 1,860 s under
  `timeout -s INT 1,865`, beside a loop that asks the board's stack for every frame length
  60–1,514 in turn; the board is read only before and after it, and no board capture runs
  during it. A console watch streams ESC into the board's console throughout it (⑥): about 100
  bytes a second into the board's UART, and back whatever `ash` at its prompt makes of them —
  unmeasured (推 little or nothing; while a command runs, the tty echoes each as `^[`, 量
  `P1-RZ`, `C5-UB`) — a load `NET-76`'s flood (seating 32) and block 48's trials did not carry,
  the same on `D4`'s two halves and on every trial here, 推 immaterial to the NIC's TX path and
  not separated (§ 7).
* **What the host keeps of a frame.** `NET-131`'s capture `N1.pcap` and `NET-76`'s `N76.pcap`
  (`tcpdump -Q in -s 64`, the board's source address), under
  `/home/key/fwre-work/rebuild/s113/pcap43b`, never the repository, read only by `pcapwin` 1.3
  (counts, lengths, sequence numbers, never an address). `D3-MISS` ②'s six on-series captures
  are card A's `TDT` — `P2`'s text capture (`tcpdump -n -tt`, block 44's filter: ICMP and the
  ARP frames of the bench's two addresses) — into each `-T` cell's own log, as seating 40's
  `P1-TCPD` and `P3-TCPD` were: the capture's form is ②'s variable, so it is card A's byte for
  byte (a cardnum row compares the two macros); what it prints is the bench's private addresses
  and the frames' times, nothing of the board's flash.
* **Verdicts come from counters**: the CPU port's and port 3's (`asicCounter`), the driver's,
  the switch page's, the host adapter's, both sides' `/proc/net/snmp`, read in brackets;
  `ping`'s, `iperf3`'s, `linkprobe`'s and `mfgtest`'s own lines beside them.

**⑥ Resets, and the one this image can do by itself.** No cell types anything that resets the
board, but `r6b6q` carries `rtl819x-wdt 1.1`, built in (`CONFIG_WATCHDOG=y`; `obj-y` in the
build cell's `drivers/watchdog/Makefile`; its `late_initcall` in the image's `System.map`),
which arms `BOOTGUARD` at `late_initcall` at OVSEL 9 and kicks it from a kernel timer every 250
ms (讀 the build cell's `rtl819x-wdt.c`; cardnum rows): a kernel whose timer wheel stops for
83.8 s (量, the driver's own record and `SPEC.md` `FW-45`; 84.001 s as `CLK-08b` measured it,
the figure the hold uses) is reset, and the loader then boots the vendor firmware unless ESC
reaches it inside its window of about 4.9 s (`console-capture`'s own record) — and every path
into vendor userspace opens with a flash write (`VDR-1`). A capture that only *ends* on the
banner stops nothing. So, whatever any reading says: **(i)** every board cell's capture ends on
the loader's banner — a read's and a map's `--until` holds `Booting\.\.\.|---RealTek` as an
alternative, and every `--idle` cell after the round carries it beside its idle (cardnum rows
count them; the loader's own `R1-DW`, before the round, is the one without), and so does every
board X-cell § 6 writes out whole (the wrapper then exits 5, so its line stops there: the
`xcells-*` rows) — and every board cell after the round carries the gate
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))` (162 gates), so a reset
stops the run in the cell it happens in; **(ii)** from the board's last byte to the next ESC
stream, every stretch of the full run stays under 76.55 s — the bite less one kick, 2 s for a
runner's stop and the next watch's start and a 5-s margin (both guesses) — a host cell counted
at its own deadline when it waits on the board (`ping`'s, `arping`'s) and at twice its estimate
otherwise, a board cell at its `--idle` or, with none, its cap, an invocation's start at 1 s:
164 stretches, the longest 76.2 s, ending at `M2F-S11-R` (`arith43b.out`'s `STRETCH` lines,
cardnum rows; the generator refuses a card over the bound). So a timer wheel that stops is
found silent by the next board cell, whose invocation stops and hands the console to a watch
before the bite; for that the maps' cap is 60 s and `mfgtest`'s 70 s (`arith43b.out`'s `CAP`
lines: each at least 2.5 times the longest committed run that ended on its own `--until`);
**(iii)** every host-only stretch longer than the bound — each of the fourteen trials, the
flood, the tail, the 1.4 load, the two cable windows and the host's wait for the board's watch
— is an invocation of its own (20 of them, `I-W…`) run while a watch holds the console, the
watch started and stopped by the wrapper around it in the same command line (§ 6, *The watch*);
**(iv)** each of the press's command lines ends with a watch, so a watch holds the console at
every later moment the board runs a kernel with no board capture open — every wait for the
owner, every decision a stop calls for, every host-only step of a recovery — until the
power-off window, which streams ESC too and is followed on its line by a watch; and after any
stop, with the board running a kernel, the watch holds the console, before any board cell is
typed and before any continuation starts, until at least 90 s after the latest board capture's
end (§ 6, *The hold after a stop*: the bite as measured, 84.001 s, `SPEC.md` `CLK-08b`, the
loader's banner to its prompt with ESC streaming, 2.3 s, block 48's `R1-CATCH`, and a 3-s
margin, a guess), so a kernel that had stopped by then has been bitten and its loader caught
inside the watch; at the loader's prompt no watch is opened, since the loader boots nothing by
itself (§ 6). **What this does not cover**: (1) a reset from another cause (the supply, a hang
the watchdog does not see) inside a board cell ends that cell on the banner with no ESC
streaming; the watch that follows on its command line opens after the runner's stop (推 2 s),
inside the loader's ~4.9-s window or not — never timed — and if not, the vendor firmware boots:
§ 6's loader rule has the owner power it off, 推 after its first write, which this card does not
claim to prevent; (2) at a watch's stop where no stop of the run came first (so no hold), a
watch does not judge what comes back, so its stop is not evidence that the board lived: a
kernel that died in the 83.8 s before a watch's stop bites after the stop, and the bite is
caught only if the next ESC stream runs by then — the next board cell found silent, the
runner's stop, the tail watch: up to 23.5 s after a stop (before `P-LW2`, the longest of the
full run's 24 stops, each in `arith43b.out`'s `GAP` lines and § 6); a death in that window,
83.8 s before a stop, is not covered. The hold after a stop narrows this and does not close it
(`arith43b.out`'s `HOLDEDGE` and `XHOLD` lines; E is the latest board capture's end, the point
the hold counts from): a kernel that had stopped kicking by E is bitten, and its loader at the
prompt with the ESC streaming, by E + 90 s inside the watch, with 3.7 s to spare for the
reset-to-banner time (unmeasured) and the host's read. Taking that time as 0 (it moves each
edge below earlier by itself): one that stops kicking between E + 3.7 and E + 6.0 s bites
between E + 87.7 and E + 90 s, its banner in the watch's log with the ESC streaming but its
prompt perhaps after the watch's stop — `--stop` looks only for `<RealTek>`, so it returns 0
and the line's first board X-cell is typed at the loader (its capture then holds the loader's
text, the wrapper exits 5 and the line stops there; no X-cell's send carries a loader write
verb, `cardcheck commands`), and whether the ESC reached the loader's check before the stop is
not known (推), so the vendor firmware may boot, as in (1); one that stops kicking in about the
g s after E + 6.0 s bites after the watch's ESC has ended and before the line's tail watch
streams it, g being the watch's stop, the line's first board cell's cap, the runner's stop and
the tail watch's start (0.5 + cap + 2 s, guesses but the cap): 12.5 to 32.5 s where a declared
board X-cell opens the line (its cap 10 to 30 s, the longest `X-<t>-S0R`'s), up to 73.5 s where
an invocation opens it (an invocation's start and its `--from` cell's cap, at most 70 s,
`P-MT2`'s) — the bite ends that cell on the banner with no ESC streaming, or comes between it
and the tail watch, and the tail watch opens inside the loader's ~4.9-s window or not, as in
(1); a kernel that stops later dies during the line itself: a bite inside a later board cell
ends it on the banner, as in (1), and one after the line lands in its tail watch; (3) a timer
wheel that stops while the console still answers (推: a stopped tick hangs `sleep`, which every
bracket types first); (4) the console, unwatched while WSL itself is down (§ 6). **The maps
carry no `--esc-after`**: while a command runs the tty echoes each ESC as `^[` (量
`bench/2026-09-25/P1-RZ.log`), which would enter the text `R1-MB0` and `R1-MB1` hash; a reset
during a map ends it on the banner with no ESC streaming, (1) above. The image has
`CONFIG_RTL_WTDOG=n` (a cardnum row); no cell touches `/dev/watchdog`, types `reboot` or a
`biteraw` (cardnum rows count zero).

**⑦ The clock.** The cut gates read the host's wall clock against the catch's own start stamp
(§ 6, S6) — the one place this card uses one. No verdict rests on a timestamp:
`linkprobe watch`'s `LPW t` (the board's `CLOCK_MONOTONIC`) and the carrier watcher's `CW t`
(the host's `CLOCK_MONOTONIC_RAW`) are two clocks on two machines and are never subtracted;
each is read against its own side's static reads.

**⑧ Runner limits** (card 1's). Background cells know three programs; this card's are `tcpdump`
only, and the kernel-log follower is an off-card process started before `I-0`. The console
watch is therefore not a cell: `inv43b.sh` starts and stops it around each watched invocation
and ends every command line with one (⑥, § 6). `N1.pcap` spans invocations, so it runs in one
of its own (`I-N0`, stopped in `I-N9`), which the session starts with the Bash tool's
`run_in_background` (never `nohup … &` inside `wsl -- bash -lc`); ②'s and `NET-76`'s captures
start and stop inside one invocation, each stopped by `pkill -INT` before the invocation ends
(the runner waits for its background cells at its end). `NAME?` marks a cell whose non-zero
exit is a reading. Macros take one parameter.

**⑨ `C-19`** is named: the kernel-log windows count `USB disconnect`, `cp210x` and `ttyUSB`
lines, and the record states every console drop and every idle longer than a minute, with the
idle before it (block 48: 212 captures, 0 drops, six gaps over a minute, none followed by a
drop; the row stays open). The flood's 31 minutes, the trigger's shape until now, are no longer
an idle console: a watch keeps the port open and writing through them (⑥), so a drop there is
`C-19` under writing, and the record states each watch's span, its stop reason and whether a
drop followed it.

**⑩ The owner's physical actions, and the owner's standing order.** For every power press,
power-off and physical action — the press, arm P's pull and re-plug, S4's re-seat, the pull's
retry — the session goes: **(1)** it tells the owner what comes next and **stops**; **(2)** the
owner's reply only authorizes opening the window — nothing physical happens yet; **(3)** the
session starts the catch or window command line in the background and confirms from its
transcript that the ESC-streaming (or recording) cell is running; **(4)** only then does it
tell the owner "open — press now" (or pull, re-plug, power off now); **(5)** the owner acts.
Each window covers the owner's reaction after (4), with the session's own latency from the
reply to (4) before it (60 s, a guess): the catch streams ESC from its start for 360 s (that
latency and 300 s for the owner's reaction, both guesses, card A's) and ends sooner, at the
loader's first prompt, once the press is caught (its cap, 380 s, keeps block 48's 20 s after
the ESC); the power-off window streams ESC for 360 s (the same two; its cap 365 s), and a watch
follows it on its line; each cable window records for 100 s (the latency and the owner's 40-s
minimum after (4)). **Each "now" states its deadline as a time of day**: the press's, the
catch's start plus 350 s (its 360 s less 10 s from power-on to the loader's prompt, a guess,
whose banner-to-prompt part was 2.3 s in block 48's catch); a cable action's, its window's
start plus 100 s; the power-off's, its window's start plus 360 s. The session says "press now"
only while the press's deadline is at least the owner's 40 s away — by 310 s after the catch's
start — and otherwise tells the owner not to press (§ 6). The owner does not act after a stated
deadline, and says so instead (§ 6's rules for a late action). `arith43b.out`'s `HANDSHAKE`
lines and cardnum rows pin each. Before `I-P1` starts the board's watch, the owner is told of
both cable actions in advance, each then going by (1)–(5). The board's
`linkprobe watch rlx0 10 600` runs across both (the coordinator's ruling of 2026-09-26: the
watch is the positive control of its own watch mode, and is cut from `linkprobe` if it records
no transition while the static reads flip — judged only at an action whose window the watch
spanned, P11); 600 s, `linkprobe`'s own limit, so that at the estimate it spans both windows
and H1 and H2 (P11, P12).

**⑪ `mfgtest auto` types a write the SPI driver refuses.** Its `MT-FLASH-2` writes `trywrite`
to `/proc/rtl819x-spi` and passes only if the driver's guard refuses it (`n_write_refused` +2,
`n_writes 0`, 讀 `config/mfgtest.sh`); its `MT-FLASH-3` runs `map 0`, the read `R1-M0` and
`R1-M1` run. It is not a flash-write command of CLAUDE.md's list, the guard is shown refusing
only (its permit side would be a write), and `R1-NW1` reads `n_writes 0` after both runs,
`n_write_refused` 4 above `R1-NW0` (P18). Its checks raise console marks that interleave with
its own lines (block 23's `C1-AUTO` and `C1-AUTO2` both read `MT-PORT      Port3 LinkURpL`, 量,
`FW-47`), so each run writes its lines to the board's tmpfs and prints the file after it ends;
block 23 read 9 of 9 once (`C1-AUTO2`) and 8 of 9 once, `MT-TICK` failing (`C1-AUTO`).

**⑬ Writes to the board's tmpfs.** The watch's log, the queue samples and `mfgtest`'s lines go
to `/tmp` (the declaration's `dir /tmp 1777`) through a relative target after `cd /tmp` or
through `busybox cp`'s argument (`cp` has no link in this image; `busybox killall` is block
48's precedent), never an absolute redirection: `cardcheck commands` checks absolute
redirection targets against the declaration's paths exactly, and the declaration names no file
inside `/tmp`. That limitation of the check is named here, not relied on to pass anything else
(a cardnum row counts zero absolute `/tmp` redirections).

**⑫ New instruments, each with a self-test and a mutation run whose unmutated pass came first**
(`/home/key/fwre-work/rebuild/s113/card43b`, `mutants43b.out`): `swpage.py` (rtl819x-switch
1.2's page; **no silicon page of 1.2 exists yet** — its fixtures are rendered from the driver's
own format strings, checked verbatim against the source), `lpread.py` (`linkprobe`'s `LP` and
`LPW` lines, red on `can` equal to the whole region, `A5A5A5A5`, errno 95, a missing `LP9`),
`cutgate.py` (1.1 adds `wait`, `P-LWH`'s; its desk rehearsal runs the card's own text,
`cutrehearse.out`), `carrierwatch.py`, `udpq.py`, `d4load.sh` with `d4cover.py` (rehearsed
against `lo`, `d4rehearse/`), `verbcheck43b.py` (card2's `verbcheck50` with its plants
re-anchored here), and, with no self-test of its own, the wrapper `inv43b.sh` (1.3: the console
watch around a watched invocation, a command line's tail watch, a watch's or a power-off
window's stop, the power-off window, the hold after a stop, a board X-cell's loader text ending
its line), rehearsed before the freeze with a stand-in `console-capture` and runner in a
scratch clone — permitting (a watch stopped by SIGINT, its `meta.json` reading `interrupted`;
the invocation's exit kept; a host-only invocation beside a running watch) and refusing (a
caught reset exits 5, a watch that did not start exits 4 with the invocation not run, a name
re-run is refused, and a board invocation, a `CAP` X-cell or a second watch beside a running
one is refused before it opens the port; a board X-cell whose capture holds the loader's text
exits 5; a watch ending on `<RealTek>` with no banner before it reads *at the loader's prompt*;
the hold waits the rest of its 90 s, returns at once once they have passed, refuses with no
watch running and exits 5 when the watch ends inside it) — and with one planted defect shown
failing: without its SIGINT-restoring shim a background watch ignores SIGINT and cannot be
stopped (`prefreeze/rc.tsv`'s `xw-` rows). Reused, pinned: `brdelta` 1.2, `pcapwin` 1.3,
`dmesgwin` 1.2 (card2), `iperflog`, and seating 43's shared `s1class.py` and card A's
`rttseries.py`. 量 at the desk (`lpqemu.out`): the image's own `/bin/linkprobe` under
`qemu-mips-static` prints `LP0 linkprobe 1 build 1bce836f2e21c43a` — the `LP0` gates' sample —
and every `SIOCETHTOOL` call returns 25 (`ENOTTY`: qemu-user does not translate it), so the
ioctl's ABI is exercised on the board only; the watch's schedule bound held there (at `10 ms`
over `1 s`, n within the bound 101, every sample `err`). `gates43b.out`: each new gate and
`--until` permitting a real or rendered sample and refusing a planted one (the catch's
`--until '<RealTek>'` on block 48's `R1-CATCH`, whole and cut before its first prompt, among
them), 28 of 28 with the GbE adapter attached, up, and the board off — its two `R0-CW` cases
read the adapter's carrier, so `gates43b.py` runs again in `chain43b.sh` after that attach and
before the freeze check (§ 6, before any cell).

---

## § 1 The image

`r6b6q`, quiet variant, recipe `acf8ed3d`, `nfjrom` `/home/key/fwre-work/rebuild/s112/r6b6/rtk/r6b6q/rlxfw/kroot/rtkload/nfjrom` (`ef5622d23738978bcce0bdce66c03c59cf86cd7320ddbbebcf58bb0f50edf6ee`), vmlinux `9e0ff326ae8bc9ccd7b66f8d58755246a4e8640a7df0011c24f6e84c73095134`, built twice byte-identical (`r6b6q2`, a cardnum row), initramfs from `_irfs-r6b6` (`/bin/iperf3`, `/bin/linkprobe` build `1bce836f2e21c43a`, `/bin/mfgtest` 1.1). Its build cell `/home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top` holds `rtl819x-nic.c` 1.5 and `rtl819x-switch.c` 1.2 (cardnum rows: their digests and version lines). The repository has since moved to rtl819x-switch 1.3 (`R6b-7`), so every source row on this card reads the build cell's copies, never the working tree's, and `linkprobe`'s and `mfgtest`'s rows read the r6b6 build's own repository copy. The chain is checked by `cardnum` rows: the manifest `verdict green`, `variant quiet`, that vmlinux and that initramfs source; the `rtkimage` record naming that `nfjrom` digest with a CLEAN tripwire verdict; the `nfjrom` on disk with that digest; `CONFIG_RTL_WTDOG` and `CONFIG_PRINTK` not set. `looprun` pins the `nfjrom` by digest before the port opens and compares the booted image's `RLXFW-ID0` with the build's (`--recipe-override acf8ed3d`, the manifest's); `R1-NW0` and `R1-NW1` read `recipe_id ACF8ED3D`. No cell names an address from `System.map`; `R1-DW`'s address is `PSRP3`'s, `0xBB800000 + 0x4128 + 3 × 4` (讀 the driver's `RTL819X_SW_PHYS` and `RTL819X_SW_PSRP0`, and `SPEC.md` `NET-30` 殘留's text: `arith43b.out`).

---

## § 2 The press, in order

| invocation | what runs | est. min (a guess) |
|---|---|---:|
| `I-0` | before power | 0.3 |
| `I-1` | the catch, `DW`, the round, the opening map | 7.1 |
| `I-B` | the opening state | 0.2 |
| `I-LP` | the `ethtool` ops; arm N | 0.1 |
| `I-D3` … `I-D3LUS1` (29) | twelve trials at the fix, two at 1.4, the re-arm back; each trial an invocation of its own under a watch | 14.1 |
| `I-CN` | cut point | 0.0 |
| `I-N0` | `NET-131`'s capture starts | 0.5 |
| `I-N` | `NET-131`: six two-request brackets | 2.9 |
| `I-N9` | that capture stops | 0.0 |
| `I-CM` | cut point | 0.0 |
| `I-M` | `D3-MISS` ②: twelve series | 2.9 |
| `I-CP` | cut point | 0.0 |
| `I-P1` | arm P: before the pull, the watch's check | 0.2 |
| `I-WPULL` | the pull's window (owner) | 2.7 |
| `I-P2` | reads with the cable out, the watch's check | 0.6 |
| `I-WPLUG` | the re-plug's window (owner) | 2.7 |
| `I-P3` | reads with the cable back, H1, H2 | 0.6 |
| `I-WLW` | the host waits for the board's watch | 3.3 |
| `I-P3B` | the watch read, a bracket, the liveness gate | 0.2 |
| `I-C4` | cut point (`R6b-4`) | 0.0 |
| `I-4F` | `D4` at the fix opened | 0.3 |
| `I-WF` | the 31-min flood | 31.1 |
| `I-4F9` | the read after it; `NET-76`'s reads | 0.4 |
| `I-CT` | cut point | 0.0 |
| `I-4T` | the tail's arm and server | 0.4 |
| `I-WT` | the TCP tail | 5.1 |
| `I-4T9` | the tail's reads | 0.2 |
| `I-CL` | cut point | 0.0 |
| `I-4L` | `D4` at 1.4 opened | 0.3 |
| `I-WL` | the 1.4 load, 2 min | 2.1 |
| `I-4L9` | the read after it; the re-arm back | 0.4 |
| `I-Z` | closing | 0.4 |

About 79 minutes from the catch window's opening to power-off if nothing is cut: a guess from
block 48's transcripts (`timings48.py`: a bracket 5.3 s, a switch 3.3, port-3 3.9, liveness
0.9, a trial at the fix 30.2, a server start 7.0, a stop 5.3, the round 24.7, a map 13.9),
block 23's `mfgtest auto` (26.9 s), the catch at its 380-s cap (it ends sooner, at the press's
first prompt), and guesses: 1 s for each invocation's start inside a command line, 1 s and 0.5
s for a watch's start and stop, 30 s for each session turn between two command lines, and 30 s
for each of the owner's two replies in arm P. The `R6b-4` cut point falls about 38.3 minutes
after the catch window opens (the rule: 44, § 6 S6); the `R6b-4` block is about 41 minutes, so
one started at 23:05 ends by about 23:45, before § 6's last-capture bound 23:52. 51 board
brackets, 51 host pre-reads, 59 invocations in four command lines. `I-0` is before power and
not in the figure. The latest catch, 23:14, allows 37.3 minutes for what is never cut: `I-1`,
`I-B`, `I-LP`, `D3`'s invocations with every trial at block 48's measured timeout (`LUS1`, 73.4
s end to end), the four cut points an all-cut path still runs, and `I-Z`, each after a refusal
and its 90-s hold. Every sum here is `arith43b.py`'s (`time_calc`, over the cells the generator
writes to `est43b.tsv`), each pinned by a cardnum row.

The order protects the priorities: `I-D3` first after the opening reads (`D3` is never cut),
then the blocks at 1.4 and the capture's effect, then arm P (after `D3` and ②, never inside a
timed run), then `R6b-4`, whose flood is the longest single cell and whose 1.4 arm comes last
so its aftermath can void nothing before it.

---

## § 3 Predictions, each with what refutes it

### 3.0 What is read, and the names used below

A **bracket** is the board read `<name>-R…` (block 48's: the driver, the board's SNMP and ARP,
the switch's counters, the driver again) between two host reads: `-P…` just before it (`HP`:
the adapter's `rx_packets` and `tx_packets`, now also `eth0`'s `tx_packets`, and the host's
`Icmp:` and `Udp:` lines) and `-H…` just after it (`HN`, a capture's read-time window where one
runs, the kernel log's window). Δ is this bracket minus the previous one; `brdelta` 1.2 prints
the pair (`board`, `cpu`, `p3`, `ident`, `buckets`, `host`, `path`, `hbound`, `snmp`, `fault`).
Names as block 48's: `n` Δ`n_tx`, the CPU port's `c` (`CRCAlignErr`), `j`, `f`, `d`
(`JabberErr`, `FragErr`, `Drop`), port 3's output `o`, K = `o` − (`c` − `j` − `f` − `d`), the
host's `h` and `i`; **`cn` = `n` − `c`**, descriptors the engine took and no counter counted
(`NET-78` 殘留). From rtl819x-switch 1.2's page (`swpage.py`): `n_linkq`, `lde0`, and per port
`psrp<p> <word> up <0|1> lde <count> lj <jiffies>`; `lde<p>` counts rlxfw's reads that saw that
port's bit 8 (`LinkDownEventFlag`, read-to-clear) — a lower bound on link-down events, blind to
the vendor's reads. From `linkprobe` (`lpread.py`): the `LP` call lines, `LP9`, and the watch's
`LPW` lines.

### 3.1 The premise, tested in every bracket

* **P0.** At every pair of consecutive board reads: **(a)** K = 0; **(b)** `inner ≤ o ≤ outer`
  (`within yes`); **(c)** for `N1.pcap`, the record-order anchor holds; **(d)** in every
  stimulus bracket with a path gate (`NET-131`'s runs, ②'s twelve series), port 3's input Δ is
  at least the host's Δ`Icmp.OutEchos`. **What a failure voids, written now** (block 48's
  text): (a) failing by K frames voids that bracket's stage chain, and a threshold verdict
  stands only if its counter lies at least |K| beyond the threshold on the side it claims; (b)
  failing voids that bracket's host side, and **at a pair that spans a re-attach (S1 branch b)
  (b) is void, never refuted** (the adapter's counters restart); (c) failing voids that
  capture's record-order windows; (d) failing is S1, never read as the fix failing.

### 3.2 The opening state, and `NET-30` 殘留

* **P1** (`I-B`). `B-SW`, the first read of rlxfw's switch page on this boot:
  `version rtl819x-switch 1.2`, `n_linkq 0`, `psrp3 000000F9 up 1` (Linux-side `PSRP3` with the
  link up, bit 12 clear: `NET-34`, 量), and `lde 3` equal to `lde0`'s bit 3 — the only rlxfw
  read of `PSRP3` before `B-SW` is the slot-0 snapshot at `subsys_initcall`, which `lde0`
  reports (讀 `rtl819x_sw_lde_boot`). The NIC's page as block 48's `B-00-T`: 1.5 untouched since
  boot (`tx15 txlen rlxfw … dirty 0`, `v15 last - 0 ok 0 refused 0`, `sw never`,
  `mt none 1455`). `B-RMEM` prints two numbers (`rmem_default`, `rmem_max`). **Refuted by**
  `lde 3` above `lde0`'s bit 3 (a link-down latched after the snapshot and before `B-SW`: a
  reading for `NET-30` 殘留, and arm N's baseline then says whether it recurs), or the NIC page
  not 1.5's untouched state (no cell after it until the owner has read it, § 6).
* **P2, `NET-30` 殘留, the reading** (no pass or fail: the reading is the experiment, `R6b-6`'s
  card rule). `R1-DW` reads `PSRP3` at the caught prompt after a cold power-on with the GbE
  adapter attached before power and untouched: `BB804134:<tab><word>`. Predicted (推): bit 4 set
  (the loader brought port 3 up before the prompt: block 24's `C10-PS0` read `000011F9` there,
  量) and bit 12 set (the loader-state value, `NET-34`: `000010F9` at the loader, `000000F9`
  under Linux, 量). **Bit 8 decides, written now:** 1 — a link-down was latched between power-on
  and the prompt with neither of `NET-30`'s two candidates (no vendor-firmware run, no attach)
  in the window: the cold power-on or the loader's PHY bring-up sets it, and the candidate list
  gains that entry; 0 — this power-on left it clear; one read does not exclude power-on as an
  occasional source (the prior below is 2 of 13). A reading beside it, since state can survive
  a short power-off (`MEM-17`): the board's off-time, from the owner's reply confirming card
  A's power-off to the banner's arrival in `R1-CATCH` — its `started_wallclock` plus the
  seconds of `R1-CATCH.timing`'s last row whose offset is at or before the first byte of
  `Booting...` (`FW-35`) — and not to the catch's start: the catch opens before the press and
  the owner may press up to 350 s after it (§ 0 ⑩, "catch open — power on now, by HH:MM:SS"),
  so its start could fall up to that long before power-on and the off-time would read short by
  as much. What it still counts wrong: the owner's lag in replying (the reading is shorter by
  it) and power-on to the banner (longer by it), neither measured here, and the wall clock to
  the second. Then `SW7` (the boot capture's `RLXFW-SW7=`, read by `R1-SW7`) and `lde0`: `DW`
  is a bus read, so it clears bit 8 (read-to-clear, `NET-11`, 量 at the loader); `SW7`'s bit 3
  then says whether the rescue, `IPCONFIG`, the upload, `J` and the kernel's boot to the switch
  driver's init latched another. Prior: 2 of 13 boot groups carried S0' bit 8 (`NET-126`). Not
  measured: a read after `IPCONFIG` and one after the upload (`looprun` does not stop there).

### 3.3 The `ethtool` ops (`I-LP`)

* **P3.** `LP-G` (`linkprobe get rlx0 lo eth4 nosuch0`) reads exactly:
  `LP0 linkprobe 1 build 1bce836f2e21c43a`;
  `LP drv rlx0 rc 0 driver "rtl819x-nic" version "rtl819x-nic 1.5" fw "" bus "platform" can 0`,
  `LP link rlx0 rc 0 data 00000001 can 0`,
  `LP ring rlx0 rc 0 rx 8/8 mini 0/0 jumbo 0/0 tx 4/4 can 0`; `lo`: `drv` rc 122 can 192,
  `link` rc 0 data 00000001 can 0, `ring` rc 122 can 32 (讀 `loopback.c`: only
  `.get_link = always_on`); `eth4`: rc 122 at all three (the vendor tree sets no
  `ethtool_ops`); `nosuch0`: rc 19 at all three; `LP9 calls 12 ok 4 refused 8 nowrite 0` (every
  figure a line of `arith43b.out`: `EOPNOTSUPP` 122 and `ENODEV` 19 from the build cell's
  headers, the ring from `NIC_RX_DESC`/`NIC_TX_DESC`). `lpread` reads `verdict read`. The
  kernel's side: `n_et_link` Δ 1 over `LP-N0` → `LP-N1` and `et_link_last` `FFFFFFFF` →
  `00000001` (量, every committed capture through block 48: 563 `n_et_link` lines in 332 files,
  every one `0`, beside `et_link_last FFFFFFFF`: `etlink.out`), `n_linkq` Δ 1 over `LP-SW0` →
  `LP-SW1`, `lde` Δ 0 at every port. Twelve calls on the probe's side against one on the
  kernel's: the two counters run at different rates, so their agreement on `rlx0`'s share is
  evidence. **Refuted by** any line otherwise — `lpread` red (a call that returned 0 and wrote
  nothing, `A5A5A5A5`, errno 95, no `LP9`), `rlx0`'s link not 1 with `psrp3 up 1`, `eth4` other
  than 122, `n_et_link` Δ other than 1: `D6`'s ops are not executed as written, named from the
  line.
* **P4, arm N** (`LP-SW1` → `AN-SW2`, nothing between). `AN-D`: `lde` Δ 0 at every port,
  `n_linkq` Δ 0, `n_writes` Δ 0, `masked 3 … bit8 0 0 same yes`. **Refuted by** `lde` Δ ≥ 1: a
  link-down latched with nothing done — a flapping link (`NET-56`'s contact, 推), which arm P's
  reading then has to exceed.

### 3.4 `D3`'s second boot, and its control (`I-D3`)

Block 48's trials, cell for cell (`NET-111`'s shapes; the board's one-off server with its own
log, the host's MIPS client under `qemu-mips-static` with `timeout 70`), and a bracket after
each. Added: each UDP receive trial's `-Q` (§ 3.5).

* **P5, `D3` at the fix.** The end-of-test exchange completes in **12 of 12** (each host log
  ends `iperf Done.` after its summary, rc 0, no `No route to host`, no `iperf3: error`;
  `iperflog parse` finds TEST_END in each board-receives trial's log); in every trial bracket
  `n` = `c` = `o`, `jfd` 0, K 0, `n_recov_fire` Δ 0, `n_tx_stop` Δ 0 (block 48: 12 of 12 and
  every one of these, 量). **What it means, written now:** a pass is boot 2 of *driver 1.5 at
  `txlen vendor`* — the NIC object byte-identical to block 48's, the image not (§ 0 ②), and
  every trial run under a watch's ESC stream, about 100 ESC a second into the board's UART
  (§ 0 ⑤), which block 48's trials did not carry — and with block 48's, `D3` is met on two
  boots. **Refuted by** any of the twelve without `iperf Done.`: *`D3` is not met on this
  boot*, recorded with the image variable (switch driver 1.2, the initramfs's two files) and
  the ESC variable (the watch's stream through every trial) beside it (neither separated), and
  the failure named from the host's output, the server log's shape, the bracket and the ring,
  as block 48's P15.
* **P6, the control at 1.4** (`LUR1` on `D3-X`'s re-armed ring, `LUS1` on `D3-Y`'s, then
  `D3-Z-SW` back to the fix). At least one of the two ends without `iperf Done.` (讀 `NET-111`,
  `NET-116`, block 48: UDP trials at 1.4 completed 1 of 14 over seatings 39, 40 and 42 —
  board-receives 1 of 7, board-sends 0 of 7; by ring state, the one known to start on a freshly
  armed ring, block 48's `LUR1`, completed, and a board-sends trial has never started on one,
  so both completing here is not improbable). **Refuted by** both completing: the positive
  control failed, and this boot's 12 of 12 says nothing about the fix. Beside it, a reading:
  `n_recov_fire` or `n_tx_stop` Δ ≥ 1 in either bracket is 1.4's setting stalling on this boot
  (`n` > `c` or an engine-owned `txd` alone is `NET-78`'s counted-nowhere shape, which fires
  nothing: a reading, not a stall). **`D4`'s fallback positive control, stated now**: used only
  if `I-4L` was cut or skipped (P13), labelled a different-stimulus control (`iperf3` UDP, not
  `D4`'s load), and shown only by `n_recov_fire` Δ ≥ 1 in `LUR1`'s or `LUS1`'s bracket — `D4`'s
  own counter; a stall shown by `n_tx_stop` alone is *control not shown*, never read as `D4`
  met.
* **P7.** At each board-receives trial at the fix that completes, `iperflog compare` reads
  AGREE (block 48: 5 AGREE and `TR1` refused, a host line in no format the tool knows —
  undetermined, a reading). **Refuted by** DISAGREE.

### 3.5 `NET-117` 殘留 (`D3-UR1`…`UR3`, `D3-LUR1`)

* **P8.** **(i)** P18's placement again (block 48's rule): with L = the host's `Sent` −
  Δ`Udp.InDatagrams` over `-S0` → `-S1`, Δ`RcvbufErrors` ≥ 0.9 L in each of `UR1`–`UR3` (block
  48: 4 of 4). **(ii) The ~64, decided.** 讀 the build cell: a socket's receive queue holds
  datagrams while `sk_rmem_alloc + truesize < sk_rcvbuf` (`sock_queue_rcv_skb`); `sk_rcvbuf` =
  `rmem_default` = 256 × (S + 256), S = `sizeof(struct sk_buff)`; a 1,400-B datagram's
  `truesize` = 1,504 + S (rtl819x-nic's `dev_alloc_skb(len + 2)`, `NET_SKB_PAD` 32,
  `SKB_DATA_ALIGN` to `SMP_CACHE_BYTES` = 1 << `L1_CACHE_SHIFT` 5 = 32 B: the build cell's
  `skbuff.h` and `asm/cache.h`, `arith43b.out`). So `B-RMEM`'s `rmem_default` gives S and the
  queue's capacity N = ⌊(`rmem_default` − 1) / (1,504 + S)⌋ (`udpq` prints `capacity … N`).
  Predicted (推): N = 64 (S 161–168: `arith43b.out`), and in each UDP receive trial the
  datagrams block 48 counted by difference (Ip `InReceives` − arrivals − the host's non-UDP
  transmits; 64, 63, 64 and 64 there) equal N less the host's ARP frames in that window — the
  full queue the one-off server discards unread when it exits. No tolerance is fitted: the one
  source of a shortfall known is that the host's non-UDP transmits (`tx_packets` −
  `Udp.OutDatagrams`) include its ARP frames, which never reach the board's IP
  (`notes/nic-driver.md` § 27.8), and no cell counts them apart. **Refuted by** a count above N
  in any of the four (the queue holds at most N), or below N by more than that window's non-UDP
  transmits: the ~64 are not the queue's contents at exit, and the row names the difference.
  **(iii) A reading beside it:** `-Q`'s two copies of `/proc/net/udp` (`busybox cp`, into
  `/tmp`, printed by `-S1`) at about 20 s and 32 s after the sampler starts (inside the 30-s
  data phase, 推 from block 48's cell times), each `rx_queue` as a count k of datagrams
  (`udpq`); no refutation rests on them (an instant's queue is not its capacity). `eth0`'s
  `tx_packets` in every `HP` bounds the host's UDP datagrams sent elsewhere (the 65 by which
  the host kernel's `Udp.OutDatagrams` exceeded the board's arrivals in block 48).

### 3.6 `NET-131` 殘留's deciding bracket (`I-N`)

Six runs — 61, 62, 63, 61, 62, 63 — identical cells but for the length (the generator refuses
otherwise): liveness; a re-arm at 1.4; the port-3 gate; a bracket `-R0`;
`ping -c 2 -s L−42 -i 0.05 -W 1`; a bracket `-R1`; the pair; a re-arm at 1.4. The re-arm's
`ifconfig rlx0 down` flushes the board's neighbour table (推), so the board's frames between
`-R0` and `-R1` are its ARP request (60 B, clean), reply 1 and reply 2: `j`, `f` and `d` there
are reply 2's alone. `N1.pcap` runs across all six (`I-N0` → `I-N9`); `W-NORD` maps the 24 host
reads taken while it ran onto record indices (block 48's anchor rule, P0 (c)), so each run's
window `-H0` → `-P1` is exactly the frames the host counted there.

* **P9.** At every run: sequence 1 answered (the first frame at L on a re-armed ring, clean
  under M1-cover8: block 48's `SL` read it answered at all seven faulty lengths, 量). Reply 2's
  `ph_len` is 256 k under H-prev at offset 52 (推), k = reply 1's payload byte 10 (`pcapwin`'s
  `echo_first … b10 k`), 0–15: **k ≥ 7** — a jabber: sequence 2 unanswered, `j` = 1; **k = 0 or
  6** — not predicted; **1 ≤ k ≤ 5** — a legal wrong length, branch (a) (answered with an
  excess of 256 k − 4 − L bytes) or (b) (unanswered, `j` = `f` = 0, `d` = 1). **The decision
  for `NET-131`, written now, in any run where `j` = `f` = 0 and `d` ≥ 1** (the bracket card
  B50's P9 names): K = 0 — the Drop-counted frame was not forwarded: candidate (2) is excluded
  for it, and E-L1's and `SL-0062`'s K is candidate (1) or a third cause; 0 < K ≤ `d` —
  candidate (2) stands and (1) is excluded; K < 0 or K > `d` — both excluded, a third cause
  named from the bucket line and the window. 推 k is about uniform over 0–15, so each run lands
  in 1–5 with about 0.33 and at least one of six with about 0.91 (`arith43b.out`) — the chance
  of reaching branch (a) or (b), not of a decision: a decision needs branch (b), whose share of
  1–5 is unknown, so no chance of a decision on this press is stated. If no run falls in branch
  (b), `NET-131` stays open (a reading), the experiment named again. **Refuted by** sequence 1
  unanswered at any run (the re-arm did not give a clean start), or sequence 2 answered at its
  own length (it did not go wrong).

### 3.7 `D3-MISS` ② at the fix (`I-M`)

* **P10.** Card A's twelve series (`ICMP`: 56, 256, 512, 1,024 and 1,472 B, 20 echoes at 50 ms
  each), the host's capture off and on in the plan `011001100110` (ABBA from off, so a drift
  linear in time weighs both states alike), card A's cells per series: the liveness gate, for
  an on-series `TDT` started, a `pgrep -xc tcpdump` before (a reading), the series, the count
  after (a reading), the capture stopped (a gate: none left), a bracket and its pair (a path
  gate). The arm runs at `txlen vendor`, on a ring re-armed once at its start (`M2F-SW`).
  `rttseries` 1.1 (card A's reader, pinned) counts a series only if its five sizes read 20 of
  20, both counts read its planned state, its liveness 4 of 4 and its pair `covered yes` and
  `fault jfd 0`; per size, the median of each state's series averages and the Mann-Whitney U
  over the on × off pairs, with lo and hi from U's exact null for the counting n (`rttseries`;
  `arith43b.py` recomputes them by its own recurrence — 6 against 6: `lowers` iff U ≤ 5,
  `raises` iff U ≥ 31; 6 against 5: `lowers` iff U ≤ 3, `raises` iff U ≥ 27; 5 against 5:
  `lowers` iff U ≤ 2, `raises` iff U ≥ 23; a state with fewer than 5 counting series is
  `unmeasured`), a two-sided 5 % test at each size, card A's, fixed there. The five sizes are
  tested on the same series: with no effect, the chance of a false `lowers` at any of them is
  at most 0.103 (the union bound), stated here and not corrected. Predicted (推, card A's
  framing: `NET-121`'s captured series moved +13.5 and +19.7 % at 256 and 1,472 B against +7.2
  and +9.9 % uncaptured, n 1–2): at no size `lowers`; with 6 against 6 and a series spread near
  ±14 %, `unresolved` is likely even if the effect is real — the test's power is low, and the
  card says so rather than widening anything. **Refuted by** `lowers` at any size. Beside it,
  P17's clause: every series pair reads `jfd` 0 at the fix. The vendor's and 1.4's arms are
  card A's; this arm is the fix's, so ② gets a third column (the image's setting), not a
  repeat.

### 3.8 Arm P: `get_link`'s positive control, and `MT-PORT` (`I-P1`…`I-P3`)

* **P11.** **Before**: `P-SW0` `psrp3 … up 1`; `P-LG0` `rlx0` and `lo` link `00000001`; `P-WS`
  `LPW start rlx0 v 1 rc 0`. **With the cable out** (the owner's pull inside `P-PULL`'s 100 s):
  `P-PULL`'s carrier watcher a `CW t … carrier 0` line (推: `R0-CW` read carrier 0 with the
  board off, 量; a `CW start` line already at carrier 0 means the owner acted before the window
  opened, and the carrier half of the pull is unmeasured); `P-SW1` `psrp3 … up 0` (a gate; 推
  the word `000000E9`, `NET-11` ①'s kept speed and duplex bits); `P-D1` `delta lde 3 d` ≥ 1 and
  0 at every other port, `n_linkq` Δ ≥ 1; `P-N1` `et_link_last 00000000`; `P-LG1`
  `LP link rlx0 rc 0 data 00000000 can 0` beside `LP link lo rc 0 data 00000001 can 0` in one
  call; `P-MT1` (its file, printed after it ends)
  `FAIL  MT-PORT      Port3 has no LinkUp -- cable out, or the wrong jack (by rtl819x-switch 1.2; psrp3 …)`
  and, 推 from block 23's `C1-AUTO2`, `8 of 9 ok, 1 FAIL` (another check failing — block 23's
  `C1-AUTO` failed `MT-TICK` — is a reading beside P11, never its refutation); `P-LW1` an
  `LPW t … v 0 rc 0` line. **After the re-plug** (inside `P-PLUG`'s 100 s): `CW t … carrier 1`;
  `P-SW2` `up 1` (a gate, S4); `P-D2` `masked 3 … same yes` (a gate: `PSRP3` equals its
  pre-pull word with bit 8 masked); `P-LG2` `rlx0` `00000001`; `P-MT2`
  `ok    MT-PORT      Port3 LinkUp by rtl819x-switch 1.2; vendor tree present` and, 推,
  `9 of 9 ok, 0 FAIL`; `P-LWR` (after the watch's own end, which `P-LWH` waits for on the host)
  `watch sequence 1,0,1`, `trans 2`, `nowrite 0`, `err 0`, `bound n … max 60001 within yes`;
  `P-N3`'s `n_et_link` exceeds `P-N0`'s by the watch's `n` + 3 (`P-LG0`, `P-LG1`, `P-LG2`; both
  watches' `n` after a restart), exactly: two counters of the same calls. **Refuted by**
  `rlx0`'s link not 0 while `psrp3` reads `up 0`, or not 1 after (`get_link` does not follow
  the cable: `D6`'s positive control fails); `lde 3` Δ 0 across the pull (1.2's accounting
  missed the event, or a vendor-internal `PSRP` read consumed bit 8 before rlxfw's first read,
  § 7: the two are not separated here); `MT-PORT` not red while out or its label not as
  written; the watch recording no transition at an action whose window it spanned while the
  static reads flip (the watch mode is refuted and cut from `linkprobe`, the ruling);
  `n_et_link`'s Δ other than n + 3 (a call one side counted and the other did not). **The
  watch's span, written now:** a half is the watch's only if its window cell's `END` line in
  its invocation's transcript (`I-WPULL`'s, `I-WPLUG`'s: `CLOCK_MONOTONIC_RAW`) is no later
  than the watch's start stamp — `P-W`'s `t0_raw` (its `meta.json`, the same clock), or
  `X-PW<n>`'s after a restart — plus 595 s (600 less a 5-s margin: the capture opens before the
  watch starts); a half whose window ends later is **unmeasured, never refuted**, and the watch
  mode is judged on the other half alone. Before the owner is asked for each action, `P-WT1`
  and `P-WT2` read the time since `P-W` started (`cutgate --since-max 5.66` on `P-W.meta.json`:
  340 s is 600 less the margin, the 100-s window, 65 s for the window's start after the reply —
  the session's latency and the wrapper's and runner's starts, guesses — and 90 s for the
  owner's reply, a guess, `arith43b.out`); `cut refuse` restarts the watch before the ask
  (§ 6), and the restarted watch is read against the sequence still to come — `1,0,1` if
  restarted before the pull, `0,1` before the re-plug, the first watch then against `1,0`. At
  the estimate `P-WT1` reads about 8 s and `P-WT2` about 205 s.
* **P12, H1 and H2** (`P-SW2` → `P-SWH1` → `P-SWH2`, the watch running). H1, the host's
  `ip link set down`, 3 s, `up`: `lde 3` Δ 0, no watch transition (`NET-30`: not a link event
  on this RTL8153, 量 once). H2, the host's `ethtool -r`: 推 refused (`r8153_ecm` implements no
  `nway_reset`), `lde 3` Δ 0. **The watch's span, as P11's:** H1's (H2's) *no watch transition*
  is the watch's only if `P-H1`'s (`P-H2`'s) `END` line in `I-P3`'s transcript is no later than
  the watch's `t0_raw` plus 595 s; past that, the half is **unmeasured**, never refuted, and
  `lde 3` alone reads it (at the estimate `P-H2` ends about 404 s after `P-W` starts).
  **Refuted by** `lde 3` Δ ≥ 1 across either: a host-side command makes a link event — `NET-30`
  殘留 ②'s answer, and `P-LWR`'s expected sequence then fails as a reading, not as the watch's
  refutation.

### 3.9 `R6b-4` (`I-4F`, `I-4T`, `I-4L`)

* **P13, `D4` at the fix.** Over `F-00-R` → `F-99-R` (the 31-minute flood beside the length
  loop). **`D4`'s criterion**, its DoD's: `n_recov_fire` Δ 0. **The traffic conjunct, fixed
  now** (`arith43b.out`): `F-COV` `sent-all yes` and `answered-all yes` (every size 18–1,472
  sent and answered at least once, so every frame 60–1,514 went each way); `flood received` ≥
  1,199,591 (0.5 × `NET-76`'s measured 1,289.9 frames/s over the 1,860-s flood — seating 32,
  driver 1.x, so a floor, not a prediction), read from `F-COV`'s line
  `d4cover flood transmitted T received R` — `d4cover`'s reading of `ping`'s own summary in
  `/home/key/fwre-work/rebuild/s113/d4-43b/F/flood.log`, the summary `F-FLOOD`'s log also
  prints as `flood … packets transmitted, … received`; `low-intervals` 0 (no 10-s interval in
  which the host's `rx_packets` rose by less than a tenth of the median); and `F-D`'s `n`
  (Δ`n_tx`) ≥ 1,201,046 (the flood floor plus one answered echo a loop size). No gate reads any
  of them: `F-COV` and `F-D` are readings (`NAME?`), scored against these floors at the record.
  **Any of them missed — `sent-all no` or `answered-all no` included — is *the traffic conjunct
  unmet*, never `D4` met**, whatever the counters read. Readings beside it: `n_tx_stop` Δ
  (stricter than `D4`'s letter: a stop with no fire is the queue stopping on a full ring and
  the recovery timer's level test finding the slot already retired, `n_recov_spurious`), `jfd`,
  `cn`, K, `F-SWD`'s `lde` Δ. **What it means, written now:** `n_recov_fire` Δ 0 with the
  traffic conjunct met, beside P16's stall at 1.4 on this boot, is `D4` met — no recovery over
  ≥ 30 min of traffic that includes every formerly bad length, on the fixed setting, while
  1.4's setting stalls on the same boot. P6's stall stands in for P16 only if `I-4L` was cut or
  skipped (`CUT-4`, `CUT-L`, an S1 whose recovery failed before it), labelled a
  different-stimulus control and counted only with `n_recov_fire` Δ ≥ 1 — `D4`'s own counter —
  in `LUR1`'s or `LUS1`'s bracket; a stop by `n_tx_stop` alone is *control not shown*, never
  `D4` met; if `I-4L` ran and read `n_recov_fire` Δ 0, `D4` is not shown on this boot.
  **Refuted by** `n_recov_fire` Δ ≥ 1: not a stop (S3), and `D4` takes its branch *the
  remaining stall named as a separate fault* — named from what the board kept, since the
  driver's own recovery (`recov_mode 1`, `recov_ms` 1000, 讀 `rtl819x-nic.c`) re-arms the ring
  about 1 s after a stall, before any cell reads it: `n_recov_arm`, `n_recov_fire`,
  `n_recov_ok`, `n_recov_fail` and `n_recov_spurious` Δ, `recov_j_fire`, `recov_rc`, `cn`,
  `jfd`, and `d4cover`'s low intervals (where in the flood the host's receive fell); the ring
  at the stall itself is not read (§ 7).
* **P14, `NET-76` 殘留** (after the flood, before any re-arm). `N76-A` 4 of 4 answered; `N76-PL`
  4 of 4; `N76-SN` Icmp `InEchos` Δ 4 and `OutEchoReps` Δ 4; `N76-W` 4 echo replies on the
  capture (推: seating 32's after-flood silence was driver 1.x's state). The host's neighbour
  state after `arping` is a reading, gated nowhere: this host's `arping` (Habets 2.24; `-I`
  names the interface, 量 at the desk) sends through its own link-layer socket, which 推 does not
  refresh the kernel's entry, so `STALE` there is no refutation. **Refuted by** fewer than 4
  (`NET-76` 殘留 reproduced): the reads place it — `InEchos` Δ < 4 is *lost before ICMP* (the
  board's Ip `InReceives` Δ in the same reads says whether they reached IP); `InEchos` Δ 4 with
  `OutEchoReps` Δ 0 is *no reply generated*; `OutEchoReps` Δ 4 with fewer on the capture is
  *generated but lost*; its read set runs before S1 (S7), and `I-4T` re-arms before its own
  liveness gate.
* **P15, the TCP tail** (five minutes, board sends, on the ring `T-SW` re-armed at the fix
  after `NET-76`'s reads). `T-TR` ends `iperf Done.` (rc 0); `T-D` `n_recov_fire` Δ 0, `jfd` 0,
  K 0. **Refuted by** either failing: the fix under a sustained TCP send, named as P13's
  failure is.
* **P16, `D4` at 1.4, the positive control** (`L-00-R` → `L-99-R`: the same load for 120 s on a
  re-armed ring). `n_recov_fire` Δ ≥ 1 — `D4`'s own counter, so the control moves what P13's
  criterion reads — and `j` + `f` + `d` ≥ 1 (推: 1.4 faults at the loop's bad lengths; block
  48's `E-L1` fired 7, 量); `cn` read beside the fix's 0 (`NET-78` 殘留). `n_tx_stop` Δ ≥ 1 with
  `n_recov_fire` Δ 0 is a stall the recovery timer found already retired (P13): *control not
  shown*, a reading, never read as the control passing. `LE-L` passes after the re-arm back to
  the fix. **Refuted by** `n_recov_fire` Δ 0, whatever `n_tx_stop` reads: the positive control
  did not move `D4`'s counter, and **`D4` is not shown on this boot** (P6's stall does not
  stand in when `I-4L` ran). **`NET-68` 殘留, a reading** (does a recovery persist under
  continued traffic): with `n_recov_fire` Δ ≥ 1, `n_recov_ok` Δ equal to it and `n_recov_fail`
  Δ 0 say each recovery restored TX; `n_recov_fire` Δ ≥ 2 with the load answered across the 120
  s (`L-COV`'s counts and `low-intervals`) says traffic flowed after a recovery until the next
  fault — a recovery that lasts until the next bad frame, at 1.4; `LE-L`, after the re-arm back
  to the fix, closes it.

### 3.10 `D2`'s refutation clause on this boot, the maps, the host path

* **P17.** Every bracket whose whole board window ran at `txlen vendor` reads `jfd` 0:
  `D3-00-R` → `D3-TR1-R` … `D3-US2-R` → `D3-US3-R`, `M2F-00-R` → `M2F-S01-R` … `M2F-S11-R` →
  `M2F-S12-R`, `F-00-R` → `F-99-R`, `T-00-R` → `T-R`; `LE-00-R`'s pair is excluded (it spans
  the re-arm from 1.4). **Refuted by** `jfd` ≥ 1 in any, subject to P0 (a): the fix is partial.
* **P18.** `R1-MB0` and `R1-MB1` read blocks 46–48's map digest (`0927be41…`), 31 groups the
  same and 1 `DIFFER` in group 0; `n_writes 0` at `R1-NW0` and `R1-NW1`, which carries no
  information about writes (`FW-142`); `n_write_refused` 4 higher at `R1-NW1` than at `R1-NW0`
  (2 a run: `MT-FLASH-2`'s two pointers both refuse, `config/mfgtest.sh`; 2 if only `P-MT1`
  ran, 0 if arm P was cut); `recipe_id ACF8ED3D`. **Refuted by** another digest or group line
  (flash moved since block 48), or `n_write_refused` moving otherwise (a refusal the card did
  not cause, or one `mfgtest`'s run did not count).
* **P19, the host path** (`NET-124` 殘留). Every liveness gate 4 of 4, every port-3 gate `LinkUp`
  on both readers, every path gate `covered yes`, every kernel-log window `follower 1`. The
  `BUG` trace is counted per window, a reading (block 48: 1,350 over the press, the path
  working). A failed gate is S1's, classified from the board before the host is touched.

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck` refuses
the verbs (`FW-113`); the one loader command is `R1-DW`'s read; every upload is `looprun`'s,
which requires `00000000` read back from the `AUTOBURN` word first; `mfgtest`'s `trywrite` is
refused by the SPI driver's guard (§ 0 ⑪). 🔴 Every `--send` is at most 127 characters, holds no
`$`, and holds no upper-case word but the loader cell's (the generator refuses a macro name in
any). 🔴 **No gate reads a console mark** (`FW-47`; a cardnum row counts zero); `SW7` is read,
never gated. 🔴 **No cell holds the ring, sweeps, or writes a PHY register** (cardnum rows count
zero; B1 is dropped). 🔴 **rlxfw's switch page before the vendor's `port_status`** in every cell
that reads both, and never a `port_status` between an owner's action and rlxfw's first read
after it (the generator refuses otherwise): the vendor's reader clears bit 8 without recording
it. 🔴 The board's `/tmp` is written only through a relative target after `cd /tmp` or
`busybox cp`'s argument (§ 0 ⑬). 🔴 `rlx0` goes down only in the card's own cells, and every
`up` finds the ring freshly armed with the engine off (`NET-58`; the generator refuses
otherwise). 🔴 **Every 1.4 arm and trial begins and ends with a re-arm before the next liveness
gate** (S2; the generator refuses a card on which any § 6 path reaches a liveness gate on a 1.4
ring that carried traffic since its switch). 🔴 **No frame capture is printed**; `pcapwin` alone
reads a capture. 🔴 **No line of the host's kernel log reaches `bench/`**: only `dmesgwin`'s
counts. 🔴 No host cell prints a home path into `bench/`. 🔴 No cell touches the reset button or
the watchdog. 🔴 No step removes `/proc/rtl865x/`. 🔴 `sudo -n pkill -INT -x tcpdump` stops every
`tcpdump` on the host: `R0-TCPC` requires none before power, `N-LIVE` exactly one before
`NET-131`'s runs, each ② on-series its own, each `-C0`/`-C1` counts them. 🔴 Exactly one `dmesg`
process, the off-card follower, runs from before `I-0` to after `I-Z`. 🔴 No `iperf3` server
outlives its trial. 🔴 **A watch holds the console whenever the board runs a kernel and no board
capture is open** (§ 0 ⑥): every host-only invocation longer than the bound runs under one
(`inv43b.sh --watch`), every command line ends with one (`--tail`), no watch or power-off
window holds the banner in its `--until` (the generator refuses one), and no board cell is
typed while a watch holds the console (`--stop` first, in the same command line; after a stop,
`--hold` before it, § 6; the wrapper refuses a board invocation, a `CAP` X-cell, a watch or the
power-off window while any console capture runs, and lets a host-only one run beside it). 🔴
**The owner's actions go by § 0 ⑩'s five steps**: no window opens before the owner has replied,
and the owner is told to act only once the window's cell is seen running, with the action's
deadline as a time of day; no "press now" with less than 40 s to the press's deadline. ⚠️
Off-card cells are declared in `bench/2026-09-27b/CORRECTIONS-block50.md` before they run,
except those § 6 fixes now (each still logged there as it runs) and a power-off, which § 6
decides now.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-27b/ --skip S2,S3,S4 --recipe-override acf8ed3d --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/s112/r6b6/rtk/r6b6q/rlxfw/kroot/rtkload/nfjrom --image-sha256 ef5622d23738978bcce0bdce66c03c59cf86cd7320ddbbebcf58bb0f50edf6ee`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 46's, unchanged
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets /sys/class/net/eth0/statistics/tx_packets ; grep -e '^Icmp:' -e '^Udp:' /proc/net/snmp` — block 48's, with `eth0` and `Udp:` added after its own lines
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — the liveness probe: 60-B frames, clean at every setting
`PG2 <s>` = `ping -I enxfc19286184c9 -c 2 -s <s> -i 0.05 -W 1 -q 10.1.1.3`
`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done` — seating 40's, card A's
`TDE <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s113/pcap43b/<f> ether src 02:52:4c:58:46:57`
`TDT` = `timeout 900 sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or (arp and arp[6:2] = 1 and arp[18:4] = 0 and arp[22:2] = 0) or (arp and arp[6:2] = 2 and ((arp[8:4] = 0x02524c58 and arp[12:2] = 0x4657) or (arp[8:4] = 0x560a0101 and arp[12:2] = 0x01e8)))'` — card A's (its frozen card's `TDT`, byte for byte: `P2`'s text capture, block 44's filter)
`PWE <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py window /home/key/fwre-work/rebuild/s113/pcap43b/N1.pcap --if enxfc19286184c9 --prev <prev>`
`PWN <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py window /home/key/fwre-work/rebuild/s113/pcap43b/N76.pcap --if enxfc19286184c9 --prev <prev>`
`PWO` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py order`
`DMW <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py window /home/key/fwre-work/rebuild/s113/host43b/dmesg-w43b.log --prev <prev>`
`BD` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py`
`SWP` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/swpage.py`
`LPR` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/lpread.py`
`CUT` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/cutgate.py decide`
`CUTW` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/cutgate.py wait`
`CW <s>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/carrierwatch.py enxfc19286184c9 <s>`
`CARRIER` = `grep -H . /sys/class/net/enxfc19286184c9/carrier /sys/class/net/enxfc19286184c9/carrier_changes /sys/class/net/enxfc19286184c9/operstate`
`UDQ` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/udpq.py`
`RTT` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43a/rttseries.py`
`S1C` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/shared/s1class.py classify` — § 6's S1 only
`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
`IPERF5` = `timeout 340 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
`ILG` = `/usr/bin/python3 tools/iperflog.py`
`D4F <d>` = `bash /home/key/fwre-work/rebuild/s113/card43b/d4load.sh --if enxfc19286184c9 --dst 10.1.1.3 --seconds 1860 --out /home/key/fwre-work/rebuild/s113/d4-43b/<d>`
`D4S <d>` = `bash /home/key/fwre-work/rebuild/s113/card43b/d4load.sh --if enxfc19286184c9 --dst 10.1.1.3 --seconds 120 --out /home/key/fwre-work/rebuild/s113/d4-43b/<d>`
`D4C <d>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/d4cover.py /home/key/fwre-work/rebuild/s113/d4-43b/<d>`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — block 46's, unchanged

A `ping`'s `-s` is L − 42. A stimulus cell's longest silence is about 1 s and its `--idle` is
3; a server-start cell's is its `sleep 2` and its `--idle` is 4; `-Q`'s send backgrounds its
sleeps and prints nothing (`--idle 3`); every read ends on a pattern (`--until`) that also
matches the loader's banner, or on `--idle` where block 48's did, with the banner beside it
(§ 0 ⑥ (i)). `P-LW2` follows `P-LWH`, the host's wait until 605 s after `P-W`'s start (`CUTW`,
on `P-W.meta.json`, a watch holding the console): its `wait` then returns at once, or within
the margin, and it ends on `--until` its `LPW end` line with a 20-s cap (at the estimate
`P-LWH` waits about 198 s; after a restart, § 6's `X-LWH<n>` waits for the later watch first).
Every `-H` cell inside `I-N` passes `pcapwin`, and every kernel-log reader passes `dmesgwin`, a
`--prev` list (§ 6, *Chained references*).

### Before power

```
CAP --out bench/2026-09-27b/R0-PRE --seconds 3
HOST bench/2026-09-27b/R0-PREC :: ls bench/2026-09-27b/R0-PRE.log bench/2026-09-27b/R0-PRE.timing bench/2026-09-27b/R0-PRE.meta.json && cat bench/2026-09-27b/R0-PRE.meta.json
HOST bench/2026-09-27b/R0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-27b/R0-ETH :: /usr/sbin/ethtool -i enxfc19286184c9 ; uname -r ; grep -H . /sys/class/net/eth0/statistics/tx_packets
HOST bench/2026-09-27b/R0-CW :: CW 3
HOST bench/2026-09-27b/R0-TCPC :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/R0-DMSG :: pgrep -xc dmesg ; true
HOST bench/2026-09-27b/R0-DW0 :: DMW none
HOST bench/2026-09-27b/R0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-27b/R0-PCAP :: mkdir -p /home/key/fwre-work/rebuild/s113/pcap43b /home/key/fwre-work/rebuild/s113/d4-43b && find /home/key/fwre-work/rebuild/s113/pcap43b /home/key/fwre-work/rebuild/s113/d4-43b -mindepth 1 | wc -l
HOST bench/2026-09-27b/R0-IPF :: sha256sum < /home/key/fwre-work/iperf3-port/iperf3 ; ls /usr/bin/qemu-mips-static
HOST bench/2026-09-27b/R0-SUM :: sha256sum < /home/key/fwre-work/rebuild/s113/card43b/swpage.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/lpread.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/cutgate.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/carrierwatch.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/udpq.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/d4load.sh ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/d4cover.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/arith43b.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/verbcheck43b.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ; sha256sum < /home/key/fwre-work/rebuild/s113/shared/s1class.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/rttseries.py ; sha256sum < tools/iperflog.py
HOST bench/2026-09-27b/R0-ST :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/swpage.py --self-test --source /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/lpread.py --self-test --source /home/key/fwre-work/rebuild/s112/r6b6/repo/config/rlxfw-user/linkprobe/linkprobe.c ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/cutgate.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/carrierwatch.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/udpq.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/d4cover.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/shared/s1class.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43a/rttseries.py --self-test ; /usr/bin/python3 tools/iperflog.py --self-test
HOST bench/2026-09-27b/R0-VERB :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/verbcheck43b.py bench/2026-09-27b/PREDICTIONS-B52-block50.md --header /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic-tx.h --driver /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c --cell /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/verbcheck43b.py --self-test bench/2026-09-27b/PREDICTIONS-B52-block50.md --header /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic-tx.h --driver /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c --cell /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top
HOST bench/2026-09-27b/R0-H :: HN
```

### The press — the catch, the loader's `PSRP3`, the round, the opening map, `n_writes`

```
CAP --out bench/2026-09-27b/R1-CATCH --esc-after 360 --esc-period 0.002 --until '<RealTek>' --seconds 380
CAP --out bench/2026-09-27b/R1-DW --send 'DW BB804134 1' --idle 2 --seconds 6
HOST bench/2026-09-27b/R1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-27b/R1Q :: LR --cell R1Q QIMG --iterations 1
CAP --out bench/2026-09-27b/R1-PS --send 'ps' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 30
HOST bench/2026-09-27b/R1-SW7 :: grep -a -o 'RLXFW-SW7=[0-9A-F]*' bench/2026-09-27b/R1Q-boot.log ; true
CAP --out bench/2026-09-27b/R1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-27b/R1-MB0 :: MB bench/2026-09-27b/R1-M0
CAP --out bench/2026-09-27b/R1-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
```

### The opening state: rlxfw's switch page first

```
CAP --out bench/2026-09-27b/B-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27b/B-00-P :: HP
CAP --out bench/2026-09-27b/B-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/B-00-H :: HN ; DMW bench/2026-09-27b/R0-DW0.log
CAP --out bench/2026-09-27b/B-00-T --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/B-RMEM --send 'cat /proc/sys/net/core/rmem_default /proc/sys/net/core/rmem_max' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/B-SWP :: SWP page bench/2026-09-27b/B-SW.log
```

### The `ethtool` ops, with dumps around them; arm N

```
CAP --out bench/2026-09-27b/LP-SW0 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/LP-N0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/LP-G --send 'linkprobe get rlx0 lo eth4 nosuch0' --until 'LP9 calls [0-9]+ ok [0-9]+ refused [0-9]+ nowrite [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/LP-N1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/LP-SW1 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/AN-SW2 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27b/LP-LR :: LPR get bench/2026-09-27b/LP-G.log --expect rlx0,lo,eth4,nosuch0
HOST bench/2026-09-27b/LP-DS :: SWP delta bench/2026-09-27b/LP-SW0.log bench/2026-09-27b/LP-SW1.log
HOST bench/2026-09-27b/AN-D :: SWP delta bench/2026-09-27b/LP-SW1.log bench/2026-09-27b/AN-SW2.log
```

### `D3`: twelve trials at the fix, then 1.4's control, each on its own re-armed ring, then the re-arm back (each trial an invocation of its own, under a watch)

```
CAP --out bench/2026-09-27b/D3-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/D3-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/B-00-H.log
HOST bench/2026-09-27b/D3-00-P :: HP
CAP --out bench/2026-09-27b/D3-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-00-H :: HN ; DMW bench/2026-09-27b/D3-L.log
HOST bench/2026-09-27b/D3-TR1-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-00-H.log
CAP --out bench/2026-09-27b/D3-TR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tr1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-TR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
```

```
CAP --out bench/2026-09-27b/D3-TR1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tr1.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-TR1-P :: HP
CAP --out bench/2026-09-27b/D3-TR1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-TR1-H :: HN ; DMW bench/2026-09-27b/D3-TR1-L.log
HOST bench/2026-09-27b/D3-TR1-D :: BD pair bench/2026-09-27b/D3-00-R.log,bench/2026-09-27b/X-D3-00-R.log bench/2026-09-27b/D3-TR1-R.log,bench/2026-09-27b/X-D3-TR1-R.log --host bench/2026-09-27b/D3-00-H.log bench/2026-09-27b/D3-TR1-H.log --pre bench/2026-09-27b/D3-00-P.log bench/2026-09-27b/D3-TR1-P.log
HOST bench/2026-09-27b/D3-TR1-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-TR1-S1.log
HOST bench/2026-09-27b/D3-TR1-SN :: BD snmp bench/2026-09-27b/D3-TR1-S0.log bench/2026-09-27b/D3-TR1-S1.log
HOST bench/2026-09-27b/D3-TR1-IC :: ILG compare --duration 30 bench/2026-09-27b/D3-TR1-S1.log bench/2026-09-27b/D3-TR1.log
HOST bench/2026-09-27b/D3-TR2-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TR1-L.log,bench/2026-09-27b/D3-TR1-H.log
CAP --out bench/2026-09-27b/D3-TR2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tr2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-TR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
```

```
CAP --out bench/2026-09-27b/D3-TR2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tr2.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-TR2-P :: HP
CAP --out bench/2026-09-27b/D3-TR2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-TR2-H :: HN ; DMW bench/2026-09-27b/D3-TR2-L.log
HOST bench/2026-09-27b/D3-TR2-D :: BD pair bench/2026-09-27b/D3-00-R.log,bench/2026-09-27b/X-D3-00-R.log,bench/2026-09-27b/D3-TR1-R.log,bench/2026-09-27b/X-D3-TR1-R.log bench/2026-09-27b/D3-TR2-R.log,bench/2026-09-27b/X-D3-TR2-R.log --host bench/2026-09-27b/D3-00-H.log,bench/2026-09-27b/D3-TR1-H.log bench/2026-09-27b/D3-TR2-H.log --pre bench/2026-09-27b/D3-00-P.log,bench/2026-09-27b/D3-TR1-P.log bench/2026-09-27b/D3-TR2-P.log
HOST bench/2026-09-27b/D3-TR2-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-TR2-S1.log
HOST bench/2026-09-27b/D3-TR2-SN :: BD snmp bench/2026-09-27b/D3-TR2-S0.log bench/2026-09-27b/D3-TR2-S1.log
HOST bench/2026-09-27b/D3-TR2-IC :: ILG compare --duration 30 bench/2026-09-27b/D3-TR2-S1.log bench/2026-09-27b/D3-TR2.log
HOST bench/2026-09-27b/D3-TR3-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TR2-L.log,bench/2026-09-27b/D3-TR2-H.log
CAP --out bench/2026-09-27b/D3-TR3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tr3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-TR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
```

```
CAP --out bench/2026-09-27b/D3-TR3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tr3.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-TR3-P :: HP
CAP --out bench/2026-09-27b/D3-TR3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-TR3-H :: HN ; DMW bench/2026-09-27b/D3-TR3-L.log
HOST bench/2026-09-27b/D3-TR3-D :: BD pair bench/2026-09-27b/D3-TR1-R.log,bench/2026-09-27b/X-D3-TR1-R.log,bench/2026-09-27b/D3-TR2-R.log,bench/2026-09-27b/X-D3-TR2-R.log bench/2026-09-27b/D3-TR3-R.log,bench/2026-09-27b/X-D3-TR3-R.log --host bench/2026-09-27b/D3-TR1-H.log,bench/2026-09-27b/D3-TR2-H.log bench/2026-09-27b/D3-TR3-H.log --pre bench/2026-09-27b/D3-TR1-P.log,bench/2026-09-27b/D3-TR2-P.log bench/2026-09-27b/D3-TR3-P.log
HOST bench/2026-09-27b/D3-TR3-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-TR3-S1.log
HOST bench/2026-09-27b/D3-TR3-SN :: BD snmp bench/2026-09-27b/D3-TR3-S0.log bench/2026-09-27b/D3-TR3-S1.log
HOST bench/2026-09-27b/D3-TR3-IC :: ILG compare --duration 30 bench/2026-09-27b/D3-TR3-S1.log bench/2026-09-27b/D3-TR3.log
HOST bench/2026-09-27b/D3-TS1-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TR3-L.log,bench/2026-09-27b/D3-TR3-H.log
CAP --out bench/2026-09-27b/D3-TS1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ts1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-TS1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
```

```
CAP --out bench/2026-09-27b/D3-TS1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ts1.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-TS1-P :: HP
CAP --out bench/2026-09-27b/D3-TS1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-TS1-H :: HN ; DMW bench/2026-09-27b/D3-TS1-L.log
HOST bench/2026-09-27b/D3-TS1-D :: BD pair bench/2026-09-27b/D3-TR2-R.log,bench/2026-09-27b/X-D3-TR2-R.log,bench/2026-09-27b/D3-TR3-R.log,bench/2026-09-27b/X-D3-TR3-R.log bench/2026-09-27b/D3-TS1-R.log,bench/2026-09-27b/X-D3-TS1-R.log --host bench/2026-09-27b/D3-TR2-H.log,bench/2026-09-27b/D3-TR3-H.log bench/2026-09-27b/D3-TS1-H.log --pre bench/2026-09-27b/D3-TR2-P.log,bench/2026-09-27b/D3-TR3-P.log bench/2026-09-27b/D3-TS1-P.log
HOST bench/2026-09-27b/D3-TS1-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-TS1-S1.log
HOST bench/2026-09-27b/D3-TS1-SN :: BD snmp bench/2026-09-27b/D3-TS1-S0.log bench/2026-09-27b/D3-TS1-S1.log
HOST bench/2026-09-27b/D3-TS2-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TS1-L.log,bench/2026-09-27b/D3-TS1-H.log
CAP --out bench/2026-09-27b/D3-TS2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ts2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-TS2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
```

```
CAP --out bench/2026-09-27b/D3-TS2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ts2.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-TS2-P :: HP
CAP --out bench/2026-09-27b/D3-TS2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-TS2-H :: HN ; DMW bench/2026-09-27b/D3-TS2-L.log
HOST bench/2026-09-27b/D3-TS2-D :: BD pair bench/2026-09-27b/D3-TR3-R.log,bench/2026-09-27b/X-D3-TR3-R.log,bench/2026-09-27b/D3-TS1-R.log,bench/2026-09-27b/X-D3-TS1-R.log bench/2026-09-27b/D3-TS2-R.log,bench/2026-09-27b/X-D3-TS2-R.log --host bench/2026-09-27b/D3-TR3-H.log,bench/2026-09-27b/D3-TS1-H.log bench/2026-09-27b/D3-TS2-H.log --pre bench/2026-09-27b/D3-TR3-P.log,bench/2026-09-27b/D3-TS1-P.log bench/2026-09-27b/D3-TS2-P.log
HOST bench/2026-09-27b/D3-TS2-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-TS2-S1.log
HOST bench/2026-09-27b/D3-TS2-SN :: BD snmp bench/2026-09-27b/D3-TS2-S0.log bench/2026-09-27b/D3-TS2-S1.log
HOST bench/2026-09-27b/D3-TS3-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TS2-L.log,bench/2026-09-27b/D3-TS2-H.log
CAP --out bench/2026-09-27b/D3-TS3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ts3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-TS3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
```

```
CAP --out bench/2026-09-27b/D3-TS3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ts3.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-TS3-P :: HP
CAP --out bench/2026-09-27b/D3-TS3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-TS3-H :: HN ; DMW bench/2026-09-27b/D3-TS3-L.log
HOST bench/2026-09-27b/D3-TS3-D :: BD pair bench/2026-09-27b/D3-TS1-R.log,bench/2026-09-27b/X-D3-TS1-R.log,bench/2026-09-27b/D3-TS2-R.log,bench/2026-09-27b/X-D3-TS2-R.log bench/2026-09-27b/D3-TS3-R.log,bench/2026-09-27b/X-D3-TS3-R.log --host bench/2026-09-27b/D3-TS1-H.log,bench/2026-09-27b/D3-TS2-H.log bench/2026-09-27b/D3-TS3-H.log --pre bench/2026-09-27b/D3-TS1-P.log,bench/2026-09-27b/D3-TS2-P.log bench/2026-09-27b/D3-TS3-P.log
HOST bench/2026-09-27b/D3-TS3-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-TS3-S1.log
HOST bench/2026-09-27b/D3-TS3-SN :: BD snmp bench/2026-09-27b/D3-TS3-S0.log bench/2026-09-27b/D3-TS3-S1.log
HOST bench/2026-09-27b/D3-UR1-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TS3-L.log,bench/2026-09-27b/D3-TS3-H.log
CAP --out bench/2026-09-27b/D3-UR1-Q --send 'cd /tmp && sleep 20 && busybox cp /proc/net/udp ur1a && sleep 12 && busybox cp /proc/net/udp ur1b &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-UR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ur1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-UR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
```

```
CAP --out bench/2026-09-27b/D3-UR1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ur1.log /tmp/ur1a /tmp/ur1b' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-UR1-P :: HP
CAP --out bench/2026-09-27b/D3-UR1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-UR1-H :: HN ; DMW bench/2026-09-27b/D3-UR1-L.log
HOST bench/2026-09-27b/D3-UR1-D :: BD pair bench/2026-09-27b/D3-TS2-R.log,bench/2026-09-27b/X-D3-TS2-R.log,bench/2026-09-27b/D3-TS3-R.log,bench/2026-09-27b/X-D3-TS3-R.log bench/2026-09-27b/D3-UR1-R.log,bench/2026-09-27b/X-D3-UR1-R.log --host bench/2026-09-27b/D3-TS2-H.log,bench/2026-09-27b/D3-TS3-H.log bench/2026-09-27b/D3-UR1-H.log --pre bench/2026-09-27b/D3-TS2-P.log,bench/2026-09-27b/D3-TS3-P.log bench/2026-09-27b/D3-UR1-P.log
HOST bench/2026-09-27b/D3-UR1-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-UR1-S1.log
HOST bench/2026-09-27b/D3-UR1-SN :: BD snmp bench/2026-09-27b/D3-UR1-S0.log bench/2026-09-27b/D3-UR1-S1.log
HOST bench/2026-09-27b/D3-UR1-IC :: ILG compare --duration 30 bench/2026-09-27b/D3-UR1-S1.log bench/2026-09-27b/D3-UR1.log
HOST bench/2026-09-27b/D3-UR1-UQ :: UDQ read bench/2026-09-27b/D3-UR1-S1.log --rmem bench/2026-09-27b/B-RMEM.log
HOST bench/2026-09-27b/D3-UR2-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-UR1-L.log,bench/2026-09-27b/D3-UR1-H.log
CAP --out bench/2026-09-27b/D3-UR2-Q --send 'cd /tmp && sleep 20 && busybox cp /proc/net/udp ur2a && sleep 12 && busybox cp /proc/net/udp ur2b &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-UR2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ur2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-UR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
```

```
CAP --out bench/2026-09-27b/D3-UR2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ur2.log /tmp/ur2a /tmp/ur2b' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-UR2-P :: HP
CAP --out bench/2026-09-27b/D3-UR2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-UR2-H :: HN ; DMW bench/2026-09-27b/D3-UR2-L.log
HOST bench/2026-09-27b/D3-UR2-D :: BD pair bench/2026-09-27b/D3-TS3-R.log,bench/2026-09-27b/X-D3-TS3-R.log,bench/2026-09-27b/D3-UR1-R.log,bench/2026-09-27b/X-D3-UR1-R.log bench/2026-09-27b/D3-UR2-R.log,bench/2026-09-27b/X-D3-UR2-R.log --host bench/2026-09-27b/D3-TS3-H.log,bench/2026-09-27b/D3-UR1-H.log bench/2026-09-27b/D3-UR2-H.log --pre bench/2026-09-27b/D3-TS3-P.log,bench/2026-09-27b/D3-UR1-P.log bench/2026-09-27b/D3-UR2-P.log
HOST bench/2026-09-27b/D3-UR2-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-UR2-S1.log
HOST bench/2026-09-27b/D3-UR2-SN :: BD snmp bench/2026-09-27b/D3-UR2-S0.log bench/2026-09-27b/D3-UR2-S1.log
HOST bench/2026-09-27b/D3-UR2-IC :: ILG compare --duration 30 bench/2026-09-27b/D3-UR2-S1.log bench/2026-09-27b/D3-UR2.log
HOST bench/2026-09-27b/D3-UR2-UQ :: UDQ read bench/2026-09-27b/D3-UR2-S1.log --rmem bench/2026-09-27b/B-RMEM.log
HOST bench/2026-09-27b/D3-UR3-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-UR2-L.log,bench/2026-09-27b/D3-UR2-H.log
CAP --out bench/2026-09-27b/D3-UR3-Q --send 'cd /tmp && sleep 20 && busybox cp /proc/net/udp ur3a && sleep 12 && busybox cp /proc/net/udp ur3b &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-UR3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ur3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-UR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
```

```
CAP --out bench/2026-09-27b/D3-UR3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ur3.log /tmp/ur3a /tmp/ur3b' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-UR3-P :: HP
CAP --out bench/2026-09-27b/D3-UR3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-UR3-H :: HN ; DMW bench/2026-09-27b/D3-UR3-L.log
HOST bench/2026-09-27b/D3-UR3-D :: BD pair bench/2026-09-27b/D3-UR1-R.log,bench/2026-09-27b/X-D3-UR1-R.log,bench/2026-09-27b/D3-UR2-R.log,bench/2026-09-27b/X-D3-UR2-R.log bench/2026-09-27b/D3-UR3-R.log,bench/2026-09-27b/X-D3-UR3-R.log --host bench/2026-09-27b/D3-UR1-H.log,bench/2026-09-27b/D3-UR2-H.log bench/2026-09-27b/D3-UR3-H.log --pre bench/2026-09-27b/D3-UR1-P.log,bench/2026-09-27b/D3-UR2-P.log bench/2026-09-27b/D3-UR3-P.log
HOST bench/2026-09-27b/D3-UR3-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-UR3-S1.log
HOST bench/2026-09-27b/D3-UR3-SN :: BD snmp bench/2026-09-27b/D3-UR3-S0.log bench/2026-09-27b/D3-UR3-S1.log
HOST bench/2026-09-27b/D3-UR3-IC :: ILG compare --duration 30 bench/2026-09-27b/D3-UR3-S1.log bench/2026-09-27b/D3-UR3.log
HOST bench/2026-09-27b/D3-UR3-UQ :: UDQ read bench/2026-09-27b/D3-UR3-S1.log --rmem bench/2026-09-27b/B-RMEM.log
HOST bench/2026-09-27b/D3-US1-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-UR3-L.log,bench/2026-09-27b/D3-UR3-H.log
CAP --out bench/2026-09-27b/D3-US1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/us1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-US1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
```

```
CAP --out bench/2026-09-27b/D3-US1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/us1.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-US1-P :: HP
CAP --out bench/2026-09-27b/D3-US1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-US1-H :: HN ; DMW bench/2026-09-27b/D3-US1-L.log
HOST bench/2026-09-27b/D3-US1-D :: BD pair bench/2026-09-27b/D3-UR2-R.log,bench/2026-09-27b/X-D3-UR2-R.log,bench/2026-09-27b/D3-UR3-R.log,bench/2026-09-27b/X-D3-UR3-R.log bench/2026-09-27b/D3-US1-R.log,bench/2026-09-27b/X-D3-US1-R.log --host bench/2026-09-27b/D3-UR2-H.log,bench/2026-09-27b/D3-UR3-H.log bench/2026-09-27b/D3-US1-H.log --pre bench/2026-09-27b/D3-UR2-P.log,bench/2026-09-27b/D3-UR3-P.log bench/2026-09-27b/D3-US1-P.log
HOST bench/2026-09-27b/D3-US1-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-US1-S1.log
HOST bench/2026-09-27b/D3-US1-SN :: BD snmp bench/2026-09-27b/D3-US1-S0.log bench/2026-09-27b/D3-US1-S1.log
HOST bench/2026-09-27b/D3-US2-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-US1-L.log,bench/2026-09-27b/D3-US1-H.log
CAP --out bench/2026-09-27b/D3-US2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/us2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-US2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
```

```
CAP --out bench/2026-09-27b/D3-US2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/us2.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-US2-P :: HP
CAP --out bench/2026-09-27b/D3-US2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-US2-H :: HN ; DMW bench/2026-09-27b/D3-US2-L.log
HOST bench/2026-09-27b/D3-US2-D :: BD pair bench/2026-09-27b/D3-UR3-R.log,bench/2026-09-27b/X-D3-UR3-R.log,bench/2026-09-27b/D3-US1-R.log,bench/2026-09-27b/X-D3-US1-R.log bench/2026-09-27b/D3-US2-R.log,bench/2026-09-27b/X-D3-US2-R.log --host bench/2026-09-27b/D3-UR3-H.log,bench/2026-09-27b/D3-US1-H.log bench/2026-09-27b/D3-US2-H.log --pre bench/2026-09-27b/D3-UR3-P.log,bench/2026-09-27b/D3-US1-P.log bench/2026-09-27b/D3-US2-P.log
HOST bench/2026-09-27b/D3-US2-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-US2-S1.log
HOST bench/2026-09-27b/D3-US2-SN :: BD snmp bench/2026-09-27b/D3-US2-S0.log bench/2026-09-27b/D3-US2-S1.log
HOST bench/2026-09-27b/D3-US3-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-US2-L.log,bench/2026-09-27b/D3-US2-H.log
CAP --out bench/2026-09-27b/D3-US3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/us3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-US3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
```

```
CAP --out bench/2026-09-27b/D3-US3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/us3.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-US3-P :: HP
CAP --out bench/2026-09-27b/D3-US3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-US3-H :: HN ; DMW bench/2026-09-27b/D3-US3-L.log
HOST bench/2026-09-27b/D3-US3-D :: BD pair bench/2026-09-27b/D3-US1-R.log,bench/2026-09-27b/X-D3-US1-R.log,bench/2026-09-27b/D3-US2-R.log,bench/2026-09-27b/X-D3-US2-R.log bench/2026-09-27b/D3-US3-R.log,bench/2026-09-27b/X-D3-US3-R.log --host bench/2026-09-27b/D3-US1-H.log,bench/2026-09-27b/D3-US2-H.log bench/2026-09-27b/D3-US3-H.log --pre bench/2026-09-27b/D3-US1-P.log,bench/2026-09-27b/D3-US2-P.log bench/2026-09-27b/D3-US3-P.log
HOST bench/2026-09-27b/D3-US3-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-US3-S1.log
HOST bench/2026-09-27b/D3-US3-SN :: BD snmp bench/2026-09-27b/D3-US3-S0.log bench/2026-09-27b/D3-US3-S1.log
CAP --out bench/2026-09-27b/D3-X-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-X-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/D3-X-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-L.log,bench/2026-09-27b/D3-US3-L.log,bench/2026-09-27b/D3-US3-H.log
HOST bench/2026-09-27b/D3-X-00-P :: HP
CAP --out bench/2026-09-27b/D3-X-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-X-00-H :: HN ; DMW bench/2026-09-27b/D3-X-L.log
HOST bench/2026-09-27b/D3-LUR1-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-X-00-H.log
CAP --out bench/2026-09-27b/D3-LUR1-Q --send 'cd /tmp && sleep 20 && busybox cp /proc/net/udp lur1a && sleep 12 && busybox cp /proc/net/udp lur1b &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-LUR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/lur1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-LUR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
```

```
CAP --out bench/2026-09-27b/D3-LUR1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/lur1.log /tmp/lur1a /tmp/lur1b' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-LUR1-P :: HP
CAP --out bench/2026-09-27b/D3-LUR1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-LUR1-H :: HN ; DMW bench/2026-09-27b/D3-LUR1-L.log
HOST bench/2026-09-27b/D3-LUR1-D :: BD pair bench/2026-09-27b/D3-X-00-R.log,bench/2026-09-27b/X-D3-X-00-R.log bench/2026-09-27b/D3-LUR1-R.log,bench/2026-09-27b/X-D3-LUR1-R.log --host bench/2026-09-27b/D3-X-00-H.log bench/2026-09-27b/D3-LUR1-H.log --pre bench/2026-09-27b/D3-X-00-P.log bench/2026-09-27b/D3-LUR1-P.log
HOST bench/2026-09-27b/D3-LUR1-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-LUR1-S1.log
HOST bench/2026-09-27b/D3-LUR1-SN :: BD snmp bench/2026-09-27b/D3-LUR1-S0.log bench/2026-09-27b/D3-LUR1-S1.log
HOST bench/2026-09-27b/D3-LUR1-UQ :: UDQ read bench/2026-09-27b/D3-LUR1-S1.log --rmem bench/2026-09-27b/B-RMEM.log
CAP --out bench/2026-09-27b/D3-Y-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-Y-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/D3-Y-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-X-L.log,bench/2026-09-27b/D3-LUR1-L.log,bench/2026-09-27b/D3-LUR1-H.log
HOST bench/2026-09-27b/D3-Y-00-P :: HP
CAP --out bench/2026-09-27b/D3-Y-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-Y-00-H :: HN ; DMW bench/2026-09-27b/D3-Y-L.log
HOST bench/2026-09-27b/D3-LUS1-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-Y-00-H.log
CAP --out bench/2026-09-27b/D3-LUS1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/lus1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/D3-LUS1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
```

```
CAP --out bench/2026-09-27b/D3-LUS1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/lus1.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/D3-LUS1-P :: HP
CAP --out bench/2026-09-27b/D3-LUS1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/D3-LUS1-H :: HN ; DMW bench/2026-09-27b/D3-LUS1-L.log
HOST bench/2026-09-27b/D3-LUS1-D :: BD pair bench/2026-09-27b/D3-Y-00-R.log,bench/2026-09-27b/X-D3-Y-00-R.log bench/2026-09-27b/D3-LUS1-R.log,bench/2026-09-27b/X-D3-LUS1-R.log --host bench/2026-09-27b/D3-Y-00-H.log bench/2026-09-27b/D3-LUS1-H.log --pre bench/2026-09-27b/D3-Y-00-P.log bench/2026-09-27b/D3-LUS1-P.log
HOST bench/2026-09-27b/D3-LUS1-IL :: ILG parse --duration 30 bench/2026-09-27b/D3-LUS1-S1.log
HOST bench/2026-09-27b/D3-LUS1-SN :: BD snmp bench/2026-09-27b/D3-LUS1-S0.log bench/2026-09-27b/D3-LUS1-S1.log
CAP --out bench/2026-09-27b/D3-Z-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/D3-Z-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/D3-SUM :: grep -c '^iperf Done[.]$' bench/2026-09-27b/D3-TR1.log bench/2026-09-27b/D3-TR2.log bench/2026-09-27b/D3-TR3.log bench/2026-09-27b/D3-TS1.log bench/2026-09-27b/D3-TS2.log bench/2026-09-27b/D3-TS3.log bench/2026-09-27b/D3-UR1.log bench/2026-09-27b/D3-UR2.log bench/2026-09-27b/D3-UR3.log bench/2026-09-27b/D3-US1.log bench/2026-09-27b/D3-US2.log bench/2026-09-27b/D3-US3.log bench/2026-09-27b/D3-LUR1.log bench/2026-09-27b/D3-LUS1.log ; grep -c 'No route to host' bench/2026-09-27b/D3-TR1.log bench/2026-09-27b/D3-TR2.log bench/2026-09-27b/D3-TR3.log bench/2026-09-27b/D3-TS1.log bench/2026-09-27b/D3-TS2.log bench/2026-09-27b/D3-TS3.log bench/2026-09-27b/D3-UR1.log bench/2026-09-27b/D3-UR2.log bench/2026-09-27b/D3-UR3.log bench/2026-09-27b/D3-US1.log bench/2026-09-27b/D3-US2.log bench/2026-09-27b/D3-US3.log bench/2026-09-27b/D3-LUR1.log bench/2026-09-27b/D3-LUS1.log ; true
```

### `NET-131`: the cut point, the capture, six two-request brackets, the capture stopped

```
HOST bench/2026-09-27b/CUT-N :: CUT --catch bench/2026-09-27b/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 19
```

```
HOST& bench/2026-09-27b/W-TCPN :: TDE N1.pcap
```

```
HOST bench/2026-09-27b/N-LIVE :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/K1-0061-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-TR2-L.log,bench/2026-09-27b/D3-TR3-L.log,bench/2026-09-27b/D3-TS1-L.log,bench/2026-09-27b/D3-TS2-L.log,bench/2026-09-27b/D3-TS3-L.log,bench/2026-09-27b/D3-UR1-L.log,bench/2026-09-27b/D3-UR2-L.log,bench/2026-09-27b/D3-UR3-L.log,bench/2026-09-27b/D3-US1-L.log,bench/2026-09-27b/D3-US2-L.log,bench/2026-09-27b/D3-US3-L.log,bench/2026-09-27b/D3-LUR1-L.log,bench/2026-09-27b/D3-Y-L.log,bench/2026-09-27b/D3-LUS1-L.log,bench/2026-09-27b/D3-LUS1-H.log
CAP --out bench/2026-09-27b/K1-0061-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/K1-0061-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K1-0061-P0 :: HP
CAP --out bench/2026-09-27b/K1-0061-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K1-0061-H0 :: HN ; PWE none ; DMW bench/2026-09-27b/K1-0061-L.log
HOST bench/2026-09-27b/K1-0061-PG :: PG2 19
HOST bench/2026-09-27b/K1-0061-P1 :: HP
CAP --out bench/2026-09-27b/K1-0061-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K1-0061-H1 :: HN ; PWE bench/2026-09-27b/K1-0061-H0.log ; DMW bench/2026-09-27b/K1-0061-H0.log
HOST bench/2026-09-27b/K1-0061-D :: BD pair bench/2026-09-27b/K1-0061-R0.log,bench/2026-09-27b/X-K1-0061-R0.log bench/2026-09-27b/K1-0061-R1.log,bench/2026-09-27b/X-K1-0061-R1.log --host bench/2026-09-27b/K1-0061-H0.log bench/2026-09-27b/K1-0061-H1.log --pre bench/2026-09-27b/K1-0061-P0.log bench/2026-09-27b/K1-0061-P1.log
CAP --out bench/2026-09-27b/K1-0061-E --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K2-0062-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/K1-0061-L.log,bench/2026-09-27b/K1-0061-H1.log
CAP --out bench/2026-09-27b/K2-0062-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/K2-0062-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K2-0062-P0 :: HP
CAP --out bench/2026-09-27b/K2-0062-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K2-0062-H0 :: HN ; PWE none,bench/2026-09-27b/K1-0061-H1.log ; DMW bench/2026-09-27b/K2-0062-L.log
HOST bench/2026-09-27b/K2-0062-PG :: PG2 20
HOST bench/2026-09-27b/K2-0062-P1 :: HP
CAP --out bench/2026-09-27b/K2-0062-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K2-0062-H1 :: HN ; PWE bench/2026-09-27b/K2-0062-H0.log ; DMW bench/2026-09-27b/K2-0062-H0.log
HOST bench/2026-09-27b/K2-0062-D :: BD pair bench/2026-09-27b/K2-0062-R0.log,bench/2026-09-27b/X-K2-0062-R0.log bench/2026-09-27b/K2-0062-R1.log,bench/2026-09-27b/X-K2-0062-R1.log --host bench/2026-09-27b/K2-0062-H0.log bench/2026-09-27b/K2-0062-H1.log --pre bench/2026-09-27b/K2-0062-P0.log bench/2026-09-27b/K2-0062-P1.log
CAP --out bench/2026-09-27b/K2-0062-E --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K3-0063-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/K2-0062-L.log,bench/2026-09-27b/K2-0062-H1.log
CAP --out bench/2026-09-27b/K3-0063-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/K3-0063-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K3-0063-P0 :: HP
CAP --out bench/2026-09-27b/K3-0063-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K3-0063-H0 :: HN ; PWE bench/2026-09-27b/K1-0061-H1.log,bench/2026-09-27b/K2-0062-H1.log ; DMW bench/2026-09-27b/K3-0063-L.log
HOST bench/2026-09-27b/K3-0063-PG :: PG2 21
HOST bench/2026-09-27b/K3-0063-P1 :: HP
CAP --out bench/2026-09-27b/K3-0063-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K3-0063-H1 :: HN ; PWE bench/2026-09-27b/K3-0063-H0.log ; DMW bench/2026-09-27b/K3-0063-H0.log
HOST bench/2026-09-27b/K3-0063-D :: BD pair bench/2026-09-27b/K3-0063-R0.log,bench/2026-09-27b/X-K3-0063-R0.log bench/2026-09-27b/K3-0063-R1.log,bench/2026-09-27b/X-K3-0063-R1.log --host bench/2026-09-27b/K3-0063-H0.log bench/2026-09-27b/K3-0063-H1.log --pre bench/2026-09-27b/K3-0063-P0.log bench/2026-09-27b/K3-0063-P1.log
CAP --out bench/2026-09-27b/K3-0063-E --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K4-0061-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/K3-0063-L.log,bench/2026-09-27b/K3-0063-H1.log
CAP --out bench/2026-09-27b/K4-0061-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/K4-0061-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K4-0061-P0 :: HP
CAP --out bench/2026-09-27b/K4-0061-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K4-0061-H0 :: HN ; PWE bench/2026-09-27b/K2-0062-H1.log,bench/2026-09-27b/K3-0063-H1.log ; DMW bench/2026-09-27b/K4-0061-L.log
HOST bench/2026-09-27b/K4-0061-PG :: PG2 19
HOST bench/2026-09-27b/K4-0061-P1 :: HP
CAP --out bench/2026-09-27b/K4-0061-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K4-0061-H1 :: HN ; PWE bench/2026-09-27b/K4-0061-H0.log ; DMW bench/2026-09-27b/K4-0061-H0.log
HOST bench/2026-09-27b/K4-0061-D :: BD pair bench/2026-09-27b/K4-0061-R0.log,bench/2026-09-27b/X-K4-0061-R0.log bench/2026-09-27b/K4-0061-R1.log,bench/2026-09-27b/X-K4-0061-R1.log --host bench/2026-09-27b/K4-0061-H0.log bench/2026-09-27b/K4-0061-H1.log --pre bench/2026-09-27b/K4-0061-P0.log bench/2026-09-27b/K4-0061-P1.log
CAP --out bench/2026-09-27b/K4-0061-E --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K5-0062-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/K4-0061-L.log,bench/2026-09-27b/K4-0061-H1.log
CAP --out bench/2026-09-27b/K5-0062-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/K5-0062-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K5-0062-P0 :: HP
CAP --out bench/2026-09-27b/K5-0062-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K5-0062-H0 :: HN ; PWE bench/2026-09-27b/K3-0063-H1.log,bench/2026-09-27b/K4-0061-H1.log ; DMW bench/2026-09-27b/K5-0062-L.log
HOST bench/2026-09-27b/K5-0062-PG :: PG2 20
HOST bench/2026-09-27b/K5-0062-P1 :: HP
CAP --out bench/2026-09-27b/K5-0062-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K5-0062-H1 :: HN ; PWE bench/2026-09-27b/K5-0062-H0.log ; DMW bench/2026-09-27b/K5-0062-H0.log
HOST bench/2026-09-27b/K5-0062-D :: BD pair bench/2026-09-27b/K5-0062-R0.log,bench/2026-09-27b/X-K5-0062-R0.log bench/2026-09-27b/K5-0062-R1.log,bench/2026-09-27b/X-K5-0062-R1.log --host bench/2026-09-27b/K5-0062-H0.log bench/2026-09-27b/K5-0062-H1.log --pre bench/2026-09-27b/K5-0062-P0.log bench/2026-09-27b/K5-0062-P1.log
CAP --out bench/2026-09-27b/K5-0062-E --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K6-0063-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/K5-0062-L.log,bench/2026-09-27b/K5-0062-H1.log
CAP --out bench/2026-09-27b/K6-0063-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/K6-0063-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/K6-0063-P0 :: HP
CAP --out bench/2026-09-27b/K6-0063-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K6-0063-H0 :: HN ; PWE bench/2026-09-27b/K4-0061-H1.log,bench/2026-09-27b/K5-0062-H1.log ; DMW bench/2026-09-27b/K6-0063-L.log
HOST bench/2026-09-27b/K6-0063-PG :: PG2 21
HOST bench/2026-09-27b/K6-0063-P1 :: HP
CAP --out bench/2026-09-27b/K6-0063-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/K6-0063-H1 :: HN ; PWE bench/2026-09-27b/K6-0063-H0.log ; DMW bench/2026-09-27b/K6-0063-H0.log
HOST bench/2026-09-27b/K6-0063-D :: BD pair bench/2026-09-27b/K6-0063-R0.log,bench/2026-09-27b/X-K6-0063-R0.log bench/2026-09-27b/K6-0063-R1.log,bench/2026-09-27b/X-K6-0063-R1.log --host bench/2026-09-27b/K6-0063-H0.log bench/2026-09-27b/K6-0063-H1.log --pre bench/2026-09-27b/K6-0063-P0.log bench/2026-09-27b/K6-0063-P1.log
CAP --out bench/2026-09-27b/K6-0063-E --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
```

```
HOST bench/2026-09-27b/W-TCPNX :: HN ; sudo -n pkill -INT -x tcpdump && sleep 1 ; HN
HOST bench/2026-09-27b/W-NWALL :: PWE none
HOST bench/2026-09-27b/W-NORD :: PWO /home/key/fwre-work/rebuild/s113/pcap43b/N1.pcap --if enxfc19286184c9 --tcpdump bench/2026-09-27b/W-TCPN.log --stop bench/2026-09-27b/W-TCPNX.log bench/2026-09-27b/K1-0061-P0.log bench/2026-09-27b/K1-0061-H0.log bench/2026-09-27b/K1-0061-P1.log bench/2026-09-27b/K1-0061-H1.log bench/2026-09-27b/K2-0062-P0.log bench/2026-09-27b/K2-0062-H0.log bench/2026-09-27b/K2-0062-P1.log bench/2026-09-27b/K2-0062-H1.log bench/2026-09-27b/K3-0063-P0.log bench/2026-09-27b/K3-0063-H0.log bench/2026-09-27b/K3-0063-P1.log bench/2026-09-27b/K3-0063-H1.log bench/2026-09-27b/K4-0061-P0.log bench/2026-09-27b/K4-0061-H0.log bench/2026-09-27b/K4-0061-P1.log bench/2026-09-27b/K4-0061-H1.log bench/2026-09-27b/K5-0062-P0.log bench/2026-09-27b/K5-0062-H0.log bench/2026-09-27b/K5-0062-P1.log bench/2026-09-27b/K5-0062-H1.log bench/2026-09-27b/K6-0063-P0.log bench/2026-09-27b/K6-0063-H0.log bench/2026-09-27b/K6-0063-P1.log bench/2026-09-27b/K6-0063-H1.log
```

### `D3-MISS` ② at the fix

```
HOST bench/2026-09-27b/CUT-M :: CUT --catch bench/2026-09-27b/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 15
```

```
CAP --out bench/2026-09-27b/M2F-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/M2F-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/M2F-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/D3-Y-L.log,bench/2026-09-27b/D3-LUS1-L.log,bench/2026-09-27b/D3-LUS1-H.log,bench/2026-09-27b/K6-0063-L.log,bench/2026-09-27b/K6-0063-H1.log
HOST bench/2026-09-27b/M2F-00-P :: HP
CAP --out bench/2026-09-27b/M2F-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-00-H :: HN ; DMW bench/2026-09-27b/M2F-L.log
HOST bench/2026-09-27b/M2F-S01-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-00-H.log
HOST bench/2026-09-27b/M2F-S01-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S01 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S01-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S01-P :: HP
CAP --out bench/2026-09-27b/M2F-S01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S01-H :: HN ; DMW bench/2026-09-27b/M2F-S01-L.log
HOST bench/2026-09-27b/M2F-S01-D :: BD pair bench/2026-09-27b/M2F-00-R.log,bench/2026-09-27b/X-M2F-00-R.log bench/2026-09-27b/M2F-S01-R.log,bench/2026-09-27b/X-M2F-S01-R.log --host bench/2026-09-27b/M2F-00-H.log bench/2026-09-27b/M2F-S01-H.log --pre bench/2026-09-27b/M2F-00-P.log bench/2026-09-27b/M2F-S01-P.log
HOST bench/2026-09-27b/M2F-S02-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S01-H.log
HOST& bench/2026-09-27b/M2F-S02-T :: TDT
HOST bench/2026-09-27b/M2F-S02-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S02 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S02-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S02-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S02-P :: HP
CAP --out bench/2026-09-27b/M2F-S02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S02-H :: HN ; DMW bench/2026-09-27b/M2F-S02-L.log
HOST bench/2026-09-27b/M2F-S02-D :: BD pair bench/2026-09-27b/M2F-S01-R.log,bench/2026-09-27b/X-M2F-S01-R.log bench/2026-09-27b/M2F-S02-R.log,bench/2026-09-27b/X-M2F-S02-R.log --host bench/2026-09-27b/M2F-S01-H.log bench/2026-09-27b/M2F-S02-H.log --pre bench/2026-09-27b/M2F-S01-P.log bench/2026-09-27b/M2F-S02-P.log
HOST bench/2026-09-27b/M2F-S03-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S02-H.log
HOST& bench/2026-09-27b/M2F-S03-T :: TDT
HOST bench/2026-09-27b/M2F-S03-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S03 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S03-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S03-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S03-P :: HP
CAP --out bench/2026-09-27b/M2F-S03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S03-H :: HN ; DMW bench/2026-09-27b/M2F-S03-L.log
HOST bench/2026-09-27b/M2F-S03-D :: BD pair bench/2026-09-27b/M2F-S02-R.log,bench/2026-09-27b/X-M2F-S02-R.log bench/2026-09-27b/M2F-S03-R.log,bench/2026-09-27b/X-M2F-S03-R.log --host bench/2026-09-27b/M2F-S02-H.log bench/2026-09-27b/M2F-S03-H.log --pre bench/2026-09-27b/M2F-S02-P.log bench/2026-09-27b/M2F-S03-P.log
HOST bench/2026-09-27b/M2F-S04-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S03-H.log
HOST bench/2026-09-27b/M2F-S04-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S04 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S04-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S04-P :: HP
CAP --out bench/2026-09-27b/M2F-S04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S04-H :: HN ; DMW bench/2026-09-27b/M2F-S04-L.log
HOST bench/2026-09-27b/M2F-S04-D :: BD pair bench/2026-09-27b/M2F-S03-R.log,bench/2026-09-27b/X-M2F-S03-R.log bench/2026-09-27b/M2F-S04-R.log,bench/2026-09-27b/X-M2F-S04-R.log --host bench/2026-09-27b/M2F-S03-H.log bench/2026-09-27b/M2F-S04-H.log --pre bench/2026-09-27b/M2F-S03-P.log bench/2026-09-27b/M2F-S04-P.log
HOST bench/2026-09-27b/M2F-S05-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S04-H.log
HOST bench/2026-09-27b/M2F-S05-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S05 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S05-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S05-P :: HP
CAP --out bench/2026-09-27b/M2F-S05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S05-H :: HN ; DMW bench/2026-09-27b/M2F-S05-L.log
HOST bench/2026-09-27b/M2F-S05-D :: BD pair bench/2026-09-27b/M2F-S04-R.log,bench/2026-09-27b/X-M2F-S04-R.log bench/2026-09-27b/M2F-S05-R.log,bench/2026-09-27b/X-M2F-S05-R.log --host bench/2026-09-27b/M2F-S04-H.log bench/2026-09-27b/M2F-S05-H.log --pre bench/2026-09-27b/M2F-S04-P.log bench/2026-09-27b/M2F-S05-P.log
HOST bench/2026-09-27b/M2F-S06-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S05-H.log
HOST& bench/2026-09-27b/M2F-S06-T :: TDT
HOST bench/2026-09-27b/M2F-S06-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S06 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S06-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S06-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S06-P :: HP
CAP --out bench/2026-09-27b/M2F-S06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S06-H :: HN ; DMW bench/2026-09-27b/M2F-S06-L.log
HOST bench/2026-09-27b/M2F-S06-D :: BD pair bench/2026-09-27b/M2F-S05-R.log,bench/2026-09-27b/X-M2F-S05-R.log bench/2026-09-27b/M2F-S06-R.log,bench/2026-09-27b/X-M2F-S06-R.log --host bench/2026-09-27b/M2F-S05-H.log bench/2026-09-27b/M2F-S06-H.log --pre bench/2026-09-27b/M2F-S05-P.log bench/2026-09-27b/M2F-S06-P.log
HOST bench/2026-09-27b/M2F-S07-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S06-H.log
HOST& bench/2026-09-27b/M2F-S07-T :: TDT
HOST bench/2026-09-27b/M2F-S07-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S07 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S07-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S07-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S07-P :: HP
CAP --out bench/2026-09-27b/M2F-S07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S07-H :: HN ; DMW bench/2026-09-27b/M2F-S07-L.log
HOST bench/2026-09-27b/M2F-S07-D :: BD pair bench/2026-09-27b/M2F-S06-R.log,bench/2026-09-27b/X-M2F-S06-R.log bench/2026-09-27b/M2F-S07-R.log,bench/2026-09-27b/X-M2F-S07-R.log --host bench/2026-09-27b/M2F-S06-H.log bench/2026-09-27b/M2F-S07-H.log --pre bench/2026-09-27b/M2F-S06-P.log bench/2026-09-27b/M2F-S07-P.log
HOST bench/2026-09-27b/M2F-S08-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S07-H.log
HOST bench/2026-09-27b/M2F-S08-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S08 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S08-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S08-P :: HP
CAP --out bench/2026-09-27b/M2F-S08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S08-H :: HN ; DMW bench/2026-09-27b/M2F-S08-L.log
HOST bench/2026-09-27b/M2F-S08-D :: BD pair bench/2026-09-27b/M2F-S07-R.log,bench/2026-09-27b/X-M2F-S07-R.log bench/2026-09-27b/M2F-S08-R.log,bench/2026-09-27b/X-M2F-S08-R.log --host bench/2026-09-27b/M2F-S07-H.log bench/2026-09-27b/M2F-S08-H.log --pre bench/2026-09-27b/M2F-S07-P.log bench/2026-09-27b/M2F-S08-P.log
HOST bench/2026-09-27b/M2F-S09-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S08-H.log
HOST bench/2026-09-27b/M2F-S09-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S09 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S09-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S09-P :: HP
CAP --out bench/2026-09-27b/M2F-S09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S09-H :: HN ; DMW bench/2026-09-27b/M2F-S09-L.log
HOST bench/2026-09-27b/M2F-S09-D :: BD pair bench/2026-09-27b/M2F-S08-R.log,bench/2026-09-27b/X-M2F-S08-R.log bench/2026-09-27b/M2F-S09-R.log,bench/2026-09-27b/X-M2F-S09-R.log --host bench/2026-09-27b/M2F-S08-H.log bench/2026-09-27b/M2F-S09-H.log --pre bench/2026-09-27b/M2F-S08-P.log bench/2026-09-27b/M2F-S09-P.log
HOST bench/2026-09-27b/M2F-S10-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S09-H.log
HOST& bench/2026-09-27b/M2F-S10-T :: TDT
HOST bench/2026-09-27b/M2F-S10-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S10 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S10-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S10-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S10-P :: HP
CAP --out bench/2026-09-27b/M2F-S10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S10-H :: HN ; DMW bench/2026-09-27b/M2F-S10-L.log
HOST bench/2026-09-27b/M2F-S10-D :: BD pair bench/2026-09-27b/M2F-S09-R.log,bench/2026-09-27b/X-M2F-S09-R.log bench/2026-09-27b/M2F-S10-R.log,bench/2026-09-27b/X-M2F-S10-R.log --host bench/2026-09-27b/M2F-S09-H.log bench/2026-09-27b/M2F-S10-H.log --pre bench/2026-09-27b/M2F-S09-P.log bench/2026-09-27b/M2F-S10-P.log
HOST bench/2026-09-27b/M2F-S11-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S10-H.log
HOST& bench/2026-09-27b/M2F-S11-T :: TDT
HOST bench/2026-09-27b/M2F-S11-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S11 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S11-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S11-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S11-P :: HP
CAP --out bench/2026-09-27b/M2F-S11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S11-H :: HN ; DMW bench/2026-09-27b/M2F-S11-L.log
HOST bench/2026-09-27b/M2F-S11-D :: BD pair bench/2026-09-27b/M2F-S10-R.log,bench/2026-09-27b/X-M2F-S10-R.log bench/2026-09-27b/M2F-S11-R.log,bench/2026-09-27b/X-M2F-S11-R.log --host bench/2026-09-27b/M2F-S10-H.log bench/2026-09-27b/M2F-S11-H.log --pre bench/2026-09-27b/M2F-S10-P.log bench/2026-09-27b/M2F-S11-P.log
HOST bench/2026-09-27b/M2F-S12-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/M2F-S11-H.log
HOST bench/2026-09-27b/M2F-S12-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S12 :: ICMP 10.1.1.3
HOST bench/2026-09-27b/M2F-S12-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27b/M2F-S12-P :: HP
CAP --out bench/2026-09-27b/M2F-S12-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/M2F-S12-H :: HN ; DMW bench/2026-09-27b/M2F-S12-L.log
HOST bench/2026-09-27b/M2F-S12-D :: BD pair bench/2026-09-27b/M2F-S11-R.log,bench/2026-09-27b/X-M2F-S11-R.log bench/2026-09-27b/M2F-S12-R.log,bench/2026-09-27b/X-M2F-S12-R.log --host bench/2026-09-27b/M2F-S11-H.log bench/2026-09-27b/M2F-S12-H.log --pre bench/2026-09-27b/M2F-S11-P.log bench/2026-09-27b/M2F-S12-P.log
HOST bench/2026-09-27b/M2F-RTT :: RTT read --dir bench/2026-09-27b --arm M2F --plan 011001100110
```

### Arm P

```
HOST bench/2026-09-27b/CUT-P :: CUT --catch bench/2026-09-27b/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 12
```

```
CAP --out bench/2026-09-27b/P-SW0 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-N0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-LG0 --send 'linkprobe get rlx0 lo' --until 'LP9 calls [0-9]+ ok [0-9]+ refused [0-9]+ nowrite [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-W --send 'cd /tmp && linkprobe watch rlx0 10 600 > lpw.log 2>&1 &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/P-WS --send 'sleep 1 ; cat /tmp/lpw.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/P-CW0 :: CARRIER
HOST bench/2026-09-27b/P-WT1 :: CUT --catch bench/2026-09-27b/P-W.meta.json --date 2026-09-27 --since-max 5.66
```

```
HOST bench/2026-09-27b/P-PULL :: CW 100
```

```
CAP --out bench/2026-09-27b/P-SW1 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-N1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-LG1 --send 'linkprobe get rlx0 lo' --until 'LP9 calls [0-9]+ ok [0-9]+ refused [0-9]+ nowrite [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-MT1 --send 'cd /tmp && /bin/mfgtest auto acf8ed3d > mt1.log 2>&1 ; cat /tmp/mt1.log ; cd /' --until ' of 9 ok|Booting\.\.\.|---RealTek' --seconds 70
CAP --out bench/2026-09-27b/P-LW1 --send 'cat /tmp/lpw.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/P-CW1 :: CARRIER
HOST bench/2026-09-27b/P-D1 :: SWP delta bench/2026-09-27b/P-SW0.log bench/2026-09-27b/P-SW1.log
HOST bench/2026-09-27b/P-LR1 :: LPR get bench/2026-09-27b/P-LG1.log --expect rlx0,lo
HOST bench/2026-09-27b/P-WT2 :: CUT --catch bench/2026-09-27b/P-W.meta.json --date 2026-09-27 --since-max 5.66
```

```
HOST bench/2026-09-27b/P-PLUG :: CW 100
```

```
CAP --out bench/2026-09-27b/P-SW2 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-N2 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-LG2 --send 'linkprobe get rlx0 lo' --until 'LP9 calls [0-9]+ ok [0-9]+ refused [0-9]+ nowrite [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/P-MT2 --send 'cd /tmp && /bin/mfgtest auto acf8ed3d > mt2.log 2>&1 ; cat /tmp/mt2.log ; cd /' --until ' of 9 ok|Booting\.\.\.|---RealTek' --seconds 70
HOST bench/2026-09-27b/P-H1 :: sudo -n ip link set enxfc19286184c9 down ; sleep 3 ; sudo -n ip link set enxfc19286184c9 up ; sleep 2 ; ip -4 addr show dev enxfc19286184c9
CAP --out bench/2026-09-27b/P-SWH1 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27b/P-H2 :: sudo -n /usr/sbin/ethtool -r enxfc19286184c9 ; echo ethtool-r-rc $?
CAP --out bench/2026-09-27b/P-SWH2 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
```

```
HOST bench/2026-09-27b/P-LWH :: CUTW --catch bench/2026-09-27b/P-W.meta.json --after 605 --max 605
```

```
CAP --out bench/2026-09-27b/P-LW2 --send 'wait ; cat /tmp/lpw.log' --until 'LPW end n [0-9]+ .*trans [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 20
CAP --out bench/2026-09-27b/P-N3 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27b/P-99-P :: HP
CAP --out bench/2026-09-27b/P-99-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/P-99-H :: HN ; DMW bench/2026-09-27b/D3-LUS1-H.log,bench/2026-09-27b/K6-0063-L.log,bench/2026-09-27b/K6-0063-H1.log,bench/2026-09-27b/M2F-L.log,bench/2026-09-27b/M2F-S12-H.log
CAP --out bench/2026-09-27b/P-PS --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/P-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/P-99-H.log
HOST bench/2026-09-27b/P-CW2 :: CARRIER
HOST bench/2026-09-27b/P-D2 :: SWP delta bench/2026-09-27b/P-SW0.log bench/2026-09-27b/P-SW2.log
HOST bench/2026-09-27b/P-DH1 :: SWP delta bench/2026-09-27b/P-SW2.log bench/2026-09-27b/P-SWH1.log
HOST bench/2026-09-27b/P-DH2 :: SWP delta bench/2026-09-27b/P-SWH1.log bench/2026-09-27b/P-SWH2.log
HOST bench/2026-09-27b/P-LR2 :: LPR get bench/2026-09-27b/P-LG2.log --expect rlx0,lo
HOST bench/2026-09-27b/P-LWR :: LPR watch bench/2026-09-27b/P-LW2.log --ms 10 --s 600 --expect-seq 1,0,1
```

### `R6b-4`: `D4` at the fix, `NET-76`'s reads, the re-arm and the TCP tail, `D4` at 1.4

```
HOST bench/2026-09-27b/CUT-4 :: CUT --catch bench/2026-09-27b/R1-CATCH.meta.json --date 2026-09-27 --since-max 44 --start-by 23:05
```

```
CAP --out bench/2026-09-27b/F-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/F-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/F-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/K6-0063-H1.log,bench/2026-09-27b/M2F-L.log,bench/2026-09-27b/M2F-S12-H.log,bench/2026-09-27b/P-L.log
HOST bench/2026-09-27b/F-00-P :: HP
CAP --out bench/2026-09-27b/F-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/F-00-H :: HN ; DMW bench/2026-09-27b/F-L.log
CAP --out bench/2026-09-27b/F-S0 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
```

```
HOST bench/2026-09-27b/F-FLOOD :: D4F F
```

```
HOST bench/2026-09-27b/F-99-P :: HP
CAP --out bench/2026-09-27b/F-99-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/F-99-H :: HN ; DMW bench/2026-09-27b/F-00-H.log
CAP --out bench/2026-09-27b/F-S1 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27b/F-D :: BD pair bench/2026-09-27b/F-00-R.log,bench/2026-09-27b/X-F-00-R.log bench/2026-09-27b/F-99-R.log,bench/2026-09-27b/X-F-99-R.log --host bench/2026-09-27b/F-00-H.log bench/2026-09-27b/F-99-H.log --pre bench/2026-09-27b/F-00-P.log bench/2026-09-27b/F-99-P.log
HOST bench/2026-09-27b/F-COV :: D4C F
HOST bench/2026-09-27b/F-SWD :: SWP delta bench/2026-09-27b/F-S0.log bench/2026-09-27b/F-S1.log
CAP --out bench/2026-09-27b/N76-S0 --send 'cat /proc/net/snmp' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST& bench/2026-09-27b/N76-T :: TDE N76.pcap
HOST bench/2026-09-27b/N76-A :: sudo -n arping -c 4 -w 6 -I enxfc19286184c9 10.1.1.3 ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9
HOST bench/2026-09-27b/N76-PL :: PL
HOST bench/2026-09-27b/N76-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
CAP --out bench/2026-09-27b/N76-S1 --send 'cat /proc/net/snmp' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/N76-SN :: BD snmp bench/2026-09-27b/N76-S0.log bench/2026-09-27b/N76-S1.log
HOST bench/2026-09-27b/N76-W :: PWN none
```

```
HOST bench/2026-09-27b/CUT-T :: CUT --catch bench/2026-09-27b/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 11
```

```
CAP --out bench/2026-09-27b/T-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/T-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/T-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/F-L.log,bench/2026-09-27b/F-99-H.log
HOST bench/2026-09-27b/T-00-P :: HP
CAP --out bench/2026-09-27b/T-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/T-00-H :: HN ; DMW bench/2026-09-27b/T-L.log
CAP --out bench/2026-09-27b/T-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tl1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --until 'Booting\.\.\.|---RealTek' --seconds 30
```

```
HOST bench/2026-09-27b/T-TR :: IPERF5 -c 10.1.1.3 -p 5201 -t 300 -i 10 -f m -R
```

```
CAP --out bench/2026-09-27b/T-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tl1.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
HOST bench/2026-09-27b/T-P :: HP
CAP --out bench/2026-09-27b/T-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/T-H :: HN ; DMW bench/2026-09-27b/T-00-H.log
HOST bench/2026-09-27b/T-D :: BD pair bench/2026-09-27b/T-00-R.log,bench/2026-09-27b/X-T-00-R.log bench/2026-09-27b/T-R.log,bench/2026-09-27b/X-T-R.log --host bench/2026-09-27b/T-00-H.log bench/2026-09-27b/T-H.log --pre bench/2026-09-27b/T-00-P.log bench/2026-09-27b/T-P.log
HOST bench/2026-09-27b/T-IL :: ILG parse --duration 300 bench/2026-09-27b/T-S1.log
HOST bench/2026-09-27b/T-SN :: BD snmp bench/2026-09-27b/T-S0.log bench/2026-09-27b/T-S1.log
```

```
HOST bench/2026-09-27b/CUT-L :: CUT --catch bench/2026-09-27b/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 5
```

```
CAP --out bench/2026-09-27b/L-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/L-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/L-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/F-L.log,bench/2026-09-27b/F-99-H.log,bench/2026-09-27b/T-L.log,bench/2026-09-27b/T-00-H.log,bench/2026-09-27b/T-H.log
HOST bench/2026-09-27b/L-00-P :: HP
CAP --out bench/2026-09-27b/L-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/L-00-H :: HN ; DMW bench/2026-09-27b/L-L.log
CAP --out bench/2026-09-27b/L-S0 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
```

```
HOST bench/2026-09-27b/L-LOAD :: D4S L
```

```
HOST bench/2026-09-27b/L-99-P :: HP
CAP --out bench/2026-09-27b/L-99-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/L-99-H :: HN ; DMW bench/2026-09-27b/L-00-H.log
CAP --out bench/2026-09-27b/L-S1 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27b/L-D :: BD pair bench/2026-09-27b/L-00-R.log,bench/2026-09-27b/X-L-00-R.log bench/2026-09-27b/L-99-R.log,bench/2026-09-27b/X-L-99-R.log --host bench/2026-09-27b/L-00-H.log bench/2026-09-27b/L-99-H.log --pre bench/2026-09-27b/L-00-P.log bench/2026-09-27b/L-99-P.log
HOST bench/2026-09-27b/L-COV :: D4C L
HOST bench/2026-09-27b/L-SWD :: SWP delta bench/2026-09-27b/L-S0.log bench/2026-09-27b/L-S1.log
CAP --out bench/2026-09-27b/LE-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27b/LE-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27b/LE-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27b/L-L.log,bench/2026-09-27b/L-99-H.log
HOST bench/2026-09-27b/LE-00-P :: HP
CAP --out bench/2026-09-27b/LE-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/LE-00-H :: HN ; DMW bench/2026-09-27b/LE-L.log
HOST bench/2026-09-27b/LE-D :: BD pair bench/2026-09-27b/X-L-00-R.log,bench/2026-09-27b/L-99-R.log,bench/2026-09-27b/X-L-99-R.log bench/2026-09-27b/LE-00-R.log,bench/2026-09-27b/X-LE-00-R.log --host bench/2026-09-27b/F-99-H.log,bench/2026-09-27b/T-00-H.log,bench/2026-09-27b/T-H.log,bench/2026-09-27b/L-99-H.log bench/2026-09-27b/LE-00-H.log --pre bench/2026-09-27b/L-00-P.log,bench/2026-09-27b/L-99-P.log bench/2026-09-27b/LE-00-P.log
```

### The closing page, the map, `n_writes`, the kernel log, `port_status` last

```
CAP --out bench/2026-09-27b/Z-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27b/R1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-27b/R1-MB1 :: MB bench/2026-09-27b/R1-M1
CAP --out bench/2026-09-27b/R1-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27b/Z-DW :: DMW bench/2026-09-27b/B-00-H.log,bench/2026-09-27b/D3-L.log,bench/2026-09-27b/D3-TR1-L.log,bench/2026-09-27b/D3-TR2-L.log,bench/2026-09-27b/D3-TR3-L.log,bench/2026-09-27b/D3-TS1-L.log,bench/2026-09-27b/D3-TS2-L.log,bench/2026-09-27b/D3-TS3-L.log,bench/2026-09-27b/D3-UR1-L.log,bench/2026-09-27b/D3-UR2-L.log,bench/2026-09-27b/D3-UR3-L.log,bench/2026-09-27b/D3-US1-L.log,bench/2026-09-27b/D3-US2-L.log,bench/2026-09-27b/D3-US3-L.log,bench/2026-09-27b/D3-US3-H.log,bench/2026-09-27b/D3-X-L.log,bench/2026-09-27b/D3-LUR1-L.log,bench/2026-09-27b/D3-LUR1-H.log,bench/2026-09-27b/D3-Y-L.log,bench/2026-09-27b/D3-LUS1-L.log,bench/2026-09-27b/D3-LUS1-H.log,bench/2026-09-27b/K1-0061-L.log,bench/2026-09-27b/K1-0061-H1.log,bench/2026-09-27b/K2-0062-L.log,bench/2026-09-27b/K2-0062-H1.log,bench/2026-09-27b/K3-0063-L.log,bench/2026-09-27b/K3-0063-H1.log,bench/2026-09-27b/K4-0061-L.log,bench/2026-09-27b/K4-0061-H1.log,bench/2026-09-27b/K5-0062-L.log,bench/2026-09-27b/K5-0062-H1.log,bench/2026-09-27b/K6-0063-L.log,bench/2026-09-27b/K6-0063-H1.log,bench/2026-09-27b/M2F-L.log,bench/2026-09-27b/M2F-S01-L.log,bench/2026-09-27b/M2F-S01-H.log,bench/2026-09-27b/M2F-S02-L.log,bench/2026-09-27b/M2F-S02-H.log,bench/2026-09-27b/M2F-S03-L.log,bench/2026-09-27b/M2F-S03-H.log,bench/2026-09-27b/M2F-S04-L.log,bench/2026-09-27b/M2F-S04-H.log,bench/2026-09-27b/M2F-S05-L.log,bench/2026-09-27b/M2F-S05-H.log,bench/2026-09-27b/M2F-S06-L.log,bench/2026-09-27b/M2F-S06-H.log,bench/2026-09-27b/M2F-S07-L.log,bench/2026-09-27b/M2F-S07-H.log,bench/2026-09-27b/M2F-S08-L.log,bench/2026-09-27b/M2F-S08-H.log,bench/2026-09-27b/M2F-S09-L.log,bench/2026-09-27b/M2F-S09-H.log,bench/2026-09-27b/M2F-S10-L.log,bench/2026-09-27b/M2F-S10-H.log,bench/2026-09-27b/M2F-S11-L.log,bench/2026-09-27b/M2F-S11-H.log,bench/2026-09-27b/M2F-S12-L.log,bench/2026-09-27b/M2F-S12-H.log,bench/2026-09-27b/P-L.log,bench/2026-09-27b/F-L.log,bench/2026-09-27b/F-99-H.log,bench/2026-09-27b/T-L.log,bench/2026-09-27b/T-00-H.log,bench/2026-09-27b/T-H.log,bench/2026-09-27b/L-L.log,bench/2026-09-27b/L-99-H.log,bench/2026-09-27b/LE-L.log,bench/2026-09-27b/LE-00-H.log
HOST bench/2026-09-27b/Z-DWALL :: DMW none
CAP --out bench/2026-09-27b/Z-PS --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
```

---

## § 6 How the cells are run

**Before the freeze** (not on the day): the GbE adapter attached and up (`R0-ADDR`'s
`ip link set … up`: while it is administratively down the kernel reports no carrier, and
`carrierwatch` prints `-`) with the board off, then `chain43b.sh`, whose `gates43b.py` step
reads that adapter's carrier for `R0-CW`'s two cases (the `gates43b` cardnum row needs 28 of
28), then the freeze check. **Before any cell** (none of it a cell), after card A's press and
its power-off, in this order: (1) the time of the owner's reply confirming card A's power-off
is noted (P2's off-time), and no other WSL job is running; (2) `wsl --shutdown` from
PowerShell, then the keeper `wsl -d Ubuntu-24.04 -- sleep 36000` in the background; (3) the
kernel-log follower, from PowerShell in the background:
`wsl -d Ubuntu-24.04 -- bash -c "mkdir -p /home/key/fwre-work/rebuild/s113/host43b && exec dmesg -w > /home/key/fwre-work/rebuild/s113/host43b/dmesg-w43b.log"`,
started before the attach so the attach is in the log; (4) `usbipd list`, read fresh, then
`usbipd attach` of the CP2102 and of the GbE adapter, reading what each prints — the GbE
adapter is not touched again before `I-WPULL` unless S1 decides so; (5) in WSL, from the
repository root: `mkdir -p /home/key/fwre-work/rebuild/s113/run43b`;
`/usr/bin/python3 tools/cardcheck.py numbers` on this card, every row re-derived;
`/usr/bin/python3 tools/check-predictions.py` on this card, reading
**`0 of 523 captures came after the prediction, 523 did not`**; every invocation once through
`runblock.py … --dry`, each ending `ALL ITEMS DONE`. **The catch window opens no later than
23:14 on 2026-09-27**; later, the card is re-dated before power. At the estimate, `R6b-4` runs
only if it opens by 22:26 (`CUT-4`'s 23:05 less the 38.3 min to it), and nothing is cut only if
it opens by 22:26 (`CUT-4` binds); both are nominal, and one S1 or a slow reply moves them
earlier.

**The command lines.** Every invocation runs through the wrapper
`bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh NAME [TAG] [--from CELL]`, which runs
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log /home/key/fwre-work/rebuild/s113/run43b/run-NAME[-TAG].log`
and appends `INVOCATION NAME[-TAG] rc=N` to `/home/key/fwre-work/rebuild/s113/run43b/rc.tsv`;
`I-0` runs alone, before power. The press is four command lines, each a script file run by path
in the background of the session, its first line a `cd` to the repository root: its invocations
chained with `&&`, so that any stop ends the line, each watched invocation `I-W…` through
`--watch X-W<n>`, and then `;` and the line's tail watch `--tail X-W<n>`, which runs however
the line ended; a later line's first step stops the watch the line before left running
(`--stop`). No gap inside a line waits on the session's turn. In the full run the watches are
`X-W1` … `X-W24` on the four lines and `X-W25` on the power-off line (25), numbered as below; a
continuation after a stop is such a line too, from `--hold` (*The hold after a stop*) and
`--stop` of the running watch through the stopped invocation `--from` a cell (a new TAG) and
the invocations after it in its line, with the next unused numbers (no watch name is ever
re-run); at the loader's prompt a continuation has no `--hold` and no `--stop` (*The watch*). A
cut invocation that refuses ends its line; the next line starts, `--hold` first, from the
invocation after the skipped block (S6). The session follows each line's output and its run
logs: a line has ended when its tail watch's `XCELL … running` line appears.

`L1` — the press: started on the owner's reply to the press's ask; the owner is told to press once its catch runs:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-B \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-LP \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W1 I-WTR1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3TR1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W2 I-WTR2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3TR2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W3 I-WTR3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3TR3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W4 I-WTS1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3TS1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W5 I-WTS2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3TS2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W6 I-WTS3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3TS3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W7 I-WUR1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3UR1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W8 I-WUR2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3UR2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W9 I-WUR3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3UR3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W10 I-WUS1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3US1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W11 I-WUS2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3US2 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W12 I-WUS3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3US3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W13 I-WLUR1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3LUR1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W14 I-WLUS1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-D3LUS1 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-CN \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W15
```

`L2` — after `I-CN` permits and `I-N0` is started (the session's own background task) and seen running:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W15 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-N \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-N9 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-CM \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-M \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-CP \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-P1 \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W16
```

`L3` — the pull: started on the owner's reply to the pull's ask; the owner is told to pull once its window runs:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W16 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W17 I-WPULL \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-P2 \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W18
```

`L4` — the re-plug: started on the owner's reply to the re-plug's ask; the owner is told to re-plug once its window runs:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W18 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W19 I-WPLUG \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-P3 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W20 I-WLW \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-P3B \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-C4 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-4F \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W21 I-WF \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-4F9 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-CT \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-4T \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W22 I-WT \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-4T9 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-CL \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-4L \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --watch X-W23 I-WL \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-4L9 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-Z \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W24
```

The power-off, after `L4`'s end, on the owner's reply to its ask; the owner is told to power
off once `X-OFF1` runs, and the watch `X-W25` follows the window on its line (after a stop
below, the same line with the running watch and the next unused numbers):

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W24 \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --off X-OFF1 \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W25
```

**Chained references, on every path** (block 48's rule, unchanged). A kernel-log window's
`--prev` (`dmesgwin` 1.2), a capture window's `--prev` (`pcapwin` 1.3) and a pair's previous
read (`brdelta` 1.2) each name, comma-separated in run order, every log that is that chain's
last on some path this section allows, and the tool reads the last of them that exists; a
pair's current read is named with its stand-in after it (`<read>.log,X-<read>.log`), and so is
every previous read. The generator enumerates the paths — the full run, each event below at
every cell it can happen at (a stand-in read, an arm voided at its first read, a trial not run,
a host-path failure whose recovery passes or fails, the loader gate, each cut point refusing,
S4), and every ordered pair of the events that skip cells — and refuses a card on which a cell
on any path reads a log that path never wrote, or a list whose last written log is not that
chain's last. Nothing a recovery types writes a log a list names.

**The watch.** `X-W<n>` —
`CAP --out bench/2026-09-27b/X-W<n> --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605`
— sends nothing but ESC, at the period of block 15's `C5-UB`, which streamed ESC into a live
`rlxfw` for 145.9 s until the hardware watchdog bit and caught the loader at its prompt (量
`bench/2026-09-09/C5-UB`, a cardnum row); it ends on the loader's prompt `<RealTek>`, on its
cap, or on the wrapper's SIGINT. A reset inside it reaches the loader while ESC is streaming,
so the loader stops at its prompt instead of booting the vendor firmware. It must not end on
the banner, which would stop the ESC before the loader's window (the generator refuses a watch
text that holds it). `inv43b.sh --watch X-W<n> NAME` starts it in the background, confirms it
running (its log open, within 10 s: `WATCH X-W<n> running`, else `not running` and exit 4, the
invocation not run), runs the invocation, stops it (SIGINT, and waits for it), and exits 5 if
its log holds `<RealTek>` — `caught a reset` when the loader's banner precedes it,
`at the loader's prompt` when not — else the invocation's own exit; its `XCELL X-W<n> rc=N`
line goes to `/home/key/fwre-work/rebuild/s113/run43b/rc.tsv` as every X-cell's does (rc 1 is
`console-capture`'s *nothing came back*, which a watch over `ash` at its prompt may well read:
a reading, never a stop). `--tail X-W<n>` runs one in the foreground at a line's end;
`--stop X-W<n>` (or `--stop X-OFF<n>`, a power-off window) stops one another line started. A
watch that reaches its cap (3600 s) is followed at once by the next (`--tail`, the next
number); what an hour of ESC does to `ash` at its prompt is unmeasured, 推 harmless (it echoes
or drops them), and the watch's closing CR runs one line of them, which `ash` does not find as
a command; the one measured case of ESC streamed through a bite is `R2-B8`, whose kernel had
its interrupts off (the `bite` verb, 讀 `rtl819x-wdt.c`) and sent nothing back for the 41.9 s
before the banner, and whose loader the stream caught (`arith43b.out`). **At the loader's
prompt no watch is opened.** A watch opened with the board already at the loader's prompt ends
within about 1.3 s on the loader's own reply to its ESC: `console-capture` arms `--until` from
the start of a capture with no `--esc` and no `--send` (讀), and the loader answers every 128
ESC at its prompt with `Unknown command !` and its prompt (量 block 48's `R1-CATCH`, 550
replies; `arith43b.out`'s `LOADER` and `CCARM` lines). So **a watch or a power-off window
caught a reset only if the loader's banner (`Booting...` or `---RealTek`) precedes its
`<RealTek>`** (the wrapper prints `caught a reset`): the board is then at the loader's prompt,
and the loader rule below applies. A `<RealTek>` with no banner before it is the loader's reply
(`at the loader's prompt`): no reset is recorded, and the board is at its prompt. Where the
board's last known state is the loader's prompt — before the round, after `gate:caught` passed
and before `R1Q`'s `J` (sent by its `R1Q-boot` capture, absent then), or once a catch, a watch,
a window or a board X-cell has caught the loader — no further watch is opened, one already on a
command line ends on that reply, no line has `--hold` or `--stop`, and a power-off needs no
window: the loader boots nothing by itself. **The hold after a stop.** After any stop past the
round with the board running a kernel — a board cell's gate, a host gate (`-L`, `-LS`, `-D`,
`-X`), a cut point's refusal or any other — the watch holds the console, before any board cell
is typed and before any continuation starts, until at least 90 s after the latest board
capture's end: the newest capture in the card's directory that is not a watch or a window, its
`.meta.json`'s `end_real` or its `.log`'s last write, whichever is later. That capture is
either a reading that showed the kernel running, ended on its own text, or **a board cell that
ended silent** — one whose capture holds neither its own expected text nor the loader's,
however it ended, on its cap or on its `--idle` (a port-3 gate's capture with no `PSRP3` row or
no port-3 line of `port_status` at all is one) — which may be a kernel whose timer wheel
stopped before the cell or during it, so its last kick of `BOOTGUARD` can be as late as the
cell's end; counted from the cell's start, the hold would end up to the cell's length early. 90
s is the bite as measured at OVSEL 9, 84.001 s (`SPEC.md` `CLK-08b`; the stretch bound (§ 0 ⑥
(ii)) keeps the driver's own 83.8 s, the conservative side there), plus the loader's banner to
its first prompt with ESC streaming, 2.3 s (block 48's `R1-CATCH`; `C5-UB` and `R2-B8`, warm
resets at the watch's period, read 2.3 s too), plus a 3-s margin (a guess), rounded up
(`arith43b.out`'s `BITEM`, `B2P` and `HOLD` lines): a kernel that had stopped by then has been
bitten and its loader caught at the prompt inside the watch; one that stops a few seconds into
the hold or later may not be (§ 0 ⑥ (2) gives the edges and the gap after the hold). The
session never computes it: every line it starts after a stop begins with
`bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold`, which finds that capture,
prints its end and the hold's, waits beside the running watch, refuses (exit 2) if no console
capture runs, and exits 5 if the watch ended inside the hold (read its log: the banner rule
above); its `HOLD <cell> rc=N` line goes to `/home/key/fwre-work/rebuild/s113/run43b/rc.tsv`. A
kernel that stops after the capture the hold counts from bites later: inside one of the line's
board cells, whose capture ends on the loader's banner and ends the line (§ 0 ⑥ (i), and its
(1)), or inside the watch that follows.

**What each split adds** between the end of its host traffic and the next board read: the
watch's stop and the next invocation's start (0.5 s and 1 s, guesses: about 1.5 s more than
when the two cells shared an invocation), and one CR on the board's console, the watch's own
terminator (推: `ash` prints at most an error line, into the watch's log or the next capture's
head, which no gate reads). So `F-99-R` reads the board about 1.5 s later after the flood, each
`D3-<t>-S1` after its trial (the one-off server has exited after its test either way; the UDP
samplers' two copies were taken inside the trial), `T-S1` after the tail, `L-99-R` after the
1.4 load (the driver's own recovery acts about 1 s after a stall with or without them, S3),
`P-SW1` and `P-SW2` after the cable windows, `P-LW2` after the host's wait. No reading this
card scores depends on those seconds: the counters are cumulative and no traffic of the card
falls in them. The watch's ESC stream itself runs through all of that host traffic (§ 0 ⑤). If
the board were silent, each watch stop's gap to the next ESC stream (§ 0 ⑥ (2)) would be:
`I-WTR1` → `D3-TR1-S1` 6.5 s; `I-WTR2` → `D3-TR2-S1` 6.5 s; `I-WTR3` → `D3-TR3-S1` 6.5 s;
`I-WTS1` → `D3-TS1-S1` 6.5 s; `I-WTS2` → `D3-TS2-S1` 6.5 s; `I-WTS3` → `D3-TS3-S1` 6.5 s;
`I-WUR1` → `D3-UR1-S1` 6.5 s; `I-WUR2` → `D3-UR2-S1` 6.5 s; `I-WUR3` → `D3-UR3-S1` 6.5 s;
`I-WUS1` → `D3-US1-S1` 6.5 s; `I-WUS2` → `D3-US2-S1` 6.5 s; `I-WUS3` → `D3-US3-S1` 6.5 s;
`I-WLUR1` → `D3-LUR1-S1` 6.5 s; `I-WLUS1` → `D3-LUS1-S1` 6.5 s; the tail before `L2` →
`K1-0061-SW` 9.7 s; the tail before `L3` → the watch over `I-WPULL` 2.5 s; `I-WPULL` → `P-SW1`
13.5 s; the tail before `L4` → the watch over `I-WPLUG` 2.5 s; `I-WPLUG` → `P-SW2` 13.5 s;
`I-WLW` → `P-LW2` 23.5 s; `I-WF` → `F-99-R` 18.7 s; `I-WT` → `T-S1` 6.5 s; `I-WL` → `L-99-R`
18.7 s; the tail before the power-off line → `X-OFF1` 1.5 s.

**The owner's power and physical actions** (§ 0 ⑩'s five steps, for every one). **The press**:
the owner is told what comes next — that the catch will stream ESC for 360 s from its start and
the deadline it gives — and the session stops; on the owner's reply, the session starts `L1` in
the background, reads `I-1`'s transcript for `RUN CAP   R1-CATCH` and sees `R1-CATCH.timing`
exist (`console-capture` creates it once the port is open, just before its ESC loop), and only
then tells the owner "catch open — power on now, by HH:MM:SS": that `RUN` line's time of day
plus 350 s (§ 0 ⑩). It says so only while that deadline is at least 40 s away — by 310 s after
the `RUN` line; later, it tells the owner not to press, the catch runs to its cap with the
board off, `gate:caught` stops `L1`, its watch runs against a board that is off, the session
stops it once the owner has confirmed no press was made, and the press is lost: nothing booted,
and the card is re-issued. **Arm P**: before `L2` runs `I-P1`, the owner is told of both cable
actions in advance, each to go by the five steps. After `L2` has ended and `P-WT1` has been
read (below), the session asks for the pull and stops; on the reply it starts `L3`, reads its
output for `WATCH X-W<n> running` and `I-WPULL`'s transcript for `RUN HOST  P-PULL`, and only
then tells the owner "pull now, by HH:MM:SS" — that `RUN` line's time of day plus 100 s, the
end of `P-PULL`'s window. After `L3` has ended and `P-WT2` has been read, the re-plug goes the
same way with `L4`, `I-WPLUG` and `P-PLUG`; S4's `X-PLUG<n>` and the pull's `X-PULL<n>` too
(each `CW 100` beside the tail watch, its `XCELL … running` line the confirmation and its
`XCELL … t0` line's time plus 100 s the deadline). **The power-off**, after `L4`'s end or
wherever a stop below calls for one — "at once" there means that this ask is the session's
first action: the tail watch holds the console while the session waits for the reply; on the
reply the session starts the power-off line (`--stop` of the running watch, then
`--off X-OFF<n>`:
`CAP --out bench/2026-09-27b/X-OFF<n> --esc-after 360 --esc-period 0.01 --until '<RealTek>' --seconds 365`,
360 s of ESC, and `;` and the next watch `--tail`) in the background, reads its
`XCELL X-OFF<n> running` and `t0` lines, and only then tells the owner "power off now, by
HH:MM:SS" — the `t0` time plus 360 s. The owner confirms the power-off in words, a report that
is data; the session then stops what still runs: `--stop X-OFF<n>` if the window still runs,
which lets the line's watch start, and that watch by `--stop` once its `XCELL … running` line
appears. If the window reaches its cap with no confirmation, the watch that follows it on its
line holds the console until the owner confirms. **At the loader's prompt** (*The watch*) the
power-off has no window and no watch: after the owner's reply the session says "power off now"
with nothing to open or confirm, and the owner confirms.

**`I-0`** — before power: the pre-flight, the address, the adapter and its carrier with the board off, no capture, one kernel-log follower and a clean log, the flush, the capture and load directories, the host's iperf3, the checkers' digests and self-tests, the verb check

```run
R0-PRE?
R0-PREC
gate:grep=^  "bytes": 0,$:R0-PREC
gate:grep=^  "duration_s": 3\.[01][0-9]*,$:R0-PREC
R0-ADDR
gate:grep=inet 10\.1\.1\.2/24:R0-ADDR
R0-ETH
gate:grep=^/sys/class/net/eth0/statistics/tx_packets:\d+$:R0-ETH
R0-CW
gate:grep=^CW start if enxfc19286184c9 raw \S+ carrier 0 :R0-CW
gate:grep=^CW end n \d+ ms \d+ trans 0 carrier 0 :R0-CW
R0-TCPC
gate:grep=\A0\n\Z:R0-TCPC
R0-DMSG
gate:grep=\A1\n\Z:R0-DMSG
R0-DW0
gate:grep=^window 0 [1-9][0-9]*$:R0-DW0
gate:grep=^bug_preempt 0$:R0-DW0
gate:grep=^usbnet_xmit 0$:R0-DW0
gate:grep=^call_trace 0$:R0-DW0
gate:grep=^follower 1$:R0-DW0
R0-FL
gate:grep=\A(?:0\n)+\Z:R0-FL
R0-PCAP
gate:grep=\A0\n\Z:R0-PCAP
R0-IPF
gate:grep=^3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8  -$:R0-IPF
gate:grep=^/usr/bin/qemu-mips-static$:R0-IPF
R0-SUM
gate:grep=^e4c2943a5c814ada92cdaa21326df04c21c5349386d09d9ab9868a462a5951a7  -$:R0-SUM
gate:grep=^61b4003b31b9367bcde519c5d649ea70b1cf7224d9abfa2babee7c27b5450fb5  -$:R0-SUM
gate:grep=^f47f7f9bad9392bc83ed95d9bb2e515e0e0337ef102f112301004497ce0367eb  -$:R0-SUM
gate:grep=^6d2cd4153ffd22860311d800b9aecf4e8d8c78a8cdaa430347abb4088e2c2f25  -$:R0-SUM
gate:grep=^e8e4fa63b4787ff697b8658db95e25024fac1e40d2488361d2d4c774b0d90040  -$:R0-SUM
gate:grep=^8608019d6b9041f97ce23951e692c10f4a8db26f9fde94b2750d63f822016b82  -$:R0-SUM
gate:grep=^2779f40b6166dc1e0c7910ed358c7323f9e5dbd57c841a69a680dbcb2887f4cf  -$:R0-SUM
gate:grep=^c81188f835456a8c10d26035989b21a7beac9fd13431028217909a50b184ff98  -$:R0-SUM
gate:grep=^1b19c9ad4adae19124a4544e79b12d9b5a4e6eca3efc23652dcb6d61ea08cc9d  -$:R0-SUM
gate:grep=^030144a35c0bf3251640fc290ac4635e1c00ba84feb07ae9f19b87e34a2b3984  -$:R0-SUM
gate:grep=^6871c76753f28fac9cdbf7227dfc8fa015d9238ba908c3a70c5aeeda98408095  -$:R0-SUM
gate:grep=^2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1  -$:R0-SUM
gate:grep=^fd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431  -$:R0-SUM
gate:grep=^fbae2a34a798514f8fff35fbea7dbf189ae537f79718f2c7a12fca460993cecf  -$:R0-SUM
gate:grep=^12ab35696c31e3949b4398f02104b7e8dbc5f029338b0e4035110be5ca1be19b  -$:R0-SUM
R0-ST
gate:grep=^swpage\ self\-test:\ 18\ of\ 18\ passed$:R0-ST
gate:grep=^lpread\ self\-test:\ 27\ of\ 27\ passed$:R0-ST
gate:grep=^cutgate\ self\-test:\ 17\ of\ 17\ passed$:R0-ST
gate:grep=^carrierwatch\ self\-test:\ 3\ of\ 3\ passed$:R0-ST
gate:grep=^udpq\ self\-test:\ 8\ of\ 8\ passed$:R0-ST
gate:grep=^d4cover\ self\-test:\ 6\ of\ 6\ passed$:R0-ST
gate:grep=^brdelta\ self\-test:\ 40\ of\ 40\ passed$:R0-ST
gate:grep=^pcapwin\ self\-test:\ 29\ of\ 29\ passed$:R0-ST
gate:grep=^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$:R0-ST
gate:grep=^s1class\ self\-test:\ 15\ of\ 15\ passed$:R0-ST
gate:grep=^rttseries\ self\-test:\ 22\ of\ 22\ passed$:R0-ST
gate:grep=^RESULT:\ 31/31$:R0-ST
R0-VERB
gate:grep=^verbcheck verdict PASS$:R0-VERB
gate:grep=^verbcheck\ self\-test:\ 6\ of\ 6\ passed$:R0-VERB
R0-H?
```

**`I-1`** — the press, the first invocation of the first command line: the catch, `NET-30` 殘留's `DW` at the caught prompt, the flush, one round to the shell, the process table, the boot's `SW7` mark read, the opening map, `n_writes`

```run
R1-CATCH
gate:caught:R1-CATCH
R1-DW
gate:grep=^BB804134:\t[0-9A-F]{8}$:R1-DW
gate:grep=<RealTek>:R1-DW
R1-FL
gate:grep=\A(?:0\n)+\Z:R1-FL
R1Q
R1-PS
gate:grep=^ *1 +\S+ +\S+ +\S+ +/bin/sh *$:R1-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-PS
R1-SW7?
R1-M0
gate:until:R1-M0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-M0
R1-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:R1-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:R1-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:R1-MB0
R1-NW0
gate:grep=^n_writes 0$:R1-NW0
gate:grep=^recipe_id ACF8ED3D$:R1-NW0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-NW0
```

**`I-B`** — the opening state: switch 1.2's page first (`lde0`, `psrp3`), then 1.4's defaults with `rlx0` up, 1.5's page untouched since boot, the UDP receive buffer's size

```run
B-SW
gate:until:B-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-SW
gate:grep=^version rtl819x-switch 1\.2$:B-SW
gate:grep=^lde0 [0-9A-F]{2}$:B-SW
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:B-SW
B-00-P?
B-00-R
gate:until:B-00-R
gate:grep=^version rtl819x-nic 1\.5$:B-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:B-00-R
gate:grep=^nd_up 1$:B-00-R
B-00-H?
B-00-T
gate:until:B-00-T
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-00-T
gate:grep=^version rtl819x-nic 1\.5$:B-00-T
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:B-00-T
gate:grep=^v15 last - 0 ok 0 refused 0 txq \d+ arm15 0$:B-00-T
gate:grep=^sw never mode loop from 0 to 0 probe 0 rc 0 bufs 00000000$:B-00-T
gate:grep=^sw key txlen rlxfw txoff 0 txrb 0 mode loop probe 0 rings 0 rec 0$:B-00-T
gate:grep=^mt none 1455 clean 0 bad_b 0 bad_a 0 void 0 skew 0$:B-00-T
B-RMEM
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-RMEM
gate:grep=\A[\s\S]*^\d+\n\d+\n# ?\Z:B-RMEM
B-SWP?
```

**`I-LP`** — the `ethtool` ops: `linkprobe get rlx0 lo eth4 nosuch0` between two switch pages and two NIC dumps, then arm N (two switch pages, nothing between)

```run
LP-SW0
gate:until:LP-SW0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LP-SW0
gate:grep=^version rtl819x-switch 1\.2$:LP-SW0
LP-N0
gate:until:LP-N0
gate:grep=^version rtl819x-nic 1\.5$:LP-N0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LP-N0
LP-G
gate:until:LP-G
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LP-G
gate:grep=^LP0 linkprobe 1 build 1bce836f2e21c43a$:LP-G
LP-N1
gate:until:LP-N1
gate:grep=^version rtl819x-nic 1\.5$:LP-N1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LP-N1
LP-SW1
gate:until:LP-SW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LP-SW1
gate:grep=^version rtl819x-switch 1\.2$:LP-SW1
AN-SW2
gate:until:AN-SW2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):AN-SW2
gate:grep=^version rtl819x-switch 1\.2$:AN-SW2
LP-LR?
LP-DS?
AN-D?
```

**`I-D3`** — `D3`'s second boot at the fix: the arm opened at the fix (`txlen vendor`); then `D3-TR1`'s liveness gate and server

```run
D3-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-SW
D3-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:D3-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:D3-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:D3-LS
D3-L
gate:grep=^4 packets transmitted, 4 received:D3-L
gate:grep=^follower 1$:D3-L
D3-00-P?
D3-00-R
gate:until:D3-00-R
gate:grep=^version rtl819x-nic 1\.5$:D3-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-00-R
gate:grep=^nd_up 1$:D3-00-R
D3-00-H?
D3-TR1-L
gate:grep=^4 packets transmitted, 4 received:D3-TR1-L
gate:grep=^follower 1$:D3-TR1-L
D3-TR1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tr1\.log *$:D3-TR1-S0
```

**`I-WTR1`** — the trial `D3-TR1` alone, host only, while a watch holds the console

```run
D3-TR1?
```

**`I-D3TR1`** — `D3-TR1`'s server stopped, its bracket and readings; then `D3-TR2`'s liveness gate and server

```run
D3-TR1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR1-S1
D3-TR1-P?
D3-TR1-R
gate:until:D3-TR1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TR1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TR1-R
gate:grep=^nd_up 1$:D3-TR1-R
D3-TR1-H?
D3-TR1-D?
D3-TR1-IL?
D3-TR1-SN?
D3-TR1-IC?
D3-TR2-L
gate:grep=^4 packets transmitted, 4 received:D3-TR2-L
gate:grep=^follower 1$:D3-TR2-L
D3-TR2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tr2\.log *$:D3-TR2-S0
```

**`I-WTR2`** — the trial `D3-TR2` alone, host only, while a watch holds the console

```run
D3-TR2?
```

**`I-D3TR2`** — `D3-TR2`'s server stopped, its bracket and readings; then `D3-TR3`'s liveness gate and server

```run
D3-TR2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR2-S1
D3-TR2-P?
D3-TR2-R
gate:until:D3-TR2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TR2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TR2-R
gate:grep=^nd_up 1$:D3-TR2-R
D3-TR2-H?
D3-TR2-D?
D3-TR2-IL?
D3-TR2-SN?
D3-TR2-IC?
D3-TR3-L
gate:grep=^4 packets transmitted, 4 received:D3-TR3-L
gate:grep=^follower 1$:D3-TR3-L
D3-TR3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tr3\.log *$:D3-TR3-S0
```

**`I-WTR3`** — the trial `D3-TR3` alone, host only, while a watch holds the console

```run
D3-TR3?
```

**`I-D3TR3`** — `D3-TR3`'s server stopped, its bracket and readings; then `D3-TS1`'s liveness gate and server

```run
D3-TR3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR3-S1
D3-TR3-P?
D3-TR3-R
gate:until:D3-TR3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TR3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TR3-R
gate:grep=^nd_up 1$:D3-TR3-R
D3-TR3-H?
D3-TR3-D?
D3-TR3-IL?
D3-TR3-SN?
D3-TR3-IC?
D3-TS1-L
gate:grep=^4 packets transmitted, 4 received:D3-TS1-L
gate:grep=^follower 1$:D3-TS1-L
D3-TS1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ts1\.log *$:D3-TS1-S0
```

**`I-WTS1`** — the trial `D3-TS1` alone, host only, while a watch holds the console

```run
D3-TS1?
```

**`I-D3TS1`** — `D3-TS1`'s server stopped, its bracket and readings; then `D3-TS2`'s liveness gate and server

```run
D3-TS1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS1-S1
D3-TS1-P?
D3-TS1-R
gate:until:D3-TS1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TS1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TS1-R
gate:grep=^nd_up 1$:D3-TS1-R
D3-TS1-H?
D3-TS1-D?
D3-TS1-IL?
D3-TS1-SN?
D3-TS2-L
gate:grep=^4 packets transmitted, 4 received:D3-TS2-L
gate:grep=^follower 1$:D3-TS2-L
D3-TS2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ts2\.log *$:D3-TS2-S0
```

**`I-WTS2`** — the trial `D3-TS2` alone, host only, while a watch holds the console

```run
D3-TS2?
```

**`I-D3TS2`** — `D3-TS2`'s server stopped, its bracket and readings; then `D3-TS3`'s liveness gate and server

```run
D3-TS2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS2-S1
D3-TS2-P?
D3-TS2-R
gate:until:D3-TS2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TS2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TS2-R
gate:grep=^nd_up 1$:D3-TS2-R
D3-TS2-H?
D3-TS2-D?
D3-TS2-IL?
D3-TS2-SN?
D3-TS3-L
gate:grep=^4 packets transmitted, 4 received:D3-TS3-L
gate:grep=^follower 1$:D3-TS3-L
D3-TS3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ts3\.log *$:D3-TS3-S0
```

**`I-WTS3`** — the trial `D3-TS3` alone, host only, while a watch holds the console

```run
D3-TS3?
```

**`I-D3TS3`** — `D3-TS3`'s server stopped, its bracket and readings; then `D3-UR1`'s liveness gate, queue sampler and server

```run
D3-TS3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS3-S1
D3-TS3-P?
D3-TS3-R
gate:until:D3-TS3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TS3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TS3-R
gate:grep=^nd_up 1$:D3-TS3-R
D3-TS3-H?
D3-TS3-D?
D3-TS3-IL?
D3-TS3-SN?
D3-UR1-L
gate:grep=^4 packets transmitted, 4 received:D3-UR1-L
gate:grep=^follower 1$:D3-UR1-L
D3-UR1-Q
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-Q
D3-UR1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ur1\.log *$:D3-UR1-S0
```

**`I-WUR1`** — the trial `D3-UR1` alone, host only, while a watch holds the console

```run
D3-UR1?
```

**`I-D3UR1`** — `D3-UR1`'s server stopped, its bracket and readings; then `D3-UR2`'s liveness gate, queue sampler and server

```run
D3-UR1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-S1
D3-UR1-P?
D3-UR1-R
gate:until:D3-UR1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-UR1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-UR1-R
gate:grep=^nd_up 1$:D3-UR1-R
D3-UR1-H?
D3-UR1-D?
D3-UR1-IL?
D3-UR1-SN?
D3-UR1-IC?
D3-UR1-UQ?
D3-UR2-L
gate:grep=^4 packets transmitted, 4 received:D3-UR2-L
gate:grep=^follower 1$:D3-UR2-L
D3-UR2-Q
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-Q
D3-UR2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ur2\.log *$:D3-UR2-S0
```

**`I-WUR2`** — the trial `D3-UR2` alone, host only, while a watch holds the console

```run
D3-UR2?
```

**`I-D3UR2`** — `D3-UR2`'s server stopped, its bracket and readings; then `D3-UR3`'s liveness gate, queue sampler and server

```run
D3-UR2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-S1
D3-UR2-P?
D3-UR2-R
gate:until:D3-UR2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-UR2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-UR2-R
gate:grep=^nd_up 1$:D3-UR2-R
D3-UR2-H?
D3-UR2-D?
D3-UR2-IL?
D3-UR2-SN?
D3-UR2-IC?
D3-UR2-UQ?
D3-UR3-L
gate:grep=^4 packets transmitted, 4 received:D3-UR3-L
gate:grep=^follower 1$:D3-UR3-L
D3-UR3-Q
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-Q
D3-UR3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ur3\.log *$:D3-UR3-S0
```

**`I-WUR3`** — the trial `D3-UR3` alone, host only, while a watch holds the console

```run
D3-UR3?
```

**`I-D3UR3`** — `D3-UR3`'s server stopped, its bracket and readings; then `D3-US1`'s liveness gate and server

```run
D3-UR3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-S1
D3-UR3-P?
D3-UR3-R
gate:until:D3-UR3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-UR3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-UR3-R
gate:grep=^nd_up 1$:D3-UR3-R
D3-UR3-H?
D3-UR3-D?
D3-UR3-IL?
D3-UR3-SN?
D3-UR3-IC?
D3-UR3-UQ?
D3-US1-L
gate:grep=^4 packets transmitted, 4 received:D3-US1-L
gate:grep=^follower 1$:D3-US1-L
D3-US1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/us1\.log *$:D3-US1-S0
```

**`I-WUS1`** — the trial `D3-US1` alone, host only, while a watch holds the console

```run
D3-US1?
```

**`I-D3US1`** — `D3-US1`'s server stopped, its bracket and readings; then `D3-US2`'s liveness gate and server

```run
D3-US1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US1-S1
D3-US1-P?
D3-US1-R
gate:until:D3-US1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-US1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-US1-R
gate:grep=^nd_up 1$:D3-US1-R
D3-US1-H?
D3-US1-D?
D3-US1-IL?
D3-US1-SN?
D3-US2-L
gate:grep=^4 packets transmitted, 4 received:D3-US2-L
gate:grep=^follower 1$:D3-US2-L
D3-US2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/us2\.log *$:D3-US2-S0
```

**`I-WUS2`** — the trial `D3-US2` alone, host only, while a watch holds the console

```run
D3-US2?
```

**`I-D3US2`** — `D3-US2`'s server stopped, its bracket and readings; then `D3-US3`'s liveness gate and server

```run
D3-US2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US2-S1
D3-US2-P?
D3-US2-R
gate:until:D3-US2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-US2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-US2-R
gate:grep=^nd_up 1$:D3-US2-R
D3-US2-H?
D3-US2-D?
D3-US2-IL?
D3-US2-SN?
D3-US3-L
gate:grep=^4 packets transmitted, 4 received:D3-US3-L
gate:grep=^follower 1$:D3-US3-L
D3-US3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/us3\.log *$:D3-US3-S0
```

**`I-WUS3`** — the trial `D3-US3` alone, host only, while a watch holds the console

```run
D3-US3?
```

**`I-D3US3`** — `D3-US3`'s server stopped, its bracket and readings; then 1.4's control opened on a re-armed ring (`D3-X`); then `D3-LUR1`'s liveness gate, queue sampler and server

```run
D3-US3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US3-S1
D3-US3-P?
D3-US3-R
gate:until:D3-US3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-US3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-US3-R
gate:grep=^nd_up 1$:D3-US3-R
D3-US3-H?
D3-US3-D?
D3-US3-IL?
D3-US3-SN?
D3-X-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-X-SW
D3-X-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-X-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:D3-X-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:D3-X-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:D3-X-LS
D3-X-L
gate:grep=^4 packets transmitted, 4 received:D3-X-L
gate:grep=^follower 1$:D3-X-L
D3-X-00-P?
D3-X-00-R
gate:until:D3-X-00-R
gate:grep=^version rtl819x-nic 1\.5$:D3-X-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-X-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-X-00-R
gate:grep=^nd_up 1$:D3-X-00-R
D3-X-00-H?
D3-LUR1-L
gate:grep=^4 packets transmitted, 4 received:D3-LUR1-L
gate:grep=^follower 1$:D3-LUR1-L
D3-LUR1-Q
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-Q
D3-LUR1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/lur1\.log *$:D3-LUR1-S0
```

**`I-WLUR1`** — the trial `D3-LUR1` alone, host only, while a watch holds the console

```run
D3-LUR1?
```

**`I-D3LUR1`** — `D3-LUR1`'s server stopped, its bracket and readings; then `LUS1`'s own re-armed ring (`D3-Y`); then `D3-LUS1`'s liveness gate and server

```run
D3-LUR1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-S1
D3-LUR1-P?
D3-LUR1-R
gate:until:D3-LUR1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-LUR1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-LUR1-R
gate:grep=^nd_up 1$:D3-LUR1-R
D3-LUR1-H?
D3-LUR1-D?
D3-LUR1-IL?
D3-LUR1-SN?
D3-LUR1-UQ?
D3-Y-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-Y-SW
D3-Y-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-Y-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:D3-Y-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:D3-Y-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:D3-Y-LS
D3-Y-L
gate:grep=^4 packets transmitted, 4 received:D3-Y-L
gate:grep=^follower 1$:D3-Y-L
D3-Y-00-P?
D3-Y-00-R
gate:until:D3-Y-00-R
gate:grep=^version rtl819x-nic 1\.5$:D3-Y-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-Y-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-Y-00-R
gate:grep=^nd_up 1$:D3-Y-00-R
D3-Y-00-H?
D3-LUS1-L
gate:grep=^4 packets transmitted, 4 received:D3-LUS1-L
gate:grep=^follower 1$:D3-LUS1-L
D3-LUS1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUS1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/lus1\.log *$:D3-LUS1-S0
```

**`I-WLUS1`** — the trial `D3-LUS1` alone, host only, while a watch holds the console

```run
D3-LUS1?
```

**`I-D3LUS1`** — `D3-LUS1`'s server stopped, its bracket and readings; then the re-arm back to the fix (`D3-Z`) and the trials' tally

```run
D3-LUS1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUS1-S1
D3-LUS1-P?
D3-LUS1-R
gate:until:D3-LUS1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-LUS1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUS1-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-LUS1-R
gate:grep=^nd_up 1$:D3-LUS1-R
D3-LUS1-H?
D3-LUS1-D?
D3-LUS1-IL?
D3-LUS1-SN?
D3-Z-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-Z-SW
D3-Z-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-Z-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:D3-Z-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:D3-Z-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:D3-Z-LS
D3-SUM?
```

**`I-CN`** — the cut point before `NET-131`'s brackets

```run
CUT-N
gate:grep=^cut permit$:CUT-N
```

**`I-N0`** — `NET-131`'s host capture (the board's source address, 64 B), in the background until `I-N9`

```run
W-TCPN
```

**`I-N`** — `NET-131`'s deciding bracket: two requests on a re-armed ring at 61, 62 and 63, twice each, each run liveness, re-arm, port-3 gate, a bracket, `ping -c 2`, a bracket, the pair, a re-arm

```run
N-LIVE
gate:grep=\A1\n\Z:N-LIVE
K1-0061-L
gate:grep=^4 packets transmitted, 4 received:K1-0061-L
gate:grep=^follower 1$:K1-0061-L
K1-0061-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K1-0061-SW
K1-0061-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K1-0061-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:K1-0061-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:K1-0061-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:K1-0061-LS
K1-0061-P0?
K1-0061-R0
gate:until:K1-0061-R0
gate:grep=^version rtl819x-nic 1\.5$:K1-0061-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K1-0061-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K1-0061-R0
gate:grep=^nd_up 1$:K1-0061-R0
K1-0061-H0?
K1-0061-PG?
K1-0061-P1?
K1-0061-R1
gate:until:K1-0061-R1
gate:grep=^version rtl819x-nic 1\.5$:K1-0061-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K1-0061-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K1-0061-R1
gate:grep=^nd_up 1$:K1-0061-R1
K1-0061-H1?
K1-0061-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:K1-0061-D
K1-0061-E
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K1-0061-E
K2-0062-L
gate:grep=^4 packets transmitted, 4 received:K2-0062-L
gate:grep=^follower 1$:K2-0062-L
K2-0062-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K2-0062-SW
K2-0062-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K2-0062-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:K2-0062-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:K2-0062-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:K2-0062-LS
K2-0062-P0?
K2-0062-R0
gate:until:K2-0062-R0
gate:grep=^version rtl819x-nic 1\.5$:K2-0062-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K2-0062-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K2-0062-R0
gate:grep=^nd_up 1$:K2-0062-R0
K2-0062-H0?
K2-0062-PG?
K2-0062-P1?
K2-0062-R1
gate:until:K2-0062-R1
gate:grep=^version rtl819x-nic 1\.5$:K2-0062-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K2-0062-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K2-0062-R1
gate:grep=^nd_up 1$:K2-0062-R1
K2-0062-H1?
K2-0062-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:K2-0062-D
K2-0062-E
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K2-0062-E
K3-0063-L
gate:grep=^4 packets transmitted, 4 received:K3-0063-L
gate:grep=^follower 1$:K3-0063-L
K3-0063-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K3-0063-SW
K3-0063-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K3-0063-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:K3-0063-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:K3-0063-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:K3-0063-LS
K3-0063-P0?
K3-0063-R0
gate:until:K3-0063-R0
gate:grep=^version rtl819x-nic 1\.5$:K3-0063-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K3-0063-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K3-0063-R0
gate:grep=^nd_up 1$:K3-0063-R0
K3-0063-H0?
K3-0063-PG?
K3-0063-P1?
K3-0063-R1
gate:until:K3-0063-R1
gate:grep=^version rtl819x-nic 1\.5$:K3-0063-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K3-0063-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K3-0063-R1
gate:grep=^nd_up 1$:K3-0063-R1
K3-0063-H1?
K3-0063-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:K3-0063-D
K3-0063-E
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K3-0063-E
K4-0061-L
gate:grep=^4 packets transmitted, 4 received:K4-0061-L
gate:grep=^follower 1$:K4-0061-L
K4-0061-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K4-0061-SW
K4-0061-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K4-0061-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:K4-0061-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:K4-0061-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:K4-0061-LS
K4-0061-P0?
K4-0061-R0
gate:until:K4-0061-R0
gate:grep=^version rtl819x-nic 1\.5$:K4-0061-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K4-0061-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K4-0061-R0
gate:grep=^nd_up 1$:K4-0061-R0
K4-0061-H0?
K4-0061-PG?
K4-0061-P1?
K4-0061-R1
gate:until:K4-0061-R1
gate:grep=^version rtl819x-nic 1\.5$:K4-0061-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K4-0061-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K4-0061-R1
gate:grep=^nd_up 1$:K4-0061-R1
K4-0061-H1?
K4-0061-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:K4-0061-D
K4-0061-E
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K4-0061-E
K5-0062-L
gate:grep=^4 packets transmitted, 4 received:K5-0062-L
gate:grep=^follower 1$:K5-0062-L
K5-0062-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K5-0062-SW
K5-0062-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K5-0062-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:K5-0062-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:K5-0062-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:K5-0062-LS
K5-0062-P0?
K5-0062-R0
gate:until:K5-0062-R0
gate:grep=^version rtl819x-nic 1\.5$:K5-0062-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K5-0062-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K5-0062-R0
gate:grep=^nd_up 1$:K5-0062-R0
K5-0062-H0?
K5-0062-PG?
K5-0062-P1?
K5-0062-R1
gate:until:K5-0062-R1
gate:grep=^version rtl819x-nic 1\.5$:K5-0062-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K5-0062-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K5-0062-R1
gate:grep=^nd_up 1$:K5-0062-R1
K5-0062-H1?
K5-0062-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:K5-0062-D
K5-0062-E
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K5-0062-E
K6-0063-L
gate:grep=^4 packets transmitted, 4 received:K6-0063-L
gate:grep=^follower 1$:K6-0063-L
K6-0063-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K6-0063-SW
K6-0063-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K6-0063-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:K6-0063-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:K6-0063-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:K6-0063-LS
K6-0063-P0?
K6-0063-R0
gate:until:K6-0063-R0
gate:grep=^version rtl819x-nic 1\.5$:K6-0063-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K6-0063-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K6-0063-R0
gate:grep=^nd_up 1$:K6-0063-R0
K6-0063-H0?
K6-0063-PG?
K6-0063-P1?
K6-0063-R1
gate:until:K6-0063-R1
gate:grep=^version rtl819x-nic 1\.5$:K6-0063-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K6-0063-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:K6-0063-R1
gate:grep=^nd_up 1$:K6-0063-R1
K6-0063-H1?
K6-0063-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:K6-0063-D
K6-0063-E
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):K6-0063-E
```

**`I-N9`** — that capture stopped, summed, and windowed by record order

```run
W-TCPNX?
W-NWALL?
W-NORD?
```

**`I-CM`** — the cut point before `D3-MISS` ②

```run
CUT-M
gate:grep=^cut permit$:CUT-M
```

**`I-M`** — `D3-MISS` ② at the fix: card A's twelve ICMP series, the host's capture off and on in ABBA order, each behind its own liveness gate and two capture counts, bracketed as one arm

```run
M2F-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-SW
M2F-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:M2F-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:M2F-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:M2F-LS
M2F-L
gate:grep=^4 packets transmitted, 4 received:M2F-L
gate:grep=^follower 1$:M2F-L
M2F-00-P?
M2F-00-R
gate:until:M2F-00-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-00-R
gate:grep=^nd_up 1$:M2F-00-R
M2F-00-H?
M2F-S01-L
gate:grep=^4 packets transmitted, 4 received:M2F-S01-L
gate:grep=^follower 1$:M2F-S01-L
M2F-S01-C0?
M2F-S01?
M2F-S01-C1?
M2F-S01-P?
M2F-S01-R
gate:until:M2F-S01-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S01-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S01-R
gate:grep=^nd_up 1$:M2F-S01-R
M2F-S01-H?
M2F-S01-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S01-D
M2F-S02-L
gate:grep=^4 packets transmitted, 4 received:M2F-S02-L
gate:grep=^follower 1$:M2F-S02-L
M2F-S02-T
M2F-S02-C0?
M2F-S02?
M2F-S02-C1?
M2F-S02-X
gate:grep=\A0\n\Z:M2F-S02-X
M2F-S02-P?
M2F-S02-R
gate:until:M2F-S02-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S02-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S02-R
gate:grep=^nd_up 1$:M2F-S02-R
M2F-S02-H?
M2F-S02-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S02-D
M2F-S03-L
gate:grep=^4 packets transmitted, 4 received:M2F-S03-L
gate:grep=^follower 1$:M2F-S03-L
M2F-S03-T
M2F-S03-C0?
M2F-S03?
M2F-S03-C1?
M2F-S03-X
gate:grep=\A0\n\Z:M2F-S03-X
M2F-S03-P?
M2F-S03-R
gate:until:M2F-S03-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S03-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S03-R
gate:grep=^nd_up 1$:M2F-S03-R
M2F-S03-H?
M2F-S03-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S03-D
M2F-S04-L
gate:grep=^4 packets transmitted, 4 received:M2F-S04-L
gate:grep=^follower 1$:M2F-S04-L
M2F-S04-C0?
M2F-S04?
M2F-S04-C1?
M2F-S04-P?
M2F-S04-R
gate:until:M2F-S04-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S04-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S04-R
gate:grep=^nd_up 1$:M2F-S04-R
M2F-S04-H?
M2F-S04-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S04-D
M2F-S05-L
gate:grep=^4 packets transmitted, 4 received:M2F-S05-L
gate:grep=^follower 1$:M2F-S05-L
M2F-S05-C0?
M2F-S05?
M2F-S05-C1?
M2F-S05-P?
M2F-S05-R
gate:until:M2F-S05-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S05-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S05-R
gate:grep=^nd_up 1$:M2F-S05-R
M2F-S05-H?
M2F-S05-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S05-D
M2F-S06-L
gate:grep=^4 packets transmitted, 4 received:M2F-S06-L
gate:grep=^follower 1$:M2F-S06-L
M2F-S06-T
M2F-S06-C0?
M2F-S06?
M2F-S06-C1?
M2F-S06-X
gate:grep=\A0\n\Z:M2F-S06-X
M2F-S06-P?
M2F-S06-R
gate:until:M2F-S06-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S06-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S06-R
gate:grep=^nd_up 1$:M2F-S06-R
M2F-S06-H?
M2F-S06-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S06-D
M2F-S07-L
gate:grep=^4 packets transmitted, 4 received:M2F-S07-L
gate:grep=^follower 1$:M2F-S07-L
M2F-S07-T
M2F-S07-C0?
M2F-S07?
M2F-S07-C1?
M2F-S07-X
gate:grep=\A0\n\Z:M2F-S07-X
M2F-S07-P?
M2F-S07-R
gate:until:M2F-S07-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S07-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S07-R
gate:grep=^nd_up 1$:M2F-S07-R
M2F-S07-H?
M2F-S07-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S07-D
M2F-S08-L
gate:grep=^4 packets transmitted, 4 received:M2F-S08-L
gate:grep=^follower 1$:M2F-S08-L
M2F-S08-C0?
M2F-S08?
M2F-S08-C1?
M2F-S08-P?
M2F-S08-R
gate:until:M2F-S08-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S08-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S08-R
gate:grep=^nd_up 1$:M2F-S08-R
M2F-S08-H?
M2F-S08-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S08-D
M2F-S09-L
gate:grep=^4 packets transmitted, 4 received:M2F-S09-L
gate:grep=^follower 1$:M2F-S09-L
M2F-S09-C0?
M2F-S09?
M2F-S09-C1?
M2F-S09-P?
M2F-S09-R
gate:until:M2F-S09-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S09-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S09-R
gate:grep=^nd_up 1$:M2F-S09-R
M2F-S09-H?
M2F-S09-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S09-D
M2F-S10-L
gate:grep=^4 packets transmitted, 4 received:M2F-S10-L
gate:grep=^follower 1$:M2F-S10-L
M2F-S10-T
M2F-S10-C0?
M2F-S10?
M2F-S10-C1?
M2F-S10-X
gate:grep=\A0\n\Z:M2F-S10-X
M2F-S10-P?
M2F-S10-R
gate:until:M2F-S10-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S10-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S10-R
gate:grep=^nd_up 1$:M2F-S10-R
M2F-S10-H?
M2F-S10-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S10-D
M2F-S11-L
gate:grep=^4 packets transmitted, 4 received:M2F-S11-L
gate:grep=^follower 1$:M2F-S11-L
M2F-S11-T
M2F-S11-C0?
M2F-S11?
M2F-S11-C1?
M2F-S11-X
gate:grep=\A0\n\Z:M2F-S11-X
M2F-S11-P?
M2F-S11-R
gate:until:M2F-S11-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S11-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S11-R
gate:grep=^nd_up 1$:M2F-S11-R
M2F-S11-H?
M2F-S11-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S11-D
M2F-S12-L
gate:grep=^4 packets transmitted, 4 received:M2F-S12-L
gate:grep=^follower 1$:M2F-S12-L
M2F-S12-C0?
M2F-S12?
M2F-S12-C1?
M2F-S12-P?
M2F-S12-R
gate:until:M2F-S12-R
gate:grep=^version rtl819x-nic 1\.5$:M2F-S12-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M2F-S12-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:M2F-S12-R
gate:grep=^nd_up 1$:M2F-S12-R
M2F-S12-H?
M2F-S12-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:M2F-S12-D
M2F-RTT?
```

**`I-CP`** — the cut point before arm P

```run
CUT-P
gate:grep=^cut permit$:CUT-P
```

**`I-P1`** — arm P's opening (the owner told of both cable actions first): the switch page, the NIC dump and `linkprobe get rlx0 lo` with the cable in, then `linkprobe watch rlx0 10 600` started on the board's tmpfs and seen running, and the watch's time checked before the pull is asked for

```run
P-SW0
gate:until:P-SW0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-SW0
gate:grep=^version rtl819x-switch 1\.2$:P-SW0
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:P-SW0
P-N0
gate:until:P-N0
gate:grep=^version rtl819x-nic 1\.5$:P-N0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-N0
P-LG0
gate:until:P-LG0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-LG0
gate:grep=^LP0 linkprobe 1 build 1bce836f2e21c43a$:P-LG0
P-W
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-W
P-WS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-WS
gate:grep=^LP0 linkprobe 1 build 1bce836f2e21c43a$:P-WS
gate:grep=^LPW start rlx0 v 1 rc 0$:P-WS
P-CW0?
P-WT1?
```

**`I-WPULL`** — the pull's window alone, host only, while a watch holds the console: the carrier watcher's 100 s, inside which the owner pulls the cable when told

```run
P-PULL?
```

**`I-P2`** — every static read with the cable out, and the watch's time checked before the re-plug is asked for

```run
P-SW1
gate:until:P-SW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-SW1
gate:grep=^version rtl819x-switch 1\.2$:P-SW1
gate:grep=^psrp3 [0-9A-F]{8} up 0 lde \d+ lj \d+$:P-SW1
P-N1
gate:until:P-N1
gate:grep=^version rtl819x-nic 1\.5$:P-N1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-N1
P-LG1
gate:until:P-LG1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-LG1
gate:grep=^LP0 linkprobe 1 build 1bce836f2e21c43a$:P-LG1
P-MT1
gate:until:P-MT1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-MT1
P-LW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-LW1
P-CW1?
P-D1?
P-LR1?
P-WT2?
```

**`I-WPLUG`** — the re-plug's window alone, host only, while a watch holds the console: the carrier watcher's 100 s, inside which the owner re-plugs the cable when told

```run
P-PLUG?
```

**`I-P3`** — every static read with the cable back, H1 and H2

```run
P-SW2
gate:until:P-SW2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-SW2
gate:grep=^version rtl819x-switch 1\.2$:P-SW2
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:P-SW2
P-N2
gate:until:P-N2
gate:grep=^version rtl819x-nic 1\.5$:P-N2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-N2
P-LG2
gate:until:P-LG2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-LG2
gate:grep=^LP0 linkprobe 1 build 1bce836f2e21c43a$:P-LG2
P-MT2
gate:until:P-MT2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-MT2
P-H1
gate:grep=inet 10\.1\.1\.2/24:P-H1
P-SWH1
gate:until:P-SWH1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-SWH1
gate:grep=^version rtl819x-switch 1\.2$:P-SWH1
P-H2?
P-SWH2
gate:until:P-SWH2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-SWH2
gate:grep=^version rtl819x-switch 1\.2$:P-SWH2
```

**`I-WLW`** — the host's wait for the board's watch to end, host only, while a watch holds the console

```run
P-LWH
gate:grep=^cutgate wait end since \d+\.\d s$:P-LWH
```

**`I-P3B`** — the board's watch read, a bracket, the vendor's `port_status` last, the liveness gate and the re-plug comparison

```run
P-LW2
gate:until:P-LW2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-LW2
P-N3
gate:until:P-N3
gate:grep=^version rtl819x-nic 1\.5$:P-N3
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-N3
P-99-P?
P-99-R
gate:until:P-99-R
gate:grep=^version rtl819x-nic 1\.5$:P-99-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-99-R
P-99-H?
P-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):P-PS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:P-PS
P-L
gate:grep=^4 packets transmitted, 4 received:P-L
gate:grep=^follower 1$:P-L
P-CW2?
P-D2
gate:grep=^masked 3 [0-9A-F]{8} [0-9A-F]{8} bit8 \d \d same yes$:P-D2
P-DH1?
P-DH2?
P-LR2?
P-LWR?
```

**`I-C4`** — the cut point before `R6b-4` (the planner's two rules, § 6 S6)

```run
CUT-4
gate:grep=^cut permit$:CUT-4
```

**`I-4F`** — `D4`'s fix run opened: the arm at the fix, the switch page before

```run
F-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-SW
F-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:F-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:F-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:F-LS
F-L
gate:grep=^4 packets transmitted, 4 received:F-L
gate:grep=^follower 1$:F-L
F-00-P?
F-00-R
gate:until:F-00-R
gate:grep=^version rtl819x-nic 1\.5$:F-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:F-00-R
gate:grep=^nd_up 1$:F-00-R
F-00-H?
F-S0
gate:until:F-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-S0
gate:grep=^version rtl819x-switch 1\.2$:F-S0
```

**`I-WF`** — `NET-76`'s 31-minute flood beside every stack length, host only, while a watch holds the console

```run
F-FLOOD?
```

**`I-4F9`** — the board read after the flood; then `NET-76` 殘留's reads before any re-arm

```run
F-99-P?
F-99-R
gate:until:F-99-R
gate:grep=^version rtl819x-nic 1\.5$:F-99-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-99-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:F-99-R
gate:grep=^nd_up 1$:F-99-R
F-99-H?
F-S1
gate:until:F-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-S1
gate:grep=^version rtl819x-switch 1\.2$:F-S1
F-D?
F-COV?
F-SWD?
N76-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):N76-S0
N76-T
N76-A?
N76-PL?
N76-X
gate:grep=^0$:N76-X
N76-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):N76-S1
N76-SN?
N76-W?
```

**`I-CT`** — the cut point before the TCP tail

```run
CUT-T
gate:grep=^cut permit$:CUT-T
```

**`I-4T`** — the tail's arm, re-armed at the fix after `NET-76`'s reads, and its server

```run
T-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):T-SW
T-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):T-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:T-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:T-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:T-LS
T-L
gate:grep=^4 packets transmitted, 4 received:T-L
gate:grep=^follower 1$:T-L
T-00-P?
T-00-R
gate:until:T-00-R
gate:grep=^version rtl819x-nic 1\.5$:T-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):T-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:T-00-R
gate:grep=^nd_up 1$:T-00-R
T-00-H?
T-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):T-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tl1\.log *$:T-S0
```

**`I-WT`** — the five-minute TCP board-sends tail, host only, while a watch holds the console

```run
T-TR?
```

**`I-4T9`** — the tail's server stopped, its bracket and readings

```run
T-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):T-S1
T-P?
T-R
gate:until:T-R
gate:grep=^version rtl819x-nic 1\.5$:T-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):T-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:T-R
gate:grep=^nd_up 1$:T-R
T-H?
T-D?
T-IL?
T-SN?
```

**`I-CL`** — the cut point before `D4`'s 1.4 arm

```run
CUT-L
gate:grep=^cut permit$:CUT-L
```

**`I-4L`** — `D4`'s 1.4 arm opened on a re-armed ring, the switch page before

```run
L-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):L-SW
L-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):L-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:L-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:L-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:L-LS
L-L
gate:grep=^4 packets transmitted, 4 received:L-L
gate:grep=^follower 1$:L-L
L-00-P?
L-00-R
gate:until:L-00-R
gate:grep=^version rtl819x-nic 1\.5$:L-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):L-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:L-00-R
gate:grep=^nd_up 1$:L-00-R
L-00-H?
L-S0
gate:until:L-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):L-S0
gate:grep=^version rtl819x-switch 1\.2$:L-S0
```

**`I-WL`** — the same load at 1.4 for 120 s, bounded by `timeout`, host only, while a watch holds the console

```run
L-LOAD?
```

**`I-4L9`** — the board read after the load; then the re-arm back to the fix and the liveness gate

```run
L-99-P?
L-99-R
gate:until:L-99-R
gate:grep=^version rtl819x-nic 1\.5$:L-99-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):L-99-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:L-99-R
gate:grep=^nd_up 1$:L-99-R
L-99-H?
L-S1
gate:until:L-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):L-S1
gate:grep=^version rtl819x-switch 1\.2$:L-S1
L-D?
L-COV?
L-SWD?
LE-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LE-SW
LE-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LE-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:LE-LS
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:LE-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:LE-LS
LE-L
gate:grep=^4 packets transmitted, 4 received:LE-L
gate:grep=^follower 1$:LE-L
LE-00-P?
LE-00-R
gate:until:LE-00-R
gate:grep=^version rtl819x-nic 1\.5$:LE-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LE-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:LE-00-R
gate:grep=^nd_up 1$:LE-00-R
LE-00-H?
LE-D?
```

**`I-Z`** — the closing switch page, the map, `n_writes`, the kernel log's last window and the vendor's `port_status` last; then the power-off, by the handshake

```run
Z-SW
gate:until:Z-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):Z-SW
gate:grep=^version rtl819x-switch 1\.2$:Z-SW
R1-M1
gate:until:R1-M1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-M1
R1-MB1
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:R1-MB1
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:R1-MB1
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:R1-MB1
R1-NW1
gate:grep=^n_writes 0$:R1-NW1
gate:grep=^recipe_id ACF8ED3D$:R1-NW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-NW1
Z-DW?
Z-DWALL?
Z-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):Z-PS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:Z-PS
```

**What each stop means, decided now** — a repeat is always a new name, declared in
`bench/2026-09-27b/CORRECTIONS-block50.md` before it runs, **except the cells whose text this
section fixes now (they are logged there as they run) and a power-off, which this card decides
and which waits for no declaration**:

* **The loader gate on any board cell** (`Booting...`, `---RealTek`, `<RealTek>` or
  `Linux version` in the capture), the same text in any other failed board cell's capture, the
  loader's banner before `<RealTek>` in a watch's or a power-off window's log (the wrapper's
  `caught a reset`, exit 5), or the loader's text in a board X-cell's capture (the wrapper's
  exit 5): the board has reset. The watch that followed that cell on its command line is read
  at once: `<RealTek>` in it, the loader was caught at its prompt and waits there (the banner
  may be in the cell's capture rather than the watch's), and no further watch is opened; not,
  the vendor firmware may be booting (§ 0 ⑥, what it does not cover), and the watch still runs.
  Either way **the owner is asked to power off at once** — the session's first action, before
  any other cell and any `bench/2026-09-27b/CORRECTIONS-block50.md` entry — by § 0 ⑩'s five
  steps, with no window at the loader's prompt (*The watch*), the watch holding the console
  meanwhile if it still runs. `I-N9` still runs if `N1.pcap` was running (host only); `I-Z`
  does not, and the next card's first map closes this press's bracket.
* **A watch not running** (`WATCH X-W<n> not running`, exit 4: the watched invocation did not
  run): `/dev/ttyUSB0` is checked, the reason read, and the line started again from that
  invocation with the next watch number and no `--hold` (no watch runs to hold beside); the
  board is then without a watch until it runs, so this comes before anything else. **A board
  cell that ended silent** (*The watch*): the hold, then the cell's own rule below.
* **`R0-*`**: no power until each reads as its gate asks (`R0-PREC`, `R0-ADDR`, `R0-FL`,
  `R0-PCAP`, `R0-TCPC`, `R0-DMSG`, `R0-DW0`, `R0-IPF`, `R0-SUM`, `R0-ST`, `R0-VERB`: block 48's
  rules). **`R0-ETH`** without `eth0`'s `tx_packets`: P8's bound on the host's other UDP is
  unmeasured, and the owner decides whether to press. **`R0-CW`** not carrier 0 with the board
  off: the carrier watcher is not the instrument arm P's windows need; arm P's `CW` lines
  become readings with no control, and the owner decides.
* **`gate:caught`** on `R1-CATCH`: the catch did not catch the loader, and `L1`'s watch is read
  at once — the loader's banner before `<RealTek>` in it, a press after the catch's stream was
  caught there and nothing booted; `<RealTek>` with no banner before it, the board already
  waited at the loader's prompt when the watch opened; neither, the loader may have autobooted
  the vendor, unless the owner had not yet pressed (their report is data). Either way the press
  is lost — power off, by § 0 ⑩'s five steps, with no window at the loader's prompt (*The
  watch*) in the first two cases — and the next card's first map brackets any boot.
  **`R1-FL`**, **`R1Q`**, **`R1-PS`**, the maps and `n_writes`: block 46's § 6 rules; a stop of
  `I-1` before `R1Q`'s `J` leaves the board at the loader's prompt, where `L1`'s watch ends on
  the loader's reply (no reset recorded) and a power-off has no window. **`R1-DW`** (no reply
  line of its form, or no prompt after it): its capture is read; if it ends at `<RealTek>`, the
  board waits at the loader's prompt, `L1`'s watch has ended on the loader's reply, and `I-1`
  continues as a line of its own —
  `bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh I-1 <tag> --from R1-FL`, then `L1`'s
  invocations after `I-1`, the watches numbered from the next unused, with no `--hold` and no
  `--stop` (the loader's prompt) — and P2's loader half is unmeasured (a reading about the
  reply's form); if not, the owner is told to power off.
* **`B-SW`**, **`B-00-R`**, **`B-00-T`** (not switch 1.2's page, not 1.4's defaults with `rlx0`
  up, or not 1.5's untouched page): no cell after it runs until the owner has read the page.
  **Any other switch page's gate** (`until`, `version`, a `psrp3` gate other than arm P's):
  after the hold, the read is typed again once under `X-<page>`; a second failure — no cell
  until the owner has read it.
* **S5, `linkprobe`** (`LP-G`, `P-LG*`, `P-WS`: its `until` or `LP0` gate failing, no loader
  text): a crash or a hang is a reading, never retried; after the hold, `/dev/ttyUSB0` is
  checked and `X-RT<n>` (the driver page) typed; if rlxfw answers, the invocation continues
  `--from` the next cell (the line *S5* under *The declared X-cells*). At `P-WS` the board's
  watch is started again once as `X-PWR<n>` (`P-W`'s own text, so `P-LW1` and `P-LW2` read it)
  and read as `X-PWRS<n>` (`P-WS`'s); `P-WT1`, `P-WT2` and `P-LWH` still count from
  `P-W.meta.json`, a few seconds before the restart's own start (the conservative side for the
  checks; `P-LW2`'s `wait` covers the rest inside its 20-s cap, and its rule below applies if
  it does not); if it still does not start, arm P runs without it and P11's watch half is
  unmeasured.
* **S1, a liveness gate** (`-L`: fewer than 4 of 4, or `follower` not 1), **a port-3 gate**
  (`-LS`) **or a path gate** (`K…-D`, `M2F-D`): `follower` alone failing — the follower is
  restarted with (3)'s command with `>>` in place of `>`, the liveness typed again as `X-L<n>`,
  every kernel-log window since the last `follower 1` void. **A port-3 gate whose capture holds
  no `PSRP3` row or no port-3 line of `port_status` at all** ended silent (*The watch*), not
  with a finding about the page: after the hold, `/dev/ttyUSB0` is checked and the gate typed
  again as its stand-in `X-<p>-LS`, read as the gate reads it — `LinkUp` on both readers, the
  invocation continues `--from` the next cell; silent again, or garbage, the owner is asked to
  power off; a row present and not `LinkUp`, in the gate's capture or its stand-in's, is S1 as
  below. Otherwise, **before anything on the host is touched and with `rlx0` left as it is**,
  after the hold, the read set, as declared cells whose text is fixed here (the line *S1's read
  set* under *The declared X-cells*): (1) `X-SW<n>`, rlxfw's switch page (1.2 counts the bit 8
  it consumes; first); (2) `X-NIC<n>`, the driver page; (3) `X-BR<n>`, the full board bracket,
  between `X-HP<n>` (`HP`) and (5); (4) `X-PS<n>`, the vendor's `port_status`, last; (5)
  `X-HN<n>` (`HN`); then (6) `X-C<n>`, the classifier, beside the watch, where `<PREV>` is the
  last board bracket read written before the failed gate on the path the press took (its
  stand-in if one was typed) and `<PREVH>` that read's `-H` log. **Branch a** (the host reached
  the board: the board's TX side is the question): after the hold (at least 3 s), `X-NIC<n>a`
  (the driver page: `n_recov_ok` moved, `txd` OWN `0000`, a reading), then `X-L<n>a` (the
  liveness) beside the watch; if it passes, the arm's re-arm is typed as `X-RA<n>a` (its switch
  cell's text, `<txlen>` the arm's policy) and the invocation continues `--from` the cell after
  the failed one, on one line — no re-attach. **Branch b** (the host → board path), **or branch
  a's `X-L<n>a` failing**: block 48's `NET-54` 殘留 ② order — `X-PHY<n>` (three `read`s of port
  3's PHY through the vendor's `phyReg`, read-only), then the recovery, a software action on
  the host, beside the watch: `X-REL<n>` (`usbipd.exe list`, read fresh for the GbE adapter's
  busid, never the CP2102's), `X-RE<n>` (`usbipd.exe detach` and `attach --wsl` of that busid,
  reading what each prints), then `X-REA<n>` (`R0-ADDR`'s command); declared now: **a re-attach
  bounces port 3's link (block 48's `X-SW1b` read `PSRP3` `000001F9`, 量) and restarts the
  adapter's `rx_packets`, so P0 (b) is void at the pair that spans it**; then, on a line after
  the hold, `X-SW<n>b` and `X-PS<n>b`; beside the watch, `X-TC<n>` (the `tcpdump` count; inside
  `I-N` the capture is started again once as the off-card `W-TCPN2`, `TDE N1b.pcap`, and
  `N1.pcap`'s anchor is void) and `X-L<n>b` (the liveness). If it passes: the invocation
  continues `--from` the cell after the failed one; an arm whose path gate failed is void,
  never a result; inside `D3`'s invocations it continues `--from` the trial's `-S0`. If it
  fails: every later host arm is skipped — `I-N9` if `N1.pcap` runs, then `I-Z`.
* **S2, the re-arm rule**: every 1.4 arm and trial begins and ends with a re-arm before the
  next liveness gate (the cells do so by construction, and the generator checks it on every
  path). If a 1.4 cell stops its invocation, the first cell typed after § 6's handling is that
  arm's end re-arm (`D3-Y-SW` after `LUR1`, `D3-Z-SW` after `LUS1`, `N-LIVE`'s next run's
  liveness after a `K` run's `-E`, `LE-SW` after `D4`'s 1.4 arm), under `X-RA<n>` if its own
  cell already ran (its switch cell's text).
* **S3, a recovery firing at the fix** (`n_recov_fire` Δ ≥ 1 in a bracket at `txlen vendor`):
  not a stop — the pair is a reading. No cell re-arms before the reads (`F-99-R`, `F-S1`; in
  `I-D3` the trial's bracket), but the driver's own recovery re-arms the ring about 1 s after
  the stall, so the reads show the ring after it: the separate fault is named from `n_recov_*`,
  `recov_j_fire`, `recov_rc`, `cn` (the pair's `n` − `c`), `jfd` and `d4cover`'s low intervals,
  and `D4` takes its *named separate fault* branch.
* **S4, `P-SW2`'s `psrp3 … up 1` gate** (the link not back after the re-plug): the owner
  re-seats the cable once, by § 0 ⑩'s steps — the window `X-PLUG<n>` (`CW 100`, host only,
  beside the tail watch) started in the background and seen running before the owner is told to
  re-seat, with its deadline; then, after the hold, `X-SW2<n>` (`P-SW2`'s text, on its own
  line): `up 1` — the press continues `--from P-N2`; still not — every host arm is skipped, the
  board is read (`I-Z`: its page, the map, `n_writes`, the kernel log's windows, `port_status`
  last), and the owner is asked to power off.
* **`P-SW1`'s `psrp3 … up 0` gate** (the pull not seen): the owner is asked again, by § 0 ⑩'s
  steps, and the window started once more as `X-PULL<n>` (`CW 100`, beside the tail watch, with
  its deadline), then, after the hold, `X-SW1<n>` (`P-SW1`'s text, on its own line); `up 0` —
  `I-P2` continues `--from P-N1`; still up — arm P's out-state is unmeasured, the re-plug's
  invocations are not run, `I-C4` is next.
* **`P-D2`'s `masked … same yes` gate** (`PSRP3` after the re-plug is not its pre-pull word
  with bit 8 masked: the link renegotiated to another state): no cell runs until the owner has
  read it. **`P-H1`'s address gate**: `R0-ADDR`'s command as `X-ADDR<n>` beside the watch, then
  a line from `I-P3` `--from P-SWH1`, `--hold` first.
* **The board's watch's checks, `P-WT1` and `P-WT2`** (readings, each read before the owner is
  asked): `cut permit` — ask. `cut refuse since-max`, or `cutgate` refusing to decide — before
  asking, the board's watch is restarted on a line of its own (after the hold, *P-WT* under
  *The declared X-cells*): `X-PW<n>` (`P-W`'s text on its own log, `lpw<n>.log`), then
  `X-PWS<n>` (`P-WS`'s on that log, reading `LPW start rlx0 v 1 rc 0` before the pull, `v 0`
  before the re-plug), and its span is `X-PW<n>`'s own (P11). After a restart at `P-WT1`, the
  check before the re-plug is `X-PWT<n>` (`P-WT2`'s text on `X-PW<n>.meta.json`). After a
  restart before the re-plug, `L4` stops after `I-WLW` (the session runs it as a line through
  `I-WLW`), then `X-LWH<n>` (`cutgate wait` on `X-PW<n>.meta.json`, beside the tail watch)
  waits for the later watch, then a line from `I-P3B`, so `P-LW2`'s `wait` finds both ended;
  after it, `X-PLW<n>` (the later watch's log), and beside the watch `X-PLWR<n>` (`<seq>`
  `1,0,1` if restarted before the pull, `0,1` before the re-plug) and, after a restart before
  the re-plug, `X-PLWR<n>b` (`P-LW2`'s log, `1,0`). **`P-LWH`'s gate** (no `cutgate wait end`
  line: its metadata unreadable, or a wait over its `--max`): the session waits beside the tail
  watch until 605 s after `P-W.meta.json`'s `started_wallclock`, read by hand, then a line from
  `I-P3B`. **`P-LW2`'s `until`** with no loader text (the board's watch not yet ended): the
  hold (longer than the 20 s the board's watch can still need), then `X-PLW2<n>` (`P-LW2`'s
  text, on its own line) once; still not ended — P11's and P12's watch halves are unmeasured,
  and a line from `P-N3` (`I-P3B` `--from P-N3`).
* **② (`I-M`)**: a capture count that is not the plan's (`-C0`, `-C1`, readings) voids that
  series (`rttseries` voids it, never repaired). An on-series' `-X` gate (a `tcpdump` left
  running): `X-TK<n>` (the `-X` cell's text, beside the watch, reading `0`) once, then the
  invocation continues `--from` that series' `-P`, after the hold; still running — no cell
  until the owner has read it. A series pair's path gate is S1. **`N-LIVE`** `0`: `N1.pcap` is
  not running — `I-N0`'s transcript is read, it is started again once as `W-TCPN2`; `2` or
  more: another `tcpdump` runs, its owner stops it.
* **S6, the cut points** (`cutgate` 1.1, the catch window's start stamp from
  `R1-CATCH.meta.json`, the wall clock, the declared date). `CUT-4` (before `R6b-4`) refuses if
  the wall clock is past 23:05 on 2026-09-27 or more than 44 minutes have passed since the
  catch window opened — the planner's two rules of 2026-09-26, the first as it was: a block
  started at 23:05 ends by about 23:45, before 23:52 (the declared date's captures, `capdate`).
  The second was the planner's guess of 35 minutes, paired with the evening's 23:05 when the
  owner chose two presses on 2026-09-26 (`LOG.md`'s 113th segment records press B then at about
  71 minutes, a guess made before this card was sized; `arith43b.out`'s `CUT4` line and a
  cardnum row). It guards no reading — `D4`'s criterion and `NET-76`'s reads depend on no boot
  age, and every `R6b-4` arm re-arms its ring before its first read — only the press's length,
  so it is derived from that: the 85 minutes the owner accepted for this press on 2026-09-27,
  less the `R6b-4` block (`I-Z` included) at the estimate, floored — 44 (`arith43b.out`'s
  `TIME since-max-4` line); a press whose block starts by then ends within 85 minutes at the
  estimate, and a daytime catch is cut by it only when the press itself runs long, as the
  planner meant. The estimate reaches it at about 38.3 minutes, 5.7 inside the rule. Every
  other cut point refuses if now plus its block's and its later higher-priority blocks' minutes
  — the estimate's, rounded down, plus 2: nominal plus a margin, not a worst case — passes
  23:52 on 2026-09-27: `CUT-N` 19 (`NET-131`, ②, arm P, `I-Z`), `CUT-M` 15, `CUT-P` 12, `CUT-T`
  11 (the tail at `timeout 340`, the 1.4 arm, `I-Z`), `CUT-L` 5. A refusal — `cut refuse …`, or
  `cutgate` refusing to decide (exit 2: a bad date, the catch on another day) — stops its
  invocation, which ends its command line, and skips its block: `CUT-N` → `I-N0`, `I-N`,
  `I-N9`; `CUT-M` → `I-M`; `CUT-P` → `I-P1` … `I-P3B`; `CUT-4` → `I-4F` … `I-4L9`; `CUT-T` →
  `I-4T`, `I-WT`, `I-4T9`; `CUT-L` → `I-4L`, `I-WL`, `I-4L9` (P13's 1.4 half then rests on P6's
  fallback, labelled a different-stimulus control). The session starts the next command line
  from the invocation after the skipped block, its first steps `--hold` (a refusal is a stop)
  and `--stop` of the running watch. The cut order this implements, first cut to last: the TCP
  tail, `D4`'s 1.4 arm, the `R6b-4` block, `NET-131`, ②, arm P; `D3` and its control are never
  cut. Why 23:52: every capture of the press stays on the declared date with minutes to spare
  (`tools/capdate.py` checks `bench/<date>/` against the captures' day).
* **S7, `NET-76`'s reads**: `N76-A`, `N76-PL` and `N76-W` are readings; a failed one is the
  reading itself and never starts S1 — the whole `N76-*` set runs first, then `I-CT`, and
  `I-4T` re-arms at the fix (`T-SW`) before its liveness gate `T-L`; a `T-L` failing after that
  re-arm is S1, as at any liveness gate, and `NET-76`'s reads already hold what the flood left.
* **A board bracket's gate** (`until`, `version`, `tx15`, `nd_up`) with no loader text: block
  48's rule after the hold — `/dev/ttyUSB0` checked, the read typed again as its stand-in
  `X-<read>`, and, if it passes, it stands in and the invocation continues `--from` the next
  cell. A `tx15` that is not the arm's policy at an arm's first read (`D3-00-R`, `D3-X-00-R`,
  `D3-Y-00-R`, `K…-R0`, `M2F-00-R`, `F-00-R`, `T-00-R`, `L-00-R`, `LE-00-R`): the switch cell
  typed again once as `X-RA<n>`, then the read as `X-<read>`, on one line; a second mismatch
  voids that arm, and the invocation continues `--from` the cell after its last (`D3-00-R` →
  `D3-X-SW`, the trials at the fix unmeasured; `D3-X-00-R` → `D3-Y-SW`; `D3-Y-00-R` →
  `D3-Z-SW`; a `K` run → the next run's liveness; `M2F-00-R`, `F-00-R`, `T-00-R`, `LE-00-R` →
  the invocation's end; `L-00-R` → `LE-SW`); a second arm voided on this press: no cell runs
  until the owner has read the page. At any later read of an arm no policy verb has been typed
  since a read that matched: no cell runs until the owner has read it. **If a read returns
  nothing, garbage, or never ends on the prompt, the owner is told to power off.**
* **A trial's `-S0` `ps` gate**: after the hold, block 48's declared `X-<t>-S0R`, once; if the
  server still does not run, that trial is not run (recorded as not run: its watched invocation
  is skipped) and the press continues `--from` the cell after the trial's last cell; a second
  trial not run: `D3`'s invocations end there and the press continues with `I-CN`. `T-S0` the
  same, and the tail's invocations end (`I-CT`'s block, then `I-CL`).
* **WSL itself stops mid-press**: the console is unwatched from that moment until a watch runs
  again (§ 0 ⑥), so, in this order: the keeper; `usbipd list` read fresh and each device no
  longer attached attached again, the CP2102 first, the GbE adapter as S1's `X-RE<n>`;
  `X-PRE<n>` (the throwaway capture a re-attach needs, the board on) and then a watch at once,
  on one line (*The declared X-cells*); the follower with `>>`; the bracket spanning the outage
  void, and the anchor of any capture running.
* **A host stimulus, a host reading, a capture stop, an `iperf3` trial, the flood**: `NAME?`;
  never a stop. **A background cell's exit** never stops a run.
* **A cable action after its window** (the owner reports acting after the stated deadline, or
  the window's `CW` lines record no carrier change while the next switch page shows one): the
  window is read as having recorded no action, and P11's carrier-watcher half for that action
  is unmeasured; the next read's gate decides as written — `P-SW1` `up 1` is *the pull not
  seen* and `P-SW2` `up 0` is S4, each asked again by § 0 ⑩'s five steps — and a page that
  shows the action stands, with the reads after it the arm's. A late action the owner reports
  made while a board read ran voids that invocation's reads from that read on, and no cell runs
  until the owner has read it. Past a stated deadline the owner does not act on the old "now"
  and says so; the session asks again.
* **Anything not listed**: no cell runs until the owner has read it; the decision goes into
  `bench/2026-09-27b/CORRECTIONS-block50.md` first.

**The declared X-cells, whole.** Each X-cell a rule above names runs as
`bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x NAME "TEXT"` with the text below,
so its `XCELL NAME rc=N` line reaches `/home/key/fwre-work/rebuild/s113/run43b/rc.tsv`: a board
X-cell's text is its model cell's — the same send, `--until` and cap, the loader's banner in
its `--until` (the generator refuses one without; the `xcells-*` rows count 26 board X-cell
lines and 18 host ones, `X-PRE<n>` among the first) — with its own `--out`. `<n>` is the next
unused number of that name and `<k>` the running watch's. A line that types a board X-cell is
one command line, started in the background: `--hold` (*The hold after a stop*), then `--stop`
of the running watch, the X-cells chained with `&&`, and `;` and the next watch, which runs
however the line ended; the wrapper exits 5 when a board X-cell's capture holds the loader's
text, so the chain stops there as the loader gate stops an invocation, and the watch follows. A
host X-cell runs alone, beside the running watch, and is read before the next line. At the
loader's prompt no line has `--hold` or `--stop` (*The watch*). Placeholders: `<txlen>` the
arm's policy (`vendor` or `rlxfw`); `<t>` the trial's lower-case name (`tr1`); `<read>` a
bracket read; `<page>` a switch page's cell; `<p>` a port-3 gate's arm (`D3`, `K1-0061`, `M2F`,
…); `<PREV>` and `<PREVH>` S1's; `<busid>` the GbE adapter's, from `X-REL<n>`; `<seq>` P11's
sequence; `<invocation> <tag> --from <cell>` the continuation, then the invocations after it in
its line.

*S1, `follower` alone: the liveness again, beside the watch*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-L<n> "FL 10.1.1.3 ; PL ; DMW none"
```

*S1's read set, before anything on the host is touched; then its classifier*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-SW<n> "CAP --out bench/2026-09-27b/X-SW<n> --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-NIC<n> "CAP --out bench/2026-09-27b/X-NIC<n> --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-HP<n> "HP" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-BR<n> "CAP --out bench/2026-09-27b/X-BR<n> --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PS<n> "CAP --out bench/2026-09-27b/X-PS<n> --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-HN<n> "HN" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-C<n> "S1C --nic bench/2026-09-27b/X-NIC<n>.log --br bench/2026-09-27b/X-BR<n>.log --prev-br <PREV> --pre bench/2026-09-27b/X-HP<n>.log --host <PREVH>"
```

*S1's branch a: the driver page after at least 3 s, the liveness beside the watch, then (if it
passes) the arm's re-arm and the continuation*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-NIC<n>a "CAP --out bench/2026-09-27b/X-NIC<n>a --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-L<n>a "FL 10.1.1.3 ; PL ; DMW none"

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-RA<n>a "CAP --out bench/2026-09-27b/X-RA<n>a --send 'ifconfig rlx0 down ; echo txlen <txlen> > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh <invocation> <tag> --from <cell> \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*S1's branch b (or branch a's `X-L<n>a` failing): the PHY read, the re-attach beside the watch,
the reads after it, the liveness, then (if it passes) the continuation*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PHY<n> "CAP --out bench/2026-09-27b/X-PHY<n> --send 'echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-REL<n> "usbipd.exe list"
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-RE<n> "usbipd.exe detach --busid <busid> ; usbipd.exe attach --wsl --busid <busid>"
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-REA<n> "sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9"

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-SW<n>b "CAP --out bench/2026-09-27b/X-SW<n>b --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PS<n>b "CAP --out bench/2026-09-27b/X-PS<n>b --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-TC<n> "pgrep -xc tcpdump ; true"
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-L<n>b "FL 10.1.1.3 ; PL ; DMW none"

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh <invocation> <tag> --from <cell> \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*S2: a 1.4 arm's end re-arm typed again (its switch cell's text), then the continuation*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-RA<n> "CAP --out bench/2026-09-27b/X-RA<n> --send 'ifconfig rlx0 down ; echo txlen <txlen> > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh <invocation> <tag> --from <cell> \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*S5: the driver page after `linkprobe`'s failure, then the continuation; at `P-WS`, the board's
watch started again with `P-W`'s own text and read with `P-WS`'s*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-RT<n> "CAP --out bench/2026-09-27b/X-RT<n> --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh <invocation> <tag> --from <cell> \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PWR<n> "CAP --out bench/2026-09-27b/X-PWR<n> --send 'cd /tmp && linkprobe watch rlx0 10 600 > lpw.log 2>&1 &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PWRS<n> "CAP --out bench/2026-09-27b/X-PWRS<n> --send 'sleep 1 ; cat /tmp/lpw.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*S4: the re-seat's window beside the watch, then `P-SW2`'s read again*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PLUG<n> "CW 100"

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-SW2<n> "CAP --out bench/2026-09-27b/X-SW2<n> --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*`P-SW1`'s gate: the pull's window again beside the watch, then `P-SW1`'s read again*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PULL<n> "CW 100"

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-SW1<n> "CAP --out bench/2026-09-27b/X-SW1<n> --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*`P-H1`'s address gate: `R0-ADDR`'s command beside the watch*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-ADDR<n> "sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9"
```

*`P-WT1`'s or `P-WT2`'s restart: the board's watch started again on its own log, its check, the
host's wait for it, its read*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PW<n> "CAP --out bench/2026-09-27b/X-PW<n> --send 'cd /tmp && linkprobe watch rlx0 10 600 > lpw<n>.log 2>&1 &' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PWS<n> "CAP --out bench/2026-09-27b/X-PWS<n> --send 'sleep 1 ; cat /tmp/lpw<n>.log' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PWT<n> "CUT --catch bench/2026-09-27b/X-PW<n>.meta.json --date 2026-09-27 --since-max 5.66"
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-LWH<n> "CUTW --catch bench/2026-09-27b/X-PW<n>.meta.json --after 605 --max 605"

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PLW<n> "CAP --out bench/2026-09-27b/X-PLW<n> --send 'cat /tmp/lpw<n>.log' --until 'LPW end n [0-9]+ .*trans [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 20" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PLWR<n> "LPR watch bench/2026-09-27b/X-PLW<n>.log --ms 10 --s 600 --expect-seq <seq>"
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PLWR<n>b "LPR watch bench/2026-09-27b/P-LW2.log --ms 10 --s 600 --expect-seq 1,0"
```

*`P-LW2`'s `until` with no loader text: its read again*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PLW2<n> "CAP --out bench/2026-09-27b/X-PLW2<n> --send 'wait ; cat /tmp/lpw.log' --until 'LPW end n [0-9]+ .*trans [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 20" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*②'s `-X` gate: the capture stopped again, beside the watch*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-TK<n> "sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true"
```

*a bracket's gate: its stand-in; at an arm's first read with `tx15` not the arm's policy, the
arm's switch cell again, then the stand-in*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-<read> "CAP --out bench/2026-09-27b/X-<read> --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>

bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-RA<n> "CAP --out bench/2026-09-27b/X-RA<n> --send 'ifconfig rlx0 down ; echo txlen <txlen> > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-<read> "CAP --out bench/2026-09-27b/X-<read> --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*another switch page's gate: the page again*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-<page> "CAP --out bench/2026-09-27b/X-<page> --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*a port-3 gate that ended silent (no `PSRP3` row, or no port-3 line of `port_status`): its
stand-in*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-<p>-LS "CAP --out bench/2026-09-27b/X-<p>-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*a trial's `-S0` `ps` gate: block 48's declared restart of the one-off server*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --hold \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --stop X-W<k> \
  && bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-<t>-S0R "CAP --out bench/2026-09-27b/X-<t>-S0R --send 'busybox killall iperf3 ; sleep 1 ; iperf3 -s -1 -f k --logfile /tmp/<t>.log > /dev/null 2>&1 & sleep 2 ; ps' --idle 6 --until 'Booting\.\.\.|---RealTek' --seconds 30" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k+1>
```

*WSL restarted mid-press, the board on: the throwaway capture a re-attach needs, then a watch
at once*:

```sh
bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-PRE<n> "CAP --out bench/2026-09-27b/X-PRE<n> --until 'Booting\.\.\.|---RealTek' --seconds 3" \
  ; bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --tail X-W<k>
```

---

## § 7 What this block does not establish

* **`D3` on the image block 48 booted.** This is boot 2 of driver 1.5 at `txlen vendor` on a
  different image (§ 0 ②); an effect of switch driver 1.2's extra `PSRP` reads, or of the
  initramfs's two files, on the trials is not separated from the fix.
* **The ring state at a stall at the fix**: the driver's own recovery (`recov_mode 1`,
  `recov_ms` 1000, not changed for this press) re-arms the ring about 1 s after a stall, so no
  read here sees the stalled ring; a separate fault is named from what the recovery counters
  kept (P13).
* **`NET-68` 殘留 beyond P16's reading**: whether a recovery persists at the fix, where none is
  predicted; and each 1.4 recovery's time against the load's answered pings (the loop's log has
  no time stamps; the counter log is 10-s coarse).
* **The fix over time beyond one flood.** `D4`'s run is 31 minutes of `ping -f` at 1,442 B
  beside a loop of single echoes at every length, and 5 minutes of TCP; not the twelve trials'
  shapes for 30 minutes, not UDP at load, not a second boot.
* **That the flood's frames cover every formerly bad length at load**: the loop sends each
  length one echo at a time beside the flood; `d4cover` says each was sent, not that the ring
  ever held two bad frames in a row.
* **Why the UDP datagrams die** beyond P8's queue: whether the application reads too slowly
  (CPU) is not separated from the buffer's size (`NET-117` 殘留 ③ is not run), and whether the
  host's `Sent` is short because the client under `qemu` under-counts (① is not run).
* **`NET-131`'s cause** unless a run falls in branch (b) (P9); and which frame of a bracket the
  CPU port refused beyond the counts and the capture (推 by elimination).
* **The capture's effect** on `eth4` and at 1.4 (card A), or its mechanism. **If card A is
  skipped or voided**, this card's twelve series still read the capture's effect on `rlx0` at
  the fix within this boot, but `D3-MISS` ②'s decision needs, in the `D3-MISS` row's words
  (`PROGRESS.md`), "vendor series in the same seating — the vendor's driver, `eth4`, on the
  same boot", so ② stays open and the series are a reading; `rttseries` is pinned by digest
  either way, and the card-A rows read card A's tracked, frozen card.
* **Containment of every reset**: (1)–(4) of § 0 ⑥'s *what this does not cover* — a reset from
  another cause inside a board cell, a death in the last seconds before a watch's stop where no
  stop came first (the hold covers the rest), a timer wheel stopped while the console answers,
  WSL down — and a press made after its stated deadline, which the catch may not catch.
* **The console's load during the watched windows**: about 100 ESC a second into the board's
  UART through every trial, the flood, the tail and the 1.4 load (§ 0 ⑤), and none of it
  separated from what those measure (推 immaterial to the TX path).
* **The series' spacing by state**: an on-series carries `-T` and `-X` (the capture's start,
  its `pkill … && sleep 1`) that an off-series lacks, so the time between series differs by a
  few seconds by state (card A's cells, inherited); ABBA balances a drift linear in time, not
  that.
* **`get_link` naming port 3**: it is *any of jacks 0–4 up*; arm P moves the one cable, so the
  flip is port 3's here and nowhere else.
* **`MT-PORT`'s source outliving `R6b-8`**: shown only by `mfginject`'s fixture until `R6b-8`
  boots an image without the vendor tree; the label names who reported the link, not who
  configured the PHY.
* **`lde` against the vendor's reads**: the vendor's `port_status` (read last, and never
  between an action and rlxfw's first read) and any vendor-internal `PSRP` read consume bit 8
  unrecorded; `lde` is a lower bound.
* **`NET-30` 殘留's full experiment**: the reads after `IPCONFIG` and after the upload are not
  taken; `SW7` spans them with the kernel's early boot. Block 24's own event stays
  unattributed.
* **B1** (a PHY autonegotiation restart): dropped by the owner's ruling for want of a second
  source for `BMCR` bit 9; **H3** (the re-attach as a link event) is `R6b-3`'s card's reading.
* **The host adapter's own drops** (`r8153_ecm` has no tally counters), and the carrier
  watcher's view of them.
* **The watch's period**: `LPW t` stamps are 10–20 ms apart at best (`HZ` 100, 推); a flap
  shorter than a poll is seen by `lde`, not by the watch.
* A flash write by anything but rlxfw's SPI driver between the two maps that the map does not
  see (`FLS-30`'s limits); `H601`'s 8,192 B are never hashed; `n_writes` carries no information
  about writes (`FW-142`).

---

```cells
bench/2026-09-27b/R0-PRE
bench/2026-09-27b/R0-PREC
bench/2026-09-27b/R0-ADDR
bench/2026-09-27b/R0-ETH
bench/2026-09-27b/R0-CW
bench/2026-09-27b/R0-TCPC
bench/2026-09-27b/R0-DMSG
bench/2026-09-27b/R0-DW0
bench/2026-09-27b/R0-FL
bench/2026-09-27b/R0-PCAP
bench/2026-09-27b/R0-IPF
bench/2026-09-27b/R0-SUM
bench/2026-09-27b/R0-ST
bench/2026-09-27b/R0-VERB
bench/2026-09-27b/R0-H
bench/2026-09-27b/R1-CATCH
bench/2026-09-27b/R1-DW
bench/2026-09-27b/R1-FL
bench/2026-09-27b/R1Q
bench/2026-09-27b/R1-PS
bench/2026-09-27b/R1-SW7
bench/2026-09-27b/R1-M0
bench/2026-09-27b/R1-MB0
bench/2026-09-27b/R1-NW0
bench/2026-09-27b/B-SW
bench/2026-09-27b/B-00-P
bench/2026-09-27b/B-00-R
bench/2026-09-27b/B-00-H
bench/2026-09-27b/B-00-T
bench/2026-09-27b/B-RMEM
bench/2026-09-27b/B-SWP
bench/2026-09-27b/LP-SW0
bench/2026-09-27b/LP-N0
bench/2026-09-27b/LP-G
bench/2026-09-27b/LP-N1
bench/2026-09-27b/LP-SW1
bench/2026-09-27b/AN-SW2
bench/2026-09-27b/LP-LR
bench/2026-09-27b/LP-DS
bench/2026-09-27b/AN-D
bench/2026-09-27b/D3-SW
bench/2026-09-27b/D3-LS
bench/2026-09-27b/D3-L
bench/2026-09-27b/D3-00-P
bench/2026-09-27b/D3-00-R
bench/2026-09-27b/D3-00-H
bench/2026-09-27b/D3-TR1-L
bench/2026-09-27b/D3-TR1-S0
bench/2026-09-27b/D3-TR1
bench/2026-09-27b/D3-TR1-S1
bench/2026-09-27b/D3-TR1-P
bench/2026-09-27b/D3-TR1-R
bench/2026-09-27b/D3-TR1-H
bench/2026-09-27b/D3-TR1-D
bench/2026-09-27b/D3-TR1-IL
bench/2026-09-27b/D3-TR1-SN
bench/2026-09-27b/D3-TR1-IC
bench/2026-09-27b/D3-TR2-L
bench/2026-09-27b/D3-TR2-S0
bench/2026-09-27b/D3-TR2
bench/2026-09-27b/D3-TR2-S1
bench/2026-09-27b/D3-TR2-P
bench/2026-09-27b/D3-TR2-R
bench/2026-09-27b/D3-TR2-H
bench/2026-09-27b/D3-TR2-D
bench/2026-09-27b/D3-TR2-IL
bench/2026-09-27b/D3-TR2-SN
bench/2026-09-27b/D3-TR2-IC
bench/2026-09-27b/D3-TR3-L
bench/2026-09-27b/D3-TR3-S0
bench/2026-09-27b/D3-TR3
bench/2026-09-27b/D3-TR3-S1
bench/2026-09-27b/D3-TR3-P
bench/2026-09-27b/D3-TR3-R
bench/2026-09-27b/D3-TR3-H
bench/2026-09-27b/D3-TR3-D
bench/2026-09-27b/D3-TR3-IL
bench/2026-09-27b/D3-TR3-SN
bench/2026-09-27b/D3-TR3-IC
bench/2026-09-27b/D3-TS1-L
bench/2026-09-27b/D3-TS1-S0
bench/2026-09-27b/D3-TS1
bench/2026-09-27b/D3-TS1-S1
bench/2026-09-27b/D3-TS1-P
bench/2026-09-27b/D3-TS1-R
bench/2026-09-27b/D3-TS1-H
bench/2026-09-27b/D3-TS1-D
bench/2026-09-27b/D3-TS1-IL
bench/2026-09-27b/D3-TS1-SN
bench/2026-09-27b/D3-TS2-L
bench/2026-09-27b/D3-TS2-S0
bench/2026-09-27b/D3-TS2
bench/2026-09-27b/D3-TS2-S1
bench/2026-09-27b/D3-TS2-P
bench/2026-09-27b/D3-TS2-R
bench/2026-09-27b/D3-TS2-H
bench/2026-09-27b/D3-TS2-D
bench/2026-09-27b/D3-TS2-IL
bench/2026-09-27b/D3-TS2-SN
bench/2026-09-27b/D3-TS3-L
bench/2026-09-27b/D3-TS3-S0
bench/2026-09-27b/D3-TS3
bench/2026-09-27b/D3-TS3-S1
bench/2026-09-27b/D3-TS3-P
bench/2026-09-27b/D3-TS3-R
bench/2026-09-27b/D3-TS3-H
bench/2026-09-27b/D3-TS3-D
bench/2026-09-27b/D3-TS3-IL
bench/2026-09-27b/D3-TS3-SN
bench/2026-09-27b/D3-UR1-L
bench/2026-09-27b/D3-UR1-Q
bench/2026-09-27b/D3-UR1-S0
bench/2026-09-27b/D3-UR1
bench/2026-09-27b/D3-UR1-S1
bench/2026-09-27b/D3-UR1-P
bench/2026-09-27b/D3-UR1-R
bench/2026-09-27b/D3-UR1-H
bench/2026-09-27b/D3-UR1-D
bench/2026-09-27b/D3-UR1-IL
bench/2026-09-27b/D3-UR1-SN
bench/2026-09-27b/D3-UR1-IC
bench/2026-09-27b/D3-UR1-UQ
bench/2026-09-27b/D3-UR2-L
bench/2026-09-27b/D3-UR2-Q
bench/2026-09-27b/D3-UR2-S0
bench/2026-09-27b/D3-UR2
bench/2026-09-27b/D3-UR2-S1
bench/2026-09-27b/D3-UR2-P
bench/2026-09-27b/D3-UR2-R
bench/2026-09-27b/D3-UR2-H
bench/2026-09-27b/D3-UR2-D
bench/2026-09-27b/D3-UR2-IL
bench/2026-09-27b/D3-UR2-SN
bench/2026-09-27b/D3-UR2-IC
bench/2026-09-27b/D3-UR2-UQ
bench/2026-09-27b/D3-UR3-L
bench/2026-09-27b/D3-UR3-Q
bench/2026-09-27b/D3-UR3-S0
bench/2026-09-27b/D3-UR3
bench/2026-09-27b/D3-UR3-S1
bench/2026-09-27b/D3-UR3-P
bench/2026-09-27b/D3-UR3-R
bench/2026-09-27b/D3-UR3-H
bench/2026-09-27b/D3-UR3-D
bench/2026-09-27b/D3-UR3-IL
bench/2026-09-27b/D3-UR3-SN
bench/2026-09-27b/D3-UR3-IC
bench/2026-09-27b/D3-UR3-UQ
bench/2026-09-27b/D3-US1-L
bench/2026-09-27b/D3-US1-S0
bench/2026-09-27b/D3-US1
bench/2026-09-27b/D3-US1-S1
bench/2026-09-27b/D3-US1-P
bench/2026-09-27b/D3-US1-R
bench/2026-09-27b/D3-US1-H
bench/2026-09-27b/D3-US1-D
bench/2026-09-27b/D3-US1-IL
bench/2026-09-27b/D3-US1-SN
bench/2026-09-27b/D3-US2-L
bench/2026-09-27b/D3-US2-S0
bench/2026-09-27b/D3-US2
bench/2026-09-27b/D3-US2-S1
bench/2026-09-27b/D3-US2-P
bench/2026-09-27b/D3-US2-R
bench/2026-09-27b/D3-US2-H
bench/2026-09-27b/D3-US2-D
bench/2026-09-27b/D3-US2-IL
bench/2026-09-27b/D3-US2-SN
bench/2026-09-27b/D3-US3-L
bench/2026-09-27b/D3-US3-S0
bench/2026-09-27b/D3-US3
bench/2026-09-27b/D3-US3-S1
bench/2026-09-27b/D3-US3-P
bench/2026-09-27b/D3-US3-R
bench/2026-09-27b/D3-US3-H
bench/2026-09-27b/D3-US3-D
bench/2026-09-27b/D3-US3-IL
bench/2026-09-27b/D3-US3-SN
bench/2026-09-27b/D3-X-SW
bench/2026-09-27b/D3-X-LS
bench/2026-09-27b/D3-X-L
bench/2026-09-27b/D3-X-00-P
bench/2026-09-27b/D3-X-00-R
bench/2026-09-27b/D3-X-00-H
bench/2026-09-27b/D3-LUR1-L
bench/2026-09-27b/D3-LUR1-Q
bench/2026-09-27b/D3-LUR1-S0
bench/2026-09-27b/D3-LUR1
bench/2026-09-27b/D3-LUR1-S1
bench/2026-09-27b/D3-LUR1-P
bench/2026-09-27b/D3-LUR1-R
bench/2026-09-27b/D3-LUR1-H
bench/2026-09-27b/D3-LUR1-D
bench/2026-09-27b/D3-LUR1-IL
bench/2026-09-27b/D3-LUR1-SN
bench/2026-09-27b/D3-LUR1-UQ
bench/2026-09-27b/D3-Y-SW
bench/2026-09-27b/D3-Y-LS
bench/2026-09-27b/D3-Y-L
bench/2026-09-27b/D3-Y-00-P
bench/2026-09-27b/D3-Y-00-R
bench/2026-09-27b/D3-Y-00-H
bench/2026-09-27b/D3-LUS1-L
bench/2026-09-27b/D3-LUS1-S0
bench/2026-09-27b/D3-LUS1
bench/2026-09-27b/D3-LUS1-S1
bench/2026-09-27b/D3-LUS1-P
bench/2026-09-27b/D3-LUS1-R
bench/2026-09-27b/D3-LUS1-H
bench/2026-09-27b/D3-LUS1-D
bench/2026-09-27b/D3-LUS1-IL
bench/2026-09-27b/D3-LUS1-SN
bench/2026-09-27b/D3-Z-SW
bench/2026-09-27b/D3-Z-LS
bench/2026-09-27b/D3-SUM
bench/2026-09-27b/CUT-N
bench/2026-09-27b/W-TCPN
bench/2026-09-27b/N-LIVE
bench/2026-09-27b/K1-0061-L
bench/2026-09-27b/K1-0061-SW
bench/2026-09-27b/K1-0061-LS
bench/2026-09-27b/K1-0061-P0
bench/2026-09-27b/K1-0061-R0
bench/2026-09-27b/K1-0061-H0
bench/2026-09-27b/K1-0061-PG
bench/2026-09-27b/K1-0061-P1
bench/2026-09-27b/K1-0061-R1
bench/2026-09-27b/K1-0061-H1
bench/2026-09-27b/K1-0061-D
bench/2026-09-27b/K1-0061-E
bench/2026-09-27b/K2-0062-L
bench/2026-09-27b/K2-0062-SW
bench/2026-09-27b/K2-0062-LS
bench/2026-09-27b/K2-0062-P0
bench/2026-09-27b/K2-0062-R0
bench/2026-09-27b/K2-0062-H0
bench/2026-09-27b/K2-0062-PG
bench/2026-09-27b/K2-0062-P1
bench/2026-09-27b/K2-0062-R1
bench/2026-09-27b/K2-0062-H1
bench/2026-09-27b/K2-0062-D
bench/2026-09-27b/K2-0062-E
bench/2026-09-27b/K3-0063-L
bench/2026-09-27b/K3-0063-SW
bench/2026-09-27b/K3-0063-LS
bench/2026-09-27b/K3-0063-P0
bench/2026-09-27b/K3-0063-R0
bench/2026-09-27b/K3-0063-H0
bench/2026-09-27b/K3-0063-PG
bench/2026-09-27b/K3-0063-P1
bench/2026-09-27b/K3-0063-R1
bench/2026-09-27b/K3-0063-H1
bench/2026-09-27b/K3-0063-D
bench/2026-09-27b/K3-0063-E
bench/2026-09-27b/K4-0061-L
bench/2026-09-27b/K4-0061-SW
bench/2026-09-27b/K4-0061-LS
bench/2026-09-27b/K4-0061-P0
bench/2026-09-27b/K4-0061-R0
bench/2026-09-27b/K4-0061-H0
bench/2026-09-27b/K4-0061-PG
bench/2026-09-27b/K4-0061-P1
bench/2026-09-27b/K4-0061-R1
bench/2026-09-27b/K4-0061-H1
bench/2026-09-27b/K4-0061-D
bench/2026-09-27b/K4-0061-E
bench/2026-09-27b/K5-0062-L
bench/2026-09-27b/K5-0062-SW
bench/2026-09-27b/K5-0062-LS
bench/2026-09-27b/K5-0062-P0
bench/2026-09-27b/K5-0062-R0
bench/2026-09-27b/K5-0062-H0
bench/2026-09-27b/K5-0062-PG
bench/2026-09-27b/K5-0062-P1
bench/2026-09-27b/K5-0062-R1
bench/2026-09-27b/K5-0062-H1
bench/2026-09-27b/K5-0062-D
bench/2026-09-27b/K5-0062-E
bench/2026-09-27b/K6-0063-L
bench/2026-09-27b/K6-0063-SW
bench/2026-09-27b/K6-0063-LS
bench/2026-09-27b/K6-0063-P0
bench/2026-09-27b/K6-0063-R0
bench/2026-09-27b/K6-0063-H0
bench/2026-09-27b/K6-0063-PG
bench/2026-09-27b/K6-0063-P1
bench/2026-09-27b/K6-0063-R1
bench/2026-09-27b/K6-0063-H1
bench/2026-09-27b/K6-0063-D
bench/2026-09-27b/K6-0063-E
bench/2026-09-27b/W-TCPNX
bench/2026-09-27b/W-NWALL
bench/2026-09-27b/W-NORD
bench/2026-09-27b/CUT-M
bench/2026-09-27b/M2F-SW
bench/2026-09-27b/M2F-LS
bench/2026-09-27b/M2F-L
bench/2026-09-27b/M2F-00-P
bench/2026-09-27b/M2F-00-R
bench/2026-09-27b/M2F-00-H
bench/2026-09-27b/M2F-S01-L
bench/2026-09-27b/M2F-S01-C0
bench/2026-09-27b/M2F-S01
bench/2026-09-27b/M2F-S01-C1
bench/2026-09-27b/M2F-S01-P
bench/2026-09-27b/M2F-S01-R
bench/2026-09-27b/M2F-S01-H
bench/2026-09-27b/M2F-S01-D
bench/2026-09-27b/M2F-S02-L
bench/2026-09-27b/M2F-S02-T
bench/2026-09-27b/M2F-S02-C0
bench/2026-09-27b/M2F-S02
bench/2026-09-27b/M2F-S02-C1
bench/2026-09-27b/M2F-S02-X
bench/2026-09-27b/M2F-S02-P
bench/2026-09-27b/M2F-S02-R
bench/2026-09-27b/M2F-S02-H
bench/2026-09-27b/M2F-S02-D
bench/2026-09-27b/M2F-S03-L
bench/2026-09-27b/M2F-S03-T
bench/2026-09-27b/M2F-S03-C0
bench/2026-09-27b/M2F-S03
bench/2026-09-27b/M2F-S03-C1
bench/2026-09-27b/M2F-S03-X
bench/2026-09-27b/M2F-S03-P
bench/2026-09-27b/M2F-S03-R
bench/2026-09-27b/M2F-S03-H
bench/2026-09-27b/M2F-S03-D
bench/2026-09-27b/M2F-S04-L
bench/2026-09-27b/M2F-S04-C0
bench/2026-09-27b/M2F-S04
bench/2026-09-27b/M2F-S04-C1
bench/2026-09-27b/M2F-S04-P
bench/2026-09-27b/M2F-S04-R
bench/2026-09-27b/M2F-S04-H
bench/2026-09-27b/M2F-S04-D
bench/2026-09-27b/M2F-S05-L
bench/2026-09-27b/M2F-S05-C0
bench/2026-09-27b/M2F-S05
bench/2026-09-27b/M2F-S05-C1
bench/2026-09-27b/M2F-S05-P
bench/2026-09-27b/M2F-S05-R
bench/2026-09-27b/M2F-S05-H
bench/2026-09-27b/M2F-S05-D
bench/2026-09-27b/M2F-S06-L
bench/2026-09-27b/M2F-S06-T
bench/2026-09-27b/M2F-S06-C0
bench/2026-09-27b/M2F-S06
bench/2026-09-27b/M2F-S06-C1
bench/2026-09-27b/M2F-S06-X
bench/2026-09-27b/M2F-S06-P
bench/2026-09-27b/M2F-S06-R
bench/2026-09-27b/M2F-S06-H
bench/2026-09-27b/M2F-S06-D
bench/2026-09-27b/M2F-S07-L
bench/2026-09-27b/M2F-S07-T
bench/2026-09-27b/M2F-S07-C0
bench/2026-09-27b/M2F-S07
bench/2026-09-27b/M2F-S07-C1
bench/2026-09-27b/M2F-S07-X
bench/2026-09-27b/M2F-S07-P
bench/2026-09-27b/M2F-S07-R
bench/2026-09-27b/M2F-S07-H
bench/2026-09-27b/M2F-S07-D
bench/2026-09-27b/M2F-S08-L
bench/2026-09-27b/M2F-S08-C0
bench/2026-09-27b/M2F-S08
bench/2026-09-27b/M2F-S08-C1
bench/2026-09-27b/M2F-S08-P
bench/2026-09-27b/M2F-S08-R
bench/2026-09-27b/M2F-S08-H
bench/2026-09-27b/M2F-S08-D
bench/2026-09-27b/M2F-S09-L
bench/2026-09-27b/M2F-S09-C0
bench/2026-09-27b/M2F-S09
bench/2026-09-27b/M2F-S09-C1
bench/2026-09-27b/M2F-S09-P
bench/2026-09-27b/M2F-S09-R
bench/2026-09-27b/M2F-S09-H
bench/2026-09-27b/M2F-S09-D
bench/2026-09-27b/M2F-S10-L
bench/2026-09-27b/M2F-S10-T
bench/2026-09-27b/M2F-S10-C0
bench/2026-09-27b/M2F-S10
bench/2026-09-27b/M2F-S10-C1
bench/2026-09-27b/M2F-S10-X
bench/2026-09-27b/M2F-S10-P
bench/2026-09-27b/M2F-S10-R
bench/2026-09-27b/M2F-S10-H
bench/2026-09-27b/M2F-S10-D
bench/2026-09-27b/M2F-S11-L
bench/2026-09-27b/M2F-S11-T
bench/2026-09-27b/M2F-S11-C0
bench/2026-09-27b/M2F-S11
bench/2026-09-27b/M2F-S11-C1
bench/2026-09-27b/M2F-S11-X
bench/2026-09-27b/M2F-S11-P
bench/2026-09-27b/M2F-S11-R
bench/2026-09-27b/M2F-S11-H
bench/2026-09-27b/M2F-S11-D
bench/2026-09-27b/M2F-S12-L
bench/2026-09-27b/M2F-S12-C0
bench/2026-09-27b/M2F-S12
bench/2026-09-27b/M2F-S12-C1
bench/2026-09-27b/M2F-S12-P
bench/2026-09-27b/M2F-S12-R
bench/2026-09-27b/M2F-S12-H
bench/2026-09-27b/M2F-S12-D
bench/2026-09-27b/M2F-RTT
bench/2026-09-27b/CUT-P
bench/2026-09-27b/P-SW0
bench/2026-09-27b/P-N0
bench/2026-09-27b/P-LG0
bench/2026-09-27b/P-W
bench/2026-09-27b/P-WS
bench/2026-09-27b/P-CW0
bench/2026-09-27b/P-WT1
bench/2026-09-27b/P-PULL
bench/2026-09-27b/P-SW1
bench/2026-09-27b/P-N1
bench/2026-09-27b/P-LG1
bench/2026-09-27b/P-MT1
bench/2026-09-27b/P-LW1
bench/2026-09-27b/P-CW1
bench/2026-09-27b/P-D1
bench/2026-09-27b/P-LR1
bench/2026-09-27b/P-WT2
bench/2026-09-27b/P-PLUG
bench/2026-09-27b/P-SW2
bench/2026-09-27b/P-N2
bench/2026-09-27b/P-LG2
bench/2026-09-27b/P-MT2
bench/2026-09-27b/P-H1
bench/2026-09-27b/P-SWH1
bench/2026-09-27b/P-H2
bench/2026-09-27b/P-SWH2
bench/2026-09-27b/P-LWH
bench/2026-09-27b/P-LW2
bench/2026-09-27b/P-N3
bench/2026-09-27b/P-99-P
bench/2026-09-27b/P-99-R
bench/2026-09-27b/P-99-H
bench/2026-09-27b/P-PS
bench/2026-09-27b/P-L
bench/2026-09-27b/P-CW2
bench/2026-09-27b/P-D2
bench/2026-09-27b/P-DH1
bench/2026-09-27b/P-DH2
bench/2026-09-27b/P-LR2
bench/2026-09-27b/P-LWR
bench/2026-09-27b/CUT-4
bench/2026-09-27b/F-SW
bench/2026-09-27b/F-LS
bench/2026-09-27b/F-L
bench/2026-09-27b/F-00-P
bench/2026-09-27b/F-00-R
bench/2026-09-27b/F-00-H
bench/2026-09-27b/F-S0
bench/2026-09-27b/F-FLOOD
bench/2026-09-27b/F-99-P
bench/2026-09-27b/F-99-R
bench/2026-09-27b/F-99-H
bench/2026-09-27b/F-S1
bench/2026-09-27b/F-D
bench/2026-09-27b/F-COV
bench/2026-09-27b/F-SWD
bench/2026-09-27b/N76-S0
bench/2026-09-27b/N76-T
bench/2026-09-27b/N76-A
bench/2026-09-27b/N76-PL
bench/2026-09-27b/N76-X
bench/2026-09-27b/N76-S1
bench/2026-09-27b/N76-SN
bench/2026-09-27b/N76-W
bench/2026-09-27b/CUT-T
bench/2026-09-27b/T-SW
bench/2026-09-27b/T-LS
bench/2026-09-27b/T-L
bench/2026-09-27b/T-00-P
bench/2026-09-27b/T-00-R
bench/2026-09-27b/T-00-H
bench/2026-09-27b/T-S0
bench/2026-09-27b/T-TR
bench/2026-09-27b/T-S1
bench/2026-09-27b/T-P
bench/2026-09-27b/T-R
bench/2026-09-27b/T-H
bench/2026-09-27b/T-D
bench/2026-09-27b/T-IL
bench/2026-09-27b/T-SN
bench/2026-09-27b/CUT-L
bench/2026-09-27b/L-SW
bench/2026-09-27b/L-LS
bench/2026-09-27b/L-L
bench/2026-09-27b/L-00-P
bench/2026-09-27b/L-00-R
bench/2026-09-27b/L-00-H
bench/2026-09-27b/L-S0
bench/2026-09-27b/L-LOAD
bench/2026-09-27b/L-99-P
bench/2026-09-27b/L-99-R
bench/2026-09-27b/L-99-H
bench/2026-09-27b/L-S1
bench/2026-09-27b/L-D
bench/2026-09-27b/L-COV
bench/2026-09-27b/L-SWD
bench/2026-09-27b/LE-SW
bench/2026-09-27b/LE-LS
bench/2026-09-27b/LE-L
bench/2026-09-27b/LE-00-P
bench/2026-09-27b/LE-00-R
bench/2026-09-27b/LE-00-H
bench/2026-09-27b/LE-D
bench/2026-09-27b/Z-SW
bench/2026-09-27b/R1-M1
bench/2026-09-27b/R1-MB1
bench/2026-09-27b/R1-NW1
bench/2026-09-27b/Z-DW
bench/2026-09-27b/Z-DWALL
bench/2026-09-27b/Z-PS
bench/2026-09-27b/R1Q-ab2
bench/2026-09-27b/R1Q-2a
bench/2026-09-27b/R1Q-boot
```

```cardnum
cells-fence	523	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^bench/2026-09-27b/
declared-date	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md [*][*]declared date 2026-09-27[*][*]
presses-caught	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/R1-CATCH -{2}esc-after 360 -{2}esc-period 0[.]002 -{2}until '<RealTek>' -{2}seconds 380$
cap-cells	165	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out
host-cells	355	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST&? bench/2026-09-27b/
send-over-127	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*AUTOBURN
no-esc-after-but-catch	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out (?!bench/2026-09-27b/R1-CATCH ).*-{2}esc-after
no-watchdog-cell	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*(watchdog|rtl819x-wdt)
no-biteraw	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*biteraw
no-reboot-cell	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*reboot
no-mark-gate	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=RLXFW-
no-txstall-cell	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*txstall
no-sweep-cell	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*echo (sweep|swclear|tx |lb |engine on)
no-phy-write	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*(echo (?!read )[^';]*phyReg|PHYW|MDIOW)
phy-reads-s1	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg'
loader-cells	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/\S+ -{2}send '[A-Z]{2,} 
loader-dw-psrp3	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/R1-DW -{2}send 'DW BB804134 1' -{2}idle 2 -{2}seconds 6$
board-brackets	51	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/\S+-R[0-9]? -{2}send 'sleep\ 2\ ;\ cat\ /proc/rtl819x\-nic\ /proc/net/snmp\ /proc/net/arp\ /proc/rtl865x/asicCounter\ /proc/rtl819x\-nic' -{2}until 'rx_ph4\ \[0\-9A\-F\]\{8\}\(\?:\\r\\n\)\+\#\ \|Booting\\\.\\\.\\\.\|\-\-\-RealTek' -{2}seconds 15$
host-pre-reads	51	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/\S+-P[0-9]? :: HP$
loader-gates	162	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|<RealTek>\|Linux\ version\)\):
switch-cells	21	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'ifconfig rlx0 down ; echo txlen (vendor|rlxfw) > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10[.]1[.]1[.]3 up'
switch-pages	19	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'cat /proc/rtl819x-switch' -{2}until 
liveness-cells	41	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/\S+-L[0-9]? :: FL 10[.]1[.]1[.]3 ; PL ; DMW 
follower-gates	42	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^follower 1\$:
port3-gates	17	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^Port3 Force Mode disable
psrp3-gates	15	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^r PSRP3 
psrp3-12-gates	19	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^psrp3 
switch-first	16	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status'
port-status-after-switch	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*port_status[^']*rtl819x-switch
map-until-prompt	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/R1-M[01] .* -{2}until 'map_lines \[0\-9\]\+\\r\\n\# \|Booting\\\.\\\.\\\.\|\-\-\-RealTek' -{2}seconds 60$
nw-cells	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/R1-NW[01] -{2}send 'cat /proc/rtl819x-spi' -{2}idle 3 -{2}until 'Booting\\\.\\\.\\\.\|-{2}-RealTek' -{2}seconds 15$
idle-cells-banner	81	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/\S+ -{2}send '[^']*' -{2}idle [0-9]+ -{2}until 'Booting\\\.\\\.\\\.\|\-\-\-RealTek' -{2}seconds [0-9]+$
idle-cells-no-banner	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/\S+ -{2}send '[^']*' -{2}idle [0-9]+ -{2}seconds
mfg-cap	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/P-MT[12] .* -{2}seconds 70$
lw2-cap	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/P-LW2 -{2}send 'wait ; cat /tmp/lpw[.]log' .* -{2}seconds 20$
lw-host-wait	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/P-LWH :: CUTW -{2}catch bench/2026-09-27b/P-W[.]meta[.]json -{2}after 605 -{2}max 605$
lp-get-cells	4	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'linkprobe get 
lp-watch-cell	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'cd /tmp && linkprobe watch rlx0 10 600 > lpw[.]log 2>&1 &'
lp-watch-cell-pw	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/P-W -{2}send 'cd /tmp && linkprobe watch rlx0 10 600 > lpw[.]log 2>&1 &'
lp0-gates	5	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^LP0 linkprobe 1 build 1bce836f2e21c43a\$:
mfgtest-cells	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'cd /tmp && /bin/mfgtest auto acf8ed3d > mt[12][.]log 2>&1 ; cat /tmp/mt[12][.]log ; cd /' -{2}until ' of 9 ok
no-abs-tmp-redirect	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send '[^']*[<>] */tmp/
decl-tmp-dir	1	count config/rlxfw-initramfs.tsv ^dir\t/tmp\t-\t1777\t
owner-windows	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/P-P(ULL|LUG) :: CW 100$
cut-cells	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-[NMP4TL] :: CUT -{2}catch bench/2026-09-27b/R1-CATCH[.]meta[.]json -{2}date 2026-09-27 
lp-watch-checks	2	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/P-WT[12] :: CUT -{2}catch bench/2026-09-27b/P-W[.]meta[.]json -{2}date 2026-09-27 -{2}since-max 5\.66$
d3-end-rearm	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/D3-Z-SW -{2}send 'ifconfig rlx0 down ; echo txlen vendor > 
t-arm-rearm	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/T-SW -{2}send 'ifconfig rlx0 down ; echo txlen vendor > 
p-bracket-after-replug	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/P-99-R -{2}send 
mfgtest-refuse-plus2	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/mfgtest.sh pointers refuse, which is [+]2[.]$
cell-l1-cache-shift	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/arch/rlx/include/asm/cache.h ^#define L1_CACHE_SHIFT\t\t5$
cell-smp-cache-bytes	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/arch/rlx/include/asm/cache.h ^#define SMP_CACHE_BYTES\t\tL1_CACHE_BYTES$
cell-net-skb-pad	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/include/linux/skbuff.h ^#define NET_SKB_PAD\t32$
cell-skb-data-align	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/include/linux/skbuff.h ^#define SKB_DATA_ALIGN[(]X[)]\t[(][(][(]X[)] [+] [(]SMP_CACHE_BYTES - 1[)][)] &
spec-net76-flood	1	count SPEC.md [*][*]2,450,381 送出／2,450,254 收到／
spec-net76-duration	1	count SPEC.md [*][*]時長 1,899[.]593 s[*][*]
spec-net68-residual	1	count SPEC.md ^[|] `NET-68` 殘留 
cut-gates	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^cut permit\$:CUT-
cut-full-N	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-N :: CUT -{2}catch bench/2026-09-27b/R1-CATCH\.meta\.json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 19$
cut-full-M	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-M :: CUT -{2}catch bench/2026-09-27b/R1-CATCH\.meta\.json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 15$
cut-full-P	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-P :: CUT -{2}catch bench/2026-09-27b/R1-CATCH\.meta\.json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 12$
cut-full-4	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-4 :: CUT -{2}catch bench/2026-09-27b/R1-CATCH\.meta\.json -{2}date 2026-09-27 -{2}since-max 44 -{2}start-by 23:05$
cut-full-T	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-T :: CUT -{2}catch bench/2026-09-27b/R1-CATCH\.meta\.json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 11$
cut-full-L	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/CUT-L :: CUT -{2}catch bench/2026-09-27b/R1-CATCH\.meta\.json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 5$
k-runs	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/K[1-6]-00(61|62|63)-PG :: PG2 (19|20|21)$
k-path-gates	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^path p3 rx d .*:K[1-6]-00(61|62|63)-D$
m2-series	12	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/M2F-S[0-9]{2} :: ICMP 10[.]1[.]1[.]3$
m2-captures	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST& bench/2026-09-27b/M2F-S[0-9]{2}-T :: TDT$
m2-stops	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\\A0\\n\\Z:M2F-S[0-9]{2}-X$
m2-pairs	12	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^gate:grep=\^path p3 rx d .*:M2F-S[0-9]{2}-D$
m2-plan-card-a	2	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026-09-27/[RE]-RTS :: RTS read --dir bench/2026-09-27 --arm [RE] --plan 011001100110( |$)
m2-tdt-card-a	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^`TDT` = `timeout 900 sudo \-n tcpdump \-n \-tt \-i enxfc19286184c9 'icmp or \(arp and arp\[6:2\] = 1 and arp\[18:4\] = 0 and arp\[22:2\] = 0\) or \(arp and arp\[6:2\] = 2 and \(\(arp\[8:4\] = 0x02524c58 and arp\[12:2\] = 0x4657\) or \(arp\[8:4\] = 0x560a0101 and arp\[12:2\] = 0x01e8\)\)\)'`
m2-tdt-here	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^`TDT` = `timeout 900 sudo \-n tcpdump \-n \-tt \-i enxfc19286184c9 'icmp or \(arp and arp\[6:2\] = 1 and arp\[18:4\] = 0 and arp\[22:2\] = 0\) or \(arp and arp\[6:2\] = 2 and \(\(arp\[8:4\] = 0x02524c58 and arp\[12:2\] = 0x4657\) or \(arp\[8:4\] = 0x560a0101 and arp\[12:2\] = 0x01e8\)\)\)'`
tcpdump-bg	8	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST& bench/2026-09-27b/
text-capture-cells	6	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST& bench/2026-09-27b/\S+ :: TDT$
d4-flood-cell	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/F-FLOOD :: D4F F$
d4-load14-cell	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/L-LOAD :: D4S L$
d4f-macro	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^`D4F <d>` = `bash /home/key/fwre-work/rebuild/s113/card43b/d4load[.]sh -{2}if enxfc19286184c9 -{2}dst 10[.]1[.]1[.]3 -{2}seconds 1860 -{2}out /home/key/fwre-work/rebuild/s113/d4-43b/<d>`
d4s-macro	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^`D4S <d>` = `bash /home/key/fwre-work/rebuild/s113/card43b/d4load[.]sh -{2}if enxfc19286184c9 -{2}dst 10[.]1[.]1[.]3 -{2}seconds 120 -{2}out /home/key/fwre-work/rebuild/s113/d4-43b/<d>`
d4load-flood	1	count /home/key/fwre-work/rebuild/s113/card43b/d4load.sh ^\s+timeout -s INT [$][(][(]SECS [+] 5[)][)] sudo -n ping -f -l "[$]PRELOAD" -s "[$]FSIZE" -w "[$]SECS" -I "[$]IF" "[$]DST"
d4load-no-flood-arg-on-card	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}flood no
iperf-macro	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
iperf5-macro	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^`IPERF5` = `timeout 340 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
iperf-trials	14	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST bench/2026-09-27b/D3-L?(TR|TS|UR|US)[0-9] :: IPERF -c 10[.]1[.]1[.]3 -p 5201 -t 30 -i [15] -f m
iperf-shapes-b48	14	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/D3-L?(TR|TS|UR|US)[0-9] :: IPERF -c 10[.]1[.]1[.]3 -p 5201 -t 30 -i [15] -f m
iperf-servers	15	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'iperf3 -s -1 -f k -{2}logfile /tmp/[a-z]+[0-9][.]log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' -{2}idle 4 -{2}until 'Booting\\\.\\\.\\\.\|-{2}-RealTek' -{2}seconds 30$
iperf-stops	15	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/[a-z]+[0-9][.]log( /tmp/[a-z]+[0-9]a /tmp/[a-z]+[0-9]b)?' -{2}idle 3 -{2}until 'Booting\\\.\\\.\\\.\|-{2}-RealTek' -{2}seconds 40$
watched-invocations	20	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^[*][*]`I-W[A-Z0-9]+`[*][*] — 
lines-watched	20	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}watch X-W[0-9]+ I-W[A-Z0-9]+ 
lines-tails	5	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}tail X-W[0-9]+$
lines-stops	4	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}stop X-W[0-9]+ 
poweroff-line	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}off X-OFF1 [\\]$
inv43b-hold	1	count /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh ^HOLD_S=90$
spec-clk08b-ovsel9	1	count SPEC.md 、9 = [*][*]84,001[.]412 ms[*][*]
log113-press-b	1	count LOG.md B [`]r6b6q[`] 約 71 分，猜
xcells-cap	26	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}x X-\S+ "CAP -{2}out 
xcells-banner	26	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}x X-\S+ "CAP -{2}out [^"]* -{2}until '[^']*Booting\\[.]\\[.]\\[.][|]---RealTek' -{2}seconds [0-9]+"
xcells-host	18	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}x X-\S+ "(?!CAP )
watch-text	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md `CAP -{2}out bench/2026-09-27b/X-W[<]n[>] -{2}esc-after 3600 -{2}esc-period 0\.01 -{2}until '[<]RealTek[>]' -{2}seconds 3605`
offwin-text	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md `CAP -{2}out bench/2026-09-27b/X-OFF[<]n[>] -{2}esc-after 360 -{2}esc-period 0\.01 -{2}until '[<]RealTek[>]' -{2}seconds 365`
inv43b-watch-template	1	count /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh ^WTEXT="CAP -{2}out @DIR@/@WN@ -{2}esc-after 3600 -{2}esc-period 0\.01 -{2}until '<RealTek>' -{2}seconds 3605"$
inv43b-off-template	1	count /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh ^OTEXT="CAP -{2}out @DIR@/@WN@ -{2}esc-after 360 -{2}esc-period 0\.01 -{2}until '<RealTek>' -{2}seconds 365"$
c5ub-cell	1	count bench/2026-09-09/PREDICTIONS-B16-block15.md -{2}out bench/2026-09-09/C5-UB -{2}send 'sleep 400 > /dev/watchdog' -{2}esc-after 450 -{2}esc-period 0[.]01 -{2}until '<RealTek>'
wdt-version	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^#define RTL819X_WDT_VERSION\t"rtl819x-wdt 1[.]1"$
wdt-bootguard-1	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^static int bootguard = 1;$
wdt-ovsel-9	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^static int hw_ovsel = 9;$
wdt-kick-250	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^static int kick_ms = 250;$
wdt-ovsel9-838	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c OVSEL 9 is 83[.]8 s 量
wdt-bootguard-armed	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^\tif [(]bootguard[)] [{]$
wdt-late-initcall	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^late_initcall[(]rtl819x_wdt_init[)];$
wdt-obj-y	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/watchdog/Makefile ^obj-y [+]= rtl819x-wdt[.]o$
wdt-config-watchdog	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.config-built ^CONFIG_WATCHDOG=y$
wdt-sysmap-initcall	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.System.map ^[0-9a-f]{8} t __initcall_rtl819x_wdt_init7$
spec-fw45-838	1	count SPEC.md [*][*]335 倍[*][*]（83[.]8 s）
progress-d3miss-eth4	1	count PROGRESS.md vendor series in the same seating — the vendor's driver, `eth4`, on the same boot
udp-samplers	4	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}send 'cd /tmp && sleep 20 && busybox cp /proc/net/udp [a-z]+[0-9]a && sleep 12 && busybox cp /proc/net/udp [a-z]+[0-9]b &'
cp-applet	1	count config/image-commands.tsv ^applet\tcp$
iperf-host-bin	3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8	sha256 /home/key/fwre-work/iperf3-port/iperf3
killall-applet	1	count config/image-commands.tsv ^applet\tkillall$
wait-builtin	1	count config/image-commands.tsv ^builtin\twait$
udp-format	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/net/ipv4/udp.c ^\t\t" %02X %08X:%08X %02X:%08lX %08X %5d %8d %lu %d %p %d%n",$
udp-rcvbuf-refusal	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/net/core/sock.c ^\tif [(]atomic_read[(]&sk->sk_rmem_alloc[)] [+] skb->truesize >=$
udp-sk-mem-packets	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/net/core/sock.c ^#define _SK_MEM_PACKETS\t\t256$
nic-rx-alloc	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c skb = len [?] dev_alloc_skb[(]len [+] 2[)] : NULL;
sha-swpage-py	e4c2943a5c814ada92cdaa21326df04c21c5349386d09d9ab9868a462a5951a7	sha256 /home/key/fwre-work/rebuild/s113/card43b/swpage.py
sha-lpread-py	61b4003b31b9367bcde519c5d649ea70b1cf7224d9abfa2babee7c27b5450fb5	sha256 /home/key/fwre-work/rebuild/s113/card43b/lpread.py
sha-cutgate-py	f47f7f9bad9392bc83ed95d9bb2e515e0e0337ef102f112301004497ce0367eb	sha256 /home/key/fwre-work/rebuild/s113/card43b/cutgate.py
sha-carrierwatch-py	6d2cd4153ffd22860311d800b9aecf4e8d8c78a8cdaa430347abb4088e2c2f25	sha256 /home/key/fwre-work/rebuild/s113/card43b/carrierwatch.py
sha-udpq-py	e8e4fa63b4787ff697b8658db95e25024fac1e40d2488361d2d4c774b0d90040	sha256 /home/key/fwre-work/rebuild/s113/card43b/udpq.py
sha-d4load-sh	8608019d6b9041f97ce23951e692c10f4a8db26f9fde94b2750d63f822016b82	sha256 /home/key/fwre-work/rebuild/s113/card43b/d4load.sh
sha-d4cover-py	2779f40b6166dc1e0c7910ed358c7323f9e5dbd57c841a69a680dbcb2887f4cf	sha256 /home/key/fwre-work/rebuild/s113/card43b/d4cover.py
sha-arith43b-py	c81188f835456a8c10d26035989b21a7beac9fd13431028217909a50b184ff98	sha256 /home/key/fwre-work/rebuild/s113/card43b/arith43b.py
sha-verbcheck43b-py	1b19c9ad4adae19124a4544e79b12d9b5a4e6eca3efc23652dcb6d61ea08cc9d	sha256 /home/key/fwre-work/rebuild/s113/card43b/verbcheck43b.py
sha-brdelta-py	030144a35c0bf3251640fc290ac4635e1c00ba84feb07ae9f19b87e34a2b3984	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py
sha-pcapwin-py	6871c76753f28fac9cdbf7227dfc8fa015d9238ba908c3a70c5aeeda98408095	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py
sha-dmesgwin-py	2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py
sha-s1class-py	fd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431	sha256 /home/key/fwre-work/rebuild/s113/shared/s1class.py
sha-rttseries-py	fbae2a34a798514f8fff35fbea7dbf189ae537f79718f2c7a12fca460993cecf	sha256 /home/key/fwre-work/rebuild/s113/card43a/rttseries.py
selftest-swpage	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-swpage.out ^swpage\ self\-test:\ 18\ of\ 18\ passed$
selftest-lpread	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-lpread.out ^lpread\ self\-test:\ 27\ of\ 27\ passed$
selftest-cutgate	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-cutgate.out ^cutgate\ self\-test:\ 17\ of\ 17\ passed$
selftest-carrierwatch	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-carrierwatch.out ^carrierwatch\ self\-test:\ 3\ of\ 3\ passed$
selftest-udpq	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-udpq.out ^udpq\ self\-test:\ 8\ of\ 8\ passed$
selftest-d4cover	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-d4cover.out ^d4cover\ self\-test:\ 6\ of\ 6\ passed$
selftest-brdelta	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-brdelta.out ^brdelta\ self\-test:\ 40\ of\ 40\ passed$
selftest-pcapwin	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-pcapwin.out ^pcapwin\ self\-test:\ 29\ of\ 29\ passed$
selftest-dmesgwin	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-dmesgwin.out ^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$
selftest-s1class	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-s1class.out ^s1class\ self\-test:\ 15\ of\ 15\ passed$
selftest-rttseries	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-rttseries.out ^rttseries\ self\-test:\ 22\ of\ 22\ passed$
selftest-verbcheck43b	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-verbcheck43b.out ^verbcheck\ self\-test:\ 6\ of\ 6\ passed$
verbcheck-pass	1	count /home/key/fwre-work/rebuild/s113/card43b/verbcheck43b.out ^verbcheck verdict PASS$
sha-iperflog	12ab35696c31e3949b4398f02104b7e8dbc5f029338b0e4035110be5ca1be19b	sha256 tools/iperflog.py
selftest-iperflog	1	count /home/key/fwre-work/rebuild/s113/card43b/selftest-iperflog.out ^RESULT:\ 31/31$
mutants-43b	1	count /home/key/fwre-work/rebuild/s113/card43b/mutants43b.out ^mutants43b: [0-9]+ planted, 0 not as expected$
d4-rehearsal	1	count /home/key/fwre-work/rebuild/s113/card43b/d4rehearse/rc.tsv ^d4cover-loop15-permits\t0\t0$
d4-rehearsal-skip	1	count /home/key/fwre-work/rebuild/s113/card43b/d4rehearse/rc.tsv ^d4cover-skip-refuses\t1\t1$
d4-rehearsal-timeout	1	count /home/key/fwre-work/rebuild/s113/card43b/d4rehearse/rc.tsv ^longw-ended-within-14s\t0\t0$
cut-rehearsal-permit	1	count /home/key/fwre-work/rebuild/s113/card43b/cutrehearse.out ^permit-case rc 0 cut permit$
cut-rehearsal-refuse	1	count /home/key/fwre-work/rebuild/s113/card43b/cutrehearse.out ^refuse-case rc 1 cut refuse since-max$
cut-rehearsal-draft	1	count /home/key/fwre-work/rebuild/s113/card43b/cutrehearse.out ^draft-case rc 2 
objdiff-recipe-only	1	count /home/key/fwre-work/rebuild/s113/card43b/objdiff43b.out ^verdict main[.]o differs only in the recipe id; rtl819x-spi[.]o differs only in the recipe id$
objdiff-control	1	count /home/key/fwre-work/rebuild/s113/card43b/objdiff43b.out ^control rtl819x-switch[.]o reads not-recipe-only 
etlink-files	1	count /home/key/fwre-work/rebuild/s113/card43b/etlink.out ^files 332$
etlink-all-zero	1	count /home/key/fwre-work/rebuild/s113/card43b/etlink.out ^value +563 n_et_link 0$
etlink-last	1	count /home/key/fwre-work/rebuild/s113/card43b/etlink.out ^last +563 et_link_last FFFFFFFF$
lpqemu-lp0	3	count /home/key/fwre-work/rebuild/s113/card43b/lpqemu.out ^LP0 linkprobe 1 build 1bce836f2e21c43a$
lpqemu-enotty	9	count /home/key/fwre-work/rebuild/s113/card43b/lpqemu.out ^LP (drv|link|ring) (lo|nosuch0|eth0) rc 25 can 
lpqemu-bound	1	count /home/key/fwre-work/rebuild/s113/card43b/lpqemu.out ^bound n [0-9]+ max 101 within yes$
gates43b	1	count /home/key/fwre-work/rebuild/s113/card43b/gates43b.out ^gates43b: 28 new gate families and untils tested, 0 not as expected 
cut-rehearsal-lwh	1	count /home/key/fwre-work/rebuild/s113/card43b/cutrehearse.out ^lwh-case rc 0 cutgate 1[.]1 wait since 100[.]0 s after 605 s: waits 505[.]0 s$
img-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.manifest ^verdict\tgreen$
img-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.manifest ^vmlinux_sha256\t9e0ff326ae8bc9ccd7b66f8d58755246a4e8640a7df0011c24f6e84c73095134$
img-manifest-variant	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.manifest ^variant\tquiet$
img-recipe	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.manifest ^recipe_id\tacf8ed3d$
img-irfs-source	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.manifest ^initramfs_source\t/home/key/fwre-work/rebuild/_irfs-r6b6/rlxfw-initramfs[.]spec$
img-record-nfjrom	1	count /home/key/fwre-work/rebuild/s112/r6b6/rtk/r6b6q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\tef5622d23738978bcce0bdce66c03c59cf86cd7320ddbbebcf58bb0f50edf6ee$
img-record-clean	1	count /home/key/fwre-work/rebuild/s112/r6b6/rtk/r6b6q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
img-nfjrom-sha256	ef5622d23738978b	sha256-16 /home/key/fwre-work/rebuild/s112/r6b6/rtk/r6b6q/rlxfw/kroot/rtkload/nfjrom
img-twin-same	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q2.manifest ^vmlinux_sha256\t9e0ff326ae8bc9ccd7b66f8d58755246a4e8640a7df0011c24f6e84c73095134$
img-sysmap-getlink	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.System.map ^[0-9a-f]{8} [tT] nic_et_get_link$
img-sysmap-lde	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.System.map ^[0-9a-f]{8} [tT] rtl819x_sw_lde_note$
img-no-wtdog	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.config-built ^# CONFIG_RTL_WTDOG is not set$
img-no-printk	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.config-built ^# CONFIG_PRINTK is not set$
img-linkprobe	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.initramfs.manifest.tsv ^/bin/linkprobe\tfile\t16240\t071c8f81a47cc8ed84ad9d6ddce8a7e5b4db45ca1ba35fd457a1d9f47bd3d723\t
img-mfgtest	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.initramfs.manifest.tsv ^/bin/mfgtest\tfile\t
img-iperf3	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b6q.initramfs.manifest.tsv ^/bin/iperf3\tfile\t252644\t3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8\t
decl-linkprobe	1	count config/rlxfw-initramfs.tsv ^file\t/bin/linkprobe\t
cell-nic-sha	ffebe8b9a3a376b38d52c9f0a463b3e3ca57375b0aab796fbd3e7a4272df25b5	sha256 /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c
cell-nictx-sha	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic-tx.h
cell-switch-sha	c546d1c505c266fd6c5ec44595a708a21d422ab5e45b7583ba21593c29009c18	sha256 /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c
mfgtest-src-sha	d954de730d5cdadb137632d44c30974bcac4d97a79d7d414480421c4dabc1588	sha256 /home/key/fwre-work/rebuild/s112/r6b6/repo/config/mfgtest.sh
nic15check-sha	13198b2c9009b5175026f8bf9fa1d4988d8e5cb466d8e45a63bd9035f5788286	sha256 tools/nic15check.py
lp-src-sha	eaeb655f5e5ba00205cdc1c88828558d20166397277a053b6fde9b94456ee56a	sha256 /home/key/fwre-work/rebuild/s112/r6b6/repo/config/rlxfw-user/linkprobe/linkprobe.c
lp-bin-sha	071c8f81a47cc8ed84ad9d6ddce8a7e5b4db45ca1ba35fd457a1d9f47bd3d723	sha256 /home/key/fwre-work/rebuild/s112/r6b6/repo/build/rlxfw-user/linkprobe/linkprobe
nic-object-same	1	count /home/key/fwre-work/rebuild/s113/plan43/txpath.out ^nic[.]o IDENTICAL$
switch-version-1.2	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_SW_VERSION\t"rtl819x-switch 1[.]2"$
switch-lde-format	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c "psrp%u %08X up %u lde %lu lj %lu[\\]n",$
switch-lde-before-table	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\tlen [+]= rtl819x_sw_lde_lines[(]page [+] len[)];
switch-psrp0	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_SW_PSRP0\t0x4128$
switch-phys	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_SW_PHYS\t\t0x1B800000$
switch-psrp3-row	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t[{] "PSRP3",\t0x4134, 0, 0 [}],$
switch-linkup-bit	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_PSRP_LINKUP\t[(]1u << 4[)]$
switch-anylink-5	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_SW_NPHYPORT\t5$
nic-ring-8	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define NIC_RX_DESC\t\t8$
nic-ring-4	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define NIC_TX_DESC\t\t4$
nic-drvinfo-bus	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c strncpy[(]di->bus_info, "platform",
nic-version-1.5	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define RTL819X_NIC_VERSION\t"rtl819x-nic 1[.]5"$
errno-eopnotsupp-122	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tEOPNOTSUPP\t122\t
errno-enodev-19	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tENODEV\t\t19\t
loopback-always-on	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b6q/top/linux-2.6.30/drivers/net/loopback.c ^\t[.]get_link\t\t= always_on,$
mfgtest-version-1.1	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/mfgtest.sh ^MFG_VERSION="mfgtest 1[.]1"$
mfgtest-port-label	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/mfgtest.sh chk MT-PORT 1 "[$]MFG_PORT LinkUp by [$]ver; [$]vt"$
mfgtest-auto-9	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/mfgtest.sh ^DECLARED_auto=9$
spec-net30-dw	1	count SPEC.md `DW BB804134 1`
spec-net117-2	1	count SPEC.md 在 `-S1` 停掉伺服器之前讀板子的 `/proc/net/udp`
spec-net131-deciding	1	count SPEC.md 能定案的現在是卡片 B50 P9 寫的那一個括號
notes-27	1	count notes/nic-driver.md ^## 27 Block 48 
b48-lus1-stall	1	count bench/2026-09-26b/D3-LUS1-L.log ^4 packets transmitted, 0 received
b48-lur1-done	1	count bench/2026-09-26b/D3-LUR1.log ^iperf Done[.]$
b48-lus1-124	1	count /home/key/fwre-work/rebuild/s112/r6b3/run2/run-I-D3-r2.log END D3-LUS1 rc=124 73[.]4 s
b48-mb1-digest	1	count bench/2026-09-26b/R1-MB1.log ^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46\s+-$
b48-psrp3-f9	1	count bench/2026-09-26b/X-SW1.log ^r PSRP3 +4134 000000F9 
b48-x-sw1b-1f9	1	count bench/2026-09-26b/X-SW1b.log ^r PSRP3 +4134 000001F9 
b48-bug-traces	1	count bench/2026-09-26b/Z-DWALL.log ^bug_preempt 1350$
b23-mfgtest-auto2-9	1	count bench/2026-09-17/C1-AUTO2.log ^9 of 9 ok, 0 FAIL
b23-mfgtest-auto-8	1	count bench/2026-09-17/C1-AUTO.log ^8 of 9 ok, 1 FAIL
b23-mfgtest-tick-fail	1	count bench/2026-09-17/C1-AUTO.log ^ +FAIL +MT-TICK 
b23-mfgtest-interleave-a	1	count bench/2026-09-17/C1-AUTO.log MT-PORT +Port3 LinkURpL$
b23-mfgtest-interleave-b	1	count bench/2026-09-17/C1-AUTO2.log MT-PORT +Port3 LinkURpL$
b24-c10-bit8	1	count bench/2026-09-17b/C10-PS0.log BB804128:\t000010E0\t000010E0\t000010E0\t000011F9
arith-controls	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^arith43b controls: 22 of 22 hold$
arith-psrp3	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^PSRP3 kseg1 BB800000 [+] 4128 [+] 3[*]4 = BB804134$
arith-lp9	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LP9 calls 12 ok 4 refused 8 nowrite 0$
arith-lp-errno	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LP errno EOPNOTSUPP 122 ENODEV 19$
arith-lp-ring	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LP ring rx 8/8 mini 0/0 jumbo 0/0 tx 4/4$
arith-lp-region	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LP region drv 192 link 4 ring 32$
arith-lpw-bound	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LPW watch rlx0 10 600 bound n <= floor[(]600[*]1000/10[)][+]1 = 60001$
arith-d4-sizes	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^D4 sizes 18-1472 count 1455 frames 60-1514$
arith-d4-fix	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^D4 fix seconds 1860 timeout 1865 minutes 31[.]08$
arith-udp-cap-168	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^UDP S 168 rcvbuf 108544 T 1672 N 64$
arith-udp-64-range	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^UDP N 64 exactly when S in 161[.][.]168$
arith-udp-b48	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^UDP block48 by-difference 64 63 64 64 [(]notes/nic-driver[.]md 27[.]8[)]: 1$
arith-udp-paced	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^UDP a 30 s trial at -b 20M -l 1400 is paced to 53571 datagrams$
arith-n131-sizes	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^N131 lengths 61 62 63 61 62 63 ping_s 19 20 21 19 20 21$
arith-n131-p	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^N131 P[(]1<=k<=5[)] about 0[.]33 a run, P[(]at least one of 6[)] about 0[.]91 
arith-m2	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^M2 plan 011001100110 series 12 on 6 off 6 echoes 1200 
arith-udp-align	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^UDP L1_CACHE_SHIFT 5 SMP_CACHE_BYTES 32 [(]asm/cache[.]h[)]
arith-udp-aligned-1504	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^UDP frame 1442 alloc 1476 aligned 1504$
arith-mw-66	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^MW on 6 off 6 lo 5 hi 31 P[(]U<=lo[)] 19/924 
arith-mw-65	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^MW on 6 off 5 lo 3 hi 27 P[(]U<=lo[)] 7/462 
arith-mw-55	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^MW on 5 off 5 lo 2 hi 23 P[(]U<=lo[)] 4/252 
arith-mw-fw	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^MW family-wise false lowers at any of 5 sizes <= 0\.103 
arith-lpw-restart	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LPW restart check: elapsed since the watch's meta start <= 340 s = .* cutgate -{2}since-max 5\.66 min$
arith-lpw-keep	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LPW a half is the watch's only if its window ENDs by the watch's t0_raw [+] 595 s$
arith-lpw-cap	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LPW P-LWH waits until the watch's meta start [+] 605 s [(]600 [+] margin 5[)], at most 605 s; P-LW2's wait then returns within the margin, cap 20$
arith-d4-net76	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^D4 NET-76 flood received 2450254 of 2450381 in 1899[.]593 s 
arith-d4-floor-flood	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^D4 floor flood received >= 1199591 
arith-d4-floor-ntx	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^D4 floor F-D n d >= 1201046 
arith-d4-floor-rest	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^D4 floor answered-all yes low-intervals 0$
arith-mfg-per-run	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^MFG n_write_refused d per mfgtest auto run 2 
arith-lus1-timeout	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME lus1 timed out at 73\.4 s 
arith-time-rules	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME rules end\-by 23:52 start\-by\-4 23:05 since\-max\-4 44 lus1\-timeout 73\.4$
arith-time-est	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME est 78\.91 min to\-cut4 38\.31 min slack\-since\-max 5\.69 min$
arith-time-need	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME need N 19 M 15 P 12 T 11 L 5 \(nominal \+ int \+ 2 min\)$
arith-time-r6b4	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME r6b4 40\.60 min from start\-by 23:05 ends 23:45$
arith-time-must	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME must 37\.32 min \(12 fix and 2 control trials at 73\.4 s; 4 refusals each followed by the 90\-s hold\) latest\-catch 23:14$
arith-time-latest-r6b4	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME latest\-catch\-r6b4 22:26 \(start\-by 23:05 less to\-cut4\)$
arith-time-latest-all	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME latest\-catch\-nothing\-cut 22:26 \(binding CUT\-4\)$
arith-time-lpw	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME lpw elapsed P\-WT1 7\.9 s P\-WT2 204\.6 s \(threshold 340 s\); P\-H1 ends 403\.0 s P\-H2 ends 404\.3 s \(the span 595 s\); the host wait 197\.7 s$
arith-mfg-runs	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^MFG runs 2 R1\-NW0 to R1\-NW1 n_write_refused d 4$
arith-time-since-max	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^TIME since\-max\-4 44 = floor\(85 \- the R6b\-4 block 40\.60 min\), the press's length the owner accepted on 2026\-09\-27$
arith-c2-01	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^WDT r6b6q's rtl819x\-wdt 1\.1: bootguard 1 hw_ovsel 9 kick_ms 250; OVSEL 9's deadline 83\.8 s \(the build cell's rtl819x\-wdt\.c\)$
arith-c2-02	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^WDT SPEC FW\-45's 335x at OVSEL 9 \(83\.8 s\): 1$
arith-c2-03	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^BOUND every stretch under 76\.55 s = the bite 83\.8 \- a kick 0\.25 \- overhead 2 \(a guess\) \- margin 5 \(a guess\)$
arith-c2-04	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^WATCH esc\-after 3600 esc\-period 0\.01 seconds 3605 until <RealTek> \(card A's watch\)$
arith-c2-05	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^BITEM OVSEL 9's bite as measured 84\.001412 s \(SPEC\.md CLK\-08b, seating 18\); the driver's own figure 83\.8 s, 0\.24 % under it \(the stretch bound keeps it\)$
arith-c2-06	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^B2P the loader's banner to its first prompt with ESC streaming: block 48's R1\-CATCH 2\.288097 s; the warm resets with the watch's period: C5\-UB 2\.304123 s, R2\-B8 2\.305032 s$
arith-c2-07	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HOLD the watch's hold after a stop 90 s = ceil\(the bite as measured 84\.001 s \+ the loader's banner to its first prompt 2\.288 s \+ a margin 3\.0 s \(a guess\)\) = ceil\(89\.290\)$
arith-c2-08	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HOLDEDGE from E, the latest board capture's end, the reset to the banner taken as 0 \(unmeasured\): a kernel that stops kicking by E\+3\.7 s \(90 \- 84\.001 \- 2\.288\) is bitten and at its prompt by E\+90 s; one that stops by E\+6\.0 s \(90 \- 84\.001\) bites by E\+90 s, after E\+87\.7 s \(90 \- 2\.288\) with its banner in the watch and its prompt perhaps after the watch's stop; one that stops later bites after the watch's ESC has ended$
arith-c2-09	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^LOADER at its prompt: block 48's R1\-CATCH, 550 replies before its CR, each after 128 ESC, each 'Unknown command !' and the prompt yes; a watch opened at the prompt ends on the first, 128 x 0\.01 s = 1\.28 s, about 1\.3 s$
arith-c2-10	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^CATCHPROMPT block 48's R1\-CATCH: its first <RealTek> after the banner yes and C\-8's cold line yes$
arith-c2-11	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^CCARM console\-capture arms \-\-until from the start of a capture with no \-\-esc and no \-\-send: 1 line$
arith-c2-12	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^WATCH a split adds 1\.5 s between its host traffic and the next board read: the watch's stop 0\.5 and the next invocation's start 1 \(guesses\)$
arith-c2-13	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^WATCH C5\-UB: period 0\.01, ESC 145\.869442 s into a live rlxfw, ended on the prompt yes$
arith-c2-14	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^WATCH R2\-B8: ESC streamed through a bite \(the bite verb disables interrupts and spins: yes\), 70 bytes back before the banner, 0 of them an ESC or its echo, the last 41\.9 s silent; the loader caught at its prompt: yes$
arith-c2-15	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HANDSHAKE catch esc\-after 360 = session 60 \+ owner 300 \(guesses, card A's\); until <RealTek>, its first prompt; seconds 380 \(block 48's 20 s after the ESC kept\)$
arith-c2-16	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HANDSHAKE the press by 350 s after the catch's start = 360 \- power\-on to the loader's prompt 10 \(a guess\); the session's 'now' no later than 310 s after it = 350 \- the owner's minimum 40$
arith-c2-17	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HANDSHAKE block 48's catch: esc 180 seconds 200 duration 200\.1 s$
arith-c2-18	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HANDSHAKE power\-off esc\-after 360 = session 60 \+ owner 300; seconds 365$
arith-c2-19	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^HANDSHAKE cable window 100 = session 60 \+ the owner's minimum 40; its end, the window's RUN line \+ 100 s, is told in the 'now'$
arith-c2-20	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^CUT4 the planner's since\-max 35 \(a guess\) beside start\-by 23:05; press B up to 85 min, the owner's decision of 2026\-09\-27; LOG\.md's 113th segment recorded about 71 min \(a guess made before the card was sized\): 1$
arith-c2-21	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^CAP maps: 24 committed of this command ended on their \-\-until, the longest 14\.175 s \(2 ran to a cap\); cap 60 = 4\.23x it, 14\.5 s under the bound$
arith-c2-22	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^CAP mfgtest auto alone: 3 committed runs ended on their \-\-until, the longest 26\.894 s \(0 ran to a cap\); cap 70 = 2\.60x it, 4\.5 s under the bound$
arith-c2-23	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^STRETCH bite 83\.8 s kick 0\.25 s overhead 2 s margin 5 s: every stretch under 76\.55 s$
arith-c2-24	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^STRETCH 164 stretches, the longest 76\.2 s ending at M2F\-S11\-R, 7\.3 s under the bite less a kick$
arith-c2-25	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^STRETCH 24 watch stops, the longest gap to the next ESC 23\.5 s \(the watch over I\-WLW, then P\-LW2\)$
arith-c2-26	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WTR1 \-> D3\-TR1\-S1 6\.5 s$
arith-c2-27	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WTR2 \-> D3\-TR2\-S1 6\.5 s$
arith-c2-28	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WTR3 \-> D3\-TR3\-S1 6\.5 s$
arith-c2-29	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WTS1 \-> D3\-TS1\-S1 6\.5 s$
arith-c2-30	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WTS2 \-> D3\-TS2\-S1 6\.5 s$
arith-c2-31	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WTS3 \-> D3\-TS3\-S1 6\.5 s$
arith-c2-32	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WUR1 \-> D3\-UR1\-S1 6\.5 s$
arith-c2-33	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WUR2 \-> D3\-UR2\-S1 6\.5 s$
arith-c2-34	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WUR3 \-> D3\-UR3\-S1 6\.5 s$
arith-c2-35	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WUS1 \-> D3\-US1\-S1 6\.5 s$
arith-c2-36	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WUS2 \-> D3\-US2\-S1 6\.5 s$
arith-c2-37	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WUS3 \-> D3\-US3\-S1 6\.5 s$
arith-c2-38	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WLUR1 \-> D3\-LUR1\-S1 6\.5 s$
arith-c2-39	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WLUS1 \-> D3\-LUS1\-S1 6\.5 s$
arith-c2-40	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the tail watch before L2 \-> K1\-0061\-SW 9\.7 s$
arith-c2-41	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the tail watch before L3 \-> the watch over I\-WPULL 2\.5 s$
arith-c2-42	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WPULL \-> P\-SW1 13\.5 s$
arith-c2-43	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the tail watch before L4 \-> the watch over I\-WPLUG 2\.5 s$
arith-c2-44	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WPLUG \-> P\-SW2 13\.5 s$
arith-c2-45	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WLW \-> P\-LW2 23\.5 s$
arith-c2-46	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WF \-> F\-99\-R 18\.7 s$
arith-c2-47	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WT \-> T\-S1 6\.5 s$
arith-c2-48	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the watch over I\-WL \-> L\-99\-R 18\.7 s$
arith-c2-49	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^GAP the tail watch before the power\-off line \-> the power\-off window 1\.5 s$
arith-c2-50	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^XHOLD 18 board lines open after a hold with a declared board X\-cell, its cap 10 to 30 s \(X\-<page>, X\-<t>\-S0R\): from the hold's stop to the tail watch's first ESC 12\.5 to 32\.5 s = the stop 0\.5 \+ the cap \+ the runner's stop and the tail watch's start 2 \(guesses\)$
arith-c2-51	1	count /home/key/fwre-work/rebuild/s113/card43b/arith43b.out ^XHOLD a board line that opens with an invocation \(a continuation, or the next line after a stop or a cut's refusal\): its \-\-from cell's cap at most 70 s \(P\-MT2, the longest board cap bar the catch\): up to 73\.5 s = the stop 0\.5 \+ an invocation's start 1 \+ the cap \+ 2 \(guesses\)$
```
