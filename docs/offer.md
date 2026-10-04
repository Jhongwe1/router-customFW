# Written offer for corresponding source

**This is not legal advice.** It is the text of an offer, written by the author
of the code against a reading of the licences the components carry. The reading
is `NOTICE`'s; the component list is `docs/sbom.md`'s.

**Marks.** 讀 is read out of a file or a licence text. 量 is a desk measurement
over the tree, a git object or a GitHub reply. 推 is inferred and says what
would settle it.

---

## 0. The condition under which this offer binds, and why it is written that way

🔴 **No binary has been distributed, so this offer does not bind yet.**

量 2026-10-04: there are **5 releases** on the repository and **0 of them has an
asset**; the `v0.6` release's `assets` list is empty. 量 nothing is written to
flash through `R9`, and the image is uploaded to `0x80500000` over TFTP and run
from RAM. So the bytes a distribution would contain exist (`docs/sbom.md` § 1
names them: `nfjrom`, 1,108,992 bytes, sha256 `9da0857a…`), and no recipient has
ever received them.

**An offer that claimed to bind today would be claiming to honour requests this
repository cannot yet satisfy** (§ 4 says exactly which two). So the offer names
its own trigger:

> **This offer takes effect on the first release of this repository that carries
> a binary asset, and it covers that release and every later one. It does not
> cover the five existing releases `v0.2`, `v0.3`, `v0.4`, `v0.5` and `v0.6`,
> because none of them carries a binary** (量 2026-10-04: 0 assets on each).

量 there are **6 annotated tags** and **5 releases**: `v0.0` is a tag with no
release at all, which is why the five above are named and the six are not. None
of the six is signed and 量 no `user.signingkey` is configured, so a recipient
cannot establish that a tag is the owner's — stated here because an offer tied
to a release is tied to something unsigned.

🔴 **Before that release is tagged, the two gaps in § 4 must be closed or the
release must not carry the component they are about.** That is a release-gate
condition, not a caveat: `P4b` owns it, and § 5 writes it as a checklist whose
every line is checkable.

---

## 1. The offer

For any release of this repository that carries a binary asset, the copyright
holder, Chung-Wei Lan, offers to any third party, for a period of **three years
from the date that release's binary was last distributed**, a complete
machine-readable copy of the corresponding source code for the GPL-2.0 and
LGPL-2.1 components of that binary, on a physical medium customarily used for
software interchange, for **a charge no more than the cost of performing the
distribution** — and, in practice, as a download at no charge.

讀 the three-year period and the cost ceiling are GPL-2.0 § 3(b)'s own terms;
the download alternative is offered in addition, not in place of them, because
§ 3(b) asks for a medium and a URL is not one.

**How to ask.** Open an issue on the repository, or write to the address in
`AUTHORS`. 🔴 **未定: neither channel is written down yet.** 量 this repository
has no `AUTHORS` file and the offer has no published contact address. What
settles it: the owner names a contact address in a file the release links to,
in the same commit that tags the first release carrying a binary. **An offer
with no way to ask is not an offer**, so that line is a release-gate item in
§ 5 and not an editorial detail.

**What the request gets.** The archive named in § 2 for the release the
requester names, plus `NOTICE`, plus this file, plus `docs/sbom.md` at that
release's commit.

---

## 2. What source is offered, for which binaries

The unit of the offer is one release's binary asset. Each row names the
component class, what "corresponding source" means for it, and where the bytes
come from.

