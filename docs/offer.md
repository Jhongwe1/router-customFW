# Corresponding source, shipped with the binary

**This is not legal advice.** It is how this project meets the source
obligations of the binaries it releases, written by the author of the code
against a reading of the licences the components carry. The reading is
`NOTICE`'s; the component list is `docs/sbom.md`'s.

**Marks.** 讀 is read out of a file or a licence text. 量 is a desk measurement
over the tree, a git object or a GitHub reply. 推 is inferred and says what
would settle it.

---

## 0. The rule, and when it applies

> **Every release of this repository that carries a binary asset carries, as a
> second asset of the same release, the corresponding-source archive of that
> binary.** 讀 GPL-2.0 § 3(a): *"Accompany it with the complete corresponding
> machine-readable source code"*.

So there is no written offer under § 3(b): no three-year clock, no medium and
no charge. The source travels with the binary, or the binary does not travel.

量 2026-10-04: there are **5 releases**, `v0.2`, `v0.3`, `v0.4`, `v0.5` and
`v0.6`, and **0 of them has an asset**, so they carry no binary and owe no
source. 量 nothing is written to flash through `R9`, and the image is uploaded
to `0x80500000` over TFTP and run from RAM. So the bytes a release would carry
exist (`docs/sbom.md` § 1 names them: `nfjrom`, 1,108,992 bytes, sha256
`9da0857a…`), and no recipient has ever received them. **Nothing is owed
today.**

量 there are **6 annotated tags** and **5 releases**: `v0.0` is a tag with no
release at all, which is why the five above are named and the six are not. None
of the six is signed and 量 no `user.signingkey` is configured, so a recipient
cannot establish from a tag that it is the owner's: an archive tied to a release
is tied to something unsigned. What a recipient can check is the commit id and
the sha256 of every asset, which the release notes list
(`docs/release-process.md`).

🔴 **Before a release carrying a binary is tagged, every line of § 5 must read
as stated, or the release must not carry the component the line is about.**
That is a release-gate condition, not a caveat: `P4b` owns it.

---

## 1. How to ask, and what a recipient gets

**How to ask.** Open an issue on the repository's GitHub Issues. That is the
only channel, and no address is published. It answers questions: the source is
not sent on request, because it is already an asset of the release that carries
the binary.

**What a recipient gets.** With the release that carries the binary, as assets
of that same release: its corresponding-source archive and the archive's
manifest, `NOTICE`, this file, `docs/sbom.md` at that release's commit, and the
licence texts of the components. `docs/release-process.md` lists the assets and
the tool that produces or checks each.

---

## 2. What the archive carries, for which binaries

The unit is one release's binary asset. Its archive is produced by
`tools/srcarchive.py` from the release commit, out of the declarations the
build reads (`SOURCES.json` `corresponding_source`, `config/`), and the
manifest inside it, `CORRESPONDING-SOURCE.tsv`, is the authority on what it
holds; this table says what each component class needs and where the bytes come
from.

