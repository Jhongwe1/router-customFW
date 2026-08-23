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
| **C5** 🆕 | `DW B8003000 1` → `EW B8003000 8000` → `DW B8003000 1` → `PHYR 0 2` → `DW B8003000 1` | in order: `00008100` · *(silent)* · **`00008000`** · `UID=0x0000001c` · **`00008100`** | 🔴 **`E5` recovered as a write, because `E5` as a read was void on arrival** — `GIMR` bit 8 was already `1`, so the bit predicted to flip had nothing to flip from. Clearing it first makes the prediction testable: **`phy_read()` sets `GIMR` bit 8 at `0x80402FB8` and this is the only thing that would put it back.** Reading `00008000` in the middle is a second finding on its own — it proves the console survives with `TCIE` masked. The value `8000` preserves bit 15 (`SWIE`), which is also set. **Licensed by a call-graph walk**: no path from the command loop at `0x80409144` to `tick()`, `delay()` or the ESC-wait, with the same walker finding `PHYR → phy_read → delay → tick` as its control. **If the third command returns nothing, the walk was wrong and the board is hung — that is the risk, and it is one power cycle** |
| **C6** 🆕 | `AUTOBURN 0` — **through `console-dump.py rescue`, not by hand** — then `DW 8040D4A0 1` | the loader echoes `AutoBurning=0`; then word 1 = **`00000000`**, against `B6`'s measured `00000001` | 🔴 **the one command standing between R0 and a flash write, and it has never been shown to work.** `AUTOBURN` is read at exactly one instruction in the whole image, `0x80401B9C`, on the upload-completion path, and `B6` measured the global at `0x8040D4A0` as `1` on this device. **Two independent sources are needed and only one exists today**: the loader's own echo is the loader telling you what it thinks; `DW 8040D4A0` reads the word the burn path actually consults. **And the syntax is not obvious** — the help prints `AUTOBURN: 0/1`, which is not the syntax, and the string table holds `AUTOBURN` and `AUTOBURN: 0/1` as two separate strings; `console-dump.py rescue` tries four forms, **every one of them carrying `0`**, and stops if the reply says `AutoBurning=1`. A wrong form returns `Unknown command !`, **which in a flow with no readback looks exactly like success.** Refuted by: the word reading `00000001` after the echo said `0` — then the echo is not the switch and nothing may be uploaded |
| **C7** 🔄 | **rewritten 2026-08-24, before it ran, because `§A` measured the thing it was going to discover.** **C7a**: `EW 81000400` + **twelve** distinct values (119 characters), then `DW 81000400 3`. **C7b**: `EW 81000440` + eleven values padded to **127** characters, then `DW 81000440 3` | C7a: all twelve land, in order, at `0x81000400`…`0x8100042C`. C7b: all eleven land -- it is C7a's boundary control | 🔴 **the original cell sent eighteen values in a 173-character line, and that line is dangerous on this loader.** Measured `§A` 2026-08-24: the console line buffer is **128 bytes** -- exactly 128 ESC bytes produced `Unknown command !`, seven times -- and read out of the code at `0x80409190`/`0x804091A0` the command loop does `memset(buf, 0, 128)` then `readline(buf, 128, 1)`. Two sources. **`readline` writes its NUL only on the `
` path** (`0x804070FC`); the `
` path and the length-limit path (`0x80407194`, `count < 128`) both return without one, and the caller's `memset` only saves a line **shorter** than 128 because that leaves at least one zero inside the buffer. **A line of exactly 128 characters is therefore unterminated, and the tokeniser at `0x80407248` scans past `sp+143` into eight bytes of stack slack and then into the saved registers.** `EW 81000400 ` + twelve values + the thirteenth's eight hex digits is exactly 128, so the original C7 would have been cut precisely there -- **with `EW` as the command**. So: **never 128.** Twelve values is the largest n with `11 + 9n < 128`. **And the cell's own question is already answered**: one line carries **twelve words, 48 bytes**, so a 1 KiB bare-metal probe needs **22 lines, not 15** -- R1's no-network path is 47% more expensive than the sheet assumed, and that number is now measured rather than derived from a buffer length nobody had checked |
| | *(the original cell, kept because a superseded plan is a record)* | | `EW 81000400 <v1> … <v18>`, eighteen values, expecting all eighteen to land. Its stated failure mode to watch for was *"truncation, or the prompt never coming back"* -- **which was the right thing to fear, and `§A` measured it for free two cells earlier** |

### D — the reset. Last, because it ends the session's state

| | command | expected | what it refutes |
|---|---|---|---|
| **D1** 🔄 | **through the tool, not by hand**: `console-capture.py capture --port /dev/ttyUSB0 --out <dir>/D1 --send 'J BFC00000' --seconds 30` | the capture holds `---Jump to address=BFC00000`, a silence, then the stage-1 banner. Then `console-capture.py report <dir>/D1 --from 'Jump to address=BFC00000' --to 'RealTek\(RTL8196E\)'` | it writes `WDTCNR = 0` and spins; only the watchdog can leave that loop. **The acceptance condition is not "it reset" — it is "the ESC window appears again afterwards"** (`C-8`). Catch the prompt again |
| **D1b** 🆕 | *(no command — read the number `D1`'s report prints)* | **a wall-clock interval, order of a second. Value not predicted** | 🔴 **What this number is NOT.** It is **not** the watchdog timeout. `WDTCNR = 0` selects `OVSEL[3:0] = 0000` = 2^15 base-clock ticks, and against `E2`'s measured 199.48 MHz that is **164 µs** undivided or **2.30 ms** through `CDBR`'s divisor of 14 — and even the longest of the ten settings (2^24) is 84 ms / 1.18 s. **Every one of those is below what any instrument in this session can resolve**, and the CP2102's latency timer (1–16 ms typical, unmeasured here) is a further floor. So the interval is the post-reset boot, and **that is the number `C-8`'s owner actually needs**: R4's `bench-ci` sets its timeout from it. Recording it as "the watchdog timeout" would be a measured quantity wearing another one's name. **Refuted by**: an interval over ~10 s (nothing in the model predicts that), or the banner never arriving (then `D1` failed, not this cell) |
| **D2** 🔄 | `DW B8003110 1` | **word 4 = `A5100000`** — the whole word, not just the bit | 🔴 **this is the cell worth the seating, and it got stronger.** Measured at the desk 2026-08-24: **the loader never writes `WDTCNR` except at two sites, `0x804012F8` (the `reboot.......` path) and `0x804092E8` (this command), and both are `sw zero` followed immediately by `j` to themselves with a `nop` in the delay slot** — so nothing executes after either. Search coverage: the `0x311c` immediate (2 hits, both these), `TC_BASE 0x3100` + displacement 28 (the one `ori …,0x3100` at `0x80408F38` builds a constant, not a store), and every non-`sp` `sw …,28(reg)` (3, resolving to `0xBB804D00`, the SPI descriptor at `0x8040FBD4`, and `0xB8B20000`). **Positive control: the same method finds the `CDBR = 0x000E0000` write at `0x80408F34`, which `B7` measured on the device.** Two consequences. ① `B7`'s `A5000000` is the **hardware reset default**, not something the loader wrote — `B7`'s verdict implied otherwise and is corrected. ② **There is no software in `D2`'s path at all**, so it reads the hardware directly. `A5000000` here means `WatchDogIND` does not survive the reset it reports, **`C-8` loses its discriminator**, and R4's `bench-ci` falls back to `D2b` |
| **D2b** 🆕 | `DW 81000000 1` | **`DEADBEEF CAFEBABE`** — the words `C1` wrote earlier in this same seating | 🆕 **a second discriminator for `C-8` that does not depend on `WatchDogIND`.** SDRAM contents survive a warm reset and not a power cycle, so a scratch word that is still there says "warm" without reading any status bit. Costs nothing: the value is already at that address from `C1`. **Its own refutation is `D3`**: after the button (a cold boot, if `C-14` says the button is `RESET#`) the same read must come back *changed*. If it reads `DEADBEEF` in both cases the loader does not clear DRAM and this discriminates nothing either; if it reads garbage in both, it clears DRAM on every init. **Two independent observables, and the session tells you which of them works** |
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

