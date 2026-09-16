#!/bin/sh
# This unit's OWN busybox ash, runnable at a desk with no board and no power.
#
# WHY THIS EXISTS
# ---------------
# tools/mfginject.py runs config/mfgtest.sh under $MFG_SHELL, defaulting to
# /bin/dash.  dash on an x86-64 host is a stand-in for busybox ash on a 32-bit
# MIPS target, and 量 2026-09-17 (seating 25) that stand-in is not faithful in
# at least one way that matters:
#
#     expression            host dash / bash      this unit's ash
#     $((0xb1818b92))       2978057106            2147483647   <- SATURATES
#     $((2147483647+1))     2147483648            -2147483648  <- WRAPS
#
# Parsing saturates and arithmetic wraps, in one shell.  A fix for MT-ID
# written with `printf '%08X' $((0x$want))` is green under dash and red on the
# die -- the 2 x 2 was run rather than argued, and it is why mfgtest.sh folds
# hex as a string.  SPEC.md FW-88.
#
#     MFG_SHELL=tools/mipsash.sh /usr/bin/python3 tools/mfginject.py
#
# 量 2026-09-17: all 25 injections and all six controls pass under this shell,
# with NO change to mfginject.py -- MFG_SHELL was already the right seam.
#
# 🔴 BENCH-ONLY, AND THAT IS NOT A PREFERENCE.  $UNIT is this device's own
# userspace, carved out of its flash dump, and CLAUDE.md's "Never" table
# forbids committing it: a flash dump identifies one physical device.  So this
# script is committed and the thing it runs is not, which is the same shape as
# tools/test-hazlint.sh's K4 population.  CI therefore still runs the fixtures
# under dash; whether to declare a bench-only skip row for a second pass is
# P1-5's decision, not this file's.
#
# ⚠️ WHAT IT IS NOT.  Running the shell is not running the KERNEL: every
# /proc file mfgtest reads is a fixture here, so this catches shell semantics
# and nothing about the driver.  The two defects it could not have caught are
# exactly the two the die found -- SPEC.md FW-87 (a read_proc file re-renders
# under a byte-at-a-time reader) and the /proc side of FW-88.

set -e

UNIT=${RLXFW_UNIT_ROOT:-/home/key/fwre-work/extracted/unit-2018/squashfs-root}
QEMU=${RLXFW_QEMU:-qemu-mips-static}

# Refuse rather than fall back.  A wrapper that silently ran the HOST's shell
# would make every result it produced a claim about the wrong machine, and the
# whole point of this file is that those two machines disagree.
if [ ! -x "$UNIT/bin/busybox" ]; then
	echo "mipsash: $UNIT/bin/busybox is not there or not executable." >&2
	echo "  This is the unit's own userspace and it is NOT in this" >&2
	echo "  repository -- see config/rlxfw-initramfs.tsv's \$UNIT." >&2
	echo "  Set RLXFW_UNIT_ROOT if it lives elsewhere." >&2
	exit 2
fi
if ! command -v "$QEMU" > /dev/null 2>&1; then
	echo "mipsash: $QEMU is not on PATH (apt install qemu-user-static)." >&2
	exit 2
fi

exec "$QEMU" -L "$UNIT" "$UNIT/bin/busybox" ash "$@"
