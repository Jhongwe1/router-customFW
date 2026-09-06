# Block 12 — corrections, and what the card got right

`PREDICTIONS-B13-block12.md` was frozen at commit `9db2e75`, 20:04:15, before
the board was powered at about 20:07. This file is everything the seating did
differently and everything the card said that the board then refuted. Neither
list is edited into the card; the card is the record of what was believed
beforehand.

Ten boots, one power-on, three operator button actions. Zero flash-write
commands and zero `FLR`.

---

## 1. 🔴 The card's `cells` fence is malformed, and `0 of 5` was on screen before the board was powered

`check-predictions.py` documents its fence as **one capture prefix per line**,
and every other card in this repository writes one repo-relative path per line
(`bench/2026-09-06b/K1-A`, and so on). §4.4 of this card writes **bare names,
eight to a line, five lines**:

```
B1-A B1-P B1-T5 B1-T12 B1-TP B1-C B1-CP B1-U
```

The tool therefore looked for a file whose whole name was that line, did not
find one, and reported *no capture* — five times. **The output was
`0 of 5`.** The card's own §4.5 states, in prose, *"32 capture lines in §4.3,
32 cells in §4.4's fence, neither list holding an entry the other lacks"*.

🔴 **`0 of 5` and `0 of 32` are the same shape**, and `0 of N` is the correct
answer for a frozen card whose seating has not happened. The difference was
visible at the desk, it went into this segment's freezing-commit message as
evidence of a pass, and nobody subtracted. That is this project's own
*quoting a partial view* hazard, inside the check that exists to prevent it.

⚠️ **The fence is NOT repaired.** Editing the card now would move its mtime past
all 32 captures and turn every one of them into *capture is OLDER than the
prediction* — `RUNSHEET`'s card-lifecycle rule 1, which cost block 11 its
ordering evidence. **The ordering is in git instead**: `9db2e75`'s author date
is 20:04:15 and the earliest capture in this directory is 20:07.

🟢 **What changed is the instrument.** `tools/check-predictions.py` gained two
refusals and two controls, `N8` and `N9`: a fence entry may not contain
whitespace, and may not be a bare name with no directory separator. 量 over the
corpus before the rule was written — **54 cards have a usable fence, exactly one
breaks either rule, and it is this one**. `--sweep bench` now reports this card
as `unreadable` rather than counting five phantom absent cells.

🔴 **The obvious third rule is wrong and is not added**: *refuse when nothing
resolves*. Before a seating nothing resolves, and that is the correct state of a
freshly frozen card. `--sweep` may refuse on it because it reads many cards at
once; the per-file check may not.

⚠️ And two counts in that tool's own docstring were wrong, neither a typo: it
said *"Fifteen of them, and eight must fail — six of the fifteen drive this file
as a subprocess"*, against **ten** and **four** measured off `LABELS` and off
the four `_cli` call sites.

---

## 2. 🔴 `B1-C` refuted its own prediction, and the card's own arithmetic contained the refutation

§5.6 predicted that `claim` then `sample` would leave `n_req_ok` at **2** — *"the
`tryout 5` in `B1-T5` took one"* — and `n_get` at **≥ 1**. 量 `B1-CP`:
`n_req_ok` **1**, `n_get` **0**. Neither verb took effect.

**The cause, measured at artefact depth in this image's own disassembly**:
`gpio_direction_output` at `0x800d637c` calls `gpio_ensure_requested`
(`0x800d5b00`) at `0x800d642c`. That is 2.6.30 gpiolib's compatibility path: it
sets `FLAG_REQUESTED` itself and calls `chip->request`. So `tryout 5` left line
5 **held**, and the later `gpio_request` was refused by gpiolib before this
driver's `.request` was reached — which is exactly why `n_req_ok` did not move.

🟢 **The errno is measured rather than inferred.** `X24` sends the write through
`cat`, whose error path prints `strerror`, and the second `claim` on a held line
reads **`cat: write error: Device or resource busy`** — `EBUSY`.

🟢 **The positive control fired.** `X3`: `release` → `r=0`, then `claim` →
`c=0`, and `X4` reads `n_req_ok` **2**, `n_get` **1**. `X2` shows `sample` alone
works — `RLXFW-G-SAMPLE=00000001`, `rc=0` — so the second verb was not broken,
it was carried down by the first.

**The card's premise is intact and its arithmetic was not finished.** It knew
`tryout 5` had taken a request; it did not ask what a second request on the same
line does.

---

## 3. 🔴 The `dat` XOR is `00000060`, not `00000020` — and the reason is a bit that is not the button's

§5.5 predicts *"The XOR of `dat` between BTN1 and BTN2 must be exactly
`00000020`"*. 量, on **both** boots that ran the triple:

| | `BTN1` released | `BTN2` held | `BTN3` released |
|---|---|---|---|
| `dat` | `0000007C` | `0000001C` | `0000007C` |
| XOR(BTN1,BTN2) | | **`00000060`** | |
| XOR(BTN1,BTN3) | | | **`00000000`** |

Bit 5 moved as predicted. **Bit 6 moved too**, and bit 6 is the pin the vendor's
driver turns into an output (`REG-35`, `DIR |= 0x40`).

🔴 **The first reading of that was wrong and a second measurement refuted it.**
Two samples 3 s apart with the button held throughout read `0000001C` then
`0000005C`, and it was written down as *bit 6 blinks on its own*. **It does
not**: with the button RELEASED, 15 samples with no delay and 12 samples at 1 s
— 27 readings over about 13 s — are all `0000007C`. Bit 6 is static when the
button is up.

🟢 **Held, it alternates, and the alternation is exact.** `X17`, 12 samples at
1 s with the button down: `5C 1C 5C 1C 5C 1C 5C 1C 5C 1C 5C 1C` — six and six,
strictly alternating. `X16`, 15 samples with no delay in the same state: all
`1C`. **The released run used the identical two instruments**, so it is a
negative control rather than a different measurement that happens to disagree.

**So `dat` is a register with a bit that changes on its own schedule while the
button is down, and no XOR of two whole-word samples can satisfy §5.5.** The
quantity the card wanted survives at a mask: `(dat_BTN1 ^ dat_BTN2) & 0x20` is
**`00000020`** on both boots. `btn_raw` and `btn_pressed` are single-bit fields
and behaved exactly as predicted, `1 → 0 → 1` and `0 → 1 → 0`, on both.

⚠️ **`BRD-05` is not refuted.** Its `XOR = 00000020` was measured in the
**loader**, where `PABCD_DIR` is `0xFF000000` and bit 6 is an input. This card
carried a loader-state reading into a booted Linux where `DIR` is `0xFF000040`.
The two are consistent; the card's prediction was the thing that did not carry.

---

## 4. 🟢 What bit 6 actually is: the vendor's button path, read end to end and then closed on the silicon

This is the largest result of the seating and none of it was on the card,
because nothing in this repository knew these symbols existed.

### 4.1 What the artefact says

Read from this image's own `vmlinux` (cell `r54b`) with a distribution
`objdump`; **no vendor `.c` was opened** — the same `artefact` depth `REG-35`
was taken at (`docs/blind-write-ledger.md` § 4.9).

The address `0xB800350C` (`PABCD_DAT`) is materialised **eleven times in nine
functions**: `reset_button_pressed`, `autoconfig_gpio_init`, `autoconfig_gpio_off`, `autoconfig_gpio_on`, `autoconfig_gpio_blink`, `autoconfig_gpio_slow_blink`, `rtl_gpio_timer` (three of the eleven), `read_proc` and `rf_switch_read_proc`.

🔴 **The first version of this paragraph said *four functions*, and it was written after resolving FIVE of the eleven addresses.** Nothing was wrong with the five; the count beside them was a generalisation from a partial view — the most expensive mistake this repository makes, and the one no checker here catches. It was found by re-deriving the number, not by re-reading the sentence, and by then it had been copied into five files.
🟢 **The five that were missing are the informative ones**: `autoconfig_gpio_blink` and `autoconfig_gpio_slow_blink` are named for exactly the behaviour § 3 measured on bit 6, so an inference from a waveform is now also a name in the image.

`reset_button_pressed` (`0x800e59d8`) calls `sys_bonding_type()`; **if the
result is not 13** it reads `PABCD_DAT`, masks `0x20`, and returns 1 when the
bit is **clear**. 🟢 **That is `BRD-05` stated by the vendor's own code** — bit
5, active low. 🟢 **And the constant 13 is `REG-30`'s**: the loader's
`0x80408DE4` takes a different branch when the same nibble reads 13. Two
independent artefacts, one constant.

`rtl_gpio_timer` (`0x800e5c48`) re-arms itself with
`mod_timer(&t, jiffies + 100)` at `0x800e5f2c`–`0x800e5f30`. **At `HZ = 100`
that is one second.** It counts consecutive seconds with the button down in
`shared_info + 0x31a0`, and on **release** it branches three ways:

| hold | what it does |
|---|---|
| `< 2` s | clears its counters, nothing else |
| `2`–`4` s | `kill_pid(find_vpid(1), 15, 1)` — **SIGTERM to PID 1** |
| `≥ 5` s | `sb 49` — ASCII `'1'` — into `default_flag` (`0x80296478`), and clears bit 6 with `& ~0x40` |