**Run 2026-08-23, from 21:51. Sections A and B complete; C and D pending an
operator.** Logs: `$FWRE_WORK/rebuild/bench-2026-08-23/`.

| cell | reading | verdict |
|---|---|---|
| A1 | banner byte-identical to 2026-08-17/18: `---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)`. `?` returned all seventeen commands | OK **and more than asked**: the command loop is confirmed *ready*, not merely the prompt drawn, because `?` echoed and returned. `MDIOR:  MDIOR <phyid> <reg>` and `PORT1: port 1 patch for FT2` appear on the device exactly as `loader.json` has them |
| A2 | *(seating 1)* not captured · 🔄 **seating 2, 2026-08-24: captured, 1,306 bytes**, `bench/2026-08-24/A-catch.{log,timing,meta.json}` | *(seating 1)* WARN **the instrument cannot do this cell.** `catch` prints the banner line and discards the rest of the pre-prompt stream. · 🔄 **RESOLVED, and by changing the instrument rather than the cell.** `tools/console-capture.py capture --esc 25` streams ESC from **inside** the capture loop, so the pre-prompt stream is kept instead of discarded. Boot log matches 2026-08-17/18 line for line, and **`---Escape booting by user` is absent**, which is what `C-13` predicts once ESC has set `gCHKKEY_HIT` |
| B1 | `8040B070 00000000 80409A9C 8040B074` | **exact.** Load base, table address, 16-byte stride, field order, and "RAM holds what the dump says", all four at once |
| B2 | `001C7016 1C701600 16000000 00400000` / `00010000 00000040 00001000 00000400` | **all four controls exact** (`+12/+16/+20/+24`), so the descriptor layout is right and the ID is trustworthy. **JEDEC ID = `0x1C7016`** -- manufacturer `0x1C`, capacity byte `0x16` = 2^22 = 4 MiB. `C-3`'s headline answered with a measured value |
| B3 | `05060000 00000000 00000000 80500000` | WARN **value matches, reading refuted.** `0x8040DD3C` is written *before* each `check_image()` call (`0x804080C0`), so it holds the candidate **being tried**, not the accepted one. With `gCHKKEY_HIT` set (B5) every check fails, the sweep runs to the end, and the last candidate is `0x060000` -- which is also where the kernel is. **The cell cannot discriminate on this unit.** Word 4 `80500000` still stands |
| B4 | `00000000 00008021 40906000 00000000` | WARN **value exact, mechanism refuted.** The cell says `check_image()` copied it during the check. It cannot have: `check_image()`'s first act is to read `gCHKKEY_HIT` and return before the copy. Something else fills `0x80500000` -- now `C-16` |
| B5 | `00000001 00000000 00000000 00000001` | **REFUTED, and it is the most informative cell in the section.** Predicted `gCHKKEY_HIT` = 0 and counter = 16. Read 1 and 0. Streaming ESC from before power-on sets the flag, `check_image()` short-circuits, and the checksum loop never runs. **The prediction assumed a boot that was not interrupted -- which is not the boot this sheet produces.** It is what exposed B3 and B4 |
| B6 | `00000001 00000000 00000000 00000000` | **`AUTOBURN` = 1 on the device.** The never-upload-without-`AUTOBURN 0` rule is now a measurement and not a reading |
| B7 | `C0000000 80000000 000E0000 A5000000` | **exact, plus three free.** `CDBR = 000E0000` as predicted; `WatchDogIND` (w4 bit 20) = **0** after power-on, which is D2's baseline. Unasked and now known: `TCCNR = C0000000` and `TCIR = 80000000` are exactly what `timer_init` writes, and `WDTE[7:0] = 0xA5` is the stop pattern, so the watchdog is stopped as documented |
| B8 | nothing at all | **exact.** `strtoul("A",_,10)` = 0, zero length, no output. The radix is decimal |
| B9 | three lines | **exact.** And the three rows carry `?`/`DB`/`DW`'s handlers `80409A9C`/`804095D0`/`804094B4`, matching `loader.json` |
| C1 | 🔄 **2026-08-24, C1's own cell: `EW 81000000 DEADBEEF CAFEBABE` printed nothing but its own echo** | **PASSES.** `EW` is silent, on scratch RAM and in the multi-value form. *(seating 1, via `C5`: the same on a hardware register.)* **The silence is only meaningful because `C2` reads it back** -- a cell whose expected answer is *nothing* cannot tell a silent command from a command that never arrived |
| C2 | 🔄 **2026-08-24: `81000000: DEADBEEF CAFEBABE FFFFFFFF 00000000`** | **PASSES, and it closes the half `C5` could not reach.** Both words landed, in order, at the address given. **`EW` writes 32-bit words consecutively from the address, and is silent** -- `docs/loader-command-semantics.md` §d option 2, the fixed-address cmdline buffer R4 patches before `J`, now rests on a measurement rather than a reading. Words 3-4 are untouched SDRAM and were not predicted |
| C3 | 🔄 **2026-08-24: `81000100: 00000400 11111111 FFFFFFFF 00000000`** | 🔴 **CONFIRMED, and it is the sharp one.** `EW 81000102` put `11111111` at **`0x81000104`** -- `EW` rounds an unaligned address **up**, silently. Not down, and not refused. Every `EW` written from here on has to assume it |
| C4 | 🔄 **2026-08-24: `81000200: 41 42 43 00   ABC.`** | **CONFIRMED, and the asymmetry is the finding.** `EB` writes bytes at the address **verbatim** -- no rounding -- while `C3` shows `EW` rounding up. **One loader, two write primitives, opposite address handling.** Byte-granular patching must use `EB`; word patching must be aligned by hand |
| **C6** | 🔄 **2026-08-24: `AUTOBURN: 0` -> `Unknown command !`; `AUTOBURN 0` -> `AutoBurning=0`; then `8040D4A0: 00000000 …`** | 🔴 **CLOSES, on two independent sources, and it is the cell that lets `B3` start.** The echo is the loader saying what it thinks it did; the word at `0x8040D4A0` is what the one instruction that reads it (`0x80401B9C`, on the upload-completion path) will actually see. `B6` measured `00000001`; this reads `00000000`. **And the hazard the cell was written around is now demonstrated rather than argued**: the help string's own form, `AUTOBURN: 0`, returns `Unknown command !` -- in a flow with no readback that is indistinguishable from success. `IPCONFIG:10.1.1.1` failed the same way and `IPCONFIG 10.1.1.1` worked, so the colon form is wrong for both. `bench/2026-08-24/C6-rescue.json` |
| **C7** | | pending -- **and rewritten before it ran**, see below |
| **A0** 🆕 | 🔄 **2026-08-24: first attempt `Unknown command !`; second attempt `8040DBC0: 8040B070 00000000 80409A9C 8040B074`** | 🆕 **a cell that did not exist when this sheet was written, and it earned its place twice.** It exists because seating 2 drove every cell through `console-capture.py`, which **re-opens the serial port per cell**; re-opening toggles DTR/RTS and nothing had confirmed those are unconnected on this 4-pin header (`BRD-09`). ① **They are: the board did not reset** -- the reply was `<RealTek>`, not `Booting...`. Inference to measurement. ② `B1` reproduced exactly on a second power cycle. ③ **The first attempt failing is the informative half**: `§A`'s capture was cut mid-ESC-stream leaving **12 unconsumed ESC bytes in the loader's line buffer**, and this command appended to them. The line buffer is per-`readline`, not per-connection, and it survives a capture boundary. **Standing rule: after any capture cut by `--seconds`, send one bare `
` before the next command** |
| **C5** | `00008100` -> *(silent)* -> **`00008000`** -> `UID=0x0000001c` -> **`00008100`** | **PASSES, and it is the causal control the whole of `E5` was for.** A bit cleared by hand came back, and `phy_read()`'s `GIMR \|= 1<<8` at `0x80402FB8` is the only thing that puts it there. **Two findings arrived free in the same transcript.** (a) The middle `DW` answered at all, so **the console does not need the timer** -- the call-graph walk that licensed this cell was right, and it is now measured rather than argued. (b) 🔴 **`GISR` moved `88000004` -> `88000104` -> `88000004`.** Bit 8 is `TCIP`, timer interrupt *pending*: with `TCIE` masked the interrupt could not be taken so it latched, and re-enabling it let the ISR run and ack. **The mask, the latch, the delivery and the ack are all visible in five lines**, and none of it was predicted |
| D1 | | 🔴 **not run 2026-08-24, and the reason is the instrument.** `D1` sends `J BFC00000`, the board resets, and `D2`/`D2b` must read **the loader prompt of that warm boot**. So one capture has to send a command and *then* stream ESC across the reboot. `console-capture.py`'s `--esc` runs **before** `--send` (the ESC loop sits above `ser.write(line)` in `capture()`), so it cannot. Running `D1` alone would boot the vendor kernel and cost a power cycle to recover -- which destroys the warm-reset condition `D2b` exists to test. **Fixed at the desk with `--esc-after`, not improvised at the bench: this is the third cell lost to an instrument that could not do it (`A2`, `E5`), and the first one caught before it ran** |
| D1b | | pending, with `D1` |
| D2 | | pending, with `D1` |
| D2b | | pending, with `D1`. **Its payload is armed by `C1`** -- `DEADBEEF CAFEBABE` at `0x81000000` -- and a power-off discards it, so `C1` must be re-run before `§D` in any later seating |
| D3 | | pending -- needs a button press |
| D4 | | pending, after `D1` |

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
| | 🆕 **why that risk is accepted, written down rather than left as nerve** | | `MDCIOSR` bit 31 is the **controller's** completion flag, not the PHY's acknowledgement: an MDIO master clocks out its 64 bits and latches whatever the line holds, so an absent PHY yields `0xFFFF` from a bus pulled high rather than a transaction that never finishes. *Inferred from the register's role, pending this measurement* — the datasheet's Table 58 does not say what the bit does when nothing answers. `E4`, `E7` and `E8` already showed the controller completing eleven times. **So `F1` is placed before `D` and `R0` in seating 2 rather than last**: if the inference is wrong the cost is one power cycle, which also re-establishes `D2`'s power-on baseline, and the two cells behind it are worth more than `F` is |
| **F2** | `MDIOR 2` — **only if `F1` returned** | 32 lines. `PhyID=0x00`…`0x04` carry `E4`/`E7`/`E8`'s value; `0x05`…`0x1f` carry `F1`'s | **the sweep, and its own refutation is built in: all 32 lines identical and plausible means the bus is echoing and nothing was measured.** Note the arity trap — `MDIOR` takes **one** argument, the register, **base 10**, and sweeps the address itself. Its help string says otherwise. If driving this through the tool, `--timeout 45`: 32 × 10 ms of erratum delay plus 32 lines at 38400 is under a second, but a tool timeout and a hung board look identical, and **the tool timing out does not un-stick the board** |

