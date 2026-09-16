# `mfgtest` — the design, and the three decisions it had to settle first

`P1-0`. Desk, 2026-09-16, zero power cycles, board unpowered throughout.

The gate is **`mfgtest` passes on a good unit, and every check has been made to
FAIL once.** The second half is the gate; the first half is a demonstration.
This file is the design the second half is scored against: one row per check,
with **how it is made to fail** and **whether that injection is reversible on
this unit**, stated before any of them runs.

`plan/router-rebuild-plan.md` §P1 has a check list of eight items. This gate
does not adopt it unaltered, and §1 says which items moved and why.

---

## 0. What the vendor's own factory test does — and what it does not

讀 2026-09-16, out of this unit's extracted rootfs and the GPL drops. **This
repository had never recorded any of it** (量: `git grep -in 'mp\.sh|UDPserver|9034'`
returned nothing before this segment).

The vendor has a manufacturing test for this SoC. It is worth reading before
designing one, because the surprise is not what it checks — it is what it
leaves out.

| the vendor tests | how |
|---|---|
| WiFi TX power / spectrum | `mp_ctx` (continuous TX), `mp_tx`; **measured externally by the jig's spectrum analyser**, not by the board |
| WiFi RX sensitivity | `mp_brx` bulk-RX then `mp_query`; the DUT counts matching frames |
| TX-power calibration index (TSSI) | `mp_tssi` per radio |
| Die temperature | `mp_ther` (the thermal meter that compensates TX power) |
| Spectral flatness | `mp_psd` sweep |
| RF-chip and WiFi-MAC register integrity | `irf`/`orf`, and thirteen generic poke scripts |
| eFuse | `efuse_get` / `efuse_set` / `efuse_sync` |
| **MAC + calibration *programming*** | `flash set <MIB>` → `flash sethw` — the jig **writes** MAC, calibration and regulatory domain into `H601`, then reads back |

| the vendor does NOT test | evidence |
|---|---|
| **LEDs** | 量: no LED test anywhere. `ledType` exists only as a configuration byte inside `H601`, consumed by the driver; nothing in `mp.sh`, `UDPserver.c` or any `/bin` script exercises one |
| **Buttons** | 量: no button or GPIO test in the MP path |
| **Flash integrity** | `flash test-hwconf`/`-dsconf`/`-csconf` exist in `/bin/flash` and are 量 present in this unit's binary — and are **never invoked** by `mp.sh` or `UDPserver.c` |
| **MAC *verification*** | `mp.sh` **overrides** the MAC with a hard-coded constant so every unit on the line answers at the same address; the real read (`flash gethw HW_NIC0_ADDR`) is commented out |
| Ethernet ports, beyond reachability | `mp.sh` bridges `eth0`+`eth1` into `br0` at a static address. If the jig can reach UDP:9034 at all, one port and the bridge work. That is the entire Ethernet test |
| DDR, USB, thermal soak, current draw | nothing |

🔴 **So the vendor's MP test is an RF-calibration-and-programming fixture, not
a functional test**, and the pass/fail limits are not on the device at all —
`UDPserver.c:202` says the reply format exists to *"match `MP_TEST.exe`'s
format"*, and `MP_TEST.exe` is the factory PC's, in none of the drops.

**The consequence for this design is the decision in §1 ②.** Four of the plan's
eight items — LED, button, flash integrity, MAC verification — are things the
vendor's own factory test does not do. There is no prior art to match on those,
only a surface list to reuse. And four of the vendor's items — TX power, RX
sensitivity, PSD, thermal — cannot be reproduced here at all, because they are
measured by instruments this project does not have. **That asymmetry is the
result, and it is stated rather than hidden:** `mfgtest` is not a smaller
version of the vendor's test. It covers a different set.

### Three corrections this reading forces on `PROGRESS.md`

1. 🔴 **`UDPserver` is not on this unit's flash.** 量: `ls` on this unit's
   extracted rootfs returns *No such file*; `grep -rl UDPserver` over the whole
   rootfs, binaries included, returns nothing. The daemon is in three GPL drops
   as **source**; the binary ships only in the `3.4.0` images.
2. 🔴 **There are thirteen poke scripts, not twelve.** 量:
   `ib ib1 id1 idd idd1 iw iw1 ob ob1 od od1 ow ow1`. `idd1` is byte-for-byte
   the same command as `id1` — a vendor copy-paste — and a census that counts
   twelve is silently dropping it.
3. 🔴 **`mp.sh` is dead code on this unit.** 量: `etc/init.d/rcS` does not
   mention it or `UDPserver`. It survives because the vendor's build copies
   `*.sh` wholesale into `/bin` on non-MP builds too.

