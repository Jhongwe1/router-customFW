#!/usr/bin/env python3
"""replay-capture -- turn a committed capture back into the terminal it came from.

`console-capture.py` writes a `.timing` sidecar beside every `.log`: one
`offset seconds` record per read, where **offset is the byte count in the `.log`
BEFORE this read** (讀, `console-capture.py`'s own header line and the order of
its `timing.write` / `offset +=` pair).  `scriptreplay(1)` wants the mirror
image -- `delay count`, seconds since the previous record and bytes to emit --
so converting one to the other is arithmetic:

    delay[i] = seconds[i] - seconds[i-1]        (delay[0] = seconds[0])
    count[i] = offset[i+1] - offset[i]          (last: len(.log) - offset[-1])

Why this is better than a screen recording
------------------------------------------
🟢 **It makes the artefact reproducible instead of merely recorded.**  Anyone
who clones this repository has the `.log` and the `.timing`; the replay is
derived from them, at the true wire speed, byte for byte.  There is no dead
`--seconds` tail, no font locked into a video file, and nothing that has to be
taken on trust about what the terminal showed.

🟢 **And it can be cross-validated, which a recording cannot.**  量 2026-08-31:
`bench/2026-08-31/W-3.log`, `bench/2026-08-31b/X-3.log` and
`bench/2026-08-30c/V-3.log` are **byte-identical** -- 849 bytes, sha256
`8317e7c9…` -- across two power cycles and two days.  So three independent
captures must produce **identical typescripts and different timing files**, and
`R4` asserts both halves.  A tool that produced identical timing would be
ignoring its input; one that produced different data would be corrupting it.

What this does NOT do
---------------------
* ⚠️ **`tool_version` in `console-capture.py` does not move for this, and must
  not.** That field's contract is *what the instrument wrote to the port*, and a
  replay writes nothing to any port.  This is a separate file for that reason,
  not a mode of the one instrument every seating runs through.
* A replay is not evidence about the device.  It is a rendering of evidence
  already committed, and the `.log` remains the artefact.
* `.timing` records when a **read** completed, not when a byte arrived.  A
  chunk of 20 bytes is emitted as one burst at one instant, because that is all
  the capture knows.  At 38400 8N1 the true spacing inside a burst is 260 µs a
  byte; the replay is faithful to the reads, not to the wire.  ⚠️ **This is why
  the replay looks slightly "chunkier" than the board did**, and it is a
  property of the original capture rather than of this conversion.

Run:  /usr/bin/python3 tools/replay-capture.py --self-test
      /usr/bin/python3 tools/replay-capture.py build bench/2026-08-31/W-3 \\
          --out $FWRE_WORK/rebuild/reel
      /usr/bin/python3 tools/replay-capture.py verify bench/2026-08-31/W-3
      /usr/bin/python3 tools/replay-capture.py play  bench/2026-08-31/W-3 [--speed 1.0]
      /usr/bin/python3 tools/replay-capture.py reel  config/r3-11-reel.tsv
      /usr/bin/python3 tools/replay-capture.py reel  config/r3-11-reel.tsv --budget

Exit codes:  0 ok · 1 a check failed · 2 refused before doing anything
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 量 2026-08-31: `scriptreplay` treats the FIRST LINE of the typescript as
# `script(1)`'s "Script started on ..." banner and does not emit it.  A file
# without one loses its first line of real output, silently.  Measured on
# util-linux 2.39.3 with an eight-byte payload: without a header the replay
# emitted 1 byte, with one it emitted all 8.
TYPESCRIPT_HEADER = (
    b"Script started -- rlxfw replay of a committed capture, "
    b"tools/replay-capture.py\n")


# 🔴 THE SKIP LABEL IS ONE VARIABLE USED THREE TIMES: printed by `R12`, checked
# by `R14` against `tools/ci-expected.tsv`, and read by `tools/ci-census.py` on
# the runner.  量 2026-08-30, CI run 33310864156: `test-kbuild-cflags` was 9/9
# green on the bench and red on the runner because its printed label and the
# table's column had drifted -- and the bench cannot see that class at all,
# because on this machine the case RUNS and its label is never compared.
# 🔄 As of 2026-08-31 this makes FOUR of the SEVENTEEN suites that declare an
# allowed skip actually assert their own label.  ⚠️ The denominator moved because
# THIS suite added one -- a session that raises the numerator and leaves the
# denominator alone reports progress it did not make, and the owner audit caught
# exactly that here.  量 by counting distinct suite names in the allowed-skip
# column: 21 rows, 17 suites (three of them declare more than one skip).
SKIP_LABEL = "R12 the round trip through scriptreplay"

# 🔴 `plan/ARTIFACTS.md` §2 asks for a **v0.2 短版, 60 s, no narration**.  That
# is a CEILING on a viewer's attention and not a floor the artefact has to
# reach -- `PROGRESS.md`'s `R3-11` row says so, and it says it because the
# repair for a short reel is more capture and never more dead terminal.  `R16`
# is the case that fires when an edit crosses the ceiling, which is the
# direction nothing was watching.  `plan/` is gitignored, so the number is
# copied here with its source named rather than read from it.
REEL_CEILING_S = 60.0
REEL = "config/r3-11-reel.tsv"


class Refuse(Exception):
    pass


def read_timing(path):
    """-> [(offset, seconds)], refusing anything it cannot parse."""
    out = []
    with open(path, "r", encoding="ascii") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                raise Refuse(f"{path}:{n}: want `offset seconds`, got {line!r}")
            try:
                out.append((int(parts[0]), float(parts[1])))
            except ValueError:
                raise Refuse(f"{path}:{n}: unparseable: {line!r}")
    if not out:
        raise Refuse(f"{path} holds no records -- a capture whose timing is "
                     f"empty replays as nothing, and reporting success on it "
                     f"would be a false clean")
    return out


def convert(prefix):
    """-> (records, logbytes).  records are (delay, count) for scriptreplay."""
    log_path, tim_path = prefix + ".log", prefix + ".timing"
    for p in (log_path, tim_path):
        if not os.path.exists(p):
            raise Refuse(f"{p} does not exist -- a replay needs BOTH the .log "
                         f"and the .timing, and a capture killed by SIGTERM "
                         f"keeps them while losing only .meta.json")
    with open(log_path, "rb") as f:
        blob = f.read()
    tim = read_timing(tim_path)

    offs = [o for o, _ in tim]
    if offs[0] != 0:
        raise Refuse(f"{tim_path}: first offset is {offs[0]}, not 0 -- the "
                     f"first read cannot start part way into the log")
    for i in range(1, len(offs)):
        if offs[i] < offs[i - 1]:
            raise Refuse(f"{tim_path}: offset goes backwards at record {i} "
                         f"({offs[i - 1]} then {offs[i]})")
        if tim[i][1] < tim[i - 1][1]:
            raise Refuse(f"{tim_path}: time goes backwards at record {i} "
                         f"({tim[i-1][1]} then {tim[i][1]}) -- monotonic() "
                         f"cannot do that, so the file has been edited")
    if offs[-1] > len(blob):
        raise Refuse(f"{tim_path}: last offset {offs[-1]} is past the end of "
                     f"{log_path} ({len(blob)} bytes)")

    recs, prev_t = [], 0.0
    for i, (off, t) in enumerate(tim):
        nxt = offs[i + 1] if i + 1 < len(tim) else len(blob)
        recs.append((t - prev_t, nxt - off))
        prev_t = t

    # 🔴 AN INVARIANT ASSERTION, NOT A GUARD, and the difference is written
    # down because a mutation suite found it.  Given the three checks above --
    # `offs[0] == 0`, offsets non-decreasing, `offs[-1] <= len(blob)` -- the
    # counts TELESCOPE: sum(offs[i+1] - offs[i]) + (len - offs[-1]) is exactly
    # len(blob) - offs[0] = len(blob), for every input that reaches here.  So no
    # `.timing` file can make this fire, and deleting it changes nothing that
    # any control can observe.  量: `test-replay-capture-mutants.py` M4
    # survived every one of the sixteen, which is what proved it.
    #
    # It stays, marked, for the reason a `_Static_assert` stays: it is the
    # statement of what the loop above is FOR, and if any of the three checks
    # is ever relaxed it becomes reachable in the same edit.  M4 is recorded as
    # EQUIVALENT rather than as a control gap, with this paragraph as the proof.
    total = sum(c for _, c in recs)
    if total != len(blob):
        raise Refuse(f"the records account for {total} bytes and {log_path} "
                     f"is {len(blob)} -- the conversion is wrong, and a replay "
                     f"that emits the wrong number of bytes is not a rendering "
                     f"of this capture")
    return recs, blob


def build(prefix, outdir):
    recs, blob = convert(prefix)
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.basename(prefix)
    tpath = os.path.join(outdir, stem + ".replay.timing")
    dpath = os.path.join(outdir, stem + ".replay.typescript")
    with open(tpath + ".tmp", "w", encoding="ascii", newline="\n") as f:
        for d, c in recs:
            f.write(f"{d:.6f} {c}\n")
    os.replace(tpath + ".tmp", tpath)
    with open(dpath + ".tmp", "wb") as f:
        f.write(TYPESCRIPT_HEADER)
        f.write(blob)
    os.replace(dpath + ".tmp", dpath)
    return tpath, dpath, recs, blob


def play(prefix, speed=1.0, outdir=None):
    if shutil.which("scriptreplay") is None:
        raise Refuse("scriptreplay(1) is not on PATH -- it is util-linux, and "
                     "`build` still works without it")
    outdir = outdir or os.environ.get("FWRE_WORK", "/tmp") + "/rebuild/reel"
    tpath, dpath, _, _ = build(prefix, outdir)
    cmd = ["scriptreplay", "--divisor", str(speed), tpath, dpath]
    return subprocess.call(cmd)


def replay_bytes(tpath, dpath, divisor=10000.0):
    """Run scriptreplay and return what it emitted.  The end-to-end control."""
    r = subprocess.run(["scriptreplay", "--divisor", str(divisor),
                        tpath, dpath], capture_output=True)
    return r.stdout


# --------------------------------------------------------------------------


def run_controls():
    import hashlib
    import tempfile
    ok = True

    def row(tag, name, good, detail):
        nonlocal ok
        ok = ok and good
        print(f"  {'ok  ' if good else 'FAIL'}  {tag} {name:<52} {detail}")

    W3 = os.path.join(ROOT, "bench/2026-08-31/W-3")
    X3 = os.path.join(ROOT, "bench/2026-08-31b/X-3")
    V3 = os.path.join(ROOT, "bench/2026-08-30c/V-3")

    # R0 -- the population.  Every control below runs on these three captures;
    # if they are not there, the rest of this list is vacuous.
    have = [p for p in (W3, X3, V3) if os.path.exists(p + ".log")]
    row("R0", "the three committed captures are present", len(have) == 3,
        f"{len(have)} of 3")
    if len(have) != 3:
        print()
        return 1

    # 🔴 EVERY CONTROL BELOW REPORTS RATHER THAN RAISING, and that changed on
    # 2026-08-31 (twentieth) because the mutation suite's new `W0` measured
    # what the old shape was worth.  Five of the fourteen mutations then in
    # `test-replay-capture-mutants.py` were counted as kills on `rc != 0`
    # alone, and every one of the five turned NO case red: they replaced a
    # `Refuse` with an IndexError or a FileNotFoundError, the `except Refuse`
    # did not catch it, and the whole self-test died on a traceback before it
    # printed anything.  A suite that dies tells you about one problem; one
    # that reports tells you about all of them, and only the second can say
    # WHICH control failed.  `except Exception` with the message assertion
    # kept is what makes the difference -- a wrong exception type fails the
    # needle and the case goes red under its own name.
    def broke(e):
        return f"{type(e).__name__}: {e}"[:66]

    try:
        recs, blob = convert(W3)
        tim = read_timing(W3 + ".timing")
        row("R1", "the records account for every byte of the .log",
            sum(c for _, c in recs) == len(blob),
            f"{len(recs)} record(s), {sum(c for _, c in recs)} of "
            f"{len(blob)} bytes")
        row("R2", "one record per .timing line", len(recs) == len(tim),
            f"{len(recs)}")
        row("R3", "the delays sum to the last timestamp",
            abs(sum(d for d, _ in recs) - tim[-1][1]) < 1e-6,
            f"sum {sum(d for d, _ in recs):.6f} s, "
            f"last stamp {tim[-1][1]:.6f} s")
    except Exception as e:                                  # noqa: BLE001
        for tag, name in (("R1", "the records account for every byte of the .log"),
                          ("R2", "one record per .timing line"),
                          ("R3", "the delays sum to the last timestamp")):
            row(tag, name, False, f"reading W-3 raised {broke(e)}")

    # R4 -- 🔴 THE CROSS-VALIDATION, and it is the reason these three captures
    # were chosen.  Identical data, different timing: both halves are asserted,
    # because a tool that ignored its timing input would pass the first half
    # and a tool that corrupted its data would pass the second.
    try:
        blobs, tims = [], []
        for p in (W3, X3, V3):
            r, b = convert(p)
            blobs.append(hashlib.sha256(b).hexdigest())
            tims.append(tuple(round(d, 6) for d, _ in r))
        row("R4a", "three independent captures give IDENTICAL data",
            len(set(blobs)) == 1, f"sha256 {blobs[0][:16]}… x3")
        row("R4b", "and DIFFERENT timing", len(set(tims)) == 3,
            f"{len(set(tims))} distinct delay sequence(s) over "
            f"{[len(t) for t in tims]} record(s)")
    except Exception as e:                                  # noqa: BLE001
        row("R4a", "three independent captures give IDENTICAL data", False,
            f"raised {broke(e)}")
        row("R4b", "and DIFFERENT timing", False, "not reached")

    # R5..R8 -- the refusals.  Each is a file this control writes.
    with tempfile.TemporaryDirectory() as d:
        def mk(name, timing_text, data=b"hello world"):
            p = os.path.join(d, name)
            open(p + ".log", "wb").write(data)
            open(p + ".timing", "w").write(timing_text)
            return p

        for tag, name, text, needle in (
            ("R5", "a last offset past the end of the .log is refused",
             "0 0.1\n99 0.2\n", "past the end"),
            ("R6", "time going backwards is refused",
             "0 0.5\n4 0.1\n", "time goes backwards"),
            ("R7", "an offset going backwards is refused",
             "0 0.1\n8 0.2\n4 0.3\n", "offset goes backwards"),
            ("R8", "an empty .timing is refused",
             "# only a header\n", "no records"),
            ("R9", "a first offset that is not 0 is refused",
             "4 0.1\n", "not 0"),
            # Two shapes, because they take different branches and the first
            # version of R10 used a one-token line while asserting on the
            # two-token message -- a control that failed for the right reason
            # and the wrong assertion.
            ("R10", "a line with the wrong field count is refused",
             "0 0.1\nnonsense\n", "want `offset seconds`"),
            ("R10b", "a line whose numbers do not parse is refused",
             "0 0.1\n8 later\n", "unparseable"),
        ):
            p = mk(tag, text)
            try:
                convert(p)
                row(tag, name, False, "it was accepted")
            except Exception as e:                          # noqa: BLE001
                # NOT `except Refuse`.  A mutation that turns this refusal
                # into an IndexError or a FileNotFoundError must make THIS
                # case red rather than kill the whole run -- see the W0
                # paragraph above R1.  The needle is what separates the two:
                # a refusal names its reason and a crash does not.
                row(tag, name, needle in str(e),
                    str(e)[:46] if isinstance(e, Refuse) else broke(e))

        # R11 -- a MISSING sidecar refuses rather than replaying the .log at
        # full speed, which would look like a successful replay of a boot that
        # took no time.
        p = os.path.join(d, "lonely")
        open(p + ".log", "wb").write(b"x")
        try:
            convert(p)
            row("R11", "a .log with no .timing is refused", False, "accepted")
        except Exception as e:                              # noqa: BLE001
            row("R11", "a .log with no .timing is refused",
                "does not exist" in str(e),
                str(e)[:46] if isinstance(e, Refuse) else broke(e))

        # R12 -- 🔴 THE END-TO-END CONTROL, through scriptreplay itself.
        # Everything above checks this tool's arithmetic against this tool's
        # reading of the format.  This one hands the pair to the program that
        # will actually consume it and compares what came out against the .log,
        # byte for byte.  If scriptreplay is absent the case says so and is
        # SKIPPED rather than passed -- an absent consumer is not a green one.
        if shutil.which("scriptreplay") is None:
            print(f"  skip  {SKIP_LABEL}   scriptreplay(1) not on PATH")
        else:
            tpath, dpath, _, want = build(W3, os.path.join(d, "out"))
            got = replay_bytes(tpath, dpath)
            # scriptreplay appends one newline of its own when the stream does
            # not end in one; compare on the prefix and say so.
            row("R12", "the round trip through scriptreplay is byte-exact",
                got.startswith(want),
                f"{len(want)} byte(s) in, {len(got)} out"
                + ("" if len(got) == len(want)
                   else f" (+{len(got) - len(want)} scriptreplay's own)"))

            # R13 -- and the header is load-bearing.  量 2026-08-31: without it
            # scriptreplay eats the first line of real output and says nothing.
            bad = os.path.join(d, "noheader.typescript")
            open(bad, "wb").write(want)
            got2 = replay_bytes(tpath, bad)
            row("R13", "without the header the replay LOSES data",
                not got2.startswith(want),
                f"{len(got2)} byte(s) out of {len(want)} -- "
                f"scriptreplay treats line 1 as script(1)'s banner")

    # R14 -- the skip label this file PRINTS must be the one
    # `tools/ci-expected.tsv` allows.  Only three suites did this before today,
    # and the one time it drifted the bench was green and CI was red.
    tsv = os.path.join(ROOT, "tools/ci-expected.tsv")
    want_lbl, found = None, False
    try:
        with open(tsv, encoding="utf-8") as f:
            for line in f:
                c = line.rstrip("\n").split("\t")
                if c and c[0] == "replay-capture":
                    found, want_lbl = True, (c[2] if len(c) > 2 else "")
    except OSError as e:
        want_lbl = f"<{e}>"
    row("R14", "the printed skip label is the one ci-expected allows",
        found and want_lbl == SKIP_LABEL,
        f"prints {SKIP_LABEL!r}; table says {want_lbl!r}"
        if found else "no `replay-capture` row in ci-expected.tsv")

    # --- R15..R18 -- the reel itself -------------------------------------
    # 🔴 Until 2026-08-31 (twentieth) NOTHING read `config/r3-11-reel.tsv`.
    # Its running time lived in a comment inside it and in a sentence in
    # `PROGRESS.md`, and a renamed capture would have been found by the
    # recorder rather than by a suite.  These six are the fix.  R15b is the
    # NEGATIVE side of R15 and R17/R17b are population controls, and both
    # exist because R15 and R16 pass on a one-row file of valid segments --
    # 量, by writing the mutations first: M16, M17 and M19 are killed by
    # nothing else.
    with tempfile.TemporaryDirectory() as d:
        def mkreel(name, text):
            q = os.path.join(d, name)
            with open(q, "w", encoding="utf-8") as f:
                f.write(text)
            return os.path.relpath(q, ROOT)

        try:
            segs, cap, pau, total = reel_budget(REEL)
            row("R15", "every segment of the reel exists and converts", True,
                f"{len(segs)} segment(s), "
                f"{sum(s[4] for s in segs)} byte(s), {cap:.3f} s of capture")
        except Exception as e:                              # noqa: BLE001
            segs = None
            row("R15", "every segment of the reel exists and converts", False,
                broke(e))

        # R15b -- 🔴 THE NEGATIVE SIDE OF R15, and without it R15 cannot be
        # killed by any mutation: its fixture is the real reel, every segment
        # of which exists, so a `reel_budget` that silently SKIPPED a missing
        # segment would leave R15 green.  量, writing the mutation first.
        gone = mkreel("gone.tsv",
                      "bench/2026-08-31/W-3\treal\t1.0\n"
                      "bench/2026-08-31/NO-SUCH-CAPTURE\tmissing\t1.0\n")
        try:
            reel_budget(gone)
            row("R15b", "a reel naming a capture that does not exist is refused",
                False, "accepted -- a missing segment was skipped silently")
        except Exception as e:                              # noqa: BLE001
            row("R15b", "a reel naming a capture that does not exist is refused",
                "does not exist" in str(e),
                str(e)[:46] if isinstance(e, Refuse) else broke(e))

        if segs is None:
            row("R16", "the reel's total is capture+pause and is under the "
                "ceiling", False, "not reached")
            row("R17", "POPULATION: more than one segment, none repeated",
                False, "not reached")
        else:
            # R16 -- recomputed here from the rows rather than trusted, so a
            # `reel_budget` that dropped a term is visible.
            want_pau = sum(q for _, _, q in read_reel(REEL))
            want_cap = sum(sum(x for x, _ in convert(os.path.join(ROOT, t[0]))[0])
                           for t in segs)
            row("R16",
                "the reel's total is capture+pause and is under the ceiling",
                abs(total - (want_cap + want_pau)) < 1e-6
                and total <= REEL_CEILING_S,
                f"{cap:.3f} + {pau:.1f} = {total:.3f} s "
                f"(ceiling {REEL_CEILING_S:.0f} s, ARTIFACTS §2)")
            pref = [t[0] for t in segs]
            row("R17", "POPULATION: more than one segment, none repeated",
                len(segs) > 1 and len(set(pref)) == len(pref),
                f"{len(segs)} row(s), {len(set(pref))} distinct prefix(es)")

        empty = mkreel("empty.tsv", "# only a comment\n\n")
        try:
            read_reel(empty)
            row("R17b", "a reel with no segments is refused", False,
                "accepted")
        except Exception as e:                              # noqa: BLE001
            row("R17b", "a reel with no segments is refused",
                "no segments" in str(e),
                str(e)[:46] if isinstance(e, Refuse) else broke(e))

        # R18 -- the rule the reel file states in its first paragraph, and
        # which nothing enforced: a segment must be a committed capture.
        outside = mkreel("outside.tsv",
                         "/home/key/fwre-work/x\ttitle\t1.0\n")
        try:
            read_reel(outside)
            row("R18", "a segment outside bench/ is refused", False,
                "accepted -- a reel could name a file no cloner has")
        except Exception as e:                              # noqa: BLE001
            row("R18", "a segment outside bench/ is refused",
                "not under `bench/`" in str(e),
                str(e)[:46] if isinstance(e, Refuse) else broke(e))

    print()
    return 0 if ok else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        print("replay-capture controls")
        return run_controls()
    if len(argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    sub, target = argv[1], argv[2]
    outdir = None
    if "--out" in argv:
        outdir = argv[argv.index("--out") + 1]
    speed = 1.0
    if "--speed" in argv:
        speed = float(argv[argv.index("--speed") + 1])
    try:
        if sub == "verify":
            recs, blob = convert(target)
            print(f"  ok  {target}: {len(recs)} record(s), {len(blob)} byte(s), "
                  f"{sum(d for d, _ in recs):.3f} s")
            return 0
        if sub == "build":
            if not outdir:
                raise Refuse("build needs --out <dir>")
            t, dpth, recs, blob = build(target, outdir)
            print(f"  ok  {t}\n  ok  {dpth}\n"
                  f"      {len(recs)} record(s), {len(blob)} byte(s), "
                  f"{sum(d for d, _ in recs):.3f} s")
            return 0
        if sub == "play":
            return play(target, speed, outdir)
        if sub == "reel":
            if "--budget" in argv:
                return print_budget(target)
            return reel(target, speed, outdir)
    except Refuse as e:
        sys.stderr.write(f"REFUSED: {e}\n")
        return 2
    sys.stderr.write(f"unknown subcommand `{sub}`\n")
    return 2


def read_reel(tsv):
    """-> [(prefix, title, pause)], refusing anything it cannot parse.

    The reel's CONTENT is data, not code: one row per segment,
    `prefix <TAB> title <TAB> pause-seconds`.

    🔴 A segment must be a path under `bench/`, and that is enforced here
    rather than remembered.  `config/r3-11-reel.tsv`'s first rule is *every
    segment is a committed capture*, and the whole claim the artefact makes
    over a screen recording is that anyone who clones this repository can
    re-run the same command and get the same bytes.  A row naming a file under
    `$FWRE_WORK` would play perfectly on this machine and on no other, and the
    failure would be invisible until someone else tried.
    """
    rows = []
    with open(os.path.join(ROOT, tsv), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 2:
                raise Refuse(f"{tsv}: want prefix<TAB>title[<TAB>pause]: {line}")
            if not p[0].startswith("bench/"):
                raise Refuse(f"{tsv}: segment {p[0]!r} is not under `bench/`, "
                             f"so it is not a committed capture -- a reel that "
                             f"names one plays on this machine and on no other")
            rows.append((p[0], p[1], float(p[2]) if len(p) > 2 else 1.5))
    if not rows:
        raise Refuse(f"{tsv} has no segments")
    return rows


def reel_budget(tsv):
    """-> (segments, capture_s, pause_s, total_s).

    Every segment is CONVERTED, not merely stat()ed: a `.timing` that
    disagrees with its `.log` is the one class the reel cannot recover from
    once the recorder is running, and `convert` is what sees it.

    This exists so the reel's running time is a number the tool re-derives
    from the captures rather than a number written in a comment.  ⚠️ It is
    the sum of the captures' own durations plus the pauses; it is not what a
    stopwatch on the recording will read, because a terminal's own scroll is
    not in it.
    """
    segs = []
    for prefix, title, pause in read_reel(tsv):
        recs, blob = convert(os.path.join(ROOT, prefix))
        segs.append((prefix, title, pause, sum(d for d, _ in recs),
                     len(blob), len(recs)))
    cap = sum(s[3] for s in segs)
    pau = sum(s[2] for s in segs)
    return segs, cap, pau, cap + pau


def print_budget(tsv):
    segs, cap, pau, total = reel_budget(tsv)
    print(f"  {tsv}")
    print(f"  {'segment':<28} {'bytes':>7} {'capture':>9} {'pause':>7}")
    for prefix, _title, pause, dur, nb, _n in segs:
        print(f"  {prefix:<28} {nb:>7} {dur:>9.3f} {pause:>7.1f}")
    print(f"  {'':<28} {'':>7} {'-' * 9} {'-' * 7}")
    print(f"  {len(segs)} segment(s){'':<16} {'':>7} {cap:>9.3f} {pau:>7.1f}")
    print(f"  TOTAL {total:.3f} s   (ceiling {REEL_CEILING_S:.0f} s, "
          f"plan/ARTIFACTS.md §2's v0.2 take)")
    return 0 if total <= REEL_CEILING_S else 1


def reel(tsv, speed=1.0, outdir=None):
    """Play a sequence of captures with titles, from a TSV.

    A screen recorder pointed at the terminal while this runs produces the
    artefact, and the artefact is then reproducible from the repository by
    re-running this one command.
    """
    import time
    rows = read_reel(tsv)
    # Convert every segment BEFORE the first one plays.  A reel that stops
    # half way is a take that has to be re-shot, and the recorder is already
    # running by then.
    reel_budget(tsv)
    for prefix, title, pause in rows:
        sys.stdout.write(f"\n\033[1;36m── {title}\033[0m\n")
        sys.stdout.write(f"\033[2m   {prefix}.log\033[0m\n\n")
        sys.stdout.flush()
        rc = play(os.path.join(ROOT, prefix), speed, outdir)
        if rc != 0:
            return rc
        time.sleep(pause)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
