# The device tree — `R5`'s `D2`

**Owner of**: everything under `dt/`, the `tools/dtcheck.py` instrument, and
the cost of `D2`'s second acceptance criterion. `PROGRESS.md` owns which step
is active; this file owns the work.

---

## 1. What `D2` actually asks for, and what arrived on 2026-09-09

`plan/router-rebuild-plan.md` § 6-R5 (v5, review item 12) gives every driver
**two** binding models. The first — `platform_device` on 2.6.30 — has run on
the silicon. The second is this, and its row has **four** acceptance criteria,
not two:

| | criterion | 2026-09-09 (forty-ninth segment) |
|---|---|---|
| ① | `dtc` compiles the `.dts` | 🟢 done |
| ② | **the driver compiles in a modern kernel tree** | 🔴 **not done — `R5-12`.** Its cost is measured in § 4 rather than estimated |
| ③ | `dt-validate` passes | 🟢 done |
| ④ | explicitly marked *never probed on hardware* | 🟢 `dt/README.md`, and repeated at the head of every file |

⚠️ Criterion ② was read as part of ①/③ in the segment's own opening brief, and
it is not. It is written down here in full so the next reader does not have to
re-derive which half is owed.

---

## 2. 🔴 The measurement that decided the instrument's shape

Taken 2026-09-09, on `dtc 1.7.0` and `dtschema 2026.6`, **before a line of
`dt/` existed** — a calibration probe, not a bug report.

| stage | on a real failure it prints | and exits |
|---|---|---|
| `dt-doc-validate` | `$id: Cannot determine base path from $id ...` | **0** |
| `dtc` | `Warning (unit_address_vs_reg): ...` | **0** |
| `dt-validate` | `'interrupts' is a required property` | **0** |

**All three.** A checker that reads exit status reports a perfect green on a
device tree that fails every stage. `tools/dtcheck.py` therefore parses the
output and treats the status as one more thing to be sceptical about, and its
`T14` case asserts that at least one tool still exits 0 on something it
reports — so a future dtschema that fixes its exit codes turns the suite red
and says the rationale moved, rather than leaving a program nobody needs.

🔴 **And one reading worse than those three.** `dt-validate` prints
`<schema>: ignoring, error in schema: ...` for a schema it could not load and
then validates nothing against it. **One typo in one binding silently turns
every node that binding describes into an unvalidated node**, with no other
symptom. `dtcheck` makes that a hard failure (`T11`).

🔴 **Two more, and each would have been a false RED rather than a false green.**
`dtc` has no `-Wall` (`FATAL ERROR: Unrecognized check name "all"`) and no
`-Werror`. And `dt-doc-validate` requires the binding's `$id` to be under
`http://devicetree.org/schemas/` **and** the file's own directory to match that
`$id`'s path — which is why `dt/bindings/` mirrors the mainline layout rather
than being flat.

⚠️ **The first calibration run proved nothing and its own output said so.**
Both halves of the stage-A pair failed, for the same unrelated `$id` reason —
a harness that kills everything and a harness that tests nothing print the same
thing. Every negative case in `dtcheck --self-test` now has a positive twin on
the same stage (`T0a`…`T0e`) for exactly that reason.

⚠️ **Two things `dt-doc-validate` does NOT check**, measured on fixtures it
passed: that `required:` names properties the schema declares, and that the
binding's own `examples:` block satisfies the binding. `dtcheck`'s `A2` and
`A3` stages exist because of those two, and `T3b`/`T4b` assert the *absence* —
so a dtschema that starts catching them makes this suite red instead of
quietly making `A2`/`A3` redundant.

---

## 3. What the tree says, and the three findings that came out of writing it

`dt/rtl8196e.dtsi` (SoC) and `dt/rtl8196e-totolink-n150rt.dts` (board), six
bindings, `21 of 21` cases and `23 of 23` self-test controls on 2026-09-09.

🔴 **① The watchdog is a register inside the timer block, and a device tree is
where that stops being free.** `WDTCNR` is at `0x1800311c`; the Timer/Counter
block starts at `0x18003100`. Two sibling nodes each claiming the documented
block would overlap, and the second `request_mem_region()` would take `-EBUSY`.
The tree gives the timer `0x00`–`0x1b` and the watchdog `0x1c`–`0x1f`:
adjacent, disjoint, at word granularity. `rtl819x-timer.c:478` already named
`0x1c` for this reason and touches nothing in it.

