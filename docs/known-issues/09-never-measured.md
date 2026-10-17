Part of [the known-issues index](../KNOWN-ISSUES.md): entry 9 of 19, moved here verbatim from that file on 2026-10-17.

## What has never been measured at all

🔄 **2026-09-02 (`R5-0`), two rows leave this section and one arrives.**
*Leaving*: the incremental cost of a real edit on a reused tree — **592 `CC` /
32.58 s**, against 3 `CC` for the same edit with `RECIPE_ID` held (`SPEC.md`
`TC-45`); and whether confining `-DRLXFW_SRC_ID` moves the product — it does
not, two fresh stages give a byte-identical `vmlinux` (`TC-46`).
*Arriving*: ✅ ~~🔴 **whether the public RTL8196E ports derive from the vendor's `arch/rlx`.**~~ 🟢 **ANSWERED 2026-09-11 (`R5-9`): they do not, with one file's exception.** The derivation check ran with its ordering constraint intact — pre-registration in `git log` eighty-five seconds before the clone — and read `shibajee` INDEPENDENT on every domain it implements and `ggbruno` DERIVED on `prom.c` alone, four `BSP_` UART macros in the early console path. ⚠️ **It does NOT clear `R5-5`.** That step's independence was already spent on the vendor side by `docs/blind-write-ledger.md` § 4.5, which is a different question from this one and is not touched. `docs/driver-diff.md` § 2.

* 🔴 **Whether an unaligned ACCESS costs an exception on bare metal.**
  `CPU-15` measured the four unaligned *instructions* — `lwl`, `lwr`, `swl`,
  `swr` — executing at the loader prompt, and `CPU-75` measured an unaligned
  *address* costing **915 ns** in Linux user mode. Two states of one machine and
  neither refutes the other. The deciding experiment is timing the same `lwu2`
  at the loader prompt; it needs a payload and a seating.
* 🔴 **Four of the eight instructions on the emulation surface are unpriced**
  — the unaligned `lh`, `lhu`, `sh` and `sw`. `4b` priced `sync`, `lwu2`, `ll`
  and `sc`; `E7` required the number to be in the write-up rather than
  discovered by a reader, and it is (`docs/emulation-surface.md`). The rows are
  still unpriced.
* 🔴 **Two counters read at one instant, through this driver's own `/proc`.**
  Neither `R5` nor `R1-pub` established it — which is what the operating clause
  fires on at nine entries. 讀 `drivers/clocksource/rtl819x-timer.c`:
  `j = get_jiffies_64()` is inside the lock held 1998–2042 and `irq_count` is
  read live at 2147, 105 lines after the unlock. 🟢 Three lines would settle the
  pairing; what it needs after that is a measurement that the five one-sided
  differences go away, and 🔴 **if they do not, the mechanism is something other
  than sampling skew and that is the larger finding** — the gap is symmetric in
  sign and does not predict five same-sign differences in sixty-four rungs.
* ⚠️ **Whether `docs/rlx-isa.md` is readable by someone who did not build it.**
  Every claim in it is *checkable* from a clone — § 9 is that table, and one row
  of it was a promise the page could not keep until the day the gate closed.
  **Checkable and readable-by-an-outsider are different properties and only the
  first is established.** That is a different deliverable and it has no DoD yet.

* ✅ ~~**Whether an interrupt of mine can be delivered at all.**~~
  🟢 **ANSWERED 2026-09-04, seating 12: yes, 119,818 times.** Every one
  of § 3.1's seven gates is now 量, `Status.IM2`/`IEc`/`BEV` included
  (`status = 10000401`) and all four routing registers read in **both**
  states — the loader's `00000000 30050004 00000000 00000000` and
  Linux's `22222222 C222FA2D 2EB29F22 22222022`. `SPEC.md` `IRQ-08`,
  `IRQ-10`, `bench/2026-09-04/CORRECTIONS-block9.md`.
  🔴 **What replaces it is narrower and was not on this list**: a
  pending bit in `TCIR` has a lifetime of at most one 10 ms tick,
  because the vendor's own ack is a read-modify-write on a
  write-1-to-clear register (`SPEC.md` `IRQ-09`). That does not stop
  delivery and it does bound every single-sample reading of that
  register ever taken here.
