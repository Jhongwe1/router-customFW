# bench/

**Raw console transcripts, one directory per power cycle.** These are the
evidence behind `RUNSHEET.md`'s Results tables, and they are here because
without them those tables are a hand transcription — and `docs/loader-command-semantics.md`
§0 records what a hand transcription is worth: *a claim with no instrument
behind it*. Upstream's command table was wrong three ways for exactly that
reason.

So: the Results tables say what a reading **means**. These files say what the
device **sent**. If the two disagree, these win.

## What is in a file, and what is not device output

`B.log` and `E.log` were produced by piping `upstream/tools/console-dump.py`
through `tee`, so they interleave three things:

```
### B1  DW 8040DBC0 1   expect: 8040B070 00000000 80409A9C 8040B074   <- MINE, written before the visit
DW 8040DBC0 1                                                        <- the tool echoing what it sent
8040DBC0:	8040B070	00000000	80409A9C	8040B074                 <- THE DEVICE
<RealTek>                                                            <- the device's prompt
```

**Only the indented data lines and the prompt come from the board.** A `###`
line is an expectation written at the desk before power was applied; it is in
the file so the prediction and the reading sit together and neither can be
edited afterwards to match the other.

`C5-picocom.log` is different: it is pasted verbatim out of a `picocom` session
typed by hand, because `console-dump.py` refuses to send `EW` and working around
a deliberate refusal is worse than typing carefully. Its columns run together —
that is the terminal rendering tabs, not a reading.

## Before adding a directory here

Run `tools/audit-bench-log.py` over it. `CLAUDE.md` forbids committing a flash
dump because a dump identifies one physical device — its MAC and its radio
calibration are in `H601`. A console transcript is not a dump, but *not a dump*
is not the same as *carries nothing*, so it gets checked rather than assumed.

The tool scans for MAC forms, `H601`/calibration strings, serial numbers,
private IPv4, SSID and passphrase text, and host paths. **It runs every pattern
against a synthetic positive control first and refuses to report a clean result
unless all of them fire**, because a scan that cannot fail proves nothing.

```
python3 tools/audit-bench-log.py bench/<date>/*.log
```

## These files are byte-exact, and that took a rule

`.gitattributes` carries `* text=auto eol=lf`, because a shell script edited on
Windows has to still run under WSL. **That rule would have edited these
transcripts.** The loader's PHY format strings end `\r\n`, so the device sends
CR in its own output — measured 2026-08-23, normalisation would have removed
**20 bytes from `B.log` and 47 from `E.log`**. A transcript that has been
normalised is not a transcript, so `bench/**` is marked `-text`.

Checked, rather than assumed, before the first push: each stored blob hashes
equal to the file the device produced, with a negative control (`B.log` against
the stored `E.log`) confirming the comparison can tell two files apart.

## 2026-08-23

First silicon. One power cycle, 🔄 **no flash-write command issued** *(this read “zero flash bytes written” until 2026-08-30 — see § “zero flash bytes” below; no `FLR` bracket ran)*.

| file | section | what it covers |
|---|---|---|
| `A-catch.log` | `B1 §A` | ESC streamed across power-on; the banner and the seventeen-command table |
| `B.log` | `B1 §B` | the nine read cells, `B1`–`B9` |
| `E.log` | `B2 §E` | `E1`–`E12` plus `E2b`, added at the bench |
| `C5-picocom.log` | `B1 §C` | `C5` — `GIMR` bit 8 cleared by hand and restored by one `PHYR` |

`§C1`–`C4`, `§D`, `E11` and `§F` did not run and need another power cycle.

**`A2` is missing on purpose and it is a gap, not an omission.** The runsheet
asks for the full boot log; `console-dump.py catch` prints the banner line and
discards the rest of the pre-prompt stream, and nothing writes it to a file. The
cell is unsatisfiable by the instrument the sheet names. `upstream/dumps/uart-bootloader.log`
is the comparison in the meantime.

## 2026-08-24 — seating 2, part one

One power cycle, 🔄 **no flash-write command issued** *(was “zero flash bytes”; no `FLR` bracket)*, about twenty minutes. Every cell went
through `tools/console-capture.py`, one byte-exact timestamped capture per cell
(`.log` + `.timing` + `.meta.json`), so **nothing in this directory is a hand
transcription** — the caveat the 2026-08-23 section had to make about `B.log`
does not apply to any file here.

| files | cell | what it covers |
|---|---|---|
| `A-catch.*` | `B1 §A` | ESC streamed across power-on **from inside the capture loop**, so the whole pre-prompt stream is kept. **This is what closes `A2`**, which the 2026-08-23 section recorded as unsatisfiable by the instrument the sheet named |
| `A0-reopen-control.*` | 🆕 `A0`, first attempt | `Unknown command !` — and that is the informative one, see below |
| `A0b-reopen-control.*` | 🆕 `A0`, second attempt | `B1` reproduced exactly on a second power cycle |
| `C1.*` `C2.*` | `B1 §C` | `EW` is silent; both words land in order at `0x81000000` |
| `C3a.*` `C3b.*` | `B1 §C` | `EW` rounds an unaligned address **up**, silently |
| `C4a.*` `C4b.*` | `B1 §C` | `EB` takes the address **verbatim** — the opposite of `EW` |
| `C6-rescue.json` `C6-readback.*` | `B1 §C` | `AUTOBURN 0` works, confirmed by the echo **and** by the word the burn path reads |

**`A-catch.log` carries a finding nobody asked for.** The ESC stream kept
running after the prompt appeared, and the loader answered `Unknown command !`
after **exactly 128 ESC bytes, seven times**. That is the console line buffer,
and the code agrees: `memset(buf,0,128)` then `readline(buf,128,1)`. It is
written up in `docs/loader-command-semantics.md` §f and it rewrote `C7` before
`C7` ran.

**`A0-reopen-control.log` is kept although it failed**, because the failure is
the record: `§A`'s capture was cut mid-ESC-stream by `--seconds`, twelve ESC
bytes were still in the loader's line buffer, and this command appended to them.
`SPEC.md` `LDR-16` already knew queued ESC poisons the next command — **the rule
was in the table and not in the procedure, so it was rediscovered rather than
followed.** Deleting the failed capture would delete that.

### The redaction audit on this directory, and the one thing it flagged

```
python3 tools/audit-bench-log.py bench/2026-08-24/*.log bench/2026-08-24/*.json
```

All eight patterns fire on the synthetic control. Every `.log` and every
`.meta.json` is clean. **`C6-rescue.json` hits `private IPv4` six times, on
`10.1.1.1`, and it is committed anyway** — with the reason here rather than by
silently widening the tool:

> `10.1.1.1` is the address **this session chose and typed** (`IPCONFIG
> 10.1.1.1`), and `10.1.1.2/24` is the workstation. Neither is a property of the
> unit: the loader's own compiled-in address is `192.168.1.6` (`SPEC.md`
> `LDR-25`), and this unit's configured addresses are in `H601` and the config
> region, neither of which is in this repository. It is the same judgement
> `SPEC.md`'s own redaction allowlist already records for `192.168.1.6` — the
> pattern is right to fire, and the value is a statement about the experiment
> and not about the device.

**The reviewing is the point.** A hit that is waved through without a written
reason is a scanner that has been turned off one value at a time.

## 2026-08-24b — seating 2, part two

One power cycle (`A-catch` opened at 03:32:42, `CONT3` landed at 04:53:45 on the
same boot), 🔄 **no flash-write command issued** *(was “zero flash bytes”; no `FLR` bracket)*, **33 captures** — 30 cells and three flushes.
Every cell went through `tools/console-capture.py`, one byte-exact timestamped
capture per cell (`.log` + `.timing` + `.meta.json`), so **nothing in this
directory is a hand transcription** either. Nothing here was typed into a
terminal and nothing was pasted back.

