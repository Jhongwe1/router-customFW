#!/usr/bin/env python3
"""reproduce-l0 -- layer 0 of REPRODUCE.md: are these the files release v1.0 published?

USAGE
  reproduce-l0.py fetch --assets DIR --release-json FILE [--tag T] [--slug O/R]
  reproduce-l0.py check --assets DIR --release-json FILE [--tag T] [--repo DIR]
                        [--no-controls]

`fetch` reads the release's description from GitHub's REST API, without
credentials, writes it to FILE, creates DIR -- which must not exist, or be
empty -- and downloads every asset the description lists into it.  It checks
nothing: `check` is the verdict, and it reads only what `fetch` wrote.

`check` reads three sources and requires them to agree:

  C1  the release manifest, `SHA256SUMS`, an asset of the release: its entries
      are parsed and counted, and the count printed is that count.
  C2  every entry's file is in DIR and has the entry's sha256.
  C3  the files in DIR are exactly the manifest's entries plus the manifest:
      nothing missing, nothing extra, no subdirectory.
  C4  GitHub's description of the release, a second source: the same names,
      each asset's `size` equal to the file's, and each asset's `digest` --
      GitHub's own sha256 of what it stores -- equal to the file's, the
      manifest included.
  C5  the commit the tag names, from the repository given by --repo (default:
      the one this file is in): the image's and `T.rlxu`'s sha256 and byte
      counts as the `CHANGELOG.md` committed at the tag states them, read out
      of the tag's own tree, equal to the files'; and the archive's name
      carries the first twelve hex digits of that commit.

Then, unless --no-controls, the controls, each a fresh run of this file on a
copy of DIR whose exit status is read: K1 one bit of the image flipped, K2 one
file added, K3 one file removed.  Each must exit 1.  A control that exits 0
means the instrument cannot fail and nothing it said is evidence.

EXIT
  0  every check passed and every control was refused
  1  a check failed: the files are not the release's
  2  a control was not refused: the instrument is broken
  3  usage or environment refusal (a missing input, an unreadable tag)

WHAT IT DOES NOT ESTABLISH
  * That the manifest itself is the owner's.  No file at the tag holds the
    sha256 of `SHA256SUMS`: it was written over the other assets after the
    release commit, and its digest was first committed after the tag, in
    `LOG.md`'s publication entry (fb5a5d17).  Here it is checked against
    GitHub's digest only.
  * That the tag or the release is the owner's: the tag is unsigned.  What C5
    reads is what the commit the tag names says, in the repository --repo
    points at.
  * That GitHub stored what the owner uploaded: C4 compares the files with
    GitHub's own digest of the bytes it serves.
  * Anything about what the files contain beyond their digests: that the
    archive rebuilds the image is layer 1's question.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

MANIFEST = "SHA256SUMS"
DEFAULT_TAG = "v1.0"
DEFAULT_SLUG = "Jhongwe1/router-customFW"
API = "https://api.github.com/repos/%s/releases/tags/%s"
HERE = os.path.dirname(os.path.abspath(__file__))
ENTRY_RE = re.compile(r"^([0-9a-f]{64}) [ *](.+)$")


class Refused(Exception):
    """A usage or environment refusal: exit 3."""


def say(msg=""):
    print(msg, flush=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise Refused("git %s in %s failed: %s" % (" ".join(args), repo,
                      p.stderr.decode("utf-8", "replace").strip()[:200]))
    return p.stdout


# ------------------------------------------------------------------ fetch
def http_get(url, accept):
    req = urllib.request.Request(url, headers={
        "Accept": accept, "User-Agent": "rlxfw-reproduce-l0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except (urllib.error.URLError, OSError) as e:
        raise Refused("GET %s failed: %s" % (url, e))


def cmd_fetch(a):
    if os.path.exists(a.assets) and (not os.path.isdir(a.assets) or os.listdir(a.assets)):
        raise Refused("%s exists and is not an empty directory: fetch writes only "
                      "into a new one, so nothing in it predates the download" % a.assets)
    if os.path.exists(a.release_json):
        raise Refused("%s exists; fetch does not overwrite a release description"
                      % a.release_json)
    raw = http_get(API % (a.slug, a.tag), "application/vnd.github+json")
    rel = json.loads(raw.decode("utf-8"))
    assets = rel.get("assets") or []
    if not assets:
        raise Refused("the release description lists no asset")
    tmp = a.release_json + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(raw)
    os.replace(tmp, a.release_json)
    os.makedirs(a.assets, exist_ok=True)
    for x in assets:
        name = x["name"]
        if "/" in name or name in (".", ".."):
            raise Refused("asset name %r is not a plain file name" % name)
        dest = os.path.join(a.assets, name)
        data = http_get(x["browser_download_url"], "application/octet-stream")
        with open(dest + ".part", "wb") as fh:
            fh.write(data)
        os.replace(dest + ".part", dest)
        say("  fetched %-100s %10d bytes" % (name, len(data)))
    say("fetch: %d asset(s) of %s %s into %s; description in %s"
        % (len(assets), a.slug, a.tag, a.assets, a.release_json))
    say("fetch checks nothing; run `check` on the same two paths")
    return 0


# ------------------------------------------------------------------ check
def read_manifest(d):
    p = os.path.join(d, MANIFEST)
    if not os.path.isfile(p):
        return None, ["C1 no %s in %s" % (MANIFEST, d)]
    entries, bad = [], []
    with open(p, "rb") as fh:
        for n, raw in enumerate(fh.read().split(b"\n"), 1):
            if not raw:
                continue
            m = ENTRY_RE.match(raw.decode("utf-8", "replace"))
            if not m:
                bad.append("C1 %s line %d is not `<sha256>  <name>`" % (MANIFEST, n))
                continue
            entries.append((m.group(2), m.group(1)))
    names = [e[0] for e in entries]
    if len(set(names)) != len(names):
        bad.append("C1 %s names a file twice" % MANIFEST)
    if MANIFEST in names:
        bad.append("C1 %s lists itself" % MANIFEST)
    return entries, bad


def changelog_values(text, tag):
    """The image's and T's (name, bytes, sha256) from the tag's section."""
    m = re.search(r"^## %s\b.*?(?=^## |\Z)" % re.escape(tag), text, re.S | re.M)
    if not m:
        raise Refused("CHANGELOG.md at %s has no `## %s` section" % (tag, tag))
    sec = re.sub(r"\s+", " ", m.group(0))
    im = re.search(r"\*\*The image\.\*\* `([^`]+\.img)`, ([0-9,]+) bytes, sha256 "
                   r"`([0-9a-f]{64})`", sec)
    if not im:
        raise Refused("the `## %s` section has no `**The image.**` sentence "
                      "naming a file, its bytes and its sha256" % tag)
    tm = re.search(r"`T\.rlxu`.*?([0-9,]+) bytes, sha256 `([0-9a-f]{64})`",
                   sec[im.end():])
    if not tm:
        raise Refused("the `## %s` section names no bytes and sha256 for T.rlxu" % tag)
    return ((im.group(1), int(im.group(2).replace(",", "")), im.group(3)),
            ("T.rlxu", int(tm.group(1).replace(",", "")), tm.group(2)))