And one correction on the `H601` spec: `PROGRESS.md` calls `UDPserver.c`'s
`PARAM_HEADER_T` *"the only candidate specification for an `H601` checksum
check"*. 讀: it is neither the only one nor a correct one. The live
implementation is `users/boa/apmib/apmib.c`; `UDPserver.c`'s copy is inside
`#if 0`, and its constants (`"hs"`, version 3) are from a different SoC
generation — this board's are `"H6"` and version **1**, which is where the name
`H601` comes from. See §4.

---

## 1. The three decisions

### ① The plan's SPI-NOR line — **the line is split; nothing is written**

The plan's check list carries *`SPI NOR` JEDEC ID + 抹一個備用 sector 寫回讀
比對* — erase a spare sector, write it back, compare. `CLAUDE.md`'s Never table
says mainline is zero-write through `R9` and **a write needs the owner's
explicit yes**. `P1` sits at cumulative segment 113; `R8` at 224.

The owner was asked and delegated the decision. 🔴 **A delegation is not an
explicit yes to a write**, and the rule's own wording is what settles it: the
permission it requires was not given, so it does not exist. Zero-write stands.

The line splits cleanly, because its two halves are not the same kind of thing:

* **JEDEC ID is a read** and it stays. It is not a discovery — `SPEC.md`
  `FLS-04` holds `0x1C7016` (vendor `0x1C` = Eon, capacity byte `0x16` = 2²²),
  量 2026-08-23 at the loader prompt with four pre-computed controls in the same
  output. So the check is a **comparison against a registered expectation**,
  which is what a manufacturing check should be rather than a reading with
  nothing to compare to. 🔴 Its cost is real and is in the table: `rtl819x-spi`
  does **not** issue `RDID` today — 量, the string appears in that file only in
  comments analysing the *loader's* `ComSrlCmd_RDID` — so this check needs a new
  verb, and that verb is `P1-1`'s.
* **Erase-and-write-back is struck**, and its replacement is not a compromise
  invented to dodge the question. `rtl819x-spi`'s `trywrite` calls `mtd->write()`
  and `mtd->erase()` **through the pointers**, receives `-EOPNOTSUPP` from both
  because `.flags = MTD_CAP_ROM`, and asserts `n_writes == 0`. *The write path
  is reachable and refuses* is a measurable property, it has a two-sided
  injection (§3, `FAIL-FLASH-2`), and it writes nothing.

⚠️ **What `mfgtest` therefore does not establish, stated so it is not read
past**: that this flash can be written. A factory checks writability because the
factory is about to write. rlxfw's mainline never writes flash, so the check as
the plan wrote it would test a capability this firmware does not use — but that
is an argument for the substitute, not a claim that nothing was given up. **The
unit's flash writability is untested by this gate.**

🔴 **And the plan contains a SECOND violation that nothing in this repository
had noticed.** Its DoD names three example injections — *拔網線、清 MAC、跳過
餵狗* (unplug the cable, clear the MAC, skip feeding the dog). 量 2026-09-16:
`清 MAC` has **exactly one hit in the whole repository** — the plan's own DoD
line — and no adjudication anywhere. Clearing the MAC means writing `H601`,
which `CLAUDE.md`'s Never table forbids touching at all and `plan/CHARTER.md`
marks 永久禁止, because it is the one region a factory reset does not restore.
**It is struck**, and `FAIL-MAC` in §3 is simulated at the boundary the check
reads, which is what `PROGRESS.md`'s own rule ③ prescribes for an injection that
cannot be shown reversible.

### ② The plan's entry method — **there is no mode, and that is the vendor's answer too**

The plan offers *hold the reset button at boot (GPIO strap), or add `mfg=1` to
the kernel cmdline*. Both halves are refuted:

* 讀 `docs/loader-command-semantics.md:294-316`: thirteen command-line-shaped
  needles — `cmdline bootargs bootcmd console= root= init= mem= rootfstype
  setenv printenv "env " ethaddr bootdelay` — **zero hits**, against a scan whose
  own control is a **refusal to emit**: `loader-unpack.py` will not produce a
  report unless it first finds all seventeen commands the console prints, in the
  same artefact. There is no environment mechanism, no storage for one, and no
  command that sets one.
* The strap route reads the button, and the button's vendor path is measured
  (`FW-40`, `FW-62`) — but `FW-62` measured that the vendor's timer acts **once
  per power-up**, and the `.to_irq` of this project's own `gpio_chip` is `NULL`.

`docs/loader-command-semantics.md:325-329` tables three costed options for
delivering a cmdline. **None of them is needed, and the reason is that the
question was the wrong one.**

