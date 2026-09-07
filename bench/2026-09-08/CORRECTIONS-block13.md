# Corrections and additions — block 13, `R5-5`, seating 16

**2026-09-08, forty-third segment, after power.** The card
(`PREDICTIONS-B14-block13.md`) is frozen and is not edited; `RUNSHEET.md`'s
lifecycle rule 1 says corrections go here.

One power cycle. **00:00:02 → 00:32:16**, ten boots, 32 carded cells all
captured, `check-predictions` **`32 of 32`**. **Zero flash-write commands, zero
`FLR`.** `AUTOBURN` was read as a *word* at `0x8040D4A0` by `looprun`'s `S5b`
gate eleven times (ten boots plus one aborted attempt) and read `00000000`
every time; the driver's own `n_writes` read **0** in every dump.

---

## 1. 🟢 What the card predicted, and what the board printed

Every field prediction on the card hit. The two the card called coin-flips are
the ones worth naming, because both were read out of the **vendor's compiled
code** and both contradicted a value this project had already *measured* at the
loader prompt.

| | card | board | |
|---|---|---|---|
| `S1` `sfcr` | `FFC00000` (÷16) | `FFC00000` | 🟢 against `REG-13`'s `3FC00000` (÷4) |
| `S3` `sfcsr` | `C8000000` | `C8000000` | 🟢 against `D8050000` |
| `S2` `sfcr2` | `0BA08000` | `0BA08000` | 🟢 |
| `S4` `kat_rc` | `0` | `0` | 🟢 |
| `S5` `wedged` | `0` | `0` | 🟢 |
| `S6` `mtd_index` | `2` | `2` | 🟢 |
| boot capture | **1,318 bytes** | **1,318 bytes**, all ten | 🟢 |
| `RLXFW-ID0` | `FCE0AF22` | `FCE0AF22`, all ten | 🟢 |
| `C1-M` | `mtd2: 00400000 00001000 "rtl819x-spi-pio"` | identical | 🟢 |
| `C1-SZ` | `4194304` | `4194304` | 🟢 |
| `C1-EA` | `Permission denied` | `can't create /dev/mtd2ro: Permission denied` | 🟢 |
| `C1-TW` | `n_write_refused 2`, `n_writes 0` | both | 🟢 |
| `C1-WD` | `n_state_bad 1` | `1` | 🟢 |
| `C1-PR` | `n_xfer +1`, `n_pio_bytes +4` | 1025→1026, 4194308→4194312 | 🟢 |
| `C1-V4` | `cmp_bytes 4096`, `cmp_equal 1` | identical | 🟢 |
| `C1-V64` | `cmp_bytes 65536`, `cmp_equal 1`, `h601_skipped 8192` | identical | 🟢 |
| `C1-NG` | `cmp_first_diff 1048576` | `1048576`, `cmp_equal` 1→0 | 🟢 the control fired |
| `C1-F` | `n_writes 0`, `n_state_bad 1` | both, plus `n_state_foreign 0` | 🟢 |
| **`C1-VF` `d1_match`** | **`1`** | **`0`** | 🔴 **refuted — §3** |
| **`C1-NF` `d1_match`** | **`1`** | **`0`** | 🔴 same single cause, not a second finding |

🔴 **`REG-38` goes 讀 → 量**, and the direction is worth keeping: the value
inferred from the vendor's *compiled* driver beat the value read off this
device's own loader prompt. `SFCR`/`SFCSR` under Linux are `FFC00000` /
`C8000000`, on all ten boots. The driver's own classification agrees without
being asked: `sfcr_as_loader 0`, `sfcr_as_kernel 1`.

### 1.1 🟢 Ten boots, and the only variation is one LED bit

The ten boot captures are **1,318 bytes each** and fall into exactly **two**
sha256 values. The whole difference is one line: `RLXFW-G3` reads `0000003C` on
eight boots and `0000007C` on two (`C8` and `C10`, mutually byte-identical).
`0x3C ⊕ 0x7C = 0x40` — **bit 6**.

`G3` is `dat`, the GPIO data register snapshot (`rtl819x-gpio.c:646`), and bit 6
is the bit `FW-40` records the vendor's `rtl_gpio_timer` blinking on a ~2 s
cycle. **So ten boots of this image are byte-identical except for one bit that
belongs to a vendor timer, sampled at two phases.** `FW-40` was measured from
the button side in seating 15; this is the same alternation seen from the boot
snapshot, which is an independent direction on it.

