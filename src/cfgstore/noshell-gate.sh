#!/usr/bin/env bash
# noshell-gate.sh -- does this ELF contain a way to reach a shell?
#
# Certifies ONE rlxfw binary (a static, big-endian MIPS ELF built by
# src/cfgstore/Makefile).  It is not a census of the image and it is not for
# vendor binaries; see WHAT IT REFUSES TO ANSWER below.
#
# ---------------------------------------------------------------------------
# WHY IT DOES NOT SCAN FOR THE NAME, AND THE MEASUREMENT THAT SETTLED IT
# ---------------------------------------------------------------------------
#
# 量 2026-09-30, on this project's own `cfgstore` (static uClibc 0.9.30,
# 76,944 bytes stripped): the token `system` appears in the shipped bytes FOUR
# times, and all four are uClibc prose --
#
#     "Interrupted system call"
#     "Too many open files in system"
#     "Read-only file system"
#     "Interrupted system call should be restarted"
#
# -- while the symbol table of the same link holds ZERO entries named `system`.
# The same shape was measured independently on a static busybox 1.13.4 for this
# target (7 string hits, all prose, symbol table clean).
#
# So a scan for the NAME reports dirty on a clean binary, and it is the scan
# that is wrong.  A string search cannot tell a reference from a mention, and
# this gate therefore never uses one for a function name.  It uses a name scan
# only for a shell INVOCATION PATH -- "/bin/sh", "/bin/ash" -- where the bytes
# are the thing being objected to rather than a word inside a sentence.
#
# ---------------------------------------------------------------------------
# THE TWO SOURCES, AND THE PRECONDITION THAT LETS ONE CARRY TO THE OTHER FILE
# ---------------------------------------------------------------------------
#
# ①  the symbol table of the UNSTRIPPED link: any symtab entry named
#     system popen pclose execl execlp execvp execv posix_spawn -- defined or
#     undefined -- is a violation.  `execve`, `fork` and `vfork` are NOT on the
#     list: SPEC-R7 § 2 permits fork/vfork + execve with a fixed argv, and a
#     gate that forbade them would forbid the sanctioned mechanism.
#
# ②  a byte scan of the SHIPPED (stripped) bytes for a shell invocation path.
#
# ① reads a file that is not shipped, so it only says something about the
# shipped bytes if the two files' code is the same code.  The precondition is
# therefore explicit and checkable: `.text` must have the same file offset, the
# same size and the same sha256 in both files.  If it does not, the gate
# REFUSES rather than assuming -- carrying a symbol reading across a link that
# changed would be the same mistake in a different place.
#
# ---------------------------------------------------------------------------
# WHAT IT REFUSES TO ANSWER
# ---------------------------------------------------------------------------
#
# A file with no section headers (`e_shnum` = 0) -- the shape the vendor's
# binaries have, which is why a `.dynsym` walk through section headers throws on
# them and a PT_DYNAMIC walk is required.  This gate does not do a PT_DYNAMIC
# walk and does not pretend to: it refuses, by name, with control C3 proving the
# refusal fires.  rlxfw's own binaries are the static shape and are what this
# certifies.
#
# It also does not establish that the program cannot reach a shell some other
# way: a path assembled at run time, an interpreter already on the filesystem
# reached through an `execve` this gate permits, or a kernel-side helper. It is
# a guard against an accident and against a regression, not against an
# adversary with the source.
#
# ---------------------------------------------------------------------------
# CONTROLS.  A tool reporting 0 is making a claim.
# ---------------------------------------------------------------------------
#
#   C1  source ② finds "/bin/sh" in a file that contains it.
#   C2  source ① finds `system` in an ELF that calls it   (--positive <elf>;
#       WITHOUT IT THE GATE REFUSES TO CERTIFY -- a guard with no positive
#       control is not a guard).
#   C3  the e_shnum precondition refuses a copy whose e_shnum is zeroed.
#   C4  the .text-equality precondition refuses a pair whose .text differs.
#   C5  the verdict is still CLEAN on a file that MENTIONS `system` -- which is
#       the subject itself, and is the case a name scan gets wrong.
#
# Usage
#     noshell-gate.sh --elf <unstripped> --bin <stripped> --positive <elf>
#                     [--readelf R] [--work DIR]
# Exit
#     0  certified      1  a violation      2  refused (a precondition or a
#                                              control did not hold)

set -o nounset

