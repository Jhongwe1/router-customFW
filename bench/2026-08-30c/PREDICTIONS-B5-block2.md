# PREDICTIONS — Session B5, `R3-8b` + `R3-10`, block 2: `quietm`, the flash bracket, and the artefact

**Written at the desk on 2026-08-30, before power.** Every value below was
measured on this host today or read out of a capture already committed, and none
of it is conditional on a reading taken at the bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in a new
file — `CORRECTIONS-block2.md`, beside this one.

**This block covers TWO power cycles, and that is deliberate.** Cycle 3 is
`quietm` (`bench/2026-08-30c/`) and cycle 4 is the second half of the flash
bracket (`bench/2026-08-30d/`). They are one file because the bracket is one
experiment: `Z-rd0` means nothing except against `V-rd0`, and a block that
predicted only the half that fits in one power cycle would be predicting half a
`cmp`. §15 predicts what the check reports if cycle 4 does not happen.

**Why this block exists now and did not yesterday.** §B5's own heading reads
*"Power cycle 3 — and what it is spent on is decided by `L-3`, not by this
card"* (`RUNSHEET.md:1392`, quoted verbatim; an earlier draft of this line
paraphrased it inside quotation marks). `L-3` reached
D4 — `bench/2026-08-30b/L5a.log` and `L5b.log` both returned — and by that
table's own first row the answer is `quietm`. The decision is made, so the
prediction is writable.

---

## §0 THE CARD — every line that gets typed, in order

**This is the only part of this file that is read at the bench.** Everything
below it is the reasoning that produced it.

🔴 **Every row carries a terminator.** `console-capture.py capture` with neither
`--seconds` nor `--idle` does not return (量 2026-08-29, `rc=124`), and as of
today it **refuses** rather than hanging. The numbers are sized against the
loader's *marginal* reply rate, **3,458–3,497 B/s** (`SPEC.md` `LDR-40`, as
corrected by `bench/2026-08-30/CORRECTIONS-block0.md` §7) — not the 3,840 line
rate and not the whole-reply 3,512–3,726.

### Before power — at the desk, and it is two commands

```
sha256sum /home/key/fwre-work/rebuild/bench-only/b5-20260830/rlxfw-quietm-20260830.bin
  cf8a93d73025292ddc61f28c7172ad00985efad8569bdfbcae69def3a10dfb8a

/usr/bin/python3 tools/flashwin.py --self-test
  19 passed, 0 failed
```

🔴 **That number was `13` on this card until 2026-08-30 and the tool printed
`19`.** `flashwin` was rewritten from 13 controls to 19 in the **same session
that wrote this card** — an adversarial pass ran 45 mutants against the first
self-test and 24 survived, three of them printing this unit's MAC — and nothing
re-read the pre-flight afterwards. A stale expectation on the FIRST line of a
pre-flight is the one place a mismatch reads as *wrong version, stop*. 量
2026-08-30 on this host, with the dump present: `19 passed, 0 failed`. **On a
machine without `$FWRE_WORK/dumps/` it is `16 passed, 0 failed` and one skip
line covering 3 (16 + 3 = 19)** — `R1`/`R2`/`R3` read this unit's own 4 MiB flash, which can
never be committed. Either line is correct; `13` is not.

⚠️ **The initramfs declaration moved today and this artefact does not carry the
change.** `config/rlxfw-initramfs.tsv` gained `nod /dev/mtdblock1 b:31:1 0400`
(`R3-9`, `SPEC.md` `FW-28`–`FW-30`). It is in **no** built image, and
specifically not in `rlxfw-quietm-20260830.bin`. **The sha256 above is the
authority for this seating**; the node lands on the next build, and that build
moves `V-0t`/`V-2c`, whose `0x805FABF0` is derived from *this* image's
`image_end`.

🔴 **Every path on this card is literal, and `$FWRE_WORK` appears nowhere
in a typed line.** 量 2026-08-30, in this host's login shell and in an
interactive one: `$FWRE_WORK` is **empty**, and nothing in `~/.bashrc`,
`~/.profile`, `/etc/profile` or `/etc/profile.d/` exports it. `CLAUDE.md` names
the value and the build tools default to it (`${FWRE_WORK:-/home/key/fwre-work}`),
but `console-capture.py` and `loader-tftp.py` take a plain path with no fallback.
量, the `V-rdh` line as it was first written on this card:

```
--out /home/key/fwre-work/rebuild/bench-only/b5-20260830c/V-rdh
  PermissionError: [Errno 13] Permission denied: '/rebuild'
```

An uncaught traceback, not one of the tool's clean refusals — and it would have
fired **after** `V-flrh` and `V-yesh` had already spent the `H601` read.

The second one is not ceremony. `V-rdh` has no committed capture to `cmp`
against and can never have one (§8.3); its expectation is a file this tool wrote
today, and the tool's own R1/R2 are what say the renderer that wrote it
reproduces two readings taken off this device on 2026-08-24.

The host preflight — the long-lived WSL process, re-reading both busids, the NIC
at `10.1.1.2/24`, `/usr/bin/python3` and the board-off 3-second capture — is
`RUNSHEET` §B5's and is not restated here. One owner.

### Power cycle 3 — `quietm`. `bench/2026-08-30c/`

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`OUT X` = `--out bench/2026-08-30c/X` — **one token**, not two. ⚠️ Typed as two, `argparse` says `unrecognized arguments: V-A` and the cell has to be retyped; 量 2026-08-30. Seconds, not a power cycle, but it is on the card because the card is what is read.

