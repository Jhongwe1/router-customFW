# config/

The declarations a build is made from: what rlxfw changes in the vendor's
kernel, how the kernel is configured, and what the image holds. Every byte under
`config/` and [`kernel/`](../kernel/) is an input to `RECIPE_ID`, the build
identity the image prints at boot -- this README's bytes included.

## The kernel

| file | what it declares |
|---|---|
| [`rlxfw-sdk.config`](rlxfw-sdk.config) | the vendor SDK's top-level selection, the file its `make config` would write |
| [`rlxfw-kernel.delta`](rlxfw-kernel.delta) | the kernel configuration, as a line-by-line delta with a reason per line; checked by `tools/kconfig-delta.py` |
| [`rlxfw-marks.tsv`](rlxfw-marks.tsv) | every line of Realtek's source rlxfw changes, one row each, and the build lines for rlxfw's own files; applied and checked by `tools/rlxfw-marks.py` |
| [`host-compat/`](host-compat/) | every patch rlxfw applies to the vendor's kernel source -- see below |
| [`rlxfw-cflags`](rlxfw-cflags) | the kernel's `CFLAGS_KERNEL` |
| [`rlxfw-build-stamp`](rlxfw-build-stamp) | the build stamp, declared so that two builds of one tree can be equal |
| [`emu-path-symbols.tsv`](emu-path-symbols.tsv) | every `CONFIG_` symbol `arch/rlx`'s own sources name, derived by `tools/emueq.py refresh` |

### `host-compat/` holds more than its name says

Every patch to the vendor's kernel source is here, applied by
`tools/rlxfw-kbuild.sh` to a staged tree and never to `src-vendor/`:

- `0001` and `0004` make the 2.6.30 build run on a current host -- perl 5.22
  and later, GNU Make 4.x. This is the host compatibility the directory is
  named for.
- `0002` and `0003` make the build deterministic: `gen_init_cpio` takes its
  mtime from a declaration, and two generated headers get a content check
  instead of a blind rewrite.
- `0005` to `0010` change what the kernel can do: gpiolib on `arch/rlx` and
  `gpio_to_irq()`, vendor Ethernet interfaces that can be made un-openable, the
  NIC header's operating-mode constants outside the layered driver, one entropy
  input in `drivers/char/random.c`, and the MTD write option declared
  `default n`.

The directory keeps its name: the build driver and the records cite it by path.

## The image

| file | what it declares |
|---|---|
| [`rlxfw-initramfs.tsv`](rlxfw-initramfs.tsv) | the initramfs: every entry, where it comes from, its mode and its reason; built by `tools/mkinitramfs.py` |
| [`rlxfw-passwd`](rlxfw-passwd), [`rlxfw-group`](rlxfw-group) | the image's users and groups |
| [`rlxfw-busybox.config`](rlxfw-busybox.config), [`busybox-patches/`](busybox-patches/) | rlxfw's busybox, built by `tools/mkbusybox.sh`, and its one patch |
| [`rlxfw-user/`](rlxfw-user/) | three programs built with the vendor toolchain for the image: `iperf3`, `isaprobe`, `linkprobe` |
| [`rlxfw-init.sh`](rlxfw-init.sh), [`rlxfw-init-quiet.sh`](rlxfw-init-quiet.sh) | rlxfw's shell `/init` (`R3`, with the LAN brought up by `P2-2`), and the same without its LAN block (`R6b-8`). The image's `/init` is now the compiled PID 1 in [`src/init/`](../src/init/), as `rlxfw-initramfs.tsv` declares |
| [`image-commands.tsv`](image-commands.tsv), [`image-commands-armed.tsv`](image-commands-armed.tsv) | what the first-boot image and the armed provisioning image can invoke, derived by `tools/appletcensus.py`; `tools/cardcheck.py` refuses any other command on a bench card |
| [`mfgtest.sh`](mfgtest.sh) | the device-side manufacturing checks (`P1`) |

## The differential and the record

| file | what it declares |
|---|---|
| [`fix-cases.toml`](fix-cases.toml) | `R9`'s per-case differential register, checked by `tools/fixcases.py` |
| [`r9-probes.toml`](r9-probes.toml) | `R9`'s probe list for `tools/diffprobe.py` |
| [`r3-11-reel.tsv`](r3-11-reel.tsv) | what `R3-11`'s artefact shows, as data |
