# Release process

How a release that carries a binary is made, from a green tree to a published
release, which tool checks each step, and which steps cannot be taken back.

**Marks.** 讀 is read out of a file. 量 is a desk measurement. 推 is inferred and
says what would settle it.

**Scope.** A release here is a tag of this repository and a GitHub release whose
assets include an image. Releases `v0.2`–`v0.6` carry no binary and are outside
this process (`docs/offer.md` § 0). `P4b` closes when every step of phases A and
B reads as stated on the release commit; phase C is the owner's, and phase D
follows it.

**Which records carry which digest.** `P4b`'s closing records — its
`docs/GATE-RESULTS.md` entry and its row on the board in `PROGRESS.md` — are
part of the release commit, because `v1.0` is tagged once all six of its gates
are `✓`. So they can name the image by sha256 and never the archive's sha256:
the archive is built from that commit and contains them (B2). Every asset's
sha256, the archive's included, is in the release notes (B6), and the published
digests are recorded afterwards, in a new dated entry (D2).

**The two `CHARTER.md` §110 rules this process owns.** Rule 2 — every version
gets a release, with its `CHANGELOG.md` section and its known issues — is A4
together with phase C. Rule 3 — every gate that closes gets a
`docs/GATE-RESULTS.md` entry: a one-line version, three claims that stand with
their evidence, and what the gate did not establish — is `P4b`'s own entry,
written in the release commit as above.

**The rule this process exists to keep.** 讀 `docs/offer.md` § 0: the release
that carries a binary carries, as assets of the same release, that binary's
corresponding-source archive (GPL-2.0 § 3(a)) and the licence texts. The image
itself carries no notice and is not rebuilt to carry one: the bytes released are
the bytes that were tested.

---

## 🔴 Outward-irreversible steps

Each needs **the owner's explicit yes, dated, for that exact act** — the commit
id, the tag name, the asset digests — written down before the act is taken. A yes
for one act is not a yes for the next. Nothing in phases A, B and D is outward.

| step | act | why it cannot be taken back |
|---|---|---|
| C1 | `git push` of the release commit | the repository is public; a pushed commit is copied at once |
| C2 | create the tag and push it | a tag is a public name for a commit; moving it later is a second, visible act |
| C3 | `gh release create` with the notes | the release page is the public statement of what was released |
| C4 | upload the assets | from this act the binary is distributed, and `docs/offer.md` § 0 applies: the archive must stay an asset of that release for as long as the binary does |
| C5 | anything addressed to a third party (Realtek, TOTOLINK, counsel) and any repository setting | it leaves the repository; no contact address is ever committed — questions go to GitHub Issues only |

The tag is unsigned, like the six before it: a release's integrity is its commit
id and the sha256 of every asset, which the notes list (B6). The signature that
protects the device is the update container's, not the tag's.

---

## Phase A — the release commit C (desk)

| step | what | checked by | passes when |
|---|---|---|---|
| A1 | every change under `config/` has landed; no `config/` byte changes after the image is built | `tools/rlxfw-kbuild.sh <cell> --variant <v> --dry-run` prints `recipe=` | the recipe printed on C equals the one the release image was built from (B1); any later `config/` edit moves `RECIPE_ID` and makes the tested image not C's |
| A2 | the per-file modification record is regenerated: `tools/modrecord.py emit --config config --out docs/vendor-modifications.md` | `tools/modrecord.py check --config config --record docs/vendor-modifications.md` (a CI step); then `check ... --tree <a fresh stage of the pinned drop>` at the desk, the stage made from the pin's git objects (`git -C <drop> archive <pin> linux-2.6.30 users/busybox-1.13 boards/rtl8196e`), since a tree a build has used is refused | rc 0 both times; with `--tree`, every marks anchor resolves exactly once in row order after the patches, and every hunk applies in declared order, a pre-image found twice placed where GNU `patch` places it |
| A3 | the sentences that the upload would make false are rewritten to be true before and after it: "nothing is owed today" in `docs/offer.md` § 0 and § 6, `NOTICE` § 8, `docs/sbom.md` § 8 and § 11, `README.md`'s *Licences* paragraph, the no-image row of `docs/KNOWN-ISSUES.md` | reading them, against the release's own asset list | each says which release carries which asset, not how many releases have one |
| A4 | the release's sections: a `CHANGELOG.md` section and a `docs/KNOWN-ISSUES.md` *What vX.Y does not establish* section | reading them | both name the release image by sha256 |
| A5 | the desk checks of `CLAUDE.md` § Closeout pass on C, `flashwin scan --dump` included | each tool's own exit status, read from a script run by path | every one rc 0, `citecheck` read after the commit |
| A6 | CI is green on C | `gh run list --commit <C> --json conclusion` (read-only) | `success`. `tools/citime.py` cannot see a red run, so the conclusion is read, not inferred |

## Phase B — the artefacts (desk, on ext4 under `$FWRE_WORK/rebuild/`)

