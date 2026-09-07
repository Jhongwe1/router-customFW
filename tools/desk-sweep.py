#!/usr/bin/env python3
"""desk-sweep -- run every CI suite at this desk, on a VERIFIED COPY of the tree.

Two jobs, and they are separable:

    enumerate   list every `run:` step `.github/workflows/ci.yml` declares,
                parsed as YAML rather than matched as lines
    run         copy the tree somewhere, prove the copy is the tree, run every
                step in the copy, prove the tree did not move underneath, put
                the outputs back, delete the copy

Why the enumeration is a tool and not a `grep`
----------------------------------------------
Three measured failures, all of them in this repository's own record, all of
them from a sweep that reconstructed the step list instead of reading it:

* 量 2026-09-02: a sweep pulled each suite out of `ci.yml` with a regex that
  stopped at the `&` of `2>&1`.  All 48 invocations ran as `... 2>` and died in
  the shell, and it printed **46 FAIL lines indistinguishable from 46 failing
  suites**.
* 量 2026-09-02, the same hour: the corrected script grepped `^\\s+run: .*tools/`
  and silently dropped `verify-backup-copy`, whose step is a YAML **literal
  block** -- its `run:` line is just `|` and the command sits in the body.  46
  suites reported ok and the 47th was never invoked.  `ci-census` named it.
* 量 2026-09-06/07: the step count was wrong by two **since 2026-08-25**.
  `ci.yml:728` and `:733` are inline `- run:` forms, which `^\\s+run: ` cannot
  match, so every desk sweep for six weeks skipped the whole `lint` job.

A line-based enumerator cannot see a block, and a hand-written command splitter
cannot see its own quoting.  PyYAML sees both.  `--self-test`'s `C2` runs the
line-based enumerator against the same fixture and requires it to come out
SHORT, so the reason this file exists is a case rather than this paragraph.

Why the sweep runs on a copy
----------------------------
🔴 量 2026-09-07 (this repository's own defect, the morning of the same day):
`spec-check` sweeps **tracked** `.md` files.  A card was committed while the
desk sweep was mid-run.  The commit changed no file's *content* -- so it looked
safe -- but it changed which files are **tracked**, and that is exactly the
population `spec-check` reads.  The card was untracked when `spec-check` walked
the tree and tracked immediately after, so **neither state was ever swept**, and
the defect reached CI.

A sweep certifies the tree it saw.  Copying first makes "the tree it saw" a
thing that exists on disk and can be compared, instead of a moment that has
already passed.  It converts a silent corruption into a stated scope limit: the
copy is frozen, so a commit during the sweep no longer changes what ran -- it
only means the green certifies the copied tree rather than the current one, and
the end-of-run drift check says so out loud.

⚠️ **The copy does NOT protect the copy phase itself.**  A commit racing `cp -a`
can be captured half-applied; that is what the fidelity check is for, and it is
a refusal.

Why the destination filesystem is an argument
---------------------------------------------
量 2026-09-07, same CPU, same RAM, same kernel, only the filesystem changed --
`test-spec-check-mutants`, n=2 each:

    9p (/mnt/c)   44.25 / 45.10 s   186/189 % CPU   680,990 / 671,883 vol.ctxsw
    ext4          1.52 / 1.47 s      98/96 % CPU            13 / 11 vol.ctxsw

Process-state sampling read 159 S / 62 R / 18 D -- asleep, not computing -- and
the working set (35 MB) against measured memory bandwidth (1.5 GB/s) rules out
the memory-bandwidth explanation, which predicts the opposite signature.  The
bottleneck is the WSL<->Windows 9p file-system bridge.

⚠️ That is **one suite**, and an import-heavy one.  Nothing here extrapolates it
to the whole sweep: `--out` writes a per-step wall time so the ratio can be
measured per suite instead of assumed.  Two runs is also not a variance
measurement, and the 9p pair happening to agree within 2 % does not repeat the
+-15 % jitter seen on this suite before.

What this CANNOT do
-------------------
* **A step that names an absolute path into the source tree reads the source,
  not the copy.**  `run` greps every step's command for the source root and
  reports any hit before running.  It does not rewrite them.
* `$FWRE_WORK` is outside the copy, deliberately and by both arms, so suites
  that read it are reading the same ext4 files whichever destination is chosen.
  Their timings are not filesystem-sensitive in the way the others are.
* **This is not CI's wall clock.**  Steps run sequentially here; CI runs four
  jobs in parallel.  A total from this tool may never be compared with
  `citime`'s BIG3.
* It does not create the `dl/` artifact directory, so the two `census` steps
  stay red here by design.  They are declared, by name, below.

Exit codes
    0  every runnable step behaved as declared, the copy verified, no drift
    1  at least one step was an unexpected red, or the source drifted
    2  refused before running anything (copy did not verify, stale declaration)
"""
import argparse
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CI = os.path.join(".github", "workflows", "ci.yml")

