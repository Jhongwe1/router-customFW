# Corrections to `PREDICTIONS-B24-block23.md`, written before each is executed

The card is frozen. `tools/check-predictions.py` reads its mtime as evidence
that the predictions preceded the captures, so the card is **not edited** —
every departure from it is written here first, with what was run instead and
why, and with the alternatives that were rejected.

---

## 0. `LOOP` is missing `--work` and `--label`, and the tool refused before it touched the board

**Written at 03:14, before the corrected form was run.**

§ 8.1's `LOOP` row is

```
/usr/bin/python3 tools/looprun.py --mode bench --cell p11d --out-dir bench/2026-09-17 --port /dev/ttyUSB0 --host 10.1.1.1 --skip S2 --recipe-override 7974982c --cell-top /home/key/fwre-work/rebuild/r3-4/cells/p11d/top
```

量, run exactly as written:

```
looprun: no --work: S3 would be handed the literal '<rtkimage work dir>', which
is a legal directory name -- so rtkimage would CREATE it, in whatever directory
this was run from. A default that succeeds in the wrong place is worse than one
that fails
```

🟢 **The refusal is the tool working, and it cost nothing**: it is raised before
any stage runs, so the board was not reset, nothing was uploaded and no capture
was taken. The card's row came from a `--mode plan` printout in which `S3`'s
`--work` renders as the placeholder `<rtkimage work dir>` — **a plan line is a
description, not a command**, and copying one as if it were a command is what
put a placeholder on a frozen card.

### What is run instead

```
/usr/bin/python3 tools/looprun.py --mode bench --cell p11d --out-dir bench/2026-09-17 --port /dev/ttyUSB0 --host 10.1.1.1 --skip S2 --recipe-override 7974982c --cell-top /home/key/fwre-work/rebuild/r3-4/cells/p11d/top --work /home/key/fwre-work/rebuild/bench-only/p11d-work-20260917 --label p11d-20260917
```

Two arguments added, nothing else changed. Confirmed complete with `--mode plan`
**before** the bench form was run: `S3` now renders a real path and `S6` sends
`<work>/<label>/kroot/rtkload/nfjrom`.

* `bench-only/` because the assembled image is a build product of this unit's
  own vendor tree and is not committed.
* The label carries the date so a second attempt on another day cannot land in
  the same tree.

### Rejected

1. **Edit the card.** Refused: `check-predictions` reads the card's mtime, and
   its own docstring says fixing even a typo has to make the check fail. The
   whole point of a frozen card is that it cannot be made right afterwards.
2. **Skip `S3` too and pass `--image` by hand.** Refused: `S3` has never run for
   `p11d`, so there is no image to name, and `--skip S2,S3` with a hand-typed
   `--image` is the shape seating 22's audit found had never been connected to
   `S2` at all.
3. **Let `rtkimage` create `<rtkimage work dir>` and move on.** Refused for the
   reason the tool gives: it would succeed, in the repository root, and a
   directory named after a placeholder is the kind of artefact nobody deletes.

### Effect on the fence

**None.** `LOOP` is not in § 9's `cells` fence — § 9 says so — so `14 of 14`
still means *every cell this card types*, and this correction does not touch any
of the fourteen.

---

## 1. `S3`'s output path is not carried to `S6` either, so the image is pinned by hand — and by sha256

**Written at 03:18, before the corrected form was run.**

With `--work` and `--label` supplied, `looprun` refused a second time, again
before any stage ran:

```
looprun: no --image: S6/S6b consume it and its default is the empty string, so
`loader-tftp.py put --image ''` would be reached with S4, S5 and S5b of a power
cycle already spent. S3 writes <work>/<label>/kroot/rtkload/nfjrom and nothing
carries that path here
```

🔴 **That last clause is a finding about the tool, not about this card.**
Seating 22's audit recorded that *`S3` had never been connected to `S2` at all*.
This is the wider version of the same gap: **`S3`'s product is not connected to
`S6` either.** Running `S3` inside the chain therefore buys nothing that running
it separately does not, and it costs the operator the ability to see the image
before it is uploaded.

### What is run instead

`S3` is run standalone first, at the desk, with the board untouched:

```
/usr/bin/python3 tools/rtkimage.py build --cell /home/key/fwre-work/rebuild/r3-4/cells/p11d/top --vmlinux /home/key/fwre-work/rebuild/r3-4/cells/p11d/top/linux-2.6.30/vmlinux --label p11d-20260917 --work /home/key/fwre-work/rebuild/bench-only/p11d-work-20260917
```

