#!/usr/bin/env python3
"""viewdecode -- read /proc/rtl819x-view pages: decode them, render the vendor's
asicCounter text from them, and bracket them between two counter readings.

WHAT IT READS
-------------
`R6b-8` 8c's node, config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-view.c
(`rtl819x-view 1.0`), prints raw words and nothing else: no register name, no
meaning, no 64-bit byte count.  Those three are this tool's, and they come from
B -- the header the build compiles, drivers/net/rtl819x/AsicDriver/
rtl865xc_asicregs.h, sha256 e29c3051... -- one source each (讀 x1).  Where the
draft datasheet names a word differently, its name is printed beside B's:
LEDCR0 for LEDCREG|LEDCR, PIN_MUX_SEL_2 for PIN_MUX_SEL2.

An input is a console capture (tools/console-capture.py's .log: CRLF, the echoed
command before the page and the prompt after it) or a bare page.  CRs are
stripped FIRST.  A page is the lines from a `version rtl819x-view ...` line to
the first `jiffies N` line after it; what surrounds it belongs to the capture.
The driver owns the format: the self-test reads its 21 sprintf literals out of
the source and requires this file's copies to be the same text, and every page
decoded must re-render, through those literals, to its own bytes.

    decode FILE...           every page, its words named from B; --one-boot
                             also checks the pages as one boot, in order
    asic FILE                the vendor's /proc/rtl865x/asicCounter text for
                             the one `last mib` page in FILE, rendered from its
                             raw words the way rtl865xC_dumpAsicDiagCounter
                             prints them (rtl865x_asicCom.c:1776-1838), with
                             the byte counts as low + (high << 22) (:1506)
    bracket BEFORE VIEW AFTER
                             VIEW is a `last mib` page; BEFORE and AFTER are a
                             page or an asicCounter capture each.  For every
                             one of the 211 counters the vendor prints (7 ports
                             x 30, and CpuEvent): before <= view <= after, so
                             equality wherever the two ends are equal.  Every
                             counter outside is named; exit 1.
    --self-test [--no-mutants] [--root DIR]

WHAT IT REFUSES (exit 2), each with its reason; a refused page is never
partially decoded
-------------------------------------------------------------------------------
  version     a version line other than `version rtl819x-view 1.0`
  terminator  a page with no `jiffies N` line before the input ends or the next
              page begins: a cut page; or a `jiffies N` line with no line end,
              whose number may be cut
  no-page     an input with no page at all (for asic and bracket: not exactly
              one, `count`)
  header      the five header lines missing, out of order, or malformed
  range       a number wider than its C type (%u/%lu 32 bits, %d int32)
  admit       admit != 298: another admission table
  ref         `ref none` with an address or with refused > 0; refused 0 with a
              reason; `psrp` outside BB804128-BB804148; `out` inside it; a
              refused word that 1.0 admits
  result-none a result line under `last none`
  mib         rc != 0; ports != 7; port lines not m0..m6 in order; a port line
              whose word count differs from `mo`'s; words != 7 x mo + mc; more
              than one mc line
  tbl         rc not 0 or -16; a name other than `last`; (base, slots) not the
              table's; words != 8; slot lines not s00, s01, ... or more than
              slots; t outside 1-10; mis without t10; a slot line without eight
              words; busy with rc 0; rc -16 without busy; busy sNN != the slot
              lines; polls < slot lines, or < slot lines + 10,001 with busy
  peek        rc != 0; an address not a multiple of 4; n outside 1-16; `a`
              addresses other than A + 4i
  cut         fewer result lines than the page's own header implies
  extra       a result line after the last one the header implies
  line        a result line that is not what 1.0 prints there (an interleaved
              console line is one)
  render      the page does not re-render, through the driver's literals, to
              its own bytes (a leading zero, a doubled space)
  name        this decoder's own, beyond the format: a MIB layout (base,
              stride, mo, mc) other than 1.0's, or a peeked word 1.0 does not
              admit -- it names words by 1.0's table and would misname them
  one-boot    --one-boot only: a counter that decreased between two pages
              whose jiffies did not (a jiffies decrease voids the pair: a
              32-bit wrap and a reboot look the same, and it says so)
  asic        an asicCounter dump cut short, interleaved with other console
              output (a foreign character in front of any of its lines), a
              printk time on some of its lines and not others, or a line or a
              value the vendor's format cannot print.  A printk time on all 86
              lines is accepted and carried verbatim; a dump whose last line
              ends the input without its line end is accepted, because " pkts"
              follows the number
  input       an unreadable file; a file that is neither kind, or both

SELF-TEST (each case prints one `  ok`/`  FAIL` line, two leading spaces)
--------------------------------------------------------------------------
  A1  every committed asicCounter capture -- each tracked bench/**/*.log with
      any line of the dump in it; 266 at 8520b6c, the floor -- is one of three
      shapes, and nothing else.  Clean (23) or printk-timed (12): it parses
      into seven port sections and CpuEvent and re-renders to its own CRLF
      bytes (2 of the clean ones end inside the last CRLF) -- the parser's
      positive control on the vendor's real output.  Interleaved (231): the
      parser REFUSES it, and a self-test-only reader finds all 86 lines in
      order behind the foreign characters and re-renders them from their
      values, so the refusal is shown to be of a whole dump and not of a
      line the parser cannot read.  Each shape has its 8520b6c count as a
      floor.  (The 8c proposal's section 3 expected every capture to
      re-render; 231 of 266 cannot.)
  B1  rtl819x-view.c's 21 sprintf literals, function by function, are this
      file's copies verbatim, and they are all the sprintf calls in it; the
      version, the three name tables, eq/mis and the constants the page's
      values come from (MIB base, stride, ports, 225, PSRP0/8, tries, bound,
      peek max, table base) are this file's
  B2  synthetic pages of every kind, rendered through those literals, decode
      and re-render byte for byte, bare and wrapped as a CRLF capture
  B3  the pages tools/viewcheck.py's harness gets from the COMPILED driver
      (boot, mib, both tables, a torn slot, t10 mis, busy, peeks, two
      refusals) decode, re-render byte for byte, are the kinds the script
      asked for, and pass --one-boot
  B4  the words this decoder names are exactly the words the driver's runs
      table admits (read from the source): 298
  C1  the byte counts: built (lo, hi) pairs with hi != 0 against decimal
      values written here by hand, not computed by the tool's formula
  C2  the offsets: a page whose every word is its own offset (+ 0x1000 x port)
      rendered as asicCounter, against the vendor's lines written here a
      second time from rtl865x_asicCom.c:1784-1835 and B's offsets
  D1  bracket permitting: between, at either end, pinned -- exit 0
  D2  bracket refusing: below, above, ends reversed -- each counter named
      with its reason, exit 1, and no other counter named
  E1-E12  each refusal above, made by editing one of B2's pages (or a dump,
      or a command line) that is accepted as it stands; the refusal's code
      and the words of its reason are checked, not only that one happened

M0..M8 then mutate a COPY of this file and run its self-test (no mutants)
against the same root; each must turn the case named for it red.  M0 is the
unmutated copy through the same path, and no kill counts unless it is green.
An anchor that does not occur exactly once is a survivor, never a skip.  The
anchors below are written as split string literals ("a" "b") so that the table
does not match itself.

  M1  a swapped offset (Multicast and Broadcast)   C2
  M2  << 32 for << 22                              C1
  M3  no CRLF strip                                A1
  M4  < for <= in the bracket                      D1
  M5  the admit check removed                      E3
  M6  a cut page skipped instead of refused        E1
  M7  reversed ends not called reversed            D2
  M8  the re-render gate removed                   E2

WHAT IT CANNOT SEE
------------------
The silicon.  A decoded word is what the driver loaded, named by B alone; the
names, the VLAN and netif field layouts (B's big-endian arm) and the << 22 have
no second source here.  `asic` agreeing with a real asicCounter capture shows
this tool copies the vendor's arithmetic, not that the arithmetic is right: the
<< 22 makes the two words overlap (bits 22-31 of low), and a capture above
2^22 bytes is what exercises it on the die.  `bracket` compares what it is
given: it cannot tell a MIB read that cleared a counter from a counter that did
not move, and a view read between two asicCounter reads is only bracketed if
nothing else read the MIB in between.  B3 depends on tools/viewcheck.py's model
and on gcc; without gcc, or without git for A1, the self-test REFUSES (exit 3).
It does not read /proc/rtl819x-mdio or /proc/rtl819x-switch pages.

    viewdecode.py decode [--one-boot] FILE...
    viewdecode.py asic FILE
    viewdecode.py bracket BEFORE VIEW AFTER
    viewdecode.py --self-test [--no-mutants] [--root DIR]
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

TOOL_VERSION = "1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PARTS = ("config", "rlxfw-src", "linux-2.6.30", "drivers", "net",
                "rtl819x-view.c")

# ------------------------------------------------------------------------
# rtl819x-view 1.0, as the driver defines it (B1 checks every one of these
# against the source).
# ------------------------------------------------------------------------
VERSION = "rtl819x-view 1.0"
VERSION_PREFIX = "version rtl819x-view"
ADMIT = 298
MIB_BASE = 0xBB801000
MIB_STRIDE = 0x80
MIB_PORTS = 7
NMIB = 225
PSRP0 = 0xBB804128
PSRP8 = 0xBB804148
TRIES = 10
BOUND = 10000
PEEK_MAX = 16
TBL_BASE = 0xBB000000
EBUSY = 16
LAST_NAMES = ("none", "mib", "vlan", "netif", "peek")
WHY_NAMES = ("none", "out", "psrp")
TBL_TYPES = (("vlan", 6, 16), ("netif", 4, 8))
TABLES = {n: (TBL_BASE + (t << 16), s) for n, t, s in TBL_TYPES}
U32 = 0xFFFFFFFF
U64 = (1 << 64) - 1

# The 21 format literals, as C text between the quotes, per function in the
# order the source holds them.
FORMATS = {
    "rtl819x_view_mib_lines": [
        r"mib base %08X stride %03X ports %u words %u\n", r"mo", r" %03X",
        r"\n", r"m%u", r" %08X", r"\n", r"mc %03X %08X\n"],
    "rtl819x_view_tbl_lines": [
        r"tbl %s base %08X slots %u words %u polls %lu\n", r"s%02u t%u %s",
        r" %08X", r"\n", r"busy s%02d\n"],
    "rtl819x_view_peek_lines": [r"peek %08X n %u\n", r"a %08X %08X\n"],
    "rtl819x_view_read_proc": [
        r"version %s\n", r"admit %u\n", r"last %s j %lu rc %d\n",
        r"n_mib %lu n_tbl %lu n_peek %lu refused %lu busy %lu ld %lu\n",
        r"ref %08X %s\n", r"jiffies %lu\n"],
}
EQ_MIS = ("eq", "mis")


def c_unescape(c):
    return c.replace("\\n", "\n")


def pyfmt(c):
    """A C format as Python's %: the length modifier dropped, %u as %d."""
    return re.sub(r"%(0?[0-9]*)(?:ll|l|h)?([udxXs])",
                  lambda m: "%" + m.group(1) +
                  ("d" if m.group(2) == "u" else m.group(2)), c_unescape(c))


_F = {k: [pyfmt(c) for c in v] for k, v in FORMATS.items()}
(F_MIB, F_MO, F_MO_OFF, F_MO_END, F_PORT, F_PORT_W, F_PORT_END,
 F_MC) = _F["rtl819x_view_mib_lines"]
F_TBL, F_SLOT, F_SLOT_W, F_SLOT_END, F_BUSY = _F["rtl819x_view_tbl_lines"]
F_PEEK, F_A = _F["rtl819x_view_peek_lines"]
(F_VERSION, F_ADMIT, F_LAST, F_COUNTS, F_REF,
 F_JIFFIES) = _F["rtl819x_view_read_proc"]

# ------------------------------------------------------------------------
# B's names.  ":N" is a line of rtl865xc_asicregs.h (sha256 e29c3051...).
# ------------------------------------------------------------------------
# The per-port MIB words in page order: 1.0's `mo` line, exactly.
MIB_OFFS = ([0x100, 0x104, 0x108] + [0x114 + 4 * i for i in range(18)] +
            [0x800, 0x804, 0x808, 0x80C, 0x810, 0x818, 0x81C, 0x820, 0x824,
             0x82C, 0x834])
