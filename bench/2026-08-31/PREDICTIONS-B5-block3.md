# PREDICTIONS — Session B5, `R3-9`/`R3-10b`, block 3: `quietmc`, the MTD path, and a bracket that can finally disagree with itself

**Written at the desk on 2026-08-30, before power.** Every value below was
measured on this host today or read out of a capture already committed, and none
of it is conditional on a reading taken at the bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in a new
file — `CORRECTIONS-block3.md`, beside this one.

**This block covers TWO power cycles, and they are deliberately IDENTICAL up to
the shell prompt.** Cycle 5 (`W-*`) and cycle 6 (`X-*`) both upload the same
image, both read the same four flash windows, and both `J`. The only difference
is what is typed after the prompt. That symmetry is not tidiness — it is what
makes cycle 6 a **null** for `SPEC.md` `FW-32 殘留`, whose 0.250 s residual has
n=1 on each side and therefore no measure of boot-to-boot variance at all.

**What block 3 carries that block 2 could not.** Four things, and three of them
are controls rather than readings:

| | |
|---|---|
| a **pre-read** of every `FLR` destination, before the `FLR` | the bracket has never had a negative control. Without one, *the RAM already held these bytes* is not excluded and an `FLR` that did nothing looks exactly like one that worked |
| **new RAM destinations**, `0x80A00400`–`0x80A00700` | block 2's second half was forced to reuse block 2's first-half addresses, because `cmp` on a `DW` reply compares the typed line and the `%08X:` column, both of which carry the destination. `flashwin normalise` (new today, `N1`–`N5`) strips both, so the destination is free to move — and moving it is what makes a match mean the flash rather than the RAM |
| a **fourth window**, `0x006400` | `FLS-21`: the only span of `H601` this device has ever been seen to change is `0x00648A`–`0x006493`, and it is `0x38A` bytes **above** the window the bracket chose. `H601` reach 3.1 % → 6.3 % |
| `M-a`–`M-d`, the MTD path | the first device-side read of the region a wrong write cannot be undone in, through a path the kernel will not let anything write. `M-d` is the positive control on that safety property and it costs **zero flash bytes**, because `open` fails before any write is issued |

---

## §0 THE CARD — every line that gets typed, in order

**This is the only part of this file that is read at the bench.** Everything
below it is the reasoning that produced it.

🔴 **Every row carries a terminator.** `console-capture.py capture` with neither
`--seconds` nor `--idle` **refuses** as of 2026-08-30. The numbers are sized
against the loader's *marginal* reply rate, **3,458–3,497 B/s** (`SPEC.md`
`LDR-40`, as corrected by `bench/2026-08-30/CORRECTIONS-block0.md` §7).

### Before power — at the desk, and it is three commands

```
sha256sum /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin
  08b088135c62cbef90a69e081dfd55381b67ab73636054ba788148cf28fb3702

/usr/bin/python3 tools/flashwin.py --self-test
  24 passed, 0 failed

ls /home/key/fwre-work/rebuild/bench-only/b5-20260831/expect-*.txt
  expect-000000.txt  expect-060000.txt  expect-h601-6000.txt  expect-h601-6400.txt
```

⚠️ **`24` and not `19`.** `flashwin` gained the `normalise` subcommand and five
controls in the session that wrote this card. On a machine without
`$FWRE_WORK/dumps/` it is **`21 passed, 0 failed`** and one skip line covering 3
(21 + 3 = 24) — `R1`/`R2`/`R3` read this unit's own 4 MiB flash, which can never
be committed. Either line is correct. The third command is not ceremony: two of
the four expectation files are `H601` windows that this repository may not hold,
so a missing one is found here rather than after an `FLR` has been spent.

🔴 **Every path on this card is literal, and `$FWRE_WORK` appears in no typed
line** — 量 2026-08-30: it is empty in this host's shells, and
`console-capture.py` and `loader-tftp.py` take a plain path with no fallback.

The host preflight — the long-lived WSL process, re-reading both busids, the NIC
at `10.1.1.2/24`, `/usr/bin/python3` and the board-off 3-second capture — is
`RUNSHEET` §B5's and is not restated here. One owner.

### Power cycle 5 — `quietmc`, the bracket's first half, and the MTD path. `bench/2026-08-31/`

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`OUT X` = `--out bench/2026-08-31/X` — **one token**, not two.