# ---------------------------------------------------------------------------
# The declarations, and there are TWO KINDS because they are two different
# things.  The distinction was not designed; C10 fired on the first run after
# a step was inserted, and the fix is this split.
#
# A SAFETY RULE says "no step of this shape may run at a desk, whoever wrote it
# and whatever it is called".  It must be a PATTERN: a new `sudo` step added
# tomorrow has to be caught without anyone remembering to declare it, and a
# rule that only knows the steps it was told about is not a safety rule.
#
# An EXCUSE says "this particular red is fine here".  It must be BY NAME, with
# a control that the name still exists -- `flrbracket`'s A20 idiom -- or the
# allow-list can only grow.
#
# 🔴 The first version of this file made the safety rule an excuse, and named
# an unnamed step by its GLOBAL index.  Adding one step to an earlier job
# renamed `lint/#58` to `lint/#59` and the declaration went stale in the same
# minute it was written.  Unnamed steps are now numbered WITHIN their job, and
# nothing safety-critical depends on that number at all.
# ---------------------------------------------------------------------------

# A step that needs root or the network. Not an allow-list: a shape.
UNSAFE_RE = re.compile(r"(?:^|[\s;&|(])sudo\s")
UNSAFE_WHY = ("needs root: it installs packages, mutates this host and reaches "
              "the network.  On a runner the image is thrown away; this desk "
              "is the machine the bench captures live on")

# Steps that are red HERE and green on a runner, with the reason.  A red that
# is expected every single time trains a reader to ignore reds, so they are
# counted separately and an unexpected red is what sets the exit code.
EXPECT_RED = {
    ("census", "merge the captures"):
        "`cp dl/*/*.out` -- `dl/` is the GitHub artifact download directory and "
        "does not exist at a desk",
    ("census", "census"):
        "consumes what the step above could not produce; reports "
        "NOT-RUN-TOTAL MISMATCH because the two suites above it did not run",
}


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------