| files | cell | what it covers |
|---|---|---|
| `A-catch.*` | `B1 §A` | ESC streamed from inside the capture loop across power-on, power applied 8.129 s in. Measured: with ESC collapsed the boot text is byte-identical to part one's `A-catch.log`; the loader echoed **730** ESC bytes in bursts `[128, 128, 128, 128, 128, 90]` |
| `flush.*` | seating rule 2 | consumes the 90-byte remainder `A-catch` left, and returns **exactly one** `Unknown command !`. That is what makes `730 = 5 × 128 + 90` a partition rather than the number 128 turning up twice |
| `A0.*` | `A0` | 71 bytes, byte-identical to part one's `A0b-reopen-control.log`. Third power cycle, same load base, same table address, same stride |
| `C7-pre.*` `C7-pre2.*` | 🆕 `B1 §C` | `DW 81000400 28` and `DW 81800000 8`, read **before** anything was written there. Measured: `0x81000400` holds a live 32-byte-periodic structure whose `+0x18` and `+0x1C` words both read `81000418`, the address of the first of the two, and `0x81800000` holds a second one pointing ~12 MiB higher |
| `G4-addr-probe.*` | 🆕 `B3 §G` | `DW 80A00000 8` — the replacement upload address, probed because the sheet's upload at `0x81000000` covers the structure `C7-pre` found. Eight words, no pointer-shaped word, no period |
| `C7a.*` `C7a-rb.*` | `B1 §C` | a **119**-character `EW` line and its readback: twelve words land in order, and the four-word over-run control past the end is unchanged |
| `C7b.*` `C7b-rb.*` | `B1 §C` | the **127**-character boundary control — the cell that makes `C7a` mean "the cliff is at 128" rather than "long lines are unsafe". Its over-run word was predicted from `C7-pre`'s period at an address never read, and came back as predicted |
| `E10b.*` | `B2 §E` | all five `PSRP` with **no cable in any jack**. This is the zero `E10` never got to take: seating 1 had a cable in, so `E10`'s stated expectation was never actually measured |
| `E11a.*` `E11a2.*` `E11b.*` `E11c.*` `E11c2.*` `E11d.*` `E11e.*` | `B2 §E` | one cable move per point, five points, each a `DW BB804128 8`. `E11a2` and `E11c2` are the pair: `E11a2` looked like "bit 8 is sticky", `E11c2` read a port whose jack was empty and took bit 8 from 1 to 0 |
| `E1b.*` `E2b.*` | `B2 §E` | the timer gate re-established on this boot — no advance, no PHY command — and tick samples 1 and 2 of four |
| `E12b.*` `E12c.*` `E12d.*` `E12e.*` | `B2 §E` | `ANLPAR` and `BMSR`, linked and unlinked, on different physical ports from seating 1's. `E12e` reads `ANLPAR` on an **unlinked** port, which no source here predicted and seating 1 never read |
| `B7a.*` `B7b.*` | `B1 §B` | `PABCD` with the button **released**, and `0xB8000000` = `8196E001` — the SoC identifying itself at a fixed address while the boot log prints `chipName: UNKNOWN` |
| `E9b.*` | `B2 §E` | `PCRP` re-read after four cable moves **inside one boot**, byte-identical to seating 1's `E9`. `F2`'s sweep now has a within-boot comparison basis instead of a cross-boot one |
| `CONT.*` | 🆕 continuity | the first command after the console adapter re-enumerated. **Kept although it failed**, see below |
| `flush-cont.*` | 🆕 continuity | a bare prompt, 11 bytes. **Kept although it failed** — it is the capture that refuted the residue explanation |
| `CONT2.*` `CONT3.*` | 🆕 continuity | tick samples 3 and 4, and the reading that settles whether this is still the same boot: `CONT2` read 428,675 where a board that had reset during the console outage would have read ~60,000 |
| `B7c.*` `flush-b7c.*` | 🆕 `B1 §B` | the button **held**. `PABCD_DAT` differs from `B7a` in bit 5 and in nothing else; `CNR` and `DIR` unchanged; no `Booting...`. Sent inside `--esc-after 20`, so ESC accounting `985 = 7 × 128 + 89` with seven `Unknown command !`, and `flush-b7c` took the remainder |
| `PREDICTIONS-block1.md` `-block2.md` `-block3.md` `-block3b.md` | — | **not device output.** Expectations written at the desk for twelve of the captures above, and the mtime check that shows they were written first, see below |

**`C7-pre` changes how part one's `C1`–`C4` rows above should be read.** Those
cells wrote to `0x81000000` on the argument that it is scratch. Measured today,
that region is not: `C7-pre` read a complete 32-byte period of a live structure
at `0x81000400`, and `C3b`'s `00000400` at `0x81000100` — recorded in part one as
unpredicted SDRAM — is the first word of that same period, untouched. The rows
stay as they are and the readings in them are still what the device sent. What
fell is the premise, and part one's writes landing on a live structure without
breaking anything was luck rather than design.

### `PREDICTIONS-block*.md` — mine, not the board's, and what they enforce

`RUNSHEET.md` house rule 2: *a cell whose expectation is written afterwards
illustrates; it cannot refute.* While the operator was driving cell by cell, the
rule enforced itself — the expectation was in a message that had already been
sent. From the point in this session where the console was driven directly, it
had **no enforcement at all**: a prediction written after the reading is
indistinguishable from one written before it, and the file it sits in cannot say
which it was.

These four files and `tools/check-predictions.py` are the enforcement. Each file
carries one fenced block whose info string is `cells`, naming the captures it
predicts, and the check is that the prediction file's mtime precedes the `.log`
mtime of **every** capture it names — the same instrument `E1b`/`E2b` used for the
timer, and it is re-runnable by anyone, afterwards, from the filesystem.

```
python3 tools/check-predictions.py bench/2026-08-24b/PREDICTIONS-block1.md
```

| file | captures it names | margin, prediction → capture |
|---|---|---|
| `PREDICTIONS-block1.md` | `E12b` `E12c` `E12d` `E12e` `B7a` `B7b` `E9b` | +8.246 s … +33.543 s |
| `PREDICTIONS-block2.md` | `B7c` `flush-b7c` | +601.688 s … +650.412 s |
| `PREDICTIONS-block3.md` | `CONT` | +92.330 s |
| `PREDICTIONS-block3b.md` | `flush-cont` `CONT2` | +7.500 s … +10.727 s |

All four report `N of N captures came after the prediction, 0 did not`, and each
run prints its controls first — `P1` prediction-before-capture passes, `N1`
capture-before-prediction is caught, `N2` a predicted cell with no capture is
caught, `N3` an empty `cells` block is refused rather than reported clean. Three
of the four must fail for a pass to mean anything, and the tool refuses to report
on the file if any of them does not behave.

**What this does not prove, and the tool says so in its own docstring**: mtime is
not a cryptographic timestamp. `touch -d` rewrites it. It proves ordering to a
cooperative auditor; it proves nothing against someone willing to forge it.
**Consequence for anyone editing this directory: never touch a predictions file
after its block has run.** Fixing a typo updates the mtime and the check fails —
correctly, and it will look like a false alarm. Corrections go in a new file,
which is what `PREDICTIONS-block3b.md` is: `block3` recorded what `CONT` was
expected to do, `CONT` did something else, and `block3` is left as it was.

**Coverage, stated rather than left to be assumed**: twelve of the 33 captures
are named in a block, and they are not simply the last twelve. The twenty sent
before `block1` went through the operator one at a time, where the expectation
was already in a sent message; from `block1` on, these files stand in for that.
**`CONT3` is the gap**: it was sent after the last block, no predictions file
names it, and its ordering is therefore unenforced. It is one of the four tick
samples the base-clock figure is fitted from, so the gap is named here rather
than left for a reader to find. The fix costs nothing and is procedural — the
block goes in before the cell is sent, not after the session has settled.

### `CONT` and `flush-cont` are kept although they failed

Same reason `A0-reopen-control.log` is kept above: the failure is the record.

Measured. `CONT` (`DW 8040DCE8 1`, 24 bytes) came back as the echo, `\n\r` and
`<RealTek>` — **no data line at all**, which is the shape `B8` produced when a
length argument parsed to zero. The obvious reading was residue in the loader's
line buffer, which is exactly the fault `A0-reopen-control` recorded.
`flush-cont` (`--send ''`, 11 bytes) refuted it: a **bare prompt with no
`Unknown command !`**, so the buffer was empty. `flush.log` and `flush-b7c.log`
are 31 bytes each and do carry that line — that is what a flush which finds
something looks like, and it is the control that makes `flush-cont`'s 11 bytes
readable. `CONT2`, the identical command sent afterwards, worked.

What is left is: **the first command sent after the console adapter re-enumerates
on the host is echoed but not acted on**, signature *echo + prompt + no output*.
The mechanism is inferred, pending a measurement — most likely the board's UART
saw a break or a framing error during re-enumeration — but the behaviour is
measured, and it is only measured because both captures are still here. **What
would refute it**: one first-command-after-re-enumeration that returns its data
line. There is a single supporting instance and no positive control, so it is a
rule to follow and not yet a finding.

The re-enumeration itself is not in these files and was not the board's doing:
`dmesg` recorded the CP2102 leaving the host bus after 7 min 24 s of pure idle,
Windows `usbipd list` moved the busid out of *Connected*, and `CONT2`'s tick
value says the board ran continuously through it.

### The redaction audit on this directory

```
python3 tools/audit-bench-log.py bench/2026-08-24b/*.log bench/2026-08-24b/*.json
```

All eight patterns fire on the synthetic control. **All 33 `.log` files and all
33 `.meta.json` files report `0 hit(s)`, and nothing is waved through** — part
one's `10.1.1.1` allowance has no counterpart here, because no TFTP, `IPCONFIG`
or rescue command ran on this power cycle and there is no rescue JSON in this
directory. The `PREDICTIONS-*.md` files are not scanned by that command line;
they are prose written at this desk and hold no device output.

**One caveat about the tool's own report, measured today.** Its byte column is a
decoded character count, not the file size on disk: `audit-bench-log.py` reads
each file with `io.open(p, encoding='utf-8', errors='replace')`, and Python's
universal newlines collapse every `\r\n` to `\n`, so the count is short by
exactly the number of CRLF pairs. `A-catch.log` is 1066 bytes on disk and reads
`1058` there (8 CRLF pairs); `B7c.log` is 1273 and reads `1266` (7); the 71-byte
and 118-byte captures have none and agree. No pattern in the tool spans a line
ending, so this changes no hit — but **that column is not a byte count and must
not be quoted as one.** The byte-exact claim in this file rests on `bench/**`
being marked `-text` and on the stored-blob hash check, not on this scan.

## 🆕 `R0` — the four directories this index skipped, and the only flash evidence here

