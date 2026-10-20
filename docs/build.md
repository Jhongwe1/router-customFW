# Building rlxfw

What a clone can build, what each step needs, and what has and has not been run
the way this page says. The commands are the top-level
[`Makefile`](../Makefile)'s; `make help` lists them.

## The host suites: `make test`

Needs a Linux host with gcc-13, clang-18 and its sanitizer runtimes, and
python3. On Ubuntu 24.04:

    sudo apt-get install gcc-13 clang-18 libclang-rt-18-dev python3
    make test O=/absolute/dir/on/a/linux/filesystem

It builds the six programs and their tests under both compilers, runs them
plain and under ASan and UBSan, then runs `rlxboot`'s host suite. It prints
`test: 6 of 6 program suites ran and passed` and `host suite: PASS`, and writes
each suite's output to `$(O)/census/` for [`tools/ci-census.py`](../tools/ci-census.py).
Each program refuses if fewer tests ran than it has. `O=` must keep file modes:
the guard writes a file, sets 0644 and refuses if it reads back anything else, as
it does on a Windows drive under WSL.

This is what CI's `build-host` job runs on every push
([`.github/workflows/build.yml`](../.github/workflows/build.yml)). 量 2026-10-17:
rc 0 on a clean clone in a runner's environment, 347 s.

## The target: `make userspace` and `make image`

Both need the vendor's GPL drop, `rtl819x-toolchain` in
[`SOURCES.json`](../SOURCES.json), at its pinned commit, and the rsdk toolchain
inside it. The drop is not in this repository.

- `make userspace TC=<rsdk root>` builds the six programs as big-endian MIPS
  ELFs with the drop's gcc 3.4.6 (`rsdk-1.3.6-4181-EB-2.6.30-0.9.30`), every
  vendor binary run through [`tools/vendor-tripwire.sh`](../tools/vendor-tripwire.sh).
- `make image` checks that the drop is at `$FWRE_WORK/rebuild/src-vendor/rtl819x-toolchain`
  (`FWRE_WORK` defaults to `~/fwre-work`) and that its `HEAD` is the pin, then
  prints the command a recipient builds the kernel image with. What that build's
  verdict means is in [`release-process.md`](release-process.md), *The build a
  recipient runs*; how the kernel is staged, configured and wrapped is in
  [`notes/kernel-build.md`](../notes/kernel-build.md).

[`tools/fetch-sources.sh`](../tools/fetch-sources.sh) clones the source trees
`SOURCES.json` marks to fetch now into `src-vendor/` (`--all` adds the rest) and
downloads its documents, refusing any whose sha256 differs from the declared one.

## What this page does not establish

- **That the drop `fetch-sources.sh` clones is the pinned one.** 讀 it clones
  each tree with `--depth 1` at its branch's tip, records the head it got in
  `src-vendor/CLONED.tsv` and does not check out `SOURCES.json`'s pin. `make
  image` refuses another revision by its `HEAD`, and `tools/reproduce-l1.sh` by
  `HEAD` and a clean `git status`; [`REPRODUCE.md`](../REPRODUCE.md) gives the commands for the pin.
- **That a recipient's kernel build succeeds off this desk.** 量 2026-10-20 one
  `--recipient` build ran here, layer 1 of [`REPRODUCE.md`](../REPRODUCE.md).
- **That a rebuilt image equals a released one off this desk.** 量 2026-10-20
  one does here, on the host and in a container pinned by digest (layers 1 and 2); 讀 outside
  such a container a build differs at least in the kernel banner's user and host (`P4A-1`; [`notes/reproducible-build.md`](../notes/reproducible-build.md)).