| step | what | checked by | passes when |
|---|---|---|---|
| B1 | the release image is the tested one | the test record's pin (`looprun --image-sha256`, `rtkimage-record.tsv`) and the build manifest | its sha256 equals the tested bytes', and the manifest's `recipe_id` equals A1's |
| B2 | the corresponding-source archive: `tools/srcarchive.py build --rev <C> --fetched <root> --out <dir> --dump $FWRE_WORK/dumps/flash-n150rt-console-2.bin --cell <the release build's cell>` | the tool's own refusals; its manifest | rc 0; the manifest's `recipe_id` equals B1's; `h601_scan` reads CLEAN; the cell line reads without `--cell-other-recipe` |
| B3 | a second reading of the archive, and a sweep of every binary the release carries | `tools/srcarchive.py verify --archive <archive> --sums <base>.SHA256SUMS`; then the archive unpacked into an empty ext4 directory, the image and every other binary asset (the slot containers and the `rlxboot` artefacts, when the release carries them) copied beside it, and `tools/flashwin.py scan --sweep <dir> --dump <dump>` | verify rc 0; the sweep CLEAN over the unpacked members and every binary asset |
| B4 | the archive is reproducible | `tools/srcarchive.py build` again into a second directory | archive and manifest sha256 identical to B2's |
| B5 | the licence texts | written by B2 beside the archive (`<base>.licence--<origin>--<path>`) and listed in `<base>.SHA256SUMS` | one file per licence text the tool finds; `NOTICE`, `LICENSE` and `config/rlxfw-src/LICENSE` among them |
| B6 | the release notes, drafted | reading them against the assets | they carry: the commit id; the image's sha256 and size and its `RECIPE_ID`; the sha256 of every asset; GitHub Issues as the only channel; the `libgcc.a` statement (`docs/offer.md` § 4, gap 2) and the iperf3 one (gap 1); what the release does not establish |
| B7 | `docs/offer.md` § 5, all seven lines | each line's own check | every line reads as stated |

The assets are: the image, and any other binary the owner names for the release
(the slot containers, the `rlxboot` artefacts); the archive; its manifest;
`<base>.SHA256SUMS` and `<base>.record.tsv`; the licence files of B5, `NOTICE`
and `LICENSE` among them; `docs/offer.md` and `docs/sbom.md`, copied from C; and
`SHA256SUMS`, written over every other asset once they all exist and not part
of C, so that `sha256sum -c SHA256SUMS` checks the whole release.

## Phase C — the outward acts (owner's dated yes, each)

C1 → C2 → C3 → C4, in that order, each only after its own yes; C5 only if
needed. A release whose assets cannot all be uploaded is not created: a binary
without its archive beside it is what `docs/offer.md` § 0 forbids.

## Phase D — after publication (desk)

| step | what | checked by | passes when |
|---|---|---|---|
| D1 | the published bytes are the prepared ones | each asset downloaded from the release page and hashed | every sha256 equals the notes' |
| D2 | the record of the publication, written after it | a new dated `LOG.md` entry and the Release clock row of `PROGRESS.md`, in a commit made after the tag | written once D1 passes; the entry gives the release's URL and each downloaded asset's sha256 as D1 read it. It is a new entry and never an edit of the release commit's records, which cannot carry the archive's digest |

## The build a recipient runs

讀 `tools/rlxfw-kbuild.sh` refuses to stage unless every reference in
`tools/rlxfw-marks-absent.tsv` verifies, and `unit-kernel` is this unit's own
vendor kernel, which no recipient is ever given. A recipient builds with
`--recipient`, which skips only the checks that read that row, with the drop
at its `SOURCES.json` pin under `$FWRE_WORK/rebuild/src-vendor/rtl819x-toolchain`
and a `tools/mkinitramfs.py` spec whose content record sits beside it:

    bash tools/rlxfw-kbuild.sh <cell> --variant quiet --marks --jobs 4 \
         --initramfs <name>.spec --recipient

Its verdict is `recipient`, never `green`: exit 7, a last line starting
`== <cell>: RECIPIENT BUILD -- unit-specific checks not run: unit-kernel`, the
manifest rows `verdict recipient` and `recipient`, and no `manifest ->` line, so
`looprun` refuses it and it is never the image B1 pins. 量 2026-10-05 the flag's
refusals and verdicts hold on synthetic inputs (`test-kbuild-cflags` Y1–Y7b and
Z0–Z7); no `--recipient` kernel build has run.

---

## What this process does not establish

- **That the archive rebuilds the image.** 量 `P4a` closed at Level 1; a third
  party's rebuild differs at least in the kernel banner's `(key@K)` (`P4A-1`).
  The archive leaves out the toolchain and the drop's prebuilt host programs
  (`rtkload/lzma-26`, `rtkload/cvimg`), which a rebuild takes from the pinned drop;
  only a rebuild in an empty directory would test sufficiency, and none is a
  step here.
- **Anything legal.** The licence readings are `NOTICE`'s and are not legal
  advice.
- **That a recipient can tell the tag is the owner's.** The tag is unsigned; what
  a recipient can check is the commit id and each asset's sha256 against the
  notes.
- **That the H601 scan sees everything.** It has `tools/flashwin.py`'s gaps: runs
  under 16 bytes, byte-swapped or encoded copies, and the inside of a compressed
  member.