**Written 2026-08-30 at the desk**, filling the gap the section further down
names: `bench/` held fourteen directories and this file had a section for nine of
them. The five with none were the whole of `R0` — `2026-08-24c`, `24d`, `24e`,
`24f` — and `2026-08-26`, which carries its own `README.md` and is the one
legitimate absence.

量 while writing them, because the paragraph that deferred the work guessed:
these four hold **81 captures across 18 prediction files** (blocks 0–13, with
`0b`, `3b`, `3c`, `9b` as lettered supplements), not *"60 captures across
thirteen prediction blocks"*. The old sentence is kept below rather than edited
away.

**Why a reader chasing the flash question comes here.** `G8-pre` → `G8a` →
`G8b` is the only `FLR` bracket this project has ever run. 量 2026-08-30, all
six captures are **777 bytes** and byte-identical across the three rounds at both
addresses:

```
cmp bench/2026-08-24c/G8pre-rd0.log bench/2026-08-24d/G8a-rd0.log   # identical
cmp bench/2026-08-24d/G8a-rd0.log   bench/2026-08-24f/G8b-rd0.log   # identical
cmp bench/2026-08-24c/G8pre-rd6.log bench/2026-08-24d/G8a-rd6.log   # identical
cmp bench/2026-08-24d/G8a-rd6.log   bench/2026-08-24f/G8b-rd6.log   # identical
```

That is **512 of 4,194,304 bytes — 0.012 %** — unchanged across the span. What
ran inside the span is worth stating exactly, because the sentence further down
says *"three kernel executions"* and only two of them are captured:

| | what | mark |
|---|---|---|
| `G6` | the vendor kernel from RAM, from bytes the loader staged itself. `bench/2026-08-24c/G6.log` | 量 |
| `G7` | the same kernel from RAM, from bytes delivered over TFTP. `bench/2026-08-24d/G7.log`, **byte-identical to `G6.log`** as a whole file, 1,789 bytes | 量 |
| the `24e` cycle | 🔴 **not captured.** `bench/2026-08-24e/A-catch.log` ends **at the loader banner** — the capture expired there. Nothing recorded what the loader did next, and the loader's own default is to boot flash. That a third kernel ran is *推*, well founded and not measured | 推 |

**And the bracket has never sampled the region that cannot be undone.** `0x000000`
covers 256 of the loader region's 24,576 bytes; `0x060000` is the `cr6c` header,
which no rule forbids writing. `H601` at `0x006000`–`0x007FFF` is **0 of 8,192**.
`bench/2026-08-30c/PREDICTIONS-B5-block2.md` §8 adds it.

### `2026-08-24c` — seating 2 part three, and `R0` opens

**One power cycle, 46 captures, 10 prediction blocks** (`0`, `0b`, `1`, `2`, `3`,
`3b`, `3c`, `4`, `5`, `6`), 13,715 bytes of `.log`. No flash-write command
issued; the `FLR` bracket's **first** round is here, so this is the one directory
of the four whose flash side is a baseline rather than a comparison.

| file(s) | cell | what it is |
|---|---|---|
| `PREDICTIONS-block0.md` … `block6.md` | — | ten blocks, each written before its own cells. `0b`, `3b` and `3c` are supplements written at the bench when the block before them decided their content — the numbering is deliberate and `block2` here is **not** the `block2` of `2026-08-25` |
| `A-catch.*` | `A-catch` | the ESC window. 🔴 **Byte 0 is the instrument's, not the device's** — `0xFF` here against `0x00` in `2026-08-25`, the two idle polarities of a line that is not yet driven. Bytes 1–180 are byte-identical across the two |
| `A0.*` | `A0` | the throwaway capture seating rule 2 requires, spent where nothing depends on it |
| `B7-cold.*` | `B7` | the reset-button GPIO read on a **cold** boot, against `2026-08-24b`'s warm reads |
| `D0a.*` `D0a2.*` `D0b.*` `D0-rb1.*` `D0-rb2.*` `D0a2-rb.*` | `D0` | the two canaries and their **readbacks**. 40 / 40 / 71 / 71 bytes. The readbacks are the cell that closed the hole `§D` had: a canary nobody read back is a canary nobody armed |
| `D1.*` | `D1` | `J BFC00000`, the warm reset. 1,363 bytes, `cr.esc_after.prompt_seen: true`; the jump→banner interval is **0.592 s** and is **not** the watchdog timeout |
| `D2.*` `D2b.*` `D2c.*` `D2d.*` `D2e.*` `D2f.*` `D2g.*` | `D2` | `WDTCNR` twice = `A5000000`, bit 20 **clear** — which refutes `D2`'s own predicted `A5100000`. `0x81000000` word 1 comes back `00000144` on **every** boot, and the `0x80A00000` canary survives **three** warm resets byte-exact. That pair is what gave `C-8` a discriminator that does not depend on a register |
| `D4.*` `D4c.*` | `D4` | the watchdog fired twice on purpose. **1122.5–1149.9 ms** at `OVSEL=1001` and **549.6–577.4 ms** at `OVSEL=1000` — `CLK-08`, and the divided/undivided choice is not in doubt |
| `flush-d1.*` `flush-d3.*` `flush-d4c.*` | seating rule 2 | each **11 bytes, a bare prompt, no `Unknown command !`** — the ESC terminator went out. 量 2026-08-30: all three have `sent: ""` and `--seconds 2.0 elapsed` in their metadata, so they are flushes and not cells. ⚠️ **`flush-d3` is named for a cell that is not in this directory** — `D3` was retired by `C-14`, and what the flush followed is not recorded |
| `E10c.*` `E10d.*` | `E10` | `PSRP0`–`PSRP4` with cables moved, against `2026-08-24b`'s no-cable negative control |
| `F1.*` `F2.*` | `F1` / `F2` | the MDIO sweep. `F1` is the **risk** cell — `phy_read()`'s wait on `MDCIOSR` bit 31 has no timeout and no iteration bound, so an unpopulated address could have hung the loader. It returned, 87 bytes. `F2` is **32 `PhyID` rows** in a 1,042-byte capture — 量 2026-08-30 the FILE is 34 lines, the extra two being the `MDIOR 2` echo and the trailing prompt, so *"32 lines"* is the table and not the file — addresses `0x00`–`0x04` → `0x001c` and `0x05`–`0x1f` → `0x0000` |
| `G0-head.*` `G0-mid.*` `G0-tail.*` | `G0` | 48 words at the head, middle and tail of the upload arena: no aligned pointer, no self-reference, no period. 🔴 **The test only means this after a *long* power-off** — `MEM-15` |
| `G1a.*` `G1b.*` `G1c.*` | `G1` | is the image already in RAM before anything is uploaded? All three match the payload file |
| `G8pre-flr0.*` `G8pre-rd0.*` `G8pre-y0.*` `G8pre-flr6.*` `G8pre-rd6.*` `G8pre-y6.*` | `G8-pre` | 🔴 **the flash baseline, taken before any kernel of this section runs.** Two 256-byte windows through `FLR`+`DW`, 128 words, all matching the 2026-08-16 dump. Added because `§G` had no baseline at all |
| `G6.*` | `G6` | the vendor kernel booted from RAM, from bytes the **loader** staged. 62 lines compared against `uart-boot.log` from `decompressing kernel:` onward, 62 identical |
| `X1.*` `X1b.*` `X1c.*` `X2.*` `X3.*` `X4.*` `X4b.*` | `C-17` | what writes the 32-byte-periodic structure at `0x81000400`. 🔴 **`X1c` is byte-identical to `X1b`, and `X1b` did not contain the structure** — which is what refutes link-up as the writer |

### `2026-08-24d` — seating 2 part four: the transport, and `R0` closes

**One power cycle, 24 captures, 6 prediction blocks** (`7`, `8`, `9`, `9b`, `10`,
`11`), 8,807 bytes of `.log` plus five JSON transfer reports and one 987,138-byte
readback that is **not** committed as a blob. No flash-write command issued; the
bracket's **second** round is here.

| file(s) | cell | what it is |
|---|---|---|
| `PREDICTIONS-block7.md` … `block11.md` | — | six blocks. `9b` was written at the bench, before relying on the poison `9` had just written — *verify the control before you trust the control* |
| `A-catch.*` `A0.*` | rules 1–2 | the ESC window and the throwaway |
| `G2-rb.*` `G2-rescue.json` | `G2` | `AutoBurning=0` · `Set TFTP Load Addr 0x80a00000` · `Now your Target IP is 10.1.1.1`, then `0x8040D4A0` read back as **`00000000`** — the burn guard, read at the one instruction that matters |
| `G4-put.json` `G4-get.json` — and `G4-back.bin`, which is **not in a clone** | `G4` | **987,138 bytes up in 1,929 blocks, back down, `cmp` byte-identical**, sha256 `396561a0…45a03e90`. The transport proved without executing anything. ⚠️ 量 2026-08-30: `G4-back.bin` is 987,138 bytes on this machine and is **untracked** — a reader of this repository has the two JSON reports and the hash, and not the blob |
| `G5-poison1..3.*` `G5-pv1..3.*` `G5-put.json` `G5-rescue.json` `G5-rb1..3.*` | `G5` | `5A5A5A5A` written at three points, **read back to confirm the poison took** (`pv`), then the upload, then the dump's own bytes read back at all three (`rb`). 🔴 **The `pv` triple is the cell that makes `rb` mean something**: `G1` had already shown the correct bytes were there, so without the poison a passing readback proves nothing |
| `G8a-ab.*` `G8a-flr0.*` `G8a-rd0.*` `G8a-y0.*` `G8a-flr6.*` `G8a-rd6.*` `G8a-y6.*` | `G8a` | the bracket's second round, taken **after `G6` and both uploads and before `G7`**. `AUTOBURN` `00000000`; both windows byte-identical to `G8-pre` |
| `G7.*` | `G7` | the vendor kernel from RAM, from bytes delivered over **TFTP**. 🔴 **`G7.log` is byte-identical to `G6.log` as a whole file** — 1,789 bytes, sha256 `2f921f75…0712070`. Stating that as a line count understated it. **`R0` closes here** |
| `G0-head-24d.*` `X1-24d.*` `X1-post.*` `X3-24d.*` | `C-17`, `MEM-15` | the arena and the `0x81000400` structure re-read after a **seconds-long** power-off, against `24c`'s reads after a 16 h 23 m one. This pair is `MEM-15`: this DRAM retains **content**, not merely bias |