While the button is **down** it sets or clears bit 6 according to `count & 1`
(`andi v1,0x1` at `0x800e5cdc`), which is a one-second parity — **the two-second
alternation `X17` measured, arrived at from the other side**.

🟢 **`FW-37` says what the 2–4 s branch would do here — and no short press was
performed.** The branch signals PID 1 (讀, from the disassembly), and `FW-37`
measured that signalling PID 1 does nothing on this image, because PID 1 is
`config/rlxfw-init.sh`, a shell script that ignores it — the same finding that
made `busybox reboot` without `-f` not reset the board. ⚠️ **Putting those two
together is an inference, not a reading**: every hold this seating performed was
well over five seconds, so the 2–4 s branch was never taken on the die. The
experiment that closes it is one press held for about three seconds.

### 4.2 Who reads the flag, and why that is the safety answer

`rtl_gpio_init` creates three `/proc` entries at `0x802b1758`, `0x802b178c` and
`0x802b17b8`, whose name strings read out of the ELF at `0x80276150`,
`0x80276160` and `0x8027616c`: **`load_default`**, **`rf_switch`**,
**`watchdog_reboot`**.

Scanning the whole disassembly for `default_flag`, the only readers in this
image are **`default_read_proc`** and **`default_write_proc`** — the `/proc`
handlers. 🟢 **Nothing in the kernel acts on it.** The factory reset is the
vendor's *userspace* job, and this image's userspace is `/bin/sh` and one init
script.

⚠️ **Four of the seven hits that scan produced are false positives and are
named rather than filtered away**: `br_update_igmp_snoop_fdb` ×2 and
`br_handle_frame_finish` ×2 match on the **offset** 25720 from a different base
(`0x8024…`, not `0x8029…`). The scan matched an offset, not an address.
🟢 Its positive control fired: `rtl_gpio_timer`'s own `sb` at `0x800e5d90` was
found by the same pattern.

### 4.3 🟢 Closed on the silicon, prediction first

`X19`, taken on boot 10 minutes before any of this was believed:
`/proc/load_default` reads **`0`**, `/proc/rf_switch` reads **`0`**.

The predictions `Q1`–`Q4` were written into the run script **before** the
operator was asked to press. Then one hold of about 8 s and a release:

| | predicted | measured |
|---|---|---|
| `Q1` `/proc/load_default` | **`1`** | **`1`** |
| `Q2` `/proc/rf_switch` | `0` | `0` |
| `Q3` nothing reboots | — | same shell, same boot |
| `Q4` `n_writes` | `0` | `0` |
| `P3` `/proc/watchdog_reboot` exists | — | listed by `ls` |

🟢 **And an unpredicted one, in the same reading**: `dat` reads `0000003C`, bit
6 low — which is `boot_dat`. 12 samples at 1 s afterwards are all `0000003C`,
using the instrument that read 12 × `0000007C` before the press. The `& ~0x40`
in the `≥ 5` s branch turns the pin off and leaves it off.

**So the whole path — one-second timer, five-second threshold, the flag, the
pin — was read out of compiled vendor code and then confirmed on the die.**

---

## 5. 🔴 `busybox ash` puts a refused write's payload on the console, and it reads like board output

`B1-T5`'s capture holds `/proc/rtl819x-gpRiLoX` followed by
`FW-G-TRYRC=FFFFFFFF`. De-interleaved that is the shell echoing `…-gpio\r\n`
and the kernel printing `RLXFW-G-TRYRC=FFFFFFFF\r\n` at the same time, character
by character on one UART. **`grep -c 'RLXFW-G-TRYRC=FFFFFFFF'` on that file
returns `0`**: the board printed the mark and the whole string is not contiguous
in the capture.

`B1-C` then held nine characters — `claisampl` — that nothing predicts.
Measured, five payloads and a negative control:

| verb written | bytes with `\n` | on the console | |
|---|---|---|---|
| `claim` | 6 | `clai` | 4 |
| `sample` | 7 | `sampl` | 5 |
| `abcd` | 5 | `abc` | 3 |
| `abcdefgh` | 9 | `abcdefg` | 7 |
| `abcdefghijklmnopqrstuvwxyz0123` | 31 | `abcdefghijklmnopqrstuvwxyz012` | 29 |
| **`lock`** — a verb that **succeeds** | 5 | **nothing** | 0 |

**The leak is the payload minus its last character and the newline, and only on
a write the driver refused.**

🟢 **Located, not guessed.** 29 characters is longer than the driver's
`char buf[24]`, so the driver's buffer is not the source. `X12` sends the same
failing write through `cat` — `echo abcd | cat > /proc/rtl819x-gpio` — and the
console holds `cat: write error: Invalid argument` and **no payload at all**.
**It is `busybox ash`'s builtin `echo`.** The exact off-by-two inside ash is not
derived; busybox source is not in this repository.