---

## 2. 🔴 What ran that was NOT on the card, and why

The card is frozen; these cells are additions and sit **outside** its fence, so
`check-predictions` counts them as `out` rather than as cells. They are listed
here because a capture in a fenced directory with no owner is worse than one
that is declared.

| cells | what | why it could not wait |
|---|---|---|
| `BIS-8192` … `BIS-57344` (19) | `verify <n>` at every 4 KiB step, digest compared against the 2026-08-16 dump computed at the desk with the same scope | the `D1` refutation is the seating's headline and the board was up. Each rung cost about six seconds; localising it next seating would cost a power cycle |
| `SEC-8`, `SEC-9`, `SEC-10` | an attempt at an independent on-board digest of three erase sectors via `/dev/mtd2ro` + busybox | it failed, and the failure is the finding — §4.5 |
| `BBLIST` | `busybox --list` | to stop future cards guessing which applets exist. It also failed — §4.5 |
| `C1-ab2-att1` | `looprun` `S5b`'s burn-flag word from the aborted first attempt | preserved rather than overwritten — §4.2 |
| `C1-F-early`, `C1-F-early2` | two `C1-F` dumps taken out of order by a false gate stop | preserved rather than overwritten. The real `C1-F` is the third and is the one in the fence |

---

## 3. 🔴 `D1` is refuted, `D3` holds, and the refutation is localised to one erase sector

### 3.1 The reading

`C1-VF`, one traversal of all 4,194,304 bytes:

```
cmp_bytes 4194304   cmp_equal 1   cmp_first_diff -1   d1_d3_agree 1
digest_bytes 4186112   h601_skipped 8192   h601_hashed 0
d1_match 0
d1_sha256 a16735789a3301a1a65201b912d2c42e19f1685469bd5a0adcfa55e7100d49eb
```

🟢 **`D3` holds.** The PIO path and the memory-mapped window at `0xBD000000`
agree over every one of the 4,194,304 bytes. **Nothing had ever read that window
under Linux before tonight** — `C1-V4` is the first, at 4 KiB, and `C1-VF` the
first past a kilobyte.

🔴 **`D1` is refuted.** `FLS-24` says the `H601` complement digests to
`a9916fd8…4ce3cba`. The board says `a1673578…100d49eb`.

### 3.2 🔴 Three ways it could have been the instrument, and all three are closed

This repository's rule is to name the tool that could be lying. Three could:

1. **The compiled-in constant is wrong.** 量: the complement
   (`[0,0x6000) ∪ [0x8000,0x400000)`, 4,186,112 bytes) was recomputed at the desk
   from **both** dump files by an independent implementation, and both give
   `a9916fd86adb49ff0a4f53d49bc377ca5c54321dcff02bdb55e7b4ab64ce3cba` — equal to
   `FLS-24` and to the constant in `rtl819x-spi.c`. **Closed.**
2. **The driver's sha256 or its scope is wrong.** 量: `C1-V4`'s own digest of the
   first 4,096 bytes is `e7d529d2…9697647d`, and the dump's first 4,096 bytes
   digest to **exactly that**. The engine and the scope reproduce an independent
   implementation. **Closed.**
3. **The digest cannot fail.** 量: `C1-NG` injected one changed byte at 1,048,576
   and the digest moved to `1682557547a05ef1…` — a different value over the same
   4,194,304 bytes. And `C1-VF` and `C1-NF` are **two independent full
   traversals returning the identical digest**, so the reading is n=2 and not a
   one-off. **Closed.**

⚠️ **The `d1_match` FLAG itself has no positive control in this seating** — it
read `0` in every cell, so nothing here shows it can read `1`. That is stated
rather than glossed: what licenses the refutation is the three items above, not
the flag.

### 3.3 🟢 Localised to `[0x9000, 0xA000)` — one erase sector

`verify <n>` hashes `[0, min(n,0x6000))` and `[0x8000, n)`, and rounds `n` down
to `RTL819X_SPI_CHUNK` = 4096 (`rtl819x-spi.c:765`, `limit &= ~(CHUNK-1u)`).

| `verify n` | hashed | vs the 2026-08-16 dump |
|---|---|---|
| 8192 … 24576 | 8192 … 24576 | **SAME** |
| **32768** | **24576** | **SAME** — this covers exactly `[0, 0x6000)` |
| **36864** | **28672** | **SAME** |
| **40960** | **32768** | 🔴 **DIFFERS** |
| 49152, 57344, 65536, all | | DIFFERS |

