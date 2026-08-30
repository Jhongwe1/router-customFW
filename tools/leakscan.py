#!/usr/bin/env python3
"""Run `audit-bench-log.py`'s patterns over the populations nothing has scanned,
and never print what matched.

WHY THIS EXISTS
---------------
🔴 量 2026-08-30.  `.github/workflows/ci.yml` runs

    audit-bench-log.py $(find bench -type f -name '*.log')

and that is the whole of this repository's leak checking.  Three populations
have never been looked at:

  * `bench/**/*.md` -- 45 committed files IN THE DIRECTORY THE GATE IS NAMED
    FOR: prediction cards and corrections, where a device reading is TRANSCRIBED
    BY HAND.  The gate scans what the instrument wrote and not what a person
    typed, and a person is the one who can mistype a MAC into prose.
  * every other tracked text file -- SPEC.md, PROGRESS.md, LOG.md, RUNSHEET.md,
    notes/, docs/, README.md, CHANGELOG.md.
  * `upstream/` -- 302 files.  `upstream` is a submodule, so `git ls-files`
    returns ONE entry (the gitlink) and every sweep built on it has looked at
    zero of them.  量: `git ls-files upstream` -> 1 line.

⚠️ AND 24 OF THOSE 302 ARE IMAGES (22 jpg, 2 png).  This is a text scanner.  It
CANNOT read them and it says so per population rather than counting them clean.
A photograph of a board with a label on it is a leak this tool is blind to.

WHY IT DOES NOT PRINT WHAT MATCHED
----------------------------------
`audit-bench-log.py` prints the matched text, which is right for a bench log the
operator is about to commit and wrong here: the question being asked is whether
this unit's MAC is in a file that is already published, and answering it by
printing the MAC is answering it in the worst possible way.  `flashwin.py` makes
the same distinction -- it publishes the verdict and refuses the digest.  `L5`
is the control on that property, because a safety claim nothing exercises is a
comment.

WHY IT IMPORTS RATHER THAN DRIVES THE CLI
-----------------------------------------
`TC-j` is the standing lesson that a private copy of a pipeline is a pipeline
the controls do not test.  This imports `audit-bench-log.py`'s own `PATTERNS`,
`ALLOW`, `allowed` and `scan` -- there is no second copy of the rules.  What it
does not reuse is `main()`, and the reason is exactly the paragraph above: that
function's output is the thing that must not happen.  `L1`/`L2`/`L3` are the
same controls run against the same imported objects.

Usage:  tools/leakscan.py [--self-test]
"""
import io
import os
import re
import subprocess
import sys
import importlib.machinery
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABL = os.path.join(ROOT, "tools", "audit-bench-log.py")

#: Extensions this scanner can read.  Anything else is reported NOT SCANNED,
#: never counted clean.  `''` covers extensionless files (Makefile, Dockerfile).
TEXTY = {".md", ".txt", ".json", ".tsv", ".csv", ".py", ".sh", ".ps1", ".yml",
         ".yaml", ".toml", ".c", ".h", ".S", ".java", ".log", ".timing",
         ".cfg", ".conf", ".ini", ".delta", ".config", ".patch", ".gitignore",
         ".gitattributes", ".gitmodules", ""}


#: 🔴 THE SPLIT, and it is the difference between a number and a finding.
#: `audit-bench-log.py`'s patterns were written for a DEVICE LOG, where the
#: string `calib` in the bytes means calibration data.  In PROSE those same
#: words are the subject matter -- this project writes `H601` in every other
#: paragraph.  Only four of the eight can identify one physical unit, and a
#: count that mixes the two answers no question.
#:
#: ⚠️ This is a property of the POPULATION, not of the patterns: on
#: `bench/**/*.log` the topic patterns are load-bearing and must stay.  The
#: split lives here, in the tool that scans prose, and not in the one that
#: scans transcripts.
IDENTITY = {"MAC, colon form", "MAC, dash form", "MAC, bare 12 hex",
            "serial-ish"}


