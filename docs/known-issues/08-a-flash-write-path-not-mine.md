Part of [the known-issues index](../KNOWN-ISSUES.md): entry 8 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 The image contains a flash-write path, and it is not mine

**量 2026-09-07 (`R5-5`, `FW-44`).** `CONFIG_RTL819X_SPI_FLASH=y`, and
`spi_probe.c`'s `spi_chip_setup()` installs `mtd->write = mtd_spi_write` and
`mtd->erase = mtd_spi_erase` unconditionally. Those reach
`ComSrlCmd_ComWriteData`, `PageWrite_111002` and `ComSrlCmd_SE` — real page
program and sector erase sequences on the SPI controller. They have been in
every image this project has ever built and in the vendor's shipped one.

What keeps them from being reached is the userspace surface, not their absence:
`/dev/mtd0ro` is an odd minor and `mtdchar`'s `mtd_open` refuses it for writing
(`:73`), and every MTD node `config/rlxfw-initramfs.tsv` declares is such a minor, `0400` —
`/dev/mtd0ro`, `mtd1ro`, `mtd2ro` (🔄 2026-10-09: this named `/dev/mtdblock1`, which the declaration withdrew on 2026-08-30). **Those are access controls on a path that
exists.**

🔴 **2026-09-14 (sixty-ninth segment): that access control exists on MY side and
NOT on the vendor's, and the difference is measured.** 讀 `unsquashfs -ll` on
this unit's own shipped image — not on the extracted tree, where `unsquashfs`
without root reports `created 0 devices` and every node reads as absent, which
is a false zero this finding nearly took: `/dev/mtd0`–`/dev/mtd4` ship
`crw-rw-rw-` and **`/dev/mtdblock0`–`3` ship `brw-rw-rw-`, mode 0666**.
`/dev/mtdblock0` covers the **loader and `H601`** — the two windows this
project's own rules call unrecoverable — and `/bin/flash` (87,664 B) sits in the
same `PATH`. 讀 the board config: `# CONFIG_MTD_CHAR is not set`, so the `mtd*`
char nodes are dead (`ENODEV`), but `CONFIG_MTD_BLOCK=y`, so **`mtdblock*` is
live**. ⚠️ **This narrows the section's own sentence rather than contradicting
it**: *the userspace surface is what keeps them unreached* is true of every
image rlxfw builds and **false of the vendor's**, where nothing is in the way
except the absence of a shell. `SPEC.md` `FW-68`; the route that would reach it,
and its own flash-write cost, is `PROGRESS.md`'s `VDR-1`.

🟢 So the sentence `R5-5`'s `D4` earns is **rlxfw contributes no
flash-write code to this image**. It is *not* *this image cannot write flash*,
and no write-up may use the first to imply the second. `rtl819x-spi`'s own
device is stricter than the vendor's partitions — `MTD_CAP_ROM` means
`mtd_open` refuses it at `:94` on **either** minor, where `/dev/mtd0` is an even
minor and passes `:73` — but that is a statement about `mtd2`, not about the
image. 🔄 2026-10-23: the `D4` sentence holds only for images built before the `MK5` ruling (`notes/self-update.md` § 2.9): every image from the next build links rlxfw's own write path, the install path, and `D4`'s build-time layer is retired; the vendor's path above is unchanged.

⚠️ And `D4`'s positive control is a control **over stubs**: the write TU's two
entry points return `-EPERM` and contain no SPI transaction, deliberately,
because mainline is zero-write through `R9`. 🔄 2026-10-23: not since `R8b` item 4 (2026-10-04, `SPEC.md` `FW-207`): the write TU is a policy layer whose entry points, once armed, issue real transactions through `rtl819x-spi.c`'s engine.
