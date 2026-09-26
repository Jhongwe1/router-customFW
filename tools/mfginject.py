#!/usr/bin/env python3
"""The injection harness for `config/mfgtest.sh`.  P1-2.

Every check in `docs/mfgtest.md` 2 has to be made to FAIL once, or its green
is a claim about a check that has never been observed doing anything.  This is
the half of that which can be done at a desk, with no board and no power.

WHY A DESK HARNESS IS POSSIBLE AT ALL
-------------------------------------
`mfgtest.sh` reads every surface through `$MFG_ROOT`.  Point it at a directory
of fixture files and its whole comparator layer runs here.  `docs/mfgtest.md`
2 already classes four rows **S** -- *simulated at the boundary; they prove the
check's logic, not its wiring* -- and this is that boundary, made executable
instead of described.

What that buys, concretely: `MT-FLASH-1`'s injection is *feed the comparator a
wrong id*.  On the die that would mean a different flash chip, which this
project does not have and could not fit.  Here it is one line of a fixture.

WHAT IT CANNOT DO, STATED RATHER THAN DISCOVERED LATER
------------------------------------------------------
  * It proves the SCRIPT's logic.  It says nothing about whether the driver
    fills those fields correctly -- that is `P1-3`, on the silicon.
  * The fixture is written by the same hand as the script, so on its own it
    cannot show the field NAMES match the driver.  `C1` is the control for
    exactly that: it takes the driver's own `sprintf` format strings out of
    the C and requires every name the script reads to be one the driver
    emits.  Without `C1` this suite could pass against a fixture describing a
    driver that does not exist.
  * Physical injections -- unplug the cable, `lock 6`, do not press the
    button -- are classes **R** and **P** and cannot happen here.  They are
    DECLARED below and stood down, so `P1-4` inherits a table rather than a
    memory.

THE CONTRACT, AND IT IS THE REPOSITORY'S, NOT A NEW ONE
-------------------------------------------------------
Copied structurally from `tools/test-flrbracket-mutants.py` and
`tools/test-looptime-mutants.py`, which are the two suites that implement it
as structure rather than as a regex over a label:

  1. Every row NAMES the check it must turn red, as a positional FIELD.  量
     2026-09-17: `tools/test-rbcheck.py` still has EIGHT rows with no
     `(kills ...)` suffix, which fall back to bare `rc != 0` -- and
     `docs/mfgtest.md` 3 says eleven, a 量-marked number that was already
     wrong when it was written (that file last changed 2026-09-14, two days
     before the design document quoted it).  A field cannot be absent.
  2. A kill is `rc != 0` AND the named check among the reds.  Anything else
     is WRONG-CASE, which is a survivor wearing another name.
  3. SURVIVOR means the check it names does not work.  It is not a pass.
  4. DECLARED is typed, not computed.  A count derived from the table it
     checks catches nothing.
  5. A REFUSING baseline, run THROUGH this harness and not at some other
     root, because a baseline that cannot see the harness's own breakage is
     not a baseline.
  6. NO-TAKE -- the injection did not happen.  The hardware analogue of
     INVALID-MUTANT, and here it is a fixture edit that changed no byte.
  7. At least one row REQUIRED TO SURVIVE.  量 2026-08-31, on
     `test-replay-capture-mutants.py`: the only thing that caught an
     always-red harness was the row that had to live.  A suite in which
     everything dies and a suite whose subject is simply broken print the
     same transcript.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "config", "mfgtest.sh")
DRIVER = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30",
                      "drivers", "mtd", "devices", "rtl819x-spi.c")
CENSUS = os.path.join(ROOT, "config", "image-commands.tsv")

#: The recipe id the fixture claims.  Any eight hex digits; it is compared
#: against what the caller passes, so the VALUE is irrelevant and the
#: AGREEMENT is the check.
FIXTURE_ID = "C433013B"

#: How long `MT-TICK` samples for under the harness.  Short, because the
#: tolerance in the script is absolute: a shorter window is a stricter test.
TICK_SECONDS = 2
#: When the second timer state is written, as a fraction of the window.  Well
#: inside it on both sides.
TICK_WRITE_AT = 0.6

# ---------------------------------------------------------------------------
# The healthy unit.  Field names and formats are the driver's; values are a
# real capture's where one exists (bench/2026-09-08/C1-F.log) and a stated
# expectation where the field is new in 1.2.
# ---------------------------------------------------------------------------

SPI_A = """version rtl819x-spi 1.2
added 1
add_rc 0
mtd_index 2
kat_rc 0
wedged 0
sfcr FFC00000
sfcr2 0BA08000
sfcsr C8000000
boot_sfcr FFC00000
boot_sfcr2 0BA08000
boot_sfcsr C8000000
sfcr_as_loader 0
sfcr_as_kernel 1
cs_idle 1
n_xfer 4115
n_reg_writes 49380
n_pio_bytes 16846856
n_mmio_bytes 12652544
n_mtd_read 1024
n_rdy_timeout 0
n_state_foreign 0
n_state_bad 0
n_writes 0
n_write_refused 2
v_ran 1
v_rc 0
cmp_bytes 4194304
cmp_equal 1
cmp_first_diff -1
cmp_diff_bytes 0
digest_bytes 4186112
complement_expected 4186112
h601_skipped 8192
h601_hashed 0
corrupt_at -1
d1_match 0
d1_d3_agree 1
v_start 0
v_len 4194304
v_jiffies 1328
hz 100
map_ran 1
map_rc 0
map_level 0
map_group 0
map_jiffies 41
recipe_id %(rid)s
n_rdid 1
rdid_ran 1
rdid_rc 0
rdid_id 1C7016
rdid_expect 1C7016
rdid_match 1
h601_ran 1
h601_rc 0
hw_sig_ok 1
hw_ver 1
hw_len 1166
hw_len_sane 1
hw_sum_ok 1
mac_not_zero 1
mac_not_ff 1
mac_group_bit 0
proc_bytes_before_this_line 900
"""

MAP_A = """version rtl819x-spi 1.2
map_ran 1
map_rc 0
map_level 0
map_group 0
map_unit 131072
map_entries 32
map_hashed 4186112
map_h601_skipped 8192
map_h601_hashed 0
map_diff_units 0
map_jiffies 41
hz 100
corrupt_at -1
map_truncated 0
map_lines 32
"""

# 🔴 `name=value`, NOT `name value`.  量 2026-09-17: rtl819x-timer emits 100
# fields in the `name=%d` form and ZERO in the space form every
# other driver here uses.  The first fixture was written in the space form,
# which agreed with the first parser and disagreed with the die -- C1 is what
# separated them.  And the jiffies field is `jiffies`; `j_now` is the KEYS
# driver's name for the same quantity.
TIMER_A = """ce_registered=1
ce_live=1
ce_mode=2
ce_mode_calls=2
irq_spurious=0
irq_stuck=0
ce_rating=0
ce_reload=2000
ce_reload_hz=2000
jiffies=100000
irq_count=200000
"""

# The same file two seconds later: 100 Hz, so both counters advance by the
# same amount.  This is what makes MT-TICK's delta real under a fixture.
TIMER_B = """ce_registered=1
ce_live=1
ce_mode=2
ce_mode_calls=2
irq_spurious=0
irq_stuck=0
ce_rating=0
ce_reload=2000
ce_reload_hz=2000
jiffies=100200
irq_count=200200
"""

WDT_A = """version rtl819x-wdt 1.0
registered 1
misc_rc 0
wdtcnr_at_probe A5000000
state_name BOOTGUARD
n_arm 1
n_hw_kick 343
hw_ovsel 9
"""

GPIO_A = """version rtl819x-pabcd 1.0
cnr FFFFFF8B
dir FF000040
dat 0000007C
n_writes 2
n_set_ok 0
n_set_no 0
n_req_ok 2
allow_out_mask 00000040
"""

GPIO_B = """version rtl819x-pabcd 1.0
cnr FFFFFF8B
dir FF000040
dat 0000003C
n_writes 3
n_set_ok 1
n_set_no 0
n_req_ok 2
allow_out_mask 00000040
"""

KEYS_A = """version rtl819x-keys 1.0
n_open 0
n_poll 0
n_report 0
"""

KEYS_B = """version rtl819x-keys 1.0
n_open 1
n_poll 60
n_report 2
"""

# The vendor NIC driver's own format, 讀 rtl865x_proc_debug.c:4182-4246.
# Port3 is the jack -- 量 NET-13, this kernel's netdev map is the mirror of
# the vendor's, so the operator's hole is SWITCH port 3 (this kernel's eth4).
# A down port prints LinkDown and `continue`s, so it emits three fewer lines.
PORT_A = """Dump Port Status:
Port0 Force Mode disable
EEE Status 0
LinkDown