ELF=""; BIN=""; POS=""; READELF="readelf"; WORK=""
while [ $# -gt 0 ]; do
    case "$1" in
        --elf)      ELF="$2"; shift 2 ;;
        --bin)      BIN="$2"; shift 2 ;;
        --positive) POS="$2"; shift 2 ;;
        --readelf)  READELF="$2"; shift 2 ;;
        --work)     WORK="$2"; shift 2 ;;
        *) echo "noshell-gate.sh: unknown option $1" >&2; exit 2 ;;
    esac
done

die ()  { echo "REFUSED: $*" >&2; exit 2; }
bad ()  { echo "VIOLATION: $*" >&2; exit 1; }

[ -n "$ELF" ] && [ -f "$ELF" ] || die "--elf <unstripped ELF> is required"
[ -n "$BIN" ] && [ -f "$BIN" ] || die "--bin <stripped binary> is required"
[ -n "$POS" ] || die "--positive <an ELF that calls system()> is required; a
  guard with no positive control certifies nothing"
[ -f "$POS" ] || die "--positive: no such file: $POS"
command -v "$READELF" >/dev/null 2>&1 || die "no readelf at '$READELF'"
[ -n "$WORK" ] || WORK="$(dirname "$BIN")"
mkdir -p "$WORK" || die "cannot write to $WORK"

FORBIDDEN="system popen pclose execl execlp execvp execv posix_spawn"
SHELLPATHS="/bin/sh /bin/bash /bin/ash /bin/dash"

# --- helpers ---------------------------------------------------------------

shnum () { "$READELF" -h "$1" | awk -F: '/Number of section headers/{gsub(/ /,"",$2); print $2}'; }

# prints "<offset-hex> <size-hex>" for .text, or nothing
text_span () {
    "$READELF" -S -W "$1" 2>/dev/null | awk \
      '{for (i = 1; i <= NF; i++) if ($i == ".text") { print $(i+3), $(i+4); exit }}'
}

text_sha () {
    local f="$1" span off sz
    span="$(text_span "$f")" || return 1
    [ -n "$span" ] || return 1
    off="$(echo "$span" | cut -d' ' -f1)"
    sz="$(echo "$span" | cut -d' ' -f2)"
    dd if="$f" bs=1 skip="$((16#$off))" count="$((16#$sz))" 2>/dev/null | sha256sum | cut -d' ' -f1
}

# source ①: how many symtab entries carry this exact name
sym_count () { "$READELF" -sW "$1" 2>/dev/null | awk -v s="$2" '$8 == s' | wc -l; }

# source ②: how many times these bytes appear
str_count () { grep -a -o -F -- "$2" "$1" 2>/dev/null | wc -l; }

# --- the controls, before the subject ---------------------------------------

echo "--- controls ---"

printf 'x /bin/sh y\n' > "$WORK/ng-c1"
c1="$(str_count "$WORK/ng-c1" /bin/sh)"
[ "$c1" -ge 1 ] || die "C1: source 2 cannot see /bin/sh in a file that has it"
c1n="$(str_count "$BIN" /no/such/interpreter)"
[ "$c1n" = "0" ] || die "C1: source 2 sees a string that is not there"
echo "  C1 source 2 sees /bin/sh ($c1) and not an absent string ($c1n)"

c2="$(sym_count "$POS" system)"
[ "$c2" -ge 1 ] || die "C2: source 1 cannot see \`system' in $POS, an ELF that
  calls it.  Either the control was built wrong or the reader is broken; either
  way nothing below can be trusted"
echo "  C2 source 1 sees \`system' in the positive control ($c2 symtab entries)"

cp -f "$ELF" "$WORK/ng-c3.elf" || die "C3: cannot copy $ELF"
# e_shoff is 4 bytes at offset 32 and e_shnum is 2 bytes at offset 48 of an
# ELF32 header.  BOTH must go: ELF's extended numbering says that when e_shnum
# is 0 and e_shoff is not, the real count lives in section header 0's sh_size,
# and readelf implements that -- so zeroing e_shnum alone leaves it printing the
# extended count and the control silently does not fire.  Found by running it
# (2026-09-30): the first version of this control refused with "zeroing e_shnum
# did not take", which is the control working on itself.
printf '\000\000\000\000' | dd of="$WORK/ng-c3.elf" bs=1 seek=32 count=4 \
    conv=notrunc 2>/dev/null || die "C3: cannot patch e_shoff"
printf '\000\000' | dd of="$WORK/ng-c3.elf" bs=1 seek=48 count=2 conv=notrunc \
    2>/dev/null || die "C3: cannot patch e_shnum"
c3="$(shnum "$WORK/ng-c3.elf" 2>/dev/null)"
[ "$c3" = "0" ] || die "C3: the no-section-header shape was not produced
  (e_shnum reads '$c3'); the precondition below cannot be trusted"
