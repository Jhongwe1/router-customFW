# PREDICTIONS — block 51, seating 43's third press (card C: `R6b-7` on `r6b7q` — `D7` through Linux's MDIO API, `C-18`'s reopening condition at register level, `NET-08`, `NET-136`'s open contract)

**declared date 2026-09-27** — **one power press, the third of seating 43**, after card B's
power-off and a host restart; § 2 holds the window's arithmetic: the catch window opens no
later than 23:45 that day — `I-T` refuses after 23:43, before the owner is asked, and
`T-CATCH`, `I-1`'s first cell, after 23:45, before the catch opens. The owner's date is
pending: the generator's `--date` sets it, and a re-dated card differs from this one in its
directory and its date only.
Card A (block 49, `p2q`) and card B (block 50, `r6b6q`) are seating 43's first two presses,
frozen as `bench/2026-09-27/PREDICTIONS-B51-block49.md` (`cc5e39d`) and
`bench/2026-09-27b/PREDICTIONS-B52-block50.md` (`255af14`); this card depends on neither's
outcome. It shares card B's classifier `s1class.py` and card B's cut-point tool `cutgate.py`
(both pinned by digest in `R0-SUM`, each digest the one card B pins: cardnum rows) and reads
card B's figures for its window from card B's frozen card (§ 2; a cardnum row each, and one for
that card's digest). Its cells are `notes/switch-driver.md` § 10.8's — L1–L2 at the loader and
(a)–(j) under Linux — for `PROGRESS.md`'s `R6b-7`; § 0 ⑦ lists every place this card departs
from that section or had to resolve it, each with its reason.

Marks: **量** measured on the device · **讀** read out of code or a dump · **推** inferred,
pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① What this press is, and the owner's decisions of 2026-09-26 it carries** (§ 10.7). One
press of `r6b7q` (recipe `50e4af55`): `rtl819x-switch` 1.3, a phylib `mii_bus` for the five
embedded PHYs behind one gated MDIO path (`SPEC.md` `NET-135`, its register contract
`NET-136`), on `rtl819x-nic` 1.5, whose source is `r6b6q`'s byte for byte. Decision A:
`CONFIG_NET_ETHERNET` and `CONFIG_PHYLIB` are in the image (cardnum rows). B: rlxfw writes PHY
register 31 for the first time, pages 0 and 1 only, the restore guaranteed or the operation
refused; `probe` and `pread` refuse unless `bound` is 10,000; the vendor's `extRead N 1 19` is
a second source for page 1. C: the MDIO verbs sit behind their own token, `mdio-i-mean-it`. D:
`C-18`'s reopening condition is observed at register level only; its functional clause is ⊘
with its price. E: this press is its own, after `R6b-6`'s; (h) is ⊘ and (i) is `R6b-8`'s.

| conjunct | carried here | not here |
|---|---|---|
| `D7` (`NET-06`, `NET-24`): the PHY IDs through Linux's MDIO API equal the loader's, address by address | L1–L2 at the caught prompt, (c)'s probe, (d)'s comparison (P0, P3, P4) | — |
| the vendor's `/proc/rtl865x/phyReg`, a third source where it reads | (d): registers 2 and 3 of PHYs 0–4 (P4) | — |
| `C-18`'s reopening condition at register level, with `NET-07` | (g)'s eight `pread`s under decision D's rule (P7); (g′)'s `extRead` beside them (P8) | whether port 1 *needs* the patch: two cable moves and a comparison arm (⊘, the owner's ruling) |
| `NET-08`: addresses 5–31, registers 1 and 3–5 | (e) `scan 0 31` (P5) | — |
| `NET-136` 殘留: register 31's read-back, `MDCIOSR` 30:16, `STATUS`'s length, the switch's own poller against a selected page | (g)'s `p0`/`ps`/`p1`; (e)'s `hi`; (e) and (f)'s `spin`; `PSRP` bit 8 either side, `scan 0 4` and liveness after, with (g)'s own positive control for the scan detector (P5–P8, P10) | — |
| the bound's positive control | (f) (P6) | — |
| `PSRP` 保留態的起點 | — | ⊘ this press (decision E: it needs a cable move and a prediction) |
| (i): `reset full`, then `scan 0 4` | — | `R6b-8`'s |

**② The image variable, named before power.** `r6b7q` is not the image cards A and B boot. 量 at
the desk (§ 10.5): vmlinux `b926105b…` and nfjrom `548f4fae…`, built twice byte-identical
(`r6b7q2`, a cardnum row); the initramfs digest `d6882c14` is `r6b6q`'s; the kernel is 40,960
bytes longer (1.3 and libphy). So a boot of this image is the first boot of 1.3, and of phylib,
on this die; § 10.9 and § 7 below name what that leaves open. The press is a cold power-on
after card B's power-off, and the loader's two `MDIOR`s come before the round.

**③ Containment, which does not depend on any outcome.**
* **The one-shot probe cannot be spent at a small bound, on any path.** The card's only `bound`
  verbs are in `I-F`, after `I-C`'s probe in the card's order, and the runner never re-runs a
  cell nor runs an invocation out of order (§ 6); the probe cell is typed only after a page
  that reads `bound 10000` (`C-UN`'s gate); after it, a `probe` returns `-EEXIST` before the
  bound is read (讀 `rtl819x_mdio_probe`: `reg_rc != 1` is its first test). § 10.8 (c)'s
  `bound 0`, then `probe` — the probe's own `-EAGAIN` guard shown on the die — is **not
  typed**: it would be safe only if the guard it tests works (§ 0 ⑦ (1)).
* **No page-1 `pread` without a page that read `bound 10000` in its own invocation**: `G-P1`, a
  page-0 read (one MDIO read, harmless at any bound), gates `bound 10000`, and so does every
  page-1 `pread` cell on its own page; `mdioverb43c.py` refuses a card otherwise (`R0-VERB`).
  The driver refuses `-EAGAIN` at any other bound: its own second layer.
* **A restore that did not verify stops every MDIO cell**: every page-1 `pread` cell and every
  vendor cell gates `dirty 0`. After a failure the PHY may sit on page 1 until power-off (推: a
  power cycle resets PHY registers, decision B); § 6 reads the pages and powers off.
* **PHY writes are register 31, values 1 and 0, and nothing else**: rlxfw's eight page-1
  `pread`s (16 writes) and the vendor's five `extRead`s (10; `arith43c.out`). `echo write`,
  `extWrite`, `PHYW` and `MDIOW` are typed nowhere (cardnum rows count zero).
* **Nothing is typed while a `pread` may be timing out**: every cell sends one line and ends on
  the page's `jiffies` line and the prompt, so the next line goes out only after the verb
  returned (≤ 130 ms with IRQs off, nominal: `arith43c.out`).
* **No flash write of any kind**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`, and no
  `DW` or `DB` either (cardnum rows count zero). The two loader cells type `MDIOR`, an MDIO
  read: it stores `MDCIOCR` and sets `GIMR` bit 8 (`NET-16`) and reaches no flash. Every upload
  is `looprun`'s, which reads `00000000` back from the `AUTOBURN` word first.
* **A reset is caught where it can be, and where it cannot the card says so** (⑤): the loader
  cells carry `--esc-after`; every board cell's `--until` carries the reset banner; cards A and
  B's watch `X-W<n>` streams ESC whenever no command line runs — every line's tail, opened by
  its `;` the moment its runner stops, however it stopped — and the power-off window `X-OFF<n>`
  before every power-off (§ 6).

**④ The host is restarted before this press**, as card B's was: between card B's power-off and
this card's `I-0`, `wsl --shutdown`, a fresh keeper, the kernel-log follower into a new file
(`/home/key/fwre-work/rebuild/s114/host43c/dmesg-w43c.log`), and both USB devices attached with
the board off. `R0-DW0` refuses power unless that log reads `bug_preempt 0`, `usbnet_xmit 0`
and `call_trace 0`.

**⑤ Resets.** **The loader cells.** L1 and L2 type `MDIOR` at the loader, whose MDIO wait has
no bound (`NET-17`): a transaction that never completed would hang it, and if the loader's
watchdog then bit (at the loader's 14.965 MHz, OVSEL 9 is ~1.12 s, `arith43c.out`), the board
would boot the vendor's firmware unless the ESC window were caught. So both carry
`--esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25` — `X8`'s form (seating 27's
`MDIOR 0 2`, a cardnum row) — and four gates: `until`, `caught` (the prompt seen after the
tool's own CR), no reset text (`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|Linux version))`), and
the 32nd address's line; a reset caught there is § 6's. **Linux: `BOOTGUARD` is armed.** 讀 the
image's own `rtl819x-wdt.c`: `bootguard = 1`, `hw_ovsel = 9`, `kick_ms = 250`, the same words
in its ELF's `.data` (cardnum rows), `bootguard` and `__initcall_rtl819x_wdt_init7` in its
`System.map`; a kernel timer kicks the watchdog every 250 ms, and a kernel whose timer wheel
stops is reset 83.8 s later (量, as the driver's own comment records it, `OVSEL 9 is 83.8 s 量`,
a cardnum row; 84.001 s as `SPEC.md` `CLK-08b` measured it, a cardnum row — this card uses the
shorter figure as a deadline, the maps' cap and the detection span below, where it is the
conservative one, as card A's § 0 ⑦ (ii) keeps it, and the longer one for the hold after a
stop, 90 s as in cards A and B (`arith43c.out`'s `HOLD` line); `CONFIG_RTL_WTDOG=n` removes the
vendor's watchdog, not this one). The loader then boots the vendor's firmware unless its ESC
window, ~4.9 s from the banner (量 2026-08-18, `console-capture.py`'s own note), is caught.
**What that vendor boot does to flash is 推**: `FLS-30` read nine vendor boots with the map's
brackets unchanged, and the map does not see `H601`, two writes that cancel, or any byte
outside it (a cardnum row); CLAUDE.md bars the boot either way. **What can bite here:** only a
stall with IRQs off that outlives 83.8 s. rlxfw's IRQs-off section is ≤ 130 ms, and the
vendor's MDIO accessors spin with IRQs on (讀 `rtl865x_asicL2.c`,
`rtl8651_getAsicEthernetPHYReg`: an unbounded `do … while` on `MDCIOSR`, no `local_irq_save` on
its path from `proc_phyReg_write`), so a vendor poll that never ends keeps the timer running
and hangs the board without a bite (推). A stall of unknown cause is the one case, and two
states can hold one: a board cell that ended without its terminator, and an asynchronous stall
that starts while the board is idle. **So**: every board cell's `--until` carries the banner's
alternatives `Booting\.\.\.|---RealTek`, so a reset ends its cell at once and the loader gate
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))` (54 gates) fails; no Linux
cell carries `--esc-after` (ESC sent into a live tty is echoed — 量 `bench/2026-09-23/P1-RZ.log`
bytes 19–24, `^[^[^[` — and would corrupt a page, and an `--until` match ends the `--esc-after`
loop, 讀 `console-capture.py`); the maps' cap is 60 s, under the bite (block 48's longest map
13.9 s); and the watch `X-W<n>` — cards A and B's form: ESC every 10 ms for up to an hour,
ending on the loader's prompt `<RealTek>`, the xcells fence's line and `inv43c.sh`'s `WTEXT` —
holds the console whenever no command line runs: every command line (§ 6) ends with `;` and a
tail watch, which opens the moment the line's runner stops, however it stopped, and holds the
console across every wait for the owner and every decision; the next line stops it (`--stop`)
and, after any stop, first waits beside it for the hold (`--hold`, 90 s after the latest board
capture's end), by when a kernel that had stalled has been bitten and its loader caught inside
the watch. What an hour of ESC does to `ash` at its prompt is 推 harmless (it echoes or drops
them, and the watch's closing CR runs one line of them, which `ash` does not find as a command:
cards A and B, `C5-UB`). **How long a stall takes to be seen** (`arith43c.out`'s `TIME detect`
lines, cardnum rows, computed from the cells this card's generator wrote): a kernel stalled
with IRQs off prints nothing, so the next cell whose `--until` needs the board's output fails
at its cap and stops its line, while `--idle` cells (they end on the silence) and host cells
are counted as passing on their estimates — an upper bound, since an `--idle` cell whose output
a gate needs stops at once on its empty capture (§ 5). The longest such span inside one
invocation is 63.7 s — a stall at `Z-PS`'s start, stopped by `R1-M1`'s cap — which leaves 20.1
s of the 83.8-s bite for the line's tail watch to open (block 50 measured its tail watches'
captures starting 0.23–0.24 s after their line's runner ended (`I-1`/`X-W15`, `I-CN`/`X-W36`,
`I-P1`/`X-W37`, `I-Z`/`X-W47`: the run log's last stamp and the watch's `t0_raw`, one clock));
a stall that crosses an invocation boundary costs a wrapper start-up there too (block 50:
0.35–0.47 s), and the tightest such case leaves 32.0 s for each, so each must stay under 20.1
s. What this leaves is § 7's: the second or so between a watch's stop and the next line's first
capture, and a reset whose banner ended a cell before the tail watch opened inside the 4.9-s
window.

