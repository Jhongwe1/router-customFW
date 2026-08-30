#!/usr/bin/env python3
"""Run `audit-bench-log.py`'s patterns over the populations nothing has scanned,
never print what matched, and -- new on 2026-08-30 -- answer *whose address is
this* by looking the bytes up in the reference dump instead of by recognising a
prefix.

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

🔴 WHY `--attribute` EXISTS, AND IT IS A CORRECTION OF THIS FILE'S FIRST DAY
---------------------------------------------------------------------------
On 2026-08-30 (thirteenth session) this tool reported one distinct MAC on
`FC:19:28` in seven files, four of them in the public `upstream/`, and the
write-up called `FC:19:28` *TOTOLINK's OUI* and recorded the attribution as
**undetermined** because `FW-17`'s SSID correlation could not be run.

Every clause of that was wrong or unnecessary, and one measurement settles all
of it:

  * `FC:19:28` is **Actions Microelectronics** (IEEE MA-L, registered
    2020-08-25), not TOTOLINK.  讀, the IEEE registry.
  * the value is the **workstation's own USB GbE adapter**: it equals the
    `enx<12 hex>` interface name recorded in nine tracked files (systemd's
    ID_NET_NAME_MAC scheme puts the adapter's MAC in the name), and in both
    committed host captures it is the source of the ICMP echo **replies** and
    never of the requests.  量.
  * it occurs **0 times** in this unit's own 4 MiB flash dump -- raw,
    byte-reversed, and as ASCII in four cases -- and its 3-byte OUI occurs 0
    times there and 0 times in the vendor GPL tree.  量.

**The correlation that could not be run was never the only one available.**  The
dump is the arbiter and it was on this disk the whole time.  So attribution
stops being a guess about prefixes and becomes a lookup:

    is this value in $FWRE_WORK/dumps/flash-n150rt-console-2.bin?

⚠️ **What `--attribute` still cannot do.**  A value absent from the dump is not
thereby harmless -- it may be a runtime address this unit synthesises, and 量,
the on-wire address of `eth4` under my own kernel is NOT in the dump either.  It
answers *does this byte string exist in this unit's flash*, and that is the only
sentence it is allowed to make.

WHY IT DOES NOT PRINT WHAT MATCHED
----------------------------------
`audit-bench-log.py` prints the matched text, which is right for a bench log the
operator is about to commit and wrong here: the question being asked is whether
this unit's MAC is in a file that is already published, and answering it by
printing the MAC is answering it in the worst possible way.  `flashwin.py` makes
the same distinction -- it publishes the verdict and refuses the digest.  `L5`
is the control on that property, and 🔴 **`L9` is the control the property
actually needed**: on 2026-08-30 a throwaway probe written to answer today's
question printed a 3-byte OUI into a transcript, because its masking covered the
file lines it echoed and not the lookup strings it built.  `L9` asserts that a
rendered attribution contains the value in none of seven encodings **and does
not contain the OUI either**.

WHY IT IMPORTS RATHER THAN DRIVES THE CLI
-----------------------------------------
`TC-j` is the standing lesson that a private copy of a pipeline is a pipeline
the controls do not test.  This imports `audit-bench-log.py`'s own `PATTERNS`,
`ALLOW`, `allowed` and `scan` -- there is no second copy of the rules.  What it
does not reuse is `main()`, and the reason is exactly the paragraph above: that
function's output is the thing that must not happen.  `L1`/`L2`/`L3` are the
same controls run against the same imported objects.

Usage:  tools/leakscan.py [--self-test] [--attribute]
"""
import hashlib
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
#: 🔄 2026-08-30 (fourteenth session): `.err`, `.s`, `.build` and `.lds` added.
#: 量 before adding them: they were 14 of the tracked files this tool called NOT
#: SCANNED, and every one of them is plain text -- two of the `.err` files carry
#: an `enx<12 hex>` name.  A text scanner that calls a text file unreadable is
#: making the same claim about itself that this whole tool exists to refuse.
TEXTY = {".md", ".txt", ".json", ".tsv", ".csv", ".py", ".sh", ".ps1", ".yml",
         ".yaml", ".toml", ".c", ".h", ".S", ".java", ".log", ".timing",
         ".cfg", ".conf", ".ini", ".delta", ".config", ".patch", ".gitignore",
         ".gitattributes", ".gitmodules", ".err", ".s", ".build", ".lds", ""}


