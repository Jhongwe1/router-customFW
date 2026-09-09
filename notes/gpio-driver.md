# `rtl819x-gpio`, and the argument for opening one bit of its write mask

**`R5-4` shipped this driver on 2026-09-06 (seating 15) and it has never had an
owner file.** `notes/timer-driver.md`, `notes/spi-mtd-driver.md` and
`notes/watchdog-driver.md` each own their step's findings; the GPIO chip's are
spread across `docs/bringup.md`, `docs/KNOWN-ISSUES.md`, `notes/device-tree.md`,
`notes/modern-kernel-port.md` and `docs/blind-write-ledger.md` § 4.9, with
`SPEC.md` indexing them. This file becomes the owner from **2026-09-10**, the
fifty-second segment. It does **not** retro-document `R5-4`: what is here is
what this segment measured, plus the argument it was measured for. Where a
`R5-4` finding is quoted below it is quoted with its owner named, and the
owner is not moved.

*(Found by enumerating every possible owner and asking whether this segment
produced something it owns — the method the forty-ninth segment's audit
established after five green gates had found nothing. The gap itself is older
than this segment and is not this segment's doing.)*

---

## 1. The question `R5-7` opens

`R5-7` puts an LED on `PABCD` bit 6. Nothing about that is possible today,
because **two guards refuse it, and both of them are mine**:

| guard | value today | what it does | where |
|---|---|---|---|
| `RTL819X_GPIO_KNOWN_MASK` | `0x00000020` | `.request` returns `-ENODEV` for every line but 5 | `rtl819x-gpio.c:178` |
| `RTL819X_GPIO_ALLOW_OUT_MASK` | `0` | `.direction_output` and `.set` refuse every line | `rtl819x-gpio.c:183` |

A third interlock sits behind the second: `rtl819x_gpio_unlocked` must equal
the line number, and the `unlock` verb that sets it is itself gated on
`ALLOW_OUT_MASK`, so with the mask at `0` the runtime path cannot be opened at
all. That is three refusals deep, and it is deliberate — `FW-39` measured that
the compiler *deleted* both write paths because the mask proved them
unreachable.

**So `R5-7` is not "write an LED driver". It is "decide to open a guard on a
one-device-no-spare project, and be able to defend the decision".** This file
is that decision. The driver comes after it.

---

## 2. What `R5-4` deliberately left shut, in its own words

`rtl819x-gpio.c`'s header states three hazards as the reason `ALLOW_OUT_MASK`
is `0`, and it is worth restating them exactly, because the whole of § 3 is
answering *these three* and not three of my own choosing:

1. **CNR.** `0xFFFFFFDF` means 31 of 32 pins are on peripheral functions this
   project has not identified. The UART the board is read through is a
   candidate and so is the SPI controller that reaches the flash. *"Clearing
   the wrong CNR bit takes a pin away from whatever owns it, and on a
   one-device-no-spare project the failure mode of 'the console stopped' is
   indistinguishable from 'the kernel hung'."*
2. **DIR.** `0xFF000000` means bits 24..31 are already outputs, driven by
   something unidentified. *"A masked write whose mask is wrong reaches them."*
3. **Bit 5.** *"The one line that IS a GPIO is the worst output of all. It has
   a pull-up and a button to ground. Driving it high while the button is held
   shorts the pad driver through the switch."*

And the sentence that makes this file possible at all:

> `RTL819X_GPIO_ALLOW_OUT_MASK` is 0. Not "0 for now" — 0 because no line on
> this die has a measured safe output state, **and the constant is the one
> place that changes when one does.**

One line now has a measured safe output state. That is what § 3 establishes.

---

## 3. The three hazards, answered one at a time, for bit 6 only

### 3.1 CNR — the hazard is structurally absent, not argued away

The driver never writes CNR. `.direction_output` writes `PABCD_DAT` and
`PABCD_DIR` and nothing else; `.direction_input` *verifies* CNR and returns
`-EIO` if it disagrees. Opening `ALLOW_OUT_MASK` does not add a CNR write,
and the change proposed in § 7 does not either.

It does not need to. 量 (`REG-35`, seating 15, ten boots, twenty-seven fields
identical): under Linux the live `cnr` reads **`FFFFFF8B`** — bit 6 is
**already clear**, i.e. already a GPIO — put there by the *vendor's own*
`rtl_gpio_init` doing `CNR &= ~0x74` at `device_initcall`. The boot snapshot
in the same dump reads `boot_cnr FFFFFFDF`, so the transition is observed
rather than assumed.

🟢 **So the correct implementation of "make bit 6 a GPIO" on this die is to
check that it already is, and the code for that already exists and already
runs.** This is the same shape `R5-4` used for bit 5's direction: *"a driver
that needs no writes should issue none; there is no separate safety argument
to make."*

⚠️ **The check has to be in the code and not in this paragraph**, because it
depends on initcall ordering — see § 3.4.

### 3.2 DIR — bounded by the operation, not by the argument

The write is `rtl819x_gpio_wr(DIR, dir | (1u << off))` with `off` constrained
to the mask: a read-modify-write that can only **set** one bit. It cannot
clear bits 24..31, which is the stated hazard. The mask restricts `off` to 6.

And again the write is one the hardware has already taken: 量 `REG-35`, live
`dir` reads **`FF000040`** — bit 6 is **already an output**, set by the
vendor's `DIR |= 0x40`. So the DIR write in `.direction_output` writes a value
the register already holds.

🔴 **What is genuinely new is a lost-update race**, and it is stated rather
than dismissed: the vendor's `rtl_gpio_timer` does read-modify-write on
`PABCD_DAT` from a timer softirq (`FW-40`), and my spinlock is unknown to it.
Two RMW sequences can lose one update. Its consequence is bounded in § 6 and
it is not a safety consequence.

### 3.3 Bit 5's pull-up — a different pin, and this one has already been driven

Bit 6 is not bit 5. Bit 5 stays out of `ALLOW_OUT_MASK`, so the pin with the
pull-up and the switch to ground is refused exactly as it is today, and § 8
makes that a *measured* refusal rather than an assumed one.

For bit 6 the hazard "driving this pin damages something" is not argued — **it
is refuted by measurement, and the measurement was taken by somebody else's
firmware on this die**:

* `FW-40`, 讀 out of this image's compiled code: `rtl_gpio_timer` re-arms at
  `jiffies + 100` and, while the button is held, sets or clears bit 6 on
  `count & 1`. That is one write per second, alternating, indefinitely.
* `REG-37`, 量 seating 15: twelve one-per-second samples read
  `5C 1C 5C 1C 5C 1C 5C 1C 5C 1C 5C 1C` — six and six, strict alternation. The
  released control in the same session is twenty-seven samples all `0000007C`.
* `BRD-13`, 量 seating 19: bit 6 drives **the 2nd of the 8 LEDs on the board**,
  **active low** — the operator reports *dark* at `1` and *steadily lit* at
  `0`, each level measured separately, with the other seven LEDs as the
  negative control.

🟢 **Both output levels of this exact pin have been driven on this exact die,
repeatedly, across at least two seatings, with light observed and nothing
damaged.** No argument I could write would be worth as much as that, and the
right thing to say about it is that it was free: nobody set out to establish
it.

### 3.4 The ordering question § 3.1 depends on, measured rather than assumed

Both of § 3.1's and § 3.2's answers say *the vendor already did it*. That is
only true if the vendor's `rtl_gpio_init` runs **before** the LED consumer
probes.

量 2026-09-10, on `r57` (`System.map`, this project's own build):

```
802d0ab0 t __initcall_rtl819x_gpio_init4      my gpio_chip, subsys_initcall
802d0bb0 t __initcall_rtl_gpio_init6          the vendor's, device_initcall
```

and 讀 `drivers/Makefile` in this drop, which fixes link order *within* a
level:

```
line  8   obj-y                 += gpio/
line 26   obj-y                 += char/          <- rtl_gpio.o
line 71   obj-$(CONFIG_INPUT)   += input/
line 94   obj-$(CONFIG_NEW_LEDS)+= leds/          <- leds-gpio.o
```

`leds-gpio`'s `gpio_led_init` is `module_init`, i.e. `device_initcall`, level
6 — the same level as the vendor's, and **linked 68 lines later**, so it runs
after. 量 for scale, the level histogram of this image: `1 / 9 / 2 / 2 / 18 /
7 / 99 / 9` for levels 0..7, so level 6 holds 99 entries and "later in the
list" is the only thing separating two of them.

🔴 **A conclusion that rests on a Makefile's line numbers is worth less than
one that rests on a register**, so the driver does not rest on it: § 7 makes
`.direction_output` *verify* CNR before it writes, exactly as
`.direction_input` already does, and return `-EIO` if bit 6 is not already a
GPIO. Then a reordering makes the LED fail to probe with a legible errno
instead of taking a pin away from a peripheral.

---

## 4. The measurement taken before the change

**Everything in this section is on `r57-20260909`, sha256-16
`ef7e8b57a46e0659` — the image that ran on the silicon at seating 19 — with
`/usr/bin/mips-linux-gnu-objdump` 2.42, a distribution binary and not the
vendor toolchain, so no `vendor-tripwire.sh` is required (the same standing as
`FW-39` and `FW-43`).**

The point of taking it *now* is that § 7's change is supposed to move these
numbers. A "before" reading whose instrument lives in a scratch directory
cannot be compared with anything, which is why § 4.2's instrument is committed.

### 4.1 `FW-39` reproduced on a second artefact — and it is 4 bytes wrong

`FW-39` records, on `r54b`: `rtl819x_gpio_direction_output` is **`0x6C`** bytes
of range check, interrupt disable, counter increment and `-EPERM`, with no
instruction reaching the GPIO block; `rtl819x_gpio_set` is `0xA0`.

量 2026-09-10, from the **symbol table's own size field** on four artefacts:

| image | `direction_output` | `set` |
|---|---:|---:|
| `r54-20260906` | **0x70** | 0xA0 |
| `r55-20260907` | **0x70** | 0xA0 |
| `r56-20260908` | **0x70** | 0xA0 |
| `r57-20260909` | **0x70** | 0xA0 |

`r54-20260906` **is** `r54b`: its `rtl_gpio_init` is at `802b1670` and its
`rtl_gpio_timer` at `800e5c48`, the two addresses `REG-35` and `FW-40` quote.
`git log` says `rtl819x-gpio.c` has not been touched since `48a7a2a`, so one
source produced all four.

🔴 **The function is `0x70` and `FW-39` says `0x6C`, and the missing 4 bytes
are the delay slot.** The disassembly ends:

```
800d6990:	2402ffff 	li	v0,-1        # -EPERM
800d6994:	03e00008 	jr	ra
800d6998:	00000000 	nop              # <- the delay slot
```

A listing read by eye ends at `jr ra`. **On a machine whose delay slot is
architecturally exposed — the property `CLAUDE.md` has a whole row about —
that is exactly the instruction a hand drops.** The symbol table's `size`
field does not have the problem, and § 4.2's tool reads addresses rather than
counting listing lines.

⚠️ `FW-39`'s **conclusion is untouched**: the only store in the function is
`sw v1,-14108(v0)` with `v0` from `lui v0,0x8036` — the `n_dirout_no` counter —
and there is no `lui 0xb800` anywhere in it. The number beside the conclusion
is what moves, and the caveat *"true of `r54b` only"* turns out to have been
cautious in one direction while the figure was wrong in the other: it is the
same on four images.

🟢 **And this run adds the control `FW-39` did not have.** `FW-39`'s control is
that two counter stores fire while `n_writes` reads zero — a control *inside*
the scan. The sibling control is stronger: `rtl819x_gpio_direction_input`, the
same file, the same build, **does** contain `lui v0,0xb800` (at `800d929c` on
`r57`) because it reads CNR and DIR. So "no `lui 0xb800` in
`direction_output`" is a reading and not a scan that finds nothing — a
function that *should* show one, does.

### 4.2 The register census, and the blind spot that hides my own driver

`docs/blind-write-ledger.md` § 4.9 records *"the **nine** functions that
materialise `0xB800350C` were located — this row said FOUR until the count was
re-derived off the eleven `ori` sites"*. That census was done by hand twice
and the two hands disagreed. `R5-7` has to re-take it before it opens a write
mask, so it is now `tools/regcensus.py`, twenty-one controls, all synthetic.

量 2026-09-10, `r57`, `--base 0xb800`:

| register | confirmed sites | symbols | mine | vendor | unpaired |
|---|---:|---:|---:|---:|---:|
| `PABCD_DAT` `0xB800350C` | 11 | **9** | **0** | 9 | 0 |
| `PABCD_DIR` `0xB8003508` | 2 | 2 | 0 | 2 | 1 |
| unnamed `0xB8003504` | **0** | 0 | 0 | 0 | 0 |
| block base `0xB8003500` | 8 | 7 | **5** | 2 | 1 |

🟢 **The ledger's nine is reproduced exactly, by a different method, including
the `addiu` completion form the hand census did not look for.**

🔴 **And the census cannot see this project's own driver.**
`rtl819x_gpio_get` reads `PABCD_DAT` on every call, and it appears **zero**
times in `PABCD_DAT`'s census — because the compiler forms the block base
once and folds `+0x0C` into the load's displacement. The vendor's code in the
same image forms full addresses and is entirely visible. So:

> **An `ori 0x350c` census counts full-address materialisations. It is a lower
> bound on the functions that touch the register, and the proof that it is a
> lower bound is that it misses the one driver whose source is in this
> repository.**

The tool therefore prints the block-base census beside it as the bound: **6
symbols form the base and never form `PABCD_DAT`'s own address**, so a
displacement access from any of them is invisible. Five are mine. The sixth is
the vendor's `rtl_gpio_init`.

⚠️ On this block the bound is unusually weak for a structural reason worth
stating: **the block base and `PABCD_CNR` are the same address**, so a symbol
that forms `0xB8003500` may be reading CNR or may be reaching any of the four
registers by displacement, and this instrument cannot tell those apart.

🟢 **A second thing the pairing test earned on its first real run.** Two
`addiu` sites with the right immediates appear in `del_sta` — a wireless
driver symbol — at `801614e0` (`0x3508`) and `80161478` (`0x3500`). Neither
has a `lui 0xb800` above it: they are ordinary pointer arithmetic on a
13,576-byte structure offset. Without the pairing test both would have been
counted as GPIO accesses, and the report would have said *the wireless driver
touches `PABCD_DIR`*. They are reported as `UNPAIRED` rather than dropped,
because a filtered list looks like a clean census.

### 4.3 What the census says, and the one number in it that is a correction

Of `PABCD_DAT`'s nine symbols, the ledger says *"**three** of them were
actually read: `reset_button_pressed`, `rtl_gpio_timer` and `rtl_gpio_init`"*.

🔴 **`rtl_gpio_init` is not one of the nine.** 量: it materialises the block
base and `PABCD_DIR`, and never `PABCD_DAT` — which is consistent with
`REG-35`, whose reading of it lists `CNR &= ~0x74` and four `DIR` operations
and **no `DAT` write at all**. So **two** of the nine were read, not three,
and **seven** are unread. The ledger's own parenthetical list — *"the other
six … plus `rf_switch_read_proc`"* — is exactly those seven, so the list was
right and the count beside it was wrong, in the same shape as the *"These
four"* it corrected on 2026-09-07.

The seven that touch `PABCD_DAT` and have never been read:

```
autoconfig_gpio_init  autoconfig_gpio_off  autoconfig_gpio_on
autoconfig_gpio_blink  autoconfig_gpio_slow_blink
read_proc             rf_switch_read_proc
```

They are contiguous in the image with the two that *were* read
(`800e849c`..`800e8dcc`), so they are one object's worth of code, and their
names read like a vendor LED API.

---

## 5. 🔴 The hole this argument does not close, and the trade that leaves it open

**Five of those seven have names that say they drive a light.** The obvious
next step is to disassemble them and find out whether anything calls them.
This segment did not, and the reason is a trade rather than an oversight.

`docs/blind-write-ledger.md` § 4.1 records the `led` domain at **zero cited
paths**, and § 8's table gives it the verdict *"blind of any implementation"*.
§ 0 ② calls that *"this ledger's strongest row"*. Reading `autoconfig_gpio_*`
would spend it — and § 4.3.1 has already established that a count taken out of
the vendor's *object* code is a declarable reading with a depth, not a
loophole.

The trade, both sides:

* **What reading them buys**: the identity of any other writer of bit 6, and
  whether the five are live or dead code.
* **What it costs**: `R5-7`'s independence claim, permanently, on the layer
  `driver-diff` scores. `R5-9` has not run yet.
* **What replaces it**: § 6's runtime detector answers the *operative*
  question — *is anything else writing this bit while my driver owns it* —
  directly, on the die, with a positive control, and at zero cost.

> § 6 of the ledger is titled *"the question this ledger cannot answer, and the
> order that keeps it answerable"*. The same order applies here: **the reading
> is available later and the blindness is not.** If the detector ever fires,
> the reading is then taken *to explain a measurement*, which is the strongest
> reason there is to take one — and by then it will not have shaped the
> decision, which is § 4.3.1's own test.

⚠️ **Stated plainly so it cannot read as coverage:** this argument opens a
write mask on a register that seven unread functions in the same image
materialise. That is a known, quantified, deliberately unresolved hole. What
bounds it is § 6 — not this paragraph.

---

## 6. The residual is contention, and it is correctness rather than safety

Two writers, no arbiter. `gpio_request` arbitrates between gpiolib consumers;
the vendor's driver does not go through gpiolib, so nothing can mediate.

🟢 **The consequence is bounded by § 3.3**: every level either writer can
produce on bit 6 has already been produced on this die by the vendor's own
firmware, at 1 Hz, with light observed. **The worst outcome of losing the race
is that a light is wrong.** It is not a safety hazard, and calling it one
would be the "agreeable understatement" this project's own house rules warn
about, in reverse.

🟢 **And the contention window is under the operator's hand.** `FW-40` reads
`rtl_gpio_timer` as touching bit 6 only while the button is held, and on
release. `REG-37`'s released control is twenty-seven samples of a static
`0000007C`, and `X6-decay`'s post-long-press control is thirty samples of a
static `0000003C` across 152.1 s. So with the button untouched the vendor is
not observed to write bit 6 at all.

### 6.1 The instrument

`rtl819x-gpio` 1.1 gains a **foreign-write detector**, the same shape as
`rtl819x-spi`'s `n_state_foreign` (which read **0** across 4,115 transfers):
the driver remembers the value it last wrote to `PABCD_DAT`, and on every
subsequent access compares the live register's **bit 6 only** against it.
Divergences are counted in `n_state_foreign` and the first one is latched with
its value.

Bit 6 only, because bit 5 is a button and legitimately moves.

### 6.2 Its positive control, which costs nothing

A counted zero is a claim. The control is already on the bench and is free:

| population | act | `n_state_foreign` |
|---|---|---|
| the ten `D1` boots | button untouched | must be **0** |
| one extra boot | button **held** for ~10 s while `/proc` is sampled | must be **> 0**, about one per second |

🔴 **The detector's stated limit**: it samples. A write undone before the next
sample is invisible. That is why the positive control holds the button for
seconds against a 1 Hz writer rather than looking for a single event.

---

## 7. What changes, exactly

```
 #define RTL819X_GPIO_KNOWN_MASK      ((1u << 5) | (1u << 6))   /* was 1<<5 */
 #define RTL819X_GPIO_ALLOW_OUT_MASK  (1u << 6)                 /* was 0    */
```

and four consequences that are not one-line:

1. **`.direction_output` verifies CNR before it writes.** `-EIO` if
   `cnr & (1<<off)` — the pin is on a peripheral function — mirroring
   `.direction_input`. This is § 3.4's ordering assumption turned into a
   runtime check. It still never writes CNR.
2. **The `rtl819x_gpio_unlocked` interlock is replaced by
   `rtl819x_gpio_out_locked`, a runtime mask that can only NARROW.** The
   effective allow mask becomes `ALLOW_OUT_MASK & ~out_locked`, default
   `out_locked = 0`.
   🔴 **This is a weakening and it is written down as one**: until today,
   output was impossible until somebody typed a verb; from now on it is
   possible for exactly the lines in the compiled mask. The reason is that
   `leds-gpio` cannot type a verb, so an opt-in interlock means either the LED
   never works or the interlock is always open — and an interlock that must be
   open for the driver's only consumer to bind is not an interlock.
   🟢 The compensation is that the guard becomes **two-sided and testable on
   the die in one boot**: `lock 6` → a sysfs `brightness` write must leave the
   register unmoved; `unlock 6` → it must move it. Until today the guard had
   only ever been observed refusing, which is a wall rather than a guard.
   ⚠️ The name is inverted deliberately relative to the old one, because
   `unlocked` defaulting to "everything unlocked" would be a name that lies.
3. **`n_state_foreign` and the counters of § 6.1.**
4. **Two new marks** so a boot capture carries the answer with no shell:
   `G7` = `PABCD_DAT` immediately before the first permitted
   `.direction_output`, `G8` = immediately after.

### What `n_writes` becomes, predicted before the build

`leds-gpio`'s probe is, 讀, verbatim: `gpio_request` → `gpio_cansleep` →
`gpio_direction_output(gpio, led_dat->active_low)` → `led_classdev_register`.
And 讀 `led-class.c`: `led_classdev_register` calls `led_update_brightness`,
which is a no-op unless `brightness_get` is set — and `leds-gpio` does not set
it. **So `.set` is not called at probe.**

`gpiolib`'s `gpio_direction_output` (讀, 2.6.30) calls `chip->direction_output`
and never `chip->set`; it requires both to be present, which is why
`R5-4` could not simply omit `.set`.

| | prediction |
|---|---|
| `n_writes` after probe | **exactly 2** — one `DAT`, one `DIR`, from one `.direction_output` |
| the `DAT` value written | `active_low` = **1** = bit 6 high = **dark** |
| whether it changes anything | **no**, if `dat` is at the vendor's resting `0000007C` |
| the `DIR` value written | `dir \| 0x40`, and `dir` already reads `FF000040` |
| whether it changes anything | **no** |

🟢 **So the first two register writes this project's LED path ever performs
both write values the register already holds, and both were put there by the
vendor's own driver, measured on this die.**

🔴 **The stated exception**: after a long press, `REG-37` measured `dat`
latched at `0000003C` — bit 6 **low**, the LED lit — stable for at least
152.1 s. If the board boots into that state, the probe write *does* change the
pin, from lit to dark. That is still a state the vendor holds it in for most
of its life, and `G7`/`G8` are there so the capture says which of the two
happened rather than leaving it to be assumed.

---

## 8. Refutation conditions, written before the change

Each of these would say the argument above is wrong, and each names the reading
that would say so.

| # | what would refute it | what is read |
|---|---|---|
| `RC1` | the compiler does **not** put the write paths back — `direction_output` stays `0x70` with no `lui 0xb800` | `regcensus` + `objdump` on the new image. If the mask change did not reach the artefact, nothing below means anything |
| `RC2` | `n_writes` after probe is **not 2** | `/proc/rtl819x-gpio` on ten boots. 3+ means something calls `.set` that this file says does not; 0 means the probe failed |
| `RC3` | `cnr_as_spec` or the live `cnr` moves from `FFFFFF8B`, or `dir` from `FF000040` | the same dump. § 3.1 and § 3.2 rest on the vendor having already done both |
| `RC4` | `.direction_output` on **line 5** returns anything but `-EPERM`, or moves any of the three registers | `tryout 5`, `G-TRYRC`/`G-TRYCNR`/`G-TRYDIR`/`G-TRYDAT`. The guard has to keep refusing the pin § 2 calls the worst output on the die, in the same boot in which it permits bit 6 |
| `RC5` | `n_state_foreign` is **non-zero** with the button untouched | ten boots. It would mean a writer this file has not accounted for, and § 5's reading becomes the next step |
| `RC6` | `n_state_foreign` stays **0** with the button held for 10 s | one boot. The detector would be measuring nothing, and `RC5`'s zero would be worthless |
| `RC7` | `leds-gpio` fails to probe | boot capture. It would mean the gpio_chip is not good enough for an unmodified upstream consumer, which is the whole claim of § 9 |
| `RC8` | the LED does not light when `brightness` is written | the operator's eyes, against `BRD-13`'s polarity |

🔴 **`RC4` and `RC6` are the two that make the rest mean anything**, and both
are positive controls rather than confirmations: one requires a refusal to
still happen, the other requires the zero to be capable of being non-zero.

---

## 9. The decision: **upstream `leds-gpio`**, not a driver of mine

`PROGRESS.md`'s step list calls `R5-7` **`leds-rtl819x`**.
`config/rlxfw-kernel.delta:82` — written 2026-09-06, at `R5-4` — calls it
**`LEDS_GPIO`**, and says `CONFIG_GENERIC_GPIO` *"is what `R5-7` (LEDS_GPIO)
and `R5-8` (KEYBOARD_GPIO) both depend on"*. 🔴 **Two owner files have been
saying different things about one step for four days.** Found by measuring,
not by re-reading.

量: `drivers/leds/leds-gpio.c` **is** in this drop (7,482 bytes), and
`LEDS_GPIO` depends on `LEDS_CLASS && GENERIC_GPIO`, which the delta already
carries.

**The delta is the correct half, and `PROGRESS.md` is amended.** The reasons,
in order:

1. The driver exists and is correct. Writing a second one is not engineering.
2. It makes the claim *stronger*. An **unmodified upstream consumer binding to
   my `gpio_chip`** is evidence about the `gpio_chip` that a driver of mine
   cannot produce, because I could have shaped mine to fit. It is the same
   reasoning `R5-4` already used for its own verbs: *"`claim`/`release` go
   through gpiolib rather than calling this driver's own ops, so what they
   exercise is the path a real consumer takes."*
3. `D1` asks for *"six drivers in-tree"*, not six drivers of mine, and `R5-8`
   was already accepted on that basis.

⚠️ **The cost, stated**: `R5-7` then contributes no LED C code. What it
contributes is the `gpio_chip`'s output path (§ 7), a platform device with
`gpio_led_platform_data`, and the DT binding — which is what a BSP is. And
`driver-diff`'s `led` row becomes a row about `rtl819x-gpio`'s handling of bit
6, because that is where the register facts live.

🔴 **One thing this decision creates that has no precedent here**: 量,
`arch/rlx` registers **zero** platform devices — `platform_device_register`
and `platform_add_devices` appear nowhere under it, and the only `platform.c`
files in the tree belong to `arch/mips` boards. `R5-7`'s platform device is
this project's first, and where it lives is an open item, not a decision this
file makes.

---

## 10. `R5-8`'s decision, which a link error makes for us

The open question was *`gpio-keys` or `gpio-keys-polled`*. It has a measured
answer and neither branch is the one that was expected.

量 2026-09-10, on this drop:

1. **`gpio-keys-polled` does not exist in it.** `drivers/input/keyboard/`
   holds `gpio_keys.c` and nothing else matching. (It reached mainline after
   2.6.30.)
2. **`gpio_keys.c` hard-requires `gpio_to_irq()`** — six call sites, at
   `:62` (a `BUG_ON` inside the ISR), `:134`, `:175`, `:199`, `:222`, `:240`.
3. 🔴 **`arch/rlx` declares `gpio_to_irq()` and defines it nowhere.** A grep
   over the whole arch returns exactly one line:
   `arch/rlx/include/asm/mach-generic/gpio.h:16`, a declaration. `R5-4`'s
   header already measured that the only caller in the built set is
   `gpiolib.c:1155`, inside `#ifdef CONFIG_DEBUG_FS`, which this image compiles
   out — *"turning `CONFIG_DEBUG_FS` on breaks the link."*

> **So `CONFIG_KEYBOARD_GPIO=y` does not fail at probe. It fails at link.**

And `input-polldev.c` **is** in the drop, with `INPUT_POLLDEV` a real Kconfig
symbol.

**The decision, in two parts, and the order matters:**

* **(a)** define `gpio_to_irq()` for `arch/rlx` as returning `-ENXIO` —
  *this arch has no GPIO interrupt controller*, which is the true statement,
  and `docs/interrupt-map.md` has no row for one. It is a `config/host-compat/`
  patch of a few lines. It **fixes a latent landmine in the vendor's arch
  port** — the declaration with no definition — as a side effect, and it turns
  `gpio_keys` from *does not link* into *probes and fails with a legible
  errno*, which is a result rather than a workaround.
* **(b)** `rtl819x-keys` on `input_polldev`, which is the one that works.

🟢 **(a) is (b)'s negative control**: the same board, the same button, two
drivers, one of which cannot work — and the reason is a property of the SoC
rather than of my code.

⚠️ (a) is a decision about *vendor source*, so it belongs in
`config/host-compat/` — the directory `HC-1` already records as having a name
narrower than its contents. This would be its sixth patch and its fourth that
the name does not fit.

---

## 11. What this file does not establish

1. **Which of `PABCD`'s four ports bit 6 belongs to.** Same as bit 5,
   `GPIO-1`, still open. It does not block anything here: the chip is labelled
   `rtl819x-pabcd` and lines are numbered by bit position, so a `leds-gpio`
   platform device names line 6 and never a port letter.
2. **What the seven unread functions do.** § 5. Deliberate, quantified, and
   the thing to reach for first if `RC5` fires.
3. **What `0xB8003504` is.** 量 today: **nothing in this image materialises
   its address** — 0 sites — which is new and is bounded by § 4.2's blind spot.
   `MAP-09` still has a value with no name.
4. **Whether the LED is safe to blink continuously.** Nothing here proposes a
   `default_trigger`; the ten boots write bit 6 exactly twice. A trigger is a
   separate decision with a separate argument, and it is the one that would
   put my driver and `rtl_gpio_timer` in contention on purpose.
5. **Anything about the loader.** No `FLR` ran, no flash byte was read, and
   the bracket is unchanged.