* ✅ ~~**Whether a DMA write is visible to a cached CPU read.** Nothing has been
  measured in that direction, and it is the one driver decision the cache gate
  closed without.~~ 🟢🟢 **ANSWERED 2026-09-17 (seating 26), and the answer is
  that it is NOT visible: this D-cache holds stale lines after a real bus master
  overwrites the underlying DRAM.** The engine is the switch's CPU-port RX DMA,
  already running at the loader prompt; the treatment is eight broadcast frames;
  two of four buffers read `V1 == V0` with `V2` different, in each of two runs.
  The reading is airtight rather than suggestive because a miss would have
  fetched `V2`, so the line *was* resident — **there is no *it was evicted*
  escape**, which is what every previous attempt lacked.
  `docs/rlx-cache-and-cp0.md` § ⓑ-4.
  🔴 **What is still open, and it is not small**:
  * the D-cache's **write policy** (`CPU-19` 殘留 ①) has **zero** measurements,
    and § ② says why that is decisive for a ring — a ring is a *write hit on a
    resident line*;
  * D-side **line size** and **associativity** have never been measured; the
    量 16-byte / 2-way figures are the **I**-cache, and `v-line`/`v-assoc` have
    never run;
  * **why two of the four buffers read the new value is undetermined** — the
    split is structural, the same two both runs, and the geometry that would
    explain it is the unmeasured one above;
  * the **throughput cost of uncached rings** is unmeasured and is a different
    number (`R6-1` `D5`).
* ✅ ~~**Whether this silicon retires the `cache` instruction.** This unit's own
  vendor kernel contains 37 of them, D side only; none has been executed by
  anything of this project's.~~
  🟢 **ANSWERED 2026-08-29, seating 7, and this bullet had carried the refuted
  sentence for fourteen days.** 量 `bench/2026-08-30/QJ.log`: `probe3`'s Group X
  issued four op values — `0x10` `IInval`, `0x11` `DInval`, `0x15` `DWBInval`,
  `0x19` `DWB` — and every one returned `n=00000000`, with `x ri`'s
  `cause=00000028` (ExcCode 10) in the **same capture on the same boot** as the
  control that makes *no trap* a reading rather than a dead handler. `SPEC.md`
  `CPU-44`, `docs/probe3-cells.md` § Group X.
  🔴 **What survives is narrower and is already written there**: `CPU-44` closes
  on *retires*, not on *invalidates* — `x c10`'s untreated twin moved too, so the
  six intervening `CCTL` stages explain the treated victim as readily as
  `cache 0x10` does.
  ⚠️ **Found by `R1-pub-0`'s census (2026-09-12), not by any gate.** Five checks
  were green over this file the whole time: none of them compares a sentence
  about the future to a capture that has already answered it.
  `docs/isa-prior-art.md` § 3.
* **The pipeline hazards**, which need a controlled loop and a timing harness.
* **What an incremental build of a REAL edit costs on this tree.** 量 2026-09-02
  fixed the reason there was no incremental build at all — a bare `#` truncating
  every `.cmd` file, so kbuild's command comparison could never match — and a
  no-op `make` went from 599 objects and 28.0–32.1 s to 2 and 6.9–10.3 s. But
  **every number taken that day is a no-op or a `touch`**, and touching a file is
  not editing it. A real `R5` iteration changes a driver's `.c` and possibly a
  header it includes; how many objects that costs, and how many seconds, has no
  reading. 🔴 It also cannot be taken with today's recipe: measuring it needs a
  reused tree, and `rlxfw-marks.py` refuses to re-apply to one. `PROGRESS.md`
  `INC-1`.