| # | typed / run | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **W-A** | `CAP OUT W-A --esc 25 --esc-period 0.002 --seconds 40` | the ESC window, then `<RealTek>`; the 181-byte cold slice | — | no prompt → power off. That is the seating |
| **W-0r** | `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-08-31/W0-rescue.json` | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1`, in that order | — | any of the three absent |
| **W-0ab** | `CAP OUT W-0ab --send 'DW 8040D4A0 1' --seconds 4` | the word at `0x8040D4A0` = **`00000000`** | **71** | ≠ `00000000` → **STOP. Nothing is uploaded** |
| **W-0t** | `CAP OUT W-0t --send 'DW 805FB3F0 8' --seconds 6` | two lines of DRAM. **Record both.** Line 1 must **not** be sixteen zero bytes | **118** | line 1 already all-zero → `W-2c`'s first half is void this seating; say so and carry on |
| **W-p0** 🆕 | `CAP OUT W-p0 --send 'DW 80A00400 64' --seconds 6` | DRAM. **Must NOT normalise equal to `expect-000000.txt`** | **777** | it DOES match → the destination already holds the flash content and `W-rd0` proves nothing. §3 |
| **W-p6** 🆕 | `CAP OUT W-p6 --send 'DW 80A00500 64' --seconds 6` | as `W-p0`, against `expect-060000.txt` | **777** | as above |
| **W-ph** 🆕 | `CAP OUT W-ph --send 'DW 80A00600 64' --seconds 6` | as `W-p0`, against `expect-h601-6000.txt` | **777** | as above |
| **W-pc** 🆕 | `CAP OUT W-pc --send 'DW 80A00700 64' --seconds 6` | as `W-p0`, against `expect-h601-6400.txt` | **777** | as above |
| **W-1** | `loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin --filename rlxfw-quietmc --rescue-report bench/2026-08-31/W0-rescue.json --expect-load 80500000 --yes` | **1,029,120** bytes accepted | — | any refusal → read it. **Never `--allow-autoexec`** |
| **W-2a** | `CAP OUT W-2a --send 'DW 80500000 8' --seconds 6` | `80500000: 00000000 00008021 40906000 00000000` · `80500010: 00000000 00000000 3C108060 2610B400` | **118** | 🔴 the word at **`0x8050001C`** ≠ `2610B400`, or **`0x80500018`** ≠ `3C108060` → the wrong image. Decode with §4.1's table. ⚠️ **Addresses, not word numbers** |
| **W-2b** | `CAP OUT W-2b --send 'DW 80540000 1' --seconds 4` | `80540000: 162DC569 E3ADCA96 CDB49F15 69045643` | **71** | ≠ → not `quietmc`, whatever `W-2a` said. §4.2 has the other three |
| **W-2c** | `CAP OUT W-2c --send 'DW 805FB3F0 8' --seconds 6` | line 1 = **sixteen zero bytes**; line 2 **byte-identical to `W-0t`'s line 2** | **118** | line 1 ≠ 0 → short transfer. line 2 moved → the write ran past `image_end` |
| **W-flr0** | `CAP OUT W-flr0 --send 'FLR 80A00400 000000 100' --seconds 5` | the echo, `Flash read from 00000000 to 80A00400 with 00000100 bytes\t?`, then `(Y)es , (N)o ? --> ` and **no `<RealTek>`** | **104** | 🔴 **read the echo before typing `Y`.** `FLR`'s first typed argument is the RAM destination; the echo prints `from <flash source> to <RAM destination>`. Pass only if it reads `from 00000000 to 80A00400` — anything else → `W-no` |
| **W-yes0** | `CAP OUT W-yes0 --send 'Y' --seconds 6` | `Flash Read Successed!` then the prompt | **35** | a failure line → record it; the region is not readable and that is the finding |
| **W-rd0** | `CAP OUT W-rd0 --send 'DW 80A00400 64' --seconds 6` | **normalises equal to `bench/2026-08-24d/G8a-rd0.log`** and to `expect-000000.txt`. §5.3 | **777** | any difference → **STOP, do not `J`** |
| **W-flr6 / W-yes6 / W-rd6** | as above with `FLR 80A00500 060000 100`, then `Y`, then `DW 80A00500 64` | `W-rd6` normalises equal to `bench/2026-08-24d/G8a-rd6.log` and to `expect-060000.txt` | 104 / 35 / **777** | as above |
| **W-flrh / W-yesh / W-rdh** 🔴 | as above with `FLR 80A00600 006000 100`, then `Y`, then **`CAP --out /home/key/fwre-work/rebuild/bench-only/b5-20260831/W-rdh --send 'DW 80A00600 64' --seconds 6`** | `W-rdh` normalises equal to `expect-h601-6000.txt` | 104 / 35 / **777** | 🔴 **`--out` is NOT under `bench/`.** These bytes are this unit's MAC and radio calibration. §5.4 |
| **W-flrc / W-yesc / W-rdc** 🔴🆕 | as above with `FLR 80A00700 006400 100`, then `Y`, then **`CAP --out /home/key/fwre-work/rebuild/bench-only/b5-20260831/W-rdc --send 'DW 80A00700 64' --seconds 6`** | `W-rdc` normalises equal to `expect-h601-6400.txt` | 104 / 35 / **777** | 🔴 **the canary page.** A difference here is a **finding, not a failure** — it is the page `FLS-21` saw move. Record it, do not `J`, and read §5.5 before doing anything else |
| **W-2d** | `CAP OUT W-2d --send 'DW 80500000 8' --seconds 6` | **byte-identical to `W-2a`** | **118** | changed → the `FLR` block reached the payload's head. Do not `J`. ⚠️ **32 bytes of 1,029,120 — this cannot find an arbitrary clobber** |
| **W-no** | *only if an `FLR` echo is wrong*: `CAP OUT W-no --send 'N' --seconds 4` | the loader abandons the read and returns to `<RealTek>` | — | 🔴 **the abort cell.** Not in §2's ordered list: it runs only on a branch |
| — | — | — | — | — |
| **W-3** | `CAP OUT W-3 --send 'J 80500000' --seconds 45` | 🔴 **byte-identical to `bench/2026-08-30c/V-3.log`, 849 bytes**, sha256 `8317e7c9fe6eb60f…` | **849** | §6 has the five shapes, and any *difference* is §6.2's question |
| **W-5a** | `CAP OUT W-5a --send 'cat /proc/cpuinfo' --seconds 15` | byte-identical to `bench/2026-08-30c/V-5a.log`, ⚠️ **except `BogoMIPS`, re-measured every boot** | **147** | a prompt that does not echo is **not** a shell |
| **W-5b** | `CAP OUT W-5b --send 'cat /proc/version' --seconds 15` | `… (key@K) … #1 Sun Aug 30 **18:56:00** CST 2026`, sha256 `af2981649f1eb541…` | **111** | `18:56:50` → **`loudmc` booted**. `23:39:33` → `quietm`, yesterday's image. `#1526`/`admin@office.hopeiot` → **unattributed**, not a pass |
| **M-a** 🆕 | `CAP OUT M-a --send 'cat /proc/mtd' --seconds 12` | three lines, §7.1, sha256 `e1272b93828f3b5b…` | **126** | any other map. **Reads zero flash bytes** — `mtd_read_proc` prints the driver's own table |
| **M-b** 🆕 | `CAP OUT M-b --send 'wc -c < /dev/mtd0ro' --seconds 25` | `1245184` | **32** | `No such file or directory` → the node is not in the image. `No such device` → no chrdev at major 90. `Permission denied` → the odd-minor rule is not what §7.2 says. A hang → the read path stalls |
| **M-c** 🆕 | `CAP OUT M-c --send 'wc -c < /dev/mtd1ro' --seconds 40` | `2949120` | **32** | as above |
| **M-d** 🔴🆕 | `CAP OUT M-d --send 'echo x > /dev/mtd0ro' --seconds 12` | `sh: can't create /dev/mtd0ro: Permission denied` | **73** | 🔴 **a SUCCESS here is a stop-if for the whole seating.** Power off and write it up. §7.3 |
| **W-6a** | `CAP OUT W-6a --send 'ifconfig -a' --seconds 15` | byte-identical to `bench/2026-08-30c/V-6a.log` — 23 interfaces | **7,658** | fewer than six `ethN` → the netdevs did not register |
| **W-6b** | `CAP OUT W-6b --send 'ifconfig eth4 10.1.1.10 netmask 255.255.255.0 up' --seconds 10` | no error | **52** | — |
| **host** | `ip neigh flush dev <if>` then `tcpdump -i <if> -n -e 'icmp or arp'` **running throughout** | — | — | hygiene, not the fix it was in `G7` |
| **W-7a** | `CAP OUT W-7a --send 'ping -c 4 10.1.1.2' --seconds 20` | 4/4, and request+reply in the host capture. ⚠️ the RTT is quantised to `CONFIG_HZ=100`'s 10 ms, so this row is *the shape*, not byte-identity | ≈**420** | ARP requests and no ARP replies = the host, not the driver |