Port1 Force Mode disable
EEE Status 0
LinkDown

Port2 Force Mode disable
EEE Status 0
LinkDown

Port3 Force Mode disable
EEE Status 0
LinkUp | NWay Mode Enabled
\tRXPause Enabled | TXPause Enabled
\tDuplex Enabled | Speed 100M

Port4 Force Mode disable
EEE Status 0
LinkDown

Port5 Force Mode disable
EEE Status 0
LinkDown

CPUPort Force Mode disable
EEE Status 0
LinkUp | NWay Mode Disabled
\tRXPause Enabled | TXPause Enabled
\tDuplex Enabled | Speed 100M

"""

PORT_DOWN = PORT_A.replace(
    "Port3 Force Mode disable\nEEE Status 0\n"
    "LinkUp | NWay Mode Enabled\n"
    "\tRXPause Enabled | TXPause Enabled\n"
    "\tDuplex Enabled | Speed 100M\n",
    "Port3 Force Mode disable\nEEE Status 0\nLinkDown\n")

# 🔄 R6b-6, 2026-09-26: MT-PORT reads rlxfw's `/proc/rtl819x-switch` 1.2 and
# not the vendor's port_status, which leaves with the vendor tree at R6b-8.
# PORT_A stays in state A only as the vendor tree's PRESENCE -- the script
# tests `[ -d .../proc/rtl865x ]` for its label and reads nothing in it.
# The format is 1.2's sprintf strings (C1 reads them); the PSRP words are the
# loader-state readings `NET-10` holds (ports 0-4 `000010E0` but the cable's
# port 3 `000010F9`, PSRP5 `000000E2`, PSRP6/7 `0000007A`), and the table is
# cut to its first rows -- mfgtest reads `version` and `psrp3`, nothing else.
SWITCH_A = """version rtl819x-switch 1.2
nreg 37
unlocked 1
n_writes 1
n_refused 0
n_reads 1120
n_reset 0
n_dumb 0
n_restore 0
boot_cvidr 81964000
slot0_full 1
slot1_full 0
slot2_full 0
slot3_full 0
n_linkq 0
lde0 00
psrp0 000010E0 up 0 lde 0 lj 0
psrp1 000010E0 up 0 lde 0 lj 0
psrp2 000010E0 up 0 lde 0 lj 0
psrp3 000010F9 up 1 lde 0 lj 0
psrp4 000010E0 up 0 lde 0 lj 0
psrp5 000000E2 up 0 lde 0 lj 0
psrp6 0000007A up 1 lde 0 lj 0
psrp7 0000007A up 1 lde 0 lj 0
jiffies 4294940001
r CVIDR     4200 81964000 81964000 00
r SSIR      4204 00000001 00000000 00
"""

# The same page with no version line: a reporter nobody can name.
SWITCH_NOVER = SWITCH_A.replace("version rtl819x-switch 1.2\n", "", 1)

# 1.1's page: a version line, and no psrp line at all.  The image that
# boots 1.1 must make MT-PORT red, never green on a missing line.
SWITCH_11 = "\n".join(ln for ln in SWITCH_A.split("\n")
                      if not ln.startswith(("psrp", "lde0", "n_linkq",
                                            "jiffies"))).replace(
    "version rtl819x-switch 1.2", "version rtl819x-switch 1.1")

#: An edit value that DELETES the file, so a directory the script tests with
#: `[ -d ]` can be made absent.  Not a string, so no fixture can equal it.
ABSENT = object()


def state_a(rid=FIXTURE_ID):
    return {
        "proc/rtl819x-spi": SPI_A % {"rid": rid},
        "proc/rtl819x-spi-map": MAP_A,
        "proc/rtl819x-timer": TIMER_A,
        "proc/rtl819x-wdt": WDT_A,
        "proc/rtl819x-gpio": GPIO_A,
        "proc/rtl819x-keys": KEYS_A,
        "proc/rtl819x-switch": SWITCH_A,
        "proc/rtl865x/port_status": PORT_A,
        "sys/class/leds/n150rt:green:led2/brightness": "0\n",
    }


def state_b():
    """Only what moves.  Everything else stays as state A wrote it."""
    return {
        "proc/rtl819x-timer": TIMER_B,
        "proc/rtl819x-gpio": GPIO_B,
        "proc/rtl819x-keys": KEYS_B,
    }


# ---------------------------------------------------------------------------
# The table.
#
#   (id, klass, what it does, the check that must go red, edits, flags)
#
# `edits` is a list of (which_state, relpath, field, new_value).  A field of
# None replaces the WHOLE file, which is how a format-level break is
# expressed.  `which_state` is "A" or "B".
# ---------------------------------------------------------------------------

EQUIV = "equivalent"
BENCH = "bench-only"
#: A row that must stay GREEN and print a stated text on its check's line.
#: The flag is (GREEN, text); EQUIV proves only that no check moved, and
#: M32's claim is stronger -- that MT-PORT passes AND says why.
GREEN = "green-with"

MUT = [
    # ---- MT-ID -----------------------------------------------------------
    ("M1", "S", "the recipe id the board reports is not the one the build computed",
     "MT-ID", [("A", "proc/rtl819x-spi", "recipe_id", "DEADBEEF")], None),
    ("M2", "S", "the driver was built with --id-scope main, so the field is absent",
     "MT-ID", [("A", "proc/rtl819x-spi", "recipe_id", "absent")], None),

    # ---- MT-FLASH-1 ------------------------------------------------------
    ("M3", "S", "a different flash part answers RDID",
     "MT-FLASH-1", [("A", "proc/rtl819x-spi", "rdid_id", "C22016"),
                    ("A", "proc/rtl819x-spi", "rdid_match", "0")], None),
    ("M4", "S", "the kernel's own comparator disagrees with the script's",
     "MT-FLASH-1", [("A", "proc/rtl819x-spi", "rdid_match", "0")], None),
    ("M5", "S", "the RDID transaction returned an error",
     "MT-FLASH-1", [("A", "proc/rtl819x-spi", "rdid_rc", "-5")], None),

    # ---- MT-FLASH-2 ------------------------------------------------------
    ("M6", "S", "a write reached the chip",
     "MT-FLASH-2", [("A", "proc/rtl819x-spi", "n_writes", "1")], None),

    # ---- MT-FLASH-3 ------------------------------------------------------
    ("M7", "S", "the two read paths disagree over one unit",
     "MT-FLASH-3", [("A", "proc/rtl819x-spi-map", "map_diff_units", "1")], None),
    ("M8", "S", "the traversal hashed bytes inside H601",
     "MT-FLASH-3", [("A", "proc/rtl819x-spi-map", "map_h601_hashed", "4096")], None),
    ("M9", "S", "the map did not complete",
     "MT-FLASH-3", [("A", "proc/rtl819x-spi-map", "map_rc", "-110")], None),

    # ---- MT-TICK ---------------------------------------------------------
    ("M10", "S", "the clockevent is registered but not live",
     "MT-TICK", [("A", "proc/rtl819x-timer", "ce_live", "0")], None),
    ("M11", "S", "the tick core never switched to PERIODIC",
     "MT-TICK", [("A", "proc/rtl819x-timer", "ce_mode", "0")], None),
    ("M12", "S", "interrupts arrive but jiffies does not advance -- a lost-tick fault",
     "MT-TICK", [("B", "proc/rtl819x-timer", "jiffies", "100000")], None),
    ("M13", "S", "a spurious interrupt was counted",
     "MT-TICK", [("A", "proc/rtl819x-timer", "irq_spurious", "3")], None),

    # ---- MT-WDT ----------------------------------------------------------
    ("M14", "S", "the vendor watchdog is still armed -- CONFIG_RTL_WTDOG=n did not take",
     "MT-WDT", [("A", "proc/rtl819x-wdt", "wdtcnr_at_probe", "00600000")], None),
    ("M15", "S", "nothing is feeding the watchdog",
     "MT-WDT", [("A", "proc/rtl819x-wdt", "state_name", "IDLE")], None),

    # ---- MT-PORT ---------------------------------------------------------
    # 🔄 R6b-6: the fixture moved to /proc/rtl819x-switch; M16's injection
    # is now psrp3's `up 0`, the line 1.2 prints for a port whose bit 4 is
    # clear.  PORT_DOWN stays defined above for the record of what M16 was.
    ("M16", "P", "the cable is out of the jack",
     "MT-PORT", [("A", "proc/rtl819x-switch", "psrp3",
                  "000010E9 up 0 lde 1 lj 4294937500")], None),

    # ---- MT-MAC ----------------------------------------------------------
    ("M17", "S", "the block is not the uncompressed H6 form",
     "MT-MAC", [("A", "proc/rtl819x-spi", "hw_sig_ok", "0")], None),
    ("M18", "S", "a blanked MAC -- all 00",
     "MT-MAC", [("A", "proc/rtl819x-spi", "mac_not_zero", "0")], None),
    ("M19", "S", "an erased MAC -- all FF",
     "MT-MAC", [("A", "proc/rtl819x-spi", "mac_not_ff", "0")], None),
    ("M20", "S", "the group bit is set, so it is not a usable station address",
     "MT-MAC", [("A", "proc/rtl819x-spi", "mac_group_bit", "1")], None),
    ("M21", "S", "a length that would have run off the end of the window",
     "MT-MAC", [("A", "proc/rtl819x-spi", "hw_len_sane", "0")], None),
    ("M22", "S", "the wrong hardware-settings version",
     "MT-MAC", [("A", "proc/rtl819x-spi", "hw_ver", "3")], None),

    # ---- MT-RFCAL --------------------------------------------------------
    ("M23", "S", "the body checksum does not close",
     "MT-RFCAL", [("A", "proc/rtl819x-spi", "hw_sum_ok", "0")], None),

    # ---- the row that must LIVE -----------------------------------------
    ("M24", "S", "a counter no check reads is changed",
     None, [("A", "proc/rtl819x-spi", "n_reg_writes", "999999")], EQUIV),

    # ---- physical, and they cannot happen here ---------------------------
    ("M25", "R", "lock 6 first, so the LED write is refused before it happens",
     "MT-LED", [], BENCH),
    ("M26", "P", "do not press the button; the counters must stay flat",
     "MT-BUTTON", [], BENCH),
    ("M27", "R", "corrupt the RAM copy so the two read paths disagree on the die",
     "MT-FLASH-3", [], BENCH),
    ("M28", "R", "cereload to a wrong value; ce_reload then differs from "
                 "ce_reload_hz, which is the driver's own -ERANGE criterion",
     "MT-TICK", [], BENCH),
    # 🔴 M29 WAS `kickms long enough that the bite falls outside the window`
    # and that was a NO-TAKE against the check that exists.  量 2026-09-17,
    # reading mt_wdt: it scores `wdtcnr_at_probe` -- latched at probe and not
    # writable at run time -- and `state_name`.  `kickms` moves NEITHER.  What
    # it does is let the hardware bite, which resets the board, so MT-WDT is
    # not turned red: the boot ends and no check runs at all.
    #
    # `stop` is the physical counterpart of fixture row M15, "nothing is
    # feeding the watchdog": state_name leaves BOOTGUARD, mt_wdt's second term
    # fails, and `bootguard` puts it back with the revert MEASURABLE in the
    # same field.  It also costs no reset, so P1-4 no longer needs one.
    ("M29", "R", "stop, so nothing is arming the watchdog and state_name "
                 "leaves BOOTGUARD",
     "MT-WDT", [], BENCH),
    # 🟢 The DESK half of M28.  M28 is class R and needs the die; this is the
    # same fault at the fixture boundary, so the term M28 relies on is tested
    # before any board is powered -- which is the whole reason the class-S
    # rows exist.
    ("M30", "S", "the tick period was reprogrammed: ce_reload no longer "
                 "matches the ce_reload_hz that HZ implies",
     "MT-TICK", [("A", "proc/rtl819x-timer", "ce_reload", "20000"),
                 ("B", "proc/rtl819x-timer", "ce_reload", "20000")], None),

    # ---- MT-PORT, R6b-6: the label is a tested conjunct ------------------
    ("M31", "S", "the switch page has no version line, so nobody can be named "
                 "as the reporter",
     "MT-PORT", [("A", "proc/rtl819x-switch", None, SWITCH_NOVER)], None),
    # 🟢 The desk proof of "outlives R6b-8": the vendor tree is gone and
    # MT-PORT must still pass, and say so.  REQUIRED TO SURVIVE, with its text.
    ("M32", "S", "the vendor tree is absent (R6b-8's image): MT-PORT must stay "
                 "green and say `vendor tree absent`",
     "MT-PORT", [("A", "proc/rtl865x/port_status", None, ABSENT)],
     (GREEN, "Port3 LinkUp by rtl819x-switch 1.2; vendor tree absent")),
    ("M33", "S", "an image that boots switch 1.1: a version line and no psrp "
                 "line, which must be red and never a silent pass",
     "MT-PORT", [("A", "proc/rtl819x-switch", None, SWITCH_11)], None),
    ("M34", "S", "the wrong jack: port 2 is up and port 3 is down",
     "MT-PORT", [("A", "proc/rtl819x-switch", "psrp2",
                  "000010F9 up 1 lde 0 lj 0"),
                 ("A", "proc/rtl819x-switch", "psrp3",
                  "000010E0 up 0 lde 0 lj 0")], None),
]

#: TYPED, never computed.  A deleted row would otherwise read as
#: "n of n killed, 0 alive" and exit 0.
#: 🔄 30 -> 34 on 2026-09-26 (R6b-6): M31-M34, all runnable.
DECLARED = 34
#: Of those, the ones this harness can actually run.
DECLARED_RUNNABLE = 29

CASE_RE = re.compile(r"^ {2}(ok|FAIL)\s{2,}(\S+)")


def write_state(root, files):
    for rel, text in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def apply_edits(files, edits, which):
    """-> (new_files, took).  `took` is False when nothing changed, which is
    NO-TAKE and never a survivor."""
    out = dict(files)
    took = False
    for state, rel, fieldname, value in edits:
        if state != which:
            continue
        if rel not in out:
            continue
        if fieldname is None and value is ABSENT:
            del out[rel]
            took = True
            continue
        if fieldname is None:
            if out[rel] != value:
                out[rel] = value
                took = True
            continue
        lines = out[rel].split("\n")
        hit = False
        for i, ln in enumerate(lines):
            # Both driver idioms, for the reason config/mfgtest.sh's field()
            # gives: rtl819x-timer emits `name=value` and every other driver
            # here emits `name value`.  An editor that knew only one would
            # silently NO-TAKE on every timer row -- which is a survivor that
            # looks like a harness limitation instead of a broken check.
            if ln.split(" ")[0:1] == [fieldname]:
                new = "%s %s" % (fieldname, value)
            elif ln.startswith(fieldname + "="):
                new = "%s=%s" % (fieldname, value)
            else:
                continue
            if new != ln:
                lines[i] = new
                took = True
            hit = True
            break
        if not hit:
            # The field the row names is not in the fixture at all.  That is
            # the row being wrong about the driver, not the check failing.
            return out, None
        out[rel] = "\n".join(lines)
    return out, took


def reds(text):
    return {m.group(2) for m in (CASE_RE.match(ln) for ln in text.splitlines())
            if m and m.group(1) == "FAIL"}


def greens(text):
    return {m.group(2) for m in (CASE_RE.match(ln) for ln in text.splitlines())
            if m and m.group(1) == "ok"}


# ---------------------------------------------------------------------------
# C1 -- the control the fixture cannot be its own.
# ---------------------------------------------------------------------------

#: Which driver owns which /proc file the script reads.  🔴 PER-FILE AND NOT
#: A UNION, and that is the whole strength of C1: a union would pass a script
#: that reads the timer's `ce_live` out of the watchdog's file.  The first
#: version of this control read one driver and reported twelve false
#: positives; the second reads all of them and would have reported none --
#: and BOTH would have missed the real defect, which was a field read from
#: the right file under the wrong NAME.
DRIVERS = {
    "P_SPI": "drivers/mtd/devices/rtl819x-spi.c",
    "P_MAP": "drivers/mtd/devices/rtl819x-spi.c",
    "P_TIMER": "drivers/clocksource/rtl819x-timer.c",
    "P_WDT": "drivers/watchdog/rtl819x-wdt.c",
    "P_GPIO": "drivers/gpio/rtl819x-gpio.c",
    "P_KEYS": "drivers/input/keyboard/rtl819x-keys.c",
    # R6b-6: MT-PORT's file is rlxfw's own switch driver since 1.2.
    "P_PORT": "drivers/net/rtl819x-switch.c",
}
SRCROOT = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30")


def driver_fields(relpath):
    """Every field name that driver can emit, taken from its own format
    strings rather than from anything written twice.

    Both idioms: `"name %..."` (spi, wdt, gpio, keys) and `"name=%..."`
    (timer).  量 2026-09-17 by counting: the timer has 100 of the second and
    0 of the first, so a scanner that knew only one would call every timer
    field missing -- which is exactly what the first run of this control did.
    """
    src = open(os.path.join(SRCROOT, relpath), encoding="utf-8").read()
    return (set(re.findall(r'"([a-z0-9_]+) %', src)) |
            set(re.findall(r'"([a-z0-9_]+)=%', src)))


#: The board file, which is the THIRD source C1 needs.  The driver says an
#: indexed template exists; this file says how many indices are legal; the
#: script says which one it reads.  No two of those were written in one
#: thought, which is the only property that makes C1 worth running.
BOARD_SRC = os.path.join(SRCROOT, "arch", "rlx", "kernel", "rlxfw-devices.c")

#: Which board array bounds which indexed prefix, per driver.  DECLARED and
#: not inferred: a tool that guessed which array bounds `b%d_` would be
#: guessing the very thing this control exists to check.
INDEX_BOUNDS = {
    ("drivers/input/keyboard/rtl819x-keys.c", "b"): ("rlxfw_board_keys", ".code"),
    # 🔄 R6b-6: `psrp%u` is bounded by the loop that prints it, whose bound
    # is a `#define` in the driver -- a second kind of bound, read from the
    # driver's own text rather than from the board file, because the number
    # of port status registers is a property of the switch, not of the board.
    ("drivers/net/rtl819x-switch.c", "psrp"): ("#define", "RTL819X_SW_NPSRP"),
}

#: 🔄 R6b-6: the suffix is optional, because `psrp%u` has none.
INDEXED_RE = re.compile(r"^([a-z]+)([0-9]+)(_[a-z0-9_]+)?$")


def _strip_c_comments(src):
    """Comments can hold braces, and the brace walk below would trip on one.

    量: rlxfw_board_keys[]'s own initialiser carries four block comments.
    """
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"//[^\n]*", " ", src)


def driver_index_templates(relpath):
    """Fields whose NAME carries a %d -- `"b%d_n_press %lu\n"`.

    driver_fields() cannot see these: its character class stops at the `%`,
    so `b%d_n_press` reads as no field at all.  量 2026-09-17, and it is how
    this function came to exist -- C1 reported `b0_n_press not emitted by
    rtl819x-keys.c` about a field the driver emits at line 486.  The control
    was right to refuse (it could not prove the field existed) and wrong
    about the driver, so it is taught rather than relaxed.

    Returns {(prefix, suffix)}, e.g. {("b", "_n_press")}.

    🔄 R6b-6: `%u` as well as `%d`, and an empty suffix, because the switch
    driver prints `"psrp%u %08X ..."` -- which the first pattern read as no
    template at all, the same blindness as the one above.
    """
    src = open(os.path.join(SRCROOT, relpath), encoding="utf-8").read()
    return (set(re.findall(r'"([a-z0-9_]*)%[du]([a-z0-9_]*) %', src)) |
            set(re.findall(r'"([a-z0-9_]*)%[du]([a-z0-9_]*)=%', src)))


def bound_of(relpath, spec):
    """How many indices `spec` allows.  An array spec counts the board file's
    initialiser (board_array_count); a ("#define", NAME) spec reads that
    define out of the DRIVER, and it must occur exactly once with a positive
    integer.  RAISES rather than guessing, for board_array_count's reason."""
    if spec[0] != "#define":
        return board_array_count(*spec)
    src = open(os.path.join(SRCROOT, relpath), encoding="utf-8").read()
    got = re.findall(r"^#define\s+%s\s+(\d+)\b" % re.escape(spec[1]), src, re.M)
    if len(got) != 1 or int(got[0]) < 1:
        raise RuntimeError("%s: `#define %s` occurs %d time(s) with %s; the "
                           "bound would be a guess"
                           % (os.path.basename(relpath), spec[1], len(got), got))
    return int(got[0])