# B's name of each per-port counter -> (offset from the MIB base, B line).
MIB_NAME = {
    "OFFSET_IFINOCTETS_P0": (0x100, 282),
    "OFFSET_IFINUCASTPKTS_P0": (0x108, 283),
    "OFFSET_ETHERSTATSUNDERSIZEPKTS_P0": (0x114, 285),
    "OFFSET_ETHERSTATSFRAGMEMTS_P0": (0x118, 286),
    "OFFSET_ETHERSTATSPKTS64OCTETS_P0": (0x11C, 287),
    "OFFSET_ETHERSTATSPKTS65TO127OCTETS_P0": (0x120, 288),
    "OFFSET_ETHERSTATSPKTS128TO255OCTETS_P0": (0x124, 289),
    "OFFSET_ETHERSTATSPKTS256TO511OCTETS_P0": (0x128, 290),
    "OFFSET_ETHERSTATSPKTS512TO1023OCTETS_P0": (0x12C, 291),
    "OFFSET_ETHERSTATSPKTS1024TO1518OCTETS_P0": (0x130, 292),
    "OFFSET_ETHERSTATSOVERSIZEPKTS_P0": (0x134, 293),
    "OFFSET_ETHERSTATSJABBERS_P0": (0x138, 294),
    "OFFSET_ETHERSTATSMULTICASTPKTS_P0": (0x13C, 295),
    "OFFSET_ETHERSTATSBROADCASTPKTS_P0": (0x140, 296),
    "OFFSET_DOT1DTPPORTINDISCARDS_P0": (0x144, 297),
    "OFFSET_ETHERSTATSDROPEVENTS_P0": (0x148, 298),
    "OFFSET_DOT3STATSFCSERRORS_P0": (0x14C, 299),
    "OFFSET_DOT3STATSSYMBOLERRORS_P0": (0x150, 300),
    "OFFSET_DOT3CONTROLINUNKNOWNOPCODES_P0": (0x154, 301),
    "OFFSET_DOT3INPAUSEFRAMES_P0": (0x158, 302),
    "OFFSET_IFOUTOCTETS_P0": (0x800, 303),
    "OFFSET_IFOUTUCASTPKTS_P0": (0x808, 304),
    "OFFSET_IFOUTMULTICASTPKTS_P0": (0x80C, 305),
    "OFFSET_IFOUTBROADCASTPKTS_P0": (0x810, 306),
    "OFFSET_DOT3STATSSINGLECOLLISIONFRAMES_P0": (0x818, 308),
    "OFFSET_DOT3STATSMULTIPLECOLLISIONFRAMES_P0": (0x81C, 309),
    "OFFSET_DOT3STATSDEFERREDTRANSMISSIONS_P0": (0x820, 310),
    "OFFSET_DOT3STATSLATECOLLISIONS_P0": (0x824, 311),
    "OFFSET_DOT3OUTPAUSEFRAMES_P0": (0x82C, 313),
    "OFFSET_ETHERSTATSCOLLISIONS_P0": (0x834, 315),
}
# The two byte counters are word pairs: low at the named offset, high at +4.
OCTETS = ("OFFSET_IFINOCTETS_P0", "OFFSET_IFOUTOCTETS_P0")
CPUEVENT = "OFFSET_ETHERSTATSCPUEVENTPKT"
CPUEVENT_OFF, CPUEVENT_LINE = 0x084, 281
SYS = "sys"

# Every other admitted word: (address, B's name(s), B's line(s), D's name
# where it differs).
REG_NAMES = ([
    (0xBB804000, "MACCR", ":997", None),
    (0xBB804004, "MDCIOCR", ":998", None),
    (0xBB804008, "MDCIOSR", ":999", None),
    (0xBB80400C, "PMCR", ":1000", None),
    (0xBB804044, "BSCR", ":1014", None),
    (0xBB804100, "PITCR", ":1133", None)] +
    [(0xBB804104 + 4 * i, "PCRP%d" % i, ":%d" % (1134 + i), None)
     for i in range(9)] + [
    (0xBB80414C, "P0GMIICR", ":1152", None),
    (0xBB804150, "P5GMIICR", ":1153", None),
    (0xBB804200, "CVIDR", ":1401", None),
    (0xBB804204, "SSIR", ":1402", None),
    (0xBB804208, "CRMR", ":1405", None),
    (0xBB80420C, "BISTCR", ":1406", None),
    (0xBB804234, "MEMCR", ":1438", None),
    (0xBB804238, "BISTTSDR0|BISTTSDR1", ":1407 :1408", None),
    (0xBB80423C, "BISTTSDR2", ":1409", None),
    (0xBB804240, "BISTTSDR3", ":1410", None),
    (0xBB804300, "LEDCREG|LEDCR", ":2627 :2633", "LEDCR0"),
    (0xBB804304, "LEDCR1", ":2628", None),
    (0xBB80430C, "LEDBCR", ":2629", None),
    (0xBB804400, "TEACR", ":1479", None),
    (0xBB804404, "TEATCR", ":1480", None),
    (0xBB804408, "RMACR", ":1481", None),
    (0xBB80440C, "ALECR|TTLCR", ":1482 :1484", None),
    (0xBB804410, "MSCR", ":1483", None),
    (0xBB804414, "L4TOCR", ":1485", None),
    (0xBB804418, "SWTCR0", ":1486", None),
    (0xBB80441C, "SWTCR1", ":1487", None),
    (0xBB804420, "PLITIMR", ":1488", None),
    (0xBB804424, "DACLRCR", ":1489", None),
    (0xBB804428, "FFCR", ":1490", None),
    (0xBB80442C, "MGFCR_E0R0", ":1491", None),
    (0xBB804430, "MGFCR_E0R1", ":1492", None),
    (0xBB804434, "MGFCR_E0R2", ":1493", None),
    (0xBB804A00, "VCR0", ":2299", None),
    (0xBB804A04, "VCR1", ":2300", None)] +
    [(0xBB804A08 + 4 * i, "PVCR%d" % i, ":%d" % (2301 + i), None)
     for i in range(5)] + [
    (0xBB804A1C, "PBVCR0", ":2306", None),
    (0xBB804D00, "SWTACR", ":196", None),
    (0xBB804D04, "SWTASR", ":197", None),
    (0xBB804D08, "SWTAA", ":198", None),
    (0xBB804D3C, "TCR7", ":206", None),
    (0xB8010000, "CPUICR", ":492", None)] +
    [(0xB8010004 + 4 * i, "CPURPDCR%d" % i, ":%d" % (494 + i), None)
     for i in range(6)] + [
    (0xB801001C, "CPURMDCR0", ":502", None),
    (0xB8010020, "CPUTPDCR0", ":503", None),
    (0xB8010024, "CPUTPDCR1", ":504", None),
    (0xB8010028, "CPUIIMR", ":512", None),
    (0xB801002C, "CPUIISR", ":513", None),
    (0xB8010030, "CPUQDM0|CPUQDM1 (two half-words)", ":514 :515", None),
    (0xB8010034, "CPUQDM2|CPUQDM3 (two half-words)", ":516 :517", None),
    (0xB8010038, "CPUQDM4|CPUQDM5 (two half-words)", ":518 :519", None),
    (0xB8010060, "CPUTPDCR2", ":508", None),
    (0xB8010064, "CPUTPDCR3", ":509", None),
    (0xB8000040, "PIN_MUX_SEL", ":3115", None),
    (0xB8000044, "PIN_MUX_SEL2", ":3116", "PIN_MUX_SEL_2"),
])


def _offset_names():
    """offset -> (label, B line) for the 32 per-port offsets."""
    out = {}
    for name, (off, line) in MIB_NAME.items():
        out[off] = (name, line)
        if name in OCTETS:
            out[off + 4] = (name + "+4 (high)", line)
    return out


OFF_NAME = _offset_names()


def _word_names():
    """KSEG1 address -> printed name, for every word 1.0 admits."""
    out = {}
    for a, n, lines, d in REG_NAMES:
        out[a] = "%s  B %s%s" % (n, lines, "  (D: %s)" % d if d else "")
    for p in range(MIB_PORTS):
        for off in MIB_OFFS:
            n, line = OFF_NAME[off]
            out[MIB_BASE + off + MIB_STRIDE * p] = \
                "%s, port %d  B :%d" % (n, p, line)
    out[MIB_BASE + CPUEVENT_OFF] = "%s  B :%d" % (CPUEVENT, CPUEVENT_LINE)
    return out


WORD_NAME = _word_names()

# ------------------------------------------------------------------------
# The vendor's asicCounter text: rtl865xC_dumpAsicDiagCounter,
# rtl865x_asicCom.c:1776-1838 (讀 x1), C text and B's name of each argument.
# RTL8651_PORT_NUMBER is 6 (rtl865x_asicCom.h:24-25), so ports 0-5 and then
# the CPU port.
# ------------------------------------------------------------------------
ASIC_PORT_HEAD = r"<Port: %d>\n"                                  # :1787
ASIC_CPU_HEAD = r"<CPU port (extension port included)>\n"          # :1785
ASIC_PORT = [
    (r"Rx counters\n", []),                                         # :1789
    (r"   Rcv %llu bytes, Drop %u pkts,etherStatsDropEvents %u\n",  # :1790
     ["OFFSET_IFINOCTETS_P0", "OFFSET_DOT1DTPPORTINDISCARDS_P0",
      "OFFSET_ETHERSTATSDROPEVENTS_P0"]),
    (r"   CRCAlignErr %u, SymbolErr %u, FragErr %u, JabberErr %u\n",  # :1794
     ["OFFSET_DOT3STATSFCSERRORS_P0", "OFFSET_DOT3STATSSYMBOLERRORS_P0",
      "OFFSET_ETHERSTATSFRAGMEMTS_P0", "OFFSET_ETHERSTATSJABBERS_P0"]),
    (r"   Unicast %u pkts, Multicast %u pkts, Broadcast %u pkts\n",  # :1799
     ["OFFSET_IFINUCASTPKTS_P0", "OFFSET_ETHERSTATSMULTICASTPKTS_P0",
      "OFFSET_ETHERSTATSBROADCASTPKTS_P0"]),
    (r"   < 64: %u pkts, 64: %u pkts, 65 -127: %u pkts, 128 -255: %u pkts\n",
     ["OFFSET_ETHERSTATSUNDERSIZEPKTS_P0",                          # :1803
      "OFFSET_ETHERSTATSPKTS64OCTETS_P0",
      "OFFSET_ETHERSTATSPKTS65TO127OCTETS_P0",
      "OFFSET_ETHERSTATSPKTS128TO255OCTETS_P0"]),
    (r"   256 - 511: %u pkts, 512 - 1023: %u pkts, 1024 - 1518: %u pkts\n",
     ["OFFSET_ETHERSTATSPKTS256TO511OCTETS_P0",                     # :1808
      "OFFSET_ETHERSTATSPKTS512TO1023OCTETS_P0",
      "OFFSET_ETHERSTATSPKTS1024TO1518OCTETS_P0"]),
    (r"   oversize: %u pkts, Control unknown %u pkts, Pause %u pkts\n",  # :1812
     ["OFFSET_ETHERSTATSOVERSIZEPKTS_P0",
      "OFFSET_DOT3CONTROLINUNKNOWNOPCODES_P0",
      "OFFSET_DOT3INPAUSEFRAMES_P0"]),
    (r"Output counters\n", []),                                     # :1817
    (r"   Snd %llu bytes, Unicast %u pkts, Multicast %u pkts\n",    # :1818
     ["OFFSET_IFOUTOCTETS_P0", "OFFSET_IFOUTUCASTPKTS_P0",
      "OFFSET_IFOUTMULTICASTPKTS_P0"]),
    (r"   Broadcast %u pkts, Late collision %u, Deferred transmission %u \n",
     ["OFFSET_IFOUTBROADCASTPKTS_P0",                               # :1822
      "OFFSET_DOT3STATSLATECOLLISIONS_P0",
      "OFFSET_DOT3STATSDEFERREDTRANSMISSIONS_P0"]),
    (r"   Collisions %u Single collision %u Multiple collision %u pause %u\n",
     ["OFFSET_ETHERSTATSCOLLISIONS_P0",                             # :1826
      "OFFSET_DOT3STATSSINGLECOLLISIONFRAMES_P0",
      "OFFSET_DOT3STATSMULTIPLECOLLISIONFRAMES_P0",
      "OFFSET_DOT3OUTPAUSEFRAMES_P0"]),
]
ASIC_TAIL = [
    (r"<Whole system counters>\n", []),                             # :1834
    (r"   CpuEvent %u pkts\n", [CPUEVENT]),                         # :1835
]
ASIC_LINES = MIB_PORTS * (1 + len(ASIC_PORT)) + len(ASIC_TAIL)     # 86
# The counters the dump prints, in its order: 7 x 30 + CpuEvent = 211.
COUNTER_KEYS = ([(p, n) for p in range(MIB_PORTS)
                 for _, names in ASIC_PORT for n in names] + [(SYS, CPUEVENT)])


def octets(lo, hi):
    """The vendor's 64-bit byte count, rtl865x_asicCom.c:1506 (讀 x1): the
    8196E arm adds the high word shifted by 22, not 32."""
    return lo + (hi << 22)


class Refused(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, "[%s] %s" % (code, msg))
        self.code = code


def strip_cr(text):
    return text.replace("\r", "")


# ------------------------------------------------------------------------
# /proc/rtl819x-view pages
# ------------------------------------------------------------------------
NUM = r"([0-9]+)"
HEX8 = r"([0-9A-F]{8})"
HEADER_RES = [
    ("admit", re.compile(r"admit " + NUM)),
    ("last", re.compile(r"last (none|mib|vlan|netif|peek) j " + NUM +
                        r" rc (-?[0-9]+)")),
    ("n_mib", re.compile(r"n_mib %s n_tbl %s n_peek %s refused %s busy %s "
                         r"ld %s" % ((NUM,) * 6))),
    ("ref", re.compile(r"ref " + HEX8 + r" (none|out|psrp)")),
]
JIFFIES_RE = re.compile(r"jiffies " + NUM)
MIB_RE = re.compile(r"mib base " + HEX8 + r" stride ([0-9A-F]{3,}) ports " +
                    NUM + r" words " + NUM)