Nothing lies between `verify 36864` and `verify 40960` but `[0x9000, 0xA000)`.

🔴 **The first difference is exactly 4,096 bytes at `[0x9000, 0xA000)` — one
erase sector** (`/proc/mtd` erasesize `00001000`), inside `mtd0`'s
`"boot+cfg+linux"`, immediately above `H601`.

🟢 **And the safety question came back the right way.** `verify 32768` covers
`[0, 0x6000)`, the **whole loader region**, and it is byte-identical to the
2026-08-16 dump over all **24,576** bytes. Every `FLR` bracket in this project
combined had sampled **256** of them.

### 3.4 What this seating can and cannot say about the flash

| | bytes | of 4,194,304 |
|---|---|---|
| proven **identical** to the 2026-08-16 dump | **28,672** | 0.684 % |
| proven **different** | **4,096** | 0.098 % |
| **undetermined** (above `0xA000`) | 4,153,344 | 99.02 % |
| never hashed, by rule (`H601`) | 8,192 | 0.195 % |

🔴 **Prefix digests find the FIRST difference and nothing past it.** `verify`
takes a limit and **no offset**, so whether anything above `0xA000` also moved is
undetermined and cannot be settled by this image. That is the highest-value
thing the next image could carry: `verify <n> <offset>`, or a per-sector digest
list.

🔴 **Attribution is not established and this seating cannot narrow it.** The
change happened somewhere between 2026-08-16 and 00:15 tonight. It was not
tonight: the loader went straight to this image on all ten boots, the vendor
firmware did not execute, `n_writes` read 0 in every dump, and no `FLW`/`EW`/
`EB`/burn command was issued. The vendor firmware **has** run on this part since
the dump (seating 8, ~2 minutes), and `[0x9000,0xA000)` is where a vendor
firmware saves configuration — **but that is a hypothesis with a mechanism, not
a measurement, and it is written here as one.**

⚠️ **This does not make the forbidden sentence sayable, and it moves it in the
harder direction.** *"Not one flash byte is written"* was previously unmeasured;
it is now **known to be false for the device** over some interval, with the write
unattributed. What is measured is narrower and better: **rlxfw's own driver
counted zero writes, and the loader region is intact over all 24,576 bytes.**

---

## 4. 🔴 Five defects of mine. Four cost a false stop; none cost a power cycle

Seven of the card's nine pre-power defects were found by running tools. All five
of these were found by running tools too — and **four of them are one root cause
appearing four times**, which is the useful part.

### 4.1 `RUNSHEET` `P3`'s NIC half was skipped

The pre-power check has two parts. The serial part ran (a 3-second board-off
capture: port opens, 0 bytes, the tool names three causes). The NIC part did
not, so `enxfc19286184c9` was **DOWN with no address** and `looprun` `S6` spent a
12-second TFTP timeout and reported `STOPPED at S6 -- exit 1`.

🔴 **`LOG.md` has recorded since seating 12 that `10.1.1.2/24` does not survive a
re-attach.** The NIC was attached fresh at 23:45. The fact lived in a log entry,
where nothing enforces it.

🔴 **And `looprun` cannot catch this**: `DEFAULT_HOST = "10.1.1.1"` is a
constant and nothing in the tool checks host-side reachability before `S6`. Every
gate it has points at the **board** — the burn flag, the staged head. None points
at the **host**, and a host fault is reported in the board's vocabulary.

🟢 The instrument that settles it is **ARP, not ICMP**: the loader answers ARP
(`10.1.1.1 lladdr 56:0a:01:01:01:e8 REACHABLE`) and does not answer ping. A
`ping` reporting 100 % loss here is a **pass**.

### 4.2 A failed `looprun` cannot be retried

The retry died at `S5b` in **0.06 s** — too fast to have reached the board.
`console-capture.py:368` refuses to overwrite an existing capture, correctly, and
`C1-ab2` was still there from the first attempt.

🔴 **At a bench the natural response to that is `--force`, which destroys the
evidence the guard exists to protect.** `looprun`'s stage artefacts should be
attempt-numbered. Here the capture was moved to `C1-ab2-att1` instead.

⚠️ **And the two tools in that pipeline disagree**: `console-dump.py` (`S5`)
silently rewrote `C1-rescue.json` while `console-capture.py` (`S5b`) refused.
Nothing declares which is intended.

