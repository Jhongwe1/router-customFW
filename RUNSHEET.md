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
| a TFTP filename containing `nfjrom` or `boot.img` | those two names force the load address to `0x80000000` and execute the image the moment the transfer ends, with nobody at the console |
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
| **P3** 🔄 | *(R0 only)* `ip -brief addr` in WSL, then **`sudo ip link set <if> up`** and **`sudo ip addr replace 10.1.1.2/24 dev <if>`** | an interface that is **not** `eth0`, and after bringing it up `ethtool <if>` reads **`Link detected: yes`** | 🔴 **2026-08-24: bringing it up is part of the check, not a later step.** `ethtool`'s `Link detected` reports the **netdev**, not the wire — on an admin-down interface it reads `no` whatever is plugged in, and `/sys/.../carrier` returns `Invalid argument` rather than the documented `1`. The board's `PSRP` register is the independent second source and it disagreed with `ethtool` for six minutes before the cause was found. **Without this the `§G` transfer fails on the host side and reads as a board fault.** | `eth0` is WSL2's NAT'd vNIC (`172.18.x`). **A TFTP reply comes from a different source port than the request went to**, and WinNAT has no conntrack helper for that, so a transfer through the NAT can hang with the board innocent. The USB GbE adapter is in usbipd's persisted list; attach it, or run `loader-tftp.py` from Windows' own Python (3.10.7, pyserial 3.5, both present) |
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