| # | typed / run | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **V-A** | `CAP OUT V-A --esc 25 --esc-period 0.002 --seconds 40` | the ESC window, then `<RealTek>`; the 181-byte cold slice, §3 | — | no prompt → power off. That is the seating |
| **V-0r** | `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-08-30c/V0-rescue.json` | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1`, in that order | — | any of the three absent |
| **V-0ab** | `CAP OUT V-0ab --send 'DW 8040D4A0 1' --seconds 4` | the word at `0x8040D4A0` = **`00000000`** | **71** | ≠ `00000000` → **STOP. Nothing is uploaded** |
| **V-0t** | `CAP OUT V-0t --send 'DW 805FABF0 8' --seconds 6` | two lines of DRAM. **Record both.** Line 1 must **not** be sixteen zero bytes | **118** | line 1 already all-zero → `V-2c`'s first half is void this seating; say so and carry on |
| **V-1** | `loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/bench-only/b5-20260830/rlxfw-quietm-20260830.bin --filename rlxfw-quietm --rescue-report bench/2026-08-30c/V0-rescue.json --expect-load 80500000 --yes` | **1,027,072** bytes accepted | — | any refusal → read it. **Never `--allow-autoexec`** |
| **V-2a** | `CAP OUT V-2a --send 'DW 80500000 8' --seconds 6` | `80500000: 00000000 00008021 40906000 00000000` · `80500010: 00000000 00000000 3C108060 2610AC00` | **118** | 🔴 the word at **`0x8050001C`** ≠ `2610AC00`, or **`0x80500018`** ≠ `3C108060` → the wrong image. Decode with §7.1's table. ⚠️ **Addresses, not word numbers** |
| **V-2b** | `CAP OUT V-2b --send 'DW 80540000 1' --seconds 4` | `80540000: AFBD0BEE AE8D991B A39DEE9F 2A62E61B` | **71** | ≠ → not `quietm`, whatever `V-2a` said. §7.2 has the other five |
| **V-2c** | `CAP OUT V-2c --send 'DW 805FABF0 8' --seconds 6` | line 1 = **sixteen zero bytes**; line 2 **byte-identical to `V-0t`'s line 2** | **118** | line 1 ≠ 0 → short transfer. line 2 moved → the write ran past `image_end` |
| **V-flr0** | `CAP OUT V-flr0 --send 'FLR 80A00000 000000 100' --seconds 5` | the echo, `Flash read from 00000000 to 80A00000 with 00000100 bytes\t?`, then `(Y)es , (N)o ? --> ` and **no `<RealTek>`** | **104** | 🔴 **read the echo before typing `Y`, and mind which field is which.** `FLR`'s **first typed argument is the RAM destination**; the echo prints `from <flash source> to <RAM destination> with <length>`, so the echo's first hex field is the SOURCE. Pass only if it reads `from 00000000 to 80A00000` — anything else → `V-no` |
| **V-yes0** | `CAP OUT V-yes0 --send 'Y' --seconds 6` | `Flash Read Successed!` then the prompt | **35** | a failure line → record it; the region is not readable and that is the finding |
| **V-rd0** | `CAP OUT V-rd0 --send 'DW 80A00000 64' --seconds 6` | **byte-identical to `bench/2026-08-24d/G8a-rd0.log`** | **777** | any difference → **STOP, do not `J`.** §8.4 |
| **V-flr6** | `CAP OUT V-flr6 --send 'FLR 80A00100 060000 100' --seconds 5` | as `V-flr0`, `from 00060000 to 80A00100` | **104** | as above |
| **V-yes6** | `CAP OUT V-yes6 --send 'Y' --seconds 6` | as `V-yes0` | **35** | as above |
| **V-rd6** | `CAP OUT V-rd6 --send 'DW 80A00100 64' --seconds 6` | **byte-identical to `bench/2026-08-24d/G8a-rd6.log`** | **777** | any difference → **STOP, do not `J`** |
| **V-flrh** | `CAP OUT V-flrh --send 'FLR 80A00200 006000 100' --seconds 5` | as above, `from 00006000 to 80A00200` | **104** | as above |
| **V-yesh** | `CAP OUT V-yesh --send 'Y' --seconds 6` | as `V-yes0` | **35** | as above |
| **V-rdh** 🔴 | `CAP --out /home/key/fwre-work/rebuild/bench-only/b5-20260830c/V-rdh --send 'DW 80A00200 64' --seconds 6` | `cmp` against `…/b5-20260830c/expect-h601-rd.txt` | **777** | 🔴 **`--out` is NOT under `bench/`.** These bytes are this unit's MAC and radio calibration. §8.3 |
| **V-2d** | `CAP OUT V-2d --send 'DW 80500000 8' --seconds 6` | **byte-identical to `V-2a`** | **118** | changed → the `FLR` block reached the payload's head. Do not `J`. ⚠️ **32 bytes of 1,027,072 — this cannot find an arbitrary clobber**, §8.5 |
| **V-no** | *only if an `FLR` echo is wrong*: `CAP OUT V-no --send 'N' --seconds 4` | the loader abandons the read and returns to `<RealTek>` | — | 🔴 **the abort cell.** Three stop-ifs say *“→ N”* and until 2026-08-30 no row on this card sent one, so the abort path was unwritten. Not a cell in §2's list: it runs only on a branch |
| 🎬 | **start recording** — phone, landscape, the terminal filling the frame | — | — | the shot must include `V-5b`'s reply. §12 |
| **V-3** | `CAP OUT V-3 --send 'J 80500000' --seconds 45` | the five `rtkload` lines, then **eleven marks with nothing between them**, then M4, then a prompt. **401 bytes** | **401** | §9.4's five shapes |
| **V-5a** | `CAP OUT V-5a --send 'cat /proc/cpuinfo' --seconds 15` | **byte-identical to `bench/2026-08-30b/L5a.log`**, ⚠️ **except `BogoMIPS`, which is re-measured every boot and may legitimately move** (§10.1) | **147** | a prompt that does not echo is **not** a shell |
| **V-5b** | `CAP OUT V-5b --send 'cat /proc/version' --seconds 15` | `… (key@K) … #1 Fri Aug 28 **23:39:33** CST 2026` | **111** | `23:37:47` → **`loudm` booted, not `quietm`**. `#1526`/`admin@office.hopeiot` → **unattributed**, not a pass |
| **V-6a** | `CAP OUT V-6a --send 'ifconfig -a' --seconds 15` | **byte-identical to `bench/2026-08-30b/L6a.log`** — 23 interfaces | **7,658** | fewer than six `ethN` → the netdevs did not register |
| **V-6b** | `CAP OUT V-6b --send 'ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up' --seconds 10` | no error | **52** | — |
| **host** | `ip neigh flush dev <if>` then `tcpdump -i <if> -n -e 'icmp or arp' \| tee bench/2026-08-30c/V7a-host.txt` **running throughout** | — | — | 🔴 **keep stderr too** — `2> V7a-host.err`. §11.3 |
| **V-7a** | `CAP OUT V-7a --send 'ping -c 4 10.1.1.2' --seconds 20` | 4/4, and request+reply in the host capture. ⚠️ **`L7e.log`'s 420 bytes hold `time=10.000 ms` five times** (four replies + the min/avg/max line), and the RTT is quantised to `CONFIG_HZ=100`'s 10 ms — **a different multiple of 10 changes the byte count and is not a failure**, so this row is *the shape*, not byte-identity | ≈**420** | ARP requests and no ARP replies = the host, not the driver |
| 🎬 | **stop recording** | — | — | — |
| **V-8a/b** | *only after a `J` that did not reach D4*: `CAP OUT V-8a --send 'DW 80500000 8' --seconds 6` and `CAP OUT V-8b --send 'DW 805FABF0 8' --seconds 6` | `V-8a`'s word at `0x8050001C` back to `26101000` with `0x80500018` = `3C10805F` (the loader re-staged) while `V-8b` line 1 is **still zero** | 118 each | three outcomes, not two |

### Power cycle 4 — the bracket's second half. `bench/2026-08-30d/`

**No upload, no `J`, no network.** Power on, catch the prompt, read nine cells,
power off. About ninety seconds of wire time.

| # | typed / run | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **Z-A** | `CAP --out bench/2026-08-30d/Z-A --esc 25 --esc-period 0.002 --seconds 40` | the 181-byte cold slice, §3 | — | no prompt → power off |
| **Z-ab** | `CAP --out bench/2026-08-30d/Z-ab --send 'DW 8040D4A0 1' --seconds 4` | 🔴 **`00000001`** | **71** | `00000000` → this is **not** a fresh boot and the bracket proves nothing. §13.2 |
| **Z-flr0 / Z-yes0 / Z-rd0** | as `V-flr0` / `V-yes0` / `V-rd0`, `--out bench/2026-08-30d/…` | `Z-rd0` **byte-identical to `V-rd0` and to `G8a-rd0.log`** | 104 / 35 / **777** | any difference → the write-up starts from this capture |
| **Z-flr6 / Z-yes6 / Z-rd6** | as the `6` triple | `Z-rd6` **byte-identical to `V-rd6` and to `G8a-rd6.log`** | 104 / 35 / **777** | as above |
| **Z-flrh / Z-yesh / Z-rdh** 🔴 | as the `h` triple; **`Z-rdh --out /home/key/fwre-work/rebuild/bench-only/b5-20260830c/Z-rdh`** | `cmp` against `V-rdh` **and** against `expect-h601-rd.txt` | 104 / 35 / **777** | as above. **`--out` is NOT under `bench/`** |