MO_RE = re.compile(r"mo((?: [0-9A-F]{3,})+)")
PORT_RE = re.compile(r"m([0-9]+)((?: [0-9A-F]{8})*)")
MC_RE = re.compile(r"mc ([0-9A-F]{3,}) " + HEX8)
TBL_RE = re.compile(r"tbl (vlan|netif) base " + HEX8 + r" slots " + NUM +
                    r" words " + NUM + r" polls " + NUM)
SLOT_RE = re.compile(r"s([0-9]{2}) t([0-9]+) (eq|mis)((?: [0-9A-F]{8})*)")
BUSY_RE = re.compile(r"busy s([0-9]{2})")
PEEK_RE = re.compile(r"peek " + HEX8 + r" n " + NUM)
A_RE = re.compile(r"a " + HEX8 + " " + HEX8)
COUNTS = ("n_mib", "n_tbl", "n_peek", "refused", "busy", "ld")


def u32(s, what, where):
    v = int(s)
    if v > U32:
        raise Refused("range", "%s: %s %s is wider than a 32-bit unsigned "
                      "long" % (where, what, s))
    return v


def render_page(pg):
    """The page 1.0 prints for these values, through the driver's literals."""
    s = F_VERSION % VERSION
    s += F_ADMIT % pg["admit"]
    s += F_LAST % (pg["last"], pg["j"], pg["rc"])
    s += F_COUNTS % tuple(pg[k] for k in COUNTS)
    s += F_REF % (pg["ref_a"], pg["ref_why"])
    if pg["last"] == "mib":
        r = pg["mib"]
        s += F_MIB % (r["base"], r["stride"], r["ports"], r["words"])
        s += F_MO + "".join(F_MO_OFF % o for o in r["mo"]) + F_MO_END
        for p, row in enumerate(r["rows"]):
            s += F_PORT % p + "".join(F_PORT_W % w for w in row) + F_PORT_END
        for off, w in r["mc"]:
            s += F_MC % (off, w)
    elif pg["last"] in TABLES:
        r = pg["tbl"]
        s += F_TBL % (r["name"], r["base"], r["slots"], r["words"], r["polls"])
        for sl in r["slot_lines"]:
            s += F_SLOT % (sl["s"], sl["t"], EQ_MIS[0] if sl["eq"] else
                           EQ_MIS[1])
            s += "".join(F_SLOT_W % w for w in sl["w"]) + F_SLOT_END
        if r["busy"] is not None:
            s += F_BUSY % r["busy"]
    elif pg["last"] == "peek":
        r = pg["peek"]
        s += F_PEEK % (r["a"], r["n"])
        for i, w in enumerate(r["w"]):
            s += F_A % ((r["a"] + 4 * i) & U32, w)
    s += F_JIFFIES % pg["jiffies"]
    return s


def _refuse_line(code, where, ln, want):
    raise Refused(code, "%s: %r is not %s" % (where, ln, want))


def parse_mib(R, pg, at):
    if pg["rc"] != 0:
        raise Refused("mib", "%s: `last mib` with rc %d; mib returns 0 or "
                      "caches nothing" % (at(2), pg["rc"]))
    if len(R) < 2:
        raise Refused("cut", "%s: `last mib` with %d result line(s); it prints "
                      "a mib line and a mo line first" % (at(5), len(R)))
    m = MIB_RE.fullmatch(R[0]) or _refuse_line(
        "line", at(5), R[0], "the `mib base ...` line")
    base, stride = int(m.group(1), 16), int(m.group(2), 16)
    ports, words = u32(m.group(3), "ports", at(5)), u32(m.group(4), "words",
                                                       at(5))
    m = MO_RE.fullmatch(R[1]) or _refuse_line("line", at(6), R[1],
                                              "the `mo` line")
    mo = [int(x, 16) for x in m.group(1).split()]
    if ports != MIB_PORTS:
        raise Refused("mib", "%s: ports %d, not 7" % (at(5), ports))
    rows = []
    for p in range(MIB_PORTS):
        k = 2 + p
        if k >= len(R):
            raise Refused("cut", "%s: the page ends after m%d; ports 7 needs "
                          "m0 to m6" % (at(5 + k), p - 1))
        m = PORT_RE.fullmatch(R[k]) or _refuse_line(
            "line", at(5 + k), R[k], "the m%d port line" % p)
        if int(m.group(1)) != p:
            raise Refused("mib", "%s: m%s where m%d belongs; the port lines "
                          "run m0 to m6 in order" % (at(5 + k), m.group(1), p))
        ws = [int(x, 16) for x in m.group(2).split()]
        if len(ws) != len(mo):
            raise Refused("mib", "%s: m%d holds %d words for %d mo offsets"
                          % (at(5 + k), p, len(ws), len(mo)))
        rows.append(ws)
    mc = []
    for k in range(2 + MIB_PORTS, len(R)):
        m = MC_RE.fullmatch(R[k]) or _refuse_line("line", at(5 + k), R[k],
                                                  "an `mc` line")
        mc.append((int(m.group(1), 16), int(m.group(2), 16)))
    if not mc:
        raise Refused("cut", "%s: no mc line after m6" % at(5 + len(R) - 1))
    if len(mc) != 1:
        raise Refused("mib", "%s: %d mc lines; 1.0 prints one (CpuEvent)"
                      % (at(5 + 2 + MIB_PORTS), len(mc)))
    if words != MIB_PORTS * len(mo) + len(mc):
        raise Refused("mib", "%s: words %d, but 7 x %d mo offsets + %d mc = %d"
                      % (at(5), words, len(mo), len(mc),
                         MIB_PORTS * len(mo) + len(mc)))
    if (base, stride, mo, [o for o, _ in mc]) != \
            (MIB_BASE, MIB_STRIDE, MIB_OFFS, [CPUEVENT_OFF]):
        raise Refused("name", "%s: a MIB layout other than 1.0's (base %08X "
                      "stride %03X, %d mo offsets, mc %s); this decoder names "
                      "words by 1.0's offsets and would misname these"
                      % (at(5), base, stride, len(mo),
                         ",".join("%03X" % o for o, _ in mc)))
    pg["mib"] = {"base": base, "stride": stride, "ports": ports,
                 "words": words, "mo": mo, "rows": rows, "mc": mc}


def parse_tbl(R, pg, at):
    rc = pg["rc"]
    if rc not in (0, -EBUSY):
        raise Refused("tbl", "%s: `last %s` with rc %d; a tbl verb caches "
                      "only with 0 or -16" % (at(2), pg["last"], rc))
    if not R:
        raise Refused("cut", "%s: `last %s` with no result line"
                      % (at(5), pg["last"]))
    m = TBL_RE.fullmatch(R[0]) or _refuse_line("line", at(5), R[0],
                                               "the `tbl ...` line")
    name, base = m.group(1), int(m.group(2), 16)
    slots = u32(m.group(3), "slots", at(5))
    words = u32(m.group(4), "words", at(5))
    polls = u32(m.group(5), "polls", at(5))
    if name != pg["last"]:
        raise Refused("tbl", "%s: `tbl %s` under `last %s`"
                      % (at(5), name, pg["last"]))
    if (base, slots) != TABLES[name]:
        raise Refused("tbl", "%s: %s base %08X slots %d; 1.0's is base %08X "
                      "slots %d" % ((at(5), name, base, slots) + TABLES[name]))
    if words != 8:
        raise Refused("tbl", "%s: words %d, not 8" % (at(5), words))
    lines, busy = [], None
    for k in range(1, len(R)):
        mb = BUSY_RE.fullmatch(R[k])
        if mb:
            if k != len(R) - 1:
                raise Refused("extra", "%s: %r follows the busy line"
                              % (at(5 + k + 1), R[k + 1]))
            busy = int(mb.group(1))
            continue
        ms = SLOT_RE.fullmatch(R[k]) or _refuse_line(
            "line", at(5 + k), R[k], "a slot line or the busy line")
        s, t, eq = int(ms.group(1)), int(ms.group(2)), ms.group(3) == "eq"
        ws = [int(x, 16) for x in ms.group(4).split()]
        if s != len(lines):
            raise Refused("tbl", "%s: s%02d where s%02d belongs; slot lines "
                          "run from s00, consecutive" % (at(5 + k), s,
                                                         len(lines)))
        if len(lines) >= slots:
            raise Refused("tbl", "%s: slot line %d of a %d-slot table"
                          % (at(5 + k), len(lines) + 1, slots))
        if not 1 <= t <= TRIES:
            raise Refused("tbl", "%s: t%d outside 1 to 10" % (at(5 + k), t))
        if not eq and t != TRIES:
            raise Refused("tbl", "%s: mis with t%d; mis means ten passes "
                          "disagreed" % (at(5 + k), t))
        if len(ws) != 8:
            raise Refused("tbl", "%s: s%02d holds %d words, not eight"
                          % (at(5 + k), s, len(ws)))
        lines.append({"s": s, "t": t, "eq": eq, "w": ws})
    n = len(lines)
    if busy is not None and rc == 0:
        raise Refused("tbl", "%s: a busy line with rc 0" % at(5 + len(R) - 1))
    if rc == -EBUSY and busy is None:
        raise Refused("tbl", "%s: rc -16 without a busy line" % at(2))
    if busy is not None and busy != n:
        raise Refused("tbl", "%s: busy s%02d after %d slot line(s); the busy "
                      "slot is the one after the last completed"
                      % (at(5 + len(R) - 1), busy, n))
    if rc == 0 and n < slots:
        raise Refused("cut", "%s: rc 0 with %d of %d slot lines"
                      % (at(5), n, slots))
    if polls < n:
        raise Refused("tbl", "%s: polls %d for %d slot lines; each slot "
                      "polls SWTACR at least once" % (at(5), polls, n))
    if busy is not None and polls < n + BOUND + 1:
        raise Refused("tbl", "%s: polls %d with busy after %d slots; the busy "
                      "slot alone polls %d" % (at(5), polls, n, BOUND + 1))
    pg["tbl"] = {"name": name, "base": base, "slots": slots, "words": words,
                 "polls": polls, "slot_lines": lines, "busy": busy}


def parse_peek(R, pg, at):
    if pg["rc"] != 0:
        raise Refused("peek", "%s: `last peek` with rc %d; peek caches only "
                      "on success" % (at(2), pg["rc"]))
    if not R:
        raise Refused("cut", "%s: `last peek` with no result line" % at(5))
    m = PEEK_RE.fullmatch(R[0]) or _refuse_line("line", at(5), R[0],
                                                "the `peek A n N` line")
    a, n = int(m.group(1), 16), u32(m.group(2), "n", at(5))
    if a & 3:
        raise Refused("peek", "%s: %08X is not a multiple of 4" % (at(5), a))
    if not 1 <= n <= PEEK_MAX:
        raise Refused("peek", "%s: n %d outside 1 to 16" % (at(5), n))
    ws = []
    for k in range(1, len(R)):
        ma = A_RE.fullmatch(R[k]) or _refuse_line("line", at(5 + k), R[k],
                                                  "an `a` line")
        i = k - 1
        if i >= n:
            raise Refused("extra", "%s: `a` line %d under n %d"
                          % (at(5 + k), k, n))
        want = (a + 4 * i) & U32
        if int(ma.group(1), 16) != want:
            raise Refused("peek", "%s: a %s where a %08X belongs"
                          % (at(5 + k), ma.group(1), want))
        ws.append(int(ma.group(2), 16))
    if len(ws) < n:
        raise Refused("cut", "%s: %d `a` line(s) under n %d"
                      % (at(5), len(ws), n))
    for i in range(n):
        if (a + 4 * i) & U32 not in WORD_NAME:
            raise Refused("name", "%s: %08X is not a word 1.0 admits, so 1.0 "
                          "never loaded it" % (at(6 + i), (a + 4 * i) & U32))
    pg["peek"] = {"a": a, "n": n, "w": ws}


