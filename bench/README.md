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

First silicon. One power cycle, zero flash bytes written.

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

One power cycle, **zero flash bytes**, about twenty minutes. Every cell went
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