### 4.3 Gating on a MARK instead of a FIELD

`C1-TW`'s gate looked for the contiguous string `S-TRYW=00000001`. What reached
the log was:

```
echo trywrite > /proc/rtl819x-spi ; cat /proc/rtlR8L19XxF-sWp-iS-
TRYW=00000001
```

The kernel's `rlxfw_mark()` output and busybox ash's echo of the typed line are
written to the console **concurrently and interleave character by character** —
`RLXFW-S-` and `819x-spi` woven together — so the mark's head is shredded and its
tail lands on the next line. **The board printed the mark; the grep could not see
it.** This is `FW-41`'s family (*a mark the board printed can be absent from a
grep*) by a new mechanism.

🔴 **The card's §4.3a already contained the fix and did not draw it**: marks come
from `write_proc` and fields from `read_proc`. The operational consequence is
that the mark is emitted **during** the echo and collides with it, while the
fields are emitted **after** and arrive clean. **Gate on fields.**

### 4.4 🔴 CRLF — one cause, three false gates, and the print disagreed with the test

Every capture line ends `\r\n`. `awk`'s `$2` is therefore `1\r`, and
`[ "1\r" = "1" ]` is false. Three gates fired wrongly on cells that had **passed**:

* `C1-WD` reported VOID while printing `n_state_bad = 1`;
* `C1-PR` printed its before/after and then failed the arithmetic silently;
* `C1-V4` reported STOP while printing `cmp_equal=1`.

🔴 **The worst part is not the bug, it is that the diagnostic looked right.** A
carriage return is invisible in display, so every one of those lines *printed the
correct value* while the comparison next to it saw a different string. Measured
with `od -c`: `1 \r \n`.

🟢 The replacement strips it and **self-tests against captures already on disk
whose answers are known, refusing to open the port if the comparison is broken** —
eight checks including two negative controls (an absent key must return empty;
arithmetic on two fields must work).

⚠️ A fifth, milder instance: `C1-NF`'s gate required `d1_match 1`, which cannot
hold while §3 stands. That one is the card's expectation, not only mine.

### 4.5 🟢 Two negatives about this image, and both are cheap to act on

* **`busybox` here has neither `dd` nor `md5sum`** (`applet not found`, three
  cells), so `/dev/mtd2ro` cannot be digested from userspace. **The driver's
  internal sha256 has no independent on-board second source on this image.**
  Every check of it in §3.2 is a desk check against the dump.
* **`busybox --list` is also absent**, so the applet set cannot be enumerated on
  the device. `wc` works, `dd`/`md5sum`/`--list` do not; future cards should not
  guess.

---

## 5. What this block did not establish

* Nothing above `0xA000` is compared — §3.4.
* The change at `[0x9000,0xA000)` is not attributed and its **content** is not
  read; with no `dd` on the device and no offset in `verify`, this image cannot
  read those 4,096 bytes on their own.
* `d1_match` has no positive control here — §3.2.
* `D2` is untouched: `H601`'s 8,192 bytes are skipped by rule and their
  verification stays in the `FLR` bracket, which did not run.
* The PIO rate is **not** re-measured. `C1-SZ`'s sidecar puts about 3.94 s
  between the echo and the answer against `FW-34`'s 4.2–4.6 s for the read
  alone, which would make the Linux path *faster* than the model — but `FW-35`
  exists because one read of latency was once turned into a 0.67 s finding here,
  and a `.timing` row cannot separate *data arrived* from *the tool began
  waiting*. It is recorded as a bounded question. The experiment that settles it
  is in-kernel: the driver can timestamp its own traversal against the 100 Hz
  clockevent and take serial timing out of the path entirely.

---

## 6. Carried forward

1. **`verify <n> <offset>`**, or a per-sector digest list, in `rtl819x-spi` 1.1.
   Without it the flash comparison can only ever find its first difference.
2. **An on-device digest path**: this image's busybox cannot hash a byte.
3. **`looprun` 1.1**: a host-side precondition before `S6` (ARP, not ping), and
   attempt-numbered stage artefacts so a failed run can be retried without
   `--force`.
4. **The `started_wallclock` checker** rule 3's ⚠️ names — see the card's §0.
5. **Gate on fields, strip `\r`** — a shared helper rather than a habit, so the
   next card's gates cannot repeat §4.3 and §4.4.
