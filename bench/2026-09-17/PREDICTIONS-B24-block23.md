# Block 23 — `P1-3` and `P1-4`, and four of the eleven checks could not have gone green on a good unit

**Frozen before the first carded capture.** Seating 25. One power cycle, budget
one — **already spent at 01:53**, and everything below runs from the loader
prompt the ESC window caught.

---

## 0. What this block is, in one paragraph

`P1-3` is *the whole check list passes on a good unit*; `P1-4` is *each row is
made red once, physically*. Both run on one image. 🔴 **The image they run on is
not the one the segment inherited.** The board sat at the loader prompt for
fifty minutes while four defects in `config/mfgtest.sh` were found by reading
the things it reads — the drivers' own source, the built `.config`, this unit's
own busybox under an emulator, and one of this project's own earlier cards.
**Three of the four would have turned a check red with a perfect board in front
of it; the fourth made two of `P1-4`'s five injections into `NO-TAKE`s.** § 2 is
the list. Nothing below was measured on the die before this card was frozen.

---

## 1. The image, pinned

| what | value |
|---|---|
| cell | **`p11d`** — built 02:41:28→02:42:19, `tools/rlxfw-kbuild.sh`, `--variant quiet --marks --jobs 4` |
| `RECIPE_ID` | **`7974982c`** — the board must print `RLXFW-ID0=7974982C` |
| recomputed | `find config -type f -print0 \| sort -z \| xargs -0 sha256sum \| sha256sum \| cut -c1-8` → `7974982c`, i.e. the tree and the image have not parted |
| `vmlinux` | **4,170,754** bytes, sha256 `6f4ab5c3180053ff…` |
| marks | `all 12 mark(s) present once, 7 witness(es) present, 1 confirmed ABSENT, absent from 2 vendor artefact(s)`, **rc 0** |
| boot capture | **1,637** bytes, derived by `tools/bootbytes.py predict` (710 const + 927 marks) |
| `strings 'rtl819x-spi 1.2'` | **3** — driver 1 + `mfgtest.sh` 2, because the script rides in the initramfs. An older control saying *1* is stale |
| staged tree | `/home/key/fwre-work/rebuild/r3-4/cells/p11d/top` |

🔴 **`rlxfw-marks verify` WITHOUT `--absent` EXITS 1 AND PRINTS A RESULT LINE
THAT READS LIKE A PASS.** 量 02:33 tonight: with no `--absent` the tool says
`0 mark(s) and 0 witness(es) not a discriminator` — which looks like the green
sentence — while printing `no --absent file given -- then "present in mine" is a
label, not a discriminator` five lines above it and exiting **1**. The two
`--absent` artefacts are the pair `LOG.md:14466` names. **The tail is not the
verdict**, which is this repository's own rule arriving on a tool that had never
tripped it.

---

## 2. The four defects, and how each was found

Every one was found by reading a **third party** — never by re-reading the
thing under test.

### 2.1 `MT-BUTTON` had no cause at all — `mfgtest.sh` never opened the device

`mt_button()` read `n_poll`, slept 4 s, read it again, and scored *it moved*.
**Nothing in it opened `/dev/input/event0`**, and `n_poll` only advances while
that node is open. So it would have read `0 → 0` and FAILED with a working
button, pressed or not.

Four sources, none of them this file:

| source | what it says |
|---|---|
| `rtl819x-keys.c:280` | `n_open` is the count of `flush()` calls, and `flush` is input-polldev's **open** callback |
| same file, `:91-103` | *"with no handler that opens, poll() is NEVER CALLED … every counter reads 0 for ever"* |
| `p11d.config-built:769` | `# CONFIG_INPUT_EVBUG is not set` — the one handler that would open it unprompted is not built |
| `bench/2026-09-10`'s own card | types `sleep 3 < /dev/input/event0`, annotated *"the open is what is needed"* |

**`mfgtest.sh` had `sleep 4`. One redirect.**