**⑥ The clock.** The cut gates (`T-LATE`, `T-CATCH`, `G-CUT`, `V-CUT`: card B's `cutgate` 1.1)
read the host's wall clock against a capture's own start stamp — the one place this card uses
one. No verdict rests on a timestamp: § 2's window is arithmetic on estimates; the pages'
`jiffies` and the kernel-log windows' times are readings.

**⑦ Where § 10.8 was ambiguous, or is departed from — each resolved here, with its reason.**
* **(1) (c)'s `bound 0`, then `probe` → `EAGAIN` is not typed** (③). This card was drafted
  under the rule that no cell may be able to spend the one-shot probe at a small bound, and
  that cell can, exactly when the guard it tests fails. The probe's own `-EAGAIN` guard stays
  shown on the host only (`mdiocheck` K4, and its mutants M1 and M6 killed); the counter it
  moves, `again`, is shown on the die by (f)'s page-0 `pread` at `bound 0`, a different guard
  in the same driver. So `again` reads 0 after (c) and 1 after (f), where § 10.8 has 1 and 2.
* **(2) The vendor's paths are kept, outside rlxfw's gate.** (d)'s `read` and (g′)'s `extRead`
  issue MDIO commands through the vendor's accessors — no gate, no IRQs off, an unbounded poll
  — and `extRead` writes register 31 (1, then 0 unconditionally). They stay because decision B
  and the step's DoD name them; each is a cell of its own behind `sleep 1`, so its reply does
  not interleave with the echo (`C19-PHYID`'s form; block 48's `X-PHY1` shows the interleave),
  and each ends on rlxfw's page (`; cat /proc/rtl819x-mdio`), whose `jiffies` line is its
  terminator and whose `version` and `dirty 0` are its gates: the vendor's `panic_printk` reply
  lines are readings, never gates. (g′) runs after (g) as § 10.8 orders. A rule that every MDIO
  command goes through rlxfw's gated path is rlxfw's design, and holds for every rlxfw verb
  here; the loader's `MDIOR` and the vendor's `phyReg` are the two other sources `D7` needs.
* **(3) Port 3's r0, r2 and r3 in (e)** are not stated in § 10.8: predicted `1100`, `001C`,
  `C880` — r0 量 under Linux by block 48's `X-PHY1`, the IDs as at 0–4.
* **(4) (a) is read first**: `cat /proc/rtl819x-switch` is the first read after the process
  table, so the opening map and `n_writes` (which read the SPI driver only) come after (a) and
  (b), not before as in cards A and B.
* **(5) Detectors § 10.8 does not list**, each read-only: `scan 0 4`, the switch page and an
  `lde` delta after (g′) (the vendor's restore, detected as (g)'s is); a page after each vendor
  read (P4's "do not move rlxfw's counters"); three board brackets and three liveness gates
  (S1's inputs, and a functional check of port 3 after each paged block); the counter chain
  (`J-CH`) over every page.
* **(6) (j)'s "`mdio_to` and `busy` as (f) predicted"** is read as: equal to their values on
  the last unlocked page (`V-SC`'s) and on `F-S1`'s, which (f)'s accounting fixed.
* **(7) The press's place.** `PROGRESS.md` § Now lists `R6b-7`'s press after seating 43 and
  after `R6b-6`'s `rtl819x-nic.c:122` comment fix; this card is drafted as seating 43's third
  press, on the image already built, which that fix (a later recipe) does not touch. **(8)**
  `PROGRESS.md`'s `R6b-7` row names `PSRP` 保留態的起點 among what the step reads through the bus;
  decision E puts (h) out of this press, and this card follows decision E. **(9)** (a)'s
  "`ifconfig` shows `rlx0` and `lo` only": `/init` brings `rlx0` up and nothing in this image
  brings `lo` up (讀 `config/rlxfw-init.sh`, a cardnum row), and plain `ifconfig` lists
  interfaces that are up, so this card predicts no `eth*`, `wlan*` or `br*` and `rlx0` once
  (the condition the bit-8 detector needs at `A-IF`, and `I-V` at `V-IFS`, the same `ifconfig`
  typed again at its start) and reads `lo` as it comes; no committed capture holds a plain
  `ifconfig` on this image family.
* **(10) (d) runs after (g)**, not second: the vendor's unbounded read path runs only after
  rlxfw's bounded verbs have tested `STATUS` ((e) and (f)), and `D-MD`'s prediction is that it
  moves none of rlxfw's counters.
* **(11) Two latest-catch gates.** `I-T`, its own invocation, runs just before the owner is
  asked and refuses after 23:43 — the latest catch less 2 minutes for the owner's reply (a
  guess) — so the owner is not asked for a press that could not start in time; `T-CATCH`,
  `I-1`'s first cell, refuses after 23:45 itself, once the reply has come. A refusal there
  costs nothing physical: the owner presses only when told the catch is open (⑪).
* **(12) A ninth `pread`, `pread 0 1 2`** (`G-P9`), is the scan and `lde` detector's positive
  control: page 1's register 2 unlike page 0's, the detector can see a PHY left on page 1;
  equal, it cannot (P7).
* **(13) No Linux cell carries `--esc-after`**, though a reset there is otherwise caught only
  by `X-W<n>`: ESC sent into a live shell is echoed into the page it would be read from, and an
  `--until` match ends the `--esc-after` loop, so on a Linux cell it would stop streaming
  exactly when a reset's banner arrives (⑤). The card carries the loader cells' `--esc-after`,
  the banner in every board cell's `--until`, and the watch `X-W<n>` whenever no command line
  runs (cards A and B's). A capture tool that starts ESC only on the banner — a
  `console-capture` 1.6, with its own self-test and mutation run — would close most of § 7's
  gap; it is a proposal, not built, and nothing on this card depends on it.
* **(14) `rlx0` is put on block 50's fix once, before the opening bracket** (`A-NIC0`, the
  boot's `/proc/rtl819x-nic` page, its `txlen` a reading; `A-FIX`; then its read-back `A-FIXR`,
  gated on `txlen vendor`, `armed 1` and `nd_up 1`; `CORRECTIONS-block50.md` § 2; the owner's
  relaxed process of 2026-09-27): on a 1.4 ring block 50's 60-B liveness read 0 of 4 while
  every host frame reached port 3, so a liveness here reads port 3's function without 1.4's
  length fault. The line writes only the CPU interface's ring registers (讀 `nic_do_arm`,
  `nic_ndo_open` and `nic_ndo_stop` in the build cell's `rtl819x-nic.c`): no switch, PHY or
  MDIO register, so no MDIO reading of this card moves with it. It follows (a), (b), the
  opening map and `n_writes`, which stay the first Linux reads, and precedes every bracket,
  liveness and MDIO verb, so all of those run on one `txlen`.

**⑧ Runner limits** (card B's). No background cell; the kernel-log follower is an off-card
process started before `I-0`. `I-0` and `I-T` run alone, in the foreground; the press is
command lines (§ 6), cards A and B's form, each a script file run by path in the session's
background, its steps chained with `&&` and ended by `;` and a tail watch. `NAME?` marks a cell
whose non-zero exit is a reading. Macros take one parameter.

**⑨ `C-19`** is named: the kernel-log windows count `USB disconnect`, `cp210x` and `ttyUSB`
lines, and the record states every console drop and every idle longer than a minute, with the
idle before it.

**⑩ New instruments, each with a self-test and a mutation run whose unmutated pass came first**
(`/home/key/fwre-work/rebuild/s114/card43c`, `mutants43c.out`: every planted mutant killed, a
cardnum row). `mdpage.py` 1.1 reads the loader's `MDIOR` lines, 1.3's `/proc/rtl819x-mdio`
page, the vendor's two reply lines, the switch page's two MDIO rows and the sysfs names, and
applies every comparing rule of § 3, the counter chain included; **no silicon page of 1.3
exists yet**, so its fixtures are rendered from the driver's own format strings, each checked
verbatim against the build cell's source, and (b)'s comparison reads `mdiocheck`'s own
`boot_page()` rather than a copy. `swpage13.py` is card B's `swpage.py` with its version moved
to 1.3 by `mkswpage13.py`, every substitution anchored. `mdioverb43c.py` is § 4's MDIO rules as
a tool — the verbs, the bound before a probe or a page-1 `pread`, the dirty gates, the loader
and vendor sends, the declared X-cells, the banner in every board cell's `--until` — run as
`R0-VERB`, each rule shown refusing a planted card. `inv43c.sh` 1.2 is card B's `inv43b.sh` 1.3
— the version block 50 ran — with the card and its directories renamed: every invocation's and
every X-cell's exit code goes to a file, and it runs the tail watch (`--tail`), the power-off
window (`--off`), their stop (`--stop`) and the hold after a stop (`--hold`), each capture it
starts in the background under a shim that restores SIGINT, which a background command inherits
ignored. Reused and pinned: `dmesgwin` 1.2 (card2), `s1class` 1.0 (seating 43's) and `cutgate`
1.1 (card B's). Their self-tests read `mdpage self-test: 71 of 71 passed`;
`swpage13 self-test: 18 of 18 passed`; `dmesgwin self-test: 9 of 9 passed`;
`s1class self-test: 15 of 15 passed`; `cutgate self-test: 17 of 17 passed` and
`mdioverb self-test: 25 of 25 passed`.

**⑪ The owner's handshake** (§ 6), cards A and B's, for the press and for the power-off: (1)
the session tells the owner what comes next — for the press, that the catch must open by 23:45
— and STOPS; (2) the owner's reply (「開始」) only authorizes opening the window; (3) the session
starts the command line in the background and confirms the ESC-streaming capture from its files
— the catch `R1-CATCH` (`--esc-after 360 --esc-period 0.002 --until '<RealTek>' --seconds 380`)
by its `RUN` line in `run-I-1.log` and its `.timing` existing (`test -e`: the capture creates
it once the port is open, before its first ESC, and it holds 0 bytes until a byte arrives), the
power-off window `X-OFF<n>` by its `XCELL X-OFF<n> running` and `t0` lines; (4) only then does
it tell the owner "catch open — power on now, by HH:MM:SS" (the `RUN` line's time plus 350 s,
said only while that is at least 40 s away) or "power off now, by HH:MM:SS" (the `t0` time plus
360 s); (5) the owner acts, and confirms a power-off in words. The catch streams ESC for at
most 360 s and ends at the loader's first prompt: 60 s for (3) and (4), 300 s for the owner
after (4) — both guesses, cards A and B's (`arith43c.out`'s `CATCH` line, a cardnum row).
Nothing physical is timed from the reply: the session's latency between a reply and a window
can exceed any count. No other physical action: no cable moves this press (decision D's price
is not paid).

---

## § 1 The image

`r6b7q`, quiet variant, recipe `50e4af55`, `nfjrom` `/home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/kroot/rtkload/nfjrom` (`548f4fae6682c295afa838e47d04db7bae13dbde06927447cce7fed4e17c8d53`), vmlinux `b926105b6318561f50971738399912d31265292277dbaeb049109942de3740d1`, built twice byte-identical (`r6b7q2`), initramfs from `_irfs-r6b6` (`d6882c14`, `r6b6q`'s). Its build cell `/home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top` holds `rtl819x-switch.c` 1.3 (`/home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c`) and `rtl819x-nic.c` 1.5, and every source row on this card reads the cell's copies (a cardnum row also finds `HEAD`'s switch driver equal to the cell's). The chain is checked by `cardnum` rows: the manifest `verdict green`, `variant quiet`, that vmlinux and that initramfs; the `rtkimage` record naming that `nfjrom` digest with a CLEAN tripwire verdict; the `nfjrom` on disk with that digest and 1,169,408 bytes; `CONFIG_RTL_WTDOG` and `CONFIG_PRINTK` not set, `CONFIG_WATCHDOG`, `CONFIG_PHYLIB`, `CONFIG_NET_ETHERNET` and `CONFIG_RLXFW_VENDOR_ETH_OPEN` set, `PREEMPT_NONE`, no `SMP`, `HZ` 100, no `panic=`. `looprun` pins the `nfjrom` by digest before the port opens and compares the booted image's `RLXFW-ID0` with the build's (`--recipe-override 50e4af55`, the manifest's); `R1-NW0` and `R1-NW1` read `recipe_id 50E4AF55`. **Addresses:** no cell types one. What the card takes from `r6b7q`'s own `System.map` is read at the desk: the 1.3 and phylib symbols (`rtl819x_mdio_xfer`, `…_read_proc`, `…_write_proc`, `mdiobus_register`, `mdiobus_scan`; `__initcall_phy_init4`, `phy_init` at `subsys_initcall`; `__initcall_rtl819x_mdio_init6`, the `/proc` entry at `device_initcall`; `bootguard` and `__initcall_rtl819x_wdt_init7`), and the boot values of `rtl819x_mdio_bound` (10,000: the word at file offset 2911424 of the vmlinux ELF), `reg_rc`, `scan_rc[0–4]` and `xrc[0–4]` (1 each: the locked page's `rc 1 xrc 1`), `bootguard`, `hw_ovsel` and `kick_ms` (1, 9, 250), each a `word32` row, beside `genphy_driver`'s `phy_id` and `phy_id_mask` (`FFFFFFFF`, the reader's positive control) — `arith43c.out` resolves each address through the ELF's section headers, and refuses a `.bss` symbol, which has no bytes in the file.

---

## § 2 The press, in order

| invocation | what runs | est. min (a guess) |
|---|---|---:|
| `I-0` | before power | 0.3 |
| `I-T` | the latest-catch gate | 0.0 |
| `I-1` | the gate again, the catch, L1-L2, the round | 0.8 |
| `I-A` | (a), (b), the map, a bracket, liveness | 0.6 |
| `I-C` | (c) the guards and the probe | 0.1 |
| `I-E` | (e) `scan 0 31` | 0.0 |
| `I-F` | (f) the timeout's control | 0.1 |
| `I-G` | (g) eight `pread`s, the control, the detector, a bracket, liveness | 0.3 |
| `I-D` | (d) the vendor's reads, `D7` | 0.2 |
| `I-V` | (g') a fresh `ifconfig`, `extRead` x5, the detector, a bracket, liveness | 0.4 |
| `I-J` | (j) lock, the final page, the chain | 0.0 |
| `I-Z` | closing | 0.4 |

About 3.1 minutes from the catch window's opening to power-off with nothing retried: a guess
from block 48's transcripts (`arith43c.out`, medians in seconds: round 24.7, ps 3.4, map 13.9,
mb 0.9, nw 3.6, bracket 5.5, live 0.9, idle3 3.4), this card's catch 17.3 s (cards A and B's
catches, the longer, open to the loader's first prompt with the owner's press inside it: the
catch ends on `<RealTek>`, its `--seconds` 380 only its cap, and a capture's own time over its
`--seconds` is 0.3 s, block 48's), `X8`'s `MDIOR` for a loader cell (0.9 s), a switch page 0.9
s and a vendor `phyReg` cell 2.3 s (guesses), an MDIO page from its byte count at 3,840 B/s
plus 0.3 s (boot 0.4 s, probe 0.4 s, scan32 0.9 s, scan32pr8 1.1 s; the widest page this card
prints, 32 rows and eight `pr` lines, is 2985 B), the fix `A-FIX` as an `--idle` cell and its
read-back as block 50's `/proc/rtl819x-nic` pages, and 0.5 s between invocations on a command
line (block 50's wrapper start-up, 0.35–0.47 s). `I-0` and `I-T` are before power and not in
the figure; the per-invocation minutes, the figure and every time below are `arith43c.out`'s
`TIME` lines (cardnum rows), computed from `est43c.tsv`, the cells this card's generator wrote.

**The window, as arithmetic.** The owner's date is pending; every figure here is a guess except
card B's, each read back from its frozen card, `bench/2026-09-27b/PREDICTIONS-B52-block50.md`
(cardnum rows, and one for its digest).

| window | figure | from |
|---|---|---|
| this card, the catch to power-off | 3.1 min | the table above |
| the catch's ESC stream, at most (it ends at the loader's first prompt) | 360 s | 60 s to open it, confirm it and say "now" + 300 s for the owner after "now" (cards A and B's guesses) |
| with one S1 read set and a retried liveness | 7 min | + 3 (a guess), rounded up |
| the last capture of a press on its declared date | 23:52 | card B's rule (`capdate`) |
| this card's latest catch | 23:45 | 23:52 − 7 min |
| the latest-catch gate, before the owner is told | 23:43 | 23:45 − 2 min |
| `T-CATCH`, `I-1`'s first cell, after the owner's reply | 23:45 | this card's latest catch |
| card B, the catch to power-off with nothing cut | 79 min | card B's § 2: its arithmetic's 78.91 min, rounded up |
| card B's power-off to this card's catch | 10 min | a guess: ④'s host restart and `I-0` |
| card B's latest catch, for both presses on one date | 22:16 | 23:45 − 10 − 79 min |
| card B's own latest catch | 23:14 | card B's header |
| card B's latest catch for nothing of it to be cut | 22:26 | card B's header (`CUT-4` binds) |
| card B's latest power-off (its cut points) | 23:52 | card B's § 6, S6: its 5 `--end-by` cut points each refuse a block that would pass 23:52 at its estimate |
| this card's catch after that | 00:02 the next day | 23:52 + 10 min |

So this card runs on card B's date only if card B's catch opens by 22:16 — before card B's own
22:26, so at card B's estimate nothing of it is cut (`arith43c.out`'s control `T9`) — and
nothing of card B is cut; otherwise it is re-dated to the next day before power (the
generator's `--date`; nothing else changes), and its catch window then opens no later than
23:45 on that day. **Enforced, not only stated**: `I-T`'s `T-LATE` refuses after 23:43 (the
latest catch less 2 minutes for the owner's reply, a guess), `T-CATCH` after 23:45, and `G-CUT`
and `V-CUT` refuse a block whose nominal minutes, rounded down, plus 2 — 3 for (g), (d), (g′),
(j) and the closing; 2 for (g′), (j) and the closing — would pass 23:52 (§ 6, S6).

The order protects the readings: the loader's two reads come before anything else the press
does; (a)'s page is the first Linux read; every rlxfw MDIO verb follows the unlock and precedes
the lock; the timeout's control (f) comes after the rows it depends on (e) and before any
page-1 read, and ends at the full bound; the vendor's unbounded paths — (d)'s reads and (g′)'s
`extRead` — run only after rlxfw's bounded verbs, (d) after (g) and (g′) last but for (j) and
the closing reads.

---

## § 3 Predictions, each with what refutes it

### 3.0 What is read, and the names used below

**The page** is `/proc/rtl819x-mdio` as 1.3 prints it (§ 10.4): `unlocked`, `bus B reg_rc R`,
`bound`, `mdio_rd`, `mdio_wr`, `mdio_to T busy B retry R`, `refused R wr_refused W again A`,
`spin N MIN MAX`, `hi_or`, `dirty`, `scanned MASK j J`, `phyN id … rc … xrc … drv … att …`, up
to eight `pr` lines, one row `aNN r0 … r5 hi H psrp P n N` per scanned address, and `jiffies`.
A `cat` issues no MDIO command and renders twice (`FW-64`). Errno on this arch (`arith43c.out`,
from the build cell's headers): `EPERM` 1, `EIO` 5, `EAGAIN` 11, `EEXIST` 17, `ENODEV` 19,
`EINVAL` 22, `EPROTO` 71, `ETIMEDOUT` 145. Every verb is routed through `cat`, so a refused one
prints `cat: write error: <text>` and never its payload (`FW-41`); the unit's uClibc holds each
text once (cardnum rows) — `EPERM`'s and `EEXIST`'s are 量 in earlier captures, `EAGAIN`'s
"Resource temporarily unavailable" is 推. **A gate reads a `/proc` page's fields, never console
text**: not that line, not a mark (`FW-47`), not the vendor's `panic_printk` replies; each of
those is a reading. Two host gates read `mdpage`'s comparison of two pages (`V-GO`) and
`ifconfig`'s interface counts (`V-IF`). Numbers are typed in decimal without leading zeros.
**No verdict on this card is a statistical test**: every rule is a deterministic comparison on
one boot, so no rate of false verdicts across several tests applies.

### 3.1 The loader (L1, L2)

* **P0** (`L1-MD2`, `L2-MD3`, read by `L-RD`). L1, `MDIOR 2`: 0–4 read `0x001c`, 5–31 `0x0000`
  (量, `F2` repeated). L2, `MDIOR 3`: 0 and 1 read `0xc880` (量 `E6`, `E8b`,
  `bench/2026-08-23/E.log` — the only loader-side register-3 reads in `bench/`; `C19` read PHY
  0's under Linux), 2–4 `0xc880` (推), 5–31 `0x0000` (推). Each reply, up to its prompt, is 1,042
  bytes (`arith43c.out`: 8 + 32 × 32 + 10 — the echo ends in LF, each line is CR-led and
  CRLF-ended, the prompt CR-led — `F2`'s measured size). **Refuted by** a 量 line otherwise (L1
  anywhere, L2 at 0 and 1): `L-RD` names the address. L2's 推 part at 2–31 is a reading: a
  register-3 value other than `c880` at 2–4 is `NET-06`'s open half answered, and `D7` is read
  against it.

### 3.2 (a) and (b): the opening pages

* **P1, (a)** (`A-SW`, `A-IF`, `A-MDC`). `version rtl819x-switch 1.3`; `psrp3 … up 1` (a gate)
  and `up 0` at 0, 1, 2 and 4 (a reading). Slot-0 `MDCIOCR` reads `1F030000` (推: L2's last
  command is a read of address 31, register 3 — `arith43c.out`); `96181441`, slot 0's value in
  all 70 committed dumps (`NET-28`: the loader's own store, `docs/loader-phy-and-switch.md`),
  would mean the TFTP/`J` path issues that store after the prompt; any other word, another
  store. Slot-0 `MDCIOSR` is decided by nothing: its bit 31 (`STATUS`) reads 0 and its bits
  15:0 `0000` after L2's read (推), and its bits 30:16 are printed as `NET-136`'s reading (未定,
  never compared). `ifconfig` (interfaces up) lists no `eth*`, `wlan*` or `br*` and `rlx0`
  once: `A-IFR` prints the two counts, `0` and `1` — an empty capture reads `0` and `0`, which
  is what makes the second count the first's positive control; `lo` is a reading (§ 0 ⑦ (9)).
  `A-SWP` prints the eight `psrp` lines: `psrp3 … up 1`, the rest `up 0`. **Refuted by** slot-0
  `MDCIOCR` other than `1F030000` — a reading for where the loader stores `MDCIOCR`, never a
  stop. **Voids** (g)'s bit-8 detector for this boot, and, seen again at `V-IFS`, bars (g′)
  (`V-IF`, § 6): a port other than 3 up, or an `eth*` interface up (the vendor's link DSR reads
  `PSRP` too, and `re865x_open` arms `one_sec_timer`, whose page-0 writes to PHYs 0–4 could
  land inside `extRead`'s IRQs-on page window, 讀 `rtl819x-switch.c`'s notes, `NET-135`;
  `CONFIG_RLXFW_VENDOR_ETH_OPEN=y`, a cardnum row).
* **P2, (b)** (`A-MD`, `A-MDP`). The locked page is byte for byte `mdiocheck`'s K1
  (`boot_page()`), its `jiffies` aside: `unlocked 0`, `bus 0 reg_rc 1`, `bound 10000`,
  `mdio_rd 0`, `mdio_wr 0`, `mdio_to 0 busy 0 retry 0`, `refused 0 wr_refused 0 again 0`,
  `spin 0 0 0`, `hi_or 00000000`, `dirty 0`, `scanned 00000000 j 0`, `phy0`–`phy4`
  `id - rc 1 xrc 1`. **Refuted by** any other line; two are gates, and no MDIO cell runs after
  either fails: `mdio_rd` or `mdio_wr` other than 0 (the boot issued an MDIO command: the
  driver header's item 2, *it writes NOTHING at boot*, is false) and a `bound` other than the
  image's 10,000 (a `word32` row).

### 3.3 (c): the guards and the probe

* **P3** (`C-P0` … `C-PR2`). `C-P0`, `probe` while locked:
  `cat: write error: Operation not permitted` (a reading), `refused 1`, `bus 0 reg_rc 1`,
  `mdio_rd 0`. `C-UN`: `unlocked 1`, `bound 10000`, nothing else moved. `C-PR`, `probe` at the
  full bound: `bus 1 reg_rc 0`, `mdio_rd 10` (registers 2 and 3 of five addresses,
  `arith43c.out`), `mdio_wr 0`, `phy0`–`phy4` `id 001CC880 rc 0 xrc 0 drv 0 att 0`,
  `refused 1 wr_refused 0 again 0`, `spin 10 …`, `hi_or 00000000`, `dirty 0`,
  `scanned 00000000`. `C-SYS`: `rlxsw:00` … `rlxsw:04` and nothing else (讀 `PHY_ID_FMT`
  `"%s:%02x"`; `/init` mounts sysfs: cardnum rows), counted by `C-SYR`
  (`sys rlxsw 5 of 5, other 0`). `C-PR2`: `cat: write error: File exists` (a reading),
  `mdio_rd 10`. **Refuted by** a locked probe not refused (`bus 1` at `C-P0`: the gate is not a
  gate); the probe not registering (`bus 0`, or `reg_rc` ≠ 0, at `C-PR`: the shot is spent, and
  every later rlxfw verb returns `-ENODEV`, § 6); a `phyN` row other than predicted (`D7`'s
  Linux half, P4; `J-CH` checks `rc 0 xrc 0 drv 0 att 0` at `C-PR` and at `J-PR`); a device
  name other than `rlxsw:0N`, or a sixth (phylib registered what the mask says it may not).

### 3.4 (d): `D7`

* **P4** (`D-V0` … `D-V4`, `D-MD`, `D-D7`), run after (g) (§ 0 ⑦ (10)). For N = 0–4, `phyN`'s
  id = `L1[N] << 16 | L2[N]` (`NET-06`, `NET-24`; not `NET-39`, which holds `BMCR` and the port
  map): `001CC880` five times, predicted. The third source: `D-VN` prints
  `read phyId(N), regId(2),regData:0x1c` and `read phyId(N), regId(3),regData:0xc880`
  (`C19-PHYID`'s form), readings, then rlxfw's page, its gates; each vendor page and `D-MD`
  read rlxfw's counters unchanged from `G-SC`'s (the vendor's reads do not move them; `J-CH`).
  A reply missing is `vendor unmeasured at aN`, and `D7`'s loader-against-Linux verdict stands
  without it. **Refuted by** an address where Linux's ID differs from the loader's
  (`d7 verdict refuted at …`), or the vendor's from either. **What it cannot see:** the five
  IDs are equal, so `D7` cannot see addresses 0–4 swapped among themselves, and P5's rows see
  only a swap that involves port 3: at 0, 1, 2 and 4 they share one prediction (which of them
  is port 1 is `NET-39`'s, § 7).

### 3.5 (e): `scan 0 31`

* **P5** (`E-SC`, `E-SW`, `E-RW`). `mdio_rd` 10 → 202 (32 × 6 = 192, `arith43c.out`),
  `scanned FFFFFFFF`. Each value carries its mark, and `mdpage rows` applies them apart: a
  **量** value that differs refutes 1.3's address path even when `D7` holds
  (`rows verdict refuted`); a **推** value that differs is a reading
  (`rows 推 reading differs at …`), never a refutation. At 0: r0 `1100` (量 `C20` under Linux),
  r1 `78C9` (量 `E12d`, `C20`), r2 `001C` (量 `F2`), r3 `C880` (量 `E6`, `C19`), r4 recorded, r5
  `0001` (推: `E12e`'s `PHYR 0 5` was read at the loader's prompt, and register 5 — the link
  partner's ability — is link state, which a loader-state value does not predict). At 1, 2 and
  4: r2 `001C` (量 `F2`) and, at 1, r3 `C880` (量 `E8b`) — the ID registers are read-only
  identifiers, so a loader read of them predicts Linux's, `D7`'s own premise; r0 `1100`, r1
  `78C9` and r5 `0001` (推 under Linux: `X8` read r0 at the loader, and a loader value of a
  state register does not predict a Linux one), r3 `C880` at 2 and 4 (推, `NET-06`'s open half).
  At 3, the cabled port: r0 `1100` (量 under Linux, block 48's `X-PHY1`); r1 with bits 2 and 5
  set (量 `X5`, `78ED`, and `X-PHY1` under Linux); r2 `001C` (量); r3 `C880` (推); r4 recorded; r5
  non-zero with bit 0 set (推: `X4`'s `PHYR 3 5`, `CDE1` against this desk's RTL8153, was read
  at the loader's prompt). 5–31: r0 and r2 `0000` (量 `X8`, `F2`) — no register's state: no PHY
  answers there (`NET-08`, `NET-24`), so each is what the MDIO controller returns for a read no
  device answers, and 1.3's read stores the word the loader's primitive stores for it
  (`MDCIOCR`'s layout, 讀 in the datasheet, the SDK header and the loader, `NET-15`; 讀
  `rtl819x_mdio_xfer`). That is why a loader read predicts Linux's there, as it does for the ID
  registers, and why a value other than `0000` there refutes 1.3's address path rather than
  being read as link state; r1 and r3–r5 `0000` (推, `NET-08`'s answer either way). `hi` `0000`
  on every row (推; the bits are 未定, `NET-136`): a `hi` other than `0000` is recorded against
  its address — whether a PHY answers there — as `NET-136` 殘留's reading. `spin` and `hi_or` are
  recorded, and `E-RW` prints (f)'s branch from `spin` before (f) runs.

### 3.6 (f): the timeout's positive control

* **P6** (`F-B0` … `F-S1`, `F-AC`). `F-B0`: `bound 0`, then `pread 0 0 16` refused:
  `cat: write error: Resource temporarily unavailable` (推, a reading), `again 1`, no `pr` line.
  `F-S0`, `scan 5 5` at `bound 0`, conditional on (e)'s `spin`: if its min is ≥ 1, the row
  holds at least one `E145`; if its max is 0, it reads `0000` ×6 with no timeout, and the
  control is ⊘ for this press; between the two, only the accounting is predicted. In every
  branch each `E145` is one `mdio_to`, each `E016` one `busy` with no store, and `mdio_rd`
  rises by 6 − Δ`busy` (`mdiocheck` K7's model, `STATUS` held for three reads, gives
  `E145 E016 E016 E145 E016 E016`). `F-B1`: `bound 10000` (a gate). `F-S1`: `0000` ×6, `n 3`,
  `mdio_to` unmoved, `mdio_rd` +6. **Refuted by** an accounting identity failing
  (`f REFUTED …`), or no `E145` in the timeout branch.

### 3.7 (g): `C-18`

* **P7** (`G-P1` … `G-P9`, `G-SC`, `G-SW`, `G-C18`, `G-PCTL`, `G-SWD`). Eight `pread`s, which
  fill the eight kept: `pread 0 0 16`, the unpaged control; `pread 0 1 16` (bits 15:13 read
  `110`, 讀 `rtl865x_asicL2.c:4177`); `pread a 1 19` for a = 0, 1, 2, 4, then 3, the cabled
  port, last; `pread 4 1 20`, recorded only. Predicted: `p0 0`, `p1 0`, `rs 0`, `rt 0`,
  `dirty 0` (推). **A `pread` whose register-31 read at rest is not 0 writes nothing and reads
  nothing more** (讀 `rtl819x_mdio_pread`: `v 0 ps 0 p1 0 rs 1`, one read and no write; `-71` or
  the read's errno): no `C-18`, bit-0, `rs` or `extRead` verdict is drawn from it. The
  accounting is each `pread`'s own cost, read from its `pr` line (`mdpage c18`, the chain's
  model): with k such reads, `mdio_rd` +29 − 3k − b and `mdio_wr` +14 − 2k, `retry` 0, where b
  of the k were refused busy at rest (`-16`: no read, one `busy`) and any that timed out
  (`-145`) count one `mdio_to` (`arith43c.out`). `ps` is 未定: 1 — register 31 reads back; 0 with
  page 1's register 16 unlike page 0's — the select works and the read-back does not reflect
  it; 0 and equal — the two cannot be told apart (`NET-136` 殘留's rule). **The select is shown**
  when `pread 0 1 16` made its select and either every paged read that made its select reads
  `ps 1` or page 1's register 16 differs from page 0's; only then are the `r16`, bit-0 and
  `C-18` rules read (`mdpage`'s `g select`; otherwise `c18 not observed`). If register 31 does
  not read back, every paged read returns `-71` with `v` kept: a reading, not a failure.
  Register 19's bit 0 reads 0 on all five (讀 `:4193`; 量 `REVR`). Each page is read at once, in
  its own cell. **`G-P9`, `pread 0 1 2`**, is the detector's positive control (4 reads and 2
  writes more, `arith43c.out`): the scan rows and `lde` can see a PHY left on page 1 only if
  registers 0–5 are paged, and `G-PCTL` sets page 1's register 2 against page 0's (`001C`) —
  `pctl blind no`, the detector can see it; **`pctl blind yes`, it cannot: then a `scan 0 4`
  equal to (e)'s and an `lde` Δ 0, here and in P8, say nothing about a PHY left on page 1**
  (§ 7), while a difference still refutes. Then `scan 0 4` equals (e)'s rows 0–4 and `G-SWD`
  reads `lde` Δ 0 at every port — the detector for a paged write landing on the wrong page,
  valid only if `A-IF` read `0` and `1` (`G-SWD` prints both again). **`C-18`'s rule**,
  decision D (§ 10.7): `C-18` reopens if PHY 1's page-1 register 19 bits 15:1 differ from the
  value PHYs 0, 2, 3 and 4 agree on (void if those four disagree), or if a port-1 link fault is
  ever observed; PHY 4's page-1 register 20 is recorded only and triggers nothing. **Refuted
  by** `dirty` ≠ 0, or `p1` ≠ 0 on a read that made its select (a restore that did not verify:
  § 6 stops every MDIO cell); `rs` ≠ 0 on a read that made its select; with the select shown,
  bits 15:13 other than `110` or a bit 0 set; the accounting other than the eight `pread`s'
  costs with `retry` 0; a `scan 0 4` row unlike (e)'s, or an `lde` Δ ≥ 1.

### 3.8 (g′): the vendor's `extRead`

* **P8** (`V-CUT`, `V-IFS`, `V-IF`, `V-GO`, `V-X0` … `V-X4`, `V-SC`, `V-SW`, `V-CMP`, `V-R04`,
  `V-SWD`). `I-V` starts only past three gates: its cut point, `V-IF` (`V-IFS`, an `ifconfig`
  typed at `I-V`'s start, reads `0` and `1`: no vendor `eth` whose timer could write page 0
  inside `extRead`'s window — seconds before the first `extRead`, not minutes) and `V-GO`
  (`G-SC`'s rows 0–4 equal `E-SC`'s: no PHY left off page 0 by (g)).
  `extRead phyId(N), pageId(1), regId(19), regData:0x…` for N = 0–4 (a reading each; then
  rlxfw's page, its gates), each equal to (g)'s `v` for that PHY where (g)'s read made its
  select and the select is shown (decision B's second source; otherwise `not compared`, and a
  missing reply `unmeasured`). That path pages with no gate, no IRQs off and an unbounded poll,
  and restores page 0 unconditionally (讀 `rtl865x_proc_debug.c`, a cardnum row), which is why
  it runs after (g). `V-R04` sets `V-SC`'s rows 0–4 against `E-SC`'s (equal predicted) and
  `V-SWD` reads `lde` Δ 0: the vendor's restore, detected as (g)'s is, and, where `G-PCTL`
  reads `blind yes`, an equality that says nothing about a PHY left on page 1. **Refuted by** a
  compared `extRead` value unlike (g)'s `v` (one of the two paths misreads page 1, or the two
  select differently), or a `V-SC` row unlike (e)'s (a PHY left off page 0 by the vendor's
  path).

### 3.9 (j): `lock`, the final page, the chain

* **P9** (`J-LK`, `J-PR`, `J-FIN`, `J-CH`). `unlocked 0`, `dirty 0`, `wr_refused 0`, `mdio_to`
  and `busy` as on the last unlocked page and as on `F-S1` (plus one `mdio_to` for each of
  (g)'s `pread`s that timed out at rest and one `busy` for each refused busy); the final
  `probe` refused: `cat: write error: Operation not permitted` (a reading), `refused` +1, no
  MDIO command; `spin`'s count = `mdio_rd` + `mdio_wr` − `mdio_to`. **When every block ran**,
  `mdio_rd` 307 − (f)'s Δ`busy` − 3k − b (303 under K7's model with k 0) and `mdio_wr` 16 − 2k
  (`arith43c.out`); on a path that skipped a block (a cut point, `V-IF`, `V-GO` or `C-PR`
  failing) these absolutes are path-dependent, `J-CH` prints `chain final: path-dependent`, and
  only the deltas below are predicted. `J-FIN` (`mdpage final`) sets `J-PR` against the last
  page before `lock` that the run left — `V-SC` when every block ran, else `D-MD`, `G-SC` or
  `F-S1` — never a fixed name, so a skipped block is read, not refused. `J-CH` (`mdpage chain`)
  sets every page from `A-MD` to `J-PR` against the counter model, cell by cell — every delta
  and the absolutes — reading a stand-in page where one was typed, a cell with no log as not
  run (Δ 0), and a span it cannot model (a page missing where the model needs its own `pr` line
  or `F-S0`'s counts) as not modelled. **Refuted by** any of these otherwise (`j REFUTED …`,
  `chain verdict differs at …`).

### 3.10 The host path and the maps

* **P10.** `A-FIXR` reads `txlen vendor`, `armed 1` and `nd_up 1` after `A-FIX` (§ 0 ⑦ (14)).
  Every liveness gate reads 4 of 4 and `follower 1` — before any MDIO verb, after (g)'s paged
  reads and after the vendor's, each on `rlx0` at `txlen vendor`; every kernel-log window's
  `bug_preempt` is counted (a reading). `R1-MB0` and `R1-MB1` read blocks 46–48's map digest
  (`0927be41…`), 31 groups the same and 1 `DIFFER` in group 0; `n_writes 0`, which carries no
  information about writes (`FW-142`); `recipe_id 50E4AF55`. `n_write_refused` reads 0 at
  `R1-NW0` and at `R1-NW1`, Δ 0 (`Z-NWR`, a reading): it moves only in the SPI driver's MTD
  write and erase stubs (讀 `rtl819x-spi.c`, two sites, a cardnum row), and this card types no
  `trywrite`, no `mfgtest` and no MTD write (cardnum rows count zero; block 48 read 0 and 0,
  量); a move is a refusal the card did not cause, recorded, and the guard working. **Refuted
  by** a liveness failure after (g) or (g′) with (a)'s link up: S1 classifies it from the board
  before the host is touched, and a paged write that broke port 3's link is what it would then
  record.

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck` refuses
the verbs (`FW-113`); the loader cells are `MDIOR 2` and `MDIOR 3` and nothing else; every
upload is `looprun`'s. 🔴 Every `--send`, the X-cells' included, is at most 127 characters,
holds no `$`, and holds no upper-case word but the loader cells' (the generator refuses a macro
name in any). 🔴 **No gate reads console text** (`FW-47`; a cardnum row counts zero mark gates
and zero vendor-reply gates). 🔴 **Every board cell's `--until` carries the reset banner**
(`Booting\.\.\.|---RealTek`), **no Linux cell carries `--esc-after`**, and **`X-W<n>` and
`X-OFF<n>` are cards A and B's watch and power-off forms exactly** (`mdioverb43c` V11,
`inv43c.sh`'s `WTEXT` and `OTEXT`, cardnum rows). 🔴 **The MDIO verbs**:
`unlock mdio-i-mean-it`, `lock`, `probe`, `bound 0` and `bound 10000`, `scan lo hi`,
`pread a 0|1 reg` — each routed through `cat` and followed by the page in the same line; the
one-shot `probe` before any `bound` verb in the card's order, after a page that read
`bound 10000`; no page-1 `pread` without a `bound 10000` page before it in its invocation;
every page-1 `pread` cell gates `dirty 0`; no X-cell types a verb (the page only: a verb is
never typed twice); `mdioverb43c.py` refuses a card otherwise (`R0-VERB`). 🔴 **The vendor's
`phyReg`**: `read N 2`, `read N 3` and `extRead N 1 19` only, N 0–4, each behind `sleep 1` and
ending on rlxfw's page; S1's `X-PHY<n>` alone adds `read 3 0` and `read 3 1` (port 3's `BMCR`
and `BMSR`, read-only, S1's branch b only). 🔴 **rlxfw's switch page before the vendor's
`port_status`**, which runs once on the card, last (`Z-PS`), and otherwise only last in S1's
read set: the vendor's reader clears bit 8 without recording it. 🔴 No cell writes
`/proc/rtl819x-switch`, `/proc/rtl819x-nic` or `/proc/rtl819x-spi` but the map's `map 0` and
`A-FIX`, block 50's fix typed once before the opening bracket — `rlx0` down, `txlen vendor`,
`arm`, `rlx0` up (§ 0 ⑦ (14); cardnum rows count that one line and no other `/proc/rtl819x-nic`
write or `ifconfig` change). 🔴 No cell touches the reset button or the watchdog. 🔴 **No line of
the host's kernel log reaches `bench/`**: only `dmesgwin`'s counts. 🔴 Exactly one `dmesg`
process, the off-card follower, runs from before `I-0` to after `I-Z`. ⚠️ Off-card cells are
declared in `bench/2026-09-27c/CORRECTIONS-block51.md` before they run, except the X-cells § 6
fixes now (each still logged there as it runs) and a power-off, which § 6 decides now.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-27c/ --skip S2,S3,S4 --recipe-override 50e4af55 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/kroot/rtkload/nfjrom --image-sha256 548f4fae6682c295afa838e47d04db7bae13dbde06927447cce7fed4e17c8d53`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 46's, unchanged
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets /sys/class/net/eth0/statistics/tx_packets ; grep -e '^Icmp:' -e '^Udp:' /proc/net/snmp` — card B's
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — the liveness probe: 60-B frames, clean at every setting
`DMW <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py window /home/key/fwre-work/rebuild/s114/host43c/dmesg-w43c.log --prev <prev>`
`MDP` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s114/card43c/mdpage.py`
`SWP` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s114/card43c/swpage13.py`
`S1C` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/shared/s1class.py classify` — § 6's S1 only
`CUT` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43b/cutgate.py decide` — card B's cut points, pinned
`IFC <cap>` = `tr -d '\r' < <cap>.log | grep -c -E '^(eth|wlan|br)[0-9]' ; tr -d '\r' < <cap>.log | grep -c '^rlx0 ' ; true` — `ifconfig`'s two counts: `0` and `1` predicted
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — block 46's, unchanged

A page cell sends one line — the verb through `cat`, then `cat /proc/rtl819x-mdio` — and ends
on the page's `jiffies` line and the prompt (`--until`, 15-s cap), or on the reset banner; a
switch page ends on its table's last row; a vendor `phyReg` cell sends `sleep 1`, its reads and
the page, and ends on the page. The `--idle` cells (`R1-PS`, `A-IF`, `R1-NW0`, `A-FIX`,
`C-SYS`, `V-IFS`, `Z-PS`, `R1-NW1`) end on `--idle 3`, their `--until` the banner alone, and
their terminator is the shell's prompt after the line they sent. A stall with IRQs off cuts one
short: nothing is echoed, so its capture is empty. Where a gate needs that capture's output —
the cell's own (`R1-PS`, `R1-NW0`, `R1-NW1`) or a host cell's (`V-IF` on `V-IFS`) — it fails at
once, and § 6 sends that stop to the unterminated-cell rule, not to the cell's own rule; a cell
whose output no gate needs (`A-IF`, `A-FIX`, `C-SYS`, `Z-PS`) passes. So every `--idle` board
cell but the last of `I-1` and of `I-Z` is followed, in its own invocation, by a cell whose
`--until` needs the board's output (§ 0 ⑤ counts the span, and the wrapper's start-up or the
tail watch after those two, as if every `--idle` cell passed). The maps end on `map_lines` or
the banner with a 60-s cap. The loader cells end on `RealTek>` with a 25-s cap. Every
kernel-log reader passes `dmesgwin` a `--prev` list naming every earlier window in run order
(it reads the last that exists).

### Before power

```
CAP --out bench/2026-09-27c/R0-PRE --seconds 3
HOST bench/2026-09-27c/R0-PREC :: ls bench/2026-09-27c/R0-PRE.log bench/2026-09-27c/R0-PRE.timing bench/2026-09-27c/R0-PRE.meta.json && cat bench/2026-09-27c/R0-PRE.meta.json
HOST bench/2026-09-27c/R0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-27c/R0-DMSG :: pgrep -xc dmesg ; true
HOST bench/2026-09-27c/R0-DW0 :: DMW none
HOST bench/2026-09-27c/R0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-27c/R0-SUM :: sha256sum < /home/key/fwre-work/rebuild/s114/card43c/mdpage.py ; sha256sum < /home/key/fwre-work/rebuild/s114/card43c/swpage13.py ; sha256sum < /home/key/fwre-work/rebuild/s114/card43c/mdioverb43c.py ; sha256sum < /home/key/fwre-work/rebuild/s114/card43c/arith43c.py ; sha256sum < /home/key/fwre-work/rebuild/s114/card43c/mkswpage13.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ; sha256sum < /home/key/fwre-work/rebuild/s113/shared/s1class.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43b/cutgate.py ; sha256sum < tools/mdiocheck.py
HOST bench/2026-09-27c/R0-ST :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s114/card43c/mdpage.py --self-test --source /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s114/card43c/swpage13.py --self-test --source /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/shared/s1class.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43b/cutgate.py --self-test
HOST bench/2026-09-27c/R0-VERB :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s114/card43c/mdioverb43c.py bench/2026-09-27c/PREDICTIONS-B53-block51.md ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s114/card43c/mdioverb43c.py --self-test bench/2026-09-27c/PREDICTIONS-B53-block51.md
HOST bench/2026-09-27c/R0-H :: HN
```

### The latest-catch gate, just before the owner is told

```
HOST bench/2026-09-27c/T-LATE :: CUT --catch bench/2026-09-27c/R0-PRE.meta.json --date 2026-09-27 --start-by 23:43
```

### The press — the latest-catch gate again, the catch, L1–L2 at the caught prompt, the round

```
HOST bench/2026-09-27c/T-CATCH :: CUT --catch bench/2026-09-27c/R0-PRE.meta.json --date 2026-09-27 --start-by 23:45
CAP --out bench/2026-09-27c/R1-CATCH --esc-after 360 --esc-period 0.002 --until '<RealTek>' --seconds 380
CAP --out bench/2026-09-27c/L1-MD2 --send 'MDIOR 2' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-27c/L2-MD3 --send 'MDIOR 3' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
HOST bench/2026-09-27c/L-RD :: MDP loader bench/2026-09-27c/L1-MD2.log bench/2026-09-27c/L2-MD3.log
HOST bench/2026-09-27c/R1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-27c/R1Q :: LR --cell R1Q QIMG --iterations 1
CAP --out bench/2026-09-27c/R1-PS --send 'ps' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 30
HOST bench/2026-09-27c/R1-SW7 :: grep -a -o 'RLXFW-SW7=[0-9A-F]*' bench/2026-09-27c/R1Q-boot.log ; true
```

### (a) and (b): rlxfw's switch page first, then the MDIO page still locked; the map, `n_writes`, the opening bracket

```
CAP --out bench/2026-09-27c/A-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27c/A-IF --send 'ifconfig' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27c/A-IFR :: IFC bench/2026-09-27c/A-IF
HOST bench/2026-09-27c/A-SWP :: SWP page bench/2026-09-27c/A-SW.log
CAP --out bench/2026-09-27c/A-MD --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/A-MDC :: MDP mdcio bench/2026-09-27c/A-SW.log
HOST bench/2026-09-27c/A-MDP :: MDP boot bench/2026-09-27c/A-MD.log
CAP --out bench/2026-09-27c/R1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-27c/R1-MB0 :: MB bench/2026-09-27c/R1-M0
CAP --out bench/2026-09-27c/R1-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/A-NIC0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/A-FIX --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27c/A-FIXR --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/B-00-P :: HP
CAP --out bench/2026-09-27c/B-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/B-00-H :: HN
HOST bench/2026-09-27c/B-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27c/R0-DW0.log
```

### (c): the guards and the probe

```
CAP --out bench/2026-09-27c/C-P0 --send 'echo probe | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/C-UN --send 'echo unlock mdio-i-mean-it | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/C-PR --send 'echo probe | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/C-SYS --send 'ls /sys/bus/mdio_bus/devices' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27c/C-SYR :: MDP sys bench/2026-09-27c/C-SYS.log
CAP --out bench/2026-09-27c/C-PR2 --send 'echo probe | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
```

### (e): `scan 0 31`

```
CAP --out bench/2026-09-27c/E-SC --send 'echo scan 0 31 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/E-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27c/E-RW :: MDP rows bench/2026-09-27c/E-SC.log ; MDP fpred bench/2026-09-27c/E-SC.log
```

### (f): the timeout's positive control

```
CAP --out bench/2026-09-27c/F-B0 --send 'echo bound 0 | cat > /proc/rtl819x-mdio ; echo pread 0 0 16 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/F-S0 --send 'echo scan 5 5 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/F-B1 --send 'echo bound 10000 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/F-S1 --send 'echo scan 5 5 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/F-AC :: MDP facct bench/2026-09-27c/E-SC.log bench/2026-09-27c/F-S0.log bench/2026-09-27c/F-B1.log bench/2026-09-27c/F-S1.log
```

### (g): `C-18` — its cut point, eight `pread`s and the control, then the detector

```
HOST bench/2026-09-27c/G-CUT :: CUT --catch bench/2026-09-27c/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 3
CAP --out bench/2026-09-27c/G-P1 --send 'echo pread 0 0 16 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P2 --send 'echo pread 0 1 16 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P3 --send 'echo pread 0 1 19 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P4 --send 'echo pread 1 1 19 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P5 --send 'echo pread 2 1 19 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P6 --send 'echo pread 4 1 19 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P7 --send 'echo pread 3 1 19 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P8 --send 'echo pread 4 1 20 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-P9 --send 'echo pread 0 1 2 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-SC --send 'echo scan 0 4 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/G-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27c/G-C18 :: MDP c18 bench/2026-09-27c/F-S1.log bench/2026-09-27c/G-P8.log bench/2026-09-27c/E-SC.log bench/2026-09-27c/G-SC.log
HOST bench/2026-09-27c/G-PCTL :: MDP pctl bench/2026-09-27c/G-P8.log bench/2026-09-27c/G-P9.log bench/2026-09-27c/E-SC.log
HOST bench/2026-09-27c/G-SWD :: SWP delta bench/2026-09-27c/E-SW.log bench/2026-09-27c/G-SW.log ; IFC bench/2026-09-27c/A-IF
HOST bench/2026-09-27c/G-99-P :: HP
CAP --out bench/2026-09-27c/G-99-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/G-99-H :: HN
HOST bench/2026-09-27c/G-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27c/R0-DW0.log,bench/2026-09-27c/B-L.log
```

### (d): the vendor's reads of registers 2 and 3, after (g), and `D7`

```
CAP --out bench/2026-09-27c/D-V0 --send 'sleep 1 ; echo read 0 2 > /proc/rtl865x/phyReg ; echo read 0 3 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/D-V1 --send 'sleep 1 ; echo read 1 2 > /proc/rtl865x/phyReg ; echo read 1 3 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/D-V2 --send 'sleep 1 ; echo read 2 2 > /proc/rtl865x/phyReg ; echo read 2 3 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/D-V3 --send 'sleep 1 ; echo read 3 2 > /proc/rtl865x/phyReg ; echo read 3 3 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/D-V4 --send 'sleep 1 ; echo read 4 2 > /proc/rtl865x/phyReg ; echo read 4 3 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/D-MD --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/D-D7 :: MDP d7 bench/2026-09-27c/L1-MD2.log bench/2026-09-27c/L2-MD3.log bench/2026-09-27c/C-PR.log bench/2026-09-27c/D-V0.log bench/2026-09-27c/D-V1.log bench/2026-09-27c/D-V2.log bench/2026-09-27c/D-V3.log bench/2026-09-27c/D-V4.log
```

### (g′): its cut point, a fresh `ifconfig` and two gates, the vendor's `extRead`, then the detector

```
HOST bench/2026-09-27c/V-CUT :: CUT --catch bench/2026-09-27c/R1-CATCH.meta.json --date 2026-09-27 --end-by 23:52 --need 2
CAP --out bench/2026-09-27c/V-IFS --send 'ifconfig' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27c/V-IF :: IFC bench/2026-09-27c/V-IFS
HOST bench/2026-09-27c/V-GO :: MDP rows04 bench/2026-09-27c/E-SC.log bench/2026-09-27c/G-SC.log
CAP --out bench/2026-09-27c/V-X0 --send 'sleep 1 ; echo extRead 0 1 19 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/V-X1 --send 'sleep 1 ; echo extRead 1 1 19 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/V-X2 --send 'sleep 1 ; echo extRead 2 1 19 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/V-X3 --send 'sleep 1 ; echo extRead 3 1 19 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/V-X4 --send 'sleep 1 ; echo extRead 4 1 19 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/V-SC --send 'echo scan 0 4 | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/V-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-27c/V-CMP :: MDP vend bench/2026-09-27c/G-P8.log bench/2026-09-27c/V-X0.log bench/2026-09-27c/V-X1.log bench/2026-09-27c/V-X2.log bench/2026-09-27c/V-X3.log bench/2026-09-27c/V-X4.log
HOST bench/2026-09-27c/V-R04 :: MDP rows04 bench/2026-09-27c/E-SC.log bench/2026-09-27c/V-SC.log
HOST bench/2026-09-27c/V-SWD :: SWP delta bench/2026-09-27c/G-SW.log bench/2026-09-27c/V-SW.log ; IFC bench/2026-09-27c/V-IFS
HOST bench/2026-09-27c/V-99-P :: HP
CAP --out bench/2026-09-27c/V-99-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/V-99-H :: HN
HOST bench/2026-09-27c/V-L :: FL 10.1.1.3 ; PL ; DMW bench/2026-09-27c/R0-DW0.log,bench/2026-09-27c/B-L.log,bench/2026-09-27c/G-L.log
```

### (j): `lock`, the final page, a final `probe`, the chain

```
CAP --out bench/2026-09-27c/J-LK --send 'echo lock | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-27c/J-PR --send 'echo probe | cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/J-FIN :: MDP final bench/2026-09-27c/
HOST bench/2026-09-27c/J-CH :: MDP chain bench/2026-09-27c/
```

### The closing page, `port_status`, the map, `n_writes`, the kernel log

```
CAP --out bench/2026-09-27c/Z-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-27c/Z-PS --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-27c/R1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-27c/R1-MB1 :: MB bench/2026-09-27c/R1-M1
CAP --out bench/2026-09-27c/R1-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27c/Z-NWR :: tr -d '\r' < bench/2026-09-27c/R1-NW0.log | grep '^n_write_refused ' ; tr -d '\r' < bench/2026-09-27c/R1-NW1.log | grep '^n_write_refused ' ; true
HOST bench/2026-09-27c/Z-DW :: DMW bench/2026-09-27c/R0-DW0.log,bench/2026-09-27c/B-L.log,bench/2026-09-27c/G-L.log,bench/2026-09-27c/V-L.log
HOST bench/2026-09-27c/Z-DWALL :: DMW none
```

---

## § 6 How the cells are run

**Before any cell** (none of it a cell), after card B's press and its power-off, in this order:
(1) no other WSL job is running; (2) `wsl --shutdown` from PowerShell, then the keeper
`wsl -d Ubuntu-24.04 -- sleep 36000` in the background; (3) the kernel-log follower, from
PowerShell in the background:
`wsl -d Ubuntu-24.04 -- bash -c "mkdir -p /home/key/fwre-work/rebuild/s114/host43c && exec dmesg -w > /home/key/fwre-work/rebuild/s114/host43c/dmesg-w43c.log"`,
started before the attach so the attach is in the log; (4) `usbipd list`, read fresh, then
`usbipd attach` of the CP2102 and of the GbE adapter, reading what each prints; (5) in WSL,
from the repository root, with this card committed at `bench/2026-09-27c/` (`runblock` runs
only a tracked card equal to `HEAD`) and `bench/README.md`'s row for its directory (`capdate`
D4): `mkdir -p /home/key/fwre-work/rebuild/s114/run43c`;
`/usr/bin/python3 tools/cardcheck.py numbers` and `commands` on this card;
`/usr/bin/python3 tools/check-predictions.py` on this card, reading
**`0 of 110 captures came after the prediction, 110 did not`**; every invocation once through
`inv43c.sh --dry`, each ending `ALL ITEMS DONE`. **The catch window opens no later than 23:45
on 2026-09-27** (§ 2; `I-T` refuses after 23:43 and `T-CATCH` after 23:45); later, the card is
re-dated before power.

**The command lines** (cards A and B's). Every invocation runs through
`bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh NAME [TAG] [--from CELL]`, which runs
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log /home/key/fwre-work/rebuild/s114/run43c/run-NAME[-TAG].log`
and appends `INVOCATION NAME[-TAG] rc=N` to `/home/key/fwre-work/rebuild/s114/run43c/rc.tsv`,
in the order `I-0`, `I-T`, `I-1`, `I-A`, `I-C`, `I-E`, `I-F`, `I-G`, `I-D`, `I-V`, `I-J`, `I-Z`
— never out of that order, and no cell twice (the runner refuses a cell whose record exists).
`NAME?` marks a cell whose non-zero exit is a reading; `gate:` items are the decision points; a
failed cell or gate stops its own invocation. `I-0` and `I-T` run alone, in the foreground,
before power. The press is command lines, each a script file under
`/home/key/fwre-work/rebuild/s114/run43c` run by path in the session's background (from
PowerShell, `wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s114/run43c/L<k>.sh`), its
first line a `cd` to the repository root: its steps chained with `&&`, so that any stop ends
the line, then `;` and the line's tail watch `--tail X-W<n>`, which runs however the line
ended; a later line's first step stops the watch the line before left running
(`--stop X-W<n>`), after `--hold` wherever a stop came before (*The hold after a stop*). No gap
inside a line waits on the session's turn: between two invocations the board idles for the
wrapper's start-up (block 50: 0.35–0.47 s). The session follows each line's output and its run
logs: a line has ended when its tail watch's `XCELL X-W<n> running` line appears, or when the
watch reports the loader's prompt (the loader rule below). Watches and windows are numbered
from 1 in the order they open, and no name is ever re-used. **Every X-cell this section fixes
runs through the same wrapper**:
`bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh --x X-NAME "TEXT"`, TEXT the X-cell's
text in the fence below with `<n>` and its other placeholders filled, the card's macros
expanded by `cardrun`'s own `expand`; a `CAP` X-cell runs under the SIGINT shim with its
`--out` `bench/2026-09-27c/X-NAME` and exits 5 if its capture holds loader text, any other
writes `bench/2026-09-27c/X-NAME.log`, neither is ever re-run, and `XCELL X-NAME rc=N` goes to
`/home/key/fwre-work/rebuild/s114/run43c/rc.tsv`; `X-W<n>` and `X-OFF<n>` run only as
`--tail X-W<n>` and `--off X-OFF<n>`, whose texts are `inv43c.sh`'s `WTEXT` and `OTEXT`, the
fence's two lines (cardnum rows). `X-RE<n>`'s `usbipd` steps run as X-cells too, as
`usbipd.exe` through WSL's interop, as block 50 ran them; its attach issued inside the second
after a detach found no device (`CORRECTIONS-block50.md` § 1), so `X-RE<n>-relist` waits 3 s
and lists again before the attach. A capture of `usbipd`'s own lines can hold the host's WSL
NAT address, which `audit-bench-log` refuses: such a log is kept outside the repository (block
50's § 6).

`L1` — the press: started on the owner's reply to the press's ask; the owner is told to power on once its catch streams:

```sh
bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-1 \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-A \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-C \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-E \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-F \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-G \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-D \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-V \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-J \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh I-Z \
  ; bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh --tail X-W1
```

The power-off line, after `L1`'s end or wherever a stop below calls for one, on the owner's
reply to its ask (after a stop, the same line with the running watch's number and the next
unused ones):

```sh
bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh --stop X-W1 \
  && bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh --off X-OFF1 \
  ; bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh --tail X-W2
```

**The hold after a stop.** After any stop past the round with the board running a kernel — a
board cell's gate, a host gate, a cut point's refusal or any other — the tail watch holds the
console, before any board cell is typed and before any continuation starts, until at least 90 s
after the latest board capture's end: the newest capture in the card's directory that is not a
watch or a window, its `.meta.json`'s `end_real` or its `.log`'s last write, whichever is
later. 90 s is the bite as measured, 84.001 s (`CLK-08b`), plus the loader's 2.288 s from its
banner to its first prompt with ESC streaming (block 48's `R1-CATCH`), plus 3 s (a guess),
rounded up (`arith43c.out`'s `HOLD` line). The session never computes it: every line it starts
after a stop begins `bash /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh --hold`, which
waits beside the running watch, refuses (exit 2) if no console capture runs, and exits 5 if the
watch ended inside the hold (read its log: the loader rule). A continuation is such a line:
`--hold`, `--stop` of the running watch, then the stopped invocation `--from` a cell (a new
TAG) or the X-cells the rule below names, then the invocations after it in the press, then `;`
and the next watch. **At the loader's prompt no watch is opened**: a watch opened there ends
within about 1.3 s on the loader's own reply to its ESC (`Unknown command !` and its prompt;
block 48's `R1-CATCH`, 550 replies). So a watch or a window caught a reset only if the loader's
banner (`Booting...` or `---RealTek`) precedes its `<RealTek>` (`inv43c.sh` prints
`caught a reset`); a `<RealTek>` with no banner before it is the loader's reply
(`at the loader's prompt`). Either way the board is at the loader's prompt: no further watch is
opened, no line has `--hold` or `--stop`, and a power-off needs no window, since the loader
boots nothing by itself.

**Before the power-off is asked**, the session lists the board reads the path still owes and
runs them, on a continuation line, unless the path forbids typing: on the normal path none
(`I-Z` read the closing switch page, `port_status`, the map and `n_writes`); after a `dirty 0`
failure, `X-MD<n>` and `X-SW<n>`, then `I-J` and `I-Z`; after `C-PR`'s failure, `I-D`, `I-J`
and `I-Z`; after a cut point's refusal, `I-J` and `I-Z`; after S1, the read set and, on branch
b, `X-SW<n>b` and `X-L<n>b`, then the next invocation; after the unterminated-cell rule,
nothing (no shell command is typed). This card starts no board process that writes a file, so
nothing lives only in the board's RAM beyond what those reads capture.

```xcells
X-W<n> :: CAP --out bench/2026-09-27c/X-W<n> --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
X-OFF<n> :: CAP --out bench/2026-09-27c/X-OFF<n> --esc-after 360 --esc-period 0.01 --until '<RealTek>' --seconds 365
X-<page> :: CAP --out bench/2026-09-27c/X-<page> --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
X-<swpage> :: CAP --out bench/2026-09-27c/X-<swpage> --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
X-MD<n> :: CAP --out bench/2026-09-27c/X-MD<n> --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
X-SW<n> :: CAP --out bench/2026-09-27c/X-SW<n> --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
X-NIC<n> :: CAP --out bench/2026-09-27c/X-NIC<n> --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
X-HP<n> :: HP
X-BR<n> :: CAP --out bench/2026-09-27c/X-BR<n> --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
X-PS<n> :: CAP --out bench/2026-09-27c/X-PS<n> --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
X-HN<n> :: HN
X-C<n> :: S1C --nic bench/2026-09-27c/X-NIC<n>.log --br bench/2026-09-27c/X-BR<n>.log --prev-br <PREV> --pre bench/2026-09-27c/X-HP<n>.log --host <PREVH>
X-NIC<n>a :: CAP --out bench/2026-09-27c/X-NIC<n>a --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
X-L<n>a :: FL 10.1.1.3 ; PL ; DMW none
X-PHY<n> :: CAP --out bench/2026-09-27c/X-PHY<n> --send 'sleep 1 ; echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
X-RE<n>-list :: usbipd.exe list
X-RE<n>-detach :: usbipd.exe detach --busid <BUSID>
X-RE<n>-relist :: sleep 3 ; usbipd.exe list
X-RE<n>-attach :: usbipd.exe attach --wsl --busid <BUSID>
X-ADDR<n> :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
X-SW<n>b :: CAP --out bench/2026-09-27c/X-SW<n>b --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
X-L<n>b :: FL 10.1.1.3 ; PL ; DMW none
X-L<n> :: FL 10.1.1.3 ; PL ; DMW none
X-PRE<n> :: CAP --out bench/2026-09-27c/X-PRE<n> --until 'Booting\.\.\.|---RealTek' --seconds 3
```

In the fence, `<n>` numbers a stop's X-cells, from 1, in the order they run; `<page>` and
`<swpage>` are the stopped cell's name; `<PREV>` and `<PREVH>` are the bracket read just before
a failed liveness gate (`B-00-R`, `G-99-R` or `V-99-R`) and its `-H`; `<BUSID>` is the GbE
adapter's, read from `X-RE<n>-list` (never the CP2102's), and read again from `X-RE<n>-relist`
3 s after the detach: the attach runs only if it reads `Shared` there.

**The owner's actions** (§ 0 ⑪) — the press and the power-off. **The press**: `I-T` runs first,
in the foreground, and must end `cut permit`; then the session tells the owner the catch comes
next — it streams ESC for at most 360 s from its start and must open by 23:45 on 2026-09-27 (a
later reply re-dates the card) — and STOPS. On the reply it starts `L1` in the background;
`I-1`'s first cell, `T-CATCH`, refuses after 23:45 (then `R1-CATCH` never opens, the owner is
told not to press, and the card is re-dated before power); its second, `R1-CATCH`, streams ESC
from its start and ends at the loader's first prompt. The session reads `run-I-1.log` for
`RUN CAP   R1-CATCH`, sees `bench/2026-09-27c/R1-CATCH.timing` exist (`test -e`; 讀
`console-capture.py`: the capture creates it once the port is open, just before its ESC loop),
and only then tells the owner "catch open — power on now, by HH:MM:SS": that `RUN` line's time
of day plus 350 s. It says so only while that deadline is at least 40 s away; later, it tells
the owner not to press, the catch runs to its cap with the board off, `gate:caught` stops `L1`,
its tail watch runs against a board that is off, the session stops it once the owner has
confirmed no press was made, and the press is re-issued. A press after the catch's stream is
not caught by it: `gate:caught` fails, `L1` stops, and its tail watch `X-W1`, streaming ESC,
catches the loader if the press comes after it opens. **The power-off**, after `L1`'s end or
wherever a stop below calls for one — "at once" there means that this ask is the session's
first action: the tail watch holds the console while the session waits for the reply; on the
reply the session starts the power-off line (`--stop` of the running watch, `--off X-OFF<n>` —
360 s of ESC — then `;` and the next watch) in the background, reads its
`XCELL X-OFF<n> running` and `t0` lines, and only then tells the owner "power off now, by
HH:MM:SS", the `t0` time plus 360 s. The owner confirms the power-off in words, a report that
is data; the session then stops what still runs: `--stop X-OFF<n>` if the window still runs,
which lets the line's watch start, and that watch by `--stop` once its `XCELL … running` line
appears. If the window reaches its cap with no confirmation, the watch that follows it on its
line holds the console until the owner confirms. **At the loader's prompt** the power-off has
no window and no watch: after the owner's reply the session says "power off now" with nothing
to open or confirm. After a power-off nothing more is typed. **The bracket.** This card is
seating 43's last press, so nothing after it closes its flash bracket: on the normal path
`R1-M1`, `R1-MB1` and `R1-NW1` (`I-Z`) close it against `R1-M0`, `R1-MB0` and `R1-NW0` (`I-A`).
On a path that powers off before `I-Z` (the unterminated-cell rule below), the bracket stays
open: what the flash's map-visible bytes did between `R1-M0` and the power-off — a vendor boot
after an uncaught reset included — and the closing `n_writes` and `n_write_refused` are
unmeasured by this card, and the next seating's first map reads the flash after everything in
between, so it cannot assign a change to this press.

**`I-0`** — before power: the pre-flight, the address, one kernel-log follower and a clean log, the flush, the checkers' digests and self-tests, the MDIO-verb check of this card

```run
R0-PRE?
R0-PREC
gate:grep=^  "bytes": 0,$:R0-PREC
gate:grep=^  "duration_s": 3\.[01][0-9]*,$:R0-PREC
R0-ADDR
gate:grep=inet 10\.1\.1\.2/24:R0-ADDR
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
R0-SUM
gate:grep=^315fc36deb12feee36f7dfefed012d041e1dcb418a1644d923f3be77563d9f8d  -$:R0-SUM
gate:grep=^810d5d31077109cc97c2f0387c247005c2f1aa4a71d479ca82e222bcf929dd1f  -$:R0-SUM
gate:grep=^524f6cd5be7c64d66ff896b594b1131cd1e67e540d152f16b0f463f3bf3124f2  -$:R0-SUM
gate:grep=^7d6e9e037a24ad0ce59ec4016cfb4455730152c7676b64265133f27f50883057  -$:R0-SUM
gate:grep=^a3b4159e1afd739e68d8e2307135044536c417e585e5a1d4e18fc0ddd9e08eb9  -$:R0-SUM
gate:grep=^2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1  -$:R0-SUM
gate:grep=^fd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431  -$:R0-SUM
gate:grep=^f47f7f9bad9392bc83ed95d9bb2e515e0e0337ef102f112301004497ce0367eb  -$:R0-SUM
gate:grep=^3f7138667abbb6c2e559c3a7e3f14a946842f00faf7ee92d7b30691533bc6342  -$:R0-SUM
R0-ST
gate:grep=^mdpage\ self\-test:\ 71\ of\ 71\ passed$:R0-ST
gate:grep=^swpage13\ self\-test:\ 18\ of\ 18\ passed$:R0-ST
gate:grep=^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$:R0-ST
gate:grep=^s1class\ self\-test:\ 15\ of\ 15\ passed$:R0-ST
gate:grep=^cutgate\ self\-test:\ 17\ of\ 17\ passed$:R0-ST
R0-VERB
gate:grep=^mdioverb verdict PASS$:R0-VERB
gate:grep=^mdioverb\ self\-test:\ 25\ of\ 25\ passed$:R0-VERB
R0-H?
```

**`I-T`** — the latest-catch gate, run in the foreground just before the owner is told of the press: it refuses after 23:43 on 2026-09-27

```run
T-LATE
gate:grep=^cut permit$:T-LATE
```

**`I-1`** — the press, started in the background once the owner's reply has come; the owner presses only when told the catch is open: the latest-catch gate at 23:45, the catch, the loader's `MDIOR 2` and `MDIOR 3` at the caught prompt (L1-L2), the flush, one round to the shell, the process table, the boot's `SW7` mark read

```run
T-CATCH
gate:grep=^cut permit$:T-CATCH
R1-CATCH
gate:caught:R1-CATCH
L1-MD2
gate:until:L1-MD2
gate:caught:L1-MD2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|Linux version)):L1-MD2
gate:grep=^PhyID=0x1f Reg=2 Data =0x[0-9a-f]{4}$:L1-MD2
L2-MD3
gate:until:L2-MD3
gate:caught:L2-MD3
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|Linux version)):L2-MD3
gate:grep=^PhyID=0x1f Reg=3 Data =0x[0-9a-f]{4}$:L2-MD3
L-RD?
R1-FL
gate:grep=\A(?:0\n)+\Z:R1-FL
R1Q
R1-PS
gate:grep=^ *1 +\S+ +\S+ +\S+ +/bin/sh *$:R1-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-PS
R1-SW7?
```

**`I-A`** — (a) rlxfw's switch page first, the interfaces, (b) the MDIO page still locked; the opening map, `n_writes`, the opening bracket and liveness

```run
A-SW
gate:until:A-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A-SW
gate:grep=^version rtl819x-switch 1\.3$:A-SW
gate:grep=^psrp3 [0-9A-F]{8} up 1 lde \d+ lj \d+$:A-SW
A-IF
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A-IF
A-IFR?
A-SWP?
A-MD
gate:until:A-MD
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A-MD
gate:grep=^version rtl819x-switch 1\.3$:A-MD
gate:grep=^unlocked 0$:A-MD
gate:grep=^bus 0 reg_rc 1$:A-MD
gate:grep=^bound 10000$:A-MD
gate:grep=^mdio_rd 0$:A-MD
gate:grep=^mdio_wr 0$:A-MD
A-MDC?
A-MDP?
R1-M0
gate:until:R1-M0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-M0
R1-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:R1-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:R1-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:R1-MB0
R1-NW0
gate:grep=^n_writes 0$:R1-NW0
gate:grep=^recipe_id 50E4AF55$:R1-NW0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-NW0
A-NIC0
gate:until:A-NIC0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A-NIC0
gate:grep=^version rtl819x-nic 1\.5$:A-NIC0
A-FIX
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A-FIX
A-FIXR
gate:until:A-FIXR
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A-FIXR
gate:grep=^version rtl819x-nic 1\.5$:A-FIXR
gate:grep=^tx15 txlen vendor\b:A-FIXR
gate:grep=^armed 1$:A-FIXR
gate:grep=^nd_up 1$:A-FIXR
B-00-P?
B-00-R
gate:until:B-00-R
gate:grep=^version rtl819x-nic 1\.5$:B-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-00-R
gate:grep=^nd_up 1$:B-00-R
B-00-H?
B-L
gate:grep=^4 packets transmitted, 4 received:B-L
gate:grep=^follower 1$:B-L
```

**`I-C`** — (c) the probe refused while locked, the unlock, the probe, the sysfs names, a second probe

```run
C-P0
gate:until:C-P0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-P0
gate:grep=^version rtl819x-switch 1\.3$:C-P0
gate:grep=^unlocked 0$:C-P0
gate:grep=^bus 0 reg_rc 1$:C-P0
gate:grep=^mdio_rd 0$:C-P0
C-UN
gate:until:C-UN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-UN
gate:grep=^version rtl819x-switch 1\.3$:C-UN
gate:grep=^unlocked 1$:C-UN
gate:grep=^bus 0 reg_rc 1$:C-UN
gate:grep=^bound 10000$:C-UN
gate:grep=^mdio_rd 0$:C-UN
C-PR
gate:until:C-PR
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-PR
gate:grep=^version rtl819x-switch 1\.3$:C-PR
gate:grep=^bus 1 reg_rc 0$:C-PR
gate:grep=^dirty 0$:C-PR
C-SYS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-SYS
C-SYR?
C-PR2
gate:until:C-PR2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-PR2
gate:grep=^version rtl819x-switch 1\.3$:C-PR2
gate:grep=^bus 1 reg_rc 0$:C-PR2
```

**`I-E`** — (e) `scan 0 31`, the switch page after it, the rows against the prediction

```run
E-SC
gate:until:E-SC
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-SC
gate:grep=^version rtl819x-switch 1\.3$:E-SC
gate:grep=^scanned FFFFFFFF j \d+$:E-SC
gate:grep=^dirty 0$:E-SC
E-SW
gate:until:E-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-SW
gate:grep=^version rtl819x-switch 1\.3$:E-SW
E-RW?
```

**`I-F`** — (f) the timeout's positive control: `bound 0`, the page-0 `pread` refused, `scan 5 5`, `bound 10000`, `scan 5 5`

```run
F-B0
gate:until:F-B0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-B0
gate:grep=^version rtl819x-switch 1\.3$:F-B0
gate:grep=^dirty 0$:F-B0
F-S0
gate:until:F-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-S0
gate:grep=^version rtl819x-switch 1\.3$:F-S0
gate:grep=^dirty 0$:F-S0
F-B1
gate:until:F-B1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-B1
gate:grep=^version rtl819x-switch 1\.3$:F-B1
gate:grep=^bound 10000$:F-B1
gate:grep=^dirty 0$:F-B1
F-S1
gate:until:F-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):F-S1
gate:grep=^version rtl819x-switch 1\.3$:F-S1
gate:grep=^bound 10000$:F-S1
gate:grep=^dirty 0$:F-S1
F-AC?
```

**`I-G`** — (g) `C-18`: its cut point, eight `pread`s and the detector's control, each page read at once; `scan 0 4` and the switch page after them; the bracket and liveness

```run
G-CUT
gate:grep=^cut permit$:G-CUT
G-P1
gate:until:G-P1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P1
gate:grep=^version rtl819x-switch 1\.3$:G-P1
gate:grep=^bound 10000$:G-P1
gate:grep=^dirty 0$:G-P1
G-P2
gate:until:G-P2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P2
gate:grep=^version rtl819x-switch 1\.3$:G-P2
gate:grep=^bound 10000$:G-P2
gate:grep=^dirty 0$:G-P2
G-P3
gate:until:G-P3
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P3
gate:grep=^version rtl819x-switch 1\.3$:G-P3
gate:grep=^bound 10000$:G-P3
gate:grep=^dirty 0$:G-P3
G-P4
gate:until:G-P4
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P4
gate:grep=^version rtl819x-switch 1\.3$:G-P4
gate:grep=^bound 10000$:G-P4
gate:grep=^dirty 0$:G-P4
G-P5
gate:until:G-P5
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P5
gate:grep=^version rtl819x-switch 1\.3$:G-P5
gate:grep=^bound 10000$:G-P5
gate:grep=^dirty 0$:G-P5
G-P6
gate:until:G-P6
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P6
gate:grep=^version rtl819x-switch 1\.3$:G-P6
gate:grep=^bound 10000$:G-P6
gate:grep=^dirty 0$:G-P6
G-P7
gate:until:G-P7
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P7
gate:grep=^version rtl819x-switch 1\.3$:G-P7
gate:grep=^bound 10000$:G-P7
gate:grep=^dirty 0$:G-P7
G-P8
gate:until:G-P8
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P8
gate:grep=^version rtl819x-switch 1\.3$:G-P8
gate:grep=^bound 10000$:G-P8
gate:grep=^dirty 0$:G-P8
G-P9
gate:until:G-P9
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-P9
gate:grep=^version rtl819x-switch 1\.3$:G-P9
gate:grep=^bound 10000$:G-P9
gate:grep=^dirty 0$:G-P9
G-SC
gate:until:G-SC
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-SC
gate:grep=^version rtl819x-switch 1\.3$:G-SC
gate:grep=^dirty 0$:G-SC
G-SW
gate:until:G-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-SW
gate:grep=^version rtl819x-switch 1\.3$:G-SW
G-C18?
G-PCTL?
G-SWD?
G-99-P?
G-99-R
gate:until:G-99-R
gate:grep=^version rtl819x-nic 1\.5$:G-99-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):G-99-R
gate:grep=^nd_up 1$:G-99-R
G-99-H?
G-L
gate:grep=^4 packets transmitted, 4 received:G-L
gate:grep=^follower 1$:G-L
```

**`I-D`** — (d) the vendor's `phyReg` reads of registers 2 and 3 on PHYs 0-4, each ending on the page, after (g); `D7`

```run
D-V0
gate:until:D-V0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-V0
gate:grep=^version rtl819x-switch 1\.3$:D-V0
gate:grep=^dirty 0$:D-V0
D-V1
gate:until:D-V1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-V1
gate:grep=^version rtl819x-switch 1\.3$:D-V1
gate:grep=^dirty 0$:D-V1
D-V2
gate:until:D-V2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-V2
gate:grep=^version rtl819x-switch 1\.3$:D-V2
gate:grep=^dirty 0$:D-V2
D-V3
gate:until:D-V3
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-V3
gate:grep=^version rtl819x-switch 1\.3$:D-V3
gate:grep=^dirty 0$:D-V3
D-V4
gate:until:D-V4
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-V4
gate:grep=^version rtl819x-switch 1\.3$:D-V4
gate:grep=^dirty 0$:D-V4
D-MD
gate:until:D-MD
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-MD
gate:grep=^version rtl819x-switch 1\.3$:D-MD
gate:grep=^dirty 0$:D-MD
D-D7?
```

**`I-V`** — (g') its cut point, a fresh `ifconfig` showing no `eth`, (g)'s scan equal to (e)'s; the vendor's `extRead N 1 19`, N = 0-4, then `scan 0 4`, the switch page, the bracket and liveness

```run
V-CUT
gate:grep=^cut permit$:V-CUT
V-IFS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-IFS
V-IF
gate:grep=\A0\n1\n\Z:V-IF
V-GO
gate:grep=^rows04 equal yes, 5 of 5$:V-GO
V-X0
gate:until:V-X0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-X0
gate:grep=^version rtl819x-switch 1\.3$:V-X0
gate:grep=^dirty 0$:V-X0
V-X1
gate:until:V-X1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-X1
gate:grep=^version rtl819x-switch 1\.3$:V-X1
gate:grep=^dirty 0$:V-X1
V-X2
gate:until:V-X2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-X2
gate:grep=^version rtl819x-switch 1\.3$:V-X2
gate:grep=^dirty 0$:V-X2
V-X3
gate:until:V-X3
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-X3
gate:grep=^version rtl819x-switch 1\.3$:V-X3
gate:grep=^dirty 0$:V-X3
V-X4
gate:until:V-X4
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-X4
gate:grep=^version rtl819x-switch 1\.3$:V-X4
gate:grep=^dirty 0$:V-X4
V-SC
gate:until:V-SC
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-SC
gate:grep=^version rtl819x-switch 1\.3$:V-SC
gate:grep=^dirty 0$:V-SC
V-SW
gate:until:V-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-SW
gate:grep=^version rtl819x-switch 1\.3$:V-SW
V-CMP?
V-R04?
V-SWD?
V-99-P?
V-99-R
gate:until:V-99-R
gate:grep=^version rtl819x-nic 1\.5$:V-99-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):V-99-R
gate:grep=^nd_up 1$:V-99-R
V-99-H?
V-L
gate:grep=^4 packets transmitted, 4 received:V-L
gate:grep=^follower 1$:V-L
```

**`I-J`** — (j) `lock`, the final page, a final `probe` refused, the counter chain

```run
J-LK
gate:until:J-LK
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):J-LK
gate:grep=^version rtl819x-switch 1\.3$:J-LK
gate:grep=^unlocked 0$:J-LK
gate:grep=^dirty 0$:J-LK
J-PR
gate:until:J-PR
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):J-PR
gate:grep=^version rtl819x-switch 1\.3$:J-PR
gate:grep=^unlocked 0$:J-PR
J-FIN?
J-CH?
```

**`I-Z`** — the closing switch page, the vendor's `port_status` last, the map, `n_writes` and the kernel log's last window; then the power-off (§ 6)

```run
Z-SW
gate:until:Z-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):Z-SW
gate:grep=^version rtl819x-switch 1\.3$:Z-SW
Z-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):Z-PS
R1-M1
gate:until:R1-M1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-M1
R1-MB1
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:R1-MB1
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:R1-MB1
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:R1-MB1
R1-NW1
gate:grep=^n_writes 0$:R1-NW1
gate:grep=^recipe_id 50E4AF55$:R1-NW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-NW1
Z-NWR?
Z-DW?
Z-DWALL?
```

**What each stop means, decided now** — a repeat is always a new name, declared in
`bench/2026-09-27c/CORRECTIONS-block51.md` before it runs, **except the X-cells whose text this
section fixes now (they are logged there as they run) and a power-off, which this card
decides**:

* **The unterminated-cell rule — a board cell (any cell after the round, X-cells included) that
  ended without its terminator, or whose capture holds loader text.** Without its terminator:
  its `until` gate failing (the cap reached with neither its terminator nor the banner); for an
  `--idle` cell, whose terminator is the shell's prompt, its capture holding no prompt (`\n# `,
  `\r` stripped) after the line it sent — a stall with IRQs off echoes nothing, so the capture
  is empty. Whenever an `--idle` cell's output stops the run, the session reads that first: a
  gate that needs the output — the own gates of `R1-PS`, `R1-NW0`, `R1-NW1`, or `V-IF` on
  `V-IFS` — failing on such a capture is this rule's trigger, and the cell's own rule does not
  apply. An `--idle` cell whose output no gate needs (`A-IF`, `A-FIX`, `C-SYS`, `Z-PS`) passes
  on such a capture; the next cell whose `--until` needs the board's output then fails at its
  cap, and that is the trigger (§ 0 ⑤ counts the span). Loader text: `Booting...`,
  `---RealTek`, `<RealTek>` or `Linux version` in any board capture (the loader gate), a cell
  whose `--until` matched the banner included. **The line's tail watch is then already
  streaming** — its `;` opened it the moment the runner stopped; the session's first action is
  to see its `XCELL X-W<n> running` line (a watch that ended on `<RealTek>`: the loader rule of
  *The hold after a stop*) — **then the power-off** above, with no hold. No shell command is
  typed after it: not a stand-in page, not a vendor read, and `I-Z` does not run (the bracket
  stays open, above). Why (§ 0 ⑤): a stall with IRQs off that outlives 83.8 s resets the board
  into the vendor's firmware, a cell that ended without its terminator is the one state here
  that can hold one, and the tail watch has 20.1 s at worst to open (block 50: 0.23–0.24 s); a
  vendor poll that never ends holds the kernel with IRQs on and cannot bite (推), and `X-W<n>`
  costs nothing on that path.
* **`R0-*`**: no power until each reads as its gate asks (`R0-PREC`, `R0-ADDR`, `R0-DMSG`,
  `R0-DW0`, `R0-FL`, `R0-SUM`, `R0-ST`, `R0-VERB`: card B's rules).
* **`I-T`** (`T-LATE`: `cut refuse start-by`, or `cutgate` refusing to decide): the owner is
  not asked; the card is re-dated before power (the generator's `--date`) and every `R0-*` cell
  of the new card runs again. **`T-CATCH`** (`I-1`'s first cell) refusing the same way:
  `R1-CATCH` never opens, the owner is told not to press, and the card is re-dated as above.
* **`gate:caught` on `R1-CATCH`**, **`R1-FL`**, **`R1Q`**, **`R1-PS`**, the maps and
  `n_writes`: exactly as block 46's § 6 decides them (block 48's words), with cards A and B's
  rule for `gate:caught`: `L1` stops and its tail watch holds the console (*The owner's
  actions*); the unterminated-cell rule first wherever it applies.
* **L1, L2** (`L1-MD2`, `L2-MD3`). The no-reset gate failing (banner text in the capture: the
  `MDIOR` reset the board): if the capture still ends at a caught `<RealTek>`, `I-1` continues
  `--from R1-FL` — the boot that follows is warm and recorded as such, the register not read is
  unmeasured, and P1's slot-0 prediction is void; if not caught, the unterminated-cell rule.
  `until`, `caught` or the 32nd-line gate failing with no banner text: the capture is read; if
  it ends at `<RealTek>`, `I-1` continues `--from` the next cell (`L2-MD3`, or `L-RD`), that
  register unmeasured and `D7` void where it is missing; if it does not, the loader hangs in
  its unbounded MDIO wait (`NET-17`): the unterminated-cell rule, and that is the reading.
* **`A-SW`** (not 1.3's page, or `psrp3` not up): no cell after it until the owner has read it.
  **`A-MD`** (not the boot state, P2): no MDIO or `phyReg` cell runs this press; after the
  owner has read it, `I-A` continues `--from R1-M0`, and then `I-Z`.
* **`A-NIC0`, `A-FIX`, `A-FIXR`** (the fix, § 0 ⑦ (14)): loader text in any of them, or
  `A-NIC0`'s or `A-FIXR`'s `until` failing, is the unterminated-cell rule; `A-FIXR` not reading
  `txlen vendor`, `armed 1` or `nd_up 1`, or a `version` gate failing, with the terminator
  seen: no cell after it until the owner has read it — the press goes on without the fix only
  on the owner's word, its livenesses then on whatever `A-FIXR` shows.
* **`C-P0`** (the locked probe not refused): no rlxfw MDIO cell after it; `I-D`'s vendor reads
  and `I-Z` run on the owner's word. **`C-UN`** (not unlocked, not `bound 10000`, or `mdio_rd`
  moved): no probe; the owner reads it.
* **`C-PR`** (`bus 1 reg_rc 0` not read): the shot is spent or was never taken, and the page is
  in the capture. `I-C` continues `--from C-SYS`; `I-E`, `I-F`, `I-G` and `I-V` are skipped
  (every rlxfw verb would return `-ENODEV`, and the vendor's paged path runs only after (g)'s
  detector passed); `I-D` runs (`D7` void where no device is), then `I-J` and `I-Z`.
* **A page's `version` gate failing with its terminator seen and no loader text** (any page
  cell, any switch page): `/dev/ttyUSB0` is checked and the page is typed again once as
  `X-<page>` or `X-<swpage>` — the page only and never the verb, which is never typed twice —
  and the invocation continues `--from` the next cell only if the stand-in's page reads
  `dirty 0` and, from `F-B1` on, `bound 10000` (the gates the stopped cell did not reach;
  otherwise the `dirty` or `bound` rule below applies); a second failure: no cell until the
  owner has read it.
* **`dirty 0` failing on any page** (a restore that did not verify, P7; a vendor cell's page
  included): **no MDIO or `phyReg` cell runs after it.** The read set: `X-MD<n>`, `X-SW<n>`;
  then `I-J` (its `lock`, and its `probe` refused) and `I-Z`; then the power-off (推: the
  power-off returns the PHY to page 0, decision B).
* **`bound 10000` failing** on `F-B1`, `F-S1` or any `G-P*` cell (the containment): no rlxfw
  MDIO verb until the owner has read it; `I-G` does not start (after `F-B1` or `F-S1`) or stops
  there (a `G-P*` cell); `I-D`, `I-V`, `I-J` and `I-Z` run on the owner's word.
* **A vendor `phyReg` cell** (`D-V*`, `V-X*`): a reply line missing is a reading
  (`unmeasured at aN` in `D-D7` or `V-CMP`), never a stop; its `until`, `version`, `dirty` and
  loader gates are the rules above.
* **`I-V`'s opening gates.** `V-CUT` refusing: S6. `V-IF` reading `0` and `0` (`V-IFS` printed
  no `rlx0`: its capture was cut short, and the board may be stalled): the unterminated-cell
  rule. `V-IF` failing otherwise (`V-IFS` listing an `eth*`, `wlan*` or `br*` up, or `rlx0`
  twice): no `I-V` (a vendor timer tick could land page-0 writes inside `extRead`'s page
  window); `I-J` and `I-Z` run. `V-GO` failing (`G-SC`'s rows 0–4 unlike `E-SC`'s, or
  unreadable): no `I-V` until the owner has read it. `I-V` also starts only after `G-L` passed
  or S1's branch a cleared it (`X-L<n>a`); after branch b, not until the owner has read it.
* **S1, a liveness gate** (`B-L`, `G-L`, `V-L`: fewer than 4 of 4, or `follower` not 1). Each
  is its invocation's last cell, so a stop there ends its line — the tail watch opens — and
  never stops an MDIO cell; every step below runs on continuation lines (`--hold` first, then
  `--stop` of the running watch, the X-cells chained with `&&`, then `;` and the next watch),
  and the press continues with the next invocation on a line of its own. `follower` alone
  failing: the follower is restarted with (3)'s command with `>>` in place of `>`, the liveness
  typed again as `X-L<n>`, every kernel-log window since the last `follower 1` void. Otherwise,
  **before anything on the host is touched**, the read set, each an X-cell above: (1) `X-SW<n>`
  (first: 1.3 counts the bit 8 it consumes); (2) `X-MD<n>`; (3) `X-NIC<n>`; (4) `X-BR<n>`, the
  full board bracket, between `X-HP<n>` and (6); (5) `X-PS<n>`, last on the board; (6)
  `X-HN<n>`; then (7) `X-C<n>`. **Branch a** (the host reached the board): wait at least 3 s,
  then `X-NIC<n>a` and `X-L<n>a`; if it passes, the press continues with the next invocation.
  **Branch b, or branch a's `X-L<n>a` failing**: `X-PHY<n>` (read-only: port 3's `BMCR` and
  `BMSR`), then the recovery, a software action on the host: `X-RE<n>-list`, `X-RE<n>-detach`,
  `X-RE<n>-relist` (3 s later; the attach only if `<BUSID>` reads `Shared` there),
  `X-RE<n>-attach`, reading what each prints, then `X-ADDR<n>` — then `X-SW<n>b` and `X-L<n>b`.
  Either way the press continues with the next invocation (`I-V` as above); a failed `X-L<n>b`
  is P10's reading, and the later liveness gates still run.
* **S6, the cut points** (`cutgate` 1.1, card B's: the wall clock read in the offset of a
  capture's own start stamp, on the declared date). `T-LATE` (`I-T`, before the owner is told)
  and `T-CATCH` (`I-1`'s first cell, after the reply): `R0-PRE`'s stamp, refusing after 23:43
  and 23:45 — above. `G-CUT` (`I-G`'s first cell) and `V-CUT` (`I-V`'s): `R1-CATCH`'s stamp,
  refusing if now plus 3 or 2 minutes passes 23:52 — the estimate's minutes, rounded down, plus
  2: nominal plus a margin, not a worst case. A refusal — `cut refuse …`, or `cutgate` refusing
  to decide — stops its line and skips its block: `G-CUT` → `I-G`, `I-D` and `I-V`; `V-CUT` →
  `I-V`. The run continues on a new line, `--hold` first, with `I-J` and `I-Z`.
* **WSL itself stops mid-press**: card B's rule — the console is unwatched from that moment
  until a watch runs again, so, in this order: the keeper; `usbipd list` read fresh and each
  device no longer attached attached again, the CP2102 first, the GbE adapter as S1's
  `X-RE<n>-*`; `X-PRE<n>` (the throwaway capture a re-attach needs, the board on) and then a
  watch at once, on one line; the follower with `>>`; every window spanning the outage void.
* **A host reading** (`NAME?`): never a stop.
* **Anything not listed**: no cell runs until the owner has read it; the decision goes into
  `bench/2026-09-27c/CORRECTIONS-block51.md` first.

---

## § 7 What this block does not establish

* **Whether port 1 needs the patch** (`C-18`'s functional clause): ⊘ by the owner's ruling
  (decision D); one link partner cannot establish *not needed*, and this press moves no cable.
* **What PHY 1's register 19 does**: P7 compares bit patterns against the value the other four
  agree on, not their function, and on one die. **At an address whose `pread` found register 31
  not 0 at rest, or where the select is not shown**, nothing about page 1: such a `pread` wrote
  nothing and read no paged register.
* **Which of addresses 0, 1, 2 and 4 is port 1** (`NET-39`'s): `D7`'s IDs are equal and the
  rows' predictions there are one, so only a swap that involves port 3 is seen.
* **`STATUS`'s length in time**: `spin` counts polls of a read plus `udelay(1)`, nominal; the
  MDC rate is not measured.
* **What `MDCIOSR` 30:16 means**: `hi` and slot 0's bits are recorded against whether an
  address holds a PHY; one press names no bit.
* **Whether register 31 reads back** when `ps` reads 0 and page 1's register 16 equals page
  0's: the two causes cannot be told apart (`NET-136` 殘留).
* **That the switch's own PHY poller never meets a selected page**: bit 8, `scan 0 4` and
  liveness see a consequence, not the absence of a collision, and only while no vendor `eth*`
  is open; **if `G-PCTL` reads `blind yes`, the scan and `lde` detectors cannot see a PHY left
  on page 1 at all** (it reads registers 0–5 unchanged).
* **That a power cycle resets PHY registers** (推, decision B).
* **The probe's own `-EAGAIN` guard on the die** (§ 0 ⑦ (1)): only the counter it moves,
  through `pread`'s guard.
* **That the vendor's `extRead` reads page 1**: it writes 31 ← 1 and reads; its equality with
  (g)'s `v` is two paths agreeing, not a third source for what the select does.
* **The vendor's MDIO census** (§ 10.3) and that IRQs off contains `one_sec_timer`: `/init`
  does not arm it, no cell opens `eth0`, and `V-IF` keeps (g′) off a board where one is up.
* **A reset the card cannot catch.** The tail watch holds the console whenever no command line
  runs, so a stall with IRQs off in a decision window bites inside it and its loader is caught
  (cards A and B's design; 推 on this image until a bite inside a watch is recorded here). What
  is left: a reset whose banner ends a board cell is caught only if the line's tail watch opens
  inside the loader's ~4.9-s ESC window (block 50 measured its tail watches' captures starting
  0.23–0.24 s after their line's runner ended (`I-1`/`X-W15`, `I-CN`/`X-W36`, `I-P1`/`X-W37`,
  `I-Z`/`X-W47`: the run log's last stamp and the watch's `t0_raw`, one clock); 推 caught); a
  stall in the second or so between a watch's stop and the next line's first board capture is
  caught by the next board cell's cap and the tail watch after it only while that span stays
  under the bite (§ 0 ⑤, the `TIME detect` lines, the wrapper's start-up under 20.1 s); and at
  a power-off the window streams 360 s from its start and the next watch follows it, so the
  owner's reaction after "power off now" is covered by what remains of the window and then the
  watch, with at most the watch's start between them (block 50: 0.23–0.24 s after a runner
  ends). The press's catch covers 300 s of the owner's reaction after "now" (60 s for the
  session, of its 360 s). **What the vendor boot that follows does to flash is 推**: `FLS-30`
  read nine vendor boots with the map's brackets unchanged, and the map does not see `H601`,
  two writes that cancel, or any byte outside it. A capture tool that starts ESC on the banner
  (§ 0 ⑦ (13)) would close most of this; it is a proposal, not built, and nothing here depends
  on it.
* **What `X-W<n>` does to a live shell**: whenever no line runs the board sits at its prompt,
  and the watch's ESC bytes and closing CR reach `ash`'s line editor as one line (推: an error
  line, a `not found`, at the head of the next capture, which no gate reads; cards A and B ran
  so, not yet read for it).
* **`PSRP` 保留態的起點** ((h), ⊘) and **(i)** (`R6b-8`'s); **the loud image** and phylib's
  `rtl819x-mdio: probed` line.
* **A second boot**: every reading here is one boot of 1.3.
* A flash write by anything but rlxfw's SPI driver between the two maps that the map does not
  see (`FLS-30`'s limits); `H601`'s 8,192 B are never hashed; `n_writes` carries no information
  about writes (`FW-142`), and `n_write_refused` counts only what reaches the MTD stubs.

---

```cells
bench/2026-09-27c/R0-PRE
bench/2026-09-27c/R0-PREC
bench/2026-09-27c/R0-ADDR
bench/2026-09-27c/R0-DMSG
bench/2026-09-27c/R0-DW0
bench/2026-09-27c/R0-FL
bench/2026-09-27c/R0-SUM
bench/2026-09-27c/R0-ST
bench/2026-09-27c/R0-VERB
bench/2026-09-27c/R0-H
bench/2026-09-27c/T-LATE
bench/2026-09-27c/T-CATCH
bench/2026-09-27c/R1-CATCH
bench/2026-09-27c/L1-MD2
bench/2026-09-27c/L2-MD3
bench/2026-09-27c/L-RD
bench/2026-09-27c/R1-FL
bench/2026-09-27c/R1Q
bench/2026-09-27c/R1-PS
bench/2026-09-27c/R1-SW7
bench/2026-09-27c/A-SW
bench/2026-09-27c/A-IF
bench/2026-09-27c/A-IFR
bench/2026-09-27c/A-SWP
bench/2026-09-27c/A-MD
bench/2026-09-27c/A-MDC
bench/2026-09-27c/A-MDP
bench/2026-09-27c/R1-M0
bench/2026-09-27c/R1-MB0
bench/2026-09-27c/R1-NW0
bench/2026-09-27c/A-NIC0
bench/2026-09-27c/A-FIX
bench/2026-09-27c/A-FIXR
bench/2026-09-27c/B-00-P
bench/2026-09-27c/B-00-R
bench/2026-09-27c/B-00-H
bench/2026-09-27c/B-L
bench/2026-09-27c/C-P0
bench/2026-09-27c/C-UN
bench/2026-09-27c/C-PR
bench/2026-09-27c/C-SYS
bench/2026-09-27c/C-SYR
bench/2026-09-27c/C-PR2
bench/2026-09-27c/E-SC
bench/2026-09-27c/E-SW
bench/2026-09-27c/E-RW
bench/2026-09-27c/F-B0
bench/2026-09-27c/F-S0
bench/2026-09-27c/F-B1
bench/2026-09-27c/F-S1
bench/2026-09-27c/F-AC
bench/2026-09-27c/G-CUT
bench/2026-09-27c/G-P1
bench/2026-09-27c/G-P2
bench/2026-09-27c/G-P3
bench/2026-09-27c/G-P4
bench/2026-09-27c/G-P5
bench/2026-09-27c/G-P6
bench/2026-09-27c/G-P7
bench/2026-09-27c/G-P8
bench/2026-09-27c/G-P9
bench/2026-09-27c/G-SC
bench/2026-09-27c/G-SW
bench/2026-09-27c/G-C18
bench/2026-09-27c/G-PCTL
bench/2026-09-27c/G-SWD
bench/2026-09-27c/G-99-P
bench/2026-09-27c/G-99-R
bench/2026-09-27c/G-99-H
bench/2026-09-27c/G-L
bench/2026-09-27c/D-V0
bench/2026-09-27c/D-V1
bench/2026-09-27c/D-V2
bench/2026-09-27c/D-V3
bench/2026-09-27c/D-V4
bench/2026-09-27c/D-MD
bench/2026-09-27c/D-D7
bench/2026-09-27c/V-CUT
bench/2026-09-27c/V-IFS
bench/2026-09-27c/V-IF
bench/2026-09-27c/V-GO
bench/2026-09-27c/V-X0
bench/2026-09-27c/V-X1
bench/2026-09-27c/V-X2
bench/2026-09-27c/V-X3
bench/2026-09-27c/V-X4
bench/2026-09-27c/V-SC
bench/2026-09-27c/V-SW
bench/2026-09-27c/V-CMP
bench/2026-09-27c/V-R04
bench/2026-09-27c/V-SWD
bench/2026-09-27c/V-99-P
bench/2026-09-27c/V-99-R
bench/2026-09-27c/V-99-H
bench/2026-09-27c/V-L
bench/2026-09-27c/J-LK
bench/2026-09-27c/J-PR
bench/2026-09-27c/J-FIN
bench/2026-09-27c/J-CH
bench/2026-09-27c/Z-SW
bench/2026-09-27c/Z-PS
bench/2026-09-27c/R1-M1
bench/2026-09-27c/R1-MB1
bench/2026-09-27c/R1-NW1
bench/2026-09-27c/Z-NWR
bench/2026-09-27c/Z-DW
bench/2026-09-27c/Z-DWALL
bench/2026-09-27c/R1Q-ab2
bench/2026-09-27c/R1Q-2a
bench/2026-09-27c/R1Q-boot
```

```cardnum
cells-fence	110	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^bench/2026-09-27c/
declared-date	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md [*][*]declared date 2026-09-27[*][*]
presses-caught	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/R1-CATCH -{2}esc-after 360 -{2}esc-period 0[.]002 -{2}until '<RealTek>' -{2}seconds 380$
cap-cells	58	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out
host-cells	49	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST&? bench/2026-09-27c/
host-bg-cells	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST& 
send-over-127	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*(EW |EB |FLW )
no-dw-db	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*(DB |DW )
no-burn	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*AUTOBURN
no-jump	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*J [0-9A-F]
no-watchdog-cell	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*(watchdog|rtl819x-wdt)
no-biteraw	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*biteraw
no-reboot-cell	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*reboot
no-mark-gate	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=RLXFW-
nic-verb-fix-only	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*> */proc/rtl819x-nic
nic-fix-cell	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/A-FIX -{2}send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10[.]1[.]1[.]3 up' -{2}idle 3 
fix-readback-gate	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^tx15 txlen vendor\\b:A-FIXR$
no-switch-verb	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*> */proc/rtl819x-switch
no-spi-write-verb	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*echo (trywrite|erase|write|unlock)[^|]*> */proc/rtl819x-spi
no-trywrite	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*trywrite
no-mfgtest	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*mfgtest
no-phy-write	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*(echo (write|extWrite|mmd|8370)|PHYW|MDIOW)
ifconfig-change-fix-only	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*ifconfig [a-z]
loader-cells	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/\S+ -{2}send '[A-Z]{2,} 
loader-mdior-2	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/L1-MD2 -{2}send 'MDIOR 2' -{2}esc-after 10 -{2}esc-period 0[.]02 -{2}until 'RealTek>' -{2}seconds 25$
loader-mdior-3	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/L2-MD3 -{2}send 'MDIOR 3' -{2}esc-after 10 -{2}esc-period 0[.]02 -{2}until 'RealTek>' -{2}seconds 25$
esc-after-cells	3	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP .*-{2}esc-after
esc-cells	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP .*-{2}esc [0-9]
linux-esc	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/(?!L[12]-MD|R1-CATCH )\S+ .*-{2}esc
board-until-banner	54	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/(?!R0-PRE |R1-CATCH |L[12]-MD)\S+ .*-{2}until '[^']*Booting\\\.\\\.\\\.\|---RealTek'
board-caps	54	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/(?!R0-PRE |R1-CATCH |L[12]-MD)\S+ 
loader-caught-gates	3	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:caught:
loader-noreset-gates	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|Linux\ version\)\):L[12]-MD[23]$
phyreg-read-cells	5	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send 'sleep 1 ; echo read [0-4] 2 > /proc/rtl865x/phyReg ; echo read [0-4] 3 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' -{2}until 'jiffies [^']*' -{2}seconds 15$
phyreg-extread-cells	5	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send 'sleep 1 ; echo extRead [0-4] 1 19 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' -{2}until 'jiffies [^']*' -{2}seconds 15$
phyreg-cells-all	10	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send '[^']*phyReg
phyreg-sends-under-128	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send 'sleep 1 ; [^']{118,}'
xphy-cells	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-PHY<n> :: CAP -{2}out bench/2026-09-27c/X-PHY<n> -{2}send 'sleep 1 ; echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; cat /proc/rtl819x-mdio' 
xcells-lines	24	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-\S+ :: 
xw-watch-form	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-W<n> :: CAP -{2}out bench/2026-09-27c/X-W<n> -{2}esc-after 3600 -{2}esc-period 0[.]01 -{2}until '<RealTek>' -{2}seconds 3605$
xoff-form	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-OFF<n> :: CAP -{2}out bench/2026-09-27c/X-OFF<n> -{2}esc-after 360 -{2}esc-period 0[.]01 -{2}until '<RealTek>' -{2}seconds 365$
xre-relist	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-RE<n>-relist :: sleep 3 ; usbipd[.]exe list$
xcells-no-page-write	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-\S+ :: .*-{2}send '[^']*[|] cat > /proc/
xcells-caps-banner	11	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-(?!W<n>|OFF<n>)\S+ :: CAP .*-{2}until '[^']*Booting\\\.\\\.\\\.\|---RealTek'
xcells-caps	11	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^X-(?!W<n>|OFF<n>)\S+ :: CAP 
mdio-verb-cells	22	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send 'echo [^']*[|] cat > /proc/rtl819x-mdio ; cat /proc/rtl819x-mdio' -{2}until 'jiffies
mdio-page-only-cells	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send 'cat /proc/rtl819x-mdio' -{2}until 'jiffies
mdio-probe	4	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo probe [|] cat > /proc/rtl819x-mdio
mdio-unlock	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo unlock mdio-i-mean-it [|] cat > /proc/rtl819x-mdio
mdio-lock	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo lock [|] cat > /proc/rtl819x-mdio
mdio-bound-0	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo bound 0 [|] cat
mdio-bound-full	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo bound 10000 [|] cat
mdio-bound-other	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send '[^']*echo bound (?!0 [|]|10000 [|])
mdio-pread-page1	8	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo pread [0-4] 1 (1[69]|20|2) [|] cat
mdio-pread-ctl	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo pread 0 1 2 [|] cat
mdio-pread-page0	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo pread 0 0 16 [|] cat
mdio-pread-other	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo pread [0-9]+ [2-9]
mdio-scan	5	count bench/2026-09-27c/PREDICTIONS-B53-block51.md echo scan (0 31|5 5|0 4) [|] cat
dirty-gates-page1	8	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^dirty 0\$:G-P[2-9]$
bound-gates-g	9	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^bound 10000\$:G-P[1-9]$
bound-gate-f	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^bound 10000\$:F-B1$
bound-gate-before-probe	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^bound 10000\$:C-UN$
dirty-gates-vendor	10	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^dirty 0\$:(D-V|V-X)[0-4]$
until-gates-vendor	10	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:until:(D-V|V-X)[0-4]$
vendor-reply-gates	0	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=[^:]*(regData|phyId)
loader-gates	54	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|<RealTek>\|Linux\ version\)\):
switch-pages	5	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send 'cat /proc/rtl819x-switch' -{2}until 
port-status-cells	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out \S+ -{2}send '[^']*port_status
liveness-cells	3	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/\S+-L :: FL 10[.]1[.]1[.]3 ; PL ; DMW 
follower-gates	4	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^follower 1\$:
board-brackets	3	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/\S+-R -{2}send 'sleep 2 ; cat /proc/rtl819x-nic 
host-pre-reads	3	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/\S+-P :: HP$
map-until-banner-60	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/R1-M[01] .* -{2}until 'map_lines \[0-9\][+]\\r\\n# \|Booting\\\.\\\.\\\.\|---RealTek' -{2}seconds 60$
nw-cells	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^CAP -{2}out bench/2026-09-27c/R1-NW[01] -{2}send 'cat /proc/rtl819x-spi' -{2}idle 3 -{2}until 'Booting\\\.\\\.\\\.\|---RealTek' -{2}seconds 15$
round-cell	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/R1Q :: LR -{2}cell R1Q QIMG -{2}iterations 1$
lr-recipe	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^`LR` = `/usr/bin/python3 tools/looprun[.]py -{2}mode bench -{2}out-dir bench/2026-09-27c/ -{2}skip S2,S3,S4 -{2}recipe-override 50e4af55 -{2}dwell-seconds 2[.]5`$
qimg	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^`QIMG` = `-{2}image /home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/kroot/rtkload/nfjrom -{2}image-sha256 548f4fae6682c295afa838e47d04db7bae13dbde06927447cce7fed4e17c8d53`$
cut-t-late	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/T-LATE :: CUT -{2}catch bench/2026-09-27c/R0-PRE[.]meta[.]json -{2}date 2026-09-27 -{2}start-by 23:43$
cut-g	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/G-CUT :: CUT -{2}catch bench/2026-09-27c/R1-CATCH[.]meta[.]json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 3$
cut-v	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/V-CUT :: CUT -{2}catch bench/2026-09-27c/R1-CATCH[.]meta[.]json -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need 2$
cut-t-catch	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/T-CATCH :: CUT -{2}catch bench/2026-09-27c/R0-PRE[.]meta[.]json -{2}date 2026-09-27 -{2}start-by 23:45$
cut-gates	4	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^cut permit\$:(T-LATE|T-CATCH|G-CUT|V-CUT)$
i1-first-cell-t-catch	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^T-CATCH$
ifconfig-cells	2	count bench/2026-09-27c/PREDICTIONS-B53-block51.md -{2}send 'ifconfig'
v-if-reads-v-ifs	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/V-IF :: IFC bench/2026-09-27c/V-IFS$
j-fin-reads-dir	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^HOST bench/2026-09-27c/J-FIN :: MDP final bench/2026-09-27c/$
v-if-gate	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\\A0\\n1\\n\\Z:V-IF$
v-go-gate	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^gate:grep=\^rows04 equal yes, 5 of 5\$:V-GO$
sha-mdpage-py	315fc36deb12feee36f7dfefed012d041e1dcb418a1644d923f3be77563d9f8d	sha256 /home/key/fwre-work/rebuild/s114/card43c/mdpage.py
sha-swpage13-py	810d5d31077109cc97c2f0387c247005c2f1aa4a71d479ca82e222bcf929dd1f	sha256 /home/key/fwre-work/rebuild/s114/card43c/swpage13.py
sha-mdioverb43c-py	524f6cd5be7c64d66ff896b594b1131cd1e67e540d152f16b0f463f3bf3124f2	sha256 /home/key/fwre-work/rebuild/s114/card43c/mdioverb43c.py
sha-arith43c-py	7d6e9e037a24ad0ce59ec4016cfb4455730152c7676b64265133f27f50883057	sha256 /home/key/fwre-work/rebuild/s114/card43c/arith43c.py
sha-mkswpage13-py	a3b4159e1afd739e68d8e2307135044536c417e585e5a1d4e18fc0ddd9e08eb9	sha256 /home/key/fwre-work/rebuild/s114/card43c/mkswpage13.py
sha-dmesgwin-py	2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py
sha-s1class-py	fd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431	sha256 /home/key/fwre-work/rebuild/s113/shared/s1class.py
sha-cutgate-py	f47f7f9bad9392bc83ed95d9bb2e515e0e0337ef102f112301004497ce0367eb	sha256 /home/key/fwre-work/rebuild/s113/card43b/cutgate.py
sha-mdiocheck	3f7138667abbb6c2e559c3a7e3f14a946842f00faf7ee92d7b30691533bc6342	sha256 tools/mdiocheck.py
ver-dmesgwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ^VERSION = "1[.]2"$
ver-s1class	1	count /home/key/fwre-work/rebuild/s113/shared/s1class.py ^VERSION = "1[.]0"$
ver-cutgate	1	count /home/key/fwre-work/rebuild/s113/card43b/cutgate.py ^VERSION = "1[.]1"$
sha-inv43c-sh	a7562716382e3356076347f0edceb9118c146cc8758ce4b56203cb52cb63963a	sha256 /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh
inv43c-version	1	count /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh ^# inv43c[.]sh 1[.]2 
inv43c-watch-template	1	count /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh ^WTEXT="CAP -{2}out @DIR@/@WN@ -{2}esc-after 3600 -{2}esc-period 0[.]01 -{2}until '<RealTek>' -{2}seconds 3605"$
inv43c-off-template	1	count /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh ^OTEXT="CAP -{2}out @DIR@/@WN@ -{2}esc-after 360 -{2}esc-period 0[.]01 -{2}until '<RealTek>' -{2}seconds 365"$
inv43c-hold	1	count /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh ^HOLD_S=90$
inv43c-sigint-shim	1	count /home/key/fwre-work/rebuild/s114/card43c/inv43c.sh signal[.]signal[(]signal[.]SIGINT, signal[.]SIG_DFL[)]
selftest-mdpage	1	count /home/key/fwre-work/rebuild/s114/card43c/selftest-mdpage.out ^mdpage\ self\-test:\ 71\ of\ 71\ passed$
selftest-swpage13	1	count /home/key/fwre-work/rebuild/s114/card43c/selftest-swpage13.out ^swpage13\ self\-test:\ 18\ of\ 18\ passed$
selftest-dmesgwin	1	count /home/key/fwre-work/rebuild/s114/card43c/selftest-dmesgwin.out ^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$
selftest-s1class	1	count /home/key/fwre-work/rebuild/s114/card43c/selftest-s1class.out ^s1class\ self\-test:\ 15\ of\ 15\ passed$
selftest-cutgate	1	count /home/key/fwre-work/rebuild/s114/card43c/selftest-cutgate.out ^cutgate\ self\-test:\ 17\ of\ 17\ passed$
selftest-mdioverb43c	1	count /home/key/fwre-work/rebuild/s114/card43c/selftest-mdioverb43c.out ^mdioverb\ self\-test:\ 25\ of\ 25\ passed$
mdioverb-pass	1	count /home/key/fwre-work/rebuild/s114/card43c/mdioverb43c.out ^mdioverb verdict PASS$
mutants-43c	1	count /home/key/fwre-work/rebuild/s114/card43c/mutants43c.out ^mutants43c: [0-9]+ planted, 0 not as expected$
mutants-43c-unmutated-first	1	count /home/key/fwre-work/rebuild/s114/card43c/mutants43c.out ^unmutated: mdpage [0-9]+ of [0-9]+, mdioverb [0-9]+ of [0-9]+, both pass$
swpage13-derived	1	count /home/key/fwre-work/rebuild/s114/card43c/mkswpage13.out ^mkswpage13: wrote /home/key/fwre-work/rebuild/s114/card43c/swpage13[.]py 
mdpage-version	1	count /home/key/fwre-work/rebuild/s114/card43c/mdpage.py ^VERSION = "1[.]1"$
img-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.manifest ^verdict\tgreen$
img-manifest-variant	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.manifest ^variant\tquiet$
img-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.manifest ^vmlinux_sha256\tb926105b6318561f50971738399912d31265292277dbaeb049109942de3740d1$
img-recipe	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.manifest ^recipe_id\t50e4af55$
img-irfs-source	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.manifest ^initramfs_source\t/home/key/fwre-work/rebuild/_irfs-r6b6/rlxfw-initramfs[.]spec$
img-irfs-manifest	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.manifest ^initramfs_manifest_sha256\td6882c14
img-twin-same	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q2.manifest ^vmlinux_sha256\tb926105b6318561f50971738399912d31265292277dbaeb049109942de3740d1$
img-record-nfjrom	1	count /home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t548f4fae6682c295afa838e47d04db7bae13dbde06927447cce7fed4e17c8d53$
img-record-clean	1	count /home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
img-nfjrom-sha256	548f4fae6682c295	sha256-16 /home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/kroot/rtkload/nfjrom
img-nfjrom-bytes	1169408	size /home/key/fwre-work/rebuild/s113/r6b7/rtk/r6b7q/rlxfw/kroot/rtkload/nfjrom
img-no-wtdog	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^# CONFIG_RTL_WTDOG is not set$
img-watchdog-y	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_WATCHDOG=y$
img-no-printk	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^# CONFIG_PRINTK is not set$
img-panic-printk	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_PANIC_PRINTK=y$
img-phylib	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_PHYLIB=y$
img-net-ethernet	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_NET_ETHERNET=y$
img-cmdline-no-panic	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_CMDLINE="console=ttyS0,38400"$
img-preempt-none	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_PREEMPT_NONE=y$
img-no-smp	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^# CONFIG_SMP is not set$
img-hz-100	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_HZ=100$
img-vendor-eth-open	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.config-built ^CONFIG_RLXFW_VENDOR_ETH_OPEN=y$
img-sysmap-rtl819x-mdio-xfer	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} t rtl819x_mdio_xfer$
img-sysmap-rtl819x-mdio-read-proc	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} t rtl819x_mdio_read_proc$
img-sysmap-rtl819x-mdio-write-proc	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} t rtl819x_mdio_write_proc$
img-sysmap-mdiobus-register	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} T mdiobus_register$
img-sysmap-mdiobus-scan	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} T mdiobus_scan$
img-sysmap-initcall-phy-init4	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} t __initcall_phy_init4$
img-sysmap-initcall-rtl819x-mdio-init6	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} t __initcall_rtl819x_mdio_init6$
img-sysmap-genphy-driver	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} d genphy_driver$
img-sysmap-rtl819x-mdio-bound	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} d rtl819x_mdio_bound$
img-sysmap-rtl819x-mdio-unlocked	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} b rtl819x_mdio_unlocked$
img-sysmap-bootguard	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} d bootguard$
img-sysmap-initcall-rtl819x-wdt-init7	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.System.map ^[0-9a-f]{8} t __initcall_rtl819x_wdt_init7$
elf-bootguard-0	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2946068
elf-genphy-driver-0	FFFFFFFF	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911536
elf-genphy-driver-1	80298250	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911540
elf-genphy-driver-2	FFFFFFFF	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911544
elf-hw-ovsel-0	00000009	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2946080
elf-kick-ms-0	000000FA	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2946076
elf-rtl819x-mdio-bound-0	00002710	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911424
elf-rtl819x-mdio-reg-rc-0	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911448
elf-rtl819x-mdio-scan-rc-0	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911428
elf-rtl819x-mdio-scan-rc-1	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911432
elf-rtl819x-mdio-scan-rc-2	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911436
elf-rtl819x-mdio-scan-rc-3	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911440
elf-rtl819x-mdio-scan-rc-4	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911444
elf-rtl819x-mdio-xrc-0	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911452
elf-rtl819x-mdio-xrc-1	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911456
elf-rtl819x-mdio-xrc-2	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911460
elf-rtl819x-mdio-xrc-3	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911464
elf-rtl819x-mdio-xrc-4	00000001	word32 /home/key/fwre-work/rebuild/r3-4/out/r6b7q.vmlinux.elf 2911468
drv-version-1.3	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_SW_VERSION\t"rtl819x-switch 1[.]3"$
drv-token	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_MDIO_TOKEN\t"mdio-i-mean-it"$
drv-bound	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_MDIO_BOUND\t10000u\t
drv-bound-guards	2	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\tif [(]rtl819x_mdio_bound != RTL819X_MDIO_BOUND[)] [{]$
drv-probe-oneshot	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\tif [(]rtl819x_mdio_reg_rc != 1[)]$
drv-phy-mask	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\tbus->phy_mask = ~0u;
drv-write-op-refuses	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\trtl819x_mdio_n_wr_refused[+][+];$
drv-pread-page	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t\t {4}v\[0\] >= RTL819X_MDIO_NPHY [|][|] v\[1\] > RTL819X_MDIO_PAGE [|][|]$
drv-page-1	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_MDIO_PAGE\t1\t
drv-pagereg-31	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_MDIO_PAGEREG\t31$
drv-restore-always	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c p->rs = rtl819x_mdio_xfer[(]1, a, RTL819X_MDIO_PAGEREG, 0[)]; +/[*] always [*]/$
drv-p0-writes-nothing	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c if [(]p->p0 != 0[)] [{]\t/[*] not on page 0, or unreadable: write nothing [*]/$
drv-noxfer-1	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_MDIO_NOXFER\t1\t
drv-lock-gate	2	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\tif [(]!rtl819x_mdio_unlocked[)] [{]$
drv-initcall	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^device_initcall[(]rtl819x_mdio_init[)];$
drv-pr-format	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c "pr a%u p%u r%02u v %d p0 %d ps %d p1 %d rs %d rt %u rc %d psrp %08X %08X[\\]n",$
drv-row-format	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c " hi %04X psrp %08X n %u[\\]n",$
drv-sw-mdciocr-row	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t[{] "MDCIOCR",\t0x4004, 1, 0 [}],$
drv-sw-mdciosr-row	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t[{] "MDCIOSR",\t0x4008, 1, 0 [}],$
drv-sw-psrp0	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_SW_PSRP0\t0x4128$
drv-cell-nic-1.5	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define RTL819X_NIC_VERSION\t"rtl819x-nic 1[.]5"$
drv-head-is-cell	80bb3f261434b0bdc924d693547a1c1807f3298a2590221823cec38f9644e391	sha256 config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c
phy-id-fmt	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/include/linux/phy.h ^#define PHY_ID_FMT "%s:%02x"$
genphy-id	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/phy/phy_device.c ^\t[.]phy_id\t\t= 0xffffffff,$
wdt-hw-ovsel-9	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^static int hw_ovsel = 9;$
wdt-kick-250	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^static int kick_ms = 250;$
wdt-bootguard-1	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c ^static int bootguard = 1;$
wdt-ovsel9-838	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/watchdog/rtl819x-wdt.c OVSEL 9 is 83[.]8 s 量
arith-bite	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^BITE bootguard 1 hw_ovsel 9 kick_ms 250: a stopped kernel timer is reset 83[.]8 s later [(]量, rtl819x-wdt[.]c[)]; at the loader's 14[.]965 MHz the same OVSEL is 1121101 us$
esc-window-4-9	1	count tools/console-capture.py The ESC window on this unit is ~4[.]9 s wide
esc-after-ends-on-until	1	count tools/console-capture.py ^ {20}if until_at is not None:$
p1rz-esc-echoed	1	count bench/2026-09-23/P1-RZ.log \^\[\^\[\^\[
spec-fls30	1	count SPEC.md ^[|] `FLS-30` 
spi-nwr-sites	2	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c ^\trtl819x_spi_n_write_refused[+][+];$
b48-nw0-refused-0	1	count bench/2026-09-26b/R1-NW0.log ^n_write_refused 0
b48-nw1-refused-0	1	count bench/2026-09-26b/R1-NW1.log ^n_write_refused 0
arith-nwr	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^NWR n_write_refused moves at 2 sites [(]the MTD write and erase stubs[)]; the card types no trywrite, no mfgtest and no MTD write: R1-NW0 0, R1-NW1 0, d 0$
vend-read-format	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x/rtl865x_proc_debug.c rtlglue_printf[(]"read phyId[(]%d[)], regId[(]%d[)],regData:0x%x[\\]n"
vend-ext-format	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x/rtl865x_proc_debug.c rtlglue_printf[(]"extRead phyId[(]%d[)], pageId[(]%d[)], regId[(]%d[)], regData:0x%x[\\]n"
vend-ext-restore	2	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x/rtl865x_proc_debug.c ^\t\t\trtl8651_setAsicEthernetPHYReg[(]phyId, 31, 0[)];$
vend-unbounded-read	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/drivers/net/rtl819x/AsicDriver/rtl865x_asicL2.c do [{] status = READ_MEM32[(] MDCIOSR [)]; [}] while [(] [(] status & MDC_STATUS [)] != 0 [)];
vend-printf-panic	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/include/net/rtl/rtl_types.h ^\t#define rtlglue_printf\tpanic_printk$
errno-line	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^ERRNO EPERM 1 EIO 5 EAGAIN 11 EEXIST 17 ENODEV 19 EINVAL 22 EPROTO 71 ETIMEDOUT 145$
errno-arch-etimedout	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tETIMEDOUT\t145\t
errno-arch-eproto	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b7q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tEPROTO\t\t71\t
strerror-eperm	1	count /home/key/fwre-work/extracted/unit-2018/squashfs-root/lib/libuClibc-0.9.30.3.so Operation not permitted
strerror-eagain	1	count /home/key/fwre-work/extracted/unit-2018/squashfs-root/lib/libuClibc-0.9.30.3.so Resource temporarily unavailable
strerror-eexist	1	count /home/key/fwre-work/extracted/unit-2018/squashfs-root/lib/libuClibc-0.9.30.3.so File exists
uclibc-sha	9e2a2bf0b4f23014	sha256-16 /home/key/fwre-work/extracted/unit-2018/squashfs-root/lib/libuClibc-0.9.30.3.so
irfs-uclibc	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.initramfs.manifest.tsv ^/lib/libuClibc-0[.]9[.]30[.]3[.]so\tfile\t205452\t9e2a2bf0b4f230140057b596dc90f430073ee864b9caf4213aed7c8ad4cbc3fb\t
irfs-ls	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.initramfs.manifest.tsv ^/bin/ls\tslink\t
irfs-ifconfig	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.initramfs.manifest.tsv ^/bin/ifconfig\tslink\t
irfs-sleep	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.initramfs.manifest.tsv ^/bin/sleep\tslink\t
irfs-init-sha	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.initramfs.manifest.tsv ^/init\tfile\t2153\tef2c87971fe158c72ea2d59cd84f495c0035d4227fa203c6d93db4a48641bab8\t
init-mounts-sysfs	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/rlxfw-init.sh ^mount -t sysfs sysfs /sys$
init-opens-rlx0-only	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/rlxfw-init.sh ^ifconfig 
init-switch-token	1	count /home/key/fwre-work/rebuild/s112/r6b6/repo/config/rlxfw-init.sh ^echo unlock i-mean-it > /proc/rtl819x-switch$
decl-ls	1	count config/rlxfw-initramfs.tsv ^slink\t/bin/ls\tbusybox\t
irfs-busybox	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b7q.initramfs.manifest.tsv ^/bin/busybox\tfile\t273332\td5310832cbbedf42a6a38788d7b254d4ba0269236ece1693247e1fb0c8d3d516\t
image-commands-busybox	1	count config/image-commands.tsv ^# busybox\tv1[.]13[.]4\t273332 bytes$
usbipd-interop-desk	1	count /home/key/fwre-work/rebuild/s114/card43c/fix/f3-usbipd.out ^usbipd[.]exe list rc=0$
f2-32-lines	32	count bench/2026-08-24c/F2.log ^PhyID=0x[0-9a-f]{2} Reg=2 Data =0x[0-9a-f]{4}
f2-0-4-001c	5	count bench/2026-08-24c/F2.log ^PhyID=0x0[0-4] Reg=2 Data =0x001c
f2-5-31-0000	27	count bench/2026-08-24c/F2.log ^PhyID=0x(0[5-9a-f]|1[0-9a-f]) Reg=2 Data =0x0000
f2-bytes	1042	size bench/2026-08-24c/F2.log
x8-reg0-1100	5	count bench/2026-09-19/X8-mdior02.log ^PhyID=0x0[0-4] Reg=0 Data =0x1100
x8-esc-after	1	count bench/2026-09-19/X8-mdior02.meta.json ^ {2}"esc_after_seconds": 10[.]0,$
e-reg3-c880	2	count bench/2026-08-23/E.log UID=0x0000c880
x5-bmsr3-78ed	1	count bench/2026-09-17b/X5-bmsr3.log UID=0x000078ed
x4-anlpar3-cde1	1	count bench/2026-09-17b/X4-anlpar3.log UID=0x0000cde1
x4-loader-phyr	1	count bench/2026-09-17b/X4-anlpar3.meta.json ^ {2}"sent": "PHYR 3 5",$
e12e-loader-phyr	1	count bench/2026-08-24b/E12e.meta.json ^ {2}"sent": "PHYR 0 5",$
e12e-r5-0001	1	count bench/2026-08-24b/E12e.log UID=0x00000001
c19-linux-id	1	count bench/2026-09-19/C19-PHYID.log ^read phyId[(]0[)], regId[(]3[)],regData:0xc880
c20-linux-bmsr	1	count bench/2026-09-19/C20-PHYST.log ^read phyId[(]0[)], regId[(]1[)],regData:0x78c9
xphy1-linux-p3-r0	1	count bench/2026-09-26b/X-PHY1.log regId[(]0[)],regData:0x1100
slot0-96181441	1	count bench/2026-09-26b/X-SW1.log ^r MDCIOCR +4004 [0-9A-F]{8} 96181441 
arith-controls	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^arith43c controls: ([0-9]+) of \1 hold$
arith-l2-word	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDCIOCR read a 31 r 3 = 1F030000 [(]L2's last command[)]$
arith-slot0-decode	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDCIOCR 96181441 = write 1 phy 22 reg 24 data 1441$
arith-hibits	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDCIOSR bits 30:16 mask 7FFF0000 
arith-d7-id	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^D7 id 001C << 16 [|] C880 = 001CC880$
arith-probe-10	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD probe 10$
arith-scan-202	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD scan 0 31 192, after it 202$
arith-g-29-14	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD g 29 MDWR g 14 
arith-g-k	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD g 29 - 3k - b MDWR g 14 - 2k [(]k: page-1 preads whose register 31 read at rest was not 0: no write, and one read each but for the b refused busy, -16, which read nothing[)]$
arith-g9	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD g9 4 MDWR g9 2 
arith-final	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD final 307 - dbusy - 3k - b MDWR final 16 - 2k$
arith-final-k7	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^MDRD final with mdiocheck K7's model [(]dbusy 4, k 0[)] 303$
arith-chain	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^CHAIN full run rd = probe 10 [+] scan 0 31 192 [+] [(]6 - dbusy[)] [+] scan 5 5 6 [+] g 29 [+] g9 4 [+] 2 x 30 - 3k - b = 307 - dbusy - 3k - b; wr 14 [+] 2 - 2k = 16 - 2k; 
arith-phyw	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^PHYW rlxfw 8 page-1 preads x 2 = 16 writes of register 31; vendor 5 extRead x 2 = 10$
arith-irqoff	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^IRQOFF pread at most 13 x 10000 x udelay[(]1[)] = 130 ms nominal$
arith-c18-mask	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^C18 mask bits 15:1 = FFFE; r16 bits 15:13 110 = value & E000 == C000$
arith-loader-bytes	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^LOADER MDIOR reply bytes 1042 = 8 [+] 32 x 32 [+] 10$
arith-page-max	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^PAGE scan32pr8 2985 bytes$
arith-bound-elf	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^ELF rtl819x_mdio_bound\[0\] d 802BECC0 file [0-9]+ section [.]data word 00002710$
arith-mapcap	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^CAP map 60 s, under the bite's 83[.]8 s and above block 48's longest map; 
arith-catch	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^CATCH -{2}esc-after 360 = the session's confirmation 60 s [(]a guess[)] [+] the owner's reaction 300 s [(]a guess[)], cards A and B's; -{2}seconds 380 = -{2}esc-after [+] 20; 
arith-hold	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^HOLD 90 s after a stop = the bite 84[.]001 s [(]SPEC[.]md CLK-08b[)] [+] the loader's banner to its first prompt 2[.]288 s 
ab-catch-a	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out bench/2026-09-27/A1-CATCH -{2}esc-after 360 -{2}esc-period 0[.]002 -{2}until '<RealTek>' -{2}seconds 380$
ab-catch-b	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^CAP -{2}out bench/2026-09-27b/R1-CATCH -{2}esc-after 360 -{2}esc-period 0[.]002 -{2}until '<RealTek>' -{2}seconds 380$
b48-catch-form	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/R1-CATCH -{2}esc 180 -{2}esc-period 0[.]002 -{2}seconds 200$
secs-catch	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS catch 200.3 
secs-catch-form	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS catch-form 17.3 
secs-capovh	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS capovh 0.3 
secs-round	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS round 24.7 
secs-ps	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS ps 3.4 
secs-map	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS map 13.9 
secs-map-max	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS map-max 13.9 
secs-mb	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS mb 0.9 
secs-nw	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS nw 3.6 
secs-bracket	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS bracket 5.5 
secs-live	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS live 0.9 
secs-idle3	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS idle3 3.4 
secs-loader-mdior	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS loader-mdior 0.9 
secs-vendor	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS vendor 2.3 
secs-nicpage	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS nicpage 0.9 
secs-swpage	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS swpage 0.9 
secs-mdpage-boot	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS mdpage-boot 0.4 
secs-mdpage-probe	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS mdpage-probe 0.4 
secs-mdpage-scan32	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS mdpage-scan32 0.9 
secs-mdpage-scan32pr8	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS mdpage-scan32pr8 1.1 
secs-reading	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS reading 0.3 
secs-cut	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^SECS cut 0.2 
time-rules	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME rules end\-by 23:52 gap 0\.5 host\-gap 10 min s1\-allow 3 min reply\-allow 2 min$
time-est	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME est 3\.06 min must 7 min latest\-catch 23:45 t\-gate 23:43$
time-need	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME need G 3 V 2 \(nominal \+ int \+ 2 min\) arrive G 1\.63 min V 2\.19 min$
time-card-b	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME card\-b est 79 min \(its 78\.91 rounded up\) latest 23:14 nothing\-cut 22:26 b\-by 22:16 c\-after\-b 00:02$
time-inv-I-0	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-0 0\.3 min$
time-inv-I-T	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-T 0\.0 min$
time-inv-I-1	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-1 0\.8 min$
time-inv-I-A	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-A 0\.6 min$
time-inv-I-C	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-C 0\.1 min$
time-inv-I-E	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-E 0\.0 min$
time-inv-I-F	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-F 0\.1 min$
time-inv-I-G	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-G 0\.3 min$
time-inv-I-D	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-D 0\.2 min$
time-inv-I-V	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-V 0\.4 min$
time-inv-I-J	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-J 0\.0 min$
time-inv-I-Z	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME inv I\-Z 0\.4 min$
time-detect-one	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME detect\-one a stall at Z\-PS's start stops its invocation 63\.7 s later \(at R1\-M1\), the most in one invocation: 20\.1 s of the 83\.8\-s bite are left for the line's tail watch X\-W<n> to open$
time-detect-two	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME detect\-two a stall at D\-D7's start crosses 1 invocation boundary before V\-X0 stops 19\.8 s later, each a wrapper start\-up too: 2 start\-ups in 64\.0 s, 32\.0 s each$
time-detect-bound	1	count /home/key/fwre-work/rebuild/s114/card43c/arith43c.out ^TIME detect\-bound the wrapper's start\-up between invocations on a line, and the tail watch's opening after a stop, must each stay under 20\.1 s \(binding at Z\-PS\); the estimate's 0\.5 s between invocations is block 50's measured start\-up \(0\.35\-0\.47 s\), rounded up$
window-card-b-sha	cb7b2dda564c1332be6a4cef8ec7bcf78d2a349412af3883311dcf8ea8232de8	sha256 bench/2026-09-27b/PREDICTIONS-B52-block50.md
window-card-b-estimate	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md About 79 minutes from the catch window's opening
window-card-b-est-arith	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^arith-time-est\t1\tcount \S+/arith43b[.]out \^TIME est 78\\[.]91 min
window-card-b-latest	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^opens no later than 23:14 that day
window-card-b-nocut	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^cut[)]; at the estimate, by [0-9]{2}:[0-9]{2} for .R6b-4. to run and by 22:26 for nothing to be cut
window-end-by	5	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^HOST \S+ :: CUT -{2}catch \S+ -{2}date 2026-09-27 -{2}end-by 23:52 -{2}need [0-9]+$
window-end-by-other	0	count bench/2026-09-27b/PREDICTIONS-B52-block50.md -{2}end-by (?!23:52 )
card-b-pins-cutgate	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^sha-cutgate-py\tf47f7f9bad9392bc83ed95d9bb2e515e0e0337ef102f112301004497ce0367eb\tsha256 /home/key/fwre-work/rebuild/s113/card43b/cutgate[.]py$
card-b-pins-s1class	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^sha-s1class-py\tfd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431\tsha256 /home/key/fwre-work/rebuild/s113/shared/s1class[.]py$
card-b-pins-dmesgwin	1	count bench/2026-09-27b/PREDICTIONS-B52-block50.md ^sha-dmesgwin-py\t2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1\tsha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin[.]py$
window-b-nocut	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^[|] card B's latest catch for nothing of it to be cut [|] 22:26 [|]
bite-measured-clk08b	1	count SPEC.md ^[|] `CLK-08b` 🆕 [|] .*、9 = [*][*]84,001\.412 ms[*][*]
window-latest-c	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^[|] this card's latest catch [|] 23:45 [|] 23:52 − 7 min [|]$
window-t-gate	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^[|] the latest-catch gate, before the owner is told [|] 23:43 [|] 23:45 − 2 min [|]$
window-c-after-b	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^[|] this card's catch after that [|] 00:02 the next day [|] 23:52 [+] 10 min [|]$
notes-40960	1	count notes/switch-driver.md so 1[.]3 and libphy cost 40,960 bytes
notes-70-dumps	1	count notes/switch-driver.md all 70 `MDCIOSR` rows in the committed
window-b-by	1	count bench/2026-09-27c/PREDICTIONS-B53-block51.md ^[|] card B's latest catch, for both presses on one date [|] 22:16 [|]
spec-net136-residual	1	count SPEC.md ^[|] `NET-136` 殘留 
spec-net135	1	count SPEC.md ^[|] `NET-135` 
notes-10-8	1	count notes/switch-driver.md ^## 10[.]8 The card, for after `R6b-6`'s seating$
mdiocheck-boot-page	1	count tools/mdiocheck.py ^def boot_page[(]bound=10000[)]:$
```
