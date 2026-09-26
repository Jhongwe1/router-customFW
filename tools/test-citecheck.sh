#!/usr/bin/env bash
# The suite for tools/citecheck.py, at the level citecheck's own --self-test
# cannot reach: a real process, a real exit code, and the shape of the output
# the census reads.
#
# citecheck's --self-test builds git fixtures in temp directories and runs the
# sweep IN PROCESS.  That is the right place for the oracle's controls and the
# wrong place for three things, which is why this file exists:
#
#   * whether the process exits 0/1/2, rather than whether a function returns
#   * whether every case line carries EXACTLY two leading spaces.  That is the
#     contract with tools/ci-census.py and it is not decoration: a suite that
#     prints four makes ok, fails, skips and unparsable ALL ZERO, the census
#     reports the suite as absent, and it has cost this repository two pushes
#   * whether the COMMITTED baseline is a file a reviewer can read -- six
#     columns, no duplicate keys, no kind citecheck cannot produce
#
# 🔴 The case count here is a property of THIS FILE and not of the repository.
# Nothing below counts citations, findings or baseline rows into a number a
# case asserts.  `test-boot-timeline`'s B2 hardcoded a population and went red
# on three consecutive seatings; `ci.yml` records that as the single largest
# source of CI failure here.  The one case that does compare two corpora
# compares the two CASE COUNTS and requires them EQUAL while requiring the two
# citation counts to DIFFER -- which is the property, stated as a test rather
# than as a comment.
#
# 🔴 citecheck's --self-test output is captured to a file and never printed.
# Its case lines have the same two-space shape as this suite's, and a census
# reads `.out` files by line, so echoing them would add another suite's cases
# to this one's total.  (No count is written here on purpose: a number in a
# comment beside a suite that grows is the thing this repository keeps
# catching.)
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CC="$HERE/citecheck.py"
BL="$HERE/citecheck-baseline.tsv"
PY="${PYTHON:-/usr/bin/python3}"

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then
        printf '  ok     %-54s %s\n' "$1" "$3"; pass=$((pass+1))
    else
        printf '  FAIL   %s  expected %s, got %s\n' "$1" "$2" "$3"
        fail=$((fail+1))
    fi
}

# Run citecheck and record its exit code without errexit killing the suite.
run () { # outfile args...
    local out="$1"; shift
    set +o errexit
    "$PY" "$CC" "$@" > "$out" 2>&1
    rc=$?
    set -o errexit
}

# A git repository that is blind to file modes the way this machine is, holding
# `a.md` citing `src/b.txt:3`.  Two commits, because the oracle needs the
# citing line to have a commit of its own.
mkrepo () { # dir  insert-lines-above-the-cited-row
    local d="$1" pre="$2" i
    mkdir -p "$d/src"
    printf '# fixture\n\nThe row is at `src/b.txt:3` and that is the claim.\n' > "$d/a.md"
    : > "$d/src/b.txt"
    for i in 1 2 3 4 5 6 7 8; do printf 'line %d\n' "$i" >> "$d/src/b.txt"; done
    git -C "$d" init -q
    git -C "$d" config core.autocrlf false
    git -C "$d" config core.fileMode false
    git -C "$d" config user.email t@t
    git -C "$d" config user.name t
    git -C "$d" add -A
    git -C "$d" -c commit.gpgsign=false commit -q -m one
    if [ "$pre" -gt 0 ]; then
        { for i in $(seq 1 "$pre"); do printf 'inserted %d\n' "$i"; done
          cat "$d/src/b.txt"; } > "$d/src/b.new"
        mv "$d/src/b.new" "$d/src/b.txt"
        git -C "$d" add -A
        git -C "$d" -c commit.gpgsign=false commit -q -m two
    fi
}

echo "=== CONTROL: a synthetic repository, one violation in each direction ==="
mkrepo "$T/moved" 4
run "$T/moved.out" --sweep-only --root "$T/moved" --baseline "$T/absent.tsv"
ck "a cited row that moved is reported" 1 "$rc"
ck "and the report says WHERE it went" 1 \
   "$(grep -c 'now at line 7' "$T/moved.out" || true)"
