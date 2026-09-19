#!/bin/bash
# a7-iperf-build.sh -- stage the hand-written config/Makefile and build.
# Runs from its own scratch directory: the rsdk wrappers write offset.tmp into
# cwd, and on 2026-08-28 one landed in the repository root.
SP=/mnt/c/Users/Key20/AppData/Local/Temp/claude/C--Users-Key20-Desktop-router-rebuild/8c694d3a-f929-49fa-b994-b400fb59e14d/scratchpad
W=/home/key/fwre-work/iperf3-port
TC=/home/key/fwre-work/rebuild/r2ab/tc/rsdk-1.3.6-4181-EB-2.6.30-0.9.30
SRC=$W/src313/src

set -u

# ---- 0. long long / double printf, MEASURED by running it ---------------
echo "== probe: does this libc's printf do %llu and %f?  (run under qemu) =="
mkdir -p $W/probe && cd $W/probe || exit 1
{
  echo '#include <stdio.h>'
  echo '#include <stdint.h>'
  echo 'int main(void){'
  echo '  uint64_t b = 1234567890123ULL;'
  echo '  printf("A=%llu B=%.3f C=%lld\n", (unsigned long long)b, 3.25, (long long)-42);'
  echo '  return 0; }'
} > ll.c
$TC/bin/mips-linux-gcc -std=gnu99 -O2 -static ll.c -o ll.elf 2>&1 | head -5
if [ -f ll.elf ]; then
  echo -n "  qemu says: "
  qemu-mips-static ./ll.elf
  echo "  expected : A=1234567890123 B=3.250 C=-42"
fi

# ---- 1. stage the generated headers -------------------------------------
echo
echo "== stage iperf_config.h + version.h into $SRC =="
tr -d '\r' < $SP/a7-iperf-config.h > $SRC/iperf_config.h || exit 1
sed 's/@PACKAGE_VERSION@/3.1.3/' $SRC/version.h.in > $SRC/version.h || exit 1
grep -n IPERF_VERSION $SRC/version.h
ls -la $SRC/iperf_config.h $SRC/version.h

# ---- 2. build, twice: with the flag and without (the control) -----------
for VARIANT in flagged flagless; do
  BD=$W/build-$VARIANT
  rm -rf $BD; mkdir -p $BD; cd $BD || exit 1
  tr -d '\r' < $SP/a7-iperf-Makefile > Makefile
  if [ "$VARIANT" = flagless ]; then EX=""; else EX="-fno-if-conversion"; fi
  echo
  echo "=================== BUILD: $VARIANT  (EXTRA_CFLAGS='$EX') ==================="
  make -j4 SRC=$SRC TC=$TC EXTRA_CFLAGS="$EX" > build.log 2>&1
  rc=$?
  echo "make rc=$rc"
  echo "--- warnings/errors (first 40) ---"
  grep -E 'error|warning|Error' build.log | head -40
  echo "--- warning count: $(grep -c warning: build.log)   error count: $(grep -c 'error:' build.log) ---"
  if [ $rc -ne 0 ]; then
    echo "--- tail of build.log ---"; tail -25 build.log
  else
    ls -la iperf3 iperf3.elf
  fi
done