---

## §1 The prefixes, and why they are new letters

`V-*` is power cycle 3 and `Z-*` is power cycle 4, for the reason §B5's card
gives for `L-*`: *"the letter is there so power cycle 3's captures cannot be
confused with these."* 量 2026-08-30, every capture prefix in `bench/`:
`A B C CONT D E F G H L Q QJ SPI X flush`. `V` and `Z` were both free; `Y` was
free too and is **deliberately not used**, because `Y` is the literal string
typed at the `FLR` confirmation and a cell called `Y-…` beside a `--send 'Y'`
is a reading waiting to be misfiled. The confirmation cells are `V-yes0`,
`V-yes6`, `V-yesh`.

Mapping to the `K` cells §B5 carries the reasoning in: `V-0r`/`V-0ab` = `K0`,
`V-1` = `K1`, `V-0t`/`V-2a`/`V-2b`/`V-2c`/`V-2d` = `K2`, `V-3` = `K3` + `K4`,
`V-5a`/`V-5b` = `K5`, `V-6*` = `K6`, `V-7*` = `K7`, `V-8` = `K8`. The `flr`/`yes`/`rd`
triples are §B3's `G8a` and `G8b`, applied to this seating; **nothing in `K`
covers them, and that is the gap this block closes.**

## §2 Cells, in order

```cells
bench/2026-08-30c/V-A
bench/2026-08-30c/V-0ab
bench/2026-08-30c/V-0t
bench/2026-08-30c/V-2a
bench/2026-08-30c/V-2b
bench/2026-08-30c/V-2c
bench/2026-08-30c/V-flr0
bench/2026-08-30c/V-yes0
bench/2026-08-30c/V-rd0
bench/2026-08-30c/V-flr6
bench/2026-08-30c/V-yes6
bench/2026-08-30c/V-rd6
bench/2026-08-30c/V-flrh
bench/2026-08-30c/V-yesh
bench/2026-08-30c/V-2d
bench/2026-08-30c/V-3
bench/2026-08-30c/V-5a
bench/2026-08-30c/V-5b
bench/2026-08-30c/V-6a
bench/2026-08-30c/V-6b
bench/2026-08-30c/V-7a
bench/2026-08-30d/Z-A
bench/2026-08-30d/Z-ab
bench/2026-08-30d/Z-flr0
bench/2026-08-30d/Z-yes0
bench/2026-08-30d/Z-rd0
bench/2026-08-30d/Z-flr6
bench/2026-08-30d/Z-yes6
bench/2026-08-30d/Z-rd6
bench/2026-08-30d/Z-flrh
bench/2026-08-30d/Z-yesh
```

**Thirty-one cells.** §15 predicts the report per branch.

**Named but not in the block, on purpose:**

* **`V-rdh` and `Z-rdh`** — the two captures that carry `H601`'s bytes. They are
  written outside this repository (§8.3), so `check-predictions.py` cannot see
  them and **their ordering is unenforced**. That cost is stated rather than
  hidden; it is the same gap `bench/README.md` already records for `CONT3` and
  for `L6c-up`.
* **`V-8a` / `V-8b`** — the post-mortem, run only after a `J` that did not reach
  D4. Naming both branches would guarantee a violation whichever way the seating
  goes, which would make the number meaningless.
* **Not captures at all**: `V0-rescue.json`, the `loader-tftp.py put`
  transcript, `V7a-host.txt`/`.err`, and the video.

---

## §3 `V-A` and `Z-A` — the power-on catch, and the census behind it is not what it was

**Prediction**: from the first `\r\nBooting` in the log, **181 bytes with
sha256 `f5287ff9f64b1035…`**.

🔴 **Re-measured today over every `A-catch*.log` in `bench/`, with no hardcoded
list, and the population is not the one the last two write-ups used.** There are
**eleven** files, not nine and not ten:

| | |
|---|---|
| carry the canonical 181-byte slice | **9** — `24`, `24b`, `24c`, `24d`, `24f/A-catch2`, `25`, `25b`, `30`, `30b` |
| a **118-byte byte-identical prefix** of it | 1 — `24e`, the warm boot |
| **no `\r\nBooting` anchor at all** | 1 — `2026-08-23` |

**And the last of those is not a `console-capture.py` capture.** 讀:
`bench/2026-08-23/A-catch.log` has **no `.meta.json`** and its content is an
interactive transcript with `ok` lines — a different instrument, sharing a
filename. Two more (`24`, `24b`) have a `.meta.json` with **no `tool_version`
field**; they predate 1.2.

🔴 **So the population of every "over all the `A-catch` captures" claim in this
repository has been defined by a filename**, and a filename is not a shape.
`bench/2026-08-30/CORRECTIONS-block0.md` said *"all nine `A-catch*.log`"* and
*"all eight committed"* — the first missed `24f/A-catch2.log` and included a file
from another tool; the second was taken before today's two were committed. The
census that is worth having keys on **the presence of a `.meta.json` carrying
`tool_version`**, and on that population it is 8 files, all 1.2 or 1.3, all nine
— sorry, **all eight** carrying the canonical slice except `24e`.

⚠️ **`A-catch` still has no negative control**, and today does not give it one.
`24e` is a *prefix*, not a different boot; the slice has never been shown able to
differ. §B5-c12 said so and it is still true.

⚠️ **The instrument prefix before `Booting` is not predicted.** 量 across the
nine: 0, 0, 1, 2,814 (`24d`), 2,810 (`24f`), 1, 2, 0 and **117**. The last is `bench/2026-08-30b`,
cycle 2 of the last seating, and it is 117 **raw `0x1B`** — the previous cycle's
loader still at its prompt, echoing.

🔴 **And that is NOT the state cycles 3 and 4 start from.** An earlier
draft of this section said *"cycles 3 and 4 are in exactly that position, so a
prefix of raw ESC is expected on both"* — wrong, by the rule it was citing. 量:
cycle 2's last capture is `L7e` at 23:26:29, `ping -c 4` **from `loudm`'s
shell**, and cycle 3's own card ends the same way at `V-7a`. **What is answering
when the next capture opens is a Linux tty, not a loader.**
`bench/2026-08-30/CORRECTIONS-block0.md` §2 owns the rule and it cuts the other
way: caret pairs `0x5E 0x5B` are a **Linux tty**, raw `0x1B` is the **loader**.

**So the prefix is a three-way reading and none of the three is a failure:**

