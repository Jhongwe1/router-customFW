# Block 24 — eleven switch registers this project has never read, and a link-state ladder the host drives end to end

**Frozen before power to these cells.** Seating 26, `bench/2026-09-17b/`,
**declared date 2026-09-17** (`CAPD-1`, see § 0.1). The board was powered at
11:02 today and has been held at `<RealTek>` since; the three captures already
in this directory (`X0-esc`, `X1-esc`, `X2-autoburn`, `X3-live`) are **`X`-prefixed
off-card** and are declared in § 0.2 rather than fenced.

---

## 0. What this block is, in one paragraph

`R6-0`'s census (this segment, desk) produced one number that decides this
block: **量 — no word in `0xBB804xxx` has ever been read under Linux, and of the
thirteen switch registers this unit's loader touches, eleven carry no value in
either state.** Eight of those eleven do not appear in `SPEC.md` at all. This
block reads them at the loader prompt. It also runs a five-rung ladder on
`PSRP` in which **the host brings its own NIC up and down** — so a causal
link-state measurement happens with no operator at the board and no power cycle.

🔴 **What this block is NOT**: it is not the `CPU-45` cell and it is not the
Linux-state contrast. Both need an upload, both are block 25, and putting them
here would make one card depend on a desk question that is still open at freeze
time (whether the loader's TFTP path does cache maintenance).

### 0.1 `CAPD-1`'s condition — the literal condition is met, the mechanism is not

`CAPD-1` was handed to `R6` a second time with the condition that **`R6`'s
first frozen card must carry a declared date**. This is that card and this is
that date: **2026-09-17**, the day the captures are taken, matching the
directory `bench/2026-09-17b/`. ⚠️ The seating began 11:02 and this card is
frozen the same morning, so the midnight-crossing failure that produced
`bench/2026-08-30`/`-30b` cannot arise.

🔴 **And that is the whole of it, which is less than it sounds.** 量 today:
`tools/cardcheck.py` contains **zero** occurrences of
`started_wallclock|strptime|datetime`, and `tools/capdate.py` never opens a
`PREDICTIONS-*.md` at all — its only `.md` input is `bench/README.md`. It
compares a **capture's** `started_wallclock` against the **directory** name and
has no idea a card exists. **So no checker in this repository reads a card's
declared date, and writing one down does not make it checked.** Designing that
mechanism is what `CAPD-1` still is; this card does the half that a card can do
and says plainly that the other half is absent. The `cardnum` row
`declared-date` below is the smallest step towards it: it makes the declaration
**machine-visible** — a checker re-derives that the string is present and
occurs once — without pretending it has been compared to anything.

### 0.2 The four off-card captures already on disk, declared

| | what it is | why it is not fenced |
|---|---|---|
| `X0-esc` | a 300 s ESC window opened **before** the operator powered on, during which the board was already running the **vendor firmware** | it caught no loader prompt; it is the evidence for § 0.3 |
| `X1-esc` | the ESC window that caught the cold boot | the cold-boot capture is a one-shot resource and predates this card by design |
| `X2-autoburn` | `DW 8040D4A0 1` → **`00000001`** | a safety precondition, not a result |
| `X3-live` | the same read 11 minutes later | a link-liveness probe |

⚠️ **`X0-esc` has no `.meta.json`** and that is not a defect in the capture. It
was ended with `pkill`, and `CLAUDE.md` records the consequence in advance: *a
SIGTERM kill loses `.meta.json`; the `.log` and `.timing` survive, flushed per
chunk.* Its two surviving artefacts are what § 0.3 rests on, and neither of them
is the metadata. 🔴 A consequence worth stating: `tools/capdate.py` reads
`started_wallclock` out of the metadata, so **this capture cannot be checked by
`capdate` at all** — it is dated here, by hand, at 10:59 on 2026-09-17, from its
`.timing` and from the seating's own ordering.

### 0.3 🔴 The vendor firmware ran on this part today, ~10:57–11:02

量, and the discriminator is this seating's own positive control. Three known
loader captures with `--esc` (`bench/2026-09-{10,14,16}/C1-A.log`) echo ESC as
**raw `0x1b`** — 65,315 / 66,134 / 66,296 of them — with **zero** `^` and
**zero** BEL. `X0-esc` holds **zero** `0x1b`, **4,095** `^`, **4,095** `[` and
**2,277** BEL. `X1-esc`, on the same adapter and the same ESC stream twelve
minutes later, holds **5,182** `0x1b`, zero `^`, zero BEL.

* **量** — whatever answered at 10:59 rendered a control character in caret
  notation and beeped on a full line buffer; the loader does neither.
* **推** — that is busybox ash's line editor (`FW-41`/`FW-47`'s family), so the
  flash image was running.
