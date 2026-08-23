# RUNSHEET

**What gets typed at the bench, and what each line is expected to return.**

House rules for this file, and they are the reason it exists as a separate
document:

1. **Nothing here is a restatement.** `docs/` owns the semantics and the
   refutation conditions; this file owns the *procedure*. Where a cell needs a
   claim, it links to the document that owns it.
2. **Every cell carries its expected value, computed before the visit**, from
   `$FWRE_WORK/dumps/flash-n150rt-console-1.bin`
   (`sha256 a800059a…10f37ea`). A cell whose expectation is written afterwards
   illustrates; it cannot refute.
3. **Every cell says what would refute the reading it tests**, and what it costs
   if it goes wrong.
4. **A command is typed from here or from a tool, never re-stated by hand.**
   Upstream `RUNBOOK` §8.12.45 records what re-stating a command by hand costs.

Console: CP2102, **38400 8N1**. Read the log with `console-lint.py`, not by eye.

---

## Session B1 — console validation, one power cycle, zero flash bytes

**What it is for.** Everything in this repository so far was read out of the
dump, the vendor GPL sources or the datasheet. **No number in `rlxfw` has been
measured on silicon.** B1 does not build anything and does not advance a gate;
it checks whether the desk reading survives contact with the device, and it is
the cheapest possible way to find out that it does not.

**No QEMU is involved, here or anywhere else in this repo yet.** When R1 uses
it, it will be to validate a harness's logic and never an answer — the emulator
has interlocks this core does not.

| | |
|---|---|
| **Power cycles** | 1 to start, plus 1 software reset in D1 |
| **Flash bytes written** | **0** |
| **RAM written** | 8 words at `0x81000000`, scratch, in C2 only |
| **New code needed** | none |
| **Closes** | `C-3` (JEDEC ID), `C-8` (watchdog reset), `C-14` (the button), and rows 1–6 of `docs/loader-command-semantics.md` §8 |

### Before power is applied

Read the whole of this section first. **One power cycle is the most expensive
unit in this project**, so every question is listed before the board is plugged
in — that is why the order below is fixed.

### How this session is driven, and why it changes tools half way

**Section B goes through `upstream/tools/console-dump.py`. Sections C and D are
typed by hand.** That is not a convenience; the tool refuses to send them:

```python
FORBIDDEN = ("FLW", "EB", "EW", "AUTOBURN", "LOADADDR", "J ")
```

> *"refusing to send …: EW writes to the device. This tool only reads. If you
> genuinely need to write, type it into picocom yourself, having decided to."*

**Working around a deliberate refusal is worse than typing carefully**, so C and
D are typed, having decided to. One serial port means one program at a time, and
the sections are already ordered read-then-write, so the switch falls between
them naturally.

| section | how |
|---|---|
| **A** | `python3 upstream/tools/console-dump.py catch` — streams ESC across power-on |
| **B** | `python3 upstream/tools/console-dump.py cmd --at-prompt DW …` per cell. `DW` and `DB` are not on the refusal list |
| **B2 §E** | the same tool. `PHYR` and `MDIOR` are not on the refusal list either — **and neither are `PHYW`, `MDIOW` and `PORT1`, which all write hardware.** See below |
| **C, D** | close the tool, `picocom -b 38400 /dev/ttyUSB0`, type by hand, capture the log |
| **B2 §F** | still in picocom, after `D3`. One cell, and it is the only one in the visit that can cost a power cycle |
| afterwards | `python3 upstream/tools/console-lint.py` over the capture. **Read the log with the linter, not by eye** |

> 🔴 **The refusal list is `("FLW", "EB", "EW", "AUTOBURN", "LOADADDR", "J ")`, and
> it has no notion of a *register* write.** `PHYW` and `MDIOW` write PHY
> registers; `PORT1` writes 884 of them and takes no arguments. The tool will
> send all three without comment. That is not a bug in a tool pinned read-only at
> `4d3ff26` — it is a model of "write" that predates these commands being read.
> **The do-not-type list below carries the gap.**