### Power cycle 6 — the same image again, the bracket's second half, and the null. `bench/2026-08-31b/`

🔴 **Identical to cycle 5 up to the prompt, and that is the experiment.** Do not
shorten it: the residual `FW-32 殘留` is about, 0.250 s, is a *difference between two
boots*, and a cycle that did less before the `J` is not a second sample of the
same thing.

| # | typed / run | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **X-A** | `CAP --out bench/2026-08-31b/X-A --esc 25 --esc-period 0.002 --seconds 40` | the 181-byte cold slice | — | no prompt → power off |
| **X-ab** | `CAP --out bench/2026-08-31b/X-ab --send 'DW 8040D4A0 1' --seconds 4` | 🔴 **`00000001`** | **71** | `00000000` → this is **not** a fresh boot and the bracket proves nothing |
| **X-0r / X-0t / X-p0 / X-p6 / X-ph / X-pc** | as `W-0r` / `W-0t` / the four pre-reads, `--out bench/2026-08-31b/…` | as cycle 5 | — / 118 / 777 ×4 | as cycle 5 |
| **X-1 / X-2a / X-2b / X-2c** | as cycle 5, same image, same expectations | as cycle 5 | — / 118 / 71 / 118 | as cycle 5 |
| **X-flr0 / X-yes0 / X-rd0** | as `W-flr0` / `W-yes0` / `W-rd0` | `X-rd0` normalises equal to `W-rd0` **and** to `G8a-rd0.log` | 104 / 35 / **777** | any difference → the write-up starts from this capture |
| **X-flr6 / X-yes6 / X-rd6** | as the `6` triple | `X-rd6` normalises equal to `W-rd6` **and** to `G8a-rd6.log` | 104 / 35 / **777** | as above |
| **X-flrh / X-yesh / X-rdh** 🔴 | as the `h` triple; **`--out /home/key/fwre-work/rebuild/bench-only/b5-20260831/X-rdh`** | normalises equal to `W-rdh` **and** to `expect-h601-6000.txt` | 104 / 35 / **777** | as above. **`--out` is NOT under `bench/`** |
| **X-flrc / X-yesc / X-rdc** 🔴 | as the `c` triple; **`--out /home/key/fwre-work/rebuild/bench-only/b5-20260831/X-rdc`** | normalises equal to `W-rdc` **and** to `expect-h601-6400.txt` | 104 / 35 / **777** | as above |
| **X-2d** | as `W-2d` | byte-identical to `X-2a` | **118** | as cycle 5 |
| **X-3** 🔴 | `CAP --out bench/2026-08-31b/X-3 --send 'J 80500000' --seconds 45` | **byte-identical to `W-3`**, 849 bytes | **849** | a difference in the BYTES is a finding about the image; a difference in the **timing** is the reading this cycle exists for. §8 |
| **X-5b** | `CAP --out bench/2026-08-31b/X-5b --send 'cat /proc/version' --seconds 15` | byte-identical to `W-5b` | **111** | it is a different image → the two boots are not the same variant and §8 is void |