| prefix | what was answering | when |
|---|---|---|
| **`0x5E 0x5B` pairs** | a **Linux tty** with `echoctl` — the `24d`/`24e`/`24f` signature | the capture was opened while the previous cycle's shell was still up |
| **0 bytes** | nothing | the board was already powered off when the capture opened |
| **raw `0x1B`** | a **loader** at its prompt | 🔴 unexpected here, and it would mean the previous cycle had already reset to the loader — which for cycle 3 means `quietm` is not the thing that was running |

🔴 **If the 181-byte slice matches `24e` instead, the board was warm-reset rather
than cold powered** — and then `AUTOBURN` state, DRAM bias and the staged image
are all a different boot's, `V-0t`'s baseline is void, and `Z-ab` (§13.2) is the
cell that says so independently.

## §4 `V-0ab` — the guard, and the one cell that can stop the seating

`--send 'DW 8040D4A0 1'`, after the rescue. **71 bytes**, and the content byte
for byte identical to `bench/2026-08-25b/H2a-ab.log` and
`bench/2026-08-30b/L0-ab.log`:

```
DW 8040D4A0 1\n\r8040D4A0:\t00000000\t00000000\t00000000\t00000000\n\r<RealTek>
```

🔴 **If word 1 is not `00000000`, STOP. Nothing is uploaded.** One instruction at
`0x80401B9C` is the burn path's own read of it, and this is read *after* the
rescue and *before* the transfer because the word that matters is the one the
burn path sees **during** the transfer.

## §5 `V-0t` — the baseline that makes `V-2c` a measurement

`--send 'DW 805FABF0 8'`, **before** the transfer. **118 bytes**, two lines.

🔴 **The address moved and every row that names it moved with it.** `loudm`'s
tail read was `0x806013F0`; `quietm` is 26,624 bytes shorter, so its `image_end`
is `0x805FAC00` and the read is at **`0x805FABF0`**. §B5's power-cycle-3 table
says *"`806013F0` becomes `805FABF0` EVERYWHERE it appears — `L-0t`, `L-2c` and
`L-8`, three rows, or the before/after pair is taken at two different addresses
and both halves are void."* Here that is `V-0t`, `V-2c` and `V-8b`. **Three
rows, checked.**

量 today: `0x80500000 + 1,027,072` = `0x805FAC00` exactly, and
`0x805FAC00 − 0x10` = `0x805FABF0`.

| line | before the transfer | why it is not a number |
|---|---|---|
| `805FABF0` | DRAM, **not sixteen zero bytes** | power-on bias. `MEM-16`: 89.5 % reproducible, measured null 55.98 %, 1 KiB period — **and never written down for this address** |
| `805FAC00` | DRAM, and **record it verbatim** | it is `V-2c`'s negative control and its value is only needed against itself |

⚠️ **Can this address be read before the upload at all?** Yes, and it is a
different margin from `loudm`'s. The loader's staged copy of the vendor image
ends at `0x805F1002` — 🔴 **讀 ＋ 推, and NOT 量**: 讀 the flash header's
`len` = `0x0F1002` (`FLM-09`) plus the inference that the loader copies exactly
`len` bytes to `startAddr`. ⚠️ **`MAP-17` is not a second source for it** — that
row is *selected*, its own value column is `—`. *(An earlier draft of this line
said "(`MAP-17`, 量)", which is both halves of a defect `notes/kernel-build.md`
§12.3 and `RUNSHEET` §B5-c5 have each already written up once. `SPEC.md` `LDR-39`
is the owner.)* `0x805FABF0` is **39,918 bytes above it** —
against `loudm`'s 66,542. Both are clear; the margin is smaller and it is
recorded, not assumed. (`notes/kernel-build.md` **§12.3** carries the same 39,918 — §12.2 ends at the
line above its table.)

## §6 `V-1` — the upload

**1,027,072 bytes**, sha256 `cf8a93d73025292d…`, byte-identical to the
pipeline's own `nfjrom` (量 2026-08-29, `cmp`, rc 0) and renamed. The rename is
`loader-tftp.py`'s `--filename` guard, §B5-c2.

⚠️ **`RLXFW` occurs ZERO times in the file that goes up** (量) — the marks are
inside the LZMA stream. What ties the wire to the marks is the sha256 above and
nothing else.

## §7 `V-2a` / `V-2b` / `V-2c` — which image landed

### §7.1 `V-2a`: the last two words are the whole cell

```
80500000:	00000000	00008021	40906000	00000000
80500010:	00000000	00000000	3C108060	2610AC00
```

量 today, straight out of the uploaded file: words 6 and 7 at file offsets
`0x18`/`0x1C` are `3C108060` `2610AC00` — `lui s0,0x8060` / `addiu s0,s0,-0x5400`,
the linker's `__vmlinux_end` = `0x805FAC00` = `0x80500000 + 1,027,072`.

**The first line does not discriminate** and is printed only because `LDR-07`
rounds a length of 8 up to two whole lines: 量, all five `nfjrom` files this
project can produce and the staged vendor image share it — one `rtkload`
`start.o`, §B5-c1.

| word 6 · word 7 | = | that would be |
|---|---|---|
| `3C108060` · **`2610AC00`** | `0x805FAC00` | 🟢 **`quietm` or `quiet`. The pass** |
| `3C10805F` · `26101000` | `0x805F1000` | 🔴 **the staged vendor image — the transfer did not land** |
| `3C108060` · `26101400` | `0x80601400` | 🔴 **`loudm`** — yesterday's file went up again |
| `3C108060` · `26101000` | `0x80601000` | 🔴 `loud`, unmarked. No ladder |
| `3C10805D` · `26100800` | `0x805D0800` | the drop's own kernel. It is not on this device |

⚠️ **It cannot separate `quietm` from `quiet`** — same size, same word. `V-2b` is
what does, and it is the only cell that can.

### §7.2 `V-2b`: the variant, at a word where no two of the six agree

`--send 'DW 80540000 1'`. **71 bytes.** File offset `0x40000`, inside the LZMA
stream.

```
80540000:	AFBD0BEE	AE8D991B	A39DEE9F	2A62E61B
```

量 today, from the uploaded file itself. The other five, so a mismatch is
diagnosable rather than merely wrong:

| | first four words at `0x80540000` |
|---|---|
| **`loudm`** | `CEC3FFD9 C013013E CE652208 749F1E48` — **and this is the one to fear**, because it is what a second upload of yesterday's file looks like |
| `quiet` | `78CBE252 D8BCCA11 8F6166EF 6024973E` |
| `loud` | `231ACB87 6A8FE6C9 9704C109 25B8056C` |
| the drop's | `806892AC E99A8B0B EB0EEE98 7FEB6193` |
| this unit's staged image | `A9FDA5F8 40713F77 AB0C8A74 B7566FE0` |

⚠️ **`quiet` and `loud` are quoted from `bench/2026-08-30b/PREDICTIONS-B5-block1.md`
and are not re-derivable from this disk today**: 量 2026-08-30, `$FWRE_WORK/rebuild/r3-4/cells/` holds `loud`, `loudm`, `quietm` and `rlxfw` — the
**`quiet` cell is gone**, and all four trees' `rtkload/nfjrom` is the stale drop copy.
`quietm`, `loudm`, the drop's and the staged image were all re-measured today; those
four rows are 量 and the other two are 讀 from a frozen block.

### §7.3 `V-2c`: the tail, after. One command, a positive and a negative control