### `2026-08-24e` — one capture, and it is the record of a failure

**One power cycle, one capture, one prediction block.** `block12` planned ten
cells; **nine of them never ran**, and `A-catch.log` is why.

| file(s) | cell | what it is |
|---|---|---|
| `PREDICTIONS-block13.md`'s subject | — | `block12` is kept **unedited**, with five cells that have no capture. `check-predictions.py --sweep` reports those as *no capture yet* and that is not a failure: a seating that stopped early is a fact about the seating |
| `A-catch.*` | `A-catch` | 🔴 **4,542 bytes, and the last four lines are `Booting...` / `chipName: UNKNOWN` / `ramSize: 32M` / the banner.** The ESC stream ran 45 s; the boot began at **t = 64.2 s**, nineteen seconds after it stopped, and the capture expired at the banner. **The first capture in this project that shows what a missed ESC window looks like from inside**, which is why it is committed rather than deleted |

**What it cost and what it changed.** One power cycle, and a standing change to
every ESC cell: **`--esc 180 --seconds 200`**. The asymmetry is the argument — an
extra ESC second is free (~50 bytes/s into a buffer the loader empties every 128
bytes) while a missed window costs the most expensive unit at this bench. Byte 0
of this capture is `0x5E`, `^`, not the raw `0x1B` of `24c`: the caret pairs are
a Linux tty's `echoctl`, which is *推* and is the open question the
`^[`-attribution row in `PROGRESS.md` carries.

### `2026-08-24f` — seating 2 part five: `G8b`, with a window that cannot be missed

**One power cycle, 10 captures, 1 prediction block** (`13`), 14,010 bytes of
`.log` — of which 11,823 are `A-catch2` alone, which is what a 180-second ESC
window costs and it is the whole point. No flash-write command issued; the
bracket's **third** round is here.

| file(s) | cell | what it is |
|---|---|---|
| `PREDICTIONS-block13.md` | — | supersedes `2026-08-24e`'s `block12`. It opens with a two-row table of the day's two missed catches and their **different** causes, because one was an instruction to the operator and the other was a window sized for a laboratory |
| `A-catch2.*` | `A-catch` | 11,823 bytes, ending `Unknown command !` / `<RealTek>` — the prompt, caught. The name carries the `2` because `24e`'s `A-catch` is the one that failed and both names had to survive |
| `A0.*` | `A0` | the throwaway |
| `G8b-ab.*` | `G8b` | `AUTOBURN` read before anything else, as every `J` and every bracket in this project is preceded by |
| `G8b-flr0.*` `G8b-rd0.*` `G8b-y0.*` `G8b-flr6.*` `G8b-rd6.*` `G8b-y6.*` | `G8b` | the bracket's third round, **after `G7`'s power cycle**. Both windows byte-identical to `G8a`'s and to `G8-pre`'s |
| `X1-24f.*` | `C-17` | the `0x81000400` structure after another short power-off — the third reading of `MEM-15` |

## 2026-08-25 — seating 3, `R1g-4a`

**One power cycle, 26 captures, 10 prediction blocks,** 🔄 **no flash-write command issued** *(was “zero flash bytes”; no `FLR` bracket)*. The
first seating in which code of mine executed on this core.

| file(s) | cell | what it is |
|---|---|---|
| `PREDICTIONS-b4-block0.md` | — | 🔴 **written at the desk at 06:09 and committed in `857d790` at 06:15**, hours before power. Its capture paths say `bench/2026-08-26/` because the seating was planned for the 26th; **that file is `bench/2026-08-26/PREDICTIONS-b4-block0.md` and it is not edited.** This one re-homes it, verbatim except for the nine paths and one instrument-version correction which is marked in the file |
| `PREDICTIONS-b4-block1,3,4,5,6,7,8,9,10.md` | — | written at the bench, each immediately before its own cells, because each is conditional on the block before it. **Block 2 does not exist**: that number belongs to `H2`, which is `R1g-4b` |
| `A-catch.*` | `A-catch` | the ESC window. 🔴 **Byte 0 is the instrument's, not the device's** — `0x00` here, `0xFF` in `2026-08-24c`, the two idle polarities of a line that is not yet driven. Bytes 1–180 are byte-identical to `24c`. See `RUNSHEET.md` § Results B4 |
| `A0.*` | `A0` | 71 bytes, byte-identical to `24b` and `24c`. The throwaway seating rule 2 requires, spent where nothing depends on it |
| `H0a.*` `H0a2.*` `H0a3.*` `H0b.*` `H0c.*` `H0d-a.*` `H0d-b.*` | `H0` | seven zero-risk reads. `H0a`/`H0a2`/`H0a3` are the same 32 words three ways — the vector, its source, and its uncached alias |
| `H1-rescue.json` `H1a-ab.*` `H1a-put.json` | `H1a` | `AUTOBURN 0` + `LOADADDR` + `IPCONFIG` in one transcript; then the word at `0x8040D4A0` read **before** the upload, because that is the word the burn path sees during it; then 19,792 bytes over TFTP |
| `H1b.*` | `H1b` | `J 80500000`. The payload's whole report **and** the watchdog reset that follows it, in one capture — which is what makes `H1b.timing` a clock measurement as well as a transcript |
| `flush-h1b.*` `flush-h3a.*` `flush-h3c-D4.*` `flush-h3c-D4c.*` | seating rule 2 | each **11 bytes, a bare prompt, no `Unknown command !`** — the ESC terminator went out |
| `H1c.*` | `H1c` | the same block read back from RAM. `DW 80A00000 137`, **not 88**: 88 stops before the seal |
| `H3a-early.*` `H3a.*` `H3a-rb.*` | `H3a` | `C-17` on two reset paths. `H3a-early` and `H3a-rb` are **byte-identical** and that is the finding |
| `E13-pos1-wan.*` `E13-posX-lan1.*` `E13-posX-lan2.*` `E13-posX-lan3.*` | `H3b` | 🔴 **the filenames are the measurement.** `pos<N>` is the position counted from the WAN socket, `<silkscreen>` is what the case says; `posX` means the case's printing order is not yet recorded, so this capture establishes *silkscreen → port* and not *position → port*. `NET-13` went wrong twice from exactly that conflation |
| `E11f-psrp2-empty.*` | `NET-11` | read `PSRP` again with nothing touched and one socket empty. Bit 8 goes 1 → 0, and bits 3/0 do not |
| `H3c-D4.*` `H3c-D4c.*` | `H3c` | the same two `OVSEL` points as `2026-08-24c/D4`, on a **2.118 ms** ESC grid instead of 20.35 ms. `esc.esc_after.achieved_period_s` in the `.meta.json` is what says which grid it actually got, and it is the reason these two captures could settle what the earlier pair could not |

**Checked before this directory was committed**, as this file's own rule requires:
`tools/audit-bench-log.py` over all 26 `.log` files — 0 hits, with all eight
patterns firing on its synthetic control first.

🔴 **And that run found a defect in the tool rather than in the logs.** It printed
a number labelled `bytes` that was the byte count **minus the number of CRLF
pairs** — `8855 → 8797`, `5356 → 5307`, `1371 → 1360`, `10790 → 10719`, and
`1671 → 1671` where a file happens to contain none. Cause: it read in text mode,
so Python's universal newlines collapsed every `\r\n`. **That is the same defect
the `.gitattributes` line `bench/** -text` exists to prevent**, applied to git and
not to the tool living beside these files. The scan itself was never affected —
every pattern is ASCII and survives the decode — but the number was. Fixed the
same day (`newline=''` and `os.path.getsize`); **the fix has no control of its
own yet**, which would need a fixture with a known CRLF count.

## 2026-08-25b — seating 4, `R1g-4b`

**One power cycle, 23 captures, four prediction blocks,** 🔄 **no flash-write command issued** *(was “zero flash bytes”; no `FLR` bracket)*, **and `R1e` closes.** The seating in which the CP0 census ran on this silicon.

**Not `bench/2026-08-26/`.** That directory holds a sealed prediction file for a
seating that happened a day early, and it is closed to captures — see
`bench/2026-08-26/README.md`, which also carries the generalised rule the sealed
file could not write about itself.

