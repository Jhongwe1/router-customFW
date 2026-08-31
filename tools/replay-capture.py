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

    recs, blob = convert(W3)
    row("R1", "the records account for every byte of the .log",
        sum(c for _, c in recs) == len(blob),
        f"{len(recs)} record(s), {sum(c for _, c in recs)} of {len(blob)} bytes")

    row("R2", "one record per .timing line",
        len(recs) == len(read_timing(W3 + ".timing")),
        f"{len(recs)}")

    tim = read_timing(W3 + ".timing")
    row("R3", "the delays sum to the last timestamp",
        abs(sum(d for d, _ in recs) - tim[-1][1]) < 1e-6,
        f"sum {sum(d for d, _ in recs):.6f} s, last stamp {tim[-1][1]:.6f} s")

    # R4 -- 🔴 THE CROSS-VALIDATION, and it is the reason these three captures
    # were chosen.  Identical data, different timing: both halves are asserted,
    # because a tool that ignored its timing input would pass the first half
    # and a tool that corrupted its data would pass the second.
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
            except Refuse as e:
                row(tag, name, needle in str(e), str(e)[:46])

        # R11 -- a MISSING sidecar refuses rather than replaying the .log at
        # full speed, which would look like a successful replay of a boot that
        # took no time.
        p = os.path.join(d, "lonely")
        open(p + ".log", "wb").write(b"x")
        try:
            convert(p)
            row("R11", "a .log with no .timing is refused", False, "accepted")
        except Refuse as e:
            row("R11", "a .log with no .timing is refused",
                "does not exist" in str(e), str(e)[:46])

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
            return reel(target, speed, outdir)
    except Refuse as e:
        sys.stderr.write(f"REFUSED: {e}\n")
        return 2
    sys.stderr.write(f"unknown subcommand `{sub}`\n")
    return 2


def reel(tsv, speed=1.0, outdir=None):
    """Play a sequence of captures with titles, from a TSV.

    The reel's CONTENT is data, not code: one row per segment,
    `prefix <TAB> title <TAB> pause-seconds`.  A screen recorder pointed at the
    terminal while this runs produces the artefact, and the artefact is then
    reproducible from the repository by re-running this one command.
    """
    import time
    rows = []
    with open(os.path.join(ROOT, tsv), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 2:
                raise Refuse(f"{tsv}: want prefix<TAB>title[<TAB>pause]: {line}")
            rows.append((p[0], p[1], float(p[2]) if len(p) > 2 else 1.5))
    if not rows:
        raise Refuse(f"{tsv} has no segments")
    missing = [r[0] for r in rows if not os.path.exists(
        os.path.join(ROOT, r[0] + ".log"))]
    if missing:
        raise Refuse(f"{tsv} names captures that do not exist: {missing}")
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
