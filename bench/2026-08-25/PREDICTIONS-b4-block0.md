# PREDICTIONS — Session B4, block 0

**Written 2026-08-25, at the desk, before power is applied.**
`tools/check-predictions.py` checks that claim against this file's mtime and each
capture's `.log` mtime. Nothing here may be edited after the block has run — even
a typo fix moves the mtime and the check fails, correctly. Corrections go in a
new file.

## Why this file exists beside `bench/2026-08-26/PREDICTIONS-b4-block0.md`

The seating was written for 2026-08-26 and is being run on **2026-08-25**. The
2026-08-26 file's own rule — *"if the seating slips past 2026-08-26, this file is
not edited; a new block is written for the new directory"* — is applied here to
the case it did not name, the seating moving **earlier**. So:

- **`bench/2026-08-26/PREDICTIONS-b4-block0.md` is not edited and not deleted.**
  Its mtime is **2026-08-25 06:09**, and that is the timestamp that actually
  establishes pre-registration: every predicted value below was fixed then, about
  eight hours before this file was written and before this seating's power-on.
- **Every device prediction below is copied from it verbatim** — every table,
  every byte count, and the 32-word `H0a` block. `diff` the two files and there
  are **six hunks, exactly one of which is inside a prediction**: `A-catch`'s
  `tool_version`, which is the instrument's version and not the device's
  behaviour, and which is 🔴 **corrected from `1.2` to `1.3` in front of the
  reader** for the reason stated below. Of the other five: two are the date, in
  the nine capture paths and in the command line; two are prose that named `H2`
  as something this seating still does (`R1g-4b` is where it went); one adds the
  two paragraphs marked 🆕/🔄 below, which say why `H0b` word 9 and `H0d-b` are
  still worth taking with `H2` gone. **Stating this as "only the paths changed"
  would itself have been false**, and the diff is the check on the sentence.
- One directory per power cycle (`bench/README.md`), named by the date the
  captures were taken. `bench/2026-08-26/` holds no captures and now never will.

Instrument: `tools/console-capture.py` — 🔴 **1.3, and the 2026-08-26 file
predicted `tool_version: "1.2"`.** 量 at the desk before power: `TOOL_VERSION =
"1.3"` in the working tree, clean, bumped by commit `4f5331e` on 2026-08-25 at
02:41 — **before** that file was written at 06:09. The seventh committed place
still carrying the old number, and the same defect class as the four `43ec0e0`
found. **This is the one prediction on this page that is not verbatim**, and it
is corrected here rather than left to fail, because a failed prediction about the
instrument's own version string is noise in the column that is supposed to be
signal. 1.2 → 1.3 added `--esc-period` and the achieved-period metadata (`H3c`
needs both); `terminate_esc_line`, which is what every ESC prediction here rests
on, arrived in 1.2 and is untouched. Nothing in this block uploads or executes
anything: **nine reads and one ESC stream, zero bytes written to the device.**