---

## Results — B2

*Empty until the session. Fill the reading beside each row, and write the verdict
even where it is the boring one.* **`E4`'s `UID` has no predicted value**, so its
verdict is a measurement and not a confirmation — say so in the cell.

**Run 2026-08-23. `E1`-`E10` and `E12` complete; `E11` and section F pending an
operator.**

| cell | reading | verdict |
|---|---|---|
| E1 | `0000473A 001E8000 0ED80000 8040A2B4` | **the control was wrong.** Predicted w2 = `00002000` from `li v1,8192` at `0x80409004`; it reads `001E8000` = 2,000,000, so something writes it after that store. The cell's *purpose* is served by E2 far more directly, so the miss costs nothing -- but the control did not work |
| E2 | `00005F52` after **61.842 s** measured -> **6168 counts** | **99.74 Hz against 100.0 Hz predicted, 0.26%.** The gate passes: the timer ISR runs, `delay(10)` returns, PHY commands are licensed. **And it hands `C-8` its clock**: with `CDBR` = 14 and `TC0DATA` = 142,858 both read on the device, base = 99.74 x 14 x 142858 = **199.48 MHz** against the compiled-in `0x0BEBC200` = 200 MHz. A divisor of 15 would give 213.7 MHz, so the measurement also settles the divisor field's semantics |
| E2b NEW | `DW B8003100 1` -> `0022E0A0 00000000 0010B960 00000000` | **added at the bench, and it is what makes E2 a derivation rather than a coincidence.** `TC0DATA` = `0x22E0A0` = 142,858 << 4, exactly the image value, so the count field is bits 31:4 and the count is 142,858. Three of the four terms are now read on silicon |
| E3 | `00008100 88000004 00000000 30050004` | **REFUTED, and it voids E5.** `GIMR` bit 8 (`TCIE`) is **already 1** at the prompt; predicted 0. Bit 15 (`SWIE`) is set too, and `IRR1` reads `30050004` where the loader writes `00050004` -- `SWIRS` = 3 at bit 28. **`doBooting()`'s `GIMR = 0` is not the last write before the prompt**, so `docs/loader-phy-and-switch.md` section 2 layer 4 is wrong. Internally consistent: the tick could not advance otherwise |
| E4 | `PHYID=0x00000000, regID=0x00000002 ,Find PHY Chip! UID=0x0000001c` | **the first MDIO transaction this device has performed.** Both echoed fields correct, so the base-16 parse holds. `0x001C` -- neither `0000` nor `ffff`. Note the loader's `%x` pads to eight digits: the expected *rendering* in the cell was wrong, the values were not |
| E5 | not runnable | **void as designed.** The bit it predicted would flip 0->1 was already 1. Recovering it needs `EW` to clear `GIMR` bit 8 first -- a register write, so it belongs in section C and needs a decision, not a bench improvisation |
| E6 | `UID=0x0000c880` | full identifier **`0x001CC880`** |
| E7 | `PHYR 2 2`, `PHYR 3 2`, `PHYR 4 2` -> `1c`, `1c`, `1c` | **all three equal E4.** One PHY macro, as `PORT1`'s single table implied |
| E8 | `PHYR 1 2` -> `1c`; `PHYR 1 3` -> `c880` | **identical to the other four.** `PORT1` skipping address 1 is about the **port**, not the PHY. One driver covers all five |
| E9 | `00000000 007F0039 047F0039 087F0039` / `0C7F0039 107F0039 00000000 187F0038` | **the load-bearing half is exact**: `ExtPHYID` (30:26) reads 0, 1, 2, 3, 4 across `PCRP0`-`PCRP4`. The weaker half passes too -- `7F` at 22:16 on all five, the datasheet's `FrcAbi` = `11111` and `Pause` = `11`. **But `PITCR` reads `00000000`, predicted `00000001`** -- and `PCRP0` shows `EnForceMode` = 0, so **the whole strap-gated force-mode branch did not run on this board.** `P0phymode=01` is therefore *not* `PITCR` bits 1:0, and the claim that the loader names a value the datasheet calls Reserved is **withdrawn**: `PITCR` = 0 is `UTP (10/100M embedded PHY)`, which is exactly what the boot line says. 🆕 **Words 7 and 8 were read and never judged**: `0xBB804118` = `00000000` and `0xBB80411C` = `187F0038`, the second carrying `30:26` = **6**. On the `PCRP` per-port stride those are ports 5 and 6 — the stride is an inference, and no source held here names either address. Recorded 2026-08-24 while building `SPEC.md`; `NET-10` there points at this cell |
| E10 | `000010E0 000010E0 00001099 000010E0` / `000010E0 000000E2 0000007A 0000007A` | **exactly one port with `LinkUp`: `PSRP2`.** `0x1099` = NWayEnable, LinkUp, full duplex, speed `01` = 100M. The other four read `0x10E0`, bit 4 clear. **Independently corroborated off-device**: Windows reports the far end of that same cable `Up, 100 Mbps` |
| E11 | | pending -- needs a cable move |
| E12 | `PHYR 2 1` -> `78ED`; `PHYR 0 1` -> `78C9`; `PHYR 2 0` -> `1100`; `PHYR 2 5` -> `C1E1` | **a paired control on one instrument, which is what E5 was supposed to give.** Linked port: `LinkStatus` = 1, `AutonegComplete` = 1. Unlinked port, same register: both **0**. Capability bits 15:11 identical on both, so the difference is link state and not a different part. `BMCR` = `1100`, autoneg enabled and full duplex, agreeing with `PCRP2`'s `EnForceMode` = 0. `ANLPAR` = `C1E1`: selector `00001` = 802.3, 10/100 half and full, **Acknowledge set and Next Page set** -- the signature of a gigabit-capable partner, which is what is in fact on the other end |
| F1 | | pending -- the one cell that can end a visit |
| F2 | | pending |