def enumerate_steps(ci_path):
    """Every `run:` step ci.yml declares, in file order, as dicts.

    Keys: index (1-based), job, name, cmd.  A step with no `name:` is given
    `#<index>` so that it can still be named in a declaration -- the two inline
    `- run:` steps in the `lint` job have no name, and being unnameable is how
    they stayed invisible.
    """
    import yaml
    with open(ci_path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    out, n = [], 0
    for job, body in (doc.get("jobs") or {}).items():
        within = 0
        for step in (body.get("steps") or []):
            if "run" not in step:
                continue
            n += 1
            within += 1
            out.append({
                "index": n,
                "job": job,
                # WITHIN the job, not globally: a global number is renamed by
                # inserting a step into any earlier job, which is how the
                # first version of this file went stale in one minute.
                "name": step.get("name") or f"#{within}",
                "cmd": step["run"],
            })
    return out


def enumerate_steps_linewise(ci_path):
    """The BROKEN enumerator, kept so C2 can require it to come out short.

    This is what every desk sweep did until 2026-09-07.  It is here as a
    control, never on a code path that runs anything.
    """
    out = []
    with open(ci_path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\s+run: (.*)$", line)
            if m:
                out.append(m.group(1))
    return out


def classify(step):
    if UNSAFE_RE.search(step["cmd"]):
        return "skip", UNSAFE_WHY
    key = (step["job"], step["name"])
    if key in EXPECT_RED:
        return "expect-red", EXPECT_RED[key]
    return "run", ""


def check_declarations(steps):
    """Complaints about the EXCUSES.  Two, in opposite directions.

    Without the first, `EXPECT_RED` is an allow-list that can only grow: rename
    a step and its excuse becomes a permanent unexplained skip.  Without the
    second, the safety rule could match nothing and its silence would be a
    claim that cannot fail.
    """
    live = {(s["job"], s["name"]) for s in steps}
    bad = []
    for key in EXPECT_RED:
        if key not in live:
            bad.append(f"EXPECT_RED names {key[0]}/{key[1]}, which ci.yml no "
                       f"longer has -- the excuse is stale")
    if steps and not any(UNSAFE_RE.search(s["cmd"]) for s in steps):
        bad.append("the safety rule matches NOTHING in this ci.yml.  Either "
                   "every root-needing step is gone -- in which case delete "
                   "the rule -- or the pattern has stopped matching and every "
                   "one of them is about to run at this desk")
    return bad


# ---------------------------------------------------------------------------
# The manifest, and what it deliberately does and does not compare
# ---------------------------------------------------------------------------

def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(root):
    """path -> fingerprint, for every file in the tree except under `.git/`.

    Three deliberate choices, each with a measured reason:

    * **`.git/` is fingerprinted by `HEAD` and `index` only**, not object by
      object.  Objects are content-addressed, and `index` is the file that
      decides `git ls-files` -- which is the population `spec-check` reads and
      the exact thing that went wrong on 2026-09-07.
    * **A symlink contributes its TARGET STRING, never the target's content.**
      `src-vendor` points into `$FWRE_WORK`; a verifier that followed it would
      hash 480 MB of vendor tree and would still pass if the link itself had
      been repointed.
    * **mtime is compared at 1-second granularity, and it is fatal.**
      `tools/check-predictions.py` decides "the prediction was written first"
      by mtime, so a copy that loses mtimes is not this tree.  One second
      rather than exact because the two filesystems do not agree on timestamp
      resolution and the ordering that matters is seconds apart.
    * **Permission bits are compared only for the executable bit.**  DrvFs
      reports every file as 777 (that is why `core.fileMode=false` here), so a
      full mode comparison would be a comparison of two lies.
    """
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel == ".git" or rel.startswith(".git" + os.sep):
            dirnames[:] = []
            continue
        if ".git" in dirnames:
            dirnames.remove(".git")
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            key = os.path.relpath(full, root).replace(os.sep, "/")
            st = os.lstat(full)
            if stat.S_ISLNK(st.st_mode):
                out[key] = ("symlink", os.readlink(full), 0, 0)
                continue
            out[key] = (
                _sha256_file(full),
                "",
                int(st.st_mtime),
                1 if (st.st_mode & 0o111) else 0,
            )
    for special in (".git/HEAD", ".git/index"):
        p = os.path.join(root, *special.split("/"))
        if os.path.exists(p):
            out[special] = (_sha256_file(p), "", 0, 0)
    return out


def compare(a, b, limit=12):
    """Differences between two manifests, as human sentences."""
    diffs = []
    for k in sorted(set(a) | set(b)):
        if k not in b:
            diffs.append(f"missing from copy: {k}")
        elif k not in a:
            diffs.append(f"present only in copy: {k}")
        elif a[k] != b[k]:
            why = []
            if a[k][0] != b[k][0] or a[k][1] != b[k][1]:
                why.append("content")
            if a[k][2] != b[k][2]:
                why.append(f"mtime {a[k][2]} vs {b[k][2]}")
            if a[k][3] != b[k][3]:
                why.append("executable bit")
            diffs.append(f"differs ({', '.join(why)}): {k}")
        if len(diffs) > limit:
            diffs.append(f"... and more; stopped at {limit}")
            break
    return diffs


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def do_run(args):
    src = ROOT
    ci_path = os.path.join(src, CI)
    steps = enumerate_steps(ci_path)
    print(f"== ci.yml declares {len(steps)} `run:` step(s)")

    stale = check_declarations(steps)
    if stale:
        for s in stale:
            print(f"REFUSED: {s}")
        return 2

    # A step naming the source root reads the source, not the copy.
    leaks = [s for s in steps if src in s["cmd"]]
    for s in leaks:
        print(f"⚠️  {s['job']}/{s['name']} names the source root literally -- "
              f"it will read the SOURCE, not the copy")

    dest = os.path.abspath(args.dest)
    if os.path.exists(dest):
        if not args.force:
            print(f"REFUSED: {dest} exists.  Pass --force to replace it, so "
                  f"that deleting a directory is never implicit")
            return 2
        shutil.rmtree(dest)

    t0 = time.time()
    print(f"== fingerprinting source {src}")
    m_src = manifest(src)
    t_hash_src = time.time() - t0
    print(f"   {len(m_src)} entries in {t_hash_src:.1f} s")

    t0 = time.time()
    print(f"== copying to {dest}")
    os.makedirs(dest, exist_ok=True)
    rc = subprocess.call(["cp", "-a", src + "/.", dest + "/"])
    t_copy = time.time() - t0
    if rc != 0:
        print(f"REFUSED: cp -a exited {rc}")
        return 2
    print(f"   copied in {t_copy:.1f} s")

    t0 = time.time()
    print("== verifying the copy")
    m_dst = manifest(dest)
    t_hash_dst = time.time() - t0
    diffs = compare(m_src, m_dst)
    if diffs:
        print(f"🔴 REFUSED: the copy is not the source -- {len(diffs)} "
              f"difference(s).  The sweep does not run.")
        for d in diffs:
            print(f"   {d}")
        if not args.keep:
            shutil.rmtree(dest, ignore_errors=True)
        return 2
    print(f"   {len(m_dst)} entries verified in {t_hash_dst:.1f} s -- "
          f"the copy IS the source")

    rows, unexpected, ran, green, expected_red, skipped = [], [], 0, 0, 0, 0
    t_sweep0 = time.time()
    for s in steps:
        kind, why = classify(s)
        if kind == "skip":
            skipped += 1
            print(f"[{s['index']:3d}/{len(steps)}] SKIP  {s['job']}/{s['name']}"
                  f"  ({why[:60]})")
            rows.append((s, "skip", None, 0.0))
            continue
        if args.only and s["name"] not in args.only:
            skipped += 1
            rows.append((s, "not-selected", None, 0.0))
            continue
        t = time.time()
        proc = subprocess.run(["bash", "-c", s["cmd"]], cwd=dest,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dt = time.time() - t
        ran += 1
        rc = proc.returncode
        if kind == "expect-red":
            expected_red += 1
            verdict = "expected-red" if rc != 0 else "UNEXPECTED-GREEN"
            if rc == 0:
                unexpected.append((s, rc, "declared red here and came out green"))
        elif rc == 0:
            green += 1
            verdict = "ok"
        else:
            verdict = "RED"
            unexpected.append((s, rc, "unexpected red"))
        print(f"[{s['index']:3d}/{len(steps)}] {verdict:16s} "
              f"{dt:8.2f}s  {s['job']}/{s['name']}")
        if verdict in ("RED", "UNEXPECTED-GREEN"):
            tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()
            for line in tail[-8:]:
                print(f"        | {line}")
        rows.append((s, verdict, rc, dt))
    t_sweep = time.time() - t_sweep0

    print("== re-fingerprinting the source")
    m_src2 = manifest(src)
    drift = compare(m_src, m_src2)

    # Put the outputs where the reader expects them, from the copy.
    out_src = os.path.join(dest, "ci-out")
    if os.path.isdir(out_src):
        out_dst = os.path.join(src, "ci-out")
        os.makedirs(out_dst, exist_ok=True)
        for fn in os.listdir(out_src):
            f = os.path.join(out_src, fn)
            if os.path.isfile(f):
                shutil.copy2(f, os.path.join(out_dst, fn))
        print(f"== ci-out/ copied back ({len(os.listdir(out_src))} file(s))")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("tag\tdest\tindex\tjob\tstep\tverdict\trc\tseconds\n")
            for s, verdict, rc, dt in rows:
                fh.write(f"{args.tag}\t{dest}\t{s['index']}\t{s['job']}\t"
                         f"{s['name']}\t{verdict}\t"
                         f"{'' if rc is None else rc}\t{dt:.3f}\n")
            fh.write(f"#phase\t{args.tag}\thash_src\t{t_hash_src:.3f}\n")
            fh.write(f"#phase\t{args.tag}\tcopy\t{t_copy:.3f}\n")
            fh.write(f"#phase\t{args.tag}\thash_dst\t{t_hash_dst:.3f}\n")
            fh.write(f"#phase\t{args.tag}\tsweep\t{t_sweep:.3f}\n")
        print(f"== timings written to {args.out}")

    if not args.keep:
        shutil.rmtree(dest, ignore_errors=True)
        print(f"== copy deleted")
    else:
        print(f"== copy KEPT at {dest}")

    print()
    print(f"  {len(steps)} declared, {skipped} skipped, {ran} ran, "
          f"{green} green, {expected_red} expected-red, "
          f"{len(unexpected)} unexpected")
    print(f"  copy {t_copy:.1f}s + verify {t_hash_src + t_hash_dst:.1f}s + "
          f"sweep {t_sweep:.1f}s")

    rc = 0
    for s, code, why in unexpected:
        print(f"  🔴 {s['job']}/{s['name']}: {why} (rc={code})")
        rc = 1
    if drift:
        print(f"  🔴 THE SOURCE MOVED WHILE THE SWEEP RAN -- "
              f"{len(drift)} difference(s).  This green certifies the tree "
              f"that was COPIED, not the tree on disk now.")
        for d in drift:
            print(f"     {d}")
        if not args.allow_drift:
            rc = 1
    else:
        print(f"  ok  the source did not move: this verdict is about the "
              f"tree on disk now")
    return rc


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

FIXTURE = """\
name: fixture
jobs:
  a:
    steps:
      - uses: actions/checkout@v4
      - name: plain
        run: echo plain
      - run: echo inline
      - name: block
        run: |
          echo one
          echo two
  b:
    steps:
      - name: second job
        run: echo b
      - run: sudo apt-get install -y -qq something
"""


def self_test():
    fails = []

    def ck(cid, cond, msg):
        print(f"  {'ok  ' if cond else 'FAIL'} {cid} {msg}")
        if not cond:
            fails.append(cid)

    tmp = tempfile.mkdtemp(prefix="desksweep-")
    try:
        fx = os.path.join(tmp, "ci.yml")
        with open(fx, "w", encoding="utf-8") as fh:
            fh.write(FIXTURE)

        steps = enumerate_steps(fx)
        ck("C1", len(steps) == 5,
           f"all three step shapes are found (plain, inline `- run:`, literal "
           f"block) across two jobs: got {len(steps)}, want 5")
        ck("C1b", steps[1]["name"] == "#2",
           "an unnamed inline step is nameable, as #<position WITHIN its job>")
        ck("C1c", steps[2]["cmd"].strip().endswith("echo two"),
           "a literal block's whole body is taken, not its first line")
        ck("C1d", steps[4]["name"] == "#2" and steps[4]["job"] == "b",
           "and that number is per-job: the second job's unnamed step is #2, "
           "not #5 -- a global number is renamed by an insert anywhere before "
           "it, which is how the first version of this file went stale")

        kinds = [classify(s)[0] for s in steps]
        ck("C12", kinds.count("skip") == 1 and kinds[4] == "skip",
           "THE SAFETY RULE, positive: the one step needing root is refused")
        ck("C13", kinds[:4] == ["run"] * 4,
           "THE SAFETY RULE, negative: the four that do not need root are not "
           "refused -- a rule that skipped everything would also 'pass' C12")

        line = enumerate_steps_linewise(fx)
        ck("C2", len(line) < len(steps),
           f"THE POSITIVE CONTROL ON C1: the line-based enumerator every desk "
           f"sweep used until today comes out SHORT ({len(line)} of "
           f"{len(steps)}) on the same fixture")

        # A tree to copy, with the two shapes that break naive verifiers.
        s = os.path.join(tmp, "src")
        os.makedirs(os.path.join(s, "sub"))
        with open(os.path.join(s, "a.txt"), "w") as fh:
            fh.write("hello\n")
        with open(os.path.join(s, "sub", "b.txt"), "w") as fh:
            fh.write("world\n")
        os.chmod(os.path.join(s, "a.txt"), 0o755)
        os.symlink("/nonexistent/target", os.path.join(s, "link"))
        old = time.time() - 90000
        os.utime(os.path.join(s, "sub", "b.txt"), (old, old))

        def fresh_copy():
            d = tempfile.mkdtemp(prefix="desksweep-dst-")
            shutil.rmtree(d)
            subprocess.check_call(["cp", "-a", s, d])
            return d

        d = fresh_copy()
        ck("C7", not compare(manifest(s), manifest(d)),
           "THE NEGATIVE CONTROL: a clean `cp -a` verifies, so the verifier "
           "does not simply fire on everything")
        ck("C11", int(os.lstat(os.path.join(d, "sub", "b.txt")).st_mtime)
           == int(old),
           "`cp -a` preserves mtime -- check-predictions reads mtimes, so a "
           "copy that lost them would not be this tree")

        with open(os.path.join(d, "a.txt"), "w") as fh:
            fh.write("hellp\n")
        ck("C3", compare(manifest(s), manifest(d)),
           "THE POSITIVE CONTROL ON THE VERIFIER: one byte changed in the copy "
           "is caught")

        d = fresh_copy()
        with open(os.path.join(d, "extra.txt"), "w") as fh:
            fh.write("x\n")
        ck("C4", compare(manifest(s), manifest(d)),
           "a file present only in the copy is caught")

        d = fresh_copy()
        os.remove(os.path.join(d, "sub", "b.txt"))
        ck("C5", compare(manifest(s), manifest(d)),
           "a file missing from the copy is caught")

        d = fresh_copy()
        os.remove(os.path.join(d, "link"))
        os.symlink("/somewhere/else", os.path.join(d, "link"))
        ck("C6", compare(manifest(s), manifest(d)),
           "a symlink REPOINTED is caught -- a verifier that followed links "
           "would hash the same missing target twice and pass")

        d = fresh_copy()
        os.chmod(os.path.join(d, "a.txt"), 0o644)
        ck("C6b", compare(manifest(s), manifest(d)),
           "the executable bit is compared (DrvFs makes a full mode "
           "comparison meaningless, this one is not)")

        d = fresh_copy()
        os.utime(os.path.join(d, "sub", "b.txt"), (time.time(), time.time()))
        ck("C8", compare(manifest(s), manifest(d)),
           "an mtime moved by a day is caught")

        d = fresh_copy()
        p = os.path.join(d, "sub", "b.txt")
        # int() + 0.4, not st_mtime + 0.4: adding to an arbitrary fraction can
        # cross a whole second, which is a DIFFERENT case and would be caught.
        whole = float(int(os.lstat(p).st_mtime))
        os.utime(p, (whole + 0.4, whole + 0.4))
        ck("C8b", not compare(manifest(s), manifest(d)),
           "a sub-second mtime difference is NOT caught -- deliberate: the two "
           "filesystems disagree on resolution and the ordering that matters "
           "is seconds apart")

        live = os.path.join(ROOT, CI)
        if os.path.exists(live):
            real = enumerate_steps(live)
            ck("C9", len(real) >= 40,
               f"POPULATION CONTROL: the live ci.yml parses and has "
               f"{len(real)} run steps, so C10 is checking something")
            ck("C10", not check_declarations(real),
               "every EXPECT_RED name still exists in ci.yml, and the safety "
               "rule still matches at least one live step -- an excuse cannot "
               "accrete unreported and a dead safety rule cannot stay silent")
            ck("C10b",
               sum(1 for s in real if classify(s)[0] == "skip") >= 1,
               f"POPULATION CONTROL on the safety rule: it refuses "
               f"{sum(1 for s in real if classify(s)[0] == 'skip')} live "
               f"step(s), so its verdict on this file is not vacuous")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for d in os.listdir(tempfile.gettempdir()):
            if d.startswith("desksweep-dst-"):
                shutil.rmtree(os.path.join(tempfile.gettempdir(), d),
                              ignore_errors=True)

    print()
    if fails:
        print(f"  {len(fails)} control(s) failed: {', '.join(fails)}")
        return 1
    print("  all controls pass")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", nargs="?", choices=["enumerate", "run"])
    ap.add_argument("--dest", help="where the copy goes; its filesystem is "
                                   "the thing being chosen")
    ap.add_argument("--out", help="per-step timing TSV")
    ap.add_argument("--tag", default="sweep", help="label for the TSV rows")
    ap.add_argument("--only", help="comma-separated step names to run")
    ap.add_argument("--keep", action="store_true", help="do not delete the copy")
    ap.add_argument("--force", action="store_true",
                    help="replace --dest if it exists")
    ap.add_argument("--allow-drift", action="store_true",
                    help="the source moving during the sweep is reported but "
                         "does not set the exit code (timing runs)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        print("desk-sweep controls")
        return self_test()
    if args.mode == "enumerate":
        steps = enumerate_steps(os.path.join(ROOT, CI))
        for s in steps:
            kind, why = classify(s)
            one = s["cmd"].strip().replace("\n", " ¶ ")
            print(f"{s['index']:3d}  {kind:10s}  {s['job']:12s}  "
                  f"{s['name']:36s}  {one[:80]}")
        print(f"\n  {len(steps)} run step(s)")
        for c in check_declarations(steps):
            print(f"  🔴 {c}")
        return 0
    if args.mode == "run":
        if not args.dest:
            print("REFUSED: run needs --dest.  The destination's filesystem is "
                  "the whole point; there is no default.")
            return 2
        args.only = set(args.only.split(",")) if args.only else None
        return do_run(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