def parse_page(L, where, first):
    """One page: L runs from the version line to the jiffies line."""
    def at(k):
        return "%s line %d" % (where, first + k)
    if L[0] != "version " + VERSION:
        raise Refused("version", "%s: %r; this decoder was written for "
                      "`version %s` and a changed literal is a changed "
                      "version" % (at(0), L[0], VERSION))
    if len(L) < 6:
        raise Refused("header", "%s: a page of %d lines; the five header "
                      "lines and the terminator are six" % (at(0), len(L)))
    pg = {"where": where, "first": first, "end": first + len(L) - 1}
    ms = {}
    for k, (key, rx) in enumerate(HEADER_RES, 1):
        m = rx.fullmatch(L[k])
        if not m:
            raise Refused("header", "%s: %r is not the `%s` line, which is "
                          "header line %d" % (at(k), L[k], key, k + 1))
        ms[key] = m
    pg["admit"] = u32(ms["admit"].group(1), "admit", at(1))
    pg["last"] = ms["last"].group(1)
    pg["j"] = u32(ms["last"].group(2), "j", at(2))
    rc = int(ms["last"].group(3))
    if not -(1 << 31) <= rc < (1 << 31):
        raise Refused("range", "%s: rc %d is wider than an int" % (at(2), rc))
    pg["rc"] = rc
    for i, key in enumerate(COUNTS):
        pg[key] = u32(ms["n_mib"].group(i + 1), key, at(3))
    pg["ref_a"] = int(ms["ref"].group(1), 16)
    pg["ref_why"] = ms["ref"].group(2)
    pg["jiffies"] = u32(JIFFIES_RE.fullmatch(L[-1]).group(1), "jiffies",
                        at(len(L) - 1))
    if pg["admit"] != ADMIT:
        raise Refused("admit", "%s: admit %d; 1.0's table admits 298, and "
                      "this decoder was written for no other" %
                      (at(1), pg["admit"]))
    why, ra = pg["ref_why"], pg["ref_a"]
    if why == "none" and ra != 0:
        raise Refused("ref", "%s: `ref none` with address %08X" % (at(4), ra))
    if why == "none" and pg["refused"] > 0:
        raise Refused("ref", "%s: `ref none` with refused %d"
                      % (at(4), pg["refused"]))
    if why != "none" and pg["refused"] == 0:
        raise Refused("ref", "%s: refused 0 with reason %s" % (at(4), why))
    if why == "psrp" and not PSRP0 <= ra <= PSRP8:
        raise Refused("ref", "%s: psrp at %08X, outside BB804128-BB804148"
                      % (at(4), ra))
    if why == "out" and PSRP0 <= ra <= PSRP8:
        raise Refused("ref", "%s: out at %08X, inside the PSRP range"
                      % (at(4), ra))
    if why != "none" and ra in WORD_NAME:
        raise Refused("ref", "%s: a refusal of %08X, a word 1.0 admits"
                      % (at(4), ra))
    R = L[5:-1]
    if pg["last"] == "none":
        if R:
            raise Refused("result-none", "%s: %r under `last none`"
                          % (at(5), R[0]))
    elif pg["last"] == "mib":
        parse_mib(R, pg, at)
    elif pg["last"] == "peek":
        parse_peek(R, pg, at)
    else:
        parse_tbl(R, pg, at)
    text = "\n".join(L) + "\n"
    again = render_page(pg)
    if again != text:
        a, b = text.split("\n"), again.split("\n")
        k = next(i for i in range(max(len(a), len(b)))
                 if i >= len(a) or i >= len(b) or a[i] != b[i])
        raise Refused("render", "%s: %r, where 1.0's literals print %r for "
                      "the same values" % (at(k), a[k] if k < len(a) else "",
                                           b[k] if k < len(b) else ""))
    return pg


def find_pages(text, where):
    """Every page in a CR-stripped text, parsed; refuses rather than skips."""
    lines = text.split("\n")
    pages = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith(VERSION_PREFIX):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not JIFFIES_RE.fullmatch(lines[j]) and \
                not lines[j].startswith(VERSION_PREFIX):
            j += 1
        if j == len(lines) or lines[j].startswith(VERSION_PREFIX):
            raise Refused(
                "terminator", "%s line %d: the page has no `jiffies N` line "
                "before %s; a cut page is never decoded" % (
                    where, i + 1, "the input ends" if j == len(lines) else
                    "the next page begins (line %d)" % (j + 1)))
        if j == len(lines) - 1:
            raise Refused("terminator", "%s line %d: %r ends the input with "
                          "no line end, so its number may be cut"
                          % (where, j + 1, lines[j]))
        pages.append(parse_page(lines[i:j + 1], where, i + 1))
        i = j + 1
    return pages


def one_boot(pages):
    """Cross-page checks for pages of one boot, in order: notes, or refuse."""
    notes = []
    for k in range(1, len(pages)):
        a, b = pages[k - 1], pages[k]
        if b["jiffies"] < a["jiffies"]:
            notes.append("pages %d and %d: jiffies %d -> %d, a 32-bit wrap or "
                         "a reboot; the cross-page checks are void for this "
                         "pair" % (k, k + 1, a["jiffies"], b["jiffies"]))
            continue
        for key in COUNTS:
            if b[key] < a[key]:
                raise Refused("one-boot", "pages %d and %d (%s line %d): %s "
                              "%d -> %d while jiffies %d -> %d"
                              % (k, k + 1, b["where"], b["first"], key,
                                 a[key], b[key], a["jiffies"], b["jiffies"]))
    return notes


# ------------------------------------------------------------------------
# The vendor's asicCounter dump
#
# The dump is printk'd (rtlglue_printf), not a /proc page: it reaches the
# console line by line and synchronously.  Two consequences, both 量 in the
# committed captures:
#   * a loud image (CONFIG_PRINTK_TIME=y, config/rlxfw-kernel.delta) puts
#     printk's "[%5lu.%06lu] " in front of every line.  It is accepted on
#     all 86 lines or on none, carried verbatim and put back on render --
#     never interpreted;
#   * other console output can land BETWEEN the printk'd lines, so a dump
#     line carries foreign characters in front of it.  量 in
#     bench/2026-09-25c/A1-00-R.log: `cat /proc/rtl819x-nic ...
#     /proc/rtl865x/asicCounter` -- the nic page `cat` had already written
#     to the tty drains one character per printk'd line ("version rtl819"
#     before <Port: 0>, then x, -, n, i, c ...).  231 committed captures
#     have foreign characters in front of their dump lines; that one was
#     traced.  Such a dump is REFUSED: this parser never takes a dump apart.
# ------------------------------------------------------------------------
PRINTK_TIME = r"(\[ *[0-9]+\.[0-9]{6}\] )?"


def _c2re(c):
    """(body regex text, conversions) for one vendor line, no newline."""
    parts = re.split(r"(%(?:ll|l)?[ud])", c_unescape(c).rstrip("\n"))
    rx, conv = "", []
    for part in parts:
        if part.startswith("%"):
            rx += "(0|[1-9][0-9]*)"
            conv.append(part)
        else:
            rx += re.escape(part)
    return rx, conv


ASIC_TEMPLATES = []      # (C text, regex, body, conversions, names, port)
for _p in range(MIB_PORTS):
    _h = ASIC_CPU_HEAD if _p == MIB_PORTS - 1 else ASIC_PORT_HEAD
    _b, _v = _c2re(_h)
    ASIC_TEMPLATES.append((_h, re.compile(PRINTK_TIME + _b), _b, _v, [], _p))
    for _c, _n in ASIC_PORT:
        _b, _v = _c2re(_c)
        ASIC_TEMPLATES.append((_c, re.compile(PRINTK_TIME + _b), _b, _v, _n,
                               _p))
for _c, _n in ASIC_TAIL:
    _b, _v = _c2re(_c)
    ASIC_TEMPLATES.append((_c, re.compile(PRINTK_TIME + _b), _b, _v, _n, SYS))
# A line that ENDS in any line of the dump, whatever is in front of it.
ASIC_ANY = re.compile("(?:%s)$" % "|".join(
    sorted({b for _, _, b, _, _, _ in ASIC_TEMPLATES})))


def render_asic(vals, stamps=None):
    """The dump's text for `vals`; `stamps`, if given, are the 86 printk
    time prefixes to put back in front of the lines."""
    out = []
    for i, (c, _, _, _, names, p) in enumerate(ASIC_TEMPLATES):
        if c == ASIC_PORT_HEAD:
            ln = pyfmt(c) % p
        else:
            ln = pyfmt(c) % tuple(vals[(p, n)] for n in names)
        out.append((stamps[i] if stamps else "") + ln)
    return "".join(out)


def asic_blocks(text, where):
    """Every complete asicCounter dump in a CR-stripped text, as values.

    A dump's last line may end the input without its line end (a capture
    stopped on `CpuEvent`): its literal " pkts" follows the number, so the
    number cannot have been cut."""
    lines = text.split("\n")
    marks = {k for k, ln in enumerate(lines) if ASIC_ANY.search(ln)}
    used, blocks = set(), []
    head = ASIC_TEMPLATES[0][1]
    k = 0
    while k < len(lines):
        m0 = head.fullmatch(lines[k])
        if not m0 or m0.group(2) != "0":
            k += 1
            continue
        vals, stamps = {}, []
        for i, (c, rx, _, conv, names, p) in enumerate(ASIC_TEMPLATES):
            ln = lines[k + i] if k + i < len(lines) else None
            m = rx.fullmatch(ln) if ln is not None else None
            if not m:
                raise Refused("asic", "%s line %d: %r where the dump prints "
                              "%r (a cut or interleaved dump)"
                              % (where, k + i + 1, ln, c_unescape(c)))
            stamps.append(m.group(1) or "")
            if bool(m.group(1)) != bool(stamps[0]):
                raise Refused("asic", "%s line %d: a printk time on some "
                              "lines of the dump and not on others"
                              % (where, k + i + 1))
            got = [int(g) for g in m.groups()[1:]]
            for g, cv in zip(got, conv):
                if g > (U64 if cv == "%llu" else U32):
                    raise Refused("asic", "%s line %d: %d is wider than %s"
                                  % (where, k + i + 1, g, cv))
            if c == ASIC_PORT_HEAD:
                if got != [p]:
                    raise Refused("asic", "%s line %d: <Port: %d> where "
                                  "<Port: %d> belongs"
                                  % (where, k + i + 1, got[0], p))
            else:
                for n, g in zip(names, got):
                    vals[(p, n)] = g
        used.update(range(k, k + ASIC_LINES))
        blocks.append({"vals": vals, "first": k + 1,
                       "stamps": stamps if stamps[0] else None,
                       "at_eof": k + ASIC_LINES == len(lines),
                       "text": "\n".join(lines[k:k + ASIC_LINES]) + "\n"})
        k += ASIC_LINES
    stray = sorted(marks - used)
    if stray:
        raise Refused("asic", "%s line %d: %r holds a line of an asicCounter "
                      "dump but belongs to no complete one (a cut dump, or "
                      "one interleaved with other console output)"
                      % (where, stray[0] + 1, lines[stray[0]]))
    return blocks


def view_counters(pg):
    """The 211 counters the vendor prints, from a `last mib` page's words."""
    r = pg["mib"]
    at = {o: k for k, o in enumerate(r["mo"])}
    vals = {}
    for p, row in enumerate(r["rows"]):
        for name, (off, _) in MIB_NAME.items():
            if name in OCTETS:
                vals[(p, name)] = octets(row[at[off]], row[at[off + 4]])
            else:
                vals[(p, name)] = row[at[off]]
    vals[(SYS, CPUEVENT)] = r["mc"][0][1]
    return vals


def key_label(key):
    p, n = key
    if p == SYS:
        return "system %s" % n
    who = "CPU port (6)" if p == MIB_PORTS - 1 else "port %d" % p
    return "%s %s%s" % (who, n, " (lo + (hi << 22))" if n in OCTETS else "")


# ------------------------------------------------------------------------
# decode's text
# ------------------------------------------------------------------------
def vlan_fields(w):
    """rtl865xc_tblAsic_vlanTable_t word 0, B rtl865x_asicCom.h:230-242, the
    big-endian arm (推: no definition of _LITTLE_ENDIAN in the staged tree,
    讀 grep; gcc packs a big-endian target's bit-fields from bit 31 down)."""
    return ("vid %d fid %d extEgressUntag %d egressUntag %02X "
            "extMemberPort %d memberPort %02X"
            % (w >> 20, (w >> 18) & 3, (w >> 15) & 7, (w >> 9) & 0x3F,
               (w >> 6) & 7, w & 0x3F))


def netif_fields(ws):
    """rtl865xc_tblAsic_netifTable_t words 0-3, B rtl865x_asicCom.h:171-191,
    the big-endian arm; MAC, MTU and inACLStart assembled as
    rtl8651_getAsicNetInterface does (rtl865x_asicCom.c:604-636)."""
    w0, w1, w2, w3 = ws[:4]
    mac = ((w1 & 0x1FFFFFFF) << 19) | (w0 >> 13)
    return ("valid %d vid %d mac %s macMask %d mtu %d inACL %d-%d "
            "outACL %d-%d enHWRoute %d"
            % (w0 & 1, (w0 >> 1) & 0xFFF,
               ":".join("%02x" % ((mac >> s) & 0xFF)
                        for s in range(40, -8, -8)),
               (w2 >> 26) & 7, ((w3 & 0xFFF) << 3) | (w2 >> 29),
               ((w2 & 0x1F) << 2) | (w1 >> 30), (w2 >> 5) & 0x7F,
               (w2 >> 12) & 0x7F, (w2 >> 19) & 0x7F, (w1 >> 29) & 1))


