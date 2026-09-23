#!/usr/bin/env python3
"""Answer *can this image run this command* -- before a card is frozen.

Why this exists
---------------
``SPEC.md`` ``FW-46`` measured, on the silicon, that this image's busybox has no
``dd``, no ``md5sum`` and no ``--list``, and its own row draws the general rule:

    ⚠️ 也就是說,未來的卡片不可以猜 applet 存不存在
    ... 而這個 repo 裡仍然沒有任何東西能在卡片凍結前問
       「這顆映像跑得動這條指令嗎」

Two seatings have been spent on that guess.  ``FW-26`` is the earlier instance
(``mtd_debug`` absent; ``R5-5``'s DoD named a binary the image does not have and
a whole desk segment had to be rewritten), ``FW-46`` the later (three bench cells
returned ``applet not found``).  Both were found *after* something had been
written that depended on the guess.

And ``tools/cardcheck.py:451`` says the same thing in its own refusal message:

    f"{base}: ALLOWED as an ash builtin -- 推, this "
    f"project has never read this binary's builtin table"

This reads it.  The image's invocable vocabulary is three disjoint sets, all of
them inside one ELF file that this project already declares by name in
``config/rlxfw-initramfs.tsv``:

* the **applet** table -- what ``busybox <name>`` will run,
* the **ash builtin** table -- what the shell runs without forking,
* the ash **keyword** table -- what the parser recognises.

None of that is device-identifying: they are BusyBox's own stock names, byte for
byte the same on every device that ships this configuration.  What IS specific to
this unit is *which* configuration, and that is the whole point.

How the tables are located, and why not by offset
-------------------------------------------------
By **signature**, never by a hardcoded offset, because an offset is one busybox
away from being silently wrong and this repository has six busybox binaries.

* applets: the longest run of contiguous, NUL-separated, strictly
  alphabetically increasing names matching ``^[a-z][a-z0-9_.-]*$``.  BusyBox
  emits ``applet_names`` in the order of ``include/applets.h``, which is sorted.
* builtins: the longest run of contiguous 8-byte-aligned ``[0-7]<name>\\0``
  records whose names are strictly alphabetically increasing.  ash's
  ``builtincmd[]`` prefixes each name with a flag character.
* keywords: the run of contiguous ``\\x01<name>\\0`` records immediately
  preceding the builtin table.

**A short or unsorted run is a REFUSAL, not a short answer.**  A tool that
reports "3 applets" when its parser has broken looks exactly like a tool
reporting a very small image, and this project's rule is that a tool reporting 0
is making a claim.

Where this will fail, written before it was used
------------------------------------------------
1. 🔴 **It answers whether the NAME is in the table, not whether the applet
   WORKS.**  An ABSENT answer is strong -- it is exactly the ``applet not found``
   that ``FW-46`` measured.  A PRESENT answer is weaker: the applet is compiled
   in, and it can still fail at run time.
2. 🔴 **It says nothing about OPTIONS.**  ``SPEC.md`` ``FW-42`` measured ``grep``
   present and ``grep -E`` absent on this same image.  This tool would say
   ``grep: PRESENT`` and be useless about the flag.  That trap has already cost
   this project once; it is not closed here and this paragraph is the whole of
   what is done about it.
3. It assumes BusyBox's table layout.  A build with a different one breaks the
   signature -- which is why a broken signature refuses.
4. The extraction half reads ``$FWRE_WORK``, which CI does not have.  So
   ``extract`` is bench-only and ``check``/``query``/``--self-test`` run against
   the committed TSV and work everywhere.

Usage
-----
    appletcensus.py extract [--binary <path>] [--write]
    appletcensus.py query cat dd printf awk
    appletcensus.py check                 # the TSV against the silicon truths
    appletcensus.py diff-builtins         # measured table vs cardcheck's 推 list
    appletcensus.py --self-test
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, "config", "image-commands.tsv")

NAME_RE = re.compile(rb"^[a-z][a-z0-9_.\-]*$")
MIN_RUN = 20

# --- the controls, and what each one's evidence ACTUALLY is ------------------
#
# 🔴 The first draft of this block cited "seating 20" for `ps` and
# "FW-41/FW-47 -- the echo interleave is ash's" for `ash`.  Both claims are
# true and both citations were wrong: a census of every `sent` field in
# bench/**/*.meta.json shows `ps` and `ash` have NEVER been typed at this
# device, and the echo-interleave reading proves the SHELL is ash, not that the
# applet NAME `ash` resolves.  That is the same over-extension this segment
# found in docs/KNOWN-ISSUES.md's citation of FW-46, committed here an hour
# later.  The real source for both is SPEC.md FW-25.
#
# Two-sided on purpose: a tool that only confirms absences passes by returning
# an empty table, and one that only confirms presences passes by returning
# every word in the binary.
SILICON_PRESENT = {
    # --- 量 2026-08-29, FW-25: this unit's own busybox under qemu-mips-static,
    #     with its own two controls (a non-applet gives `sh: ... not found`;
    #     `cat` reaches open() before failing).  FW-25 names 13 of the 50.
    "cat":      "FW-25 (qemu) + 412 bench sends",
    "ifconfig": "FW-25 (qemu) + 38 bench sends",
    "ping":     "FW-25 (qemu) + 22 bench sends; R3 D5 answered 4 replies",
    "ls":       "FW-25 (qemu) + 4 bench sends",
    "ps":       "FW-25 (qemu) -- never typed at the device",
    "mount":    "FW-25 (qemu) -- never typed at the device",
    "echo":     "FW-25 (qemu) + 246 bench sends",
    "sleep":    "FW-25 (qemu) + 59 bench sends",
    "mkdir":    "FW-25 (qemu) -- never typed at the device",
    "sh":       "FW-25 (qemu) -- never typed as a command; /init execs it",
    "ash":      "FW-25 (qemu) -- never typed at the device",
    "sed":      "FW-25 (qemu) -- never typed at the device",
    "grep":     "FW-25 (qemu) + 6 bench sends (FW-42: the applet, not -E)",
    # --- 量 on the die, from the committed capture corpus
    "reboot":   "63 bench sends; FW-37 -- reboot -f resets the board in 2.407 s",
    "wc":       "8 bench sends; FW-46's own control C1-SZ read back 4194304",
}
SILICON_ABSENT = {
    "uname":    "FW-25, 量 2026-08-29 -- busybox uname -a: applet not found",
    "dd":       "FW-46, 量 2026-09-08 seating 16 -- dd: applet not found",
    "md5sum":   "FW-46, 量 2026-09-08 seating 16 -- md5sum: applet not found",
    # 🟢 OUT OF SAMPLE.  This row was added AFTER the extractor had already run
    # and reported its table; it was found by censusing every `sent` field, not
    # by being remembered.  bench/2026-09-14c/X-seq.log: `busybox seq 3` ->
    # `seq: applet not found`.  It is the only control here that the tool did
    # not have a chance to be fitted to.
    "seq":      "bench/2026-09-14c/X-seq.log, 量 -- seq: applet not found "
                "(registered after extraction: an out-of-sample prediction)",
}

# 🟢 The strongest single control is a COUNT from a different method.
# FW-25 counted the applet table by RUNNING the binary under qemu-mips-static
# on 2026-08-29 and reports 50.  This tool counts it by parsing bytes and never
# executes anything.  Two methods, no shared code, one number.
FW25_APPLET_COUNT = 50

# cardcheck.py's 推 list, copied here so the two can be compared by program.
# 🔴 This copy is a SECOND owner of that set and it is deliberate and bounded:
# `diff-builtins` exists to report when they disagree, and `--self-test` case
# T5 fails if this copy stops matching cardcheck's.
CARDCHECK_BUILTINS_推 = {
    ":", ".", "break", "cd", "continue", "eval", "exec", "exit", "export",
    "false", "hash", "local", "read", "return", "set", "shift", "source",
    "test", "times", "trap", "true", "type", "ulimit", "umask", "unset",
    "wait", "[",
}


class Refuse(Exception):
    pass


# ---------------------------------------------------------------- extraction

def _runs(blob, base=0):
    """Every NUL-separated non-empty byte string, with its absolute offset."""
    out, cur, start = [], b"", base
    for i, ch in enumerate(blob):
        if ch == 0:
            if cur:
                out.append((start, cur))
            cur, start = b"", base + i + 1
        else:
            if not cur:
                start = base + i
            cur += bytes([ch])
    if cur:
        out.append((start, cur))
    return out


def _longest_sorted_run(items, keyfn):
    """Longest maximal slice of `items` on which keyfn is strictly increasing."""
    best = (0, 0)
    i = 0
    while i < len(items):
        j = i
        while j + 1 < len(items) and keyfn(items[j + 1]) > keyfn(items[j]):
            j += 1
        if j - i + 1 > best[1] - best[0]:
            best = (i, j + 1)
        i = j + 1
    return items[best[0]:best[1]]


def find_applets(data):
    """The applet_names run: plain names, contiguous, alphabetically sorted."""
    cand = [(o, s) for (o, s) in _runs(data) if NAME_RE.match(s)]
    # contiguity: the next record must begin exactly one byte past this one's NUL
    groups, cur = [], []
    for rec in cand:
        if cur and rec[0] != cur[-1][0] + len(cur[-1][1]) + 1:
            groups.append(cur)
            cur = []
        cur.append(rec)
    if cur:
        groups.append(cur)
    best = []
    for g in groups:
        run = _longest_sorted_run(g, lambda r: r[1])
        if len(run) > len(best):
            best = run
    # 🔴 The FIRST name of the blob is not preceded by a NUL of its own -- it is
    # preceded by whatever datum sits before `applet_names`, and on this unit
    # that datum's last byte is 0x01.  So the record holding it reads as
    # b"\x01ash" and NAME_RE drops the whole entry.  Recover it by stripping
    # leading non-name bytes off the record immediately before the run, and only
    # if the remainder still sorts before the run's first name.
    #
    # 量 This was found by the two-sided silicon control, not by reading the
    # code: `ash` came back ABSENT and the table came back 49 long against a
    # hand count of 50.
    if best:
        first_off = best[0][0]
        prev = [r for r in _runs(data) if r[0] + len(r[1]) + 1 == first_off]
        if prev:
            raw = prev[0][1]
            m = re.search(rb"[a-z][a-z0-9_.\-]*$", raw)
            if m and m.group(0) != raw and m.group(0) < best[0][1]:
                best = [(prev[0][0] + m.start(), m.group(0))] + best
    if len(best) < MIN_RUN:
        raise Refuse(
            f"REFUSING: the longest contiguous sorted name run is {len(best)} "
            f"entries, below the {MIN_RUN} this parser requires. Either this is "
            f"not a BusyBox binary or its table layout is not the one this tool "
            f"reads. A short list would look like a small image and it is not "
            f"one -- see the docstring.")
    return [s.decode() for (_, s) in best], best[0][0]


def _prefixed_run(data, prefix_ok, stride=8):
    """Runs of `stride`-aligned records `<flag><name>\\0` with flag in prefix_ok."""
    out = []
    for off, s in _runs(data):
        if len(s) < 2 or s[0] not in prefix_ok:
            continue
        name = s[1:]
        if not NAME_RE.match(name) and name not in (b"[", b"[[", b":", b".", b"}"):
            continue
        out.append((off, chr(s[0]), name))
    groups, cur = [], []
    for rec in out:
        if cur and not (0 < rec[0] - cur[-1][0] <= stride * 2):
            groups.append(cur)
            cur = []
        cur.append(rec)
    if cur:
        groups.append(cur)
    best = []
    for g in groups:
        run = _longest_sorted_run(g, lambda r: r[2])
        if len(run) > len(best):
            best = run
    return best


def find_builtins(data):
    run = _prefixed_run(data, set(b"01234567"))
    if len(run) < MIN_RUN:
        raise Refuse(
            f"REFUSING: the ash builtin run is {len(run)} entries, below "
            f"{MIN_RUN}. See the docstring: a short list is a broken parser, "
            f"not a small shell.")
    return [n.decode() for (_, _, n) in run], run[0][0]


def find_keywords(data, before):
    """ash keywords sit immediately before the builtin table, flag \\x01."""
    window = data[max(0, before - 256):before]
    run = _prefixed_run(window, {1})
    return sorted({n.decode() for (_, _, n) in run})


def extract(path):
    with open(path, "rb") as f:
        data = f.read()
    applets, a_off = find_applets(data)
    builtins, b_off = find_builtins(data)
    keywords = find_keywords(data, b_off)
    ver = None
    m = re.search(rb"BusyBox v([0-9][0-9.]*)", data)
    if m:
        ver = m.group(1).decode()
    return {
        "path": path,
        "size": len(data),
        "version": ver,
        "applets": applets,
        "applet_off": a_off,
        "builtins": builtins,
        "builtin_off": b_off,
        "keywords": keywords,
    }


# ------------------------------------------------------------------- the TSV

def write_tsv(info, out=TSV):
    lines = [
        "# config/image-commands.tsv -- what the first-boot image can INVOKE.",
        "# Derived by tools/appletcensus.py from the busybox declared at",
        "# config/rlxfw-initramfs.tsv:104.  Regenerate with `appletcensus.py",
        "# extract --write`; that half is BENCH-ONLY because it reads $FWRE_WORK.",
        "#",
        "# 🔴 kind=applet means `busybox <name>` resolves.  It does NOT mean the",
        "#    applet works, and it says NOTHING about options: SPEC.md FW-42",
        "#    measured `grep` present and `grep -E` absent on this same image.",
        f"# busybox\tv{info['version']}\t{info['size']} bytes",
        "kind\tname",
    ]
    for n in info["applets"]:
        lines.append(f"applet\t{n}")
    for n in info["builtins"]:
        lines.append(f"builtin\t{n}")
    # 🔴 NO keyword rows, deliberately, and this is a measurement rather than a
    # preference.  ash's `tokname_array` entries include "end of file", ";;",
    # "!" and "{", which the name regex drops -- and dropping one splits the
    # contiguous run, so the extractor recovers 8 of the ~20 keywords.  量,
    # from the same corpus that produced the controls above: `for` was typed at
    # this device 17 times and `while` 4 times, both worked, and NEITHER is in
    # the extracted run.  A keyword list that is known to be short is worse
    # than none, because a checker that consumes it reports a missing program
    # for a word the board runs.  `find_keywords()` stays for `extract`'s human
    # output; nothing machine-readable rests on it.
    body = "\n".join(lines) + "\n"
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    os.replace(tmp, out)
    return body


def read_tsv(path=TSV):
    if not os.path.exists(path):
        raise Refuse(f"REFUSING: {path} does not exist. Run `extract --write` "
                     f"at a bench host first.")
    kinds = {"applet": [], "builtin": [], "keyword": []}
    meta = {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("# busybox"):
            parts = line.split("\t")
            if len(parts) >= 2:
                meta["version"] = parts[1]
        if not line or line.startswith("#") or line.startswith("kind\t"):
            continue
        k, _, n = line.partition("\t")
        if k in kinds:
            kinds[k].append(n)
    total = sum(len(v) for v in kinds.values())
    if total < MIN_RUN:
        raise Refuse(f"REFUSING: {path} holds {total} names, below {MIN_RUN}.")
    return kinds, meta


def classify(word, kinds):
    if word in kinds["applet"]:
        return "applet"
    if word in kinds["builtin"]:
        return "builtin"
    if word in kinds["keyword"]:
        return "keyword"
    return None


# ------------------------------------------------------------------ commands

def cmd_extract(args):
    path = args.binary or default_binary()
    info = extract(path)
    print(f"  {os.path.basename(path)}  BusyBox v{info['version']}  "
          f"{info['size']} bytes")
    print(f"  applets  {len(info['applets']):>3}  at 0x{info['applet_off']:X}")
    print(f"  builtins {len(info['builtins']):>3}  at 0x{info['builtin_off']:X}")
    print(f"  keywords {len(info['keywords']):>3}")
    print()
    print("  applets : " + " ".join(info["applets"]))
    print("  builtins: " + " ".join(info["builtins"]))
    print("  keywords: " + " ".join(info["keywords"]))
    if args.write:
        write_tsv(info)
        print(f"\n  wrote {TSV}")
    return 0


def default_binary():
    work = os.environ.get("FWRE_WORK", "/home/key/fwre-work")
    return os.path.join(work, "extracted", "unit-2018", "squashfs-root",
                        "bin", "busybox")


def cmd_query(args):
    kinds, meta = read_tsv()
    bad = 0
    for w in args.words:
        k = classify(w, kinds)
        if k:
            print(f"  {w:<12} PRESENT  ({k})")
        else:
            print(f"  {w:<12} ABSENT")
            bad += 1
    if bad:
        print(f"\n  🔴 {bad} of {len(args.words)} are not invocable in this image.")
    return 1 if bad else 0


def cmd_check(args):
    """The committed TSV against the readings taken on the die."""
    kinds, meta = read_tsv()
    fails = []
    for w, why in sorted(SILICON_PRESENT.items()):
        k = classify(w, kinds)
        ok = k is not None
        print(f"  {'ok  ' if ok else 'FAIL'}  present  {w:<10} "
              f"{'(' + k + ')' if k else '*** NOT IN TSV ***':<10}  {why}")
        if not ok:
            fails.append(("present", w))
    for w, why in sorted(SILICON_ABSENT.items()):
        k = classify(w, kinds)
        ok = k is None
        print(f"  {'ok  ' if ok else 'FAIL'}  absent   {w:<10} "
              f"{'' if ok else '*** FOUND as ' + str(k) + ' ***':<10}  {why}")
        if not ok:
            fails.append(("absent", w))
    n = len(SILICON_PRESENT) + len(SILICON_ABSENT)
    print(f"\n  {n - len(fails)} of {n} silicon readings reproduced "
          f"({len(SILICON_PRESENT)} present, {len(SILICON_ABSENT)} absent).")
    return 1 if fails else 0


def cmd_diff_builtins(args):
    kinds, meta = read_tsv()
    measured = set(kinds["builtin"])
    applets = set(kinds["applet"])
    missing = sorted(measured - CARDCHECK_BUILTINS_推)
    extra = sorted(CARDCHECK_BUILTINS_推 - measured)
    print(f"  cardcheck's 推 list: {len(CARDCHECK_BUILTINS_推)} names")
    print(f"  measured table     : {len(measured)} names")
    print()
    print(f"  in 推 but NOT measured (false positives -- these would be "
          f"WRONGLY allowed): {extra or 'none'}")
    print()
    print(f"  measured but NOT in 推 ({len(missing)}): {' '.join(missing)}")
    only = [m for m in missing if m not in applets]
    print(f"  of those, NOT also an applet, so cardcheck would report them "
          f"'NOT IN IMAGE' ({len(only)}): {' '.join(only)}")
    return 0


# ----------------------------------------------------------------- self-test

def _selftest():
    ok = True

    def case(tag, cond, msg):
        nonlocal ok
        print(f"  {'ok  ' if cond else 'FAIL'}  {tag}  {msg}")
        if not cond:
            ok = False

    # T1 -- the TSV reproduces every silicon reading.
    try:
        kinds, meta = read_tsv()
        miss_p = [w for w in SILICON_PRESENT if classify(w, kinds) is None]
        miss_a = [w for w in SILICON_ABSENT if classify(w, kinds) is not None]
        case("T1", not miss_p and not miss_a,
             f"committed TSV vs the die: {len(SILICON_PRESENT)} present / "
             f"{len(SILICON_ABSENT)} absent"
             + (f"  MISSES {miss_p + miss_a}" if (miss_p or miss_a) else ""))
    except Refuse as e:
        case("T1", False, f"{e}")
        kinds = None

    # T2 -- a parser that cannot refuse proves nothing: give it rubbish.
    try:
        find_applets(b"\x00".join([b"zzz", b"aaa", b"mmm"]))
        case("T2", False, "rubbish input did NOT refuse")
    except Refuse:
        case("T2", True, "rubbish input refuses rather than reporting a short list")

    # T3 -- and it must not refuse a table that IS there.
    synth = b"\x00" + b"\x00".join(
        [f"cmd{i:03d}".encode() for i in range(40)]) + b"\x00"
    try:
        got, _ = find_applets(synth)
        case("T3", len(got) == 40, f"synthetic 40-name table -> {len(got)} names")
    except Refuse as e:
        case("T3", False, f"refused a good table: {e}")

    # T4 -- ORDER is load bearing: an unsorted table must not be accepted whole.
    unsorted = b"\x00" + b"\x00".join(
        [f"cmd{i:03d}".encode() for i in range(40)][::-1]) + b"\x00"
    try:
        got, _ = find_applets(unsorted)
        case("T4", False, f"a reversed table was accepted as {len(got)} names")
    except Refuse:
        case("T4", True, "a reversed table refuses (the sort is the signature)")

    # T5 -- this file's copy of cardcheck's list must still match cardcheck's.
    cc = os.path.join(ROOT, "tools", "cardcheck.py")
    if os.path.exists(cc):
        src = open(cc, encoding="utf-8").read()
        m = re.search(r"ASH_BUILTINS\s*=\s*\{(.*?)\}", src, re.S)
        live = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
        case("T5", live == CARDCHECK_BUILTINS_推,
             f"the copy of cardcheck's 推 list is current "
             f"({len(live)} live vs {len(CARDCHECK_BUILTINS_推)} here)"
             + ("" if live == CARDCHECK_BUILTINS_推
                else f"  DRIFT: {sorted(live ^ CARDCHECK_BUILTINS_推)}"))
    else:
        case("T5", False, "tools/cardcheck.py not found")

    # T6 -- the 推 list must be a SUBSET of the measured one, or the guess was
    #       not merely incomplete, it was wrong, and cards rest on it.
    if kinds:
        measured = set(kinds["builtin"])
        case("T6", CARDCHECK_BUILTINS_推 <= measured,
             f"cardcheck's 推 list is a subset of the measured table"
             + ("" if CARDCHECK_BUILTINS_推 <= measured
                else f"  FALSE POSITIVES: "
                     f"{sorted(CARDCHECK_BUILTINS_推 - measured)}"))

    # T7 -- printf: named because it is the one that changes what P1-1 can write.
    if kinds:
        case("T7", classify("printf", kinds) == "builtin",
             "printf is a builtin (awk is absent, so it is the only format verb)")

    # T8 -- the count, against a number measured by a DIFFERENT METHOD.
    #       FW-25 ran the binary under qemu-mips-static on 2026-08-29 and
    #       counted 50.  This tool never executes anything.  No shared code.
    if kinds:
        n = len(kinds["applet"])
        case("T8", n == FW25_APPLET_COUNT,
             f"applet count {n} against FW-25's independently measured "
             f"{FW25_APPLET_COUNT} (qemu-mips-static, 2026-08-29)")

    # T9 -- the keyword list must NOT be in the TSV: it is known short.
    case("T9", not kinds or not kinds.get("keyword"),
         "no keyword rows in the TSV (the extracted run is short -- "
         "`for` and `while` run on the die and are not in it)")

    # 🔴 NOT a two-space `ok`: `tools/ci-census.py` parses every line that
    # starts with two spaces and `ok`/`FAIL`/`skip` as a CASE line, and a
    # summary in that shape comes back as "1 line(s) ... did not parse".
    # 量: it did, on this tool's first census run.
    print()
    print(f"== {'all cases ok' if ok else 'FAILED'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("extract")
    p.add_argument("--binary")
    p.add_argument("--write", action="store_true")
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("query")
    p.add_argument("words", nargs="+")
    p.set_defaults(fn=cmd_query)

    p = sub.add_parser("check")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("diff-builtins")
    p.set_defaults(fn=cmd_diff_builtins)

    args = ap.parse_args()
    if args.self_test:
        return _selftest()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    try:
        return args.fn(args)
    except Refuse as e:
        print(f"  {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