def load_abl():
    ldr = importlib.machinery.SourceFileLoader("abl", ABL)
    spec = importlib.util.spec_from_loader("abl", ldr)
    m = importlib.util.module_from_spec(spec)
    ldr.exec_module(m)
    return m


def tracked(root):
    out = subprocess.run(["git", "-C", root, "ls-files"],
                         capture_output=True, text=True, encoding="utf-8")
    return [p for p in out.stdout.split("\n") if p.strip()]


def walk(root, rel):
    base = os.path.join(root, rel)
    got = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            got.append(os.path.relpath(full, root).replace(os.sep, "/"))
    return sorted(got)


def populations(root):
    """(name, [paths], why it has never been scanned)."""
    tr = tracked(root)
    bench_md = [p for p in tr if p.startswith("bench/") and p.endswith(".md")]
    other = [p for p in tr
             if not p.startswith("upstream")
             and p not in bench_md
             and not (p.startswith("bench/") and p.endswith(".log"))]
    up = walk(root, "upstream")
    return [
        ("bench/**/*.md", bench_md,
         "in the directory the CI gate is named for, and the gate globs *.log"),
        ("tracked, not bench/*.log", other,
         "SPEC/PROGRESS/LOG/RUNSHEET/notes/docs -- prose, where a reading is "
         "transcribed by hand"),
        ("upstream/ (submodule)", up,
         "git ls-files returns ONE line for the whole submodule, so every "
         "sweep built on it has read zero of these"),
    ]


def scan_population(abl, root, paths):
    """-> (findings, scanned, not_scanned_by_ext).  findings carry NO text."""
    findings = []
    scanned = 0
    skipped = {}
    for rel in paths:
        full = os.path.join(root, rel)
        ext = os.path.splitext(rel)[1].lower()
        if ext not in TEXTY:
            skipped[ext or "<none>"] = skipped.get(ext or "<none>", 0) + 1
            continue
        try:
            with io.open(full, encoding="utf-8", errors="strict",
                         newline="") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            skipped["<undecodable> " + (ext or "<none>")] = \
                skipped.get("<undecodable> " + (ext or "<none>"), 0) + 1
            continue
        scanned += 1
        for label, ln, txt, line in abl.scan(rel, text):
            if abl.allowed(txt, line):
                continue
            # NO `txt`, and no slice of `line`.  Length only.
            findings.append((rel, label, ln, len(txt)))
    return findings, scanned, skipped


def controls(abl):
    """Every control must pass before a single population is reported."""
    rows = []

    ctl = abl.scan("control", abl.CONTROL)
    fired = {h[0] for h in ctl}
    missing = [l for l, _ in abl.PATTERNS if l not in fired]
    rows.append(("L1 every imported pattern fires on the control",
                 not missing,
                 "%d/%d fired" % (len(fired), len(abl.PATTERNS))))

    swallowed = [h for h in ctl if abl.allowed(h[2], h[3])]
    rows.append(("L2 the allowlist swallows no control hit",
                 not swallowed, "%d swallowed" % len(swallowed)))

    probe = "addr 10.9.9.9 and mac 00:12:34:56:AA:BB\n"
    ph = [h for h in abl.scan("c", probe) if not abl.allowed(h[2], h[3])]
    rows.append(("L3 a non-allowlisted MAC and address still fire",
                 len(ph) >= 2, "%d hit(s)" % len(ph)))

    # L4 -- a population that is empty reports 0 and means nothing.  This is the
    # defect the whole file is about, one level up.
    pops = populations(ROOT)
    up = dict((n, p) for n, p, _ in pops)["upstream/ (submodule)"]
    rows.append(("L4 the upstream/ population is non-empty",
                 len(up) > 100, "%d file(s) walked from disk" % len(up)))

    # L5 -- THE control on this tool's own reason for existing: a finding must
    # not carry the bytes that produced it.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        secret = "00:E0:4C:AB:CD:EF"
        p = os.path.join(d, "fx.md")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("hwaddr %s here\n" % secret)
        f, n, _s = scan_population(abl, d, ["fx.md"])
        rendered = "\n".join(render(x) for x in f)
        ok5 = (len(f) >= 1 and n == 1 and secret not in rendered
               and "AB:CD" not in rendered)
        rows.append(("L5 a finding never carries the matched bytes",
                     ok5, "%d finding(s), %d char(s) rendered, secret absent=%s"
                     % (len(f), len(rendered), secret not in rendered)))

    # L6 -- and a binary is NOT counted clean.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "fx.jpg")
        with open(p, "wb") as fh:
            fh.write(b"\xff\xd8\xff\xe0" + b"\x00" * 64)
        f, n, s = scan_population(abl, d, ["fx.jpg"])
        rows.append(("L6 a binary is reported NOT SCANNED, not clean",
                     n == 0 and sum(s.values()) == 1 and not f,
                     "scanned=%d skipped=%s" % (n, s)))
    return rows