量, `rc=0`: `nfjrom` **1,071,104** bytes, sha256
`cb0fdd20edb4156a2a7a18324181b493a7848c58340a74a928c7b38035cd964e`.

Then the chain, with `S3` skipped and the image **pinned by digest**:

```
/usr/bin/python3 tools/looprun.py --mode bench --cell p11d --out-dir bench/2026-09-17 --port /dev/ttyUSB0 --host 10.1.1.1 --skip S2,S3 --recipe-override 7974982c --image /home/key/fwre-work/rebuild/bench-only/p11d-work-20260917/p11d-20260917/kroot/rtkload/nfjrom --image-sha256 cb0fdd20edb4156a2a7a18324181b493a7848c58340a74a928c7b38035cd964e
```

🟢 **This is stronger than the card's form, not weaker.** `--image-sha256` is
the argument whose own help says `RLXFW-ID0` is a digest over `config/` only and
*cannot tell two images built from one frozen `config/` apart; this can*. The
card's `LOOP` row, had it worked, would have uploaded an image nothing pinned.

### Rejected

1. **Pass `--image` with the path `S3` is about to create.** Refused: it would
   make the run depend on a file appearing between two stages, and if `S3`
   failed the chain would reach `S6` with a stale image from an earlier build
   still at that path — which is exactly the confusion `--image-sha256` exists
   to prevent.
2. **Edit `looprun` to carry `S3`'s path into `S6`.** It is the right fix and it
   is **not** made tonight: changing the instrument in the middle of the seating
   it is instrumenting is how a green becomes unreadable. Carried forward.

### Effect on the fence

**None**, for § 0's reason.

---

## 2. `MT-TICK` failed on a good unit, and the two causes are both properties of this shell that no fixture can show

**Written at 03:03, after the failure was diagnosed and before the corrected
image was uploaded.** The card's § 5 predicted `9 of 9 ok`. `C1-AUTO`
(02:51:48) returned **`8 of 9 ok, 1 FAIL`**:

```
  FAIL  MT-TICK   ce_live=11 ce_mode=(absent) spur=(absent) stuck=(absent)
                  reload=-1 want=-2 dj=-429433734 di=70 skew=429433804
```

**The board is not at fault.** A `cat` of the same file 59 seconds later
(`X1-timer`, off-card) shows all **101** fields intact, with `ce_live=1`,
`ce_mode=2`, `ce_reload=2000`, `ce_reload_hz=2000`, `irq_spurious=0`,
`irq_stuck=0`. The tick is healthy; the *reader* is broken, in two independent
ways.

### 2a. A `read_proc` file re-renders under the shell's byte-at-a-time reader

`X2-fieldrepeat` (02:54:05), three passes of the same `while read` loop over
the live file, looking for `ce_live`:

```
[ce_live==1]        <- ONE doubled `=`
(nothing)
(nothing)
```

`read` consumes one byte per syscall so as not to over-read a pipe; a 2.6.30
`read_proc_t` re-renders its whole page on **every** read and the kernel hands
back one byte of the fresh render. `/proc/rtl819x-timer` carries several
free-running counters, so a field that grows one character between two
byte-reads shifts everything after it and a character already consumed is
served **again** — the doubled `=`. A field that shrinks skips one, and the
`case` pattern then misses the line entirely. That is all three passes
explained, and it is why every field after `ce_live` read `(absent)`.

🟢 **The fix was measured on the die before it was built in.** `X4-snap`
(02:56:28), same shell, same loop, same fields, over a `cat` snapshot:

```
[ce_reload=2000] [ce_reload_hz=2000] [ce_reload_writes=0] [ce_reload_exact=1]
[ce_rating=300] [ce_rating_probe=99] [ce_rating_vendor=100] [ce_registered=1]
[ce_live=1] [ce_mode=2] [ce_mode_calls=2]
```

Eleven of eleven, clean. `cat` reads in whole blocks, so one render answers the
whole file.

### 2b. Parsing saturates at `INT32_MAX` while arithmetic wraps

`X3-arith` (02:55:06), on the die:

| expression | result |
|---|---|
| `$((4294950451))` | **2147483647** — parsing saturates |
| `$((4294950451-4294950000))` | **0** — both operands saturate, the difference is lost |
| `$((2147483647+1))` | **-2147483648** — arithmetic wraps |