| file(s) | cell | what it is |
|---|---|---|
| `PREDICTIONS-b4-block0.md` | — | written at the desk **before power**. Eight zero-risk reads. Carries the measurement that decided the seating's shape: **this DRAM's power-on bias is reproducible but not deterministic** — 4, 25 and 27 of 256 bits differ across three cold power-ons at `0x80A00000`, with a positive control (0/256, self) and a negative one (123/256, against a loader-written page) |
| `PREDICTIONS-b4-block1,2.md` | — | written at the bench, each immediately before its own cells, because each is conditional on the block before it |
| `PREDICTIONS-b4-block3.md` | — | 🔴 **names three cells and only one ran.** `check-predictions.py` reports `1 of 3` and that is correct: the two unrun cells were made unrunnable by the reading of the first. **Not edited** — same situation as `2026-08-24e`'s `block12` |
| `A-catch.*` | `A-catch` | the ESC window, on a **2.32 ms** grid (`--esc-period 0.002`) rather than 20.35 ms, so the log is ~10× the usual size and that is the instrument. 🔴 **Byte 0 is not the only instrument byte this time**: the prefix is **two** bytes, `00 fc`, and `0xFC` is a framing error rather than an idle sample. Bytes 2–182 are byte-identical to `24c` and `25`; the negative control — the same slice against a warm boot — differs at +48, the `C-8` marker |
| `A0.*` | `A0` | 71 bytes, byte-identical to `24b`, `24c` and `25`. Fourth consecutive. The throwaway seating rule 2 requires |
| `SPI-cold.*` `SPI-warm.*` | 🆕 `CLK-15 冷暖差` | `DW B8001200 4`, the **first reading of the SPI controller window on this device**, cold and after a watchdog reset. `SFCR`/`SFCR2`/`SFCSR` byte-identical, only `SFDR` moves — **the divider hypothesis is excluded, and `SFDR` moving is what makes that mean anything** |
| `H0a.*` `H0b.*` | `H0` | byte-identical to `2026-08-25`'s. Class (a): the loader re-makes both on every boot. Re-taken because `H0a` is the cell that forbids the payload and `H0b` is the safety net's own check |
| `H0c.*` | `H0c` | 🔴 **32 words, not 8, and re-taken rather than carried across.** The UTLB refill vector is DRAM bias — class (c). Its words 1–7 differ from `2026-08-25`'s by **20 of 224 bits**, which is why `H2h-utlb` had to compare against *this* capture |
| `H0d-a.*` `H0d-b.*` | `H0d` | `0x80A00000` came back **bias, not `probe1`'s block** — so `MEM-15`'s retention is gone by ~3.9 h, measured with a 548-byte chosen value rather than a two-word canary. `0x80A01000` is neither poison nor a magic |
| `H2-rescue.json` `H2a-ab.*` `H2a-put.json` | `H2a` | `AUTOBURN 0` + `LOADADDR` + `IPCONFIG` in one transcript; then `0x8040D4A0` read **`00000000`** before the transfer; then 9,392 bytes of `probe2` over TFTP |
| `H2a.*` | `H2a` | 🔴 **the seating.** `J 80500000`, the whole 2,909-byte report, the 39 printed census rows and the watchdog reset that follows, in one capture |
| `flush-h2a.*` | seating rule 2 | 11 bytes, a bare prompt, no `Unknown command !` |
| `H2g-hdr.*` `H2g.*` | `H2g` | the block from RAM. `DW 80A01000 40` then `DW 80A01000 **817**` — 817 and not 809, so all eight poison-margin words are read **and three words past the poison loop's own end**, which is the control on the poison |
| `H2h-gen.*` `H2h-utlb.*` | `H2h` | both vectors after the run, 32 words each. `H2h-utlb` byte-identical to **this seating's** `H0c` |
| `H2i-below.*` | 🆕 | `DW 80A00000 8`, byte-identical to `H0d-a` — `probe2` wrote nothing below its own block |
| `H2a2.*` | 🔴 block 3 | **kept although it failed, and the failure is the record.** A second `J 80500000` to get a repeatability control on the census printed `decompressing kernel:` and booted the factory firmware to userspace. **The loader re-stages `0x80500000` on a watchdog reset too**, so the payload had been overwritten. Cost: one power cycle. What it measured is `C-16`'s copier on a warm reset, which nothing had written down |

**Checked before this directory was committed**, as this file's own rule
requires: `tools/audit-bench-log.py` over all 23 `.log` files and every
`.meta.json` — **all eight patterns fire on the synthetic control first**, and
every one of those files reports `0 hit(s)`.

> **`H2-rescue.json` hits `private IPv4` six times, on `10.1.1`, and it is
> committed anyway** — the same judgement, with the same reason, that
> `bench/2026-08-24/C6-rescue.json` already carries: `10.1.1.1` is the address
> **this session chose and typed**, and `10.1.1.2/24` is the workstation.
> Neither is a property of the unit — the loader's own compiled-in address is
> `192.168.1.6` (`SPEC.md` `LDR-25`), and this unit's configured addresses are
> in `H601` and the config region, neither of which is in this repository. The
> pattern is right to fire and the value is a statement about the experiment.

### What the prediction files enforce here, and what they caught

```
python3 tools/check-predictions.py bench/2026-08-25b/PREDICTIONS-b4-block0.md
```

| file | captures it names | result |
|---|---|---|
| `block0` | `A-catch` `A0` `SPI-cold` `H0a` `H0b` `H0c` `H0d-a` `H0d-b` | **8 of 8 came after** |
| `block1` | `H2a-ab` `H2a` | **2 of 2** |
| `block2` | `flush-h2a` `H2g-hdr` `H2g` `H2h-gen` `H2h-utlb` `SPI-warm` | **6 of 6** |
| `block3` | `H2a2` `flush-h2a2` `H2g2-hdr` | **1 of 3** — and see the row above |

**16 of 16 for the cells that ran.** And `tools/reply-size.py` says every one of
the sixteen byte counts was exact, which `check-predictions.py` structurally
cannot: it verifies **ordering**, not arithmetic. Both of the previous seating's
arithmetic errors were in blocks written at the bench, which is why the counts
now come out of the tool rather than out of a person.

🔴 **Five predictions of mine were refuted and all five are in the blocks,
unedited.** `RUNSHEET.md` § Results B4 `R1g-4b` lists them. The expensive one is
block 3's *the payload is unchanged in DRAM at `0x80500000`* — an assumption
written as a fact, in a repository that already contained `§G1` and `§H1a`, both
of which say otherwise.

⚠️ **`2026-08-24c` through `2026-08-24f` have no section in this file.** They were
seating 2 part three, five power cycles and 81 captures, and they are described in
`RUNSHEET.md` § Results — seating 2 part three instead. Noted rather than
back-filled, because a directory index that is silently incomplete is worse than
one that says where the gap is.

## 2026-08-30 — seating 5, power cycle 1, `R1h-3`. **The prediction, before the seating**

🔴 **One file, no captures**, like `2026-08-30b` beside it:
`PREDICTIONS-B5-block0.md`, written and frozen at the desk on **2026-08-29**.
This is `probe3` — `R1h`'s bench half, riding `R3`'s seating and running
**first** within it, because `R3`'s pass state is *a kernel is running* and in
that state there is no `<RealTek>` prompt to type `J` into and no `DW` to
recover a result block with.

🔴 **This block is also the CARD.** `RUNSHEET` §B5's card says of power cycle 1
*"`R1h-3` owns it; it is not on this card"*, so §0 of the block is the only
place the typed lines exist. Two files are read at the bench on this seating.
Its rows are prefixed `Q-*` because `P0`…`Pn` already means three different
things in this repository — the host preflight, `R3`'s desk checks, and
`probe3`'s own at-the-prompt group — and §1 of the block is the only place that
collision is written down.

| | |
|---|---|
| **cells named** | thirteen: `A-catch`, `Q0-ab`, `Q1-tc`, `Q1-tc2`, `Q2-rbhead`, `Q2-arena0`, `Q2-arena1`, `Q2-arena2`, `Q3-len`, `Q0-ab2`, `Q4-head`, `QJ`, `Q5-rb` |
| **at the desk** | `check-predictions.py` reports **`0 of 13`**, all fifteen controls green — control `N2` firing on every cell, which is the correct answer before a seating |
| **deliberately not named** | `Q5-margin` (the rest of the poison margin, only if the free three come back non-poison) and `Q6-post` (a post-mortem `DW` after a silent `J`) |
| **desk work already spent** | `P7`, the rebuild-on-the-day: `probe3` rebuilt 2026-08-29, sha256 `1a0725c0…`, 29,088 bytes — **byte-identical to the value `R1h-1` recorded on 2026-08-26**, `hazlint` 0 violations in 804 loads |

**What writing it produced, beyond the block.** Three things, each landing in an
owner file rather than here: the loader's **`DW` emission rate** measured for the
first time (`SPEC.md` `LDR-40`, 3,594–3,726 B/s, n=2 — every `--seconds` on
every card had been sized against the 3,840 line rate); `LDR-07`'s round-up
handing back **three poison-margin words for free** on `DW 80A02000 641`, so the
over-run control costs no command (`docs/probe3-cells.md` §4); and the scope of
§B5-c1 — *the head does not discriminate* is about `nfjrom` files, and a flat
`rlxprobe` payload's head **does**, by the same linker-constant mechanism
(`RUNSHEET` §B5-c1).