def describe(pg, index):
    out = ["page %d: %s lines %d-%d" % (index, pg["where"], pg["first"],
                                        pg["end"]),
           "  last %s  j %d  rc %d  jiffies %d" % (pg["last"], pg["j"],
                                                   pg["rc"], pg["jiffies"]),
           "  " + "  ".join("%s %d" % (k, pg[k]) for k in COUNTS) +
           "  ref %08X %s" % (pg["ref_a"], pg["ref_why"])]
    if pg["last"] != "none" and pg["j"] > pg["jiffies"]:
        out.append("  note: last j %d > jiffies %d -- a 32-bit jiffies wrap "
                   "between the verb and the render, or a corrupt page; not "
                   "refused" % (pg["j"], pg["jiffies"]))
    if pg["last"] == "mib":
        r = pg["mib"]
        out.append("  mib base %08X stride %03X: ports 0-5 and 6 (the CPU "
                   "port), %d words, loaded m0 to m6 left to right, then mc"
                   % (r["base"], r["stride"], r["words"]))
        vals = view_counters(pg)
        for p, row in enumerate(r["rows"]):
            out.append("  %s (m%d)" % ("CPU port 6" if p == 6 else
                                       "port %d" % p, p))
            for off, w in zip(r["mo"], row):
                n, line = OFF_NAME[off]
                out.append("    +%03X %08X  %08X %10d  %s  B :%d"
                           % (off, r["base"] + off + r["stride"] * p, w, w,
                              n, line))
            for n in OCTETS:
                out.append("    %s = lo + (hi << 22) = %d  (B's formula, "
                           "rtl865x_asicCom.c:1506, one source)"
                           % (n, vals[(p, n)]))
        for off, w in r["mc"]:
            out.append("  system (mc)")
            out.append("    +%03X %08X  %08X %10d  %s  B :%d"
                       % (off, r["base"] + off, w, w, CPUEVENT,
                          CPUEVENT_LINE))
    elif pg["last"] in TABLES:
        r = pg["tbl"]
        out.append("  tbl %s base %08X: %d slots of 8 words; %d slot line(s); "
                   "polls %d; a slot number is not a VID"
                   % (r["name"], r["base"], r["slots"],
                      len(r["slot_lines"]), r["polls"]))
        for sl in r["slot_lines"]:
            out.append("    s%02d t%d %-3s %s" % (
                sl["s"], sl["t"], "eq" if sl["eq"] else "mis",
                " ".join("%08X" % w for w in sl["w"])))
            out.append("        B, big-endian arm: " +
                       (vlan_fields(sl["w"][0]) if r["name"] == "vlan"
                        else netif_fields(sl["w"])))
        if r["busy"] is not None:
            out.append("    busy at s%02d: SWTACR stayed busy past 10,000 "
                       "polls; no table word was loaded after it" % r["busy"])
    elif pg["last"] == "peek":
        r = pg["peek"]
        out.append("  peek %08X n %d" % (r["a"], r["n"]))
        for i, w in enumerate(r["w"]):
            a = (r["a"] + 4 * i) & U32
            out.append("    %08X  %08X  %s" % (a, w, WORD_NAME[a]))
    return out