| # | binaries in the asset | licence class 讀 | what is supplied | where it comes from |
|---|---|---|---|---|
| 1 | the kernel inside `nfjrom`: Realtek's `linux-2.6.30` tree, `arch/rlx`, the board BSP, the `rtl8192cd` WLAN driver, the NAT fast path, the MTD/SPI and GPIO code (`docs/sbom.md` `K1`–`K5`) | GPL-2.0 | the complete staged tree as built, including every file rlxfw's declarations changed, **plus the scripts that control compilation**: `tools/rlxfw-kbuild.sh`, `config/rlxfw-marks.tsv`, `config/host-compat/`, `config/rlxfw-kernel.delta`, the built `.config`, and `tools/modrecord.py`'s generated per-file modification record | `SOURCES.json` `rtl819x-toolchain` at pin `5c9be5d943318fdb4d048ae22078129594eb5a10`, re-staged and re-declared; the declarations are in this repository |
| 2 | the loader stub in `nfjrom`: `rtkload` (`W1`) and the LZMA decoder (`W2`) | GPL-2.0; LZMA LGPL or CPL 讀 | that directory's source as built, with `tools/rtkimage.py` as the script that wraps it | the same drop, `linux-2.6.30/rtkload/` |
| 3 | rlxfw's own 12 compiled kernel sources (`K6`) | GPL-2.0-only (`NOTICE` § 2) | the 16 files of `config/rlxfw-src/`, which are already in this repository | this repository |
| 4 | `/bin/busybox` (`U8`) and its 11 applet symlinks | GPL-2.0-only | the drop's `busybox-1.13` as staged, plus `config/busybox-patches/`, `config/rlxfw-busybox.config` and `tools/mkbusybox.sh` | the same drop; the recipe is in this repository |
| 5 | uClibc 0.9.30, statically linked into all 11 ELF files (`L1`, `L2`) | LGPL-2.1 | the library's complete source **and the relink path**: each program's own sources and Makefiles, so a recipient can modify uClibc and relink (讀 LGPL-2.1 § 6(a); `NOTICE` § 5) | the drop's `toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/config/uclibc/`; the programs are in this repository |
| 6 | rlxfw's six userspace programs, the probes, `mfgtest`, the web UI and the configuration files (`U1`–`U7`, `U10`–`U15`) | MIT (`NOTICE` § 4) | already published: this repository, at the release's commit | this repository |
| 7 | `src/lib/ed25519.c` and `src/lib/sha512.c` (`X1a`) | public domain | already published; `src/rlxboot/test/mk-import.sh` regenerates them from the upstream file and `check-import.sh` fails on a one-byte difference | `SOURCES.json` `tweetnacl` |
| 8 | `/bin/iperf3` (`U9`) | LBNL three-clause BSD, with bundled MIT / BSD / NCSA / public-domain notices 讀 | **see § 4, gap 1** — the notices, and the tree they are in, which this repository does not hold | `$FWRE_WORK/iperf3-port/src313/`, outside any clone |
| 9 | `libgcc.a` of gcc 3.4.6-1.3.6, statically linked into 7 of the 11 ELFs (`L3`) | 推 GPL-2.0-or-later with the libgcc linking exception | **see § 4, gap 2** — nothing | no pinned tree holds gcc or binutils source |

**One thing row 1 and row 4 both depend on, said once.** 讀 `docs/sbom.md`
§ 2.4: `SOURCES.json` records a URL and a pin on a **third party's** repository
(`github.com/frederic/rtl819x-toolchain`), and 量 that repository reports
`license` null, was last pushed 2020-03-08, and can be deleted or rewritten by
its owner. 推 GPL-2.0 § 3 asks the distributor to supply the source or an offer
**of its own**; a URL it does not control is neither. So the offer above says
*"re-staged and re-declared"*: discharging rows 1, 2, 4 and 5 means this project
holding and serving the bytes, not pointing at the pin. The pin is what makes
the third party's tree a citable artefact; it is not this project's offer.

---

## 3. For how long, and at what cost

- **How long:** three years from the last distribution of that release's binary,
  讀 GPL-2.0 § 3(b). The repository's releases are not deleted, so in practice
  the clock starts at the tag and runs while the release exists.
- **Cost:** no more than the cost of performing the distribution 讀; a download
  at no charge is offered in addition.
- **Form:** one archive per release, whose sha256 is published in that release's
  notes, so a recipient can check that what arrived is what was offered.
- **What the offer is not:** it is not a support commitment, a warranty, or an
  undertaking that the archive rebuilds bit-for-bit. 量 `P4a` closed at **Level
  1** only, and 讀 this drop's `scripts/mkcompile_h` has no
  `KBUILD_BUILD_USER`/`_HOST` and writes `(key@K)` from `whoami` and `hostname`,
  so a third party rebuilding the published recipe gets a different banner and a
  different sha256 whatever is done about the clock (`P4A-1`). Corresponding
  source is what the licences ask for; a reproducible build is a separate claim
  and this offer does not make it.

---

## 4. The two gaps, stated here rather than hidden

An offer is worth what it can supply. These two are open on the day this file
is written, and both are 未定 rows of `docs/sbom.md` § 9.

### Gap 1 — `SBOM-3`: iperf3's source tree is not held by this project

🔴 量 2026-10-04: `SOURCES.json` contains the word `iperf` **0 times**. The
repository holds `config/rlxfw-user/iperf3/` — 4 files, the recipe — and that
Makefile says in so many words that a clean clone cannot build this target. The
tree that was compiled lives at `$FWRE_WORK/iperf3-port/src313/`, which no
clone has.

**What that costs the offer.** iperf3 is BSD-licensed, so the licence asks for
notices rather than source 讀. But 量 the image carries **no** notices: 0 of 17
`file` rows of `config/rlxfw-initramfs.tsv` is a licence text. So the gap is
real in the direction that matters — a recipient of the binary gets neither the
notice nor a way to find the tree it came from.