讀, from the vendor's own build system: **manufacturing mode on this SoC is a
different image, chosen at build time.**
`boards/rtl8196e/board-configuration.in:16` makes `MODEL_RTL8196E_MP` a Kconfig
**`choice` member**, mutually exclusive with the three GW models. The MP image's
entire `/etc/init.d/rcS` is 21 lines ending `/bin/sh /bin/mp.sh` and
`UDPserver &` — no web server, no config load, a bare respawning root shell on
the console. `boards/rtl8196e/Makefile:188` **skips `root.bin`, skips the web
pages and skips `mkbin` entirely**, and `:73` names the output `MP_NFJROM`.

🟢 **An `nfjrom` is a RAM-loaded image, and it is exactly the format this project
already ships**: `loudm`, the first kernel of mine that ran on this die, is *"the
`rtkload` pipeline's own `nfjrom` renamed"*.

**Decision: `mfgtest` is its own image, delivered to RAM over TFTP and entered
with `J`. There is no mode flag, no strap and no cmdline, because the image is
the mode.** That is not a workaround for a missing mechanism; it is the vendor's
own architecture, read out of the vendor's own Kconfig and Makefile.

**Cost, written down as the step required:**

| | |
|---|---|
| one extra image in the build matrix | the same tree, the same six drivers, a different `/init` |
| `RECIPE_ID` differs from the shipped image | it is a digest over `config/`, so the boot-capture byte count must be **re-derived, not copied** |
| the port checks run the vendor's NIC driver | so `mfgtest`'s output must record **which driver is running** — the plan's own v7 note, and it is load bearing once `R6` lands |
| zero flash writes, zero new loader mechanisms, zero power cycles to establish | — |

🔴 **A fourth entry mechanism exists and is rejected with a measurement.**
`gCHKKEY_HIT` at `0x8040DBA4` is a genuine console-key-at-power-on strap that the
vendor's loader already implements: `check_image()` returns *no image* when it is
1, `doBooting()` then goes straight to the rescue path, and `SPEC.md` `REG-22`
records it **量 set** when ESC is streamed from before power-on. It is settable
from the host at zero risk and readable with one `DW`. **And it is useless as a
mode signal here, for exactly the reason that makes it reachable**: streaming ESC
from before power-on is what every rlxfw seating already does to catch the loader
prompt, so it would read 1 on every boot this project makes. *A mode signal that
is 1 in the workflow that would use it is not a mode signal.*

### ③ Physical failure injection on a one-of-a-kind device

Every failure-injection precedent in this repository mutates software: the
mutation suites `str.replace(old, new, 1)` into a copy of a source tree and risk
nothing. *Every check has been made to FAIL once* means provoking a real failure
on the only unit this project has.

The owner authorised three classes and declined the fourth:

| class | authorised | what it covers |
|---|:---:|---|
| **P** physical, operator-performed, zero-risk | ✅ | unplug the Ethernet cable, press the button, power the link partner down, power the board off |
| **R** register, through **my own** `/proc` verbs | ✅ | a wrong `cereload`, `lock 6`, `biteraw`, `stop` — reversibility comes from *a reboot restores the initial state*, which is 量 (seventeen byte-identical boots, seating 20) |
| **V** vendor driver / vendor state | ✅ | `ifconfig` the vendor NIC down; let the vendor's `rtl_gpio_timer` be consumed |
| **T** anything needing a tool — shorting a pin, desoldering, an external signal source | ❌ | not designed for; a row that would need it is recorded **unfalsifiable-on-this-hardware** |

And one class the precedent does not have a word for:

| class | what it covers |
|---|---|
| **S** simulated at the boundary the check reads | the check is fed a value that cannot be produced physically without an irreversible act. The *check* is falsified; the *hardware* is not touched. Every `S` row must say what physical failure it stands in for, and that it is a stand-in |

🔴 **`S` is weaker than `P`/`R`/`V` and the table says so per row.** An `S`
injection proves the check's decision logic works. It does not prove the check is
wired to the peripheral. Where a row is `S`, the wiring is evidenced separately —
by the check's own positive reading on a good unit — and that is stated, not
assumed.

---

## 2. The check table

Six columns as `P1-0`'s DoD requires, plus the reversibility column `③` adds.

**`SPEC.md` id** names what the pass criterion cites. 🔴 Where it reads
*(driver: none)*, the hardware has a numbered owner and the **driver** does not —
see §5.