# and the symbol reader must come back EMPTY on that shape rather than clean
c3s="$(sym_count "$WORK/ng-c3.elf" main)"
[ "$c3s" = "0" ] || die "C3: a file with no section headers still yielded
  symbols; source 1's blind spot is not where this gate thinks it is"
echo "  C3 a copy with no section headers reads e_shnum 0 and yields 0 symbols,"
echo "     which is why that shape is refused instead of reported clean"

cp -f "$BIN" "$WORK/ng-c4.bin" || die "C4: cannot copy $BIN"
c4span="$(text_span "$WORK/ng-c4.bin")"
[ -n "$c4span" ] || die "C4: no .text in $BIN"
c4off="$(echo "$c4span" | cut -d' ' -f1)"
# flip one byte inside .text; the equality check must then refuse
old="$(dd if="$WORK/ng-c4.bin" bs=1 skip="$((16#$c4off))" count=1 2>/dev/null | od -An -tu1 | tr -d ' ')"
printf "$(printf '\\%03o' $(( (old + 1) % 256 )))" | \
    dd of="$WORK/ng-c4.bin" bs=1 seek="$((16#$c4off))" count=1 conv=notrunc 2>/dev/null
if [ "$(text_sha "$ELF")" = "$(text_sha "$WORK/ng-c4.bin")" ]; then
    die "C4: the .text comparison calls two different .text sections equal"
fi
echo "  C4 the .text comparison refuses a pair whose .text differs by one byte"

# --- preconditions on the subject ------------------------------------------

echo "--- preconditions ---"
n="$(shnum "$ELF")"
[ -n "$n" ] || die "cannot read e_shnum from $ELF"
if [ "$n" = "0" ]; then
    die "$ELF has no section headers (e_shnum = 0).  That is the vendor's shape;
  reading it needs a PT_DYNAMIC walk, which this gate does not do.  It refuses
  rather than reporting a clean count it did not earn"
fi
echo "  e_shnum $n (section headers present, so source 1 can read a symtab)"

a="$(text_sha "$ELF")"; b="$(text_sha "$BIN")"
[ -n "$a" ] && [ -n "$b" ] || die "no .text in one of the two files"
[ "$a" = "$b" ] || die "the unstripped ELF and the stripped binary do not share
  a .text (${a:0:16} vs ${b:0:16}); a symbol reading from one cannot be carried
  onto the other"
echo "  .text identical in both files, sha256 ${a:0:16}...  (source 1's reading"
echo "    of the unstripped ELF therefore applies to the shipped bytes)"

# --- source 1 --------------------------------------------------------------

echo "--- source 1: the symbol table of the unstripped link ---"
v=0
for s in $FORBIDDEN; do
    c="$(sym_count "$ELF" "$s")"
    printf '  %-12s symtab entries %s\n' "$s" "$c"
    [ "$c" = "0" ] || v=1
done
for s in execve fork vfork; do
    printf '  %-12s symtab entries %s   (permitted by SPEC-R7 § 2)\n' \
        "$s" "$(sym_count "$ELF" "$s")"
done
[ "$v" = "0" ] || bad "a forbidden symbol is in the link"

# --- source 2 --------------------------------------------------------------

echo "--- source 2: a byte scan of the shipped bytes, PATHS ONLY ---"
for p in $SHELLPATHS; do
    c="$(str_count "$BIN" "$p")"
    printf '  %-12s occurrences %s\n' "$p" "$c"
    [ "$c" = "0" ] || v=1
done
[ "$v" = "0" ] || bad "a shell path is in the shipped bytes"

# --- C5: the case a name scan gets wrong -----------------------------------

echo "--- C5: the mention-versus-reference case, on this very file ---"
for s in $FORBIDDEN; do
    c="$(str_count "$BIN" "$s")"
    [ "$c" = "0" ] && continue
    printf '  the token `%s'"'"' appears %s time(s) in the shipped bytes; source 1\n' "$s" "$c"
    printf '    says the link holds %s symtab entries for it, so these are\n' \
        "$(sym_count "$ELF" "$s")"
    printf '    MENTIONS.  A gate that scanned for the name would refuse here:\n'
    "$READELF" --version >/dev/null 2>&1
    strings -a "$BIN" 2>/dev/null | grep -F -- "$s" | head -4 | sed 's/^/      /'
done
echo "  verdict below is CLEAN in spite of those mentions, which is the point"

echo "NOSHELL-GATE: CLEAN  $(basename "$BIN")  2 sources, 5 controls held"
exit 0