**Settled by** the `SOURCES.json` entry drafted in `sources-patch.md`: the three
origins that agree on all sixteen compiled files (讀 `notes/iperf3-port.md` § 1 —
the GitHub tag archive, sha256 `e34cf60c…`; the Debian orig tarball, sha256
`60d8db69…`; a clone at tag 3.1.3, commit `274eaed5…`) plus a copy this project
holds, fetchable from a clean clone.

**Until it lands, this offer's row 8 reads: the notices are in the upstream
tree, this project does not serve them, and a release carrying `/bin/iperf3`
must either land the entry or drop the binary.**

### Gap 2 — `SBOM-4`: no gcc or binutils source is held anywhere

🔴 量 2026-10-04: names that only a compiler tree has — `libgcc2.c`,
`reload1.c`, `ldlang.c`, `tc-mips.c` — are found in **0 of the 3** pinned GPL
drops. The one near-hit, `elf32-mips.c`, is inside `users/gdb/gdb-6.8/bfd`,
gdb's bundled copy. The control, `fork.c` in each kernel tree, is found in all
three. So `libgcc.a` and the compiler that built it have no corresponding source
in any tree `SOURCES.json` pins.

量 `libgcc.a`'s objects are nevertheless **in** the image: members of the
default variant are found byte for byte in 7 of the 11 ELF files.

**What that costs the offer.** 推 if the libgcc linking exception applies, the
offer owes nothing for `libgcc.a` and this gap is cosmetic. If it does not — for
example because the RSDK patch set changed something the exception's wording
turns on, which 量 cannot be checked, since the patch set is not held — then the
offer cannot be honoured for row 9 and no amount of work in this repository
changes that.

**Settled by** the RSDK gcc source, which no pinned tree holds; failing that, by
reading the FSF gcc 3.4.6 `libgcc2.c` header as the governing text, with the
RSDK patch set still unknown. 讀 `SOURCES.json` holds a **binutils** 2.24 Lexra
patch (`lexra-binutils-2.24`, sha256 `888e368a…`) and a gcc 4.8.4 Lexra patch is
recorded as a URL only, not fetched — and neither is the 3.4.6 / 2.16.94
toolchain that actually built the image, so neither closes this.

**This offer therefore does not promise `libgcc.a`'s source. It says what is
known, what is inferred, and what would settle it.**

---

## 5. The release gate — what must be true before the first binary ships

Each line is checkable and names its checker or its measurement. `P4b` owns the
list.

| # | condition | how it is checked |
|---|---|---|
| 1 | a contact channel exists and the release links to it | 量 the file exists and the release notes name it; § 1's 未定 is closed |
| 2 | `SOURCES.json` has the iperf3 entry and `tools/fetch-sources.sh` fetches it from a clean clone | 量 `fetch-sources.sh` reports success on a fresh clone; gap 1 closed |
| 3 | the release's archive is served by this project, not by a pin on a third party's repository | 量 the asset exists and its sha256 is in the release notes (§ 2's note) |
| 4 | the archive's uClibc half includes the relink path: each program's sources and Makefiles | 量 the archive contains them (讀 LGPL-2.1 § 6(a)) |
| 5 | `NOTICE`, `LICENSE` and this file are in the archive **and reachable from the running image** | 🔴 量 today 0 of 17 `file` rows is a notice; closing this is a change to `config/rlxfw-initramfs.tsv`, not to this document |
| 6 | gap 2 is either closed or the release states that `libgcc.a`'s source is not supplied and why | 量 the release notes say so, or `SBOM-4` is resolved |
| 7 | the per-file modification record is generated, not written by hand | `tools/modrecord.py check` is green against the committed record |

---

## 6. What this document does not establish

- **It is not legal advice** and it is not a lawyer's reading of GPL-2.0 § 3 or
  LGPL-2.1 § 6. Every 讀 above is a quotation of a licence's own words; every
  conclusion drawn from one is marked 推.
- **It does not bind today.** § 0 says why: 量 0 of 5 releases has an asset, so
  there is no distribution and no recipient.
- **It does not establish that the archive in § 2 exists.** No release has been
  built to these terms; § 5 is the list of what would have to be true, and every
  line of it is open.
- **It does not settle `SBOM-2`** — the 35 Realtek-directory sources with no
  licence text, plus 3 in the loader stub. 推 the directory's `COPYING` governs
  them, and that is a reading of somebody else's release.
- **It cannot see** two things no measurement here reaches: whether the third
  party's pinned repository will still exist when a request arrives, and whether
  the drop that Realtek published is a GPL release at all in the sense `SBOM-2`
  needs.