#: 🔴 THE SPLIT, and it is the difference between a number and a finding.
#: `audit-bench-log.py`'s patterns were written for a DEVICE LOG, where the
#: string `calib` in the bytes means calibration data.  In PROSE those same
#: words are the subject matter -- this project writes `H601` in every other
#: paragraph.  Only these can identify one physical unit, and a count that mixes
#: the two answers no question.
#:
#: ⚠️ This is a property of the POPULATION, not of the patterns: on
#: `bench/**/*.log` the topic patterns are load-bearing and must stay.  The
#: split lives here, in the tool that scans prose, and not in the one that
#: scans transcripts.
IDENTITY = {"MAC, colon form", "MAC, dash form", "MAC, bare 12 hex",
            "MAC, enx interface", "serial-ish"}

#: The files whose identity hits are this repository's own scanner literals.
#: File-scoped rather than value-scoped on purpose: a literal is a control
#: because of where it lives, and 🔴 a value that is ALSO in the dump must not
#: be excused by sitting in one of them.  `L13` is that ordering, as a case.
SCANNER_FILES = {"tools/audit-bench-log.py", "tools/leakscan.py",
                 "tools/spec-check.py", "tools/test-leakscan-mutants.py"}

#: The arbiter.  Never committable -- 4 MiB of one physical device.
DUMP_REL = os.path.join("dumps", "flash-n150rt-console-2.bin")
#: `SPEC.md` `FLS-14`.  量 2026-08-30: both full dumps hash to this.
DUMP_SHA256 = ("a800059a9b8c414df026a22b8423a5939d0f9bb"
               "793109d0f7ce086f6810f37ea")
#: 🔴 One variable, used three times: the case, the printed skip and the
#: assertion against `tools/ci-expected.tsv`.  量 2026-08-30, CI run
#: 33310864156: `test-kbuild-cflags` was 9/9 green on this bench and red on the
#: runner because the label it printed was not the label the table carried, and
#: a machine that has `$FWRE_WORK` never prints the skip so never compares it.
#: The label starts with the case id, which is the convention that carried-
#: forward row proposes.  `L15` is the assertion.
DUMP_SKIP_LABEL = "L16 the reference flash dump"

H601 = (0x006000, 0x008000)

_MAC_SEP = re.compile(r"^([0-9A-Fa-f]{2})([:-])(?:[0-9A-Fa-f]{2}\2){4}"
                      r"[0-9A-Fa-f]{2}$")
_MAC_BARE = re.compile(r"^[0-9A-Fa-f]{12}$")
_MAC_ENX = re.compile(r"^enx([0-9A-Fa-f]{12})$")
ENX_IN_TEXT = re.compile(r"\benx([0-9A-Fa-f]{12})\b")


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


def read_text(root, rel):
    full = os.path.join(root, rel)
    try:
        with io.open(full, encoding="utf-8", errors="strict", newline="") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def scan_population(abl, root, paths):
    """-> (findings, scanned, not_scanned_by_ext).  findings carry NO text."""
    findings = []
    scanned = 0
    skipped = {}
    for rel in paths:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in TEXTY:
            skipped[ext or "<none>"] = skipped.get(ext or "<none>", 0) + 1
            continue
        text = read_text(root, rel)
        if text is None:
            skipped["<undecodable> " + (ext or "<none>")] = \
                skipped.get("<undecodable> " + (ext or "<none>"), 0) + 1
            continue
        scanned += 1
        for label, ln, txt, line in abl.scan(rel, text):
            if abl.allowed(txt, line):
                continue
            # NO `txt`, and no slice of `line`.  Length only -- except for the
            # six bytes an address encodes, which `--attribute` needs and which
            # never leave this process.
            findings.append((rel, label, ln, len(txt), mac_bytes(txt)))
    return findings, scanned, skipped


# --------------------------------------------------------------------------
# attribution
# --------------------------------------------------------------------------

