#!/usr/bin/env bash
# qemu-run.sh -- run an rlxprobe payload under qemu-system-mips.
#
# WHAT A PASS HERE MEANS, AND IT IS LESS THAN IT LOOKS
# ----------------------------------------------------
# qemu interlocks the load delay slot. This core does not -- that is F46, it is
# measured, and it is the whole reason `tools/hazlint` exists. So a payload that
# produces the right value under qemu has demonstrated that its CONTROL FLOW is
# right: it is linked where it thinks it is, the entry is the first byte, the
# UART routine's loop terminates, the report is well formed, and the run reaches
# its end marker. It has demonstrated NOTHING about the silicon.
#
# For probe1 the gap is sharper still and it is worth stating before anyone runs
# it: TCG invalidates its translation blocks when a store lands on code it has
# already translated, so **qemu behaves like a machine with a coherent I-cache**.
# Every cache cell should therefore come back FRESH under qemu, including cell 1,
# which is the cell whose whole purpose on the device is to come back STALE.
# A qemu run where cell 1 is STALE would mean the harness is broken, not that
# qemu found something. The expectations are opposite, and that is the point:
# an emulator kinder than the device certifies exactly the bugs the device
# rejects, which is how upstream's P9-12 got certified by its own simulator.
#
# THE ONE THING THAT HAS TO CHANGE
# --------------------------------
# The device's 16550 is at 0xB8002000 with LSR at 0xB8002014 -- four-byte
# register spacing. qemu's Malta board has an ordinary ISA 16550 at 0xB80003F8
# with LSR at 0xB80003FD. That is a build knob (`UART_THR` / `UART_LSR`), so the
# same sources are assembled for both and exactly one pair of constants differs.
#
# MEASURED 2026-08-25 on this host, qemu-system-mips 8.2.2:
#   * `-M malta -m 32 -kernel <elf>` loads a plain ELF linked at 0x80500000 and
#     jumps to its entry. Verified with a nine-instruction payload that wrote
#     'A', 'B', '\n' to 0xB80003F8 and produced exactly those three bytes.
#   * `-M mipssim` is the other candidate; malta is used because its 16550 is
#     where an ordinary bare-metal MIPS payload expects one.
#   * Nothing here exits qemu by itself -- `rlx_reset` writes WDTCNR and spins,
#     and Malta has no watchdog at 0xB800311C -- so the run is bounded by
#     `timeout` and judged on what reached the serial file before it.
set -o nounset

P="${1:?usage: qemu-run.sh <payload> [bin] [elf]}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECS="${QEMU_SECONDS:-8}"
OUT="${QEMU_OUT:-$(mktemp -d)/$P}"

if ! command -v qemu-system-mips >/dev/null 2>&1; then
    echo "  skip   qemu                                       no qemu-system-mips on this machine"
    exit 0
fi

mkdir -p "$(dirname "$OUT")"
B="$(mktemp -d)"
trap 'rm -rf "$B"' EXIT

echo "--- rebuilding $P for qemu: UART 0xB80003F8, vector 0x80000180, BEV cleared, eret ---"
# Three constants change and nothing else. qemu's Malta is a 24Kf -- a MIPS32
# part -- so its general exception vector with BEV=0 is 0x80000180, and it comes
# out of `-kernel` with BEV set, which is the one state probe2 refuses to install
# into. Overriding both is what lets the handler, the `break` control, the 256
# stubs and the restore be exercised at all before they cost a power cycle.
if ! make -C "$HERE" BUILD="$B" P="$P" payload \
        UART_THR=0xB80003F8 UART_LSR=0xB80003FD \
        VEC_GENERAL=0x80000180 CLEAR_BEV=1 RET_ERET=1 >"$B/build.log" 2>&1; then
    sed 's/^/    /' "$B/build.log"
    echo "  FAIL   the qemu build did not complete"
    exit 1
fi
ELF="$B/$P/$P.elf"

echo "--- qemu-system-mips -M malta, ${SECS}s ---"
: >"$OUT.txt"
timeout "$SECS" qemu-system-mips \
    -M malta -m 32 -nographic -monitor none \
    -kernel "$ELF" -serial "file:$OUT.txt" </dev/null >"$OUT.qemu.log" 2>&1
rc=$?
echo "  qemu exit $rc (124 = the timeout expired, which is expected: nothing here halts)"
echo "  serial   $OUT.txt   $(wc -c <"$OUT.txt") bytes"
echo
sed 's/^/  | /' "$OUT.txt"
echo

if grep -q 'rlxprobe: end' "$OUT.txt"; then
    echo "  ok     the payload reached its end marker under qemu"
    echo "         -- control flow only. qemu has interlocks and this core does not."
    exit 0
fi
echo "  FAIL   no 'rlxprobe: end' in the serial output"
echo "         Either the payload did not run, or it stopped early. The bytes above"
echo "         are what reached the port; a truncated report is a different"
echo "         observation from an absent one, which is why there is an end marker."
exit 1