⚠️ **And re-measuring `A-catch` over all nine captures in this directory tree
reproduced a correction the repository had already made.** §B5-c12 records it:
seven complete 181-byte slices, one hash, and `2026-08-24e` is a **118-byte
truncation whose bytes are a byte-identical prefix** — not a warm-boot control.
**The cell has no demonstrated negative**, and block 0 says so rather than
repeating block 1's framing.

## 2026-08-30b — seating 5, `R3-8a`. **The prediction, before the seating**

🔴 **This directory holds one file and no captures**, and that is the point:
`PREDICTIONS-B5-block1.md` was written and frozen at the desk on **2026-08-29**,
the day before the seating it predicts. `bench/2026-08-26/` is the precedent for
a prediction file that is closed to editing before its captures exist; this one
differs from it in that the captures are still expected.

**Why `2026-08-30b` and not `2026-08-30`.** One directory per power cycle, and
power cycle 1 of this seating is `probe3` (`R1h-3`), which owns
`bench/2026-08-30/` and its own block. This is power cycle 2 — `loudm`,
`R3`'s D1–D5. Power cycle 3 has no directory yet **because its identity is not
decided**: `quietm` if `L-3` reaches D4, and the plan's halving experiment (the
vendor's kernel with my initramfs) if it does not reach D2.

| | |
|---|---|
| **cells named** | twelve: `A-catch`, `L0-ab`, `L0-tail`, `L2a`, `L2b`, `L2c`, `L3`, `L5a`, `L5b`, `L6a`, `L6b`, `L7a` |
| **at the desk** | `check-predictions.py` reports **`0 of 12`**, all fifteen controls green. That is control `N2` — *a predicted cell whose capture does not exist* — firing on every cell, and it is the correct answer before a seating |
| **what the block also predicts** | what the check will say afterwards: `12 of 12` on D5, `10 of 12` with no link, `7 of 12` if the boot stops at B07 |
| **deliberately not named** | the branch cells `L-6c`/`L-6d`/`L-7b` (the second interface) and `L-8a`/`L-8b` (the post-mortem). Naming both branches guarantees a violation whichever way the seating goes. **The cost is stated in the block**: if a branch cell runs, its ordering is unenforced — the same gap this file records for `CONT3` |

**What the block is worth, and it is not that it will be right.** Four of its
twelve cells exist because writing it refuted the seating sheet: `L2a` reads
eight words instead of one because the first sixteen bytes of my image and of the
staged vendor image are **byte-identical** (量, against `2026-08-23/B.log:16`,
`2026-08-24c/G1a.log` and `2026-08-24d/G5-rb1.log`), and `L0-tail`/`L2c` are a
before/after pair on a region 66,542 bytes above the staged image's end, which is
the only part of the upload that can be watched **changing** without poisoning
the fallback. `RUNSHEET.md` §B5-c1 has the measurement.

## The whole record is swept now, and it was not before

🆕 **2026-08-29.** `tools/check-predictions.py` gained `--sweep`. It walks
every `PREDICTIONS-*.md` under `bench/` and checks **ordering only**:

```
38 prediction file(s), 168 cell(s): 136 ordered, 32 with no capture yet, 0 OUT OF ORDER
```

**A predicted cell with no capture is reported and is not a failure** — a
seating that stopped early is a fact about the seating, and `2026-08-25b`'s
`block3` is the worked example. What the sweep can go red on is a committed
capture **older** than the prediction naming it, which is either an edited
predictions file or a touched capture: the two failure modes of house rule 2
that a runner can see at all. It refuses rather than reporting green if it finds
no predictions files, and on **zero resolvable cells** — a renamed directory,
a typo'd path or the wrong working directory, all three of which used to read
as a clean result.

🔴 **And it is NOT a CI gate, because git does not store mtimes.** A step was
written for it and taken out the same hour: `actions/checkout` writes every
file fresh, so on a clone the whole of this directory carries a handful of
timestamps spanning tens of milliseconds and the sweep reads **128 of 156
cells as out of order**. 量 twice, on two independent `git clone --depth 1`
of this repository. **The ordering claim is a pre-push gate on the machine
that took the captures and it proves nothing to anyone who clones this
repository** — which is sharper, and worse, than *not a cryptographic
timestamp*. What CI runs is the tool's fifteen controls, which build their
own fixtures and are clone-stable. The fix that would make the sweep a CI
gate is known: every capture already carries a committed `started_wallclock`,
so the capture side survives a clone; the prediction side would need a
declared timestamp inside the file, which the blocks already frozen cannot
have. Carried forward rather than half-done.

⚠️ **It says how many cells have no capture and not which.** Twelve of the 32
are `2026-08-30b`'s; the rest are seatings that stopped, and the per-file check
already names them. Carried forward in `PROGRESS.md` rather than fixed with a
second way to print what `check` prints.

---

## 🔴 2026-08-30 and 2026-08-30b — what the seating produced. Written after it

Both directories were named for the seating their cards were written for, and
the seating ran on the **evening of 2026-08-29**. The names do not move: renaming
would break a frozen file and a committed card to fix a label.

