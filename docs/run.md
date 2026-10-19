# `make run` — `v1.0`'s userspace on an emulated board

**A simulation, not a measurement.** `make run` boots the programs `v1.0` shipped, cut
byte for byte out of the release image, on `qemu-system-mips -M malta`, so that someone
without the board can send them a request. Nothing it prints is a reading of the device,
and no sentence on this page about what the emulator did is one either: the CPU is not
the board's, the kernel is not rlxfw's, the network card is not the board's. The marks
量 (measured on the board), 讀 (read out of code or a dump) and 推 (inferred) are on
sentences about the board, each the one its owner gives, and 讀 also marks a value read
out of a source file; nothing the emulator did carries a mark.
[`qemu/README.md`](../qemu/README.md) holds the rule — a capture from the emulator is not
a measurement of this device — and [`emulation-surface.md`](emulation-surface.md) § 8.1
one reason: 34 of 75 payload rows disagree between the die and `qemu-mips-static`.

## Run it

    make run         # the guest's console is this terminal; Ctrl-A then X quits qemu
    make run-test    # the host test, then its two red controls; rc 0 when all three hold

The web API answers on `http://127.0.0.1:20080/`; `RUN_PORT=` picks another port, 20000
or above. Output goes under `O=` (default `build/make`, which git ignores): the downloads
in `run-cache/`, everything derived from them in `run/`. [`tools/maltarun.py`](../tools/maltarun.py)
does the work and refuses, with the reason, whatever is missing.

## Prerequisites

- `qemu-system-mips`; this page was run with 8.2.2, Ubuntu 24.04's `1:8.2.2+ds-0ubuntu1.18`.
- Python 3 at `/usr/bin/python3` (`PYTHON=`), standard library only; run here with 3.12.3.
- `git`, and the tag `v1.0` in the clone: the host test reads `BK_VERSION_STR` from it.
- Network access for the first run: four downloads, each pinned in
  [`tools/maltarun-pins.tsv`](../tools/maltarun-pins.tsv), which owns these values; this
  page repeats them, and `tools/maltarun.py --self-test` (`C18`) fails when the two differ
  either way. A file whose size or sha256 differs from its pin is refused, and a cached
  file is re-verified on every run.

| file | bytes | sha256 | from |
|---|---:|---|---|
| `SHA256SUMS`, the release manifest | 1,884 | `5622a5105c41ae1184647714f8a5c76aec90e0aabd2ad074cd18334124d862d3` | the `v1.0` release |
| `mainline-9bb2bec7.img`, the release image | 1,110,016 | the manifest's line for it, which `v1.0:CHANGELOG.md` also carries; both are checked | the `v1.0` release |
| `linux-image-4.19.0-21-4kc-malta_4.19.249-2_mips.deb` | 35,569,888 | `2866a3f2bd33f43b3619cd10b60a9f730c3dd4384db65ab042feb1c8a521ecfb` | `archive.debian.org`, buster |
| `busybox-static_1.30.1-4_mips.deb` | 869,600 | `7dcb0c063198fe3e2651f3bf72a6cd9c3668317b913b65fbdc4702deac0c354f` | `archive.debian.org`, buster |

The two Debian pins equal their entries in buster's `main/binary-mips/Packages.xz`, whose
sha256 is the one buster's `Release` lists; `Release`'s three signatures were checked with
`gpgv` against `debian-archive-keyring` 2023.4ubuntu1, fetched through Ubuntu's own signed
archive. That chain was walked once, on 2026-10-20, when the pins were written; `make run`
checks the pins.

## What it boots

1. **`v1.0`'s initramfs, unmodified.** In the image, one LZMA stream, at byte 11,272,
   decodes to 4,128,768 bytes. The newc archive starts at decoded byte 2,863,104 and runs
   through 55 entries to its `TRAILER!!!` record, then through `gen_init_cpio`'s zero
   padding to the next 512-byte boundary: 1,265,664 bytes, sha256
   `c4a04b7b962a9e965e78777a6c6efe80fb33b43ad246d238f97ca8af5dec1f10`, pinned as
   `v10-cpio` and printed by every run. Those bytes equal the `.init.ramfs` section of the
   release build's `vmlinux`, compared once, on 2026-10-20, on the machine that built it;
   that ELF is not a release asset.