def mac_bytes(txt):
    """The six bytes a matched string encodes, or None if it encodes none.

    `serial-ish` matches a PHRASE (`S/N:`), not a value, so it has no bytes and
    is classified NOVALUE rather than crashing the classifier -- which is what
    the first draft did."""
    if _MAC_SEP.match(txt):
        h = txt.replace(":", "").replace("-", "")
    elif _MAC_BARE.match(txt):
        h = txt
    else:
        m = _MAC_ENX.match(txt)
        if not m:
            return None
        h = m.group(1)
    return bytes(int(h[i:i + 2], 16) for i in range(0, 12, 2))


def dump_path():
    work = os.environ.get("FWRE_WORK", "/home/key/fwre-work")
    return os.path.join(work, DUMP_REL)


def region_of(off):
    """Flash map, 讀 `SPEC.md` §8 / `FLM-02` / `FW-28`."""
    if off < 0x006000:
        return "loader"
    if H601[0] <= off < H601[1]:
        return "H601"
    if off < 0x130000:
        return "boot+cfg+linux (mtd0)"
    return "root fs (mtd1)"


def find_all(hay, needle):
    off, i = [], hay.find(needle)
    while i != -1:
        off.append(i)
        i = hay.find(needle, i + 1)
    return off


def enx_names(root, pops):
    """Every `enx<12 hex>` name written anywhere in the corpus, as bytes.

    systemd's ID_NET_NAME_MAC puts the adapter's own MAC in the interface name,
    so the name IS the value and no separate source is needed to say that a
    matched address belongs to the workstation rather than to the device.

    🔴 **Harvested from everything EXCEPT this repository's own scanners.** 量
    2026-08-31: `tools/test-leakscan-mutants.py` plants a synthetic
    `enx040506070803` in its fixture, and with the scanners in the population
    that literal put itself into `hostnames` and then classified ITSELF `HOST` —
    a value calling itself the workstation's adapter on its own authority. The
    real names live in `LOG.md`, `PROGRESS.md`, `RUNSHEET.md` and the bench
    cards, so excluding the scanners costs nothing and removes the circle.
    """
    got = set()
    for _name, paths, _why in pops:
        for rel in paths:
            if rel in SCANNER_FILES:
                continue
            if os.path.splitext(rel)[1].lower() not in TEXTY:
                continue
            text = read_text(root, rel)
            if text is None:
                continue
            for m in ENX_IN_TEXT.finditer(text):
                h = m.group(1)
                got.add(bytes(int(h[i:i + 2], 16) for i in range(0, 12, 2)))
    return got


#: The classes, in the order `classify` tries them.  The order is the claim:
#: 🔴 **UNIT is tried before every inference**, because "these bytes are in this
#: unit's flash" is a measurement and "this address is locally administered, so
#: it cannot be burned in" is not.  `L11` and `L13` are that ordering as cases.
CLASSES = ("NOVALUE", "TRIVIAL", "UNIT", "HOST", "SYNTH", "CONTROL", "UNKNOWN")


def classify(value, rel, dump, hostnames):
    """-> (class, detail).  Never returns the value or any encoding of it."""
    if value is None:
        return "NOVALUE", "the pattern matched a phrase, not an address"
    if value == b"\x00" * 6 or value == b"\xff" * 6:
        return "TRIVIAL", "all-zero or broadcast; identifies nothing"
    offs = find_all(dump, value)
    if offs:
        where = sorted({region_of(o) for o in offs})
        return "UNIT", ("in the reference dump %d time(s), in %s"
                        % (len(offs), "+".join(where)))
    if value in hostnames:
        return "HOST", ("equals an enx<12hex> interface name in the corpus: "
                        "the workstation's adapter, not the device")
    if value[0] & 0x02:
        return "SYNTH", ("locally administered (bit 0x02 of octet 0), so it is "
                         "not a burned-in address, and it is not in the dump")
    if rel in SCANNER_FILES:
        return "CONTROL", "a scanner literal in this repository's own tools"
    return "UNKNOWN", "globally administered, not in the dump -- needs a person"


def render_attr(rel, label, ln, klass, detail):
    """🔴 The one line this mode prints per hit.  It carries a file, a pattern,
    a line number, a class and a sentence.  It carries no byte of the value and
    no prefix of it; `L9` is the control."""
    return "  %-50s %-20s line %-6d %-8s %s" % (rel, label, ln, klass, detail)


