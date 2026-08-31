#!/usr/bin/env bash
# Do R3-4's two gates actually gate?   tools/kconfig-delta.py and tools/mkinitramfs.py
#
# Both tools carry their own controls and both run them before they report on
# anything.  That is not enough on its own: a control that has never been shown
# to fire is indistinguishable from one that cannot.  So each mutation below
# breaks ONE thing in the tool and names the control that must go red.
#
#   D1  the delta parser stops caring about the `from` value      -> C5 must fail
#   D2  a missing rule stops being an error                       -> C2 and C6 must fail
#   D3  `# X is not set` and "absent" are made the same value     -> C8 must fail
#   D4  the duplicate-symbol refusal is removed                   -> C11 must fail
#   M1  a missing source file is skipped instead of refused       -> A2 must fail
#   M2  the /init requirement is dropped                          -> A3 must fail
#   M3  the `unit` tag stops being checked                        -> A5 must fail
#   D5  the .config grammar made stricter than kconfig's     -> C22 must fail
#   D6  `apply` stops applying anything                      -> C17 must fail
#   M4  the `unit` counterpart check becomes a no-op         -> A13 must fail
#   M5  the manifest digest is of the path, not the bytes    -> A11 must fail
#
# D5, D6, M4 and M5 exist because the adversarial pass of 2026-08-28 pointed
# out that all seven original mutations sat in one place per tool -- the
# comparison inside `check`, and the refusals inside `resolve` -- so `apply`,
# the .config recogniser, and everything mkinitramfs EMITS had no mutation at
# all.  Each of the four passed the full suite before it was written.
#
# and, in the other direction, four end-to-end cases on the real repository
# files, because a suite that only ever runs on synthetic input has not been
# shown to work on the artefact it exists for.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
KD="$HERE/kconfig-delta.py"
MK="$HERE/mkinitramfs.py"
PY="${PYTHON:-python3}"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0; skip=0
ck () {  # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-52s %s\n' "$1" "$2"; skip=$((skip+1)); }

echo "=== S1: both tools pass their own controls, unmutated ==="
o="$("$PY" "$KD" self-test 2>&1)"; rc=$?
ck "kconfig-delta self-test exit 0"        0 "$rc"
ck "kconfig-delta 24 controls"             1 "$(printf '%s\n' "$o" | grep -c '24 passed, 0 failed')"
o="$("$PY" "$MK" self-test 2>&1)"; rc=$?
ck "mkinitramfs self-test exit 0"          0 "$rc"
ck "mkinitramfs A2 present"                1 "$(printf '%s\n' "$o" | grep -c 'A2 ')"

echo
echo "=== D1-D4: break kconfig-delta, and name the control that must go red ==="
mutkd () { sed "$2" "$KD" > "$T/$1"; }

mutkd d1 's|if rule.frm != frm or rule.to != to:|if rule.to != to:  # MUTATED: the from value is no longer checked|'
ck "D1 mutation landed"   1 "$(grep -c 'MUTATED: the from value' "$T/d1")"
o="$("$PY" "$T/d1" self-test 2>&1)"
ck "D1 fails C5"          1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*C5 ')"

mutkd d2 's|^            r.undeclared.append((sym, frm, to))|            pass  # MUTATED: an undeclared difference is ignored|'
ck "D2 mutation landed"   1 "$(grep -c 'MUTATED: an undeclared difference' "$T/d2")"
o="$("$PY" "$T/d2" self-test 2>&1)"
ck "D2 fails C2"          1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*C2 ')"

mutkd d3 's|^ABSENT = "-"|ABSENT = "n"  # MUTATED: absent and n are the same value|'
ck "D3 mutation landed"   1 "$(grep -c 'MUTATED: absent and n' "$T/d3")"
o="$("$PY" "$T/d3" self-test 2>&1)"
ck "D3 fails C8"          1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*C8 ')"

mutkd d4 's|^        if sym in rules:|        if False:  # MUTATED: duplicate rules are allowed|'
ck "D4 mutation landed"   1 "$(grep -c 'MUTATED: duplicate rules' "$T/d4")"
o="$("$PY" "$T/d4" self-test 2>&1)"
ck "D4 fails C11"         1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*C11 ')"

echo
echo "=== M1-M3: break mkinitramfs, and name the control that must go red ==="
mutmk () { sed "$2" "$MK" > "$T/$1"; }

mutmk m1 's|^        if not os.path.exists(src):|        if False:  # MUTATED: a missing source is no longer an error|'
ck "M1 mutation landed"   1 "$(grep -c 'MUTATED: a missing source' "$T/m1")"
o="$("$PY" "$T/m1" self-test 2>&1)"
ck "M1 fails A2"          1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*A2 ')"

mutmk m2 's|^    if "/init" not in have:|    if False:  # MUTATED: /init is no longer required|'
ck "M2 mutation landed"   1 "$(grep -c 'MUTATED: /init is no longer' "$T/m2")"
o="$("$PY" "$T/m2" self-test 2>&1)"
ck "M2 fails A3"          1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*A3 ')"

mutmk m3 's|^        if e.owner == "unit" and not _inside(src, unit):|        if False:  # MUTATED: the unit tag is taken on trust|'
ck "M3 mutation landed"   1 "$(grep -c 'MUTATED: the unit tag' "$T/m3")"
o="$("$PY" "$T/m3" self-test 2>&1)"
ck "M3 fails A5"          1 "$(printf '%s\n' "$o" | grep -c '^  .*FAIL.*A5 ')"

# D5: the .config grammar.  kconfig's own reader is `strncmp(p, "is not set",
# 10)` -- unanchored -- so an anchored regex here drops a line the compiler
# honoured and a real drift walks through.  Measured on the real pair before
# the fix: `# CONFIG_KGDB is not set   (rlxfw)` passed the gate.
mutkd d5 's|is not set")$|is not set$")  # MUTATED: anchored, unlike confdata.c|'
ck "D5 mutation landed"   1 "$(grep -c 'MUTATED: anchored' "$T/d5")"
o="$("$PY" "$T/d5" self-test 2>&1)"
ck "D5 fails C22"         1 "$(printf '%s\n' "$o" | grep -c '^  FAIL  C22 ')"

# D6: `apply` is the half that writes the build input, and it had no control of
# its own until 2026-08-28.
mutkd d6 's|^    sets = {s: r for s, r in rules.items() if r.kind == "set"}|    sets = {}  # MUTATED: apply applies nothing|'
ck "D6 mutation landed"   1 "$(grep -c 'MUTATED: apply applies nothing' "$T/d6")"
o="$("$PY" "$T/d6" self-test 2>&1)"
ck "D6 fails C17"         1 "$(printf '%s\n' "$o" | grep -c '^  FAIL  C17 ')"

echo
echo "=== M4-M5: the mkinitramfs checks that had no mutation ==="
# M4: 15 of the real declaration's 31 entries were `slink`, and their tag was
# taken on trust.  Turning the check on found two wrong ones the same day.
mutmk m4 's|^            _unit_counterpart(e, unit, decl_path)|            pass  # MUTATED: the unit counterpart is not checked|'
ck "M4 mutation landed"   1 "$(grep -c 'MUTATED: the unit counterpart' "$T/m4")"
o="$("$PY" "$T/m4" self-test 2>&1)"
ck "M4 fails A13"         1 "$(printf '%s\n' "$o" | grep -c '^  FAIL  A13 ')"

# M5: the manifest is the traceability record RUNSHEET P9 and SPEC FW-24 cite.
# A digest of the path would look exactly like a digest of the bytes.
mutmk m5 's|^        for chunk in iter(lambda: f.read(1 << 20), b""):|        for chunk in [path.encode()]:  # MUTATED: hashes the path, not the bytes|'
ck "M5 mutation landed"   1 "$(grep -c 'MUTATED: hashes the path' "$T/m5")"
o="$("$PY" "$T/m5" self-test 2>&1)"
ck "M5 fails A11"         1 "$(printf '%s\n' "$o" | grep -c '^  FAIL  A11 ')"

echo
echo "=== M6-M7: the flash-write node ban, and why A26 is not redundant ==="
# The ban is the only thing standing between an edit to
# config/rlxfw-initramfs.tsv and a node root can write flash through on a
# device with no spare.  Two mutations, because a ban has two ways to be wrong:
# not running at all, and running on the wrong evidence.

# M6 -- the call site.  A guard that is never called looks exactly like one
# that never fires, which is this repository's own "a tool reporting 0 is
# making a claim".
mutmk m6 's|^    check_no_writable_flash_node(entries, decl_path)|    pass  # MUTATED: the flash-write node ban is never called|'
ck "M6 mutation landed"   1 "$(grep -c 'MUTATED: the flash-write node ban is never called' "$T/m6")"
o="$("$PY" "$T/m6" self-test 2>&1)"
ck "M6 fails A24"         1 "$(printf '%s\n' "$o" | grep -c '^  FAIL  A24 ')"

# M7 -- the ban keys on the PATH instead of the major.  This is the subtle one:
# all three of A24's declarations are still refused (two by name, the third by
# the even-minor clause), so A24 stays GREEN and only A26 goes red.  That is
# the whole reason A26 exists, and without this mutation nothing says so.
# It is also the defect A15 found one level up -- a nod's major and minor were
# passed through as text until 2026-08-28.
mutmk m7 's|^        if maj == MTD_BLOCK_MAJOR:|        if e.path.startswith("/dev/mtdblock"):  # MUTATED: the ban keys on the path|'
ck "M7 mutation landed"   1 "$(grep -c 'MUTATED: the ban keys on the path' "$T/m7")"
o="$("$PY" "$T/m7" self-test 2>&1)"
ck "M7 fails A26"         1 "$(printf '%s\n' "$o" | grep -c '^  FAIL  A26 ')"
ck "M7 leaves A24 GREEN"  1 "$(printf '%s\n' "$o" | grep -c '^  ok    A24 ')"

echo
echo "=== E1-E4: on this repository's own declaration files ==="
DELTA="$REPO/config/rlxfw-kernel.delta"
DECL="$REPO/config/rlxfw-initramfs.tsv"

# E1 needs no vendor material, so it is the one case here that runs on a clean
# clone: does the committed delta file parse, and is every mechanism in it one
# of the five the tool will accept?  A typo in this file would otherwise only
# surface on a machine that has the drop.
cat > "$T/e1.py" <<'PY'
import importlib.machinery, importlib.util, sys
ldr = importlib.machinery.SourceFileLoader("kd", sys.argv[1])
m = importlib.util.module_from_spec(importlib.util.spec_from_loader("kd", ldr))
ldr.exec_module(m)
rules, headers = m.parse_delta(sys.argv[2])
sets = sum(1 for r in rules.values() if r.kind == "set")
print("%d %d %d" % (len(rules), sets, len(rules) - sets))
PY
ck "E1 the committed delta parses: 36 rules, 15 set, 21 derived" "36 15 21" \
   "$("$PY" "$T/e1.py" "$KD" "$DELTA" 2>&1 | tail -1)"

# E1b -- the same file, per variant, and it also runs on a clean clone.  Without
# it the variant mechanism is exercised only on kconfig-delta's own synthetic
# C23 fixture, and the COMMITTED delta could carry a malformed `@loud` row that
# nothing ever reads.  The three cases are a set: loud must pick the two extra
# rows up, quiet must NOT, and a variant nobody declared must be refused rather
# than falling through to "no variant" -- which would build the quiet image and
# label it whatever was typed.
cat > "$T/e1b.py" <<'PY'
import importlib.machinery, importlib.util, sys
ldr = importlib.machinery.SourceFileLoader("kd", sys.argv[1])
m = importlib.util.module_from_spec(importlib.util.spec_from_loader("kd", ldr))
ldr.exec_module(m)
want = sys.argv[3] if len(sys.argv) > 3 else None
try:
    rules, _ = m.parse_delta(sys.argv[2], variant=want)
except SystemExit as e:
    print("REFUSED %s" % e.code)
    raise SystemExit(0)
sets = sum(1 for r in rules.values() if r.kind == "set")
print("%d %d %d" % (len(rules), sets, len(rules) - sets))
PY
ck "E1b --variant loud: 38 rules, 17 set, 21 derived"  "38 17 21" \
   "$("$PY" "$T/e1b.py" "$KD" "$DELTA" loud 2>&1 | tail -1)"
ck "E1b --variant quiet does NOT pick them up"         "36 15 21" \
   "$("$PY" "$T/e1b.py" "$KD" "$DELTA" quiet 2>&1 | tail -1)"
ck "E1b an undeclared variant is refused, not ignored" "REFUSED 3" \
   "$("$PY" "$T/e1b.py" "$KD" "$DELTA" loudd 2>&1 | tail -1)"

BASE="$WORK/rebuild/src-vendor/rtl819x-toolchain/boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW"
if [ -f "$BASE" ]; then
    # E2: the sha256 in the delta's header is the file it claims.
    want="$(sed -n 's/^# baseline-sha256: //p' "$DELTA")"
    got="$(sha256sum "$BASE" | cut -d' ' -f1)"
    ck "E2 the baseline sha256 in the header is that file" "$want" "$got"

    # E3: apply(baseline, delta) must differ from the baseline in exactly the
    # `set` rules -- and applying it twice must give the same file.
    "$PY" "$KD" apply --baseline "$BASE" --delta "$DELTA" --out "$T/a1" >/dev/null 2>&1
    ck "E3 apply exits 0"  0 "$?"
    "$PY" "$KD" apply --baseline "$BASE" --delta "$DELTA" --out "$T/a2" >/dev/null 2>&1
    ck "E3 apply is deterministic" 0 "$(cmp -s "$T/a1" "$T/a2"; echo $?)"

    # E4: THE trap.  Feeding the gate the file that was copied in -- rather than
    # the one the build used -- must refuse.  This is the mistake
    # notes/kernel-build.md 6.4 names, made on purpose.
    "$PY" "$KD" check --baseline "$BASE" --delta "$DELTA" --built "$BASE" >/dev/null 2>&1
    ck "E4 the pre-oldconfig file is REFUSED" 1 "$?"
else
    sk "E2-E4 the vendor template" "no drop under $WORK"
fi

UNIT="$WORK/extracted/unit-2018/squashfs-root"
if [ -d "$UNIT" ]; then
    "$PY" "$MK" build --decl "$DECL" --unit "$UNIT" --repo "$REPO" --out "$T/ir" \
        >"$T/ir.log" 2>&1
    ck "E5 the initramfs declaration resolves"  0 "$?"
    ck "E5 every file is unit-owned or named as mine" 1 \
       "$(grep -c 'nothing was substituted' "$T/ir.log")"
    # and it refuses when a source is taken away, on the real declaration
    sed 's|\$UNIT/bin/busybox|$UNIT/bin/busybox-gone|' "$DECL" > "$T/decl-bad"
    "$PY" "$MK" build --decl "$T/decl-bad" --unit "$UNIT" --repo "$REPO" \
        --out "$T/ir2" >/dev/null 2>&1
    ck "E6 a missing source in the REAL declaration refuses" 3 "$?"
else
    sk "E5-E6 this unit's rootfs" "no extracted tree under $WORK"
fi

echo
echo "=== S3/G1-G4: rlxfw-marks, R3-6's source gate ==="
# This is the first tool in the repository that edits somebody else's source.
# It runs on any machine: the controls build their own tree and their own
# fixtures, so nothing here needs a vendor drop.
RM="$HERE/rlxfw-marks.py"
o="$("$PY" "$RM" self-test 2>&1)"
ck "S3 rlxfw-marks self-test exit 0"       0 "$?"
ck "S3 rlxfw-marks 18 controls"            1 "$(printf '%s\n' "$o" | grep -c '18 passed, 0 failed')"

mutrm () { sed "$2" "$RM" > "$T/$1"; }

# G1 -- an ambiguous anchor must not be resolved by taking the first.  This is
# the difference between this file and a .patch, so it is the mutation that
# matters most.
mutrm g1 's|^    if len(hits) > 1:|    if False:  # MUTATED: pick the first of several|'
ck "G1 mutation landed" 1 "$(grep -c 'MUTATED: pick the first' "$T/g1")"
"$PY" "$T/g1" self-test >/dev/null 2>&1
ck "G1 an ambiguous anchor resolved silently -> refuse" 2 "$?"

# G2 -- the search string must carry its terminator.  Without it RLXFW-B01
# matches RLXFW-B010 and a ladder is unreadable; 量 2026-08-28, RLXFW-B1
# matched RLXFW-B10 on the first real verify.
mutrm g2 's|return PREFIX + self.tag + ("=" if self.computed else "\\n")|return PREFIX + self.tag  # MUTATED: no terminator|'
ck "G2 mutation landed" 1 "$(grep -c 'MUTATED: no terminator' "$T/g2")"
"$PY" "$T/g2" self-test >/dev/null 2>&1
ck "G2 a search string without its terminator -> refuse" 2 "$?"

# G3 -- verify's second half. A mark present in MY image and also in the
# vendor's is not a discriminator, and the anti-DoD is the record of what
# believing one costs.
mutrm g3 's|^        outs = \[(a, _count(a, s)) for a in absent\]|        outs = [(a, 0) for a in absent]  # MUTATED: the vendor image is not read|'
ck "G3 mutation landed" 1 "$(grep -c 'MUTATED: the vendor image is not read' "$T/g3")"
"$PY" "$T/g3" self-test >/dev/null 2>&1
ck "G3 verify that never reads the vendor image -> refuse" 2 "$?"

# G4 -- and the REAL declaration parses, with the count pinned.  A tool whose
# controls pass on synthetic fixtures while the committed file is malformed is
# the shape E6 pins one file along.
o="$("$PY" "$RM" verify --decl "$REPO/config/rlxfw-marks.tsv" \
     --image "$REPO/config/rlxfw-marks.tsv" 2>&1)"
ck "G4 the real declaration parses"        1 \
   "$(printf '%s\n' "$o" | grep -c 'RLXFW-B00')"
ck "G4 and it declares eleven LADDER marks" 11 \
   "$(printf '%s\n' "$o" | grep -c '^  B[0-9]')"
# 🔴 The line above pinned `^  B[0-9]` and called it "eleven marks". On
# 2026-09-01 `ID0` was added and that assertion stayed green while the file
# declared TWELVE -- a gate reading a pattern narrower than the claim it makes.
# The ladder count is still worth pinning on its own, so it stays; these two
# are what make a new mark row impossible to land unnoticed.
ck "G4a and one identity mark"             1 \
   "$(printf '%s\n' "$o" | grep -c '^  ID[0-9]')"
ck "G4b and TWELVE marks in total"        12 \
   "$(printf '%s\n' "$o" | grep -cE '^  [A-Z][A-Z0-9]{2} ')"
ck "G4 verify with no --absent is refused"  1 \
   "$(printf '%s\n' "$o" | grep -c 'no --absent file given')"

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
