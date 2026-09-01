# PREDICTIONS — Session B8, `R4-3`, block 7: the loop tool's first run on the silicon, `ESC-1`'s finer grid, and `CARD-1` repaired in the card's own shape

**Written at the desk on 2026-09-02, twenty-fifth segment, before power.**
Every number below was re-derived on this host tonight from a file already
committed or an image already staged. Nothing here is conditional on a reading
taken at the bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in
`CORRECTIONS-block7.md`, beside this one.

**One power cycle.** Cells are `LP-*` — a stem no directory under `bench/` uses,
and not `Y` or `N`, which are the literal characters typed at the `FLR`
confirmation prompt.

---

## 0. The one structural change: every row states the STATE it assumes

`CARD-1`, 量 2026-09-01 **on the device**: block 5's `Y-ab` predicted
`AUTOBURN` = `00000000` and aborted on anything else. The board answered
`00000001`, which is the **power-on default** (`REG-23`, `RUNSHEET` `B6`, both
量). Every `00000000` this repository holds was read *after* a rescue sent
`AUTOBURN 0` — a step block 5 does not have. The expectation had been copied
from a card that had that step. Block 6 repeated the defect the same evening.

`cardcheck commands` asks whether a command is *invocable*; `cardcheck numbers`
asks whether a number *re-derives*. **Neither asks whether a cell's expectation
belongs to the state the card is in when it runs**, and no tool here does.

So this card carries a **precondition** column, and it is not decoration:
`LP-ab` and `LP-ab2` are the **same command** with **different expectations**,
and the only thing that distinguishes them is the precondition. If a reader
cannot tell those two rows apart by their precondition, the column has failed
and this card is worse than block 5.

⚠️ **This is a convention, not an enforcer.** `cardcheck` cannot read it. Making
the column machine-checkable needs a state model the project does not have, and
inventing one in the hour before power is how block 5 happened.

---

## 1. What this block is for, and the three questions it answers

**① `R4-3`'s `D3` on real silicon.** `tools/looprun.py` runs the whole
iteration and asserts that **the board printed the id the build computed**.
`rlxfw-kbuild.sh` derives `RLXFW_SRC_ID` as a sha256 over `config/`; `ID0`
prints it as eight **upper-case** hex digits. Tonight's build computed
`b1434383`, so the console must say `RLXFW-ID0=B1434383`. Nobody types that
value at the bench; it comes out of the driver's stdout.

**② `ESC-1`.** 量 2026-09-01: `boot-timeline`'s `entry` over 21 resets is
1.7–2.8 ms, mean 2.4 — but those captures ran `--esc-period 0.002`, whose
`drain()` pins the read cadence at a 2.088–2.126 ms median, so `entry` and one
read period are not separable. The chain resolves **0.216 ms** (pooled over
108,527 inter-read gaps). `--esc-period 0.0005` on two reset cells is the whole
experiment and it costs nothing extra.

**③ `CARD-1`**, above.

🔴 **This block runs no `FLR`.** So it adds **zero** bytes to the flash
bracket's coverage, which stands at 1,024 of 4,194,304 = **0.0244 %**, and the
forbidden sentence — *not one flash byte is written* — is exactly as unsayable
after this seating as before it. Said here so that a seating with no bracket is
a recorded decision rather than an omission.

---

## 2. Before power

| | |
|---|---|
| image | `$FWRE_WORK/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin`, **1,027,072** bytes, sha256-16 `3f58d559b24e2951` — **staged, 2026-09-02 04:49**, `rtkload`'s own `nfjrom` renamed |
| its source | `vmlinux` sha256-16 `c788348d7b7f9886`, cell `i3`, recipe `b1434383`, 4 host-compat patches, 16 mark rows, `.version` = 1 |
| `CAP` | `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0` |
| `OUT` | `--out bench/2026-09-02/` |
| pre-flight | a 3 s capture with the board **off**: 0 bytes, which separates the adapter, the port and the board before a power cycle is spent |

---

## 3. The cells

`bytes` is `tools/reply-size.py predict`'s number, re-derived tonight, not
copied.

