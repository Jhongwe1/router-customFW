#!/usr/bin/env bash
# Can this toolchain build, or can it only print a version?
#
# `R2a/b/d-3` asked for a container and its DoD was `rsdk-linux-gcc --version`
# prints `4.4.5`. 量 2026-08-27: both rsdk generations print their version on
# this distro with no container at all, so the DoD fired and the step was still
# not done -- because `--version` on the gcc driver is a statically linked
# binary asking itself a question. It never touches `as`, `ld`, `ar`, or a
# single byte of MIPS. 量 2026-08-28: with that same DoD satisfied,
# rsdk-1.5.5's ENTIRE binutils -- seventeen host programs, `as` `ld` `ar`
# `ranlib` `nm` `objcopy` `objdump` `readelf` `size` `strings` `strip`
# `addr2line` `c++filt` `gprof` and the `xld` variants -- would not start, for
# one missing i386 `libz.so.1`.
#
# So the ladder. Each rung is reported separately and a rung that is not
# reached is printed as not reached, because "it compiles" and "it links" and
# "the result runs" are three different claims and this repository has been
# bitten by treating the first as the third.
#
#   L1  every binutils program this project needs starts, and its exit status
#       is read DIRECTLY -- never `prog | head`, which reports head's status.
#       That mistake produced a clean-looking `rc=0` beside an
#       `error while loading shared libraries` on 2026-08-28.
#   L2  .c -> .s -> .o -> statically linked ELF, each step separately, and the
#       result is checked to be 32-bit MSB MIPS EXEC rather than assumed to be.
#   L3  the instructions this kernel is actually made of: `lwl`/`lwr`/`swl`/`swr`
#       (arch/rlx/lib/memcpy.S's ULS path), `mtc3` (the four CP3 writes in
#       _imem_dmem_init), `cache` (arch/rlx/mm/cache-rlx.c), under
#       `.set noreorder`. Assembled, then the ENCODING is read back as a
#       sha256 over the emitted `.text` -- an assembler that accepts a mnemonic
#       and emits something else passes a test that only checks exit status.
#       量 2026-08-28: all three rsdk releases emit the same 48 bytes for this
#       file at their own configured -march, so the constant is a cross-vendor
#       agreement and not one toolchain's habit.
#       L3 also reports, separately, whether `gcc -c feat.S` works -- the path a
#       kernel build actually takes. 量 2026-08-28 it does NOT on rsdk-1.3.6:
#       the driver hands `as` its default `lx4180` rather than the wrapper's
#       configured 4181, and `cache` is then rejected with
#       `opcode not supported on this processor: lx4180`. `-Wa,-march=` fixes
#       it and says so: `Warning: A different -march was already specified`.
#   L4  the linked binary is executed under qemu-mips and its output compared
#       against a value computed at build time. This is the rung that separates
#       "the linker produced a file" from "the toolchain produced a program".
#
# TWO CONTROLS, and neither is decoration:
#
#   POS  the ladder is monotone: a rung may read `ok` only if every rung below
#        it does. COMPUTED over the rows, not asserted -- until the 2026-08-28
#        review this control was a printf of a sentence, which is to say it was
#        not a control at all, and a mutant that let L3 and L4 read ok under a
#        FAILed L2 kept the suite green.
#   NEG  the binutils `-march` spellings -- `lx4180`, `rlx4181`, `rlx5281` --
#        must be REJECTED by the compiler driver. They are binutils names; the
#        gcc side takes bare numbers. If a driver accepts them, `-march` is
#        being ignored and every per-arch number this project has is one column
#        repeated. 量 2026-08-27, this exact confusion produced a table of
#        four false zeros that survived into a commit.
#
# WHERE IT FAILS
#   - It says the toolchain can build. It says NOTHING about whether the output
#     is correct for this silicon. `-march=5281` builds cleanly and emits code
#     with no load-delay padding; on an RLX4181 that is wrong and this tool
#     will still print L1..L4 all green. `hazlint` is the instrument for that
#     question and `notes/vendor-toolchains.md` carries the numbers.
#   - L4 proves semantics only for what the test program exercises.
#   - It runs the vendor's binaries. That is not a read-only act -- see
#     `tools/vendor-tripwire.sh`, which exists because of it. Run this under
#     the tripwire.
#
# Usage
#     tc-smoke.sh [--tc DIR]... [--qemu PATH] [--quiet]
#
#     --tc     a toolchain root (the directory holding bin/). Repeatable.
#              Default: every rsdk under $FWRE_WORK/rebuild/src-vendor.
#     --qemu   the MIPS user-mode emulator. Default: qemu-mips-static on PATH.
#              Without it L4 is reported as not reached, never as passed.
#     --quiet  table only.
#
# Exit
#     0  every toolchain found reached L4, and both controls held
#     1  a rung FAILED
#     2  a control failed -- nothing certified
#     3  no toolchain found, or a named --tc is not one
#     4  a rung was NOT REACHED (no MIPS emulator). Nothing failed and
#        nothing above L3 is certified -- these are different answers and
#        they had the same exit code until the 2026-08-28 review said so
set -o nounset