🔴 **The reach is beyond this block**: every `--send` capture in this repository
where an `echo … > file` failed contains a partial echo of what was written,
produced by the shell, sitting where board output goes. And any assertion that
greps a whole mark out of a `--send` capture can report *absent* on a mark the
board printed.

⚠️ Two instrument limits found on the way, both recorded because a missing
applet and a broken experiment look alike: **this busybox has no `dd` applet**
(`dd: applet not found`), which closed the first route to the paragraph above;
and **its `grep` has no `-E`** (`grep: invalid option -- E`).

---

## 6. 🟢 What the card predicted and the board confirmed

Ten boots. One cold power-on inside a 150 s ESC window (`B1-A`, 78,825 bytes,
495 `Unknown command !`, ending on a clean `<RealTek>`); nine warm resets by
`busybox reboot -f`.

| | predicted before power | measured |
|---|---|---|
| `RLXFW-ID0` | `5DA34246` | `5DA34246`, ten times, compared by the tool against the digest the build computed |
| `G1` (negative control) | `FFFFFFDF` | `FFFFFFDF`, ten times |
| `G2` (negative control) | `FF000000` | `FF000000`, ten times |
| `G3` | bit 5 set | `0000003C`, ten times |
| `G4` | `00000000` | `00000000` — `gpiochip_add()` returned 0 |
| `G5` | `00000001` | `00000001` |
| `G0`, `G6` | present | present |
| boot capture | **1,184 bytes** (1,069 + 115, from the mark strings) | **1,184 bytes** |
| ten boot captures | — | **byte-identical**, one sha256-16 `d12fc9c057e4e1c3` |
| `boot_cnr` / `boot_dir` | `FFFFFFDF` / `FF000000` | as predicted |
| **`cnr` live** | **`FFFFFF8B`** (推, `0xFFFFFFDF & ~0x74`) | **`FFFFFF8B`** |
| **`dir` live** | **`FF000040`** (推, `0xFF000000 \| 0x40`) | **`FF000040`** |
| `cnr_as_spec` / `dir_as_spec` | 0 / 0 | 0 / 0 |
| `tryout 5` | `FFFFFFFF` (`-EPERM`), three XORs `00000000` | as predicted |
| `tryout 12` | `FFFFFFED` (`-ENODEV`), three XORs `00000000` | as predicted |
| `n_dirout_no` / `n_req_no` / `n_req_ok` | 1 / 1 / 1 | 1 / 1 / 1 |
| `n_writes` | `0`, and non-zero stops the block | **`0`** in every dump of the seating |
| oops text | absent, and absence is measurable (`FW-36`) | absent |
| `probe04` | no prediction; the point is to have the number | `0xB8003504` reads **`00000000`** |

All ten `Bn-P` dumps agree in **every one of 27 fields**.

🟢 **The initcall ordering is observed rather than derived.** `G0`…`G6` appear
in every boot capture *before* the vendor's `Probing RTL8186` and `eth0 added.`
lines and after `TA0`…`TA4` — `arch_initcall` 3, `subsys_initcall` 4,
`device_initcall` 6, in that order, on the die. `REG-35` read those levels out
of `System.map`; the capture shows them happening.

`looprun --mode bench` closed ten times with six assertions each:
**24.85 – 25.22 s**, mean **24.93 s**, total **249.32 s** of machine time.

---

## 7. What this block still does not establish

§7 of the card lists five, and all five stand: which port letter bit 5 is;
whether bits 2, 4 and 6 are usable; any output; any GPIO interrupt; and whether
the loader is safe to boot with the button held.

**The last one has moved, and only for Linux.** § 4 above answers what the
*vendor's Linux driver* does with a held button, from its own compiled code and
then on the die. It says nothing about the **loader**, which is where the card's
§2.1 drew the line, and no `FLR` bracket ran this seating — so *not one flash
byte is written* is exactly as unsayable as it was, and the bracket stands where
it stood.

Two new open items, both desk work:

1. **Seven of the nine functions that touch `PABCD_DAT` were seen and not
   read**: `autoconfig_gpio_init`, `autoconfig_gpio_off`, `autoconfig_gpio_on`,
   `autoconfig_gpio_blink`, `autoconfig_gpio_slow_blink`, `read_proc` and
   `rf_switch_read_proc`. Only `reset_button_pressed`, `rtl_gpio_timer` and
   `rtl_gpio_init` were disassembled and understood.
2. **`sys_bonding_type()` is read by both the loader and this kernel and
   nothing here knows what it is.** It is the gate on the whole button path in
   both artefacts.
