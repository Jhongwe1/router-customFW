# Block 11 — corrections, and what the card got right

`PREDICTIONS-B12-block11.md` was frozen at commit `e0c0508`, 14:25, before the
board was powered. This file is everything the seating did differently and
everything the card said that the board then refuted. Neither list is edited
into the card; the card is the record of what was believed beforehand.

---

## 1. 🔴 The card was wrong about `busybox reboot`, and the reason is not a typo

§2.1 named `busybox reboot` as the decision cell and reasoned about two
outcomes: it reaches `<RealTek>`, or it does not. **Neither happened.** 量
`K1-Z`: the applet exists — there is no `applet not found` — it ran, the shell
prompt came straight back, and the next 4,500 bytes of the capture are `^G`
(BEL, 0x07), which is the shell beeping at every ESC the instrument was
sending. **The board did not reset and the shell was never gone.**

讀, and consistent with it: busybox's `reboot` signals PID 1 rather than
calling `reboot(2)`, and this image's PID 1 is `config/rlxfw-init.sh`, a shell
script that does not handle it. The vendor's rootfs runs busybox `init` there,
which does.

🟢 **`busybox reboot -f` works, and `-f` is exactly the flag that skips the
init hand-off.** 量 `K1-Z2`: the command echo, then `Booting...`, then
**`Reboot Result from Watchdog Timeout!`** — `C-8`'s discriminator, where a
cold boot prints a single space — then `<RealTek>`, 66 times. **2.407 s from
the command to the loader prompt**, measured from the capture's own `.timing`,
which is what let the remaining nine cells use `--esc-after 8 --seconds 12`
instead of the card's 20/35.

⚠️ **And it worked with this driver's clockevent driving the tick**, since
`K1` had been handed over from `/proc` by then. `machine_restart` on this part
does not depend on the vendor's timer.

**Consequence for the seating**: one power press for the whole session, and it
was the one the operator had already made. Nine of the ten DoD boots are warm.

---

## 2. 🔴 The image the card names refused its own handover, twice, identically

`K1` (cold) and `K2` (warm), image `0a3135af`, driver **4.0**:

```
RLXFW-TA7=FFFFFFC2        = -62 = -ETIME
ce_check_dj=585   ce_check_dc=574     boot_stage=7  boot_rc=-62  boot_done=0
```

Over the span from `reqirq` at `arch_initcall` to the pre-check at
`late_initcall` — which is exactly the vendor's NIC driver initialisation —
TC1 delivered **574** of the **585** interrupts a 100 Hz source owes. **Eleven
short, 1.88 %**, against the pre-check's 1 % tolerance.

🟢 **Every one of those fields was byte-identical on the cold boot and the warm
one**, including `tccnr_at_init`, `boot_ack_tries` and `boot_j_early`. The
shortfall is deterministic, not noise.

🟢 **The soft-failure path worked exactly as the card's §2.3 said it would**:
`TA8` and `TA9` were never printed, the board booted on the vendor's tick, and
`/proc` carried the reason. The card's stop condition 4 allows three
consecutive `-ETIME` before stopping; **two were enough**, because the second
was identical to the first to the interrupt and a third could not have added
anything.

### 1.1 The cell that settled it, and it cost nothing

`K1-Q` (off-card, prediction written first in `PREDICTIONS-K1-extra.md`):
over **14,385 jiffies at the shell**, `Δjiffies = 14,385` and
`Δirq_count = 14,384` — **one short, 0.0070 %**. 🔴 **The tick was still the
vendor's, so those are two independent sources and not one identity written
twice**, which is the weakness of every zero-lost-tick figure taken after a
handover.

