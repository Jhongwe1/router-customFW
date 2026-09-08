# CLAUDE.md

rlxfw — an independent firmware for the TOTOLINK N150RT: Realtek RTL8196E, Lexra
core, big-endian, 4 MiB SPI NOR. **One device, no spare.** Built from four
vendors' GPL drops and one leaked draft datasheet, because TOTOLINK never
released source.

> **This file holds only what is true today.** 🔄 **2026-08-29, third update:
> MY KERNEL BOOTED ON THE SILICON.** `loudm` — 1,053,696 bytes, the `rtkload`
> pipeline's own `nfjrom` renamed — went to `0x80500000` over TFTP and was
> entered with `J`. It printed all eleven boot marks, reached a shell that
> **returns output from a typed command**, and pinged the workstation with the
> host's own capture holding both directions. `probe3` ran on the power cycle
> before it and measured this die's I-cache by experiment — **16 KiB, 16-byte
> lines, 2-way** — with both of its refutation controls firing, and found that
> **CP3 is reachable on this part** where the emulator says every `mfc3` traps.
> 🔴 **No flash-write command was issued, and that is NOT the same sentence as
> "not one flash byte is written"** — `RUNSHEET` `G8b` forbids the second without a
> full re-dump, and this seating ran no `FLR` bracket, so the flash-byte count is
> **unmeasured**. 🔄 **2026-08-30, fourth update: that bracket RAN, both
> halves, and it is now a reading.** *(This said “the next seating's card carries
> the bracket”.)* Three 256-byte windows over two power cycles — the loader head,
> the `cr6c` header, and **`H601`, which no bracket in this project had ever
> sampled** — six reads, all byte-identical to the 2026-08-16 dump; the first two windows
> also match the 2026-08-24 captures, and 🔴 **`H601` has none — there is no
> 2026-08-24 capture of it, so its gap is 14 days rather than 6**, with `AUTOBURN` reading `00000001` on the second cycle so
> the second half is an instrument's word and not the operator's. **768 of
> 4,194,304 bytes = 0.0183 %.** It still does not make the forbidden sentence
> sayable — it cannot see two writes that cancel, and it reads 256 of `H601`'s
> 8,192. 🔄 **2026-08-31, fifth update: 1,024 bytes = 0.0244 %, and for the
> first time the bracket has a NEGATIVE CONTROL.** Four windows — the fourth is
> `0x006400`, the canary page `FLS-21` measured moving — read on two power
> cycles, and **every destination was read BEFORE its `FLR`**: all eight
> pre-reads differed from the expectation, so *the `FLR` wrote* is measured
> rather than assumed. `H601` reach **6.3 %**. 🟢 **And one round ran AFTER a
> complete rlxfw boot** — kernel, userspace, 4 MiB through `mtd_read`, an
> `EACCES` write attempt, a ping — which is the first evidence here that a full
> boot of my firmware leaves those windows unchanged. 🔴 **The forbidden
> sentence is no closer**: 0.0244 % cannot see a write outside the windows, and
> no `FLR` full re-dump ran. 🔴 **Cycle 6's carded round was VOID and that is
> the control working** — DRAM retained cycle 5's contents across the power
> cycle (`MEM-17`), so four pre-reads came back equal to the flash and the
> bracket moved to fresh addresses. The same seating booted `quietm` to a shell in **7.260 s** and pinged
> 4/4. 🔴 **It also refuted its own byte prediction**: `quietm` printed 849
> bytes where 401 was predicted, because `CONFIG_PRINTK=n` removes `printk` and
> **not** the vendor driver's 97 `panic_printk` call sites (`SPEC.md` `FW-31`; the same
> evening's adversarial pass corrected that number from 274, which counted seven
> `built-in.o` aggregations alongside the leaves inside them). There is still no driver of mine —
> the ping went out through the vendor's `rtl819x`, which is in the vendor's own
> configuration. *(Until today this said "nothing of mine has executed on the
> silicon", which stopped being true at 23:09; the sentence before that said "no
> loadable image", and that stopped being true at 02:20 the same day.)*
> 🔄 **2026-08-31, SIXTH update — seating 8, four power cycles, and the two
> biggest results of `R3` came out of the last thing it still needed power
> for.** 🟢 **`FW-34`'s last row is CLOSED by measurement**: `probe3`'s Group F
> timed 1,024 uncached loads through `0xBD000000` at stride 4 and at stride
> 1,024 and got **the same number both times** — 30,354 ticks, `R = 1.0000` —
> so the memory-mapped SPI window serves a single-word read as its own
> transaction and the instruction-fetch amplification is the `9×` the model
> bounds it at. The same six words compared `0xBFC00000` against `0xBD000000`
> for the first time in this project. 🟢 **The I-cache is two-way by a SECOND
> route, and it is a shape rather than a count**: at the eviction walk's
> boundary point the victims that miss on re-execution arrive as **ten
> `{k, k+256}` pairs with no singleton**, which two-way predicts and
> direct-mapped does not, *while both predict the same number of them*.
> 🔴 **A bit of DRAM changed while the board was off and the block's own seal
> caught it** — the first thing that seal has ever caught — **and a fourth
> power cycle then refuted this session's own explanation of it**: 35.1 minutes
> off, both ends timed, **598 of 22,976 bits = 2.603 %**, so retention falls off
> steeply with time and one bit after two minutes needs no thermal story. The
> thermal story is retracted in place. 🔴 **The flash sentence has not moved**:
> the bracket ran twice on one seating, `1,024` bytes = **0.0244 %**, all
> byte-identical — **and for the first time with an observed vendor-firmware
> boot bracketed between the two rounds** — but no full re-dump ran and the
> vendor firmware executed on this part for ~2 minutes. ⚠️ **Three defects in
> the seating's own card**, two caught before power: a directory named for a day
> the seating did not happen on, an image the card told the operator to upload
> that was never staged, and a `J` row that had lost the ESC-after-jump that
> hands the loader prompt back — the third cost a power cycle.
> 🔄 **2026-09-02, seventh update: an `edit → result`
> iteration ran as ONE COMMAND against the silicon and reported a
> number.** `looprun --mode bench` drove reset → rescue → burn-flag
> read-back → upload → staged-head read-back → boot → assert with **no
> operator gap between any two stages**, and printed **34.74 s** and seven
> assertions. The one that matters is that **the board printed the id the
> build computed** — `RLXFW-ID0=B1434383`, a sha256 over `config/`,
> compiled in and compared by the tool, **typed by nobody**. 🔴 **And the
> audit run in the hour before power found three defects in that tool, two
> of them safety**: it uploaded with the loader's *echo* as its only
> evidence that the burn flag was off (and `C-6`, 量 2026-08-24, is
> the measurement that says an echo and the word at `0x8040D4A0` are two
> sources); it jumped to `0x80500000` without checking
> what was there, on a board whose reset re-stages that address from flash;
> and 🔴 **`S3` had never been connected to `S2` at all**, so the
> `--skip S2,S3` the card called a convenience was **necessary** rather than
> chosen — an explicit `--cell-top` would have worked too, and nobody knew
> there was anything to pass. **Zero flash-write commands and no `FLR`**, decided
> before power, so the bracket stands at **1,024 of 4,194,304 = 0.0244 %**
> and *not one flash byte is written* is exactly as unsayable as it was.
> 🔄 **2026-09-03, EIGHTH update — seating 11, and a sentence in the fifth
> update above expired.** 🟢 **A driver of mine drove a peripheral.**
> `rtl819x-timer` programmed `TC1DATA` and `TCCNR` on the silicon, registered a
> clocksource the kernel listed as `rtl819x-tc1`, was read fourteen times and
> unwound both writes on disarm — twice, the second after a **703-second** arm.
> *(§ 5 above says "There is still no driver of mine"; that stopped being true
> at 21:20. What is still true is narrower and is kept in
> `docs/KNOWN-ISSUES.md`: nothing of mine has driven a peripheral the system
> DEPENDS on — the timer ran at rating 0 so the kernel would not switch to it,
> and `GIMR` bit 9 was read and never written, so no interrupt of mine was ever
> delivered.)* 🟢 **The headline is a ratio with no residual**:
> `ΔTC1 / ΔTC0_total = 1` over three intervals, **integer-exact**, the longest
> 703.46 s / 140,693,532 counts and crossing one 2²⁷ wrap. 🔴 **And the first
> cell refuted a prediction in a way that broke the card's own arithmetic
> before it was used**: under Linux `CDBR` divides by **1000** and `TC0DATA`
> reloads at **2,000**, where the loader left 14 and 142,858 — **the same
> 100 Hz by two different routes**, done by a vendor file still unopened. The
> card hardcoded the loader's constant; using it would have "refuted" the
> headline by 71.4× with the hardware innocent. **It was caught because the
> block ran as three commands split at the card's own decision points.**
> 🔴 **The most valuable result is negative**: `TC1IP` does not latch while
> `TC1IE` is clear ~~, so the driver's whole masked-observation safety strategy
> does not work on this part and `R5-3` must arm the interrupt for real~~.
> 🔄 **2026-09-04, and this correction is one segment late: the observation
> stands, the attribution was retracted by `R5-10` on 2026-09-04 and this line
> was not one of the places that got fixed.** `TCIR` read `80000000` for the whole
> 703 s arm, so **bit 30 — the timer block's OWN interrupt enable — was clear
> too**, and `rtl819x_tc1_arm()` never writes it. `RUNSHEET` `C5` (量 2026-08-24,
> fourteen days older than the question) shows a `GISR` pending bit latching
> **while masked in `GIMR`**, so the mask is not the cause. **The masked-observation
> strategy is intact; nothing had ever set the bit that makes a pending flag happen.**
> 🟢 **2026-09-04 (`R5-3a`): the driver now sets it** — `armirq` writes `TCIR`
> bit 30 alone with `GIMR` bit 9 still clear, which is zero-risk BY MEASUREMENT
> rather than by argument, and ~~`Q11` is testable again~~. `R5-3` is split into
> `R5-3a` (that path) and `R5-3b` (clockevent); which gate is active,
> `PROGRESS.md` says.
> 🔄 **2026-09-04, NINTH update — seating 12, one power cycle, and `Q11` is not
> testable, it is ANSWERED.** 🟢 **An interrupt of mine was delivered, 119,818
> times**, `irq_spurious` **0**, `irq_stuck` **0**, across three
> arm→deliver→disarm cycles at two periods — and the strongest evidence that
> the line is mine is not the count but a three-state reading: `/proc/interrupts`
> had **no line 25** before `reqirq` (`EX-0`), a line `25: … ICTL rtl819x-timer`
> during, and **no line 25** again after `free_irq` (`EX-19`).
> 🟢 **It arrives at the rate the driver programmed, and that is a slope rather
> than a point**: `Δirq_count / Δjiffies` against
> `hz_used / period_cycles / hz_kernel` is 0.0199 % at period 2⁸ and 0.0994 % at
> 2¹², with the measured ratio between them **15.9873 against a predicted 16**.
> A third point, taken with the NIC up and four pings in flight, reads 0.0206 %.
> 🔴 **And the card's own decision cell came out `0|0`, which the card assigned
> to "the timer block needs something not identified" — the assignment was
> wrong and the reading was right.** TC1 had wrapped **16.62 times** with
> `TC1IE` set and `TC1IP` still read 0, because the VENDOR's tick handler does
> `REG32(BSP_TCIR) |= BSP_TC0IP` — a read-modify-write on a register whose `IP`
> bits are write-1-to-clear — a hundred times a second, and it clears every
> pending bit in that register including one belonging to a driver it has never
> heard of. **So a `TCIR` pending bit on this part has a lifetime of at most one
> 10 ms tick, which bounds every single-sample reading of that register this
> project has ever taken.** The duty cycle was written down before the cells
> ran — **0.19 %** at 2²⁰ and **87.20 %** at 2⁸ — and shortening the period to
> 2⁸ made `tcir_tc1ip` and `gisr_tc1ip` both read 1 with `GIMR` bit 9 still
> clear, which also confirms the masked-observation strategy a second time.
> `SPEC.md` `IRQ-08`/`IRQ-09`, `docs/interrupt-map.md` § 3.6.
> 🔴 **One inference of mine was refuted mid-seating by the same register**: I
> read `2: 0 RLX cascade` as "no ICTL interrupt has ever been delivered", and
> after 29,602 of them the cascade still read 0 — a chained cascade does not
> increment its own count. The narrow claim (no line 25 beforehand) survives.
> ⚠️ **What is still true and narrower**: nothing of mine drives a peripheral
> the system *depends on*. `rating` read **0** in all eighteen dumps and the
> time base was `jiffies` throughout, deliberately — that is `R5-3b`.
> **Zero flash-write commands, zero `FLR`, bracket unchanged at 0.0244 %.**
> 🔄 **2026-09-06, TENTH update — seating 13, three power cycles, and the
> sentence two paragraphs above expired at 03:11.** 🟢 **The system tick is
> mine.** `R5-3b-1` registered a `clock_event_device` at rating 300 and the
> tick core exchanged the devices on **three independent cold boots** —
> `ce_registered=1`, `ce_live=1`, **`ce_mode=2`**, **`ce_mode_calls=2`**
> (SHUTDOWN then PERIODIC, which `clockevents_exchange_device()` and
> `tick_setup_periodic()` were read to predict *before the board was
> powered*), and `ce_handler` moving from **`80036D50`**
> (`clockevents_handle_noop`) to **`80036FC4`** (`tick_handle_periodic`), both
> resolved from this image's own `System.map` by `cardcheck numbers` and typed
> by nobody. *(§ 9 above says "nothing of mine drives a peripheral the system
> DEPENDS on — `rating` read 0 in all eighteen dumps and the time base was
> `jiffies` throughout"; the clocksource half of that is still exactly true
> and `rating` read 0 again in every dump of this seating, but the tick is a
> clockevent and it is now mine.)*
> 🟢 **And it is caused, not asserted.** `cereload` changes TC1's reload and
> the kernel's clock follows: six rows, four distinct reloads, **1× to 10×**,
> ratios `1.0000 / 2.0000 / 1.0000 / 4.0000 / 1.0000 / 10.0000`, each landing
> on its prediction to four decimals. At 20000 the shell answered a `cat`
> after a `sleep 5` that took **50 real seconds**, and nothing in the kernel
> could notice. 🟢 **Zero lost ticks** over 258.53 s: `Δjiffies`,
> `Δirq_count` and `Δce_cycles / reload` are **25,853** three ways.
> 🟢 **The best reading was not on the card and cost 90 seconds.** The card
> correctly refused to quote `Δjiffies == Δ(line 25)` as evidence, because
> both timers run at 100 Hz — but `P3-6` leaves mine at 10 Hz and the
> vendor's untouched, so `P3-7` could take the two apart: over **30.10 real
> seconds the vendor's line 13 advanced 3,009, my line 25 advanced 301, and
> `jiffies` advanced 301.** Residual **0**, no address quoted, no question put
> to the tick core.
> 🔴 **Six defects in the seating's own card, all with captures**: a predicted
> line 12 that cannot exist before `ndo_open`; `NET-14` not reproducing;
> an `≈800` whose interval was 11.69 s and not 8 s (`P2-3`/`P3-3`, same work
> in one cell, read **803** twice); four cells that type only `echo` and carry
> expectations they cannot show; a `ping` cell whose interface no cell on that
> cycle brings up; and **PC3 entirely outside the `cells` fence, so
> `32 of 32` is not "the whole seating was checked"**.
> 🔴 **Two findings with reach beyond the block.** This image's `ping`
> **ignores `-c`** — five requests including `busybox ping` directly, all four
> packets — so every `ping -c 4` in this repository has been getting the
> default rather than what it asked for. And **`NET-14` was an id collision**:
> `SPEC.md` `NET-14` is the MII register row, while the `eth4` carried-forward
> item had used the same id since 2026-09-04, **and that device measurement
> was not in `SPEC.md` at all**. It is `NET-25` now.
> ⚠️ **What is still true and narrower again**: the dependence is created by a
> `/proc` write **after userspace exists**. All three boots came up on the
> vendor's tick and were handed over by hand; arming at boot is `R5-3b-2`,
> which needs a different image because `RECIPE_ID` is a digest over `config/`.
> **Zero flash-write commands, zero `FLR`, bracket unchanged at 0.0244 %.**
> 🔄 **2026-09-06, ELEVENTH update — seating 14, ONE power cycle, and the
> sentence directly above expired at 14:48.** 🟢 **The tick is mine from boot.**
> `R5-3b-2` arms the timer from inside the kernel — `arch_initcall` does
> `arm`/`ackip`/`reqirq`, `late_initcall` takes the pre-check window and
> registers the rating-300 `clock_event_device` — and the DoD's **ten boots**
> came out identical to the field: `boot_done=1`, `boot_rc=0`, `ce_live=1`,
> `ce_mode=2`, `ce_mode_calls=2`, `ce_handler` `80036D50` → `80036FC4`, the
> rating-99 negative control registered and never called,
> `irq_spurious`/`irq_stuck`/`ce_hw_bad`/`ce_badmode` all **0**, boot capture
> **1,069 bytes** every time. An **eleventh** boot from a cold power-on is
> byte-identical and is the control, not one of the ten.
> 🟢 **And *before userspace* is proved by an ORDERING rather than by a field**:
> `RLXFW-TA8` — printed the instant `clockevents_register_device()` returned —
> precedes `RLXFW-B10`, which sits immediately before `init_post()`'s branch
> into `/sbin/init`, in the same capture, on all eleven. Byte 887 against 925.
> **No address quoted, nothing asked of the tick core about itself, no shell
> required.** 🟢 Zero lost ticks over **263.73 s** (`Δjiffies` = `Δirq_count` =
> `Δce_cycles ÷ 2000` = **26,373**) and again over **654.76 s** on the cold
> boot (all three = **65,476**), both residuals 0 in both, and the vendor's
> line 13 minus mine stays at **34** across the longer one.
> 🔴 **The most valuable thing here is a REFUSAL, not the success.** Driver 4.0
> refused its own handover on both boots it was given — `RLXFW-TA7=FFFFFFC2`,
> `-ETIME` — with `ce_check_dj=585 / dc=574` **byte-identical on a cold boot and
> a warm one**. Its pre-check window spanned the vendor's NIC driver
> initialisation, over which TC1 delivers **574 of 585** interrupts: 11 short,
> **1.88 %**, against a 1 % tolerance. The same boot at a shell loses **1 in
> 14,385** (0.0070 %) — and there the tick was still the vendor's, so
> `Δjiffies` and `Δirq_count` are two independent sources rather than one
> identity. **The tolerance was not widened; the window was moved.** Widening it
> would have been repairing the instrument to agree with the experiment, and
> what the 1 % refused was a boot whose clock ran 1.88 % slow with nothing in
> the kernel able to notice. `SPEC.md` `IRQ-13`.
> 🟢 **`busybox reboot` does not reset this board and `busybox reboot -f` does**
> — the first signals PID 1, and this image's PID 1 is a shell script — 2.407 s
> from the command to the loader prompt, **with my clockevent driving the
> tick**. That is why twelve boots cost one power press. `FW-37`.
> 🔴 **Two instruments of mine produced false findings and controls caught both,
> before power.** `awk` parses an address like `8001e714` as SCIENTIFIC NOTATION
> (→ `inf`), so a numeric symbol lookup made every such address equal to every
> other; and a `.timing` row is written BEFORE its chunk, so a byte's arrival is
> the last row with `offset <= b` and not the first with `offset >= b` — the
> draft reported a 0.67 s "difference between images" that was one read of
> latency across a 0.63 s silence. `notes/kernel-build.md` § 17.3a documented
> the wrong rule; **its published numbers were then audited and are right**,
> because every landmark happened to fall on a read boundary. `FW-35`.
> ⚠️ **What is still true and narrower again**: the **clocksource** half is
> untouched — `rating` read **0** in all eleven dumps and the system's time
> SOURCE is still `jiffies`; only the *tick* is this driver's. And the loss
> mechanism in `IRQ-13` is **not isolated**: the driver works around it rather
> than explaining it. **Zero flash-write commands, zero `FLR`, bracket unchanged
> at 0.0244 %.**
> 🔄 **2026-09-06, TWELFTH update — seating 15, one power cycle, and the two
> best results came from the card being WRONG.** 🟢 **A `gpio_chip` of mine is
> on `PABCD`**: `RLXFW-G0`…`G6` on ten boots, `G1=FFFFFFDF` and `G2=FF000000`
> as negative controls, **`G4=00000000`** from `gpiochip_add()`, ten boot
> captures **byte-identical at 1,184 bytes against a prediction of 1,184**, ten
> `/proc` dumps agreeing in **27 of 27 fields**, `n_writes` **0** throughout,
> and the write guard refusing on the die at two layers with `-EPERM` and
> `-ENODEV`. 🟢 **`REG-35` goes 讀 → 量**: live `cnr FFFFFF8B` / `dir
> FF000040`, the two values inferred at the desk from the vendor driver's
> compiled form, and the initcall order (`subsys` 4 before `device` 6) is
> **observed in every capture** rather than derived from `System.map`.
> 🔴 **Two card predictions were refuted and both were chased to a cause.**
> `claim` was refused by gpiolib with **`EBUSY`** — measured, by routing the
> write through `cat` so `strerror` printed it — because `tryout 5` had already
> auto-requested line 5 through 2.6.30's `gpio_ensure_requested()`; **the
> card's own arithmetic contained that subtraction and nobody finished it.**
> And the `dat` XOR is `00000060`, not `00000020`, on both boots.
> 🟢 **Chasing that second one produced the largest result of the seating, and
> it was not on the card.** The vendor's whole reset-button path, read out of
> this image's compiled code with no `.c` opened: `rtl_gpio_timer` re-arms at
> `jiffies + 100` — **one second at `HZ = 100`** — blinks bit 6 on the hold
> counter's parity (**the 2 s alternation measured from the other side**), and
> on release does nothing under 2 s, **SIGTERM to PID 1 at 2–4 s** (which this
> image's PID 1 ignores — `FW-37`, the same reason `busybox reboot` without
> `-f` does not reset the board), and at **≥ 5 s writes ASCII `'1'` into
> `default_flag`**, whose only readers here are two `/proc` handlers.
> **Predicted before the press, then measured**: `/proc/load_default` read `0`,
> then **`1`**. `SPEC.md` `FW-40`. 🔴 **This says nothing about the LOADER** —
> where the card drew its line — and no `FLR` ran, so the flash sentence has
> not moved. 🔴 **The card's own `cells` fence is malformed and `0 of 5` was
> on screen before power**, shaped exactly like the correct `0 of 32`; the
> fence is **not** repaired (that would destroy 32 captures' mtime evidence)
> and `check-predictions` gained `N8`/`N9` instead, written after measuring
> the corpus — **54 cards with a usable fence, exactly one breaks either rule**.
> 🔴 **`busybox ash` puts a refused write's payload on the console minus its
> last character**, five lengths, negative control, located to ash by sending
> the same failing write through `cat`; so a mark the board printed can be
> absent from a `grep` (`FW-41`). ⚠️ **What is still narrower**: nothing
> depends on this chip — no consumer is bound, `ALLOW_OUT_MASK` is 0, `.to_irq`
> is NULL — and **which of `PABCD`'s four ports bit 5 belongs to is still
> unmeasured**, which is exactly the claim a seating full of `PABCD` readings
> looks like it closed. **Zero flash-write commands, zero `FLR`, bracket
> unchanged at 0.0244 %.**
> 🔄 **2026-09-08, THIRTEENTH update — seating 16, one power cycle, and the
> experiment built to confirm a number refuted it.** 🟢 **A read-only MTD
> device of mine issues real SPI transactions on this part**, sharing the
> controller with the vendor's driver: `mtd2: 00400000 00001000
> "rtl819x-spi-pio"`, `4194304` bytes through `mtd->read`, `n_state_foreign`
> **0** across **4,115** transfers. Ten boots, **1,318 bytes each against a
> prediction of 1,318**, `RLXFW-ID0=FCE0AF22` every time, `check-predictions`
> **`32 of 32`**. 🟢 **Both declared coin-flips landed on the side read out of
> the vendor's COMPILED driver, against values measured on this device at the
> loader prompt**: `SFCR` **`FFC00000`** (÷16) not `REG-13`'s `3FC00000` (÷4),
> `SFCSR` **`C8000000`** not `D8050000`. `REG-38` 讀 → 量. 🟢 **Ten boot
> captures fall into TWO sha256 values and the whole difference is one bit** —
> `RLXFW-G3` bit 6, the LED the vendor's `rtl_gpio_timer` blinks, so `FW-40` is
> now seen from a second direction. 🔴🔴 **`D3` holds and `D1` is REFUTED.**
> The PIO path and the memory-mapped window at `0xBD000000` agree over all
> 4,194,304 bytes — **nothing had ever read that window under Linux before** —
> but `H601`'s complement digests to `a1673578…100d49eb` where `FLS-24` says
> `a9916fd8…4ce3cba`. Three ways it could have been the instrument are closed
> by measurement: the constant recomputes to `a9916fd8…` from **both** dump
> files under an independent implementation, the driver's own `verify 4096`
> digest is byte-identical to the dump's first 4,096 bytes, and `C1-NG`'s
> injected byte moved the 4 MiB digest while `C1-VF`/`C1-NF` are two
> traversals returning the same value. ⚠️ **The `d1_match` FLAG has no positive
> control here** — it read 0 in every cell — and the refutation rests on those
> three, not on it. 🟢 **Nineteen off-card rungs localised it, and the safety
> question came back right**: `verify 32768` covers exactly `[0, 0x6000)`, the
> whole loader region, and it is byte-identical to 2026-08-16 over all
> **24,576** bytes, where every `FLR` bracket combined had sampled **256**.
> **The first difference is `[0x9000, 0xA000)` — 4,096 bytes, exactly one erase
> sector.** 🔴 **Proven identical 28,672 B (0.684 %), proven different 4,096 B
> (0.098 %), UNDETERMINED 4,153,344 B (99.02 %)** — a prefix digest finds the
> first difference and nothing past it, and `verify` takes a limit with **no
> offset** *(1.1 adds one and a two-level map — the fourteenth update — and
> neither has run, so every figure in this paragraph is unchanged)*.
> 🔴 **So *"not one flash byte is written"* is no longer merely
> unmeasured: it is KNOWN FALSE for the DEVICE over some interval, with the
> write unattributed** and not attributable by this seating (not tonight —
> loader straight to my image ten times, no vendor firmware, `n_writes` 0 in
> every dump, no `FLW`/`EW`/`EB`/burn). What rlxfw can say is narrower and
> measured: **its own driver counted zero writes, and the loader region is
> intact over all of it.** `SPEC.md` `FLS-26`. 🔴 **Five defects were mine and
> four were false stops, none costing a power cycle, and four are ONE root
> cause**: every capture line is CRLF, so `awk`'s field is `"1\r"` and
> `[ "1\r" = "1" ]` is false — **three gates reported STOP or VOID on cells that
> had PASSED, each while printing the correct value beside the wrong verdict**,
> because a carriage return is invisible in display. The fourth gated on a
> **mark** rather than a **field**, and `rlxfw_mark()` interleaves
> character-by-character with busybox ash's echo (`FW-47`, `FW-41`'s family).
> **The replacement self-tests against captures whose answers are known and
> refuses to open the port if its own comparison is broken.** 🔴 `FW-46`: this
> image's busybox has **no `dd`, no `md5sum`, no `--list`**, so nothing on the
> device can digest a byte and the driver's sha256 has no independent on-device
> second source — `FW-26` is the same class one instance earlier, and nothing
> here can ask *"can this image run this command"* before a card is frozen.
> ⚠️ **What is still narrower**: `D2` is untouched (`H601`'s 8,192 bytes are
> skipped by rule, their verification stays in the `FLR` bracket, which did not
> run), and the PIO rate under Linux is a bounded QUESTION rather than a result
> (`FW-48`, `FW-35`'s trap). **Zero flash-write commands, zero `FLR`, bracket
> unchanged at 0.0244 %** — and that last number now sits beside a second
> instrument that measures a different thing and found a difference.
> 🔄 **2026-09-08, FOURTEENTH update — the forty-fourth segment, desk, no
> power, and the two best results came out of captures that were already
> committed.** 🟢 **A checker for `RUNSHEET` lifecycle rule 3 finally exists
> and it fired on its first sweep.** `tools/capdate.py` compares a capture's
> committed `started_wallclock` against the `bench/<date>/` directory it sits
> in — the check rule 3's own ⚠️ named as missing, after three consecutive
> seatings hit it and a human caught all three. 量: **25 directories, 762
> captures**, and **two reds that had been in the record since 2026-08-29** —
> `bench/2026-08-30` and `-30b` hold 37 captures taken entirely on **08-29**,
> in directories git shows were created *before* those captures existed. **The
> directory name was a prediction that the seating would cross midnight, and
> it did not.** Not renamed (40 and 84 references, two frozen cards among
> them); declared by name, with the list swept in both directions.
> 🟢 **`FW-48` goes 推 → 量 with no new reading, because the objection was
> pointed at the wrong term.** *(The old row said a `.timing` row cannot
> separate "data arrived" from "the tool began waiting".)* True of the
> **intercept**; says nothing about the **slope**. Nineteen rungs give
> `t = −2.086 ms + 3.1434 µs × cmp_bytes`, which predicts the 4 MiB traversal
> at **13.18 s** against three measured at **13.276 / 13.325 / 13.432 s** — a
> **64× extrapolation** landing within 1.9 %, with repeatability free from
> `limit &= ~(CHUNK−1)` making six rungs the same experiment. 🔴 **That slope
> is not the PIO rate**; the PIO leg alone is **3.936 s / 4,194,304 bytes =
> 1,040.5 KiB/s**, bracketed on both sides by the driver's own counters
> (`0/0/0` before, `1024/4194304/0` after).
> 🟢 **`rtl819x-spi` 1.1** adds `verify <n> <off>` and a two-level `map`
> (32 × 32 = 1024 exactly) on a **second** `/proc` file, with
> `tools/flashmap.py` as the desk half — it **imports**
> `flashwin.overlaps_forbidden` instead of restating the `H601` rule. 🔴 The
> two-level shape is a hard limit, not a preference: `read_proc_t` `sprintf`s
> into one 4,096-byte page with no bounds check and 1,024 lines is 78 KiB.
> **The point is that every line can be predicted from the dump before the
> board is powered**, which a bisection's rungs cannot — that is why seating
> 16's nineteen `BIS-*` rungs were off-card. It builds (`RECIPE_ID`
> `fce0af22` → **`7b6bfa83`**, `vmlinux` **+33,539** bytes, `1.1` in the image
> once and `1.0` zero times) and 🔴 **nothing of it has run on the silicon** —
> the map's first reading is `R5-6`'s seating.
> 🟢 **`looprun` 1.1**: an `S5c` precondition using **ARP, not ICMP** (the
> loader answers ARP and not ping, so 100 % loss is a *pass* and a ping gate
> would abort every healthy run), and attempt-numbered artefacts so a failed
> run is retried with `--attempt 2` rather than the `--force` that destroys
> the previous attempt's evidence. Ten new cases reach the shape
> `notes/dev-loop.md` § 15 said `--self-test` could not.
> 🔴 **A local census run caught two defects in this segment's own tools
> before they were pushed**: `capdate` and `capfield` printed case lines with
> four leading spaces where `ci-census` parses two, so both would have read
> `ran 0/13` and `ran 0/10` with zero failures — green tools, red census,
> discovered after a push. 🔴 **Two OTHER defects did reach CI, and the pair
> is a finding about CI rather than about them**: run `34156759778` went red
> at `text/test-file-modes` (the executable bit, which CI caught before the
> local gate did) with `census` **skipped**; the next run, with the mode
> fixed, went red at `census` — `RED looprun ran 66/55 … CENSUS-MISMATCH
> 66+0+0 != 55`, the exact line predicted at the desk an hour earlier; the
> third was green. **`census` declares `needs: [text, instruments]`, so a red
> `text` HIDES the census entirely** — the two reds are serial by
> construction, and one push shows one layer. A green run means *this layer*
> is clean. 🟢 **`FW-49`**: `\r\r\n` has **two** sources and
> only one is a wrap — ash's line editor wraps the *echo* at the terminal
> width (33 of 713 classified captures, all `len(sent) ≥ 80`), while the other
> 33 are the loader's own `\r` + `\r\n`; **output is never wrapped**, an
> 88-character `/proc/version` line arriving whole in five captures.
> ⚠️ **What is still narrower**: the scope decision this segment made is that
> 1.1's verbs ride on `R5-6`'s image, so `FLS-26`'s **99.02 % is exactly as
> undetermined as it was** — the instrument exists and has read nothing. And
> 量 2026-09-08: that 99.02 % is not uniform — **180 of 1,024 chunks (17.58 %)
> of the reference dump are entirely `0xFF`**, with a 737,280-byte blank run
> from `0x34C000`. **Zero flash-write commands, zero `FLR`, bracket unchanged
> at 0.0244 %.**
> 🔄 **2026-09-08, FIFTEENTH update — the forty-fifth segment, third on one
> calendar day, desk, no power, and the most valuable result is a prediction
> this segment's own build refuted.** 🔴 **This board runs a 17.5 ms watchdog
> under Linux, kicked every 10 ms, and § 13's `FW-45` had been reasoning from
> "about one second".** 讀 `boards/rtl8196e/bsp/timer.c:75-84` and 量 on the
> artefact at `bsp_timer_init+0xb8`: `WDTCNR = 0x00600000`, a **full-word**
> store so `WDTE` goes to `0x00` rather than the `0xA5` stop pattern, and
> `OVSEL` 3 = 2¹⁸ ÷ ~~14,965,000 Hz = **17,517 µs**. The margin over `HZ=100` is
> **7.5 ms, so not one timer interrupt may be lost**~~ 🔴 **REFUTED ON THE
> SILICON the same night — see the sixteenth update. That divisor is a
> LOADER-state constant; under Linux the watchdog counts at 200,180 Hz and the
> same encoding bites at 1,334.723 ms. Wrong by 76×, and the margin is ~1.3 s.**
> The ~1 s figure is the
> **loader's** `OVSEL=1001`; ~~wrong by 64×~~ **and it was closer than what
> replaced it**. ~~🟢 **The correction makes an older
> measurement worth more**: seating 16's three 4 MiB PIO traversals ran under
> that deadline across ten boots, so **no interrupt-blocked window on that path
> exceeded 17.5 ms** — nobody set out to measure it.~~ 🔴 **That bound is
> 1,310 ms, i.e. 75× weaker**; the sentence is kept struck through because
> "the correction makes an older measurement worth more" is exactly the kind of
> claim that gets quoted onward. 🟢 **And
> `bsp_machine_restart` is itself a bite** (`boards/rtl8196e/bsp/setup.c:114`,
> in no `#if`): `WDTCNR = 0` then spin, with an unreachable `back_to_prom()`
> after it — **there is no second reset controller on this part's software
> path**, so every `busybox reboot -f` this project has run was a watchdog bite
> at `OVSEL` 0 = 2,190 µs, which re-attributes `FW-37`'s 2.407 s and gives
> `CLK-08`'s ≤2.3 ms bound a source-side prediction that fits.
> 🔴 **A `/dev/watchdog` beside a 100 Hz unconditional kick cannot bite**, so
> `CONFIG_RTL_WTDOG=n` is `R5-6`'s precondition and not a tidy-up; the blast
> radius was enumerated first and `bsp_machine_restart` and
> `/proc/watchdog_reboot` both survive it, so `reboot -f` still works and a
> vendor "bite now" instrument remains as an independent control.
> 🔴 **The refuted prediction**: `0xB800311C` references fell **9 → 6**, not
> 9 → 2. Four wlan references survived because they are gated on
> `CONFIG_RTL_8196E` — *which board this is* — and the `CONFIG_RTL_WTDOG`
> wrappers the claim came from live in `drivers/net/wireless/rtl8192e/` while
> the directory that **builds** is `rtl8192cd/`, **measured an hour earlier in
> the same session**. The evidence was in that grep's own output and was read
> past. 🟢 The cost is bounded by measurement: all three surviving kicks are
> `__initcall_rtl8192cd_init6` against this driver's `…_init7`, so they cannot
> feed a guard that does not exist yet. ⚠️ **`R5-6` therefore leaves the
> blind-write ledger's § 4.1** — seven paths, four on the *decision* layer,
> because a decision to delete code cannot be made blind — and
> `driver-diff`'s watchdog section is an informed contrast rather than a blind
> diff. 🔴 **Two gates that exist, work, and are on no path**:
> `CONFIG_GPIO_SYSFS` has been an undeclared config difference since
> 2026-09-06 in `r54b`, `r55b` and `spi11` — including the image seating 16 ran
> — because `kconfig-delta check` is never invoked by `rlxfw-kbuild.sh`; and
> `spec-check`'s `C12` took the **last** dated block of `Next after this`,
> which on the live file has been the **oldest** since 2026-09-07. 🔴 The fix
> is not "take the first" either — at `HEAD~40` that is wrong and the old rule
> is right — because the row is ordered **neither way**, so it selects by date
> now, and `P21` (the same blocks in both orders must give the same verdict) is
> what makes that a rule. **Image `r56c`: `RECIPE_ID` `b417a3e7`, vmlinux
> 4,049,497 bytes, `(NEW)` 0, `kconfig-delta check` green, `rlxfw-marks verify`
> 12 marks and 6 witnesses with zero occurrences in the vendor image.**
> ⚠️ **Nothing of this has run on the silicon**, `FLS-26`'s 99.02 % is
> untouched, and the boot-capture prediction for the next card moves
> **1,318 → 1,424** (spi 1.1's `S8` +10, the wdt's six marks +96), of which
> **106 bytes are predicted and unmeasured**. **Zero flash-write commands,
> zero `FLR`, bracket unchanged at 0.0244 %.**
> 🔄 **2026-09-08, SIXTEENTH update — seating 17, the fourth segment on one
> calendar day, and the paragraph directly above expired at 22:45.** 🟢 **A
> `/dev/watchdog` of mine runs on this part and bites**: ten boots, every boot
> capture **1,424 bytes** against the 1,424 predicted above,
> `RLXFW-ID0=B417A3E7`, `wdtcnr_at_probe` **`A5000000`** — one field with two
> possible values, and the whole proof that `CONFIG_RTL_WTDOG=n` did what the
> blast radius said. `TA5` read `FFFF8D38` against a written `FFFF8D37 ± 2`,
> all ten `ovselN` rows exact **including `ovsel3 enc 00600000`, the vendor's
> own constant computed by a driver written blind**, and `W4` read `00240000`
> where `00A40000` was written — so **`WDTCLR` does not read back on this die**,
> a reading nobody planned.
> 🔴🔴 **THE HEADLINE IS THAT THE FIFTEENTH UPDATE'S OWN NUMBER IS WRONG BY
> 76×, AND THE SAME MISTAKE HAD ALREADY BEEN MADE FIVE DAYS EARLIER ON THE
> REGISTER NEXT DOOR.** Two rungs 32× apart, each carrying its own `mdelay(50)`
> ruler in the same capture (floors **0.517** and **0.868 ms** — so the
> instrument's *"1–16 ms, unmeasured on this host"* is now measured):
> `OVSEL` 3 = **1,334.723 ms**, `OVSEL` 8 = **41,930.599 ms**. The difference
> cancels the offset: `(2²³−2¹⁸) / 40,595.876 ms` = **`f = 200,180 Hz`**, and
> `CLK-17` measured `TC0CNT` under Linux at **200,005 Hz** by a different method
> on a different register in a different seating. **Ratio 0.999.** So
> `CLK-08b`'s 14.965 MHz is a **loader-state** constant exactly as `CLK-17`'s
> 14,286,057 Hz is — Linux reprograms `CDBR` and both slow together — and
> `CLK-08b`'s open residual *what does the watchdog count* is **answered**: it
> counts what the timer block counts. ⚠️ **`RTL819X_WDT_HZ` and every `usec` in
> the driver's table are therefore documented-wrong by 76× and deliberately NOT
> changed**: the table is what `/proc` prints and what a card predicts against.
> 🔴 **The `9−8` test written into the driver was CIRCULAR and `SPEC.md` already
> said so** — 14.965 MHz was solved *from* that difference, and `CLK-08b` 殘留
> reads *"這一格不能靠再量一次逾時解決"*. **Two files in this repository
> disagreed about whether an experiment could succeed and nothing noticed until
> a card had to write the prediction down.**
> 🟢 **`FW-51` 殘留 closes and the answer is the negative one**: the carded cell
> was void (`kickms 3000` against an 83.8 s deadline tests nothing), and re-run
> at `OVSEL` 0 the board reset **both with `wlan0` down and with it up** — so
> nothing else writes `WDTCLR` after `late_initcall`. 🔴 **`FW-53`: neither bit
> 19 nor bit 20 is `OVSEL[2]`** — both *shorten* the timeout below `OVSEL` 0
> (68.647 and 12.336 ms), which no `OVSEL` reading predicts. 🟢 **`FLS-26`
> moves for the first time**: `rtl819x-spi` 1.1's map ran twice on silicon,
> 31 of 32 groups identical = **4,063,232 bytes proven unchanged**, the one
> difference being group 0, where seating 16's bisection had put it.
> 🟢 **Constraint ① became a ratio with no residual**: `Δn_hw_kick` **485**
> against 485.7 predicted across a 12.8 s *armed* SPI traversal, with the
> at-rest 343/14 as its control.
> 🔴 **It cost three power cycles against a budget of one, and both extra ones
> were the same mistake**: a cell whose payload can reset the board, given no
> `--esc-after`. `wedge` bit once and **did not reproduce**; rung 8's window was
> 20 s and the answer 41.9 s — *the same root cause as the headline*, since
> every window on the card came from the constant the card's own third cell
> refuted. The guard added after the second (prove the loader was caught before
> handing the board to `looprun`) fired twice more. 🔴 **`OVSEL` 0 is not
> measurable this way at all**: `prom_putchar` fills a FIFO, not the wire, so
> the reset lands mid-drain — the ladder has **two** clean rungs, not four.
> 🟢 **And the loader prints its own reset cause** —
> `Reboot Result from Watchdog Timeout!` after every watchdog reset, absent
> after every cold power-on — **which has been on disk since 2026-08-24 and
> nothing had read it**. ⚠️ **Zero flash-write commands, zero `FLR`,
> `n_writes 0`, bracket unchanged at 0.0244 %** — but the **vendor firmware ran
> twice**, ~2 and ~4 minutes, because two bites were not caught. 🟢 That
> accident built the first half of `FLS-26`'s attribution bracket: the map ran
> at 22:45, the vendor firmware after it, so **one `map 0` on the next
> seating's first boot closes it at zero cost.**
> 🔄 **2026-09-09, SEVENTEENTH update — seating 18, ONE power cycle against a
> budget of one, fourteen boots, 828 s of chained cells with no operator gap,
> and the best result is a mechanism nobody put on the card.**
> 🟢🟢 **`OVSEL[2]` IS BIT 17, and `CLK-28`'s and `FW-53`'s residuals close
> together.** `biteraw 0x00020000` bit at **2,475.923 ms** = 494,944 counts, and
> with the deficit bounded at `kick_ms × f` = **49,976 counts** only `2^19` is
> admissible — `2^18` would need a negative deficit and `2^20` would need
> 553,632. **The field is non-contiguous and out of order**: `[0]`=bit21,
> `[1]`=bit22, **`[2]`=bit17**, `[3]`=bit18, with bit 19 and `WDTIND` (bit 20)
> sitting *inside* the range and inert for the timeout.
> 🟢🟢 **That bound exists because the card got a column wrong.** § 3.3 tabled
> the arming words without `WDTCLR`; the board printed `00800000` / `00E00000` /
> `00840000` / `00A40000`, because `verb_bite` composes with `kick = 1`. **So
> `bite` clears the counter and `biteraw` does not** — it continues from wherever
> `BOOTGUARD`'s last kick left it. **The control is a factor of ninety** at one
> period: **with** `WDTCLR`, two readings of the *same word* on two different
> boots differ by **1.456 ms**; **without**, three readings spread **131.7 ms**.
> 🔴 **`FW-53`'s conclusion is refuted and what refutes it is
> non-reproducibility.** It read *bits 19 and 20 both shorten the timeout below
> `OVSEL` 0, which no `OVSEL` reading predicts*. They are inert; the shortening
> is the uncleared counter, and the proof is that the two seatings disagree by
> **−68.1 %** and **+638.9 %**. A hardware divider bit does not change value
> between seatings. ⚠️ **And the method's own limit, which the card did not
> know**: 49,976 exceeds `2^15` (32,768), so an un-cleared reading cannot tell
> `OVSEL` 0 from `OVSEL` 1 — bits 16, 20, 21 and 23 stay ambiguous, and
> `kickms 5000` before the `biteraw` fixes it for one extra command.
> 🟢🟢 **`FLS-26`'s attribution bracket closed BYTE-IDENTICAL.** `cmp` on the
> two seatings' `C1-M0` logs: **identical**, and between them the vendor firmware
> ran **twice** — so those two runs wrote nothing to 4,186,112 bytes. `map 1 0`
> then found **TWO** differing units in group 0, not one: `009000` and
> **`00D000`**, the second of which nothing had ever seen, because *a prefix
> digest cannot look past its first difference* — which the card said in advance
> and then predicted "exactly one" anyway. **Ledger: proven identical
> 4,177,920 B (99.61 %), proven different 8,192 B (0.195 %), undetermined
> 8,192 B (0.195 %) — and that is exactly `H601`.** ⚠️ *Proven identical* still
> means *digests agree with the 2026-08-16 dump*: it cannot see two writes that
> cancel, and **no `FLR` ran**.
> 🔴 **Four rungs refute the linear model, and the fourteenth update's own
> `d` is probably an artefact.** `OVSEL` 0/3/8/9 = **163.911 / 1,340.982 /
> 41,910.358 / 84,001.412 ms**; least squares leaves residuals **+3.5 / +32.5 /
> −71.0 / +35.0 ms** against a repeatability of **1.456 ms**. Read against the
> 0 & 8 pair — `f = 200,157 Hz`, `d = +0.20 ms`, which is what the physics
> predicts (`CLK-14`'s +2.07 ms minus `RLXFW-W-GO`'s 12 bytes at 38400) — rungs
> 0, 8 and 9 land within **0.13 %** of their powers of two and **`OVSEL` 3 is
> 2.26 % long**. Seating 17's rung 3 is ~1.8 % long the same way, so
> `CLK-08b`'s `d = +25.179 ms` is most likely **a two-point fit absorbing that
> anomaly into the offset** — which is what a two-point fit does when there are
> no residuals to look at. **`f_wdt` is not a quantity either seating has
> measured.**
> 🔴 **The host-clock hypothesis is refuted and the correction goes the WRONG
> WAY.** `C1-R` — one capture, two `/proc` reads 120 s apart, both timestamps in
> one `.timing` — gives **board/host = −484.3 ppm** where the hypothesis needed
> ~900 ppm the other way. Expressed against that one clock,
> `f_tick = 199,903 Hz` and the watchdog's excess over the timer grows from
> **+0.090 % to +0.138 %**.
> 🟢 **`WDT-1`: seven `/proc` fields, seven hits**, derived on the die at `init`
> from `TC0DATA` and `CDBR` by a driver written blind, every one predicted at the
> desk from registers `TM-1` measured six days earlier. `wdt_hz 14965000` prints
> beside `hz_derived 200000` — **the 76× on one page**, which is why the compiled
> table was deliberately not rewritten.
> 🟢 **The `/dev/watchdog` USER path ran end to end**: the board reset
> **143.563 s** after the device was held open with `sleep 400 > /dev/watchdog`,
> against 143.886 s predicted (**−0.22 %**) — and **the evidence that the open
> reached `WDT_USER` is the bite itself**, because `BOOTGUARD` is fed every
> 250 ms and cannot bite. A consequence, not a field. 🔴 The card's first draft
> used `exec 3>` and `cardcheck` **refused** it: `exec` is on its `ASH_BUILTINS`
> list, whose own comment says the list is 推 and that no card rests on it.
> 🟢 **`console-capture` 1.4's `--until` worked on the silicon first try**, on
> **23 of 27** cells. `C1-M0` returned **3,013 bytes in 13.684 s** where seating
> 17 took **120.106 s** for the same 3,013 bytes. 🔴 **It exists because
> seating 17's own rule does not fix what it was written for**: *take three times
> the prediction* does not cover 76×, and `FW-53`'s bit scan has **no prediction
> to multiply**. 量 `R2-B8.timing`: the console is silent for **41.931 s** while
> a bite is pending, so `--idle` cannot wait for one either.
> 🔴 **The boot-capture control FIRED.** All thirteen are **1,424 bytes** — the
> length half holds exactly — but **three** fields differ from seating 17, not
> two. `RLXFW-TA6`, which is `IRQ-13`'s lost-interrupt count, reads **8 on all
> thirteen** against 11 on nine of seating 17's ten. 推, and the only candidate:
> `vmlinux` grew 233 bytes and moved the vendor NIC init's I-cache alignment.
> **Refuted by a third image whose size changes and whose `TA6` does not.**
> ⚠️ **Zero flash-write commands, zero `FLR`, `n_writes 0`** — and that last one
> was read by an **explicitly declared off-card cell**, because § 6 of the card
> made the claim and no cell on the card tested it.
> 🔴🔴 **THE FREEZE PROCEDURE HAS A HOLE AND THE DESK SWEEP IS WHAT FOUND IT.**
> Gate 2 is `spec-check`, and `spec-check` sweeps **tracked** `.md` files — but a
> card is untracked until the freezing commit, so **the gate that exists to check
> the card cannot see the card**. 量: all five gates passed at 03:11, and the
> sweep at 04:32 reported a `C8c` in the frozen card (§ 1 quotes the `RECIPE_ID`
> formula in prose and the quotation wraps onto a line beginning `|`). It **must
> not be repaired** — `check-predictions` reads the card's mtime and its own
> docstring says fixing even a typo has to make the check fail — so it is
> exempted **by name** in a new `C8C_EXEMPT`, mirroring `C10_EXEMPT` for
> `bench/2026-08-25b`, with **`T13b`** as the control that re-runs the check with
> the exemption off and goes red if the file is ever clean. `spec-check` 54 → 55
> cases, its 21 mutants still all killed. *(The fix for the hole itself is
> carried forward: gate 2 has to run on a tree where the card is staged.)*
> 🔴 **And ONE unclosed backtick produced EIGHTY reported defects — the third
> time, and the second time the message alone identified it.** A `` ` `` I left
> off `f_tick = …` in a `SPEC.md` patch shifted the pairing for the rest of the
> file: **79 `C9` + 1 `C10`**, all of them artefacts, all of them gone when the
> one tick went in. `f451f1f` was 49 and `837cd22` was the second.
> 🔴 **I also repeated this file's own `EXIT CODE: 0` incident.** Every
> `spec-check rc=0` reported after the freeze came from
> `bash -c '… ; echo "rc=$?"'` through the Bash tool, and the row above says
> `$?` is expanded in the **outer** shell there — so those were not
> measurements. The freeze-time one WAS real, because it ran inside `freeze.sh`.
> **The rule is not "be careful with `$?`", it is "read an exit code only from
> inside a script file", and this segment proves it by having done both.**
> > **Which gate that is, `PROGRESS.md` says** — this
> file does not restate it, because one piece of state has exactly one owner
> and a gate id copied to a second place goes stale there.
> Conventions for files that do not exist are not written
> here; they go in when the file appears. Where this contradicts the repo, the
> repo wins and this file is wrong.

## Where things are

|                   |                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **`PROGRESS.md`** | sole owner of *where I am* — active gate, active step, blockers, carried-forward. **Read it first, every session**          |
| **`plan/`**       | gitignored, always present locally. Index: `plan/README.md`.  Whole plan: `plan/.md`                                        |
| **`upstream/`**   | the RE project, submodule pinned at `4d3ff26`, **read-only** — that pin is the whole credibility of R9's differential proof |
| **`$FWRE_WORK`**  | `/home/key/fwre-work` — every binary, shared with `../router`. This project's output goes in `$FWRE_WORK/rebuild/`          |
| **`SPEC.md`**     | every number this project holds about the device — part numbers, register readings, addresses, budgets — each with a mark for where the **value** came from and a separate mark for where its **name** came from, and a link to the file that owns the finding. **An index, not an owner**: a finding or a correction lands in the owning file first and in `SPEC.md` in the same commit. Written in Chinese |

**A gate is not a session.** R6 is 35 work-segments, about a month. A session is
one step inside a gate. When I say "do R5", ask which driver.

## How to work here

**You build the instruments, I read the dials.** When I state a finding, do not
agree — name the tool that could be lying and the second source that settles it.
Agreeable understatement is how a claim reaches a hostile reader undefended.

- **Every sentence about this machine is marked**: *measured on the device*, *read
  out of the code or the dump*, or *inferred, pending a measurement*. Mixed
  together they are worth neither.
- **No register value enters code on one source.** datasheet → SDK header →
  `devmem`; two must agree, or it is recorded as undetermined.
- **Nothing counts as a result until its refutation condition is written first** —
  what outcome would have proved it wrong.
- **A tool reporting `0` is making a claim.** Every sweep needs a positive control;
  a tool that cannot fail proves nothing.
- **Uncertain is a valid answer** — follow it with the experiment that decides it.
  Five minutes at the bench beats a paragraph of reasoning.
- **Propose before writing** anything over ~50 lines: the approach, and where it
  will fail. **Label estimates as guesses** — nothing here is calibrated yet.
- **Negative results stay in place.** So does the record of being wrong.

## Never

|                                                        |                                                                                                                             |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| write flash                                            | mainline is zero-write through R9. A write needs my explicit yes                                                            |
| touch `0x000000–0x005FFF` or `0x006000–0x007FFF`       | loader — bricked is unrecoverable, there is no spare. `H601` — this unit's MAC and radio calibration, not restored by reset. 🔄 **2026-08-30, twice in one day — and the morning's sentence was too strong.** *(It read: “nothing has ever CHECKED the second one”.)* True of **rlxfw's own** `G8a`/`G8b` bracket; **false about the device** — `upstream/BENCH-LOG.md` holds seven baselines of `H601`'s first 4 KiB across three days, five power-ups and two flash writes, and it is the check that **caught** the 2026-08-17 write. This file's own rule is that where it contradicts the repo, the repo wins. **Evening: rlxfw's bracket now checks it too.** `bench/2026-08-30c`/`d` read `0x006000`–`0x0060FF` on both power cycles and both were byte-identical to the 2026-08-16 dump — **256 of `H601`'s 8,192 bytes, 3.1 %**, and the other 96.9 % is still unchecked. 🔄 **2026-09-01 (seating 9): a THIRD reading of the same two pages, and this time it answers a different question — whether a *scripted* reset writes them.** `bench/2026-09-01/T-flrh`/`T-flrc`, after one cold boot and twenty `J BFC00000` watchdog resets: both byte-identical to the 2026-08-16 dump, with the read-backs outside the repository and **four RAM destinations no `FLR` here had ever used**, so `MEM-17`'s retention path could not pre-fill them. The reach does not move. 🔄 **2026-08-31: 512 bytes, 6.3 %, and the other 93.7 % is still unchecked** — `bench/2026-08-31*` add `0x006400`, the canary page, on both power cycles; all four readings byte-identical to the 2026-08-16 dump. 🔴 **And a capture of one of these windows nearly entered the repository**: the card writes `FLR` PRE-reads under `bench/` because a pre-read is *expected* to be garbage, and when DRAM retention made that false two files held this unit's MAC. Untracked, moved, nothing in history — but **a containment rule whose correctness depends on the experiment coming out the expected way is not a containment rule**, and the card template still has it. ✅ **2026-09-03: an enforcer now does, and the template was still not edited.** `tools/cardcheck.py` `A19` reports an `FLR` typed inside a `--send`, which is the bypass that reaches `console-capture.py` without `flrbracket run`; `A20` excuses the two frozen cards that do it **by name**, not by date; `A21` is the control that says it is a guard and not a blanket; and `B10` sweeps the corpus **in both directions**, so the allow-list cannot accrete unreported. 量 on its first run: 50 cards, 2 type `FLR`, list exact. The morning's reading, which is what made that bracket exist: 量: `RUNSHEET` §B3's `G8a`/`G8b` flash bracket samples 256 of the loader region's 24,576 bytes, 256 bytes of the `cr6c` header — which no rule forbids writing — and **0 of `H601`'s 8,192**. Six days of write-ups called those *"the two regions that would change"*, and neither of them was the one that cannot change back. `bench/2026-08-30c/PREDICTIONS-B5-block2.md` §8 adds it; its capture may not enter this repository and **not even its sha256 may** (with the window otherwise known, a digest is a 2^24 search for the MAC), which `tools/flashwin.py` enforces rather than remembers. 🆕 **2026-08-31: the OTHER half of that rule now has an enforcer too, and it is the half the template kept getting wrong.** `flashwin` governs what may be *printed*; nothing governed *where a capture of a forbidden window may land*, and on 2026-08-31 two files inside this repository held this unit's MAC because the card wrote `H601` pre-reads under `bench/` on the assumption they would be garbage. `tools/flrbracket.py`'s `run` refuses, **before it opens the port**, to write the read-back of an `H601`-overlapping window anywhere inside this repository, and **the pre-read anywhere inside it at all, whatever the window is** — a pre-read is a `DW` of the RAM destination before the `FLR`, so its content is decided by what was last written there, and `MEM-17` measured DRAM keeping a previous cycle's `FLR` output across a power cycle. *(The first version of this row keyed both on the flash source; an adversarial pass showed that is the 2026-08-31 incident with the roles swapped.)* The line is drawn at **content, not mention**: the `FLR` echo capture holds addresses and no flash bytes, which is why `bench/2026-08-31/W-flrh.log` names `00006000` and is correctly committed. 🆕 **2026-08-31: a THIRD enforcer, and it asks the question the other two cannot.** `flashwin` governs what may be *printed*; `flrbracket` governs where a *bracket's* read-back may land; both act when a file is produced. **`flashwin scan` asks whether a file this repository has ALREADY COMMITTED holds forbidden content** — by the bytes, not by the shapes an address takes, with the probe set filtered on the reference side. 量 on its first sweep: rlxfw's own tree is **CLEAN over 1,381 files** (`--sweep . --exclude upstream`), `K-P3` included; the default `--sweep .` reads **1,683** and reports **1 HIT** — `upstream/BENCH-LOG.md:2557`, sixteen bytes of `H601` as a hexdump line. ⚠️ **`leakscan` does not name that line (it names 22 hit rows over 18 other lines of the same file); `audit-bench-log` does, on its topic keyword `H601` (the flash bytes there ARE the ASCII `H`,`6`,`0`,`1`) among 183 hits, exiting 0** — so neither identifies it as forbidden CONTENT, which is the narrower and correct claim. It does not move `FLS-22`'s decision and it is not meant to; it is the sentence *nothing checks the committed record* that stops being true |
| build with `-march=mips32`                             | the load delay slot is architecturally exposed; mips32 miscompiles **silently** — no fault, no warning, just wrong values. 🆕 **2026-09-04 (`R5-10`): a second reason, and this one is NOT silent.** 量, the rsdk assembler: `mflxc0`/`mtlxc0` — the instructions `arch/rlx` uses to mask a LOPI interrupt, and the only way to reach `ESTATUS`/`ECAUSE`/`INTVEC`/`CCTL` — assemble at `rlx4181`, `rlx4281`, `rlx5181`, `lx5280` and `rlx5281`, and are **rejected** at `lx4180` and at `mips32`. So the ban is not only about wrong values; at `mips32` the interrupt-mask primitive does not build. 🔴 **And they are not `mfc3`**: as built they are `0x40620000`/`0x40e20000` — COP0's opcode with MIPS-unassigned `rs` 3 and 7 — while `mfc3` is `0x4c020000`. Do not carry the 2026-08-29 CP3 result across. `docs/interrupt-map.md` § 1.1   |
| write asm under `.set reorder`                         | you cannot know what the assembler filled in. `noreorder`, fill every delay slot yourself                                   |
| measure the ISA or a CPU hazard under Linux            | the vendor kernel emulates `ll`/`sc` (and `sync`, as a no-op), so you would measure the kernel. Bare metal only. 🔄 **2026-08-27: the reason was half wrong and is narrowed.** This row said "and the FPU" — **there is no FPU emulator in this kernel at all**: `arch/rlx` has no `math-emu`, and `do_cpu` gives `SIGILL` for any coprocessor but 0. `simulate_llsc` alone is enough, so the rule does not move; only its reason does. `CPU-47` |
| edit vendor source by hand, or apply a patch to `src-vendor/`             | 🆕 **2026-08-29: rlxfw patches Realtek's source for the first time.** 🔄 **2026-09-01: there are TWO sanctioned ways, and this row said one.** A row in `config/rlxfw-marks.tsv` is one of them and it is the narrow one — `rlxfw-marks.py` refuses any insert that is not `rlxfw_mark("TAG");`, `rlxfw_markx("TAG", expr);`, `obj-y += NAME.o` or the mark header include, on the stated ground that *an arbitrary statement here would be a patch with no reviewer*. The other is a patch in `config/host-compat/`, applied by `rlxfw-kbuild.sh`, which **stops the build if it does not apply**; `0001` predates this row (2026-08-28) and `0002` (2026-09-01, `P4a`) is what made the omission matter. ⚠️ That directory's name is now narrower than its contents — the driver describes it as *every source change to the vendor tree*, which is the accurate scope — and a rename is carried forward rather than done in the session that widened it. 🔄 **2026-09-02: two more, and they pull the name in OPPOSITE directions.** `0004` is host compatibility in the strictest sense — a 2009 kernel's `\#` escape is a no-op under GNU Make 4.3, so every `.cmd` file is truncated at a bare `#` and every build is a full rebuild — which is the same shape as `0001` and perl 5.22. `0003` is not: it is about when kbuild rewrites a generated header. **So the directory now holds two patches its name fits and two it does not**, and the rename is still carried forward. 🔄 **2026-09-06 (`R5-4`): a FIFTH, and it is the third the name does not fit.** `0005` adds `select ARCH_WANT_OPTIONAL_GPIOLIB` to `arch/rlx/Kconfig` so a `gpio_chip` can be registered at all — 量 `FW-38`, with `CONFIG_SWAP` as the positive control in the same run. **Two fit the name, three do not.** The 594-object figure below was taken with FOUR declared and has not been re-taken. 量: with all four declared, a fresh stage builds 594 objects and a no-op `make` costs 2; the product moves by 4 bytes of 3,968,240, all of them `RLXFW_SRC_ID`, because `RECIPE_ID` is a digest over `config/` and `config/` gained two files. `notes/incremental-build.md` **The rule below is unchanged: never by hand, never inside `src-vendor/`, always to a staged tree.** Every inserted line is a row in `config/rlxfw-marks.tsv` with a reason, applied by `tools/rlxfw-marks.py` to a **staged** tree — the tool refuses any path under `src-vendor/`, and the anchor must occur **exactly once** or it refuses rather than picking one. Files of mine live in `config/rlxfw-src/`, mirroring the staged layout. ⚠️ **`check` reads the tree and `verify` reads the built artefact, and only the second one can catch a mark that compiled and is not in the image** — measured, on the first run. 🆕 **2026-09-02 (`R5-0`): a staged tree has THREE states and the third is the one that carries the rule.** `apply` used to refuse any second run outright, because applying twice emits the mark twice and a doubled mark reads in a capture as a boot loop — so `--keep --marks` could not run at all, which is what `INC-1` had to measure. `--if-needed` splits that: a **clean** tree is applied to, a **fully applied** one is a no-op, and a 🔴 **partially applied one is REFUSED** — some marks present is a tree that builds and is not what the table describes. The row's rule does not move: `A20` requires plain `apply` to still refuse a marked tree, so `A4` is bypassed only when asked for, never by default |
| commit the datasheet, a flash dump, or a vendor binary | one is someone else's property; the others identify one physical device                                                     |
| open `$FWRE_WORK/disclosure/`                          | unsent vulnerability reports, mode 600                                                                                      |
| ~~write `RLX5281`~~ ✅ **lifted 2026-08-27**                | 🔴 **The `PRId` assignment table this row named arrived, and it was in a GPL drop this project already had.** `arch/rlx/include/asm/cpu.h` maps `PRID_IMP_RLX4181 = 0xcd00`; `PRId = 0x0000CD01` (量) has bits 15:8 = `0xCD`, so the core is **`RLX4181`, revision 1** — and **`RLX5281` is `0xdc01`, now positively excluded rather than merely unproven**. Write `RLX4181`, marked **讀**, with `PRId` itself still 量. Three weaknesses travel with it and must not be dropped when it is quoted: the three drops are **byte-identical** in that header (one source, three copies), **no code in the port reads the table**, and its own encoding breaks for `0xdc01`/`0xdc02`. `notes/vendor-kernel-isa.md` §5. **`RLX5281` stays unwritable, for the opposite reason from before.** *(Original row: `R1-gate` closed 2026-08-26 and did not name it … what lifts it is a `PRId` assignment table, not another seating.)* |

## Environment

- **`usbipd` has nothing to attach to unless a WSL process is already running.**
  Measured 2026-08-24: with the distro idle, `usbipd attach` fails with *there is
  no WSL 2 distribution running*, and 🔄 **an attachment already made can drop
  while the distro is still running** — it died between two tool calls mid-session
  and took `/dev/ttyUSB0` with it. **That drop was not distro idle**, which is
  what this line said until 2026-08-25: `uptime` ran continuously through it, and
  what left was the **CP2102**, off the Windows USB bus after **7 min 24 s of pure
  console idle**, with `usbipd list` moving the busid out of *Connected*. Root
  cause **undetermined**, and none of the three candidates has been ruled out:
  usbip socket transient, USB selective suspend not waking, a loose connector.
  🆕 **2026-08-29: that signature is not specific, 量.** A deliberate
  `usbipd detach` takes the busid out of *Connected* too — for about a second,
  while Windows re-enumerates the device — so a `usbipd list` run immediately
  after a detach reads **exactly** like the drop. **Re-read before concluding
  anything from one listing.** The same day the CP2102 was also absent from
  *Connected* on **first insertion**, with no COM port on the Windows side at
  all, and returned only after a re-seat: consistent with the loose connector
  and separating nothing, so the three candidates stand.
  Start a long-lived process first and leave it running:
  `wsl -d Ubuntu-24.04 -- sleep 36000` in the background — **that is for the attach
  step and is not a fix for the drop above; do not record it as one.** **And the busid is not
  stable** — the USB GbE moved `3-4` → `2-4` across one re-enumeration the same
  day, so re-read `usbipd list` every time rather than reusing the number.
- **The Bash tool is Git Bash, not WSL.** `-lc` mangles the command: `$VAR` is
  stripped and a leading `/` is MSYS-translated (`bash /mnt/c/x.sh` became
  `bash C:/Program Files/Git/mnt/c/x.sh`). 🆕 **2026-08-30: "stripped" is the
  kind half. `$?` is EXPANDED, in the OUTER shell**, so
  `bash -lc 'cmd > f; echo "rc=$?" >> f'` records the outer shell's status and
  not `cmd`'s — 量, it wrote `rc=0` for a suite that had exited 1, and the
  wrong number is worse than an empty one because it reads as a measurement.
  🔴 **2026-09-06 (seating 15): it did the worst version of this — it made a
  VERIFICATION GATE read green, and the green was pushed.** `spec-check` was run
  as `… > f 2>&1; echo "EXIT CODE: $?"`, printed **`EXIT CODE: 0`**, and was
  believed; the tool was exiting **1** on a real `C5` finding, which CI then
  caught. ⚠️ **The same run also shows the second half of the trap**: reading
  `spec-check | tail -2` shows the *table sweep's* ok line while the file's own
  findings sit above it, so **a tail is not a verdict**. Both halves have one
  fix: put the command in a script file, run it by path, and read `rc=$?` there.
  It also swallowed a whole run: a `nohup … &` inside `wsl -- bash -lc` dies
  with its parent, and a progress check written
  `tail -6 f 2>/dev/null || echo "still running"` cannot tell *running* from
  *never started* — that is this project's own "a tool reporting 0 is making a
  claim", in a one-line shell check. **Feed the script over stdin instead** —
  nothing in the body is touched, and shell variables work:

  ```
  wsl -d Ubuntu-24.04 -- bash -ls <<'EOF'
  … ordinary shell, literal paths, $VAR all fine …
  EOF
  ```
  🔴 **2026-09-08: and a heredoc terminator ENDS the command, so a `&&`
  written after it chains nothing.** 量, on this segment's own closeout: a
  patch script was written as `python - <<'PY' … PY` followed on the next
  line by `git add -A && git commit …`. Those are **two commands**. The
  script hit its own anchor check, printed a refusal and exited 1 — **and the
  commit ran anyway**, producing a commit whose message described a change the
  commit did not contain. That is this file's own `EXIT CODE: 0` incident with
  the roles swapped: there a failure was reported as a success, here a failure
  was reported correctly and nothing downstream read it. **A step whose
  failure must stop the next one has to be on the same command line, or the
  next one has to test for its output.**
  🆕 **But do not nest a second heredoc inside that one.** Measured 2026-08-26,
  three times before it was believed: a `python3 - <<'PY' … PY` inside the outer
  heredoc **loses one level of backslash**, so `\\t` reaches Python as `\t` and
  `"…1 \\\n"` becomes a line continuation that eats the newline. The symptoms are
  a `SyntaxWarning: invalid escape sequence` and an `assert … in s` that fails on
  a string you can see in the file. It also breaks the outer heredoc outright if
  the inner body contains the outer terminator. **Write the script to a file with
  the Write tool and run it by path** — `python3 /mnt/c/…/scratchpad/x.py` — which
  has no quoting layers at all.
  🔄 **2026-08-27: it is not the nesting. ONE quoted heredoc from the Bash tool
  loses a backslash level, and the note above blamed the wrong thing.** 量 with
  `od -c`, which is the instrument to use because everything else in the path
  re-escapes: send `re.compile(r'(?<!\\)\|')` through a single `<<'EOF'` and the
  bytes that reach disk are `re.compile(r'(?<!\)\|')`; `printf 'a\\b'` arrives as
  `printf 'a\b'`. It cost two `re.error: missing ), unterminated subpattern` in
  one session, and once it went further than an error — `cat > f <<'EOF'` wrote
  the corruption into a committed file. ⚠️ **Root cause undetermined**: the tool's
  own command marshalling and the shell are both in the path and this measurement
  does not separate them. **The workaround is unchanged and it is the whole
  point** — Write the file, run it by path. 🔴 **And never `open(path, 'w')` in a
  script that can raise before it writes**: `open()` truncates immediately, so a
  `NameError` one line later leaves the file at zero bytes. It emptied
  `PROGRESS.md` on 2026-08-27; `git checkout --` got it back because it was
  committed. Build the whole string first, write to `path.tmp`, `os.replace`.
- 🆕 **Running a vendor binary is not a read-only act, and `--version` is not a
  safe way to ask one what it is.** Measured 2026-08-28: a census that ran every
  executable in the three rsdk `bin/` directories with `--version` deleted
  **2,580 tracked files** from a pinned vendor clone — mostly regular files
  under `config/uclibc/`, not the symlink farm the first write-up said —
  rewrote four tracked files and left seventeen ignored build products — because `rsdk-linux-config`
  is a statically linked i386 ELF that runs `make` in the tree it lives in. It
  also wrote an `offset.tmp` into **this repository's root**, which is a place no
  vendor-tree check watches. It was recoverable only because the trees are clones
  pinned at known shas. **Wrap anything that executes a vendor binary in
  `tools/vendor-tripwire.sh`, and run it from a scratch directory**, never from
  the repo root and never from inside `src-vendor/`.

- **Binaries and vendor source trees never live under `/mnt/c`.** Measured
  2026-08-23: DrvFs *keeps* symlinks, but reports every file as `777`, so git sets
  `core.fileMode=false` and stops seeing mode changes at all; and NTFS is
  case-insensitive, which silently drops **254 files** from the vendor kernel trees
  (`xt_CONNMARK.h` against `xt_connmark.h`). On this project part of the finding
  *is* filesystem metadata. `src-vendor/` is a symlink into `$FWRE_WORK/rebuild/`.
  - **The same blindness quietly loses the executable bit on new tools.** With
    `core.fileMode=false` a file is recorded with whatever mode `git add` happened
    to capture and nothing ever corrects it: **7 of the first 10 files in `tools/`
    drifted to `100644`** while the three oldest stayed `100755`. Every tool here
    carries a shebang, so every tool is recorded `100755`; the fix for a drifted
    one is `git update-index --chmod=+x <path>`, and `tools/test-file-modes.sh`
    reads the **index** — the thing DrvFs cannot lie about — in both directions.
  - 🔴 **2026-09-08: the action that RE-INTRODUCES the drift is
    `git restore --staged .`, and nothing had written that down.** 量, on the
    forty-fourth segment's closeout: three new tools were added and set
    `100755` by hand; the index was then reset to split one staged change into
    three commits; that reset made the three files **untracked again** — they
    were not in `HEAD` — so the re-`add` was a *first* add and recorded
    `100644`. **The mode was right, then right in a commit, then wrong**, and
    `test-file-modes.sh` caught it after the push. Setting the bit before
    splitting a commit is not enough: **check it again after any
    `git restore --staged` that touches a file `HEAD` does not have.**
- **Session working files do not go in WSL's `/tmp`.** Measured 2026-08-23: the
  distro restarts between tool calls (`uptime -s` moved forward mid-session,
  `uptime -p` read "up 0 minutes"), and `/usr/lib/tmpfiles.d/tmp.conf` carries
  `D /tmp` — a capital `D`, so `systemd-tmpfiles-setup` **empties it at every
  start**. It is not a tmpfs; the wipe is deliberate, not a side effect. Derived
  artefacts go in `$FWRE_WORK/rebuild/`, which is where they belong anyway.
- 🆕 **Every bench command runs `/usr/bin/python3`, never `python3`.** Measured
  2026-08-29 (and the tool has said so since 2026-08-24, in a message nothing in
  this file repeated): `python3` on this host resolves to
  `~/.venvs/thermal/bin/python3`, which has **no `pyserial`**, so
  `console-capture.py` refuses. It refuses with the reason rather than a
  traceback, which is the only thing that made it a two-second problem instead of
  a bench-time one. **And a 3-second capture with the board OFF is a free
  pre-flight**: 0 bytes, and the tool splits that into three causes — the
  adapter, the port, or the board — before a power cycle is spent.
  🔄 **2026-09-02: the resolution above is true in a LOGIN shell and not
  otherwise, which makes the trap intermittent rather than constant — and
  an intermittent trap is the worse kind.** 量, with the control run beside
  it: `wsl -- bash -lc 'command -v python3'` gives
  `/home/key/.venvs/thermal/bin/python3`, while `wsl -- bash -c` and
  `wsl -- bash <script>` both give `/usr/bin/python3`, because the venv
  reaches `PATH` through a login profile. **So a script that works when run
  one way breaks when run the other, and neither run tells you which you
  got.** The rule does not move: write `/usr/bin/python3` and the question
  never arises.
- 🆕 **Windows-side Python is cp950 here, and it breaks in BOTH directions.**
  量 2026-09-09, twice in one segment. ① `subprocess.run(..., text=True)`
  decoding a tool's UTF-8 output raises `UnicodeDecodeError: 'cp950' codec can't
  decode byte 0xe2` — a `gh run view` whose display title held an em-dash was
  enough. ② `print()` of any emoji raises `UnicodeEncodeError`, and **that one
  is the dangerous direction**: it fired inside a patch script that had already
  rewritten its target in memory and had not yet written it out, so a slightly
  different script would have left a half-applied edit. 🟢 It did not, because
  the write is `build the whole string, write to path.tmp, os.replace` — the
  same rule this file already carries for `open(path, 'w')`. **Pass
  `encoding="utf-8"` to every `subprocess` capture and put
  `sys.stdout.reconfigure(encoding="utf-8")` at the top of every script run by
  `C:\Program Files\Python310\python.exe`.** WSL's `/usr/bin/python3` has
  neither problem, so a script that works one side can fail the other with no
  code difference at all.
- 🆕 **`gh` exists only on the Windows side and `jq` only inside WSL, so no
  single shell can run both — and a tool that needs one runs where that one
  is.** 量 2026-09-07: `tools/citime.py` shells out to `gh`, so running it
  under WSL dies with `FileNotFoundError: [Errno 2] No such file or directory:
  'gh'`; it runs under `C:\Program Files\Python310\python.exe`. The reverse
  holds for anything wanting real `jq` (WSL has 1.7; `gh --jq` is a reduced
  builtin that rejects `\(...)` interpolation). 🟢 **That split is what makes
  a `citime` cross-check genuinely independent** — the `gh` JSON is produced on
  one side and the arithmetic redone by `jq` on the other, sharing no code and
  not even a language. ⚠️ **This was true on every previous segment and was
  written down nowhere**, which is why it cost two failed invocations before
  being noticed.
- ✅ **`console-capture.py` refuses a capture with neither `--seconds` nor
  `--idle`, and records both in its metadata — fixed 2026-08-30.** *(Until then
  such a capture never returned: both default to `0.0` and the read loop broke on
  neither, so `timeout -s TERM 8` gave `rc=124`. A SIGTERM kill loses
  `.meta.json`; the `.log` and `.timing` survive, flushed per chunk.)*
  **Every capture command still carries a terminator** — the guard makes that a
  refusal rather than a habit, and §B5's card now carries one on all fifteen of
  its capture rows. 🔴 **Where the guard sits was measured, and the obvious
  placement is wrong**: it goes after `_check_send` and before the port is
  opened. Of the four terminator-less invocations in
  `tools/test-console-capture.sh` only **one** changes (`P4`, the 127-character
  line, the only one whose assertion is that the run reaches the port); the other
  three are refused inside `_check_send` first. 🔄 **2026-08-30, later the same
  day: this bullet said *"`N21` pins both sides with one command"* and that is
  false.** `N21` sends **127** characters — a length `_check_send` **accepts** —
  so it gets the terminator refusal whether or not the guard sits above
  `_check_send`; that side was held only by `N4`/`N7`/`N8` happening to carry no
  terminator, which is coverage by accident. **`N29` sends 128 and requires the
  LENGTH refusal**, and `N30` pre-creates the output files and requires the
  TERMINATOR refusal ahead of the overwrite one — those two pin the position,
  one edge each. Found by `tools/test-console-capture-mutants.py`: **25 mutants
  of that guard, TEN alive against the forty cases**, in four classes the cases
  could see only one instance of each. Suite 40 → 46, 25/25 killed.
  🔴 **And a green suite is a claim about the suite**: the mutant runner is now
  the thing that says the cases work, and it runs in CI.
  ⚠️ **`tool_version` deliberately did not move**: it owns *what the
  instrument wrote to the port*, and nothing new goes on the wire — the
  **presence** of the `seconds` key is what dates a capture instead.
- 🆕 **PowerShell has its own four traps, and two of them make a check silently
  useless rather than noisy.** *(①–③ 量 2026-09-01; ④ 量 2026-09-08.)*
  ① `Get-Date -Format`
  eats format letters **inside literal text**: `"Windows: yyyy-MM-dd"` printed
  `Win1ow20:` because `d` and `s` are specifiers. ② `<long command> |
  Select-Object -Last N` **buffers the whole pipeline** — a 25-minute suite
  showed nothing until it ended, so there is no progress to watch; run it in the
  background, or let it write files and read those. ③ `wsl -- bash -c "…$?…"`
  dies with *unexpected EOF* on nested quotes. **Same fix as the Bash tool's:
  write the script to a file and run it by path** — `wsl -d Ubuntu-24.04 --
  bash /mnt/c/…/x.sh`.
  🆕 ④ **`| Select-Object -First N` KILLS the native process when `N` is fewer
  lines than it produces, and the exit code becomes `-1` — which the tool
  surfaces as `255` and which is indistinguishable from a real failure.** 量,
  the same command twice: `citime.py stats 2>&1 | Select-Object -First 3`
  → `rc=-1`; `… | Select-Object -First 100` (its output is ~17 lines, so nothing
  is truncated) → `rc=0`; and standalone with no pipe, `rc=0`. **The truncation
  is the cause, not the tool.** 🔴 **It fails in the safe direction — it invents
  a red and can never invent a green — but it is still a check reporting
  something that is not true**, and this file's own `EXIT CODE: 0` incident is
  the same class with the sign flipped. `-First N` is fine for reading *output*;
  **never read `$LASTEXITCODE` through it**. Run the command bare (or redirect to
  a file) when the exit code is the thing being measured.
- 🆕 **The `Monitor` tool's command runs in the Bash tool's shell — Git Bash —
  so a `/mnt/c/…` path there is not a missing file, it is a DIFFERENT
  filesystem's name for nothing.** 量 2026-09-07: a monitor watching a
  background WSL sweep was written with the `/mnt/c/…` path its own producer
  used. In Git Bash that path does not exist, so `grep -c` returned **0** and
  `pgrep -f` found nothing, and the monitor's two terminal branches — *no
  events yet* and *the process is gone* — **collapsed onto the same reading**.
  It reported `sweep process gone, done=0/59` while the sweep was at 27/59 and
  running. 🔴 **The coverage rule was followed and did not help**: both
  branches were written, and both read the same unreachable path. **A watcher
  needs a startup assertion that it can SEE its input** — `[ -f "$O" ] || {
  echo REFUSED; exit 1; }` — because *a tool reporting 0 is making a claim*
  applies to the watchdog too. Git Bash's form is `/c/Users/…`; WSL's is
  `/mnt/c/Users/…`; **the producer and the watcher are in different shells and
  need different spellings of the same file**.
- 🆕 **A sweep that RECONSTRUCTS the command it runs will eventually run a
  broken one and report it as a broken suite.** 量 2026-09-02: a script that
  pulled each suite out of `ci.yml` with a regex stopped at the `&` of `2>&1`,
  so all 48 invocations ran as `... 2>` and died in the shell — and it printed
  **46 FAIL lines that are indistinguishable from 46 failing suites**. That is
  this project's own rule about `test-flashwin-mutants` (a harness that kills
  everything and a harness that tests nothing print the same thing), inside the
  harness. **Take the whole `run:` value verbatim and hand it to `bash -c`**, so
  what runs on the desk is character-for-character what runs in CI, and read the
  first few lines of the output before believing any summary.
  🔴 **And that is still not enough, measured the same hour.** The corrected
  script grepped `^\s+run: .*tools/` and **silently dropped
  `verify-backup-copy`**, whose step is a YAML literal block: its `run:` line is
  just `|` and the command sits in the body. 46 suites reported ok and the
  47th was never invoked. **`ci-census` is what named it** — `RED … no
  verify-backup-copy.out` — which is the second time that suite has been lost
  this way and the second time the census caught it. **A sweep that selects
  `run:` LINES cannot see a `run:` BLOCK**; either parse the YAML or let the
  census be the arbiter, and never read a sweep's own count as coverage.
  🔴 **2026-09-02: and `ci-census` cannot be that arbiter ON THIS HOST, which is the half the sentence above still got wrong.** 量, running every `run:` step here: 47 of 49 suites green, and the two reds are the census **working**. `test-hazlint` (142 cases) and `test-hazlint-objs` (**41** as of 2026-09-04; 28 when this line was written) are declared `*bench-only*` in `ci-expected.tsv` because their `K4` population control is `$FWRE_WORK/stage2.bin` — 56 KiB of this unit's vendor bootloader, which may not be committed. `ci-census`'s own `C10` requires *`*bench-only*` plus a real `.out` → red*. **~~This desk has that file, so they run, so their `.out` exists, so red.~~ 🔴 **2026-09-06 (thirty-fourth segment): that attribution is FALSE, and the two reds are real.** 量, three ways: `grep -nE '^\s+run:.*hazlint' .github/workflows/ci.yml` returns **0**; `git log -S'test-hazlint.sh' -- .github/workflows/ci.yml` is **empty over the whole history**, so no such step has ever existed; and `tools/ci-expected.tsv:142` states it outright — *"CI runs zero hazlint cases"*. **Nothing in a `ci.yml` sweep invokes either suite, on any host**, so having `stage2.bin` cannot make them run. 🟢 **The two reds are `census/merge the captures` and `census/census`, and the first causes the second**: 量 2026-09-06, a full sweep of all **60** `run:` steps *(🔄 **61** from the thirty-seventh segment the same day, when `citime self-test` was added)* — **58 ok, 2 RED, 1,478 s** — where `merge the captures` dies on `cp: cannot stat 'dl/*/*.out'` (the GitHub artifact download directory does not exist at the desk) and `census` then reports `NOT-RUN-TOTAL MISMATCH: declares 491 and this job did not run 2`. ⚠️ **This paragraph's CONCLUSION is untouched** — run every suite here and read the per-suite lines, let the census on GitHub decide the census; only its reason moves.** Those two are **183** of the declared `# not-run-total: 491` *(477 when this line was written, then 478; 量 2026-09-03 against the tsv and against CI run 33747027566's census, which printed the same 478; **491 from 2026-09-04**, `R5-3a`, when `test-hazlint-objs` went 28 → 41 and the whole row is bench-only)*, so the total collapses to **2** here and the mismatch check fires too. ⚠️ **And the total is not recomputable from the table**: `ci-census`'s own docstring says a suite's skip rows are *alternatives, not additive* — which fire depends on configuration — so summing the covers column gives 517, not 478, and that is the table being right rather than wrong. **So: run every suite here and read the per-suite lines; let the census on GitHub decide the census.** A local sweep that ends in two reds every time trains a reader to ignore reds, which is the failure this whole paragraph exists to prevent.
- 🆕 **The desk sweep is `tools/desk-sweep.py`, it runs on a COPY, and the copy
  goes on ext4. Three rules, and each one is a refusal rather than a habit.**
  🔴 **① The step list is READ, never reconstructed.** The tool parses
  `.github/workflows/ci.yml` with PyYAML. Everything above this bullet about
  regexes that stop at `2>&1`, greps that cannot see a `run:` BLOCK, and the
  two inline `- run:` steps at the `lint` job that **every desk sweep from
  2026-08-25 to 2026-09-07 skipped** — 59 of 61, wrong by two for six weeks —
  is the reason. Its `C2` control runs the old line-based enumerator against
  the same fixture and requires it to come out short, so the reason is a case
  and not a paragraph. 量 2026-09-07: **62** `run:` steps (61 plus this tool's
  own self-test), **2** refused here because they need root, **2** expected-red
  (`census/merge the captures`, `census/census`), **58** runnable. 🟢 **And it
  settled the two that were invisible**: `lint/#1` is `sudo apt-get install
  shellcheck`, refused at a desk; `lint/#2` is `shellcheck --severity=error
  tools/*.sh`, and it is **green here, rc 0** — the first time it had ever been
  run at this desk.
  🔴 **② Copy to ext4 first, VERIFY the copy, sweep the copy, delete it.**
  量 2026-09-07, the whole sweep, both arms as COPIES so the only variable is
  the destination filesystem: **9p 1,893.4 s → ext4 1,002.7 s = 1.89×**, and
  the sweep phase alone 1,813.0 → 957.6 s, also **1.89×**. Per suite, 57 paired
  legs, **median 1.77×**; 13 of them within ±15 % and **7 actually slower on
  ext4**. Verdicts are IDENTICAL on both arms — **58 ok, 2 refused, 2
  expected-red** — which is the control that licenses the change at all: a
  faster sweep that reached a different conclusion would be worthless.
  🔴 **The gain is bimodal and neither half is the filesystem in general.**
  Three mutation suites that re-exec Python hundreds of times collapse —
  `rbcheck` **47.75×** (326.4 → 6.8 s), `cardcheck` **37.56×** (219.4 → 5.8 s),
  `replay-capture` **33.80×** (190.8 → 5.7 s) — together **40.6 % of the 9p
  sweep, 736.5 s → 18.3 s**. What is left on ext4 is dominated by work no
  filesystem touches: `test-console-capture-mutants` **0.98×**,
  `test-console-capture` **1.00×**, `test-deskchan` **1.00×**, together
  **54.2 % of the ext4 sweep** — the first is sleep-bound by design (ptys and
  played gaps) and the others run `qemu-system-mips` single-threaded at 100 %
  of one core. 🔴 **So `1.89×` is the number, and it will not improve by moving
  the tree anywhere else — including a tmpfs.**
  🔴 **AND THE FIGURE THIS RULE WAS FIRST WRITTEN FROM DOES NOT SURVIVE, WHICH
  IS THE MORE USEFUL RESULT.** It was `test-spec-check-mutants` at 9p
  **44.25 / 45.10 s** against ext4 **1.52 / 1.47 s** — *29×*. 量, chasing it:
  the **9p leg reproduces** (45.27 s here) and the **ext4 leg does not** —
  standalone on ext4 with n=3 it is **19.42 / 23.80 / 20.29 s**, and under the
  sweep 16.50 s, so the suite's real ratio is **2.2–2.8×**. The 1.5 s is
  reproducible on demand and it is **a run in which the suite REFUSED**:
  with `.git` absent `git ls-files '*.md'` returns **0** instead of 108, and
  the suite exits **rc 1** printing *"REFUSING: the unmutated self-test already
  fails (rc=2) -- every mutation below would 'kill' a suite that was already
  red"* — measured, **1.36 s**. So the 29× was
  9p-with-a-population ÷ ext4-with-no-population, two different experiments.
  ⚠️ **This is this project's own rule arriving in the timing domain: a suite
  that refuses is FAST, and a fast suite looks like a win.** Time a suite only
  beside the count of what it actually ran.
  🟢 The mechanism is unchanged and still measured: 量 on this run's own
  source-hash phase, **1 CPU second in 36 s of wall clock with 78,549 voluntary
  context switches and 8 non-voluntary** — the process is asleep waiting for 9p
  replies. ⚠️ **`iowait` does not see this** (it read **0.0 %** while that was
  happening): iowait counts block-device waits, and a 9p wait is a sleep on a
  transport reply, accounted as *idle*. The instrument is voluntary context
  switches, not `iowait`.
  ⚠️ **The verify is cheap, measured rather than assumed**: hash + copy + hash
  is **80 s of 1,893 (4.2 %)** on 9p and **45 s of 1,003 (4.5 %)** on ext4. 🔴 **The verification is not optional and it is a refusal,
  not a warning**: the sweep reads the copy and the conclusion is about the
  tree, so a hash list is taken on both sides and a mismatch stops the run
  before a single suite starts. `C3` is the positive control on it — one byte
  changed in the copy must be caught, or *"the copy IS the source"* is a line
  that cannot fail.
  🔴 **③ DO NOT COMMIT WHILE A SWEEP IS RUNNING, and the reason is not that a
  commit changes content — it does not. A commit changes the POPULATION.**
  量 2026-09-07: `spec-check` sweeps **tracked** `.md` files; a bench card was
  committed while the desk sweep was mid-run; the card was untracked when
  `spec-check` walked the tree and tracked immediately after, so **neither
  state was ever swept** and its `C8` defect reached CI. A sweep certifies the
  tree it saw. Copying first makes "the tree it saw" a thing on disk that can
  be compared, which turns that silent hole into a stated scope limit: the tool
  re-reads the source at the end and says out loud whether the green is about
  the tree on disk now. ⚠️ **The copy does not protect the copy PHASE** — a
  commit racing `cp -a` can be captured half-applied, which the fidelity check
  refuses. The window is the first minute or two of each run.
  🔴 **2026-09-08: the rule is not "do not commit", it is "do not TOUCH the
  tree" — and that is wider than it reads.** 量, on the forty-fourth
  segment's own sweep: it ended `🔴 THE SOURCE MOVED WHILE THE SWEEP RAN -- 1
  difference(s)`, and the difference was
  `tools/__pycache__/flashmap.cpython-310.pyc`. Nothing was committed and no
  source file was edited; a **read-only experiment** was run from the source
  tree while waiting, and `import flashmap` wrote a `.pyc`. 🟢 **The guard
  worked and it is worth what it cost**: the file is gitignored and no tracked
  file moved, so the green stands — but the tool SAID so rather than leaving
  it to be assumed, which is the difference between a scope limit and a hole.
  **Run tools from a copy while a sweep is up, or read the notice and check
  what moved.**
  ⚠️ **What it cannot do**, stated rather than left to be found: a step naming
  an absolute path into the source reads the SOURCE, not the copy (it greps for
  that and reports); `$FWRE_WORK` is outside the copy for both arms on purpose;
  and **its total is not CI's wall clock** — it runs steps sequentially where CI
  runs four jobs in parallel, so it may never be compared with `citime`'s BIG3.
- 🆕 **Reading a suite's output files is a measurement, so it needs a control —
  and freshness is NOT completion.** 量 2026-09-01: `ci-out/` holds the previous
  run's `.out` files, so a summary that just reads them scores stale results as
  new (an mtime cut caught exactly one, and it was the one that would have been
  misread). Then the mtime cut passed a file that was **still being written** —
  3,645 bytes, `RESULT:` absent; 5,968 bytes forty seconds later. **Wait for the
  process's exit code; the output file is not the instrument.**
- Serial console: CP2102, **38400 8N1**. You cannot see it — at the bench you write
  the commands and read what I paste back. One power cycle is the most expensive
  unit here, so list every question before the device is plugged in.

## Committed files

**Written for an engineer, never for a hiring panel.** State the finding, name the
artefact it was measured on, stop. No résumé bullets, no "this proves I can X".
`plan/` is gitignored and may address me directly; committed files may not.

English, except the working log and `SPEC.md`. Commit messages say *why* — the
diff says what.

🔴 **And `ci-census --only <the suites you touched>` is the wrong rule when what you touched is `bench/`.** 量 2026-08-30: a seating that adds two captures moves the population every census-shaped case reads, and `tools/test-boot-timeline.sh`'s `B2` — a hardcoded `N cold, M warm` — went red on GitHub twice while the local `--only` run was green. **A seating changes data, and data is what those cases assert on.** After a seating, run every suite that can run on this host, not only the ones whose code changed. 🔴 **2026-09-08: and on a DESK day the same rule bites for a different reason — `--only` cannot report on a suite it was not given, so a suite you edited but did not name is invisible to the check you ran to be safe.** 量, on the forty-fourth segment's closeout: `flashmap`'s declared total was corrected 12 → 14 and the census was run `--only capdate,capfield,flashmap` and came back green, while `tools/ci-expected.tsv` still declared `looprun 55` against a suite that had grown to **66**. That is a `CENSUS-MISMATCH` on the next push, and it was found by a `git grep` for stale counts and not by the census. **Name every suite you touched, including the ones you only added cases to** — or run the census with no `--only` at all and read the reds you already expect.

**Before you stop**: update `PROGRESS.md` § Now, and append a dated entry to
`LOG.md` (create it on the first session) — **including desk-only days**, because
a desk-only day is exactly when the next bench visit's plan changes. **If the
session produced, changed or refuted a number, `SPEC.md` changes in the same
commit** — a spec table that lags the finding is worse than no table, because it
reads as current. Then run `python3 tools/spec-check.py` — it runs its eight
controls first and refuses to report on the file if any of them fails — and
`bash tools/test-file-modes.sh` if a file was added. Two seconds for both.