mkrepo "$T/still" 0
run "$T/still.out" --sweep-only --root "$T/still" --baseline "$T/absent.tsv"
ck "a cited row that did not move is not" 0 "$rc"
ck "and nothing is reported about it" 0 \
   "$(grep -c 'CITE-' "$T/still.out" || true)"

echo
echo "=== CONTROL: the case-line shape tools/ci-census.py parses ==="
# EXACTLY two leading spaces, measured with the census's own anchor.
two="$(grep -cE '^ {2}(ok|FAIL|skip)\b' "$T/moved.out" || true)"
ck "every case line is at exactly two spaces" "$two" \
   "$(grep -cE '^ +(ok|FAIL|skip)\b' "$T/moved.out" || true)"
ck "and there is more than one of them" 1 \
   "$([ "$two" -gt 1 ] && echo 1 || echo 0)"
# The control on that control: the informational lines are deliberately at four
# spaces so the census cannot see them, and something must assert they exist.
ck "the un-counted detail lines are at four" 1 \
   "$([ "$(grep -cE '^ {4}[a-zA-Z]' "$T/moved.out" || true)" -gt 0 ] && echo 1 || echo 0)"
ck "the RESULT line is the last thing printed" 1 \
   "$(tail -1 "$T/moved.out" | grep -c '^RESULT: ' || true)"

echo
echo "=== CONTROL: the refusals, which are the reason this tool can fail ==="
mkdir -p "$T/empty"
run "$T/empty.out" --sweep-only --root "$T/empty"
ck "a directory that is not a repository: rc" 2 "$rc"
ck "and it said REFUSING"                  1 \
   "$(grep -c REFUSING "$T/empty.out" || true)"
# 🔴 A shallow clone is the control that makes every reading above mean
# something: with --depth 1 every line blames to one commit, so the cited file
# "at the citing commit" IS the cited file now and every citation reads STABLE.
git clone -q --depth 1 "file://$T/moved" "$T/shallow" 2>/dev/null || true
if [ "$(git -C "$T/shallow" rev-parse --is-shallow-repository 2>/dev/null || echo no)" = true ]; then
    run "$T/shallow.out" --sweep-only --root "$T/shallow" --baseline "$T/absent.tsv"
    ck "a SHALLOW clone: rc"          2 "$rc"
    ck "and it named the depth"       1 \
       "$(grep -c 'SHALLOW' "$T/shallow.out" || true)"
    # the negative control: the same tree, full depth, is NOT refused
    run "$T/deep.out" --sweep-only --root "$T/moved" --baseline "$T/absent.tsv"
    ck "the same tree at full depth is not" 1 "$rc"
else
    # ONE skip line standing for THREE cases, which is the shape ci-census
    # reads: a skip LINE is not a skipped CASE, and the table says how many
    # each label covers.
    printf '  skip   %-52s %s\n' "shallow clone" \
        "git would not make a --depth 1 clone here (covers 3)"
fi

echo
echo "=== CONTROL: the committed baseline is a file a reviewer can read ==="
rows="$(grep -vcE '^\s*(#|$)' "$BL" || true)"
ck "it has rows"                          1 \
   "$([ "$rows" -gt 0 ] && echo 1 || echo 0)"
ck "every row has six tab-separated cells" 0 \
   "$(awk -F'\t' '!/^[ \t]*#/ && NF>0 && NF!=6' "$BL" | grep -c . || true)"
ck "every kind is one citecheck produces"  0 \
   "$(awk -F'\t' '!/^[ \t]*#/ && NF==6 && $1!="ROT" && $1!="M3" && $1!="M4" \
        && $1!="M1" && $1!="M2"' "$BL" | grep -c . || true)"