Two different behaviours in one shell. This kernel's `jiffies` starts at
`INITIAL_JIFFIES`; the board printed `jiffies=4294950451` at 131 s of uptime,
so **every jiffies reading this project has ever taken is past the saturation
point** and `$(( j1 - j0 ))` is `0` whatever really happened.

🟢 The same saturation was measured **at the desk hours earlier**, under
`qemu-mips-static` with this unit's own busybox, while fixing `MT-ID` — and it
predicted the die exactly. It was not looked for in a second place, which is
why it reached the board.

### What changed

`config/mfgtest.sh` gains `snap()` and `jdelta()`. `mt_tick`, `mt_led` and
`mt_button` — the three checks that compare a counter across time — read from a
snapshot; `jdelta` reduces both operands to their last six digits, zero-padded
and prefixed with `1` so that a leading zero cannot make `$(( ))` read octal
and neither operand can reach the saturation point. Verified on the target
shell: `4294950451 → 4294950951` gives **500**, `999999 → 1000005` gives **6**,
and the octal case gives **1**.

⚠️ **The other eight checks are deliberately left alone.** In the very capture
that caught this, they read `/proc/rtl819x-spi`, `/proc/rtl819x-wdt` and the
vendor's `port_status` **correctly**, because those files' fields are static
between verbs. The hazard is latent for them; fixing what is not measured broken
at 03:00 is how a new defect gets in. Carried forward.

### The image, and every cell's argument

| | card | run |
|---|---|---|
| cell | `p11d` | **`p11e`** |
| `RECIPE_ID` | `7974982c` | **`bb684eb0`** |
| board prints | `RLXFW-ID0=7974982C` | **`RLXFW-ID0=BB684EB0`** |
| `vmlinux` | 4,170,754 | **4,174,850**, sha256 `f3d274592a63367a…` |
| boot capture | 1,637 | **1,637** — re-derived, unchanged |

**Every cell that types `7974982c` is run with `bb684eb0` instead, and nothing
else about any cell changes.** The fence is unaffected: the fourteen cell
*names* are identical, so `14 of 14` still means what § 9 says it means.

🔴 `C1-AUTO` is **re-run**, and its first capture is kept. A card whose
prediction was refuted, and the refutation, are both part of the record; the
second run is `C1-AUTO2`, declared off-card, and § 5's `9 of 9` is scored
against it.

### Rejected

1. **Widen `MFG_TICK_TOL` until the skew fits.** Refused outright: that is
   repairing the instrument to agree with the experiment, and `IRQ-13` is this
   project's own precedent for moving the window instead.
2. **Drop the reload term and keep the old `MT-TICK`.** Refused: the reload
   term was not what failed — it read `-1`/`-2` because the file could not be
   parsed at all, which the two sentinels correctly reported.
3. **Score `8 of 9` and carry `MT-TICK` forward.** Refused: `P1-3` is *the whole
   list passes on a good unit*, and a gate that reports success with a row it
   could not read is the failure mode this whole block exists to find.

---

## 3. `C4-BTN`'s window was tied to a conversation turn, and the operator cannot see this console

**Written at 03:35, while the replacement window was open.**

`C4-BTN` ran exactly as § 8.2 types it and returned

```
  FAIL  MT-BUTTON    n_open 0->1 (open) n_poll 0->400 (poller) b0_n_press 0->0 (press)
```

🟢 **The first two terms are the night's fix working on the die.** `n_poll`
moved by **exactly 400**, which is 20 Hz over the 20 s window, and
`j_last - j_first` is **1,995 jiffies = 19.95 s**. Before § 2.1's fix this
would have read `0->0` and MT-BUTTON would have failed with a perfect button.

🔴 **The third term did not move, and the driver says why.** Off-card read of
`/proc/rtl819x-keys` immediately after: **`b0_n_edge 0`**, **`n_ev 0`**,
`b0_raw 1`, `b0_state 0`. `n_edge` counts RAW pin transitions before any
debounce, so a 10 ms bounce would have registered. **Nothing touched GPIO 5
during those 400 polls**, and the poller was demonstrably running throughout.

So this is not the button and not the driver: the window and the operator were
not in the same 20 seconds.

### The cause is a protocol defect this project had already written down

The operator cannot see this console — `CLAUDE.md` § Environment — so the
`OPERATOR: press and hold …` line the script prints is never read at the moment
it is printed. § 3 ④ of the card says exactly that and the window was made 20 s
*because* of it. **20 s was not enough, because the window's START was still
tied to a conversation turn**: the operator answers, the answer is read, the
command is issued, and only then does the window open.

### What is run instead

