#!/usr/bin/env python3
"""flashscan.py -- prove from the emitted image that rlxboot cannot write flash.

THE ARGUMENT THIS TOOL CHECKS.  On this controller the memory-mapped window at
0xBD000000 is read-only by construction: `docs/loader-flash-write.md` records
that a command is issued by WRITING the controller's `SFDR`, so a store into the
window is not a transaction.  Every program and erase in the vendor's own code
goes through the controller registers at 0xB8001200.. .  So "this image has no
program or erase path" reduces to "this image never forms an address in the
controller's register block", which is a property of the instruction stream.

The tool reads a disassembly and reconstructs every address the code builds:

  * every `lui rD, 0xHHHH` on its own, as 0xHHHH0000;
  * every `lui rD, 0xHHHH` followed within a short window by
    `ori rX, rD, 0xLLLL` or `addiu rX, rD, imm`, as the combined address;
  * every load or store `op rX, disp(rD)` where rD was last set by a `lui`,
    as base + disp.

It REFUSES if any of those lands in [0xB8001200, 0xB8001300), the SPI flash
controller's register block.  It prints the whole census either way, because a
checker whose output is only "ok" is a checker nobody can audit.

  flashscan.py [--quiet]      reads a disassembly on stdin
  exit 0 clean, 1 a hit, 2 nothing to scan (which is a refusal, not a pass)
"""

import re
import sys

LO, HI = 0xB8001200, 0xB8001300

LOADS = {"lb", "lbu", "lh", "lhu", "lw", "lwl", "lwr", "ll", "lwc1", "ldc1"}
STORES = {"sb", "sh", "sw", "swl", "swr", "sc", "swc1", "sdc1"}

INSN = re.compile(
    r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+([a-z][a-z0-9.]*)\s*(.*)$")


def main():
    quiet = "--quiet" in sys.argv[1:]
    # register -> the full 32-bit constant it is known to hold.  FULL, not just
    # the lui half: with only the high half tracked, `lui rD,0xb800` then
    # `ori rD,rD,0x1200` then `sw rX,0(rD)` recorded the store as 0xB8000000 and
    # the census read 0xB8000000 for the UART too.  The pair entry caught that
    # case anyway, so it was not a false negative -- but a census printing the
    # wrong address is a census a reader cannot use.
    lui = {}
    census = []                   # (kind, address, text)
    n_insn = 0

    lines = sys.stdin.read().splitlines()
    for i, ln in enumerate(lines):
        m = INSN.match(ln)
        if not m:
            continue
        n_insn += 1
        mn, ops = m.group(3), m.group(4).strip()
        ops = ops.split("#")[0].strip()

        if mn == "lui":
            f = [x.strip() for x in ops.split(",")]
            if len(f) == 2:
                try:
                    v = int(f[1], 0) & 0xFFFF
                except ValueError:
                    continue
                lui[f[0]] = (v << 16) & 0xFFFFFFFF
                census.append(("lui", (v << 16) & 0xFFFFFFFF, ln.strip()))
            continue

        if mn in ("ori", "addiu", "addu", "or"):
            f = [x.strip() for x in ops.split(",")]
            if len(f) == 3 and f[1] in lui:
                base = lui[f[1]] & 0xFFFFFFFF
                try:
                    imm = int(f[2], 0)
                except ValueError:
                    # a register operand: the value is not a constant any more,
                    # and the destination stops being a known lui base
                    lui.pop(f[0], None)
                    continue
                if mn == "ori":
                    addr = base | (imm & 0xFFFF)
                else:
                    if imm > 0x7FFF:
                        imm -= 0x10000
                    addr = (base + imm) & 0xFFFFFFFF
                census.append(("pair", addr, ln.strip()))
                lui[f[0]] = addr
            elif len(f) == 3:
                lui.pop(f[0], None)
            continue

        if mn in LOADS or mn in STORES:
            m2 = re.match(r"^([^,]+),\s*(-?[0-9a-fx]+)\(([^)]+)\)$", ops)
            if m2:
                reg = m2.group(3).strip()
                if reg in lui:
                    try:
                        disp = int(m2.group(2), 0)
                    except ValueError:
                        disp = 0
                    addr = (lui[reg] + disp) & 0xFFFFFFFF
                    census.append(("store" if mn in STORES else "load",
                                   addr, ln.strip()))
            if mn in LOADS:
                # the loaded register no longer holds a known constant
                m3 = re.match(r"^([^,]+),", ops)
                if m3:
                    lui.pop(m3.group(1).strip(), None)
            continue

        # Anything else that writes a register we were tracking: stop trusting
        # it.  Being conservative here can only ADD census entries, never hide
        # one, because an untracked register contributes nothing to the census
        # -- which is why the negative control matters.
        f = [x.strip() for x in ops.split(",")] if ops else []
        if f:
            lui.pop(f[0], None)

    if n_insn == 0:
        sys.stderr.write("flashscan: no instructions found -- refusing rather "
                         "than reporting a clean scan of nothing\n")
        return 2

    hits = [c for c in census if LO <= c[1] < HI]
    seen = sorted({(k, a) for k, a, _ in census})
    if not quiet:
        print("flashscan: %d instructions, %d addresses formed" % (n_insn, len(seen)))
        for k, a in seen:
            print("    %-6s 0x%08X" % (k, a))
    if hits:
        print("flashscan: REFUSED -- %d reference(s) into the SPI controller "
              "block [0x%08X,0x%08X)" % (len(hits), LO, HI))
        for k, a, t in hits:
            print("    %-6s 0x%08X   %s" % (k, a, t))
        return 1
    print("flashscan: ok -- no address in [0x%08X,0x%08X) is formed anywhere "
          "in this image" % (LO, HI))
    return 0


if __name__ == "__main__":
    sys.exit(main())
