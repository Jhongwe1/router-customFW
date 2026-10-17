# `rlxfw-seam.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/net/rlxfw-seam.c`](../../kernel/linux-2.6.30/drivers/net/rlxfw-seam.c)
until 2026-10-18 — lines 1–86 at commit `79fc1345` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [nic](nic.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rlxfw-seam.c` counts the file's lines at `79fc1345`.

```c
/*
 * rlxfw-seam.c -- what code outside the vendor Ethernet tree still needs from
 * it when that tree is not built.   R6b-8 8b.   THIS FILE IS NOT REALTEK'S.
 *
 * ======================================================================
 * WHAT IT IS
 * ======================================================================
 *
 * `CONFIG_RTL_819X_SWCORE=n` (config/rlxfw-kernel.delta: `quiet` and
 * `loud` since R6b-8 8g) drops `drivers/net/rtl819x/` and
 * `drivers/net/rtk_vlan.o` from the link.  Ten symbols that code OUTSIDE
 * that tree references are then defined nowhere -- R6-4's count, in four
 * places (config/host-compat/0007's header, and the R6-4 row of
 * config/rlxfw-kernel.delta).  The vendor callers may change only through
 * a marks row or a host-compat patch, and six of the ten sit in compiler-
 * output `.S` files and a WLAN driver whose conditional structure is not
 * this project's, so the ten are PROVIDED here instead, each with the value
 * the vendor's own code gives when it has nothing to report.
 *
 * The body is under `#ifndef CONFIG_RTL_819X_SWCORE`, so the SWCORE=y image
 * -- the mainline until 8g -- links the vendor's ten and this file adds only
 * `rlxfw_seam_id`, the witness `config/rlxfw-marks.tsv` MK12 reads in both
 * images (`str:rlxfw-seam`).  A body built beside the vendor's would be a
 * second definition of each name and the link would say so.
 *
 * ======================================================================
 * THE ONE WRITE: THE LOADER'S DMA ENGINE
 * ======================================================================
 *
 * The loader leaves the CPU port's DMA engine RUNNING: `CPUICR = C4000000`
 * at the prompt (量 `bench/2026-09-19b/X7-cpufull-a`), RXCMD set, rings at
 * `0xA040FC70` -- physical `0x0040FC70`, memory this kernel uses.
 * With SWCORE=y the vendor's `re865x_probe()` disarms it at
 * `device_initcall` (讀 `rtl_nic.c:6224-6225` in the staged tree:
 * `CPUIIMR = 0x00` then `CPUICR &= ~(TXCMD | RXCMD)`), and `RLXFW-N1` reads
 * `00000000` at `late_initcall` after it (量: 63 such lines in the committed
 * bench files at 95dabac, and no other value of N1 in any of them).  With
 * SWCORE=n nothing does, and `rtl819x-nic.c`'s own header says
 * why that is the dangerous state (`docs/history/known-issues-segment-limits.md`, `R6-4`'s `D4`
 * row: "Remove the driver and something else must do that first").
 *
 * So the seam's `bsp_swcore_init()` makes the vendor's two writes, in the
 * vendor's order.  It is called from `bsp_setup()` (the `B07` mark's
 * anchor), the first call in `arch_mem_init()`, so it runs before
 * `bootmem_init()` and `paging_init()` (`B08`) -- before any allocator
 * exists, and EARLIER than the vendor's `device_initcall`.  A disarm moved
 * into `rtl819x-nic`'s `late_initcall` would be later than today's, and is
 * the wrong place.
 *
 * Each register and bit has two sources, as `rtl819x-nic.c` records for the
 * same names: 讀 `rtl865xc_asicregs.h` (`CPUICR` :492, `CPUIIMR` :512,
 * `TXCMD` :527, `RXCMD` :528, `CPU_IFACE_BASE` :491) and 量 on this die
 * (`CPUICR` `C4000000` at the loader, `00000000` under Linux after the
 * vendor's probe; `CPUIIMR` `000007F8` at the loader, whose decode against
 * the header has no residue -- `notes/nic-driver.md` § 2).
 *
 * The two marks put the before and after on every boot capture of the
 * SWCORE=n image, where `N1` alone would show only the after:
 *
 *   RLXFW-SM0=XXXXXXXX   CPUICR as the loader left it (predicted C4000000)
 *   RLXFW-SM1=XXXXXXXX   CPUICR read back after the write (predicted with
 *                        bits 31 and 30 clear, the rest as SM0)
 *
 * The SWCORE=y image prints neither: the vendor's `bsp_swcore_init()` runs
 * there, and the absence of both lines is how a capture says which one ran.
 *
 * ======================================================================
 * WHAT THIS FILE DOES NOT DO
 * ======================================================================
 *
 * 1. It does not configure the switch.  Every switch register the vendor's
 *    probe wrote is left here as the loader left it.  rtl819x-switch's verbs,
 *    which /init types, take some over: 1.5's `init` sets `EnablePHYIf`
 *    (`notes/switch-driver.md` § 8.3); 1.6's `vlan` writes the VLAN group.
 * 2. It does not check `REVR`.  The vendor's `bsp_swcore_init()` returns
 *    non-zero for an unrecognised chip, and `bsp_setup()` then halts; this
 *    board's `REVR` is `8196E001` (量, `SPEC.md` `REG-29`) and `RLXFW-B07`
 *    reads `00000000` (量: 169 such lines in the committed bench files at
 *    95dabac, and no other value in a capture), so the seam returns 0 and
 *    the halt branch is not taken.
 * 3. It does not bound the window before it runs.  From kernel entry to
 *    `bsp_setup()` the loader's engine is still armed, on this image as on
 *    every earlier one; the seam shortens the window the vendor's probe
 *    closed later, it does not remove it.  What owns `0x8040FC70` in each
 *    image's `System.map` is `notes/switch-driver.md` § 13's reading.
 */
```