---

## Seating 2 — the cells seating 1 could not reach, plus R0

**Written 2026-08-24 at the desk, from the same dump as seating 1** (`sha256
a800059a…10f37ea`, rule 2). **Nothing here needs preparation on the day.**

Seating 1 ran `§A`, `§B`, `E1`–`E12` and `C5`. What is left is `§C1`–`C4`,
`E11`, `§F` and `§D`; this seating adds five cells to them — `C6`, `C7`, `D1b`,
`D2b`, `D4` — and one new session, **`B3`, which is R0**.

### Running order, and it is not seating 1's

`§A` capture → `§C1`–`C7` → `E11` → **`§F`** → `§D` → **session `B3` (R0)**

Two changes from seating 1's order, both deliberate:

| change | why |
|---|---|
| **`§F` moves from last to the middle** | seating 1 put it last on the argument that if it hangs, nothing is left to lose. That was right when nothing was behind it. Now `§D` and `B3` are, and they are worth more — `B3` closes the active gate. `F1`'s hang is also cheaper than the sheet implies (see the note under `F1`), and the power cycle it would cost **re-establishes `D2`'s power-on baseline**, which `§D` needs anyway |
| **`§D` before `B3`** | `§D` resets the board twice (`D1`, `D3`) and `D4` resets it a third time. `B3` ends with a kernel running and the loader gone. Resets before the thing that is not coming back |