Blocks 1 (`H1`) and 3 (`H3`) are written at the bench immediately before their
own cells, because each is conditional on a reading in the block before it — the
whole of `H1` on the upload completing. **Block 2 (`H2`) does not exist this
seating**: `H2` is deferred to `R1g-4b` (`docs/rlxprobe-audit-2026-08-25.md`,
`RUNSHEET.md` §H2's deferral box). A block written for a cell that cannot run is
a block that fails for the wrong reason.

---

## What this block is for

`H0a` decides whether `probe2` runs at all — in `R1g-4b`, not here. Until
2026-08-25 its expected value cited a file that did not contain it, so the cells
that make it checkable did not exist. Two of the nine are here because a reading,
not an argument, should settle them:

1. **`H0a2` compares the vector against the source of its own copy**, read on the
   same power cycle. It needs no predicted value, so it covers the twenty-one
   words nobody in this repository had predicted before today.
2. **`H0a3` reads the same 32 words through the uncached alias.** `H0a` goes
   through KSEG0; nothing else in the session separates *the vector is not there*
   from *a stale D-cache line is being handed to `DW`*.

---

## Cells, in order

```cells
bench/2026-08-25/A-catch
bench/2026-08-25/A0
bench/2026-08-25/H0a
bench/2026-08-25/H0a2
bench/2026-08-25/H0a3
bench/2026-08-25/H0b
bench/2026-08-25/H0c
bench/2026-08-25/H0d-a
bench/2026-08-25/H0d-b
```

Every command is `/usr/bin/python3 tools/console-capture.py capture --port
/dev/ttyUSB0 --baud 38400 --out bench/2026-08-25/<cell>` plus the arguments in
the row. **No line reaches 128 characters**; the longest is 14.

`DW` reply size is `len(cmd) + 2 + 47 × lines + 9` bytes — exact on six replies
across two seatings, so every byte count below is a prediction and not a
description. Address hex, **length decimal**, `4 × ceil(N/4)` words printed four
to a line (`LDR-07`).

---

### A-catch — `--esc 180 --seconds 200 --cr-settle 3`

The capture starts **first**; power is applied while ESC is streaming. `180` and
not `45`: a 45 s window was missed on 2026-08-24 with the boot beginning at
t = 64.2 s, and it cost a power cycle.

| | prediction |
|---|---|
| boot text | the first **181 bytes** byte-identical to `bench/2026-08-24c/A-catch.log` — this would be the fourth consecutive |
| after the prompt | *n* × (128 ESC → `Unknown command !` → `<RealTek>`). *n* is **not** predicted; it depends on when power is applied |
| last bytes | a prompt, not a run of ESC — 1.2 writes its own terminating CR |
| metadata | 🔴 `tool_version: **"1.3"**`, `cr.esc.written: true`, `cr.esc.prompt_seen: true`, and `esc.esc.achieved_period_s` present |

**Refutes**: nothing about the device. It is the window, and a `prompt_seen:
false` beside a full settle is what a missed one looks like from the instrument's
side.

### A0 — `--send 'DW 8040DBC0 1' --seconds 4`

| | prediction |
|---|---|
| bytes | **71**, byte-identical to `bench/2026-08-24b/A0.log` and `bench/2026-08-24c/A0.log` |
| content | `8040DBC0:` then `8040B070 00000000 80409A9C 8040B074`, then the prompt |

**Two jobs, and the second is why it is first.** Rule 1: one command with a
precomputed answer, re-establishing that re-opening the port did not disturb the
board. And it **spends the post-re-enumeration throwaway** — the first command
after the console adapter re-enumerates is echoed and not acted on, signature
*echo + prompt + no data line*. 🔴 **That signature is indistinguishable at the
bench from `H0a` finding nothing**, and `H0a` is the cell that forbids `probe2`.
Any `Unknown command !` here, or a reply with no data line, and the cell is
re-sent before anything is read into.

### H0a — `--send 'DW 80000080 32' --seconds 6`

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| content | the 32 words below, in `DW`'s own layout. The loader prints hex **upper case**, tab separated |

```
80000080:  401B6800  00000000  00000000  3C1A8041
80000090:  275AEB40  337B007C  035BD021  8F5A0000
800000A0:  00000000  03400008  00000000  00000000
800000B0:  00000000  401A6000  00000000  001AD0C0
800000C0:  07400003  03A0D821  3C1B8041  8F7BDD40
800000D0:  03A0D021  277DFF50  AFBA008C  AFA30024
800000E0:  AFA00018  40036000  AFA20020  AFA300A8
800000F0:  AFA40028  40036800  AFA5002C  AFA300AC
```

🔴 **The gate is words 0–10 only** — `mfc0 k1,c0_cause` / nop / nop /
`lui k0,0x8041` / `addiu k0,k0,-5312` / `andi k1,k1,0x7c` / `addu` /
`lw k0,0(k0)` / nop / `jr k0` / nop. Words 11–31 are the tail of the 128 bytes
`trap_init` copies, and **they are not zero**: word 13 `401A6000` is
`mfc0 k0,c0_status`, the first instruction of the loader's IRQ handler at
`0x80400580`, dragged in because the copy is 128 bytes and the dispatcher is 44.

**Refutes**: that the loader populated a vector at `0x80000080` rather than at
MIPS32's `0x80000180`. Three sources agree and none says `0x180`.
⚠️ **It does not refute anything about which base the core fetches from.** That
is `Status.BEV`, no loader command reads CP0, and only `probe2` can measure it.

**What each miss means** is in `RUNSHEET.md` § Session B4 under *If `H0a` does not
match*, written before this file and not restated here.

### H0a2 — `--send 'DW 8040054C 32' --seconds 6`

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| content | 🔴 **word for word identical to `H0a`, all 32** — this is the source `trap_init` copies from |

**Refutes**: that the copy landed intact — and it needs no predicted value, which
is the point: it is the only cell covering words 11–31 without trusting a list.
Its positive control is built in: a broken `DW`, or an address form being
rewritten under it, cannot produce two agreeing reads.

⚠️ **`0x8040054C` is not 16-byte aligned, and no `DW` in this project has ever
been given an unaligned address** — every measured reply so far started on a
16-byte boundary. If the first printed address is `80400540` rather than
`8040054C`, then `DW` aligns its start down. **That is new about `LDR-07` and is
worth more than this cell**; the comparison is then done by printed word address
rather than by line position.

⚠️ `0x8040054C` is stage 2's own image **in DRAM**, not ROM. The loader runs from
`0x80400000` in KSEG0; the ROM window is `0xBFC00000`. This is a RAM-to-RAM
identity and must not later be read as agreement with flash.

### H0a3 — `--send 'DW A0000080 32' --seconds 6`

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| content | identical to `H0a`, and the first printed address is `A0000080` |

**Refutes**: that a stale D-cache line is what `H0a` read. `DW` forces the address
into KSEG0 only when bit 31 is clear, so `0xA0000080` passes through uncached.
🔴 **A difference is worth more than the cell**, and `probe2` does not run until
it is explained — `probe2` installs its handler through KSEG1 and would be racing
the same line.

If the printed address comes back `80000080`, the loader rewrote it after all and
this cell measured nothing. That is checkable from the capture itself.

### H0b — `--send 'DW 8040EB40 32' --seconds 6`

| | prediction |
|---|---|
| bytes | **401**, 8 lines |
| content | `[0] = 80400580`, `[23] = 804007C0`, **the other thirty = 80400BE8** |

Line by line: line 0 is `80400580 80400BE8 80400BE8 80400BE8`; lines 1–4 are four
`80400BE8` each; line 5 is `80400BE8 80400BE8 80400BE8 804007C0`; lines 6–7 are
four `80400BE8` each.

**Runs whatever `H0a` did**, and it is what separates the failures: `.bss` is
zeroed at boot by the loop at `0x8040046C`, so an **all-zero `H0b` means
`trap_init` never ran**, and that is distinguishable from every other reading. A
correct `H0b` beside a garbage `H0a` says the table is live but the vector copy is
not where three sources put it.

**Refutes**: that `exception_handlers[32]` is at `0x8040EB40`. `SPEC.md` `CPU-26`
named `0x8040A5C0` until 2026-08-25 and that is the boot state machine. The
30-of-32 shape is a positive control a wrong table cannot fake.

🆕 **And index 9 is the one word this seating owes another document.**
`docs/rlxprobe-audit-2026-08-25.md` § Must-fix 1 rests on
`exception_handlers[9] == 0x80400BE8` being *讀* and unverified; it is word 9 of
this reply — line 2, column 2. `80400BE8` confirms it; anything else drops that
finding's severity, and either way it is a reading rather than an argument.

### H0c — `--send 'DW 80000000 8' --seconds 4`

| | prediction |
|---|---|
| bytes | **118**, 2 lines |
| content | 🔴 **not predicted.** `0x5A5AA5A5` is one candidate — stage 1's DRAM-sizing probe writes it — but stage 1 writes several patterns and which lands last was never traced |

**Refutes**: nothing on its own, and that is why it is here rather than in the
write-up. It is the **precondition of an escalation `tools/rlxprobe/cache.S` has
already withdrawn**: that file argues there is no demonstrated brick path because
`0x5A5AA5A5` decodes as `BLEZL` and cannot reach loader code. 🔴 **If word 0 has
top six bits `000010` (`j`) or `000011` (`jal`), that argument is void and
`probe1` does not run until it has been re-made.**

### H0d-a — `--send 'DW 80A00000 8' --seconds 4` · H0d-b — `--send 'DW 80A01000 8' --seconds 4`

| | prediction |
|---|---|
| bytes | **118** each, 2 lines each |
| required | word 0 is **neither `DEADC0DE` nor `524C5831` nor `524C5832`** in either |

**Refutes**: that a result block read later in this seating belongs to this
seating. `MEM-10` measured a **two-word** canary at `0x80A00000` surviving three
warm resets; **`0x80A01000` has never been read on this device at all**, and
`probe2` is about to poison 537 words from it. Same job `G0` did for `R0` — it
turns *the block is left over from the previous payload* from an inference into a
comparison.

🔄 **`H0d-b` is kept although `probe2` does not run this seating.** It is one free
read; it is the only baseline `R1g-4b` will have for a window this device has
never shown; and taking it on the seating that does *not* write there is strictly
better than taking it on the seating that does.

Free and unasked, at no cost: if `H0d-a` comes back byte-identical to
`bench/2026-08-24c/G0-head.log`'s words across a power cycle, this device's SDRAM
power-on state is deterministic at that address. Nothing here turns on it.

---

## What this block does not do

- **It writes nothing.** Nine `DW` reads and one ESC stream. No `EW`, no `EB`, no
  `put`, no `J`, no flash.
- It cannot measure `Status.BEV`, and therefore cannot say which vector base the
  core fetches from. Only `probe2` can, and `probe2` is not run this seating.
- `H0a2` proves the copy landed, not that it agrees with flash.
- Nothing here is a cache-model reading. `probe1` is block 1.
