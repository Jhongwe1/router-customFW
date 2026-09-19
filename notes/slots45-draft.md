# Slots 4 and 5 — the Linux half of a seating, ~~drafted but not carded~~ carded and run

**Written 2026-09-14, sixty-sixth segment, at the desk.** ~~This is a DRAFT, not a
card: nothing here has been frozen, no `cardcheck` has run over it, and no cell has
executed.~~ 🔄 **2026-09-14: frozen as `bench/2026-09-14c/PREDICTIONS-B21-block20.md`; 27 cells ran, `check-predictions` 27 of 27.** `PROGRESS.md`'s `BLKC-1` owns it.

It exists because the two residuals it covers need **no build** — they ride
`$FWRE_WORK/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin`, seating 20's
image — and because three things about them are **not precedent in this
repository**, which is the part worth writing down before it is forgotten.

---

## 0. What the two slots are

| slot | row | what it asks for |
|---|---|---|
| 4 | `SPEC.md:665` (`FW-65` 殘留), 🔄 **was `:625`, which is a different, already-closed row — the citation was measured before the commit that shipped it added three lines above it** | `/proc/gpio` is the **vendor's** user-writable path and `FW-65` only read the compiled code. Two questions: ① does `echo 1 > /proc/gpio` get seen by `rtl819x-gpio`'s `n_state_foreign` — which would be that detector's first **non-synthetic** positive control; ② is `AutoCfg_LED_Blink` (set by `echo 2`) consumed by the second bit-6 block inside `rtl_gpio_timer`, which only runs while the timer is alive |
| 5 | `SPEC.md:664` (`FW-63` 殘留), 🔄 **was `:624`, then `:627`, same cause both times — and this is the THIRD rot of this one citation, on 2026-09-19, when seven `NET-*` rows went in above it. The two citations in this table have now rotted five times between them for one reason: a line-number citation into `SPEC.md` is invalidated by any row inserted above it, and only `citecheck` can see it** | **is the steady-lit interval a constant 5.000 s?** The shape read out of the code is *dark `φ+1` s → lit 5.000 s → alternate every 1 s starting dark*, and seating 20's three low-fractions all fall inside its band — **but a fraction is an integral and has limited power to resolve a shape.** It needs an instrument that **timestamps every bit-6 transition**, and `FW-63`'s own instrument counts samples |

**Slot 4's ② and slot 5 both depend on `FW-62`**: the vendor's `rtl_gpio_timer`
acts **once per boot**, started by the first hold past ~2 s. So slot 4's two
`echo 2` arms bracket one long hold — before it the LED should blink, after it
the flag is set and nothing blinks — and **slot 5 needs its own fresh boot**,
reached by `busybox reboot -f` (`FW-37`, 2.407 s, no power cycle).

---

## 1. 🔴 THREE THINGS THAT ARE NOT PRECEDENT. Read these before writing a card.

### ① `/proc/uptime` has never been read on this device

量: zero hits across every committed capture. It is unconditional in the source
(`fs/proc/Makefile:19`, `proc-y += uptime.o`, no `#if`) and its format is
`"%lu.%02lu %lu.%02lu\n"` — **10 ms resolution** — but that is 讀, not 量.

**So it needs its own probe cell, running before anything depends on it.** If it
is absent, slot 5 falls back to the host's `.timing` file, which still measures
the *intervals* (a constant console-buffer delay cancels in differences) and
only loses the absolute `φ+1` offset. ⚠️ And `FW-35`'s rule applies to that
fallback: a byte's arrival is the **last** `.timing` row with `offset <= b`, not
the first with `offset >= b`.

### ② No `--send` in this project's history has ever contained a shell loop

🔴 **REFUTED 2026-09-14 (sixty-seventh segment). There are TEN**, on silicon:
`bench/2026-09-06c/X14-fast`, `X15-slow`, `X16-heldfast`, `X17-heldslow`,
`X23-after` and `bench/2026-09-09b/X2-relax`, `X3-relax`, `X4-relax`,
`X5-blink`, `X6-decay` — all `for i in <literal list>; do busybox grep …; done`,
four of them nested two deep, across two images and two seatings. 量 over 1,135
committed `.meta.json`. **So the construct needed no pre-flight at all**; what
is genuinely un-exercised is `while`/`until`/`$((…))`, and `cardcheck`'s `B9`
then refused those anyway. The struck claim, as written:

> ~~量: 0 of all committed `*.meta.json` `sent` fields contain `while`, `until` or
> `for`.~~ `while` / `[` / `$((…))` are POSIX and busybox ash has them — but that
> is **推** about *this* binary, and `tools/cardcheck.py:166 (this project has)`
> says in its own comment that this repository has never enumerated its builtin
> table. 🟢 **That half is now 量 too — `SPEC.md` `FW-66`.**

**Pre-flight it at the desk** with the instrument that produced `FW-25`, `FW-26`
and `FW-42`: `qemu-mips-static -L $FWRE_WORK/extracted/unit-2018/squashfs-root`
running that unit's own `bin/busybox ash -c '<the loop>'` against a fake `/proc`
file, wrapped in `tools/vendor-tripwire.sh`. **This is the one thing in the draft
that could produce nothing and cost a boot.**