> 🔴 **Every reset puts `AUTOBURN` back to `1`.** Its initialiser in the image is
> `1` (`0x8040D4A0`) and `B6` measured `1` on the device. `C6` proves the switch
> works; **`B3` sends it again, after the last reset, as the operative guard.**
> Those are two different jobs and they are two cells.

### Before power is applied — the instruments, checked

**Two cells have already been lost to an instrument that could not do them**:
`A2`, because `console-dump.py catch` discards the pre-prompt stream, and `E5`,
whose "before" reading was already in its "after" state. A cell whose instrument
cannot produce its output is a cell that reads as done. So the instruments are
checked before the board is, and each check has an expected output.

| | check | expected | why this one |
|---|---|---|---|
| **P0** | `/usr/bin/python3 -c 'import serial; print(serial.__version__)'` | `3.5` | 🔴 **Measured 2026-08-24: the command this sheet names does not run in a fresh login shell.** `python3` on this host resolves to `~/.venvs/thermal/bin/python3`, which has **no** `serial` module; the apt package `python3-serial` is installed for `/usr/bin/python3`. So `python3 upstream/tools/console-dump.py …` fails with `ModuleNotFoundError` depending on invisible shell state. **Every command in this file uses `/usr/bin/python3` explicitly** |
| **P1** | `usbipd list` on Windows, then `usbipd attach --wsl --busid <id>` for `10c4:ea60` | `/dev/ttyUSB0` exists in WSL, group `dialout` | the CP2102 is `COM3` on the Windows side and is **not** in WSL until it is attached. It is in usbipd's persisted list, so it has been bound before |
| **P2** | `bash tools/test-console-capture.sh` | `7 passed, 0 failed` | the timing instrument `D1` and `D4` depend on. Five of its seven cases are controls that must fail; three of them **did** fail on first run, which is why they are trusted |
| **P3** | *(R0 only)* `ip -brief addr` in WSL | an interface that is **not** `eth0` | `eth0` is WSL2's NAT'd vNIC (`172.18.x`). **A TFTP reply comes from a different source port than the request went to**, and WinNAT has no conntrack helper for that, so a transfer through the NAT can hang with the board innocent. The USB GbE adapter is in usbipd's persisted list; attach it, or run `loader-tftp.py` from Windows' own Python (3.10.7, pyserial 3.5, both present) |
| **P4** | *(R0 only)* `sha256sum $FWRE_WORK/rebuild/r0-vendor-kernel.bin` | `396561a0565f8cf62ffd7df6b4105ae3943337ada0fdedc109eb586445a03e90` | the payload, cut from the dump at the desk. **987,138 bytes** = `0x0F1002`, the length in the image's own header |