ck "no two rows share a key"               0 \
   "$(awk -F'\t' '!/^[ \t]*#/ && NF==6 {print $1"\t"$2"\t"$3"\t"$4"\t"$5}' "$BL" \
      | sort | uniq -d | grep -c . || true)"
ck "every cited line number is a number"   0 \
   "$(awk -F'\t' '!/^[ \t]*#/ && NF==6 && $4 !~ /^[0-9]+$/' "$BL" | grep -c . || true)"

echo
echo "=== CONTROL: the baseline is swept in BOTH directions ==="
# forward: a finding that is NOT on the baseline is red
"$PY" "$CC" --write-baseline --rev HEAD --root "$ROOT" > "$T/gen.tsv" 2>/dev/null
run "$T/withbl.out" --sweep-only --rev HEAD --root "$ROOT" --baseline "$T/gen.tsv"
ck "a generated baseline covers its own findings" 0 "$rc"
grep -v '^ROT' "$T/gen.tsv" > "$T/short.tsv"
run "$T/short.out" --sweep-only --rev HEAD --root "$ROOT" --baseline "$T/short.tsv"
ck "dropping the ROT rows turns it red"           1 "$rc"
ck "and C3 is the case that says so"              1 \
   "$(grep -cE '^  FAIL   C3 ' "$T/short.out" || true)"
# reverse: a row naming no finding is red, so the list cannot accrete unread
{ cat "$T/gen.tsv"; printf 'ROT\tno/such.md\tno/such.txt\t9\t%s\tinvented\n' \
    "0000000000000000"; } > "$T/extra.tsv"
run "$T/extra.out" --sweep-only --rev HEAD --root "$ROOT" --baseline "$T/extra.tsv"
ck "a row naming no finding turns it red"         1 "$rc"
ck "and C4 is the case that says so"              1 \
   "$(grep -cE '^  FAIL   C4 ' "$T/extra.out" || true)"

echo
echo "=== CONTROL: --write-baseline cannot silence the gate by itself ==="
before="$(cksum < "$BL")"
"$PY" "$CC" --write-baseline --rev HEAD --root "$ROOT" > /dev/null 2>&1
ck "it writes stdout and not the file" "$before" "$(cksum < "$BL")"

echo
echo "=== THIS REPOSITORY ==="
run "$T/self.out" --self-test
ck "citecheck's own controls pass"        0 "$rc"
ck "and there were some"                  1 \
   "$([ "$(grep -cE '^ {2}ok ' "$T/self.out" || true)" -gt 10 ] && echo 1 || echo 0)"
run "$T/head.out" --sweep-only --rev HEAD --root "$ROOT"
ck "HEAD is clean against the committed baseline" 0 "$rc"

# The corpus-invariance property, as a measurement rather than a comment: two
# different states of the real corpus, different citation counts, SAME number
# of case lines.
run "$T/old.out" --sweep-only --rev HEAD~30 --root "$ROOT" --baseline "$T/absent.tsv"
if [ "$rc" = 2 ]; then
    printf '  skip   %-52s %s\n' "deep history" \
        "HEAD~30 is not reachable from this checkout (covers 2)"
else
    n_new="$(grep -cE '^ {2}(ok|FAIL)\b' "$T/head.out" || true)"
    n_old="$(grep -cE '^ {2}(ok|FAIL)\b' "$T/old.out" || true)"
    # Citations and files together: 36bfff8 and 3e72889 each carry 450
    # citations at HEAD and at HEAD~30 (203 and 192 files), so the count
    # alone read two different corpora as one.
    c_new="$(sed -n 's/.*  \([0-9]* citations over [0-9]* tracked\).*/\1/p' "$T/head.out")"
    c_old="$(sed -n 's/.*  \([0-9]* citations over [0-9]* tracked\).*/\1/p' "$T/old.out")"
    ck "case count invariant to corpus size" "$n_new" "$n_old"
    ck "and the two corpora really differ"   1 \
       "$([ "$c_new" != "$c_old" ] && echo 1 || echo 0)"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