def attribute(abl, root):
    """The desk verdict run.  Refuses without the dump rather than reporting a
    clean sweep it cannot have measured."""
    dp = dump_path()
    if not os.path.exists(dp):
        print("REFUSED: --attribute needs %s, which is 4 MiB of this unit's "
              "own flash and can never be committed. Without it every value "
              "would classify as 'not in the dump', which is a claim this run "
              "has not measured." % dp)
        return 2
    with open(dp, "rb") as fh:
        dump = fh.read()
    got = hashlib.sha256(dump).hexdigest()
    if got != DUMP_SHA256:
        print("REFUSED: %s hashes %s..., not the FLS-14 reference"
              % (dp, got[:16]))
        return 2

    pops = populations(root)
    hosts = enx_names(root, pops)
    tally = dict((k, 0) for k in CLASSES)
    unit_values = set()
    print("=== attribution: whose address is it, decided against the dump ===")
    print("  arbiter: %s (4,194,304 bytes, sha256 %s...)"
          % (DUMP_REL, DUMP_SHA256[:8]))
    print("  enx<12hex> interface names found in the corpus: %d" % len(hosts))
    print("")
    for name, paths, _why in pops:
        findings, _scanned, _skipped = scan_population(abl, root, paths)
        ident = [f for f in findings if f[1] in IDENTITY]
        print("=== %s === %d identity hit(s)" % (name, len(ident)))
        for rel, label, ln, _n, value in ident:
            klass, detail = classify(value, rel, dump, hosts)
            tally[klass] += 1
            if klass == "UNIT":
                unit_values.add(value)
            print(render_attr(rel, label, ln, klass, detail))
        print("")
    total = sum(tally.values())
    print("=== %d identity hit(s): %s ==="
          % (total, ", ".join("%s %d" % (k, tally[k]) for k in CLASSES
                              if tally[k])))
    if tally["UNIT"]:
        print("🔴 %d hit(s) carry %d distinct value(s) that exist in this "
              "unit's own flash. The values are deliberately not printed; open "
              "the file at the line named." % (tally["UNIT"], len(unit_values)))
        return 1
    print("🟢 no hit carries a value that exists in this unit's flash. That is "
          "NOT the same sentence as 'no leak': the NOT SCANNED counts in the "
          "default run are what this instrument cannot see, and a value the "
          "device synthesises at runtime is not in the dump either.")
    return 0


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

def _synth_dump(planted, at=(0x006010, 0x006020)):
    """A 4 MiB-shaped fixture with a known value planted at known offsets, so
    every classifier control runs on a runner.  Only `L16` needs the real one.

    🔴 Planted TWICE on purpose.  The real finding is a value that occurs twice
    inside `H601`, and with one plant `L7` could not tell `find_all` from a
    `find` that stops at the first hit -- the detail sentence would read
    `1 time(s)` either way."""
    d = bytearray(b"\x00" * 0x140000)
    for off in at:
        d[off:off + len(planted)] = planted
    return bytes(d)