| # | typed | **precondition** | expect | bytes | 🔴 stop if |
|---|---|---|---|---:|---|
| **`LP-A`** | `CAP OUT LP-A --esc 25 --esc-period 0.002 --idle 3 --seconds 45` | capture opened **before** power; board cold | `<RealTek>`; a single space where `C-8`'s watchdog line would be | — | no prompt → power off, that is the seating. Vendor boot text → the ESC window was missed; power-cycle and retry **once** |
| **`LP-ab`** | `CAP OUT LP-ab --send 'DW 8040D4A0 1' --idle 2 --seconds 6` | 🔴 **no rescue has run this power cycle** | **`00000001`** — the power-on default, `REG-23` | **71** | `00000000` here would mean something ran `AUTOBURN 0` before this card did, and nothing on this card has. Read it, do not proceed |
| **`LP-wd`** | `CAP OUT LP-wd --send 'DW B800311C 1' --idle 2 --seconds 6` | before any `J BFC00000` | `A5000000` — `WDTCNR`'s reset value | **71** | anything else → the loader touched the watchdog after all, which `CLK-11` says it does not |
| **`LP-e5`** 🆕 | `CAP OUT LP-e5 --send 'J BFC00000' --esc-after 10 --esc-period 0.0005 --idle 3 --seconds 25` | board at a prompt | echo, `Booting...`, then **`Reboot Result from Watchdog Timeout!`**, then `<RealTek>` | — | the discriminator absent → the reset did not happen. Nothing but the echo → **the board is wedged; power-cycle and do NOT repeat `J BFC00000`** |
| **`LP-e5b`** 🆕 | the same line, `--out LP-e5b` | as above | as above | — | as above. **n = 1 measures nothing**; this cell exists so `entry` has two readings at the finer grid |
| **`LP-0r`** | `/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-02/LP-rescue.json` | at `<RealTek>` after `LP-e5b` | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1`, in that order | — | any of the three absent |
| **`LP-ab2`** | `CAP OUT LP-ab2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6` | 🔴 **`LP-0r` HAS run** | **`00000000`** | **71** | ≠ → **STOP, upload nothing.** The next command is the only one on this card that could reach flash |
| **`LP-1`** | `/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image $FWRE_WORK/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin --filename rlxfw-lp --rescue-report bench/2026-09-02/LP-rescue.json --expect-load 80500000 --yes` | `LP-ab2` read `00000000` | **1,027,072** bytes accepted | — | any refusal → read it. **Never `--allow-autoexec`** |
| **`LP-2a`** | `CAP OUT LP-2a --send 'DW 80500000 8' --idle 2 --seconds 8` | after `LP-1` | `80500000: 00000000 00008021 40906000 00000000` · `80500010: 00000000 00000000 3C108060 2610AC00` | **118** | 🔴 the word at `0x8050001C` ≠ **`2610AC00`** → **not tonight's image.** `2610B400` is `quietmc`, and a watchdog reset re-stages `0x80500000` from flash, so the alternative here is a real image and not an empty address |
| **`LP-3`** 🟢 | `CAP OUT LP-3 --send 'J 80500000' --idle 8 --seconds 45` | `LP-2a` matched | eleven `RLXFW-B00`..`B10` in order, then 🔴 **`RLXFW-ID0=B1434383`**, then a shell prompt | — | `RLXFW-ID0=` absent → an image built before `ID0` existed. A **different** id → the tree moved between build and upload |
| **`LP-5b`** | `CAP OUT LP-5b --send 'cat /proc/version' --idle 3 --seconds 15` | at a shell | `(key@K)` and `#1 Tue Sep 1 00:00:00 UTC 2026` — the **declared** stamp | — | `admin@office.hopeiot` → the vendor's. A wall-clock-looking time → a `--no-stamp` build |

`--idle 8` on `LP-3` and not less: 量, the `quietm` boot log holds a **4.576 s**
silence at byte 350 of 849, so the `--idle 3` that the cold (1.644 s) and warm
(1.565 s) populations justify would cut it there and lose 497 bytes — looking
exactly like a boot that died.

---

## 4. What `looprun` does with the same cells, and why both are here

`tools/looprun.py --mode plan` renders `S4`–`S7` as the same four commands
`LP-e5`, `LP-0r`, `LP-1` and `LP-3` above, because the card's command column
and the runner's plan come from one list. Run it either way:

```
tools/looprun.py --mode bench --cell LP --out-dir bench/2026-09-02 \
    --skip S2,S3 --recipe-override b1434383 \
    --image $FWRE_WORK/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin \
    --iterations 1
```

🔴 **`--skip S2,S3` is deliberate and it is not laziness.** The image is
already staged and its sha256 is in §2; rebuilding it here would spend 40 s of
the scarcest resource this project has and would add a failure mode to a run
that is supposed to be unattended. `--skip S2` removes the only thing that
computes the recipe id, so the tool **refuses** unless `--recipe-override`
supplies it — otherwise `A3` would fail for a reason that looks exactly like a
stale image, which is the one thing that assertion exists to tell apart.
⚠️ **The card's own §3 rows are the fallback and they are complete**: the
hand-typed column runs the same four wire commands without the tool.

⚠️ **`--mode bench` has never run against a board.** Its assertions, its abort
conditions and its refusals have 23 controls behind them and every one of those
is synthetic. **If it misbehaves, the cells above are the fallback and they are
typed by hand** — that is why both are on this card and why the hand-typed
column is complete rather than a summary. A tool's first seating is not the
place to have only one way to get the reading.

---