| line | prediction | what it refutes |
|---|---|---|
| `805FABF0` | **sixteen zero bytes** | 量 today: `quietm`'s trailing zero run is **552 bytes** (`loudm`'s is 688), from `rtkload/ld.script.in` aligning `__vmlinux_end` to 1024. So the last 16 bytes are zero and **a short transfer does not reach here.** On its own a zero is what a dead instrument prints; what makes it evidence is that `V-0t` read the same address minutes earlier and it was not zero |
| `805FAC00` | **byte-identical to `V-0t`'s second line** | the negative control: the transfer did not run past `image_end`. 🔴 **NOT "exactly 1,027,072 bytes and not one more"** — `SPEC.md` `LDR-39` rejects that phrasing in as many words: the pair brackets **`[n, n+16)`**, because line 1 going zero says the write reached `image_end−1` and line 2 not moving says it did not touch `image_end`..`+15`. **Sixteen bytes of slack, and the earlier draft of this cell claimed none** |

🔴 **This pair is the only place in the seating where a *change* is observed
rather than a value matched**, and it is what §B5-c1 rebuilt `K2` into after the
head was measured not to discriminate.

⚠️ **And `DW` goes through KSEG0, which is cached** (`CPU-25`: 16-byte lines), so
`V-0t` pulls the two lines `V-2c` wants to see change into the I/D cache before
the transfer runs. `LDR-39` hands this cell the positive control for it and this
block had left it out: **`bench/2026-08-24d`'s `G5-pv1` → TFTP `put` → `G5-rb1`**
— the same read → write → re-read shape at three addresses, and the re-read
returned the **new** data (`5A5A5A5A` → `00000000`). So a stale-cache reading is
not merely unlikely here; it has been shown not to happen on this device.

---

## §8 🔴 The flash bracket — what it buys, what it does not, and the one region it could not reach before today

### §8.1 Why this is on the card at all

`RUNSHEET` §B3 `G8b` writes the rule this project has to live by: the evidence
two 256-byte reads entitle you to is *"the loader head and the `cr6c` header are
unchanged"* — **not** *"zero flash bytes written"*, which needs a full re-dump
hashed against `FLS-14` and costs the 105 minutes that dump's own metadata
records (量: 6,300.1 s).

**The last seating ran no `FLR` at all.** So on the night this project's own MTD
stack came up over a partition table spanning both regions `CLAUDE.md` forbids,
it held **less** flash evidence than `R0` did. That is the hole this closes.

### §8.2 The three regions, and the third one is new

| | flash | RAM | what it is | committed baseline |
|---|---|---|---|---|
| `0` | `0x000000`–`0x0000FF` | `0x80A00000` | the loader head | ✅ `bench/2026-08-24d/G8a-rd0.log`, sha256 `cea9a0f1eeaaa884…` |
| `6` | `0x060000`–`0x0600FF` | `0x80A00100` | the `cr6c` kernel header | ✅ `bench/2026-08-24d/G8a-rd6.log`, sha256 `8c9949bcd28ff86a…` |
| `h` | `0x006000`–`0x0060FF` | `0x80A00200` | 🔴 **`H601`** — this unit's MAC and radio calibration | ❌ **none, and there can never be one** |

🔴 **`H601` has never been in this bracket, and it is the region `CLAUDE.md`
calls unrecoverable.** `G8a`/`G8b` read `0x000000` and `0x060000`; the second of
those is not even a forbidden region. So the sampling was: 256 bytes of the
24,576-byte loader region, **0 bytes of the 8,192-byte `H601`**, and 256 bytes of
a region nothing forbids. Nobody wrote that down until today.

The three RAM destinations are `+0x000`, `+0x100`, `+0x200` and do not overlap,
so all three stay resident and can be re-read without a second `FLR`.

### §8.3 🔴 Why `V-rdh` is written outside this repository

Its 777 bytes are a hex rendering of this unit's MAC address and radio
calibration. `CLAUDE.md` forbids committing anything that identifies one physical
device, and `tools/audit-bench-log.py` scans every `bench/**/*.log` for exactly
that. So:

* the capture goes to `/home/key/fwre-work/rebuild/bench-only/b5-20260830c/`, beside the
  uploaded images, which are out of the repository for the same class of reason;
* what is written down is the **verdict** — `cmp` against the desk-computed
  expectation, and `Z-rdh` against `V-rdh`;
* 🔴 **and not a hash.** A digest over a 256-byte window whose only unknown is 24
  bits of MAC is a 2^24 search for anyone who knows the format, so publishing the
  digest publishes the address. `tools/flashwin.py` refuses to print one for a
  forbidden window and its `C8` is the control.

**The control is public even though the reading is not**, and that is the whole
design: `flashwin`'s `R1`/`R2` require the same renderer that produced
`expect-h601-rd.txt` to reproduce `G8a-rd0.log` and `G8a-rd6.log` **byte for
byte**, from the same dump, in the same run. 量 today, and both do — 777 bytes
each, sha256 `cea9a0f1eeaaa884…` and `8c9949bcd28ff86a…`, identical to the
committed captures.

⚠️ **`V-flrh` and `V-yesh` ARE committed.** The `FLR` echo carries only
`Flash read from 00006000 to 80A00200 with 00000100 bytes` and the confirmation
carries `Flash Read Successed!`; neither contains a flash byte. Only the `DW` is
withheld, and withholding the whole triple would hide the fact that the read
happened.

### §8.4 The `cmp` matrix, and what each edge covers

| `cmp` | covers |
|---|---|
| `V-rd0` ≟ `bench/2026-08-24d/G8a-rd0.log` | 🔴 **2026-08-24 → this upload**: four seatings, five kernel executions (two of them mine), three uploads, and the MTD map of 2026-08-29 |
| ~~`V-rd0` ≟ `expect-rd0.txt`~~ | 🔴 **STRUCK OUT before the seating: it is the same test as the row above.** 量 2026-08-30, `cmp` → identical: `expect-rd0.txt` **IS** `G8a-rd0.log`, byte for byte — that equality is exactly what `flashwin`'s `R1` asserts, so this row cannot fail if row 1 passes and it covers no span row 1 does not. *(It also said the dump was taken “not with `FLR`”, which is false: `FLS-14` records `FLR`+`DB`. The real difference is `DB` vs `DW` and scripted vs hand-typed.)* 🔴 **The dump↔device agreement is real and it is already banked** — it was measured TODAY, at the desk, and it is what makes the `H601` expectation trustworthy. It is not something the seating re-earns |
| `Z-rd0` ≟ `V-rd0` | **the `quietm` kernel's own execution** |
| the same three for `6` and for `h` | as above |
| `G8pre-rd0` ≟ `G8a-rd0` ≟ `G8b-rd0` | already 量 2026-08-24, all three identical — this is the bracket's precedent, not a new reading |

**Reach, stated where it will be quoted from**: three 256-byte windows are **768
bytes of 4,194,304** — **0.0183 %**. The entitled sentence is *"the loader head,
the `cr6c` header and `H601`'s first 256 bytes are byte-identical to the
2026-08-16 dump and to the 2026-08-24 captures"*. **It is not "zero flash
bytes."** It is not even "`H601` is unchanged" — 256 of its 8,192 bytes are read.

