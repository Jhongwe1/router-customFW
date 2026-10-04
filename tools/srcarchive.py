#!/usr/bin/env python3
"""srcarchive -- pack the corresponding source of an image built from this
repository, and write down exactly what the pack holds.

WHY THIS EXISTS
---------------
`docs/offer.md` says every release carrying a binary carries its complete
corresponding source beside it.  量 2026-10-05, at `c7716fbe`: no tool produced
that archive, and the two committed descriptions of what it would contain --
`docs/offer.md` § 2 and `docs/sbom.md` row `K7` -- named different script
lists, neither of which had `tools/kconfig-delta.py`, which the build driver
calls.  An archive assembled from either list would not have rebuilt the image.
This tool takes its file list from the declarations the build itself reads,
packs it reproducibly, and refuses, with the reason, when a declared input is
missing.

WHAT IT PACKS, AND WHERE EACH PART COMES FROM
--------------------------------------------
  repository  every file tracked at --rev (default HEAD), read from git
              objects and never from the working tree, minus the paths
              `SOURCES.json` `corresponding_source.repository.exclude` names.
              A gitlink (`upstream/`) is listed in the manifest, not packed.
  trees       for each tree `corresponding_source.trees` names, the declared
              paths, read from git objects at the tree's `pin` -- a drop's
              working tree is not its pin (three files of the base drop were
              deleted from its working tree on 2026-10-04) -- and placed at the
              tree's own `dest`.  A blob git calls binary (a NUL byte in its
              first 8,000 bytes, git's own test) is LEFT OUT and listed in the
              manifest with its sha256: the drops carry prebuilt objects, host
              tools and images inside their source trees, and the boundary
              below excludes them.
  imported    every `SOURCES.json` entry whose `role` is `imported-source`,
              read from <fetched>/<dest> and refused unless its sha256 (and its
              byte count, where declared) match.  Placed at its `dest`.
  manifest    CORRESPONDING-SOURCE.tsv inside the archive, and the same bytes
              beside it: every member with sha256, bytes, mode, type and
              origin; every left-out blob; every gitlink.

The boundary is the owner's (2026-10-05): every source file that enters the
image and every build script, configuration and patch that produces it; not the
compilers, and not prebuilt vendor binaries.

DETERMINISM
-----------
Members sorted bytewise by path.  Every mtime is the epoch
`config/rlxfw-build-stamp` declares, the one the kernel and the initramfs are
built with.  uid and gid 0, empty owner names.  0755 for a blob git records as
100755, 0644 for every other file, 0777 for a symlink; no directory entries.
POSIX pax format, xz at preset 6.  The xz bytes also depend on the liblzma
version; the uncompressed tar's sha256, in the run record, does not.

WHAT MAKES THE LIST A DERIVATION AND NOT A SECOND LIST
------------------------------------------------------
The declared tree paths are checked against everything else that names a
vendor file, and a disagreement is a refusal:
  * every vendor file a declaration changes -- `tools/modrecord.py`'s own
    derivation over config/ at --rev -- lies under a declared path and exists
    at the pin;
  * the drop `config/rlxfw-marks.tsv`'s `# baseline-drop:` header names is a
    declared tree, at that tree's pin;
  * every archived external input is `fetch: now`, so `tools/fetch-sources.sh`
    plans it for a recipient;
  * no `$REPO/` source `config/rlxfw-initramfs.tsv` puts in the image lies
    under an exclusion, no `file` row reads `$UNIT/` (this unit's own flash),
    and config/ is never excluded (RECIPE_ID digests all of it);
  * with --cell, every drop file a kernel build read (its kbuild .cmd
    records) lies under a declared path, and no left-out blob is named there.

WHAT IT REFUSES TO PACK
-----------------------
  * this unit's `H601` bytes: with --dump, every member is scanned with
    `tools/flashwin.py`'s own probes and scanner (imported, not restated); the
    dump must hash to `tools/leakscan.py`'s DUMP_SHA256, so the probes are this
    unit's window and not another file's.  --no-dump-scan has to be asked for,
    and the manifest then says NOT RUN instead of CLEAN.
  * the reference dump itself (a member whose sha256 is DUMP_SHA256), and any
    member named `stage2.bin`;
  * a tracked file that the repository's own `.gitignore` rules ignore, which
    is how a dump, a datasheet or a vendor binary gets force-added;
  * any input or output path under `$FWRE_WORK/disclosure/`; output inside the
    repository or on a DrvFs mount (`/mnt/<drive>/`).

WHERE IT FAILS, stated before it was used
-----------------------------------------
1. The declared tree paths are cross-checked against what the declarations
   CHANGE and, with --cell, against what ONE kernel build read.  A drop file
   the userspace or image steps read and nothing declares is invisible: the
   image step (`tools/rtkimage.py build`) runs `rtkload/lzma-26` and
   `rtkload/cvimg` out of the staged kernel tree, and both are left-out
   binaries.  A rebuild takes them, and the toolchain, from the drop at its pin.
2. git's binary rule is a heuristic: a text file with a NUL in its first 8,000
   bytes is left out (and listed), and a binary without one is packed.
3. The H601 scan has `flashwin`'s gaps: runs under 16 bytes, byte-swapped or
   encoded copies, and anything inside a compressed member (the iperf3
   tarball's inside is not seen; its sha256 is upstream's, verified).
4. The ignore check reads the `.gitignore` files on disk, and refuses unless
   each one tracked at --rev is byte-identical there.
5. Nothing here rebuilds the image from the archive.  That the archive is
   sufficient is a claim only a rebuild in an empty directory can test.

Usage
    srcarchive.py build --out DIR (--dump FILE | --no-dump-scan)
                        [--repo DIR] [--rev REV] [--fetched DIR]
                        [--cell DIR [--cell-other-recipe]] [--dry-run]
    srcarchive.py verify --archive FILE [--sums FILE]
    srcarchive.py check-decl [--repo DIR]
    srcarchive.py --self-test

--fetched is where the `dest` paths of SOURCES.json resolve (default: --repo,
which is where `tools/fetch-sources.sh` puts them).  --cell is a kernel build
cell, `<...>/r3-4/cells/<name>`; its manifest is `<...>/r3-4/out/<name>.manifest`.
Exit status: 0 done, 1 a verify or self-test finding, 3 a refusal.
"""

import hashlib
import importlib.util
import io
import json
import lzma
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GIT = "git"
FORMAT = 1
MANIFEST_NAME = "CORRESPONDING-SOURCE.tsv"
XZ_PRESET = 6
#: git's own binary test (xdiff `buffer_is_binary`): a NUL in the first 8000.
BINARY_PROBE = 8000
LICENCE_RX = re.compile(r"^(COPYING|COPYRIGHT|LICEN[CS]E|NOTICE)([._-].*)?$",
                        re.I)
TARBALL_RX = re.compile(r"\.(tar\.gz|tgz|tar\.xz|tar\.bz2|tar)$")
DRVFS_RX = re.compile(r"^/mnt/[A-Za-z]/")
SHA_RX = re.compile(r"^[0-9a-f]{64}$")
PIN_RX = re.compile(r"^[0-9a-f]{40}$")
REL_RX = re.compile(r"^[A-Za-z0-9._@+-]+(/[A-Za-z0-9._@+-]+)*$")
#: `git -C REPO` must mean REPO; an inherited GIT_DIR (a hook sets one) would
#: silently read another repository.  docmove.py strips the same set.
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                 "GIT_COMMON_DIR", "GIT_NAMESPACE")


class Refusal(Exception):
    """An input this tool cannot honestly pack or report on.  Exit 3."""


def refuse(msg):
    raise Refusal(msg)