| id | what it reads | peripheral · `SPEC.md` id | pass criterion | how it is made to fail | class | reversible on this unit? |
|---|---|---|---|---|:---:|---|
| **`MT-ID`** | the image's own `RLXFW-ID0` mark | — | equals the `RECIPE_ID` the build computed | build a second image; the printed id must differ | S | n/a (build-time) |
| **`MT-FLASH-1`** | `/proc/rtl819x-spi`, new `rdid` verb | SPI NOR · `FLS-04` | `1C7016` | feed the comparator a wrong id | S — stands in for *a different or dead flash part*, which needs class **T** | n/a |
| **`MT-FLASH-2`** | `/proc/rtl819x-spi` after `trywrite` | SPI NOR · `FLS-27` | both pointers return `-EOPNOTSUPP`; `n_writes == 0` | build one image with `.flags` not `MTD_CAP_ROM` | S | n/a (build-time); **this is the substitute for the plan's erase/write-back** |
| **`MT-FLASH-3`** | `/proc/rtl819x-spi-map`, 32 × 32 | flash content · `FLS-26` | 31 of 32 groups identical to the reference; group 0 as recorded | the driver's existing `corrupt` verb, which moved the 4 MiB digest on `C1-NG` | R | 量 — it corrupts the RAM copy, not flash; a reboot clears it |
| **`MT-TICK`** | `/proc/rtl819x-timer` + `/proc/interrupts` | TC1 · `CLK-27` | `ce_live=1`, `ce_mode=2`, `irq_spurious=0`, `irq_stuck=0`, and `Δjiffies == Δirq_count` | `cereload` to a wrong value: the ratio breaks | R | 量 — seating 13 did six reloads over four values and came back each time |
| **`MT-WDT`** | `/proc/rtl819x-wdt` | watchdog · `FW-52` | `wdtcnr_at_probe = A5000000`; the ten `ovselN` rows exact; `BOOTGUARD` feeding | `kickms` long enough that the bite falls outside the window | R | 量 — a reboot restores it. 🔴 **Ordered last: the pass path resets the board** |
| **`MT-LED`** | `/proc/rtl819x-gpio`, `/sys/class/leds/*/brightness`, **and the operator's eye** | LED · `BRD-13` (driver: none) | `dat` bit 6 clears, `n_set_ok` increments, `n_writes` increments, operator sees LED #2 of eight lit | `lock 6` first: the write is refused **before** it happens, `n_writes` unmoved, the lamp does not change | R | 量 — `unlock 6` restores it; both directions ran at seating 20 |
| **`MT-BUTTON`** | `/proc/rtl819x-keys` | button · `BRD-05`, `REG-28` (driver: none) | a 3 s hold at 20 Hz gives `(n_open, n_poll)` `(1, 60)`, and a second gives `(2, 120)` | do not press: the counters stay flat | P | 量 — the flat control already ran at seating 20 |
| **`MT-PORT`** | vendor `/proc/rtl865x/port_status` 推 | Ethernet · **no Linux-state id** — every `NET-*` is loader-state | link up on the connected port, and the output **names the vendor driver** | unplug the cable | P | 量 — plug it back in |
| **`MT-MAC`** | `H601` header + body, in the kernel, **verdict only** | `H601` · see §4 | signature `H6`, version `1`, body checksum 0, MAC not all-`00`, not all-`FF`, group bit clear | feed the parser a synthetic buffer (`$FWRE_WORK/h601-synth.bin`) | S — stands in for *清 MAC*, which is **permanently forbidden** | n/a |
| **`MT-RFCAL`** | the same read, the same verdict | `H601` · see §4 | the 8-bit sum of all `len` body bytes, checksum byte included, is 0 | the same synthetic buffer with one byte moved | S | n/a |
| **`MT-DDR`** | 🔴 **struck, with the reason** | — | — | — | — | — |

### The struck row, and why it is struck rather than attempted

