# Software bill of materials — the R7 image, as cell `f184a` built it

**`R9-10`, desk, 2026-10-04. No power, no flash byte, no device reading.** Derived with the repository at `HEAD` `d4d0dbcc`.

**Owner of:** which components are in the image `rlxfw` builds and boots; each one's version, licence and source location; and which of those are not established. It does not own the programs' designs (the notes under `notes/`), what the image does on the die (`docs/GATE-RESULTS.md`), or the image's declaration (`config/rlxfw-initramfs.tsv`).

**Marks.** 讀 is read out of a file or an artefact. 量 in this file is a desk measurement over a build artefact, a git object or a GitHub reply, never a reading off the device (the convention `notes/reproducible-build.md` states for itself). 推 is inferred and says what would settle it. 未定 is an open value, and § 9 says what settles each. 殘留 is the question left after a value is settled.

**Format.** One row per component with these fields, which carry the NTIA minimum elements: supplier and component (the component column), version, other unique identifiers (sha256 and pins), dependency relationship (the relationship column), the author of this data (this file's commit) and its timestamp (the date above). No SPDX or CycloneDX rendering exists; the tables in § 4 and § 7 are the only form.

## 1. What "the image" is, and which one this covers

`rlxfw` distributes no image. 量: the `v0.6` release has no assets (`gh release view v0.6`, 2026-10-04, `assets` is empty); nothing is written to flash through `R9` and the config store is on ramfs (讀 `README.md`). So "ships" in this file means *builds, and boots from RAM after a TFTP upload* — the bytes a distribution would contain. Nothing below discharges an obligation that distributing them would create (§ 8).

What is uploaded to `0x80500000` and jumped to is `nfjrom`, and it has three layers.

| layer | what it is | identity 讀 from the records of cell `f184a` |
|---|---|---|
| `nfjrom` | the loader stub plus the LZMA stream of the kernel, linked by the drop's own `rtkload` Makefile, driven by `tools/rtkimage.py build` | 1,108,992 bytes, sha256 `9da0857a9af8c5de24c2413a39da83d2c95e2b5e38f5fac110059804c519f720` (`rtkimage-record.tsv`, label `f184a`) |
| `vmlinux` | the kernel, with the initramfs linked in | 4,588,155 bytes, sha256 `8b67d48c4b8280e5d70ce89b889977b70cc714d48313b68ba103e7463420c54a`, recipe id `0e45c61d`, variant `quiet`; 量 the banner string in the built ELF reads `Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Tue Sep 1 00:00:00 UTC 2026` |
| initramfs | the cpio the kernel unpacks | 55 manifest rows, 17 of them files, 1,258,538 bytes of file content (§ 3, Appendix A) |

The records are under `$FWRE_WORK/rebuild/r3-4/out/` (`f184a.manifest`, `f184a.initramfs.manifest.tsv`, `f184a.build.log`, `f184a.System.map`, `f184a.vmlinux.elf`, `f184a.config-built`) and `$FWRE_WORK/rebuild/s119/fw184-work/img/image/f184a/` (`rtkimage-record.tsv`, `make.log`). None is committed.

Cell `f184a` is the most recent cell under `r3-4` (its files are dated 2026-10-03, 19:05 to 19:07) and the board ran it (`FW-186`, `FW-188`). The `loud` and `quiet-swcore` variants are other kernels, and `quiet-swcore` compiles in the vendor Ethernet tree; neither is covered. 量: in the `f184a` configuration `CONFIG_RTL_819X_SWCORE` is not set and `CONFIG_MODULES` is not set, so the kernel is one monolithic file and no `.ko` exists.

## 2. Four things checked first

### 2.1 uClibc: is its source in the drop?

**Answer: yes, and it is the source of the library that is linked.** The suspicion that LGPL source might be absent is refuted for uClibc. It holds for gcc, which is a different gap (below).

| check | reading | mark |
|---|---|---|
| which library is linked | busybox, iperf3 and the three probes are built with the `rsdk-1.3.6-4181-EB-2.6.30-0.9.30` toolchain (their Makefiles and `tools/mkbusybox.sh` name it). The six programs take the compiler driver's 4181 default and carry no `-march` (four of their Makefiles refuse one, two state it in a comment); `SOURCES.json` records that each of the three drivers accepts exactly one `-march` and that only this toolchain's is 4181. All link that toolchain's `libc.a`: 1,523,240 bytes, sha256 `519913981a093c339a7c9c414dd6f36efbcec7342b7c84767ac4925c1319a639` | 讀 |
| the toolchain copy the iperf3 Makefile names | `libc.a`, `libm.a`, `libgcc.a` and `crt1.o` have the same sha256 as the drop's (8-hex prefixes `51991398`, `a705cec6`, `3f7ea52a`, `99f049a1`) | 量 |
| the source | inside that toolchain, `config/uclibc/`: 1,764 `.c`, 722 `.h`, 24 `.S`, `COPYING.LIB` (LGPL v2.1), a `.config` with `TARGET_ARCH="rlx"`, and `Rules.mak` giving 0.9.30. The same counts hold in all three pinned drops | 量 and 讀 |
| correspondence | the tree's own `lib/libc.a` has the same sha256; 906 of 906 members of `libc.a` and 164 of 164 members of `libm.a` are byte-equal to an object (`.o`, `.os` or `.oS`) that the tree holds; `crt1.o`, `crti.o`, `crtn.o` and `Scrt1.o` equal the tree's `lib/` copies. Controls: a wrong hash matched nothing, and the tree's object set was non-empty (1,147 distinct objects in 1,158 files) | 量 |
| every image ELF is static | all 11 are ELF32 big-endian MIPS with no `PT_INTERP` and no `PT_DYNAMIC` (header parse of the `build/rlxfw-user` copies; control: a synthetic ELF carrying a `PT_INTERP` header is reported dynamic; 10 of the 11 files are the recorded bytes, `brokerd` is the build before `FW-184`) | 量 |
| libc code is inside each ELF | 94 members of the drop's `libc.a` have a relocation-free `.text` of at least 24 bytes (93 distinct patterns). Each of the 11 ELFs contains between 3 (`ucost`, `linkprobe`) and 31 (`busybox`) of them byte for byte. Controls: the same patterns with the last byte flipped matched 0 in `busybox`, the 93 patterns matched 0 in `index.html`, and `busybox` contains `memcpy`, `memset`, `strchr`, `strcmp` and `strlen` | 量 |

So each of the 11 ELF files carries its libc objects inside it, and the source of those objects is in the pinned drop.

**What is absent instead: gcc and binutils.** 量: names that only a compiler tree has (`libgcc2.c`, `reload1.c`, `ldlang.c`, `tc-mips.c`) are found in 0 of the 3 drops. The one hit, `elf32-mips.c`, sits inside `users/gdb/gdb-6.8/bfd`, which is gdb's bundled copy. The control, `fork.c` in each kernel tree, is found in all three. So `libgcc.a` (L3) and the compiler that built it (B1) have no corresponding source in any tree `SOURCES.json` pins.

**殘留 `SBOM-R1`.** Object equality shows that the in-drop tree built the archive. It does not show that the tree's `.c` files are unmodified since. Recompiling a sample of them under `tools/vendor-tripwire.sh` and comparing the objects settles it; that was not done.

### 2.2 iperf3: is it in `SOURCES.json`, and what is its licence and origin?

🔄 **2026-10-04, and the answer moved in this project's own commit `01cff02b`
(`P4b`): iperf 3.1.3 is in the image as `/bin/iperf3`, it IS in `SOURCES.json`
now, and its source tree is still not in the repository.** What is missing is
no longer the entry but the **unpack step** — `SOURCES.json`'s own `fetch_gap`
key on that entry owns the correction and states it: `build.sh` sets
`SRC=$W/src313/src`, a path no clean clone has. The sentence below it replaces
read *"it is not in `SOURCES.json`"*, which was true when written at
`76d0a121` and false from `01cff02b` onwards; this paragraph is the correction
and `SOURCES.json` is where the live statement lives.

- 讀 `/bin/iperf3` is a `file` row of `config/rlxfw-initramfs.tsv`: 252,644 bytes, sha256 `3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8`, static. 🔄 量 2026-10-04: `SOURCES.json` carries an `iperf3` entry with role `imported-source`, three independent origins, `dest refs/iperf-3.1.3.tar.gz` and a `fetch` line, so its `imported-source` role now holds **two** entries and not one — `tweetnacl` and this. The superseded reading (*"the file contains the word 0 times"*) was taken before `01cff02b`.
- Origin 讀 (`notes/iperf3-port.md` § 1): ESnet's iperf at tag 3.1.3, three routes that agree on all sixteen compiled files: the GitHub tag archive (549,466 bytes, sha256 `e34cf60cffc80aa1322d2c3a9b81e662c2576d2b03e53ddf1079615634e6f553`), the Debian orig tarball from `archive.debian.org` (546,899 bytes, sha256 `60d8db69b1d74a64d78566c2317c373a85fef691b8d277737ee5d29f448595bf`), and a clone at tag 3.1.3 (commit `274eaed5b17f664e4ac6c79f1ba854b55f15a3a3`). 讀 `configure.ac` of the tree on disk: `AC_INIT(iperf, 3.1.3, ...)`.
- Where it lives 讀: `$FWRE_WORK/iperf3-port/src313/`, outside any clone. The repository holds the recipe only, `config/rlxfw-user/iperf3/` (4 files: `Makefile`, `build.sh`, `probe.sh`, `iperf_config.h`), and that Makefile says in so many words that a clean clone cannot build this target.
- Licence 讀 from the tree's `LICENSE`: the Lawrence Berkeley National Laboratory three-clause BSD licence with an enhancements paragraph. The same file lists code bundled inside it: `cjson` (MIT, Dave Gamble); `net` (MIT, Russ Cox, with a Lucent permission notice); `queue.h` (three-clause BSD, Regents of the University of California); `tcp_window_size` and `units` (the University of Illinois / NCSA permission text); `portable_endian.h` (public domain). 量 over the 16 compiled sources: 13 carry the LBNL header, 1 the cJSON text, 2 the Illinois text.

It is not rlxfw's code and not rlxfw's to describe as such. 🔄 **2026-10-04: the entry exists, so what would settle `SBOM-3` is now narrower** — the step that unpacks `refs/iperf-3.1.3.tar.gz` into a tree `build.sh` can point `SRC` at, plus a run of `tools/fetch-sources.sh` succeeding on a fresh clone, with a corrupted-sha256 fetch refused as the control that the success is a reading. Until that step is written, the entry pins the bytes and does not make the target buildable from a clean clone, which is why `SBOM-3` stays 未定 — and not for want of an entry (`SOURCES.json`'s `fetch_gap` key owns this statement). 🔄 2026-10-05: the entry is `fetch: now`, so `tools/fetch-sources.sh` plans it and re-checks this sha256 on every run (量 `--list` names it), and `tools/srcarchive.py` packs the pinned tarball into a release's corresponding-source archive; until then its `fetch` was a command line, which the planner does not plan.

### 2.3 rlxfw's own code: does it carry a licence?

**Answer: yes, since 2026-10-04 (`P4b`) — `GPL-2.0-only` for rlxfw's own kernel
files, `MIT` for its userspace, tools, scripts, declarations, assets and
documents.** 讀 `LICENSE` carries the MIT text, `NOTICE` § 1 carries the two
clauses and the one sentence that decides each, and `config/rlxfw-src/LICENSE`
carries the kernel clause where it cannot move a line number. The four
measurements below are **kept as the record of what was absent** on 2026-10-04
before that commit, and the first of them is the one that has changed: 量
`git ls-files` now matches `LICENSE` and `NOTICE`.

- 量 GitHub reports the repository's `license` as null (`gh api repos/Jhongwe1/router-customFW`, 2026-10-04). 量 no `LICENSE`, `LICENCE`, `COPYING`, `NOTICE` or `COPYRIGHT` file is tracked (`git ls-files`, 0 matches).
- 量 8 files carry an `SPDX-License-Identifier` in their first 12 lines, of 16,061 tracked files at `d4d0dbcc` (the total moves with every capture commit: 15,476 of them are under `bench/` and 585 are not). All 8 are under `dt/`: six device-tree bindings (`GPL-2.0-only OR BSD-2-Clause`), `rtl8196e.dtsi` and `rtl8196e-totolink-n150rt.dts` (`GPL-2.0-only OR MIT`). None is in any image: 讀 the `f184a` manifest has no `.dts` or `.dtb` row, and the 2.6.30 port has no device-tree support (`SOURCES.json`, `reference_only`). A raw `git grep` finds a ninth line, in `tools/dtcheck.py`; it is a fixture string, not a tag.
- 量 over the 126 tracked files in the directories that build the image's own code (userspace 91, kernel 16, probes 9, the iperf3 recipe 4, assets and configuration 6; tests included): 0 carry a copyright line. 1 states a licence for rlxfw's own code: the `MODULE_LICENSE("GPL")` macro in the `rtl819x-wdt` driver, which the kernel reads as a declaration of GPL compatibility. 4 mention a licence for another reason: `ed25519` and `sha512` declare the imported TweetNaCl public domain (and only `rlxboot` links them, § 7); `uprobe` and `ucost` use the words in prose. The census read each file whole; its first pass read 64 KiB per file and missed the `MODULE_LICENSE` at the end of a 69 KB driver, which its positive control caught.
- "Own" in this file is a statement about provenance (no imported source, no `IMPORTED` marker, first commit in this repository), not about who holds the copyright.

What would settle it is the owner declaring a licence (`SBOM-1`). 推: the twelve kernel files link into a GPL-2.0-only kernel, so their licence has to be GPL-2.0 compatible; counsel settles the reading.

### 2.4 The base tree is a third party's repository

**Answer: it is, and a pin on someone else's repository is not this project's own offer.**

- 讀 `SOURCES.json` gives the base drop, `rtl819x-toolchain` (role `base`), the URL `github.com/frederic/rtl819x-toolchain` and the pin `5c9be5d943318fdb4d048ae22078129594eb5a10`, which its `pin_note` calls the commit this project actually read. The drop that carries the kernel, busybox, uClibc and the loader stub is that repository.
- 量 (`gh api`, 2026-10-04): `frederic/rtl819x-toolchain` is public, not archived, last pushed 2020-03-08, and `license` is null; the pinned commit resolves (committer date 2014-03-24, message "update README"). The other two GPL drops are the same: `jameshilliard/WECB-VZ-GPL` and `Saturn49/wecb` both report `license` null and both pins resolve.
- 量 the on-disk clone's `HEAD` equals the pin in all three drops (`git rev-parse`, 2026-10-04, and again 2026-10-05). Its tree was clean in all three on 2026-10-04 (`git status --porcelain`: 0 lines); 🔄 量 2026-10-05, `rtl819x-toolchain` reads 3 lines — three tracked files under `users/miniigd/` deleted from its working tree — while the other two still read 0. So a copy of the working tree is not the pinned commit; 推 the kernel build is unaffected, the three being under `users/` and not `linux-2.6.30/`.
- 讀 what does not exist: a copy of these trees that this project holds and offers. `src-vendor` is a symlink into `$FWRE_WORK`, which no clone has; `SOURCES.json` records a URL and a pin, not a copy; `P4b`, the corresponding-source gate, is in progress (`PROGRESS.md`: `~`) and the archive it owes does not exist.
- 推 (GPL-2.0 section 3, which counsel should read): the distributor supplies the source with the binary, or a written offer of its own; a URL it does not control is neither. The pin makes the third party's repository a citable artefact; it does not make it this project's offer, and the third party can delete or rewrite it.

`notes/busybox-build.md` § 8 lists busybox's four corresponding-source inputs and says all four are committed. Three are in this repository; the fourth is this third-party tree, and what is committed is its pin.

## 3. Coverage of the manifest

`config/rlxfw-initramfs.tsv` at `HEAD` is the `R7` manifest. There is no separate one: `R7-8` rewrote the file in place (commit `f353b7b8`) and its header still reads "R3-5". 量 two parses over 55 rows each: the declaration at `HEAD` and the manifest `f184a` recorded have the same 55 `(kind, path)` pairs, and the difference is empty in both directions.

| kind | rows | `owner=rlxfw` | `owner=unit` | what it is |
|---|---:|---:|---:|---|
| `file` | 17 | 17 | 0 | the content; each belongs to one component row in § 4 (Appendix A) |
| `slink` | 11 | 11 | 0 | the 11 busybox applet names `sh ash cat echo ls mount ps ifconfig ping mkdir sleep`; no bytes (covered by U8) |
| `nod` | 11 | 11 | 0 | device nodes; no bytes, no component |
| `dir` | 16 | 9 | 7 | directories; no bytes, no component. The 7 `unit` rows are `/bin /dev /lib /proc /sys /var /etc`: the tag records that the directory exists in this unit's dump and carries nothing from it |

The `owner` column says which tree a row was carved from or built in. It does not say who wrote the bytes: `/bin/busybox` and `/bin/iperf3` are tagged `rlxfw` because rlxfw built them.

量 identity: for 16 of the 17 `file` rows the sha256 recorded for `f184a` equals the file at the same `$REPO` path in the working tree. The 17th, `/usr/sbin/brokerd`, differs: recorded 101,212 bytes (built after `FW-184`), working-tree `build/` copy 101,172 bytes (the build before it). The `build/` copy is stale, not the manifest.

Appendix A maps each of the 17 `file` rows to its component row in § 4.

The 11 ELF files total 1,206,012 bytes; busybox and iperf3 are 700,328 of them. Each of the 11 also contains uClibc objects (L1), which this split does not separate.

## 4. Components in the image

31 rows: **24 resolved, 7 未定** 🔄 **re-derived 2026-10-04 (`P4b`), from 8 and 23**: `SBOM-1` closed and 量 **16** of this table's rows named it as their only reason, so 8 + 16 = 24 and 23 − 16 = 7. The seven are `W1`, `K2`, `K3`, `K4`, `K5` (`SBOM-2`), `U9` (`SBOM-3`) and `L3` (`SBOM-4`) — counted off the status column, not carried. A row is **resolved** when its version, licence, source location and relationship are all established; **未定** when one is not, with the register entry in § 9. Hashes are 8-hex prefixes; Appendix A has the full digests of the 17 files.

| id | component | version | licence | source | relationship | status |
|---|---|---|---|---|---|---|
| W1 | `rtkload` loader stub (Realtek): `start`, `hfload`, `read_memory`, `vsprintf`, `prom_printf`, `string`, `ctype`, `misc`, `cache`, and the kernel-blob wrapper `vmlinux_img` | none of its own; SDK family `rtl819x-SDK-v32_v321_v3211_322_3221` 讀 (the build path in the DWARF of the drop's prebuilt, `notes/kernel-build.md` § 13.1) | GPL-2.0 by the directory's `COPYING` 讀. Per file 讀: 3 of the 10 cite it (`cache`, `hfload`, `read_memory`), 4 carry a copyright line only (`ctype`, `string`, `vsprintf` by Linus Torvalds; `prom_printf` by Harald Koerfgen), 3 carry neither (`misc`, `start`, `vmlinux_img`) | `SOURCES.json` `rtl819x-toolchain`, directory `linux-2.6.30/rtkload/` | contained in `nfjrom`; the link line in the build's `make.log` names these objects 量 | 未定 `SBOM-2` |
| W2 | LZMA decoder `LzmaDecode`, inside the stub | LZMA SDK 4.22 (Igor Pavlov, 2005-06-10) 讀 the `.c` header; the `.h` says 4.21 | LGPL (version not stated) or CPL, the licensee's choice, plus Pavlov's special exception for linking to the file's interfaces 讀 header | `rtl819x-toolchain`, same directory | linked into the stub; `LzmaDecode.o` is on the link line 量 | resolved |
| K1 | Linux kernel, generic code: 489 of the 618 compiled sources (outside the Realtek-named directories and rlxfw's twelve) | 2.6.30.9 讀 top-level `Makefile` of the staged tree; 量 the banner in `f184a.vmlinux.elf` | GPL-2.0-only 讀 `COPYING`, which says the only valid version of the GPL for the kernel is v2, "(ie v2, not v2.2 or v3.x or whatever), unless explicitly otherwise stated". Header scan 量: 229 carry GPL text in the first 80 lines, 13 only a `MODULE_LICENSE`, 231 a copyright line or nothing (`COPYING` conveys them), 16 a BSD or public-domain keyword (keyword hits: the network stack's headers say "BSD socket") | `rtl819x-toolchain` (role `base`), directory `linux-2.6.30/`; board template `boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW`, sha256 `44f781de`, which `config/rlxfw-kernel.delta` names as its baseline 讀 | linked into `vmlinux`; the initramfs is linked in as `usr/initramfs_data` | resolved; 殘留 `SBOM-R4` |
| K2 | Realtek Lexra port and board BSP: `arch/rlx` and `boards/rtl8196e/bsp` (59 compiled sources) | none of its own; SDK family as W1 | GPL-2.0 text in 39 of 59 headers 讀; the other 20 carry a copyright line (8) or nothing (12), listed in Appendix B | `rtl819x-toolchain`, directories `linux-2.6.30/arch/rlx/` and `boards/rtl8196e/` | linked into `vmlinux` | 未定 `SBOM-2` |
| K3 | Realtek WLAN driver `rtl8192cd` with its `OUTSRC` ODM code (42 compiled sources) | 1.6 讀 `DRV_VERSION_H` 1 and `DRV_VERSION_L` 6 in `8192cd_cfg.h`; the release-date macro there is 2012-12-04 and is redefined in another branch of the same header, which one applies to this build is not read | GPL-2.0 text in 34 of 42 headers (the three read in full say version 2, with no "or later"), and `MODULE_LICENSE("GPL")` present 讀. Of the other 8, 3 carry a third party's notice (K3a, K3b, K3c) and 5 are Realtek's with a copyright line only (`HalPwrSeqCmd`, `Hal8188EPwrSeq`, `Hal8188ERateAdaptive`) or nothing (`8192d_hw`, `HalDMOutSrc`) | `rtl819x-toolchain`, directory `linux-2.6.30/drivers/net/wireless/rtl8192cd/` | linked into `vmlinux` (`CONFIG_RTL8192CD=y`, `CONFIG_RTL_88E_SUPPORT=y`; 92C and 92D support are not set 量). The four MCU firmware arrays in that directory (`data_rtl8192cfw`, `data_rtl8192cfwn`, `data_rtl8192cfwua`, `data_rtl8192dfw_n`) are absent from the ELF: a leading and a middle 32 bytes of each were searched and not found, with controls (the banner and the cpio magic found, an impossible pattern not found) 量 | 未定 `SBOM-2` |
| K3a | RC4 reference code (Eric Young), file `1x_rc4`, inside K3 | none; the file's first line is a comment naming its SSLeay origin, `crypto/rc4/rc4_enc` 讀 | the SSLeay licence, with its advertising clause (clause 3) and the closing paragraph that the code "cannot simply be copied and put under another distribution licence [including the GNU Public Licence.]" 讀 header | K3's directory | compiled in: `RC4`, `RC4_options` and `RC4_set_key` are at `8017c164`, `8017c724` and `8017c730` in `f184a.System.map` 量 | resolved; 殘留 `SBOM-R3` |
| K3b | MD5 reference code (RSA Data Security, Inc.), file `1x_md5c`, inside K3 | none | RSA's MD5 permission text: copy and use granted if identified as the "RSA Data Security, Inc. MD5 Message-Digest Algorithm"; derivative works identified as "derived from" it 讀 header | K3's directory | compiled in (`1x_md5c.o` is in the build log 量) | resolved |
| K3c | AES (Brian Gladman, "an independent implementation" of Rijndael, 14 January 1999), file `1x_kmsm_aes`, inside K3 | dated 1999-01-14 讀 header | permission "for its free direct or derivative use subject to acknowledgment of its origin and compliance with any conditions that the originators of the algorithm place on its exploitation" 讀 header | K3's directory | compiled in (`1x_kmsm_aes.o` is in the build log 量) | resolved |
| K4 | Realtek NAT fast path and its glue: `net/rtl/fastpath`, `net/rtl/features` (10 compiled sources) | none of its own; SDK family as W1 | 9 of the 10 carry no text; `fastpath_common` carries `MODULE_LICENSE("GPL")` only 讀. 6 of the 10 are compiler output in assembler form (`.file "fastpath_core.c"`, `.ident "GCC: (GNU) 3.4.6-1.3.6"`), and 量 none of the six has a C source in any of the three drops (names searched in each, control `fork.c`); `config/host-compat/0007`'s header calls them "compiler output" | `rtl819x-toolchain`, directory `linux-2.6.30/net/rtl/` | linked into `vmlinux` (`CONFIG_RTL_IPTABLES_FAST_PATH=y`) | 未定 `SBOM-2` |
| K5 | other Realtek-named vendor code: the flash map `rtl819x_flash`, the SPI chip layer (4 files under `drivers/mtd/chips/rtl819x`), and `rtl_gpio` (6 compiled sources) | none of its own; SDK family as W1 | GPL-2.0 text in 4 of 6 (`spi_common`, `spi_flash`, `spi_probe`, `rtl_gpio`); `spi_cmd` carries a third party's copyright line only ("(C) 2006 Atmark Techno, Inc."); `rtl819x_flash` carries `MODULE_LICENSE` only 讀 | `rtl819x-toolchain`, directories `linux-2.6.30/drivers/mtd/` and `linux-2.6.30/drivers/char/` | linked into `vmlinux` | 未定 `SBOM-2` |
| K6 | rlxfw's own kernel code, 12 compiled sources: `rlxfw-devices`, `rlxfw_mark`, `rlxfw-entropy`, `rtl819x-timer`, `rtl819x-gpio`, `rtl819x-keys`, `rtl819x-spi`, `rtl819x-wdt`, `rtl819x-nic`, `rtl819x-switch`, `rtl819x-view`, `rlxfw-seam` | none; identity is the file digests in the repository. What each driver read of other implementations is `docs/blind-write-ledger.md`'s | `GPL-2.0-only`, declared for every file under `config/rlxfw-src/` by `config/rlxfw-src/LICENSE` and `NOTICE` § 2 (`LIC-01`). In the files themselves 11 of the 12 carry no licence or copyright text of any kind, and `rtl819x-wdt` has `MODULE_LICENSE("GPL")` and nothing else 讀 | repository `config/rlxfw-src/linux-2.6.30/` (16 files at `d4d0dbcc`: these 12, `rtl819x-spi-write` which is declared and not built because `CONFIG_MTD_RTL819X_WRITE` is not set, and 3 headers). 🔄 量 2026-10-05 at `c7716fbe`: 17, the 17th a fourth header, `rtl819x-spi-wrpolicy.h`, added by `fa36f7a2` and compiled only where `CONFIG_MTD_RTL819X_WRITE` is set, which no committed image sets | copied into the staged tree and linked into `vmlinux` | resolved |
| K7 | rlxfw's edits to vendor kernel and build files, and the scripts that build and wrap the image: `config/rlxfw-marks.tsv`, `config/host-compat/`, `config/rlxfw-kernel.delta`, `tools/rlxfw-kbuild.sh`, `tools/rlxfw-marks.py`, `tools/kconfig-delta.py`, `tools/mkinitramfs.py`, `tools/rtkimage.py`, `tools/vendor-tripwire.sh`. 🔄 2026-10-05: `tools/kconfig-delta.py` was missing from this list; 讀 the build driver calls it, at `d4d0dbcc` as at `HEAD`, to derive the `.config` from the delta | 28 marks rows and 9 patches 量 (`f184a.manifest`: `marks 28`, `host_compat_patches 9`). 讀 the patch headers: 0002 and 0005 to 0009 (6) change what the image contains; 0001, 0003 and 0004 touch only the host build | mixed, by `NOTICE` § 3 (`LIC-01`): a hunk or row that changes a GPL-2.0 file is GPL-2.0 推, and the prose — reason columns, patch headers — is `MIT`; the scripts are `MIT` (`NOTICE` § 4). 讀 none of the rows, patches or scripts states it itself | repository, those paths | applied to the staged tree before the build; the scripts run the build | resolved |
| U1 | `/init`, rlxfw's PID 1 | no version string; 75,128 bytes, sha256 `77571ca3`; source revision `f353b7b8`. 🔄 Not this SBOM's image: since `034b5a7d` (2026-10-08, `R6c`'s `vlan` verb) the tree builds it at 75,144 bytes, sha256 `ae1f2645`, 量 two builds byte-equal (`$FWRE_WORK/rebuild/s128/p/run/r6c/`) | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `src/init/`, `src/lib/` | initramfs file; static ELF 量; statically links L1 and L3 | resolved |
| U2 | `/sbin/ifupd` | no version string; 23,164 bytes, sha256 `9bd95a79`; revision `f353b7b8` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `src/ifupd/`, `src/lib/` | initramfs file; static ELF 量 | resolved |
| U3 | `/usr/sbin/brokerd` | no version string; 101,212 bytes, sha256 `263aad52`; revision `44b333d6` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `src/brokerd/`, `src/lib/` | initramfs file; static ELF 量 | resolved |
| U4 | `/usr/sbin/httpd` | no version string; 83,836 bytes, sha256 `d301a049`; revision `f353b7b8` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `src/httpd/`, `src/lib/` | initramfs file; static ELF 量 | resolved |
| U5 | `/usr/sbin/dnsfwd` | no version string; 73,908 bytes, sha256 `ced6956e`; revision `f353b7b8` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `src/dnsfwd/`, `src/lib/` | initramfs file; static ELF 量 | resolved |
| U6 | `/usr/sbin/cfgstore` | no version string; 86,320 bytes, sha256 `abc6b5f7`; revision `f353b7b8` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `src/cfgstore/`, `src/lib/` | initramfs file; static ELF 量 | resolved |
| U7 | rlxfw's shared library units, compiled into U1 to U6: `cfg`, `client`, `crc32`, `json`, `kdf`, `netutil`, `proto`, `schema`, `sha256`, `tlv` | none; revision `f353b7b8`. `kdf` says "Written from the RFC text. No third-party code." and `sha256` says it was written from FIPS 180-2, RFC 6234 and RFC 2104 讀 (the author's statements) | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the files themselves 讀 | repository `src/lib/`. `ed25519` and `sha512` also live there and only `rlxboot` links them (§ 7) | static objects inside U1 to U6, not a file of its own; which units each program links is in the programs' Makefiles and is not enumerated here | resolved |
| U8 | BusyBox, `/bin/busybox` with the 11 applet symlinks | 1.13.4 讀 `Makefile` of `users/busybox-1.13` (VERSION 1, PATCHLEVEL 13, SUBLEVEL 4) and `busybox.build`; 量 the banner `BusyBox v1.13.4 (2026-09-01 00:00:00 UTC)` in the ELF; 447,684 bytes, sha256 `ef057f6e`; 53 applets, 43 ash builtins | GPL-2.0-only 讀 `LICENSE` ("Version 2 is the only version of this license which this version of BusyBox (or modified versions derived from this one) may be distributed under"). Header scan 量 over the 203 compiled sources: 178 GPL text, 3 GPL and BSD, 2 GPL and public domain, 6 BSD only (`change_identity`, `restricted_shell`, `run_shell`, `setup_environment`, `uidgid_get`, `traceroute`), 14 a copyright line or nothing. BSD-licensed sources are among those compiled; which of them the link kept is not enumerated | `rtl819x-toolchain`, directory `users/busybox-1.13/`, the source is byte-identical in `saturn49-wecb` and `wecb-vz-gpl` (`notes/busybox-build.md` § 2; the base copy also carries 14 build products), and the build's gate G1 compares against the second drop (`ref_drop saturn49-wecb` 讀 `busybox.build`); the recipe rlxfw wrote is U8b | initramfs file, static ELF built with the 4181 toolchain; `notes/busybox-build.md` owns the build and § 8 its GPL input list. 讀 its `Makefile.flags` puts `-lm -lcrypt` on the link line; 量 the unstripped link's 1,857 symbol names include 769 of `libc.a`'s 1,863 defined globals, none of `libm.a`'s 233 and none of `libcrypt.a`'s 5 (control: 200 invented names, 0), so only libc and libgcc objects were pulled in | resolved; 殘留 `SBOM-R2` |
| U8b | rlxfw's busybox recipe: `config/busybox-patches/0001-udhcpd-drop-notify_file-system-hook.patch`, `config/rlxfw-busybox.config`, `tools/mkbusybox.sh` | none; 量 the configuration's sha256 `bc940e48` equals the `config_sha256` in `busybox.build`; the patch removes udhcpd's `notify_file` hook and the `system()` call behind it (`notes/busybox-build.md` § 4) | mixed, by `NOTICE` § 3 (`LIC-01`): the patch's `+`/`-` lines take busybox's GPL-2.0-only 推 and its header is `MIT`; the configuration and `tools/mkbusybox.sh` are `MIT` (`NOTICE` § 4). 讀 none of the three states it itself | repository, those three paths | applied to the staged busybox source before the build; gate G2 refuses a build in which a declared patch did not apply (`notes/busybox-build.md` § 2) | resolved |
| U9 | iperf 3.1.3 (ESnet and Lawrence Berkeley National Laboratory), `/bin/iperf3` | 3.1.3 讀 `configure.ac` and `notes/iperf3-port.md`; 252,644 bytes, sha256 `3144db60` | LBNL three-clause BSD with an enhancements paragraph 讀 `LICENSE`; bundled `cjson` MIT, `net` MIT, `queue.h` BSD, `tcp_window_size` and `units` University of Illinois text, `portable_endian.h` public domain (§ 2.2) | 🔄 2026-10-04: **in `SOURCES.json` since `01cff02b`** (role `imported-source`, three origins, `dest refs/iperf-3.1.3.tar.gz`), still **not in the repository**. Origins in `notes/iperf3-port.md` § 1; the tree used is `$FWRE_WORK/iperf3-port/src313/`. The repository holds the recipe only, `config/rlxfw-user/iperf3/`, and the unwritten step is the unpack — `SOURCES.json`'s `fetch_gap` owns it | initramfs file, static ELF; links L1, L2 (`-lm`) and L3; nothing in `/init` starts it | 未定 `SBOM-3` |
| U10 | `/bin/uprobe` | no version string; 29,184 bytes, sha256 `f3bf56ee`; first commit 2026-09-15 | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `config/rlxfw-user/isaprobe/uprobe.c` with `tools/rlxprobe/` `cells4.S` (generated by `tools/isapay.py emit`), `probe4rows.h`, `rlxasm.h` | initramfs file; static ELF 量 | resolved |
| U11 | `/bin/ucost` | no version string; 16,692 bytes, sha256 `76c7e231`; first commit 2026-09-16 | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `config/rlxfw-user/isaprobe/ucost.c`, `ucost-cells.S` | initramfs file; static ELF 量 | resolved |
| U12 | `/bin/linkprobe` | no version string; 16,240 bytes, sha256 `071c8f81`; first commit 2026-09-26 | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀. It includes two kernel headers from the toolchain's sysroot (`<linux/ethtool.h>`, `<linux/sockios.h>`), GPL-2.0 headers used at compile time; the kernel's `COPYING` says it does not cover user programs that use kernel services through system calls 讀 | repository `config/rlxfw-user/linkprobe/linkprobe.c` | initramfs file; static ELF 量 | resolved |
| U13 | `/bin/mfgtest`, a shell script run by the image's own ash | no version string; 32,620 bytes, sha256 `d954de73`; first commit 2026-09-17 | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the file itself 讀 | repository `config/mfgtest.sh`; `docs/mfgtest.md` owns it | initramfs file, script | resolved |
| U14 | the web UI: `/srv/www/index.html`, `static/style.css`, `static/app.js` | 3,850, 3,430 and 12,488 bytes; sha256 `f7afe413`, `730ef34f`, `5907e45d`; revision `f353b7b8` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the files themselves 讀 | repository `srv/www/` | initramfs files; 量 the three reference only each other (no external script, stylesheet or font) | resolved |
| U15 | `/etc/passwd` and `/etc/group` | 101 and 37 bytes; sha256 `dcb10945`, `abe98245` | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the files themselves 讀 | repository `config/rlxfw-passwd`, `config/rlxfw-group` | initramfs files; configuration data | resolved |
| L1 | uClibc C library, static: `libc.a` and the start files `crt1.o`, `crti.o`, `crtn.o` | 0.9.30 讀 `Rules.mak` (MAJOR_VERSION 0, MINOR_VERSION 9, SUBLEVEL 30) and the toolchain's directory name; built for `TARGET_ARCH="rlx"`, MIPS ISA 1, big-endian 讀 `.config` | LGPL-2.1 讀 `COPYING.LIB` and `COPYING.LIB.boilerplate` ("Licensed under the LGPL v2.1"). Header scan 量 over the tree's 1,494 sources outside `test/` (an upper bound on what the archive holds): 1,249 LGPL, 131 Sun fdlibm permission text, 25 BSD only, 14 LGPL and BSD, 11 public-domain mentions (7 of them the `malloc-standard` files), 1 ISC style, 1 LGPL and public domain, 1 LGPL and BSD and ISC, 14 copyright line only, 41 nothing, 6 GPL (all under `extra/config/lxdialog`, host tooling that is not in `libc.a`) | `rtl819x-toolchain`, directory `toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/config/uclibc/`, the same in `saturn49-wecb` and `wecb-vz-gpl` | static link into all 11 ELF files, each holding byte-identical `libc.a` members; the source corresponds at object level (§ 2.1) | resolved; 殘留 `SBOM-R1` |
| L2 | uClibc maths library, `libm.a` | as L1; 327,214 bytes, sha256 `a705cec6` | LGPL-2.1 for uClibc's own files; the fdlibm-derived files carry Sun's text "Permission to use, copy, modify, and distribute this software is freely granted, provided that this notice is preserved" 讀 (`e_sqrt`). 量 over `libm`: 90 Sun text, 47 LGPL, 4 public domain, 1 nothing | as L1 | 讀 `-lm` is on iperf3's and busybox's link lines; the six programs and the three probes link with `-static` alone. 量 of 11 relocation-free `libm.a` members, 3 (`s_copysign`, `s_fabs`, `s_fpclassify`) are in iperf3 byte for byte and none is in the other ten ELFs (a lower bound for them); busybox's link holds none of `libm.a`'s symbols (U8) | resolved |
| L3 | `libgcc.a` of gcc 3.4.6-1.3.6 | gcc 3.4.6-1.3.6 讀 (the `.ident` strings in the compiler's own output and the kernel banner). The toolchain has two variants: the default `libgcc.a` (346,846 bytes, sha256 `3f7ea52a`) and `4181/libgcc.a` (347,738 bytes, sha256 `01a4f930`); 25 of their 103 members differ. 量: members of the default variant (`_fpcmp_parts_df`, `_pack_df`, `_unpack_df`, and in iperf3 also `_pack_sf`, `_unpack_sf`, `_cmpdi2`) are found byte for byte in 7 of the 11 ELFs, and four of those six differ between the variants, so the default variant is the one linked | 推: GPL-2.0-or-later with the libgcc linking exception, from upstream gcc 3.4's `libgcc2.c` header. It cannot be read here: no tree holds gcc source | binary only, `rtl819x-toolchain` `toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/lib/gcc/mips-linux/3.4.6-1.3.6/`; no source in any of the 3 drops (§ 2.1) | static link into `init`, `brokerd`, `httpd`, `dnsfwd`, `cfgstore`, `busybox` and `iperf3` (量, above). `ifupd`, `uprobe`, `ucost` and `linkprobe` matched none of the 16 relocation-free probe members, a lower bound and not a proof that they hold none | 未定 `SBOM-4` |

## 5. The five `/bin` entries that are not busybox applets

讀 the committed capture `bench/2026-10-04/SOAK-BB2`, a reading off the device that `FW-189` owns: `ls /bin` returns exactly seventeen entries, `busybox`, the 11 applet symlinks, and these five.

| entry | own or imported | evidence | bytes and sha256 prefix | where its source is | licence |
|---|---|---|---|---|---|
| `linkprobe` | **own** | 讀 one source file, first committed 2026-09-26 (`920875f4`); its Makefile's `IN_NAMES` is `linkprobe.c` alone; no `IMPORTED` marker; named nowhere in `SOURCES.json` | 16,240 / `071c8f81` | `config/rlxfw-user/linkprobe/linkprobe.c` | `MIT` (`NOTICE` § 4, `LIC-01`); none stated in the file |
| `mfgtest` | **own** | 讀 a busybox-ash script, first committed 2026-09-17 (`46e6df75`); 量 the image's file has the same sha256 as `config/mfgtest.sh` | 32,620 / `d954de73` | `config/mfgtest.sh` | `MIT` (`NOTICE` § 4, `LIC-01`); none stated in the file |
| `ucost` | **own** | 讀 first committed 2026-09-16 (`9d4f8e30`); it hand-writes its probed words and `tools/ucostcheck.py` checks each against `tools/isa-payload.tsv` (the manifest's note) | 16,692 / `76c7e231` | `config/rlxfw-user/isaprobe/ucost.c`, `ucost-cells.S` | `MIT` (`NOTICE` § 4, `LIC-01`); none stated in the file |
| `uprobe` | **own** | 讀 first committed 2026-09-15 (`490f5f51`); it links `cells4.S`, which `tools/isapay.py emit` generates, so the 75 encodings bare metal ran are the same bytes | 29,184 / `f3bf56ee` | `config/rlxfw-user/isaprobe/uprobe.c` with `tools/rlxprobe/cells4.S`, `probe4rows.h`, `rlxasm.h` | `MIT` (`NOTICE` § 4, `LIC-01`); none stated in the file |
| `iperf3` | **imported**: ESnet's iperf 3.1.3. rlxfw wrote only the recipe, including `iperf_config.h`, which replaces what `./configure` would generate | 讀 the tree's `LICENSE` and the headers of its 16 compiled sources name the Regents of the University of California / LBNL, the University of Illinois, MIT and others (§ 2.2) | 252,644 / `3144db60` | in `SOURCES.json` since `01cff02b` (entry `iperf3`, `dest refs/iperf-3.1.3.tar.gz`), not in the repository; the tree used is `$FWRE_WORK/iperf3-port/src313/` | LBNL BSD-style plus bundled notices (§ 2.2) |

## 6. `IMG-1` clause 2, re-derived

`IMG-1` is a row of `PROGRESS.md` § Carried forward. `SPEC.md` has no row of that name (量: 0 occurrences). Its clause ② reads: "**four of five `file` entries in `config/rlxfw-initramfs.tsv` are `owner=unit`** — the vendor's busybox, uClibc and libgcc out of this device's dump, so the image is not all mine to publish".

量, from the git object of the declaration at each tag (not from the working tree), counting `file` rows by owner:

| revision | commit | `file` rows | `owner=unit` | `owner=rlxfw` | the `unit` rows |
|---|---|---:|---:|---:|---|
| `v0.0` | `ba252e35` | — | — | — | the file does not exist at this tag |
| `v0.2` | `432a83da` | 5 | 4 | 1 | `/bin/busybox`, `/lib/libuClibc-0.9.30.3.so`, `/lib/ld-uClibc-0.9.30.3.so`, `/lib/libgcc_s.so.1` |
| `v0.3` | `da8cbf6f` | 5 | 4 | 1 | the same four |
| `v0.4` | `aaba65ce` | 8 | 4 | 4 | the same four |
| `v0.5` | `8e1ca57e` | 10 | 4 | 6 | the same four |
| `v0.6` | `4b110a0b` | 17 | 0 | 17 | none |
| `HEAD` | `d4d0dbcc` | 17 | 0 | 17 | none |

The clause was true at `v0.2` (4 of 5) and stayed at 4 through `v0.5` (4 of 10). It stopped being true when `R7-8` deleted five rows: the three vendor files and the two loader-name symlinks `/lib/libc.so.0` and `/lib/ld-uClibc.so.0` (讀 the deletion note in the declaration), and re-pointed `/bin/busybox` at rlxfw's build. At `HEAD` it is 0 of 17. The only `unit` rows left are the seven directories.

The clause's premise is gone. Its conclusion, that the image is not all rlxfw's to publish, is not, and the reasons are different ones: the kernel is Realtek's GPL tree with Realtek's WLAN driver in it (K1 to K5); busybox and iperf3 are other people's programs (U8, U9); every ELF embeds uClibc (LGPL) and some embed libgcc (L1, L3); 35 Realtek-directory sources carry no licence text (`SBOM-2`); the image carries no licence text and no source offer (讀: none of the 17 `file` rows is a notice); and rlxfw's own licence, declared since 2026-10-04 (`LIC-01`), is not in the image either.

## 7. Built here but not in the image, and build-time only

10 rows: **6 resolved, 4 未定** 🔄 **re-derived 2026-10-04 (`P4b`), from 4 and 6**: 量 `X1` and `X2` named `SBOM-1` as their only reason, so 4 + 2 = 6 and 6 − 2 = 4. The four are `B1` (`SBOM-4`), `B2` (`SBOM-5`), `B3` (`SBOM-6`) and `E1` (`SBOM-7`). 16 + 2 = 18 is what `SBOM-1`'s own row in § 9 claims, and it closes.

| id | component | version | licence | source | relationship | status |
|---|---|---|---|---|---|---|
| B1 | the `rsdk-1.3.6-4181-EB-2.6.30-0.9.30` toolchain: gcc, binutils, the `rsdk-linux-*` wrappers | gcc 3.4.6-1.3.6 and binutils 2.16.94-1.3.6 20060612 (`notes/vendor-toolchains.md`'s table 量 there, not re-run) | 推: GPL for gcc and binutils; their source is in none of the 3 drops (§ 2.1) | `SOURCES.json` `rtl819x-toolchain`, key `contains.toolchain_4181` | build-time; its `libgcc.a` and the uClibc it was configured with enter the image as L3 and L1 | 未定 `SBOM-4` |
| B2 | the loader image tools `lzma-26` and `cvimg`, in the stub's directory (`lzma-24` is also there and unused) | `lzma-26` is LZMA 4.06 (`notes/kernel-build.md` § 13); `cvimg` has none | not known for either. 讀 `file`: `lzma-26` and `lzma-24` are dynamically linked i386 ELF, `cvimg` a statically linked i386 ELF; no source for either is in the drop (the Makefile prefers a `cvimg` the drop does not contain) | `rtl819x-toolchain`, directory `linux-2.6.30/rtkload/`, binaries only | build-time, run under `tools/vendor-tripwire.sh`; only their output, the LZMA stream and its 8-byte prefix, enters the image | 未定 `SBOM-5` |
| B3 | the host build environment | 量 on this host, 2026-10-04: Ubuntu 24.04.4 LTS on WSL2 (kernel 6.6.87.2-microsoft-standard-WSL2), gcc 13.3.0, GNU Make 4.3, perl 5.38.2, Python 3.12.3, qemu-mips 8.2.2 (tests only) | each package's own; not examined | none: `SOURCES.json` has no entry and nothing pins them | build-time; none of it is in the image | 未定 `SBOM-6` |
| B4 | kernel host tools built from the staged tree: kconfig `conf`, `modpost`, `gen_init_cpio` (patched by `config/host-compat/0002`) | part of K1's tree, 2.6.30.9 | GPL-2.0, as K1 | `rtl819x-toolchain`, directory `linux-2.6.30/` | build-time; the cpio `gen_init_cpio` writes is the initramfs | resolved |
| B5 | `saturn49-wecb`, the second GPL drop | pin `40e21cb7c66880172910ae00c18663ed48e0123d` 讀 `SOURCES.json` | Realtek's SDK with the same layout; 量 GitHub `license` null; no bytes of it are in the image | `SOURCES.json` `saturn49-wecb` (role `reference`) | build-time check only: busybox's gate G1 compares the staged source with this drop's copy | resolved |
| B6 | the other pinned trees: `wecb-vz-gpl` (the third GPL drop) and the reference-only `openwrt-rtk`, `utessel-edimax`, `vankel-rtl819x-sdk`, `ggbruno-openwrt`, `shibajee-linux-rtl8196e`, `realtek-switch-hacking` | pins as in `SOURCES.json` | not examined: 讀 the kernel manifest and the busybox record both say `drop rtl819x-toolchain`, so no byte of these is in the image | `SOURCES.json` ids | read and cross-checked, never built from | resolved |
| X1 | `rlxboot`, the signed-update verifier payload | none declared | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the files themselves | repository `src/rlxboot/` | NOT in the image: a freestanding RAM payload staged separately (`R8a`); `src/Makefile` leaves it out of the image's programs 讀 | resolved |
| X1a | TweetNaCl 20140427, the retained ranges that became `ed25519` and `sha512` | 20140427 | public domain 讀 `SOURCES.json` (`licence`) and the file header | `SOURCES.json` `tweetnacl` (sha256 `02e65bc3`); generated into `src/lib/` by `src/rlxboot/test/mk-import.sh` | NOT in the image: 量 only `src/rlxboot/Makefile` names `ed25519` and `sha512`; no other Makefile does | resolved |
| X2 | `tools/rlxprobe`, the bare-metal probes | none | `MIT` by `LICENSE` and `NOTICE` § 4 (`LIC-01`); none stated in the files themselves | repository `tools/rlxprobe/` | NOT in the image: uploaded to RAM and run bare metal; three of its files are compiled into `uprobe` (U10) | resolved |
| E1 | the Realtek boot loader on the unit (bootcode 2014.04.22 v1.3) | 2014.04.22 v1.3 讀 `SOURCES.json` (the `wecb-vz-gpl` caveat) | not known | only a different bootcode generation is public: `SOURCES.json` `wecb-vz-gpl` | a runtime dependency, not shipped, not built here, not in the repository: it TFTP-loads `nfjrom` and jumps into it | 未定 `SBOM-7` |

## 8. Corresponding source, per component

推 throughout: this is the licence classes' usual requirement read against the table above, not legal advice.

| components | what a recipient would need | where it is today | how it is supplied |
|---|---|---|---|
| kernel and Realtek code (W1, K1 to K5), GPL-2.0 | complete corresponding source with the scripts that control compilation | the base drop at its pin (a third party's repository, § 2.4) plus this repository's K6, K7, `config/`, `tools/` | the corresponding-source archive, an asset of the same release as the binary (`docs/offer.md`, GPL-2.0 § 3(a)); owed by no release today — 量 2026-10-04: 5 releases, 0 assets. 🔄 2026-10-05: replaces the written offer `docs/offer.md` was until then |
| busybox (U8), GPL-2.0-only | the same, with the patch, the configuration and the build script | the base drop plus `config/busybox-patches/`, `config/rlxfw-busybox.config`, `tools/mkbusybox.sh` | the corresponding-source archive, an asset of the same release (`docs/offer.md`); owed by no release today — 量 2026-10-04: 5 releases, 0 assets |
| uClibc (L1, L2), LGPL-2.1 | the library source, and what lets a recipient relink | the source is in the drop (§ 2.1); the programs' sources and Makefiles are in this repository | the corresponding-source archive, an asset of the same release (`docs/offer.md`); owed by no release today — 量 2026-10-04: 5 releases, 0 assets |
| LZMA decoder (W2), LGPL or CPL | its source | in the drop | the corresponding-source archive, an asset of the same release (`docs/offer.md`); owed by no release today — 量 2026-10-04: 5 releases, 0 assets |
| `libgcc` (L3) | probably nothing, if the linking exception applies; not decidable here | no source anywhere | not applicable until `SBOM-4` is settled |
| iperf3, RC4, MD5, AES (U9, K3a to K3c) | the notices | the notices are in the sources (iperf3's only in `$FWRE_WORK`) | the licence texts, as assets of the same release as the binary (`docs/release-process.md`); owed by no release today |
| notices of every component above | each notice-bearing component's text beside the binary | 讀 the image carries none: 0 of 17 `file` rows is a licence text or an offer | assets of the same release as the binary, written beside the archive by `tools/srcarchive.py`, and members of the archive; the image carries none, by decision (`docs/release-process.md`); owed by no release today — 量 2026-10-04: 5 releases, 0 assets |

## 9. What is 未定, and what settles it

| id | open value | rows | what settles it |
|---|---|---|---|
| `SBOM-1` ✅ | the licence of rlxfw's own code | K6, K7, U1 to U7, U8b, U10 to U15, X1, X2 (18) | ~~the owner declares a licence: a `LICENSE` file and a per-file statement~~ ✅ 2026-10-04 (`01cff02b`): `LICENSE` (MIT), `NOTICE` §§ 1–4 by directory, and `config/rlxfw-src/LICENSE` for the kernel files — `GPL-2.0-only`, forced by provenance, and `MIT` for the rest. The value is `SPEC.md` `LIC-01`, which also says why no file carries a per-file tag: a first-line SPDX tag would rot 108 line citations that `citecheck` reads. The 18 rows read `resolved`; K7 and U8b are mixed files and their GPL-2.0 half is 推 (`NOTICE` § 3) |
| `SBOM-2` | the licence of sources in Realtek's directories whose headers carry no licence text: 35 compiled kernel sources (Appendix B; one of them, `spi_cmd`, carries a third party's copyright line) and 3 in the loader stub | W1, K2, K3, K4, K5 | not obtainable from this repository's measurements. Realtek's statement, or counsel's reading of the drop as a GPL release. 6 of the 35 also lack a C source anywhere (K4), which bears on what "source" is for them |
| `SBOM-3` | where iperf3's source is held | U9 | 🔄 2026-10-04, narrowed: the `SOURCES.json` entry **exists** (`01cff02b`), so what is left is the step that unpacks `refs/iperf-3.1.3.tar.gz` into a tree `build.sh` can point `SRC` at, and `tools/fetch-sources.sh` succeeding on a fresh clone — with a corrupted-sha256 fetch refused as the control that makes the success a reading. 🔄 2026-10-05: the entry is `fetch: now` and `tools/fetch-sources.sh --list` names it (量), so the fetch half needs only that run on a fresh clone; the unpack step is still unwritten |
| `SBOM-4` | the licence text and the corresponding source of `libgcc` and the compiler | L3, B1 | the RSDK gcc source, which no pinned tree holds; failing that, the FSF gcc 3.4.6 `libgcc2.c` header as the governing text, with the RSDK patch set still unknown |
| `SBOM-5` | the licence and source of `lzma-26` and `cvimg` | B2 | none needed unless the tools are redistributed: their output, not their code, is in the image |
| `SBOM-6` | the host environment is not pinned | B3 | recording package versions per build, or a pinned container; the versions here are for one host on one day |
| `SBOM-7` | the licence and provenance of the Realtek boot loader on the unit | E1 | not this project's to settle: the loader is neither shipped nor built here |

Residuals on rows that are otherwise resolved:

| id | residual | row | what settles it |
|---|---|---|---|
| `SBOM-R1` | the tree's `.c` files are unmodified since they built the archive | L1, L2 | recompile a sample under `tools/vendor-tripwire.sh` and compare the objects |
| `SBOM-R2` | whether the drop's `busybox-1.13` is pristine upstream 1.13.4 (`notes/busybox-build.md` § 9: G1 shows two Realtek drops agree, not that either is upstream) | U8 | diff against busybox.net's own 1.13.4 tarball |
| `SBOM-R3` | whether the SSLeay text of `1x_rc4` is compatible with a GPL-2.0-only kernel: its own text says it cannot be relicensed, the GPL included | K3a | counsel; or replacing the file, which is a design change through `config/rlxfw-marks.tsv` or `config/host-compat/` and not an SBOM edit |
| `SBOM-R4` | the header classifier cannot see a licence that only `COPYING` conveys: the kernel's `fork.c`, which carries no licence sentence, classes as "copyright only", and that was the classifier's own control before it was understood | K1 | none needed: the kernel's convention covers such files; the count states what the classifier saw |

## 10. How this was derived, what it swept, and what it could miss

**Derived** from the tree at `HEAD` `d4d0dbcc` and the records of cell `f184a` (§ 1), by one-off scripts run from a scratch directory. They are not committed; each count states its rule, and the rules are these.

- **The image.** Parse `config/rlxfw-initramfs.tsv` (skip `#` and blank lines, split on tab: kind, path, source, mode, owner) and `f184a.initramfs.manifest.tsv`; compare the `(kind, path)` sets both ways; hash the files at the declared paths and compare with the recorded sha256. Repeat on the git object at each tag for § 6. Control: a planted `unit` file row is counted as `unit`.
- **The kernel's population.** The `CC` and `AS` lines of `f184a.build.log`: 622. Excluded as not entering the image: 3 (`scripts/mod/empty.o` and the two generators `kernel/bounds.s` and `arch/rlx/kernel/asm-offsets.s`). 619 compiles of image objects, 618 distinct paths (`init/version.o` is compiled twice, before and after the build counter is bumped). Each object is mapped to its source in the staged tree of the cell (`.c`, then `.S`); 618 of 618 found. Files `#include`d into a compiled source (the WLAN driver's `data_*.c` tables) are inside their includer and are not counted separately.
- **The licence classifier**, used for the kernel (first 80 lines), busybox (203 `.o` with a `.c` beside them in its stage, first 60 lines) and uClibc (1,494 sources outside `test/`, first 60 lines): comment markers dropped and whitespace collapsed, then keyword patterns for GPL, BSD, MIT, public domain, LGPL and a copyright line; `MODULE_LICENSE` is looked for anywhere in the file. It classifies header text, nothing else. Controls: the `arch/rlx` `setup` file (its GPL sentence wraps over two comment lines) and the WLAN driver's `osdep` file class as GPL; a synthetic empty header classes as "nothing". Its first version classed the wrapped sentence as "copyright only" and was rewritten before any count here was taken.
- **uClibc correspondence.** Parse `libc.a` and `libm.a` as `ar` archives and hash each member without extracting; hash every `.o`, `.os` and `.oS` in the uClibc tree; compare. Controls in § 2.1.
- **Static linkage.** Parse each ELF's header and program headers; no program is run.
- **Archive code inside the ELFs.** For `libc.a` (906 members), `libm.a` (164) and both `libgcc.a` variants (103 each), take the `.text` of every member that has no relocation against it (94, 11 and 16), and search each ELF for those bytes. Controls as in § 2.1. For busybox, whose unstripped link survives, intersect the symbols that `libc.a`, `libm.a` and `libcrypt.a` define with the link's symbol names (control: invented names).
- **Firmware in the kernel.** Search the built `vmlinux` for byte windows parsed out of the four firmware arrays, with controls (§ 4, K3).
- **GitHub facts.** `gh api repos/<owner>/<repo>` and `gh release view`, on 2026-10-04.
- **Own-code census.** `git ls-files` at `HEAD`, whole-file reads, with the population stated in § 2.3.

**What it swept:** the 55 declared rows; 618 kernel sources; 203 busybox sources; 1,494 uClibc sources; 11 ELF headers and bodies; 906, 164 and 103 archive members; the tracked files of this repository.

**What it could miss.**
- A licence stated outside the first 60 or 80 lines of a header, or in a separate file; a directory-level notice other than the stub's `COPYING`.
- Third-party code inside the generic kernel (zlib's inflate, the LZMA decompressor, crypto tables, netfilter pieces) beyond what a header keyword shows; it is counted, not itemised.
- Which `libc`, `libm` and `libgcc` members each ELF pulled in beyond the relocation-free probes. The shipped files are stripped and no link map is recorded for the six programs, so the probe counts are a lower bound per file.
- The `OUTSRC` and `data_*.c` pieces that are `#include`d: their own headers were not read.
- Anything that reaches the image outside the manifest's 17 file rows and the compiled objects. The cpio is built from the manifest alone, so this should be nothing, and nothing was found.
- Anything that changed after `HEAD` `d4d0dbcc` or after cell `f184a`.

## 11. What this does not establish

- **It is not a legal opinion.** The classifier reads header text; the readings in § 8 and § 2.4 are marked 推 and need counsel before they are acted on.
- **It is not the corresponding source, and it discharges nothing.** No binary has been distributed (§ 1). When one is, the release carries the corresponding-source archive and the licence texts as assets beside it (§ 8, `docs/offer.md`); the image itself carries no notice.
- **It does not establish that the image the device ran is the image described.** The digests are copied from build records; the bytes the loader received were not re-read. For 16 of 17 files the record equals the working tree; the 17th is explained (§ 3); `RECIPE_ID` cannot see the binaries under `build/` (`notes/iperf3-port.md` § 8), so a captured `RLXFW-ID0` does not pin the userspace.
- **It does not establish that the build reproduces on a clean clone.** `build/` is untracked, the iperf3 source is outside the repository, and `P4a`'s Level 2 residual stands (`notes/reproducible-build.md` § 6).
- **It covers one variant.** `loud` and `quiet-swcore` are other kernels; `quiet-swcore` adds the vendor Ethernet tree, whose licences were not surveyed.
- **It says nothing about the WLAN radio's firmware.** None of the four MCU firmware arrays is in the image; whether the 88E path needs a firmware this image does not hold was not read.
- **It does not examine patents, export classification or the vendor's own firmware obligations.** The image contains RC4, AES, MD5 and SHA-256 code, and TOTOLINK's firmware is not in it.
- **It does not say who wrote rlxfw's code, or who holds its copyright.** "Own" is provenance.
- **It does not say the static link pulled in no code under a licence other than those listed.** The tree-level licence census of uClibc is an upper bound, not a list of what was linked, and the byte search is a lower bound.

## Appendix A. The 17 `file` rows of cell `f184a`

量 from `f184a.initramfs.manifest.tsv`; the owner of every row is `rlxfw`.

| path | bytes | sha256 | component |
|---|---:|---|---|
| `/init` | 75,128 | `77571ca36ccafc0341c63011d942674833b96729a314d2758cbfa982d9777cc2` | U1 |
| `/bin/uprobe` | 29,184 | `f3bf56ee6d97712e55307d57f5e005ea3588a1aa14b3671a6f85c5502203cebb` | U10 |
| `/bin/ucost` | 16,692 | `76c7e2318021484967ccc0e8c5a2eadd992c5bee372a2a7bcd10d0a1ebe3c6db` | U11 |
| `/bin/mfgtest` | 32,620 | `d954de730d5cdadb137632d44c30974bcac4d97a79d7d414480421c4dabc1588` | U13 |
| `/bin/busybox` | 447,684 | `ef057f6ee7a4ead58d8b2028dbaaf0899b65d9c8ad41ec8e8e7c143f567fec60` | U8 |
| `/bin/iperf3` | 252,644 | `3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8` | U9 |
| `/bin/linkprobe` | 16,240 | `071c8f81a47cc8ed84ad9d6ddce8a7e5b4db45ca1ba35fd457a1d9f47bd3d723` | U12 |
| `/sbin/ifupd` | 23,164 | `9bd95a79f7c3ac500644cbb27f0e7708fd39dcf12bc92194daa1ce20561d3346` | U2 |
| `/usr/sbin/brokerd` | 101,212 | `263aad52585a970b4f7dad6401ab4efe60043061ed3cc7185fd0ca7c5bcb77cb` | U3 |
| `/usr/sbin/httpd` | 83,836 | `d301a049a3e498a35496ed273cf555c2c84f58d40910195b4d3ef9e5259b5d90` | U4 |
| `/usr/sbin/dnsfwd` | 73,908 | `ced6956e941e3aabf1909b4287126e5c228cfe08eb5f3be127e265366bff9365` | U5 |
| `/usr/sbin/cfgstore` | 86,320 | `abc6b5f75c73cde92a12418d4b43d299b3271b0136c4a1a433e23842e99d6928` | U6 |
| `/srv/www/index.html` | 3,850 | `f7afe413de1c8b3ff02733c2cb4eb208436fce1392abcc4ab2afdab27a9a9832` | U14 |
| `/srv/www/static/style.css` | 3,430 | `730ef34fd5d653966e0fdd3f0516dd6454c71e5c01fe0a04e43a23b594507999` | U14 |
| `/srv/www/static/app.js` | 12,488 | `5907e45d6d2771102c51b25e1cc7ffaf8de7a99dfbab69098c65672c5940e6d8` | U14 |
| `/etc/passwd` | 101 | `dcb10945dae12445965cb6027e00be023e01928d92758d2fced76a9128a42d79` | U15 |
| `/etc/group` | 37 | `abe982457adea0cdfeb1f003b31c7022f8898e9d7110ae76f8c1418be3573057` | U15 |

## Appendix B. Realtek-directory compiled sources with no licence text in their headers

量 over the 117 compiled sources in `arch/rlx`, `net/rtl`, `drivers/net/wireless/rtl8192cd`, and the vendor flash, SPI and GPIO files (the 12 of rlxfw's own are counted apart, K6). 37 carry no licence text. Two of the 37, `1x_md5c` and `1x_kmsm_aes`, carry a third party's permission notice that the classifier does not recognise as a licence (K3b, K3c), so 35 carry none of any kind. Names are relative to each directory, without extension.

| directory | n | copyright line only | nothing |
|---|---:|---|---|
| `arch/rlx` | 20 | `bsp/prom`, `bsp/setup`, `bsp/serial`, `kernel/rlx-switch`, `kernel/proc`, `mm/tlb-rlx`, `lib/iomap`, `lib/rlx_dump_tlb` | `bsp/irq`, `kernel/topology`, `mm/extable`, `kernel/irq_vec`, `kernel/init_task`, `mm/cache-rlx`, `mm/imem-dmem`, `lib/ashldi3`, `lib/ashrdi3`, `lib/cmpdi2`, `lib/lshrdi3`, `lib/ucmpdi2` |
| `drivers/net/wireless/rtl8192cd` | 7 | `HalPwrSeqCmd`, `Hal8188EPwrSeq`, `OUTSRC/rtl8188e/Hal8188ERateAdaptive`, `1x_kmsm_aes`, `1x_md5c` | `8192d_hw`, `HalDMOutSrc` |
| `net/rtl` | 9 | none | `fastpath/96E/fastpath_core`, `fastpath/96E/filter`, `fastpath/96E/fast_pptp_core`, `fastpath/96E/fast_l2tp_core`, `fastpath/96E/filter_v2`, `fastpath/96E/fast_pppoe_core` (six assembler files), `features/rtl_features`, `features/rtl_ps_hooks`, `features/96E/rtl_nf_connGC` |
| `drivers/mtd/chips/rtl819x` | 1 | `spi_cmd` | none |

Two more compiled Realtek-directory sources carry `MODULE_LICENSE("GPL")` and no header text: `fastpath_common` and the flash map `rtl819x_flash`. One carries a third party's licence in full: `1x_rc4` (K3a).