* **How long the watchdog takes to fire at its SHORTEST setting.**
  ⚠️ **This bullet replaces one added and withdrawn on the same day, and the
  withdrawn one was false.** It read *`CLK-08` has been an empty cell since
  2026-08-24*. 量: `CLK-08` was measured — **1118.133 ms** at `OVSEL=1001` and
  **557.583 ms** at `OVSEL=1000`, `bench/2026-08-25/H3c-D4.timing`. The false
  claim came from `SPEC.md` §17's residual row for the same id, whose prose still
  said *empty*; a search for `WDT`/`watchdog` in ASCII matched that row and not
  the measured one, which records the fact in Chinese. **What is genuinely
  unmeasured is narrower**: both measured points are high `OVSEL` settings, while
  `J BFC00000` writes `WDTCNR = 0` — the **lowest** setting, ~~推 2.184 ms by
  halving, never observed. `R4` predicts it and then measures it.~~
  🔴 **2026-09-08 (`R5-6`): the halving is not merely imprecise, it is
  STRUCTURALLY INVALID at this end, and the owning gate was stale too — `R4`
  closed on 2026-09-02.** 2.184 ms is `1118.133 ÷ 2⁹`. But `CLK-08b` solved
  the two measured points for a common offset and got **`c` = 2.967 ms**:
  what was measured is `2^(15+OVSEL)/f − c`, not `2^(15+OVSEL)/f`. Halving a
  quantity that carries a constant offset scales the offset with it, and at
  `OVSEL` 0 the offset is **larger than the number being predicted** — the
  halved prediction of the *measured interval* is negative. The correct
  prediction comes from the model and not from the ladder:
  **2^15 ÷ 14,965,000 = 2,190 µs** (`CLK-28`).
  🟢 **And it has gained two independent supports without a seating.**
  `bsp_machine_restart` (`boards/rtl8196e/bsp/setup.c:114`, not inside any
  `#if`) writes `WDTCNR = 0` and spins, so **every `busybox reboot -f` this
  project has ever run was a bite at exactly this setting** — dozens of them,
  and `FW-37` timed one end to end at 2.407 s. `CLK-08`'s own upper bound of
  **≤2.3 ms** from `entry` sits 0.11 ms above the prediction. ~~**`R5-6`
  measures it directly**: the `bite 0` rung of the OVSEL ladder, one reboot,
  no power cycle.~~
  🔴 **2026-09-08 (seating 17): that rung RAN and this bullet stays open, with
  BOTH of its halves now wrong for different reasons.**
  ① **The prediction is a loader-state figure.** `2,190 µs` = `2^15 ÷
  14,965,000`, and 量 that divisor is `CLK-08b`'s **loader** constant: under
  Linux the watchdog counts at **200,180 Hz**, so `OVSEL` 0 is **163.7 ms**,
  not 2.19 ms. Everything above this line that divides by 14,965,000 is
  describing the loader. The `≤2.3 ms` bound from `entry` is a **loader**
  measurement and still stands *for the loader*; it is not a bound on the
  Linux figure and this bullet had been reading it as one.
  ② 🔴 **The method does not work at this end, and that is a fact about the
  instrument rather than about the setting.** `rlxfw_puts` returns when the
  bytes are in the UART **FIFO**, not on the wire, so the arm happens with up
  to 16 characters still queued; at 163.7 ms the reset lands mid-drain and
  corrupts the marker the interval is measured from — 量, the `0x8D` after
  `RLXFW-W-GO` in `bench/2026-09-08b/C1-B.log`, and a "gap" of 1.095 ms that
  no non-negative offset can reconcile with the rung above it. **The ladder has
  two clean rungs, not four**, and neither is this one.
  🟢 **What it would take**: a marker whose last byte is known to be on the
  wire before the arm — either a drain loop reading the UART's own TX-empty
  status, or a rung timed from the PREVIOUS rung's arm rather than from a
  print. Neither exists yet. `SPEC.md` `FW-50`/`CLK-08b`,
  `notes/watchdog-driver.md` § 2.1 and § 10.6.
* ~~**`RLXFW-ID0`, the build-identity string added on 2026-09-01, has never
  been read off the board.**~~ 🟢 **CLOSED 2026-09-02, seating 10.** The board
  printed `RLXFW-ID0=B1434383` and `looprun`'s `A3` compared it against the id
  the build had just computed: *board printed b1434383, build computed
  b1434383*. **Nobody typed that value at any point** — it is a sha256 over
  `config/`, compiled in, printed by the kernel, and read back by the tool.
  It was checked twice on the day: once inside the bench run, and once by a
  desk run whose build started at 12:29 asserting over the capture the board
  produced at 12:15. `bench/2026-09-02/LP-boot.log`, `docs/GATE-RESULTS.md`
  `R4` claim 1.