🔴 **And the consequence is larger than the check**: `M26` is *do not press; the
counters must stay flat*. Against the old code the counters were flat **either
way**, so `M26` proved nothing — the seating's own brief calls this shape
*pulling a cable that was never plugged in*. Fixed, `mt_button` now scores three
terms with three distinct meanings — `n_open` moved (the node opened),
`n_poll` moved (the poller ran), `b0_n_press` moved (a debounced press was
seen) — and **the first two are what make `M26` a kill**.

### 2.2 `MT-ID` compared two cases of the same number

`rtl819x-spi.c:1457` prints `recipe_id %08X` — **upper**. `rlxfw-kbuild.sh:262`
computes the id as `sha256sum | cut -c1-8` — **lower**. `mt_id` compared them
with `=`.

🔴 **So `mfgtest auto 7974982c` — the spelling `PROGRESS.md:19` and this
segment's own brief both carry — would have turned `MT-ID` red with exactly the
right image on the board.** It is the only comparand in the file that comes from
outside it: `MFG_RDID`, `A5000000` and `BOOTGUARD` were each written by reading
the driver's format string, so their case was never in question. Fixed: the
comparand is folded, so either case now passes.

### 2.3 This unit's `$(( ))` SATURATES, and it was measured rather than assumed

量 on this unit's own busybox, `qemu-mips-static -L <squashfs-root> bin/busybox
ash`:

| shell | `$((0xb1818b92))` |
|---|---|
| host `dash` (what `mfginject` runs fixtures under) | 2978057106 |
| host `bash` | 2978057106 |
| **this unit's `ash`** | **2147483647** |

The obvious fix for § 2.2 — `printf '%08X' $((0x$want))` — therefore rewrites
every id with its top bit set, which is half of them, and `b1818b92`, the image
built four minutes earlier, was one. The 2 × 2 was run rather than argued: the
arithmetic form is **ok under dash and FAIL under this unit's ash** (`expected=7FFFFFFF`);
the shipped string fold is ok under both. `mt_led`'s
`$(( (0x$dat >> 6) & 1 ))` has the same exposure and now parses the low byte
only, behind a hex guard — on this board `dat` is `000000xx`, and the same
driver's `cnr` reads `FFFFFF8B`.

🟢 **And the harness can be run on the right shell for free.** `mfginject` already
takes `MFG_SHELL`; pointed at a two-line wrapper that execs
`qemu-mips-static … busybox ash`, **all 25 injections and all six controls pass
on the shell the die runs**, with no change to the tool.

### 2.4 `MT-TICK` could not see a wrong tick rate, so `M28` was a `NO-TAKE` too

`mt_tick` compared `Δjiffies` with `Δirq_count`. One tick is one of each, so a
clock at a tenth of its rate keeps `skew` at 0 and `dj > 0`; `sleep 5` simply
takes fifty real seconds. Seating 13 measured exactly that and wrote
**"nothing in the kernel could notice"**.

Fixed by reading the driver's *own* criterion: `rtl819x-timer.c:860-861` keeps
`ce_reload` (live, what `cereload` writes) beside `ce_reload_hz` (what `HZ`
implies), and `:1544` refuses to hand the tick over with **`-ERANGE`** when they
differ, its comment reading *"`cereload` has already made the period
deliberately wrong"*. Two different sentinels, so two absent fields cannot
compare equal and satisfy the term.

⚠️ **Scope, stated rather than left to be found**: both values are software, so
this catches a period programmed wrong and says nothing about a hardware clock
that has drifted. `docs/mfgtest.md` § 2 lists `/proc/interrupts` among
`MT-TICK`'s inputs and **this script still does not read it**; the independent
rate check is `Δjiffies` against the vendor's line 13, which `cereload` does not
touch and which seating 13's `P3-7` used. **Carried forward, not closed.**

### 2.5 `M29` was a `NO-TAKE` against the check that exists

`kickms long enough that the bite falls outside the window` moves neither field
`mt_wdt` reads: `wdtcnr_at_probe` is latched at probe and `state_name` is not a
function of the kick period. What `kickms` does is let the hardware bite, which
**resets the board** — so `MT-WDT` is not turned red, the boot simply ends.
`M29` is now `stop`, the physical counterpart of fixture row `M15`: `state_name`
leaves `BOOTGUARD`, and `bootguard` puts it back with the revert readable in the
same field.

🟢 **Two consequences.** `P1-4` no longer needs a reset at all. And the carried
instruction *"`MT-WDT` must be ordered last because its pass path resets the
board"* is **about the table in `docs/mfgtest.md` § 2, not about the script**:
`mt_wdt` issues no verb and reads two fields.

### 2.6 What the desk could NOT settle, and is going to the die as a risk

`MT-PORT` parses the vendor's `/proc/rtl865x/port_status`, whose format is 讀
only — `NET-27` says the entry exists in this image and **has never been read on
silicon**. 讀 `rtl865x_proc_debug.c:4182`: each port emits `Port%d ` then
`Force Mode disable\n`, then `EEE Status`, then either `LinkUp | …` or
`LinkDown\n\n`, so `LinkUp` is on a **later line** than the `PortN` that opens
the block — which is what `mt_port`'s block tracker is for. ⚠️ **One false
positive is possible and is not defended against**: if `EnForceMode` *and*
`PollLinkStatus` are set, `" | polling LinkUp"` lands on the `PortN` line
itself. `C2-PORT` dumps the whole file so the reading is checkable either way.

---

## 3. The order, and what forces it

1. **`LOOP` first.** The board is at the loader prompt now; `S4` sends
   `J BFC00000`, which is a watchdog reset, and `S5` is what sets `IPCONFIG` —
   量 tonight, the loader's own help lists `IPCONFIG:<TargetAddress>`, so the
   address is **not persistent** and ARP to `10.1.1.1` is `INCOMPLETE` until
   `S5` runs. The host side is already up: `10.1.1.2/24` on `enxfc19286184c9`,
   `Link detected: yes`, 100 Mb/s.
2. **`C1-AUTO` before every injection**, because `P1-3` is *the good unit
   passes* and a nine-of-nine taken after a revert is weaker evidence than one
   taken before anything was injected.
3. **Each `R` row's revert is measured before the next injection**, and the
   measurement is the full `mfgtest auto` going nine-of-nine again — not a
   `reversible` column asserting it.
4. **The operator cells are a separate phase** and may run at any time after
   `C1-AUTO`: the operator cannot see this console, so no cell may depend on
   reading a prompt at the instant it is printed. `MFG_BUTTON_SECONDS` defaults
   to **20** for that reason and nothing on this card overrides it.
5. **`C10-M28` runs the clock at a tenth**, so its own `sleep 5` costs fifty
   real seconds — `--seconds 240`, and `C11-M28r` follows it immediately.

---

## 4. The guards

* **Zero flash writes.** No `FLW`, `EW`, `EB`, `FLR` or burn anywhere on this
  card; `cardnum` rows below count them and require zero. The bracket stays at
  **1,024 of 4,194,304 = 0.0244 %** and `FLS-26`'s ledger does not move.
* **`--allow-autoexec` is never passed**, and `looprun` cannot pass it.
* `S5b` aborts unless the burn flag word at `0x8040D4A0` reads `00000000`.
  `C-6` measured the loader's echo and that word disagreeing, so the word is the
  source.
* `S6b` aborts unless the eight words at `0x80500000` are the image `S6` sent —
  `S4`'s reset re-stages that address from flash, so the alternative is a real
  image and not garbage.
* **No `--idle` shorter than a cell's own `sleep`.** `--idle N` is *N seconds
  since the last byte*; five cells of seating 20's card would have stopped
  11–21 s before their own output. `C4-BTN` and `C9-M26` carry **`--seconds`
  only**.
* Every LED cell writes `0` to the brightness first, so the transition the
  check makes is always `0 → 1` and never `1 → 1`. Whether this kernel's LED
  class short-circuits an unchanged brightness is **not known here**, and this
  removes the question rather than answering it.

---

## 5. `P1-3` — the predictions

`mfgtest auto` prints one two-space `ok`/`FAIL` line per check and then
`9 of 9 ok, 0 FAIL`.

| check | predicted line |
|---|---|
| `MT-ID` | `ok    MT-ID        recipe_id=7974982C expected=7974982C` |
| `MT-FLASH-1` | `ok    MT-FLASH-1   rdid_id=1C7016 rdid_match=1` |
| `MT-FLASH-2` | `ok    MT-FLASH-2   n_write_refused=2 n_writes=0` — **+2, and the driver's own KAT at `rtl819x-spi.c:2003` states `r0 + 2`** |
| `MT-FLASH-3` | `ok    MT-FLASH-3   map_rc=0 h601_hashed=0 diff_units=0 (digests scored at the desk)` |
| `MT-TICK` | `ok    MT-TICK      ce_live=1 ce_mode=2 reload=2000=2000 dj≈500 di≈500 skew≤2` |
| `MT-WDT` | `ok    MT-WDT       wdtcnr_at_probe=A5000000 state=BOOTGUARD` |
| `MT-PORT` | `ok    MT-PORT      Port3 LinkUp` — **only if the cable is in the jack silkscreened `LAN3`**; `NET-13` closed silkscreen→port as WAN→0, LAN1→1, LAN2→2, LAN3→3 |
| `MT-MAC` | `ok    MT-MAC       sig_ok=1 ver=1 len=<n> mac unicast` — no byte of `H601` is printed |
| `MT-RFCAL` | `ok    MT-RFCAL     hw_sum_ok=1 over <n> body bytes` |
| `MT-LED` | `ok    MT-LED       dat=0000003C bit6=0 …` + the operator sees LED #2 of eight lit |
| `MT-BUTTON` | `ok    MT-BUTTON    n_open 0->1 n_poll 0->~400 b0_n_press 0->1` |

🔴 **`MT-PORT` is the one row whose prediction depends on something nobody has
measured tonight** — which jack the cable is in. If it reads
`Port3 has no LinkUp`, `C2-PORT`'s dump names the port that *is* up and the
operator moves the cable; that is a cable, not a failure, and it costs no power
cycle.

⚠️ `n_poll 0->~400`: 20 Hz over the 20 s window, and the exact number is not
predicted because the window includes shell latency at both ends. What is
predicted is `> 0` on all three counters.

---

## 6. `P1-4` — five physical injections, each with a measured revert

| id | typed | kills | predicted red line | revert, measured before the next |
|---|---|---|---|---|
| `M27` | `corrupt 0x9000` | `MT-FLASH-3` | `map_diff_units` > 0 → `8 of 9 ok, 1 FAIL` | `corrupt off` → nine of nine |
| `M28` | `cereload 20000` | `MT-TICK` | `reload=20000 want=2000` → `8 of 9` | `cereload 2000` → nine of nine |
| `M29` | `stop` | `MT-WDT` | `state=STOPPED (want BOOTGUARD)` → `8 of 9` | `bootguard` → nine of nine |
| `M25` | `lock 6` | `MT-LED` | `n_set_ok` and `n_writes` **unmoved**, lamp **stays lit** through a `brightness ← 0` | `unlock 6` → `1 of 1 ok` and the lamp obeys again |
| `M26` | nothing — **do not press** | `MT-BUTTON` | `n_open 1->2 n_poll rising b0_n_press flat` → `0 of 1 ok, 1 FAIL` | none needed; the positive run is `C4-BTN` |

🔴 **`M26`'s red line is the finding, not the red.** The first two terms must
MOVE and the third must not. A red with all three flat would mean the node did
not open, which is § 2.1's defect and not the button — **`NO-TAKE`, and it gets
that name rather than `SURVIVOR`.**

🔴 **`M25` is read in two places and they must agree**: `n_writes` unmoved says
the refusal is ordered *before* the write, and the operator's eye says the lamp
never went out. A refusal logged *after* a write would move `n_writes` and dim
the lamp.

---

## 7. What this block does NOT claim

1. **Nothing about flash content.** No `FLR`, no full re-dump. *Not one flash
   byte is written* stays unsayable; `MT-FLASH-3`'s device-side half says the
   traversal completed, hashed nothing inside `H601`, and that the two read
   paths agree — the digest-against-reference half is `tools/flashmap.py`'s, at
   the desk.
2. **Nothing about the tick's absolute rate** — § 2.4.
3. **Nothing about `MT-DDR`**, struck in `docs/mfgtest.md` § 2 with its reason.
4. **`rlxfw-spi 1.2` has still never run on silicon before this seating**;
   `rdid_ran` and `h601_ran` have read 0 in every dump to date, so `MT-FLASH-1`,
   `MT-MAC` and `MT-RFCAL` are all first readings.
5. The `--absent` pair pins the marks against **two vendor artefacts**, not
   against every image this board could hold.

---

## 8. The cells

`H` = host, `L` = at the loader prompt, `S` = at the Linux shell.
`<ID>` is `7974982c` throughout — typed lower case **on purpose**, because
§ 2.2's fix is what makes that pass and a card typing it upper case would not
exercise the fix.

### 8.1 Phase A — nothing here needs the operator

```
#-- L. reset -> rescue -> burnflag -> hostlink -> upload -> staged head -> boot -> assert.
/usr/bin/python3 tools/looprun.py --mode bench --cell p11d --out-dir bench/2026-09-17 --port /dev/ttyUSB0 --host 10.1.1.1 --skip S2 --recipe-override 7974982c --cell-top /home/key/fwre-work/rebuild/r3-4/cells/p11d/top
```

```
#-- S. P1-3's nine.  The board prints the id the build computed, typed by nobody but me.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C1-AUTO --send '/bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 150
#-- S. FW-42's debt, one line, NO PIPE.  bench/2026-09-06c/X18-procls.log was destroyed by busybox grep -E.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C2-PROCLS --send 'ls /proc' --idle 3 --seconds 20
#-- S. the whole port file, so MT-PORT's verdict is checkable against the format NET-27 says is unread.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C2-PORT --send 'cat /proc/rtl865x/port_status' --idle 3 --seconds 25
#-- S. M27 in, MT-FLASH-3 red.  0x9000 is where seating 16's bisection put the one known difference.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C5-M27 --send 'echo corrupt 0x9000 > /proc/rtl819x-spi ; /bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 150
#-- S. M27 out.  Nine of nine IS the revert measurement.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C6-M27r --send 'echo corrupt off > /proc/rtl819x-spi ; /bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 150
#-- S. M28 in.  The clock now runs at a tenth, so this cell's own sleep 5 costs fifty real seconds.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C10-M28 --send 'echo cereload 20000 > /proc/rtl819x-timer ; /bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 240
#-- S. M28 out, immediately.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C11-M28r --send 'echo cereload 2000 > /proc/rtl819x-timer ; /bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 240
#-- S. M29 in.  `stop` and not `kickms`: 2.5.  Nothing resets.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C12-M29 --send 'echo stop > /proc/rtl819x-wdt ; /bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 150
#-- S. M29 out.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C13-M29r --send 'echo bootguard > /proc/rtl819x-wdt ; /bin/mfgtest auto 7974982c' --until ' of 9 ok' --seconds 150
```

### 8.2 Phase B — the operator is at the board

```
#-- S. MT-LED positive.  The echo 0 makes the transition 0 -> 1 rather than 1 -> 1.  OPERATOR: is LED #2 of eight lit?
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C3-LED --send 'echo 0 > /sys/class/leds/n150rt:green:led2/brightness ; /bin/mfgtest led' --until ' of 1 ok' --seconds 30
#-- S. M25 in.  lock 6, then a brightness of ZERO: the lamp must STAY LIT and n_writes must not move.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C7-M25 --send 'echo lock 6 > /proc/rtl819x-gpio ; echo 0 > /sys/class/leds/n150rt:green:led2/brightness ; /bin/mfgtest led' --until ' of 1 ok' --seconds 30
#-- S. M25 out.  The lamp obeys again.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C8-M25r --send 'echo unlock 6 > /proc/rtl819x-gpio ; echo 0 > /sys/class/leds/n150rt:green:led2/brightness ; /bin/mfgtest led' --until ' of 1 ok' --seconds 30
#-- S. MT-BUTTON positive.  A 20 s window; OPERATOR presses and holds ~3 s any time inside it.  NO --idle.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C4-BTN --send '/bin/mfgtest button' --seconds 60
#-- S. M26.  DO NOT PRESS.  n_open and n_poll must MOVE and b0_n_press must not.  NO --idle.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17/C9-M26 --send '/bin/mfgtest button' --seconds 60
```

### 8.3 The numbers this card states, and where each is re-derived FROM

```cardnum
p11d-bytes	4170754	size /home/key/fwre-work/rebuild/r3-4/out/p11d.vmlinux.elf
p11d-sha16	6f4ab5c3180053ff	sha256-16 /home/key/fwre-work/rebuild/r3-4/out/p11d.vmlinux.elf
cells-fence	14	count bench/2026-09-17/PREDICTIONS-B24-block23.md ^bench/2026-09-17/C[0-9]+-[A-Za-z0-9]+$
send-over-127	0	count bench/2026-09-17/PREDICTIONS-B24-block23.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-17/PREDICTIONS-B24-block23.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
no-flr	0	count bench/2026-09-17/PREDICTIONS-B24-block23.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-17/PREDICTIONS-B24-block23.md -{2}send '[^']*(EW |EB |FLW )
no-autoexec	0	count bench/2026-09-17/PREDICTIONS-B24-block23.md ^/usr/bin/python3 .*(allow-autoexec|boot[.]img)
no-kickms	0	count bench/2026-09-17/PREDICTIONS-B24-block23.md -{2}send '[^']*kickms
```

---

## 9. The fence

```cells
bench/2026-09-17/C1-AUTO
bench/2026-09-17/C2-PROCLS
bench/2026-09-17/C2-PORT
bench/2026-09-17/C3-LED
bench/2026-09-17/C4-BTN
bench/2026-09-17/C5-M27
bench/2026-09-17/C6-M27r
bench/2026-09-17/C7-M25
bench/2026-09-17/C8-M25r
bench/2026-09-17/C9-M26
bench/2026-09-17/C10-M28
bench/2026-09-17/C11-M28r
bench/2026-09-17/C12-M29
bench/2026-09-17/C13-M29r
```

⚠️ **`looprun`'s own four captures — `p11d-rz`, `p11d-ab2`, `p11d-2a`,
`p11d-boot` — are deliberately outside this fence**, because the tool asserts
over them itself and `S8` is its verdict, not this card's. `14 of 14` therefore
means *every cell this card types*, and it does **not** mean *every capture the
seating produced*. Seating 15's card had a malformed fence that read `0 of 5`
and looked correct; this note exists so the number's scope is stated rather than
assumed.

---

## 10. The drop order, if the window closes

1. `C2-PROCLS` — a debt, not a result.
2. `C12-M29` / `C13-M29r` — `MT-WDT`'s row also has fixture kills `M14`/`M15`.
3. `C10-M28` / `C11-M28r` — the most expensive pair, 8 minutes for two cells.
4. **Never dropped**: `C1-AUTO`, `C3-LED`, `C4-BTN`, `C9-M26`. The first is all
   of `P1-3`'s automatic half; the last three are the only rows on this card
   that cannot be simulated at a desk, and `C9-M26` is the one whose red line
   is the finding.