| # | binaries in the asset | licence class 讀 | what the archive carries | where it comes from |
|---|---|---|---|---|
| 1 | the kernel inside `nfjrom`: Realtek's `linux-2.6.30` tree, `arch/rlx`, the board BSP, the `rtl8192cd` WLAN driver, the NAT fast path, the MTD/SPI and GPIO code (`docs/sbom.md` `K1`–`K5`) | GPL-2.0 | the kernel tree and the board BSP the build compiles, every file rlxfw's declarations change included, **plus the scripts that control compilation**: the repository at the release commit, which holds the build driver `tools/rlxfw-kbuild.sh` and everything it calls, the declarations under `config/`, and `tools/modrecord.py`'s generated per-file modification record | `SOURCES.json` `rtl819x-toolchain` at pin `5c9be5d943318fdb4d048ae22078129594eb5a10` — its `linux-2.6.30/`, `boards/rtl8196e/bsp/` and the board template — read at the pin and packed; the declarations are in this repository |
| 2 | the loader stub in `nfjrom`: `rtkload` (`W1`) and the LZMA decoder (`W2`) | GPL-2.0; LZMA LGPL or CPL 讀 | that directory's source, with `tools/rtkimage.py` as the script that wraps it. ⚠️ The two host programs that pipeline runs, `rtkload/lzma-26` and `rtkload/cvimg`, are prebuilt binaries in the drop; the archive leaves them out and lists them with their sha256 | the same drop, `linux-2.6.30/rtkload/` |
| 3 | rlxfw's own 12 compiled kernel sources (`K6`) | GPL-2.0-only (`NOTICE` § 2) | every file under `config/rlxfw-src/` at the release's commit | this repository |
| 4 | `/bin/busybox` (`U8`) and its 11 applet symlinks | GPL-2.0-only | the drop's `busybox-1.13`, plus `config/busybox-patches/`, `config/rlxfw-busybox.config` and `tools/mkbusybox.sh` | the same drop, read at the pin and packed; the recipe is in this repository |
| 5 | uClibc 0.9.30, statically linked into all 11 ELF files (`L1`, `L2`) | LGPL-2.1 | the library's complete source **and the relink path**: each program's own sources and Makefiles, so a recipient can modify uClibc and relink (讀 LGPL-2.1 § 6(a); `NOTICE` § 5) | the drop's `toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/config/uclibc/`, packed without the prebuilt objects the drop keeps beside its sources; the programs are in this repository |
| 6 | rlxfw's six userspace programs, the probes, `mfgtest`, the web UI and the configuration files (`U1`–`U7`, `U10`–`U15`) | MIT (`NOTICE` § 4) | this repository at the release's commit | this repository |
| 7 | `src/lib/ed25519.c` and `src/lib/sha512.c` (`X1a`) | public domain | the two files, and the upstream file `src/rlxboot/test/mk-import.sh` regenerates them from; `check-import.sh` fails on a one-byte difference | `SOURCES.json` `tweetnacl`, checked against its sha256 and packed |
| 8 | `/bin/iperf3` (`U9`) | LBNL three-clause BSD, with bundled MIT / BSD / NCSA / public-domain notices 讀 | the upstream tarball iperf 3.1.3, whose `LICENSE` carries every bundled notice; **see § 4, gap 1** for what it does not give | `SOURCES.json` `iperf3`, checked against its sha256 and packed |
| 9 | `libgcc.a` of gcc 3.4.6-1.3.6, statically linked into 7 of the 11 ELFs (`L3`) | 推 GPL-2.0-or-later with the libgcc linking exception | **see § 4, gap 2** — nothing | no pinned tree holds gcc or binutils source |

**What the archive no longer depends on, and what still does.** 讀
`docs/sbom.md` § 2.4: `SOURCES.json` records a URL and a pin on a **third
party's** repository (`github.com/frederic/rtl819x-toolchain`), and 量 that
repository reports `license` null, was last pushed 2020-03-08, and can be
deleted or rewritten by its owner. The archive carries the drop's declared paths
read at the pin, so a recipient needs nothing from that repository to read the
source of the binary. 推 What still comes only from it is the toolchain: the
compilers, binutils and the prebuilt host programs of row 2, which the boundary
leaves out of the archive and which a rebuild needs.

---

## 3. Form, and what it is not

- **Form:** one archive per release, `rlxfw-src-<commit>.tar.xz`, with its
  manifest beside it, and the sha256 of both in that release's notes, so a
  recipient can check that what arrived is what was released.
  `tools/srcarchive.py verify` re-reads an archive against its own manifest.
- **What it is not:** it is not a support commitment, a warranty, or an
  undertaking that the archive rebuilds bit-for-bit. 量 `P4a` closed at **Level
  1** only, and 讀 this drop's `scripts/mkcompile_h` has no
  `KBUILD_BUILD_USER`/`_HOST` and writes `(key@K)` from `whoami` and `hostname`,
  so a third party rebuilding the published recipe gets a different banner and a
  different sha256 whatever is done about the clock (`P4A-1`). Corresponding
  source is what the licences ask for; a reproducible build is a separate claim
  and this file does not make it.

---

## 4. The two gaps, stated here rather than hidden

An archive is worth what it can supply. These two are open on the day this file
is written, and both are 未定 rows of `docs/sbom.md` § 9.

### Gap 1 — `SBOM-3`: iperf3 cannot be built from a clean clone

量 2026-10-05: `SOURCES.json` carries an `iperf3` entry — role
`imported-source`, `dest refs/iperf-3.1.3.tar.gz`, `fetch: now` — and
`tools/fetch-sources.sh --list` plans it; `tools/srcarchive.py` refuses to pack
an archive unless that file is present with the pinned sha256. The tree itself
is not in this repository: it holds `config/rlxfw-user/iperf3/` — 4 files, the
recipe — and that Makefile says in so many words that a clean clone cannot build
this target. The tree that was compiled lives at `$FWRE_WORK/iperf3-port/src313/`,
which no clone has. The entry records the three origins that agree on all
sixteen compiled files (讀 `notes/iperf3-port.md` § 1 — the GitHub tag archive,
sha256 `e34cf60c…`; the Debian orig tarball, sha256 `60d8db69…`; a clone at tag
3.1.3, commit `274eaed5…`).