def controls(abl):
    """Every control must pass before a single population is reported."""
    rows = []
    skips = []

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
        # 🔴 The first version checked the colon form and one four-character
        # slice of it.  量 2026-08-30 by mutation `C13`: a `render` that prints
        # the whole finding TUPLE passed it, because the tuple now carries the
        # DECODED SIX BYTES and `b'\x00\xe0L\xab\xcd\xef'` contains neither of
        # the two strings that were checked.  A finding gained a field and the
        # control that guards findings did not.
        raw = bytes.fromhex(secret.replace(":", ""))
        forms = [secret, secret.lower(), "AB:CD",
                 secret.replace(":", ""), secret.replace(":", "").lower(),
                 repr(raw), repr(raw)[2:-1], "\\xab\\xcd"]
        leaked5 = [x for x in forms if x in rendered]
        ok5 = len(f) >= 1 and n == 1 and not leaked5
        rows.append(("L5 a finding never carries the matched bytes",
                     ok5, "%d finding(s), %d char(s) rendered, %d of %d "
                     "encoding(s) present"
                     % (len(f), len(rendered), len(leaked5), len(forms))))

    # L6 -- and a binary is NOT counted clean.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "fx.jpg")
        with open(p, "wb") as fh:
            fh.write(b"\xff\xd8\xff\xe0" + b"\x00" * 64)
        f, n, s = scan_population(abl, d, ["fx.jpg"])
        rows.append(("L6 a binary is reported NOT SCANNED, not clean",
                     n == 0 and sum(s.values()) == 1 and not f,
                     "scanned=%d skipped=%s" % (n, s)))

    # ---- the classifier.  Synthetic dump, so all of these run anywhere. -----
    # 🔴 The first draft picked `02...` and `0a...` for these two and BOTH have
    # bit 0x02 set, so both were locally administered and `L13` failed on a
    # fixture defect rather than on the tool.  Octet 0 is chosen here so that
    # `planted` and `absent` are globally administered and only `laa` is not --
    # otherwise the SYNTH branch shadows the two cases below it.
    planted = bytes.fromhex("040506070809")          # globally administered
    absent = bytes.fromhex("0c0d0e0f1011")           # globally administered
    laa = bytes.fromhex("560a01010101")              # the loader's own shape
    dump = _synth_dump(planted)

    k, det = classify(planted, "notes/x.md", dump, set())
    rows.append(("L7 a value planted twice inside H601 is UNIT, counted twice",
                 k == "UNIT" and "H601" in det and "2 time(s)" in det,
                 "%s -- %s" % (k, det)))

    k2, _ = classify(absent, "notes/x.md", dump, set())
    rows.append(("L8 a value absent from the dump does not classify UNIT",
                 k2 != "UNIT", k2))

    # L9 -- the control the never-print property actually needed.  量
    # 2026-08-30: a throwaway probe leaked a 3-byte OUI this way.
    line = render_attr("notes/x.md", "MAC, colon form", 7, *classify(
        planted, "notes/x.md", dump, set()))
    enc = [":".join("%02X" % c for c in planted),
           ":".join("%02x" % c for c in planted),
           "-".join("%02X" % c for c in planted),
           "-".join("%02x" % c for c in planted),
           "".join("%02X" % c for c in planted),
           "".join("%02x" % c for c in planted),
           "enx" + "".join("%02x" % c for c in planted),
           ":".join("%02X" % c for c in planted[:3]),
           "".join("%02x" % c for c in planted[:3])]
    leaked = [e for e in enc if e in line]
    rows.append(("L9 a rendered attribution carries neither value nor OUI",
                 not leaked, "%d of %d encoding(s) present" % (len(leaked),
                                                               len(enc))))

    k3, _ = classify(laa, "notes/x.md", dump, set())
    rows.append(("L10 a locally administered value absent from the dump is "
                 "SYNTH", k3 == "SYNTH", k3))

    # L11 -- and the ORDER: a measurement beats the inference above it.
    k4, _ = classify(laa, "notes/x.md", _synth_dump(laa), set())
    rows.append(("L11 the same value IN the dump is UNIT, not SYNTH",
                 k4 == "UNIT", k4))

    k5, _ = classify(absent, "notes/x.md", dump, {absent})
    rows.append(("L12 a value equal to an enx name is HOST",
                 k5 == "HOST", k5))

    # L13 -- a scanner literal does not excuse a value that is in the dump.
    k6, _ = classify(planted, "tools/audit-bench-log.py", dump, set())
    k7, _ = classify(absent, "tools/audit-bench-log.py", dump, set())
    rows.append(("L13 CONTROL never masks UNIT, and still applies otherwise",
                 k6 == "UNIT" and k7 == "CONTROL", "%s / %s" % (k6, k7)))

    # L14 -- every hit gets exactly one class from the declared set.
    probes = [None, b"\x00" * 6, b"\xff" * 6, planted, absent, laa]
    ks = [classify(v, "notes/x.md", dump, set())[0] for v in probes]
    rows.append(("L14 every value classifies, and only into CLASSES",
                 len(ks) == len(probes) and all(k in CLASSES for k in ks),
                 ",".join(ks)))

    # L17 -- 🔴 the four encodings reach the classifier as the SAME six bytes.
    # Every control above hands `classify` a byte string directly, so none of
    # them exercises `mac_bytes`, and a decoder that dropped one form would
    # make every hit in that form NOVALUE -- classified, counted, and silently
    # never looked up.  This drives the real path: text -> abl.scan ->
    # scan_population -> mac_bytes.
    with tempfile.TemporaryDirectory() as d:
        want = bytes.fromhex("00e04c112233")
        with io.open(os.path.join(d, "fx.md"), "w", encoding="utf-8") as fh:
            fh.write("colon 00:E0:4C:11:22:33\ndash 00-E0-4C-11-22-33\n"
                     "bare 00e04c112233\niface enx00e04c112233\n")
        f, _n, _s = scan_population(abl, d, ["fx.md"])
        vals = [x[4] for x in f if x[1] in IDENTITY]
        rows.append(("L17 all four MAC encodings decode to the same six bytes",
                     len(vals) == 4 and all(v == want for v in vals),
                     "%d identity hit(s), %d decoded to the same value"
                     % (len(vals), sum(1 for v in vals if v == want))))

    # L15 -- the skip label this tool prints is the one the census expects.
    tsv = os.path.join(ROOT, "tools", "ci-expected.tsv")
    if os.path.exists(tsv):
        want = None
        with io.open(tsv, encoding="utf-8") as fh:
            for row in fh:
                if row.startswith("#"):
                    continue
                parts = row.rstrip("\n").split("\t")
                if len(parts) > 2 and parts[0] == "leakscan":
                    want = parts[2]
        rows.append(("L15 ci-expected.tsv's allowed skip is this tool's label",
                     want == DUMP_SKIP_LABEL, "table says %r" % (want,)))
    else:
        rows.append(("L15 ci-expected.tsv's allowed skip is this tool's label",
                     False, "no ci-expected.tsv beside this tool"))

    # ---- L16, the only one that needs the real 4 MiB ------------------------
    dp = dump_path()
    if not os.path.exists(dp):
        skips.append((DUMP_SKIP_LABEL, 1))
    else:
        with open(dp, "rb") as fh:
            real = fh.read()
        rows.append(("L16 the reference dump is FLS-14, byte for byte",
                     len(real) == 4194304
                     and hashlib.sha256(real).hexdigest() == DUMP_SHA256,
                     "%d bytes, sha256 %s..."
                     % (len(real), hashlib.sha256(real).hexdigest()[:8])))
    return rows, skips