def run_checks(a):
    """Return (fails, notes, image name).  Raises Refused on a usage problem."""
    fails, notes, iname = [], [], None
    if not os.path.isdir(a.assets):
        raise Refused("no directory %s" % a.assets)
    if not os.path.isfile(a.release_json):
        raise Refused("no release description %s (fetch writes it)" % a.release_json)

    # C1
    entries, bad = read_manifest(a.assets)
    fails += bad
    if entries is None:
        return fails, notes, iname
    n = len(entries)
    say("C1 %s lists %d file(s)" % (MANIFEST, n))

    # C2
    have = {}
    ok2 = 0
    for name, want in entries:
        p = os.path.join(a.assets, name)
        if not os.path.isfile(p):
            fails.append("C2 %s: listed, not in %s" % (name, a.assets))
            continue
        have[name] = sha256_file(p)
        if have[name] == want:
            ok2 += 1
        else:
            fails.append("C2 %s: sha256 %s..., the manifest says %s..."
                         % (name, have[name][:16], want[:16]))
    say("C2 %d of %d listed file(s) have the manifest's sha256" % (ok2, n))

    # C3
    on_disk = set(os.listdir(a.assets))
    expected = set(e[0] for e in entries) | {MANIFEST}
    for x in sorted(on_disk):
        if not os.path.isfile(os.path.join(a.assets, x)) or os.path.islink(
                os.path.join(a.assets, x)):
            fails.append("C3 %s is not a regular file" % x)
    extra, missing = sorted(on_disk - expected), sorted(expected - on_disk)
    for x in extra:
        fails.append("C3 %s is in %s and not in the manifest" % (x, a.assets))
    for x in missing:
        fails.append("C3 %s is in the manifest and not in %s" % (x, a.assets))
    say("C3 %d file(s) present, %d expected (the manifest's %d entries and the "
        "manifest); %d extra, %d missing" % (len(on_disk), len(expected), n,
                                              len(extra), len(missing)))
    have[MANIFEST] = sha256_file(os.path.join(a.assets, MANIFEST))

    # C4
    with open(a.release_json, "rb") as fh:
        rel = json.loads(fh.read().decode("utf-8-sig"))
    gh = {x["name"]: x for x in rel.get("assets") or []}
    if rel.get("tag_name") != a.tag:
        fails.append("C4 the description is of tag %r, not %r" % (rel.get("tag_name"), a.tag))
    for x in sorted(set(gh) ^ expected):
        fails.append("C4 %s is %s" % (x, "on GitHub and not in the manifest set"
                                      if x in gh else "in the manifest set and not on GitHub"))
    ok4 = 0
    for name in sorted(set(gh) & expected):
        p = os.path.join(a.assets, name)
        if name not in have or not os.path.isfile(p):
            continue
        dg, sz = gh[name].get("digest") or "", gh[name].get("size")
        if not dg.startswith("sha256:"):
            fails.append("C4 %s: GitHub gives no sha256 digest (%r)" % (name, dg[:20]))
        elif dg[7:] != have[name]:
            fails.append("C4 %s: GitHub's digest %s..., the file's %s..."
                         % (name, dg[7:23], have[name][:16]))
        elif sz != os.path.getsize(p):
            fails.append("C4 %s: GitHub's size %s, the file's %d"
                         % (name, sz, os.path.getsize(p)))
        else:
            ok4 += 1
    say("C4 %d of %d asset(s) GitHub lists have its size and digest, the manifest "
        "included" % (ok4, len(gh)))

    # C5
    repo = os.path.abspath(a.repo)
    tagtype = git(repo, "cat-file", "-t", a.tag).decode().strip()
    commit = git(repo, "rev-parse", "--verify", a.tag + "^{commit}").decode().strip()
    text = git(repo, "show", "%s:CHANGELOG.md" % commit).decode("utf-8")
    (iname, ibytes, isha), (tname, tbytes, tsha) = changelog_values(text, a.tag)
    say("C5 tag %s (%s) names commit %s; its CHANGELOG.md states %s and %s"
        % (a.tag, tagtype, commit, iname, tname))
    for name, nbytes, want in ((iname, ibytes, isha), (tname, tbytes, tsha)):
        p = os.path.join(a.assets, name)
        if name not in have or not os.path.isfile(p):
            fails.append("C5 %s: stated at the tag, not among the files" % name)
            continue
        if have[name] != want or os.path.getsize(p) != nbytes:
            fails.append("C5 %s: the tag states %d bytes %s..., the file is %d bytes %s..."
                         % (name, nbytes, want[:16], os.path.getsize(p), have[name][:16]))
        else:
            say("C5 %s: %d bytes, sha256 %s, as the tag states" % (name, nbytes, want))
    arch = [x for x in expected if re.match(r"^rlxfw-src-[0-9a-f]{12}\.tar\.xz$", x)]
    if len(arch) != 1:
        fails.append("C5 %d archive(s) named rlxfw-src-<12 hex>.tar.xz, not 1" % len(arch))
    elif arch[0][10:22] != commit[:12]:
        fails.append("C5 the archive %s does not name the tag's commit %s"
                     % (arch[0], commit[:12]))
    else:
        say("C5 the archive %s names the tag's commit" % arch[0])
    notes.append("%s's own sha256 is %s: no file at %s holds it (it was written "
                 "after the release commit, and first committed after the tag, "
                 "fb5a5d17); C4 is its only second source here"
                 % (MANIFEST, have[MANIFEST], a.tag))
    return fails, notes, iname