2. **A second cpio, appended after it**: five paths, all under `/rlxsim/` — Debian's static
   busybox, `mii.ko`, `pcnet32.ko`, and [`maltarun-rdinit.sh`](../tools/maltarun-rdinit.sh)
   as `/rlxsim/load`. The kernel would overwrite a file of the same name as it unpacks, and
   re-mode a directory, so the tool lists both archives and refuses to boot if any path is
   in both; it writes the two listings beside the initrd.
3. **Debian's kernel**, from the package above, with `console=ttyS0 nokaslr
   rdinit=/rlxsim/load`. The loader loads the two modules, renames `eth0` to `rlx0`, and
   execs `v1.0`'s `/init`, which is PID 1 from then on.
4. **qemu**: `-M malta -cpu 24Kf -m 32 -no-reboot`, and one network card,
   `-nic user,model=pcnet,restrict=on,net=10.1.1.0/24,host=10.1.1.2,hostfwd=tcp:127.0.0.1:<port>-10.1.1.1:80`:
   user-mode networking, the guest cut off from the host and the outside, one forwarded
   port, bound to 127.0.0.1.

Nothing is compiled. `/init` and every other guest program run only inside
`qemu-system-mips`: the tool never runs a file it extracted, writes each one mode 0644,
and runs no other emulator — `qemu-mips`, the user-mode one, would run the guest's programs
against the host's own kernel and files.

## What stands in for the silicon

| | the board, `v1.0` | here | how it is made |
|---|---|---|---|
| CPU | RLX4181 rev 1: `PRId` `0x0000CD01` 量, the name 讀 from a table in one vendor header that is copied three times, that no code reads, and whose encoding breaks for `0xdc01`/`0xdc02` (`CPU-04`); the load delay slot exposed, no interlock, 量 (`CPU-14`) | MIPS 24Kf, interlocked | `-cpu 24Kf`: Debian's "4kc" kernel is built for MIPS32 R2 (讀 its `config`, `CONFIG_CPU_MIPS32_R2=y`) |
| kernel | rlxfw's Linux 2.6.30.9 and its drivers: 讀 the staged tree's `Makefile`, 量 the banner in the built `vmlinux` ([`sbom.md`](sbom.md), `K1`) | Debian's 4.19.249; no rlxfw driver | `-kernel`, from the pinned package |
| RAM | 32 MiB, 量 (`MEM-04`); 26,052 kB of it given to Linux, 量 (`MEM-06`) | 32 MiB | `-m 32`, with `nokaslr`: Debian's kernel otherwise moves itself by up to 16 MiB at random (讀 its `config`, `CONFIG_RANDOMIZE_BASE_MAX_OFFSET`), and one boot in 32 MiB without it printed nothing |
| network driver | [`rtl819x-nic`](drivers/nic.md) and [`rtl819x-switch`](drivers/switch.md), built into the kernel (讀 `config/rlxfw-marks.tsv`, `MK9` and `MK10`: `obj-y`) | `pcnet32` and `mii`, for qemu's PCnet card | the second cpio |
| its loader | none: the two are built in (the row above) | Debian's busybox-static 1.30.1 and `maltarun-rdinit.sh` | `rdinit=/rlxsim/load`, which `insmod`s the two modules |
| interface name | `rlx0`, the name `/init` configures (讀 `src/init/init.h`, `RLXFW_LAN_IF`) | `eth0`, renamed `rlx0` | the loader's `ip link set dev eth0 name rlx0`; `/init` then sets the address itself |
| MAC address | `02:52:4C:58:46:57` on `rlx0`, 量 (`NET-51`), which `rtl819x-nic` sets (讀 its source) | qemu's default | no option given |
| entropy | [`rlxfw-entropy`](drivers/entropy.md) | the 4.19 kernel's own pool, no rlxfw source | nothing added. Until `entropy_avail` has read 128 once, `brokerd` answers `/api/login` and the password change `503 noentropy` (讀 `src/brokerd/brokerd.h`, `BK_ENTROPY_MIN`; `src/httpd/routes.c`, `map_broker`); the host test sends neither |
| `/proc/rtl819x-*` | the switch and NIC verbs `/init` writes at LAN bring-up (讀 `src/init/main.c`, `write_verbs`) | absent | nothing added: `/init`'s six writes fail with `errno=2`, are logged, and it goes on |
| flash | 4 MiB of SPI NOR, 量 (`FLS-03`; the part, `FLS-01`), and [`rtl819x-spi`](drivers/spi.md) | none of it | nothing added. On the board too, `v1.0` keeps its configuration in `/var/lib/cfg.bin`, in RAM (讀 `src/init/init.h`, `PATH_CFG`; `src/init/mounts.c`, whose `tmpfs` is ramfs there) |
| `RLXFW-ID0` | the image's name in a capture: `v1.0` printed `RLXFW-ID0=9BB2BEC7` at boot, 讀 in three committed captures ([`sbom.md`](sbom.md)) | never printed: it is a kernel mark | a run is named by the cut's sha256 instead |
| console | the SoC's UART at 38400 8N1, 量 (`BRD-10`) | Malta's 16550, `ttyS0` | `console=ttyS0`; the terminal (`make run`) or a file (`make run-test`) |

## The host test

`make run-test` boots three times, one qemu at a time, each with its console in a file
under `run/runs/`. It polls `GET /api/status` every 0.5 s until 120 s after qemu started
(`RUN_CAP=`), never a fixed sleep: `brokerd`'s socket appears some time after `httpd`
starts, and a request in between is answered `503 broker`. A boot passes only when all
three hold:

- **S** — `/api/status` answers 200, the body begins `{"ok":true`, and its `version` is
  `BK_VERSION_STR` as `v1.0`'s `src/brokerd/brokerd.h` defines it, read with `git show`
  and never typed. `httpd` writes that string only from `brokerd`'s answer (讀
  `src/httpd/routes.c`, `h_status`), so a stand-in that answers 200 does not pass.
- **A** — `/api/config` with a well-formed invented `rlxs` cookie, 32 hex digits from the
  host's CSPRNG, answers `401 {"ok":false,"error":"auth"}`: `brokerd` holds no such session
  (讀 `src/brokerd/ops.c`, `ST_AUTH`).
- **N** — `/api/config` with a malformed `rlxs` cookie, 31 hex digits, answers
  `401 {"ok":false,"error":"nosession"}`: `httpd`'s parser drops a token that is not
  exactly 32 hex digits (讀 `src/httpd/http.c`, `take_tok32`), so this answer is decided
  without the broker, and A's came from somewhere else.

The two red controls change only the kernel command line. With `rlxsim.omit=brokerd` the
loader deletes `/usr/sbin/brokerd` from the unpacked root before `/init` starts: every
answer S gets until the cap is `503 {"ok":false,"error":"broker"}`, A gets the same, and N
still holds, which is the run that shows N needs no broker. With `rlxsim.omit=httpd`
nothing answers at all. Each control also needs the console lines, from the loader and
from `/init`, that show the program was left out and the other one started. `v1.0`'s cpio
is the same bytes in every run. `make run-test` exits 0 only when the green boot passes
(`RUN_GREEN=` boots it more than once) and both controls read red for those reasons.
Against a `make run` already up, `tools/maltarun.py probe --port 20080` runs S, A and N
once.

## What it does not establish

- Anything about the board's core (`CPU-04`): its timing, its hazards, its drivers
  ([`emulation-surface.md`](emulation-surface.md) § 8.1). A load-delay hazard, a cache
  effect or a driver defect cannot show here.
- Any code path the host test does not reach: login, configuration writes, the password
  change, ping, reboot, firmware upload, `dnsfwd`'s forwarding, DHCP.
- That `v1.0` answers the same way on the board, whose kernel, drivers, entropy and timing
  all differ from these.
- That the Debian packages are what Debian built: they are trusted through the archive's
  signatures and the pins.