The plan asks for *DDR walking-1s + an address-bus short test (one segment, not
all of it)*. **There is no owned surface for it.** This image has no `devmem`
(量, `FW-46`'s family), so it cannot be done from userspace; doing it in the
kernel means a new verb that writes and reads a `__get_free_pages` region, which
is `P1-1` work nobody has costed. And `MEM-17` measured DRAM **retaining a
previous power cycle's contents**, so a naive walking-1s over a region the
allocator just handed out can pass on stale data rather than on the bus.

It is recorded **not-done with the reason**, per `P1-0`'s DoD, rather than
written as a row that would pass without discriminating. 🔴 The vendor does not
test DDR either (§0), so this is not a gap against the prior art — it is a gap
against the plan.

---

## 3. The injection design

Following the mutation-suite contract exactly, because this repository has
already measured what happens when it is relaxed: 量 2026-08-31, five of
`test-replay-capture-mutants.py`'s fourteen rows were counted as kills on
`rc != 0` alone **and turned no case red at all**.

1. **Every row NAMES the check it must turn red.** The name is a required field
   of the row, not a substring of a free-text label — 量, in the
   `(kills XX)`-in-the-label flavour, `test-rbcheck.py` has ~~eleven~~ **EIGHT** rows
   with no
   such suffix and they silently fall back to bare `rc != 0`. 🔴 **量 2026-09-17, two
   ways (a grep and a structural parse of the `MUT` table), and the number was
   already wrong when it was written**: that file last changed 2026-09-14 and
   this document was written 2026-09-16, so nothing moved between them. The
   CLASS of defect is real and still unfixed; the count was a 量-marked figure
   with no instrument behind it.
2. **A kill is `rc != 0` **and** the named check among the reds.** Anything else
   is `WRONG-CASE`, which is a survivor with a different name.
3. **`SURVIVOR`** means the check it names does not work. It is not a pass.
4. **`DECLARED`** — a population constant, so a harness that silently runs fewer
   rows than it has is caught.
5. **A `REFUSING` baseline** — if the un-injected run is already red, every
   "kill" below it is a kill of something that was already broken.
6. 🆕 **`NO-TAKE`** — the hardware analogue of `INVALID-MUTANT`: *the injection
   did not happen*. Unplugging a cable that was already unplugged, `lock 6` on a
   line that was already locked. The precedent is unanimous that collapsing
   verdicts is how these harnesses go wrong, so this gets its own word rather
   than being folded into `SURVIVOR`.
7. 🆕 **`reversible`**, and it is a gate rather than a column: **an injection
   whose reversal is 推 rather than 量 does not run at all.** Every `R` and `V`
   row's reversal is verified by measurement *before the next injection*, not at
   the end of the seating.

🟢 **REALISED 2026-09-17 as `tools/mfginject.py` (`P1-2`).** 29 rows, four
controls and a REFUSING `B0`. **24 of 24 class-S injections killed, 0 alive**, and
the must-survive row survived as proved. The five class-R/P rows are physical and
stand down as ONE skip line covering 5, so `P1-4` inherits a table rather than a
memory. It runs at a desk because `config/mfgtest.sh` reads every surface through
`$MFG_ROOT` — which is what makes *simulated at the boundary* an executable
statement instead of a described one.

**Ordering is a safety property, not a convenience.** `MT-WDT` resets the board
and goes last. `MT-FLASH-3`'s `corrupt` is in RAM and must be followed by a
verified clean re-read before anything else is trusted.

---

## 4. `H601`, read as a structure and never as bytes

讀, from `users/boa/apmib/apmib.h`. **No byte of `0x006000`–`0x007FFF` was read
to write this section**, and none may be printed by any check.

The name is not a magic number. `HW_SETTING_HEADER_TAG` is `"H6"` for this SoC
family (`:1520`) and `HW_SETTING_VER` is `1` (`:1589`); the version is written as
two ASCII decimal digits (`sscanf(&sig[2], "%02d", &ver)`). **`"H6"` + `"01"` =
`H601`, at `HW_SETTING_OFFSET 0x6000`**, length `0x2000` — exactly the window
`CLAUDE.md` fences.

| offset | size | field |
|---|---|---|
| `+0x0000` | 4 | `signature[4]` = `'H' '6' '0' '1'` |
| `+0x0004` | 2 | `len` — body byte count, **including** the trailing checksum byte |
| `+0x0006` | `len-1` | body — `HW_SETTING_T`, packed: `boardVer`, `nic0Addr[6]`, `nic1Addr[6]`, then the per-radio calibration block |
| `+0x0006+len-1` | 1 | checksum |

The checksum is a one-byte two's-complement sum, ~~live at `apmib.c:547`~~
🔴 **defined at `apmib.h:1833-1846` — `:547` is the VERIFICATION CALL SITE,
not the formula** (corrected 2026-09-17):
`CHECKSUM(d,n) = (~Σd[i] + 1) & 0xFF`, and the invariant a reader checks is
**`Σ` over all `len` body bytes, checksum byte included, `== 0`**. The 6-byte
header is not covered — 讀 twice independently, `apmib.c:537`+`:547` and
`/bin/flash`'s own `flash.c:2946-2951`, both of which advance past
`sizeof(header)` before checksumming.

🔴 **FOUR CORRECTIONS TO THE TABLE ABOVE, all 讀 2026-09-17, and three of
them change a parser.**

1. **`len` IS BIG-ENDIAN AND THIS SECTION WAS SILENT ON IT.** The device stores
   it in native order and this part is big-endian; the proof is the x86 HOST
   builder, which swaps on the way in — `cvcfg.c:635`,
   `Header.len = WORD_SWAP(header.len);//important!`, and again at `:1794`,
   `:1829`, `:1883`. Read the other way round, `0x048E` becomes `0x8E04`, a
   length that runs off the end of the window. Silence here is not neutral.
2. **The vendor bounds `len` FROM BELOW ONLY.** `apmib.c:469` refuses
   `len < sizeof(HW_SETTING_T)+1` and compares it against nothing else;
   `HW_SETTING_SECTOR_LEN` appears only on the *compressed* path (`:369`,
   `:1626`). 量 by grep: there is no upper bound on the uncompressed path, so
   a corrupt length makes the vendor read straight through this window and
   into `DEFAULT_SETTING` at `0x8000`. **Any parser of ours must clamp, and
   that clamp is ours and not the vendor's.**
3. **`"H6"` is not the only tag the vendor accepts.** `apmib.c:338` also takes
   `"Hf"` and `"Hu"`; anything else means a COMPRESSED block with a different
   layout, not a corrupt one. So `hw_sig_ok 0` means *not the uncompressed H6
   form*, which is a stricter test than the vendor's and must not be reported
   as *corrupt*.
4. **The body holds TEN more MACs, not two.** *"then the per-radio calibration
   block"* understates it: `HW_WLAN_SETTING_T` opens with `macAddr` …
   `macAddr7`, **eight further 6-byte MACs** (`mibdef.h:21-28`), and
   calibration starts 48 bytes in. `nic0Addr` is at body **+1** (one byte of
   `boardVer` first), absolute `0x6007` — the one offset `MT-MAC` needs, and
   it is confirmed.

🟢 **`/bin/flash test-hwconf` does exactly this and exits 0 or −1**, and the
literal is 量 present in this unit's own `/bin/flash`. 🔴 **It is not available
here**: 量, `config/rlxfw-initramfs.tsv` declares **seven** files — `/init`,
`/bin/uprobe`, `/bin/ucost`, `/bin/busybox` and three libraries — and `/bin/flash`
is not one of them. Adding it is possible (it is this unit's own binary, so
`R3`'s Decision B survives) and is **not** the design, because that binary also
carries `sethw`, `default` and `reset`, which write. **Putting a flash-writing
binary into the image of a zero-write project to save thirty lines of kernel code
is the wrong trade**, and it is recorded as a rejected alternative rather than an
unconsidered one.

**So `MT-MAC` and `MT-RFCAL` are a kernel verb in `rtl819x-spi` that prints
verdicts and never bytes**: `hw_sig_ok`, `hw_ver`, `hw_len`, `hw_sum_ok`,
`mac_not_zero`, `mac_not_ff`, `mac_group_bit`. ⚠️ `hw_len` is a structure size,
identical on every unit of this model, and leaks nothing about the MAC; the four
booleans leak four bits per run. That is stated so the containment tools can rule
on it rather than being left to be discovered.

---

## 5. What this design does NOT establish

* **Flash writability is untested** (§1 ①). The substitute tests that the write
  path refuses, which is a different claim.
* **DDR is untested** (§2), and the row is struck rather than weakened.
* **Nothing the vendor measures with an instrument is covered**: TX power, RX
  sensitivity, PSD, thermal. Four of the vendor's eight areas are outside what
  this project can measure at all.
* 🔴 **Four of the eleven live rows are class `S`** — simulated at the boundary.
  They prove the check's logic, not its wiring.
* **`MT-PORT` has no Linux-state `SPEC.md` id to cite.** Every `NET-*` row in
  this repository is loader-state. The check reads a vendor `/proc` file whose
  existence in *this* kernel is 推 until the first seating.
* 🔴 **The driver ids do not exist for two peripherals.** `PROGRESS.md`'s P1
  inherited table says *"the LED and the button have no `SPEC.md` id at all"*,
  and 量 that is false in the safe direction: `BRD-05` (the button — `PABCD`
  bit 5, active-low with a pull-up, not `RESET#`, 量 2026-08-24) and `BRD-13`
  (the LED — #2 of eight on the board, active-low, 量 2026-09-09) both exist and
  are both 量, alongside `REG-28`, `REG-30`, `FW-40`, `FW-62`, `FW-63`, `FW-65`.
  **What is actually missing is narrower**: `rtl819x-keys` — the *driver* — has
  no id, and `BRD-13` is the *lamp's* row rather than the gpio driver's. So
  `MT-LED` can cite which lamp and what polarity, and has nothing numbered to
  cite for the code that lit it.
* **The unit's identity is the host's, not the device's.** The plan's
  `mfg-station.py` records results by serial number; this unit's serial-equivalent
  is its MAC, which may not enter this repository. The device prints verdicts
  about `H601`; the operator supplies the serial; the CSV lives outside the
  repository, the same rule `flrbracket` already enforces for `FLR` read-backs.

---

## 6. The 段 band, re-derived

`P1-0`'s DoD requires this to be re-derived from ten points rather than copied.
It was, by a script whose **positive control is that, fed the nine points
`PROGRESS.md` already publishes, it reproduces that line's own six figures
exactly** — `n 9 · min 0.33× · max 1.38× · spread 4.15× · mean 0.844× · median
0.833×`. It does.

🔴 **The tenth point is one gate, not two.** `PROGRESS.md` names `R1-pub + R2c`
at 20/20 and `R1z` at 3/3. `R1z` is **not** a calibration point: its own gate
board row says it *沒有計畫數字可以校準* — the plan does not contain that gate —
so `3/3` compares a number to itself. It is excluded for the same reason
`P4b-gate` already is.

| | nine points | ten points | |
|---|---:|---:|---|
| min / max / spread | 0.33× / 1.38× / 4.15× | **0.33× / 1.38× / 4.15×** | unchanged — the tenth lands inside |
| mean | 0.844× | **0.859×** | moved |
| median | 0.833× | **0.917×** | moved |
| **`P1` against the plan's 小計 of 11** | 4–15 段, median ≈ 9 | **4–15 段, median ≈ 10** | edges unchanged, median +1 |

⚠️ **A structure in that data was tested and is not used.** The plan's estimate
appears to get better for bigger gates — the two largest (`R5` plan 31, `R1-pub`
plan 20) land at 1.03× and 1.00×, the two smallest (`P4a` 2, `S0` 3) at 0.50× and
0.33×. Spearman ρ between plan size and `|ratio − 1|` is **−0.643**, permutation
p **0.049** against a pre-written threshold of 0.10, with a null median |ρ| of
0.238 at n = 10. **It is not used to narrow the band**, because size and recency
are collinear here (ρ = **+0.486**, measured) and n = 10 cannot separate *the
estimator improved with practice* from *big gates average out*.

🔴 **And the first version of that test had a control that could not fail.** It
was one shuffle, scored *did the shuffled column do worse than the real one* —
which passes on 95.1 % of draws by construction when p = 0.05. The shuffle landed
at ρ = −0.579, a 1-in-12 draw, close enough to the real −0.643 to look like a
problem, and reading that output is what caught it. The control is now the null
distribution, not a sample from it.

---

## 7. What `P1-1` and `P1-2` inherit

| | |
|---|---|
| `MT-FLASH-1` needs an `rdid` verb in `rtl819x-spi` | ✅ **CLOSED 2026-09-17 (`P1-1`), and the question was wrong twice over.** 🔴 **量: this driver has NEVER had that contract.** The only *never writes it* in `rtl819x-spi.c` is line 110 and its subject is **SFCSR's `CMD_BYTE` field**, not `SFCR`; the driver writes `SFCR` on every transaction at `:619`, restoring what `:583` read. The true invariant is narrower and stronger — it never writes a value of its OWN choosing, and `release()`'s read-back enforces that rather than asserting it. 🔴 **讀: and the `C-3` excerpt is a PARTIAL VIEW.** `docs/loader-flash-write.md:137` opens at `0x8040591C`; the routine starts at `0x804058BC`, so **96 bytes and 24 instructions precede it and nothing said so**. A fresh disassembly of the whole routine (same recipe, same `sha256 f88869d1…`) shows the order: spin → **`SFCR = 0xFFC00000` at `0x80405900`** → a CS idle toggle → `SFCSR_CS_L` at `0x80405914` → the opcode. **CS is asserted sixteen instructions AFTER the SFCR write**, so that write is bus setup at probe time and not a step the opcode needs. And 量 seating 16 read live `SFCR = FFC00000` under Linux — the exact word `ComSrlCmd_RDID` writes — so it would be idempotent here anyway. **The verb writes no `SFCR` and the reason is measured, not hoped.** `SPEC.md` `LDR-43`/`REG-39` |
| `MT-MAC` / `MT-RFCAL` need an `h601` verb | ~30 lines, verdicts only, §4 |
| `MT-PORT`'s surface is ~~推~~ ✅ **讀 + 量-on-artefact 2026-09-17** | **CLOSED AT THE DESK, zero bench time.** `CONFIG_RTL_DEBUG_TOOL` is a *promptless* `default y` symbol (`drivers/net/rtl819x/Kconfig:45-47`) so it cannot be switched off from a menu; it is `=y` in the board template and `config/rlxfw-kernel.delta` is silent on it. The entry is created at `rtl865x_proc_debug.c:5854` under `#if CONFIG_RTL_PROC_DEBUG \|\| CONFIG_RTL_DEBUG_TOOL`. 🟢 **And the artefact agrees TWO-SIDED**: `strings` over my own `vmlinux` finds `port_status`, `rtl865x` and `Dump Port Status:` present, and `vlan`, `netif`, `priveSkbDebug` — the entries gated on `CONFIG_RTL_PROC_DEBUG` ALONE, which is off — absent. Every entry the config predicts present is present and every one it predicts absent is absent. 🔴 **And the pass criterion was written against the wrong index space**: the file prints SWITCH port indices, and 量 `NET-13` says this kernel's netdev map is the MIRROR of the vendor's, so the operator's jack is **switch port 3** (`eth4` here). The token is **`Port3`**, not `Port4`. `SPEC.md` `NET-27` |
| the image is a second build-matrix entry | 🔴 **量 2026-09-17: `RECIPE_ID` MOVES NO BYTES.** `RLXFW-ID0=XXXXXXXX` is twenty bytes whatever the digest is, so this row's stated reason does not hold. What would move the count is a different `/init`, which changes the 93-byte userspace tail. ✅ **Re-derived rather than copied, by `tools/bootbytes.py`**: `boot_bytes = 710 + Σ marks`, with the 710 recomputed independently from **95 committed captures spanning seven images** and coming out to one value. The two new verbs' marks (`S-RDID`, `S-H601`) are on-demand and fire only when the verb is typed, so **the prediction is 1,637 — unchanged — and that is a derivation, not a copy**. The script ships as `/bin/mfgtest`, a file nothing execs, which the `/bin/uprobe` precedent in `config/rlxfw-initramfs.tsv` already measured as costing 0 bytes. So there is no second image: `P1-3` types `mfgtest auto <id>` at the shell. `SPEC.md` `FW-86` |
| what the device can actually run is now measured | `config/image-commands.tsv` and `tools/appletcensus.py` — §8 |

---

## 8. `tools/appletcensus.py`, and the reason it exists

`SPEC.md` `FW-46`'s own ⚠️ reads: *未來的卡片不可以猜 applet 存不存在 … 而這個
repo 裡仍然沒有任何東西能在卡片凍結前問「這顆映像跑得動這條指令嗎」*. `P1-1`'s
named failure mode is that same row. A design that hands `P1-1` a device-side
program without settling it is a design that repeats `FW-26` and `FW-46`.

🔴 **The more useful finding is that the question was already answerable.**
`FW-25`, 量 **2026-08-29** — ten days before `FW-46` spent three bench cells
guessing — ran this unit's own busybox under `qemu-mips-static` and reports
**50 applets**, naming fourteen of them. It recorded the **count** and not the
**list**, and it was not made repeatable. So `FW-46`'s ⚠️ is an over-claim:
the instrument existed and was used once.

`appletcensus.py` reads the tables out of the binary statically, by signature
rather than by offset, and never executes anything. 量:

| | |
|---|---|
| the binary | this unit's own `/bin/busybox`, **273,332 bytes**, `BusyBox v1.13.4 (2018-01-10 14:56:45 CST)`, declared at `config/rlxfw-initramfs.tsv:105` |
| applets | **50** — against `FW-25`'s independently measured 50, by a different method with no shared code |
| ash builtins | **40** — `cardcheck.py:451`'s own refusal message says *"this project has never read this binary's builtin table"*. 🔄 **Was `:370`; that row moved when `P1-1` inserted the `CARD-4` correction above it, and `citecheck` caught the rot on the same segment that caused it** |
| controls | **19 of 19** silicon readings reproduced: 15 present, 4 absent, from three sources |
| one of them out-of-sample | `seq` was registered **after** the extractor had run, found by censusing every `sent` field in `bench/**/*.meta.json`. `bench/2026-09-14c/X-seq.log`: `busybox seq 3` → `seq: applet not found` |

🟢 **And it changes what `P1-1` can write.** `cardcheck`'s 推 builtin list has
**zero false positives** — every one of its 27 names is real — and is **missing
13**, of which **11 are not also applets**, so a card using them is reported
`NOT IN IMAGE`: `[[ alias bg chdir fg jobs let printf pwd readonly unalias`.
🔴 **The one that matters is `printf`.** `awk` is genuinely absent from this
image, so `printf` is the only formatting primitive a device-side test has, and
until now a card that used it would have been refused.

⚠️ **Two limits, stated rather than found later.** The tool answers whether the
*name* resolves, not whether the applet works — an ABSENT is strong, a PRESENT is
weaker — and it says **nothing about options**: `FW-42` measured `grep` present
and `grep -E` absent on this same image. And it ships **no keyword list**: the
run-based signature recovers 8 of ash's ~20 keywords, while 量 `for` was typed at
this device 17 times and `while` 4 times and neither is in the extracted run. A
short list a checker consumes is worse than none.