**Running order for the visit**: `B1 §A` → `B1 §B` → `B2 §E` → close the tool,
open picocom → `B1 §C` → `B1 §D` → `B2 §F`. `B2 §E` is read-side and goes
through the tool, so it belongs with `§B`; `B2 §F` is last on purpose, because
if it is wrong it ends the session and by then nothing is left to lose.

> ⚠️ **`B2` is a session name *and* a cell name in this file**, and they are not
> the same thing: `B2` on its own is a cell of session B1 (`DW 8040FBD4 8`,
> the JEDEC ID), while the second session is always written `session B2` or
> `B2 §E` / `B2 §F`. Session B2's cells are lettered `E` and `F` for exactly
> this reason. A command re-stated under the wrong label is how upstream's
> `A2.7` went wrong four ways at once.

> ⚠️ **`--at-prompt` is not optional once the board is sitting at `<RealTek>`.**
> Without it the tool streams ESC for the full window and then reports *"nothing
> came back at all — TX/RX swapped, wrong port, or the board never powered on"*,
> which is three causes and none of them the real one. Upstream lost a session
> to exactly this.

**This session is driven cell by cell, live.** Paste each reply back before the
next command is sent; several cells decide whether the next one is worth
sending, and **B1 decides whether any of them are.**

### A — catch the prompt

| | step | expected | if not |
|---|---|---|---|
| **A1** | console attached, capture from before power-on; power on and send ESC through the window | the stage-1 banner, then `<RealTek>` | the ESC window is ~4.9 s wide on this unit (banner to `Jump to image start` measured 4.886 s on 2026-08-18). Missing it costs one power cycle, nothing else |
| **A2** | keep the full log | a boot log to compare against 2026-08-17/18 | — |

> The prompt appearing does **not** mean the command loop is ready — upstream
> found `<RealTek>` may be drawn from the interrupt path. Wait for a command to
> echo before trusting it.

### B — reads. Every one is zero-risk, and every one has a precomputed answer

`DW <addr> <len>`: **the address is hex, the length is DECIMAL**, it counts
**words**, and it prints **four per line**. So `1` prints one line of four
words. See `docs/loader-command-semantics.md` §f.

| | command | expected | what it refutes |
|---|---|---|---|
| **B1** | `DW 8040DBC0 1` | `8040B070 00000000 80409A9C 8040B074` | **the global control.** Four exact words: the `?` row of the command table — name pointer, `argc`, handler, help pointer. If this line is right, the load base, the table address, the 16-byte stride and the field order are all right, and RAM holds what the dump says. **If it is wrong, stop: every other address in this sheet is suspect** |
| **B2** | `DW 8040FBD4 8` | word 1 = **the JEDEC ID — this is the measurement**; then `+12 = 00400000`, `+16 = 00010000`, `+20 = 00000040`, `+24 = 00001000` | **`C-3`.** Four controls in the same output as the unknown. If they match, the ID is trustworthy. If they do not, the descriptor layout is misread and the ID must not be recorded. `docs/loader-flash-write.md` |
| **B3** | `DW 8040DD3C 1` | `05060000 ???????? ???????? 80500000` | **the scan reading, `C-1`.** Word 1 is the accepted candidate biased by `0x05000000` — `0x05060000` means the loader found the kernel at flash `0x060000`, the last of its six candidates. Word 4 is the image's `startAddr` from its own header. Anything else and `docs/loader-command-semantics.md` §a is wrong |
| **B4** | `DW 80500000 1` | `00000000 00008021 40906000 00000000` | **that `check_image()` copied the payload into RAM during the *check*, before the ESC window** — the mechanism behind upstream's `T-09`. These are flash `0x060010`'s first 16 bytes. If RAM here is zeros or garbage, the copy happens later and §a's step 3 is wrong |
| **B5** | `DW 8040DBA4 1` | `00000000 00000010 ???????? ????????` | word 1 is `gCHKKEY_HIT`; **`0` is required**, because `1` makes `check_image()` declare every image bad (`C-13`). Word 2 is the block counter: **exactly `0x10` = 16**, which is `ceil(987138 / 65536)` — one increment per 64 KiB of the kernel image, and the only image that reaches the checksum loop. Both initialisers are `0` in the image, so the count is clean. A different count means a different set of candidates got that far |
| **B6** | `DW 8040D4A0 1` | word 1 = `00000001` | 🔴 **`AUTOBURN` defaults to ON.** Its initialiser in the image is `1`. Confirming it on the device is what makes the "never upload without sending `AUTOBURN 0` first" rule a measurement rather than a habit |
| **B7** | `DW B8003110 1` | `???????? ???????? 000E0000 ????????` | word 3 is `CDBR`, and `0x000E0000` is what the loader writes at `0x80408F34` — divisor field 14. Word 4 is `WDTCNR`; **record bit 20 (`WatchDogIND`) — it should be `0` after a power-on reset.** This is D2's baseline. All four addresses are documented registers in the datasheet's timer block |
| **B8** | `DW 8040DBC0 A` | **nothing at all** | the radix, a second way. `strtoul("A", …, 10)` parses no digits and returns `0`, and `DW` prints nothing for a zero length. Output here would mean the length is hex after all |
| **B9** | `DW 8040DBC0 10` | **three** lines | the radix, a third way: `i` runs 0, 4, 8 against a limit of ten. Four lines would mean `0x10` |