def bound_name(spec):
    return spec[1] if spec[0] == "#define" else "%s[]" % spec[0]


def board_array_count(symbol, member):
    """How many entries the board file declares in `symbol[]`.

    rtl819x-keys prints b%d_* for i < nbuttons, and nbuttons is
    ARRAY_SIZE(rlxfw_board_keys).  A desk tool cannot evaluate that; it can
    count the initialiser.

    Counts `member =` occurrences inside the outer braces rather than
    brace-depth, because a struct entry and a nested initialiser look the
    same to a depth counter and a gpio_keys_button carries exactly one .code.

    RAISES rather than returning a default.  A bound this tool guessed would
    make C1's refusal unfalsifiable, which is the failure this whole file is
    written against.
    """
    src = _strip_c_comments(open(BOARD_SRC, encoding="utf-8").read())
    m = re.search(r"\b%s\s*\[\s*\]\s*=\s*\{" % re.escape(symbol), src)
    if not m:
        raise RuntimeError("%s: no `%s[] = {` declaration"
                           % (os.path.basename(BOARD_SRC), symbol))
    i = m.end() - 1
    depth = 0
    body = None
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                body = src[i + 1:j]
                break
    if body is None:
        raise RuntimeError("%s: `%s[]` initialiser is not brace-balanced"
                           % (os.path.basename(BOARD_SRC), symbol))
    n = len(re.findall(re.escape(member) + r"\s*=", body))
    if n < 1:
        raise RuntimeError("%s: `%s[]` declares no `%s =`; the bound would be 0"
                           % (os.path.basename(BOARD_SRC), symbol, member))
    return n


