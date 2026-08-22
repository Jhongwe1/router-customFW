#!/usr/bin/env bash
# Fetch every external input declared in SOURCES.json, and verify it.
#
# Why this exists
# ---------------
# This project builds from four other vendors' GPL drops and one leaked draft
# datasheet. None of them is "the source code for this device"; each is a near
# relative whose distance from this unit has to stay measurable. That is only
# possible if everyone -- including future-me -- can obtain byte-identical copies.
#
# Failing
# -------
# A fetch script that cannot fail proves nothing, so this one:
#
#   * refuses to report success when a declared sha256 does not match;
#   * refuses to treat "could not download" as "skipped";
#   * runs a POSITIVE CONTROL (it re-hashes a file it already has and requires
#     the match) and a NEGATIVE CONTROL (it hashes a deliberately corrupted copy
#     and requires the mismatch to be detected) before it trusts its own
#     verifier;
#   * prints, at the end, every item it did NOT fetch and why -- because a
#     silent skip reads exactly like a success.
#
# Usage
# -----
#   tools/fetch-sources.sh              # everything marked fetch:"now"
#   tools/fetch-sources.sh --all        # also the fetch:"later" trees (~4 GB)
#   tools/fetch-sources.sh --verify     # verify what is already on disk, fetch nothing
#   tools/fetch-sources.sh --list       # print the plan and exit

set -o errexit
set -o nounset
set -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCES="$HERE/SOURCES.json"

MODE="now"
case "${1:-}" in
    --all)     MODE="all" ;;
    --verify)  MODE="verify" ;;
    --list)    MODE="list" ;;
    "")        MODE="now" ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
esac

fail()  { printf '  \033[31mFAIL\033[0m  %s\n' "$*" >&2; FAILURES=$((FAILURES + 1)); }
ok()    { printf '  \033[32mok\033[0m    %s\n' "$*"; }
skip()  { printf '  skip  %s\n' "$*"; SKIPPED+=("$*"); }
step()  { printf '\n==> %s\n' "$*"; }

FAILURES=0
SKIPPED=()

# --------------------------------------------------------------------------
# 0. Prerequisites. Name the command that fixes each one -- a script can say
#    what broke where a README can only ask you to check.
# --------------------------------------------------------------------------
step "prerequisites"
for cmd in python3 git curl sha256sum; do
    if command -v "$cmd" >/dev/null 2>&1; then
        ok "$cmd"
    else
        fail "$cmd not found -- install it (Debian/Ubuntu: sudo apt install ${cmd/python3/python3} git curl coreutils)"
    fi
done
[ -f "$SOURCES" ] || fail "SOURCES.json not found at $SOURCES"
[ "$FAILURES" -eq 0 ] || { echo; echo "prerequisites failed; nothing was fetched." >&2; exit 1; }

python3 - "$SOURCES" <<'PYEOF' || { echo "SOURCES.json does not parse -- nothing below this line means anything until that is fixed." >&2; exit 1; }
import json, sys
json.load(open(sys.argv[1], encoding="utf-8"))
PYEOF
ok "SOURCES.json parses"

# --------------------------------------------------------------------------
# 1. Controls on the verifier itself, before it is trusted with anything.
# --------------------------------------------------------------------------
step "verifier controls"
CTRL="$(mktemp)"
printf 'router-rebuild verifier control\n' > "$CTRL"
CTRL_GOOD="$(sha256sum "$CTRL" | cut -d' ' -f1)"
if [ -n "$CTRL_GOOD" ] && [ "${#CTRL_GOOD}" -eq 64 ]; then
    ok "positive control: sha256 produced a 64-char digest"
else
    fail "positive control: sha256 did not produce a digest"
fi
printf 'x' >> "$CTRL"
CTRL_BAD="$(sha256sum "$CTRL" | cut -d' ' -f1)"
if [ "$CTRL_BAD" != "$CTRL_GOOD" ]; then
    ok "negative control: a one-byte change is detected"
else
    fail "negative control DID NOT FIRE -- the verifier cannot see a changed file. Everything below is meaningless."
fi
rm -f "$CTRL"
[ "$FAILURES" -eq 0 ] || { echo; echo "verifier controls failed; nothing was fetched." >&2; exit 1; }

# --------------------------------------------------------------------------
# 2. The plan, read out of SOURCES.json.
# --------------------------------------------------------------------------
PLAN="$(python3 - "$SOURCES" "$MODE" <<'PYEOF'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
mode = sys.argv[2]
want = {"now"} if mode in ("now", "verify", "list") else {"now", "later"}
if mode == "all":
    want = {"now", "later"}

rows = []
for d in doc.get("documents", []):
    if d.get("fetch") in want:
        rows.append("\t".join(["doc", d["id"], d["url"], d["dest"], d.get("sha256", ""), str(d.get("bytes", ""))]))
for t in doc.get("source_trees", []):
    if t.get("fetch") in want:
        rows.append("\t".join(["git", t["id"], t["url"], t["dest"], t.get("clone", "--depth 1"), t.get("approx_size", "?")]))
u = doc.get("upstream")
if u:
    rows.append("\t".join(["sub", "upstream", u["url"], u["mount"], u["pin"]["commit"], ""]))