---

## §1 The prefixes

`W` for power cycle 5, `X` for power cycle 6, `M` for the four MTD cells inside
cycle 5. **`Y` is skipped**, as it was in block 2: `Y` is the literal string
typed at the `FLR` confirmation prompt, and a cell named `Y-…` beside a
`--send 'Y'` is a reading waiting to be misfiled. **`Z` is skipped** because
`bench/2026-08-30d/` already holds `Z-*` and a sweep that walks captures back to
predictions has to be able to tell them apart.

## §2 Cells, in order

```cells
bench/2026-08-31/W-A
bench/2026-08-31/W-0ab
bench/2026-08-31/W-0t
bench/2026-08-31/W-p0
bench/2026-08-31/W-p6
bench/2026-08-31/W-ph
bench/2026-08-31/W-pc
bench/2026-08-31/W-2a
bench/2026-08-31/W-2b
bench/2026-08-31/W-2c
bench/2026-08-31/W-flr0
bench/2026-08-31/W-yes0
bench/2026-08-31/W-rd0
bench/2026-08-31/W-flr6
bench/2026-08-31/W-yes6
bench/2026-08-31/W-rd6
bench/2026-08-31/W-flrh
bench/2026-08-31/W-yesh
bench/2026-08-31/W-flrc
bench/2026-08-31/W-yesc
bench/2026-08-31/W-2d
bench/2026-08-31/W-3
bench/2026-08-31/W-5a
bench/2026-08-31/W-5b
bench/2026-08-31/M-a
bench/2026-08-31/M-b
bench/2026-08-31/M-c
bench/2026-08-31/M-d
bench/2026-08-31/W-6a
bench/2026-08-31/W-6b
bench/2026-08-31/W-7a
bench/2026-08-31b/X-A
bench/2026-08-31b/X-ab
bench/2026-08-31b/X-0t
bench/2026-08-31b/X-p0
bench/2026-08-31b/X-p6
bench/2026-08-31b/X-ph
bench/2026-08-31b/X-pc
bench/2026-08-31b/X-2a
bench/2026-08-31b/X-2b
bench/2026-08-31b/X-2c
bench/2026-08-31b/X-flr0
bench/2026-08-31b/X-yes0
bench/2026-08-31b/X-rd0
bench/2026-08-31b/X-flr6
bench/2026-08-31b/X-yes6
bench/2026-08-31b/X-rd6
bench/2026-08-31b/X-flrh
bench/2026-08-31b/X-yesh
bench/2026-08-31b/X-flrc
bench/2026-08-31b/X-yesc
bench/2026-08-31b/X-2d
bench/2026-08-31b/X-3
bench/2026-08-31b/X-5b
```

**Fifty-four cells**, 31 in cycle 5 and 23 in cycle 6.

**Named on the card but not in the block, on purpose:**

* 🔴 **`W-rdh`, `W-rdc`, `X-rdh`, `X-rdc`** — the four captures that carry
  `H601`'s bytes. They are written outside this repository (§5.4), so
  `check-predictions.py` cannot see them and **their ordering is unenforced**.
  That gap is already carried forward (*a capture that cannot be committed*),
  and this block **doubles it from two files to four**, which is a cost and is
  written down rather than absorbed.
* **`W-no`** — the abort cell. It runs only if an `FLR` echo is wrong, and
  naming a branch that should not be taken would guarantee a violation.
* **Not captures at all**: `W0-rescue.json`, `X0-rescue.json`, the two
  `loader-tftp.py put` transcripts, `W7a-host.txt`/`.err`, and the video.

## §3 🆕 The pre-read, and it is the control this bracket has never had

`W-p0`, `W-p6`, `W-ph`, `W-pc` read the four `FLR` destinations **before** any
`FLR` runs.

🔴 **What the bracket claims, and what it has actually been showing.** The claim
is *these flash bytes are unchanged since the 2026-08-16 dump*. The evidence is
that a `DW` of the destination, after an `FLR`, matches a rendering of the dump.
That chain has a hole in the middle: **nothing has ever shown that the `FLR`
wrote anything.** An `FLR` that silently did nothing, over a destination that
happened to hold the right bytes, produces exactly the same capture.