def resolve_indexed(relpath, fld, templates, bounds):
    """(ok, why) for a field driver_fields() could not see literally.

    Three conditions, and the third is the one with teeth: the driver has the
    template, the prefix has a DECLARED bounding array, and the index is
    inside it.  Without the third, `b7_n_press` would resolve on a
    one-button board.
    """
    m = INDEXED_RE.match(fld)
    if not m:
        return False, "not an indexed name"
    prefix, idx, suffix = m.group(1), int(m.group(2)), m.group(3) or ""
    if (prefix, suffix) not in templates:
        return False, "no `%s%%d%s` template in that driver" % (prefix, suffix)
    key = (relpath, prefix)
    if key not in INDEX_BOUNDS:
        return False, "no declared bounding array for `%s%%d_` in that driver" % prefix
    spec = INDEX_BOUNDS[key]
    n = bounds[key] if key in bounds else bound_of(relpath, spec)
    bounds[key] = n
    if idx >= n:
        return False, ("index %d is outside %s, which declares %d"
                       % (idx, bound_name(spec), n))
    return True, "%s%%d%s with %d < %s=%d" % (prefix, suffix, idx,
                                              bound_name(spec), n)


#: TYPED, never computed, for the same reason DECLARED is.
#:
#: 🔴 量 2026-09-17, and this is the failure C1 exists to catch arriving in C1
#: itself.  When mt_tick, mt_led and mt_button moved to `snap` + `field
#: "$MFG_SNAP"`, the regex below stopped matching them: C1 went from **36
#: reads over 5 drivers** to **22 over 2** and PRINTED `ok`, because its
#: population floor was `checked >= 15`.  A control that silently covers less
#: prints the same green as one that covers everything.  C1b -- "the indexed
#: path must have been taken" -- is what fired.
#: 🔄 36/5 -> 38/6 on 2026-09-26 (R6b-6): MT-PORT reads `version` and
#: `psrp3` out of rtl819x-switch, the sixth driver.
DECLARED_READS = 38
DECLARED_DRIVERS = 6