## 5. Predictions, with refutation conditions

| id | prediction | refuted by |
|---|---|---|
| **`Q1`** | `LP-ab` reads `00000001` | `00000000`, which would mean the power-on default is not what `REG-23` says, or that something ran a rescue |
| **`Q2`** | `LP-ab2` reads `00000000` | anything else — and then nothing is uploaded |
| **`Q3`** | 🔴 `LP-3` prints `RLXFW-ID0=B1434383` | its absence, or any other eight digits. **This is the cell the whole loop tool exists for** |
| **`Q4`** | `boot-timeline`'s `entry` over `LP-e5`/`LP-e5b` is **below 2.8 ms** and its read cadence is **below 1 ms**, so the two are separable where they were not on 2026-09-01 | a cadence still ≥ 2 ms → `--esc-period` is not what sets it and `ESC-1`'s model is wrong |
| **`Q5`** | 猜, uncalibrated: `entry` lands in **1.0–2.6 ms**. The derived value is 2.184 ms and the 2026-09-01 bound is < 2.8 | nothing; it is a guess, recorded so a surprise is visible |
| **`Q6`** | `LP-wd` reads `A5000000` | 讀 `CLK-11` says the loader never writes `WDTCNR`; a different value refutes that reading, not this cell |
| **`Q7`** | the eleven boot marks appear in `LP-3` in declaration order | any out of order — which would be a finding about the boot ladder, not about the loop |

🔴 **`Q3` is the one that cannot be satisfied by accident.** The vendor's
firmware, a stale image of mine, and the loader's own re-staging of
`0x80500000` from flash after `LP-e5`'s reset all fail it, and they fail it for
the same reason: none of them was compiled from the `config/` this repository
holds tonight.

---

## 6. Abort conditions for the seating as a whole

* `LP-A` gives no prompt → power off. Nothing here is worth a second cold cycle.
* `LP-e5` gives only the echo → **the board is wedged.** Power-cycle once, and
  do **not** repeat `J BFC00000`. That outcome is the most valuable thing this
  card can produce and it is recorded, not retried.
* `LP-ab2` ≠ `00000000` → stop before `LP-1`.
* `LP-2a`'s head words wrong → stop before `LP-3`; a `J` into the wrong image
  is a power cycle spent on nothing.
* Any capture that opens **after** the board has started talking is void; re-take
  it rather than reading it. Seating 9's `Y-A` was lost to exactly that, 1.093 s
  late.

---

## 7. The machine-readable halves

`cardcheck numbers` re-derives every value below from the artefact named beside
it, rather than comparing it to a transcription. `check-predictions` uses the
cell list to prove each capture's mtime is later than this file's.

```cardnum
dw-1word	71	dwreply 1
dw-8words	118	dwreply 8
img-bytes	1027072	size /home/key/fwre-work/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin
img-sha16	3f58d559b24e2951	sha256-16 /home/key/fwre-work/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin
img-word-18	3C108060	word32 /home/key/fwre-work/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin 24
img-word-1C	2610AC00	word32 /home/key/fwre-work/rebuild/bench-only/lp-20260902/rlxfw-lp-20260902.bin 28
prev-img-word-1C	2610B400	word32 /home/key/fwre-work/rebuild/bench-only/b5-20260831/rlxfw-quietmc-20260830.bin 28
boot-bytes-x3	849	size bench/2026-08-31b/X-3.log
boot-sha16-x3	8317e7c9fe6eb60f	sha256-16 bench/2026-08-31b/X-3.log
```

⚠️ `prev-img-word-1C` is here so that `LP-2a`'s discriminator is a **contrast**
and not a lone value: `2610AC00` is tonight's image and `2610B400` is
`quietmc`, and both are re-derived from images on disk. A stop condition that
names only the value it wants cannot say what it would be seeing instead.

⚠️ `boot-*-x3` are last seating's boot, named here because `LP-3` is expected
to be **longer** than 849 bytes — this image carries a twelfth mark line that
`X-3`'s did not. A cell that predicted byte-identity would be wrong for a
reason the card can state in advance.

```cells
bench/2026-09-02/LP-A
bench/2026-09-02/LP-ab
bench/2026-09-02/LP-wd
bench/2026-09-02/LP-e5
bench/2026-09-02/LP-e5b
bench/2026-09-02/LP-ab2
bench/2026-09-02/LP-2a
bench/2026-09-02/LP-3
bench/2026-09-02/LP-5b
```

⚠️ `LP-0r` and `LP-1` are not in the cell list: neither produces a
`console-capture` `.log`/`.timing` pair. `LP-0r` writes `LP-rescue.json` and
`LP-1` writes a `-put.json`, and `check-predictions` reads captures. Naming
them here would make the sweep report two cells permanently absent, which is
the same noise as a missing capture and would train a reader to ignore it.