* 🔴 **`R4`'s loop has never run `S2` to `S7` in one invocation, so its 73.88 s
  is a sum of two runs.** The bench half skipped the build; the desk half
  skipped the board. The one stage untested in a single command is *upload
  the image the loop just assembled*, ~~and it needs a power cycle~~. `SEAM-1`.
  🔴🔴 **2026-09-14: and it CANNOT be run at all, which is narrower and worse
  than needing a power cycle.** The `--image` pre-flight is above the stage loop
  and requires the file to exist; `S3` is what creates it. Two arms refused with
  **zero files created**; the control (`--skip S2,S3` with an existing image)
  passed the same guard and reached `S4`. So the never-run is **structural**, not
  a scheduling accident, and it cost no power cycle to establish.
  `notes/dev-loop.md` § 10.6.
* 🔴 **`looprun --iterations` above 1 is refused, because the loop cannot
  repeat.** `S4` is a loader command and iteration 1 ends with the loader
  gone. A loop that runs once is what exists; `R5` is six drivers. `LOOP-3`.
* 🆕 **`gpio_to_irq()` on this die.** 2026-09-10 (`R5-8`).
  `config/host-compat/0006` aliases it to gpiolib's `__gpio_to_irq`, which
  returns `-ENXIO` when `chip->to_irq` is `NULL`, and `rtl819x-gpio.c:658` is
  `.to_irq = NULL` — but **that chain is READ, not measured on the silicon**.
  🔄 **2026-09-11 (`R5-9`): still not measured, and it is now an unmeasured thing rather than an unknown one.** `ggbruno/openwrt`'s
  `arch/mips/realtek/gpio.c` implements a full `irq_chip` on this SoC's GPIO with a chained parent handler, and `shibajee`'s SoC header names the three
  registers it would need — `GPABCDISR`, `GPABIMR`, `GPCDIMR` — which this repository had never named. `docs/driver-diff.md` § 3.2 and
  § 3.4.5. ⚠️ Neither is 量 on this die and neither third-party image has been run here, so this row does not move: what changed is that
  *nobody has shown it works on this part* is no longer one of the reasons.
  `rtl819x-keys` prints the live value as `RLXFW-K4` on every boot and the
  prediction is `FFFFFFFA`; ~~nothing has booted it~~ 🔄 **量 2026-09-10,
  seating 20: `RLXFW-K4 = FFFFFFFA` on all seventeen boot captures, and
  `/proc/rtl819x-keys` prints `irq_probe -6`, `irq_live -6`, `enxio -6` —
  the same errno from a latched call site, a live one, and the constant
  itself. The read chain is now measured on the silicon.** The same sentence covers
  the `-EINVAL` this patch gives `irq_to_gpio()`, and that half is WEAKER
  still: 量, three files in this drop call it and this board builds none of
  them, so no image this project ships can demonstrate it either way.
* 🆕 **This button's bounce.** 2026-09-10 (`R5-8`). The
  `debounce_interval = 100` in `arch/rlx/kernel/rlxfw-devices.c` is a guess
  and the file says so. The instrument for it is `rtl819x-keys`' 32-slot
  jiffies ring and its `b0_n_bounce` counter, and the ring's resolution is
  bounded at 10 ms by `HZ=100` — which is also the floor of the poll
  interval, because `input-polldev` converts it with `msecs_to_jiffies()`.
  **A polled button cannot see bounce finer than its own poll interval**;
  that is a property of polling and not a defect of the timestamp.
* 🆕 **Whether `rtl819x-keys` polls at all on the die.** 2026-09-10.
  `input-polldev` queues no work until a HANDLER opens the input device
  (讀 `drivers/input/input-polldev.c`), and in this image the only handler
  that can is `evdev`, whose `input_open_device()` is inside `evdev_open()`
  (`drivers/input/evdev.c:190`) — i.e. it needs a userspace open of
  `/dev/input/event0`. Nothing has performed one. `n_open`/`n_poll` are the
  three-state reading that will say so.
* 🆕 **`SPEC.md` `FW-55`'s `111,540 個 load` is not reproducible.**
  2026-09-10. The same `tools/hazlint-objs.py` on `r59` — a SUPERSET of
  `r58`'s population — reports 3,096 loads over 70 leaf objects, and a
  superset cannot be smaller. `--also drivers`, the only wider run, REFUSES
  on `Q7b`. The row does not record which directories were swept, and the
  tool prints its population on every run precisely because a sweep's own
  population is a claim. The number stays in place with the correction beside
  it.


---
