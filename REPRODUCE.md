# Reproducing `v1.0`

Three layers, each answering one question about release
[`v1.0`](https://github.com/Jhongwe1/router-customFW/releases/tag/v1.0), each
resting on the one before it.

| layer | question | run with | state |
|---|---|---|---|
| 0 | are these the files the release published? | [`tools/reproduce-l0.py`](tools/reproduce-l0.py) | run 2026-10-20 |
| 1 | does the release's corresponding-source archive rebuild its image, byte for byte, in an empty directory? | [`tools/reproduce-l1.sh`](tools/reproduce-l1.sh) | run 2026-10-20, on the host and as the user that built the release |
| 2 | does layer 1 hold in a container pinned by digest, with no network, on any host? | not written | the next step |

**Marks.** 量 is a desk measurement, 讀 is read out of a file, 推 is inferred and
says what would settle it. No digest of a release file is typed on this page or
in the two scripts: each is read from the release's own manifest, from GitHub,
or from the tree the tag names.

**What a host needs.** Linux; a filesystem that keeps file modes (ext4, not a
Windows drive under WSL, which reports every file 0777); room for the two trees
and a build (量 here: 1.7 GB for the first tree's checkout, 2.2 GB for a build);
network access for the downloads; and `git`, `python3` (3.12 was used), GNU
`make`, `gcc`, `perl`, `patch`, `tar`, `xz`, and util-linux's `unshare` and
`mount`, with unprivileged user namespaces enabled. Every vendor binary runs
under the archive's own `tools/vendor-tripwire.sh`.

## The pins

`tools/reproduce-l1.sh` reads the two lines below. It refuses unless each
equals the pin [`SOURCES.json`](SOURCES.json) gives and the pin the archive's
own `SOURCES.json` and `CORRESPONDING-SOURCE.tsv` give, and it refuses a tree
whose `HEAD` is not that commit or whose `git status` is not empty, ignored
files included:

    pin  rtl819x-toolchain  5c9be5d943318fdb4d048ae22078129594eb5a10
    pin  saturn49-wecb      40e21cb7c66880172910ae00c18663ed48e0123d

The toolchain, `toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30`, is inside the
first tree and pinned with it. `tools/fetch-sources.sh` does not produce these
trees: it clones each branch's tip with `--depth 1` and does not check out the
pin ([`docs/build.md`](docs/build.md)). This does:

    git clone https://github.com/frederic/rtl819x-toolchain drop
    git -C drop checkout --detach 5c9be5d943318fdb4d048ae22078129594eb5a10
    git clone https://github.com/Saturn49/wecb ref
    git -C ref checkout --detach 40e21cb7c66880172910ae00c18663ed48e0123d

`bash tools/reproduce-l1.sh pincheck --name rtl819x-toolchain --tree drop`
answers whether a tree is the pinned one, and builds nothing.

## Layer 0 — the release's files

    /usr/bin/python3 tools/reproduce-l0.py fetch --assets <new dir> --release-json <file>
    /usr/bin/python3 tools/reproduce-l0.py check --assets <dir> --release-json <file>

`fetch` reads the release's description from GitHub's API, without
credentials, and downloads every asset it lists into a directory that must not
exist or must be empty. `check` requires three sources to agree: the release
manifest `SHA256SUMS`, whose entries it counts and whose every file must be
present with its sha256, the directory holding those files and the manifest and
nothing else; GitHub's own `digest` and `size` for every asset, the manifest
included; and the commit the tag names, whose `CHANGELOG.md`, read out of the
tag's own tree, states the image's and `T.rlxu`'s byte counts and sha256, and
whose first twelve hex digits the archive's name carries. Then it runs itself
three more times, on copies of the directory with one bit of the image
flipped, one file added and one removed, and requires each to exit 1.

量 2026-10-20: `SHA256SUMS` lists 16 files and 16 of 16 match; the directory
holds those 16 and the manifest; GitHub's digest and size agree for 17 of 17;
the tag names `2eb1a3d6`, and the image and `T.rlxu` have the values its
`CHANGELOG.md` states; the three controls each exit 1. The 17 files are
byte-equal to a second download made on 2026-10-09.

**It does not establish** that `SHA256SUMS` is the owner's: no file at the tag
holds its digest, which was written over the other assets after the release
commit and first committed after the tag (`fb5a5d17`), so GitHub's digest is
its only second source here. Nor that the tag is the owner's (it is unsigned),
nor that GitHub served what was uploaded, beyond its own digest of what it
serves.

## Layer 1 — the image, rebuilt from the archive

    bash tools/reproduce-l1.sh build --assets <layer 0's dir> --release-json <file> \
         --drop <rtl819x-toolchain at its pin> --ref-drop <saturn49-wecb at its pin> \
         --root <a new, empty directory> [--release-vmlinux <file>]

It takes these inputs and no others: the release's files, on which it runs
layer 0 again, controls included, before anything else; the two trees, each
checked against its pin before use; and `--root`, which must not exist or must
be empty. `--release-vmlinux` is optional: the release build's `vmlinux` is not
a release asset, and only the machine that built the release has it.

**The environment** is cleared: the script re-executes itself under `env -i`
with `HOME` an empty directory under `--root`, `PATH=/usr/sbin:/usr/bin:/sbin:/bin`,
`LC_ALL=C`, `TZ=UTC`, `TMPDIR` under `--root`, `PYTHONDONTWRITEBYTECODE=1`,
`FWRE_WORK` under `--root`, and its own marker, `RLXFW_L1_INNER=1`; bash itself
adds `PWD`, `SHLVL` and `_`, and the script prints the names it runs with.

**The steps.** What compiles and links is the archive's own `src/`, `config/`
and `tools/`, as they were at `v1.0`'s commit; the script adds the order and
the arguments.

| step | what runs | whose |
|---|---|---|
| L1-1 | layer 0 on the release's files | this repository |
| L1-2 | the two trees against the pins | this repository |
| L1-3 | the archive unpacked, and read back against its manifest by its own `tools/srcarchive.py verify`; its `SOURCES.json` and `CORRESPONDING-SOURCE.tsv` must name the pins | the archive's tool |
| L1-4 | each tree cloned under `$FWRE_WORK` at its pin, sparse: the release build's copy of the drop held `boards/`, `linux-2.6.30/` and the 4181 toolchain, and busybox adds its source. The archive's 26,293 drop files are copied over the clone, which must stay clean: git's proof that each is the pinned file. Then a control: no file under the archive or the clones may already hold a released initramfs program's bytes | this script |
| L1-5 | the six programs: `make -C src target`, then `install` | the archive's Makefiles |
| L1-6 | busybox: `tools/mkbusybox.sh --drop rtl819x-toolchain --ref saturn49-wecb` | the archive's script |
| L1-7 | `uprobe`, `ucost`, `linkprobe`: their Makefiles under `config/rlxfw-user/` | the archive's Makefiles |
| L1-8 | `iperf3`: the pinned tarball from `refs/`, unpacked and staged, then its Makefile, in the directory its released bytes name (below) | the archive's Makefile |
| L1-9 | the initramfs: `tools/mkinitramfs.py build`; its 17 files compared with the released image's, which `tools/relimage.py` reads out of the image and checks against `docs/sbom.md`'s Appendix A, an asset of the release | the archive's tool |
| L1-10 | the kernel: `tools/rlxfw-kbuild.sh <cell> --variant quiet --marks --jobs 4 --initramfs <spec> --recipient`, whose expected verdict is exit 7 and its `RECIPIENT BUILD` line | the archive's driver |
| L1-11 | the image: `tools/rtkimage.py build` | the archive's tool |
| L1-12 | the rebuilt image's sha256 against `SHA256SUMS`'s entry for the image and against `T.rlxu`'s payload; `tools/repdiff.py` on the two `vmlinux` when the release build's is given | this repository |

**`iperf3`'s directory.** The released `/bin/iperf3` carries the absolute
directory it was compiled in, in three `assert()` strings (`docs/sbom.md`
`SBOM-R5`); built anywhere else it is other bytes. The script reads that
directory out of the released image (`tools/relimage.py srcdir`), never from a
typed value, and builds in a private mount namespace (`unshare --user
--map-root-user --mount`) in which the staged tree is bind-mounted over it. A
marker file proves the bind before the build; outside the namespace the
directory is not written, and its content digest is compared before and after.
It has to exist on the host to be a mount point; where it does not, the build
stops and says so. Layer 2 creates it inside the container.

量 2026-10-20, on the machine that built `v1.0`, in an empty directory whose
path is not the release build's: **the rebuilt image is the released one, byte
for byte**, with the sha256 of `SHA256SUMS`'s entry for
`mainline-9bb2bec7.img` and of `T.rlxu`'s payload, in each of three runs. The kernel
build exited 7 with its `RECIPIENT BUILD` line, `verdict recipient` and
`recipient` in its manifest, and no `manifest ->` line; its `vmlinux` differs
from the release build's in 0 of 4,621,952 bytes (`tools/repdiff.py`), so
`--recipient` changes no byte of the image. All 17 initramfs files rebuilt equal
to the released ones, five of which the release build had copied in by digest
rather than built. Every tripwire verdict was CLEAN, and a run took between 2
min 17 s and 3 min 18 s. The controls: `pincheck` refused the shared drop on this desk, which
is at the pin with three tracked files deleted (`SPEC.md` `FW-235`), and a
tree at another commit; before the build no file of the archive or the clones
held a released program's bytes (6 matched a released file's sha256, all of
them text files the repository tracks); and `--control-iperf3-path`, which
builds `iperf3` in the staged tree's own directory, gave an image that differs,
twice, `/bin/iperf3` (252,772 bytes, not 252,644) being the one initramfs file
that does, and `tools/repdiff.py` putting every differing byte of the `vmlinux`
in `.init.ramfs`.

### What `v1.0`'s archive did not supply

Each is a step or an input that `tools/reproduce-l1.sh` supplies and the
archive does not. Item 1 is the script that controlled the release build; what
its absence means for the archive as corresponding source is for
[`docs/offer.md`](docs/offer.md) and [`NOTICE`](NOTICE) to read, not this page.
The others are invocations and inputs: 讀 the archive's own `cell` line records
that the release kernel build read no drop file the archive leaves out, and
every userspace source the script compiles is a member of the archive.

1. **The build driver.** The release image was built by a script that was never
   committed (`docs/sbom.md` § 11). The order of the steps and the arguments of
   each are this script's reconstruction, which gives the same bytes.
2. **The builds of five initramfs files.** The release build did not build
   `busybox`, `iperf3`, `uprobe`, `ucost` or `linkprobe`: it copied them from a
   gitignored `build/` directory, admitted by their digests (`docs/sbom.md`
   § 3). The archive carries each one's recipe; the commands that run them,
   with the toolchain, kernel-tree and output paths, are this script's.
3. **`iperf3`'s staging.** Unpacking `refs/iperf-3.1.3.tar.gz` and writing
   `iperf_config.h` and `version.h` into it is step 1 of
   `config/rlxfw-user/iperf3/build.sh`, which writes into a fixed directory of
   its own (`docs/sbom.md` `SBOM-3`).
4. **`iperf3`'s build directory.** The archive states it nowhere; the released
   bytes are its only record.
5. **The toolchain's path for `iperf3`.** Its Makefile at `v1.0`'s commit
   defaults `TC` to an absolute path on the build machine; the script passes the
   pinned toolchain's.
6. **`--unit` for `tools/mkinitramfs.py`.** It requires a tree carved from this
   unit's flash dump and checks every row tagged `unit` against it. In `v1.0`'s
   declaration seven rows are, all directories with no content, and an empty
   directory holding the seven stands in. A declaration that took a file or a
   link from the dump is refused by the script: no recipient can supply one.
7. **A second GPL drop.** `tools/mkbusybox.sh` refuses to build unless the
   staged busybox source equals a second drop's copy (its gate G1; `--ref none`
   is refused), and the archive packs one drop. `saturn49-wecb` at its pin
   supplies the comparison and no byte of the image.