Block 2 could not close it, and the reason was mechanical rather than an
oversight. `cmp` on a `DW` reply compares the whole reply — the echoed command
and the `%08X:` address column both carry the RAM destination — so a capture
taken at one destination can only be compared with a capture taken at the *same*
destination. That forced cycle 4 to reuse cycle 3's addresses, and with the
address pinned there was nowhere to put a pre-read that could be compared
against anything.

`flashwin normalise` (new 2026-08-30, `N1`–`N5`) reduces a `DW` reply to its
data. `N2` is the case that matters: the same flash window rendered at RAM
`0x80B50000` normalises **identically** to the capture taken at `0x80A00000`.
`N3` is its control: two different windows do not.

So this block does two things block 2 could not:

| | |
|---|---|
| the destinations **move** to `0x80A00400`–`0x80A00700` | a match can no longer be explained by anything left at block 2's addresses, in this power cycle or any earlier one |
| each destination is **read first** | the pre-read must NOT normalise equal to the expectation. If it does, the `FLR` that follows is uninterpretable and this block says so instead of reporting a pass |

**Prediction.** All four pre-reads differ from their expectations. 推 rather than
量, and the strength is worth stating: `MEM-16` measures this DRAM's power-on
bias as **89.5 % reproducible against a measured null of 55.98 %**, so the
content is neither random nor arbitrary — but it is not flash, and a 256-byte
accidental match is not a thing this project needs to bound numerically.

**Refuted by** any pre-read that normalises equal to its expectation. That
outcome is *not* a bench failure; it is a finding about the loader or the DRAM,
and it voids that one window for this seating.

⚠️ **What it still does not close.** The pre-read shows the destination changed.
It does not show the bytes came from the *flash offset asked for* — the `FLR`
echo check (`from <source> to <destination>`) is what covers that, and it stays
on every row.

## §4 Which image landed

### §4.1 `W-2a`: the last two words are the whole cell

```
80500000:	00000000	00008021	40906000	00000000
80500010:	00000000	00000000	3C108060	2610B400
```

量 today, straight out of the uploaded file: words 6 and 7 at file offsets
`0x18`/`0x1C` are `3C108060` `2610B400` — `lui s0,0x8060` / `addiu s0,s0,-0x4C00`,
the linker's `__vmlinux_end` = `0x805FB400` = `0x80500000 + 1,029,120`.

**The first line does not discriminate** and is printed only because `LDR-07`
rounds a length of 8 up to two whole lines — every `nfjrom` shares `rtkload`'s
`start.o` (§B5-c1).

| word 6 · word 7 | = | that would be |
|---|---|---|
| `3C108060` · **`2610B400`** | `0x805FB400` | 🟢 **`quietmc`. The pass** |
| `3C108060` · `2610AC00` | `0x805FAC00` | 🔴 **`quietm`** — yesterday's image went up |
| `3C108060` · `26101800` | `0x80601800` | 🔴 **`loudmc`** |
| `3C108060` · `26101400` | `0x80601400` | 🔴 **`loudm`** |
| `3C10805F` · `26101000` | `0x805F1000` | 🔴 **the staged vendor image — the transfer did not land** |

### §4.2 `W-2b`: the variant, at a word where no two of the four agree

`--send 'DW 80540000 1'`. **71 bytes.** File offset `0x40000`, inside the LZMA
stream. 量 today, from the four images on this disk:

| | first four words at `0x80540000` |
|---|---|
| **`quietmc`** | `162DC569 E3ADCA96 CDB49F15 69045643` — **the pass** |
| `loudmc` | `ADDA1F6B A4DE8C84 7DC1FBC3 398E0BA1` |
| `quietm` | `AFBD0BEE AE8D991B A39DEE9F 2A62E61B` — **the one to fear**, because it is what a second upload of yesterday's file looks like |
| `loudm` | `CEC3FFD9 C013013E CE652208 749F1E48` |

### §4.3 `W-0t` / `W-2c`: the tail

量 today: `0x80500000 + 1,029,120` = `0x805FB400` exactly, so the read is at
**`0x805FB3F0`**. `quietmc`'s trailing zero run is **652 bytes** (`quietm`'s was
552), from `rtkload/ld.script.in` aligning `__vmlinux_end` to 1024 — so the last
16 bytes are zero after the transfer and are the positive control, while the
line above `image_end` is the negative one.

⚠️ **Can it be read before the upload?** `0x805FB3F0` is **41,966 bytes** above
the loader's staged copy of the vendor image, which ends at `0x805F1002`
(讀 + 推, `SPEC.md` `LDR-39`; **not** 量, and `MAP-17` is not a second source for
it). Block 2's margin was 39,918. Clear, and recorded rather than assumed.

## §5 The flash bracket — four windows, and the fourth is the one that moves

### §5.1 What it buys

Four 256-byte windows × two rounds = **2,048 bytes of 4,194,304 = 0.0488 %**,
against block 2's 0.0183 %. `H601` reach goes from 256/8,192 (**3.1 %**) to
512/8,192 (**6.3 %**).