### §8.5 The two ways this block can go wrong, and neither is a hypothetical

🔴 **`FLR`'s first argument is the RAM destination, and there is no bound check
on any of its three.** 讀 `docs/loader-command-semantics.md` §`FLR`: three
`strtoul(_,_,16)`, then `sw s0,-8920(v0)` stores the length and
`jal 0x80404F38` calls `flash_read(dst_RAM, src_flash, len)`. A mistyped
destination writes 256 bytes of flash **over whatever is in RAM there** —
including the loader's own `.data` at `0x8040D000`+, and including the payload at
`0x80500000`. The `(Y)es` prompt is the only thing between a typo and that, which
is why the card's stop-if is *read the echo back before typing `Y`*: the echo
prints all three arguments in `Flash read from %X to %X with %X bytes`.

🔴 **And a mistyped destination cannot be recovered inside this power cycle.**
`0x80409A04` writes the TFTP length global `0x8040DD28`, so **no `put` or `get`
may follow an `FLR`** — the image cannot be re-uploaded. `V-2d` is the cell that
finds out: it re-reads `0x80500000` after all nine `FLR` cells and must be
byte-identical to `V-2a`. If it is not, **do not `J`** — power-cycle and start
again, having learned what the typo did.

⚠️ **The ordering is not new.** §B3 ran `G5` (the upload) → `G8a` (the `FLR`
block) → `G7` (`J 80500000`), and `G7` is the boot that closed `R0`. So an `FLR`
block sitting between an upload and a jump is measured not to break the boot, on
this device, on 2026-08-24. `V-2d` makes it a reading on this one too.

---

## §9 `V-3` — the boot, and it is a **401-byte** prediction

`--send 'J 80500000' --seconds 45`.

### §9.1 Where 401 comes from, term by term

Every term is 量, read out of `bench/2026-08-30b/L3.log` — the same kernel from
the same tree with two config symbols different:

| | bytes | |
|---|---:|---|
| `J 80500000` echo + the four `rtkload` lines + `start address: 0x80003600` | **169** | the prefix, byte for byte |
| eleven marks, `RLXFW-B00` … `RLXFW-B10` | **139** | nine plain × 11, two valued × 20 |
| M4, `rlxfw: init running, RLXFW-R3-RUNG1-OK` | **40** | |
| `/bin/sh: can't access tty; job control turned off` | **51** | |
| `# ` | **2** | |
| | **401** | |

**And the number it must NOT be is measured too**: `loudm` printed **6,459**
bytes through the same window, and the whole 6,058-byte difference is **105
`printk` lines**. 量.

### §9.2 What `quietm` can and cannot print, read out of the tree and the artefact

`quiet.config` and `loud.config` differ on **exactly two symbols** — `diff` reports
`226c226,227`, so one line is replaced by two and the hunk is three lines. 量:
`CONFIG_PRINTK` and `CONFIG_PRINTK_TIME`. So this is a one-variable experiment,
and the following are 讀/量 rather than expectation:

| | |
|---|---|
| the eleven marks | **arrive.** `rlxfw_puts` → `prom_putchar`, no console and no `printk` in the path |
| `[    0.000000] CPU revision is: 0000cd01` | **absent.** It is `arch/rlx/kernel/cpu-probe.c:39`'s `printk`. 量 on the desk channel: `quietm` prints **106** bytes where `loudm` prints **148**, and the 42-byte difference is exactly this line |
| the 105 `printk` lines between B04 and B10 | **absent** |
| M4, and the shell | **arrive.** 讀 `kernel/printk.c`: `console_setup()` (`:802`) and `register_console()` (`:1123`) are **outside** the `#ifdef CONFIG_PRINTK` that spans `:132`–`:539`, so `console=ttyS0,38400` is still parsed and `/dev/console` still binds to ttyS0. Userspace output is not `printk` |
| 🔴 a **panic**, if it panics | **arrives.** 讀 `kernel/panic.c:27`: `#define printk panic_printk` under `CONFIG_PANIC_PRINTK`, which is `bool` with **no prompt and `default y`** (讀 `init/Kconfig:843`) and is `=y` in `quiet.config` (量). 量 on the built artefact: `panic_printk` is a **GLOBAL FUNC in the `quietm` symbol table** and `<0>Kernel panic - not syncing: %s` occurs **once** |

🔴 **That last row is what makes silence mean something.** In `quietm`, silence
after a mark is a **hang**, not a suppressed panic — the panic path is linked and
its format string is in the image. ⚠️ And it is 讀+量, not 量-on-the-wire: no
channel has ever made this build panic, so *the panic path reaches the UART* is
the one link in that chain still 推.

### §9.3 The marks, and what each one still buys

The ladder is `bench/2026-08-30b/PREDICTIONS-B5-block1.md`'s and is not restated.
What changes under `quietm`:

* **`RLXFW-B02=0000CD01`** — `PRId` off this die, upper case. Under `loudm` this
  seating read `PRId` through **three** formatters; under `quietm` it is
  **two** — B02 and `V-5a`'s `cpu model : 52481` — because the middle one was a
  `printk`. **Predicting three would be predicting `loudm`.**
* **`RLXFW-B09`** — 讀 `notes/kernel-build.md` §11.1: this mark *"marks the
  console handover only in `quiet`"*, because in `loud` the handover already
  announced itself (`console handover: boot [early0] -> real [ttyS0]`, 量 in
  `L3.log:30`; `:31` is `RLXFW-B09` itself). Here B09 is the only evidence that
  `console_init()` returned.
* **`RLXFW-B07=00000000`** — D3. `FFFFFFFF` then silence is the designed silent
  hang and is a **result**, read off the wire rather than inferred from absence.

### §9.4 Five shapes, and they are not one hang

| bytes | what arrives | what it says |
|---:|---|---|
| **401** | the ladder, contiguous | 🟢 the pass, **and the printk model is complete to the byte** |
| **443** | 401 + a 42-byte `CPU revision is:` line | 🔴 `CONFIG_PRINTK=n` did not take the early console with it. A finding about the config, not about the boot |
| **6,459** | `loudm`'s exact number | 🔴 yesterday's file went up. `V-2a`/`V-2b` should have caught it two cells earlier — if they did not, **the discriminators are wrong**, which is the bigger finding |
| **< 401**, ending in a mark | the ladder stopped | the mark names where. This is what the ladder is for |
| **169**, then nothing | entered and died before B00 | the case B00 exists to separate. `V-8a`/`V-8b` are the post-mortem |
| `start address: 0x80003440` | — | 🔴 the staged **vendor** image booted. Recorded as *unattributed*, never as a pass |

⏱ **`--seconds 45`, and it is sized from a measurement rather than a guess.** 量
`bench/2026-08-30b/L3.timing`: `loudm` went from `J` to the shell prompt in
**8.98 s** — not the 26.05 s of this unit's own kernel that §B5's card sized 90 s
against. `quietm` prints 6,058 fewer bytes, which at 3,840 B/s is 1.58 s less, so
**≈ 7.4 s** is the prediction. 45 s is **6.1×** that, and still 1.7× the vendor
kernel's own 26.05 s, which is the number to be safe against if the ladder stalls
somewhere the desk channel has never reached.

