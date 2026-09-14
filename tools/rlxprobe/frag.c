/* frag.c -- `R1f`'s fragment.  ONE translation unit, compiled once per row of
 * `tools/isa-toolchain.tsv` by a different (toolchain, -march) pair each time.
 *
 * 🔴 THIS FILE IS BUILT BY TOOLCHAINS THAT ARE UNDER TEST.  Nothing else in
 * `probe6` is: the framework -- `start.S`, `uart.S`, `report.c`, `exc.S`,
 * `cells6.S`, `probe6rows.c`, `probe6.c` -- is built by the host cross-compiler
 * at `-march=mips1`, the configuration every payload that has ever executed on
 * this die was built with.  An instrument built out of the thing it measures
 * cannot tell a failure to compute from a failure to print.
 *
 * WHY IT IS THIS FRAGMENT.  `tools/isa-toolchain.tsv`'s header carries the
 * refutation that chose it; the short version is that the obvious fragment
 * (`*p ^ seed`) had its load delay slot filled with `jr ra` in all nine
 * configurations tried, so there was no hazard left to expose.  This one
 * compiles, in every column, to exactly:
 *
 *     lw   v0,0(a1)        <- the load
 *     nop                  <- present iff the -march is on TC-15's exposed side
 *     sw   v0,0(a0)        <- the consumer, at distance 0 when the nop is absent
 *
 * and the register is `v0` in every column, which is the one the caller can
 * prime -- see `cells6.S`'s thunk.  Both facts are re-checked against the built
 * object by `tools/tcpay.py verify`; neither is taken on trust from this
 * comment.
 *
 * WHY `volatile` ON BOTH.  Without it the whole function is a no-op the
 * optimiser may delete or reorder, and a fragment that was optimised away reads
 * exactly like a fragment whose hazard did not fire.  With it, the load and the
 * store both stay and stay in this order, in every column -- which is what
 * makes the ONLY difference between columns the presence of the nop.
 *
 * WHY NO HEADER.  This file must compile under gcc 3.4.6 with no include path
 * into this tree: `rlxprobe.h` uses `-D` macros the variant drivers are never
 * given, on purpose.  It has no dependencies at all.
 *
 * The symbol is renamed per variant with `-Drlxf=rlxf_<vid>` so that ten
 * objects defining one function can be linked into one image.
 */
void rlxf(volatile unsigned *d, volatile const unsigned *s)
{
	*d = *s;
}