🔴 **② `CDBR` lives inside the timer too, and that is why the timer is a clock
provider.** The 2.6.30 watchdog derives its own rate by reading `TC0DATA` and
`CDBR` — another device's registers — which is only possible because that
kernel has no ownership model. It is also how a **loader-state** constant
(14,965,000 Hz) reached a shipped driver's table and stayed there while the
hardware counted at 200,180 Hz, wrong by **76×** (`SPEC.md` `CLK-08b`,
`CLK-28`). In the tree the watchdog has `clocks = <&timer>` and cannot make
that mistake. This is a **decision-layer** choice and belongs to
`docs/blind-write-ledger.md` § 5's L2, not to L1.

🔴 **③ `dtc` classifies a node by its NAME.** A node called `spi@18001200` is
an SPI *bus* to dtc, which then demands `#size-cells = <0>` on it
(`Warning (spi_bus_bridge)`, 量 on the first run of `dtcheck` against the real
tree). This block is not an SPI bus in the device-tree sense — one NOR device
behind a fixed chip select and a 4 MiB read window, not a set of addressable
slaves — so the node is `flash-controller@18001200`. Found by the instrument,
on its first real run, and it would not have been found by reading.

🟢 **And one thing the tree can say that no other file in this repository
could.** `CLAUDE.md`'s *Never* table forbids writing `0x000000–0x005FFF` and
`0x006000–0x007FFF` — the loader, which is unrecoverable, and `H601`, which
holds this unit's MAC and radio calibration. In `dt/rtl8196e-totolink-n150rt.dts`
those two partitions carry `read-only;`. **That is the first machine-readable
form that rule has ever had.**

⚠️ `dt/unmatched-allow.tsv` is the enumeration of what is NOT checked: seven
`compatible` strings that no schema in the corpus describes, each with the
reason. `dt-validate` is *silent* on such a node unless given `-m`, so without
that file a green means "every node that happened to have a schema was
checked" while reading as "every node was checked".

---

## 4. 量: how big is criterion ②

`plan` estimates the whole of `D2` at **~0.3 segments per driver**. That is
compatible with a `.dts` node and a binding; whether it is compatible with
*"the driver compiles in a modern kernel tree"* was an open question, and the
segment's own opening brief predicted it was not.