* **量** — `X0-esc` holds no shell prompt, no command echo and no command
  output. **Nothing was executed.**

**Consequence for the flash ledger**: this is a ~5-minute vendor-firmware
interval, exactly the kind `FLS-26`'s attribution bracket exists for. It is
**not** closed by this block; block 25 carries a `map 0`, which is the zero-cost
closure `SPEC.md` `FLS-26` already names.

---

## 1. What the desk settled today, zero power

| | 量/讀 | the reading |
|---|---|---|
| `0xBB804xxx` under Linux | 量 | `grep -rl BB804 bench/` → 41 files in four directories, **newest `bench/2026-08-25`**. Twenty-three seatings, zero Linux-state reads. Mechanism: `FW-46` (no `devmem` in this image) and no driver of mine touches the switch |
| the thirteen loader-touched addresses | 讀 `NET-21` | 2 carry a value (`0xBB804100`, `0xBB804104`); **11 carry none**; **8 of the 11 are absent from `SPEC.md`** |
| `0xBB804234` | 讀 | **no documentary source names it** — not D, not B, not A beyond the `lui` site |
| `R6-2`'s DoD | 讀 | *"a read-back whose value differs from reset"* is **not satisfiable today**: none of the eight has a known reset value. This block is what makes `R6-2` possible |
| `DW`'s segment behaviour | 讀 | `DW` forces KSEG0 **only when bit 31 is clear**; `0xBB804xxx` has bit 31 set, so the address goes to the bus as typed |

---

## 2. The order, and it is forced rather than chosen

1. 🔴 **Every cell here is loader-state and must precede any `J` to a kernel.**
   `CLK-17`: `TC0CNT` reads **14,286,057 Hz** at the prompt and **200,005 Hz**
   under Linux — Linux reprograms `CDBR`. A loader-state question asked after a
   boot is a different question with the same words.
2. 🔴 **`PSRP` bit 8 is read-to-clear** (`NET-11`, 量 ×3). Every `DW BB804128`
   consumes the latch, so the ladder's rungs are **ordered and not
   interchangeable**, and no rung may be re-run to "check".
3. The eight never-read registers go **first**, because they are the only cells
   here whose value is unknown, and § 10 drops from the bottom.
4. `C9-SW100` is the **instrument's positive control** and is read before the
   ladder, so a failure of the instrument is separated from a failure of the
   ladder.

---

## 3. The guards

* **Zero writes.** Every cell is `DW`. No `EB`, no `EW`, no `FLW`, no `FLR`, no
  `PORT1`, no `PHYW`, no `MDIOW`, no TFTP, no `J`. `AUTOBURN` is **left at
  `00000001`** — 量 `X2-autoburn`, which is `REG-23`'s documented power-on
  state (母體 117 committed readings: 110 zero, 7 one) — because **nothing is
  uploaded**, and changing it would be a write this block has no use for.
* 🔴 **`DW B8002000` is never typed.** That address pops the console's `RBR` and
  clears `IIR`. No cell here starts inside `0xB800xxxx`.
* 🔴 **No `PHYR`/`MDIOR`.** `NET-17`: the `MDCIOSR` spin has no timeout, so an
  unanswered address ends the seating. Those belong in a block that can afford
  to be last.
* Every `--send` is 13 characters, single-quoted, with no `"`, no backtick and
  no `$`.
* Every cell carries `--seconds` as its terminator and `--until 'RealTek>'` as
  its early exit. `--until` is not a terminator and is not relied on as one.

### 3.1 The risk this block does take, stated rather than discovered