And the arithmetic closes, over three independent reads and with the residual
stated rather than waved at. `/proc/interrupts` line 13 (the vendor's) against
line 25 (this driver's): **33** at `K1-Q`, **34** at `K1-T`, **34** at
`M10-L`. Three terms account for it — `TA0` says this driver's counter starts
at uptime **21** jiffies, the driver-init phase costs **10–11**, and the
steady state costs ~1 per 15,000 — so at `M10-L`, where uptime is 28,136
jiffies, the prediction is 21 + 10 + ~2 = **33** against a measured **34**.

🔴 **The steady-state term is not a fudge; it is measured twice.** `K1-Q`:
1 in 14,385 (0.0070 %). `K1-Q` → `K1-T`, the vendor's line advancing 16,464
against this driver's 16,463: 1 in 16,464 (0.0061 %). Both are comparisons
between two interrupt lines, so neither depends on which of them drives
`jiffies`.

---

## 3. What changed in the image, mid-seating

Driver **4.0 → 4.1**, `RECIPE_ID` **`0a3135af` → `ea6ee537`**, image
`rlxfw-r53b2-20260906.bin` (1,034,240 B, `23539da9…`) →
`rlxfw-r53b2b-20260906.bin` (1,033,216 B, `60bfddf5…`).

The late half now **re-bases** `ce_base_j`/`ce_base_irq` and takes the
pre-check window at `late_initcall`, where the system is quiet, and keeps the
driver-init span as a reading (`boot_pre_dj`, `boot_pre_dc`, and `TA6`, which
was the wait and is now the shortfall). Up to three windows; `boot_ce_tries`
says how many were used.

🔴 **The tolerance did not move.** Widening 1 % until the measurement passed
would have been fixing the instrument to agree with the experiment. What the
1 % refused was a state in which the system clock would have run 1.88 % slow
through boot with nothing in the kernel able to notice — which is precisely
what `R5-3b-1`'s `cereload` rows demonstrated is undetectable from inside.

**So the ten DoD boots are `M1`…`M10`, not `K1`…`K10`.** `K1` and `K2` are the
diagnostic pair and they are not DoD boots.

---

## 4. The `cells` fence over-declares, and that is left visible

The frozen card's fence names `K1-A`…`K10-L`, 24 cells. What ran is `K1-*`,
`K2-*` and `M1-*`…`M10-*`. **`check-predictions` will therefore report the
`K3`…`K10` cells as absent, and that is the correct output** — the card
predicted ten boots with an image that turned out to refuse its own handover,
and hiding the gap by editing a frozen card would be worse than the gap.

`K1-D`'s row could not run as written either: its precondition is a registered
clockevent, and `TA7`'s refusal meant there was none. It ran after the off-card
`K1-S` established one, and returned the `-16` the card predicted.

`K1-T` used `sleep 30` where the extras file said 10, to cross the 32-bit
`jiffies` wrap deliberately — `4294967069 → 4294973518` spans 2³².

---

## 5. 🟢 What the card predicted and the board confirmed

Written before power, checked afterwards against the captures:

| card | prediction | 量 |
|---|---|---|
| §5.3 | `Kn-boot.log` is **1,069 bytes** | **1,069**, on all ten `M` boots |
| §5.2 | `RLXFW-TA6=00000000` (4.0's meaning: the wait) | `TA6=00000000` on `K1` and `K2` |
| §5.2 | `TA5 − TA0` = **540…600** jiffies | `FFFF8D2E − FFFF8AE5` = **585** |
| §5.4 | `TA2` in **1…5** | **1**, every boot |
| §5.1 | **`TA8` occurs before `B10`** | true on all ten; byte 887 against 925 on `M1` |
| §5.6 | the vendor's NIC bring-up sits **between `TA4` and `TA5`** | exactly so, on every boot |
| §5.5 | `ce_probe_registered=1` with `ce_probe_mode_calls=0` | on all ten, at boot |
| §2.1 | 推 a watchdog reset clears `TCCNR`'s `TC1En` | `tccnr_at_init=C0000000` and `TA1=00000000` on the warm boots — two witnesses |
| §2.3 | an oops would print, control = the vendor's `panic_printk` lines | the `Realtek FastPath:v1.03` line present in **10 of 10** |
| §1.2 | `ce_handler` `80036D50` → `80036FC4` | on all ten |

**The one number the card got wrong before power was its own timing table, and
it was corrected before power** by a control that recomputed it with the other
anchor (`SPEC.md` `FW-35`).

---

## 6. 🔴 The frozen card was edited once, after the seating, and here is exactly what for

`spec-check`'s `C8` went red on it: three table headers in §4.1, §4.2 and §4.3
declared **one column more than their rows carry** — the `#` and `capture`
columns were merged in every row and not in any header. Eight rows were ragged.

That is not a cosmetic complaint. `C8`'s own message says why: an unescaped
`|` or a missing cell shifts every column after it, so a checker that reads a
field **by index** then reads the wrong cell and passes. The rows would also
render as a mangled table for a human.

**What was changed: the three headers, to match the rows.** No row text, no
prediction, no number, no expectation. `git diff e0c0508 -- <the card>` is the
evidence: **6 insertions, 6 deletions** — three headers and their three
separator rows, and nothing else.

⚠️ **The rule this bends is real and is stated rather than skipped**: a card is
frozen so that "the predictions were written first" stays checkable. The
alternative was leaving a red check in CI that everyone learns to ignore, which
this repository has written down as the worse failure. The seam is that the
edit is declared here, is confined to table syntax, and is one `git diff` away
from being confirmed.

🔴 **AND IT COST MORE THAN THAT, WHICH THE DECISION UNDER-WEIGHTED.**
`tools/check-predictions.py` decides "written first" by **mtime**: every
capture must be newer than the predictions file. Editing the card at 15:05
made it newer than the six `K1`/`K2` cells, which ran at 14:28–14:43. 量, the
actual output:

```
0 of 24 captures came after the prediction, 24 did not
```

**18 of those 24 are the fence over-declaring** (§ 4, `K3`…`K10` never ran).
**Six are the header fix**, and they read `capture is OLDER than the
prediction` rather than `no capture`.

🔴 **The mtime evidence is not recoverable and will not be faked.** `touch`-ing
the card back to 14:25 would make the checker pass by falsifying an artefact's
timestamp, which is the opposite of what the check is for. **What survives is
stronger anyway and is in git**: commit `e0c0508` froze the card at **14:25:56**
and every capture in this directory is timestamped 14:28 or later, which
`git log --format=%ad` and `stat` settle between them.

⚠️ **The lesson is not "never fix a frozen card".** It is that
`check-predictions` and `spec-check` disagree about what a frozen card is —
one wants it immutable in *time*, the other wants it correct in *syntax* — and
nothing in this repository had noticed. **Fix the table syntax before the
freeze**, which costs nothing: `spec-check` runs in two seconds and was not run
on the card before it was committed.

🟢 **And the same pass caught two defects of the same shape in `SPEC.md`'s new
rows, before they were committed**: `IRQ-13` wrote an absolute value as
`|574−585|`, whose two bars ARE column separators, and `REG-34` merged §9's
`位址` and `名稱` columns. Both were written this session; `C8` found them the
first time it ran.

---

## 8. 🟢 `M11`, the eleventh boot — a real power-on, and it is the control the other ten needed

`M1`…`M10` are all **warm** resets: the DoD's ten were driven by
`busybox reboot -f` from the host, and the seating's one power press was spent
on `K1`, back when the image was 4.0. **Ten warm boots is a weaker claim than
ten boots**, so an eleventh was taken as a cold power-on.

量: `M11-A` holds `Booting...` and **no** `Reboot Result from Watchdog
Timeout!` — `C-8`'s discriminator, so it is a power-on and not a reset. And
then:

**Every field is byte-identical to the ten warm boots.** All ten `RLXFW-TA`
lines, 1,069 bytes, `tccnr_at_init=C0000000`, `boot_pre_dj=584`,
`boot_pre_dc=574`, `ce_check_dj=300` / `dc=301`, `boot_ce_tries=1`,
`boot_wait_j=300`, `ce_mode=2`, `ce_mode_calls=2`, `ce_handler=80036FC4`,
`ce_probe_mode_calls=0`. Re-derived from the captures: **11 of 11** meet every
clause of the card's §2.2, and the oops channel was live in 11 of 11.

🟢 **So the warm/cold distinction does not reach any number this step
measures**, including the one that could most plausibly have differed — the
driver-init shortfall, which is **574 of 584 on the cold boot too**.

🟢 `M11-N`: `NET-25`'s reproduction condition — the first open of `eth4` after
power — on a boot whose tick was armed before userspace existed. **4/4, 0 %
loss**, RX 5 / TX 5. Third consecutive non-reproduction. Every RTT is exactly
**10.000 ms**, which is the quantisation of a 100 Hz clock, and that clock is
this driver's.

🟢 `M11-D`: `disarm` returns **-16** (`-EBUSY`) with `state=armed` and
`ce_live=1` — the one-way door, now entered from a **boot-time** registration
rather than a `/proc` one.
, and every one of the five is the checker being right

The card is frozen and describes image `0a3135af`, driver **4.0**. The tree
holds **4.1**. So five rows no longer re-derive, and they fall into two classes
that are worth separating because only one of them is recoverable:

| row | now | why |
|---|---|---|
| `vmlinux-bytes` / `vmlinux-sha16` | 3,976,241 / `b8248b3d…` | 🔴 **the artefact was destroyed.** The 4.1 build reused the cell name `r53b2`, so `out/r53b2.vmlinux.elf` and `r53b2.System.map` were overwritten. 4.0's ELF no longer exists anywhere |
| `drv-lines` / `proc-lines` / `boot-proc-lines` | 2,813 / 101 / 10 | the rows point at `config/rlxfw-src/…/rtl819x-timer.c`, which is a **live** file. They would have drifted on the next edit whatever it was |

🟢 **The image's own identity survived**: `img-bytes` and `img-sha16` still
re-derive, because the `.bin` lives in its own dated directory
(`bench-only/r53b2-20260906/`) and the 4.1 build wrote to
`bench-only/r53b2b-20260906/`. So `K1` and `K2` can still be tied to the exact
bytes that produced them; what is gone is the intermediate.

**Two rules follow, and they are for the next card rather than for this one:**

1. **One cell name per image.** `rlxfw-kbuild.sh` writes `out/<cell>.*`, so a
   second build with the same cell overwrites the first image's ELF, map,
   manifest and build log. A mid-seating rebuild is exactly when that matters
   and exactly when nobody is thinking about it.
2. **A frozen card's `cardnum` rows may only name frozen artefacts.** Pointing
   at a live source tree makes a row that must go red eventually, and a row
   that must go red eventually teaches the reader to skip the report.

⚠️ CI does not run `cardcheck numbers` over the corpus — it runs the self-test
and the mutation suite (`ci.yml`:423, :430) — so this is a fact about one card
and not a red build. **It is written down anyway**, because the reason it is
not a red build is a property of today's CI and not of the defect.