def script_fields():
    """(P_ variable, field name) for every read the script makes, so the
    check can be per-file.

    🔴 A READ THROUGH THE SNAPSHOT IS ATTRIBUTED TO THE FILE THAT WAS
    SNAPSHOTTED.  `snap "$P_X"` sets the owner for the reads that follow it in
    the same function; a function boundary clears it, so a `field "$MFG_SNAP"`
    with no `snap` ahead of it is reported as UNMAPPED rather than silently
    dropped -- which is the difference between a control that shrinks and one
    that complains.
    """
    src = open(SCRIPT, encoding="utf-8").read()
    out = set()
    owner = None
    for line in src.splitlines():
        if re.match(r"^[a-z0-9_]+\(\)\s*\{", line):
            owner = None
            continue
        m = re.search(r'snap "\$(P_[A-Z]+)"', line)
        if m:
            owner = m.group(1)
            continue
        for pv, fld in re.findall(r'field "\$(P_[A-Z]+)" ([a-z0-9_]+)', line):
            out.add((pv, fld))
        for fld in re.findall(r'field "\$MFG_SNAP" ([a-z0-9_]+)', line):
            out.add((owner or "P_UNSNAPPED", fld))
    return out


def script_commands():
    """Every external command the script invokes, so it can be checked
    against what this image measurably has.

    🔴 CONSERVATIVE ON PURPOSE, and the first version was not.  It matched
    `(` as a command separator, so `$((bad + 1))` yielded a command called
    `bad`; and it scanned inside quotes, so printf's own text yielded `the`
    and `these`.  Twelve false positives on the first run.  Quoted strings
    and arithmetic expansions are removed BEFORE anything is matched, and a
    word only counts in a command position.
    """
    src = open(SCRIPT, encoding="utf-8").read()
    src = re.sub(r"^\s*#.*$", "", src, flags=re.M)          # comments
    src = re.sub(r"\$\(\(.*?\)\)", " 0 ", src, flags=re.S)  # arithmetic FIRST:
    src = re.sub(r"'[^']*'", " '' ", src)                   # it can hold quotes
    src = re.sub(r'"[^"]*"', ' "" ', src)
    src = re.sub(r"\$\{[^}]*\}", " v ", src)                # parameter expansion
    found = set()
    # A command position is the start of a line, or just after a separator,
    # or just inside a $( ).
    for seg in re.split(r"[\n;|&]+|\$\(", src):
        seg = seg.strip()
        # strip leading shell keywords, which are not commands
        while True:
            m = re.match(r"^(if|then|else|elif|while|until|do|done|case|esac|"
                         r"in|!|time)\s+", seg)
            if not m:
                break
            seg = seg[m.end():]
        m = re.match(r"^([a-z][a-z0-9_.-]*)(\s|$)", seg)
        if m:
            found.add(m.group(1))
    return found


