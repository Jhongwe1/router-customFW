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
| **RAM written** | 8 words at `0x81000000`, in C2 only — 🔄 **called "scratch" here and measured live 2026-08-24**, see `C7` |
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
**words**, and it prints **four per line** — `i` steps 0, 4, 8 … while `i < len`
and each pass prints a whole line. So **`DW <addr> N` prints `4 × ceil(N/4)`
words, never `N`**: `1`, `2`, `3` and `4` all print four; `10` prints twelve
(`B9`); `28` prints twenty-eight. See `docs/loader-command-semantics.md` §f,
which owns it.

> 🔴 **The rounding is *up*, so a length that is too small does not announce
> itself.** The reply is always a whole number of lines, so a readback that asks
> for fewer words than were written comes back looking complete. **Every length
> in this file is the number of words the cell needs, checked against
> `4 × ceil(N/4)` before it is typed.** `C7`'s readback was written `3` for
> twelve written words — four of twelve, and `C7` is the cell that hunts
> truncation. See its row.

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

> 🔴 **That argument is refuted and the paragraph above is kept only as the
> record.** It excludes two known things and excludes nothing the loader
> allocates at run time. `C7-pre` measured a **live 32-byte descriptor table**
> across `0x81000400`, and `C7-pre2` a second live structure at `0x81800000`
> pointing to 28.04 MiB. `C1`–`C4` wrote onto a live structure and nothing broke;
> **that was luck, not design.** Nothing here is scratch until it has been read.
> The address `§G` and `§D`'s canary use instead is `0x80A00000`, and it was
> chosen by a probe rather than by an argument — `G0`.

| | command | expected | what it refutes |
|---|---|---|---|
| **C1** | `EW 81000000 DEADBEEF CAFEBABE` | **no output whatsoever** | `EW` is silent. Any echo and §f is wrong |
| **C2** | `DW 81000000 1` | `DEADBEEF CAFEBABE ???????? ????????` | `EW` writes 32-bit words at the address given, in order |
| **C3** | `EW 81000102 11111111` then `DW 81000100 1` | `???????? 11111111 ???????? ????????` — the value at `0x81000104`, **not** `0x81000100` | 🔴 **`EW` rounds an unaligned address *up*, silently.** If `11111111` lands at `0x81000100`, it rounds down; if the command is refused, it validates. Either would change every `EW` written from now on |
| **C4** | `EB 81000200 41 42 43` then `DB 81000200 4` | `41 42 43` at `…200`, `…201`, `…202` | `EB` writes bytes at the address **verbatim** — no rounding, unlike `EW` |
| **C5** 🆕 | `DW B8003000 1` → `EW B8003000 8000` → `DW B8003000 1` → `PHYR 0 2` → `DW B8003000 1` | in order: `00008100` · *(silent)* · **`00008000`** · `UID=0x0000001c` · **`00008100`** | 🔴 **`E5` recovered as a write, because `E5` as a read was void on arrival** — `GIMR` bit 8 was already `1`, so the bit predicted to flip had nothing to flip from. Clearing it first makes the prediction testable: **`phy_read()` sets `GIMR` bit 8 at `0x80402FB8` and this is the only thing that would put it back.** Reading `00008000` in the middle is a second finding on its own — it proves the console survives with `TCIE` masked. The value `8000` preserves bit 15 (`SWIE`), which is also set. **Licensed by a call-graph walk**: no path from the command loop at `0x80409144` to `tick()`, `delay()` or the ESC-wait, with the same walker finding `PHYR → phy_read → delay → tick` as its control. **If the third command returns nothing, the walk was wrong and the board is hung — that is the risk, and it is one power cycle** |
| **C6** 🆕 | `AUTOBURN 0` — **through `console-dump.py rescue`, not by hand** — then `DW 8040D4A0 1` | the loader echoes `AutoBurning=0`; then word 1 = **`00000000`**, against `B6`'s measured `00000001` | 🔴 **the one command standing between R0 and a flash write, and it has never been shown to work.** `AUTOBURN` is read at exactly one instruction in the whole image, `0x80401B9C`, on the upload-completion path, and `B6` measured the global at `0x8040D4A0` as `1` on this device. **Two independent sources are needed and only one exists today**: the loader's own echo is the loader telling you what it thinks; `DW 8040D4A0` reads the word the burn path actually consults. **And the syntax is not obvious** — the help prints `AUTOBURN: 0/1`, which is not the syntax, and the string table holds `AUTOBURN` and `AUTOBURN: 0/1` as two separate strings; `console-dump.py rescue` tries four forms, **every one of them carrying `0`**, and stops if the reply says `AutoBurning=1`. A wrong form returns `Unknown command !`, **which in a flow with no readback looks exactly like success.** Refuted by: the word reading `00000001` after the echo said `0` — then the echo is not the switch and nothing may be uploaded |
| **C7** 🔄 | **rewritten 2026-08-24, before it ran, because `§A` measured the thing it was going to discover.** **C7a**: `EW 81000400` + **twelve** distinct values (119 characters), then `DW 81000400 16`. **C7b**: `EW 81000440` + eleven values padded to **127** characters, then `DW 81000440 16` | C7a: all twelve land, in order, at `0x81000400`…`0x8100042C`. C7b: all eleven land -- it is C7a's boundary control. **`16` and not `12`**: `4 × ceil(16/4)` = sixteen words, which is the twelve written plus a **four-word over-run control line** that must come back unchanged | 🔴 **the original cell sent eighteen values in a 173-character line, and that line is dangerous on this loader.** Measured `§A` 2026-08-24: the console line buffer is **128 bytes** -- exactly 128 ESC bytes produced `Unknown command !`, seven times -- and read out of the code at `0x80409190`/`0x804091A0` the command loop does `memset(buf, 0, 128)` then `readline(buf, 128, 1)`. Two sources. **`readline` writes its NUL only on the `
` path** (`0x804070FC`); the `
` path and the length-limit path (`0x80407194`, `count < 128`) both return without one, and the caller's `memset` only saves a line **shorter** than 128 because that leaves at least one zero inside the buffer. **A line of exactly 128 characters is therefore unterminated, and the tokeniser at `0x80407248` scans past `sp+143` into eight bytes of stack slack and then into the saved registers.** `EW 81000400 ` + twelve values + the thirteenth's eight hex digits is exactly 128, so the original C7 would have been cut precisely there -- **with `EW` as the command**. So: **never 128.** Twelve values is the largest n with `11 + 9n < 128`. **And the cell's own question is already answered**: one line carries **twelve words, 48 bytes**, so a 1 KiB bare-metal probe needs **22 lines, not 15** -- R1's no-network path is 47% more expensive than the sheet assumed, and that number is now measured rather than derived from a buffer length nobody had checked. 🔴 **And the readback lengths in this rewrite were themselves wrong, caught at the desk before the cell ran.** The row said `DW 81000400 3` for twelve written words. `DW` prints `4 × ceil(N/4)`, so `3` prints **four** words: values 1–4, then `<RealTek>`. **That is byte-for-byte what a truncation at the fourth value looks like — a false positive of precisely the failure this cell exists to detect**, and the cell would have "found" it with the write having been perfect. Corrected to `16` before it was typed. The general rule and its consequence are in `§B`'s preamble |
| | *(the original cell, kept because a superseded plan is a record)* | | `EW 81000400 <v1> … <v18>`, eighteen values, expecting all eighteen to land. Its stated failure mode to watch for was *"truncation, or the prompt never coming back"* -- **which was the right thing to fear, and `§A` measured it for free two cells earlier** |

### D — the reset. Last, because it ends the session's state

> 🔄 **Re-planned 2026-08-24, part two, and this is a re-plan and not an edit.**
> Three of this section's five cells rested on things the bench then measured, and
> in each case the measurement came from a cell outside `§D`:
>
> | what changed | measured by | consequence here |
> |---|---|---|
> | the button is a GPIO on `PABCD` bit 5, not `RESET#` | `B7a` / `B7b` / `B7c` | **`D3` is retired.** It cannot produce a cold boot, so it cannot produce `D2b`'s refutation either |
> | `0x81000000` is inside a live 32-byte descriptor table, not scratch | `C7-pre` | **`D2b` has three outcomes, not two.** The middle one is that table's initialiser re-running, which `D2b`'s two-row version would have recorded as "the reset cleared DRAM" |
> | ESC streams at 50.2 bytes/s and the line buffer partitions at 128 | `§A`, `B7c` | **`D2` was unreachable as written.** `--esc-after` leaves a residue that eats the front of the next command line |
>
> The rows below carry the old plan beside the new one. Nothing is deleted.

**Arming, and it is no longer done once at `§C` time.** `D2b` and `D2c` read back
what `EW` wrote before the reset, and seating 2's running order puts **`§F`
between `§C` and `§D`**. `F1` can cost a power cycle — its own row says so, and
that is the argument for placing it there — and a power cycle takes DRAM with it.
**So the arming writes are the first two cells of `§D`, after `§F` has returned.**