def render(f):
    rel, label, ln, n = f[0], f[1], f[2], f[3]
    return "  %-52s %-22s line %-6d %d char(s)" % (rel, label, ln, n)


def main(argv):
    abl = load_abl()

    print("=== controls (they run first; nothing is reported if one fails) ===")
    rows, skips = controls(abl)
    for name, ok, detail in rows:
        print("  %-5s %-50s %s" % ("ok" if ok else "FAIL", name, detail))
    for lbl, n in skips:
        print("  skip   %-52s %s" % (
            lbl, "needs $FWRE_WORK/%s -- 4 MiB of this unit's own flash, which "
                 "can never be committed (covers %d)" % (DUMP_REL, n)))
    bad = [r for r in rows if not r[1]]
    print("")
    if bad:
        print("REFUSED: %d control(s) failed. A clean population would mean "
              "nothing." % len(bad))
        return 2

    if "--self-test" in argv:
        for lbl, n in skips:
            print("  (skipped: %s, %d case(s))" % (lbl, n))
        print("RESULT: \033[32m%d passed, 0 failed\033[0m" % len(rows))
        return 0

    if "--attribute" in argv:
        return attribute(abl, ROOT)

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
        for f in findings:
            by_pat.setdefault(f[1], []).append(f[0])
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
            print("  🟢 0 hits on the patterns that can name one unit")
        print("")

    if total:
        print("%d raw hit(s) across the three populations, %s of them on a "
              "pattern that can identify one unit." % (total, ident_total))
        print("The matched bytes are deliberately not printed; open the file "
              "at the line named. `--attribute` says which of them are THIS "
              "unit's, by looking the bytes up in the reference dump.")
        return 1 if ident_total else 0
    print("\033[32m0 findings\033[0m in what could be read. That is not the "
          "same sentence as `no leak`: the NOT SCANNED counts above are the "
          "part this instrument cannot see.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