def image_commands():
    names = set()
    with open(CENSUS, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("kind\t"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                names.add(parts[1])
    return names


def main(argv):
    shell = os.environ.get("MFG_SHELL", "/bin/dash")
    if not os.path.exists(shell):
        shell = "/bin/sh"

    print("mfginject 1.0  --  the injection harness for config/mfgtest.sh")

    # --- the population control, before anything else ---------------------
    ids = [r[0] for r in MUT]
    runnable = [r for r in MUT if r[5] != BENCH]
    if len(MUT) != DECLARED or len(set(ids)) != len(ids):
        print("the table is %d rows with %d distinct ids; DECLARED says %d."
              % (len(MUT), len(set(ids)), DECLARED))
        print("   A deleted row would read as 'n of n killed, 0 alive'.")
        return 2
    if len(runnable) != DECLARED_RUNNABLE:
        print("%d runnable rows; DECLARED_RUNNABLE says %d."
              % (len(runnable), DECLARED_RUNNABLE))
        return 2

    ok = fails = 0

    # --- C1: every field the script reads, the OWNING driver emits --------
    cache = {}
    tcache = {}
    bounds = {}
    checked = 0
    indexed = 0
    missing = []
    for pvar, fld in sorted(script_fields()):
        rel = DRIVERS.get(pvar)
        if rel is None:
            missing.append("%s (no driver mapped for %s)" % (fld, pvar))
            continue
        if rel not in cache:
            cache[rel] = driver_fields(rel)
            tcache[rel] = driver_index_templates(rel)
        checked += 1
        if fld in cache[rel]:
            continue
        got, why = resolve_indexed(rel, fld, tcache[rel], bounds)
        if got:
            indexed += 1
        else:
            missing.append("%s not emitted by %s -- %s"
                           % (fld, os.path.basename(rel), why))
    # The population half: a mapping that resolved to nothing would report
    # zero missing, which is what a control that cannot fail prints.
    biggest = max((len(v) for v in cache.values()), default=0)
    if checked != DECLARED_READS or len(cache) != DECLARED_DRIVERS:
        missing.append("POPULATION: %d read(s) over %d driver(s); DECLARED_READS "
                       "says %d over %d.  A control that covers less prints the "
                       "same green as one that covers everything"
                       % (checked, len(cache), DECLARED_READS, DECLARED_DRIVERS))
    good = not missing and biggest >= 30
    print("  %s  %-14s %s" % ("ok  " if good else "FAIL", "C1",
                              "every field the script reads is emitted by the driver "
                              "that owns that file (%d reads, %d drivers, %d by index)"
                              % (checked, len(cache), indexed)
                              if good else
                              "%s" % (missing or
                                      "the control resolved nothing: %d reads, "
                                      "largest driver %d fields" % (checked, biggest))))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # --- C1b: the index path is EXERCISED, and the bound is named ---------
    #
    # C1 above would print the same `ok` if no read had gone through
    # resolve_indexed() at all, which is a control that cannot fail on the
    # half of itself that is new.  This one requires the path to have been
    # taken and prints where the bound came from, so a reader can check it
    # against the file rather than against this tool.
    kb = ("drivers/input/keyboard/rtl819x-keys.c", "b")
    try:
        nb = board_array_count(*INDEX_BOUNDS[kb])
        err = None
    except RuntimeError as e:
        nb, err = 0, str(e)
    good = err is None and indexed >= 1 and nb >= 1
    print("  %s  %-14s %s" % ("ok  " if good else "FAIL", "C1b",
                              "%d indexed read(s) resolved; the bound is "
                              "%s[]=%d, counted in %s"
                              % (indexed, INDEX_BOUNDS[kb][0], nb,
                                 os.path.basename(BOARD_SRC))
                              if good else
                              "indexed=%d bound=%d %s" % (indexed, nb, err or "")))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # --- C1c: THE BOUND IS LOAD-BEARING, and the suffix is checked --------
    #
    # Two probes against the real driver and the real board file.  The first
    # asks for the index one past the last legal one: a control that accepted
    # it would accept `b7_n_press` on a one-button board, which is C1 giving
    # its blessing to a field that cannot exist.  The second asks for a
    # suffix no template carries, so a prefix-only match is caught too.
    rel_k = kb[0]
    if rel_k not in tcache:
        tcache[rel_k] = driver_index_templates(rel_k)
    over, over_why = resolve_indexed(rel_k, "b%d_n_press" % nb, tcache[rel_k], bounds)
    bogus, bogus_why = resolve_indexed(rel_k, "b0_no_such_field", tcache[rel_k], bounds)
    # 🔄 R6b-6: the same two-sided probe on the `#define` bound.  psrp7 must
    # resolve and psrp8 must not; 8 is typed here, so a driver whose loop
    # bound drifted is named rather than followed.
    sw = DRIVERS["P_PORT"]
    if sw not in tcache:
        tcache[sw] = driver_index_templates(sw)
    try:
        npsrp, perr = bound_of(sw, INDEX_BOUNDS[(sw, "psrp")]), ""
    except RuntimeError as e:
        npsrp, perr = 0, str(e)
    pin, pin_why = resolve_indexed(sw, "psrp%d" % (npsrp - 1), tcache[sw], bounds)
    pover, pover_why = resolve_indexed(sw, "psrp%d" % npsrp, tcache[sw], bounds)
    good = ((not over) and (not bogus) and nb >= 1
            and pin and (not pover) and npsrp == 8)
    print("  %s  %-14s %s" % ("ok  " if good else "FAIL", "C1c",
                              "b%d_n_press is REFUSED (%s) and b0_no_such_field "
                              "is REFUSED (%s); psrp%d resolves and psrp%d is "
                              "REFUSED (%s) -- the bounds and the suffix bite"
                              % (nb, over_why, bogus_why, npsrp - 1, npsrp,
                                 pover_why)
                              if good else
                              "over=%s(%s) bogus=%s(%s) psrp: bound=%d %s in=%s(%s) "
                              "over=%s(%s)"
                              % (over, over_why, bogus, bogus_why, npsrp, perr,
                                 pin, pin_why, pover, pover_why)))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # --- C1d: the port the script reads is the port it names --------------
    #
    # MT-PORT prints `$MFG_PORT` (Port3) and reads `psrp3`: two spellings of
    # one number in one script, which is one owner too many unless something
    # holds them together.  This does, both ways: the script as it is must
    # agree, and a copy whose MFG_PORT says Port2 must be caught.
    def port_agreement(text):
        mp = re.findall(r'^MFG_PORT="Port(\d+)"', text, re.M)
        reads = re.findall(r'field "\$MFG_SNAP" psrp(\d+)', text)
        return (len(mp) == 1 and len(reads) == 1 and mp[0] == reads[0],
                "MFG_PORT=Port%s, reads psrp%s" % ("/".join(mp) or "?",
                                                    "/".join(reads) or "?"))
    stext = open(SCRIPT, encoding="utf-8").read()
    agree, agree_why = port_agreement(stext)
    probe2 = stext.replace('MFG_PORT="Port3"', 'MFG_PORT="Port2"', 1)
    caught, caught_why = port_agreement(probe2)
    good = agree and probe2 != stext and not caught
    print("  %s  %-14s %s" % ("ok  " if good else "FAIL", "C1d",
                              "%s agree, and a copy saying Port2 is caught (%s)"
                              % (agree_why, caught_why)
                              if good else
                              "agree=%s (%s) probe-took=%s caught=%s (%s)"
                              % (agree, agree_why, probe2 != stext, not caught,
                                 caught_why)))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # --- C2: every command the script types exists in this image ----------
    have = image_commands()
    # Shell keywords and the script's own functions are not applets.
    builtin_kw = {"if", "then", "else", "elif", "fi", "for", "while", "do",
                  "done", "case", "esac", "in", "function", "return", "local"}
    ours = set(re.findall(r"^([a-z0-9_]+)\(\)", open(SCRIPT, encoding="utf-8").read(),
                          flags=re.M))
    want = script_commands() - builtin_kw - ours
    absent = sorted(w for w in want if w not in have)
    # A population floor.  The script deliberately uses very few commands, so
    # "0 absent" is cheap; "0 absent out of 0 scanned" is a control that
    # cannot fail, and this repository does not accept those.
    good = not absent and len(want) >= 4 and len(have) >= 80
    print("  %s  %-14s %s" % ("ok  " if good else "FAIL", "C2",
                              "every command the script types is in config/image-commands.tsv"
                              " (%d typed, %d in the image)" % (len(want), len(have))
                              if good else
                              "NOT IN IMAGE: %s (typed %d, image %d)"
                              % (absent, len(want), len(have))))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # --- C3: THE CONTROL THAT SAYS C2 IS A GUARD AND NOT A BLANKET --------
    #
    # C2 above passes.  So would a C2 whose scanner had stopped finding
    # anything -- 量, that is exactly what happened on this file's first run,
    # where a too-LOOSE scanner produced twelve false positives and the
    # obvious fix (tighten it) can overshoot into finding nothing at all.
    # This feeds the scanner a script that types `awk`, which FW-83 measured
    # absent from this image, and requires it to be caught.
    probe = open(SCRIPT, encoding="utf-8").read().replace(
        "\tsleep \"$MFG_TICK_SECONDS\"", "\tawk 'BEGIN{}' </dev/null", 1)
    took = "awk" in probe
    d3 = tempfile.mkdtemp(prefix="mfginject-c3-")
    try:
        probe_path = os.path.join(d3, "probe.sh")
        with open(probe_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(probe)
        saved = globals()["SCRIPT"]
        globals()["SCRIPT"] = probe_path
        try:
            pw = script_commands() - builtin_kw - ours
        finally:
            globals()["SCRIPT"] = saved
    finally:
        shutil.rmtree(d3, ignore_errors=True)
    caught = "awk" in pw and "awk" not in have
    good = took and caught
    print("  %s  %-14s %s" % ("ok  " if good else "FAIL", "C3",
                              "a script typing `awk` IS caught -- C2 is a guard, "
                              "not a blanket"
                              if good else
                              "the injected `awk` was not caught (injected=%s, "
                              "scanned=%s)" % (took, sorted(pw))))
    ok, fails = (ok + 1, fails) if good else (ok, fails + 1)

    # --- B0: the un-injected fixture must be all green --------------------
    d = tempfile.mkdtemp(prefix="mfginject-")
    write_state(d, state_a())
    rc, out = _run(d, FIXTURE_ID, shell, state_b())
    if rc != 0:
        print("B0 the UNINJECTED fixture is not green. Refusing to report kills:")
        print("   every injection below would be 'killed' by a run that was")
        print("   already red.  rc=%d  red: %s" % (rc, sorted(reds(out))))
        print(out)
        shutil.rmtree(d, ignore_errors=True)
        return 2
    shutil.rmtree(d, ignore_errors=True)
    print("  ok    %-14s %s" % ("B0", "the uninjected fixture is green "
                                "(%d checks) -- the kills below are the "
                                "injections" % len(greens(out))))
    ok += 1

    results = []
    for mid, klass, what, wants, edits, flag in MUT:
        if flag == BENCH:
            results.append((mid, "stood-down", klass, what, wants,
                            "class %s: physical, and P1-4 runs it on the die"
                            % klass))
            continue
        d = tempfile.mkdtemp(prefix="mfginject-")
        try:
            a, took_a = apply_edits(state_a(), edits, "A")
            b, took_b = apply_edits(state_b(), edits, "B")
            if took_a is None or took_b is None:
                results.append((mid, "NO-TAKE", klass, what, wants,
                                "a field this row names is not in the fixture"))
                continue
            if not (took_a or took_b):
                results.append((mid, "NO-TAKE", klass, what, wants,
                                "the edit changed no byte"))
                continue
            write_state(d, a)
            rc, out = _run(d, FIXTURE_ID, shell, b)
            red = reds(out)
            if isinstance(flag, tuple) and flag[0] == GREEN:
                line = [ln for ln in out.splitlines()
                        if CASE_RE.match(ln) and CASE_RE.match(ln).group(2) == wants]
                said = bool(line) and line[0].rstrip().endswith(flag[1])
                if rc == 0 and not red and said:
                    results.append((mid, "survived", klass, what, wants,
                                    "green, and %s says `%s`" % (wants, flag[1])))
                else:
                    results.append((mid, "WRONG-GREEN", klass, what, wants,
                                    "rc=%d red=%s line=%r" % (rc, sorted(red),
                                                              line[:1])))
                continue
            if flag == EQUIV:
                if rc == 0 and not red:
                    results.append((mid, "survived", klass, what, wants,
                                    "as proved: no check reads that field"))
                else:
                    results.append((mid, "KILLED-EQUIV", klass, what, wants,
                                    "the equivalence proof is stale; red: %s"
                                    % sorted(red)))
                continue
            if rc == 0:
                results.append((mid, "SURVIVOR", klass, what, wants,
                                "the run stayed GREEN"))
            elif wants not in red:
                results.append((mid, "WRONG-CASE", klass, what, wants,
                                "it went red, but on %s and not on %s"
                                % (sorted(red) or ["(no case line)"], wants)))
            else:
                results.append((mid, "killed", klass, what, wants,
                                "%s went red (%d red in total)"
                                % (wants, len(red))))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    killed = alive = stood = 0
    for mid, verdict, klass, what, wants, why in results:
        if verdict in ("killed", "survived"):
            killed += 1
            print("  ok    %-14s [%s] %s" % (mid, klass, what))
            print("        -> %s" % why)
            ok += 1
        elif verdict == "stood-down":
            stood += 1
        else:
            alive += 1
            print("  FAIL  %-14s [%s] %s" % (mid, klass, what))
            print("        -> %s: expected %s to go red; %s"
                  % (verdict, wants, why))
            fails += 1

    # ONE skip line for all of them, not one each.
    #
    # tools/ci-census.py allows a suite exactly one skip LABEL, and
    # tools/ci-expected.tsv's `covers` column is how many cases that one line
    # stands down.  Five lines with five labels would not reconcile against a
    # table that can hold one, and the failure would arrive as a
    # CENSUS-MISMATCH nobody could read.  The ids go in the reason so nothing
    # is lost.
    if stood:
        ids = " ".join(m for m, v, _k, _w, _n, _y in results
                       if v == "stood-down")
        # 🔴 TWO spaces between the label and the reason, explicitly, not a
        # %-14s pad.  ci-census's SKIP_RE is
        #   ^ {2}skip\s{2,}(label)\s{2,}(reason)$
        # so a label LONGER than the pad width gets exactly one space after
        # it and the label then swallows the reason.  量: `physical-injection`
        # is 18 characters against a 14-wide pad, and the census reported
        # UNEXPECTED-SKIP with the entire sentence as the label.
        print("  skip  %s  %s" % ("physical-injection",
                                  "%d rows need the die and the operator "
                                  "(%s) -- P1-4 runs them" % (stood, ids)))

    print("%d of %d injections killed, %d alive, %d stood down for P1-4"
          % (killed, len(results) - stood, alive, stood))
    return 1 if (alive or fails) else 0


def _run(root, rid, shell, advance_to):
    """run_once with the state-B writer bound."""
    env = dict(os.environ)
    env["MFG_ROOT"] = root
    env["MFG_TICK_SECONDS"] = str(TICK_SECONDS)
    proc = subprocess.Popen(
        [shell, SCRIPT, "auto", rid],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=ROOT, env=env, text=True, encoding="utf-8")

    def advance():
        time.sleep(TICK_SECONDS * TICK_WRITE_AT)
        try:
            write_state(root, advance_to)
        except OSError:
            pass

    t = threading.Thread(target=advance)
    t.start()
    try:
        out, _ = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        out = "(timed out)"
    t.join()
    return proc.returncode, out


if __name__ == "__main__":
    sys.exit(main(sys.argv))