8. **The drop itself**, by design: the toolchain and the 1,316 files the
   archive's manifest lists as left out, among them `rtkload/lzma-26`,
   `rtkload/cvimg` and the drop kernel the marks gate reads as absent, come
   from the pinned tree (the archive's own `# not packed` line).

**It does not establish** a rebuild on another machine or by another user: the
kernel banner carries the builder's user and host names, here this machine's
(`P4A-1`); nor a difference located without the release build's `vmlinux`,
which is not a release asset; nor the toolchain's provenance, trusted by its
pin; nor that the archive suffices alone (items 7 and 8); nor that the build is
independent of the filesystem it runs on: every run was on this desk's ext4,
where 推 a new directory's listing order depends on the names and the
filesystem's hash seed, not on the directory; nor anything about the device.

## Layer 2 — the next step, not built

Layer 1 inside a container, so that what layer 1 cannot pin — the host, its
packages, its user and its host name — is pinned too:

- the base image named by digest, and every package by exact version or from a
  dated snapshot;
- run with no network, with only the release's files, the two pinned trees and
  this repository mounted read-only, and `--root` on a volume of its own;
- the user and host names the kernel banner carries read by a script from the
  released image (`tools/relimage.py info` prints the banner) and given to the
  container as its user and its host name, never typed: the drop's
  `scripts/mkcompile_h` takes them from `whoami` and `hostname` and has no
  variable for either (`notes/reproducible-build.md` § 6, `L2-1`);
- `iperf3`'s directory created inside the container, where no namespace is
  needed;
- with a tree withheld, it stops and names the tree.

It passes when it reproduces layer 1's sha256. It is not built yet. Its engine
here is rootless Podman 4.9.3, installed 2026-10-20 because `docker` on this
desk's WSL is Docker Desktop's shim with its WSL integration off (量 2026-10-19).