def render(f):
    rel, label, ln, n = f
    return "  %-52s %-22s line %-6d %d char(s)" % (rel, label, ln, n)


def main(argv):
    abl = load_abl()

    print("=== controls (they run first; nothing is reported if one fails) ===")
    rows = controls(abl)
    for name, ok, detail in rows:
        print("  %-5s %-50s %s" % ("ok" if ok else "FAIL", name, detail))
    bad = [r for r in rows if not r[1]]
    print("")
    if bad:
        print("REFUSED: %d control(s) failed. A clean population would mean "
              "nothing." % len(bad))
        return 2

    if "--self-test" in argv:
        print("RESULT: \033[32m%d passed, 0 failed\033[0m" % len(rows))
        return 0

    total = 0
    ident_total = 0
    for name, paths, why in populations(ROOT):
        findings, scanned, skipped = scan_population(abl, ROOT, paths)
        total += len(findings)
        ident_total += sum(1 for f in findings if f[1] in IDENTITY)
        print("=== %s ===" % name)
        print("  why nothing has scanned it: %s" % why)
        print("  %d file(s), %d scanned, %d finding(s)"
              % (len(paths), scanned, len(findings)))
        if skipped:
            n = sum(skipped.values())
            print("  🔴 NOT SCANNED: %d file(s) -- this is a TEXT scanner and "
                  "these are not text. They are not clean, they are unread:"
                  % n)
            for ext, k in sorted(skipped.items(), key=lambda kv: -kv[1]):
                print("       %-28s %d" % (ext, k))
        by_pat = {}
        for rel, label, ln, n in findings:
            by_pat.setdefault(label, []).append(rel)
        if by_pat:
            print("  per pattern:")
            for label in sorted(by_pat, key=lambda k: -len(by_pat[k])):
                where = by_pat[label]
                mark = " 🔴 IDENTITY" if label in IDENTITY else "    topic"
                print("   %s  %-22s %5d hit(s) in %d file(s)"
                      % (mark, label, len(where), len(set(where))))
        ident = [f for f in findings if f[1] in IDENTITY]
        if ident:
            print("  🔴 the %d IDENTITY hit(s), file and line only:" % len(ident))
            for f in ident:
                print(render(f))
        else:
            print("  🟢 0 hits on the four patterns that can name one unit "
                  "(MAC colon / dash / bare 12 hex / serial)")
        print("")

    if total:
        print("%d raw hit(s) across the three populations, %s of them on a "
              "pattern that can identify one unit." % (total, ident_total))
        print("The matched bytes are deliberately not printed; open the file "
              "at the line named.")
        return 1 if ident_total else 0
    print("\033[32m0 findings\033[0m in what could be read. That is not the "
          "same sentence as `no leak`: the NOT SCANNED counts above are the "
          "part this instrument cannot see.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
