# Reading `SPEC.md`

[`SPEC.md`](../../SPEC.md) is the index of every number this project holds about one
TOTOLINK N150RT (RTL8196E, Lexra `RLX4181` core), written in Chinese. This page is its
English entry: what a row is, where rows live, the rows cited most, and how to find a value
without reading Chinese. `SPEC.md` owns no finding: each row links the file that does, and
the owner wins where they disagree. Counts are as of `e949311f` (2026-10-17), before this page.

## A row

Most sections have seven columns: `id`, stable, cited by other files instead of a line
number; `項目`, the item; `值`, the value with its date and the capture it came from; `V`,
where the value came from; `N`, where the field's name and meaning came from; `來源`, the
sources; `擁有者`, the file that owns the finding (`同上`: the row above's owner). `V` and
`N` use one alphabet:

| Mark | Meaning |
|:-:|---|
| 量 | measured on this unit; the value names the capture |
| 讀 | read out of code or a dump; static, true of the named artefact |
| 推 | inferred, pending a measurement |
| 文 | read in a document (datasheet, vendor header); never enough on its own for a value in code |
| 算 | derived by arithmetic from values the repository already holds |
| — | not established: the value says `留白`, `未定` or `未讀` (open; § 17 says what settles it), or `§18` / `選定` (not a value to measure) |

Sources: **A** this unit's flash dump and binaries cut from it; **B** vendor GPL source, a
different SDK generation, which explains a constant but never replaces A; **C** `upstream/`
at `4d3ff26`, measurements on this same unit; **D** a draft datasheet for the embedded-DRAM
variants, not this chip; **E** vendor Linux headers; **P** this unit's markings and photos;
**S** this repository's bench transcripts; **X** third-party specs, listed to be refuted.
A row naming one source has not met the house rule of two. One row, whole:

    | `IDN-06` | PCB 日期標 | `18.15` —— 2018 年第 15 週 | 量 | 推 | P | 同上 §6 |

Two marks, because a value can be right while its name is wrong: the ink `18.15` was read
off this board, so the value is 量; that it is a date code for week 15 of 2018 is an
inference, so the name is 推. The one source is the board (P); the owner is the row above's,
`upstream/notes/hardware-inspection.md`, at its § 6. **A cell grows by revisions appended to
its end**, each dated and marked `🔄`, `🟢` or `🔴`, so its first sentence can be out of date:
read a cell to its end. `殘留` is the question left once a value is settled.
`tools/spec-check.py` checks each row's form — a unique id, legal marks, an owner that exists
and still holds every literal value — never whether a value is right.

## The sections

| § | Holds | Rows | Id prefixes |
|--:|---|--:|---|
| 0 | how to read a row: the legend above | — | — |
| 1 | identity | 8 | `IDN` |
| 2 | silicon: SoC and CPU core | 58 | `CPU` |
| 3 | memory: SDRAM | 16 | `MEM` |
| 4 | flash | 26 | `FLS` |
| 5 | Ethernet: switch, PHY, ports | 72 | `NET` 70, `FW` 2 |
| 6 | radio | 7 | `RF` |
| 7 | board: power, connectors, headers | 13 | `BRD` |
| 8 | address map | 17 | `MAP` |
| 9 | registers read or written on this unit; columns address, name, reading | 39 | `REG` |
| 10 | clocks, timers, watchdog, interrupts | 42 | `CLK` 29, `IRQ` 13 |
| 11 | the boot loader | 50 | `LDR` |
| 12 | the vendor firmware found on this unit | 23 | `FW` |
| 13 | flash contents read from this unit; columns offset, content, length | 15 | `FLM` |
| 14 | toolchain and libc, and the kernels built with them | 105 | `TC` 57, `FW` 46, `MEM` 2 |
| 15 | rlxfw's design targets: chosen, not measured, so no marks | 10 | `TGT` |
| 16 | published specifications and where they are wrong | 3 | `PUB` |
| 17 | open values; columns what is missing, what settles it, owning gate | 96 | the id of the row each belongs to |
| 18 | what is deliberately absent: MAC, serial, WPS PIN, radio calibration, the dump, the datasheets | — | — |
| 19 | rows that belong to an earlier section and cannot be inserted there (below), every topic | 331 | `FW` 176, `NET` 103, `CLK` 20, `CPU` 15, `FLS` 6, `TC` 5, `LDR` 2, `MEM` 2, `IRQ` 1, `LIC` 1 |

835 rows outside § 17, 846 ids. § 17's 96 entries carry the id of the row each belongs to —
85 for rows elsewhere (81 ids, four with two entries), 11 ids that exist only there — and 22
more lines are closed entries, struck through. **Find a row by its id, not its section:** a row
inserted mid-file would move every line below it, which records cite by number, so new rows go
at the end of § 19 (`FW-110`), in order of discovery: 103 of the 173 `NET` rows are there.

## The rows cited most

For each id: its occurrences as a whole word (`git grep -w`'s rule) in every tracked text
file outside `bench/`, `SPEC.md` included and its id cells excluded — 597 files; 774 of the
846 ids are cited at least once. Re-count one with `git grep -Iow FW-35 -- ':!bench' | wc -l`
less its id cells (one, plus one per § 17 entry). The 20th has 72, the 21st (`CLK-02`) 71.

| # | Row | § | Cites | Files | V | What the row holds |
|--:|---|--:|--:|--:|:-:|---|
| 1 | `FW-35` | 14 | 170 | 24 | 量 | the kernel's boot split into initcall phases (0.63 s for levels 0–5, where rlxfw's `arch_initcall` runs), and the rule for reading a `.timing` row that the split exposed |
| 2 | `CPU-45` | 2 | 147 | 29 | 量 | D-cache coherence with memory written by something other than the CPU: it read-allocates, and an uncached read invalidates the resident line |
| 3 | `CPU-57` | 2 | 145 | 10 | 量 | which instructions the core implements, a 75-row census with both controls: branch-likely, the conditional traps, `clz`, `mul` and `sync` trap; the Lexra multiply-accumulate extension runs |
| 4 | `FW-34` | 14 | 124 | 21 | 量 + 讀 | the kernel's flash read path returns this unit's flash: four reads over two power cycles match the dump's counts; the path is programmed I/O, and the vendor `copy_from` that could read short is not on it |
| 5 | `CPU-25` | 2 | 118 | 38 | 量 | cache geometry: the 16 KiB I-cache measured 2-way, 512 sets, 16-byte lines; the 8 KiB D-cache's geometry read, never measured; no L2 |
| 6 | `FLS-26` | 4 | 116 | 28 | 量 | flash against the 2026-08-16 dump by on-device digests: the loader region is unchanged; a two-level map proved 99.61 % equal and two 4 KiB sectors, `0x9000` and `0xD000`, different; `H601` skipped by rule |
| 7 | `NET-67` | 5 | 116 | 12 | 量 | the NIC's wedge under sustained TCP is a TX stall: all four TX descriptors stay with the engine and the stopped queue is never woken, while RX stays healthy |
| 8 | `CLK-15` | 10 | 111 | 20 | 量 | the loader's silence after `Booting...`, about 0.35 s: cold and warm boots first looked disjoint (seven each), then overlapped at 18 and 11, and on a raw host clock cold is not slower (§ 17, `CLK-43`) |
| 9 | `FW-124` | 19 | 109 | 32 | 量 | bench cards' host commands are checked by each tool's own argument parser before power, with one grammar shared by checker and runner |
| 10 | `CLK-08b` | 10 | 99 | 26 | 量 | the watchdog's counting clock: 14.9650 MHz in the loader's state, which is not the divided timer clock, and about 200 kHz under Linux, which rewrites the divider; what it counts is open |
| 11 | `NET-61` | 5 | 94 | 13 | 量 | a multi-frame burst can leave the engine's two RX position registers apart while the driver reads both with one index, so a frame arrives with another's length; the gap, first read as a fixed 4, has been seen at every value from 1 to 7 |
| 12 | `FLS-14` | 4 | 91 | 25 | 量 | the full 4 MiB dump: 105 minutes over the console, read twice byte-identical, two windows equal to the device's own `DW` output; never committed (§ 18) |
| 13 | `NET-54` | 5 | 90 | 14 | 量 | a wedge after a flood in which the switch port counted no inbound frame; a cold power-on cleared it; its cause, and what a watchdog reset does to it, are open, and the shape recurred (`NET-124`) |
| 14 | `FW-175` | 19 | 89 | 15 | 量 | rlxfw's own userspace on the silicon: six programs run, privilege separation shows in `ps`, and `dnsfwd`'s `setuid(0)` is refused |
| 15 | `NET-78` | 19 | 76 | 9 | 量 | a second NIC failure, unlike `NET-67`: the engine takes and returns every TX descriptor, yet no frame reaches the wire; two independent cold boots |
| 16 | `MEM-17` | 14 | 75 | 36 | 量 | DRAM keeps written data across a power cycle, so a read-back equal to flash proves nothing unless its destination was pre-read |
| 17 | `NET-13` | 5 | 75 | 24 | 量 + 推 | which RJ45 jack is which switch port: WAN and LAN1–3 measured as ports 0–3, LAN4 → 4 by elimination; ports are named by number, since two builds name their netdevs in mirror order |
| 18 | `FW-40` | 14 | 74 | 24 | 量 | the vendor's reset-button path as compiled into an image built here, read from its code and closed on the silicon: a 2–4 s press signals PID 1, which ignores it; 5 s or more sets a flag only `/proc` handlers read |
| 19 | `FLS-22` | 4 | 73 | 17 | 量 | how much of `H601` the public `upstream/` already exposes — at least 45 of its 146 non-zero bytes, a lower bound — and the decision to accept it; offsets and counts only, never values |
| 20 | `CLK-17` | 10 | 72 | 24 | 推 | `TC0CNT`'s rate in the loader's state, 14,286,057 Hz, derived from two measured values; under Linux the driver derives 200,000 Hz at init |

## Without reading Chinese

Ids, numbers, addresses, register names, paths and code are ASCII, so search for them:
`git grep -n NET-102 SPEC.md` finds a row, `git grep -n TC0DATA SPEC.md` every row naming
the register; at 1.7 MB the file is easier to search than to scroll. Read `V` and `N` with
the table above, then follow the owner link: of the 140 files owner cells name, 134 are
English apart from the marks, the other six being the log, `SPEC.md` itself, `PROGRESS.md`,
two files under `docs/history/` and `upstream/test-ledger.md`; fifteen rows name the private
planning directory, which is not published. A row missing from its section is in § 19.

## What this page does not establish

The counts measure mentions, not dependence: `CPU-45` has 119 of its 147 in records —
`LOG.md`, `docs/log/`, `docs/history/`, `CHANGELOG.md`, `docs/GATE-RESULTS.md` — cited for
its history. Each summary is this page's reading of its row at `e949311f`; the row, and above
it the owner, win. "English" means under 1 % of a file's non-space characters are CJK.