**推** — a read of an undocumented switch register could have a side effect, as
`PSRP` bit 8 and the console `RBR` both do. The mitigation is not an argument,
it is the cost: nothing depends on the switch right now (no kernel, no traffic
except the ladder's own link), and a disturbed switch is undone by the power
cycle this seating was always going to end with. **量**: the loader's own
`Ethernet init` already reads and writes all thirteen (`NET-21`, 48 `lui` sites),
so `DW` is not reaching anything the loader has not already reached.

---

## 4. Phase L — the predictions

### 4.1 The eight with no predictable value, and what IS predicted

For `C1`–`C8` **no value is predicted, and saying so is the point.** What is
pre-registered is the instrument and the controls:

| | pre-registered |
|---|---|
| reply size | **71 bytes** each, from `reply-size.py`'s model (n=91 captures). 量 today: `X2-autoburn` and `X3-live` both came back at exactly 71 |
| the label | the first token of the body is the address as typed, e.g. `BB804234:` |
| word count | `DW … 4` prints **4** words on **1** line (`LDR-07` rounds up) |
| 🔴 **negative control** | **the eight cells must not all return the same value.** If they do, the block is not decoded there and `DW` is reporting a bus artefact — which is exactly the built-in refutation `NET-24`'s 32-line `MDIOR` sweep carried and which had a real chance to fire there and did not |
| 🟢 **positive control, free** | `C9` reads `0xBB804118` = `00000000` and `0xBB80411C` = `187F0038` — **adjacent words, different values, 量 on two prior seatings.** That the same `DW` distinguishes two neighbouring words is what licenses reading `C1`–`C8` as per-word values at all |

**推, one weak value prediction, recorded so it can be wrong**: `0xBB804008` is
`MDCIOSR`, whose bit 31 is `STATUS` (`NET-15`, ×3 sources). The loader's MDIO
activity completed long ago, so bit 31 should read **0**. A `1` would mean a
transaction is still outstanding.

### 4.2 `C9-SW100` — predicted exactly, from `bench/2026-08-24b/E9b.log`

```
BB804100:	00000000	007F0039	047F0039	087F0039
BB804110:	0C7F0039	107F0039	00000000	187F0038
```

**118 bytes.** `PCRP` is port *control*, not status, and `NET-09`'s `ExtPHYID`
field (bits 30:26 = 0,1,2,3,4) re-derives from those five words, so it is
link-independent and the loader writes it identically every boot.

> **否證** — any difference from the eight words above means either this
> loader's init is not deterministic across power cycles, or `PCRP` carries
> link-dependent state that `NET-09`/`NET-20` do not describe. **Either is a
> finding and neither is a retry.**

---

## 5. Phase M — the ladder, and the host is the only thing that moves

The peer is the workstation's **RTL8153 USB GbE**, WSL interface
`enxfc19286184c9`. 量 at freeze time: `ip -br link` reads **DOWN** and `ethtool`
reads `Link detected: no`. So the board sees no link on any port, and bringing
the interface up is a transition **this session causes and timestamps**.

| rung | host state | predicted `PSRP0`…`PSRP4` | basis |
|---|---|---|---|
| `C10-PS0` | DOWN | all five **`000010E0`** | 量 `bench/2026-08-24b/E10b.log`, all ports down. Cold power-on, so no port has negotiated this cycle and `NET-11`'s `…E9` residue cannot be present |
| `C11-PS0b` | DOWN | **identical to `C10`**, bit 8 still 0 | the read-to-clear control with nothing to clear |
| `C12-PS1` | **UP** | **exactly one** port with bit 4 set, value **`000010F9`** | 量 `NET-11`: an RTL8153 peer advertises `ASM_DIR`+`PAUSE`, which reads as bits 6 and 5 set → `0xF9`. The other four stay `000010E0` |
| `C13-PS1b` | UP | the same, and bit 8 **may** be 1 on the linked port | `NET-11`'s `E11a2`: a second autoneg latch during convergence is a real event, not an instrument fault |
| `C14-PS2` | **DOWN** | on that port **`000011E9`** — bit 4 clear, **bit 8 set**, bits 3 and 0 still reporting 100M full duplex | 量 `bench/2026-08-25/E13-pos1-wan.log` read exactly `000011E9` on an unplugged port. `NET-11` ②: unplugging into an empty jack is the cleanest down event this desk can make |
| `C15-PS2b` | DOWN | on that port **`000010E9`** — bit 8 cleared by `C14`'s read | 量 `bench/2026-08-25/E11f-psrp2-empty.log` read exactly `000010E9` |

🔴 **Which port comes up is the measurement, not the prediction.** `NET-13`
recorded the cable in **switch port 3** on 2026-08-29, but the cable has been
moved since and this card does not assume it. What is predicted is **exactly
one**, which is the bijection that has survived thirteen tests.

> **否證 ①** — if `C10` shows any port with bit 4 set, a link exists that the
> host says does not, and the ladder's baseline is wrong. **Stop the ladder and
> record it**; the rest of Phase L still stands because it does not depend on
> link.

> **否證 ②** — if `C12` shows **more than one** port up, `NET-13`'s bijection
> is refuted after thirteen survivals, and that is a bigger result than the
> ladder.

> **否證 ③** — if `C14` does **not** set bit 8, the read-to-clear latch does not
> fire on a host-driven down event, and `NET-11` ② is true only of a physical
> unplug. That distinction has never been tested and the ladder exists partly
> to test it.

> **否證 ④ — the whole ladder is void as an instrument** if `C11` differs from
> `C10`. Two reads with nothing changing between them must agree; if they do
> not, every later rung is measuring the instrument.

---

## 6. What this block does NOT claim

1. **It does not answer `CPU-45`.** No bus master runs here.
2. **It does not give `R6-2` a reset value.** It gives `R6-2` a *loader-state*
   value, which is the thing a later read-back can differ **from**. Those are
   not the same and `R6-2`'s DoD says reset.
3. **It says nothing about Linux state.** Every reading here is loader-state,
   and `R6-0`'s census exists precisely because those were being conflated.
4. **It does not close `MT-PORT`'s gap.** That gap is a *Linux-state* row for
   link on a named port; this ladder is loader-state. It makes the two-state
   comparison possible by supplying the half that did not exist.
5. **It does not name `0xBB804234`.** Reading a word is not learning what it is.

---

## 7. The cells

`H` = host, `L` = at the loader prompt. Every `L` cell is one `DW`.

### 7.1 Phase L — the eight never read, then the control

```
#-- L. MACCR, MDCIOCR, MDCIOSR, +0x400C.  Named and bit-mapped by three sources; never read on this die.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C1-SW00 --send 'DW BB804000 4' --until 'RealTek>' --seconds 15
#-- L. P0GMIICR.  The CPU-port GMII control register, on NET-21's list, never read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C2-SW4C --send 'DW BB80414C 4' --until 'RealTek>' --seconds 15
#-- L. 0xBB804234.  NO SOURCE NAMES THIS ADDRESS.  The loader touches it and nothing says why.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C3-SW234 --send 'DW BB804234 4' --until 'RealTek>' --seconds 15
#-- L. SWTCR0, the switch control register 0.  Never read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C4-SW418 --send 'DW BB804418 4' --until 'RealTek>' --seconds 15
#-- L. FFCR, the frame-forward control register.  Never read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C5-SW428 --send 'DW BB804428 4' --until 'RealTek>' --seconds 15
#-- L. PVCR0.  This is the PVID register R6-6 is about, and R6-6 has never seen its value.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C6-SWA08 --send 'DW BB804A08 4' --until 'RealTek>' --seconds 15
#-- L. SWTACR and SWTAA, the switch table access pair, in one line.  Never read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C7-SWD00 --send 'DW BB804D00 4' --until 'RealTek>' --seconds 15
#-- L. TCR7.  Never read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C8-SWD3C --send 'DW BB804D3C 4' --until 'RealTek>' --seconds 15
#-- L. THE INSTRUMENT'S POSITIVE CONTROL.  Eight words predicted exactly; 4118 and 411C are adjacent and differ.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C9-SW100 --send 'DW BB804100 8' --until 'RealTek>' --seconds 15
```

### 7.2 Phase M — the ladder, host-driven

```
#-- L. rung 1.  Link DOWN.  Consumes whatever bit 8 holds from before this card.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C10-PS0 --send 'DW BB804128 8' --until 'RealTek>' --seconds 15
#-- L. rung 2.  Link still DOWN.  Must equal rung 1 or the ladder is void.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C11-PS0b --send 'DW BB804128 8' --until 'RealTek>' --seconds 15
#-- H. bring the peer up, then let autoneg converge.  No operator, no board action.
wsl -d Ubuntu-24.04 -- sudo ip link set enxfc19286184c9 up
#-- L. rung 3.  Link UP.  Exactly one port with bit 4 set.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C12-PS1 --send 'DW BB804128 8' --until 'RealTek>' --seconds 15
#-- L. rung 4.  Link still UP.  Bit 8 may be 1 here and that is NET-11's second autoneg latch.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C13-PS1b --send 'DW BB804128 8' --until 'RealTek>' --seconds 15
#-- H. take the peer down.  This is the down event NET-11's second half was measured on.
wsl -d Ubuntu-24.04 -- sudo ip link set enxfc19286184c9 down
#-- L. rung 5.  Link DOWN.  Bit 8 SET on the port that dropped, speed bits still reporting 100M.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C14-PS2 --send 'DW BB804128 8' --until 'RealTek>' --seconds 15
#-- L. rung 6.  Bit 8 cleared by rung 5's own read.  This is the read-to-clear, caused.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C15-PS2b --send 'DW BB804128 8' --until 'RealTek>' --seconds 15
```

### 7.3 The numbers this card states, and where each is re-derived FROM

```cardnum
cells-fence	15	count bench/2026-09-17b/PREDICTIONS-B25-block24.md ^bench/2026-09-17b/C[0-9]+-[A-Za-z0-9]+$
declared-date	1	count bench/2026-09-17b/PREDICTIONS-B25-block24.md [*][*]declared date 2026-09-17[*][*]
dw4-bytes	71	dwreply 4
dw8-bytes	118	dwreply 8
send-over-127	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
no-flr	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md -{2}send '[^']*(EW |EB |FLW )
no-autoexec	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md ^/usr/bin/python3 .*(allow-autoexec|boot[.]img)
no-phy-verb	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md -{2}send '[^']*(PHYR |PHYW |MDIOR |MDIOW |PORT1)
no-rbr-pop	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md -{2}send '[^']*DW B8002000
no-jump	0	count bench/2026-09-17b/PREDICTIONS-B25-block24.md -{2}send '[^']*J [0-9A-F]
```

---

## 8. The fence

```cells
bench/2026-09-17b/C1-SW00
bench/2026-09-17b/C2-SW4C
bench/2026-09-17b/C3-SW234
bench/2026-09-17b/C4-SW418
bench/2026-09-17b/C5-SW428
bench/2026-09-17b/C6-SWA08
bench/2026-09-17b/C7-SWD00
bench/2026-09-17b/C8-SWD3C
bench/2026-09-17b/C9-SW100
bench/2026-09-17b/C10-PS0
bench/2026-09-17b/C11-PS0b
bench/2026-09-17b/C12-PS1
bench/2026-09-17b/C13-PS1b
bench/2026-09-17b/C14-PS2
bench/2026-09-17b/C15-PS2b
```

⚠️ **The two `H` rows are deliberately outside this fence** — they produce no
capture, so `15 of 15` means *every cell that writes a file*, and it does not
mean *every line this card tells the operator to run*. Seating 15's fence read
`0 of 5` while looking correct; this note exists so the number's scope is
stated rather than assumed.

---

## 9. The drop order, if the window closes

1. `C11-PS0b` — the null rung. Dropping it costs 否證 ④ and nothing else.
2. `C13-PS1b` — the second UP read is the weakest rung.
3. `C2-SW4C`, `C8-SWD3C` — named by `NET-21` and by nothing downstream.
4. **Never dropped**: `C3-SW234` (no source names it), `C6-SWA08` (`R6-6`'s
   register), `C9-SW100` (without it nothing else here is licensed),
   `C10-PS0` / `C12-PS1` / `C14-PS2` (the three rungs that carry the ladder's
   whole causal claim).