### C — the write primitive, on scratch RAM

**This is what R4's kernel command-line plan rests on** — see
`docs/loader-command-semantics.md` §d, option 2. If `EW` does not write where it
is told, that plan does not exist.

Scratch address `0x81000000`: 16 MiB into the 32 MiB of SDRAM, far above the
loader's image (ends `0x8040DD10`) and far above the staged kernel
(`0x80500000` + `0x0F1002` ≈ `0x805F1002`).

| | command | expected | what it refutes |
|---|---|---|---|
| **C1** | `EW 81000000 DEADBEEF CAFEBABE` | **no output whatsoever** | `EW` is silent. Any echo and §f is wrong |
| **C2** | `DW 81000000 1` | `DEADBEEF CAFEBABE ???????? ????????` | `EW` writes 32-bit words at the address given, in order |
| **C3** | `EW 81000102 11111111` then `DW 81000100 1` | `???????? 11111111 ???????? ????????` — the value at `0x81000104`, **not** `0x81000100` | 🔴 **`EW` rounds an unaligned address *up*, silently.** If `11111111` lands at `0x81000100`, it rounds down; if the command is refused, it validates. Either would change every `EW` written from now on |
| **C4** | `EB 81000200 41 42 43` then `DB 81000200 4` | `41 42 43` at `…200`, `…201`, `…202` | `EB` writes bytes at the address **verbatim** — no rounding, unlike `EW` |

### D — the reset. Last, because it ends the session's state

| | command | expected | what it refutes |
|---|---|---|---|
| **D1** | `J BFC00000` | the console prints `---Jump to address=BFC00000`, then the board resets | it writes `WDTCNR = 0` and spins; only the watchdog can leave that loop. **The acceptance condition is not "it reset" — it is "the ESC window appears again afterwards"** (`C-8`). Catch the prompt again |
| **D2** | `DW B8003110 1` | word 4 bit 20 (`WatchDogIND`) = **`1`**, against B7's `0` | 🔴 **this is the cell worth the seating.** The datasheet says `1` = a watchdog reset occurred, `0` = power-on or pin reset. If it reads the same in both cases the bit does not discriminate on this part, and `C-8` needs another observable before R4's `bench-ci` can be built on it |
| **D3** | press the push button beside the barrel jack, console attached | a full stage-1 cold boot: `Booting...` and the banner | **`C-14`.** Anything less — nothing, or a reboot without the stage-1 lines — means the button is a GPIO, not `RESET#`. `notes/power-and-programmer.md` §3 |