🔴 **It still does not make the sentence `G8b` forbids sayable.** It cannot see
two writes that cancel, it cannot see a write outside the four windows, and
93.7 % of `H601` remains unread by anything but the 2026-08-16 dump. The
sentence that may be written is `G8b`'s, verbatim, with the four regions named.

### §5.2 The four windows

| window | flash | RAM this block | expectation | why this one |
|---|---|---|---|---|
| loader head | `0x000000` | `0x80A00400` | `expect-000000.txt`, and `bench/2026-08-24d/G8a-rd0.log` | the region a wrong write bricks the device in |
| `cr6c` header | `0x060000` | `0x80A00500` | `expect-060000.txt`, and `G8a-rd6.log` | ⚠️ **no rule forbids writing it** — it is in the bracket because there is a committed capture to compare against, which is a different reason from the other three |
| `H601` head | `0x006000` | `0x80A00600` | `expect-h601-6000.txt` | this unit's MAC and radio calibration |
| 🆕 `H601` canary | `0x006400` | `0x80A00700` | `expect-h601-6400.txt` | **the only page of `H601` this device has ever been seen to change** |

### §5.3 The `cmp` matrix, and it is `normalise` now

Every comparison in this block runs on **normalised** captures:

```
/usr/bin/python3 tools/flashwin.py normalise <capture> --out /tmp/a
/usr/bin/python3 tools/flashwin.py normalise <expectation> --out /tmp/b
cmp /tmp/a /tmp/b
```

| edge | what it covers |
|---|---|
| `W-rd0` ≡ `expect-000000.txt` | the window is unchanged since the dump |
| `W-rd0` ≡ `G8a-rd0.log` | **and the renderer is the same one** that reproduced a 2026-08-24 device capture. `flashwin`'s `R1`/`R2` are that claim as a control |
| `W-rd0` ≢ `W-p0` | the `FLR` wrote. §3 |
| `X-rd0` ≡ `W-rd0` | two rounds, and `X-ab` = `00000001` says the second is a separate observation |

### §5.4 Why `W-rdh`, `W-rdc`, `X-rdh` and `X-rdc` are written outside this repository

Their bytes are this unit's MAC and radio calibration. They go to
`$FWRE_WORK/rebuild/bench-only/b5-20260831/`, **and not even their sha256 is
published**: with the rest of a 256-byte `H601` window known, a digest is a
2^24 search for the address. `flashwin` enforces both — it refuses to print a
digest for a forbidden window and refuses `--out` inside this repository.

🔴 **And that argument is now weaker than it was, from the other direction.**
量 2026-08-31 (`SPEC.md` `FLS-22`): the six bytes at `H601+0x07` and `H601+0x13`
are already printed verbatim in the **public** `upstream/BENCH-LOG.md:216`, and
45 of `H601`'s 146 non-zero bytes are recoverable from that repository. The rule
here does not change — this repository does not add to it — but *"the only
unknown is 24 bits"* is, for that particular window, an understatement rather
than a bound.

### §5.5 🆕 `W-rdc`: a difference here is a finding

`FLS-21`, 量 2026-08-30, offsets only: `$FWRE_WORK/dumps/w06-S3-fired.bin`
(2026-08-17) differs from the reference dump by **9 bytes at
`0x00648A`–`0x006493`** — page `0x006400`, and **zero** of them inside the
`0x006000`–`0x0060FF` window the bracket had been using. `w06-S4-final.bin`,
seven minutes later, differs by none. 讀 `upstream/BENCH-LOG.md`: a `formWsc`
POST wrote `HW_WLAN0_WSC_PIN` and the device recomputed the region checksum at
`0x006493`, three times.

So this page carries **both** a field that has been seen to move and the
device's own checksum over it.

🔴 **And its whole information content is those nine bytes.** 量 today, offsets
only: page `0x006400` holds **9 non-zero bytes out of 256**, at `+0x8A`–`+0x91`
and `+0x93` — exactly the span `FLS-21` measured moving, and nothing else. So a
`W-rdc` that matches is 247 bytes of agreeing that zero is still zero plus 9
bytes that are the reading. **The window is not 256 bytes of evidence and this
card does not count it as such** — the same mistake, one order of magnitude
smaller, as the `H601` coverage figure that came out at 98.9 % before the zeros
were taken out of it (`SPEC.md` `FLS-22`).

⚠️ It does mean the pre-read control (§3) is safe here: for `W-pc` to match the
expectation spuriously, power-on DRAM would have to be zero everywhere except
those same nine offsets.

If `W-rdc` differs from the expectation:

* it is **not** a stop-if in the sense the other three are — nothing this
  seating did could have written it, and the dump is 14 days old;
* it is the first evidence in this project that `H601` moved **without** a
  `formWsc` POST, and that is a bigger finding than the bracket;
* record it, do **not** `J`, and do not attempt any comparison that would
  require publishing the bytes.

## §6 `W-3` — the boot, and the prediction is byte-identity

**849 bytes, byte-identical to `bench/2026-08-30c/V-3.log`**, sha256
`8317e7c9fe6eb60f004624c06913cc316ebaaf632c07a9aeee9ebb8ef04869a9`.

### §6.1 Why byte-identity is the right prediction and not a lazy one

Three things could have moved it and 量 says none of them does:

| | |
|---|---|
| addresses in the text | the only address `V-3.log` prints is `start address: 0x80003600`, which is the kernel **entry**, not `__vmlinux_end`. It does not move with image size |
| mtdchar's own output | 讀 `drivers/mtd/mtdchar.c`: `init_mtdchar` prints only on `register_chrdev` failure, through `printk`, which `CONFIG_PRINTK=n` removes. The map driver's `printk(KERN_NOTICE "name=%s, size=0x%x\n", …)` at `rtl819x_flash.c:333` is in **`quietm` too** and does not appear in `V-3.log` — so the observation, not the reasoning, is what says it stays silent |
| the 448 bytes of driver output | `FW-31`: 13 of those 15 lines are `rtlglue_printf` → `panic_printk`, which no Kconfig symbol controls. Unchanged between the two builds |
| the two marks that carry runtime values | `RLXFW-B02` is `PRId` and `RLXFW-B07` is a register read, so either could in principle move. 量: both are byte-identical across `bench/2026-08-30b/L3.log` (`loudm`) and `bench/2026-08-30c/V-3.log` (`quietm`) — `0000CD01` and `00000000`, n=2 across two variants. **推 that they hold, and it is the weakest clause in this prediction** |

### §6.2 So a difference is the interesting outcome

If `W-3` is **not** 849 bytes, the first question is whether the extra text is
mtdchar's. That would mean a `printk` survived `CONFIG_PRINTK=n` by a route this
project has not mapped, which is `FW-31`'s territory and worth more than the
prediction it broke.

Five failure shapes — no output at all, output stopping at `start address:`,
stopping inside the marks, a prompt that does not echo, and a prompt that echoes
but `cat` fails — are §B5-c3's and are not restated here.

## §7 `M-a`–`M-d` — the MTD path

### §7.1 `M-a`: `cat /proc/mtd`, and the erasesize field is not what `SPEC.md` says

```
dev:    size   erasesize  name
mtd0: 00130000 00001000 "boot+cfg+linux"
mtd1: 002d0000 00001000 "root fs"
```

**126 bytes**, sha256 `e1272b93828f3b5be9598a0148f574974cb1e82849d8e2284edf948d87d87564`.
Every field is 讀, and the chain is worth writing out because the middle of it
is a surprise:

| | |
|---|---|
| the format | 讀 `drivers/mtd/mtdcore.c:569` (the header) and `:561` (`"mtd%d: %8.8llx %8.8x \"%s\"\n"`) |
| the names and sizes | 讀 `drivers/mtd/maps/rtl819x_flash.c:171-186`, the `CONFIG_ROOTFS_SQUASH` non-dual-image branch. 讀 `quietmc.config-built`: `CONFIG_ROOTFS_SQUASH=y`, `CONFIG_RTL_ROOT_IMAGE_OFFSET=0x130000`, `CONFIG_RTL_FLASH_SIZE=0x400000` |
| 🔴 the **erasesize** | 讀 `drivers/mtd/mtdpart.c:471` — a partition inherits the master's. 讀 `drivers/mtd/chips/rtl819x/spi_probe.c:99` — `mtd->erasesize = chip_info->flash->sectorSize`. And 讀 `spi_common.c:566-573`: **this unit's JEDEC id `0x1C7016` is in no row of the kernel's chip table either**, so `spi_regist` takes its UNKNOWN fallback — `set_flash_info(…, SIZE_064K, SIZE_004K, SIZE_256B, "UNKNOWN", …)` — and `sector_size` is `SIZE_004K` = **`0x1000`** |

🔴 **That is a third source on a number this project holds two answers for.**
`FLS-08` says the erase granularity is 64 KiB, from the *loader's* unknown-chip
descriptor; `FLS-13` says 4 KiB, inferred from `FLW` being able to write `FF`
back. The kernel's own driver takes `sector_size`, not `block_size`, and its
unknown-chip fallback sets that to 4 KiB. **`M-a` is the first device-side
reading of which of the two the kernel believes**, and it costs one typed line.

⚠️ **And it says the kernel is in the same position as the loader.** `FLS-10`
records that the loader's 32-entry chip table has no match for `1c7016` and
prints `chipName: UNKNOWN`. 量 today: the kernel's table has 29 rows and no
match either. Two independent tables, same outcome, and the device works because
both have a sane fallback.

### §7.2 `M-b` / `M-c`: what a size buys

`wc -c` on a character device has no shortcut: 讀 `mtd_read`, every byte goes
through `part_read` → `rtl819x_flash`. So the two cells together read
**4,194,304 bytes — the whole part — through a path the kernel will not let
anything write**, and `M-b` alone reads all 8,192 bytes of `H601`.

⚠️ **It is not a content check and does not move `FLS-20`.** Nothing compares
the bytes to anything: this userspace has no `dd`, `md5sum`, `od`, `hexdump`,
`cmp`, `cksum`, `sum` or `sha1sum` (量, two routes, `notes/rootfs-census.md`).
What it establishes is that the *path* works end to end over the region a wrong
write cannot be undone in.