## §10 `V-5a` / `V-5b` — and one of them is a byte-identical prediction

### §10.1 `V-5a` — `cat /proc/cpuinfo`

🔴 **Predicted byte-identical to `bench/2026-08-30b/L5a.log`: 147 bytes, sha256
`84d830ac031dd096…`.**

```
cat /proc/cpuinfo\r\nsystem type\t\t: RTL819xD\r\nprocessor\t\t: 0\r\n
cpu model\t\t: 52481\r\nBogoMIPS\t\t: 398.95\r\ntlb_entries\t\t: 32\r\n
mips16 implemented\t: yes\r\n#
```

Nothing in `fs/proc` is `printk`, so removing `CONFIG_PRINTK` cannot move any of
these six fields. ⚠️ **The one field with a licence to move is `BogoMIPS`**: it is
`calibrate_delay()`'s `udelay_val`, measured against the timer interrupt each
boot. If only that field differs, that is calibration jitter and is recorded as a
reading, not a miss — and it is worth having, because it is the second sample of
a quantity this project has exactly one of.

**`TC-36` fires again for free**: six fields and **no `hardware watchpoint`** —
the seventh field this unit's shipped kernel prints and no build from these drops
can (量: the format string occurs zero times in either of my images). Its
presence would mean the vendor kernel answered.

### §10.2 `V-5b` — `cat /proc/version`, and it is the discriminator the video needs

**111 bytes, sha256 `ef82d7ecd2ca1ff6…`** — `bench/2026-08-30b/L5b.log`'s 111
with **exactly three characters different**. The hash is constructed rather than
hoped for: 量, that file with `23:37:47` replaced by `23:39:33` is 111 bytes and
differs in 3 positions, so the check at the bench is a `sha256sum` and not a
reading of hex by eye.

```
cat /proc/version\r\n
Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Fri Aug 28 23:39:33 CST 2026\r\n
#
```

量, two sources that are not each other: the `UTS_VERSION` string
`#1 Fri Aug 28 23:39:33 CST 2026` occurs **twice** in the `quietm` `vmlinux` —
🔄 *(an earlier draft said once)*: at `0x2701ed` in `.rodata`, inside
`linux_banner` and immediately after the `linux_proc_banner` format string, and at
`0x299437` in `.data`, which is the `init_uts_ns` copy `/proc/version` actually
formats from. ⚠️ **So “two sources that are not each other” is weaker than it
sounds**: one of the two is the same `.rodata` object as the format string beside
it. What is genuinely independent is `RUNSHEET` §B5's power-cycle-3 table, written
yesterday from the build record. The string
(3,968,240 bytes, sha256 `dd0c1190f3646561…`, the file `quietm-build.txt` records
as this build's output), and `linux_proc_banner` —
`%s version %s (key@K) (gcc version 3.4.6-1.3.6) %s` — occurs once beside it.

🔴 **`23:39:33`, not `loudm`'s `23:37:47`.** The two builds are 106 seconds apart
and that is the only thing in this string that separates them. `2.6.30.9` is
identical in both and in **this unit's shipped kernel**, so the release is not the
discriminator; the version field is.

⚠️ `uname -a` cannot run: this unit's busybox lists 50 applets and `uname` is not
one of them (量, §B5-c7). `/proc/version` is not a substitute chosen for
convenience — with `CONFIG_PRINTK` off it is **the only place the build stamp can
be read at all**, because the banner is never printed.

## §11 `V-6a` / `V-6b` / `V-7a` — the network, straight to the socket

### §11.1 `V-6a` — `ifconfig -a`

🔴 **Predicted byte-identical to `bench/2026-08-30b/L6a.log`: 7,658 bytes, sha256
`16067d2e7ce2ba86…`.** 量, that file holds **23** interfaces, not the six the
last card counted: `eth0`–`eth4`, `eth7`, `lo`, `peth0`, `pwlan0`, `wlan0`,
`wlan0-va0`…`va3`, `wlan0-vxd` and **eight** `wlan0-wds`. The card's *"six"* was
always *"six `ethN`"* and that is what it meant; the file is the fuller statement.

Every interface is down and carries no address, so there is nothing dynamic in
the output — which is why byte-identical is a legitimate prediction and not
optimism. A difference is a finding about netdev registration under
`CONFIG_PRINTK=n`, which is not a dependency anything in the driver should have.

### §11.2 🔴 The port map cannot be read this time, and that is the interesting part

Under `loudm` the netdev↔switch-port binding was 讀 straight off the boot log's
own registration lines (`eth4 … vid=9 Member port 0x8`). **Under `quietm` those
lines are `printk` and do not exist.** So on this power cycle:

* the binding is **推**, carried over from `bench/2026-08-30b/L3.log`;
* the only in-band evidence is `V-6a`'s MAC list, where the last octet names the
  netdev (`…:94` = `eth4`), and the host's `tcpdump -e` source MAC;
* which is exactly why the host capture's `-e` flag is not optional here.

**The cable is on switch port 3** — `eth4` under this build, `eth2` under the
vendor's, and `bench/2026-08-30b/CORRECTIONS-block1.md` §1 is why the answer has
to be a port number rather than a netdev name: `mine = 4 − vendor` for all five,
a 5-bit reversal with `eth3` as its own fixed point.

### §11.3 `V-6b` / `V-7a` — one interface, because the socket is known

`ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up` → **52 bytes**, then
`ping -c 4 10.1.1.2` → **420 bytes**, predicted byte-identical to
`bench/2026-08-30b/L7e.log`, sha256 `68ad0ca9578e6c81…`.

⚠️ **The RTT is the one field with a licence to move.** `time=10.000 ms` ×4 is
quantised to `CONFIG_HZ=100`'s 10 ms tick. A different multiple of 10 changes the
byte count and is not a failure; a value that is **not** a multiple of 10 would be
a finding about the clock.

🔴 **The five-interface sweep is not on this card and its absence is a
prediction.** `L-6c`…`L-6f` cost four `down`s, four `up`s and four pings last
time; going straight to `eth4` bets the whole of D5 on `bench/2026-08-30b`'s
answer. **If `V-7a` gets nothing, that is not D5 refuted** — it is the sweep owed,
and the fallback is `L-6c`'s form with `V-6c`…`V-6f`. §B5-c9 is the correction
that exists because trying two of five would have refuted D5 from a working
driver.

🔴 **Keep the host capture's stderr.** Last seating, `L7b`/`L7c`/`L7d`'s host-side
files are **one byte each** and their stderr was discarded, so three of the five
interfaces are evidenced by the board alone. `L7a-host.err` kept tcpdump's own
`0 packets captured` and is the reason `L-7a` is a reading rather than an absence.

## §12 🎬 The artefact, and what makes it evidence rather than footage

🔄 **`plan/ARTIFACTS.md` §2 asks for TWO videos, and this is the first of them.** Its heading says *「3 到 5 分鐘」* and that is the **v1.0** version, after `R9`; the row above it is **v0.2 短版, 「60 秒，無旁白」**, and its trigger is written as *「自建 kernel 第一次開機那一天」*. ⚠️ **That day was 2026-08-29 and no video was shot**, so this is late rather than early. 🔴 **And its storyboard is already written**: *上電 → 序列 log 滾動 → `Linux version 2.6.30.9 (你@你的主機)` → shell prompt → `uname -a`* —— **and the last step cannot run on this device**, because this unit's busybox has no `uname` applet (§B5-c7, `FW-25`). `cat /proc/version` is the substitute, and it is a better shot anyway: it prints the gcc version and `(key@K)`, which `uname -a` drops. `quietm` is the build to shoot
it on: **7.4 s from `J` to the prompt** and 401 bytes on screen, where `loudm`
takes 9.0 s and 6,459 bytes of scrolling `printk`.

The shot must contain, in this order: `J 80500000`, the eleven marks, the prompt,
`cat /proc/version` returning **`(key@K) … #1 Fri Aug 28 23:39:33 CST 2026`**, and
`ping -c 4 10.1.1.2` returning 4/4.

🔴 **A video of a router booting is not evidence of anything.** The whole content
is the build stamp being typed for and returned — a string the vendor image
cannot produce. If the frame does not carry it, the artefact is a router with a
light on.

⚠️ The video is **not** a bench capture, does not go in `bench/`, and is not in
the ```cells``` block. If it is ever published, note that the frame shows the
operator's own `/home/key` paths and `10.1.1.0/24` — the host's, not the unit's,
which is the same distinction `ci.yml` draws for `.meta.json` versus `.log`.

## §13 Power cycle 4 — ninety seconds, and it is the only cell that can speak for the kernel

### §13.1 What it buys

`V-rd0`/`V-rd6`/`V-rdh` are read **before** the `J`, so they cover the upload and
everything before it and say **nothing** about the kernel that is about to run.
`Z-*` is the other half. It cannot ride cycle 3: after `J` the loader is gone,
and an `FLR` before `J` cannot see a kernel that has not run yet.

**And it is the half that matters most on this seating**, because the kernel in
question instantiates `0x000000–0x130000` as a writable MTD partition —
`bench/2026-08-30b/L3.log`, 量 — and that partition contains both regions
`CLAUDE.md` forbids.

### §13.2 🔴 `Z-ab` is the control that makes cycle 4 a cycle

**`DW 8040D4A0 1` must read `00000001`.** 量 `bench/2026-08-24f`'s `G8b-ab` (🔄 *an earlier draft said `24e`; that
directory holds only `A-catch.*` and its prediction block*):
every reset puts `AUTOBURN` back to `1`, and that reading is what turned *"every
reset resets it"* from an argument about the image's initialiser into a
measurement.