### How seating 2 was actually driven, and the two rules that came out of it

**Every cell went through `tools/console-capture.py`, not `console-dump.py` and not
picocom.** One byte-exact, timestamped file per cell, no hand transcription, and
it is the instrument `D1`/`D4` already depend on. It carries no forbidden-command
list — that list belongs to `console-dump.py`, which is pinned read-only
upstream — so it sends `EW`, `EB` and `J` the same way `D1` always did.

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400     --out bench/<date>/<cell> --send '<one command>' --seconds 5
```

Two rules came out of doing it that way, and both were paid for once:

| | rule | why |
|---|---|---|
| **1** | **The first cell of any seating is `A0`**, a re-read of `B1` through the same instrument | Driving cell-by-cell re-opens the serial port per cell, which toggles DTR/RTS. Nothing had confirmed those are unconnected on this 4-pin header. `A0` answers that, confirms the prompt is live, and re-establishes the load base, in one command with a precomputed answer |
| **2** | **After any capture cut short by `--seconds`, send one bare `` before the next command** | `§A`'s capture was cut mid-ESC-stream and left **12 unconsumed ESC bytes in the loader's line buffer**. The next command appended to them and came back `Unknown command !`. **The line buffer is per-`readline`, not per-connection** — closing the port does not clear it |

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400     --out bench/<date>/flush --send '' --seconds 2 --force
```