def _load(name):
    """A sibling tool, imported by path, so its rules are not restated here."""
    path = os.path.join(HERE, name + ".py")
    spec = importlib.util.spec_from_file_location("srcarchive_" + name, path)
    if spec is None or not os.path.isfile(path):
        refuse("cannot load tools/%s.py, whose rules this tool uses instead "
               "of a copy" % name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fwre_work():
    return os.environ.get("FWRE_WORK") or "/home/key/fwre-work"


def _under(path, parent):
    p, q = os.path.realpath(path), os.path.realpath(parent)
    return p == q or p.startswith(q.rstrip(os.sep) + os.sep)


def guard_path(path, what, work):
    if _under(path, os.path.join(work, "disclosure")):
        refuse("%s %s is under $FWRE_WORK/disclosure/, which nothing in this "
               "project opens" % (what, path))


# --------------------------------------------------------------------------
# git, object store only
# --------------------------------------------------------------------------

def _env(extra=None):
    env = dict((k, v) for k, v in os.environ.items()
               if k not in GIT_REDIRECTS)
    if extra:
        env.update(extra)
    return env


def git(repo, args, what, extra=None, ok=(0,)):
    try:
        r = subprocess.run([GIT, "-C", repo] + list(args),
                           capture_output=True, env=_env(extra))
    except OSError as e:
        refuse("%s: cannot run git: %s" % (what, e.strerror))
    if r.returncode not in ok:
        refuse("%s: `git %s` exited %d: %s"
               % (what, " ".join(args[:2]), r.returncode,
                  r.stderr.decode("utf-8", "replace").strip()[:300]))
    return r.returncode, r.stdout


def ls_tree(repo, rev, paths, what):
    _rc, out = git(repo, ["ls-tree", "-r", "-z", "--full-tree", rev, "--"]
                   + list(paths), what)
    ents = []
    for rec in out.split(b"\0"):
        if not rec:
            continue
        meta, raw = rec.split(b"\t", 1)
        mode, typ, sha = meta.decode("ascii").split()
        try:
            path = raw.decode("utf-8")
        except UnicodeDecodeError:
            refuse("%s: a path that is not UTF-8 (%r); a pax name would be a "
                   "guess" % (what, raw[:60]))
        ents.append((mode, typ, sha, path))
    return ents


class Blobs(object):
    """`git cat-file --batch`, so every byte packed is a git object's."""

    def __init__(self, repo, what):
        self.what = what
        try:
            self.p = subprocess.Popen([GIT, "-C", repo, "cat-file", "--batch"],
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, env=_env())
        except OSError as e:
            refuse("%s: cannot run git cat-file: %s" % (what, e.strerror))

    def read(self, sha):
        self.p.stdin.write(sha.encode("ascii") + b"\n")
        self.p.stdin.flush()
        hdr = self.p.stdout.readline().split()
        if len(hdr) != 3 or hdr[1] != b"blob":
            refuse("%s: object %s is not a readable blob (%r)"
                   % (self.what, sha[:12], b" ".join(hdr)[:60]))
        n = int(hdr[2])
        data = self.p.stdout.read(n)
        self.p.stdout.read(1)
        if len(data) != n:
            refuse("%s: object %s came back short" % (self.what, sha[:12]))
        return data

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait()
        except OSError:
            pass


class GitView(object):
    """A repository at one commit, read from its object store."""

    def __init__(self, repo, rev):
        self.repo = repo
        _rc, out = git(repo, ["rev-parse", "--verify", "-q",
                              rev + "^{commit}"], "--rev %s" % rev)
        self.rev = out.decode("ascii").strip()
        self.ents = ls_tree(repo, self.rev, [], "the repository at %s"
                            % self.rev[:12])
        self.by = dict((p, (m, t, s)) for m, t, s, p in self.ents)
        self.blobs = Blobs(repo, "the repository")

    def has(self, path):
        e = self.by.get(path)
        return e is not None and e[1] == "blob"

    def read(self, path):
        if not self.has(path):
            refuse("%s is not tracked at %s" % (path, self.rev[:12]))
        return self.blobs.read(self.by[path][2])

    def regular_under(self, prefix):
        return sorted(p for m, t, s, p in self.ents
                      if t == "blob" and m != "120000"
                      and p.startswith(prefix + "/"))

    def label(self):
        return self.rev[:12]


class DiskView(object):
    """A working tree, for `check-decl`: what CI and the desk have on disk."""

    def __init__(self, root):
        self.root = root
        self.rev = None

    def has(self, path):
        return os.path.isfile(os.path.join(self.root, path))

    def read(self, path):
        try:
            with open(os.path.join(self.root, path), "rb") as f:
                return f.read()
        except OSError as e:
            refuse("cannot read %s: %s" % (path, e.strerror))

    def regular_under(self, prefix):
        out = []
        base = os.path.join(self.root, prefix)
        for root, dirs, files in os.walk(base):
            dirs.sort()
            for n in files:
                p = os.path.join(root, n)
                if os.path.isfile(p) and not os.path.islink(p):
                    out.append(os.path.relpath(p, self.root).replace(os.sep, "/"))
        return sorted(out)

    def label(self):
        return "the working tree"


# --------------------------------------------------------------------------
# the declarations
# --------------------------------------------------------------------------

def recipe_id(view):
    """tools/rlxfw-kbuild.sh's RECIPE_ID: `find config -type f -print0 |
    LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -c1-8`.  The
    self-test runs that script's own --dry-run as the second source."""
    lines = []
    for p in sorted(view.regular_under("config"),
                    key=lambda s: s.encode("utf-8")):
        lines.append("%s  %s\n" % (hashlib.sha256(view.read(p)).hexdigest(), p))
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()[:8]


def stamp_epoch(view):
    """The epoch tools/rlxfw-kbuild.sh reads: comments stripped, blanks
    removed, the first line that is all digits."""
    path = "config/rlxfw-build-stamp"
    if not view.has(path):
        refuse("%s is missing at %s: the archive's mtime is the declared build "
               "stamp, and a clock reading in its place would make two packs "
               "of one commit differ" % (path, view.label()))
    for raw in view.read(path).decode("utf-8", "replace").split("\n"):
        s = re.sub(r"#.*", "", raw).replace(" ", "").replace("\t", "")
        if re.match(r"^[0-9]+$", s):
            return int(s)
    refuse("%s declares no epoch" % path)


def _rel_ok(p):
    return isinstance(p, str) and REL_RX.match(p) is not None and \
        ".." not in p.split("/")


def _decl_list(items, what):
    if not isinstance(items, list) or not items:
        refuse("SOURCES.json corresponding_source: %s must be a non-empty list"
               % what)
    out = []
    for it in items:
        if not isinstance(it, dict) or not _rel_ok(it.get("path")) \
                or not str(it.get("why", "")).strip():
            refuse("SOURCES.json corresponding_source: every entry of %s needs "
                   "a relative `path` and a non-empty `why` (got %r)"
                   % (what, it))
        out.append(it["path"])
    if len(set(out)) != len(out):
        refuse("SOURCES.json corresponding_source: %s names a path twice" % what)
    return out


def _covered(path, roots):
    return any(path == r or path.startswith(r + "/") for r in roots)


def read_decl(view, cfgdir):
    """Everything the archive's list is derived from, read at one view, and
    every check that needs no drop and no fetched file.  `cfgdir` is a
    directory holding that view's config/ (modrecord reads a directory)."""
    d = {"problems": []}
    prob = d["problems"].append
    try:
        src = json.loads(view.read("SOURCES.json").decode("utf-8"))
    except ValueError as e:
        refuse("SOURCES.json at %s does not parse: %s" % (view.label(), e))
    cs = src.get("corresponding_source")
    if not isinstance(cs, dict):
        refuse("SOURCES.json at %s has no `corresponding_source` object. "
               "Nothing then declares what the archive carries, and a list "
               "this tool made up would be the second list the declaration "
               "exists to prevent" % view.label())
    d["sources"] = src
    rep = cs.get("repository", {})
    d["exclude"] = _decl_list(rep.get("exclude", []),
                              "repository.exclude") \
        if rep.get("exclude") else []
    d["exclude_why"] = dict((e["path"], e["why"])
                            for e in rep.get("exclude", []) or [])
    trees = cs.get("trees")
    if not isinstance(trees, dict) or not trees:
        refuse("SOURCES.json corresponding_source.trees must name at least one "
               "source tree")
    st = dict((t.get("id"), t) for t in src.get("source_trees", []))
    d["trees"] = []
    for tid in sorted(trees):
        paths = _decl_list(trees[tid], "trees.%s" % tid)
        t = st.get(tid)
        if t is None:
            refuse("corresponding_source.trees names %r, which is not a "
                   "SOURCES.json source tree" % tid)
        if not PIN_RX.match(str(t.get("pin", ""))):
            refuse("source tree %s has no 40-hex `pin`: an archive read from a "
                   "moving branch is not a citable artefact" % tid)
        if not _rel_ok(t.get("dest")):
            refuse("source tree %s has no relative `dest`" % tid)
        if t.get("fetch") != "now":
            prob("source tree %s is `fetch: %s`, not `now`: tools/fetch-sources"
                 ".sh does not plan it, so a recipient cannot obtain what this "
                 "archive cites" % (tid, t.get("fetch")))
        d["trees"].append({"id": tid, "pin": t["pin"], "dest": t["dest"],
                           "paths": paths})
    d["imported"] = []
    for e in src.get("documents", []) + src.get("source_trees", []):
        if e.get("role") != "imported-source":
            continue
        if not _rel_ok(e.get("dest")) or not SHA_RX.match(
                str(e.get("sha256", ""))):
            refuse("imported source %s needs a relative `dest` and a 64-hex "
                   "`sha256`: an unpinned import is not corresponding source"
                   % e.get("id"))
        if e.get("fetch") != "now":
            prob("imported source %s is `fetch: %s`, not `now`: tools/fetch-"
                 "sources.sh does not plan it" % (e.get("id"), e.get("fetch")))
        d["imported"].append(e)
    if not d["imported"]:
        prob("SOURCES.json declares no `imported-source` entry, and the image "
             "carries /bin/iperf3, whose source is one")
    d["stamp"] = stamp_epoch(view)
    d["recipe"] = recipe_id(view)
    for ex in d["exclude"]:
        if ex == "config" or ex.startswith("config/"):
            prob("repository.exclude names %s, but RECIPE_ID digests every file "
                 "under config/, so the image's identity could not be "
                 "recomputed from the archive" % ex)

    # -- the four declarations, through modrecord's own derivation
    modrecord = _load("modrecord")
    err, keep = io.StringIO(), sys.stderr
    sys.stderr = err
    try:
        mr = modrecord.derive(cfgdir)
    except SystemExit:
        refuse("tools/modrecord.py refused the declarations: %s"
               % err.getvalue().strip())
    finally:
        sys.stderr = keep
    d["vendor_files"] = sorted(mr["files"])
    m = re.match(r"^(\S+)\s*@\s*([0-9a-f]{7,40})$", mr["drop"].strip())
    d["marks_tree"] = None
    if not m:
        prob("config/rlxfw-marks.tsv's `# baseline-drop: %s` is not "
             "`<dest> @ <commit>`" % mr["drop"])
    else:
        hit = [t for t in d["trees"] if t["dest"] == m.group(1)]
        if not hit:
            prob("config/rlxfw-marks.tsv's baseline drop %s is not a declared "
                 "corresponding_source tree" % m.group(1))
        elif not hit[0]["pin"].startswith(m.group(2)):
            prob("config/rlxfw-marks.tsv's baseline drop is at %s and "
                 "SOURCES.json pins %s at %s" % (m.group(2), hit[0]["id"],
                                                 hit[0]["pin"][:12]))
        else:
            d["marks_tree"] = hit[0]
            for vf in d["vendor_files"]:
                if not _covered(vf, hit[0]["paths"]):
                    prob("a declaration changes %s, which lies outside every "
                         "declared path of %s: the archive would ship the "
                         "patch and not the file it patches"
                         % (vf, hit[0]["id"]))

    # -- what the image reads from this repository
    mki = _load("mkinitramfs")
    mki._RAISE = True
    decl = "config/rlxfw-initramfs.tsv"
    if not view.has(decl):
        refuse("%s is missing at %s" % (decl, view.label()))
    try:
        ents = mki.parse_decl(decl, text=view.read(decl).decode("utf-8"))
    except mki.Refused as e:
        refuse("tools/mkinitramfs.py refused %s: %s" % (decl, e))
    d["image_reads"] = []
    for e in ents:
        if e.kind != "file":
            continue
        if e.source.startswith("$UNIT/"):
            prob("%s line %d puts %s in the image from $UNIT -- this unit's "
                 "own flash -- which no public archive may carry"
                 % (decl, e.lineno, e.path))
        elif e.source.startswith("$REPO/"):
            rel = e.source[len("$REPO/"):]
            d["image_reads"].append(rel)
            if _covered(rel, d["exclude"]):
                prob("%s line %d reads %s, which repository.exclude leaves "
                     "out of the archive" % (decl, e.lineno, rel))
            elif not rel.startswith("build/") and not view.has(rel):
                prob("%s line %d reads %s, which is not in %s"
                     % (decl, e.lineno, rel, view.label()))
        else:
            prob("%s line %d: source %r is neither $REPO/ nor $UNIT/"
                 % (decl, e.lineno, e.source))
    return d


def extract_config(view, dest):
    for p in view.regular_under("config"):
        out = os.path.join(dest, *p.split("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(view.read(p))
    return os.path.join(dest, "config")


def _problems(d):
    if d["problems"]:
        refuse("the declarations disagree (%d):\n  %s"
               % (len(d["problems"]), "\n  ".join(d["problems"])))


# --------------------------------------------------------------------------
# the plan
# --------------------------------------------------------------------------

def ignored_tracked(view, what):
    """Tracked files the repository's own .gitignore rules ignore, at the
    view's commit.  The rules are read from disk, so each .gitignore tracked
    at that commit must be the one on disk."""
    for p in sorted(view.by):
        if p == ".gitignore" or p.endswith("/.gitignore"):
            disk = os.path.join(view.repo, *p.split("/"))
            try:
                with open(disk, "rb") as f:
                    same = f.read() == view.read(p)
            except OSError:
                same = False
            if not same:
                refuse("%s: %s on disk is not the one tracked at %s, so the "
                       "ignore check would test other rules" % (what, p,
                                                                view.label()))
    with tempfile.TemporaryDirectory(prefix="srcarchive-idx-") as td:
        idx = {"GIT_INDEX_FILE": os.path.join(td, "index")}
        git(view.repo, ["read-tree", view.rev], what, extra=idx)
        _rc, out = git(view.repo, ["ls-files", "-z", "-c", "-i",
                                   "--exclude-per-directory=.gitignore"],
                       what, extra=idx)
    return sorted(x.decode("utf-8", "replace") for x in out.split(b"\0") if x)


def plan(view, d, fetched, work):
    """-> (members, gitlinks, excluded_counts).  A member is a dict:
    arc, origin, kind (file|symlink), mode, src ('blob', reader, sha) or
    ('mem', bytes), vendor (True for a drop blob), licence (bool)."""
    members, gitlinks = [], []
    exc = dict((p, [0, 0]) for p in d["exclude"])
    _rc, sizes = git(view.repo, ["ls-tree", "-r", "-z", "-l", "--full-tree",
                                 view.rev], "sizes")
    size_of = {}
    for rec in sizes.split(b"\0"):
        if rec:
            meta, raw = rec.split(b"\t", 1)
            f = meta.split()
            if f[1] == b"blob":
                size_of[raw.decode("utf-8", "replace")] = int(f[3])
    for mode, typ, sha, p in view.ents:
        hit = [x for x in d["exclude"] if p == x or p.startswith(x + "/")]
        if hit:
            exc[hit[0]][0] += 1
            exc[hit[0]][1] += size_of.get(p, 0)
            continue
        if typ == "commit":
            gitlinks.append((p, sha))
            continue
        members.append({"arc": p, "origin": "repository",
                        "kind": "symlink" if mode == "120000" else "file",
                        "mode": 0o755 if mode == "100755" else 0o644,
                        "src": ("blob", view.blobs, sha), "vendor": False,
                        "licence": LICENCE_RX.match(p.rsplit("/", 1)[-1])
                        is not None})
    for x, (n, _b) in exc.items():
        if n == 0:
            refuse("repository.exclude names %s, which matches nothing "
                   "tracked at %s: a stale exclusion is a declaration nobody "
                   "can check" % (x, view.label()))
    bad = [p for p in ignored_tracked(view, "the ignore check")
           if not _covered(p, d["exclude"])]
    if bad:
        refuse("%d tracked file(s) match the repository's own .gitignore -- "
               "the way a dump, a datasheet or a vendor binary is force-added:"
               "\n  %s" % (len(bad), "\n  ".join(bad[:20])))

    readers = []
    for t in d["trees"]:
        drop = os.path.join(fetched, *t["dest"].split("/"))
        guard_path(drop, "tree %s" % t["id"], work)
        if not os.path.isdir(drop):
            refuse("tree %s: no clone at %s (SOURCES.json dest %s under "
                   "--fetched); tools/fetch-sources.sh clones it"
                   % (t["id"], drop, t["dest"]))
        rc, _o = git(drop, ["cat-file", "-e", t["pin"] + "^{commit}"],
                     "tree %s" % t["id"], ok=(0, 1, 128))
        if rc != 0:
            refuse("tree %s: the pin %s is not in the clone at %s (a --depth 1 "
                   "clone of a branch that moved does not have it)"
                   % (t["id"], t["pin"][:12], drop))
        ents = ls_tree(drop, t["pin"], t["paths"], "tree %s" % t["id"])
        reader = Blobs(drop, "tree %s" % t["id"])
        readers.append(reader)
        t["blob_paths"] = set()
        t["dirs"] = set()
        for want in t["paths"]:
            n = [p for m_, ty, s, p in ents
                 if p == want or p.startswith(want + "/")]
            if not n:
                refuse("tree %s: the declared path %s is not in the tree at "
                       "its pin %s" % (t["id"], want, t["pin"][:12]))
            if any(p != want for p in n):
                t["dirs"].add(want)
        for mode, typ, sha, p in ents:
            arc = t["dest"] + "/" + p
            if typ == "commit":
                gitlinks.append((arc, sha))
                continue
            t["blob_paths"].add(p)
            root = [w for w in t["dirs"] if p.startswith(w + "/")
                    and "/" not in p[len(w) + 1:]]
            members.append({"arc": arc, "origin": t["id"],
                            "kind": "symlink" if mode == "120000" else "file",
                            "mode": 0o755 if mode == "100755" else 0o644,
                            "src": ("blob", reader, sha), "vendor": True,
                            "licence": bool(root) and LICENCE_RX.match(
                                p.rsplit("/", 1)[-1]) is not None})
        if d.get("marks_tree") is t or (d.get("marks_tree") or {}).get(
                "id") == t["id"]:
            missing = [vf for vf in d["vendor_files"]
                       if vf not in t["blob_paths"]]
            if missing:
                refuse("a declaration changes %d file(s) that tree %s does not "
                       "have at its pin: %s" % (len(missing), t["id"],
                                                ", ".join(missing[:10])))

    for e in d["imported"]:
        p = os.path.join(fetched, *e["dest"].split("/"))
        guard_path(p, "imported source %s" % e["id"], work)
        if not os.path.isfile(p):
            refuse("imported source %s: no file at %s; tools/fetch-sources.sh "
                   "fetches it (SOURCES.json dest %s, `fetch: now`)"
                   % (e["id"], p, e["dest"]))
        with open(p, "rb") as f:
            data = f.read()
        got = hashlib.sha256(data).hexdigest()
        if got != e["sha256"]:
            refuse("imported source %s: %s hashes to %s..., and SOURCES.json "
                   "pins %s...: not the bytes this project was built from"
                   % (e["id"], p, got[:16], e["sha256"][:16]))
        if "bytes" in e and int(e["bytes"]) != len(data):
            refuse("imported source %s: %d bytes, SOURCES.json says %s"
                   % (e["id"], len(data), e["bytes"]))
        members.append({"arc": e["dest"], "origin": e["id"], "kind": "file",
                        "mode": 0o644, "src": ("mem", data), "vendor": False,
                        "licence": False})
    seen = {}
    for m in members:
        if m["arc"] in seen or m["arc"] == MANIFEST_NAME:
            refuse("two members would share the archive path %s (%s and %s)"
                   % (m["arc"], seen.get(m["arc"], "the manifest"),
                      m["origin"]))
        seen[m["arc"]] = m["origin"]
    return members, gitlinks, exc, readers


def content(m):
    kind, a = m["src"][0], m["src"][1:]
    return a[0].read(a[1]) if kind == "blob" else a[0]


def classify(data):
    if b"\0" not in data[:BINARY_PROBE]:
        return None
    if data[:4] == b"\x7fELF":
        return "elf"
    if data[:8] == b"!<arch>\n":
        return "ar"
    return "binary"


def tarball_licences(name, data):
    """Licence files at the top directory of an imported tarball."""
    out = []
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
            for ti in tf.getmembers():
                parts = ti.name.strip("/").split("/")
                if ti.isfile() and len(parts) == 2 and LICENCE_RX.match(
                        parts[1]):
                    out.append((ti.name.strip("/"),
                                tf.extractfile(ti).read()))
    except (tarfile.TarError, OSError, EOFError) as e:
        refuse("imported source %s is a tarball this tool cannot read: %s"
               % (name, e))
    return sorted(out)


# --------------------------------------------------------------------------
# the cell check
# --------------------------------------------------------------------------

TOKEN_SPLIT = re.compile(r"[\s:=,;'\"()\\]+")


def cell_reads(celldir):
    top = os.path.join(celldir, "top")
    kdir = os.path.join(top, "linux-2.6.30")
    if not os.path.isdir(kdir):
        refuse("--cell %s has no top/linux-2.6.30" % celldir)
    topr = os.path.realpath(top)
    seen, ncmd = set(), 0
    # The whole staged top, symlinks not followed: the kernel tree, and the
    # board directory its arch/rlx/bsp link reaches (kbuild writes the BSP's
    # .cmd records there), but not the toolchain link.
    for root, dirs, files in os.walk(top):
        dirs.sort()
        for f in sorted(files):
            if not (f.startswith(".") and f.endswith(".cmd")):
                continue
            ncmd += 1
            with open(os.path.join(root, f), "r", encoding="latin-1") as fh:
                text = fh.read()
            for tok in TOKEN_SPLIT.split(text):
                if not tok or tok.startswith("-") or "$" in tok:
                    continue
                p = tok if os.path.isabs(tok) else os.path.join(kdir, tok)
                rp = os.path.realpath(p)
                if rp.startswith(topr + os.sep) and os.path.isfile(rp):
                    seen.add(rp[len(topr) + 1:].replace(os.sep, "/"))
    if ncmd == 0:
        refuse("--cell %s holds no kbuild .cmd record: a check over zero "
               "records passes everything" % celldir)
    return ncmd, seen


def cell_check(celldir, d, left_out, allow_other):
    name = os.path.basename(os.path.normpath(celldir))
    mpath = os.path.join(os.path.dirname(os.path.dirname(
        os.path.normpath(celldir))), "out", name + ".manifest")
    try:
        with open(mpath, encoding="utf-8") as f:
            man = dict(ln.rstrip("\n").split("\t", 1) for ln in f
                       if "\t" in ln)
    except OSError:
        refuse("--cell %s: no build manifest at %s" % (celldir, mpath))
    t = d.get("marks_tree")
    if t is None:
        refuse("--cell needs the marks drop to be a declared tree")
    if man.get("drop") != os.path.basename(t["dest"]):
        refuse("--cell %s was built from drop %r, and the declarations name %s"
               % (name, man.get("drop"), t["dest"]))
    note = ""
    if man.get("recipe_id") != d["recipe"]:
        if not allow_other:
            refuse("--cell %s was built from recipe %s and this archive is "
                   "recipe %s: it is not a build of this config/. Say "
                   "--cell-other-recipe to read it anyway"
                   % (name, man.get("recipe_id"), d["recipe"]))
        note = "; NOT this archive's recipe %s" % d["recipe"]
    _rc, out = git(os.path.join(ARGS_FETCHED[0], *t["dest"].split("/")),
                   ["ls-tree", "-r", "-z", "--name-only", "--full-tree",
                    t["pin"]], "the whole drop")
    in_drop = set(x.decode("utf-8", "replace") for x in out.split(b"\0") if x)
    ncmd, seen = cell_reads(celldir)
    read = sorted(p for p in seen if p in in_drop)
    outside = [p for p in read if not _covered(p, t["paths"])]
    named = [p for p in read if (t["dest"] + "/" + p) in left_out]
    if outside:
        refuse("cell %s read %d drop file(s) no declared path covers: %s"
               % (name, len(outside), ", ".join(outside[:10])))
    if named:
        refuse("cell %s's records name %d left-out binary blob(s): %s"
               % (name, len(named), ", ".join(named[:10])))
    beyond = [p for p in read if not p.startswith("linux-2.6.30/")]
    return ("%s\trecipe %s%s\t%d .cmd record(s), %d drop file(s) read, %d of "
            "them outside linux-2.6.30, all under declared paths; 0 left-out "
            "blob named" % (name, man.get("recipe_id"), note, ncmd, len(read),
                            len(beyond)))


#: set by build(); cell_check reads the drop at the same --fetched
ARGS_FETCHED = [None]


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

class HashWriter(object):
    def __init__(self, f):
        self.f, self.h, self.n = f, hashlib.sha256(), 0

    def write(self, b):
        self.h.update(b)
        self.n += len(b)
        return self.f.write(b)

    def flush(self):
        self.f.flush()


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def flat(origin, path):
    return "%s--%s" % (origin, path.replace("/", "__"))


def build(repo, rev, fetched, out, dump=None, no_scan=False, cell=None,
          cell_other=False, dry_run=False, expect_dump=None, deny=None,
          work=None, quiet=False):
    work = work or fwre_work()
    say = (lambda s: None) if quiet else print
    for what, p in (("--repo", repo), ("--fetched", fetched), ("--out", out),
                    ("--cell", cell), ("--dump", dump)):
        if p:
            guard_path(p, what, work)
    if not dry_run:
        if _under(out, repo):
            refuse("--out %s is inside the repository: the archive is a "
                   "build artefact and goes under $FWRE_WORK/rebuild/" % out)
        if DRVFS_RX.match(os.path.realpath(out) + "/"):
            refuse("--out %s is on a DrvFs mount: CLAUDE.md keeps binaries "
                   "off /mnt/<drive>, where every mode reads 777" % out)
    if dump is None and not no_scan:
        refuse("give --dump FILE (the reference flash dump, for the H601 "
               "scan) or say --no-dump-scan; an unscanned archive has to be "
               "asked for, and its manifest then says NOT RUN")
    if dump is not None and no_scan:
        refuse("--dump and --no-dump-scan together: pick one")
    flashwin = _load("flashwin")
    leakscan = _load("leakscan")
    expect_dump = expect_dump or leakscan.DUMP_SHA256
    deny = set(deny if deny is not None else [leakscan.DUMP_SHA256])
    probes = None
    if dump is not None:
        try:
            with open(dump, "rb") as f:
                ref = f.read()
        except OSError as e:
            refuse("--dump %s: %s" % (dump, e.strerror))
        if _sha(ref) != expect_dump:
            refuse("--dump %s is not the reference dump (its sha256 is not "
                   "tools/leakscan.py's DUMP_SHA256); a scan against another "
                   "file's H601 window says nothing about this unit" % dump)
        err, keep = io.StringIO(), sys.stderr
        sys.stderr = err
        try:
            probes = flashwin.scan_probes(ref, flashwin.FORBIDDEN)
        except SystemExit:
            refuse("tools/flashwin.py refused the dump: %s"
                   % err.getvalue().strip())
        finally:
            sys.stderr = keep
        del ref
    ARGS_FETCHED[0] = fetched

    view = GitView(repo, rev)
    readers = [view.blobs]
    try:
        with tempfile.TemporaryDirectory(prefix="srcarchive-cfg-") as td:
            d = read_decl(view, extract_config(view, td))
        _problems(d)
        members, gitlinks, exc, rd = plan(view, d, fetched, work)
        readers += rd

        # ---- pass 1: read, hash, classify, scan
        left, kept, hits, lic_files = [], [], [], []
        for m in sorted(members, key=lambda x: x["arc"].encode("utf-8")):
            data = content(m)
            m["sha256"], m["bytes"] = _sha(data), len(data)
            if m["kind"] == "file" and m["vendor"]:
                cls = classify(data)
                if cls:
                    left.append((m["arc"], m["sha256"], m["bytes"], cls,
                                 m["origin"]))
                    continue
            if m["sha256"] in deny:
                refuse("%s is the reference flash dump (its sha256 is "
                       "DUMP_SHA256): it identifies one physical device"
                       % m["arc"])
            if m["arc"].rsplit("/", 1)[-1] == "stage2.bin":
                refuse("%s is named stage2.bin: this unit's own loader "
                       "stage, which may not be published" % m["arc"])
            if probes is not None:
                for ch, off, at, n in flashwin.scan_capture(data, probes):
                    hits.append("%s  %s channel, offset %d .. %d, %d byte(s) "
                                "of flash 0x%06X" % (m["arc"], ch, off,
                                                     off + n - 1, n, at))
            if m["licence"]:
                lic_files.append((flat(m["origin"], m["arc"] if m["origin"]
                                       == "repository" else m["arc"][len(
                                           [t for t in d["trees"] if t["id"]
                                            == m["origin"]][0]["dest"]) + 1:]),
                                  data))
            if m["src"][0] == "mem" and TARBALL_RX.search(m["arc"]):
                for p, b in tarball_licences(m["origin"], data):
                    lic_files.append((flat(m["origin"], p), b))
            kept.append(m)
        if probes is not None:
            for name, b in lic_files:
                for ch, off, at, n in flashwin.scan_capture(b, probes):
                    hits.append("licence file %s  %s channel, offset %d, %d "
                                "byte(s) of flash 0x%06X" % (name, ch, off,
                                                             n, at))
        if hits:
            refuse("%d run(s) of H601 content, given as where and never "
                   "what:\n  %s" % (len(hits), "\n  ".join(hits[:20])))
        scan = ("CLEAN: %d member(s) and %d licence file(s) scanned, %d probe(s)"
                " of %d bytes (tools/flashwin.py)" % (
                    len(kept), len(lic_files), len(probes),
                    flashwin.SCAN_WINDOW)) if probes is not None else \
            "NOT RUN (--no-dump-scan)"

        cellnote = "NOT RUN (no --cell)"
        left_set = set(a for a, _s, _b, _c, _o in left)
        if cell:
            cellnote = cell_check(cell, d, left_set, cell_other)

        # ---- the manifest
        top = "rlxfw-src-%s" % view.rev[:12]
        man = manifest_text(view, d, kept, left, gitlinks, exc, scan, cellnote)
        mbytes = man.encode("utf-8")
        if probes is not None:
            for ch, off, at, n in flashwin.scan_capture(mbytes, probes):
                refuse("the manifest itself holds H601 content (%s channel, "
                       "offset %d)" % (ch, off))
        summary = summarise(view, d, kept, left, gitlinks, exc, scan,
                            cellnote, lic_files)
        if dry_run:
            for ln in summary:
                say(ln)
            say("")
            say("RESULT: dry run -- %d member(s) would be packed, nothing "
                "written" % (len(kept) + 1))
            return 0, None

        # ---- pass 2: write
        os.makedirs(out, exist_ok=True)
        names = {"archive": top + ".tar.xz", "manifest": top + ".manifest.tsv",
                 "sums": top + ".SHA256SUMS", "record": top + ".record.tsv"}
        lic_names = [(top + ".licence--" + n, b) for n, b in sorted(lic_files)]
        for n in list(names.values()) + [x for x, _b in lic_names]:
            if os.path.exists(os.path.join(out, n)) or os.path.exists(
                    os.path.join(out, n + ".tmp")):
                refuse("%s already exists in %s; this tool does not "
                       "overwrite a release artefact" % (n, out))
        tmps = []
        try:
            apath = os.path.join(out, names["archive"] + ".tmp")
            tmps.append(apath)
            with open(apath, "wb") as raw:
                with lzma.LZMAFile(raw, "wb", format=lzma.FORMAT_XZ,
                                   check=lzma.CHECK_CRC64,
                                   preset=XZ_PRESET) as xz:
                    hw = HashWriter(xz)
                    with tarfile.open(fileobj=hw, mode="w|",
                                      format=tarfile.PAX_FORMAT) as tf:
                        allm = kept + [{"arc": MANIFEST_NAME, "kind": "file",
                                        "mode": 0o644, "src": ("mem", mbytes),
                                        "sha256": _sha(mbytes),
                                        "bytes": len(mbytes)}]
                        for m in sorted(allm,
                                        key=lambda x: x["arc"].encode("utf-8")):
                            data = content(m)
                            if _sha(data) != m["sha256"]:
                                refuse("%s changed between the two reads"
                                       % m["arc"])
                            ti = tarfile.TarInfo(top + "/" + m["arc"])
                            ti.mtime, ti.uid, ti.gid = d["stamp"], 0, 0
                            ti.uname = ti.gname = ""
                            if m["kind"] == "symlink":
                                ti.type, ti.mode = tarfile.SYMTYPE, 0o777
                                ti.linkname = data.decode("utf-8")
                                tf.addfile(ti)
                            else:
                                ti.type, ti.mode = tarfile.REGTYPE, m["mode"]
                                ti.size = len(data)
                                tf.addfile(ti, io.BytesIO(data))
            tar_sha, tar_n = hw.h.hexdigest(), hw.n
            with open(apath, "rb") as f:
                ablob = f.read()
            outs = [(names["manifest"], mbytes)] + lic_names
            sums = "".join("%s  %s\n" % (_sha(b), n) for n, b in
                           sorted([(names["archive"], ablob)] + outs))
            outs.append((names["sums"], sums.encode("ascii")))
            rec = record_text(view, d, names, ablob, tar_sha, tar_n, mbytes,
                              kept, left, scan, cellnote)
            outs.append((names["record"], rec.encode("utf-8")))
            for n, b in outs:
                p = os.path.join(out, n + ".tmp")
                tmps.append(p)
                with open(p, "wb") as f:
                    f.write(b)
            for p in tmps:
                os.replace(p, p[:-4])
            tmps = []
        finally:
            for p in tmps:
                try:
                    os.remove(p)
                except OSError:
                    pass
        for ln in summary:
            say(ln)
        say("archive        %s  %d bytes  sha256 %s" % (
            os.path.join(out, names["archive"]), len(ablob), _sha(ablob)))
        say("tar            %d bytes uncompressed  sha256 %s" % (tar_n,
                                                                  tar_sha))
        say("manifest       %s  sha256 %s" % (names["manifest"],
                                              _sha(mbytes)))
        say("licences       %d file(s) beside it, in %s" % (len(lic_names),
                                                            names["sums"]))
        say("")
        say("RESULT: %d member(s) packed, %d binary blob(s) left out and "
            "listed" % (len(kept) + 1, len(left)))
        return 0, {"archive": os.path.join(out, names["archive"]),
                   "sha256": _sha(ablob), "bytes": len(ablob),
                   "members": len(kept) + 1, "manifest": mbytes,
                   "tar_sha256": tar_sha, "names": names,
                   "licences": [n for n, _b in lic_names]}
    finally:
        for r in readers:
            r.close()


def manifest_text(view, d, kept, left, gitlinks, exc, scan, cellnote):
    w = []
    w.append("# %s -- what this archive holds and where each file came from."
             "\n" % MANIFEST_NAME)
    w.append("# Written by tools/srcarchive.py %s; `srcarchive.py verify "
             "--archive FILE` checks an archive against it.\n" % VERSION)
    w.append("# format\t%d\n" % FORMAT)
    w.append("# rev\t%s\n" % view.rev)
    w.append("# recipe_id\t%s\tsha256 over config/ at rev, the value "
             "tools/rlxfw-kbuild.sh compiles in as RLXFW_SRC_ID\n"
             % d["recipe"])
    w.append("# mtime\t%d\tconfig/rlxfw-build-stamp\n" % d["stamp"])
    for t in d["trees"]:
        w.append("# tree\t%s\t%s\t%s\t%s\n" % (t["id"], t["pin"], t["dest"],
                                               ",".join(t["paths"])))
    for e in d["imported"]:
        w.append("# imported\t%s\t%s\t%s\n" % (e["id"], e["sha256"],
                                               e["dest"]))
    for x in sorted(exc):
        w.append("# excluded\t%s\t%d file(s), %d bytes\t%s\n"
                 % (x, exc[x][0], exc[x][1], d["exclude_why"][x]))
    w.append("# h601_scan\t%s\n" % scan)
    w.append("# cell\t%s\n" % cellnote)
    w.append("# not packed\tthe toolchain (compilers, binutils, its libc.a "
             "and libgcc.a) and every left-out row below: obtain them from "
             "the tree at its pin\n")
    w.append("# counts\tmembers %d (+ this file)\tleft-out %d\tgitlinks %d\n"
             % (len(kept), len(left), len(gitlinks)))
    w.append("#\n# path\tsha256\tbytes\tmode\ttype\torigin\tnote\n")
    rows = []
    for m in kept:
        rows.append((m["arc"], "%s\t%s\t%d\t%s\t%s\t%s\t%s\n" % (
            m["arc"], m["sha256"], m["bytes"],
            "0777" if m["kind"] == "symlink" else "%04o" % m["mode"],
            m["kind"], m["origin"], "licence" if m["licence"] else "-")))
    for arc, sha, n, cls, origin in left:
        rows.append((arc, "%s\t%s\t%d\t-\tleft-out\t%s\t%s\n"
                     % (arc, sha, n, origin, cls)))
    for arc, sha in gitlinks:
        rows.append((arc, "%s\t%s\t-\t160000\tgitlink\t-\tnot packed\n"
                     % (arc, sha)))
    for _k, r in sorted(rows, key=lambda x: x[0].encode("utf-8")):
        w.append(r)
    return "".join(w)


def summarise(view, d, kept, left, gitlinks, exc, scan, cellnote, lic):
    by = {}
    for m in kept:
        b = by.setdefault(m["origin"], [0, 0])
        b[0] += 1
        b[1] += m["bytes"]
    out = ["srcarchive %s" % VERSION,
           "rev            %s  recipe_id %s  mtime %d"
           % (view.rev, d["recipe"], d["stamp"])]
    n, b = by.get("repository", [0, 0])
    out.append("repository     %d file(s), %d bytes; excluded %s; gitlinks %s"
               % (n, b, ", ".join("%s (%d file(s), %d bytes)"
                                  % (x, exc[x][0], exc[x][1])
                                  for x in sorted(exc)) or "none",
                  ", ".join(p for p, _s in gitlinks) or "none"))
    for t in d["trees"]:
        n, b = by.get(t["id"], [0, 0])
        cls = {}
        for _a, _s, _n, c, o in left:
            if o == t["id"]:
                cls[c] = cls.get(c, 0) + 1
        out.append("tree           %s @ %s: %d file(s), %d bytes; left out "
                   "%d binary blob(s) (%s)" % (
                       t["id"], t["pin"][:12], n, b, sum(cls.values()),
                       ", ".join("%s %d" % kv for kv in sorted(cls.items()))
                       or "none"))
    for e in d["imported"]:
        out.append("imported       %s  %s  sha256 matches SOURCES.json"
                   % (e["id"], e["dest"]))
    out.append("declarations   %d vendor file(s) changed by config/ "
               "(tools/modrecord.py), all under declared paths at the pin"
               % len(d["vendor_files"]))
    out.append("h601 scan      %s" % scan)
    out.append("cell           %s" % cellnote.replace("\t", "  "))
    out.append("licences       %s" % (", ".join(n for n, _b in sorted(lic))
                                      or "none"))
    return out


def record_text(view, d, names, ablob, tar_sha, tar_n, mbytes, kept, left,
                scan, cellnote):
    return "".join([
        "srcarchive-record\t%d\n" % FORMAT,
        "tool\tsrcarchive %s\n" % VERSION,
        "rev\t%s\n" % view.rev,
        "recipe_id\t%s\n" % d["recipe"],
        "archive\t%s\t%d\t%s\n" % (names["archive"], len(ablob), _sha(ablob)),
        "tar\t%d\t%s\n" % (tar_n, tar_sha),
        "manifest\t%s\t%d\t%s\n" % (names["manifest"], len(mbytes),
                                    _sha(mbytes)),
        "members\t%d\n" % (len(kept) + 1),
        "left_out\t%d\n" % len(left),
        "h601_scan\t%s\n" % scan,
        "cell\t%s\n" % cellnote,
        "xz\tpreset %d, liblzma %s\n" % (XZ_PRESET, _liblzma()),
    ])


def _liblzma():
    try:
        import ctypes
        import ctypes.util
        lib = ctypes.CDLL(ctypes.util.find_library("lzma") or "liblzma.so.5")
        lib.lzma_version_string.restype = ctypes.c_char_p
        return lib.lzma_version_string().decode("ascii")
    except (OSError, AttributeError):
        return "unknown"


# --------------------------------------------------------------------------
# verify -- a second reading of a produced archive, by the tar it is
# --------------------------------------------------------------------------

def verify(archive, sums=None, quiet=False):
    say = (lambda s: None) if quiet else print
    finds = []
    try:
        tf = tarfile.open(archive, mode="r:*")
    except (OSError, tarfile.TarError, lzma.LZMAError) as e:
        refuse("--archive %s cannot be read as a tar: %s" % (archive, e))
    names, info, data = [], {}, {}
    with tf:
        try:
            for ti in tf:
                names.append(ti.name)
                info[ti.name] = ti
                if ti.isfile():
                    data[ti.name] = _sha(tf.extractfile(ti).read())
                elif ti.issym():
                    data[ti.name] = _sha(ti.linkname.encode("utf-8"))
        except (tarfile.TarError, lzma.LZMAError, EOFError) as e:
            refuse("--archive %s is truncated or damaged: %s" % (archive, e))
    if not names:
        refuse("--archive %s holds no member" % archive)
    top = names[0].split("/", 1)[0]
    mname = top + "/" + MANIFEST_NAME
    if mname not in info:
        refuse("--archive %s has no %s" % (archive, mname))
    with tarfile.open(archive, mode="r:*") as tf2:
        mtext = tf2.extractfile(mname).read().decode("utf-8")
    hdr, rows = {}, {}
    for ln in mtext.split("\n"):
        if ln.startswith("# ") and "\t" in ln:
            k, v = ln[2:].split("\t", 1)
            hdr.setdefault(k, v)
        elif ln and not ln.startswith("#"):
            f = ln.split("\t")
            if len(f) != 7:
                refuse("manifest row with %d field(s): %r" % (len(f), ln[:80]))
            rows[f[0]] = f
    stamp = int(hdr.get("mtime", "x\t").split("\t")[0]) \
        if hdr.get("mtime", "").split("\t")[0].isdigit() else None
    if stamp is None:
        refuse("the manifest has no `mtime` header")
    if [n.encode("utf-8") for n in names] != sorted(
            n.encode("utf-8") for n in names):
        finds.append("members are not in sorted order")
    packed = set()
    for n in names:
        ti = info[n]
        if not n.startswith(top + "/") or ".." in n.split("/") \
                or n.startswith("/"):
            finds.append("%s is outside %s/" % (n, top))
            continue
        if ti.isdir():
            finds.append("%s is a directory entry" % n)
        if ti.uid or ti.gid or ti.uname or ti.gname:
            finds.append("%s is not owned 0:0 with empty names" % n)
        if ti.mtime != stamp:
            finds.append("%s has mtime %d, the manifest says %d"
                         % (n, ti.mtime, stamp))
        if n == mname:
            continue
        rel = n[len(top) + 1:]
        packed.add(rel)
        r = rows.get(rel)
        if r is None:
            finds.append("%s is packed and not in the manifest" % rel)
            continue
        want_type = "symlink" if ti.issym() else "file"
        if r[4] != want_type:
            finds.append("%s is a %s, the manifest says %s"
                         % (rel, want_type, r[4]))
        if r[1] != data.get(n):
            finds.append("%s: sha256 differs from the manifest" % rel)
        mode = "0777" if ti.issym() else "%04o" % ti.mode
        if mode != r[3] or (ti.isfile() and ti.mode not in (0o644, 0o755)):
            finds.append("%s: mode %s, the manifest says %s" % (rel, mode,
                                                                r[3]))
    for rel, r in rows.items():
        if r[4] in ("file", "symlink") and rel not in packed:
            finds.append("%s is in the manifest and not packed" % rel)
    if sums:
        try:
            with open(sums, encoding="utf-8") as f:
                listed = dict((ln.split("  ", 1)[1].strip(), ln.split()[0])
                              for ln in f if "  " in ln)
        except OSError as e:
            refuse("--sums %s: %s" % (sums, e.strerror))
        with open(archive, "rb") as f:
            got = _sha(f.read())
        if listed.get(os.path.basename(archive)) != got:
            finds.append("%s's sha256 is not the one %s lists"
                         % (os.path.basename(archive), sums))
    say("srcarchive %s verify" % VERSION)
    say("archive        %s  (%d member(s), manifest rows %d)"
        % (archive, len(names), len(rows)))
    for x in finds[:30]:
        say("  DIFF  %s" % x)
    say("")
    if finds:
        say("RESULT: %d difference(s) between the archive and its manifest"
            % len(finds))
        return 1
    say("RESULT: every member matches its manifest row; order, owner, mtime "
        "and mode follow the policy")
    return 0


# --------------------------------------------------------------------------
# check-decl -- the declarations alone, on the working tree (no drop needed)
# --------------------------------------------------------------------------

def check_decl(repo, quiet=False):
    say = (lambda s: None) if quiet else print
    view = DiskView(repo)
    d = read_decl(view, os.path.join(repo, "config"))
    _problems(d)
    say("srcarchive %s check-decl" % VERSION)
    say("declarations   %s" % repo)
    say("trees          %s" % ", ".join("%s @ %s (%d path(s))" % (
        t["id"], t["pin"][:12], len(t["paths"])) for t in d["trees"]))
    say("imported       %s" % ", ".join(e["id"] for e in d["imported"]))
    say("vendor files   %d changed by config/, all under declared paths"
        % len(d["vendor_files"]))
    say("image reads    %d $REPO source(s), none excluded"
        % len(d["image_reads"]))
    say("recipe_id      %s" % d["recipe"])
    say("")
    say("RESULT: the declarations agree (the drop and the fetched files are "
        "not read here; `build` reads them)")
    return 0


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

_STAMP = 1788220800


def _hermetic(tmp):
    cfg = os.path.join(tmp, "empty.gitconfig")
    if not os.path.exists(cfg):
        open(cfg, "wb").close()
    env = dict((k, v) for k, v in os.environ.items()
               if not k.startswith("GIT_"))
    # Fixed dates, so every fixture's drop has the same pin and its config/
    # the same RECIPE_ID: the cell cases key on that id.
    env.update(GIT_CONFIG_GLOBAL=cfg, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="srcarchive", GIT_AUTHOR_EMAIL="s@invalid",
               GIT_COMMITTER_NAME="srcarchive",
               GIT_COMMITTER_EMAIL="s@invalid",
               GIT_AUTHOR_DATE="2026-09-01T00:00:00+0000",
               GIT_COMMITTER_DATE="2026-09-01T00:00:00+0000")
    return env


def _put(root, rel, data, mode=None):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    if mode:
        os.chmod(p, mode)
    return p


def _commit(root, env, force=()):
    def g(*a):
        r = subprocess.run([GIT, "-C", root] + list(a), capture_output=True,
                           env=env)
        if r.returncode:
            raise RuntimeError("fixture git %s: %s" % (a[0], r.stderr[:200]))
        return r.stdout
    if not os.path.isdir(os.path.join(root, ".git")):
        g("init", "-q")
    g("add", "-A")
    for p in force:
        g("add", "-f", p)
    g("commit", "-q", "-m", "fixture")
    return g("rev-parse", "HEAD").decode().strip()


def _tgz(files):
    bio = io.BytesIO()
    import gzip
    with gzip.GzipFile(fileobj=bio, mode="wb", mtime=0, filename="") as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) \
                as tf:
            for n, b in files:
                ti = tarfile.TarInfo(n)
                ti.size, ti.mtime = len(b), 0
                tf.addfile(ti, io.BytesIO(b))
    return bio.getvalue()


def _patch(target, old, new):
    return ("prose\n--- a/%s\n+++ b/%s\n@@ -1,1 +1,2 @@\n %s\n+%s\n"
            % (target, target, old, new))


def _fixture(tmp, m=()):
    """A drop, a repository and a fetched root, all synthetic.  `m` names the
    defects to plant; with none, a build must succeed."""
    m = set(m)
    env = _hermetic(tmp)
    fetched = os.path.join(tmp, "fetched")
    drop = os.path.join(fetched, "src-vendor", "fakedrop")
    C = "int f(void)\n{\n\treturn 0;\n}\n"
    _put(drop, "linux-2.6.30/Makefile", "obj-y += a.o\n")
    _put(drop, "linux-2.6.30/COPYING", "GPL version 2, the fixture's\n")
    _put(drop, "linux-2.6.30/init/main.c", C + "anchor_main();\n")
    _put(drop, "linux-2.6.30/arch/x/Kconfig", "config X\n\tbool\n")
    _put(drop, "linux-2.6.30/rtkload/lzma-26", b"\x7fELF\x01\x02\x01\0" * 8,
         0o755)
    _put(drop, "linux-2.6.30/rtkload/nfjrom", b"\x5d\0\0\x80\0" * 20)
    _put(drop, "linux-2.6.30/lib/vendor.a", b"!<arch>\n" + b"\0" * 40)
    _put(drop, "linux-2.6.30/scripts/run.sh", "#!/bin/sh\necho x\n", 0o755)
    os.makedirs(os.path.join(drop, "linux-2.6.30", "arch", "x"),
                exist_ok=True)
    os.symlink("../../../target/hw",
               os.path.join(drop, "linux-2.6.30", "arch", "x", "hw"))
    _put(drop, "plates/b/hw/start.c", C + "anchor_hw();\n")
    cfg_base = "CONFIG_A=y\n# CONFIG_B is not set\n"
    _put(drop, "plates/b/config.base", cfg_base)
    _put(drop, "plates/b/image/fw.bin", b"\0\1\2\3" * 64)
    _put(drop, "plates/other/x.c", C)
    _put(drop, "users/busybox-1.13/LICENSE", "GPL version 2, busybox's\n")
    _put(drop, "users/busybox-1.13/net/b.c", C + "anchor_bb();\n")
    _put(drop, "tc/uclibc/COPYING.LIB", "LGPL 2.1, the fixture's\n")
    _put(drop, "tc/uclibc/libc/x.c", C)
    _put(drop, "tc/uclibc/lib/libc.a", b"!<arch>\n" + b"\0" * 64)
    pin = _commit(drop, env)
    if "pin-missing" in m:
        pin = "0123456789abcdef0123456789abcdef01234567"

    imp = _tgz([("imp-1.0/LICENSE", b"BSD, the fixture's\n"),
                ("imp-1.0/src.c", C.encode())])
    one = b"/* public domain, the fixture's */\n" + C.encode()
    _put(fetched, "refs/imp-1.0.tar.gz", imp)
    if "imported-missing" not in m:
        _put(fetched, "refs/one.c", one if "imported-sha" not in m
             else one + b"x")

    trees = [{"path": "linux-2.6.30", "why": "k"},
             {"path": "plates/b/hw", "why": "bsp"},
             {"path": "plates/b/config.base", "why": "template"},
             {"path": "users/busybox-1.13", "why": "bb"},
             {"path": "tc/uclibc", "why": "libc"}]
    if "path-not-at-pin" in m:
        trees.append({"path": "tc/missing", "why": "planted"})
    excl = [{"path": "bench", "why": "the record"}]
    if "exclude-reads" in m:
        excl.append({"path": "srv", "why": "planted"})
    if "exclude-stale" in m:
        excl.append({"path": "nosuch", "why": "planted"})
    src = {"source_trees": [{"id": "fakedrop", "role": "base", "kind": "git",
                             "url": "https://example.invalid/fakedrop",
                             "pin": pin, "dest": "src-vendor/fakedrop",
                             "fetch": "now"}],
           "documents": [
               {"id": "imp", "role": "imported-source", "kind": "file",
                "dest": "refs/imp-1.0.tar.gz", "bytes": len(imp),
                "sha256": _sha(imp), "fetch": "now"},
               {"id": "one", "role": "imported-source", "kind": "file",
                "dest": "refs/one.c", "sha256": _sha(one),
                "fetch": "later" if "fetch-later" in m else "now"},
               {"id": "adoc", "role": "doc", "dest": "refs/adoc.pdf",
                "fetch": "now"}],
           "corresponding_source": {"repository": {"exclude": excl},
                                    "trees": {"fakedrop": trees}}}
    if "no-cs" in m:
        del src["corresponding_source"]
    repo = os.path.join(tmp, "repo")
    _put(repo, "SOURCES.json", "{ not json" if "bad-json" in m
         else json.dumps(src, indent=1, sort_keys=True) + "\n")
    if "no-stamp" not in m:
        _put(repo, "config/rlxfw-build-stamp", "# the stamp\n%d\n" % _STAMP)
    _put(repo, "config/rlxfw-cflags", "-fno-if-conversion\n")
    drop_hdr = "src-vendor/%s @ %s" % (
        "otherdrop" if "drop-mismatch" in m else "fakedrop", pin[:8])
    rows = ["IN1\tlinux-2.6.30/init/main.c\tafter\tanchor_main();\t"
            "mark();\t\tthe reason\n",
            "B04\tplates/b/hw/start.c\tafter\tanchor_hw();\tmark();\t\t"
            "the reason\n"]
    if "decl-outside" in m:
        rows.append("B99\tplates/other/x.c\tafter\treturn 0;\tmark();\t\t"
                    "planted\n")
    _put(repo, "config/rlxfw-marks.tsv",
         "# fixture marks\n# baseline-drop: %s\n" % drop_hdr + "".join(rows))
    _put(repo, "config/rlxfw-kernel.delta",
         "# fixture delta\n# baseline-drop: %s\n# baseline-file: "
         "plates/b/config.base\n# baseline-sha256: %s\nset\tCONFIG_A\ty\tn"
         "\t-\tthe reason\n" % (drop_hdr, _sha(cfg_base.encode())))
    _put(repo, "config/host-compat/0001-x.patch",
         _patch("arch/x/Kconfig", "config X", "\tdefault y"))
    _put(repo, "config/busybox-patches/0001-y.patch",
         _patch("net/b.c", "int f(void)", "/* y */"))
    irfs = ("# fixture image\ndir\t/etc\t-\t0755\trlxfw\t-\n"
            "file\t/etc/x\t$REPO/srv/x\t0644\trlxfw\t-\n"
            "file\t/init\t$REPO/build/rlxfw-user/init/init\t0755\trlxfw\t-\n")
    if "unit-source" in m:
        irfs += "file\t/bin/v\t$UNIT/bin/v\t0755\tunit\tplanted\n"
    _put(repo, "config/rlxfw-initramfs.tsv", irfs)
    _put(repo, "srv/x", "served\n")
    _put(repo, "LICENSE", "MIT, the fixture's\n")
    _put(repo, "NOTICE", "notice, the fixture's\n")
    _put(repo, "tools/build.sh", "#!/bin/sh\necho build\n", 0o755)
    _put(repo, "bench/cap.log", "a capture\n")
    _put(repo, "refs/README.md", "what goes in refs/\n")
    gi = "refs/*\n!refs/README.md\nbuild/\n" + \
        ("" if "no-bin-rule" in m else "*.bin\n")
    _put(repo, ".gitignore", gi)
    force = []
    if "ignored-tracked" in m:
        _put(repo, "tools/stray.bin", "forced\n")
        force.append("tools/stray.bin")
    if "stage2" in m:
        _put(repo, "tools/stage2.bin", "a file by that name\n")
    if "plant" in m:
        _put(repo, "notes/plant.md", b"text " + m_plant[0] + b" more\n")
    if "dump-member" in m:
        _put(repo, "notes/dump.dat", m_plant[1])
    os.symlink("srv/x", os.path.join(repo, "served-link"))
    _commit(repo, env, force)
    return repo, fetched, drop, pin, env


#: the H601 plant and the synthetic dump, set by self_test before use
m_plant = [b"", b""]


def _synthetic_dump():
    out, h = bytearray(), b"srcarchive synthetic dump"
    while len(out) < 0x10000:
        h = hashlib.sha256(h).digest()
        out += h
    return bytes(out[:0x10000])


def self_test():
    rows = []

    def ck(name, ok, detail=""):
        rows.append((name, bool(ok), detail))

    def attempt(fn, *a, **kw):
        """-> (refused, message, value)."""
        buf, keep = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            return False, buf.getvalue(), fn(*a, **kw)
        except Refusal as e:
            return True, str(e), None
        except Exception as e:                       # noqa: BLE001
            return True, "RAW %s: %s" % (type(e).__name__, e), None
        finally:
            sys.stdout = keep

    dump = _synthetic_dump()
    flashwin = _load("flashwin")
    lo = flashwin.FORBIDDEN[0][0]
    m_plant[0] = dump[lo + 0x100:lo + 0x120]
    m_plant[1] = dump
    dsha = _sha(dump)
    base = tempfile.mkdtemp(prefix="srcarchive-st-")
    work = os.path.join(base, "fwre")
    os.makedirs(os.path.join(work, "disclosure"))
    dpath = os.path.join(base, "dump.bin")
    with open(dpath, "wb") as f:
        f.write(dump)

    def run(tmpname, m=(), **kw):
        tmp = os.path.join(base, tmpname)
        os.makedirs(tmp)
        repo, fetched, drop, pin, env = _fixture(tmp, m)
        out = kw.pop("out", os.path.join(tmp, "out"))
        args = dict(dump=dpath, expect_dump=dsha, deny=[dsha], work=work,
                    quiet=True)
        args.update(kw)
        r = attempt(build, repo, "HEAD", fetched, out, **args)
        return r, repo, fetched, out, tmp

    try:
        # S1 -- the permitting run: a sound fixture packs, and the pack is
        # what the declarations say.
        (refd, msg, val), repo, fetched, out, tmp = run("s1")
        ok = not refd and val and val[1]
        ck("S1  a sound fixture packs", ok, msg[:200] if refd else "")
        names, info = [], {}
        if ok:
            with tarfile.open(val[1]["archive"], "r:xz") as tf:
                for ti in tf:
                    names.append(ti.name)
                    info[ti.name] = ti
            top = names[0].split("/")[0]
            rel = sorted(n[len(top) + 1:] for n in names)
            want = sorted([
                ".gitignore", "LICENSE", "NOTICE", "SOURCES.json",
                MANIFEST_NAME, "config/busybox-patches/0001-y.patch",
                "config/host-compat/0001-x.patch", "config/rlxfw-build-stamp",
                "config/rlxfw-cflags", "config/rlxfw-initramfs.tsv",
                "config/rlxfw-kernel.delta", "config/rlxfw-marks.tsv",
                "refs/README.md", "refs/imp-1.0.tar.gz", "refs/one.c",
                "served-link", "srv/x", "tools/build.sh"] + [
                "src-vendor/fakedrop/" + p for p in (
                    "plates/b/hw/start.c", "plates/b/config.base",
                    "linux-2.6.30/COPYING", "linux-2.6.30/Makefile",
                    "linux-2.6.30/arch/x/Kconfig", "linux-2.6.30/arch/x/hw",
                    "linux-2.6.30/init/main.c", "linux-2.6.30/scripts/run.sh",
                    "tc/uclibc/COPYING.LIB", "tc/uclibc/libc/x.c",
                    "users/busybox-1.13/LICENSE",
                    "users/busybox-1.13/net/b.c")])
        ck("S2  the member set is the declared set: repository minus bench/, "
           "declared drop paths minus binaries, the two imports, the manifest",
           ok and rel == want,
           "extra %s missing %s" % (sorted(set(rel) - set(want))[:5],
                                    sorted(set(want) - set(rel))[:5])
           if ok else "no archive")
        man = val[1]["manifest"].decode() if ok else ""
        lefts = sorted(ln.split("\t")[0] + ":" + ln.split("\t")[6]
                       for ln in man.split("\n")
                       if "\tleft-out\t" in ln)
        ck("S3  every binary blob under a declared path is left out AND "
           "listed with its class; undeclared paths are not listed at all",
           lefts == ["src-vendor/fakedrop/linux-2.6.30/lib/vendor.a:ar",
                     "src-vendor/fakedrop/linux-2.6.30/rtkload/lzma-26:elf",
                     "src-vendor/fakedrop/linux-2.6.30/rtkload/nfjrom:binary",
                     "src-vendor/fakedrop/tc/uclibc/lib/libc.a:ar"],
           str(lefts))
        pol = ok and all(info[n].uid == 0 and info[n].gid == 0
                         and info[n].uname == "" and info[n].gname == ""
                         and info[n].mtime == _STAMP
                         and not info[n].isdir() for n in names)
        ck("S4  owner 0:0, empty names, every mtime the declared stamp, no "
           "directory entries", pol)
        ex = info.get(top + "/tools/build.sh") if ok else None
        nx = info.get(top + "/srv/x") if ok else None
        ln = info.get(top + "/src-vendor/fakedrop/linux-2.6.30/arch/x/hw") \
            if ok else None
        ck("S5  mode 0755 for a 100755 blob, 0644 otherwise, symlinks kept "
           "as symlinks with their target",
           ex is not None and ex.mode == 0o755 and nx.mode == 0o644
           and ln is not None and ln.issym()
           and ln.linkname == "../../../target/hw")
        ck("S6  members are sorted bytewise",
           ok and names == sorted(names, key=lambda s: s.encode()))
        lic = sorted(n.split(".licence--", 1)[1] for n in val[1]["licences"]) \
            if ok else []
        ck("S7  licence files: repository-wide by name, a tree's at the root "
           "of a declared path, an imported tarball's at its top directory",
           lic == ["fakedrop--linux-2.6.30__COPYING",
                   "fakedrop--tc__uclibc__COPYING.LIB",
                   "fakedrop--users__busybox-1.13__LICENSE",
                   "imp--imp-1.0__LICENSE", "repository--LICENSE",
                   "repository--NOTICE"], str(lic))
        rc = attempt(verify, val[1]["archive"],
                     os.path.join(out, val[1]["names"]["sums"]),
                     quiet=True) if ok else (True, "", None)
        ck("S8  verify, a second reading of the produced tar, agrees with the "
           "manifest and SHA256SUMS", not rc[0] and rc[2] == 0, rc[1][:200])
        ck("S9  the manifest records the H601 scan as CLEAN and names the "
           "excluded path with its count", "# h601_scan\tCLEAN" in man
           and "# excluded\tbench\t1 file(s)" in man)

        # S10 -- determinism: a second build of the same commit is the same
        # bytes, archive and manifest.
        (r2, m2, v2), *_ = run("s10")
        same = ok and not r2 and v2[1]["sha256"] == val[1]["sha256"] \
            and v2[1]["manifest"] == val[1]["manifest"]
        ck("S10 two builds of one fixture are byte-identical (archive and "
           "manifest)", same, "" if same else (m2[:120] if r2 else "differ"))

        # S11 -- the recipe id against the build driver's own --dry-run
        kb = os.path.join(HERE, "rlxfw-kbuild.sh")
        rr = subprocess.run(["bash", kb, "st", "--variant", "quiet",
                             "--dry-run"], capture_output=True,
                            env=dict(os.environ, RLXFW_REPO=repo,
                                     FWRE_WORK=work))
        got = re.search(r"recipe=([0-9a-f]{8})",
                        rr.stdout.decode("utf-8", "replace"))
        mine = re.search(r"# recipe_id\t([0-9a-f]{8})", man)
        ck("S11 recipe_id equals tools/rlxfw-kbuild.sh --dry-run's on the "
           "same tree (a second implementation)", got and mine
           and got.group(1) == mine.group(1),
           "driver %s, here %s, rc %d" % (got and got.group(1),
                                          mine and mine.group(1),
                                          rr.returncode))

        # ---- the positive controls: delete or damage one declared input
        cases = [
            ("S12 a declared import deleted from --fetched is a refusal",
             "s12", ("imported-missing",), "no file at"),
            ("S13 an import whose bytes differ from its sha256 is a refusal",
             "s13", ("imported-sha",), "hashes to"),
            ("S14 a declared tree path absent at the pin is a refusal",
             "s14", ("path-not-at-pin",), "is not in the tree at its pin"),
            ("S15 a declaration changing a vendor file outside every declared "
             "path is a refusal", "s15", ("decl-outside",),
             "lies outside every declared path"),
            ("S16 a pin the clone does not have is a refusal", "s16",
             ("pin-missing",), "is not in the clone"),
            ("S17 no corresponding_source declaration is a refusal", "s17",
             ("no-cs",), "no `corresponding_source`"),
            ("S18 a missing build stamp is a refusal", "s18", ("no-stamp",),
             "rlxfw-build-stamp is missing"),
            ("S19 a tracked file the .gitignore rules ignore is a refusal",
             "s19", ("ignored-tracked",), "tools/stray.bin"),
            ("S20 an exclusion covering a file the image reads is a refusal",
             "s20", ("exclude-reads",), "reads srv/x"),
            ("S21 an exclusion matching nothing is a refusal", "s21",
             ("exclude-stale",), "matches nothing"),
            ("S22 an import that fetch-sources.sh does not plan is a refusal",
             "s22", ("fetch-later",), "fetch: later"),
            ("S23 an image file read from $UNIT is a refusal", "s23",
             ("unit-source",), "$UNIT"),
            ("S24 a marks drop that is not the declared tree is a refusal",
             "s24", ("drop-mismatch",), "not a declared corresponding_source"),
            ("S25 malformed SOURCES.json is a refusal with a reason", "s25",
             ("bad-json",), "does not parse"),
            ("S26 a member named stage2.bin is a refusal", "s26",
             ("stage2", "no-bin-rule"), "stage2.bin"),
        ]
        for name, tdir, mut, needle in cases:
            (rf, msg, _v), _r, _f, o, _t = run(tdir, mut)
            clean = not os.path.exists(o) or not os.listdir(o)
            ck(name, rf and needle in msg and "RAW" not in msg and clean,
               msg.replace("\n", " ")[:160])

        # S27/S28 -- H601: a planted run is refused and NOT printed; the same
        # dump over a clean fixture is the permitting half (S1, S9).
        (rf, msg, _v), *_ = run("s27", ("plant",))
        printed = m_plant[0] in msg.encode("latin-1", "replace") or \
            m_plant[0].hex() in msg.lower()
        ck("S27 a planted H601 run is refused, naming where and not what",
           rf and "notes/plant.md" in msg and "flash 0x0061" in msg
           and not printed, msg.replace("\n", " ")[:160])
        (rf, msg, _v), *_ = run("s28", ("dump-member",), dump=None,
                                no_scan=True)
        ck("S28 the reference dump as a member is refused even with the "
           "scan off (the sha256 denylist)", rf and "reference flash dump"
           in msg, msg[:160])
        (rf, msg, _v), *_ = run("s29", (), expect_dump="0" * 64)
        ck("S29 a --dump that is not the reference dump is a refusal",
           rf and "not the reference dump" in msg, msg[:160])
        (rf, msg, _v), *_ = run("s30", (), dump=None)
        ck("S30 neither --dump nor --no-dump-scan is a refusal",
           rf and "--no-dump-scan" in msg, msg[:160])
        (rf, msg, v31), *_ = run("s31", (), dump=None, no_scan=True)
        ck("S31 --no-dump-scan packs and its manifest says NOT RUN",
           not rf and "# h601_scan\tNOT RUN" in v31[1]["manifest"].decode(),
           msg[:160])

        # S32/S33 -- where outputs and inputs may be
        tmp = os.path.join(base, "s32")
        os.makedirs(tmp)
        repo2, fetched2, _d, _p, _e = _fixture(tmp)
        rf, msg, _v = attempt(build, repo2, "HEAD", fetched2,
                              os.path.join(repo2, "out"), dump=dpath,
                              expect_dump=dsha, deny=[dsha], work=work,
                              quiet=True)
        ck("S32 --out inside the repository is a refusal",
           rf and "inside the repository" in msg, msg[:160])
        rf, msg, _v = attempt(build, repo2, "HEAD", fetched2,
                              os.path.join(work, "disclosure", "x"),
                              dump=dpath, expect_dump=dsha, deny=[dsha],
                              work=work, quiet=True)
        ck("S33 an output under $FWRE_WORK/disclosure/ is a refusal",
           rf and "disclosure" in msg, msg[:160])

        # S34 -- verify catches a changed member (the tamper control for S8)
        if ok:
            bad = os.path.join(base, "tampered.tar.xz")
            with tarfile.open(val[1]["archive"], "r:xz") as src, \
                    lzma.open(bad, "wb") as dst:
                with tarfile.open(fileobj=dst, mode="w|",
                                  format=tarfile.PAX_FORMAT) as tf:
                    for ti in src:
                        b = src.extractfile(ti).read() if ti.isfile() else None
                        if ti.name.endswith("/srv/x"):
                            b = b"served!\n"
                            ti.size = len(b)
                        tf.addfile(ti, io.BytesIO(b) if b is not None
                                   else None)
            rf, msg, rcv = attempt(verify, bad, quiet=True)
            ck("S34 verify names a member changed after packing",
               not rf and rcv == 1, msg[:160])
        else:
            ck("S34 verify names a member changed after packing", False,
               "no archive from S1")

        # S35-S37 -- the cell check
        if ok:
            cells = os.path.join(base, "r3-4")
            ctop = os.path.join(cells, "cells", "c1", "top")
            for rel in ("linux-2.6.30/init/main.c", "plates/b/hw/start.c",
                        "plates/other/x.c", "linux-2.6.30/rtkload/lzma-26"):
                _put(ctop, rel, "x\n")
            os.makedirs(os.path.join(ctop, "linux-2.6.30", "arch", "x"),
                        exist_ok=True)
            os.symlink("../../../target/hw",
                       os.path.join(ctop, "linux-2.6.30", "arch", "x", "hw"))
            os.symlink("plates/b", os.path.join(ctop, "target"))

            def cmd(extra=""):
                _put(ctop, "linux-2.6.30/init/.main.o.cmd",
                     "cmd_init/main.o := gcc -Iinclude -c -o init/main.o "
                     "init/main.c\ndeps_init/main.o := \\\n  init/main.c \\\n"
                     "  arch/x/hw/start.c \\\n" + extra)
            man_rec = re.search(r"# recipe_id\t([0-9a-f]{8})", man).group(1)

            def cmanifest(recipe):
                _put(cells, "out/c1.manifest",
                     "rlxfw-build-manifest\t2\ncell\tc1\nrecipe_id\t%s\n"
                     "drop\tfakedrop\n" % recipe)
            cmd()
            cmanifest(man_rec)
            (rf, msg, v35), *_ = run("s35", (), cell=os.path.join(
                cells, "cells", "c1"))
            mn = v35[1]["manifest"].decode() if v35 else ""
            ck("S35 a cell whose records stay inside declared paths passes, "
               "and the manifest says what it read",
               not rf and "1 of them outside linux-2.6.30" in mn, msg[:160])
            cmd("  rtkload/lzma-26 \\\n")
            (rf, msg, _v), *_ = run("s36", (), cell=os.path.join(
                cells, "cells", "c1"))
            ck("S36 a cell record naming a left-out binary is a refusal",
               rf and "left-out binary" in msg, msg[:160])
            cmd("  ../plates/other/x.c \\\n")
            (rf, msg, _v), *_ = run("s37", (), cell=os.path.join(
                cells, "cells", "c1"))
            ck("S37 a cell that read a drop file no declared path covers is "
               "a refusal", rf and "plates/other/x.c" in msg, msg[:160])
            cmd()
            cmanifest("deadbeef")
            (rf, msg, _v), *_ = run("s38", (), cell=os.path.join(
                cells, "cells", "c1"))
            (rf2, msg2, v39), *_ = run("s39", (), cell=os.path.join(
                cells, "cells", "c1"), cell_other=True)
            ck("S38 a cell of another recipe is refused unless asked for, "
               "and then the manifest says so", rf and "recipe deadbeef" in msg
               and not rf2 and "NOT this archive's recipe" in
               v39[1]["manifest"].decode(), (msg + " / " + msg2)[:160])
        else:
            for n in ("S35", "S36", "S37", "S38"):
                ck(n + " the cell check", False, "no archive from S1")

        # S39 -- the CLI refuses without a traceback
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "build",
                            "--out", os.path.join(base, "cli")],
                           capture_output=True)
        e = r.stderr.decode("utf-8", "replace")
        ck("S39 the command line refuses with a reason and no traceback",
           r.returncode == 3 and "srcarchive:" in e and "Traceback" not in e,
           "rc %d: %s" % (r.returncode, e.strip()[:120]))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    # S40 -- LIVE: the repository's own declarations agree.  Without this
    # every case above is about a fixture this file wrote.
    rf, msg, rv = attempt(check_decl, ROOT, quiet=True)
    ck("S40 the repository's own declarations agree (check-decl on %s)"
       % ("the working tree"), not rf and rv == 0,
       msg.replace("\n", " ")[:300])

    print("srcarchive %s self-test" % VERSION)
    bad = 0
    for name, ok, detail in rows:
        bad += not ok
        print("  %s  %-72s %s" % ("ok  " if ok else "FAIL", name,
                                  detail if not ok else ""))
    print("")
    print("%d passed, %d failed" % (len(rows) - bad, bad))
    return 1 if bad else 0