| | command | expected | what it refutes |
|---|---|---|---|
| **D0a** 🆕 | `EW 81000000 DEADBEEF CAFEBABE` — `C1`'s pattern, re-armed | silent, as `C1` | nothing on its own; it is `D2b`'s payload. **If `§F` cost a power cycle, this is the write that makes `D2b` a measurement instead of a reading of whatever survived** |
| **D0b** 🆕 | `EW 80A00000 5EA72D2B A5A5A5A5` — the canary | silent | 🔴 **the cell that makes `D2b`'s middle outcome decidable.** `0x81000000` is **inside** the table `C7-pre` measured, so a warm reset that re-runs that table's initialiser puts `00000400 00000001 FFFFFFFF 00000000` back at `D2b`'s address — neither `C1`'s pattern nor garbage. `0x80A00000` is outside it (`G4-addr-probe`: no pointer-shaped word, no self-reference, no period). **The value is deliberately not part one's `DEADBEEF CAFEBABE`**, so reading it back proves *this* write arrived rather than that *some* write once did. ⚠️ **`§G`'s address probe must have run before this cell** — it reads the head of `0x80A00000` and this cell writes it |
| **D1** 🔄 | **through the tool, not by hand**: `console-capture.py capture --port /dev/ttyUSB0 --out <dir>/D1 --send 'J BFC00000' --esc-after 20 --seconds 45` | the capture holds `---Jump to address=BFC00000`, a silence, then the stage-1 banner. Then `console-capture.py report <dir>/D1 --from 'Jump to address=BFC00000' --to 'RealTek\(RTL8196E\)'` | it writes `WDTCNR = 0` and spins; only the watchdog can leave that loop. **The acceptance condition is not "it reset" — it is "the ESC window appears again afterwards"** (`C-8`). Catch the prompt again. `--esc-after` and not `--esc`, because the ESC has to be streamed *after* the command that causes the reboot — see this cell's Results row |
| **flush-d1** 🆕 🔄 | `console-capture.py capture --port /dev/ttyUSB0 --out <dir>/flush-d1 --send '' --seconds 2` | 🔄 **the expectation is inverted as of `console-capture.py` 1.2, and that is the point of keeping the cell**: a **bare prompt, 11 bytes, no `Unknown command !`** — the shape of `bench/2026-08-24b/flush-cont.log`. `Unknown command !` + `<RealTek>` (≈31 bytes, `flush.log`'s shape) is now the **failing** reading: it means residue was still in the buffer, i.e. `D1`'s capture did not write its terminator | 🔄 **This is no longer a chore, it is the on-silicon positive control for 1.2.** Its two possible readings are exactly the two tool versions: 11 bytes ⇒ the terminator went out inside `D1`'s own capture, 31 bytes ⇒ it did not. **Deleting the cell would have thrown away the only measurement that can tell them apart** — the tool's own suite proves what the tool *writes*, and nothing but this proves what the loader *did with it*. Check `D1`'s `.meta.json` `cr.esc_after` in the same breath: `written: true` with `prompt_seen: true` is the tool's half of the same claim. *Original reason for the cell, which still holds if the reading is 31 bytes:* 🔴 **without it `D2` does not run, and `D2` is the cell worth the seating.** `D1` ends with `--esc-after`, so the last bytes written to the port are ESC and not a CR: whatever ESC the command loop received past its last completed 128-byte fill is still in `readline`'s buffer, and the next command appends to it. **量, `§A`**: ESC leaves the host at **50.2 bytes/s** (730 bytes over 14.55 s; the wire would take 0.19 s, so the ceiling is the tool's `write` + `drain(0.02)` loop), so `--esc-after 20` streams ≈**1000** bytes. The residue is `N mod 128` and **`N` is not knowable in advance**, because when inside the ESC stream the warm prompt appears is not repeatable to the byte: the pre-flight audit's figure for `D1` is ≈**117**, and `B7c` — the same `--esc-after 20`, measured — left `985 = 7 × 128 + **89**`. At 117, `117 + len('DW B8003110 1') = 130 ≥ 128`, and `D2`'s line is cut at the buffer boundary, unterminated. **So the flush is unconditional and not conditional on the arithmetic**; the arithmetic is why it cannot be skipped, not a test to apply on the day |
| **D1b** 🆕 | *(no command — read the number `D1`'s report prints)* | **a wall-clock interval, order of a second. Value not predicted** | 🔴 **What this number is NOT.** It is **not** the watchdog timeout. `WDTCNR = 0` selects `OVSEL[3:0] = 0000` = 2^15 base-clock ticks, and against the measured base clock that is **164 µs** undivided or **2.30 ms** through `CDBR`'s divisor of 14 *(computed here from `E2`'s 199.48 MHz; seating 2 part two superseded that with **200.0049 MHz ±7 ppm** — 163.8 µs and 2.29 ms, which changes nothing this cell turns on)* — and even the longest of the ten settings (2^24) is 84 ms / 1.18 s. **Every one of those is below what any instrument in this session can resolve**, and the CP2102's latency timer (1–16 ms typical, unmeasured here) is a further floor. So the interval is the post-reset boot, and **that is the number `C-8`'s owner actually needs**: R4's `bench-ci` sets its timeout from it. Recording it as "the watchdog timeout" would be a measured quantity wearing another one's name. **Refuted by**: an interval over ~10 s (nothing in the model predicts that), or the banner never arriving (then `D1` failed, not this cell) |
| **D2** 🔄 | `DW B8003110 1` | **word 4 = `A5100000`** — the whole word, not just the bit | 🔴 **this is the cell worth the seating, and it got stronger.** Measured at the desk 2026-08-24: **the loader never writes `WDTCNR` except at two sites, `0x804012F8` (the `reboot.......` path) and `0x804092E8` (this command), and both are `sw zero` followed immediately by `j` to themselves with a `nop` in the delay slot** — so nothing executes after either. Search coverage: the `0x311c` immediate (2 hits, both these), `TC_BASE 0x3100` + displacement 28 (the one `ori …,0x3100` at `0x80408F38` builds a constant, not a store), and every non-`sp` `sw …,28(reg)` (3, resolving to `0xBB804D00`, the SPI descriptor at `0x8040FBD4`, and `0xB8B20000`). **Positive control: the same method finds the `CDBR = 0x000E0000` write at `0x80408F34`, which `B7` measured on the device.** Two consequences. ① `B7`'s `A5000000` is the **hardware reset default**, not something the loader wrote — `B7`'s verdict implied otherwise and is corrected. ② **There is no software in `D2`'s path at all**, so it reads the hardware directly. `A5000000` here means `WatchDogIND` does not survive the reset it reports, **`C-8` loses its discriminator**, and R4's `bench-ci` falls back to `D2b`. ③ 🔄 **It is reachable only because `flush-d1` sits in front of it.** The residue arithmetic in that row is about this command line and the thirteen characters it costs |
| **D2b** 🔄 | `DW 81000000 1` | **one of three readings, not two** — see the table under this one. `DEADBEEF CAFEBABE` is the outcome the cell was written for | 🆕 **a second discriminator for `C-8` that does not depend on `WatchDogIND`.** SDRAM contents survive a warm reset and not a power cycle, so a scratch word that is still there says "warm" without reading any status bit. 🔴 **Rewritten 2026-08-24 part two, because the address is not scratch.** `C7-pre` measured a live 32-byte descriptor table at `0x81000400` with a complete period, and `0x81000000` is inside the same region — `C2` and `C3b` read `00000400` there in part one and it was recorded as "untouched SDRAM". **So a warm reset that re-runs that table's initialiser writes `00000400 00000001 FFFFFFFF 00000000` over `D0a`'s payload**, which is neither the pattern nor garbage, and the two-row version of this cell would have recorded it as *"the reset cleared DRAM"* — the wrong answer, arrived at confidently. **`D2c` is what separates that outcome from a real DRAM loss** |
| **D2c** 🆕 | `DW 80A00000 1` | **`5EA72D2B A5A5A5A5 11744D3C E1553515`** — `D0b`'s two canary words, then words 3 and 4 as `G4-addr-probe` measured them, which nothing has written since. **The tail is a free control**: `D0b` wrote two words, so if words 3–4 have moved, something other than DRAM retention is in play | 🔴 **the middle row of `D2b`'s table.** This address is outside every structure measured on this boot, so nothing but a genuine loss of DRAM contents can clear it. Canary intact + table pattern at `D2b` ⇒ **DRAM was retained and the loader rebuilt the structure**; canary gone ⇒ DRAM was not retained. **Refuted by**: the canary reading `5EA72D2B` after a **power cycle** as well — then it is not DRAM retention that is being observed, and both cells are void. That is the read that has moved to `§G` |
| **D3** ⛔ | *(**retired 2026-08-24, part two. Not run, and it will not be.** Kept because a superseded plan is a record)* press the push button beside the barrel jack, console attached | *(as written)* a full stage-1 cold boot: `Booting...` and the banner | **`C-14` was answered without it, and answered better.** `B7a`/`B7b`/`B7c` read the pin: `PABCD_DAT` bit 5 went `1` → `0` when the button was held and back, with `CNR` and `DIR` unchanged and **no `Booting...`** — a bit that **moved**, where `D3` offered an absence. **The shape was the problem, not the luck**: `D3`'s negative branch was *"anything less — nothing, or a reboot without the stage-1 lines"*, and this file's own `C1` verdict says an expected answer of *nothing* cannot tell a silent mechanism from an input that never arrived. `notes/power-and-programmer.md` §3's *"this unit's loader polls only the UART"* is refuted by the same three cells. **What it takes with it: `D2b`'s refutation condition, which was this cell** — see under the table |
| **flush-d3** 🆕 🔄 | `console-capture.py capture --port /dev/ttyUSB0 --out <dir>/flush-d3 --send '' --seconds 2` | as `flush-d1` — **a bare prompt, 11 bytes**, under 1.2 | 🔄 **The second instance of the same control, and it is worth having both**: `flush-d1` follows `D1`'s `--esc-after 20` and this one follows `D4`'s, so two independent chances for the terminator to fail to go out. One instance is an anecdote. *Original text:* the pre-flight audit named two flush cells for `§D`, `flush-d1` and `flush-d3`, on the grounds that both `D1`'s and `D3`'s captures would end with ESC. **`D3` is retired, so what this one now follows is `D4`** — the same shape, an `--esc-after` capture across a reset the cell caused. The audit's name is kept so the requirement it came from is still traceable; the `--out` is distinct from `flush-d1`'s for the reason under `§`"How seating 2 was actually driven" |

**`D2b` and `D2c` are read as one result, and it has three rows.**

| `D2b` at `0x81000000` | `D2c` at `0x80A00000` | what it is |
|---|---|---|
| `DEADBEEF CAFEBABE …` | `5EA72D2B A5A5A5A5 …` | **DRAM survived the warm reset and nothing rebuilt it.** `C-8` gets its second discriminator: a canary word tells warm from cold with no status bit involved |
| `00000400 00000001 FFFFFFFF 00000000` | `5EA72D2B A5A5A5A5 …` | 🔴 **DRAM survived and the table's initialiser re-ran over it.** Not a DRAM result at all — it is a measurement of *when* that structure is built, which is what `C-16` wants and which `C7-pre` could not date. The discriminator moves to `D2c`'s address. **This is the row the two-outcome version would have called "the reset cleared DRAM"** |
| anything else | not `5EA72D2B` | **DRAM contents did not survive.** Then neither cell discriminates, `C-8` has no second observable, and R4's `bench-ci` needs a third |

**Where `D2b`'s refutation went, and why it is free.** `D2b` needs a cold boot to
prove it is measuring retention and not something that is simply always there,
and `D3` was that cold boot. `§G` takes **two power cycles of its own** — the
first is the one that recovers the loader prompt after `G6`'s `J 80500000`. So:

| | command | expected | what it refutes |
|---|---|---|---|
| **`D2b-cold`** 🆕 | at the loader prompt of the power cycle that recovers from `G6`, **before anything is uploaded**: `DW 81000000 1`, then `DW 80A00000 1` | **both changed.** Neither `DEADBEEF CAFEBABE` nor `5EA72D2B A5A5A5A5` may still be there | 🔴 **the refutation `D3` was supposed to supply, at a power cycle that is being taken anyway.** If either address still holds this seating's value after a power cycle, then what `D2b`/`D2c` measure is not DRAM retention and **both cells are void** — the same way `E5` was void when its "before" state was already its "after". ⚠️ **It has to be read before `G4`**: `G4` uploads onto `0x80A00000` and would supply the canary's disappearance itself |

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
| 🔴 a TFTP filename containing `nfjrom` or `boot.img` | 🔄 **2026-08-25: read at instruction level, and it is worse than this row said.** The name compare against `0x8040A6A8` reaches `0x80401250`, which stores `0x80000000` into **both** the `LOADADDR` global (`0x8040D3A8`) **and** the running TFTP write pointer (`0x8040DD10`); `0x80401A10`'s memcpy then walks up from there. So the transfer **overwrites the UTLB refill vector at `0x80000000` and the general exception vector at `0x80000080` while it is in progress**, destroying the loader's own exception handling mid-flight — and then executes the image the moment the transfer ends, with nobody at the prompt. `docs/loader-command-semantics.md` §10 |
| `EW` or `EB` anywhere below `0x80500000` | the loader's own image and `.data` live at `0x80400000`–`0x8040DD10` |

---

## Results

*Empty until the session. Fill the reading beside each row, and write the
verdict even where it is the boring one.*

**Run 2026-08-23 from 21:51** — `§A`, `§B`. **2026-08-24 part one** — `A0`,
`C1`–`C4`, `C6`. **2026-08-24 part two** — `A0`, `C7`, `B7a`–`B7c`. 🔄 **`§C` is
complete; `§D` has not started.** Logs: `$FWRE_WORK/rebuild/bench-2026-08-23/`,
then `bench/2026-08-24/` and `bench/2026-08-24b/`.

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
| **C7** | 🔄 **2026-08-24 part two, six captures in `bench/2026-08-24b/`.** `C7-pre` (`DW 81000400 28`, **354 bytes**, seven lines): a complete 32-byte period -- `00000400 00000001 FFFFFFFF 00000000` / `00000000 00000000 81000418 81000418`, repeating. `C7a` (119 characters, **130**-byte log): echo only, no `Unknown command !`. `C7a-rb` (`DW 81000400 16`, **213** bytes): `C7A00001`…`C7A0000C` in order at `0x81000400`--`0x8100042C`, and the over-run control line at `0x81000430` byte-identical to its pre-state. `C7b` (127 characters, **138**-byte log): echo only. `C7b-rb`: eleven values landed, word 12 at `0x8100046C` still `00000000` | 🔴 **CLOSES, and every headline in it is a bit or a byte that was predicted first.** ① **The cliff is at 128 and 127 is safe** -- both lines came back complete, which is the boundary `_check_send`'s `>=` now enforces. ② **`EW` writes exactly `argc − 1` words, not "at least"**: both over-run controls are unchanged. ③ **One command line carries twelve 32-bit words = 48 bytes**, so R1's no-network 1 KiB probe is `ceil(1024/48)` = **22 lines, not 15**. ④ 🆕 **The loader's hex parse is `strtoul`-like, not fixed-width**: `C7b` padded with leading zeros and `00C7B00001` -- ten characters -- read back as `C7B00001`. **No source in this repository predicted that**, and padding was chosen as the method precisely because a wrong answer lands a wrong *value* at a known address rather than a wrong *address* somewhere unknown. ⑤ 🔴 **The cell's own out-of-sample test passed**: `C7-pre` stopped at `0x8100046F`, the 32-byte period predicts `0x81000470` = `00000000 00000000 81000478 81000478`, and `C7b-rb` -- reading an address never read before -- returned exactly that. ⑥ 🔴 **And `§C`'s premise is refuted.** `0x81000400` is not scratch: `next = prev = &next` at `0x81000418` is `INIT_LIST_HEAD`'s shape, and uninitialised DRAM cannot produce its own address. **Part one wrote onto a live structure and nothing broke; that was luck.** `§G`'s upload address moves off it -- see `G0`/`G4`. The length arithmetic that nearly voided this cell is in its command row |
| **C7-pre2** 🆕 | `DW 81800000 8`, 118 bytes: `81C09988 81810000 00000058 81800058` / `0000000F FFFFFFFF 00002534 00000001` | **added at the bench, and it is what stops `C7-pre` being read as one stray structure.** `+0x08` = `0x58` and `+0x0C` = `0x81800058` = **base + the value at `+0x08`** -- a length and a pointer to base+length, self-referential the same way and with different content. `0x81C09988` points to **28.04 MiB**. So `0x81000000`--`0x81C09988` holds at least two live, mutually pointing structures. **This is not a fill pattern**, and it is the reason `§G`'s new address had to be probed rather than argued |
| **A0** 🆕 | 🔄 **2026-08-24: first attempt `Unknown command !`; second attempt `8040DBC0: 8040B070 00000000 80409A9C 8040B074`** | 🆕 **a cell that did not exist when this sheet was written, and it earned its place twice.** It exists because seating 2 drove every cell through `console-capture.py`, which **re-opens the serial port per cell**; re-opening toggles DTR/RTS and nothing had confirmed those are unconnected on this 4-pin header (`BRD-09`). ① **They are: the board did not reset** -- the reply was `<RealTek>`, not `Booting...`. Inference to measurement. ② `B1` reproduced exactly on a second power cycle. ③ **The first attempt failing is the informative half**: `§A`'s capture was cut mid-ESC-stream leaving **12 unconsumed ESC bytes in the loader's line buffer**, and this command appended to them. The line buffer is per-`readline`, not per-connection, and it survives a capture boundary. **Standing rule, since restated**: the trigger is not `--seconds` at all but *any capture whose last byte written to the port was not a CR* -- see rule 2 under "How seating 2 was actually driven". `§A`'s capture qualifies either way, because it ran `--esc 25`. · 🔄 **2026-08-24 part two: `A0` ran a third time, on a third power cycle, and returned the same 71 bytes** (`bench/2026-08-24b/A0.log`, byte-identical to part one's `A0b-reopen-control.log`). 🆕 **And the 71 is itself a structural constant**: a `DW <addr> 1` reply on this loader is `len(command) + 2` (the echo and its `\n\r`) + `47 × lines` + `9` (`<RealTek>`), which predicted `C7-pre` = 354, `C7a-rb` = 213, `E10b` = 118, `C7a` = 130 and `C7b` = 138, every one before the cell ran and every one exact. **A byte count is now a cheap check that a reply is complete** |
| **C5** | `00008100` -> *(silent)* -> **`00008000`** -> `UID=0x0000001c` -> **`00008100`** | **PASSES, and it is the causal control the whole of `E5` was for.** A bit cleared by hand came back, and `phy_read()`'s `GIMR \|= 1<<8` at `0x80402FB8` is the only thing that puts it there. **Two findings arrived free in the same transcript.** (a) The middle `DW` answered at all, so **the console does not need the timer** -- the call-graph walk that licensed this cell was right, and it is now measured rather than argued. (b) 🔴 **`GISR` moved `88000004` -> `88000104` -> `88000004`.** Bit 8 is `TCIP`, timer interrupt *pending*: with `TCIE` masked the interrupt could not be taken so it latched, and re-enabling it let the ISR run and ack. **The mask, the latch, the delivery and the ack are all visible in five lines**, and none of it was predicted |
| **B7a** 🆕 | 2026-08-24 part two, button **released**: `DW B8003500 1` -> `FFFFFFDF 00000000 FF000000 0000003C` | 🆕 **a cell that did not exist when this sheet was written, and it is the read half of `C-14`.** w1 `PABCD_CNR` = `FFFFFFDF`: 🔴 **bit 5 is the only cleared bit in the entire 32-bit word**, which confirms on silicon the disassembly claim that `0x804083AC` -- called unconditionally from main at `0x80406778` -- clears bit 5 of `0xB8003500` and `0xB8003508`. w3 `PABCD_DIR` = `FF000000`, bit 5 = 0 -> **input**. w4 `PABCD_DAT` = `0000003C`, **bit 5 = 1** -> released, active-low with a pull-up. Expected value written to `bench/2026-08-24b/PREDICTIONS-block1.md` before the capture existed, checked by `tools/check-predictions.py` |
| **B7b** 🆕 | `DW B8000000 1` -> `8196E001 00000002 00100200 0000000F` | **the multiplex control, and the SoC naming itself.** `0xB800000C & 0xF` = **`0xF`, not 13** -- `0x80408DE4` takes the button state from `[0x8040DD4C]+0x44` only when that nibble is 13, so it reads the real GPIO and **`B7a`/`B7c` are reading the pin the loader reads.** Without this cell, `B7a` measures a pin and not necessarily *the* pin. 🆕 🔴 **`0xB8000000` = `0x8196E001`** -- the chip identification register, reading **`8196E`** with what is most likely revision `001` (量 for the word, 推 for the revision split). **And the boot log prints `chipName: UNKNOWN`**: the loader fails to recognise its own ID at a fixed address it could read. Bears on `NET-23`, the vendor kernel's driver calling this part "8196C" |
| **B7c** 🆕 | button **held**, sent inside `--esc-after 20 --seconds 35`: `DW B8003500 1` -> `FFFFFFDF 00000000 FF000000 0000001C`. XOR against `B7a` = `00000020`. **No `Booting...`, no banner.** ESC accounting `985 = 7 × 128 + 89`, seven `Unknown command !`, and `flush-b7c` consumed the residue and returned one more | 🔴 **`C-14` CLOSES: the button is a GPIO on `PABCD` bit 5, active low. It is not `RESET#`.** One bit changed and `CNR` and `DIR` did not, so it is the pin state and not a reconfiguration. **Answered by a bit that moved rather than by an absence**, which is what retires `D3`. **Reconciled with the operator's report** that a ten-second hold factory-resets the unit: that is software timing a GPIO under the vendor kernel, and a hardware `RESET#` cannot carry a hold-duration semantic; at the loader prompt nothing is timing it. Both observations are of the same pin. **This refutes `notes/power-and-programmer.md` §3's "this unit's loader polls only the UART"** -- the loader's own init configures this pin as a GPIO input and `0x80408DE4` reads it. The `--esc-after` was there so that the branch this cell did **not** expect -- a reset -- would have been recoverable; the ESC accounting is the receipt that it ran as designed |
| D0a | | pending. New 2026-08-24 part two -- `C1`'s pattern re-armed **after `§F`**, not at `§C` time, because `F1` can cost a power cycle and DRAM goes with it |
| D0b | | pending. New 2026-08-24 part two -- the canary at `0x80A00000`. **Order**: `§G`'s address probe (`G0`) reads that address and must run before this write |
| D1 | | 🟢 **runnable again as of 2026-08-24: `--esc-after` exists and `tools/test-console-capture.sh` is 10/10 with `P3`/`N6` guarding it.** The command is `console-capture.py capture --send 'J BFC00000' --esc-after 20 --seconds 45`, and it gets `D1`, `D1b`, `D2` and `D2b` in one capture and one warm reset. *(why it did not run on the day:)* 🔴 **the reason was the instrument.** `D1` sends `J BFC00000`, the board resets, and `D2`/`D2b` must read **the loader prompt of that warm boot**. So one capture has to send a command and *then* stream ESC across the reboot. `console-capture.py`'s `--esc` runs **before** `--send` (the ESC loop sits above `ser.write(line)` in `capture()`), so it cannot. Running `D1` alone would boot the vendor kernel and cost a power cycle to recover -- which destroys the warm-reset condition `D2b` exists to test. **Fixed at the desk with `--esc-after`, not improvised at the bench: this is the third cell lost to an instrument that could not do it (`A2`, `E5`), and the first one caught before it ran** · 🔄 **still pending after seating 2 part two**, which ran out before `§F` and so never started `§D`. Two things changed for it in the meantime: `tools/test-console-capture.sh` is now **24** results over 23 cases, and **the command needs `flush-d1` behind it** -- see that row · 🔄 **2026-08-24, `console-capture.py` 1.2**: the ESC loop writes its own terminating CR, so `D1`'s capture consumes its own residue and `flush-d1` **changes from a chore into this change's positive control on silicon**. `D1`'s command line is unchanged; what changed is what `flush-d1` afterwards is entitled to report |
| D1b | | pending, with `D1` |
| D2 | | pending, with `D1` -- and **only if `flush-d1` runs first**. Its thirteen-character line is what the ESC residue would have eaten |
| D2b | 🔄 **rewritten before it ran, and not run** | pending, with `D1`. **Its payload is armed by `D0a`/`D0b` now, not by `C1`** -- a power-off discards it and `§F` sits in between. 🔴 **And it has three outcomes, not two**: `C7-pre` measured a live table at `0x81000400` and `0x81000000` is in the same region, so the initialiser re-running is a third reading that the old two-row cell would have called "the reset cleared DRAM". `D2c` is the cell that separates them |
| D2c | | pending, with `D2b` |
| D2b-cold | | pending, in `§G`. **`D2b`'s refutation condition moved here** when `D3` was retired: it needs a cold boot, and `§G`'s first power cycle is one that is being taken anyway |
| D3 | | ⛔ **not run, and it will not be.** `C-14` was answered by `B7a`/`B7b`/`B7c` -- a GPIO bit that moved -- **before this cell was spent.** Retired rather than deleted; the row in `§D` says why its shape was wrong independently of the answer |
| D4 | | pending, after `D1`. `flush-d3` follows its capture |

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
to the second**, for `E2`. *(🔄 The clock requirement is retired: two reads of the
timer word taken through `console-capture.py` over a long baseline beat a human
with a stopwatch by two orders of magnitude — `E2`'s Results row. The cable is
still needed.)*

> 🔴 **If the far end is the USB GbE adapter, `carrier` and `operstate` cannot be
> the off-device corroboration.** **量** 2026-08-24: `0bda:8153` binds to
> **`r8153_ecm`**, the CDC-ECM driver, and `/sys/class/net/<if>/carrier` reads
> **`1` permanently** while `operstate` reads **`unknown` permanently** — cable in
> or out. **A tool that always says `1` cannot fail.** `ethtool <if> | grep 'Link
> detected'` tracks the real link and is what corroborated `E11a`/`E11b` off the
> device. `Speed` and `Duplex` from `ethtool` are **not** reliable on this driver
> either: `Speed: Unknown!`, `Duplex: Half`, while the link was up at 100M full.

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

> 🔄 **The heading records seating 1's placement and seating 2 does not use it.**
> `§F` runs in the middle now — after `E11`, before `§D` — for the reason under
> "Running order", and `D3`, the cell it was placed after, is retired. **The move
> is what puts `D0a`/`D0b` where they are**: `F1` can cost a power cycle, so the
> arming writes have to be on the far side of it.

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

**Run 2026-08-23** — `E1`–`E10`, `E12`. **2026-08-24 part two** — `E10b`, `E11`
(five cable moves), `E12b`–`E12e`, `E9b`, and the re-measurement that supersedes
`E2`'s clock. 🔄 **`§E` is complete; section `F` has not run.**

| cell | reading | verdict |
|---|---|---|
| E1 | `0000473A 001E8000 0ED80000 8040A2B4` | **the control was wrong.** Predicted w2 = `00002000` from `li v1,8192` at `0x80409004`; it reads `001E8000` = 2,000,000, so something writes it after that store. The cell's *purpose* is served by E2 far more directly, so the miss costs nothing -- but the control did not work |
| E2 | `00005F52` after **61.842 s** measured -> **6168 counts** | **99.74 Hz against 100.0 Hz predicted, 0.26%.** The gate passes: the timer ISR runs, `delay(10)` returns, PHY commands are licensed. **And it hands `C-8` its clock**: with `CDBR` = 14 and `TC0DATA` = 142,858 both read on the device, base = 99.74 x 14 x 142858 = **199.48 MHz** against the compiled-in `0x0BEBC200` = 200 MHz. A divisor of 15 would give 213.7 MHz, so the measurement also settles the divisor field's semantics · 🔴 **SUPERSEDED 2026-08-24 part two, and the old number stays here with the reason it fell.** Four reads of the same word across a 2,080-second baseline (`E1b`, `E2b`, `CONT2`, `CONT3`, intervals from `.log` mtimes) give **100.0018 Hz** and **200.0049 MHz ±7 ppm**, and every pair that excludes the shortest baseline agrees to five significant figures. **The 0.26 % was the instrument**: this cell was hand-timed over 61.842 s, a human reading a clock is good to about ±0.15 s, and ±0.15 s in 61.8 s **is** ±0.25 %. So the compiled-in 200,000,000 is right to 24 ppm -- inside a normal crystal's tolerance -- and the deviation this row reported as a property of the board was a property of the stopwatch. The gate verdict is untouched: the ISR runs, `delay(10)` returns, PHY commands are licensed |
| E2b NEW | `DW B8003100 1` -> `0022E0A0 00000000 0010B960 00000000` | **added at the bench, and it is what makes E2 a derivation rather than a coincidence.** `TC0DATA` = `0x22E0A0` = 142,858 << 4, exactly the image value, so the count field is bits 31:4 and the count is 142,858. Three of the four terms are now read on silicon |
| E3 | `00008100 88000004 00000000 30050004` | **REFUTED, and it voids E5.** `GIMR` bit 8 (`TCIE`) is **already 1** at the prompt; predicted 0. Bit 15 (`SWIE`) is set too, and `IRR1` reads `30050004` where the loader writes `00050004` -- `SWIRS` = 3 at bit 28. **`doBooting()`'s `GIMR = 0` is not the last write before the prompt**, so `docs/loader-phy-and-switch.md` section 2 layer 4 is wrong. Internally consistent: the tick could not advance otherwise |
| E4 | `PHYID=0x00000000, regID=0x00000002 ,Find PHY Chip! UID=0x0000001c` | **the first MDIO transaction this device has performed.** Both echoed fields correct, so the base-16 parse holds. `0x001C` -- neither `0000` nor `ffff`. Note the loader's `%x` pads to eight digits: the expected *rendering* in the cell was wrong, the values were not |
| E5 | not runnable | **void as designed.** The bit it predicted would flip 0->1 was already 1. Recovering it needs `EW` to clear `GIMR` bit 8 first -- a register write, so it belongs in section C and needs a decision, not a bench improvisation |
| E6 | `UID=0x0000c880` | full identifier **`0x001CC880`** |
| E7 | `PHYR 2 2`, `PHYR 3 2`, `PHYR 4 2` -> `1c`, `1c`, `1c` | **all three equal E4.** One PHY macro, as `PORT1`'s single table implied |
| E8 | `PHYR 1 2` -> `1c`; `PHYR 1 3` -> `c880` | **identical to the other four.** `PORT1` skipping address 1 is about the **port**, not the PHY. One driver covers all five |
| E9 | `00000000 007F0039 047F0039 087F0039` / `0C7F0039 107F0039 00000000 187F0038` | **the load-bearing half is exact**: `ExtPHYID` (30:26) reads 0, 1, 2, 3, 4 across `PCRP0`-`PCRP4`. The weaker half passes too -- `7F` at 22:16 on all five, the datasheet's `FrcAbi` = `11111` and `Pause` = `11`. **But `PITCR` reads `00000000`, predicted `00000001`** -- and `PCRP0` shows `EnForceMode` = 0, so **the whole strap-gated force-mode branch did not run on this board.** `P0phymode=01` is therefore *not* `PITCR` bits 1:0, and the claim that the loader names a value the datasheet calls Reserved is **withdrawn**: `PITCR` = 0 is `UTP (10/100M embedded PHY)`, which is exactly what the boot line says. 🆕 **Words 7 and 8 were read and never judged**: `0xBB804118` = `00000000` and `0xBB80411C` = `187F0038`, the second carrying `30:26` = **6**. On the `PCRP` per-port stride those are ports 5 and 6 — the stride is an inference, and no source held here names either address. Recorded 2026-08-24 while building `SPEC.md`; `NET-10` there points at this cell |
| **E9b** 🆕 | 2026-08-24 part two, `DW BB804100 8` -> `00000000 007F0039 047F0039 087F0039` / `0C7F0039 107F0039 00000000 187F0038` | **byte-identical to `E9`, on a different power cycle and after the cable had been in four different jacks.** So `PCRP` is confirmed **link-independent**, which `E9` asserted from the loader never writing it and could not show. It also gives `F2`'s sweep a **within-boot** comparison basis instead of one carried over from a previous power cycle |
| E10 | `000010E0 000010E0 00001099 000010E0` / `000010E0 000000E2 0000007A 0000007A` | **exactly one port with `LinkUp`: `PSRP2`.** `0x1099` = NWayEnable, LinkUp, full duplex, speed `01` = 100M. The other four read `0x10E0`, bit 4 clear. **Independently corroborated off-device**: Windows reports the far end of that same cable `Up, 100 Mbps` |
| **E10b** 🆕 | **with no cable in any jack**: `DW BB804128 8` -> `000010E0 000010E0 000010E0 000010E0` / `000010E0 000000E2 0000007A 0000007A` | 🔴 **the negative control `E10` was never able to take**, and it is `E10`'s own argument being cashed. `E10`'s stated expectation was *"with no cable in: every word bit 4 = 0"* -- but a cable **was** connected during seating 1 and `PSRP2` read `0x1099`, so the zero was never measured. Here all five read `000010E0`, bit 4 clear, all identical. **A zero that later becomes a one is worth more than a one on its own** -- `E10`'s words, and this is the zero. Words 6--8 are byte-identical to seating 1 |
| E11 | 🔄 **2026-08-24 part two, five cable moves, `E11a`--`E11e`, each `DW BB804128 8`.** Exactly one port with bit 4 set on every read, and a different one each time: jack 1 (WAN) -> `PSRP0`; jack 2 -> `PSRP2`; jack 3 -> `PSRP3`; jack 4 -> `PSRP4`; jack 5 -> **`PSRP1`** | 🔴 **`NET-13` CLOSES, five points, all measured.** The bit follows the cable, so the register is port-indexed as Table 62 says and `E9`'s map means what it says. **The cell's own prediction held**: upstream's boot log has port 0 carrying vid 8 against ports 1--4 on vid 9, so *"the WAN jack should light word 1"* -- it does. 🔴 **And the physical order is `0, 2, 3, 4, 1`, not linear.** A driver that takes the port index from the silkscreen position is wrong on **exactly one jack**, and it is the jack whose port `PORT1` skips. `E12`'s rule (*take `n` from `E9`, not from the port number*) now has a concrete instance -- silkscreen position against port index, rather than `ExtPHYID` against port index. **An intermediate conclusion of mine, "`PSRP1` has no jack", was wrong and is retracted here**: it rested on a jack count reported at the bench rather than measured, and it was killed by `E11e`, whose refutation condition named that outcome in advance. `NET-03`'s five RJ45 stands; **`NET-07`'s explanation is what changes** -- the reason `PORT1` skips address 1 is not "port 1 has no jack", and the remaining candidate is the help string's own words, `port 1 patch for FT2`, a patch applied to the other four so port 1 can be tested alone (*推*; `docs/loader-phy-and-switch.md` §4 owns the refutation path). 🔄 **The mechanism half of this cell is only half right.** Bit 8 *is* the link-down flag and it *is* read-to-clear, but *"read it again and bit 8 is 0"* is not a reliable discriminator: `E11a2` re-read an untouched port and bit 8 was **still set**, which was recorded as *"bit 8 is sticky and `DW` does not clear it"* and is **retracted**. `E11c2` -- built to separate the two models by reading a port whose jack was **empty**, so no new down-event was possible -- took bit 8 from 1 to 0 in a single read, and `E11e` did it a third time. `E11a2` is explained as a **second autoneg latch on a link still settling**, a real event and not an instrument defect. **Bit 4 following the cable is what carried this cell**; bit 8 was the part that needed a designed control. 🆕 **量 Two words with no jack behind them**: the 7th and 8th read `0000007A` on all eight reads today and the 6th reads `000000E2` throughout, unchanged by five physical cable moves -- so they are not driven by any physical jack. *推*: the switch's internal / CPU-side ports. `NET-10` already flags that the stride past port 4 is an inference; this adds an invariance with five independent chances to fail |
| E12 | `PHYR 2 1` -> `78ED`; `PHYR 0 1` -> `78C9`; `PHYR 2 0` -> `1100`; `PHYR 2 5` -> `C1E1` | **a paired control on one instrument, which is what E5 was supposed to give.** Linked port: `LinkStatus` = 1, `AutonegComplete` = 1. Unlinked port, same register: both **0**. Capability bits 15:11 identical on both, so the difference is link state and not a different part. `BMCR` = `1100`, autoneg enabled and full duplex, agreeing with `PCRP2`'s `EnForceMode` = 0. `ANLPAR` = `C1E1`: selector `00001` = 802.3, 10/100 half and full, **Acknowledge set and Next Page set** -- the signature of a gigabit-capable partner, which is what is in fact on the other end |
| **E12b** 🆕 | 2026-08-24 part two, linked port, PHY address 1: `PHYR 1 5` -> `UID=0x0000cde1` | 🆕 🔴 **`PSRP` bits 6 and 5 are the negotiated flow control, and this is a paired comparison across two power cycles and two instruments.** Seating 1's partner was a PC NIC and `ANLPAR` read `0xC1E1` with `PSRP` bits 6,5 **clear**; today's is an RTL8153 USB GbE and `ANLPAR` reads `0xCDE1` with bits 6,5 **set**. **`0xCDE1 XOR 0xC1E1 = 0x0C00`** -- the two `ANLPAR`s differ in bits 11 (`ASM_DIR`) and 10 (`PAUSE`) and in nothing else, and the two `PSRP` readings differ in bits 6 and 5 and in nothing else. In the **down** state bits 6,5 are set on every port, so the default is "enabled" and a partner that does not advertise PAUSE clears them. `NET-11` already names 6 RxPause and 5 TxPause from source B; **this is the first time either has been made to move on demand** |
| **E12c/E12d** 🆕 | `PHYR 1 1` -> `78ED` (linked); `PHYR 0 1` -> `78C9` (unlinked) | **`E12`'s pair reproduced exactly, on different physical ports.** `XOR = 0x24` -- bits 5 (Autoneg Complete) and 2 (Link Status) **and nothing else**. Two power cycles, two port pairs, same two bits: `BMSR`'s link half is not port-specific and not a one-off |
| **E12e** 🆕 | `PHYR 0 5`, an **unlinked** port -> `UID=0x00000001` | 🆕 **`ANLPAR` is per-port, and an unlinked port's is cleared rather than stale.** `0x0001` is the 802.3 selector alone, every ability bit clear. **Different from `E12b`'s value read seconds earlier, which is the control**: one register shared across ports would have voided `E12b` entirely. No source predicted this and seating 1 never read it |
| | 🆕 *(these four are also `F1`'s positive control)* | the MDIO controller completed transactions on addresses 0 and 1 over four registers seconds before `§F` would run, so **a hang at `PHYR 5 2` would be attributable to address 5 alone** and not to the controller, the bus or the command. `F1`'s risk paragraph argues that from the register's role; this is the measured half |
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

`§A` capture → `§C1`–`C7` → **`G0`** → `E11` → **`§F`** → `§D` (`D0a`, `D0b`
first) → **session `B3` (R0)**

🔄 **Two changes from that, made 2026-08-24 part two**: `G0` — `§G`'s address
probe — is a pure read and moves up next to `§C`, because `D0b` **writes** the
address `G0` has to read untouched; and the arming writes `D0a`/`D0b` sit at the
head of `§D` rather than back at `§C`, because `§F` is between them and `F1` can
cost a power cycle.

Two changes from seating 1's order, both deliberate:

| change | why |
|---|---|
| **`§F` moves from last to the middle** | seating 1 put it last on the argument that if it hangs, nothing is left to lose. That was right when nothing was behind it. Now `§D` and `B3` are, and they are worth more — `B3` closes the active gate. `F1`'s hang is also cheaper than the sheet implies (see the note under `F1`), and the power cycle it would cost **re-establishes `D2`'s power-on baseline**, which `§D` needs anyway |
| **`§D` before `B3`** | `§D` resets the board twice — `D1`'s warm reset and `D4`'s watchdog reset. *(As written it was three: `D3` was the middle one, and it is retired.)* `B3` ends with a kernel running and the loader gone. Resets before the thing that is not coming back |

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
| **P2** 🔄 | `bash tools/test-console-capture.sh` | **`25 passed, 0 failed`** *(7 when this row was written; 10 with `--esc-after`'s `P3`/`N6`; 13 with the 128-byte cliff; **25 since `console-capture.py` 1.2**)* | the timing instrument `D1` and `D4` depend on. **14 of the 24 cases are controls that must fail**; three of the original seven **did** fail on first run, which is why they are trusted. 🔴 **This row has now been stale twice** — `6c6c3b5` took the suite 7→10 and left it reading 7, and 1.2 took it 13→24 — so the number is quoted here and nowhere else, and a mismatch is the gate failing, not a rounding error. The 1.2 additions: `P5`/`N9` (an ESC loop ends on a CR / `--no-cr` turns it off), `P6` (the CR lands *between* the ESC and the command), `P7` (no ESC loop ⇒ no extra CR), `N10` (the CR write removed from a copy of the tool ⇒ `P5` must fail), `P8`/`N11` (**the `--esc`-with-no-`--send` shape, which is `A-catch`**, and the mutant that would have skipped it), `P9`/`N12`/`N13` (the settle observed in both directions, and a `PROMPT` that cannot match), `N14` (a `--seconds` that leaves no settle budget records `prompt_seen` **null**, never `false`), `P10` (**Ctrl-C inside an ESC loop still writes the terminator**). 🔴 **`P8`/`N11`, `P9`/`N12`/`N13`, `N14` and `P10` all came out of the adversarial review of 1.2 itself, and every one of them killed a mutant the first eighteen cases had let through** |
| **P3** 🔄 | *(R0 only)* `ip -brief addr` in WSL, then **`sudo ip link set <if> up`** and **`sudo ip addr replace 10.1.1.2/24 dev <if>`** | an interface that is **not** `eth0`, and after bringing it up `ethtool <if>` reads **`Link detected: yes`** | 🔴 **2026-08-24: bringing it up is part of the check, not a later step.** `ethtool`'s `Link detected` reports the **netdev**, not the wire — on an admin-down interface it reads `no` whatever is plugged in, and `/sys/.../carrier` returns `Invalid argument` rather than the documented `1`. The board's `PSRP` register is the independent second source and it disagreed with `ethtool` for six minutes before the cause was found. **Without this the `§G` transfer fails on the host side and reads as a board fault.** `eth0` is WSL2's NAT'd vNIC (`172.18.x`). **A TFTP reply comes from a different source port than the request went to**, and WinNAT has no conntrack helper for that, so a transfer through the NAT can hang with the board innocent. The USB GbE adapter is in usbipd's persisted list; attach it, or run `loader-tftp.py` from Windows' own Python (3.10.7, pyserial 3.5, both present) |
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

Three rules came out of doing it that way, and each was paid for once:

| | rule | why |
|---|---|---|
| **1** | **The first cell of any seating is `A0`**, a re-read of `B1` through the same instrument | Driving cell-by-cell re-opens the serial port per cell, which toggles DTR/RTS. Nothing had confirmed those are unconnected on this 4-pin header. `A0` answers that, confirms the prompt is live, and re-establishes the load base, in one command with a precomputed answer |
| **3** 🆕 | 🔴 **An `--esc` window is `180`, not `45`.** Catching a cold boot means the ESC stream has to be running **before power is applied**, and the operator has to physically reach a barrel jack. **量 2026-08-24**: a 45 s window was missed — `bench/2026-08-24e/A-catch.timing` has the boot beginning at **t=64.2 s**, nineteen seconds after the stream stopped, and `cr.prompt_seen: false` beside a full settle is the signature. The standing form is `--esc 180 --seconds 200` | **the cost is wildly asymmetric.** An extra ESC second is free — the tool streams ~50 B/s into a buffer the loader empties every 128 bytes, and 1.2's terminator tidies it at the end regardless. A missed window costs **a power cycle**, which is the most expensive unit here. 45 s was sized for a laboratory |
| **2** 🔄 | **Restated 2026-08-24, part two.** The trigger is **not** "a capture cut short by `--seconds`". It is **any capture whose last byte written to the port was not a CR** — i.e. any capture that ran `--esc` or `--esc-after` — **and any USB re-enumeration of the console adapter**. After either, send one bare CR (`--send ''`) before the next command | **量, and the evidence runs in both directions.** *The old rule was too wide*: part one's `C1` → `C2` → `C3a` → `C3b` → `C4a` → `C4b` → `C6-readback` were **every one** stopped by `--seconds` (`bench/2026-08-24/*.meta.json`, `"stop_reason": "--seconds N elapsed"`, `"esc_seconds": 0.0`), **none** was flushed, and every one is correct. A `--send` capture ends with the CR the tool itself wrote; an ESC loop ends on a wall-clock deadline and writes no terminator. *And too narrow*: a re-enumeration is not a capture at all, so nothing covered it — see below. *Positive control, both times the corrected rule fires*: `A-catch` (`--esc 25`) left **12** ESC bytes and `A0`'s first attempt came back `Unknown command !`; `B7c` (`--esc-after 20`) left `985 = 7 × 128 + 89`, and `flush-b7c` returned **exactly one** `Unknown command !`, 31 bytes |

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400     --out bench/<date>/flush-<what-it-follows> --send '' --seconds 2
```

**`--out` carries what the flush follows, and `--force` is not in that line.** A
seating needs several of these — 2026-08-24b ran `flush`, `flush-cont` and
`flush-b7c` — and one `--out` reused with `--force` overwrites the evidence for
the earlier one. Let the tool refuse instead.

**What rule 2 said until 2026-08-24, and the cell that killed each half.** It
read *"after any capture cut short by `--seconds`, send one bare CR"*, and it is
kept here because a superseded rule is a record. The half that was too wide fell
to part one's own captures, listed in the row above: seven cells cut by
`--seconds`, none flushed, none wrong. The half that was too narrow fell to the
console adapter leaving the host's USB bus mid-session — **量**, `dmesg`
`cp210x ttyUSB0 ... disconnected`, and Windows `usbipd list` moved the busid out
of *Connected*, so it left the host bus and not merely the usbip attachment.

> 🆕 **The first thing sent after a re-enumeration is a throwaway, and residue is
> not the reason.** **量** `CONT` (`DW 8040DCE8 1`) came back **24 bytes**: the
> echo, `\n\r`, `<RealTek>` — **no data line**, the shape `B8` produced when a
> length argument parsed to zero. The obvious explanation was residue in the line
> buffer, and it is **refuted**: `flush-cont` (`--send ''`) returned a **bare
> prompt, 11 bytes, with no `Unknown command !`**, so the buffer was empty.
> `CONT2`, the identical command sent afterwards, worked. So the flush after a
> re-enumeration is not there to drain anything — **it is there to spend the
> throwaway on a command with nothing at stake.** Its signature is *echo +
> prompt + no output*. *推* for the mechanism (most likely a break or framing
> error into `readline` while the adapter re-enumerates); **量** for the
> behaviour. `bench/2026-08-24b/CONT.log`, `flush-cont.log`, `CONT2.log`.

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
| **Power cycles** | 🔴 🔄 **two of its own** — one to recover the loader prompt after `G6`'s jump, one after `G7`'s. *(This row said "0 of its own" until the 2026-08-24 pre-flight audit. Both jumps end with a kernel running and the loader gone, and there is no other way back; the count was wrong, not the plan.)* It still runs after `§D`'s last reset. **Two directories, `bench/<date>c` and `bench/<date>d`**, under `bench/README.md`'s one-directory-per-power-cycle rule |
| **Flash bytes written** | **0.** `G2` is the *guard*; `G8a`/`G8b` are the *evidence*, and they reach **512 bytes of a 4 MiB part** — see `G8b` for what that entitles the write-up to say |
| **RAM written** | 987,138 bytes twice: 🔄 at **`0x80A00000`** — not `0x81000000`, see `G0` — then at `0x80500000`. Plus `§D`'s two canary words at `0x80A00000`, which the first upload lands on top of |
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

> 🔄 **Corrected 2026-08-24 from the pre-flight audit, and the corrections are
> about the tools, not the plan.** This section was read against
> `upstream/tools/loader-tftp.py` and `console-dump.py` **as they are actually
> pinned**, and the findings were then put through an adversarial refutation
> pass; what survived is in the rows below, and what did not is not here. Every
> one of them would otherwise have surfaced at the bench with the board powered,
> which is the expensive place to find out that a flag is called something else.

| | command | expected | what it refutes |
|---|---|---|---|
| **G0** 🆕 | **runs with `§C`, long before the rest of this section**: `DW 80A00000 1`, `DW 80A78000 1`, `DW 80AF1000 1` — head, middle and tail of `0x80A00000`–`0x80AF1002` | head = `55617135 0077BF55 11744D3C E1553515` (**量** `G4-addr-probe`, 2026-08-24). Middle and tail: **not predicted** — what is predicted is their *shape*: no pointer-shaped word, no word equal to its own address or to a nearby one, no repeating period | 🔴 **the selection of the upload address, and it is a refutation condition and not a justification.** `G4` as written uploaded to `0x81000000`, and `C7-pre` then measured a **live descriptor table** there: if that table is the loader's network buffer pool, `G4` would have been using a TFTP transfer to overwrite the TFTP transfer's own buffers (*推* — and the kind of thing that fails mid-transfer and reads as a board fault). `0x80A00000` is above the staged kernel's end (`0x805F1002`) and below the structures at 16 MiB, and `G4-addr-probe` found no pointer, no self-reference and no period there. **But eight words is one 32-byte window and does not speak for 964 KiB.** **Any pointer-shaped word in any of the three reads and the address is re-chosen** — that is the whole point of the cell. ⚠️ It must run **before `D0b`**, which writes the canary at the head of this region |
| **G1** | `DW 805F0FF0 1` and `DW 80580000 1`, **before anything is uploaded** | tail = `00000000 00000000 00000000 00000000`; middle = `9D7111B4 08ABB9AE 978855A8 E63174AD` | 🔴 **is the whole image already in RAM?** `B4` measured the first 16 bytes there, and `C-16` records that nothing yet explains how. If the tail and the middle also match the dump, **the loader has already staged all 964 KiB and `J 80500000` boots the vendor kernel from RAM with no network at all** — that is `G6`, and it becomes the reference the network path is compared against. If they do not match, only the header region was copied and `G6` is skipped |
| **G2** 🔄 | **one invocation, not three**: `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80A00000 -o <dir>/G2-rescue.json`, then `console-capture.py … --send 'DW 8040D4A0 1'` | in the transcript, in this order: `AutoBurning=0`, `Set TFTP Load Addr 0x80a00000`, `Now your Target IP is 10.1.1.1`; then word 1 = `00000000` | 🔴 **the operative guard, and it is `C6` repeated because `§D` reset it.** Read at exactly one instruction, `0x80401B9C`, on the upload-completion path. **If word 1 is not `00000000`, stop. Nothing is uploaded.** 🔄 **What the audit corrected**: `rescue` sends **AUTOBURN, then LOADADDR, then IPCONFIG, in one run** — autoburn before the network is up on purpose, and the load address settled before the loader starts answering TFTP. So `G3` and `G4`'s LOADADDR step are steps *of this cell*. It records a `load_addr` key **only when `--load-addr` is given**, which is what `G4`'s `--expect-load` checks against — **part one's `bench/2026-08-24/C6-rescue.json` has no such key and cannot be reused**. ⚠️ **`--load-addr` is `int(s, 0)`: write `0x80A00000`, with the `0x`.** ⏱ **And this transcript must be produced *after* `G6`'s power cycle** — `--max-rescue-age` defaults to 3600 s and its own help says why: AUTOBURN is RAM state that a power cycle clears, so a transcript from before the cycle describes a switch that has since flipped back |
| **G3** 🔄 | *(folded into `G2` — kept as the record, not as a step)* `IPCONFIG 10.1.1.1`, workstation at `10.1.1.2/24` | `Now your Target IP is 10.1.1.1` | `IPCONFIG` gives the **loader** its own address — it synthesises its MAC from that address, so it is the board's and not the peer's. The loader answers the network only after this. **It is step 3 of `G2`'s single invocation**; typing it separately would leave `G2`'s transcript describing a run that did not happen |
| **G4** 🔄 | `loader-tftp.py put --host 10.1.1.1 --image $FWRE_WORK/rebuild/r0-vendor-kernel.bin --rescue-report <dir>/G2-rescue.json --expect-load 80A00000 --yes`, then `get -o <dir>/G4-back.bin --force` and `cmp` | the round trip is **byte-identical** to the file (`sha256 396561a0…45a03e90`, 987,138 bytes) | 🔴 **the transport, proved without executing anything.** 🔄 **Not `0x81000000`, and not `0x80500000`.** Not `0x80500000` because `G1` may have shown the real bytes already sitting there, and then "the upload arrived" and "it was already there" are the same reading. Not `0x81000000` because `C7-pre` measured a live structure there — see `G0`, which owns the choice and its refutation condition. 🔄 **What the audit corrected in this line**: the flag is **`--image`**, not `--file`; **`--rescue-report` and `--yes` are both required**; and 🔴 **`--expect-load` is `int(s, 16)` — bare hex, `80A00000`, no `0x`** — the **opposite** convention to `--load-addr` in `G2`, in the same session, twenty minutes apart. **Blind spot, and it is why `G5` exists**: `put` and `get` both serve `[0x8040D3A8]`, so a round trip cannot catch a load address that is consistently wrong. Never a filename containing `nfjrom` or `boot.img` — those two force `0x80000000` and auto-execute with nobody at the console; `loader-tftp.py` refuses them unless `--allow-autoexec` |
| **G5** 🔄 | `EW 80500000 5A5A5A5A` · `EW 80580000 5A5A5A5A` · `EW 805F0FF0 5A5A5A5A`; then **`rescue` again with `--load-addr 0x80500000 -o <dir>/G5-rescue.json`**; then `put … --rescue-report <dir>/G5-rescue.json --expect-load 80500000 --yes`; then `DW` all three | after poisoning, `5A5A5A5A` at each; after the upload, `00000000` / `9D7111B4` / `00000000` — the dump's own bytes back | **that the upload landed where it was told**, which `G4` structurally cannot test. Three points spread across 964 KiB. Poisoning first is what makes a match mean anything: `G1` may have left the correct bytes there, and an unpoisoned re-read would pass whether or not anything arrived. 🔄 **The second `LOADADDR` goes through `rescue` too**, for the same reason as `G2`: `--expect-load` is checked against a transcript, and a `LOADADDR` typed outside one leaves nothing to check against. `LOADADDR` is on `console-dump.py cmd`'s refusal list and `rescue` is where it has a deliberate home |
| **G6** | *(only if `G1` matched)* `console-capture.py capture --send 'J 80500000' --seconds 60` | `---Jump to address=80500000`, then the vendor kernel's boot output | **the reference boot, from bytes the loader staged.** Run this *before* `G2`–`G5`, because it costs a power cycle to get back to the prompt and it is what makes every later comparison a comparison. 🔄 **That power cycle now carries two more jobs**: it is where `D2b-cold` is read, **before** anything is uploaded, and it is what makes `G2`'s rescue transcript fresh enough for `put` to accept it |
| **G7** | `J 80500000` after `G5`, captured the same way | the same output as `G6`, **line for line to the first shell prompt** | 🔴 **R0 closes here.** The payload came over the wire this time. **`G6` is the positive control and that is the whole design**: the question is not "did a kernel boot" but "did the network path deliver the same bytes", and a difference is a transport fault caught against a reference produced twenty minutes earlier on the same board. Without `G6`, a successful boot proves only that *some* image booted. 🔄 **This is the second of `§G`'s two power cycles**: it ends with a kernel running and the loader gone, and `G8b` needs the prompt back |
| **G8a** 🆕 🔄 | **after `G5`, before `G7`.** `DW 8040D4A0 1`; then flash `0x000000` and `0x060000` read through `FLR` + `DW`, into `0x80A00000` and `0x80A00100` | `00000000`; then the loader head and the `cr6c` header as the dump has them | **that the two completed transfers did not reach flash.** 🔄 **Why this is not part of `G8b`, and both halves are the audit's.** ① 🔴 **`DW 8040D4A0 1` has to be read here.** `§`"Running order" already says every reset puts `AUTOBURN` back to `1`, and `G7` ends in a power cycle — so the same read after it returns `00000001` and means nothing. The word that matters is the one the burn path saw **during** the transfers. ② 🔴 **`FLR` writes the TFTP length global `0x8040DD28`** (`docs/loader-command-semantics.md` §f), so **no `put` or `get` may follow it**. `G5` is the last transfer; this is the first moment `FLR` is allowed |
| | 🔴 **and `FLR` costs three captures per read, not one** | `FLR 80A00000 000000 100` · `Y` · `DW 80A00000 64` | `FLR` prompts `(Y)es , (N)o ? --> ` and `console-capture.py`'s `_check_send` **refuses an embedded CR** — one line per `--send`, by design — so the confirmation cannot ride on the `FLR` line. Two regions × three captures = **six**. `64` is `0x100` bytes in words (`4 × ceil(64/4)` = 64 words = 16 lines, and the reply is `14 + 2 + 47×16 + 9` = **777 bytes**, which is the completeness check). The `FLR` destination is `0x80A00000` because `G0` probed it — **never `0x80500000`, which holds the payload `G7` is about to jump into** |
| **G8b** 🆕 🔄 | **after `G7`'s power cycle**: the same two `FLR` + `DW` reads, `cmp`'d against `G8a`'s captures | the two `.log` files **byte-identical** to `G8a`'s | **that the kernel `G7` booted did not write flash.** This is the half `G8` could not do from one position: `G8a` covers the transfers, and `G8b` covers `G7` itself — **and `G7` runs the vendor kernel, which has an MTD driver and every ability to write.** The comparison is `cmp` on two transcripts of the same command, so a single changed byte shows up without anyone reading hex. 🔴 **And the reach, stated where it will be quoted from**: two `0x100`-byte reads are **512 bytes of a 4,194,304-byte part**. The evidence line R0 is entitled to is *"the loader head and the `cr6c` header are unchanged"* — **not** *"zero flash bytes written"*, which needs a full re-dump hashed against `FLS-14` and costs the 105 minutes `FLS-14`'s own row records |

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
- **`G7` says nothing about flash.** `G2`, `G8a` and `G8b` are what do — and what
  they say is bounded: **512 bytes of a 4 MiB part**, at two addresses chosen
  because they are the two that would change. `G8b`'s row carries the wording
  that is entitled to.

---

---

## Session B4 — `R1-gate`: the cache model and the CP0 census, on silicon

**Written 2026-08-25, at the desk, before any of it runs; corrected the same
day, before any of it ran.** Two payloads, and `rlx_reset` means they cost **one**
power cycle between them, not two. Written here rather than typed from memory
because `RUNSHEET.md` rule 4 exists: a command is typed from here or from a tool,
never re-stated by hand — and the first draft of this section broke that rule in
its two most expensive cells, `H1a` and `H2a`, which were cross-references and
carried no command at all.

> **Standing capture forms, because rule 4 means they are not recalled at the
> bench.** From seating 2's rules 1-3 and from `D1`, which is the only cell that
> has run this shape:
>
> | | |
> |---|---|
> | the opening catch | `python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out <dir>/A-catch --esc 180 --seconds 200` |
> | an ordinary read cell | `python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out <dir>/<cell> --send '<command>' --seconds 5` |
> | **a cell whose command resets the board** | the same, plus `--esc-after N --seconds M`. `--esc-after` streams ESC for N seconds **after** the send, which is what `--esc` cannot do and what `D1` needed |
> | after every `--esc` / `--esc-after` capture | `… --out <dir>/flush-<what-it-follows> --send '' --seconds 2` |
>
> 🔴 **Every `J` in this section resets the board, and the reset lands under a
> second after the payload's last line.** `rlx_reset` drains the UART on `TEMT`,
> counts 16,777,216 iterations of a three-instruction loop, then writes
> `WDTCNR = 0` at the shortest `OVSEL` — *讀*, `tools/rlxprobe/uart.S`. The ESC
> window is ~4.9 s wide. **No hand starts a capture inside that.** ESC arriving
> while the payload runs is harmless: `uart.S` never reads `RBR`, so the bytes sit
> in the receive FIFO and overrun. The cost of an oversized window is log noise;
> the cost of a missed one is a power cycle, and this project has paid it twice.
> 🆕 **`--esc-after 60` is now derived, and the derivation is the point — not the
> number, which does not change.** The old note here called it "a guess", and the
> half of it that was actually uncalibrated was not the half it named. Budget from
> `J` to the ESC window closing:
>
> | term | value | mark |
> |---|---:|---|
> | `J` echo and the loader's jump path | ~0.010 s | 推 |
> | **`probe1`'s report** | **0.4018 s** | 算 — **1,543 bytes** exactly (`104 × 13` rows `+ 32` banner `+ 144` six `field()`s `+ 15` end) ÷ 3840 B/s |
> | `rlx_reset`'s 16,777,216-iteration delay loop | **0.126 s** at 400 MHz / 3 cycles per iteration | 🔴 **推, and this is the term that rests on an unmeasured number** — `CLK-01`'s 400 MHz is a **banner string**, and `CLK-03` says outright that its relation to the measured 200.0049 MHz is 未量. At 200 MHz it is 0.252 s |
> | watchdog, `OVSEL=0000` = 2¹⁵ ticks | 2.15–2.26 ms | 量 — `CLK-08b`'s 14.53–15.26 MHz |
> | reset → first console byte | 2.07 ms | 量 — `CLK-14` |
> | first byte → banner | 0.592 s | 量 — `D1b` |
> | **banner → `Jump to image start`** | **4.886 s** | 量 — `LDR-15`, and it is **81 % of the whole budget** |
> | **total** | **6.02 s** | |
>
> So **60 is ten times the requirement** and `--seconds 120` is twenty. Both stay:
> seating rule 3's asymmetry has not changed, and `--seconds 120` doubles as the
> **sixty-second silence observation** this section's own fault box requires —
> which nothing said until now, and which is a reason not to shorten it.
> The report length is **6.7 %** of the budget, so calibrating `--esc-after` from
> it would have calibrated the smallest term in the table.
>
> 🆕 **The residual is a free measurement, and it is the only reason this
> arithmetic was worth doing.** `--esc-after` puts the report and the post-reset
> boot in **one** capture, so `H1b.timing` already carries both timestamps:
>
> ```
> Δ = t(first byte after the reset) − t(last byte of `rlxprobe: end`)
>   = drain(≤0.26 ms) + delay loop + watchdog(2.15–2.26 ms) + 2.07 ms
>   = delay loop + [4.5, 4.6] ms
> ```
>
> **Predicted, before the run:** `130.4 ms` if (400 MHz **and** 3 cycles/iteration);
> `172.3 ms` at 4 cycles; `256.2 ms` at 200 MHz. `CLK-15` got a 3.5 %全距 over n=9
> on a 350 ms interval through this same `.timing` mechanism, so 130 and 256 are
> separated by far more than the instrument's spread. ⚠️ **This measures `f/CPI`,
> not `f`** — 400 MHz with 6 cycles/iteration is indistinguishable from 200 MHz
> with 3 — so what a reading near 256 ms refutes is the **combination**
> (banner's 400 MHz **and** a filled-delay-slot 3-cycle loop), which is still a
> result. `CLK-03` has had no experiment assigned to it; this is one, and it costs
> nothing but reading a file that is written either way.
>
> `terminate_esc_line` writes the CR that terminates an ESC loop itself, so a
> flush cell no longer *creates* the terminator — it **checks** that one went out.
> 🔄 **It arrived in 1.2 and the tool in this tree is `1.3`** — 量 2026-08-25
> before power, `TOOL_VERSION = "1.3"`, bumped by `4f5331e` at 02:41 the same day,
> which added `--esc-period` and the achieved-period metadata that `H3c` reads.
> This box, `flush-h1b`'s row and `bench/2026-08-26/PREDICTIONS-b4-block0.md` all
> said *1.2*; the sheet is corrected, the sealed prediction file is not, and
> `bench/2026-08-25/PREDICTIONS-b4-block0.md` carries the corrected value with the
> reason. **A stale version number in a sheet costs one failed prediction against
> the instrument**, which is noise in the column that has to stay signal. **The other half of seating rule 2 is not covered
> by the instrument and cannot be**: the first command after the console adapter
> re-enumerates on the host is echoed and not acted on, signature *echo + prompt +
> no data line*, and no capture can see an event that happened while it was not
> running. That is what `A0` is for, and it is why `A0` runs before `H0a` —
> **a poisoned first command and "the 32 words are not there" are the same
> observation at the bench**, and `H0a` is what decides whether `probe2` runs.

> 🔴 **What a fault costs, and it is the reason the running order is what it is.**
> `docs/loader-command-semantics.md` §10: an exception the loader does not handle
> reaches `do_reserved` at `0x80400BE8`, which prints two lines with **no
> trailing newline** and then executes `j 0x80400C18` — a branch to itself, with
> `IEc` already 0 and the watchdog not armed. **It hangs forever.** So:
>
> - every cell that can fault runs **after** every cell that cannot;
> - both payloads write each result into `0x80A00000` **before** taking the next
>   one, through KSEG1, so a hang costs the cells after it and not the cells
>   before it;
> - **if the board goes silent, do not touch the power for 60 seconds.** The
>   claim that the hang is permanent is READ, not measured, and a spontaneous
>   recovery would refute it. Then power-cycle, ESC to the prompt, and
>   `DW 80A00000 137` — `MEM-15` says a short power-off keeps the contents.
>   **137 and not 88**: the block is 137 words and `88` stops before the seal,
>   which is the word that tells a completed run from a truncated one.
>
> 🔴 **THAT LAST LINE IS `probe1`'s AND IT IS THE WRONG COMMAND FOR `R1g-4b`.**
> Corrected 2026-08-25, at the desk, before the second seating. `probe2`'s block
> is at **`0x80A01000`** and is **817 poisoned words**, not 137 at `0x80A00000`
> — `probe2.c` `RB_HDR 40 + RB_CELLS 256 × RB_CELLW 3 + 1` = 809, `RB_POISON_W`
> = 817. So on a hang tonight the recovery read is
>
> ```
> DW 80A01000 817          9,661 bytes, 2.52 s (tools/reply-size.py)
> ```
>
> and typing `DW 80A00000 137` instead is worse than reading nothing: **`MEM-15`
> is exactly why.** `probe1`'s block from 2026-08-25 — `magic=524C5831`,
> `nonce=9D34F1C7`, thirteen filled rows and a valid seal at word 136
> (`bench/2026-08-25/H1c.log`) — is still at `0x80A00000` unless the power-off
> cleared it, and it would come back **looking like a completed run**. The
> operator would read yesterday's answer as tonight's. `H0d-a` is what turns
> that from an inference into a comparison, and it is why the cell is in
> tonight's block 0.
>
> **Word 2 is the first word to read on a recovered block**: `H_PROGRESS`, a
> monotone marker, so a hang says where it stopped instead of leaving it to be
> inferred from what is missing. `DEADC0DE` there means the run never reached
> its own header.

**Running order.** 🔄 **`A-catch` -> `A0` -> `H0` -> `H1` -> `H3b` -> `H3a` ->
`H3c`. `H2` is not in it** — see the box at the head of `§H2`; this seating is
`R1g-4a` and `H2` is `R1g-4b`. `A0` is first because seating rule 1 says so.
**`H3b` moves ahead of `H3a` and `H3c` and behind `H1a`**: it is four cable moves
on the same link the TFTP upload uses, and a stale neighbour entry cost `G4-put`
three retransmits and 8.935 s (*量*, `§`Results). 🔄 **It used to say "behind
`H2a`" because there were two uploads; there is now one, and `H1a` is it.**
`H3a` and `H3c` both reset the board, so they go last.

🆕 **`H3a` is now probably free, and the sheet already said why.** `H3a`'s own row
notes its reset is redundant with `H1b`'s — `rlx_reset` writes the same
`WDTCNR = 0`. With `H2` gone, nothing between `H1b` and `H3a` runs a kernel, so
`H1b`'s reset **already produced** the condition `C-17` needs. **Try
`DW 81000400 16` immediately after `flush-h1b` and `H1c`**; if the reading is
there, `H3a`'s `J BFC00000` is a second instance rather than the only one, and it
is the first thing dropped if the seating runs long.

> ⚠️ **Everything from `**Running order.**` to here is `R1g-4a`'s order and it
> ran on 2026-08-25.** It is left standing as the record. The order for the
> second seating is the next subsection, and it is not this one.

### Running order — `R1g-4b`, the second seating, `bench/2026-08-25b/`

**Written 2026-08-25 at the desk, before power.** Rule 4: every command tonight
is typed from this subsection or from a tool, never re-stated by hand. Two of
the three cells the 2026-08-25 pre-flight audit caught were cross-references
that carried no command, so the commands are literal here.

**Directory `bench/2026-08-25b/`, not `bench/2026-08-26/`** — one directory per
power cycle, and `bench/2026-08-26/README.md` records why that one is closed to
captures.

🔴 **`§H3` does not run. All three of its cells closed on 2026-08-25** and the
section is left standing as the record, not as a plan:

| | why it does not run tonight |
|---|---|
| `H3a` `C-17` | closed. `H3a-early` and `H3a-rb` came back **byte-identical**, 213 bytes each, `578D0314 5B774B35 …` — bias, not the 32-byte-periodic structure — on two reset paths |
| `H3b` `NET-13` | closed on **silkscreen → port** (`WAN→0 LAN1→1 LAN2→2 LAN3→3` 量, `LAN4→4` 推). What is left is the **position** map, and `SPEC.md` §17 says outright it needs *one look at the case*, not a register. **Running it would spend four captures re-measuring a closed question and disturb the link the upload uses** — `G4-put` lost 8.935 s to a stale neighbour entry (量) |
| `H3c` `CLK-08b` | closed. 14.9650 MHz, the residual is proportional, and its own row forbids a third `OVSEL` point |

**Three new ride-alongs replace them**, and they are `R1` §17 rows rather than
`§H3` rows: `SPI-cold`/`SPI-warm` (`CLK-15 冷暖差`), `--esc-period 0.002` on the
two reset-crossing captures (`CLK-15 殘留`, **and see what it can actually
settle** in the block-0 file), and the case silkscreen, which needs no power.

#### Block 0 — eight reads, zero bytes written to the device

Prediction file: `bench/2026-08-25b/PREDICTIONS-b4-block0.md`, written before
power. Every line below is `/usr/bin/python3 tools/console-capture.py capture
--port /dev/ttyUSB0 --baud 38400 --out bench/2026-08-25b/<cell>` plus the
arguments shown. **No line reaches 128 characters**; the longest command is 15.

| # | cell | arguments | bytes |
|---:|---|---|---:|
| 1 | `A-catch` | `--esc 180 --esc-period 0.002 --seconds 200 --cr-settle 3` | — |
| 2 | `A0` | `--send 'DW 8040DBC0 1' --seconds 4` | 71 |
| 3 | `SPI-cold` 🆕 | `--send 'DW B8001200 4' --seconds 4` | 71 |
| 4 | `H0a` | `--send 'DW 80000080 32' --seconds 6` | 401 |
| 5 | `H0b` | `--send 'DW 8040EB40 32' --seconds 6` | 401 |
| 6 | `H0c` 🔄 | `--send 'DW 80000000 32' --seconds 6` — **32, not 8** | 401 |
| 7 | `H0d-a` | `--send 'DW 80A00000 8' --seconds 4` | 118 |
| 8 | `H0d-b` | `--send 'DW 80A01000 8' --seconds 4` | 118 |

Byte counts from `tools/reply-size.py predict`, not from a person — `LDR-07`'s
formula is a tool since 2026-08-25 and both of that seating's arithmetic errors
were in blocks written at the bench.

🔴 **`H0c` is `32` and not `8`, and it is the correction that matters most in
this subsection.** `§H2h` says its two reads must come back *byte-identical to
`H0a` and `H0c`*. `H0a` is safe to carry across a power cycle — `trap_init`
re-makes that copy on every boot. **`H0c` is not**: the loader never populates
the UTLB refill vector, so `0x80000000` holds DRAM power-on bias, and `probe2`
restores it from a copy it takes **tonight**. Comparing tonight's restore against
2026-08-25's bias is the `D2c`/`E10d` defect class, and the false alarm it
produces reads as *`probe2` corrupted physical 0* — the one outcome that would
stop the gate. **Taking 32 words rather than 8 also makes `install.changed` an
exact prediction instead of a non-zero one**, and lets `§H2h` cover all 64 words
of both vectors rather than 32 + 8.

`H0a2` and `H0a3` are **not** repeated. `H0a2` (`DW 8040054C 32`) proves
`trap_init`'s copy landed and it is a RAM-to-RAM identity — a property of the
boot, already 量 on 2026-08-25 and re-derived identically every boot. `H0a3`
(`DW A0000080 32`) is about the D-cache being coherent for this page, which
`H1` settled as a property of the core — 🔄 **and the narrower form is the one
that holds: a cached store to a line the D-cache does not hold reaches memory
unaided (2026-08-26).** Both are class (a)/(b);
`H0c` is class (c) and that is the whole distinction.

#### Block 1 — the upload and the run

🔴 **The `--image` path is `build/probe2/`.** `§H2a` said
`build/p2a/probe2/probe2.bin` until tonight, and 量 2026-08-25 18:2x that file
**exists** and is a different, withdrawn **6,656**-byte binary
(`8a15b501c160dd59…`) — the pre-fix `p2a`. It would have uploaded cleanly and run
the payload whose `break` failure is silent, whose census is contaminated and
whose `FLUSH_ISC` knob still exists. Same defect class as `G2`/`G4`'s
`--load-addr 0x80A00000`, and it survived the collapse to one binary because
nothing pointed a tool at the string.

| # | cell | command |
|---:|---|---|
| 1 | `H2-rescue` | `/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-08-25b/H2-rescue.json` |
| 2 | `H2a-ab` | `… console-capture.py capture … --out bench/2026-08-25b/H2a-ab --send 'DW 8040D4A0 1' --seconds 4` — **71 bytes, word 1 must be `00000000`. If it is not, stop. Nothing is uploaded** |
| 3 | `H2a-put` | `/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/probe2/probe2.bin --rescue-report bench/2026-08-25b/H2-rescue.json --expect-load 80500000 --yes` |
| 4 | `H2a` | `… console-capture.py capture … --out bench/2026-08-25b/H2a --send 'J 80500000' --esc-after 60 --esc-period 0.002 --seconds 120` |

⚠️ `--load-addr` is `auto_int`, so `0x80500000` **with** the `0x`; `--expect-load`
is `int(s,16)`, so `80500000` **without** it. Opposite conventions, same session,
one minute apart — 量 tonight from `argparse` in both files.

**`H2b`–`H2f` are readings out of capture 4**, not commands. `G5`'s shape, not
`G2`/`G4`'s: those two carry `0x80A00000`, which is `probe1`'s block.

#### Block 2 — after the payload's own watchdog reset

`RESET=1`, so `start.S` calls `rlx_reset` the instant `main` returns and the
prompt comes back inside capture 4's `--esc-after` window. `trap_init` has
re-run before anything below is typed.

| # | cell | arguments | bytes |
|---:|---|---|---:|
| 1 | `flush-h2a` | `--send '' --seconds 2` | 11, a bare prompt, **no `Unknown command !`** |
| 2 | `H2g-hdr` | `--send 'DW 80A01000 40' --seconds 6` | 495 |
| 3 | `H2g` 🔄 | `--send 'DW 80A01000 817' --seconds 10` — **817, not 809** | **9,661**, 2.52 s of wire |
| 4 | `H2h-gen` | `--send 'DW 80000080 32' --seconds 6` | 401 |
| 5 | `H2h-utlb` 🔄 | `--send 'DW 80000000 32' --seconds 6` — **32, not 8** | 401 |
| 6 | `SPI-warm` 🆕 | `--send 'DW B8001200 4' --seconds 4` | 71 |

**The block comes before the ride-along and that is deliberate**: `H2g` is the
only irreplaceable reading of the six, and a console that dies mid-block should
cost the ride-along rather than the census.

🔄 **`§H2h`'s expected value is corrected**: `H2h-gen` against **tonight's**
`H0a`, `H2h-utlb` against **tonight's** `H0c` — never against
`bench/2026-08-25/`. What `H2h-gen` can say is also narrower than the row
claims: the watchdog reset re-runs `trap_init`, so it checks the loader, not
`probe2`'s restore. **`H2h-utlb` is the half that checks `probe2`**, because
nothing on a warm reset writes `0x80000000`.

| | command | expected | what it refutes |
|---|---|---|---|
| **A0** | `DW 8040DBC0 1` | 71 bytes, `8040DBC0: 8040B070 00000000 80409A9C 8040B074` — byte-identical to `bench/2026-08-24b/A0.log`, which is itself byte-identical to part one's | that the console path is the one seating 2 measured, and that DTR/RTS toggling on this 4-pin header does not disturb the board. **It is also the throwaway seating rule 2's second half requires**, spent here where nothing depends on the answer |

### H0 — six reads, before anything is uploaded. Zero risk, and they turn a whole document from READ into 量

| | command | expected | what it refutes |
|---|---|---|---|
| **H0a** | `DW 80000080 32` | the 32 words `notes/cache-model.md` lists, of which **words 0-10 are the gate**: `401b6800 00000000 00000000 3c1a8041 275aeb40 337b007c 035bd021 8f5a0000 00000000 03400008 00000000`. 🔄 **Words 11-31 are not part of the gate and are not zero.** They are the tail of the 128 bytes `trap_init` copies from `0x8040054C`: words 11-12 are padding and **word 13 (`401a6000` = `mfc0 k0,c0_status`) begins a second routine** — `exception_handlers[0]` = `0x80400580` lies at `0x8040054C + 0x34`, so words 13-31 are a verbatim, never-executed copy of the loader's IRQ entry. An operator who reads nonzero words past index 10 as a mismatch would abort `H2` for nothing | 🔴 **that the loader populated a vector at `0x80000080` and not at MIPS32's `0x80000180`.** Three sources agree and this is the reading that settles it. **If words 0-10 are not there, `probe2` must not be run** — its handler would go somewhere the core does not fetch from. ⚠️ **What it cannot settle**: which base the core actually fetches from is `Status.BEV`, no loader command reads CP0, and only `probe2` can measure it. This cell confirms the copy, not the dispatch |
| **H0a2** 🆕 | `DW 8040054C 32` | **word for word identical to `H0a`, all 32** | 🔴 **that `trap_init`'s 128-byte copy landed intact — and it needs no predicted value at all**, so it is the only thing here that covers words 11-31, which nothing in this repository predicted until 2026-08-25. Its positive control is built in: a broken `DW`, or an address form being rewritten under it, would not produce two agreeing reads. ⚠️ `0x8040054C` is stage 2's own image **in DRAM**, not ROM — the loader runs from `0x80400000` in KSEG0 and the ROM window is `0xBFC00000` — so this is a RAM-to-RAM identity and must not later be read as agreement with flash |
| **H0a3** 🆕 | `DW A0000080 32` | identical to `H0a` | 🔴 **that a stale D-cache line is not what `H0a` read.** `DW` forces the address into KSEG0 only when bit 31 is clear (`docs/loader-command-semantics.md` §f), so `0xA0000080` passes through uncached. A difference is worth more than the original cell, and **`probe2` must not run until it is explained** — `probe2` installs its handler through KSEG1 (`wr_unc`) and would be racing the same line |
| **H0b** | `DW 8040EB40 32` | `[0] = 80400580`, `[23] = 804007c0`, the other thirty `= 80400be8` | that `exception_handlers[32]` is the real dispatch table, and that thirty of the thirty-two entries are the print-and-hang. **`SPEC.md` `CPU-26` named `0x8040A5C0` until today and that was the boot state machine** |
| **H0c** | `DW 80000000 8` | undetermined. `0x5A5AA5A5` is one candidate — stage 1's DRAM-sizing probe writes it to `0xA0000000` — but stage 1 writes several patterns and which lands last was not traced | what the UTLB refill vector actually holds. It matters because a kuseg load from a faulting payload goes **here**, and the loader never populated it |
| **H0d** 🆕 | `DW 80A00000 8`, then `DW 80A01000 8`, **before anything is uploaded** | word 0 neither `DEADC0DE` nor `524c5831`/`524c5832` in either. 🔴 **REVERSED AT `0x80A00000` FOR `R1g-4b`, and the reversal is the point.** This rule was written when `0x80A00000` had never held a block. It has held one since 2026-08-25: `524C5831 9D34F1C7 …` with a valid seal (`bench/2026-08-25/H1c.log`). **So tonight `524C5831` at `0x80A00000` is the CORRECT reading and not the failure** — it is `MEM-15` measured with a chosen value across a real power-off, which is stronger than the two-word canary `MEM-15` currently rests on. The rule stands **unchanged at `0x80A01000`**, where `524C5832` has never been written by anything and would mean the block read after the run is not this run's | 🔴 **that a result block read later belongs to this seating.** `MEM-10` measured a **two-word** canary at `0x80A00000` surviving three warm resets byte for byte; **`0x80A01000` has never been read on this device at all**. Same job `G0` did for `R0`: it turns *the block is left over from the previous payload* from an inference into a comparison |

**Reply sizes, from `LDR-07`'s rule** (address hex, **length decimal**;
`DW <addr> N` prints `4 × ceil(N/4)` words, four to a line): `H0a`, `H0a2`, `H0a3`
and `H0b` are **8 lines / 401 bytes** each; `H0c` and each half of `H0d` are
**2 lines / 118 bytes**. `A0` is **71 bytes**. Byte counts by
`docs/loader-command-semantics.md` §f's own weight formula, and a short reply is
the completeness check — `DW` rounds the count **up**, so a length given too small
never says so.

**If `H0a` does not match, and it is not one outcome.** Written before the run
because the decision has to be made in front of a live board. `H0b` runs
regardless: it reads loader BSS rather than the vector page, and `.bss` is zeroed
at boot by the loop at `0x8040046C`, so an all-zero `H0b` is distinguishable from
every other reading.

| what came back | what it means | what still runs |
|---|---|---|
| words 0-10 match, 11-31 differ from `H0a2` | something wrote the vector page after `trap_init` copied it | everything. `probe2` saves and restores whatever it finds; record that the page is not stable |
| all zero, `H0b` correct | the table was filled but the 128-byte copy is not visible here | **`H2` void.** `H1` runs, but its fault containment is undetermined rather than the bounded hang `cache.S` argues for. `H3` unaffected |
| all zero, `H0b` all zero | `trap_init` never ran; the board is not in the state this session assumes | **`H2` void**, `H1` unsafe. End the seating and take the reading home |
| a stage-1 DRAM-sizing pattern | the residue was never overwritten, i.e. the copy did not land here — note the sheet expects that pattern at `0x80000000` (`H0c`) and calls it undetermined *there* | **`H1` and `H2` both void.** `H0c`'s own answer becomes the interesting one |
| MIPS-I, but a different `lui`/`addiu` pair | the vector is real and the core does fetch here; `exception_handlers` is **not** at `0x8040EB40` | everything. `H0b`'s expected value and `SPEC.md` `CPU-26` are void — decode the pair at the bench and read the new address |
| `42000018` (`eret`) anywhere in the 32 | 🔴 the R3000 reading is refuted, including `notes/cache-model.md`'s zero-`eret` control | **`probe2` must not run**: `exc.S` returns with `rfe` on a device build. `probe1` runs. **This is the most valuable outcome available this seating and it costs nothing to observe** |
| fewer than 8 lines, or an error | this refutes `LDR-07`, which is worth more than `H0a` | everything, after the command is retyped from this sheet (rule 4) |

⚠️ **`BEV=1` is not on that list, and that is deliberate.** `trap_init` copies the
128 bytes **unconditionally** — no `BEV` test on the path (*讀*, `trap_init` at
`0x8040D07C`) — so what is in RAM at `0x80000080` and what base the core fetches
from are independent. Reading `0xBFC00180` would not settle it either: that window
holds stage-1 flash bytes whichever base is live, so it is a read that cannot fail.
`probe2` is the instrument — it reads `Status` itself and, on `BEV=1`, refuses to
install and resets. **So `probe2` is safe to launch on this question; it is the
measurement.** 🔴 **This sentence said *stamps `0xBE71BAD1` into result word 23*
until 2026-08-25, and that constant exists in no payload source** — 量:
`grep -rin be71bad1 tools/` returns nothing, and the same grep run for
`DEADC0DE` finds it in `probe1.c:117` and `probe2.c:127`, so the search could
have fired. Word 23 is now `H_CNT_BEFORE`. **What a `BEV=1` refusal actually
looks like is two independent signals rather than one magic number**:
`progress = 00000010` at block word 2 and bit 22 set in `status` at word 6, plus
`rlxprobe: BEV=1 -- vectors are NOT at 0x80000080. Refusing to install.` on the
wire — a **242**-byte report (`tools/reply-size.py`'s sibling arithmetic, from
`probe2.c`'s own field list). `§H2g`'s row had already recorded the replacement;
this site and two others had not been reached, which is `43ec0e0`'s defect class
for the fourth time.

🔴 **And `H0a` does not gate `H1`.** Not one of `probe1`'s six cells reads or
writes an exception vector, so its result is unaffected by where the vectors are.
What a failed `H0a` changes is `cache.S`'s containment argument — the bounded
*two prints and a hang* becomes undetermined — so a silent board is then recorded
as unexplained rather than as `do_reserved`. Refusing to run `probe1` on a failed
`H0a` would spend the power cycle to avoid a risk that is bounded at the same one
power cycle either way.

### H1 — `probe1`, the cache-model discriminator

**Build line. Build into an empty directory, and the `show` output must NOT
print `*** NOT A DEVICE BUILD ***`:**

```
rm -rf tools/rlxprobe/build/probe1
make -C tools/rlxprobe P=probe1 payload
make -C tools/rlxprobe P=probe1 show
```

`LOADADDR=0x80500000`, `RESULT_BASE=0x80A00000`, `GEOM=0`. Record the `sha256`
`make show` prints; it goes in the capture's metadata.

> 🔴 **`make` does not rebuild when a knob changes, and `make show` reports
> the knob you asked for beside the binary you already had.** 量 2026-08-25, in
> this tree: `make -C tools/rlxprobe P=probe2 payload RESULT_BASE=0x80A01000`
> printed **`make: Nothing to be done for 'payload'.`** — no compile, no `show`,
> and therefore no `sha256` to record — while `build/probe2/probe2.bin` held
> `lui *,0x80a0` ×1 and `lui *,0xa0a0` ×2 and `0x80a1`/`0xa0a1` **zero times**,
> i.e. it was a `RESULT_BASE=0x80A00000` build. The object rules depend on the
> sources and two headers and on nothing that carries a `-D`, and
> `tools/test-rlxprobe.sh` builds into a fresh `BUILD=` every time, which is why
> 62 cases have never seen it. **So: empty the build directory before every line,
> and treat `Nothing to be done` as a hard stop.**
>
> ⚠️ **`GEOM=0` is what `seq=0000000d` below assumes.** `GEOM=1` arms a walk
> that writes 1 MiB of real memory at `0x80B00000` if this core does not implement
> `Status.IsC`, and this sheet has no before/after read of that window — so
> `CPU-25` (cache size, line size, associativity) is **not** measured this seating.
> `PROGRESS.md`'s `R1g-1` describes cell ⑥ as `r3k_cache_size()`; in the payload
> that is the `XGMI`/`XGMD` extras behind `#if RLX_GEOM`, and cell 6 is
> store-uncached + `CCTL 0x002`. The write-up owns closing that gap.

| | command | expected | what it refutes |
|---|---|---|---|
| **H1a** 🔄 | **the two lines, not a cross-reference — and the shape is `§G`'s `G5`, not `G2`/`G4`'s.** `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o <dir>/H1-rescue.json`; then `DW 8040D4A0 1`; then `loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/probe1/probe1.bin --rescue-report <dir>/H1-rescue.json --expect-load 80500000 --yes` | in the transcript, in this order: `AutoBurning=0`, `Set TFTP Load Addr 0x80500000`, `Now your Target IP is 10.1.1.1`; then word 1 = `00000000`. **If word 1 is not `00000000`, stop. Nothing is uploaded** | that this upload could reach flash — same control as `R0`'s, and read **before** the `put` as `G2` does it, because the word that matters is the one the burn path sees during the transfer. 🔴 **Why the literal lines, and it is the defect this row was:** `G2` carries `--load-addr 0x80A00000` and `G4` `--expect-load 80A00000`, which is `probe1`'s own `RESULT_BASE`. An image there plus `J 80500000` boots the vendor kernel the loader has already staged (`G1`) — loader gone, DRAM gone, one power cycle — and **`--expect-load` cannot catch it**, because `put` and `get` both serve `[0x8040D3A8]` and the flag is checked against the transcript. ⚠️ `--load-addr` is `int(s,0)`, so `0x80500000`; `--expect-load` is `int(s,16)`, so bare `80500000` |
| **H1b** 🔄 | `console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out <dir>/H1b --send 'J 80500000' --esc-after 60 --seconds 120` | the `*** rlxprobe P1 9d34f1c7 ***` banner, **`rb=80a00000`**, then **thirteen** `t=…` rows, then `seq=0000000d`, `sum=…`, `end` — then the payload's own watchdog reset, with the ESC stream already running across it. **1,543 bytes, 0.4018 s at 38400 8N1** — the report is `104 × 13 + 32 + 144 + 15`, and a short capture is a truncated one | **that the payload ran at all.** 🔴 **The payload prints hex in LOWER case and this sheet used to be written in the loader's UPPER case** — `report.c`'s digit table is `"0123456789abcdef"`, while `DW` replies `8040DBC0:` (讀, `report.c:18`; 量, every `A0.log`). So it is `rb=80a00000`, and `pc=` must begin **`805`** — if it begins **`a05`**, lower case, the operator typed `J A0500000`. **Grepping the capture for `80A00000` returns nothing on a correct run**, and the sheet asked for exactly that grep until 2026-08-25. 🔄 **Thirteen, not twelve**: twelve cell rows plus one `t=58435430` (`'XCT0'`) carrying the first read anyone has taken of CP0 register 20. `seq=0000000d` is 13 and always said so. ⚠️ **The rows come in risk order, not numeric order** — `CELLS[] = 1, 5, 4, 2, 3, 6`, two victims each — so row *n* is not cell *n*; `t=` is the label. `rb=` is the stale-build check and costs nothing. 🆕 ⚠️ **`flags` bit 0 clear does NOT mean the cells are void, and the payload's own message says it does.** `rlxprobe: NOT IN KSEG0 -- every cache cell is void` is printed and then control branches straight back into the cell loop; every cell runs and the block seals normally. The claim is also false: the build is `-mno-abicalls -fno-pic -G0`, so `victims`, `vaddr`, the patch store and `$sp` are all **absolute KSEG0 addresses whatever the PC is** — only the payload's *own* instruction fetch changes segment, which removes the one eviction source `victims.S` admits the 7 KiB pair gap cannot exclude. **Record the reading, do not discard it** |
| **flush-h1b** 🆕 | `console-capture.py capture --port /dev/ttyUSB0 --out <dir>/flush-h1b --send '' --seconds 2` | a **bare prompt, 11 bytes, no `Unknown command !`** — `bench/2026-08-24b/flush-cont.log`'s shape | that `console-capture`'s own ESC terminator (`terminate_esc_line`, 1.2, in a 1.3 tree) went out. ≈31 bytes with `Unknown command !` means it did not, and the next command line would have been appended to the residue (`LDR-16`) |
| **H1c** 🔄 | `DW 80A00000 137` | the same **thirteen** rows from RAM, and the seal at word 136. 🆕 **Plus twenty-seven words of `DEADC0DE`, and they are correct**: `RB_ROWS` is 16 and only 13 are used, so words **112–135** stay poisoned, and `LDR-07`'s round-up makes `DW … 137` print **140** words, so **137–139** are poisoned too. `24 + 3 = 27`. A reader who takes poison where a row should be as a truncated run will abort `H1` for nothing | **that the UART report and the RAM block agree.** Two channels, because P9-12 lost its nonce to a 16-byte FIFO. 🔴 **137, not 88.** The block is `RB_HDR 8 + RB_ROWS 16 × RB_ROWW 8 + 1` = **137 words**; `88` returns the header and ten rows, dropping cell 6's two victims, the `XCT0` row, and **the seal — the only word that separates a completed run from a truncated one**. 35 lines, 1671-byte reply; a 777-byte / 16-line reply was measured six times last seating, so no split is needed. `tools/rlxprobe/Makefile`'s `show` printed the same `88` for **both** payloads and has been corrected in the same commit as this row |
| **H1d** | *(only if `H1b` and `H1c` disagree, or the run stopped early)* `DW 80A00000 08` | `magic=524c5831`, `nonce=9d34f1c7`, and `seq` = how many rows completed | how far it got. A poisoned block (`DEADC0DE`) means it started and got nowhere, which is a different observation from the previous run's data still being there |

**The reading, written before the run.** Each row is
`t v pr ex mb ma g vd`; `vd` is the verdict:

| `vd` | means | and what it would say |
|---|---|---|
| `01` STALE | executed the OLD constant, memory holds the NEW one | the I-cache held stale bytes and the treatment did not take |
| `02` FRESH | executed the NEW constant | the treatment took — **or there was nothing to take** |
| `03` NOSTORE | executed OLD, memory still holds OLD | the store never reached memory; a write-back D-cache is holding it |
| `07` CORRUPT | the victim's `jr ra` is no longer `03e00008` | 🔴 **the treatment wrote memory where it was meant to write cache tags.** Measured under qemu 2026-08-25 for cell 4: `Status.IsC` did not isolate, `03e00008` became `00e00008` = `jr $7`, and without the guard the payload jumped into the weeds |
| `04` VOIDPRIME | the prime call did not return the OLD constant | the harness is wrong, not the core — the victim never reached a known state |
| `05` NOTVICTIM | the word at that address was not the victim's | the slot arithmetic or the load address is wrong |
| `06` WEIRD | executed neither constant | 🔴 **the run is uninterpretable, and so is every cell around it** |

**🔴 The refutation condition, and it is on cell 1.** Cell 1 stores through the
cached window and applies **no treatment at all**. It must read `01` STALE. If it
reads `02` FRESH — on either of its two victims — then either this core has no
I-cache, or the line was evicted between the two calls, or the caches are
coherent; **under any of the three the other five cells passed without being
tested, and the gate does not close.** The two victims of a cell are 7 KiB apart
precisely so that eviction has to explain both.

🔄 **And `03` NOSTORE on cell 1 is not a pass either.** A write-back D-cache
legitimately produces it — the store never reached memory — and it says nothing
about the I-cache, which is the only thing cell 1 exists to test. Record it, read
it against cell 5 (the same store through KSEG1, no treatment), and close the gate
on the pair or not at all. `04`, `05` and `06` are the harness reporting that it
is itself wrong; on cell 1 any of them voids the table exactly as `02` does.

**🆕 Read cell 1 against cell 5 on the `ma` column, and it is a measurement in its
own right.** The paragraph above says to do it; this is the table, written before
the run. The two cells differ in exactly one variable — cell 1 stores through the
cached window, cell 5 through KSEG1 — and both apply `T_NONE`, so `ma`
(`mem_after`, an **uncached** read-back) partitions cleanly:

| cell 1 `ma` | cell 5 `ma` | reading |
|---|---|---|
| `240222b2` | `240222b2` | **D-cache is write-through** (or does not allocate on write). Both cells report `01` STALE and the only stale thing is the I-cache. This is the case the verdict names were written for |
| `240211a1` | `240222b2` | 🔴 **D-cache is write-back.** Cell 1's cached store is still sitting dirty. Cell 1 reports `03` NOSTORE **and that verdict name must not be read as "the store did not happen"** — it did |
| `240211a1` | `240211a1` | the store did not happen at all. Instrument failure, not a cache finding — check `mb` and `05` NOTVICTIM before reading anything else |
| `240222b2` | `240211a1` | **impossible under any cache model.** It refutes the KSEG1-alias assumption this whole payload rests on, and it is worth more than the cell it broke |

⚠️ **The two constants are written in the payload's case, which is lower.** The
UART report prints `ma=240211a1`; `DW 80A00000 137` prints the same word as
`240211A1`, because the loader's hex is upper case. **Two channels, two cases,
one word** — and comparing them by eye is the whole point of `H1c`.

**否證** — if cell 1 and cell 5 disagree on `ex` (executed) rather than on `ma`,
this table does not apply: that reading is about the I-cache, not the D-cache.

🔴 **The consequence, and it is the one that reaches a driver.** Four of the six
cells store through the cached window — 1, 4, 2 and 3 — so in the write-back
case **all four** inherit it. Cell 2 (`CCTL 0x002` alone) then reads `03` NOSTORE
while cell 3 (`0x200` then `0x002`) reads `02` FRESH, and the natural reading —
*"invalidating I alone is insufficient on this core"* — **is wrong**. `0x002`
alone is sufficient; what `0x200` added was getting the store out of the D-cache.
That sentence would go into `notes/cache-model.md` and then into `R5b`'s MTD
driver as the flush recipe, which is decision ① of the four this gate exists to
unblock. **In the write-back case, cell 2 against cell 3 measures the D-flush and
not the I-invalidate, and the write-up says so or it is wrong.**

Cells 5 and 6 are the pair that is *not* contaminated — both store through KSEG1
— so **in the write-back case the flush answer comes from `5 → 6`, not from
`2 → 3`.** `probe2`'s own `flush_for_handler()` is the store-uncached recipe, so
that is the pair it depends on anyway.

**Expected on the device, and it is the opposite of qemu.** qemu came back FRESH
on cells 1 and 5 because TCG invalidates a translation block when a store lands
on translated code. **A device run that looks like the qemu run is the run that
refutes the experiment**, not the one that confirms it.

### H2 — `probe2`, the exception handler and the CP0 census — 🔴 **DEFERRED, does not run this seating**

> 🔴 **`H2` is not run in `R1g-4a`. It moves to `R1g-4b`, a second seating, with
> `probe2` fixed first.** Decided 2026-08-25 at the desk, after an independent
> audit of `probe1.c`/`probe2.c` — `docs/rlxprobe-audit-2026-08-25.md`. The
> section below is left standing **verbatim** rather than deleted, because it is
> what `R1g-4b` runs and because deleting a sheet that was audited is how the
> audit's findings stop being traceable to the cells they came from.
>
> **Two reasons, and they are different reasons.**
>
> ① 🔴 **`probe2`'s designed "visible failure" is measured to be complete
> silence.** `probe2.c` and `H2c` below both promise that a handler which did not
> take produces `Undefined Exception happen.` — *"an unambiguous observation"*.
> 量 2026-08-25 by disassembling `build/p2a/probe2/probe2.elf`: `rlx_puts` exits
> its loop on `bnez a0` (`0x80500f40`) so it **always returns with `$a0 = 0`**,
> nothing writes `$a0` between there and `jal rlx_do_break` (`0x80501364`), and
> `rlx_do_break` is `break / jr ra / nop` with **no `SAFE_A0`**. So on the failure
> branch `do_reserved` does `move v0,a0` (v0 = 0) then `lw a3,148(v0)` — a kuseg
> load through a TLB nothing initialised — **at `0x80400C00`, four bytes before
> its first `prom_printf`**. Neither line reaches the wire. `cache.S` spends
> thirty lines establishing exactly this hazard and applies the macro to three
> routines; the one instruction in the tree that is **guaranteed by design to
> fault** is the one without it, and `tools/test-rlxprobe.sh`'s `S1` scopes it out
> because `break` is not a CP0 instruction.
>
> ② 🔴 **Three of the four things `H2` exists to answer are contaminated.**
> `rlx_call0` (`0x80500218`) never writes `$2`, and `rlx_count_delta`
> (`0x805002d4`) reads `Count` into `$8`/`$15` without initialising either — both
> 量 from the emitted image. On the trap branch the handler skips the faulting
> `mfc0` without touching its destination, so a trapped census row's `v` column
> carries the running `zeros` counter (a steadily increasing small integer that
> reads like a family of registers answering) and `count.delta` is
> `(loader's leftover $t7) − 0xA0500150`. `H2e`'s written-before-the-run
> expectation is `delta = 00000000`, so **a residue-arithmetic non-zero reads as
> its refutation and answers `F50b` backwards** — demoting `R5-0`'s SoC timer
> driver from prerequisite to bonus, which is one of the four decisions this gate
> exists to make.
>
> **What deferring costs: one additional planned power cycle.** Stated plainly.
> `rlx_reset` means `H1` hands the prompt back by itself, so ending the seating
> after `H3` spends nothing extra *this* visit; `R1g-4b` needs its own cold-boot
> `A-catch` and its own `A0`.
>
> **What deferring buys, and it is not only safety:** `H0b` measures
> `exception_handlers[9]` — the single unverified link in reason ① — `H0c`
> measures what a kuseg fault actually lands on, `H0a3` measures whether the
> uncached view of the vector page is coherent, and **`H1` collapses `p2a`/`p2b`
> into one binary**, which dissolves the whole "two images, four characters apart,
> indistinguishable on both channels" hazard rather than papering a `field()` over
> it. The fix gets written against measured values instead of read ones.
>
> **`R1g-4b`'s must-fix list is in the audit document**, §"Must-fix". Do not
> attempt any of it at the bench.
>
> ---
>
> ✅ **2026-08-25, second desk sitting: the list is done and the deferral paid
> for itself.** All five items are in the payload, `probe2` builds gated, runs to
> its end marker under qemu, and `tools/test-rlxprobe.sh` is **106 cases, 0
> failed** — up from 66, with **four qemu-level mutations, one per fix**. The
> cells below are corrected for what changed; **their expected values are not
> rewritten**, because those are the hypotheses this seating exists to test and
> a desk day is the wrong place to invent new ones. What IS rewritten is
> everything the code change made false: one binary instead of two, a 40-word
> header, three words per census row, `DW 80A01000 809`, and the new fields.
>
> 🔴 **One thing the audit did not ask for is in here as well, and it is the
> reason the census grew a word.** The census now reads every register TWICE
> with two different primes. `S_NOWRITE` becomes certain rather than likely, and
> **a register that CHANGES between two reads reports itself** — which is a
> second, independent route to `F50b` that does not touch `rlx_count_delta`'s
> arithmetic at all. qemu's own `Count` is running, so its row `0x48` comes back
> `S_MOVES` and that is the positive control on the mechanism, obtained free.

✅ **All three preconditions are met.** `H0a` matched 32 of 32 words, `H0a3`
agreed with it through KSEG1, and `H1` reported `CCTL 0x002` alone as sufficient.

🔴 **There is ONE binary now, and that is Must-fix 3's actual fix.** `p2a` and
`p2b` were indistinguishable on every channel — not in a header word, not in a
`field()`, not in the banner, absent from `make show`, same `rb=`, command lines
four characters apart. The repair was never a `field()`: `H1` measured which
flush works, so `R1g-4b` builds one image against that measurement and
`RLX_FLUSH_ISC` no longer exists. `ISC` is now set per payload in the `Makefile`
with `override`, so `make P=probe2 ISC=1` cannot resurrect it — `test-rlxprobe.sh`
`C5` is that case.

```
rm -rf tools/rlxprobe/build/probe2
make -C tools/rlxprobe P=probe2 payload show RESULT_BASE=0x80A01000
```

🔄 **`make show` echoes the variables it was passed, not the binary's own
contents, so the check is the `sha256` against a clean build recorded here.**
量 2026-08-25, gcc 12.4.0, `-march=mips1 -msoft-float`, all three with no
`*** NOT A DEVICE BUILD ***` line:

| build | bytes | `sha256` |
|---|---:|---|
| **`probe2`, `RESULT_BASE=0x80A01000`** — what `R1g-4b` uploads | **9,392** | `78beb72f77f601017f363d14de9467646f3ff9a4515e3673b64972b74c745261` |
| `probe1`, `RESULT_BASE=0x80A00000`, `GEOM=0` — **rebuilt 2026-08-25, and this is NOT what ran** | 19,792 | `932fb2d5b435a385112c2e2d267baf8f653dbbc0e169850e7de7b11ff9619d27` |
| ~~`probe1`, the build that ran `H1`~~ | 19,792 | `fbac7d60319aacf9e86a4a673f899eaf41d3659ad9d55417da4c4c70c6d289f6` — **commit `2db12bb`**, and it is the artefact `R1d` was measured on |
| ~~`probe2` `p2a` / `p2b`~~ | 6,656 / 6,592 | withdrawn: two binaries no longer exist |

🔴 **`probe1`'s hash moved today and the row above says so rather than being
overwritten.** `rlx_call0` became `rlx_call0_primed` and `uart.S`'s four CP0
readers gained `SAFE_A0`, so the source that produced `R1d`'s measurement is the
one at commit `2db12bb` and nothing else. The size did not change — the growth
was absorbed by `.victims`'s `.align 10` padding — **so size alone would not have
caught it, and that is exactly why the hash is here.**

✅ **And the pointer is checked rather than asserted.** `git archive 2db12bb`
into a clean directory, rebuilt with the same gcc 12.4.0: **`fbac7d60…`,
exact.** So *the artefact `R1d` was measured on* names something that can be
reproduced from the repository, which is what a commit id is worth here. 🆕 It
is also `P4a`'s first data point, arriving four gates early and by accident:
**this tree already builds reproducibly across a checkout.**

**A `sha256` that is not one of these means the build did not happen**, which is
exactly what the stale case looks like: `payload` says `Nothing to be done` while
`show` prints the requested `RESULT_BASE` beside the old binary's hash
(`bda8bb96f1d42d9a…`, the artefact that was in this tree until 2026-08-25).
🆕 **`make show` now prints `flags 50010002` as well, and that word is IN the
report** — so the stale-build check has a second leg that comes back over the
wire rather than out of the build directory. `LOADADDR` joined the rebuild stamp
on 2026-08-25 too (`test-rlxprobe.sh` `A3`/`A4`): until then a second `make` with
a different `LOADADDR` relinked nothing and left an image for the old address.
⚠️ **Do not try to read the address out of the disassembly instead.** 量: both
`0x80A00000` and `0x80A01000` materialise through `lui …,0xa0a0`, because the
KSEG1 alias of `0x80A01000` is `0xA0A01000`; the only difference is a following
`addiu …,4096`. A `grep` for `0xa0a1` finds nothing on a **correct** build.

`RESULT_BASE=0x80A01000` so `probe1`'s block survives at `0x80A00000` and both
are recoverable from the same seating. The block on the console (`rb=`) is the
second channel that checks the right one went up. **`make show` must not print
`*** NOT A DEVICE BUILD ***`** — that line fires if any of `UART_THR`,
`VEC_GENERAL`, `CLEAR_BEV` **or `RET_ERET`** is off its default (four, not the
three this sheet said), and they exist only because qemu has no MIPS-I core.
⚠️ It does not test `VEC_UTLB` or `UART_LSR`, so a build that moved only one of
those would pass the badge.

| | command | expected | what it refutes |
|---|---|---|---|
| **H2a** 🔄 | **four steps, and the first exists because `H1b` reset the board.** `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o <dir>/H2-rescue.json`; then `DW 8040D4A0 1`; then `loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/p2a/probe2/probe2.bin --rescue-report <dir>/H2-rescue.json --expect-load 80500000 --yes`; then `console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out <dir>/H2a --send 'J 80500000' --esc-after 60 --seconds 120` | rescue transcript as `H1a`'s; then word 1 = `00000000`; then banner, **`rb=80a01000`**, **`flags=50010002`**, `status=`, `vec=80000080`, `handler_words=00000016`, `install.changed=` non-zero, **`install.bad=00000000`** | 🔴 **that the upload is running against this boot's state and not `H1a`'s.** `H1b`'s payload ends in `rlx_reset`, and a reset clears the loader's IP, its `LOADADDR` and `AUTOBURN` -- the Running order box states it and `G8b-ab` measured `00000001`. **`--max-rescue-age` cannot see it**: the bound is 3600 s and `loader-tftp.py`'s own docstring says bounding the age does not establish same-boot. The first symptom of skipping this is a transfer with nobody answering, because `rescue` is also what sends `IPCONFIG`; the flash hazard is second and needs the operator to restore the network by hand instead of by `rescue`. ⚠️ Two further barriers stand behind it and neither is a reason to skip the guard: `burn()` matches one of eight section signatures and `probe2.bin` carries none, and its length is not 4 KiB-aligned. **`rb=80a01000` is the stale-build check** -- `rb=80a00000` means the binary is the one that was already on disk, and it is about to poison `probe1`'s block. 🔄 **Lower case**: `report.c`'s digit table is `"0123456789abcdef"` and the loader's is upper, so `rb=80A01000` is a string a correct run never produces. 🆕 **`flags=50010002` is the second leg** -- `0x50` tag, `RESET=1` in bit 16, `CCTL 0x002` in the low half, and every qemu-only knob clear. Any other value and the image is not the device build. 🆕 **`install.bad=00000000` is Must-fix 2**: the payload now reads all 44 installed words back through KSEG1 before it dares `break`, so *the stores did not land* and *the core does not fetch there* stopped being one hang |
| **H2b** 🔄 | read `status=` | 🔴 **`CPU-27`, and it is deliberately not predicted.** `BEV` is bit 22. 🔄 **This row said `1000FC01` at the prompt, traced through ten writes to Status, and that value existed in no other file** -- while `SPEC.md` `CPU-27` is blank and `docs/loader-command-semantics.md` §9 says outright that whether `BEV` is 0 at the prompt **has not been traced**. The reading is whatever `status=` prints; **only bit 22 is load-bearing**, and any other bit differing from an expectation is an observation, not a fault | if `BEV` is 1 the payload refuses to install and still resets -- so this cell is safe to reach -- and `R1-gate`'s stop-loss applies: the census falls back to the no-handler subset. 🔄 **`stamps 0xBE71BAD1 into result word 23` is struck 2026-08-25**: that constant is in no payload source (量, grep with a positive control), and word 23 is `H_CNT_BEFORE`. The refusal signature is `progress=00000010` at word 2 **and** bit 22 set in `status` at word 6, and a 242-byte report that ends after `vec=` |
| **H2c** | `break.count` / `break.cause` | `count=00000001`, and `cause`'s ExcCode field (bits 6:2) = `9` → `cause & 0x7c = 0x24` | 🔴 **the positive control on the handler.** `break` traps on every MIPS ever built, so a `count` of 0 is the instrument reporting that it is not installed, not a property of this core. If the handler did not take, the loader prints `Undefined Exception happen.` and the board hangs — an unambiguous observation. 🔴 **That sentence was FALSE until 2026-08-25 and the fix is two instructions.** `rlx_puts` always returns `$a0 = 0`, and `do_reserved`'s `lw a3,148(v0)` at `0x80400C00` is four bytes before its first `prom_printf` -- so the promised message was measured to be complete silence. `rlx_do_break` now carries `SAFE_A0`, and `H0b` measured `exception_handlers[9] == 0x80400BE8`, which is the link that finding rested on. 🆕 **And the failure is now decomposed**: `install.bad=0` says the bytes ARE at the vector, so a `break.count` of 0 means the I-cache did not see them -- which would refute `H1`'s `CCTL 0x002` result on a different address range and a different store path |
| **H2d** 🔄 | the `cp0` rows, and `traps=` / `values=` / `zeros=` / **`nowrite=`** / **`moves=`** / **`mixed=`** | 🔴 **`PRId` is row `0x78`** (rd 15, sel 0). **The prediction, written before the run: `0x0000CD01`.** Four public sources point at the 4181 family; `52481` = `0xCD01` comes from this unit's kernel printing `%d`. **A reading in the 5281 range is worth more than one in the 4181 range** — it would refute a Realtek datasheet and two public kernel trees at once | `CPU-04`. `Config` is row `0x80`: **`Config.M == 0` proves outright that this is not a MIPS32 core**. 🔄 **Each row is now three words -- `v1 v2 state` -- and the report prints `rlxprobe: cp0 <row> <v1> <v2> <state>`.** Every register is read twice with a different prime (`0xC0DE00nn` then `0xD1CE00nn`, `nn` = the row), so: both primes back = `03` **the destination was not written**; the two disagree and neither is a prime = `04` **the register changed between the reads**; one prime and one not = `05`, unexplained and reported as its own state. 🔴 **Until 2026-08-25 a trapped row's `v` carried the running `zeros` counter** -- a steadily increasing small integer that reads like a family of related registers answering, and this cell's instruction was to transcribe that column. 🆕 **The UART prints every select-0 row plus any select != 0 row that DIFFERS from its own register's select-0 row**, capped at 96 with `rows.suppressed` beside it. 🔴 **`rows.printed=00000020` is NOT the select answer, and that sentence was wrong — corrected 2026-08-25 before the seating.** The predicate compares `(v1, v2, state)` against the register's own select-0 row, and **a register whose value CHANGES between the two reads cannot equal its own earlier row**, so it prints all eight of its selects on a core that ignores select entirely. The arithmetic is `rows.printed = 32 + 7 × (registers in state S_MOVES)`. 🔴 **And at least one register is expected to move, which is the point**: `Random` is **rd 1**, row `0x08`, and on an R3000 it free-runs downward — `CPU-08` has 32 TLB entries **量**, so the TLB is real and `Random` is real. **Row `0x08` reading `04` S_MOVES is the DEVICE-side positive control on the whole S_MOVES mechanism**, and without it `count.row48` reading anything other than `04` is unfalsifiable: qemu's `0x48` = S_MOVES is a control on qemu, not on this silicon. So the honest predictions are `rows.printed = 00000027` (39) if `Random` alone moves, `0000002E` (46) if `Count` moves too, `00000020` (32) only if **nothing** moves — which would itself say the TLB's `Random` is not free-running and is worth more than the select answer. The select question is answered by **which** rows print, not by how many |
| **H2e** 🔄 | `count.spins` / `count.before` / `count.after` / `count.delta` / `count.traps` / `count.row48` | 🔴 **`delta = 00000000` was written here as the expected answer and that was the defect, not the value.** It is still the expected answer -- an R3000-class CP0 has no `Count` -- but until 2026-08-25 the routine read `Count` into two uninitialised registers, so on a core whose `mfc0` does not write `rt` the delta was `(the loader's leftover $t7) - 0xA0500150`: **a large residue-arithmetic number that reads as this cell's own refutation.** Both destinations are primed now, with DIFFERENT values (`C0DE0009` and `D1CE0009`) because priming both with zero would have made the instrument's failure wear the result's clothes. **Read `count.before`/`count.after` first**: if they are those two constants, `mfc0 $9` delivered nothing and the delta is arithmetic on primes | `F50b`. A zero makes **`R5-0`'s SoC timer driver a prerequisite rather than a bonus**, and `R1c` loses its first timing route. 🆕 **Two independent cross-checks, and neither existed before**: `count.traps` brackets the call the way the census brackets its stubs, and **`count.row48` is census row `0x48` -- rd 9, sel 0, the same register through the same instruction on a different path.** If row `0x48` is `02` (trapped) or `03` (not written), `count.delta` is residue arithmetic and **`F50b` is answered by the row, not by the delta**; the payload prints that verdict itself rather than leaving it to the reader. And if row `0x48` is `04` (`S_MOVES`), `Count` is running and the R3000 expectation is refuted by two reads that need no arithmetic at all |
| **H2f** 🔄 | `restore.mismatch` **and `restore.stillhandler`** | both `00000000`, **and `restore.mismatch` now covers all 64 words of both vectors** | that part of the loader's general vector is back. 🔴 **This control is narrower than its name, and the name was the defect.** `probe2` writes 22 words into **both** vectors and saves 32 words of each; the check reads back **8 of those 64**, and it never reads `0x80000000` at all -- the vector `notes/cache-model.md` records the loader as never having populated, and the one a faulting kuseg load goes to. It is also `field()` only: **it is not in the result block**, so alone among the `H2` cells it has no RAM channel. The check that does cover both vectors is `H2h`, and it is free. ✅ **2026-08-25: the 8-of-64 half is fixed here as well** -- `restore.mismatch` reads all 32 words of BOTH vectors back through KSEG1, and it is in the result block at word 28. 🆕 **`restore.stillhandler` is the leg that was missing**: of the words the install demonstrably CHANGED, how many still hold OUR handler. A check whose failure mode is *the value is unchanged* needs a companion whose failure mode is *the value is still mine*. The `changed` guard is not tidiness -- **seven** of the device handler's **22** words are `nop`, and counting every coincidental match returned 20 on a qemu run whose restore was perfect. 🔄 **"ten of 22" was true of neither build** and is corrected 2026-08-25 from the emitted images: the device build is `rlx_exc_end - rlx_exc_entry` = `0x58` = **22 words, 7 nops** (`jr $26` / `rfe`), the qemu build is **25 words, 10 nops** (`mtc0` / nop / nop / `eret` / nop). The 20 came from the qemu build, so the number and the build it belongs to had been separated. **What neither can do is tell you whether `saved_vec` itself is right**, and nothing in this payload can; `H2h` cannot either, because the watchdog reset re-runs `trap_init` first. 🔄 **The instruction to stop the seating here is withdrawn**: `RESET` defaults to 1 and `start.S` calls `rlx_reset` the instant `main` returns, so the loader never regains control before the reset and `trap_init` has re-run before anything after this is typed |
| **H2g** 🔄 | after the watchdog reset: `DW 80A01000 40`, then as much of the census as is worth reading. The whole block is `DW 80A01000 809` = **9,567 bytes, 2.49 s** (`tools/reply-size.py`) | `magic=524c5832` at word 0, `nonce=3ab0e572` at 1, **`progress=00000090` at word 2**, `flags=50010002` at 5, the counts at 16-21, `count.*` at 22-27, `restore.*` at 28-29, and the eight saved GENERAL-vector words at 32-39 | the same two-channel agreement as `H1c`. 🔄 **40, not 24, and the reason is better than the old one.** The header is 40 words now and **word 2 is a monotone progress marker** -- `0x10` header written, `0x20` past the `BEV` gate, `0x30` vectors saved, `0x40` installed and read back, `0x50` `break` returned, `0x60` census done, `0x70` count done, `0x80` restored, `0x90` sealed. **A block recovered after a hang says where the run stopped instead of leaving it to be inferred from what is missing**, and it replaces the `0xBE71BAD1` refusal marker outright: a `BEV` refusal is `progress=00000010` with bit 22 set in `status` at word 6, which is two independent signals rather than one magic number. Poison (`DEADC0DE`) at word 2 means it never reached the header at all. The block is 809 words; **the poison margin runs eight words past it**, so a run that wrote past its own block shows data where poison was predicted. 🔴 **Corrected 2026-08-25: the command has to be `DW 80A01000 817`, not `809`, or the margin is 3/8 delivered.** `RB_POISON_W` is `RB_WORDS + 8` = 817; `LDR-07` rounds `809` up to **812** printed words, which shows only 809/810/811 of the eight. `817` rounds to **820**, so it shows all eight margin words **and three words past the poison loop's own end** — un-poisoned DRAM where poison stops, which is the positive control on the poison: a loop that ran too far would show `DEADC0DE` at 817–819 and there would be nothing to say it had. `9,661` bytes / 2.52 s against `9,567` / 2.49 s (`tools/reply-size.py`), so the whole correction costs **94 bytes and 24 ms** |
| **H2h** 🆕 | after the reset: `DW 80000080 32`, then `DW 80000000 8` | byte-identical to `H0a` and `H0c` | 🔴 **the check `H2f` cannot make.** `H0a` and `H0c` establish the before-state at zero risk, so comparing against them after `probe2` is the only reading in this session that covers **both** vectors and all 32 words rather than 8 of 64. Two read-only commands, and the baseline is already being taken |

### H3 — the ride-alongs, which cost nothing once the board is up

| | command | expected | what it refutes |
|---|---|---|---|
| **H3a** `C-17` 🔄 | `console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out <dir>/H3a --send 'J BFC00000' --esc-after 20 --seconds 45`, then `flush-h3a` (`--send '' --seconds 2`), then `DW 81000400 16` | 🔴 **the deciding grid.** After a warm reset with no kernel run since, `0x81000400` should hold **bias garbage**, not the 32-byte-periodic structure. If the structure is there, it was not the vendor kernel that wrote it | `C-17`'s remaining half -- *which execution wrote that structure*. `MEM-15` is why the question is live at all: a seconds-long power-off keeps contents, so *it was there* never meant *something just wrote it*. 🔄 **immediately is withdrawn**: the capture ends on ESC and not on a CR, so seating rule 2's flush goes between -- that is the fault `D2` was lost to. ⚠️ **And this reset is redundant with `H1b`'s**: `rlx_reset` writes the same `WDTCNR = 0` this command's path does, so `H1`'s reset already produced a warm reset with no kernel run since. Kept because it is one command; it is the first thing dropped if the seating runs long. The expected value is also a weak pass -- after a long power-off `MEM-15` predicts garbage there whatever `H3a` does |
| **H3b** `NET-13` | four cable moves, one capture each, **the jack written into the `--out` filename**: `--out <dir>/E13-jack1`, `…-jack2`, `…-jack4`, `…-jack5`. Each is 🔄 **`DW BB804128 8`** (`PSRP0`–`PSRP4`, **118 bytes**, 2 lines) with only that jack populated. 🔴 **This row said `DW B8003250 8` until 2026-08-25, and that address exists nowhere else in this repository** — `SPEC.md` `NET-10`/`NET-11`/`NET-12`, `docs/loader-phy-and-switch.md` §7, `bench/README.md`, `docs/loader-command-semantics.md`, **this file's own `E10` row**, and the eight captures of 2026-08-24 all read `0xBB804128`. **It would not have failed visibly**: `0xB8003250` is inside the SoC register window, so `DW` returns eight plausible words and four cable moves would have measured something else. Caught at the bench before it was typed; the same defect class as `43ec0e0`'s four | one port's bit 4 set per capture, and **the filename is the label** | 🔴 **that the jack map is derived from anything but the filesystem.** It has gone wrong twice: once from labels assigned after the fact, once from an expected value derived from the very map the cell was testing. Jacks 1 and 5 are where the old map and the linear map disagree, so those two alone would settle it — the other two are the control. ⚠️ 🔄 **Runs after `H1a`'s `put` and before `H3a`/`H3c`** — it said `H2a` while there were two uploads; `H2` is deferred to `R1g-4b` and `H1a` is now the only one. The upload goes over the link these four moves disturb, and a stale neighbour entry cost `G4-put` three retransmits and 8.935 s (*量*). Flush the host's neighbour entry for `10.1.1.1` after the last move if anything else on the seating still needs the network |
| **H3c** `CLK-08b` | re-run `D4` and `D4c` with **`--esc-period 0.002`** | the same two `OVSEL` points, on a **2.32 ms** grid instead of a 20.35 ms one — and `esc.achieved_period_s` in each capture's `.meta.json` says which grid it actually got | 🔴 **whether the watchdog's residual is fixed or proportional.** The two hypotheses differ by ~15 ms, which was smaller than one tick of the old grid. **Do not run a third `OVSEL` point** — `OVSEL=0111` predicts 286.2 ms proportional against 263.6 ms fixed, 22.6 ms apart, which the old grid could not separate either |

### What this session cannot tell you, stated before it runs

- **`probe1` measures which flush works on this die.** It does not measure why,
  and it licenses no statement about the Lexra family.
- **`probe2`'s `ZERO` state is three things at once.** A CP0 read that returns 0
  without trapping does not distinguish *implemented and zero* from *not
  implemented and the bus returned zero*, and nothing in the payload can. It is
  reported as its own state rather than folded into either.
- **Neither payload measures a hazard or a time.** Both need a controlled loop
  and `R1b`'s harness, and a number produced without them would be a number.
- **The qemu runs prove control flow and nothing else.** qemu interlocks the load
  delay slot and this core does not. An emulator kinder than the device certifies
  exactly the bugs the device rejects — which is how `P9-12` was certified by its
  own simulator the day before it failed on this silicon.
- 🆕 **`CPU-25` is not measured this seating.** `GEOM=0`, so the cache-sizing
  walk does not run, and cache size, line size and associativity stay blank. That
  is a choice — `GEOM=1` writes 1 MiB of real memory at `0x80B00000` if this core
  does not implement `Status.IsC`, and this sheet has no before/after read of that
  window — but it is a choice this sheet did not previously state.
- 🆕 **Neither channel records which build produced it.** `RLX_NONCE` is a source
  constant, identical across every build of a payload, and `FLUSH_ISC` appears in
  no header word, no `field()` and no banner. *Which flush this census was taken
  under* is answered by the `sha256` recorded at build time and by nothing the
  device sends. Keep the two `probe2` binaries in separate directories for that
  reason alone.
- 🆕 **Whether the loader's `J` flushes the caches is not established.** Only the
  `J BFC00000` special case has been disassembled. It does not block this session:
  upstream's `P9-12` ran a TFTP-delivered payload from `0x80500000` on this unit,
  which empirically excludes the dirty-D-cache delivery failure — but that is one
  instance and not a control.
- 🔴 🆕 **`CPU-04`, `CPU-27` and `F50b` are not answered this seating, and that is
  a decision rather than a gap.** All three live in `H2`, which is deferred to
  `R1g-4b` — see the box at the head of `§H2`. So `PRId` stays *undetermined*
  (**do not write `RLX5281`**), `Status.BEV` at the prompt stays *讀, one source*
  (`0x80406694`, `docs/loader-phy-and-switch.md` §2 — which is more than the blank
  `SPEC.md` `CPU-27` carried until today, and less than a measurement), and
  whether `R5-0`'s SoC timer driver is a prerequisite stays open. **`R1-gate` does
  not close on this seating.** `R1d` can; `R1e` cannot.
- 🔴 🆕 **`probe1` carries one known power-cycle defect into this seating,
  knowingly.** `CELLS[]` runs cell 4 — the `Status.IsC` path, the only cell with
  a demonstrated kill (qemu, 2026-08-25) — **third**, ahead of cells 2, 3 and 6,
  whose `mtc0 $t,$20` this unit's own loader executes five times on every
  power-on. `probe1.c` argues both orderings in two different comment blocks.
  It is carried rather than fixed for three reasons: the qemu kill's mechanism is
  already caught by the `V_CORRUPT` guard, which did not exist when it happened;
  rows 0–3 — cell 1, cell 5, **the negative control and the write-back
  discriminator** — are banked before cell 4 runs; and **`rlx_isc_inv` is entered
  with `$a0` = the victim address, which `cache.S` §SAFE_A0 argues is a real word,
  so a fault there prints and hangs rather than double-faulting silently.** That
  last property is exactly what `rlx_do_break` lacks and is the line the `H2`
  deferral was decided on. **If `H1b` stops after row 3, that is this defect**, and
  `H1c`'s `DW 80A00000 137` still recovers rows 0–3 and the discriminator.
- 🆕 **The audit that produced these two entries is itself incomplete.** 47
  findings, **21 put to an adversarial refuter (10 refuted), 26 not** — the
  verification stage died on a session limit. The `H2` findings above were
  re-checked by hand against the emitted binary; `docs/rlxprobe-audit-2026-08-25.md`
  marks every finding that is still single-source. **Nothing in it was measured on
  the device**, and its one load-bearing unverified link —
  `exception_handlers[9] == 0x80400BE8` — is measured by `H0b`, third cell of this
  seating.

## Results — seating 2 part three, 2026-08-24

**Five power cycles, `bench/2026-08-24c` / `d` / `e` / `f`, 81 captures, 18
prediction blocks — **17 pass `tools/check-predictions.py`; `block12` fails, and
correctly so** (nine of its ten cells never ran when the `24e` ESC window was
missed, and were re-run as `24f`/`block13`, which passes 10/10). **Every capture
that exists postdates its own prediction file** — 81 of 81, minimum margin
**+7.7 s**. **no flash-write command issued in 81 captures**, and the loader head and `cr6c` header byte-identical to a same-session pre-boot baseline across three kernel executions — **512 of 4,194,304 bytes re-read, 0.012 %**.** `R0` closes here.

Instrument: `console-capture.py` **1.2** for every cell;
`upstream/tools/console-dump.py rescue` and `loader-tftp.py` for `§G`'s network
steps. Two power cycles were spent on missed ESC windows — the two rows at the
bottom are the record of why.

### `§F` — closed, and the expected finding was backwards

| cell | reading | verdict |
|---|---|---|
| **F1** | `PHYR 5 2` → `PHYID=0x00000005, regID=0x00000002 ,Find PHY Chip! UID=0x00000000`, **87 bytes**, the predicted count | ✅ **it returns.** The load-bearing inference holds: an MDIO read of an unpopulated address **completes** — `MDCIOSR` bit 31 is the controller's completion flag, not the PHY's acknowledgement. 🔴 **The mechanism detail is refuted**: the argument said `0xFFFF` *"from a bus pulled high"*, and the answer is **`0x0000`**. So this part does not pull the MDIO data line high, or the controller zeroes when nothing drives the ACK — and that is the test a driver would use to detect an absent PHY |
| **F2** | `MDIOR 2` → **32 lines, 1042 bytes**, size accounted for to the byte. Addresses `0x00`–`0x04` → `0x001c`; `0x05`–`0x1f` → `0x0000` | ✅ **`docs/loader-phy-and-switch.md` §6's pre-visit prediction confirmed on 32 points**, split exactly on the boundary the datasheet names. **The built-in refutation had a real chance and did not fire**: two distinct values, not one, so the bus is not echoing. `F1` and `F2` agree on address 5 across two commands and two format strings. 🔴 **The sheet expected the finding *"`MDIOR` must never be run on this part"*; the opposite is true, and `MDIOR` is now the cheapest full PHY-address sweep available — one command instead of 32.** Format-string correction: §3's table says `Reg=%02d`, silicon renders `Reg=2`, so it is `%d`; `PhyID=0x%02x` and `Data =0x%04x` confirmed exactly |

### `§D` — and `C-8` closes on something better than the register it was waiting for

| cell | reading | verdict |
|---|---|---|
| **D0a / D0b / D0-rb1 / D0-rb2** | 40 / 40 / 71 / 71 bytes; `81000000: DEADBEEF CAFEBABE 34361357 AB2563FB`, `80A00000: 5EA72D2B A5A5A5A5 13344D3C A1573115` | 🆕 **the two readbacks are added, and they close a hole `§D` had**: `D0a`/`D0b` both expected *silent*, and a silent `EW` cannot be told from a refused one. Words 3–4 are the free control — `EW` wrote **two** words, not four |
| **D1** | `---Jump to address=BFC00000`, silence, stage-1 boot text; **1363 bytes**, `cr.esc_after.prompt_seen: true` | ✅ the warm reset happened and the ESC window came back |
| **flush-d1** | **11 bytes, bare prompt, no `Unknown command !`** | 🔴 **1.2's on-silicon control, and its expectation is inverted from what this sheet carried until today.** `D1`'s capture consumed its own residue. Under 1.1 this would have been 31 bytes. The suite proves what the tool *writes*; only this proves what the loader *did with it*. Reproduced by `flush-d3` and `flush-d4c` — **three independent instances** |
| **D1b** | **0.592 s**, jump → banner | the post-reset boot, which is what `C-8`'s owner actually needs. **Not** the watchdog timeout: `OVSEL=0000` is 163.8 µs undivided / 2.29 ms divided, both far under this instrument's floor |
| **D2 / D2d** | `DW B8003110 1` → `C0000000 80000000 000E0000 A5000000`, twice. **The word that matters is the 4th, at `0xB800311C` = `WDTCNR`** — `0xB8003110` is the dump line's base and is `TCCNR` | 🔴 **`WatchDogIND` bit 20 is CLEAR** after both a `J BFC00000` reset and a real timeout. `D2`'s predicted `A5100000` is refuted — **the bit does not survive to the prompt**, so `C-8` cannot use it. *推*: the loader reads and clears it, because it prints the line below |
| **D-CLK** 🆕 | `Reboot Result from Watchdog Timeout!` in the warm boot text, where the cold boot prints **a single space**. Three instances (`D1`, `D4`, `D4c`) | 🔴 **`C-8` closes on the boot text.** And it reads a **hardware** bit, not a software flag on `J BFC00000`'s path: `D4`/`D4c` armed the watchdog with `EW` from the prompt and the loader executed nothing afterwards, and the line still appeared. Free, in every capture, no register read |
| **D2b / D2e** | `00000144 CAFEBABE …`, then `00000144 CAFEBABE …` again after re-arming word 1 with `F00DFACE` | 🔴 **`0x81000000` word 1 is written `0x00000144` on every boot** — three reproductions counting `X3-24d`'s cold read. Word 2 survived both resets, so it is not decay. **`D2b`'s address was a bad choice; `MEM-14` owns the finding.** It also re-reads an earlier number: in the 1 KiB-periodicity check word 1 was the outlier at **13/32 bits** against 4, 0 and 3 — recorded as noise, and it was signal |
| **D2c / D2f / D2g** | `5EA72D2B A5A5A5A5 13344D3C A1573115`, **three times** | ✅ the canary survived **three** warm resets byte-exact. `C-8` gets its second discriminator — **at `0x80A00000`, not `0x81000000`** |
| **D4 / D4c** | timeout ∈ **1122.5–1149.9 ms** (`OVSEL=1001`) and **549.6–577.4 ms** (`OVSEL=1000`) | ✅ **`CLK-08` filled, and the divided/undivided choice is not in doubt** — computed 1174.376 / 587.188 ms, against an undivided candidate of 83.9 ms, 14× away. 🆕 **An independent confirmation that uses no timestamp at all**: the two captures echo **56 and 28** ESC bytes, exactly 2.000, which confirms the split-field `OVSEL` decode of `0x240000`/`0x40000` on its own. 🔴 **The residual's *shape* is undetermined and this experiment cannot settle it** — proportional predicts `D4c`'s shortfall is half `D4`'s, fixed predicts equal, and the two differ by ~15 ms, **under the 20 ms heartbeat grid**. A single fixed lag `L ∈ 24.5–37.6 ms` fits both points as well as a scale factor does, and this sheet's own prescribed estimator (`D4 − D1`, boot cancels) gives shortfalls 37.2 / 24.9 ms, ratio **1.495** — nearer fixed's 1.00 than proportional's 2.00. **Deciding experiment is a finer heartbeat, not a third `OVSEL` point** (`SPEC.md` §17). *(An arithmetic slip went out with the first draft of this row and is corrected here: "a fixed lag would give 0.975 and 0.952" is wrong — `L` = 29.4 ms gives **0.9750** and **0.9499**, and no single `L` produces that pair at all.)* |
| **D3** | ⛔ not run, retired 2026-08-24 part two | — |

**New instrument, free**: the ESC echo stream is a **20 ms-resolution heartbeat**
— the loader echoes each ESC and the echoes stop the instant the board dies.
That is what made the watchdog measurable at all; an interval taken to the banner
conflates the timeout with the boot. `D4`'s last echo landed at t=1.159 against
the command executing by t=0.014.

🔴 **Reset → first console byte was published here as 340 / 348 / 345 ms and that
was a measured quantity wearing another one's name** — the exact failure `D1b`
exists to prevent. Those three numbers are real but they are the loader's
**silence after `Booting...`** (`CLK-15`, 344.7–356.9 ms over n=9, cold and warm
alike), which *begins after console output has already started*, plus one
`0xFF`-to-`Booting` interval. It contradicted this sheet's own `D1b`: 0.592 s
minus the 0.583 s `Booting`→banner leaves ~9 ms, not 348 ms. **Measured
properly**: reset → first console byte is **2.07 ms** on `D1` (exact, same
capture) and **≤21.1 / ≤19.2 ms** on `D4`/`D4c` (upper bounds set by the 20 ms
heartbeat). **Cold power-on is not measurable** — no reset timestamp exists in
the file. **R4's `bench-ci` should set its timeout from reset → prompt** (2.24 s
on `D1`, 2.81 s on `D4c`) with margin, not from any 345 ms figure.

### `§G` — R0 closes

| cell | reading | verdict |
|---|---|---|
| **G0-head/mid/tail** | 48 words at `0x80A00000`, `0x80A78000`, `0x80AF1000`: no aligned pointer, no self-reference, no period | the upload address stands. 🔴 **But the test only means this after a *long* power-off** — see `MEM-15` |
| **G1a / G1b / G1c** | `00000000 00008021 40906000 00000000` · `9D7111B4 08ABB9AE 978855A8 E63174AD` · `00000000 00000000 00000000 00000000` | ✅ **all three match the payload file**, so the loader had already staged the whole 964 KiB and `G6` runs. 🔴 **Today made `G1c` a much stronger test than when it was written**: uninitialised DRAM here is high-entropy garbage, so sixteen zero bytes can only have been written |
| **G8-pre** 🆕 | flash `0x000000` and `0x060000` through `FLR`+`DW`, **128 words all matching the dump** | 🆕 **added today, because `§G` had no flash baseline before its first kernel boot.** `G8a`/`G8b` compared against a dump taken on another day; now they are same-session `cmp`s. `FLR` is allowed only here — it writes the TFTP length global, so no transfer may follow it |
| **G6** | full vendor kernel boot from RAM to `boa: starting server pid=350, port 80`. **62 lines compared against `uart-boot.log` from `decompressing kernel:` onward, 62 identical, 0 differing — and byte-exact, 1687 of 1687 bytes.** 🔴 *(This read `63` until the refutation audit: `str.splitlines()` breaks on the bare CR before `init started:` and invents a line. The only 63-line window starts one line earlier and contains the one line that **does** differ — `---Jump to address=80500000` against the autoboot's `Jump to image start=0x80500000...`, which is exactly why the window starts where it does.)* | ✅ the reference exists. Unasked: **ping `10.1.1.1` 2/2 at 1.9 ms** — the RAM-booted kernel reached userspace and answers, which is more than the cell needed |
| **G2 / G2-rb** | `AutoBurning=0` · `Set TFTP Load Addr 0x80a00000` · `Now your Target IP is 10.1.1.1`; then `8040D4A0` = **`00000000`** | ✅ the guard passes, read at the one instruction the burn path uses |
| **G4** | 987,138 bytes up in 1929 blocks, back down, **`cmp` byte-identical**, sha256 `396561a0…45a03e90` | ✅ the transport, proved without executing anything |
| **G5-poison1/2/3 + G5-pv1/2/3** | `5A5A5A5A` at each, words 2–4 untouched | 🆕 **the verification is added, and it closes the same hole `D0-rb` did.** `G1` had shown the correct bytes were already there, so without it *"`5A5A5A5A` was overwritten"* could not be told from *"the poison never landed"* — the cell would pass with no packet arriving |
| **G5-rb1/2/3** | the dump's own bytes back at all three points | ✅ **it landed where it was told**, across 964 KiB, which `G4` structurally cannot test |
| **G8a** | `AUTOBURN` `00000000`; both regions **byte-identical to `G8-pre`** | ✅ nothing wrote the two regions across two kernel boots and two uploads |
| **G7** | 🔴 **`G7.log` is byte-identical to `G6.log` as a whole file** — 1789 bytes, sha256 `2f921f75…0712070` on both, `cmp` clean. Stating it as a line count understated it | 🔴 **R0 closes.** The device executed an image delivered over the network. The ping failed at first and that was **stale ARP, not a failed boot** — after `ip neigh del`, 2/2 at 3.6 ms |
| **G8b-ab** | **`00000001`** | 🔴 **the positive control on `G8a`'s ordering.** *"Every reset puts `AUTOBURN` back to 1"* had been an argument from the image's initialiser plus `B6`; this makes it a measurement, and it confirms `G8a` had to be read when it was |
| **G8b-rd0 / rd6** | **byte-identical to both `G8a` and `G8-pre`** | ✅ nothing wrote the loader head or the `cr6c` header across **three** kernel executions and two uploads |

🔴 **What R0 may claim, and what it may not.** Entitled: the vendor kernel booted
from RAM from bytes delivered over TFTP to an address poisoned first and verified
at three points across 964 KiB, with `AUTOBURN` measured `00000000` at the
instruction the burn path reads, during the transfers; and the loader head and
the `cr6c` header unchanged against a baseline taken before any kernel executed
this session. **Not entitled**: *"zero flash bytes written"* — the three flash
blocks reach **512 bytes of a 4,194,304-byte part**.

### The ARP finding, and it is an R4 requirement

`G4-put` took **10.46 s** with **3 retransmits**; `G5-put` took **1.52 s** with
**0**. 3 × the 3.0 s TFTP timeout = 9.0 s, against a measured difference of
8.935 s. **The loader synthesises its MAC from the IP it was given** — the
neighbour entry reads `56:0a:01:01:01:e8` for `10.1.1.1` — while the vendor
kernel uses the real one. A stale entry from the other side costs the first
transfer three retransmits, and after `G7` a stale *loader* entry broke the ping
outright until it was flushed. **Confirmed in both directions.** R4's unattended
`bench-ci` must flush the neighbour entry at every loader↔kernel transition.

### Two power cycles lost, two different causes, and only one of them is human

| | what happened | cause |
|---|---|---|
| **1** | the operator was told to re-plug **first** and then say so, which puts the ESC stream after the window | 🔴 **sequencing, and it was mine.** Fixed: the capture starts first |
| **2** | capture started first and correctly, ESC ran 45 s, **the boot began at t=64.2 s** — nineteen seconds after the stream stopped. `bench/2026-08-24e/A-catch.meta.json` records `prompt_seen: false` with a full 3-second settle | 🔴 **window length — a procedure defect, not an operator one.** The cost is wildly asymmetric: an extra ESC second is free, a missed window costs a power cycle. **Standing change: `--esc 180 --seconds 200`** |

`bench/2026-08-24e/A-catch` is kept: it is the first capture here that shows what
a missed ESC window looks like from the instrument's side, and
`cr.prompt_seen: false` beside a full settle is the signature. **That field
exists because the completeness critic of the 1.2 review demanded that "never
looked" and "looked and saw nothing" not share a value** — case `N14`, written
hours before it was needed.

**Free and unasked**: the boot region is **byte-identical across the three power
cycles where it was completely captured** — `24c`, `24d`, `24f`, 181 bytes each.
🔴 *(This read "five consecutive" until the audit. `24e` stops 63 bytes short with
no `<RealTek>` in the file at all — the missed window, which this same section
records four paragraphs above — and the fifth cycle produced no boot capture.)*
`A0` is byte-identical across `24c`, `24d` and `24f`; and the vendor
kernel's console echoes control characters as the literal two-character sequence
`^[` (canonical mode with `ECHOCTL`), which is how a kernel console is told from
a loader prompt in a transcript without sending anything to it.

---

## Results — Session B4, `R1g-4a`, 2026-08-25

**One power cycle, `bench/2026-08-25/`, 26 captures, 10 prediction blocks —
26 of 26 captures postdate their own prediction file**, minimum margin **+7.9 s**,
`tools/check-predictions.py` with its four controls passing on every block.
**Zero flash bytes.** Every command sent this seating, enumerated from the
captures' own metadata rather than from the logs: **22 `DW` reads, two `J`, two
`EW` — and both `EW`s are `B800311C`, the watchdog register.** A scanner for
`FLW` / `AUTOBURN 1` / `EB` / a flash-range `EW` returns 0 over all 26 and fires
on a planted line.

`H2` did not run and was never intended to: this is `R1g-4a`.

### The gate closes on `R1d`, and the negative control is why it is allowed to

| cell | verdict | reading |
|---|---|---|
| **1** — no treatment, stored **cached** | `01` STALE ×2 | 🔴 **the refutation condition holds.** `ex=000011a1` — the OLD constant executed — while `ma=240222b2`, the NEW word, is in memory. Both victims, 7 KiB apart, so eviction has to explain both |
| **5** — no treatment, stored **uncached** | `01` STALE ×2 | same, through KSEG1 |
| **4** — `Status.IsC`/`SwC` | 🔴 `07` CORRUPT ×2 | see below |
| **2** — `CCTL 0x002` alone | `02` FRESH ×2 | the I-invalidate took |
| **3** — `CCTL 0x200` then `0x002` | `02` FRESH ×2 | so did the vendor's sequence |
| **6** — `CCTL 0x002`, stored uncached | `02` FRESH ×2 | and so did it with the store out of the way |

**And it is the opposite of the qemu run**, which returned FRESH on cells 1 and
5 because TCG invalidates a translation block when a store lands on translated
code. §H1 wrote that down before the seating: *a device run that looks like the
qemu run is the run that refutes the experiment*.

### `ma` on cell 1 against cell 5: a cached store reaches memory unaided

🔄 **This section was headed *"the D-cache is write-through"* until 2026-08-26.
The reading below is unchanged; what it licenses is narrower than the old
heading said.**

Both read **`240222b2`** — row 1 of §H1's four-way table. The cached store
reached memory with no treatment applied, so **the only stale thing this seating
found on this core is the I-cache**.

> 🔴 **What the pair cannot separate, 2026-08-26.** In **both** cells the store
> landed on a word that had been **executed and never loaded** — a D-cache
> **miss**. Under a miss, *write-through* and *write-back that does not allocate
> on a write miss* produce the identical `ma`, and §H1's four-way table above has
> no row for the second because it was written as a two-way question.
> `notes/cache-model.md` carried the disjunction from day one and every
> restatement dropped it. **And both GPL drops' `boards/rtl8196e` configs carry
> `CONFIG_ARCH_CACHE_WBC=y`** — write-back; one vote, not two, since the drops
> share an ancestor.
>
> **The consequence is a decision, not a nuance.** A descriptor ring is *load the
> status word, then store the ownership bit* — **a write hit on a resident
> line**, which no cell here exercised. So `R1-gate`'s decision ② is unanswered
> in **both** directions. The cell that decides this one is `R1h`'s **cell E**:
> store to a line the CPU has just loaded, then read it back uncached.

🔴 **What that cancels.** `docs/rlxprobe-audit-2026-08-25.md` §5 carried
`V_NOSTORE` conflating two physically different states, and its consequence: in
the write-back case **cell 2 against cell 3 would have measured the D-flush and
not the I-invalidate**, and *"invalidating I alone is insufficient on this core"*
would have gone into `notes/cache-model.md` and then into `R5b`'s MTD driver as
the flush recipe. The case did not arise — **and what made it decidable was a
table the audit put in the sheet rather than a verdict it put in the binary.**

### `CCTL 0x002` alone is sufficient; the vendor's D-then-I is unnecessary, not wrong

Cells 2, 3 and 6 all FRESH, guards intact. **For the store these cells make**
there is nothing for `0x200` to write back — 🔄 **and *for the store these cells
make* is the narrowing added 2026-08-26**: all six stores are D-cache misses, so
this says nothing about a store that hits a resident line. `PROGRESS.md` `R1g-1` wrote the entitled wording
before the payload existed — *"a write-through D-cache makes 2 and 3 agree, so
the vendor's D-then-I sequence would be **unnecessary rather than wrong** — a
result, and it has to be written as one"* — and this is that result.

**Decision 1 of the four this gate exists to unblock is answered: `R5b`'s MTD
driver invalidates I through `CCTL 0x002`.** The D-flush is belt and braces on
this die, and the write-up may not upgrade that to *wrong*.

### `Status.IsC` does not isolate on this core, and it destroys memory

```
victim   240222b2 -> 000222b2        guard   03e00008 -> 00e00008
                ^^                               ^^      the top byte of each word, stride 4
```

`cache.S`'s `rlx_isc_inv` sets `Status |= ISC|SWC`, clears `IEc`, and its only
memory reference while isolated is `sb $0, 0($4)` walking by 4. On a core that
isolates, those byte stores write cache tags. **Here they wrote DRAM**, and
big-endian byte 0 is the MSB. `V_CORRUPT` on both victims; the payload survived
and completed the remaining six cells.

- qemu found this exact failure on 2026-08-25, **one day before the bench**, and
  the guard it produced is what turned a jump into the weeds into a printed
  verdict.
- `PROGRESS.md`'s stop-loss anticipated the reverse — *"`mtc0 $t,$20` faults ->
  the `Status.IsC` path becomes the only route"*. **`CCTL` works and `IsC` is the
  broken one.**
- It retro-justifies `GEOM=0`: `GEOM=1` writes 1 MiB at `0x80B00000` **if this
  core does not implement `Status.IsC`**, and it does not.
- **What is measured is behaviour, not bits.** Stores issued while `IsC` was
  set reached memory. Whether the two `Status` bits are implemented, and whether
  `mtc0` wrote them, needs a `Status` read-back — that is `probe2`, `R1g-4b`.

### Two channels, and the block on both

`H1b`'s report is **1,543 bytes**, the byte count §H1 computed as
`32 + 144 + 13 x 104 + 15` before the run. `H1c` is **1,671 bytes / 140 words**.
The 104 row words agree **104/104** between the UART report (lower case) and the
RAM block (upper case), with a one-word shift as the negative control; header,
`seq=0000000d`, `sum=914fd3ef` and the poison at words 112–135 and 137–139 all as
written in advance.

### `H0` — six reads that turned a document into a measurement

| | |
|---|---|
| `H0a` | **32/32 words identical** to the list pre-registered at 06:09. 🔴 **The general exception vector is populated at `0x80000080`.** Three sources said so; it is now measured |
| `H0a2` | `DW 8040054C 32` — **word for word identical to `H0a`**, so `trap_init`'s 128-byte copy landed intact, including the twenty-one words nothing in this repository had predicted. 🆕 **And `DW` does not align its start address down**: the first printed address is `8040054C`, not `80400540`. That is new about `LDR-07` and it was an open question in the block-0 file |
| `H0a3` | `DW A0000080 32` — identical, and the first printed address is `A0000080`. **No stale D-cache line was involved**, and the vector page reads the same through the cached and uncached windows |
| `H0b` | `[0]=80400580`, `[23]=804007C0`, **the other thirty `80400BE8`**. 🔴 **`exception_handlers[9] == 0x80400BE8` — the single load-bearing unverified link under `docs/rlxprobe-audit-2026-08-25.md` § Must-fix 1 — is measured.** The `SAFE_A0` finding on `rlx_do_break` stands at full severity and the `H2` deferral was correct |
| `H0c` | word 0 = **`5A5AA5A5`**, opcode `010110` = 22 = `BLEZL`. **Not `j` (2), not `jal` (3)**, so `cache.S`'s no-demonstrated-brick-path argument holds by measurement. **This is the cell that permitted `probe1` to run** |
| `H0d-a` / `H0d-b` | neither `DEADC0DE` nor `524C5831`/`524C5832`. 🆕 **And cold SDRAM here is strongly biased but not deterministic**: `0x80A00000` came back `55617135 00F73F55 11744D3C E1553515` against `G4-addr-probe`'s `55617135 0077BF55 11744D3C E1553515` — three of four words identical across a power cycle, **word 1 differing in two bits**. *The region looks like noise* is therefore not an authentication; the magic word, the nonce and the seal are |

### `CLK-03` gets its first experiment, and it costs nothing

`Delta = t(first byte after the reset) - t(last byte of "rlxprobe: end")` =
**123.7 ms**, read out of `H1b.timing`, which `--esc-after 60` put in one capture.

| candidate, pre-registered | predicted | verdict |
|---|---|---|
| 400 MHz **and** 3 cycles/iteration | 130.4 ms | **survives**, 5.1 % low, inside this instrument's demonstrated spread |
| 400 MHz and 4 cycles | 172.3 ms | refuted, 1.39x |
| 200 MHz and 3 cycles | 256.2 ms | refuted, 2.07x |

`f/CPI = 1.408 x 10^8` iterations/s. **It measures `f/CPI`, not `f`** — 400 MHz
with 6 cycles is indistinguishable from 200 MHz with 3 — so what survives is the
**combination**.

### `CLK-08b` closes: the watchdog residual is proportional, and the fixed model has no solution

`H3c` re-ran `D4`/`D4c` on a **2.118 / 2.115 ms** achieved heartbeat instead of
20.35 ms.

```
measured   D4 (OVSEL=1001) = 1118.133 ms      D4c (OVSEL=1000) = 557.583 ms
ratio 2.0053                ESC echoes 528 : 262 = 2.0153, using no timestamp at all
```

With `L` the lag and `c` the offset from arming to the prompt's last byte, both
shared by the two cells:

* **fixed lag** requires `L + c = 56.243` from `D4` and `29.605` from `D4c`.
  **No solution.**
* **proportional** — `2^24/(A4+c) = 2^23/(A4c+c)` — has exactly one:
  `c = 2.967 ms`, `f_wdt = 14.9650 MHz`.

🔴 **`c` is not a free parameter and its physical bound is what settles this.**
`c` spans the loader's prompt, which must be *transmitted* before its last byte
arrives: both captures show **10 bytes** between the command echo and the first
ESC, so **`c >= 2.604 ms`**. The solved `c = 2.967 ms` clears that bound by
0.363 ms, which is read latency. The tidy-looking alternative
**15.000 MHz** (`= 200.0049 x 3/40`) needs `c = 0.32 ms` and `c = 1.64 ms` —
**two contradictory values, both below the prompt's own transmission time.**
Excluded.

| | |
|---|---|
| **watchdog base clock** | **14.965 MHz**, +/-0.02 from the bound on `c` |
| prior `CLK-08b` | 14.53–15.26 MHz — narrowed about 35x, and the new value is inside it |
| 🔴 refuted | `f_timer / 14 = 14.2861 MHz`, by **4.75 %**. The timer base is measured to +/-7 ppm, so the gap is about 6,800x its precision. **The watchdog does not count the divided timer clock** |
| undetermined | what integer relation, if any, ties 14.965 MHz to 200.0049 MHz. `/13` = 15.385, `/14` = 14.286, `400/26` = 15.385, `400/27` = 14.815 — **none within 1 %** |
| withdrawn | the 1.495 shortfall ratio. It was the 20.35 ms grid |

### `NET-13` closes, on a map that is not either of the two that were withdrawn

Both withdrawn maps were **position -> port**, and both had their positions
assigned after the reading. This one is **silkscreen -> port**, and every point's
label was stated by the operator *before* its own capture:

| socket, as the case is printed | port | |
|---|---|---|
| WAN | **0** | 量 `E13-pos1-wan` |
| LAN1 | **1** | 量 `E13-posX-lan1` — 🔴 **the socket behind the port `PORT1`'s patch list skips, named for the first time with its label fixed in advance** |
| LAN2 | **2** | 量 `E13-posX-lan2` |
| LAN3 | **3** | 量 `E13-posX-lan3` |
| LAN4 | **4** | 推, by elimination from a bijection with 13 unrefuted chances. The operator declined the fifth move and the entry is marked accordingly |

Every read had **exactly one** port with bit 4 set. **The position map stays
未定** and what it now lacks is one look at the case's printing order — not a
register read. `posX` in the filenames records exactly that gap.

### Two `PSRP` findings that were not on anyone's list

1. 🔴 **Speed and duplex are not gated by `LinkUp`.** A port that has negotiated
   and then been unplugged reads `...E9` — bit 4 clear, **bits 3 and 0 still
   reporting 100M full duplex**. The control is inside a single capture:
   `E13-posX-lan3` shows four previously-linked ports at `E9` and `PSRP4`, the
   only port that has never negotiated this power cycle, at `E0`. **A driver that
   reads speed without reading bit 4 first reports a live 100M link on an empty
   socket.**
2. **Bit 8 read-to-clear, now on a link settling *down*.** `E13-pos1-wan` caught
   `PSRP2` at `000011E9` immediately after its cable was pulled; `E11f-psrp2-empty`,
   with nothing touched between, read `000010E9`. Every prior observation behind
   `NET-11` came from a link settling **up**, where *a second real latch* and
   *the read did not clear it* are indistinguishable. A cable pull into an empty
   socket is the clean version of that event.

Both then survived a fourth and fifth independent test: `E13-posX-lan1` and
`E13-posX-lan3` each **derived** three of five port words in advance from them,
and all six derived words were right.

### `C-17` closes, on two reset paths

`DW 81000400 16` returned bias garbage with **no word equal to its own address**,
after `H1b`'s watchdog reset (`H3a-early`) and again, **byte for byte identical**,
after `J BFC00000`'s ROM-vector reset (`H3a-rb`).

🔴 **The strong form is available and it is not the absence.** On this power
cycle the loader brought up `IPCONFIG` and completed a 19,792-byte TFTP transfer,
and warm resets preserve DRAM. **If `0x81000400` were the loader's network
descriptor pool, that transfer would have built it and it would still be there.**
It is not. So the structure `C7-pre` measured was written by the **vendor
kernel**, and `§G`'s move off `0x81000000` was justified.

🆕 And the same comparison is a retention measurement: **sixteen words of DRAM
power-on bias survived a ROM-vector reset byte for byte** — stronger than a
canary, because a canary is a value someone chose.

### Free controls, none of them planned

* **The 128-byte console line buffer**: `A-catch` echoed `6968 = 128 x 54 + 56`
  ESC bytes — **54 consecutive full lines, zero exceptions**, against `LDR-06b`'s
  previous n=7. The 56-byte remainder was terminated by `console-capture`'s own
  CR, which is `terminate_esc_line` measured on silicon rather than on a pty.
* **`LDR-07`'s reply-size formula**: nine of nine byte counts in block 0, plus
  71 / 1543 / 11 / 1671 / 213 / 118 in the later blocks. Every one predicted.
* **`CLK-13`**: `Reboot Result from Watchdog Timeout!` on four more warm boots,
  and on `H3c`'s two it discriminates — the watchdog was armed by `EW` from the
  prompt and the loader executed nothing afterwards.
* **`CLK-15`**: the post-`Booting` silence at 0.352 / 0.356 s, inside the
  344.7–356.9 ms window, n=9 -> **n=11**.
* **`NET-10`'s three invariant words** `000000E2 / 0000007A / 0000007A`: five more
  reads, and 🆕 **the first on a different power cycle.** The previous eight were
  all one boot, so *invariant across cable moves* and *invariant across boots*
  were the same eight readings until today.

### The first byte of a cold power-on is the instrument's, and it is a timestamp

Block 0 predicted `A-catch`'s first 181 bytes byte-identical to
`bench/2026-08-24c/A-catch.log`. **Measured: byte 0 differs — `0x00` today,
`0xFF` on `24c` — and bytes 1–180 are identical.**

That byte is not the device speaking. It is the receiver's first sample of a line
that is not yet driven, and `0x00` and `0xFF` are the two idle polarities — which
is why two cold starts give complementary extremes where a printed character
would give the same one. **And it is a timestamp**: on both cold captures the
next byte follows **0.340 / 0.349 s** later, while `H1b`'s and `H3a`'s warm resets
show **0.001 / 0.010 s** and no artifact byte at all.

🔴 **So there are two ~345 ms silences around `Booting...`, adjacent, and only one
of them is `CLK-15`'s.** `CLK-15` owns the one **after**. The one **before** is
cold-power-on only. `SPEC.md` `CLK-14` records *"冷上電量不到"* and also records
that a `340 / 348 / 345 ms` family was once mislabelled and re-homed to `CLK-15`
on 2026-08-25. **Two adjacent intervals of the same size is exactly how a number
gets attributed to the wrong span**, and whether that re-homing sent them to the
right one is now a desk question with all nine captures on disk. Not settled
here.

### The prediction that was too tight, twice, and the form that fixed it

`Booting -> banner` was predicted as **0.577–0.590 s** and measured 0.573; then as
**0.573–0.590** and measured 0.5712. **Both were the observed sample range
written as if it were a bound.** Restated as a tolerance derived from `CLK-15`'s
own recorded 3.5 % unexplained spread — **0.567–0.601 s** — `H3c`'s two boots came
in at 0.5712 and 0.5691, inside. The range is now 0.5691–0.590 over n=10.

### What did not close, and it is a decision rather than a gap

* **`R1e` does not close.** `CPU-04` (`PRId`), `CPU-27` (`Status.BEV`) and `F50b`
  live in `H2`, which is `R1g-4b`. **Do not write `RLX5281`.**
* **`CPU-25`** — cache size, line size, associativity — stays blank. `GEOM=0`,
  and today's cell-4 result says what `GEOM=1` would have cost.
* **CP0 register 20's read side** is `00000000`, the first read anyone has taken.
  `rlx_mfc0_cctl` contains exactly one writer of `$v0`, the `mfc0` itself, so
  *implemented and zero* and *destination not written* are not separable by this
  cell — the same limitation `§H2` states for `probe2`'s `ZERO` state. **The
  write side is now measured**: cells 2, 3 and 6 prove `mtc0 $t,$20` has an
  effect, so r20 is at least a write-effective command register that reads 0.
* **Whether the core fetches from `0x80000080`** is `Status.BEV` and no loader
  command reads CP0. `H0a` confirms the copy, not the dispatch.

### Four errors of mine, kept

1. 🔴 **Block 1's six member-1 victim addresses are each one slot (`0x400`) too
   high.** The payload's twelve rows all carry `mb=240211a1`, so `V_NOTVICTIM`
   would have caught a real mismatch and the device was right at every address.
   **The block is not edited** — it has run, and editing it would move its mtime
   past its captures and fail `check-predictions.py`, correctly.
2. Block 3 predicted **214 bytes** and measured **213**: `DW 81000400 16` is 14
   characters, not 15. The formula was right; the arithmetic was not.
3. The first word-level comparator returned **zero words on both sides and
   reported IDENTICAL** — a comparison that could not fail. Redone with a
   positive control (the count must be 32) and a negative one (`H0a` against
   `H0b` must differ).
4. The `^[` sequences in `bench/2026-08-24d/` and `24e` were read first as an
   archive-integrity defect — **wrong** — and then as the vendor kernel's
   `ECHOCTL` echo, which is right and **was already recorded in this file and in
   `LOG.md` on 2026-08-24**. Not a finding; a file this session had not read.

**Both arithmetic errors are in blocks written at the bench and neither is in the
block written at the desk.** `check-predictions.py` verifies *ordering*, not
*arithmetic*. **The reply-size formula should be a tool before the next seating**,
and the count it produces should go into the prediction file from the tool rather
than from a person.

---

## Results — Session B4, `R1g-4b`, 2026-08-25b

**One power cycle, 23 captures, four prediction blocks, zero flash bytes,
`R1e` closes.** `bench/2026-08-25b/`. Every command came from
§ *Running order — `R1g-4b`* or from a tool; nothing was typed from memory.

`tools/check-predictions.py`: **16 of 16 captures came after the block that
predicted them, 0 did not**, across blocks 0, 1 and 2.
`tools/reply-size.py`: **every one of the 16 byte counts exact**, and the sweep
over the whole of `bench/` now reads **135 modelled, 0 unexplained**.

### The census, and what each row settles

`probe2`, 9,392 bytes, `sha256 78beb72f…`, `flags=50010002`, at `0x80500000`
with `RESULT_BASE=0x80A01000`. `AUTOBURN` read `00000000` at the burn path's own
instruction **before** the transfer. Report **2,909 bytes**, which is
`2552 + 51 × (39 − 32)` — the length model derived at the desk, and it had
already reproduced `probe1`'s measured 1,543 and the qemu run's 5,875.

| | reading | what it settles |
|---|---|---|
| 🔴 `CPU-27` | `status = status_end = 1000fc00`, **bit 22 = 0** | **`BEV` is 0 on this core at the prompt, 量.** The vectors are in RAM at `0x80000080` and the core fetches there. Goes from *讀, one source* to measured, and it is the reading `probe2` was built to take |
| 🔴 `CPU-04` | **`PRId` = `0000CD01`** (row `0x78`, `S_VALUE`, both reads) | The prediction written before the run — `52481` = `0xCD01`, from this unit's own kernel printing a decimal — **hit exactly**. ⚠️ **The VALUE is now 量 and the NAME is not**: nothing here maps `0xCD01` onto `RLX4181` rather than `RLX5281`. **Do not write `RLX5281`** |
| 🔴 `F50b` | `Count` (rd 9, row `0x48`) = `00000000`, `S_ZERO`; `count.before = count.after = count.delta = count.traps = count.row48 = 0` | **`Count` is not implemented.** So **`R5-0`'s SoC timer driver is a PREREQUISITE, not a bonus**, and `R1c` loses its first timing route. That is one of the four decisions this gate exists to make |
| 🔴 `nowrite = 00000000` over all 256 rows | every `mfc0` wrote its destination | **This is what makes the zero above a real zero.** The audit's Must-fix 4 asked whether `mfc0` writes `rt` on this core; the answer is yes, always, so *the destination was never written* is excluded **by the instrument built to detect it** rather than by assumption |
| 🔴 select field | `moves = 8` — all eight of `rd 1`'s selects — `rows.suppressed = 0`, `rows.printed = 39` | **This CP0 ignores the select field.** Every other register returned identical values across its eight selects and was suppressed. R3000-class decode, measured rather than assumed |
| 🔴 CP0 20 (`CCTL`, row `0xa0`) | `00000000`, `S_ZERO` | `probe1`'s `XCT0` row read the same `0` and **could not tell *implemented and reads zero* from *destination never written***. With `nowrite = 0` proving `mfc0` writes `rt`, it can now: **rd 20 genuinely reads zero.** The write side is already 量 (`H1` cells 2/3/6 prove `mtc0 $t,$20` has an effect), so **CP0 20 is a write-only command register that reads back zero** — the sentence `R5b`'s MTD driver needs |
| `Config` (rd 16, row `0x80`) | `00000000`, `S_ZERO` | **`Config.M = 0`, so this is not a MIPS32 core**, proved outright. **And there is no `Config1`** — so `CPU-25` cannot be read out of CP0 on this part, and the free route named in the `GEOM` decision is closed by measurement |
| `traps = 00000000` | no CP0 read trapped, on any of 256 | reading an unimplemented `rd` on this core **returns zero; it does not trap**. That was the third of three hypotheses and it is now decided |
| 🆕 rd 6 | `00000004`, `S_VALUE`, stable across both primes | **Unexplained.** Not on the R3000 map; `Wired` sits at rd 6 on R4000-class parts and a value of 4 would be a plausible wired count. One reading, no second source — recorded as open |
| the partition | `values 40` + `zeros 208` + `moves 8` = **256** | 5 registers answer (rd 6, 12, 13, 14, 15), 1 moves (rd 1), 26 read zero. `× 8` selects each. The arithmetic closes |

### `Random` is the positive control, and it corroborates `CPU-08` by a route with no TLB probe in it

Row `0x08` is `mfc0 v0, c0_random` — 量, disassembled from the emitted image at
`0x80500330`. It came back `S_MOVES` with sixteen values across its eight rows:

```
0a00 1100 / 0900 1000 / 1d00 0800 / 1500 1c00 / 0600 0d00 / 1a00 0500 / 1200 1900 / 1100 1800
```

`Random`'s index field is bits 13:8, so those are **5 … 29, every one inside
0 … 31** — and `CPU-08` holds **32 TLB entries, 量**. A classic 64-entry R3000
would wrap `Random` over 8 … 63.

🔴 **Why this row matters more than any other.** `F50b` is decided by *`Count`
does not move*. Without a register that **does** move on this die, that reading
is unfalsifiable — a broken double-read mechanism produces the same answer.
qemu's `0x48 = S_MOVES` is a control on **qemu**. This is the control on **this
silicon**, and it was free.

### The handler took, and `CCTL 0x002` is confirmed on new ground

`install.bad = 0`, `break.count = 1`, `break.cause = 00000024` (ExcCode 9 =
`Bp`), `break.epc = 80500270` — **the exact address of the `break` instruction
in the emitted image**. So the vectors were written through KSEG1, read back
word for word, and the core **fetched** them.

🔴 **That is a second, independent test of `R1d`'s decision 1**, on a different
address range (`0x80000000`/`0x80000080` rather than the victims at `0x805…`)
and through a different store path (`wr_unc` rather than a cached store).
`CCTL 0x002` alone was sufficient there too.

**`install.changed = 0000002b` = 43, and it was written down before the run.**
Derived at the bench from this seating's own `H0a` and `H0c`: 21 of 22 positions
differ on the general vector (the single coincidence is index 10, the handler's
third `nop` on `H0a[10] = 00000000`) and 22 of 22 on the UTLB vector.
The model's positive control had already fired under qemu — 25 words × 2 vectors
− 20 `nop`-on-zero coincidences = 30, and qemu reported `0000001e`.

### `rfe` balances the KU/IE stack, and it cost nothing to find out

`status_end` = `status` = `1000fc00`, **exactly**. Derived before the run from
the R3000 rule that an exception shifts the three-deep `(KU,IE)` stack left and
`rfe` shifts it right, copying `p→c` and `o→p`: `status_end` must equal `status`
except in bits 5:4, which after the first exception equal `status`'s bits 3:2 —
and those are both `0` here, so the two words are identical. **A difference
anywhere else would have refuted the R3000 `rfe` model on this core**, which is
worth more than the census. Both words are in the report and at block words 6
and 30; the check is free.

🆕 **And the withdrawn `1000FC01` is vindicated with a mechanism rather than
resurrected.** That value was struck because it existed in exactly one place with
no source. The measurement is `1000FC00` — **every bit identical except bit 0,
`IEc`** — and `IEc = 0` is what *`J <addr>` clears `IE`* predicts for a payload.
So the old number described the loader at the prompt correctly and the payload
sees the same word with interrupts off. `CU0` set (bit 28) and `IM[7:2]`
unmasked (`0xFC00`) are now 量 as well.

### Two channels, and every control fired

| | |
|---|---|
| `H2g-hdr` | **all forty header words identical to the UART report.** Words 32–39 — `probe2`'s own KSEG1 copy of the general vector — equal `H0a`'s first eight words, read by the loader through a different command six minutes earlier |
| `H2g` | `DW 80A01000 `**`817`**, **9,661 bytes**, 820 words. Seal `EC84408D` at word 808 agrees with `sum=ec84408d` on the wire. Six spot-checked census rows agree word for word |
| the poison margin | words 809–816 **all `DEADC0DE`**; words 817–819 **`513A4757 71151DD1 11537755`**, not poison — **the two-sided control.** `809` would have shown three of the eight and nothing at all beyond the loop's end |
| `H2h-utlb` | **byte-identical to this seating's `H0c`** — the restore confirmed through a second instrument. `restore.mismatch = 0` and `restore.stillhandler = 0` from inside the payload |
| `H2i-below` | `DW 80A00000 8` byte-identical to `H0d-a` — **`probe2` wrote nothing below its own block** |

🔴 **The false alarm this seating avoided is measured, not argued.** `H2h-utlb`
against **2026-08-25's** `H0c` — the baseline the sheet named until tonight —
**differs**. The UTLB refill vector is DRAM power-on bias, the loader never
populates it, and `probe2` restores it from a copy taken on the boot it runs on.
A perfect restore compared against the previous seating's capture would have read
as *`probe2` corrupted physical 0*, which is the one outcome that stops the gate.

### The seal cannot be verified by re-adding it, and that is now written down

🔴 A straight re-sum of words 0–807 gives `EC84409D` against a stored
`EC84408D` — **high by exactly `0x10`, on every complete run.** `probe2.c`
computes the sum, writes it at word 808, and **then** calls
`progress(P_SEALED)`, so word 2 held `P_RESTORED` (`0x80`) when the sum was
taken rather than `P_SEALED` (`0x90`). Re-summing with word 2 forced to `0x80`
gives `EC84408D`, exact.

**Not reordered.** Sealing first and stamping progress afterwards is what keeps
`progress` monotone to the end — a block whose seal is written but whose progress
says `P_RESTORED` is a run that died between the two, and that state is worth
being able to see. The repair is the comment in `probe2.c` and this paragraph.

### `CLK-15 冷暖差`: the SPI-divider hypothesis is excluded

`DW B8001200 4`, the first reading of that window on this device (`REG-13` was
*未讀*), cold and after a watchdog reset:

```
cold  B8001200:  3FC00000  0BA08000  D8050000  FFFF0002
warm  B8001200:  3FC00000  0BA08000  D8050000  FFFF0000
                 SFCR      SFCR2     SFCSR     SFDR
```

**`SFCR`, `SFCR2` and `SFCSR` are byte-identical.** `SFCR` is the register that
carries the clock divider, so **the divider does not change between a cold
power-on and a watchdog reset** and it cannot be the mechanism behind
`CLK-15`'s +4.5 … +14.5 ms. The next candidate is the NOR's own power-on
wake-up.

🔴 **And `SFDR` moving is what makes that mean anything.** `FFFF0002` → `FFFF0000`
proves the four words are not a frozen constant, which is the control the cell
lost when its designed positive control failed (below). Without it, *identical*
would have been compatible with *this window does not reflect boot-time state at
all*.

`SFCSR = D8050000` decodes against D table 10 as `CSB0`=1, `CSB1`=1, `LEN`=`01`
(2 bytes), `SPI_RDY`=1, `IO_WIDTH`=serial, `CMD_BYTE`=**`0x05`** — the SPI
`RDSR` opcode. `SFCR2`'s top byte is `0x0B`, `Fast Read`. **The loader does not
leave this controller at reset; it leaves it configured for status polling.**

### Cold and warm, a third within-cycle pair

`tools/boot-timeline.py` over the whole corpus, with tonight's captures in:
**`booting` cold n=8, 348.0–356.9 ms; warm n=8, 338.2–347.6 ms — still not
overlapping.** And the comparison with no day in it gains a third pair:

| power cycle | cold | max warm | cold − warm |
|---|---:|---:|---:|
| `2026-08-24c` | 352.1 | 347.6 | **+4.5 ms** |
| `2026-08-25` | 355.7 | 341.1 | **+14.5 ms** |
| 🆕 `2026-08-25b` | 348.8 | 342.8 | **+6.0 ms** |

Tonight's cold `booting` of **348.8 ms** is **inside** `CLK-15`'s published cold
range on a **2.32 ms** ESC grid rather than a 20.35 ms one, so the fine grid did
not move the number. That is the whole of what one point can say — a bias check
that came back negative, and **not** a measurement of the spread, which n=1
cannot do.

### Four of my predictions were refuted, and all four are kept

1. 🔴 **`A-catch` bytes 1–181.** There were **two** artifact bytes tonight —
   `00 fc` — so the device's boot text starts at byte 2. The 181 bytes
   themselves are byte-identical to `2026-08-24c` and `2026-08-25` (negative
   control: the same slice against a warm boot differs at +48, the `C-8`
   marker). **What is not predictable is the instrument's prefix**, and `0xFC`
   is not an idle-line sample — it is a framing error, the receiver catching a
   character that began before it was listening.
2. **`SFCSR & 0xF8000000 == 0xF8000000`**, predicted from D's reset values.
   Measured `D8050000`; `LEN` is `01`, not the reset `11`.
3. **`SFDR` contains `1C 70 16`.** `ComSrlCmd_RDID()` runs twice on every boot
   and ends with `lw` from `SFDR`, and `REG-21`'s descriptor at `0x8040FBD4`
   holds `001C7016 1C701600` — so the JEDEC ID should have been sitting there.
   Measured `FFFF0002`. **The positive control designed for that cell did not
   fire**, and it was rescued only by `SFDR` moving between cold and warm.
4. **Pre-registered and confirmed**: `probe2`'s verdict line fires on
   `cnt_traps != 0 || row48 == S_TRAP || row48 == S_NOWRITE` and **does not name
   `S_ZERO`**. The device answered `S_ZERO`, so the line did not print. Named in
   block 1 before the run; it cost nothing this time because `count.delta = 0`
   is the right answer under `S_ZERO` anyway.

### 🔴 The fifth, and it is the expensive one: run 2 booted the vendor kernel

After run 1's watchdog reset, `J 80500000` was sent a second time to get a
repeatability control on the census. **It did not run `probe2`.** It printed
`decompressing kernel:` and booted the factory firmware to userspace — `boa`
on port 80, the same shape as `G6`/`G7`.

**Cause: the loader re-stages the vendor kernel at `0x80500000` on every boot,
including a watchdog reset.** Block 3 asserted *the payload is unchanged in DRAM
at `0x80500000`* — an assumption, not a measurement, and **this repository
already contained the fact that refutes it**: `§G1` exists to ask whether the
image is already staged there, and `§H1a`'s own warning says an image at the
wrong address plus `J 80500000` *"boots the vendor kernel the loader has already
staged — loader gone, DRAM gone, one power cycle."* That correction was written
into this sheet the same evening, from the other direction.

**What it cost: one power cycle.** Nothing earned was lost — run 1's block is on
disk on both channels and all three of the blocks that ran pass.

**What it measured, and it is not a consolation prize:**

* 🔴 **`C-16`'s copier runs on a warm reset**, not only on a cold power-on. 量,
  directly. So **a payload cannot be re-run on one power cycle at
  `LOADADDR=0x80500000` without re-uploading it** — a structural fact about
  every future seating, and it was not written anywhere.
* The vendor kernel booted from RAM to userspace again — `G6` repeated for free.

⚠️ **`bench/2026-08-25b/PREDICTIONS-b4-block3.md` names three cells and only one
ran.** `check-predictions.py` reports `1 of 3`. The file is not edited: the two
unrun cells were made unrunnable by the reading of the first, which is the same
situation as `bench/2026-08-24e`'s `block12` and is recorded the same way.

### Three tool defects, found by pointing the tools at tonight's captures

| | |
|---|---|
| `tools/reply-size.py` | 🔴 **`check` crashed on an unreadable `.meta.json`** — `TypeError: %d format: a real number is required, not str`. The `UNREADABLE` branch existed, was tallied and counted toward `misses`, and **could never print**, because it stored its error message in the column the printer formats with `%+d`. Same defect class as `hazlint` 1.0's `K4`. Fixed, with `S5`: 12 cases → **21**, including a mutation that restores both halves and demands the traceback come back. 🆕 And `UNREADABLE` no longer counts toward `modelled`, which had inflated the population figure this project quotes |
| `tools/boot-timeline.py` | 🔴 **the artifact anchor was `byte 0 → byte 1`**, which is right only for a one-byte prefix. On tonight's two-byte prefix it measured the gap **between the two artifact bytes** and reported **4.2 ms** where the other cold starts read 340.4 and 349.0 — pooled spread **149.1 %**, with nothing saying why. Now `byte 0 → the device's own `\r\nBooting``, guarded on byte 0 being an idle sample **and** the prefix being ≤ 8 bytes, because removing the first guard made a warm capture's whole 2,909-byte report the "prefix" and printed 63.7 s. Pooled artifact spread **149.1 % → 2.5 %**. 12 cases → **15** |
| `tools/rlxprobe/exc.S` | the comment said a non-writing `mfc0` pair gives `0x110F0000`; `0xD1CE0009 − 0xC0DE0009 = 0x10F00000`, two digits transposed. A comment, so no emitted word changed — **but it is the number a reader checks the reading against**, and a correct not-written run would have been called a mismatch. The device answered `S_ZERO` rather than `S_NOWRITE`, so the branch was never exercised and the wrong constant cost nothing this time |

### What this seating did not answer

* **`CPU-25`** — cache size, line size, associativity — **stays blank, and the
  route through CP0 is now closed rather than untried.** `Config` reads
  `00000000`, so there is no `Config1` to carry `IS/IL/IA` and `DS/DL/DA`.
  `GEOM=1` was not run and the reason is a measurement rather than caution:
  `rlx_r3k_size` needs isolation to work, `probe1` cell 4 measured that this
  core does not isolate, so the routine can only return `0` — which is its own
  *the core does not answer* value. **The remaining route is an eviction walk
  that needs no isolation**, using the mechanism cell 1 already proved (a store
  into the instruction stream is not seen): prime N victims at stride S, execute,
  rewrite, execute again, and read the STALE/FRESH boundary. That is a `probe3`
  and it is desk work.
* **`0xCD01` → a part number.** The value is measured; the mapping is not.
* **rd 6 = `00000004`.** One reading, no second source.
* **Whether `Random` free-runs or steps a fixed sequence.** The repeat that would
  have settled it is what booted the kernel. The `S_MOVES` *mechanism* control is
  unaffected — the two reads of the same row returned different values, which is
  what proves the census can detect a change — but the statement about `Random`
  itself is n=1.
* 🔴 **The seating measured `Status` once, on a payload, after `J` cleared `IE`.**
  It did not read `Status` as the loader sees it at the prompt, and no loader
  command can. `IEc = 0` is therefore a property of the payload's context, not of
  the prompt.
