# `K1`'s extra cells — written 2026-09-06 14:35, before any of them ran

The card (`PREDICTIONS-B12-block11.md`) is frozen at commit `e0c0508`. `K1`
came out `TA7=FFFFFFC2` (`-ETIME`), which the card's §6 stop condition 4 calls
*the guard doing its job*, so the cells below are **not** on it. They are
written here first, with their refutation conditions, because a cell whose
prediction is written after the reading is not a prediction.

## What `K1` measured, and it is the reason these exist

`ce_check_dj=585`, `ce_check_dc=574` — over the 5.85 s from `reqirq`
(`arch_initcall`) to the pre-check (`late_initcall`), TC1 delivered **574** of
the **585** interrupts a 100 Hz source owes. **11 short, 1.88 %**, against a
1 % tolerance. That span is exactly the vendor's NIC driver initialisation
(`Realtek WLAN driver` … `Realtek FastPath:v1.03`).

**Hypothesis, 推**: the loss is confined to that phase, and the steady state
after userspace exists loses nothing — which is what seating 13 measured
(258.53 s, `Δjiffies` = `Δirq_count` = 25,853, three ways) but only *after* a
handover, where the equality is partly by construction.

## The cells, and what would refute each

| cell | typed | prediction, written first | 🔴 refuted by |
|---|---|---|---|
| **`K1-Q`** | `sleep 10 ; cat /proc/rtl819x-timer ; cat /proc/interrupts` | **`\|Δjiffies − Δirq_count\| ≤ 2`** over ~1,000 jiffies, i.e. the loss has STOPPED. This is the strongest form available: the tick is still the vendor's, so `Δjiffies` and `Δirq_count` are two independent sources | a difference near **19** (1.88 % of 1,000) → the loss is ongoing and the hypothesis is wrong; the pre-check would then be refusing a real defect rather than a boot-phase artefact |
| **`K1-R`** | `echo cevtprobe > /proc/rtl819x-timer ; cat /proc/rtl819x-timer` | `last_verdict=0` and `ce_probe_registered=1` with **`ce_probe_mode_calls=0`** — the rating-99 negative control, which `TA7` could not reach. Arithmetic: the pre-check needs `11×1000 ≤ dj×10`, i.e. **`dj ≥ 1100`**; `dj` was 585 at `TA7` and ~1,585 by now | `-ETIME` again → `dc` fell further behind during the 10 s, which `K1-Q` will already have said |
| **`K1-S`** | `echo cevt > /proc/rtl819x-timer ; cat /proc/rtl819x-timer` | 🔴 **THE HANDOVER**, from `/proc` on a boot whose boot-time attempt was refused: `ce_registered=1`, `ce_mode=2`, `ce_mode_calls=2`, `ce_live=1`, **`ce_handler=80036FC4`** (was `80036D50`), `ce_handler_is_noop=0` | `-ETIME` → same as above. No output at all → wedged; power-cycle |
| **`K1-T`** | `sleep 10 ; cat /proc/rtl819x-timer ; cat /proc/interrupts` | alive, line 25 rising, `irq_stuck=0`, `ce_hw_bad=0`, and `Δjiffies` = `Δirq_count` = `Δce_cycles ÷ 2000` | silence → wedged after the handover |
| **`K1-D`** | `echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer` | `last_verdict=-16` (`-EBUSY`). ⚠️ **The card's `K1-D` row could not run as written** — its precondition is a registered clockevent, and `TA7`'s refusal meant there was none. `K1-S` establishes it | `last_verdict=0` → `disarm` ran under a registered device. **The one cell whose success is the bad outcome** |

## Why this is worth the cells

If `K1-Q` holds, the fix for the image is small and it is **measured rather
than guessed**: the pre-check's window must be taken in the state the tick will
run in, not across a driver initialisation. The late half re-bases
`ce_base_j`/`ce_base_irq` and waits `MIN_J` there, and the boot-phase counts
become their own reading on every boot instead of a failure.

If `K1-Q` is refuted, the fix is not that, and the seating has learned
something more expensive.