---

## Do not type, this session

| | why |
|---|---|
| 🔴 **`PORT1`, with or without arguments** | it reads no `argv` and no `argc`. It is a factory-test routine that walks a Gray-code table through PHY vendor register 19 on PHY addresses `{0, 2, 3, 4}` — **884 PHY register writes** (612 of the Gray-code payload into register 19, plus 272 page-select and control writes), with no way to stop it. `docs/loader-phy-and-switch.md` §4. **`console-dump.py` will send it** |
| **`PHYW` or `MDIOW`, any arguments** | they write PHY registers, and B2 is a read session. Also on the tool's blind side |
| a bare `EB`, `EW`, `LOADADDR`, `FLR`, `FLW`, `PHYR` or `PHYW` — no arguments | six handlers dereference `argv[0]` before any count test, and the tokeniser zeroes all twenty slots, so it reaches `strtoul(NULL, …)`. **Costs a power cycle.** Listed so it is not typed by accident. (`MDIOR` and `MDIOW` are **not** in this group — both check `argc` and print `Parameters not enough!`) |
| **`MDIOR <phyid> <reg>`, the form its own help string gives** | the handler reads `argv[0]` only and parses it **base 10** as the *register*, then sweeps the PHY address itself. `MDIOR 0 2` silently sweeps register **0**. `docs/loader-phy-and-switch.md` §3 |
| `J` with no argument | `blez a0` skips the parse and jumps to whatever is on the stack |
| `FLW`, anything | it writes flash. Mainline is zero-write through R9 |
| any TFTP upload | **`AUTOBURN` defaults to `1`** (B6). An upload that completes without `AUTOBURN 0` having been sent is burned to flash |
| a TFTP filename containing `nfjrom` or `boot.img` | those two names force the load address to `0x80000000` and execute the image the moment the transfer ends, with nobody at the console |
| `EW` or `EB` anywhere below `0x80500000` | the loader's own image and `.data` live at `0x80400000`–`0x8040DD10` |

---

## Results

*Empty until the session. Fill the reading beside each row, and write the
verdict even where it is the boring one.*

| cell | reading | verdict |
|---|---|---|
| A1 | | |
| B1 | | |
| B2 | | |
| B3 | | |
| B4 | | |
| B5 | | |
| B6 | | |
| B7 | | |
| B8 | | |
| B9 | | |
| C1 | | |
| C2 | | |
| C3 | | |
| C4 | | |
| D1 | | |
| D2 | | |
| D3 | | |

---

## Session B2 — PHY and switch, on the same power cycle as B1

**Written 2026-08-23 from `docs/loader-phy-and-switch.md`, which owns every claim
below.** B2 does not have a power cycle of its own: it rides on B1's, in the two
places the running order above puts it.

| | |
|---|---|
| **Power cycles** | **0 of its own.** Rides on B1's one |
| **Flash bytes written** | **0** |
| **RAM written** | **0** |
| **Registers written** | 🔴 **not zero.** `MDCIOCR` once per PHY read, and **`GIMR` bit 8**, which `phy_read()` sets and never restores. B2 is zero-write to flash and memory; it is **not** register-read-only, and calling it "zero risk" would be wrong |
| **New code needed** | none |
| **Closes** | the input R6 needs — which PHY addresses exist, which port each one serves, and how the switch is left configured. Hands `C-8` its missing bus-clock number. Puts `PORT1` on the do-not-type list, which is where the desk work said it belongs |

**Two things B2 needs that B1 does not.** An Ethernet cable with something at the
far end — a PC NIC is enough, link only, no traffic. And **a clock you can read
to the second**, for `E2`.

### E — reads, through `console-dump.py`, alongside B1 §B

`python3 upstream/tools/console-dump.py cmd --at-prompt <words…>`. `PHYR` and
`MDIOR` are not on the refusal list. **`--at-prompt` is not optional** — same
trap as B1.