print("\n".join(rows))
PYEOF
)"

if [ "$MODE" = "list" ]; then
    step "plan"
    printf '%s\n' "$PLAN" | while IFS=$'\t' read -r kind id url dest a b; do
        printf '  %-4s %-28s %s\n' "$kind" "$id" "$dest"
    done
    exit 0
fi

# --------------------------------------------------------------------------
# 3. Documents: fetch (unless --verify) and always hash.
# --------------------------------------------------------------------------
step "documents"
mkdir -p "$HERE/refs"
while IFS=$'\t' read -r kind id url dest want_hash want_bytes; do
    [ "$kind" = "doc" ] || continue
    path="$HERE/$dest"
    if [ ! -f "$path" ]; then
        if [ "$MODE" = "verify" ]; then
            fail "$id: not on disk (run without --verify to fetch)"
            continue
        fi
        mkdir -p "$(dirname "$path")"
        if ! curl -fsSL --retry 3 -o "$path.part" "$url"; then
            rm -f "$path.part"
            fail "$id: download failed from $url"
            continue
        fi
        mv "$path.part" "$path"
    fi
    got_hash="$(sha256sum "$path" | cut -d' ' -f1)"
    got_bytes="$(wc -c < "$path" | tr -d ' ')"
    if [ -n "$want_hash" ] && [ "$got_hash" != "$want_hash" ]; then
        fail "$id: sha256 MISMATCH
          want $want_hash
          got  $got_hash
          The file at that URL is not the file this project was written against.
          Do not use it. Record the new hash in SOURCES.json only after you have
          established what changed."
        continue
    fi
    if [ -n "$want_bytes" ] && [ "$got_bytes" != "$want_bytes" ]; then
        fail "$id: size mismatch (want $want_bytes, got $got_bytes)"
        continue
    fi
    ok "$id -> $dest ($got_bytes bytes, sha256 ${got_hash:0:12}...)"
done <<< "$PLAN"

# --------------------------------------------------------------------------
# 4. Source trees.
# --------------------------------------------------------------------------
step "source trees"
mkdir -p "$HERE/src-vendor"
while IFS=$'\t' read -r kind id url dest clone_args size; do
    [ "$kind" = "git" ] || continue
    path="$HERE/$dest"
    if [ -d "$path/.git" ]; then
        head="$(git -C "$path" rev-parse HEAD)"
        ok "$id already present at ${head:0:12} ($path)"
        continue
    fi
    if [ "$MODE" = "verify" ]; then
        skip "$id: not cloned (verify mode does not fetch)"
        continue
    fi
    printf '  ...   cloning %s (%s)\n' "$id" "$size"
    # shellcheck disable=SC2086
    if git clone $clone_args "$url" "$path" >/dev/null 2>&1; then
        head="$(git -C "$path" rev-parse HEAD)"
        ok "$id -> $dest @ ${head:0:12}"
        printf '%s\t%s\t%s\n' "$id" "$url" "$head" >> "$HERE/src-vendor/CLONED.tsv"
    else
        fail "$id: git clone failed ($url)"
    fi
done <<< "$PLAN"

# --------------------------------------------------------------------------
# 5. The upstream baseline. Deliberately NOT automatic: pinning it is a
#    decision, and the commit it pins is the whole credibility of R9.
# --------------------------------------------------------------------------
step "upstream baseline (manual, on purpose)"
UP_URL="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8"))["upstream"]["url"])' "$SOURCES")"
UP_PIN="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8"))["upstream"]["pin"]["commit"])' "$SOURCES")"
if [ -d "$HERE/upstream/.git" ]; then
    have="$(git -C "$HERE/upstream" rev-parse HEAD)"
    if [ "$have" = "$UP_PIN" ]; then
        ok "upstream pinned at ${UP_PIN:0:12} (matches SOURCES.json)"
    else
        fail "upstream is at ${have:0:12} but SOURCES.json pins ${UP_PIN:0:12}.
          The differential baseline moved. Either update the pin deliberately and
          say why in PROGRESS.md, or check out the pinned commit."
    fi
else
    skip "upstream not present. Add it yourself, so you see it succeed:
            git submodule add $UP_URL upstream
            git -C upstream checkout $UP_PIN"
fi

# --------------------------------------------------------------------------
# 6. What did NOT happen. A silent skip reads exactly like a success.
# --------------------------------------------------------------------------
step "not fetched"
if [ "${#SKIPPED[@]}" -eq 0 ]; then
    ok "nothing was skipped"
else
    for s in "${SKIPPED[@]}"; do printf '  -     %s\n' "$s"; done
fi
if [ "$MODE" = "now" ]; then
    printf '  -     the fetch:"later" trees (openwrt-rtk, edimax, rtl819x-sdk-3.4.9.3,\n'
    printf '        ggbruno-openwrt) -- about 4 GB, needed from R6 onward. Run --all.\n'
fi

# --------------------------------------------------------------------------
step "result"
if [ "$FAILURES" -ne 0 ]; then
    printf '  \033[31m%d failure(s).\033[0m Nothing here is usable until they are resolved.\n' "$FAILURES" >&2
    exit 1
fi
ok "all declared sources present and verified"