> 🔴 **And the line buffer is 128 bytes, which changes `C7` and bounds every
> command this sheet will ever send.** Measured and read, two sources — see
> `C7`'s rewritten row and `docs/loader-command-semantics.md` §f. **No command
> line in this file may be exactly 128 characters**, because that is the one
> length at which `readline` returns without a terminator and the caller's
> `memset` has no zero left to supply one.

---

### D4 — the cell that actually measures the watchdog

`D1b` says why `D1`'s interval is not the watchdog timeout. **This is the cell
that is**, and it works by changing the experiment rather than the instrument.

| | command | expected | what it refutes |
|---|---|---|---|
| **D4** 🆕 | **last thing before an intended reset**: `EW B800311C 240000`, then type nothing | the board resets on its own. Capture it as `D1` was captured, and take the interval to the banner | 🔴 **`OVSEL` = `1001` instead of `0000` — the longest of the ten timeouts instead of the shortest.** Raw base clock → 2²⁴ / 199.48 MHz = **84.1 ms**; through `CDBR`'s divisor of 14 → **1.177 s**. Those are 14× apart and **both are far above the timestamp floor**, where `D1`'s 164 µs and 2.30 ms were both far below it. **`D1` is this cell's control**: `D1`'s interval is boot time plus a timeout of ≈ 0, so `D4 − D1` is the timeout alone and the boot cancels. `1.17 s` → the watchdog counts the divided clock; `84 ms` → it counts the raw one; **any other power of two → the `OVSEL` field is packed differently than `D` Table 27 was read**, which the measurement identifies rather than hides. Fills `SPEC.md` `CLK-08`, whose own row names a stopwatch — and a stopwatch cannot tell 164 µs from 2.30 ms |

**Why `240000`.** `OVSEL[3:0] = 1001`, split across two fields: `OVSEL[1:0]` at
bits 22:21 gives `1 << 21`, `OVSEL[3:2]` at bits 18:17 gives `1 << 18`. `WDTE` =
`0x00`, which is ≠ `0xA5` and therefore **enables** the watchdog; bit 20 is
written `0`, a no-op on a write-1-to-clear bit. The marginal risk over `D1` is
nil: both end in a watchdog reset, which is the point of both.

---

## Session B3 — R0: the vendor kernel booted from RAM, zero flash bytes

**This is the active gate.** Everything below is read out of this unit's own
loader or measured on it, and the mechanism has been done once on this physical
device — upstream's `P9-12`, 2026-08-21: `J 80500000` into a 156-byte image the
device had never seen, zero flash bytes, `AutoBurning=0` echoed in the same boot.
**What is new here is the payload: 987,138 bytes instead of 156, and a real entry
point instead of a marker loop.**

| | |
|---|---|
| **Power cycles** | 0 of its own; it runs after `§D`'s last reset |
| **Flash bytes written** | **0**, and `G2` is what makes that a measurement |
| **RAM written** | 987,138 bytes twice: at `0x81000000`, then at `0x80500000` |
| **New code needed** | none. `upstream/tools/loader-tftp.py` — `plan/UPSTREAM-INVENTORY.md` says 引用, not rewrite |
| **Closes** | **R0**, and it proves the transport `R1`'s bare-metal payload will use |

### The image, cut at the desk

The header at flash `0x060000` is `cr6c | 80500000 | 00060000 | 000F1002` —
**signature, `startAddr`, flash offset, length**, in that order. *(Corrected
2026-08-24: it had been assumed to be signature/length/startAddr/checksum, and
the two numbers R0 needs came out of the wrong words. `B3`'s measured word 4 of
`80500000` is what the corrected reading agrees with.)*

So: payload = dump `[0x060010, 0x060010 + 0x0F1002)`, **987,138 bytes**, sha256
`396561a0…45a03e90`, landing at `0x80500000`–`0x805F1002`.

### G — the sequence