TCS=()
QEMU="$(command -v qemu-mips-static 2>/dev/null || true)"
QUIET=0

while [ $# -gt 0 ]; do
    case "$1" in
        --tc)    TCS+=("$2"); shift 2 ;;
        --qemu)  QEMU="$2"; shift 2 ;;
        --quiet) QUIET=1; shift ;;
        *) echo "tc-smoke.sh: unknown option $1" >&2; exit 3 ;;
    esac
done

say () { [ "$QUIET" -eq 1 ] || printf '%s\n' "$*"; }

if [ ${#TCS[@]} -eq 0 ]; then
    ROOT="${FWRE_WORK:-/home/key/fwre-work}/rebuild/src-vendor"
    # Each drop ships its own copy of the same rsdk releases. 量 2026-08-28:
    # three drops x three releases = nine directories and three distinct
    # toolchains. Testing the same release once per drop would treble the run
    # and print one answer three times, so the first copy of each release name
    # is taken and the count of copies is reported.
    seen=""
    for d in "$ROOT"/*/toolchain/*/ "$ROOT"/*/*/toolchain/*/; do
        [ -x "$d/bin/mips-linux-gcc" ] || continue
        n="$(basename "${d%/}")"
        case " $seen " in *" $n "*) continue ;; esac
        seen="$seen $n"
        TCS+=("${d%/}")
    done
fi

if [ ${#TCS[@]} -eq 0 ]; then
    echo "tc-smoke.sh: SKIPPED  no rsdk toolchain under \${FWRE_WORK:-/home/key/fwre-work}/rebuild/src-vendor" >&2
    exit 3
fi

# A directory named with --tc that holds no compiler driver is not a toolchain
# that failed L1 -- it is a question that cannot be asked. Refuse, the way
# isa-probe refuses with no assembler, rather than printing a row of FAIL that
# reads as a measurement of something.
for tc in "${TCS[@]}"; do
    if [ ! -x "$tc/bin/mips-linux-gcc" ]; then
        echo "tc-smoke.sh: SKIPPED  not a toolchain (no bin/mips-linux-gcc): $tc" >&2
        exit 3
    fi
done

W="$(mktemp -d)"
trap 'rm -rf "$W"' EXIT

cat > "$W/hello.c" <<'CEOF'
/* Computes its answer rather than printing a constant, so that a toolchain
   which mangles arithmetic fails L4 instead of passing it. */
static unsigned sum(unsigned n){ unsigned i,s=0; for(i=1;i<=n;i++) s+=i*i; return s; }
extern int printf(const char *, ...);
int main(void){ printf("rlxfw-smoke %u\n", sum(100)); return 0; }
CEOF
EXPECT="rlxfw-smoke 338350"

# The instructions arch/rlx is built out of. `.set noreorder` throughout: the
# assembler must not be the one deciding what goes in a delay slot.
cat > "$W/feat.S" <<'SEOF'
	.set	noreorder
	.text
	.globl	feat
feat:
	lwl	$8, 0($5)
	lwr	$8, 3($5)
	swl	$8, 0($4)
	swr	$8, 3($4)
	mtc3	$0, $0
	mtc3	$0, $1
	cache	0x11, 0($4)
	jr	$31
	nop
SEOF
# What those nine words must encode to, as a sha256 over the emitted `.text`.
# 量 2026-08-28: 48 bytes (nine instructions plus the section pad), identical
# from all three rsdk releases at their own configured -march. The words are
#   88a80000 98a80003 a8880000 b8880003 4c800000 4c800800 bc910000 03e00008 0
# i.e. lwl lwr swl swr mtc3 mtc3 cache jr nop, big-endian.
FEAT_SHA="298d5f2a5b417a961293b3f609f7c757d8927e69140a0adad350c5e2d36b5e5f"

BAD_MARCH="lx4180 rlx4181 rlx5281"
# `rsdk-linux-gcc` is on the list because that, not `mips-linux-gcc`, is
# what arch/rlx/Makefile calls: `CROSS_COMPILE := rsdk-linux-`.
NEED="as ld ar ranlib nm objcopy objdump readelf size strip"

fail=0; ctlfail=0; notreached=0
say "tc-smoke -- can it build, not can it print a version"
say ""
printf '%-34s %-6s %-6s %-6s %-6s %s\n' TOOLCHAIN L1 L2 L3 L4 NOTE
POSBAD=0

for tc in "${TCS[@]}"; do
    name="$(basename "$tc")"
    G="$tc/bin/mips-linux-gcc"
    l1=- ; l2=- ; l3=- ; l4=- ; note=""

    # ---- L1: every program starts. Status read DIRECTLY, never through a
    # pipe -- `prog | head` reports head's status, which on 2026-08-28 printed
    # a clean rc=0 beside an `error while loading shared libraries`.
    missing=""
    for p in $NEED; do
        b="$tc/bin/mips-linux-$p"
        if [ ! -x "$b" ]; then
            missing="$missing $p(absent)"
            continue
        fi
        if ! "$b" --version >/dev/null 2>"$W/e1"; then
            why="$(head -1 "$W/e1" 2>/dev/null | sed 's|.*/||; s/^[^:]*: *//' | cut -c1-46)"
            missing="$missing $p(${why:-nonzero exit})"
        fi
    done
    if [ -z "$missing" ]; then l1=ok; else l1=FAIL; note="L1:$missing"; fail=1; fi

    # ---- L2: compile, assemble, link, and READ the result
    if [ "$l1" = ok ]; then
        rm -f "$W/h.s" "$W/h.o" "$W/h.elf"
        "$G" -O2 -S "$W/hello.c" -o "$W/h.s" >"$W/e" 2>&1 && [ -s "$W/h.s" ] || { l2=FAIL; note="${note} L2:-S $(head -1 "$W/e")"; }
        if [ "$l2" != FAIL ]; then
            "$tc/bin/mips-linux-as" "$W/h.s" -o "$W/h.o" >"$W/e" 2>&1 && [ -s "$W/h.o" ] || { l2=FAIL; note="${note} L2:as $(head -1 "$W/e")"; }
        fi
        if [ "$l2" != FAIL ]; then
            "$G" -O2 -static "$W/hello.c" -o "$W/h.elf" >"$W/e" 2>&1 && [ -s "$W/h.elf" ] || { l2=FAIL; note="${note} L2:link $(head -1 "$W/e")"; }
        fi
        if [ "$l2" != FAIL ]; then
            hdr="$("$tc/bin/mips-linux-readelf" -h "$W/h.elf" 2>/dev/null)"
            case "$hdr" in
                *"big endian"*) ;;
                *) l2=FAIL; note="${note} L2:not-big-endian" ;;
            esac
            case "$hdr" in
                *MIPS*) ;;
                *) l2=FAIL; note="${note} L2:not-MIPS" ;;
            esac
            case "$hdr" in
                *EXEC*) ;;
                *) l2=FAIL; note="${note} L2:not-EXEC" ;;
            esac
        fi
        [ "$l2" = FAIL ] && fail=1 || l2=ok
    fi

    # ---- L3: the kernel's own instructions, and their encoding read back
    if [ "$l2" = ok ]; then
        # Which core is this toolchain CONFIGURED for?  Asked, not assumed --
        # the directory name is a label and a label is not a measurement, and
        # `mips-linux-gcc` is the wrong thing to ask: on rsdk-1.3.6 it is the
        # raw gcc driver, which accepts all six Lexra multilibs, so the first
        # one that works says nothing. `rsdk-linux-gcc` is the RSDK wrapper,
        # it accepts exactly one -march, and it is what a kernel build calls
        # (`CROSS_COMPILE := rsdk-linux-`, arch/rlx/Makefile). 量 2026-08-28:
        # rsdk-1.3.6-5281 refuses -march=4181 through the wrapper and accepts
        # it through the raw driver, so these two questions have different
        # answers on the same toolchain.
        arch=""; via=""
        WG="$tc/bin/rsdk-linux-gcc"
        if [ -x "$WG" ]; then probe="$WG"; via="cfg"; else probe="$G"; via="raw"; fi
        for cand in 4180 4181 5181 5280 5281 4281; do
            rm -f "$W/p.o"
            if "$probe" -march=$cand -c "$W/hello.c" -o "$W/p.o" >/dev/null 2>&1 && [ -s "$W/p.o" ]; then
                arch=$cand
                [ "$via" = cfg ] && break
            fi
        done
        # Only mark the answer uncertain when there IS one. Appending to an
        # empty string produced "?" , which is non-empty, so the "no -march
        # accepted" branch below became unreachable on the raw path.
        [ "$via" = raw ] && [ -n "$arch" ] && arch="${arch}?"
        if [ -z "$arch" ]; then
            l3=FAIL; note="${note} L3:no -march accepted"; fail=1
        else
            rm -f "$W/f.o" "$W/f.bin"
            if "$tc/bin/mips-linux-as" -march="${arch%\?}" -EB "$W/feat.S" -o "$W/f.o" >"$W/e" 2>&1 && [ -s "$W/f.o" ]; then
                "$tc/bin/mips-linux-objcopy" -O binary --only-section=.text "$W/f.o" "$W/f.bin" 2>/dev/null
                got="$(sha256sum "$W/f.bin" 2>/dev/null | cut -d' ' -f1)"
                if [ "$got" = "$FEAT_SHA" ]; then l3=ok; note="${note} ${via}-march=$arch"
                else l3=FAIL; note="${note} L3:text-sha[$got]"; fail=1; fi
            else
                l3=FAIL; note="${note} L3:as $(grep -m1 Error "$W/e" | cut -c1-60)"; fail=1
            fi
            # the build path, reported but not fatal -- it is a property of the
            # vendor driver, not of whether the ISA is available
            rm -f "$W/g.o"
            if ! ( "$G" -c "$W/feat.S" -o "$W/g.o" >/dev/null 2>&1 && [ -s "$W/g.o" ] ); then
                note="${note} [gcc -c *.S refuses: driver passes its own default -march to as]"
            fi
        fi
    fi

    # ---- L4: run it
    if [ "$l3" = ok ]; then
        if [ -z "$QEMU" ] || [ ! -x "$QEMU" ]; then
            l4=noqemu; notreached=1
            note="${note} L4:no MIPS emulator on PATH -- not reached, not passed"
        else
            out="$("$QEMU" "$W/h.elf" 2>&1)"
            if [ "$out" = "$EXPECT" ]; then l4=ok
            else l4=FAIL; note="${note} L4:got[$out]"; fail=1; fi
        fi
    fi

    # POS, computed: the ladder is monotone. A rung may only read `ok` if
    # every rung below it does. Anything else means a rung was skipped rather
    # than passed, which is the one failure a four-rung report can hide.
    prev=ok
    for c in "$l1" "$l2" "$l3" "$l4"; do
        if [ "$c" = ok ] && [ "$prev" != ok ]; then POSBAD=$((POSBAD+1)); fi
        prev="$c"
    done
    printf '%-34s %-6s %-6s %-6s %-6s %s\n' "$name" "$l1" "$l2" "$l3" "$l4" "$note"