`C4-BTN2`, off-card: `MFG_BUTTON_SECONDS=90`, `--seconds 130`, and the capture
is started **in the background** so the instruction to press reaches the
operator while the window is already open. The operator presses at a moment of
their own choosing and reports afterwards; nothing about the verdict depends on
when inside the window the press lands.

🔴 `C4-BTN`'s capture is **kept**. A prediction that was refuted, and the
refutation, are both part of the record.

### An unplanned instance of `M26`

⚠️ **`C4-BTN`'s line is, letter for letter, the reading § 6 predicts for
`M26`** — `n_open` and `n_poll` moving while `b0_n_press` stays flat. It is
**not** scored as `M26`: an injection is a thing that is done on purpose, and
an accident that produces the same reading is evidence about the prediction,
not an execution of it. `M26` is still run deliberately, and this capture is
cited beside it as an independent arrival at the same line.

### Rejected

1. **Score `C4-BTN` as `M26` and re-run only the positive.** Refused, above.
2. **Shorten the hold instead.** There is nothing to shorten: the pin never
   moved, so no hold of any length was seen.
3. **Raise `MFG_BUTTON_SECONDS`'s default from 20.** Not tonight — the default
   is compiled into an image the rest of this seating is running, and changing
   it costs a rebuild for a value the card can pass. Carried forward: the
   default should be the one a bench card actually uses.

---

## 4. Off-card work, declared

Four groups, all after the carded cells, none of them in the fence.

| cell | why it is off-card |
|---|---|
| `X6a-unlockoff`, `X6a-dat`, `X6b-lockon` | § 2 of the card gives `M25` in one direction only, and the operator's reading there is *lit* — the same word as `C3-LED`'s. These three run the guard in the OTHER direction so the operator's readings **differ**: off after `unlock`, still off under `lock` with the check asking for ON. A guard seen only refusing is a wall. |
| `C4-BTN2` | § 3. |
| `X8-M0` | The 32-group flash map, to bracket the seating. **Byte-identical to `bench/2026-09-09b` and `bench/2026-09-10`** — digest `ae87ac03269985d6` over all 32 lines. |
| `X10-rateA`, `X10-rateB`, `X10-slow-in`, `X10-slow-out`, `X11-final` | § 9.3's carried-forward item, measured instead of left as a guess — below. |

### 4.1 The independent rate reference works, and the numbers are exact

§ 2.4 records that `MT-TICK` catches a period programmed wrong and says nothing
about rate, and that the independent reference is the vendor's tick on
`/proc/interrupts` line 13. 量, same cell shape twice on one boot:

| | Δ line 13 (vendor) | Δ line 25 (mine) | ratio |
|---|---|---|---|
| normal | **503** | **503** | **1.000** |
| `cereload 20000` | **5,009** | **501** | **9.998** |

🟢 **`Δ mine` is ~500 in both.** The kernel's own view of elapsed time is
identical whether the clock is right or ten times slow, which is exactly why
an internal comparison cannot see the fault — and the vendor's line 13 is the
only counter in the system that noticed.

🟢 It also reconciles a number that was already on disk: at the end of the
seating line 13 minus line 25 read **6,058**, where seating 14 measured that
difference at **34**. `C10-M28` ran 66.78 s with the clock at a tenth, losing
`66.78 × 90 ≈ 6,010` ticks; `6,010 + 34 = 6,044`, against 6,058 — **14 ticks
apart**, and the extra is the `echo cereload` cell either side.

⚠️ **The scope limit, stated rather than found later**: line 13's own rate comes
from the same timer block, set by `TC0DATA` and `CDBR`. It is independent of
**this driver's clockevent reload** and **not** independent of the SoC's
divider — a real clock drift would move both. What it buys is a check that
`cereload`, and anything else that reprograms TC1 alone, cannot fool.

### 4.2 A cell of mine walked into the trap the card's § 4 names

`X10-rateA`'s first run carried `--idle 4` against a payload whose own `sleep`
is 5 s. It stopped at **4.28 s**, before the second half of its own output —
which is § 4's *"No `--idle` shorter than a cell's own `sleep`"*, on an
off-card cell, written by the same person who wrote the rule an hour earlier.
Re-run with `--seconds` only. **The rule is in the card and the card is not a
place a command looks.**

### 4.3 The unit was left clean

`X11-final`, after every injection and every revert: **`9 of 9 ok, 0 FAIL`**,
`MT-TICK ce_live=1 ce_mode=2 reload=2000=2000 dj=525 di=525 skew=0`.