**26 captures across two power cycles, and no flash-write command issued** — ⚠️ **not the same as "zero flash bytes", which needs the `FLR` bracket this seating did not run.** Both blocks pass
their own gate — **13 of 13** and **12 of 12** — and `--sweep bench` read
**39 files, 181 cells, 161 ordered, 0 out of order** on the night. 🔄 **量
2026-08-30, after block 2 landed: 40 files, 212 cells, 161 ordered, 51 with no
capture yet, 0 out of order** — the 31 new cells are all "no capture yet", which
is the correct state for a block written before its seating. *(This line kept the
night's numbers in the present tense while the line above it was being rewritten.)*

### `2026-08-30` — power cycle 1, `probe3`, `R1h-3`

| file | what it is |
|---|---|
| `A-catch` | the cold power-on. Prefix **0 bytes**, and the 181-byte slice hashes `f5287ff9…` — the eighth agreeing capture |
| `Q0-rescue.json` | the rescue transcript. Not a capture; it has no `.log` |
| `Q0-ab`, `Q0-ab2` | `AUTOBURN` at both ends of the preflight, `00000000` both times |
| `Q1-tc`, `Q1-tc2` | `TC0CNT` twice, seconds apart. Different — the counter is live |
| `Q2-rbhead`, `Q2-arena0/1/2` | four DRAM windows, power-on bias |
| `Q3-len` | `DW 80A00000 2000` — 23,527 bytes, the largest `DW` this device has run |
| `Q0-put.json` | the TFTP transcript. **Not on the card**: `--report` was added so the transfer has a committed record. Additive, local, and it changes nothing on the wire |
| `Q4-head` | the image head, byte-identical to the prediction |
| `QJ` | the run. 38,295 bytes, of which 5,642 is the report and the rest the post-reset ESC storm |
| `Q5-rb` | the result block, 7,593 bytes / 161 lines |
| `CORRECTIONS-block0.md` | 🔴 **what the frozen block got wrong.** The block is not edited; this is the file its own second paragraph asks for |

### `2026-08-30b` — power cycle 2, `loudm`, `R3-8a`

| file | what it is |
|---|---|
| `A-catch` | power cycle 2's catch. Prefix is **117 raw `0x1B`** — cycle 1's loader still answering, and the negative control the `^[` question lacked |
| `L0-rescue.json`, `L1-put.json` | rescue and TFTP transcripts |
| `L0-ab` | `AUTOBURN` = `00000000` |
| `L0-tail`, `L2c` | 🔴 **the before/after pair at `0x806013F0`**, and it is the best upload check this project has built — line 1 goes to sixteen zero bytes (reached `image_end`), line 2 stays byte-identical (did not run past) |
| `L2a`, `L2b` | the head, and the variant discriminator at `0x80540000` |
| `L3` | **the boot.** 6,459 bytes, eleven marks, M4, a shell prompt |
| `L5a`, `L5b` | `/proc/cpuinfo` and `/proc/version` — D4, and the build-stamp discriminator |
| `L6a`, `L6b` | six netdevs; `eth0` brought up |
| `L7a` | ping on `eth0` — 0 received, **and nothing at all in the host capture** |
| `L6c`…`L6f`, `L6c-up`… | the interface sweep, one up at a time, `eth1` → `eth4` |
| `L7b`, `L7c`, `L7d` | `eth1`, `eth2`, `eth3` — all silent |
| `L7e` | 🔴 **`eth4`. 4/4, 0 % loss**, with the host capture holding request and reply |

⚠️ **`L6c-up`, `L6d-up`, `L6e-up`, `L6f-up` are cells nobody predicted.** The card
writes `L-6c` as *"`ifconfig <prev> down` then `ifconfig <next> … up`"* — two
commands, one row. Each is a `console-capture.py` invocation, so each is a
`.log`, and the second needed a name. **`--sweep` walks predictions to captures
and never the other way**, so these are outside the ordering discipline; that
gap is the one already recorded for `CONT3`.

⚠️ **Twelve of §B5's thirteen card rows carry no `--seconds`, and the tool has no
default.** What was actually typed is in `RUNSHEET` §B5-c13, row by row, because
a card whose typed lines differ from what was typed is worse than no card.

### The redaction audit on these two directories

`audit-bench-log.py` reports **53 hits** across the 26 captures, and every one
was reviewed before the commit. It is advisory (exit 0) and it should stay
advisory, because both classes below are legitimate.

**`10.1.1.x` — 45 hits.** The bench-side private network the operator chose:
`10.1.1.1` is the address `IPCONFIG` gives the loader, `10.1.1.2` the
workstation, `10.1.1.10` the board under Linux. None is this unit's
configuration; the loader's own compiled-in TFTP address is `192.168.1.6` and is
already on `spec-check`'s allowlist for the same reason.

🔴 **MAC addresses — 8 hits, and this one needed a measurement rather than an
argument.** `L6a.log` prints `00:12:34:56:78:90`…`:94`, `:97` for the netdevs and
**`00:E0:4C:81:86:86` / `00:E0:4C:81:96:96` for `wlan0` / `pwlan0`** — a Realtek
OUI, which is exactly the shape of a real radio address, and `CLAUDE.md` forbids
committing anything that identifies this physical unit. `H601` at flash
`0x006000` holds this unit's MAC and radio calibration.

量: **all four are compiled into the `vmlinux` this seating uploaded**, as
literal bytes — `00:E0:4C:81:86:86` at file offset `0x288cc0`,
`00:E0:4C:81:96:96` at `0x288e04`, `00:12:34:56:78:90` at `0x2b5d64`,
`00:12:34:56:78:94` at `0x2b5e14`. They are SDK defaults in a GPL source tree
anyone can build, not values read from flash.

**And the mechanism agrees**: this boot mounted **my** initramfs, so none of the
vendor's init scripts — the things that normally read `H601` and program the
interfaces — ever ran. The board came up on the driver's built-in defaults,
which is also why the Ethernet MACs are the obvious `00:12:34:56:78:9x`
placeholder series.

⚠️ **This clearance does not transfer to a flash-root boot.** The moment the
vendor's userspace runs, the interfaces get their real addresses from `H601`,
and a capture of `ifconfig` from that boot **would** identify the unit. The
check is *are these bytes in the image I built*, and it has to be re-run, not
remembered.

### 🔴 The host-side captures, and what three of them do NOT prove

`L7a-host.txt` … `L7e-host.txt` are the workstation's `tcpdump -e -n 'icmp or
arp'` output for each interface tried, committed because `R3`'s **D5 requires
the host-side capture**, not only the board's own reply count, and
`PROGRESS.md`'s `R3-10` row says it is committed beside the board-side log.

`L7e-host.txt` (eth4) is 1,804 bytes and holds the whole exchange: the board's
ARP request, the workstation's reply, four ICMP echo request/reply pairs, and a
closing ARP from the workstation. **That is D5.**

🔴 **`L7b`/`L7c`/`L7d`-`host.txt` are one byte each — a newline — and that is
NOT evidence of silence.** A one-byte file looks identical whether `tcpdump`
captured nothing or `tcpdump` never ran. Their stderr went to `/dev/null`, so
nothing distinguishes the two. **This project does not accept a tool reporting
zero without a positive control, and here the control is missing for exactly
those three.**

**What IS evidenced**: `L7a-host.err` is committed and holds tcpdump's own
summary — `0 packets captured / 0 packets received by filter / 0 packets dropped
by kernel` — so `eth0`'s silence is a reading. And `L7e` proves the harness
captures when there is something to capture. For `eth1`, `eth2` and `eth3` the
evidence is **the board side alone**: `L7b`/`L7c`/`L7d.log` each report
`4 packets transmitted, 0 packets received, 100% packet loss`.

⚠️ **This does not weaken D5**, which is met on `eth4` with a complete
two-directional capture. It weakens the *subsidiary* claim that nothing left the
board on `eth1`–`eth3`. The fix for next time is one flag: keep stderr, or run
`tcpdump -w` per interface so an empty capture is a well-formed pcap with a
header rather than a zero-length file.

---

## 🔴 "zero flash bytes" — the sentence this file used five times and is not entitled to

**2026-08-30, at the desk.** `RUNSHEET` §B3's `G8b` row states the rule: two
256-byte `FLR`+`DW` reads entitle a write-up to *"the loader head and the `cr6c`
header are unchanged"* — **not** *"zero flash bytes written"*, which needs a full
re-dump hashed against `FLS-14` and costs the 6,300.1 s that dump's own metadata
records.

量, this file, before the correction below: the phrase stood in **five**
per-seating headings, and **not one of those five seatings ran an `FLR` bracket**.

| heading | seating | `FLR` bracket | what it is entitled to |
|---|---|---|---|
| `2026-08-23` | first silicon | none | *no flash-write command issued* |
| `2026-08-24` | seating 2, part one | none | as above |
| `2026-08-24b` | seating 2, part two | none | as above |
| `2026-08-25` | seating 3, `R1g-4a` | none | as above |
| `2026-08-25b` | seating 4, `R1g-4b` | none | as above |
| `2026-08-30` / `30b` | already corrected | none | already corrected on the day |

🔴 **And the seating that DOES hold the bracket has no heading in this
file at all.** 量 2026-08-30: `bench/` holds fourteen directories and this file
has a section for nine of them. The five with none are **`2026-08-24c`,
`2026-08-24d`, `2026-08-24e`, `2026-08-24f`** — the whole of `R0`, which is
where `G8-pre`, `G8a` and `G8b` live and therefore the only flash evidence this
project has — and `2026-08-26`, which carries its own `README.md` and is the
one legitimate absence.

So the index of *what each directory holds* skips the four directories a reader
chasing the flash question would go to first, while five headings it does carry
overstate what their own seatings measured. **Both halves of that are this
file's job.** ✅ **Both are done: the headings were corrected on 2026-08-30 with
the originals kept, and the four `R0` sections were written the same day** — see
*"`R0` — the four directories this index skipped"* above. 🔴 **Two numbers in
the paragraph this replaces were guesses and both were wrong**: 量 while writing
the sections, the four hold **81 captures across 18 prediction files**, not *"60
captures across thirteen prediction blocks"*. *(Original: "The headings are
corrected below with the originals kept; writing the four `R0` sections is not
done today and is carried in `PROGRESS.md` rather than half-done — they are 60
captures across thirteen prediction blocks and they deserve a session, not a
paragraph.")*

**What `R0` is entitled to**, so that the gap does not also lose the finding:
`G8-pre` → `G8a` → `G8b` read `0x000000` and `0x060000` three times
across three power cycles, and 量 2026-08-30 all three rounds are byte-identical
at both addresses — **512 of 4,194,304 bytes unchanged** across the span. That
is the strongest flash statement this project has, and it is 0.012 % of the part.
🔴 **What ran inside the span is TWO captured kernel executions and one
inferred**, not three measured: `G6` and `G7` are captures; the `24e` cycle's
boot is *推*, because `bench/2026-08-24e/A-catch.log` expires at the loader
banner and nothing recorded what the loader did next. *(This paragraph said
"across two power cycles" and "three kernel executions" until 2026-08-30; the
first was a miscount of the three directories the rounds live in and the second
promoted an inference. The R0 section above carries the per-round table.)*

**The headings are corrected in place below, with the original kept.** The rule
is not that a desk day may not say it — a session with the board unplugged
genuinely writes zero flash bytes and says so in `LOG.md` all the time. The rule
bites when **a seating happened**: then *"zero"* is a count, and a count needs a
reading.

🔴 **And the bracket that does exist has never sampled the region that cannot be
undone.** `G8a`/`G8b` read `0x000000` (256 of the loader region's 24,576 bytes)
and `0x060000` (the `cr6c` header, which no rule forbids writing). **`H601` at
`0x006000`–`0x007FFF` — this unit's MAC and radio calibration, *"not restored by
reset"* — is 0 of 8,192.** `bench/2026-08-30c/PREDICTIONS-B5-block2.md` §8 adds
it as a third region.

## 2026-08-30c and 2026-08-30d — seating 6's cards, written before it

**Written 2026-08-30 at the desk, before power.** One block covers both
directories — `bench/2026-08-30c/PREDICTIONS-B5-block2.md`, **31 cells**, frozen,
`0 of 31` at the desk — because the flash bracket is one experiment whose two
halves cannot share a power cycle.

| | |
|---|---|
| **`2026-08-30c`** | power cycle 3: `quietm`, the `FLR` bracket's first round, and 🎬 the artefact. Prefix `V-*` |
| **`2026-08-30d`** | power cycle 4: the bracket's second round and nothing else. Prefix `Z-*`. No upload, no `J`, no network — about ninety seconds |

**`V` and `Z`, and `Y` was deliberately skipped**: `Y` is the literal string typed
at the `FLR` confirmation prompt, and a cell named `Y-…` beside a `--send 'Y'` is
a reading waiting to be misfiled. The confirmations are `V-yes0`, `V-yes6`,
`V-yesh`.

🔴 **A policy this repository enforces under `bench/` is already broken in
`upstream/`, and it cannot be fixed by editing.** 量 2026-08-30: `upstream/BENCH-LOG.md`
prints actual `H601` byte values at named offsets, and commits a sha256 prefix over the
**4 KiB at flash `0x6000`** seven times — a superset of the window `FLS-20` refuses to
publish a digest for. `upstream` is a **gitlink** pinned at `4d3ff26`, so `git ls-files`
returns nothing under it and every sweep built on it — including `audit-bench-log.py`,
which walks `bench/**/*.log` only — has never looked there. The 4 KiB range carries more
entropy than the 256-byte window, so the 2^24 argument does not transfer directly; the
finding is that **`tools/flashwin.py` enforces the rule on the paths it knows about, and
the repository is larger than those paths.**

🔄 **2026-08-30, fourteenth session: that paragraph was right and it was not
specific enough.** 量, with `tools/leakscan.py --attribute`: the six bytes at
`H601+0x07` and `H601+0x13` are printed **verbatim** at
`upstream/BENCH-LOG.md:216`, labelled 「（裝置）」 — one line, one file, and the
only `UNIT` classification in 161 identity hits across both repositories.
**45 of `H601`'s 146 non-zero bytes are recoverable from the public
repository**, `HW_WLAN0_WSC_PIN` and the region checksum are not among them, and
the owner's decision is to leave `upstream/` alone because the device is end of
life. `SPEC.md` `FLS-22`; the reasoning and what is still open are in
`notes/leak-surface.md`.

🔴 **Two captures in this seating will not be in this directory, and that is a
first.** `V-rdh` and `Z-rdh` are `DW` reads of `H601`, so their bytes are this
unit's MAC and radio calibration. They go to
`$FWRE_WORK/rebuild/bench-only/b5-20260830c/`, **and not even their sha256 is
published** — a digest over a 256-byte window whose only unknown is 24 bits of
MAC is a 2^24 search. What is committed is the verdict and the *control*:
`tools/flashwin.py`'s `R1`/`R2` require the same renderer that computed their
expectation to reproduce `bench/2026-08-24d/G8a-rd0.log` and `G8a-rd6.log` byte
for byte, which it does.

⚠️ **The cost, stated rather than hidden**: `check-predictions.py` resolves a
cell to `<prefix>.log`, so those two sit outside the ordering discipline
entirely. That is the same hole this file already records for `CONT3` and for
`L6c-up`, but with a reason that will never be fixable rather than one that
could.

### 🔴 Both cycles ran, 2026-08-30. `31 of 31`

**21 captures in `2026-08-30c` and 10 in `2026-08-30d`**, plus `V0-rescue.json`,
`V1-put.json` and `V7a-host.txt`/`.err`, which are not cells. Every stop-if
stayed clear; `V-no`, `V-8a` and `V-8b` are branch cells and none of their
branches was taken.

| | |
|---|---|
| the bracket | all six reads matched: `V-rd0`≡`Z-rd0`≡`G8a-rd0.log`, `V-rd6`≡`Z-rd6`≡`G8a-rd6.log`, and `V-rdh`≡`Z-rdh`≡ the desk expectation. **768 / 4,194,304 = 0.0183 %** |
| `Z-ab` | **`00000001`** (量) — it says no `AUTOBURN 0` was typed since the last **reset**. 🔴 ⚠️ **Narrowed the same evening: it does not prove a power cycle.** `EW` writes it in four bytes with no bound check and prints nothing, and a warm `J BFC00000` restores it *and* reproduces `Z-A`'s cold slice — the two routes share one blind spot. `RUNSHEET` § Results, seating 6 |
| the one refuted cell | `V-3` is **849** bytes, not 401. Five predicted terms exact, a sixth asserted to be zero and worth 448. `CORRECTIONS-block2.md` |
| the artefact | 🎬 shot on cycle 3, `V-3` → `V-7a` |

**Corrections live in `bench/2026-08-30c/CORRECTIONS-block2.md`**, beside the
frozen block, which is not edited.

⚠️ **`bench/2026-08-25b/PREDICTIONS-b4-block2.md` carries a rendering defect that
will not be repaired.** 量 2026-08-30 by `spec-check`'s new `C10`: one paragraph
leaves a code span open, so the prose after it renders as code. Repairing it
would move the file's mtime, and `check-predictions.py` reads that mtime — every
one of its 2026-08-25 captures would then read as older than the prediction
naming it. The defect is recorded here and the file is exempt, with a control
(`T13`) that goes red if the file is ever repaired and the exemption left
behind.

## 2026-08-31 and 2026-08-31b — seating 7, `R3-9`/`R3-10b`. Two power cycles

| | |
|---|---|
| **`2026-08-31`** | power cycle 5: `quietmc`, the `FLR` bracket **with a negative control for the first time**, and the MTD path. Prefixes `W-*` and `M-*` |
| **`2026-08-31b`** | power cycle 6: the same image again — the `FW-32 殘留` null — plus a re-sited bracket and two safety cells. Prefixes `X-*` and `X2-*` |

🆕 **2026-08-31, desk: eighteen of these captures are now a test corpus as well as a record.** `tools/flrbracket.py`'s controls read the nine `*-flr*.log` echoes, the eight `*-yes*.log` replies and `W-no.log` — `P1` requires all nine to classify `PROCEED` against their own three numbers, `Q2` re-derives those numbers from each capture's own `.meta.json` rather than trusting a table, and `P2` is a regression on the defect `CORRECTIONS-block3.md` §9 records: `W-flr0a` is the echo the previous instrument wrongly aborted, and it is committed for that reason. 🔴 **So these files are load-bearing for CI now**: deleting or rewriting one turns `flrbracket --self-test` red, which is the intended behaviour and not a fragility — a corpus that can go missing without anything noticing is the population control this repository keeps writing.

**Five prediction files, and four of them were written at the bench.** That is
not untidiness: three of the four exist because the card was refuted while it
was being run, and a recovery cell without a prediction written first is not a
reading.

| file | cells | gate | why it exists |
|---|---|---|---|
| `2026-08-31/PREDICTIONS-B5-block3.md` | 54 | **42 of 54** | the card, written 2026-08-30 at the desk |
| `2026-08-31/PREDICTIONS-B5-block3b.md` | 2 | 2 of 2 | `M-b`/`M-c` died on `wc: not found`; recovered with `busybox wc` |
| `2026-08-31b/PREDICTIONS-B5-block3c.md` | 2 | 2 of 2 | the read rate and the line counts both had n=1; repeated on cycle 6 |
| `2026-08-31b/PREDICTIONS-B5-block3d.md` | 12 | 12 of 12 | cycle 6's bracket was void — DRAM retained cycle 5's contents — so it moved to fresh addresses |
| `2026-08-31b/PREDICTIONS-B5-block3e.md` | 2 | 2 of 2 | the safety property had one instance; this gives it a second, and tests the absent even minor |

**The twelve that did not run in block 3** are cycle 6's ten bracket cells,
voided by their own pre-read stop-if, plus `X-ph` and `X-pc`, whose captures were
moved out of the repository — see below. Corrections:
`2026-08-31/CORRECTIONS-block3.md`, nine items.

### 🔴 The captures that are deliberately not here, and this seating doubled them

**Eight files**, in `$FWRE_WORK/rebuild/bench-only/b5-20260831/`:
`W-rdh`, `W-rdc`, `X2-rdh`, `X2-rdc` (the `H601` read-backs, as designed) and
🔴 `X-ph`, `X-pc` (the `H601` **pre-reads**, moved mid-seating).

The last two are the finding. The card writes pre-reads under `bench/` because a
pre-read is *expected* to be DRAM garbage — **and that expectation is the cell's
own hypothesis.** When it failed, two files inside this repository contained this
unit's MAC and radio calibration.

> A containment rule whose correctness depends on the experiment coming out the
> expected way is not a containment rule.

量 `git status` **before** the move: both were `??`. Nothing entered history.
`PREDICTIONS-B5-block3d.md` writes every `H601` capture outside the repository,
pre-read included. Their ordering is therefore unenforced by
`check-predictions.py`, which is the carried-forward row *a capture that cannot
be committed*, now at eight files.

### What this seating establishes, and the one sentence it still cannot say

* 🟢 **The bracket has a negative control.** Every `FLR` destination was read
  first; all eight pre-reads (four per round, after the re-siting) differed from
  their expectations, so *the `FLR` wrote* is measured rather than assumed.
* 🟢 **1,024 of 4,194,304 bytes**, four windows, byte-identical to the
  2026-08-16 dump on both rounds — including `0x006400`, the canary page and the
  only span this unit has ever been seen to change. `H601` reach **6.3 %**.
* 🟢 **Block 3d's round ran AFTER a complete rlxfw boot** — kernel, userspace,
  4 MiB through `mtd_read`, an `EACCES` write attempt, a ping. First evidence
  here that a full boot of my firmware leaves those windows unchanged.
* 🟢 **`W-3` and `X-3` are byte-identical to `V-3`**, 849 bytes, sha256
  `8317e7c9…` — three boots of my kernel across two days, identical on the wire.
* 🔴 **It still does not license "not one flash byte is written".** 1,024 bytes
  is 0.0244 % of the part; the sentence needs a full re-dump hashed against
  `FLS-14` (`RUNSHEET` `G8b`), and this seating ran none.

### The host-side capture

`2026-08-31/W7a-host.txt` — 12 packets, both directions, ARP both ways.
`W7a-host.err` carries the adapter's `enx<12 hex>` name, as
`2026-08-30b/L7a-host.err` and `2026-08-30c/V7a-host.err` already do. 量: that
is the **workstation's** adapter, `HOST` class under `leakscan --attribute`, not
this unit — the row that decided it is `SPEC.md` `FLS-22`. Unchanged practice,
checked rather than assumed.