done

# ---- NEG control: the binutils -march spellings must be refused by the driver
say ""
say "controls"
neg_bad=0; neg_tested=0
for tc in "${TCS[@]}"; do
    G="$tc/bin/mips-linux-gcc"
    [ -x "$G" ] || continue
    for m in $BAD_MARCH; do
        rm -f "$W/n.o"
        neg_tested=$((neg_tested+1))
        if "$G" -march=$m -c "$W/hello.c" -o "$W/n.o" >/dev/null 2>&1 && [ -s "$W/n.o" ]; then
            neg_bad=$((neg_bad+1))
            say "  FAIL  NEG  $(basename "$tc") accepted -march=$m -- a binutils spelling. -march is being ignored."
        fi
    done
done
if [ "$neg_bad" -eq 0 ]; then
    say "  ok    NEG  $neg_tested binutils -march spellings, all refused by the compiler driver"
else
    ctlfail=1
fi

# ---- POS control: the ladder is monotone. A later rung green under an earlier
# rung that is not green would mean a rung was skipped rather than passed.
if [ "$POSBAD" -eq 0 ]; then
    say "  ok    POS  the ladder is monotone in every row: no rung reads ok above a rung that does not"
else
    say "  FAIL  POS  $POSBAD rung(s) read ok above a rung that did not -- a rung was skipped, not passed"
    ctlfail=1
fi

say ""
if [ "$ctlfail" -ne 0 ]; then
    say "RESULT: control failed -- nothing certified"
    exit 2
fi
if [ "$fail" -ne 0 ]; then
    say "RESULT: at least one rung was not reached"
    exit 1
fi
if [ "$notreached" -ne 0 ]; then
    # A rung that was not reached must not produce the verdict that says it
    # was. Exit 4 is its own code: nothing failed, and nothing is certified.
    say "RESULT: L4 was not reached on at least one toolchain -- nothing is certified above L3"
    exit 4
fi
say "RESULT: every toolchain reached L4"
exit 0
