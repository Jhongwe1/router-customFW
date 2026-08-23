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
| a bare `EB`, `EW`, `LOADADDR`, `FLR`, `FLW`, `PHYR` or `PHYW` — no arguments | six handlers dereference `argv[0]` before any count test, and the tokeniser zeroes all twenty slots, so it reaches `strtoul(NULL, …)`. **Costs a power cycle.** Listed so it is not typed by accident |
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