**What that costs.** iperf3 is BSD-licensed, so the licence asks for notices
rather than source 讀, and the notices are in the tarball's `LICENSE`, which the
release carries as an asset beside the binary (§ 1). What the gap costs is the
build: a recipient holds the source and the recipe, and has to unpack the
tarball and point the Makefile's `SRC` at it by hand.

**Settled by** the unpack step that `SOURCES.json`'s `fetch_gap` key names, and
a run of `tools/fetch-sources.sh` succeeding on a fresh clone, with a corrupted
sha256 refused as the control that makes the success a reading.

### Gap 2 — `SBOM-4`: no gcc or binutils source is held anywhere

🔴 量 2026-10-04: names that only a compiler tree has — `libgcc2.c`,
`reload1.c`, `ldlang.c`, `tc-mips.c` — are found in **0 of the 3** pinned GPL
drops. The one near-hit, `elf32-mips.c`, is inside `users/gdb/gdb-6.8/bfd`,
gdb's bundled copy. The control, `fork.c` in each kernel tree, is found in all
three. So `libgcc.a` and the compiler that built it have no corresponding source
in any tree `SOURCES.json` pins.

量 `libgcc.a`'s objects are nevertheless **in** the image: members of the
default variant are found byte for byte in 7 of the 11 ELF files.

**What that costs.** 推 if the libgcc linking exception applies, nothing is owed
for `libgcc.a` and this gap is cosmetic. If it does not — for example because
the RSDK patch set changed something the exception's wording turns on, which 量
cannot be checked, since the patch set is not held — then the archive cannot
supply row 9 and no amount of work in this repository changes that.

**Settled by** the RSDK gcc source, which no pinned tree holds; failing that, by
reading the FSF gcc 3.4.6 `libgcc2.c` header as the governing text, with the
RSDK patch set still unknown. 讀 `SOURCES.json` holds a **binutils** 2.24 Lexra
patch (`lexra-binutils-2.24`, sha256 `888e368a…`) and a gcc 4.8.4 Lexra patch is
recorded as a URL only, not fetched — and neither is the 3.4.6 / 2.16.94
toolchain that actually built the image, so neither closes this.

**The archive therefore does not carry `libgcc.a`'s source, and a release
carrying a binary says so in its notes (§ 5, row 6).**

---

## 5. The release gate — what must be true before a binary ships

Each line is checkable and names its checker or its measurement. `P4b` owns the
list; `docs/release-process.md` runs it.

| # | condition | how it is checked |
|---|---|---|
| 1 | the release notes name GitHub Issues as the only channel for questions | 量 the notes link the repository's Issues and publish no address |
| 2 | `SOURCES.json` plans `iperf3` and `tweetnacl`, and the archive carries both | 量 `tools/fetch-sources.sh --list` names both (it does, 2026-10-05); `tools/srcarchive.py` refuses to pack while either is missing, unplanned or not at its pinned sha256 |
| 3 | the archive is an asset of the same release as the binary | 量 the release's asset list holds both, and its notes carry the archive's sha256 |
| 4 | the archive carries the uClibc source and the relink path: each program's sources and Makefiles | 量 the archive's manifest lists the drop's `config/uclibc/` and the repository's `src/` |
| 5 | `NOTICE`, `LICENSE`, this file and the components' licence texts are assets of the release and members of the archive; the image itself carries none of them | 量 `tools/srcarchive.py` writes the licence files beside the archive and lists each in its `SHA256SUMS`, and the release's asset list holds them |
| 6 | gap 2: the release states that `libgcc.a`'s source is not supplied, and why | 量 the release notes say so, or `SBOM-4` is resolved |
| 7 | the per-file modification record is generated, not written by hand | `tools/modrecord.py check` is green against the committed record (a CI step) |

---

## 6. What this document does not establish

- **It is not legal advice** and it is not a lawyer's reading of GPL-2.0 § 3 or
  LGPL-2.1 § 6. Every 讀 above is a quotation of a licence's own words; every
  conclusion drawn from one is marked 推.
- **Nothing is owed today.** § 0 says why: 量 0 of 5 releases has an asset, so
  there is no distribution and no recipient.
- **It does not establish that any release meets § 5.** No release has been
  built to these terms; `docs/release-process.md` is the order in which one
  would be.
- **It does not settle `SBOM-2`** — the 35 Realtek-directory sources with no
  licence text, plus 3 in the loader stub. 推 the directory's `COPYING` governs
  them, and that is a reading of somebody else's release.
- **It cannot see** two things no measurement here reaches: whether the drop
  that Realtek published is a GPL release at all in the sense `SBOM-2` needs,
  and whether the third party's repository will still hold the toolchain when
  someone rebuilds (§ 2).
