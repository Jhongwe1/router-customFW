# CORRECTIONS — block 41, seating 38

Every departure from the frozen card, and every defect found in it. The card
itself is **not edited** — `check-predictions` reads its mtime, and repairing a
frozen card destroys the evidence that its predictions were written first.

---

## § 1 Two defects in the frozen card, both corrected at the bench

### 1.1 🔴 `C2-OFF` would have turned the engine off before the dose

The card reads:

    CAP --out bench/2026-09-22b/C2-OFF --send 'echo recover 0 > /proc/rtl819x-nic ; echo engine off > /proc/rtl819x-nic' ...

The intent of `C2-OFF` is stated in § 2.3: disable the stall detector so the
wedge is visible, with `recover 0` in **both** arms. The `engine off` is wrong
— with the DMA engine stopped, `C4-DOSE` cannot wedge anything and the whole
of Part C measures nothing.

**What ran instead**: `echo recover 0 > /proc/rtl819x-nic`, alone. Nothing else
on the card changed.

⚠️ **How it survived the freeze.** `cardcheck commands` passed 18 of 18 and
`cardcheck numbers` 11 of 11. Neither asks what a verb *does*: the first checks
that a command name is invocable, the second that a declared count re-derives.
A verb that is spelled correctly and does the wrong thing is outside both.

### 1.2 🔴 Both `NB blast` lines name options `netblast` does not have

The card reads `NB blast --host 10.1.1.3 --frames 347 --size 1400 --rate 43`.
量 `tools/netblast.py blast --help`: the options are `--target`, `--src`,
`--dev`, `--port`, `--rates`, `--step-s`, `--arp-load`, `--out`. There is no
`--host`, no `--frames`, no `--size`, and `--rate` is `--rates`.

**What ran instead**, identically in both arms:

    netblast.py blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 \
        --rates 43 --step-s 8 --arp-load --out bench/2026-09-22b/C<n>-DOSE.json

🔴 **And `--rates` is Mbit/s, not frames per second.** The card's § 2.3 called
for `NET-87`'s minimal reproduction — 347 frames at 43 frame/s. What ran was
**20,094 frames at 29.04 Mbit/s** (arm 1) and **20,391 frames at 29.36 Mbit/s**
(arm 4): about 58× the intended dose. The A/B is unharmed, because both arms
took the same dose and the comparison is between them — but it is **not**
`NET-87`'s minimal repro, and no claim here rests on it being one.

⚠️ `cardcheck commands` cannot catch this either, for the same reason as 1.1.
**That is the finding the two defects share, and it is about the checker rather
than about me**: nothing in this repository reads a card's *arguments*.

---

## § 2 Cells that ran on a different boot than the card places them

`B4-PH0`, `B5-IPERF0`, `B6-N`, `B7-PH1` and `C9-PING` were not reached on the
first boot: `B2-IPERF` wedged the board (`NET-67`) and the rest of Part B would
have measured a wedged path. They ran on the **third** boot, reached with
`busybox reboot -f` and a fresh `looprun` upload (`X20`), after `X21-SW` /
`X22-UP` / `X23-SRV` re-established the same starting state.

🔴 **What that costs, stated rather than left to be inferred**: `B2-IPERF`
(arm 1) and `B5-IPERF0` (arm 0) are **not** a same-boot A/B. Both are the first
`iperf3` after a clean boot with the same setup verbs, which is the closest
comparison available, and the claim that rests on them is not the throughput
figures — it is `n_ph_used` **136** against **0**, which is a property of the
code path and not of the boot.

`C9-PING` is placed after Part C on the card and ran after Part B on the third
boot. Its reading is `100 % loss`, and the dump taken immediately after
(`X24-FINAL`) says why: `n_tx_stop 1`, `tx_stopped 1` — an ordinary `NET-67`
wedge on a boot where `recov_mode` is 0 again. It is **not** the transient
silence of `NET-110`.

---

## § 3 The card's own discriminator for `B` was wrong

§ 2.2 wrote: *REFUTED BY anything in the 0.04–0.07 band, which is the arm-0
signature and would mean the compiled default did not take.*

量: `B2-IPERF`, with `phfollow` compiled to 1 and no verb typed, came out at
**0.06 Mbit/s** overall — inside that band — while `A4-BASE` read `ph_follow 1`
and `B3-N` read `n_ph_used` **136**. The control arm `B5-IPERF0` came out at
**0.04**. So the two arms are 1.5× apart on throughput and the band contains
both.

**A throughput band cannot separate *the fix is not in* from *the fix is in and
something else stopped the traffic*.** The counter on the fix's own branch can,
and it did. `SPEC.md` `NET-107`.

---

## § 4 One prediction refuted, with the residual closed

§ 2.4 predicted the boot capture at **7,717 bytes**. 量: **7,705**.

Both captures are 187 lines and their printk timestamps total **1,728 bytes on
each side**, so timing is not the cause. With timestamps stripped the only
content difference besides `RLXFW-ID0` is the vendor wlan driver printing
`tmpReg[0xe]` where `s99c` printed `tmpReg[0x2e]`: **exactly 12 occurrences,
1 byte each, 12 = 12, no residual.**

🔴 `tools/bootbytes.py`'s `K7` control already documents this field —
*"the varwidth normalisation is load-bearing: 16 capture(s) carry the field,
hex-digit widths {1: 16, 2: 176}; WITHOUT the normalisation they give
[6541, 6550, 6552, 6553], WITH it [6541]"*. The prediction was made by copying
`s99c`'s measured length instead of asking the tool, and the tool would have
said so.

---

## § 5 One loader behaviour that cost a `looprun` attempt

`looprun` attempt 1 stopped at `S4`: `J BFC00000` was answered
`Unknown command !` and the reset did not happen. The same eleven bytes
succeeded at seating 37 (`bench/2026-09-22/A0-rz.log`, byte-identical send).

量: that `J` was the **first command after an ESC-streaming capture was killed
with `TaskStop`**. One harmless `DW 8040D4A0 1` flushed it, and the identical
`J BFC00000` then reset the board normally (`---Jump to address=BFC00000`,
`Booting...`, `Reboot Result from Watchdog Timeout!`).

**Killing a capture mid-ESC-stream eats the next command.** Attempt 1's
artefacts are kept (`A0-rz.*`) rather than overwritten, which is what
`--attempt 2` is for.

---

## § 6 What is NOT a correction

* The burn-flag reading `00000001` at `X-probe1` is the **expected pre-rescue
  state**, not a fault. The card's stop condition is `00000001` *after* `S5`;
  `A0-att2-ab2` read `00000000` after the rescue and the seating proceeded.
* `X*` cells are off-card by declaration, not by omission. They are: the cold
  loader catch (`X0`), the recovery demonstration (`X1`, `X2`), the server
  restarts (`X4`, `X23`), the liveness and wire readings (`X6`, `X7`, `X11`),
  the engine-side reads (`X8b`, `X9`, `X10`), the third boot (`X20`–`X23`), and
  the two final dumps (`X12`, `X24`).
* `A0-att2-*` supersedes `A0-*` for the boot that carried the seating. Both are
  committed.