**`wc` is present** — 量 2026-08-30 under `qemu-mips-static` against this unit's
own extracted rootfs, through `tools/vendor-tripwire.sh`: the binary's applet
table lists 50 names and `wc` is one of them, with the negative control
(`definitely_not_an_applet: applet not found`) in the same run. **And its output
carries no field padding**: 量, three sizes through this exact busybox, the
digits and nothing else. That is where the 32-byte counts come from.

**The 25 s and 40 s terminators** are sized on the read, not the reply: 1.25 MB
and 2.95 MB through `rtl819x_flash` at SPI speed, with nothing on the wire until
it finishes. If either returns nothing in the window, that is a hang and it is
the stop-if.

### §7.3 `M-d`: the positive control on the safety property, at zero cost

讀 `drivers/mtd/mtdchar.c`, `mtd_open`:

```
int minor = iminor(inode);
int devnum = minor >> 1;
if ((file->f_mode & FMODE_WRITE) && (minor & 1))
        return -EACCES;
```

`/dev/mtd0ro` is `c 90 1`: `minor >> 1` = device 0, `minor & 1` = 1, so a write
open is refused **by the kernel**, before any write is issued — which is why
this cell costs zero flash bytes. That is stronger than any mode bit, because
root ignores DAC.

**The expected line is measured, not guessed**: 量 2026-08-30, this unit's own
busybox under `qemu-mips-static` with an `EACCES` target produces
`sh: can't create <path>: Permission denied`, which is where the 73 bytes come
from.

⚠️ **One source in three copies.** `mtdchar.c` is byte-identical across the
three GPL drops that carry it (md5 `83d6fc7bbec987be1cbca27d8bc006bd`) — the
same weakness that travels with the `PRId` assignment table. The enforcement is
**讀 until `M-d` runs on the silicon**, and that is the whole point of the cell.

🔴 **If `M-d` succeeds**, then either the node in the image is not `c 90 1`, or
this kernel's `mtdchar.c` is not the one that was read. Both are reasons to stop:
the image contains a writable path to the loader region, and nothing else on the
card is worth more than finding that out cleanly.

## §8 🆕 Cycle 6 and the `FW-32 殘留` null

`SPEC.md` `FW-32 殘留`: `quietm` reaches the prompt **1.711 s** before `loudm`,
and the byte difference explains **1.461 s** (5,610 B ÷ 3,840 B/s). The residual
**0.250 s** has two candidates that cannot be separated — `printk`'s formatting
and console-lock cost, or ordinary between-boot variation — **because there is
n=1 on each side**.

Cycle 6 is the null. Two boots of the **same** image, with the same preceding
activity, give the first measurement of between-boot variance on this device.

| | |
|---|---|
| the reading | `X-3.timing`'s last offset minus its first, against `W-3.timing`'s |
| 推 | the two agree within the residual — the absolute difference is **under 0.250 s**, which would leave the residual attributable to `printk` |
| **refuted by** | an absolute difference of **0.250 s or more** — in which case the residual is *within* boot-to-boot noise, `FW-32 殘留`'s two candidates both stay open, and the null is measured instead of assumed |

⚠️ **This is n=2, not a curve.** Two boots bound the variance about as well as
two boots can, which is to say weakly, and the row that records it must say so.

## §9 What this block cannot show

| | |
|---|---|
| that no flash byte was written | 2,048 of 4,194,304 bytes, four windows, two rounds. Two writes that cancel are invisible; a write outside the four windows is invisible; 93.7 % of `H601` is unread |
| that the MTD path is read-only in general | `M-d` shows one node refuses one write open. It says nothing about `/dev/mtd1ro`, and nothing about any path the *kernel* takes internally |
| that `quietmc` is byte-identical to `quietm` in behaviour | the boot text is predicted identical; `M-a`–`M-d` are the difference, and they are the only cells that exercise it |
| that the pre-reads bound the accidental-match probability | §3 is 推 on `MEM-16`'s bias, not a computed bound |

## §10 The check

```
/usr/bin/python3 tools/check-predictions.py bench/2026-08-31/PREDICTIONS-B5-block3.md
```

**`0 of 54` before the seating, and that is the correct answer.** 量: it reports
`0 of 54 captures came after the prediction, 54 did not`, which is what a block
written before its seating must say. The four `H601` captures are not in the
block at all (§2), so they are not among the 54.

🆕 **And every number on this card was re-derived from the artefacts after it was
written, not just when it was written.** 量 2026-08-31: **36 of 36** — the
image's size and digest, both head words and the `image_end` they decode to, the
tail address and the 652-byte zero run, the variant line, the nine non-zero bytes
of the canary page and their exact offsets, all five shell-cell byte counts and
two of their digests, the boot's 849 and its digest, both partition sizes, seven
reply sizes through `reply-size.py`'s model, and the four expectation files'
lengths.

⚠️ **The checker that did it is a scratchpad script and is deliberately not
committed.** It has no controls and no mutation suite, and writing a new
instrument at the end of a long session — into the path a seating depends on —
is the shape `P7` exists to prevent. What it bought is this paragraph: the card's
own claim that its values are *computed rather than transcribed* is now something
that was actually re-run, once, rather than a description of intent. Generalising
it belongs beside `check-predictions.py` and goes in as its own step.