| | command | expected | what it refutes |
|---|---|---|---|
| **G1** | `DW 805F0FF0 1` and `DW 80580000 1`, **before anything is uploaded** | tail = `00000000 00000000 00000000 00000000`; middle = `9D7111B4 08ABB9AE 978855A8 E63174AD` | 🔴 **is the whole image already in RAM?** `B4` measured the first 16 bytes there, and `C-16` records that nothing yet explains how. If the tail and the middle also match the dump, **the loader has already staged all 964 KiB and `J 80500000` boots the vendor kernel from RAM with no network at all** — that is `G6`, and it becomes the reference the network path is compared against. If they do not match, only the header region was copied and `G6` is skipped |
| **G2** | `AUTOBURN 0` via `console-dump.py rescue`, then `DW 8040D4A0 1` | `AutoBurning=0` echoed; word 1 = `00000000` | 🔴 **the operative guard, and it is `C6` repeated because `§D` reset it.** Read at exactly one instruction, `0x80401B9C`, on the upload-completion path. **If word 1 is not `00000000`, stop. Nothing is uploaded.** With autoburn on, a transfer that completes is written to flash and R0's whole claim is gone |
| **G3** | `IPCONFIG 10.1.1.1`, workstation at `10.1.1.2/24` | `Now your Target IP is 10.1.1.1` | `IPCONFIG` gives the **loader** its own address — it synthesises its MAC from that address, so it is the board's and not the peer's. The loader answers the network only after this |
| **G4** | `LOADADDR 81000000`, then `loader-tftp.py put --host 10.1.1.1 --file r0-vendor-kernel.bin`, then `get` it back and `cmp` | `Set TFTP Load Addr 0x81000000`; the round trip is **byte-identical** to the file | 🔴 **the transport, proved without executing anything.** `0x81000000` and not `0x80500000` **on purpose**: `G1` may have shown the real bytes already sitting at `0x80500000`, and then "the upload arrived" and "it was already there" are the same reading. The scratch region holds only what `C1`–`C7` put there. **Blind spot, and it is why `G5` exists**: `put` and `get` both serve `[0x8040D3A8]`, so a round trip cannot catch a load address that is consistently wrong. Never a filename containing `nfjrom` or `boot.img` — those two force `0x80000000` and auto-execute with nobody at the console; `loader-tftp.py` refuses them |
| **G5** | `EW 80500000 5A5A5A5A` · `EW 80580000 5A5A5A5A` · `EW 805F0FF0 5A5A5A5A`, then `LOADADDR 80500000`, then `put` again, then `DW` all three | after poisoning, `5A5A5A5A` at each; after the upload, `00000000` / `9D7111B4` / `00000000` — the dump's own bytes back | **that the upload landed where it was told**, which `G4` structurally cannot test. Three points spread across 964 KiB. Poisoning first is what makes a match mean anything: `G1` may have left the correct bytes there, and an unpoisoned re-read would pass whether or not anything arrived |
| **G6** | *(only if `G1` matched)* `console-capture.py capture --send 'J 80500000' --seconds 60` | `---Jump to address=80500000`, then the vendor kernel's boot output | **the reference boot, from bytes the loader staged.** Run this *before* `G2`–`G5`, because it costs a power cycle to get back to the prompt and it is what makes every later comparison a comparison |
| **G7** | `J 80500000` after `G5`, captured the same way | the same output as `G6`, **line for line to the first shell prompt** | 🔴 **R0 closes here.** The payload came over the wire this time. **`G6` is the positive control and that is the whole design**: the question is not "did a kernel boot" but "did the network path deliver the same bytes", and a difference is a transport fault caught against a reference produced twenty minutes earlier on the same board. Without `G6`, a successful boot proves only that *some* image booted |
| **G8** | after `G7`: `DW 8040D4A0 1`, and re-read flash `0x000000` and `0x060000` through `FLR` + `DW` | `00000000`; the loader head and the `cr6c` header unchanged | **that nothing was written.** `G7` matching `G6` says the RAM path worked; it says nothing about flash. Three arguments, as `P9-12` used: the echo, the one-instruction read of `0x8040D4A0`, and the bytes themselves |

### What `B3` cannot tell you, stated before it runs

Upstream's `P9-12` wrote a three-outcome table for a `J` — banner repeats, only
the jump line, nothing at all — **and what happened was the fourth**: the banner
appeared and was cut at the same character every iteration, because a payload a
simulator had approved sat an `andi` in a load delay slot. So:

- **partial output is a fourth outcome, not a failure of `G7`.** The image here is
  the vendor's, so a delay-slot bug inside it is not on the table — but any
  output that stops mid-line is recorded as its own row rather than squeezed into
  one of three.
- **silence after `---Jump to address=` cannot separate "jumped and the target was
  silent" from "never jumped."** The vendor kernel has a great deal to say, so
  silence would be informative; it is still two causes and not one.
- **`G7` says nothing about flash.** `G2` and `G8` are what do.
