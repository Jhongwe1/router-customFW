# `rtl819x-view.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/net/rtl819x-view.c`](../../kernel/linux-2.6.30/drivers/net/rtl819x-view.c)
until 2026-10-18 — lines 1–149 at commit `7f23a2e3` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [switch](switch.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-view.c` counts the file's lines at `7f23a2e3`.

```c
/*
 * rtl819x-view.c -- a read-only view of the RTL8196E's switch registers, its
 * MIB counters, its CPU interface, PIN_MUX, and three of its tables.
 *
 * R6b-8 8c, and 8d for 1.1.  One node, /proc/rtl819x-view, three verbs:
 *
 *     mib              the 225 MIB words of ports 0-6, one load each
 *     tbl vlan|netif|l2  the VLAN table's 16 slots, the netif table's 8 or
 *                      the L2 table's 1,024 (1.1), as the vendor's reader does
 *     peek A [n]       n words (1-16, default 1) from the KSEG1 address A
 *
 * A `cat` prints the cached result of the last verb that loaded anything, and
 * loads nothing itself -- which matters because one `cat` renders the page
 * twice (FW-64).
 *
 * ======================================================================
 * WHY A FILE OF ITS OWN
 * ======================================================================
 *
 * Not a 1.4 of rtl819x-switch.c.  Seating 43's third press pins HEAD's
 * rtl819x-switch.c and tools/mdiocheck.py by sha, and mdiocheck cuts that
 * driver from its 1.3 banner to the END OF THE FILE, so a block appended
 * there would enter mdiocheck's harness and fail it.  This file shares no
 * code and no symbol with it: rtl819x-switch keeps its own read path, its
 * PSRP bookkeeping and its MDIO gate, and nothing here calls them.
 *
 * ======================================================================
 * WHAT MAY BE LOADED: THE ADMISSION TABLE
 * ======================================================================
 *
 * A word is loaded only if it lies inside one of four named blocks AND two of
 * three sources place it: B, the header the build compiles
 * (drivers/net/rtl819x/AsicDriver/rtl865xc_asicregs.h, sha256 e29c3051...);
 * D, the draft datasheet; and 量, a value this die printed for the word in a
 * capture committed under bench/: a loader DW dump, or, for the MIB, the
 * vendor's /proc/rtl865x/asicCounter dump.  That is CLAUDE.md's rule for a
 * register value entering code, applied to an address entering a read path.
 * 311 words pass under it -- the table below, 298, and 1.1's at the end of
 * this file, 13 -- word for word, and every run carries its sources.
 *
 * That 量 is narrower than "any reading": a read through the vendor's
 * /proc/rtl865x/memory does not count, and in 1.0 one word turned on it:
 * 0xBB804500, SBFCTR/SBFCR0 (B :1673-:1674), printed 000000F4 on all three
 * such reads (bench/2026-09-21b: B5-REGc, B5-REGc2, D2-REGa-a2), and 1.0
 * refused it (8c's census: 299 with it, 298 with 量 limited as above; 8c's
 * ruling D2: 298).  8c-cells then read it and twelve one-source words with
 * the loader's DW (bench/2026-09-27d/AL-D*), so 1.1 admits the thirteen
 * (notes/switch-driver.md section 16.4).  0x4D48 stays out: a reading and
 * no name in B's live branch.  Such words go through the vendor's memory
 * node, which bounds nothing itself; tools/cardcheck.py does (HW-1).
 *
 * Everything else is refused BEFORE ANY LOAD, the whole request with it:
 * `peek A n` checks all n words first, and loads none unless all n pass.
 * Flash (0xBD000000-0xBD3FFFFF, 0xBFC00000 up) is in no block, so H601
 * (flash 0x6000-0x7FFF) cannot reach a capture through this node.  The
 * admission is by exact KSEG1 address: the KSEG0 alias of an admitted
 * register (0x9B80xxxx) and its physical address are refused like any other.
 *
 * PSRP0-PSRP8 (0xBB804128-0xBB804148) are refused with a reason of their
 * own, `psrp`: bit 8, LinkDownEventFlag, clears when read (B :1328, D Table
 * 65, 量 NET-11), and /proc/rtl819x-switch 1.2 already reads them and keeps
 * what it consumes.  A read here would consume it where nothing keeps it.
 *
 * ======================================================================
 * WHAT THIS DRIVER DOES NOT DO
 * ======================================================================
 *
 * 1. It STORES TO NO REGISTER, ever: there is no store accessor in this file,
 *    and so no unlock.  NET-109's ByPassTCRC cell, which needs a write, goes
 *    through the vendor's /proc/rtl865x/memory (decision D4).
 * 2. It loads nothing at boot.  The initcall creates the node and prints
 *    nothing unless that fails (RLXFW-VW0-NOPROC).
 * 3. It issues no table command.  `tbl` never writes SWTACR, SWTAA, a TCR
 *    or EN_STOP_TLU, so the table engine runs nothing and no table can
 *    change because of it; see the table read below.
 * 4. It issues no MDIO command.  MDIO stays rtl819x-switch 1.3's.
 * 5. It says nothing about read side effects beyond the ones named here:
 *    none is known for the 311 (推), and which of them were read on this die
 *    before is in the sources column.  The MIB's read-to-clear is 未定.
 *
 * ======================================================================
 * THE TABLE READ
 * ======================================================================
 *
 * 讀 `_rtl8651_readAsicEntry`, drivers/net/rtl819x/AsicDriver/96E/
 * rtl865x_asicBasic.S:1043-1215, the reader the vendor's VLAN, netif and L2
 * getters call.  Per slot: load SWTACR (0xBB804D00) until bit 0,
 * ACTION_START (B :209-:211), reads clear -- the vendor's wait is unbounded;
 * this one gives up after RTL819X_VIEW_BOUND polls with udelay(1) between
 * them, 1.3's MDIO bound, and returns -EBUSY with the slot named and no
 * table load after it.  Then, up to ten times (`li $16,10`): the slot's
 * eight words at 0xBB000000 + (type << 16) + (slot << 5) into a first buffer,
 * the same eight into a second, compared word by word.  Equal ends the
 * tries; after ten unequal ones the vendor copies the SECOND buffer out and
 * returns success.  This prints that second buffer, the number of tries, and
 * `eq` or `mis`.  The StopTLU variant (:1216 on) sets EN_STOP_TLU in SWTCR0
 * and has no C caller in the tree (讀, grep); it is not what this copies.
 * Base 0xBB000000 is REAL_SWTBL_BASE (B :151), the type numbers are the
 * enum in rtl865x_asicBasic.h (VLAN 6, netif 4; L2 0), the slot counts are
 * rtl865x_asicCom.h's (16 VLAN slots under CONFIG_RTL_8196E, 8 netifs), and
 * the 32-byte stride is the `sll $2,$18,5` of the reader; 量 SWTAA reads
 * BB060100 at the loader and BB040020 under Linux (NET-28), both inside
 * these windows on slot boundaries.  D has no table section (L2: 1.1's).
 *
 * ⚠️ `rtl8651_getAsicVlan` reads index = vid (rtl865x_asicCom.c:146) while
 * the vendor's writer searches for a free slot, so a slot number here is NOT
 * a VID; the decoder never takes one for the other.
 *
 * ======================================================================
 * THE MIB
 * ======================================================================
 *
 * The 32 words per port that the vendor's `rtl865xC_dumpAsicDiagCounter`
 * (rtl865x_asicCom.c:1776 on) reads, for ports 0-6 (0-5 and the CPU port),
 * and CpuEvent: 7 x 32 + 1 = 225.  Loaded per port in ascending address
 * order, RX then TX, and CpuEvent last; the vendor's order is unsequenced C
 * (printf arguments), so no order is copied.  Out: MIB_CONTROL at 0x000 (a
 * write restarts the counters; it is never read either), etherStatsOctets
 * (0x10C/0x110), ifOutDiscards (0x814), 0x828 and 0x830, which the vendor's
 * dump does not read (B only), and ports 7-8 (B only).  The byte counters are
 * a word pair (lo, lo + 4); the pair can tear across a carry between its two
 * loads, and nothing here can tell (推).
 *
 * ======================================================================
 * THE PAGE
 * ======================================================================
 *
 *     version rtl819x-view 1.1
 *     admit %u                 words the tables admit, summed at render
 *     last %s j %lu rc %d      none|mib|vlan|netif|peek|l2, its jiffies, rc
 *     n_mib %lu n_tbl %lu n_peek %lu refused %lu busy %lu ld %lu
 *     ref %08X %s              the last refused word and none|out|psrp
 *     ...the last verb's result...
 *     jiffies %lu              the terminator
 *
 * `refused` counts -EACCES refusals, `busy` the tbl verbs refused -EBUSY,
 * `ld` every load this file has made.  A refused or malformed request
 * changes no cached result.  The result's own lines, and the page's size,
 * are over the /proc section below.
 *
 * ======================================================================
 * WHAT IT CANNOT SEE
 * ======================================================================
 *
 * The silicon.  tools/viewcheck.py drives this file on the host against a
 * model written from the same sources as the table, so a misreading shared
 * by both passes there.  How long SWTACR stays busy, whether a table slot
 * tears, whether a MIB read clears a counter: the bench says.
 */
```