### ③ `cardcheck commands` will report five issues per loop cell and exit 1

`argv0s()` (`tools/cardcheck.py:371-396`) has no notion of shell keywords, so
after each `;` it takes the next word as an `argv[0]`: `n=0`, `while`, `do`,
`n=$((n+1))` and `done` are all reported *NOT IN IMAGE*. The mechanism for that
is a ```` ```cardabsent ```` fence (`:389`, `:428-434`), which reports them as
intentional instead of swallowing them — **and the card must say they are ash
keywords and assignments, not applet names.**

🔴 **And it exposes a tool gap that must be recorded, not worked around**:
because `expect_cmd` is false after `do`, the `cat` **inside** the loop body is
never classified at all. **The one command the cell actually runs in a loop is
the one command `cardcheck` cannot see**, so the card must state that it was
checked by hand. `cardcheck.py:27` already says *"THE TOKENISER IS NOT A SHELL,
and the gap is stated rather than left to be found"* — this is that sentence
arriving.

⚠️ The loop-free alternative (`cat X ; cat X ; cat X ; cat X ; cat X`) gives
about five samples per cell, which **cannot resolve a 1.000 s alternation**. It
is not a substitute.

---

## 2. The image, as card predictions

| quantity | value |
|---|---|
| image | `$FWRE_WORK/rebuild/bench-only/r59-20260910/rlxfw-r59-20260910.bin`, 1,052,672 B |
| sha256 | `c890e0efeb6881ecb87473a737a139cd23c95c651dd942af59c7fe088019fcb5` |
| `RECIPE_ID` / `RLXFW-ID0` | `692a2801` / **`692A2801`** |
| boot capture | **1,637 bytes**, every boot, two sha256 classes whose whole difference is `RLXFW-G3` bit 6 |

`looprun` **can** drive this one — it is a kernel, not a self-resetting payload —
with `--skip S2,S3 --recipe-override 692a2801 --image <path> --image-sha256 <above>`.
That is `LOOP-4b`'s constraint satisfied rather than violated.

**At-rest `/proc/rtl819x-gpio` on a fresh r59 boot**, 量
`bench/2026-09-10/C11-P0.log`: `cnr FFFFFF8B` · `dir FF000040` · `dat 0000007C` ·
`cnr_as_spec 0` · `dir_as_spec 0` (**both 0 and that is correct** — the `EXPECT`
constants are loader-state, `REG-26`/`REG-27`, while Linux reads the other pair;
量 29 committed files, 35 occurrences, every one `0`) · `n_writes 2` ·
`n_state_chk 1` · `n_state_foreign 0` · `allow_out_mask 00000040`.

⚠️ `n_get 1 / n_state_chk 1` holds **only** with no keys read in front of it.
With `cat keys ; cat gpio` it is `3 / 3` — `FW-64`, one `cat` is two `read_proc`
invocations.

**One `cat /proc/rtl819x-gpio` is 574 bytes on the wire** = 0.1495 s at 38400.
That is the hard floor on any sampling loop's period, and it makes such a loop
**wire-bound**, which is why its duration is predictable.

---

## 3. What the drivers actually expose

**`/proc/rtl819x-gpio`** write verbs (`rtl819x-gpio.c:876-921`): `claim`,
`release`, `tryout <N>`, `unlock <N>`, `lock <N>`, `lock`, `probe04`, `sample`.
Anything else is `-EINVAL`. Read handler prints 37 fields ending in `val04`,
which is why `--until 'val04'` is safe on a gpio cell (it is the last `sprintf`
before `*eof`; seating 19 measured 16 bytes arriving after the match).

**The foreign detector** (`:399-413`) compares live `DAT` against `state_last`
**on bit 6 only**, and **no read ever updates the reference** — so once bit 6
diverges, every subsequent sample counts as foreign until this driver writes
again. Its own stated limit: *"IT SAMPLES. A write undone before the next sample
is invisible."*

**`/proc/rtl819x-keys`** write verbs (`:615-643`): `interval <N>` (10–60000 ms),
`clear`, `sample`, `irq`. Its read prints the 32-slot ring **last**, as
`ev <slot> <jiffies> <btn> <raw>` — which is why **`--until` is NOT safe on a
keys cell**: a match drains only 50 ms = 192 bytes against a full ring of ~800.

🔴 **Nothing in this image timestamps a bit-6 transition.** The ring records
**bit 5** (the button) only; the gpio driver has no ring, no timestamp and no
`jiffies` anywhere — only counts and a latched first value. **So the time base
must come from outside the driver**, which is what item ① above is about.

Three observables, in order of directness:
1. `dat` sampled repeatedly — carries **bit 5 and bit 6 in one word**, so press
   and LED share one clock with no bridging;
2. `Δn_state_foreign / Δn_state_chk` between consecutive samples — with the
   evdev node open at `interval 10` the detector samples bit 6 at 100 Hz, so each
   sample carries a 10 ms-resolution integral of the preceding interval. **This
   gives sub-sample resolution for free** and is an independent second route;
3. the host `.timing` file — third, independent, no board cost.

---

## 4. The predictions, written before any cell exists

Bit 6 = 1 is **dark**, = 0 is **lit** (`BRD-13`). `dat`: `0000007C`
released+dark · `0000003C` released+lit · `0000005C` pressed+dark · `0000001C`
pressed+lit.

**Slot 4**, with `t` = a fresh boot, no button touched:

| | expected | source |
|---|---|---|
| `echo 1 > /proc/gpio` then read | `dat` **`0000003C`** | `FW-65`, `DAT &= ~0x40` |
| same | `n_state_foreign` **+2** | `FW-64` (two `read_proc`) × the detector never updating its reference |
| same | `foreign_seen 1`, `foreign_first 0000003C` | `rtl819x-gpio.c:407-410` |
| `echo 2` **before** the long hold | **the LED blinks** | `FW-65` 殘留 ② |
| the long hold (≈8 s) | `/proc/load_default` → **`1`** | `FW-40`, ≥5 s branch |
| `echo 2` **after** it | **no blink, steady** | `FW-62`'s once-per-boot timer |
| throughout | `n_writes` still **`2`** | this driver writes nothing in slot 4 |

**Slot 5**, `t0` = the first sample with `btn_pressed 1`:

| # | prediction |
|---|---|
| 1 | first bit-6 `1→0` at **`t0 + φ + 1`**, `φ ∈ (0,1]` → 1.0–2.0 s after `t0` |
| 2 | bit 6 then stays **0 for exactly 5.000 s** |
| 3 | then alternation at **1.000 s** per level |
| 4 | the first level of that alternation is **HIGH (dark)** |
| 5 | after release, bit 6 latched **0**, held ≥ ~~152.1~~ 🔄 **139.251** s (`REG-37`) — 更正 2026-09-14 (第六十八段): 152.098 是那份擷取的 `duration_s`，含它自己 `--idle 8.0` 的尾巴；量到的閂住區間是 **139.251348 s**，舊值高報 9.2 %。`SPEC.md:331` 是擁有者。這一行被 `bench/2026-09-14c/CORRECTIONS-block20.md` § 0.4 逐字指名過而當時沒改 —— 那張卡已凍結不能動，**這份草稿沒有凍結** |
| 6 | the ring gives `(j_release − j_press)/100` ≈ the hold, `b0_n_release 1` |
| 7 | integral cross-check `Δforeign/Δchk` over the hold ≈ **0.58–0.61** (量 0.608 / 0.573 / 0.609 on three seating-20 holds) |

**Refutation, written first**

| id | if this happens | what it refutes |
|---|---|---|
| `R4-0` | `/proc/gpio` does not exist | `FW-65` is wrong about this image and **slot 4 is void** — record it, do not improvise a substitute |
| `R4-3` | **`n_state_foreign` does not move** on a real foreign write | the detector cannot see the thing it was built for. **The load-bearing one** |
| `R4-5` | the LED blinks **after** the hold | `FW-62`'s once-per-boot mechanism |
| `R4-6` | the hold gives `b0_n_release 0` or `load_default 0` | the timer was not consumed → the second arm tests nothing, **re-run the boot** |
| `R5-b` | the steady interval is **not 5.000 s** ± one sample period | the *constant 5.000 s* reading, and `FW-63`'s struck-through `T = 3.95/3.05/3.90` comes back |
| `R5-c` | the period is not 1.000 s, or it starts **low** | the counter-parity reading and `FW-40`'s 1 s `mod_timer` |
| `R5-d` | bit 6 never goes low in a ≥15 s hold | **VOID, not a refutation** — the timer was already consumed on this boot. Abandon it and re-run; precedent is seating 20's boot 16 → 17 |
| `R5-f` | the two routes (samples, `Δforeign/Δchk`) disagree | one of them is wrong. **Do not average them** |

---

## 5. The operator protocol, which is already written down

`config/rlxfw-src/.../rtl819x-keys.c:114-117`, in the driver itself:

> *The bench protocol for a button is a TIMED PHYSICAL ACTION — press, hold,
> release — and it cannot be timed by conversation turns. The instrument has to
> record its own timing, so every raw edge goes into a ring with the jiffies
> count at which it was seen and /proc prints the ring.*

Five parts, all precedented on seating 20:

1. the payload's `sleep N < /dev/input/event0` **is** the operator's window — the
   redirect opens evdev, which is what starts `input-polldev` polling;
2. the instruction is a `#--` comment directly above the command, imperative and
   upper-case, and it says that launch time does not matter;
3. `--seconds` alone. **No `--idle`** — `cardcheck`'s `A22` now refuses
   `--idle N` under a `sleep >= N`, and seating 20's card is exempted by name
   while a new one will not be;
4. the duration is recovered afterwards from the ring, not from a stopwatch;
5. 🔴 **a hold with `b0_n_release 0` gives no duration** — the operator was still
   holding when the window closed. Seating 20's `C13-H10` is the precedent.

⚠️ **The owner has agreed to take the button**: the window is opened long, the
operator says "start" and times the hold themselves, and the instrument records
the sequence. `PROGRESS.md`'s `BLKC-1` carries that agreement.