# ------------------------------------------------------------------------
# The verbs
# ------------------------------------------------------------------------
def read_input(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        raise Refused("input", "cannot read %s: %s" % (path, e.strerror or e))
    return raw, strip_cr(raw.decode("utf-8", "replace"))


def has_page(text):
    return any(ln.startswith(VERSION_PREFIX) for ln in text.split("\n"))


def has_asic(text):
    return any(ASIC_ANY.search(ln) for ln in text.split("\n"))


def one_mib_page(path, text):
    pages = find_pages(text, path)
    if len(pages) != 1:
        raise Refused("count", "%s holds %d pages; this verb takes a file "
                      "with one" % (path, len(pages)))
    if pages[0]["last"] != "mib":
        raise Refused("input", "%s: its page is `last %s`, not `last mib`"
                      % (path, pages[0]["last"]))
    return pages[0]


def counter_source(path, role):
    _, text = read_input(path)
    page, asic = has_page(text), has_asic(text)
    if page and asic:
        raise Refused("input", "%s (%s) holds a view page and an asicCounter "
                      "dump; give each its own file" % (path, role))
    if page:
        pg = one_mib_page(path, text)
        return view_counters(pg), "view page, last mib j %d, jiffies %d" % (
            pg["j"], pg["jiffies"])
    if role == "view":
        raise Refused("input", "%s (view) holds no /proc/rtl819x-view page"
                      % path)
    if not asic:
        raise Refused("input", "%s (%s) is neither a view page nor an "
                      "asicCounter dump" % (path, role))
    blocks = asic_blocks(text, path)
    if len(blocks) != 1:
        raise Refused("count", "%s (%s) holds %d asicCounter dumps; give it "
                      "one" % (path, role, len(blocks)))
    return blocks[0]["vals"], "asicCounter dump at line %d" % \
        blocks[0]["first"]


def cmd_decode(files, check_boot):
    pages = []
    for path in files:
        _, text = read_input(path)
        got = find_pages(text, path)
        if not got:
            raise Refused("no-page", "%s holds no line starting `%s`"
                          % (path, VERSION_PREFIX))
        pages += got
    print("viewdecode %s decode: %d page(s); names from B "
          "(rtl865xc_asicregs.h), one source each" % (TOOL_VERSION,
                                                      len(pages)))
    for i, pg in enumerate(pages, 1):
        for ln in describe(pg, i):
            print(ln)
    if check_boot:
        notes = one_boot(pages)
        print("one boot: counters never decrease across %d page(s)%s"
              % (len(pages), "" if not notes else "; " + "; ".join(notes)))
    return 0


def cmd_asic(path):
    _, text = read_input(path)
    if not has_page(text):
        raise Refused("no-page", "%s holds no line starting `%s`"
                      % (path, VERSION_PREFIX))
    sys.stdout.write(render_asic(view_counters(one_mib_page(path, text))))
    return 0


def bracket(before, view, after):
    """(failures, pinned, moved): failures is [(key, reason)]."""
    fails, pinned, moved = [], 0, 0
    for key in COUNTER_KEYS:
        b, v, a = before[key], view[key], after[key]
        rev = b > a
        below = not (b <= v)
        above = not (v <= a)
        if rev:
            fails.append((key, "ends reversed: before %d > after %d (view %d)"
                          % (b, a, v)))
        elif below:
            fails.append((key, "below: view %d < before %d (after %d)"
                          % (v, b, a)))
        elif above:
            fails.append((key, "above: view %d > after %d (before %d)"
                          % (v, a, b)))
        elif b == a:
            pinned += 1
        else:
            moved += 1
    return fails, pinned, moved


def cmd_bracket(bpath, vpath, apath):
    before, bdesc = counter_source(bpath, "before")
    view, vdesc = counter_source(vpath, "view")
    after, adesc = counter_source(apath, "after")
    fails, pinned, moved = bracket(before, view, after)
    print("viewdecode %s bracket" % TOOL_VERSION)
    print("  before  %s  (%s)" % (bpath, bdesc))
    print("  view    %s  (%s)" % (vpath, vdesc))
    print("  after   %s  (%s)" % (apath, adesc))
    print("  %d counters (7 ports x 30, and CpuEvent): %d pinned (before = "
          "after = view), %d moved and bracketed, %d outside"
          % (len(COUNTER_KEYS), pinned, moved, len(fails)))
    for key, why in fails:
        print("  outside  %s: %s" % (key_label(key), why))
    print("RESULT: %s" % ("the bracket holds" if not fails else
                          "the bracket FAILS on %d counter(s)" % len(fails)))
    return 1 if fails else 0


# ------------------------------------------------------------------------
# Self-test
# ------------------------------------------------------------------------
class NoRun(Exception):
    """The self-test cannot run here (exit 3)."""


def git_bench_logs(root):
    try:
        p = subprocess.run(["git", "-C", root, "ls-files", "-z", "--",
                            "bench"], capture_output=True)
    except OSError as e:
        raise NoRun("git cannot run (%s); A1's population is git ls-files "
                    "bench/" % e)
    if p.returncode != 0:
        raise NoRun("git ls-files failed at %s: %s; A1's population is the "
                    "tracked bench/ files" % (root, p.stderr.decode(
                        "utf-8", "replace").strip()))
    return sorted(f for f in p.stdout.decode("utf-8", "replace").split("\0")
                  if f.endswith(".log"))


def load_viewcheck(root):
    path = os.path.join(root, "tools", "viewcheck.py")
    spec = importlib.util.spec_from_file_location("viewcheck_for_decode",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_page(last, **kw):
    pg = {"admit": ADMIT, "last": last, "j": 4242, "rc": 0, "n_mib": 0,
          "n_tbl": 0, "n_peek": 0, "refused": 0, "busy": 0, "ld": 0,
          "ref_a": 0, "ref_why": "none", "jiffies": 4242}
    pg.update(kw)
    return pg


def mib_result(word, cpu):
    return {"base": MIB_BASE, "stride": MIB_STRIDE, "ports": MIB_PORTS,
            "words": NMIB, "mo": list(MIB_OFFS),
            "rows": [[word(p, o) & U32 for o in MIB_OFFS]
                     for p in range(MIB_PORTS)], "mc": [(CPUEVENT_OFF, cpu)]}


def mix(p, o):
    return ((p * 0x1000 + o) * 0x9E3779B1) & U32


def base_pages():
    """One valid page of every kind, as (name, page dict)."""
    out = [("boot", make_page("none", j=0))]
    out.append(("mib", make_page("mib", n_mib=1, ld=225,
                                 mib=mib_result(mix, 0x75EF951E))))
    vl = [{"s": s, "t": 1, "eq": True,
           "w": [mix(9, 32 * s + 4 * k) for k in range(8)]} for s in range(16)]
    vl[3] = dict(vl[3], t=10, eq=False)
    vl[5] = dict(vl[5], t=4)
    out.append(("vlan", make_page("vlan", n_tbl=1, ld=16 * 17 + 36 * 16,
                                  tbl={"name": "vlan", "base": 0xBB060000,
                                       "slots": 16, "words": 8, "polls": 16,
                                       "slot_lines": vl, "busy": None})))
    busy = [dict(sl) for sl in vl[:3]]
    out.append(("vlan-busy", make_page(
        "vlan", rc=-EBUSY, n_tbl=1, busy=1, ld=3 * 17 + 10001,
        tbl={"name": "vlan", "base": 0xBB060000, "slots": 16, "words": 8,
             "polls": 3 + 10001, "slot_lines": busy, "busy": 3})))
    ni = [{"s": s, "t": 1, "eq": True,
           "w": [mix(10, 32 * s + 4 * k) for k in range(8)]} for s in range(8)]
    out.append(("netif", make_page("netif", n_tbl=1, ld=8 * 17,
                                   tbl={"name": "netif", "base": 0xBB040000,
                                        "slots": 8, "words": 8, "polls": 8,
                                        "slot_lines": ni, "busy": None})))
    out.append(("peek", make_page("peek", n_peek=1, ld=4, peek={
        "a": 0xBB804100, "n": 4, "w": [mix(11, k) for k in range(4)]})))
    out.append(("peek-ref", make_page(
        "peek", n_peek=2, ld=6, refused=2, ref_a=0xBB804128, ref_why="psrp",
        peek={"a": 0xB8000040, "n": 2, "w": [0x00000000, 0x12345678]})))
    out.append(("peek-out", make_page(
        "peek", n_peek=1, ld=16, refused=1, ref_a=0xBD006000, ref_why="out",
        peek={"a": 0xBB801114, "n": 16, "w": [mix(12, k) for k in
                                              range(16)]})))
    return out


def as_capture(page_text, cmd="cat /proc/rtl819x-view"):
    return ("# " + cmd + "\n" + page_text + "# ").replace("\n", "\r\n")


def expect_refusal(text, code, needle=""):
    """'' if decoding `text` refuses with `code` (and `needle` in the
    reason), else what happened instead."""
    try:
        pages = find_pages(strip_cr(text), "t")
        if not pages:
            raise Refused("no-page", "t holds no page")
    except Refused as e:
        if e.code != code or needle not in str(e):
            return "refused %s, not [%s] %r" % (e, code, needle)
        return ""
    return "decoded %d page(s); wanted [%s]" % (len(pages), code)


def edit(text, fn):
    lines = text.split("\n")
    return "\n".join(fn(lines))


def run_main(argv):
    """main(argv) with its output captured; argparse's own exit is a code."""
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        try:
            rc = main(argv)
        except SystemExit as e:
            rc = e.code
    return rc, buf.getvalue() + err.getvalue()


def deinterleave(text):
    """SELF-TEST ONLY, never a decoding path.  For a capture whose dump
    asic_blocks refuses: the dump's 86 lines, in order, each behind zero or
    more foreign characters, with foreign line ends as empty lines between
    them.  (values, the 86 vendor lines, foreign characters) or None."""
    lines = text.split("\n")
    starts = [k for k, ln in enumerate(lines) if ln.endswith("<Port: 0>")]
    if len(starts) != 1:
        return None
    k, vals, got, foreign = starts[0], {}, [], 0
    for c, _, body, _, names, p in ASIC_TEMPLATES:
        while k < len(lines) and lines[k] == "":
            foreign += 1
            k += 1
        m = re.fullmatch("(.*?)(" + body + ")", lines[k]) \
            if k < len(lines) else None
        if not m:
            return None
        foreign += len(m.group(1))
        got.append(m.group(2))
        nums = [int(x) for x in m.groups()[2:]]
        if c == ASIC_PORT_HEAD:
            if nums != [p]:
                return None
        else:
            for n, v in zip(names, nums):
                vals[(p, n)] = v
        k += 1
    return vals, got, foreign


# The shapes of the committed dumps at 8520b6c, 量 by this case's first run:
# floors, because a record is never removed.
A1_FLOORS = (("clean", 23), ("printk-time", 12), ("interleaved", 231))


def case_a1(root):
    logs = git_bench_logs(root)
    cls = dict((c, 0) for c, _ in A1_FLOORS)
    hits, at_eof, foreign, big, bad = 0, 0, 0, 0, []

    def nbig(vals):
        return sum(1 for p in range(MIB_PORTS) for n in OCTETS
                   if vals[(p, n)] >= 1 << 22)
    for rel in logs:
        with open(os.path.join(root, rel), "rb") as fh:
            raw = fh.read()
        text = strip_cr(raw.decode("utf-8", "replace"))
        if not has_asic(text):
            continue
        hits += 1
        try:
            blocks = asic_blocks(text, rel)
        except Refused as e:
            d = deinterleave(text)
            if e.code != "asic" or d is None or d[2] == 0:
                bad.append("%s: refused (%s) and not a whole dump behind "
                           "foreign characters" % (rel, e))
            elif render_asic(d[0]) != "".join(g + "\n" for g in d[1]):
                bad.append("%s: its 86 de-interleaved lines do not re-render"
                           % rel)
            else:
                cls["interleaved"] += 1
                foreign += d[2]
                big += nbig(d[0])
            continue
        if not blocks:
            bad.append("%s: a line of the dump and no dump" % rel)
        for b in blocks:
            again = render_asic(b["vals"], b["stamps"])
            crlf = again.replace("\n", "\r\n").encode("ascii")
            if b["at_eof"]:
                at_eof += 1
                same = raw.endswith(crlf[:-2]) or raw.endswith(crlf[:-1])
            else:
                at = raw.find(crlf)
                same = at == 0 or (at > 0 and raw[at - 1:at] == b"\n")
            if again != b["text"] or not same:
                bad.append("%s line %d: does not re-render to its own bytes"
                           % (rel, b["first"]))
                continue
            cls["printk-time" if b["stamps"] else "clean"] += 1
            big += nbig(b["vals"])
    ok = (not bad and hits >= 266 and big > 0 and
          all(cls[c] >= f for c, f in A1_FLOORS))
    return ok, (
        "%d captures of %d tracked bench .log (floor 266): %d clean and %d "
        "printk-timed, parsed into 7 port sections + CpuEvent and re-rendered "
        "to their own CRLF bytes (%d end the capture inside the last CRLF); "
        "%d interleaved with other console output (%d foreign characters) "
        "REFUSED, each with all 86 lines present behind them and re-rendered; "
        "%d byte "
        "counts >= 2^22; floors %s%s"
        % (hits, len(logs), cls["clean"], cls["printk-time"], at_eof,
           cls["interleaved"], foreign, big,
           " ".join("%s %d" % cf for cf in A1_FLOORS),
           "" if ok else "; " + "; ".join(bad[:3])))


def source_literals(src):
    out = {}
    for fn in FORMATS:
        m = re.search(r"^static int %s\(.*?^\}$" % fn, src, re.M | re.S)
        out[fn] = None if not m else re.findall(
            r'sprintf\(page \+ len,\s*"((?:[^"\\\n]|\\.)*)"', m.group(0))
    return out, len(re.findall(r"\bsprintf\(", src))


def source_defines(src):
    d = {}
    for name, tok in re.findall(r"^#define (RTL819X_VIEW_\w+)\s+(\S+)", src,
                                re.M):
        d[name] = tok
    return d


def case_b1(src):
    got, total = source_literals(src)
    bad = [fn for fn in FORMATS if got[fn] != FORMATS[fn]]
    n = sum(len(v) for v in FORMATS.values())
    d = source_defines(src)
    want = {"RTL819X_VIEW_MIB": MIB_BASE, "RTL819X_VIEW_MIB_STRIDE": MIB_STRIDE,
            "RTL819X_VIEW_MIB_PORTS": MIB_PORTS, "RTL819X_VIEW_NMIB": NMIB,
            "RTL819X_VIEW_PSRP0": PSRP0, "RTL819X_VIEW_PSRP8": PSRP8,
            "RTL819X_VIEW_TRIES": TRIES, "RTL819X_VIEW_BOUND": BOUND,
            "RTL819X_VIEW_PEEK_MAX": PEEK_MAX, "RTL819X_VIEW_TBL_BASE": TBL_BASE}
    for k, v in want.items():
        tok = d.get(k, "")
        try:
            val = int(tok.rstrip("u"), 0)
        except ValueError:
            val = None
        if val != v:
            bad.append("%s %r" % (k, tok))
    ver = re.findall(r'^#define RTL819X_VIEW_VERSION\s+"([^"]*)"\s*$', src,
                     re.M)
    if ver != [VERSION]:
        bad.append("RTL819X_VIEW_VERSION %r" % ver)

    def strs(rx):
        m = re.search(rx, src, re.S)
        return tuple(re.findall(r'"([^"]*)"', m.group(1))) if m else None
    if strs(r"rtl819x_view_why\[\] = \{([^}]*)\}") != WHY_NAMES:
        bad.append("rtl819x_view_why")
    if strs(r"rtl819x_view_lname\[\] = \{([^}]*)\}") != LAST_NAMES:
        bad.append("rtl819x_view_lname")
    m = re.search(r"rtl819x_view_tbls\[\] = \{(.*?)\n\};", src, re.S)
    tb = tuple((a, int(b), int(c)) for a, b, c in re.findall(
        r'\{ "(\w+)",\s*(\d+),\s*(\d+) \}', m.group(1))) if m else None
    if tb != TBL_TYPES:
        bad.append("rtl819x_view_tbls %r" % (tb,))
    if re.findall(r'\? "(\w+)" : "(\w+)"', src) != [EQ_MIS]:
        bad.append("eq/mis")
    ok = not bad and total == n == 21
    return ok, ("%d of %d literals verbatim in 4 functions, %d sprintf calls "
                "in the file; version, why/last/tbls, eq/mis and 10 constants "
                "%s" % (n - len([b for b in bad if b in FORMATS]), n, total,
                        "equal" if ok else "DIFFER: " + ", ".join(bad)))


def case_b2():
    bad, n = [], 0
    pages = base_pages()
    for name, pg in pages:
        text = render_page(pg)
        for form, t in (("bare", text), ("capture", as_capture(text))):
            n += 1
            try:
                got = find_pages(strip_cr(t), name)
            except Refused as e:
                bad.append("%s %s: %s" % (name, form, e))
                continue
            if len(got) != 1 or render_page(got[0]) != text:
                bad.append("%s %s: re-rendered differently" % (name, form))
    joined = as_capture("".join(render_page(pg) for _, pg in pages))
    try:
        got = find_pages(strip_cr(joined), "all")
        if [render_page(g) for g in got] != [render_page(p) for _, p in pages]:
            bad.append("the %d pages in one capture" % len(pages))
    except Refused as e:
        bad.append("one capture: %s" % e)
    return not bad, ("%d page kinds, %d decodes bare and CRLF-wrapped, and "
                     "all %d in one capture, re-rendered byte for byte%s"
                     % (len(pages), n, len(pages),
                        "" if not bad else ": " + "; ".join(bad[:3])))


B3_SCRIPT = [
    ("none", ["init"]), ("mib", ["w mib"]), ("vlan", ["w tbl vlan"]),
    ("netif", ["w tbl netif"]),
    ("vlan", ["set tear 0 3 12 7", "w tbl vlan"]),
    ("vlan", ["set tear 0 3 0 7", "set tear 0 5 4 2", "w tbl vlan"]),
    ("vlan", ["set tear 0 5 0 2", "set busy 5 10001", "w tbl vlan"]),
    ("peek", ["w peek 0xBB804100 4"]), ("peek", ["w peek 0xBB804128"]),
    ("peek", ["w peek 0xBD006000"]), ("peek", ["w peek 0xBB801114 16"]),
    ("peek", ["w peek 0xB8000040 2"]), ("peek", ["w peek 0xBB804300 2"]),
    ("mib", ["w mib"]),
]


def case_b3(root, src):
    vc = load_viewcheck(root)
    try:
        cut, _ = vc.extract(src)
    except SystemExit:
        return False, "viewcheck refused to cut the driver"
    work = tempfile.mkdtemp(prefix="viewdecode-b3-")
    try:
        exe, out = vc.build(cut, work, "b3")
        if exe is None:
            return False, "the harness does not compile: %s" % \
                out.strip().splitlines()[-1:]
        script = []
        for _, ops in B3_SCRIPT:
            script += ops + ["r"]
        r = vc.Run(exe, script)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    texts = [p["text"] for p in r.pages]
    bad, kinds, pages = [], [], []
    for i, t in enumerate(texts):
        try:
            got = find_pages(t, "harness page %d" % (i + 1))
        except Refused as e:
            bad.append(str(e))
            continue
        if len(got) != 1 or render_page(got[0]) != t:
            bad.append("harness page %d re-rendered differently" % (i + 1))
            continue
        pages.append(got[0])
        kinds.append(got[0]["last"])
    want = [k for k, _ in B3_SCRIPT]
    extra = []
    if pages and len(pages) == len(want):
        extra = [pages[6]["tbl"]["busy"] == 5 and pages[6]["rc"] == -EBUSY,
                 not pages[4]["tbl"]["slot_lines"][3]["eq"],
                 pages[5]["tbl"]["slot_lines"][5]["t"] == 5,
                 pages[8]["ref_why"] == "psrp", pages[9]["ref_why"] == "out"]
    try:
        notes = one_boot(pages)
    except Refused as e:
        bad.append(str(e))
        notes = None
    ok = (r.rc == 0 and not bad and kinds == want and all(extra) and
          len(extra) == 5 and notes == [])
    return ok, ("%d pages from the compiled driver (%s) decode and re-render "
                "byte for byte, busy s05 / t10 mis / t5 / psrp / out as "
                "scripted, one boot%s"
                % (len(pages), " ".join(kinds),
                   "" if ok else ": %s; kinds %s; rc %d; %s" % (
                       "; ".join(bad[:2]), kinds, r.rc, extra)))


def case_b4(src):
    m = re.search(r"rtl819x_view_runs\[\] = \{(.*?)\n\};", src, re.S)
    rows = re.findall(r"\{ 0x([0-9A-F]{8}),\s*(\d+), (\d+), (0x[0-9A-F]+|0) "
                      r"\}", m.group(1)) if m else []
    words = set()
    for a, n, rep, stride in rows:
        for k in range(int(rep)):
            for i in range(int(n)):
                words.add(int(a, 16) + k * int(stride, 16) + 4 * i)
    names = set(WORD_NAME)
    ok = words == names and len(words) == ADMIT and len(REG_NAMES) == 73
    return ok, ("%d runs in the driver's table expand to %d words; this "
                "decoder names %d; %s"
                % (len(rows), len(words), len(names),
                   "the same set" if ok else "only in the driver: %s; only "
                   "here: %s" % (sorted("%08X" % a for a in words - names)[:4],
                                 sorted("%08X" % a for a in names - words)[:4])))


# (port, lo, hi, what the vendor's formula prints), written by hand.
C1_PAIRS = [
    (0, 0x00000000, 0x00000001, "4194304"),
    (1, 0x00000001, 0x00000001, "4194305"),
    (2, 0xFFFFFFFF, 0x00000000, "4294967295"),
    (3, 0xFFFFFFFF, 0x00000001, "4299161599"),
    (4, 0x12345678, 0x00000400, "4600387192"),
    (5, 0xFFFFFFFF, 0xFFFFFFFF, "18014402800254975"),
]


def case_c1():
    def word(p, o):
        for q, lo, hi, _ in C1_PAIRS:
            if o in (0x100, 0x800) and q == (p if o == 0x100 else 5 - p):
                return lo
            if o in (0x104, 0x804) and q == (p if o == 0x104 else 5 - p):
                return hi
        return 0
    pg = make_page("mib", n_mib=1, ld=225, mib=mib_result(word, 0))
    try:
        got = find_pages(render_page(pg), "c1")[0]
    except Refused as e:
        return False, "the built page is refused: %s" % e
    lines = render_asic(view_counters(got)).split("\n")
    bad = []
    for p in range(6):
        rcv = [ln for ln in lines[12 * p:12 * p + 12] if ln.startswith(
            "   Rcv ")]
        snd = [ln for ln in lines[12 * p:12 * p + 12] if ln.startswith(
            "   Snd ")]
        want_r = "   Rcv %s bytes, Drop 0 pkts,etherStatsDropEvents 0" % \
            C1_PAIRS[p][3]
        want_s = "   Snd %s bytes, Unicast 0 pkts, Multicast 0 pkts" % \
            C1_PAIRS[5 - p][3]
        if rcv != [want_r] or snd != [want_s]:
            bad.append("port %d: %s | %s" % (p, rcv, snd))
    return not bad, ("%d (lo, hi) pairs with hi != 0 print the hand-written "
                     "lo + hi x 4194304 in Rcv and Snd%s"
                     % (len(C1_PAIRS), "" if not bad else ": " + bad[0]))


def c2_expected(p):
    """The vendor's port section for a page whose word at offset o of port p
    is 0x1000 x p + o, written from rtl865x_asicCom.c:1784-1830 and B's
    offsets, not from this file's tables."""
    def v(o):
        return 0x1000 * p + o
    head = "<CPU port (extension port included)>" if p == 6 else \
        "<Port: %d>" % p
    return [
        head, "Rx counters",
        "   Rcv %d bytes, Drop %d pkts,etherStatsDropEvents %d"
        % (v(0x100) + v(0x104) * 4194304, v(0x144), v(0x148)),
        "   CRCAlignErr %d, SymbolErr %d, FragErr %d, JabberErr %d"
        % (v(0x14C), v(0x150), v(0x118), v(0x138)),
        "   Unicast %d pkts, Multicast %d pkts, Broadcast %d pkts"
        % (v(0x108), v(0x13C), v(0x140)),
        "   < 64: %d pkts, 64: %d pkts, 65 -127: %d pkts, 128 -255: %d pkts"
        % (v(0x114), v(0x11C), v(0x120), v(0x124)),
        "   256 - 511: %d pkts, 512 - 1023: %d pkts, 1024 - 1518: %d pkts"
        % (v(0x128), v(0x12C), v(0x130)),
        "   oversize: %d pkts, Control unknown %d pkts, Pause %d pkts"
        % (v(0x134), v(0x154), v(0x158)),
        "Output counters",
        "   Snd %d bytes, Unicast %d pkts, Multicast %d pkts"
        % (v(0x800) + v(0x804) * 4194304, v(0x808), v(0x80C)),
        "   Broadcast %d pkts, Late collision %d, Deferred transmission %d "
        % (v(0x810), v(0x824), v(0x820)),
        "   Collisions %d Single collision %d Multiple collision %d pause %d"
        % (v(0x834), v(0x818), v(0x81C), v(0x82C)),
    ]


def case_c2():
    pg = make_page("mib", n_mib=1, ld=225,
                   mib=mib_result(lambda p, o: 0x1000 * p + o, 0x7084))
    try:
        got = find_pages(render_page(pg), "c2")[0]
    except Refused as e:
        return False, "the built page is refused: %s" % e
    have = render_asic(view_counters(got)).split("\n")
    want = [ln for p in range(7) for ln in c2_expected(p)] + \
        ["<Whole system counters>", "   CpuEvent %d pkts" % 0x7084, ""]
    diff = [i for i in range(max(len(have), len(want)))
            if i >= len(have) or i >= len(want) or have[i] != want[i]]
    return not diff, ("86 lines, every counter at its B offset in all 7 "
                      "sections and CpuEvent%s"
                      % ("" if not diff else ": line %d reads %r, want %r" % (
                          diff[0] + 1, have[diff[0]] if diff[0] < len(have)
                          else None, want[diff[0]] if diff[0] < len(want)
                          else None)))


def _bracket_files(work, tag, before_vals, view_page, after_vals):
    paths = []
    for role, body in (("before", render_asic(before_vals)),
                       ("view", render_page(view_page)),
                       ("after", render_asic(after_vals))):
        p = os.path.join(work, "%s-%s.log" % (tag, role))
        with open(p, "w", encoding="ascii", newline="") as fh:
            fh.write(as_capture(body))
        paths.append(p)
    return paths


def _view_and_vals():
    pg = make_page("mib", n_mib=1, ld=225,
                   mib=mib_result(lambda p, o: (mix(p, o) & 0xFFFF) + 10,
                                  0x7084))
    return pg, view_counters(find_pages(render_page(pg), "d")[0])


def case_d1(work):
    pg, v = _view_and_vals()
    keys = COUNTER_KEYS
    half = set(keys[::2])
    runs = [
        ("pinned", dict(v), dict(v), 0, len(keys), 0),
        ("between", {k: x - 1 for k, x in v.items()},
         {k: x + 1 for k, x in v.items()}, 0, 0, len(keys)),
        ("at either end", {k: (x if k in half else x - 3) for k, x in
                           v.items()},
         {k: (x + 5 if k in half else x) for k, x in v.items()}, 0, 0,
         len(keys)),
    ]
    bad = []
    for tag, b, a, want_rc, want_pin, want_moved in runs:
        paths = _bracket_files(work, "d1-" + tag.replace(" ", "-"), b, pg, a)
        rc, out = run_main(["bracket"] + paths)
        m = re.search(r"(\d+) pinned .*?, (\d+) moved and bracketed, (\d+) "
                      r"outside", out)
        got = (rc, int(m.group(1)), int(m.group(2)), int(m.group(3))) if m \
            else (rc, None, None, None)
        if got != (want_rc, want_pin, want_moved, 0):
            bad.append("%s: rc %s pinned %s moved %s outside %s"
                       % ((tag,) + got))
    return not bad, ("pinned (211 equal), strictly between, and at either end "
                     "(106 at before, 105 at after): exit 0, none outside%s"
                     % ("" if not bad else ": " + "; ".join(bad)))


def case_d2(work):
    pg, v = _view_and_vals()
    k_below = (2, "OFFSET_DOT3STATSFCSERRORS_P0")
    k_above = (5, "OFFSET_IFOUTOCTETS_P0")
    k_rev = (SYS, CPUEVENT)
    b = {k: x - 1 for k, x in v.items()}
    a = {k: x + 1 for k, x in v.items()}
    b[k_below] = v[k_below] + 1
    a[k_above] = v[k_above] - 1
    b[k_rev], a[k_rev] = v[k_rev] + 2, v[k_rev] - 2
    paths = _bracket_files(work, "d2", b, pg, a)
    rc, out = run_main(["bracket"] + paths)
    named = re.findall(r"^  outside  (.*?): (\w+)", out, re.M)
    want = [(key_label(k_below), "below"), (key_label(k_above), "above"),
            (key_label(k_rev), "ends")]
    ok = rc == 1 and sorted(named) == sorted(want)
    return ok, ("view below before, above after, and reversed ends, one "
                "counter each: exit %d, named %s" % (rc, named if not ok else
                                                     "exactly those three"))


def e_cases(work):
    """(id, list of (what, problem-or-'')) for E1..E12."""
    P = dict(base_pages())
    T = {k: render_page(v) for k, v in P.items()}

    def rep(name, old, new):
        return T[name].replace(old, new, 1)

    def drop(name, pred):
        return edit(T[name], lambda ls: [x for x in ls if not pred(x)])

    def swap(name, i, j):
        def f(ls):
            ls = list(ls)
            ls[i], ls[j] = ls[j], ls[i]
            return ls
        return edit(T[name], f)

    def ins(name, before_prefix, line):
        def f(ls):
            k = next(i for i, x in enumerate(ls) if x.startswith(before_prefix))
            return ls[:k] + [line] + ls[k:]
        return edit(T[name], f)

    mib_lines = T["mib"].split("\n")
    mo_line = mib_lines[6]
    mo_sw = mo_line.replace(" 13C 140", " 140 13C", 1)
    m2 = next(x for x in mib_lines if x.startswith("m2 "))
    vl = T["vlan"].split("\n")
    s04 = next(x for x in vl if x.startswith("s04 "))
    groups = [
        ("E1", [
            ("version 1.1", expect_refusal(rep("boot", "view 1.0", "view 1.1"),
                                           "version")),
            ("no terminator", expect_refusal(drop("peek", lambda x:
                                                  x.startswith("jiffies")),
                                             "terminator", "input ends")),
            ("a cut page, then a whole one", expect_refusal(
                drop("peek", lambda x: x.startswith("jiffies")) + T["boot"],
                "terminator", "next page")),
            ("jiffies with no line end", expect_refusal(
                T["boot"].rstrip("\n"), "terminator", "no line end")),
            ("no page", expect_refusal("# cat /proc/rtl819x-view\ncat: can't "
                                       "open\n# ", "no-page"))]),
        ("E2", [
            ("admit line missing", expect_refusal(drop(
                "mib", lambda x: x.startswith("admit")), "header", "admit")),
            ("a five-line page", expect_refusal(drop(
                "boot", lambda x: x.startswith("admit")), "header",
                "a page of 5 lines")),
            ("last and n_mib swapped", expect_refusal(swap("boot", 2, 3),
                                                      "header", "last")),
            ("j not a number", expect_refusal(rep("mib", "j 4242", "j x"),
                                              "header", "last")),
            ("lower-case ref", expect_refusal(rep(
                "peek-ref", "ref BB804128", "ref bb804128"), "header", "ref")),
            ("admit 0298", expect_refusal(rep("boot", "admit 298",
                                              "admit 0298"), "render",
                                          "admit 298")),
            ("ld 4294967296", expect_refusal(rep("mib", "ld 225",
                                                 "ld 4294967296"), "range")),
            ("a doubled space", expect_refusal(rep("peek", "a BB804104 ",
                                                   "a BB804104  "), "line"))]),
        ("E3", [
            ("admit 297", expect_refusal(rep("boot", "admit 298",
                                             "admit 297"), "admit")),
            ("admit 299", expect_refusal(rep("mib", "admit 298",
                                             "admit 299"), "admit"))]),
        ("E4", [
            ("a result line under last none", expect_refusal(ins(
                "boot", "jiffies", "a BB804000 00000000"), "result-none"))]),
        ("E5", [
            ("m6 missing", expect_refusal(drop("mib", lambda x:
                                               x.startswith("m6 ")),
                                          "line", "m6")),
            ("m3 before m2", expect_refusal(swap("mib", 9, 10), "mib",
                                            "m3 where m2")),
            ("31 words in m2", expect_refusal(rep(
                "mib", m2, m2.rsplit(" ", 1)[0]), "mib", "31 words")),
            ("words 224", expect_refusal(rep("mib", "words 225", "words 224"),
                                         "mib", "words 224")),
            ("ports 6", expect_refusal(rep("mib", "ports 7", "ports 6"),
                                       "mib", "ports 6")),
            ("rc -16", expect_refusal(rep("mib", "rc 0", "rc -16"), "mib",
                                      "rc -16")),
            ("mc missing", expect_refusal(drop("mib", lambda x:
                                               x.startswith("mc ")), "cut")),
            ("two mc lines", expect_refusal(ins("mib", "jiffies",
                                                "mc 088 00000000"), "mib",
                                            "2 mc lines")),
            ("mo not 1.0's", expect_refusal(rep("mib", mo_line, mo_sw),
                                            "name"))]),
        ("E6", [
            ("tbl netif under last vlan", expect_refusal(rep(
                "vlan", "tbl vlan base BB060000", "tbl netif base BB060000"),
                "tbl", "under")),
            ("vlan with netif's base", expect_refusal(rep(
                "vlan", "base BB060000", "base BB040000"), "tbl", "1.0's")),
            ("words 7", expect_refusal(rep("vlan", "words 8", "words 7"),
                                       "tbl", "words 7")),
            ("s04 missing", expect_refusal(drop("vlan", lambda x:
                                                x.startswith("s04 ")), "tbl",
                                           "s05 where s04")),
            ("a 9th netif slot", expect_refusal(ins(
                "netif", "jiffies", "s08 t1 eq" + " 00000000" * 8), "tbl",
                "slot line 9")),
            ("t0", expect_refusal(rep("vlan", "s00 t1 eq", "s00 t0 eq"), "tbl",
                                  "t0 outside")),
            ("t11", expect_refusal(rep("vlan", "s00 t1 eq", "s00 t11 eq"),
                                   "tbl", "t11 outside")),
            ("mis with t9", expect_refusal(rep("vlan", "s03 t10 mis",
                                               "s03 t9 mis"), "tbl",
                                           "mis with t9")),
            ("seven words", expect_refusal(rep("vlan", s04,
                                               s04.rsplit(" ", 1)[0]), "tbl",
                                           "7 words")),
            ("busy with rc 0", expect_refusal(ins("netif", "jiffies",
                                                  "busy s08"), "tbl",
                                              "busy line with rc 0")),
            ("rc -16 without busy", expect_refusal(drop(
                "vlan-busy", lambda x: x.startswith("busy ")), "tbl",
                "without a busy")),
            ("busy s02 after 3 slots", expect_refusal(rep(
                "vlan-busy", "busy s03", "busy s02"), "tbl", "busy s02")),
            ("rc 0 with 15 slots", expect_refusal(drop(
                "vlan", lambda x: x.startswith("s15 ")), "cut", "15 of 16")),
            ("polls under the slots", expect_refusal(rep(
                "vlan", "polls 16", "polls 15"), "tbl", "polls 15")),
            ("busy with too few polls", expect_refusal(rep(
                "vlan-busy", "polls 10004", "polls 10003"), "tbl",
                "polls 10003")),
            ("rc -5", expect_refusal(rep("vlan", "rc 0", "rc -5"), "tbl",
                                     "rc -5")),
            ("a line after busy", expect_refusal(ins(
                "vlan-busy", "jiffies", "s03 t1 eq" + " 00000000" * 8),
                "extra"))]),
        ("E7", [
            ("unaligned", expect_refusal(rep("peek", "peek BB804100",
                                             "peek BB804102"), "peek",
                                         "multiple of 4")),
            ("n 0", expect_refusal(rep("peek", "n 4", "n 0"), "peek", "n 0")),
            ("n 17", expect_refusal(rep("peek", "n 4", "n 17"), "peek",
                                    "n 17")),
            ("3 a lines under n 4", expect_refusal(drop(
                "peek", lambda x: x.startswith("a BB80410C")), "cut")),
            ("5 a lines under n 4", expect_refusal(ins(
                "peek", "jiffies", "a BB804110 00000000"), "extra")),
            ("a gap", expect_refusal(rep("peek", "a BB804108",
                                         "a BB80410C"), "peek",
                                     "a BB80410C where")),
            ("rc -13", expect_refusal(rep("peek", "rc 0", "rc -13"), "peek",
                                      "rc -13")),
            ("a word 1.0 does not admit", expect_refusal(rep(
                "peek-ref", "peek B8000040 n 2\na B8000040 00000000\n"
                "a B8000044", "peek B8000044 n 2\na B8000044 00000000\n"
                "a B8000048"), "name", "B8000048"))]),
        ("E8", [
            ("none with an address", expect_refusal(rep(
                "boot", "ref 00000000 none", "ref BB804128 none"), "ref")),
            ("none with refused 1", expect_refusal(rep(
                "boot", "refused 0", "refused 1"), "ref")),
            ("refused 0 with out", expect_refusal(rep(
                "boot", "ref 00000000 none", "ref BD006000 out"), "ref")),
            ("psrp outside", expect_refusal(rep(
                "peek-ref", "ref BB804128 psrp", "ref BB80414C psrp"), "ref")),
            ("out inside", expect_refusal(rep(
                "peek-ref", "ref BB804128 psrp", "ref BB804130 out"), "ref")),
            ("out naming an admitted word", expect_refusal(rep(
                "peek-out", "ref BD006000 out", "ref BB804000 out"), "ref"))]),
        ("E9", [
            ("a console line inside a mib page", expect_refusal(as_capture(ins(
                "mib", "m3 ", "[   12.340000] eth4: link up")), "line",
                "eth4")),
            ("a console line inside a vlan page", expect_refusal(as_capture(
                ins("vlan", "s07 ", "eth4: link down")), "line", "eth4"))]),
    ]
    # E10: the asicCounter dump
    vals = {k: 7 for k in COUNTER_KEYS}
    good = render_asic(vals)
    e10 = []

    def asic_refusal(text, needle, code="asic"):
        try:
            asic_blocks(strip_cr(text), "t")
        except Refused as e:
            return "" if e.code == code and needle in str(e) else str(e)
        return "accepted"
    e10.append(("the good dump parses", "" if len(
        asic_blocks(good, "t")) == 1 else "not one block"))
    e10.append(("cut before CpuEvent", asic_refusal(
        good.rsplit("   CpuEvent", 1)[0], "CpuEvent")))
    e10.append(("Rcv -1", asic_refusal(good.replace("   Rcv 7 ", "   Rcv -1 ",
                                                     1), "Rcv -1")))
    e10.append(("%u above 2^32-1", asic_refusal(good.replace(
        "Drop 7 pkts", "Drop 4294967296 pkts", 1), "wider")))
    e10.append(("an interleaved line", asic_refusal(good.replace(
        "Output counters\n", "eth4: link up\nOutput counters\n", 1),
        "eth4")))
    e10.append(("a stray section", asic_refusal(good.split(
        "<Port: 0>\n", 1)[1], "no complete one")))
    stamped = "".join("[  116.%06d] %s\n" % (i, ln) for i, ln in
                      enumerate(good.split("\n")[:-1]))
    e10.append(("a printk-timed dump parses", "" if [
        b["stamps"] is not None for b in asic_blocks(stamped, "t")] == [True]
        else "not one timed block"))
    e10.append(("a printk time on some lines only", asic_refusal(
        stamped.replace("[  116.000003] ", "", 1), "some lines")))
    e10.append(("one foreign character before a line", asic_refusal(
        good.replace("\nRx counters\n", "\nxRx counters\n", 1),
        "xRx counters")))
    groups.append(("E10", e10))
    # E11: the command line
    e11 = []

    def wfile(name, body):
        p = os.path.join(work, name)
        with open(p, "w", encoding="ascii", newline="") as fh:
            fh.write(body)
        return p
    pk = wfile("e11-peek.log", as_capture(T["peek"]))
    mb = wfile("e11-mib.log", as_capture(T["mib"]))
    two = wfile("e11-two.log", as_capture(T["mib"] + T["mib"]))
    ac = wfile("e11-asic.log", as_capture(good, "cat /proc/rtl865x/asicCounter"))
    nop = wfile("e11-none.log", "# ls\r\n# ")
    for what, argv, want in [
            ("no verb", [], 2), ("asic with two files", ["asic", mb, mb], 2),
            ("bracket with two files", ["bracket", mb, mb], 2),
            ("a missing file", ["decode", os.path.join(work, "nope.log")], 2),
            ("decode with no page", ["decode", nop], 2),
            ("asic on a peek page", ["asic", pk], 2),
            ("asic on two pages", ["asic", two], 2),
            ("bracket VIEW an asicCounter dump", ["bracket", ac, ac, ac], 2),
            ("bracket VIEW a peek page", ["bracket", ac, pk, ac], 2),
            ("--self-test with a verb", ["--self-test", "decode", mb], 2),
            ("decode permitted", ["decode", pk, mb], 0),
            ("asic permitted", ["asic", mb], 0),
            ("bracket permitted", ["bracket", ac, mb, mb], None)]:
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                rc, out = run_main(argv)
            except SystemExit as e:
                rc, out = e.code, ""
        if want is None:
            ok = rc in (0, 1) and "REFUSED" not in out
        else:
            ok = rc == want and (want != 2 or "REFUSED" in out)
        e11.append((what, "" if ok else "rc %s: %s" % (rc, out.strip()[:120])))
    groups.append(("E11", e11))
    # E12: --one-boot
    b0 = render_page(dict(P["mib"], n_mib=2, ld=450, jiffies=5000))
    b1 = render_page(dict(P["mib"], n_mib=1, ld=225, jiffies=5100))
    w1 = render_page(dict(P["mib"], n_mib=1, ld=225, jiffies=100))
    f0, f1, fw = wfile("e12-a.log", b0), wfile("e12-b.log", b1), \
        wfile("e12-w.log", w1)
    rc, out = run_main(["decode", "--one-boot", f0, f1])
    e12 = [("n_mib 2 -> 1 with jiffies rising",
            "" if rc == 2 and "[one-boot]" in out else "rc %d" % rc)]
    rc, out = run_main(["decode", "--one-boot", f0, fw])
    e12.append(("jiffies 5000 -> 100 voids the pair, said, exit 0",
                "" if rc == 0 and "void" in out else "rc %d" % rc))
    rc, out = run_main(["decode", f0, f1])
    e12.append(("without --one-boot no cross-page check",
                "" if rc == 0 else "rc %d" % rc))
    groups.append(("E12", e12))
    return groups


def selftest(root):
    """Print the cases; return the number that failed."""
    src_path = os.path.join(root, *SOURCE_PARTS)
    with open(src_path, encoding="utf-8") as fh:
        src = fh.read()
    print("viewdecode %s self-test" % TOOL_VERSION)
    print("  source  %s  sha256 %s" % (src_path, hashlib.sha256(
        src.encode("utf-8")).hexdigest()[:16]))
    work = tempfile.mkdtemp(prefix="viewdecode-")
    fails, n = 0, 0
    try:
        cases = [("A1", lambda: case_a1(root)), ("B1", lambda: case_b1(src)),
                 ("B2", case_b2), ("B3", lambda: case_b3(root, src)),
                 ("B4", lambda: case_b4(src)), ("C1", case_c1),
                 ("C2", case_c2), ("D1", lambda: case_d1(work)),
                 ("D2", lambda: case_d2(work))]
        for cid, fn in cases:
            try:
                ok, det = fn()
            except Exception as e:
                ok, det = False, "raised %s: %s" % (type(e).__name__, e)
            n += 1
            fails += 0 if ok else 1
            print("  %-4s  %-4s %s" % ("ok" if ok else "FAIL", cid, det))
        try:
            groups = e_cases(work)
        except Exception as e:
            groups = [("E1", [("building the E cases", "raised %s: %s"
                                % (type(e).__name__, e))])]
        for cid, items in groups:
            bad = [(w, p) for w, p in items if p]
            n += 1
            fails += 1 if bad else 0
            print("  %-4s  %-4s %d of %d refused for the named reason, each "
                  "an edit of an input that is accepted%s"
                  % ("ok" if not bad else "FAIL", cid, len(items) - len(bad),
                     len(items), "" if not bad else ": " + "; ".join(
                         "%s: %s" % b for b in bad[:3])))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("RESULT: %d case(s), %d failed" % (n, fails))
    return n, fails


# Each mutant: (id, what it breaks, the case that must go red, [(old, new)]).
# The anchors are split literals so this table cannot match itself.
MUTANTS = [
    ("M1", "a swapped offset: Multicast and Broadcast trade places", "C2",
     [('"OFFSET_ETHERSTATSMULTICASTPKTS_P0": (0x' '13C, 295)',
       '"OFFSET_ETHERSTATSMULTICASTPKTS_P0": (0x140, 295)'),
      ('"OFFSET_ETHERSTATSBROADCASTPKTS_P0": (0x' '140, 296)',
       '"OFFSET_ETHERSTATSBROADCASTPKTS_P0": (0x13C, 296)')]),
    ("M2", "the high word shifted by 32, the other SDKs' arm", "C1",
     [("return lo + (hi <" "< 22)", "return lo + (hi << 32)")]),
    ("M3", "no CRLF strip", "A1",
     [('return text.replace("\\r", ' '"")', "return text")]),
    ("M4", "< for <= at the bracket's lower end", "D1",
     [("below = not (b <" "= v)", "below = not (b < v)")]),
    ("M5", "the admit check removed", "E3",
     [('if pg["admit"] !' '= ADMIT:', "if False:")]),
    ("M6", "a cut page skipped instead of refused", "E1",
     [("            raise Refused(\n                \"terminator\"" ", ",
       "            i = j\n            continue\n            raise Refused(\n"
       "                \"terminator\", ")]),
    ("M7", "reversed ends not called reversed", "D2",
     [("rev = b >" " a", "rev = False")]),
    ("M8", "the re-render gate removed", "E2",
     [("    if again !" "= text:", "    if False:")]),
]


def mutants(root):
    """Print M0..M8; return the number of survivors."""
    me = os.path.abspath(__file__)
    with open(me, encoding="utf-8") as fh:
        own = fh.read()
    work = tempfile.mkdtemp(prefix="viewdecode-mut-")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

    def run(text, tag):
        d = os.path.join(work, tag)
        os.makedirs(d)
        path = os.path.join(d, "viewdecode.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        p = subprocess.run([sys.executable, path, "--self-test",
                            "--no-mutants", "--root", root],
                           capture_output=True, text=True, encoding="utf-8",
                           env=env, timeout=600)
        res = {}
        for ln in p.stdout.split("\n"):
            m = re.match(r"^ {2}(ok|FAIL)\s{2,}([A-E][0-9]+)\s", ln)
            if m:
                res[m.group(2)] = m.group(1) == "ok"
        return res, p

    print("")
    print("mutants (M0 is the unmutated copy through the same path)")
    try:
        res0, p0 = run(own, "M0")
        if not res0 or not all(res0.values()) or p0.returncode != 0:
            print("  FAIL  M0   the unmutated copy is not green (rc %d, %d "
                  "cases): no kill counts" % (p0.returncode, len(res0)))
            return len(MUTANTS) + 1
        print("  ok    M0   unmutated copy green on %d cases" % len(res0))
        survivors = 0
        for mid, what, named, edits in MUTANTS:
            text, why = own, ""
            for old, new in edits:
                k = own.count(old)
                if k != 1:
                    why = "anchor occurs %d times: %r" % (k, old[:40])
                    break
                text = text.replace(old, new)
            if why:
                print("  FAIL  %-4s %s (%s)" % (mid, why, what))
                survivors += 1
                continue
            res, p = run(text, mid)
            red = sorted((c for c, ok in res.items() if not ok),
                         key=lambda c: (c[0], int(c[1:])))
            killed = named in red and set(res) == set(res0)
            survivors += 0 if killed else 1
            print("  %-4s  %-4s %-50s named %-4s red %s"
                  % ("ok" if killed else "FAIL", mid, what, named,
                     ",".join(red) or ("-" if res else "(no case ran: rc %d)"
                                       % p.returncode)))
        print("RESULT: %d mutant(s), %d killed by the case named for them, "
              "%d survived" % (len(MUTANTS), len(MUTANTS) - survivors,
                               survivors))
        return survivors
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="viewdecode.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", nargs="?", choices=["decode", "asic", "bracket"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--one-boot", action="store_true",
                    help="decode: the pages are one boot, in order")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--no-mutants", action="store_true")
    ap.add_argument("--root", default=ROOT,
                    help="self-test: the repository whose bench/ and driver "
                         "it reads")
    a = ap.parse_intermixed_args(argv)
    try:
        if a.self_test:
            if a.verb or a.files:
                raise Refused("args", "--self-test takes no verb and no file")
            if not shutil.which("gcc"):
                raise NoRun("no gcc on PATH: B3 compiles the driver through "
                            "tools/viewcheck.py's harness")
            if not os.path.isfile(os.path.join(a.root, *SOURCE_PARTS)):
                raise NoRun("no %s under %s" % ("/".join(SOURCE_PARTS),
                                                a.root))
            if not git_bench_logs(a.root):
                raise NoRun("git ls-files lists no bench/**/*.log under %s"
                            % a.root)
            n, fails = selftest(a.root)
            if fails or a.no_mutants:
                return 1 if fails else 0
            return 1 if mutants(a.root) else 0
        if a.verb is None:
            raise Refused("args", "name a verb: decode, asic or bracket (or "
                          "--self-test)")
        if a.no_mutants or a.root != ROOT:
            raise Refused("args", "--no-mutants and --root go with "
                          "--self-test")
        if a.one_boot and a.verb != "decode":
            raise Refused("args", "--one-boot goes with decode")
        if a.verb == "decode":
            if not a.files:
                raise Refused("args", "decode takes one file or more")
            return cmd_decode(a.files, a.one_boot)
        if a.verb == "asic":
            if len(a.files) != 1:
                raise Refused("args", "asic takes one file, not %d"
                              % len(a.files))
            return cmd_asic(a.files[0])
        if len(a.files) != 3:
            raise Refused("args", "bracket takes BEFORE VIEW AFTER, not %d "
                          "file(s)" % len(a.files))
        return cmd_bracket(*a.files)
    except Refused as e:
        print("REFUSED %s" % e)
        return 2
    except NoRun as e:
        print("REFUSED: the self-test cannot run here: %s" % e)
        return 3


if __name__ == "__main__":
    sys.exit(main())