So `00000001` says **this is a fresh boot**; `00000000` says the loader is the
one `V-0r` configured and the `Z-*` reads are not a second observation at all.
Without this cell the whole bracket rests on the operator having actually cycled
the power, which is not an instrument.

`Z-A`'s 181-byte slice says the same thing by an independent route. Both are
cheap; both are on the card.

### §13.3 What cycle 4 does NOT need

No `rescue`, no `IPCONFIG`, no upload, no network. `FLR` reads flash into RAM and
`DW` reads RAM; neither needs an IP. The card is shorter for it.

---

## §14 What this block does not do

* 🔴 **It issues no flash-write command** — and that is deliberately not the
  sentence *“it writes no flash byte”*, which an earlier draft of this bullet used
  and which is a claim about **bytes** that the enumeration below cannot reach.
  §13.1 supplies the counterexample two sections earlier: cycle 3 runs `quietm` to
  a shell with a writable MTD partition spanning both forbidden regions, and what
  the operator typed says nothing about what that kernel did. `AUTOBURN` is read `00000000` at the burn path's own instruction
  before the transfer, the uploaded file is an `nfjrom` payload with no `cr6c`
  header, and every `--send` on both cards is a `DW`, an `FLR`, a `Y`, a `J` or a
  userspace command. What the bracket *measures* is **768 bytes of 4,194,304**.
  The rest is unmeasured and stays unmeasured.
* **It does not read `H601` whole.** 256 of 8,192 bytes. A write to
  `0x006100`–`0x007FFF` is invisible to this block.
* **It cannot see two writes that cancel.** A `cmp` is a comparison of end
  states.
* **It does not cross-check the flash through my own MTD stack**, which would be
  a genuinely independent second path. 量 today, and it is a measurement rather
  than caution: this unit's busybox lists **50 applets and none of them is `dd`,
  `md5sum`, `od`, `hexdump`, `cmp` or `cksum`** (讀, the applet-name table at
  file offset 266740 — the same instrument that killed `/bin/uname` and
  `/bin/dmesg`), and `config/rlxfw-initramfs.tsv` declares **three** device
  nodes, none of them `/dev/mtd*`. Doing it needs a node — free — **and a
  foreign binary**, which breaks Decision B's third leg: *the contents are this
  unit's own binaries, unmodified; if the shell does not come up, the shell is
  not the new thing*. `R3-9` owns it.
* **It says nothing about the load-delay behaviour of this die.** A boot that
  works is consistent with a hazard that has not been hit. `R1a` has not moved.
* **A `quietm` pass is not a second `loudm` pass.** If `quietm` fails where
  `loudm` passed, that is a finding about `CONFIG_PRINTK` on this silicon and it
  is recorded, not averaged — `notes/kernel-build.md` §11.6 wrote that
  refutation condition on 2026-08-28, before either was built.
* **`check-predictions.py` cannot be satisfied today.** Run at the desk it
  reports `0 of 31`, because control `N2` — a predicted cell whose capture does
  not exist — fires on all thirty-one. That is the correct answer before a
  seating.
* **mtime is not a cryptographic timestamp.** `touch -d` rewrites it, and a
  clone destroys the signal entirely. This proves ordering to a cooperative
  auditor standing at the machine that took the captures, and nothing else.

## §15 What the check will report, per branch — predicted before the seating

| how far it gets | expected report |
|---|---|
| both cycles, everything | `31 of 31 captures came after the prediction, 0 did not` |
| cycle 3 complete, **cycle 4 not spent** | `21 of 31`, and the ten unrun ones are the `Z-*` |
| 🔴 D4, and the ping gets **nothing** | **still `21 of 31`.** A failed ping is a capture — `bench/2026-08-30b/L7a.log` is 160 bytes of *"4 packets transmitted, 0 packets received"*. What is missing in that branch is the `V-6c`… interface sweep, which is deliberately not in the block. *(Block 1's equivalent row said `10 of 12`, `L6b`/`L7a` unrun; the seating ran both and reported `12 of 12`. Same error, corrected here rather than copied.)* |
| `V-3` reaches B07 and stops | `16 of 31`, and the five unrun in cycle 3 are `V-5a`, `V-5b`, `V-6a`, `V-6b`, `V-7a` — 21 − 5 |
| nothing after `J` | `16 of 31`, same five, and `V-3` is the finding |
| the seating stops at `V-0ab` (`AUTOBURN` ≠ 0) | 🔴 **`2 of 31`** — `V-A` and `V-0ab`, both of which ran. *(This said `1 of 31` when the table was first written, which forgot that the cell doing the stopping has itself produced a capture.)* That is the correct outcome of a guard doing its job |

🔴 **A number below 31 is not a failure of this block.** A seating that stops
where it stops is a fact about the seating; what the tool is checking is that no
capture is **older** than the prediction naming it.