# --------------------------------------------------------------------------

def main(argv):
    if not argv:
        sys.stderr.write(__doc__)
        return 3
    if argv[0] in ("--self-test", "self-test"):
        return self_test()
    cmd, rest = argv[0], argv[1:]
    flags = {"--dry-run", "--no-dump-scan", "--cell-other-recipe"}
    vals = {"--out", "--dump", "--repo", "--rev", "--fetched", "--cell",
            "--archive", "--sums"}
    a = {}
    i = 0
    while i < len(rest):
        x = rest[i]
        if x in flags:
            a[x] = True
            i += 1
        elif x in vals:
            if i + 1 >= len(rest):
                refuse("%s needs a value" % x)
            a[x] = rest[i + 1]
            i += 2
        else:
            refuse("unknown option %s" % x)
    if cmd == "build":
        if not a.get("--out"):
            refuse("build needs --out DIR")
        repo = os.path.abspath(a.get("--repo", ROOT))
        rc, _v = build(repo, a.get("--rev", "HEAD"),
                       os.path.abspath(a.get("--fetched", repo)),
                       os.path.abspath(a["--out"]), dump=a.get("--dump"),
                       no_scan=a.get("--no-dump-scan", False),
                       cell=a.get("--cell"),
                       cell_other=a.get("--cell-other-recipe", False),
                       dry_run=a.get("--dry-run", False))
        return rc
    if cmd == "verify":
        if not a.get("--archive"):
            refuse("verify needs --archive FILE")
        return verify(a["--archive"], a.get("--sums"))
    if cmd == "check-decl":
        return check_decl(os.path.abspath(a.get("--repo", ROOT)))
    refuse("unknown command %r. Commands: build, verify, check-decl, "
           "--self-test" % cmd)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Refusal as e:
        sys.stderr.write("srcarchive: %s\n" % e)
        sys.exit(3)
    except KeyboardInterrupt:
        sys.stderr.write("srcarchive: interrupted\n")
        sys.exit(3)
    except Exception as e:                           # noqa: BLE001
        sys.stderr.write("srcarchive: %s: %s. This is a defect in srcarchive, "
                         "not a verdict about the inputs\n"
                         % (type(e).__name__, e))
        sys.exit(3)