def control(a, label, mutate):
    tmp = tempfile.mkdtemp(prefix="reproduce-l0-ctl-")
    try:
        d = os.path.join(tmp, "assets")
        shutil.copytree(a.assets, d, symlinks=True)
        what = mutate(d)
        p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "check",
                            "--assets", d, "--release-json", a.release_json,
                            "--tag", a.tag, "--repo", a.repo, "--no-controls"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        first = [ln for ln in p.stdout.decode("utf-8", "replace").splitlines()
                 if ln.startswith("  FAIL")]
        say("%s %s: exit %d%s" % (label, what, p.returncode,
                                  ("; first finding: " + first[0].strip()) if first else ""))
        return p.returncode == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_check(a):
    fails, notes, img = run_checks(a)
    for f in fails:
        say("  FAIL  " + f)
    for x in notes:
        say("  note  " + x)
    if fails:
        say("RESULT: REFUSED -- %d finding(s); these are not the %s release's files"
            % (len(fails), a.tag))
        return 1
    say("RESULT: PASS -- the files are the ones release %s lists, by three sources"
        % a.tag)
    if a.no_controls:
        return 0
    entries, _ = read_manifest(a.assets)

    def flip(d):
        p = os.path.join(d, img)
        os.chmod(p, 0o644)
        with open(p, "r+b") as fh:
            off = os.path.getsize(p) // 2
            fh.seek(off)
            b = fh.read(1)
            fh.seek(off)
            fh.write(bytes([b[0] ^ 0x01]))
        return "one bit of %s flipped (byte %d)" % (img, off)

    def add(d):
        with open(os.path.join(d, "EXTRA"), "wb") as fh:
            fh.write(b"x\n")
        return "one file added"

    def remove(d):
        os.unlink(os.path.join(d, entries[0][0]))
        return "%s removed" % entries[0][0]

    ok = [control(a, "K1", flip), control(a, "K2", add), control(a, "K3", remove)]
    if not all(ok):
        say("CONTROLS: %d of 3 refused -- the instrument cannot be trusted" % sum(ok))
        return 2
    say("CONTROLS: 3 of 3 refused (exit 1 each)")
    return 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="reproduce-l0.py")
    sub = ap.add_subparsers(dest="verb")
    for v in ("fetch", "check"):
        s = sub.add_parser(v)
        s.add_argument("--assets", required=True)
        s.add_argument("--release-json", required=True)
        s.add_argument("--tag", default=DEFAULT_TAG)
        if v == "fetch":
            s.add_argument("--slug", default=DEFAULT_SLUG)
        else:
            s.add_argument("--repo", default=os.path.dirname(HERE))
            s.add_argument("--no-controls", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.verb == "fetch":
            return cmd_fetch(a)
        if a.verb == "check":
            return cmd_check(a)
        ap.print_usage()
        return 3
    except Refused as e:
        say("REFUSED: %s" % e)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