| | command | expected | what it refutes |
|---|---|---|---|
| **E1** | `DW 8040DCE8 1` | word 2 = `00002000` | **the gate's control.** `0x8040DCEC`'s initialiser in the image is `0x1000`; the code writes `8192` there immediately after `timer_init` returns. `00002000` means the timer was initialised. `00001000` means it was not, and then `E2` cannot pass. Word 1 is the tick counter — non-zero, value not predictable |
| **E2** | wait **≥ 10 s by the clock**, then `DW 8040DCE8 1` again | word 1 advanced by ≈ **100 × seconds waited** | 🔴 **the gate, and the whole session's PHY half depends on it.** `phy_read()` calls `delay(10)`, which waits for the timer ISR to advance `0x8040DCE8`; `doBooting()` cleared `GIMR` on the way to this prompt. **No advance → send no PHY command: the board would hang inside the delay, not in the MDIO poll.** A rate that is not ~100 Hz → the compiled-in `200000000` at `0x8040DBA0` is not this board's clock, which is worth more than the number. `docs/loader-phy-and-switch.md` §2 |
| **E3** | `DW B8003000 1` | word 1 (`GIMR`) **bit 8 = `0`**; word 4 (`IRR1`) = `00050004` | the "before" half of `E5`, and `IRR1` is its control — the loader writes exactly that constant at `0x80408F90`. If bit 8 is already `1`, something between `doBooting()` and the prompt sets it and §2's chain is incomplete |
| **E4** | `PHYR 0 2` | `PHYID=0x0, regID=0x2 ,Find PHY Chip! UID=0x????` | **the first MDIO transaction this device has ever performed.** The two echoed fields are the control — `0x0` and `0x2` prove the base-16 parse. **`UID` cannot be predicted from any source** (§6: the datasheet has no PHY register map, the vendor's only ID constant is an external gigabit part, and no capture contains this string). It must be neither `0000` nor `ffff` |
| **E5** | `DW B8003000 1` | word 1 **bit 8 now `1`**, word 4 unchanged | 🔴 **the causal control, and it was predicted from the code before the visit.** `phy_read()` does `GIMR \|= 1<<8` at `0x80402FB8`. A specific bit, predicted to change, on demand. If it does not change, the function at `0x80402F80` is not what §1 says it is |
| **E6** | `PHYR 0 3` | as `E4`, `regID=0x3` | the low half of the identifier. Together with `E4` it is the 32-bit value everything else compares against |
| **E7** | `PHYR 2 2`, `PHYR 3 2`, `PHYR 4 2` | **all three equal `E4`'s `UID`** | `PORT1` patches addresses `{0,2,3,4}` from one table — this unit's own code saying they are one PHY macro. Different values refute that, and refute using one `phylib` driver for all of them |
| **E8** | `PHYR 1 2` | the same value again | **the address `PORT1` skips.** Same → the skip is about the port. Different, or no answer → it is about the PHY, and R6 needs to know that |
| **E9** | `DW BB804100 8` | 🔴 **the load-bearing part**: word 1 = `00000001`, and words 3–6 **bits 30:26** = `1, 2, 3, 4` (top hex digits `04`, `08`, `0C`, `10`). *Weaker, same cell, judged separately*: bits 22:16 = `7F` on all four | **the PHY-address map, read without MDIO.** Word 1 is `PITCR`: the loader does `\|= 1` at two sites, and this unit printed `P0phymode=01, embedded phy` at boot — **against a datasheet that calls `01` Reserved.** Words 3–6 are `PCRP1`–`PCRP4`, which the loader never writes, so they hold reset defaults. **`ExtPHYID` at 30:26 is the half this session depends on and it is what `F2`'s sweep is checked against; the `FrcAbi`/`Pause` defaults at 22:16 come from a watermarked draft's default column and a wrong reading there must not be allowed to read as "the cell failed".** Word 2 is `PCRP0`, which the loader *does* configure — **record it, do not predict it** |
| **E10** | `DW BB804128 8` | **`PSRP0`–`PSRP4`. With no cable in: every word bit 4 = `0`** | link state per port, no MDIO. Bit 4 = `LinkUp`, bit 3 = duplex, bits 1:0 = speed (`01` = 100M), bit 8 = `LinkDownEventFlag`, latched and **read-to-clear**. All-zero with nothing plugged in is the cheaper half of `E11`'s control: a zero that then becomes a one is worth more than a one on its own |
| **E11** | plug the cable into **one LAN jack**; `DW BB804128 8`. Then move it to the **WAN jack**; `DW BB804128 8` again | **exactly one word has bit 4 set each time, and it is a different word the second time.** On the first read after the move, the vacated port's bit 8 reads `1`; read it again and bit 8 is `0` | 🔴 **the causal control on the whole switch-register reading.** This is what maps a physical RJ45 to a port index, and it is a change you make rather than a value you accept. If the bit does not follow the cable, the register is not port-indexed the way Table 62 says, and `E9`'s map means nothing. Upstream's boot log says port 0 carries vid 8 while ports 1–4 carry vid 9 — **so the WAN jack should light word 1** |
| **E12** | `PHYR <n> 1`, where `n` is **the PHY address `E9` reports in bits 30:26 of the `PCRP` for the port `E11` lit** — not the port index, even though the default map makes them the same number | bit 2 (`Link Status`) set, bit 5 (`Autoneg Complete`) set | MII `BMSR`, the same fact through the other instrument. Two paths, one silicon. If `PSRP` and `BMSR` disagree about link, one of them is not reading the port you think it is. **Taking `n` from `E9` rather than from the port number is the point**: if `ExtPHYID` ever differs from the port index, the shortcut hides exactly the thing R6 needs |

### F — last of the whole visit, in picocom, after `D3`

**Everything above has been captured by the time this runs.** That is the point:
`F1` is the only cell in either session that can end the visit.

| | command | expected | what it refutes |
|---|---|---|---|
| **F1** | `PHYR 5 2` | **it returns**, with `UID=0xffff` or `0x0000` | 🔴 **the negative control, and it is the risk.** `phy_read()`'s wait on `MDCIOSR` bit 31 has **no timeout and no iteration bound** (`bltz v1, …` at `0x80402FD8`). The datasheet assigns `ExtPHYID` only for ports 0–4, so address 5 should not answer. **If it does not return, the board is stuck and the visit is over** — and the finding is that `MDIOR` must never be run on this part. If it returns `ffff`, that value is also what `F2`'s rows 5–31 must show |
| **F2** | `MDIOR 2` — **only if `F1` returned** | 32 lines. `PhyID=0x00`…`0x04` carry `E4`/`E7`/`E8`'s value; `0x05`…`0x1f` carry `F1`'s | **the sweep, and its own refutation is built in: all 32 lines identical and plausible means the bus is echoing and nothing was measured.** Note the arity trap — `MDIOR` takes **one** argument, the register, **base 10**, and sweeps the address itself. Its help string says otherwise. If driving this through the tool, `--timeout 45`: 32 × 10 ms of erratum delay plus 32 lines at 38400 is under a second, but a tool timeout and a hung board look identical, and **the tool timing out does not un-stick the board** |

---

## Results — B2

*Empty until the session. Fill the reading beside each row, and write the verdict
even where it is the boring one.* **`E4`'s `UID` has no predicted value**, so its
verdict is a measurement and not a confirmation — say so in the cell.

| cell | reading | verdict |
|---|---|---|
| E1 | | |
| E2 | | |
| E3 | | |
| E4 | | |
| E5 | | |
| E6 | | |
| E7 | | |
| E8 | | |
| E9 | | |
| E10 | | |
| E11 | | |
| E12 | | |
| F1 | | |
| F2 | | |