**Method.** For each driver take every identifier it uses; keep the ones that
are kernel API in 2.6.30 (present anywhere under that tree's `include/`); ask
which survive into `linux-headers-6.8.0-139`'s `include/`.
**Refutation condition, written first:** a large missing set, or one containing
the driver's *registration* calls rather than only helpers, refutes the
estimate.

| driver | identifiers | kernel API in 2.6.30 | gone in 6.8 | |
|---|---|---|---|---|
| `rtl819x-timer` | 226 | 111 | **8** | 7.2 % |
| `rtl819x-gpio` | 90 | 67 | **3** | 4.5 % |
| `rtl819x-spi` | 154 | 94 | **5** | 5.3 % |
| `rtl819x-wdt` | 152 | 113 | **3** | 2.7 % |

**Union: 10**, and **7 of the 10 are the same three names repeated** —
`create_proc_entry`, `read_proc`, `write_proc`. Those are the `/proc`
instrumentation these drivers carry to be *measured on the bench*, not the
driver. The genuinely distinct removals are `clocksource_register`, `cycle_t`,
`clock_event_mode`, `clockevents_handle_noop`, `getnstimeofday` and
`add_mtd_device`. One of the ten (`unwedge`) is a false positive — a verb of
this project's own that the filter's namespace pattern missed — so the honest
figure is **9**.

🔴 **So the prediction was wrong and the plan's estimate survives the
experiment built to refute it.** It is recorded that way round deliberately.

🔴 **2026-09-09 (fiftieth segment): a SECOND limit, measured by compiling
the driver, and it is not the one declared below.** `rtl819x-wdt`'s figure
here is 3; the compiler names **4** APIs against 6.8. The miss is
`setup_timer`, and the mechanism is a **name collision**: its only
occurrence under 6.8's and 6.18's `include/` is
`serial_8250.h:97`, `void (*setup_timer)(struct uart_8250_port *)` — a
member of an unrelated struct. This method asks *does the identifier
appear*, sees that line and scores the symbol as surviving. So the table
under-counts for two separate reasons, not one; both push the same way, so
the conclusion below stands and its stated reason was incomplete.
`notes/modern-kernel-port.md` § 4.

🔴 **And the limit stated below is now MEASURED, on the two drivers where
it dominates.** 量 2026-09-09, all four compiled verbatim against 6.18.50:
`timer` **1 fatal**, `gpio` **24**, `spi` **18**, `wdt` **6** diagnostics,
against this table's 8 / 3 / 5 / 3. 🔄 **20** of gpio's 24 are `struct gpio_chip`
*(this line said 21 until 2026-09-10; the classification that makes the classes
sum to 24 gives 20 + 1 `gpiochip_add` + 3 `/proc`, and it was re-derived
independently on 2026-09-10 from a fresh round 0)*
used as an **incomplete type** — the name is in both trees, mainline moved
the definition into `<linux/gpio/driver.h>` — and spi's are `mtd_info has
no member named ‘read’; did you mean ‘_read’?`, `erase_info` without
`state` or `mtd`, `MTD_ERASE_FAILED` removed. **That is the sentence below,
with numbers.** ⚠️ Diagnostics are not root causes; only `wdt` has a
measured root-cause count (4, by ladder). 🔴 **And `timer` is a third
category this table cannot express at all**: it stops at `#include
<asm/rlxregs.h>`, a header that exists only under `arch/rlx/include/asm/`,
and mainline has no `arch/rlx`. An identifier census cannot see an
`#include`, and no kernel version will ever supply this one.
`notes/modern-kernel-port.md` § 5.

⚠️ **And the limit is what carries the residual.** This method cannot see a
symbol that still *exists* with a changed **signature**, and those are the
expensive ones: `clocksource.read` gained a parameter, `gpio_chip`'s accessors
changed, `mtd->read` became `_read`, and the hand-rolled watchdog misc device
is replaced by `watchdog_device`. **10 is a lower bound.** So criterion ② is
neither confirmed nor refuted as a ~0.3-segment item, and the experiment that
settles it is compiling **one** driver against 6.8 — the first cell of
`R5-12`, and `rtl819x-wdt` is the candidate because it has the smallest
missing set and the largest expected shrink.

🔴 **The measurement's own positive control fired once, and it saved a
published number.** The first run pointed at `linux-headers-6.8.0-139-generic`
— the *build* directory, which carries almost no headers — indexed **128**
identifiers against 2.6.30's 69,873, and reported `request_irq` and `kmalloc`
as *removed from Linux*. The per-driver percentages it produced were **86–93 %
gone**, which is exactly the shape the prediction expected and would have been
published. What caught it was two symbols asserted present, not the
plausibility of the table. The script now refuses outright below 10,000
identifiers.

---

## 5. What is NOT claimed

* **Nothing here has been probed on hardware and nothing here can be.** 2.6.30
  has no device tree. `R10a` is the gate that makes these nodes bind.
* **No third-party port has been read.** `docs/blind-write-ledger.md` § 4.6
  records the only contact — one `cpu@0` node of `shibajee`'s `rtl8196e.dtsi`,
  fetched 2026-08-25 for `CPU-25` — and § 6 makes the derivation check the
  first operation on those trees at `R5-9`. `lexra,rlx4181` appears in
  `dt/unmatched-allow.tsv` rather than getting a binding for that reason: the
  string is the recorded contact, and the *value* behind it is independently
  量 on this die (`PRId 0x0000CD01` → `PRID_IMP_RLX4181`).
* **The kernel's binding corpus is not in the schema set.** `dtschema` ships
  the core schemas only, so `gpio-leds`, `gpio-keys`, `fixed-partitions`,
  `fixed-clock` and `simple-bus` are declared unmatched.
  `dtcheck --extra-schema <linux>/Documentation/devicetree/bindings` validates
  against them when a kernel tree is at hand, and **that has not been run**.
* ~~**`R5-7` (🔄 upstream `leds-gpio`, *not* `leds-rtl819x` — decided
  2026-09-10, `notes/gpio-driver.md` § 9) and `R5-8` (`gpio-keys`) have no
  drivers**~~ 🔄 **2026-09-10, later the same day: `R5-7` has one and `R5-8`
  does not.** The `leds` node's consumer exists — `rtl819x-gpio` 1.1 carries
  `known_mask 0x60` and `ALLOW_OUT_MASK (1u << 6)`, and
  `arch/rlx/kernel/rlxfw-devices.c` registers the `platform_device` upstream
  `leds-gpio` binds to, in image `r58`. **Nothing has probed on hardware**, so
  the `.dts` claim is unchanged: this file describes measured hardware and the
  binding has never been exercised by a device tree, because 2.6.30 has none.
  🔴 **The `keys` node still has nothing bound**, and 量 2026-09-10 the reason
  is a link error rather than a probe failure: `gpio_keys.c` calls
  `gpio_to_irq()` at six sites and `arch/rlx` declares it without defining it
  anywhere, so `CONFIG_KEYBOARD_GPIO=y` does not build. That is `R5-8`.
  The LED node also documents a conflict rather than
  hiding it: the vendor's `rtl_gpio_timer` drives bit 6 as well. ⚠️ The
  sentence that used to end this bullet — *bit 6 is not in the 2.6.30 driver's
  `known_mask` (`0x00000020`, bit 5 only), so that driver would refuse the
  consumer at `.request` before `ALLOW_OUT_MASK` was ever consulted* — was true
  of 1.0 and is false of 1.1; it is kept here because it is the reading that
  made the two-mask change necessary.
