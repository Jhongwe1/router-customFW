# Self-update and anti-rollback from the running firmware: the design (`P6r-10`, `P6r-11`)

The design `P6r-10` and `P6r-11` are built to, written at the desk on 2026-10-23 before any of it
exists: nothing here was built, run on the device or measured for this note, and no flash was read
or written. Marks: **量** measured on the device, with its capture or `SPEC.md` row; **讀** read
from code, a dump or an artefact, with `file:line`; **推** inferred, with what would settle it. A
number with no mark and no source is not in this file; estimates are labelled guesses. Line
numbers are at `948ff614`. Vendor files are cited under `src-vendor/rtl819x-toolchain/`, the drop
at its pin; paths under `$FWRE_WORK` are named where they are used. Once the code lands, the code
and its host tests own what it does, and this note keeps the reasons. 🔄 2026-10-23: §§ 1–2 landed
in `948ff614` (phase 1: the handoff and the install path, built at the desk, run on no die); where
the code differs from the design, the section says so in a dated note, and §§ 3–5 are still design.

The DoD designed to is `PROGRESS.md` rows `P6r-10` and `P6r-11`, amended in `25268298` before
any work where this design showed the first text unmeetable (§ 0.2). The rulings it follows were
made on the owner's delegation of 2026-10-23 and are recorded in `LOG.md`'s entry for the 142nd
segment: `MK5` retired for a `sym:` witness (§ 2.9); writes whose bytes are
unknown before power authorised by category (§ 0.2, § 6.3); the shipped image without the console
shell (§ 3.8); no card publishes the working admin password (§ 6.4).

## 0. The design on one page

### 0.1 The pieces

| piece | files | what it does | § |
|---|---|---|---|
| handoff, loader | `src/rlxboot/jump.S`, `main.c`, `rlxboot.h`, new `handoff.h` | `rlxboot` leaves magic, slot, version and a check word in a0–a3 at the jump | 1.2 |
| handoff, decompressor | new `config/host-compat/0011-rtkload-boot-handoff.patch`; `tools/rtkimage.py:789`, `:814` | `rtkload` saves a0–a3 at entry and reloads them in `start_kernel` | 1.3 |
| handoff, kernel | new `kernel/linux-2.6.30/arch/rlx/kernel/rlxfw-boot.c`, `include/linux/rlxfw-handoff.h`, one marks row | `/proc/rlxfw-boot` reads `slot B ver 6` or `none` | 1.4 |
| install path | `rtl819x-spi-install.h`, `rtl819x-spi.c`, `config/rlxfw-kernel.delta`, `MK5` | in the shipped image; regions `cfg0`/`cfg1`; verbs `ctr`, `ctrloop`, `erase cfgN`, `repeat=`; a running-slot fence | 2 |
| store | `src/lib/cfg.c`, new `src/lib/cfgflash.c`, `cfg.h`; `cfgstore`, `brokerd`, `init` paths | reads through `/dev/mtd2ro`, writes one slot through stage → arm → `install cfgN` | 3 |
| update | `src/httpd/http.c`, `serve.c`, `routes.c`, new `upload.c`; `src/brokerd/ops.c`, new `update.c`, `Makefile` | a streaming `POST /api/firmware` → `UPDATE_BEGIN/DATA/END`; `rlxboot`'s own `container.c` decides | 4 |
| counter advance | `src/init/main.c` (+ `client.c`, `proto.c` linked in) | a helper PID 1 forks after `lan up` and one `brokerd` round trip writes `ctr <ver>` | 5 |

### 0.2 Where the DoD was amended (`25268298`), and why

1. **Naming each write.** The first text named every payload written by its digest. 讀 a record
   carrying a fresh salt cannot be named that way: `cfgstore passwd` draws the salt on the device
   (`src/cfgstore/main.c:619-620`, `pwhash_salt`) and `brokerd`'s `PWSET` does too
   (`src/brokerd/ops.c:571`), so the 4,096 bytes such a write stages cannot be known before the
   write; and the install path never prints the staged digest, by design
   (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2217-2220`). Amended: a container or an
   `rlxboot` payload is named by its exact sha256 as before; a salted store record and the
   firmware's counter advance are named by region, operation, bound (the `seq` or the target
   value) and the issuing image's sha256. An unsalted record — `cfgstore init --force`, and a `set`
   on a store holding no password hash — is deterministic and can still be named by digest
   (§ 6.3); 讀 a `set` on a store that holds `admin.pwhash` writes a record carrying that hash and
   its salt, since `cmd_set` loads the whole record (`src/cfgstore/main.c:286`), changes one key
   (`:333`) and stores the whole record again (`:339`; § 3.2).
2. **The counter after a cut.** The first text asked for the old value or the new one. That holds
   for an advance by one step and cannot hold for an advance by more than one under a cut,
   whatever the program order (§ 2.4.4); the round's first advance is 0 → 6. Amended: *"a value
   from the old one to the new one, never below the old nor above the new — each page program
   clears one bit"*. "Never below the old" holds after any cut. "Never above the new" holds only
   if no program clears a bit it was not asked to: a stray clear at a position at or above the new
   value reads one more than the new, malformed (§ 2.4.4), and the host suite carries that case
   (§ 2.8, groups H and I).
3. **Where the cut rounds run.** The first text looped a write too short to aim a hand-timed cut at
   on a scratch region. For the slot write there is none of a slot's size: 讀 the free area below
   the store, `0x2B0000`–`0x3BFFFF`, is 1,114,112 B, under a slot's 1,179,648
   (`src/rlxboot/rlxboot.h:74-78`). For the store write, a scratch-region loop would leave the
   store's own pass criterion vacuous, since no real store write is cut. Amended: the unpaced slot
   write repeated on the slot `rlxboot` did not boot, the store write repeated on the store's own
   regions, the counter's program loop run on the erase probe's block (§ 6.5 says why each is
   safe).
4. **"Both invalid".** 讀 `cfgstore show` loads strictly (`src/cfgstore/main.c:203`), and a store
   that holds bytes but no valid record exits 4 before printing anything
   (`src/cfgstore/main.c:105-114`). Amended to *both erased*: an erased slot reads as absent
   (§ 3.1), so with both regions erased `show` prints `source default` (§ 3.6, option A).
5. **The bootstrap.** T, `v1.0`'s image in slot A, has no update path (§ 6.1). Amended: the
   round's first slot write is made from the console of an image booted from RAM, and the update
   path is shown on the image it installed.
6. **The password.** Every `--send` lands in a committed `.meta.json` (§ 6.4). Amended: the
   password a card sets is disposable, declared public on that card and destroyed in the same
   seating by erasing both store regions; the unit's working password is set off-card.

## 1. The handoff: `rlxboot` → `rtkload` → the kernel

### 1.1 What kills a register handoff today

- 讀 `rlxboot` zeroes a0–a3 at the jump: `src/rlxboot/jump.S:57-62` moves the entry to t0, zeroes
  a0, a1, a2 and fills `jr`'s delay slot with `a3 = 0`. Until `948ff614` the file had one commit,
  `457b2314` (`git log -- src/rlxboot/jump.S`), so build `127a71cf` at `0x010000` and `0x020000`
  does the same (`LOG.md:945`, `:971`; `notes/rlxboot.md:746-748`). 🔄 2026-10-23: that entry,
  `rlxboot_jump`, is what `BOOT=ram` still takes; a slot boot takes `rlxboot_jump_handoff` (§ 1.2).
- 讀 `rlxboot` does not enter the kernel: it enters `rtkload`, the decompressor at the head of the
  image, at `0x80500000` (`notes/update-chain.md:490-493`, `FW-23`).
- 讀 `rtkload` as built clobbers a0 before `main()` and zeroes a0–a2 before the kernel. In the
  drop at its pin `5c9be5d9` (`git status` clean under `linux-2.6.30/rtkload/`):
  `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/start.S:38-47` is `#if 0`, and `:49-104`
  is `CONFIG_RTL_EB8186`'s; the code that runs is `:26` (`nop`), `:33-36` (`Status = 0`),
  `:124-132` (the `.bss` clear with s0, s1, t0), `:141-144` (`move a0, t0` — the stack top
  becomes `main`'s argument), `:148` (`j main`); then C code
  (`src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/hfload.c:77-117`) that uses a0–a3 freely;
  then `start_kernel` at `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/start.S:156-163`:
  `move t0,a0; li a0,0; li a1,0; li a2,0; jr t0; nop`, called as `start_kernel(kernelStartAddr)`
  at `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/hfload.c:115`. a3 is never zeroed: it
  holds whatever the C code left.
- 讀 the shipped artefact agrees, byte for byte. `v1.0`'s `nfjrom`
  (`$FWRE_WORK/rebuild/s132/p5e1/art/p5e1-preB/nfjrom`, 1,110,016 B, sha256 `295d4f6a…86bd`, the
  release image's digest, `docs/known-issues/v1.0.md:9`) disassembled at `0x80500000` by the
  host's `mips-linux-gnu-objdump`: `0x80500000` `nop`; `0x80500004`–`08`
  `move s0,zero; mtc0 s0,c0_sr`; `0x80500018`–`38` the `.bss` loop over `0x8060F000`–`0x80617858`;
  `0x80500048` `move a0,t0`; `0x8050004C` `j 0x80500200`; `0x80500064`–`7C`
  `move t0,a0; li a0,0; li a1,0; li a2,0; jr t0; nop; nop`. No instruction of the `#if 0` block is
  there. `SPEC.md` `FW-261` indexes this and § 1.4. 🔄 2026-10-23 (1C): seven words, not the six
  this listed until then: the reorder-mode assembler fills `jr`'s delay slot with a `nop` of its
  own and the source's `nop` follows it at `0x8050007C`; 讀 again the same day with the host
  `objdump`, the next word, `0x80500080`, is `lui t1,0xbd01`.

### 1.2 The `rlxboot` side

**`src/rlxboot/handoff.h`** (new, asm-safe: `#define`s only, a `BUILD_ID` input):

```c
#define RLXB_HANDOFF_MAGIC   0x524C5848     /* "RLXH"                        */
#define RLXB_HANDOFF_SLOT_A  0x41           /* 'A', what RLXBOOT-SLOT prints */
#define RLXB_HANDOFF_SLOT_B  0x42
/* C only: the check word.  Not cryptographic -- see 1.6. */
#define RLXB_HANDOFF_CHECK(slot, ver) \
	((~(RLXB_HANDOFF_MAGIC ^ (unsigned long)(slot) ^ (unsigned long)(ver))) & 0xFFFFFFFFUL)
```

**`src/rlxboot/jump.S`**, a second entry beside `rlxboot_jump` (which stays, unchanged, for
`BOOT=ram`). Every instruction written by hand under the file's existing
`.set noreorder`/`noat`/`nomacro` (`src/rlxboot/jump.S:23-25`); no load, so nothing for
`tools/hazlint`. The new entry sits under `#if RLXBOOT_SLOTS`, and `ASFLAGS` gains `$(BOOT_DEF)`:
讀 until `948ff614` it carried no `RLXBOOT_SLOTS` (`CFLAGS` does, `src/rlxboot/Makefile:107`);
🔄 2026-10-23 it does (`:113-114`, the reason at `:108-112`), and `jump.S` refuses an undefined
`RLXBOOT_SLOTS` with an `#error` (`src/rlxboot/jump.S:19-21`). Without the change the RAM build
would assemble the magic too and the census row below would read it there:

```asm
#include "handoff.h"
/* void rlxboot_jump_handoff(u32 entry, u32 slot, u32 version, u32 check)
 * o32: a0 = entry, a1 = slot, a2 = version, a3 = check.  a1..a3 are left
 * exactly where the C caller put them; a0 is replaced by the magic. */
	.globl	rlxboot_jump_handoff
	.ent	rlxboot_jump_handoff
	.type	rlxboot_jump_handoff, @function
rlxboot_jump_handoff:
	addu	$8, $4, $0				/* t0 = entry, out of a0, FIRST */
	lui	$4, (RLXB_HANDOFF_MAGIC >> 16)		/* a0 = magic, high half      */
	jr	$8
	ori	$4, $4, (RLXB_HANDOFF_MAGIC & 0xFFFF)	/* delay slot: low half      */
	.end	rlxboot_jump_handoff
```

讀 the encodings, assembled alone by the host's binutils at `-march=r3000` with the magic restated
in the snippet, not included from `handoff.h` (desk only,
`$FWRE_WORK/rebuild/s142/design/check/jump-handoff.S`): `00804021 3c04524c 01000008 34845848`.
a0 reaches `rtkload` holding a kuseg value either way, 0 before and the magic now, so what
`src/rlxboot/jump.S:41-44` says about a fault dereferencing a0 is unchanged. 🔄 2026-10-23 (1C):
the vendor's assembler emits the same four words in the linked slots image, by the vendor
`objdump`, and the payload gate now reads them back from it (`src/rlxboot/Makefile:343-362`).

**`src/rlxboot/main.c`**: `boot_verified()` (`src/rlxboot/main.c:242-296`) gains a `slot`
argument. The slots build passes `win->name` (`src/rlxboot/main.c:438-439`; `'A'` or `'B'`,
`src/rlxboot/slots.h:29`); the RAM build passes 0. Before the UART drain
(`src/rlxboot/main.c:280-286`) a slot boot prints one more line (`:263-274`), so the capture says
what was handed over:

```
RLXBOOT-BOOT load=80500000 entry=80500000
RLXBOOT-HANDOFF slot=B ver=6
```

and jumps with `rlxboot_jump_handoff(r->entry_addr, slot, r->version,
RLXB_HANDOFF_CHECK(slot, r->version))`; slot 0 keeps `rlxboot_jump(r->entry_addr)`. The payload
gate (`src/rlxboot/Makefile:315-342`) gains one census row: the slots image must form
`0x524C5848`, the RAM image must not — each the other's control, the pattern `D28` already uses.
讀 the census can see it: `src/rlxboot/test/flashscan.py:14-16` rebuilds a `lui` followed by an
`ori` into the combined value. 🔄 2026-10-23 (1C), beyond the design: the gate also pins the four
words at `rlxboot_jump_handoff` in the linked image (`src/rlxboot/Makefile:343-362`), and `main.c`
does not compile unless `'A'`/`'B'` equal `RLXB_HANDOFF_SLOT_A`/`_B` (`src/rlxboot/main.c:330-334`).

**What moves.** `BUILD_ID` hashes every source in `MY_C`, `MY_S` and `MY_HDR`
(`src/rlxboot/Makefile:190-195`), so `handoff.h` joins `MY_HDR` (`:182`) or the id would not cover
it; with it the new `rlxboot` has a new id. `hazlint`, `flashsafe` and the no-signer gate run on it
as on every build (`src/rlxboot/Makefile:264-272`, `:308-314`, `:509-510`). The rescue copy at
`0x020000` stays build `127a71cf` (§ 1.7). 🔄 2026-10-23 (1C, at its tree): the production slots
id went `8ddddcfc` → `3b7474de`, and `make rescue` now makes `3b7474de` images; `8ddddcfc` already
differed from the flashed `127a71cf`, through the comment-only commit `e9f0ff27`.

### 1.3 The `rtkload` side

**Vehicle.** Vendor code changes only through `config/rlxfw-marks.tsv` or `config/host-compat/`
(`CLAUDE.md` § Never). 讀 the marks vocabulary is closed at mark calls, `obj-y` lines (plain or
conditional) and one exact include (`tools/rlxfw-marks.py:115-137`), so assembly needs a patch:
`config/host-compat/0011-rtkload-boot-handoff.patch`, the next free number (`0001`–`0010` existed;
🔄 2026-10-23 `0001`–`0011` do). 讀 `tools/rlxfw-kbuild.sh` stages the whole `linux-2.6.30/`
(`tools/rlxfw-kbuild.sh:539`) and applies every patch with `patch -p1 --forward` inside it
(`:568-576`; 🔄 since `948ff614` with `--fuzz=0`, so a hunk whose context drifted is refused, not
applied nearby: all eleven apply that way), so a patch to `rtkload/start.S` reaches the **cell's** copy.

🔴 **And the cell's copy was not what built the image.** 讀 until `948ff614` `tools/rtkimage.py`
copied `rtkload` from the pristine drop (`shutil.copytree(os.path.join(DROP, 'linux-2.6.30/rtkload'),
rtk)`, then its line 621); only `include/`, `arch/` and `lib/` are linked from the cell
(`tools/rtkimage.py:802-803`). The patch would have shown as applied in the tree and been absent from
the `nfjrom` (`SPEC.md` `FW-262`). 🔄 2026-10-23: `rtkimage` 1.1 copies the cell's `rtkload/`
(`tools/rtkimage.py:789`, `:814`), which `cp -a` already holds (`tools/rlxfw-kbuild.sh:539`), and
records it as `rtkload_source`; 量 the first build's record names the cell's copy (`FW-264`).

**The patch.** 讀 the hunks below are `diff -u` output, made by
`$FWRE_WORK/rebuild/s142/design/check/mkpatch.py` from a copy of the pinned `start.S` (sha256
`58cb9a79…de46`; it refuses any other file and any anchor that does not occur exactly once).
Regenerated on 2026-10-23 in a fresh directory, the hunks were identical and only the two header
timestamps differed; applied with `patch -p1 --forward` to a fresh copy of the pinned file they
give sha256 `3661a64a…74b4`, the intended file, and a second apply is refused (*Reversed (or
previously applied) patch detected*). The header text above the hunks, in the style of `0010`,
is written with the patch.

```diff
--- a/rtkload/start.S
+++ b/rtkload/start.S
@@ -18,9 +18,39 @@
         
 	.extern __start_dram
  
+/* rlxfw (config/host-compat/0011): the boot handoff, P6r-10.
+ * rlxboot (src/rlxboot/jump.S) enters here with a0..a3 = magic, slot,
+ * version, check.  They are saved at entry -- before `move a0, t0`
+ * below puts the stack top in a0 and before main() uses a0..a3 at all --
+ * and loaded back into a0..a3 by start_kernel, which used to zero
+ * a0..a2.  One 16-byte D-cache line of its own (cache.c: 4 words), in
+ * .data and not .bss, because the loop at _bstart below clears .bss.
+ * Written and read only through the KSEG1 alias, so no cache state
+ * decides what start_kernel reads. */
+	.data
+	.align	4
+	.globl	rlxfw_rtk_handoff
+	.type	rlxfw_rtk_handoff, @object
+	.size	rlxfw_rtk_handoff, 16
+rlxfw_rtk_handoff:
+	.word	0, 0, 0, 0
+	.ascii	"RLXFW-RTKH1"
+
         .text
         .globl __start              
 __start:
+	.set	noreorder		/* rlxfw: no branch, no load: no slot */
+	.set	nomacro
+	lui	$8, %hi(rlxfw_rtk_handoff)
+	addiu	$8, $8, %lo(rlxfw_rtk_handoff)
+	lui	$9, 0x2000
+	or	$8, $8, $9		/* KSEG0 -> KSEG1: uncached */
+	sw	$4, 0($8)		/* a0: magic */
+	sw	$5, 4($8)		/* a1: slot */
+	sw	$6, 8($8)		/* a2: version */
+	sw	$7, 12($8)		/* a3: check */
+	.set	macro
+	.set	reorder
 		 
 #ifdef CONFIG_DONOT_ADJUST_SYSCLK_MEMSP
 		nop
@@ -155,12 +185,21 @@
 
         .globl start_kernel
 start_kernel:
-        move t0, a0
-        li a0, 0
-        li a1, 0
-        li a2, 0
-		jr t0
-       	nop 
+	.set	noreorder		/* rlxfw: every slot below is filled by hand */
+	.set	nomacro
+	addu	$8, $4, $0		/* t0 = the kernel entry, out of a0 FIRST */
+	lui	$9, %hi(rlxfw_rtk_handoff)
+	addiu	$9, $9, %lo(rlxfw_rtk_handoff)
+	lui	$10, 0x2000
+	or	$9, $9, $10		/* KSEG0 -> KSEG1: uncached */
+	lw	$4, 0($9)		/* next: lw, reads $9 not $4 */
+	lw	$5, 4($9)		/* next: lw, reads $9 not $5 */
+	lw	$6, 8($9)		/* next: lw, reads $9 not $6 */
+	lw	$7, 12($9)		/* next: jr, reads $8 not $7 */
+	jr	$8
+	nop				/* delay slot: nothing */
+	.set	macro
+	.set	reorder
 
 
 hfclock_setting:
```

The context lines carry the drop's own whitespace (spaces, tabs, trailing blanks); the diff was
generated, not typed, so applying it is the check.

**Delay slots and hazards, every one.** The entry block has no branch and no load. In
`start_kernel` the only branch is `jr $8`, whose slot holds `nop`; each `lw` is followed by an
instruction that does not read its target (`lw`, `lw`, `lw`, `jr $8`), and the kernel's first
instruction is two instructions after the last load. 讀 `tools/hazlint`, run with its own controls
(its population controls against this unit's `stage2.bin` and the vendor kernel both held), on the
snippets assembled alone by the host `as` at `-march=r3000`: **0 violations in 4 loads**; the same
run on a planted `lw a3,…; jr a3` reports **1** (the control). On the whole patched `start.S`,
preprocessed by the host `gcc -E` against a configured cell's headers (`r3-4/cells/rlxfw`) and
assembled by the host `as` at `-march=r3000`: it assembles, and `hazlint` reads 0 violations in 9
loads (the pinned file: 0 in 5). ⚠️ That object is the host assembler's, not the vendor's: the host
`as` scheduled the vendor's reorder-mode `move a0,t0` into `j main`'s slot where the drop's
2.16-era `as` left `nop` (compare `0x80500048`–`50` above). Only the artefact the vendor toolchain
makes counts, and § 1.3's gate reads it. 🔄 2026-10-23 (1C), vendor-built: `hazlint` reads the
patched `start.o` 0 violations in 9 loads and its linked `memload-full` 0 in 277 (the pristine
stub: 0 in 5, 0 in 273), and a planted `lw a3; jr a3`, vendor-built, 1.

**Why `.set reorder` and `macro` are restored, not pushed.** 讀 `start.S` holds no `.set`
directive (`grep -c '\.set'` reads 0; the same grep finds its 4 `.globl` lines), so the file runs
in gas's default reorder/macro mode and the vendor's own lines rely on it — `beq t0, VERSION_D, …`
is a macro (`src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/start.S:174`; in `v1.0`'s `nfjrom`,
`li at,4` at `0x80500098` and the `beq` at `0x8050009C`). Restoring the defaults leaves them as
they were.

**Placement.** 讀 `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/ld.script:21-41`: `.text` at
`0x80500000`, then `.rodata`, then `.data` = `_fdata`, `*(.data)`, `ALIGN(1024)`, the compressed
kernel, `ALIGN(1024)` (`:33`, `:37`), then `.bss` (`_bstart`, `_bend`). The array lands in
`.data` ahead of the compressed kernel, so the decompressor's output (`0x80000000`–`0x803F0000`,
`$FWRE_WORK/rebuild/s132/p5e1/art/p5e1-preB/rtkimage-p5e1-preB.log`: `decompress end 0x803f0000`)
and its heap (from the stack top up, `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/hfload.c:103`,
above `.bss`) never reach it. 讀 `start.o` is first in the link
(`$(START_FILE) $(LOADER_FILES) …`, `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/Makefile:223`),
so `__start` stays at `0x80500000` and, 推, the array at `_fdata`; the gate below reads both.
🔄 2026-10-23: 量 on the first build it read both: `rlxfw_rtk_handoff` at `0x805028A0`, which is
`_fdata`, and `__start` at `0x80500000` (`SPEC.md` `FW-264`).

**The artefact gate** (what `rlxfw-marks verify` cannot do: it reads the kernel ELF and
`System.map`, `tools/rlxfw-marks.py:25-34`, `:75-80`, and `rtkload` is in neither).
`tools/rtkimage.py`'s `build`, after `make` and before writing its record, refuses unless:

| check | the built image | the control, read the same way |
|---|---|---|
| `memload-full`'s `.symtab` has `rlxfw_rtk_handoff`, 16 bytes, 16-aligned, at or above `_fdata` and below `__vmlinux_start` — all three from the same table (`elf_symbols`, `tools/rtkimage.py:273-298`, which gives values and sizes, not sections) | present | the drop's `rtkload/memload-full` (`CTL_MEMLOAD`, `:141`): absent |
| `__start` = `0x80500000` | equal | — |
| the five words `00804021 24040000 24050000 24060000 01000008` in the first 16 KiB of `nfjrom` | 0 | the drop's `image/nfjrom` (`CTL_NFJROM`): 1 |
| the bytes `RLXFW-RTKH1` in `nfjrom` | exactly 1 | the drop's: 0 |

讀 desk counts with `$FWRE_WORK/rebuild/s142/design/check/zeroseq.py` (bytes only, nothing run),
re-run 2026-10-23: `v1.0`'s `nfjrom` zero sequence 1, witness 0; the drop's `image/nfjrom` and
`rtkload/nfjrom` (two copies of one file, 854,016 B, sha256 `5cc8d61d…`) zero sequence 1, witness
0 — so the control fires on both reference images today; a 31-byte file built to hold the sequence
and the witness once each reads 1 and 1, so the counter can see both. 🔄 2026-10-23 (1C, desk):
the gate as built passes a stub made with `0011` around `v1.0`'s `vmlinux` and refuses the pristine
stub on three conditions, whose `nfjrom` is `v1.0`'s `295d4f6a…` byte for byte; a refused `build`
writes no record, so `R3-2`'s positive control can no longer pass `build` (an inverted-gate mode
would restore it; not built).

**Cost.** 讀 12 more instructions (48 B: 8 at entry, 11 in place of `start_kernel`'s 7 words, § 1.1;
🔄 2026-10-23, 1C: this read 13 and 52 B, from the 6 source lines) and 27 B
of `.data` plus its 16-byte alignment; the image grows in 1,024-byte steps
(`src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/ld.script:33`, `:37`), so 推 this costs 0 or
1,024 B of image depending on where `.data` ends. 🔄 2026-10-23: 量 0 for `v1.0`'s kernel, whose
`nfjrom` built with `0011` keeps 1,110,016 B (1C); 讀 in the first build's `nfjrom` `start_kernel`
is at `0x80500084`, not `0x80500064`, and the next vendor word moved 48 B (`0x80500080` → `0x805000B0`).

### 1.4 The kernel side

讀 the kernel saves the four registers before anything else uses them:
`src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/kernel/head.S:121-144` — `kernel_entry`,
`kernel_entry_setup` (empty: `src-vendor/rtl819x-toolchain/boards/rtl8196e/bsp/bspinit.h:12-13`,
reached through `head.S`'s `#include <bspinit.h>` at `:29`, `arch/rlx/bsp` being a link to
`target/bsp` and `target` to `boards/rtl8196e` in the drop and in a cell), `setup_c0_status_pri`
(t0 only, `:76-89`), `jr t0` to the link address, the `.bss` clear with t0 and t1 (`:133-139`),
then `LONG_S a0..a3, fw_arg0..fw_arg3` (`:141-144`). The stores come after the clear, and
`fw_arg0..3` are ordinary globals
(`src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/kernel/setup.c:564`; in the `System.map` of
the build that reproduces `v1.0`'s image, `$FWRE_WORK/rebuild/s132/p5e1/art/p5e1-preB/`, `B`
symbols at `0x803F0524`–`0x803F0530`, inside `__bss_start` `0x803F0000` … `__bss_stop`
`0x8053F040`).

讀 **nothing in the vendor's built kernel reads them** (🔄 2026-10-23: rlxfw's `rlxfw-boot.c`, below,
does since `948ff614`, by design, and is their one reader). Over the drop's whole `linux-2.6.30/` and
`boards/rtl8196e/`, the only readers of `fw_arg0..3` outside `arch/mips/` (another architecture,
never built here) are `src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/fw/arc/init.c:30-32`
and `src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/fw/sni/sniprom.c:139-140`, and
no Makefile builds `arch/rlx/fw/`
(`src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/Makefile:114-117`: `core-y` is `kernel/` and
`mm/`, and `#libs-y += arch/rlx/fw/lib/`); the board's BSP has none. The same `System.map` holds no
`prom_argc`, `_prom_argv`, `_prom_envp` or `prom_init`, and the grep that found none found the
four `fw_arg` symbols. So non-zero a0–a3 at kernel entry change nothing the kernel did before;
⚠️ that is a reading of the vendor tree, and what keeps it true is a `System.map` absence check
for `prom_argc` and `_prom_argv` — the kind of reading `rlxfw-marks verify` makes, though its
pairing rule ties `absent:` to conditional Kbuild rows (`tools/rlxfw-marks.py:92-96`), so the check
needs a home of its own: the kernel build's post-build checks, beside the step that runs `verify`
with the build's `System.map` (`tools/rlxfw-kbuild.sh:965-971`). 🔄 2026-10-23: that home is
`fwarg_check` (`tools/rlxfw-kbuild.sh:1010-1031`), called at the end of `run_gates` (`:989`) on the
same map, with `fw_arg0..3` as its control; its verdict is in the manifest and in the build's
verdict, and a red or refused one exits 6 (`tools/test-kbuild-cflags.sh` `F1`–`F7`). 量 green on the
first build: `fw_arg0..3` at `0x803F8524`–`0x803F8530`, no `prom_argc` or `_prom_argv` (`FW-264`).

**`include/linux/rlxfw-handoff.h`** (new, pure, no `#include`, the shape of
`rtl819x-spi-install.h`): the three constants of `handoff.h` restated, and

```c
enum { RLXFW_HO_OK = 0, RLXFW_HO_MAGIC, RLXFW_HO_CHECK, RLXFW_HO_SLOT, RLXFW_HO_VERSION };
static inline int rlxfw_handoff_parse(u32 a0, u32 a1, u32 a2, u32 a3, u32 *slot, u32 *ver)
{
	if (a0 != RLXFW_HANDOFF_MAGIC)                  return RLXFW_HO_MAGIC;
	if (a3 != ~(a0 ^ a1 ^ a2))                      return RLXFW_HO_CHECK;
	if (a1 != RLXFW_HANDOFF_SLOT_A && a1 != RLXFW_HANDOFF_SLOT_B) return RLXFW_HO_SLOT;
	if (a2 < 1u || a2 > 0xFFFFFFFEu)                return RLXFW_HO_VERSION;  /* RLXU_VER_MIN..MAX */
	*slot = a1; *ver = a2;                          return RLXFW_HO_OK;
}
```

**`arch/rlx/kernel/rlxfw-boot.c`** (new, rlxfw's own, linked by a marks row `obj-y +=
rlxfw-boot.o` in `arch/rlx/kernel/Makefile` with witness `str:rlxfw-boot`; the anchor must occur
exactly once in the staged file, and `MK7` already anchors there, `config/rlxfw-marks.tsv:249`;
the file itself lives in `kernel/linux-2.6.30/`, mirroring the staged layout, as
`kernel/linux-2.6.30/arch/rlx/kernel/rlxfw_mark.c` does, whose `rlxfw_puts` (`:85`) prints the line):
an `arch_initcall` parses `fw_arg0..3` once, latches the result, prints one console line, and
creates `/proc/rlxfw-boot` (mode 0444, one `read_proc` well inside one page); it exports
`int rlxfw_boot_handoff(u32 *slot, u32 *ver)`, `-ENOENT` for none, for § 2. 🔄 2026-10-23, as built
and ruled: the row is `MK14` (`config/rlxfw-marks.tsv:279`), anchored after `MK`'s own
`obj-y += rlxfw_mark.o`, and its witness is `sym:rlxfw_boot_handoff`: `str:rlxfw-boot` would stop
being able to fail once a program that reads `/proc/rlxfw-boot` is in the initramfs, which the ELF
carries uncompressed. The function is a plain global, not `EXPORT_SYMBOL`'d (`CONFIG_MODULES` is
not set). 量 the first build: `rlxfw_boot_handoff` at `8000b0e4` (`T`), `MK14` `sym:` `mine:1`.

| boot | console (`rlxfw_puts`) | `/proc/rlxfw-boot` |
|---|---|---|
| handoff valid | `RLXFW-HANDOFF slot=B ver=6` | `slot B ver 6` |
| anything else | `RLXFW-HANDOFF none why=magic a0=00000000` (`why` ∈ magic, check, slot, version) | `none` |

A gate reads `/proc/rlxfw-boot`, never the console line (`CLAUDE.md` § At the bench). The raw
`a0` on the `none` line costs nothing to print and answers an open question (§ 9, item 2).
🔄 2026-10-23: the line is `RLXFW-HANDOFF`, renamed from this design's `RLXFW-BOOT`, which is one
glyph from the boot ladder's `RLXFW-B00`; 量 the first build's `vmlinux` holds both formats and no
`RLXFW-BOOT`. Every boot capture from the next image gains this line and `RLXFW-SW0=` (§ 2.9), so
a prediction of a boot's console bytes moves with them.

### 1.5 Why it is fresh

- The four values travel in registers from `rlxboot`'s `jr` to `rtkload`'s first instruction, and
  registers do not survive a reset. 讀 nothing executes between the two but the delay-slot
  `ori` (§ 1.2).
- In memory they live for one boot only, in `rtkload`'s own `.data`, and **that location is
  rewritten every boot before the save**: 讀 `rlxboot` copies the payload — this array's initial
  zeros included — to `load_addr` from its verified buffer (`src/rlxboot/main.c:250`) and only
  then jumps. So if the entry store were somehow lost, `start_kernel` would read the image's zeros
  and the kernel would read `none`; 推 no path makes it read a previous boot's handoff, which is
  the `MEM-17` hazard (`SPEC.md` `MEM-17`, 量: written DRAM survives a power cycle). The loader's
  `J` after a TFTP upload rewrites it the same way, with the loader's registers.
- **KSEG1, so no cache state decides it.** ⚠️ Two cache facts are not settled on this die: whether
  the D side is write-through or write-back without write-allocate (`SPEC.md` `CPU-19`'s 殘留 ①,
  with zero measurements, `docs/known-issues/09-never-measured.md:63`, although
  `src/rlxboot/main.c:19-21` states the second as fact), and the write-back half of `CCTL 0x200`
  (`notes/rlxboot.md:295-305`). Through KSEG1 the store goes to DRAM and the load reads DRAM,
  whatever either answer is; 讀 `rtkload`'s `flush_cache()`
  (`src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/hfload.c:112`) → `CCTL 0x200` then `0x002`
  (`src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/cache.c:40-50`, `:132-160`, `:69-78`)
  touches no line of the array, because no cached access in `rtkload` ever fills one: the array is
  one 16-byte line of its own (4 words a line,
  `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/cache.c:24`; `.align 4`), and nothing reads or
  writes it through KSEG0. The one assumption kept is the one every `rlxboot` boot already rests
  on: that `rlxboot`'s own `0x200` before its jump (`src/rlxboot/main.c:255`) leaves no dirty line
  of the payload copy to be written back later over the array. If it did, the write-back would
  land after the entry store and `start_kernel` would read the image's zeros: the kernel reads
  `none`, the fail-closed case, and B2 (§ 6.3) would show it.
- The kernel latches `fw_arg0..3` once (§ 1.4); they are stored on every kernel entry
  (`src-vendor/rtl819x-toolchain/linux-2.6.30/arch/rlx/kernel/head.S:141-144`).

### 1.6 The check word

It catches registers that are not a handoff, not an attacker. Anyone who can run code before the
kernel — a payload typed at the loader's prompt (`T6`) — can set any four values; that position
already writes flash with `FLW` (`docs/threat-model.md` § 7), so the check defends nothing it
could. 推 a stray four-register state passes only if a0 equals the magic **and** a3 equals the
complement of a0⊕a1⊕a2, about 2⁻⁶⁴ for unrelated values; what the loader's `J` leaves is
unmeasured (`docs/loader-command-semantics.md` § d says only that the target cannot rely on it,
`docs/loader-command-semantics.md:332-333`), and the `none` line's `a0=` records it (§ 9).

### 1.7 What each boot path produces

| path | a0–a3 at `rtkload` | `/proc/rlxfw-boot` on the new image | |
|---|---|---|---|
| new `rlxboot` at `0x010000`, slot boot | magic, slot, version, check | `slot X ver N` | 讀 § 1.2–1.4 |
| rescue copy at `0x020000` (`127a71cf`) | 0, 0, 0, 0 (`src/rlxboot/jump.S:57-62`, `rlxboot_jump`; the file's one commit until `948ff614`) | `none` (`why=magic`) — **the fail-closed case** | 讀 |
| `rlxboot` built `BOOT=ram` (`J 81800000`) | 0, 0, 0, 0 | `none` | 讀 |
| the loader's `J 80500000` after a TFTP upload | whatever the loader leaves | `none`, 推 | 推 |
| new `rlxboot` booting an **old** image (T, S) | handoff registers | — T's `rtkload` overwrites a0 at `src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/start.S:144` and zeroes a0–a2 at `:159-161`; T's kernel reads no `fw_arg` | 讀 |

The last row is what makes `W1` (§ 6) safe while slot A still holds T.

## 2. The install path, extended and shipped

### 2.1 Two regions, `cfg0` and `cfg1`

讀 before 1.1 the table held six regions, ascending, asserted at compile time, the last
(`probe`, `0x3E0000`) ending exactly at the state block. Since 1.1 (`5dedaee2`) it is
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:182-202`, asserted at `:102-151`,
the probe (`:76-77`) still ending at the state block (`:128-129`), and two rows have joined it
between `slotB` and `probe`:

| name | base | size | kind | why there |
|---|---|---|---|---|
| `cfg0` | `0x3C0000` | 65,536 | `K_CFG` | 讀 inside the tail the 2026-08-16 dump read erased (`0x34C000`–`0x3FFFFF`, `notes/update-chain.md:318`); 推 still erased — no install-path region named it before 1.1, and no `FLW`/`EW`/`EB` was issued at any seating since `v0.6` (`docs/known-issues/v1.0.md:103-108`), but writers nobody identified exist (`FLS-26`), so the card pre-reads it; the top of the free area, so `0x2B0000`–`0x3BFFFF` stays free for larger slots |
| `cfg1` | `0x3D0000` | 65,536 | `K_CFG` | its own 64 KiB block: no erase of one can reach the other at either candidate grain (`FW-187`); 量 the grain is 4,096 (`FW-244`) |

New compile-time asserts, beside `:81-111`: each of `cfg0`, `cfg1` 64 KiB-aligned and exactly
`RLXFW_SPI_INST_BLOCK`; `SLOTB_END <= CFG0_BASE`; `CFG0_END <= CFG1_BASE`;
`CFG1_END <= PROBE_BASE`; `CFG0_BASE >= 0x2B0000` and `CFG1_END <= 0x3E0000` (the DoD's
window); `IMG_CAP >= CFG sizes`. `RLXFW_SPI_INST_NREGIONS` is 8 in the provisioning table and 5 in the shipped one, and
the host test's index enums (`tools/test-spi-install.c:69-74`) and its region-count row
(`:246-252`) follow it (1.1).

**Chosen: a shipped table without `rlxboot`, `rescue` and `barrier`.** Behind
`RLXFW_SPI_INST_PROVISION` (0 in the shipped build, 1 in a RAM-only provisioning build), so the
lowest address the shipped image can name is `0x070000` and no running image can rewrite
`rlxboot` or its rescue copy through a verb. `W1` (§ 6) uses the existing armed image `8dce09c5`,
which has them. The cost: updating `rlxboot` is a bench act.

### 2.2 The `K_CFG` payload check

`rlxfw_spi_inst_chk_cfg(img, len)`: `len == 4,096` exactly (`CFG_SLOT_SIZE`, `src/lib/cfg.h:52`),
magic `RLXC` at 0, format 1 and header length 24 at 4 and 6, `seq` at 8 in
1..`0xFFFFFFFE` (`src/lib/cfg.h:30-43`) — the constants restated, as `container.h`'s are
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:670-688`), and compared with
`src/lib/cfg.h` by the host test. No CRC in the kernel: the loader of the record checks it
(`src/lib/cfg.c:308-338`), and the kind check exists to stop a container landing in a store region
or a record in a slot (`chk_rlxu` already refuses anything not `RLXU`, so a record:
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:694-695`). New reason `HDR_SEQ`.
`chk_payload` (`:786-798`) gains the kind.

### 2.3 `erase cfg0` / `erase cfg1`

`erase` today is barrier-only
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:523-526`, `NOT_ERASABLE`). It is
allowed on `K_CFG` too, with the usual arm equal to the region. It is the deterministic way to
make a slot invalid on the die (§ 3.6; § 6.3 W8, W9); `n_writes` +16 (`plan_init`: 65,536 / 4,096
SEs, no programs, `:863-864`).

### 2.4 The counter verb `ctr <N>`

#### 2.4.1 The encoding it writes

讀 `notes/rlxboot.md:155-170` and `src/rlxboot/container.c:180-207`: a 512-byte bitmap at
`0x3F0000`, 4,096 bits; the value is the number of leading zero bits, MSB first within a byte,
bytes in address order; a zero after the first one is *malformed*, and then the value is the
**total** zero count, never below the leading run. 讀 `rlxboot` reads it through the window at
`0xBD3F0000`, byte loads (`src/rlxboot/flashread.c:99-100`), once per boot
(`src/rlxboot/main.c:373-380`), and refuses `version < counter` (`src/rlxboot/container.c:401-403`).

#### 2.4.2 Semantics

`ctr <N>`: `N` is 1–4 decimal digits, the first not `0` (so `ctr 0` is `SYNTAX` and `ctr 4097`
reaches the range check), after exactly one space, nothing trailing; no address anywhere (the
bitmap's place is the compile-time `RLXFW_SPI_INST_STATE`,
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:54`). 讀 the `/proc` handler hands
a line to the install parser by prefix (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3425-3427`)
and the parser reads the first token whole
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:481-500`), which is how
`eraseprobe` is told from `erase` today; `ctr` and `ctrloop` take the same path, so `ctrloop`
never reaches `ctr`'s grammar (§ 2.8, group B). Under `rtl819x_spi_lock`, in this order:

1. **parse** — else `SYNTAX`;
2. **range** — `N > 4,096` → `CTR_ABOVE`;
3. **handoff tie** (chosen, § 2.4.5) — `rlxfw_boot_handoff()` is `none`, or its version is
   not `N` → `CTR_HANDOFF`;
4. **read** the 512 bytes by PIO (`read_pio`,
   `kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:535-584`) and decode with the same rule
   as `rlxboot` (a restatement, compared with `rlxu_counter_from_bitmap` by the host test, § 2.8 M)
   → `cur`, `malformed`;
5. **refusals** — `N < cur` → `CTR_BELOW`; malformed with any zero at a position `>= N` →
   `CTR_MALFORMED` (bits cannot be set back without an erase); `N == cur` and well-formed → done,
   result `SAME`, **nothing sent**;
6. **program, one bit per page program**, ascending: for each bit `b` below `N` that reads 1 (on a
   well-formed bitmap, every bit of `[cur, N)`), one `PP` of one byte at `0x3F0000 + b/8` whose
   value is `0xFF >> ((b % 8) + 1)` — which clears exactly bit `b`, since 推 (JEDEC's `PP`; the
   part's datasheet is not in hand, `FW-191`) a program only takes bits from 1 to 0 and bits
   already 0 stay 0. Each op goes through `rlxfw_spi_wr_chk_prog` against a per-op arm equal to
   `[0x3F0000, 0x3F0200)` (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h:215-234`),
   so the forbidden-window rule runs on every byte.
   **The plan holds no erase op, by construction and by host test.**
7. **read back** the 512 bytes; decode must be `N` and well-formed, else `CTR_CMP` (after a write:
   a failure, not a refusal).

`n_writes` moves by the number of bits cleared — `N - cur` on a well-formed bitmap (`+6` for
0 → 6, `+1` for 6 → 7). Console: `RLXFW-SC-GO cur=<c> new=<n>` before the first op and
`RLXFW-SC-END <reason> cur=<c> new=<n> read=<r> pp=<k> ms=<t>` after. `/proc/rtl819x-spi` gains
`ctr_ran ctr_cur ctr_new ctr_read ctr_pp ctr_reason ctr_attempts ctr_refused ctr_failed`; the page
budget (`RLXFW_SPI_INST_PROC_MAX`, 1,152 in 1.1, 1,183 since 1.2,
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:1301`) is re-measured by the host
test, as now.

🔄 2026-10-23, as built (`rtl819x-spi-install` 1.2, `948ff614`):

- **`n_writes` counts page programs**, one per program the primitive completed
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2894`), not bits cleared: on a faithful
  part the two are equal; a stuck bit is a program counted and no bit cleared (1B: six programs for
  five bits), which step 7 reports as `CTR_CMP`.
- **Every reason has an errno** (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2323-2330`;
  1.1's eight new reasons had none and all read `-EPROTO`, `ARM_READ`'s): `HDR_SEQ` `-ENOEXEC`,
  `REPEAT_ONLY_SLOT` `-EINVAL`, `RUNNING_SLOT` `-EBUSY`, `CTR_ABOVE` and `CTR_BELOW` `-ERANGE`,
  `CTR_HANDOFF` `-EPERM`, `CTR_MALFORMED` `-EILSEQ`, `CTR_CMP` `-EIO`; a glue case checks every
  reason has a row.
- **The counter block** prints `ctr_attempts ctr_done ctr_refused ctr_failed ctr_ran ctr_reason
  ctr_cur ctr_malformed ctr_new ctr_read ctr_pp ctr_ms`, `ctrloop`'s `loop_*` and `ctrscratch_*`
  (§ 2.7), and its own `ctr_truncated 0`; the install block ends `inst_truncated 0`. Each block's
  maximum is the host test's measurement at the widest every field's type can print, asserted
  equal: `RLXFW_SPI_INST_PROC_MAX` **1,183** (the shipped table 1,181) and
  `RLXFW_SPI_INST_CTR_PROC_MAX` **501**
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:1301`, `:1509`). 1.1's 1,152
  was measured with products that wrapped to 1, so two fields printed one digit, and it left out
  the block's own `inst_truncated` line (`SPEC.md` `FW-265`).
- **The counter block prints first**, under the page budget of 3,584
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:214`, `:3249-3261`): at `read_proc`'s
  widest prefix by its own comments, 2,323 B, the counter block prints whole and the install block
  says `inst_truncated 1`; at the armed image's measured 1,304 both print.
- **Machine readers get `/proc/rtl819x-spi-inst`**, mode 0400
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3539`): `n_writes <N>`, the install block
  and the counter block, nothing else, at most `RLXFW_SPI_INST_NODE_MAX` = 20 + 1,183 + 501 = 1,704 B,
  asserted at compile time to fit one `read(2)` (`PAGE_SIZE − 1024`); 量 on the host its widest is
  1,692 B (1B v3). Not in the first kernel build (`FW-267`).

**No arm, and the verb still ends disarmed.** Like every write verb it disarms on exit
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3162-3164`), so every caller takes the
flash lock (§ 3.2) to keep it out of
another process's arm → install pair. With the tie, the two statements `D6` asks to agree are the
typed value and the version `rlxboot` handed over; without it (if the tie is declined) the verb
requires an arm equal to `[0x3F0000, 0x3F0200)`, budget 512.

#### 2.4.3 Why one bit per program

Each op changes one bit, so the bitmap is well-formed after any prefix of the plan, and a cut can
leave at most one bit in doubt (§ 2.4.4). 推 one op is `WREN`, a 5-byte `PP` and the `RDSR` wait,
about 0.4–0.5 ms (`FW-245`: a page program's `WIP` wait about 0.36 ms); six ops about 3 ms.

#### 2.4.4 A torn program, and what the DoD can and cannot get

The zero set only grows. Let the advance be `c → n`, ops `j = 1 … n-c`, op `j` clearing bit
`c+j-1`.

- **A cut after `k` ops completed** leaves bits `[0, c+k)` zero and the rest one: well-formed,
  value `c+k`, with `c <= c+k <= n`.
- **A cut inside op `k+1`** leaves bit `c+k` cleared, not cleared, or *marginal* — a cell that reads
  0 on one read and 1 on another. Every read then decodes to `c+k` or `c+k+1`: well-formed both
  ways, because the doubtful bit is the first one after the zero run.
- So after any cut **the value is between the old and the new, inclusive, and never below the
  old** — the anti-rollback property. **For `n = c+1` it is exactly the old or the new**, as the
  DoD asks.
- **For `n > c+1` an intermediate value is possible, and no program order removes it.** Proof:
  every zero set `Z` reachable during the advance contains `[0, c)`, so its value is its size
  whether it is well-formed (the leading run is `|Z|`) or malformed (the total is `|Z|`); a `Z`
  with `c < |Z| < n` therefore reads strictly between the old and the new, and 推 clearing more
  than one bit, in one program or in several, passes through such sets whenever a cut can stop it
  (a cell does not flip at the same instant as its neighbours). The
  first advance of this round is `0 → 6` (§ 6): a cut inside it can leave 1–5. Each value is
  harmless (it refuses nothing a later value would accept), but it is neither old nor new. § 0.2
  item 2.
- **A malformed bitmap** can come only from a program that cleared a bit it was not asked to, or
  from an erase — and the state block is never erased. `rlxboot` resolves it upward
  (`src/rlxboot/container.c:200-206`), and `ctr` refuses to advance across it (step 5).
- **So "never above the new" rests on one assumption**: no program clears a bit it was not asked
  to. A stray clear at a position at or above `n` leaves the bitmap malformed, and its value is
  then the total zero count, `n + 1`: above the new. 推 JEDEC's `PP` takes only the addressed
  byte's bits from 1 to 0 (`FW-191`: the part's datasheet is not in hand); the host suite carries
  the case (§ 2.8, groups H and I), and on the die only the read-back of step 7 would see it.

#### 2.4.5 The handoff tie (chosen)

With step 3, `ctr` advances only to a version `rlxboot` booted on this boot, and an image
`rlxboot` did not start cannot advance it at all — the DoD's *"an image `rlxboot` did not start
never advances it"* becomes a kernel refusal, testable on the host and shown on the die, not a
property of `init`'s code. It also means the verb cannot burn the counter to 4,096 (the `T9`
denial), unless `rlxboot` booted a version-4,096 image — 推 root keeps another route (§ 7).

### 2.5 The running-slot fence (chosen)

`install slotA|slotB` refuses with `RUNNING_SLOT` before its GO line when
`rlxfw_boot_handoff()` names that slot. The update path never needs to write the slot it runs
from (§ 4), so this costs nothing and makes it a kernel property. A RAM boot reads `none`, so the
bench's own installs (§ 6) are unaffected. Glue-only reason, exempt by name in the pure suite
(the mechanism of `tools/test-spi-install.c:22-26`). 🔄 2026-10-23: not glue-only, and not
exempt: since 1.1 the pure `rlxfw_spi_inst_fence`
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:1245-1254`) produces it, the pure
suite drives it, and its exemption list does not name it (`tools/test-spi-install.c:2230-2234`).
The glue calls the fence before it reads the arm
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2664-2669`), so an unarmed install of the
running slot reads `RUNNING_SLOT`.

### 2.6 `install <slot> sha=<64> repeat=<k>` (for the unpaced-write cut rounds)

`k` 2–8, `K_RLXU` regions only (`REPEAT_ONLY_SLOT` otherwise), not with `pace=` (`SYNTAX`): the
same staged bytes written `k` times back to back under one arm, each time the whole plan (erase
all, program, header last, read back), a `RLXFW-SI-REP i/k` line between. It exists because a
hand-timed cut needs a window of at least 40 s (`CLAUDE.md` § At the bench) and an unpaced slot
write lasts 10.26–11.24 s (量 `FW-246`); `install slotB sha=<64> repeat=5` is 91 characters, so it
stays one `--send` under 127 that `cardcheck` can see. The alternative, a shell loop, does not fit
in 127 characters and puts the verb in a file `cardcheck` cannot read (`FW-113`'s old boundary,
`notes/spi-mtd-driver.md:1742-1745`). `n_writes` = `k × (288 + ⌈len/256⌉)`. 🔄 2026-10-23, as
built (1B; the design did not fix these, the glue suite drives each): `RLXFW-SI-REP i/k` comes
before repetitions 2…k only; under `repeat=` the counters accumulate and `committed` resets at
each repetition.

### 2.7 The scratch loop `ctrloop` (for the counter's cut rounds)

Under an arm equal to `probe` (`arm 0x3e0000 0x3f0000 0x10000`, the arm `eraseprobe` takes,
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2246-2249`; `arm` takes the window's two
ends and a budget, `:2166-2188`):

- `ctrloop <p>` (`p` 1–64): per pass, one `SE` of the 4 KiB sector at `0x3E0000`
  (`RLXFW-SL p=<i> erase`, then `… erased`), then 4,096 one-bit programs **with the routine of
  § 2.4 step 6**, on the bitmap at `0x3E0000`, a progress line `RLXFW-SL p=<i> bit=<b> ms=<t>`
  every 256 bits; at the end one `SE` and a verify, so `eraseprobe` finds the block clean.
  `n_writes` = `p × 4,097 + 1`. 推 about 2 s a pass: 4,096 × ~0.45 ms, one ~21.5 ms `SE`
  (`FW-245`), 18 console lines (`erase`, `erased` and 16 progress lines).
- `ctrloop show`: read-only, no arm; decodes the scratch bitmap with § 2.4 step 4's function and
  prints `ctrscratch value=<v> malformed=<0|1> erased=<0|1>` — never a byte.

What it measures and what it cannot (`P6r-11`'s own *does not establish*): the routine under a
cut, and how often a re-programmed page reads back right (§ 9 item 4) — not the state block.

🔄 2026-10-23, as built (1B; the design did not fix these, and the glue suite drives each):
`RLXFW-SL p=` is the pure plan's 0-based pass, and the final `SE` prints `p=<passes>`; `bit=` is
the bits cleared so far in the pass (256 … 4,096); after every `SE` the 512-byte bitmap is read
back and must be erased, else `PROBE_UNCLEAN` (which catches an `SE` that does nothing); after
every pass the bitmap must read 4,096, well-formed, else `CTR_CMP`; the final check reads the
whole 64 KiB probe block; a failure stops at once, with no clean-up erase; `ctrloop` attempts
are not counted in `ctr_attempts`, and every dispatched verb, `show` included, ends disarmed.
**`show` lands in `/proc`**, so a card gates on a field, not on its console line (`FW-47`):
`ctrscratch_shows` (attempts since boot), `ctrscratch_rc`, `ctrscratch_value`,
`ctrscratch_malformed` and `ctrscratch_erased`, the last over the whole 4 KiB sector; a failed read
records its errno and clears the three values. For `ctr` itself: `SAME` prints no GO line, and
`ctr_read` is step 7's read-back, `cur` for `SAME`, else 0.

### 2.8 Host test cases to add to `tools/test-spi-install.c` (each refusing and permitting)

In the file's groups (`tools/test-spi-install.c:164`, `:262`, `:431`, `:498`, `:543`, `:643`,
`:926`, `:952`, `:1070`, `:1244`: A, B, C, E, F/G, H/I, J, L, K, M), every reason produced by a case
and every case under `--mutate`. 🔄 2026-10-23: they landed beside those groups, as `P6r-10: the
store's payload` (`:1311`), `P6r-11: ctr, ctrloop, repeat=` (`:1390`) and a second group `M`, the
boot handoff's second source (`:1959`); `RUNNING_SLOT` and `CTR_HANDOFF` are produced by pure
functions (§ 2.5, `rlxfw_spi_inst_ctr_tie`), so neither is glue-only below:

| group | permits | refuses |
|---|---|---|
| A table | `cfg0`/`cfg1` at their bases, 64 KiB each, `K_CFG`, ascending, inside `[0x2B0000, 0x3E0000)`; every region `>= 0x010000`; no region reaches `0x3F0000`; shipped build lowest base `0x070000` (compiled with `PROVISION=0`) | — (compile-time: a header mutation moving `cfg1` onto `probe`, or `STATE` below `0x010000`, must not build — `test-spi-install.sh` mutates the header today) |
| B verbs | `install cfg0 sha=<64>`; `erase cfg1`; `ctr 6`; `ctr 4096`; `ctrloop 30` parsed as `ctrloop`, not as `ctr`; `ctrloop show`; `install slotB sha=<64> repeat=5` | `ctrl 30` and `ctr6` `SYNTAX`; `install cfg2 …` `REGION`; `erase slotA` `NOT_ERASABLE`; `ctr 0` `SYNTAX`; `ctr 06`, `ctr -1`, `ctr 0x10`, `ctr 6 ` (trailing), `ctr`, `ctr 99999` `SYNTAX`; `ctr 4097` `CTR_ABOVE`; `ctrloop 0`, `ctrloop 65` `SYNTAX`; `repeat=1`, `repeat=9`, `repeat=5 pace=…` `SYNTAX`; `install cfg0 sha=<64> repeat=2` `REPEAT_ONLY_SLOT` |
| C arm | `install cfg1` under `arm 0x3d0000 0x3e0000 0x10000`; `ctr` with no arm; `ctr` leaves no arm behind | `install cfg1` under a slot's arm `ARM_WINDOW`; `ctrloop` unarmed `UNARMED`, under `cfg1`'s arm `ARM_WINDOW` |
| F/G payload | a slot image made by the host build of `cfgstore --file … init --force` (the producer, as `mkfw2`/`mkcr6c` fixtures are) into `cfg0` | magic `HDR_MAGIC`; 4,095 / 4,097 bytes `HDR_LEN`; format 2 `HDR_FORMAT`; `seq` 0 and `0xFFFFFFFF` `HDR_SEQ`; a container into `cfg0` `HDR_MAGIC`; a record into `slotA` `HDR_MAGIC` |
| H plan | for every `c` in 0…4,096 and `n` in `c`…min(`c`+8, 4,096): `n-c` ops, each one byte inside `[0x3F0000, 0x3F0200)`, each clearing exactly one bit, ascending, applied to a model bitmap → decode `n`, well-formed; `c = n` → 0 ops | `n < c` `CTR_BELOW`; malformed with a zero at `>= n` `CTR_MALFORMED`; malformed with all zeros below `n` permitted and repaired; mutation "program two bits per op" and "insert an SE" each turn a property case red |
| I cuts | a cut after `k` ops and inside op `k+1` (bit stays 1, becomes 0, reads either): every read decodes to `c+k` or `c+k+1`, never below `c`, well-formed | a stray clear at a position `>= n` during the advance: decodes to `n+1`, malformed — the one case § 2.4.4's upper bound excludes, asserted as excluded rather than left out |
| J read-back | `ctr`'s compare passes on a faithful part | a stuck-at-1 bit → `CTR_CMP` |
| K `/proc` | the widest `ctr_*` + `inst_*` block fits the page budget | — |
| M second source | `rlxfw_handoff_parse` accepts (magic, `A`, 1, check) and (magic, `B`, `0xFFFFFFFE`, check); kernel and `rlxboot` check words equal over a sweep; the kernel's counter decode equals `rlxu_counter_from_bitmap` on all 4,097 well-formed bitmaps, every single-bit flip of 64 of them and 10,000 random ones (linking `container.c`, as `-DWITH_CONTAINER_H` already includes its header, `tools/test-spi-install.c:53-56`); `cfg0`/`cfg1` equal `cfg.h`'s flash constants (§ 3.7); `RLXC`, format, header length and slot size equal `cfg.h`'s | handoff with magic ±1, check ±1, slot `C` and 0, version 0 and `0xFFFFFFFF`, each its reason |
| L `ctrloop` plan | per pass one `SE` at `0x3E0000`, 4,096 one-byte ops inside `[0x3E0000, 0x3E0200)`, nothing outside `probe`, a final clean `SE` | — |

`tools/test-spi-install-glue.c` (the extracted glue against a simulated part) gains: `ctr` with a
valid and a `none` handoff (`CTR_HANDOFF`, glue-only), `n_writes` = bits cleared, a stuck bit, a
cut inside op `k`; `install slotA` refused `RUNNING_SLOT` when the handoff names `A` and permitted
when it names `B` or is `none`; `repeat=3` writing the region three times; `ctrloop 2` under a cut.
🔄 2026-10-23: `CTR_HANDOFF` is not glue-only (above), and `n_writes` counts programs (§ 2.4.2). 量
`tools/test-spi-install.sh` at `948ff614`'s code: 930 pure + 710 shipped + 302 glue + 300 shipped
glue cases, the glue built against both region tables because the shipped one is what the device
will run (1B v3, `$FWRE_WORK/rebuild/s144/1b/`; `948ff614`'s message records the same four counts).

### 2.9 Shipping the install path: the blast radius

- **`MK5` is retired, by ruling.** 讀 `config/rlxfw-kernel.delta:59`, its reason until `948ff614`
  (the row now reads `y` and records the ruling): flipping
  `CONFIG_MTD_RTL819X_WRITE` to `y` turns `MK5`'s `absent:rtl819x_spi_write_page` red, and it
  "CANNOT be re-witnessed without either retiring D4's build-time layer or relaxing
  tools/rlxfw-marks.py's pairing rule, which is a choice about a containment check and therefore
  the owner's". The owner delegated the choice and the ruling (2026-10-23, `LOG.md`'s 142nd
  entry) is the first route: `MK5` becomes `obj-y += rtl819x-spi-write.o` with
  `sym:rtl819x_spi_write_page`, retiring `D4`'s build-time layer, and the delta's row goes to `y`,
  edited where it stands (`SPEC.md` `FW-228` cites that line). Rejected: `--expect-present MK5` on
  every build. The flag inverts one named row for one run (`tools/rlxfw-marks.py:35-39`) and is
  "the whole record of which rows were exempted on this run" (`:644-646`), so passing it on every
  build would record the norm as an exception, while a `sym:` witness states what is true and
  still reds a build that drops the path. Containment moves to the run-time layers: the table's
  compile-time asserts, the single-use arm, the typed digest, `brokerd`'s signature check,
  `rlxboot`'s boot-time check, the running-slot fence (§ 2.5), and `cardcheck` at the bench.
  🔄 2026-10-23, 量 by 2M with planted faults: the ruling's blast radius in the checkers was wider
  than this list — `tools/test-config-gates.sh` `G4d` (twice) and `G4e`, and
  `tools/test-kbuild-cflags.sh` `X6` and `X8`, go red on the ruled declaration and were rewritten
  (`G4f` is now `G4d`'s positive control; `X6`–`X8` drive the flag through a fixture row, and `X5b`
  pins that `--expect-present MK5` is refused); `X7`, guessed red, is not, because its
  `--target none` refusal fires first. The delta's row back at `n` stops the build at compile time,
  at `rtl819x-spi-write.c`'s `#error`
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-write.c:48-50`), not at link (量 both
  ways with the armed cell's kbuild command for that object). And the write TU's `late_initcall`
  prints `RLXFW-SW0=<grain>` (`:359-365`): every image from the next build has that boot line.
- `unarmed_rc` reads `-EACCES` instead of `-EOPNOTSUPP`
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:324-333`); `MT-FLASH-2` already
  compares against the image's own constant, and in a write image expects `-EPERM` (`docs/mfgtest.md`,
  `kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2126-2144`). ⚠️ Its last conjunct,
  `n_writes == 0` (`:2144`), is one `docs/mfgtest.md`'s row says cannot fail today (`FW-142`): no
  committed image increments the counter. In an image that writes, a boot that has stored a record
  or advanced the counter before `trywrite` runs reads `n_writes` above 0 and the row goes red on
  a correct image, so the conjunct becomes `n_writes == w0` alone, or the row states when in the
  boot it runs. 🔄 2026-10-23: 讀 not done in `948ff614`: `trywrite` still asserts
  `n_writes == 0` (`:2144`) and so does `config/mfgtest.sh:392-396`. Phase 1 adds no writer
  that runs at boot, so the conjunct holds on its images; the first image whose boot writes before
  `trywrite` runs — § 5's counter advance — fails `MT-FLASH-2` on a correct refusal.
- `cardcheck` must learn every new write verb (`ctr`, `ctrloop`, `erase cfgN`, `repeat=`) — its
  `A56`–`A62`/`B16` scope names `install`, `erase`, `eraseprobe` today
  (`notes/spi-mtd-driver.md:1728-1732`) — **and** the writes no `--send` names: a `cfgstore`
  command, an HTTP upload, and the boot of an image whose `init` advances the counter.
  🔄 2026-10-23: 🔴 讀 not done in `948ff614`, and half of it is now live: `tools/cardcheck.py`
  refuses a driver write only when the echoed line begins `install` or `erase`
  (`tools/cardcheck.py:977`), which covers `erase cfgN` and `repeat=`, while the driver hands
  every line beginning `ctr` to the install parser
  (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3425-3427`). So on every image from the
  next build a card's `ctr <N>` or `ctrloop <p>` programs flash and passes `cardcheck` with no
  owner-yes; the tie limits `ctr` to the booted version, and `ctrloop` to the probe block.
- `docs/known-issues/v1.0.md:32-38` ("the image in the slots has no install path"), `docs/sbom.md`
  (the armed image not covered), `notes/spi-mtd-driver.md`, `docs/drivers/spi.md`,
  `docs/threat-model.md` (§§ 3, 9, 10, for `T2`, `T8`, `T9`; § 7 below) and `REPRODUCE.md` move
  with it. 🔄 2026-10-23 (2M): so do `NOTICE` § 2, `kernel/README.md`, `docs/mfgtest.md`'s
  `MT-FLASH-2`, `docs/known-issues/08`, `docs/bringup.md`, `notes/kernel-build.md`'s armed recipe,
  `notes/reproducible-build.md` § 9, `SPEC.md` `FW-44`, `FW-207`, `FW-210` and `FW-228`, and two
  comments, `tools/cardcheck.py`'s write-verb block and `tools/test-spi-wrpolicy.c`'s head.
- The `/dev/mtd*ro` nodes stay (§ 3.1 needs `mtd2ro`), and busybox `nc` stays out of the shipped
  image: 讀 the armed image drops the nodes to carry `nc` (`notes/update-chain.md:520-525`), and
  `mkinitramfs`'s `check_no_h601_dumper` is the reason the two do not mix
  (`config/rlxfw-initramfs.tsv:246-249`).

**Headroom.** 讀 a slot holds the whole container, image + 160 B (`notes/update-chain.md:37-39`),
and the image grows in 1,024-byte steps
(`src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/ld.script:33`, `:37`): the largest image a
1,179,648-byte slot holds is 1,178,624 B (1,151 × 1,024; 1,152 × 1,024 + 160 would not fit), so
the room above `v1.0`'s 1,110,016 B is **68,608 B, 67 steps** (`SPEC.md` `FW-263`). 推, every
row a guess:

| addition | uncompressed | in the image (LZMA) | source |
|---|---|---|---|
| install path + write TU in the shipped kernel | `rtl819x-spi.o` `.text` 10,208 → 22,608 B (objects read at the desk, `notes/spi-mtd-driver.md:1562`), plus the write TU | about 6 KB | 讀 the artefacts: armed `8dce09c5` 1,117,184 B − `9bb2bec7` 1,110,016 B = 7,168 B (`LOG.md:1045`), which also carries busybox `nc` (+2,232 B uncompressed, `notes/update-chain.md:525-526`) and three fewer nodes |
| handoff TU, `ctr`, `ctrloop`, `K_CFG`, fence, `repeat` | 3–4 KB | 1.5–2 KB | 推 |
| `rtkload` patch | 12 more instructions (48 B; 🔄 2026-10-23, this read 13 and 52 B), 27 B of `.data` | 0 or 1,024 B (the step); 量 0 for `v1.0`'s kernel | § 1.3 |
| `brokerd`: `container.c`, `slots.c`, `sha256b.c`, `ed25519.c`, `sha512.c` | 13–15 KB | 6–8 KB | 推 from `rlxboot`'s `.text` 13,808 B (`notes/rlxboot.md:524-526`), which is mostly this code |
| `brokerd` update ops, flash I/O | 3–4 KB | 1.5–2 KB | 推 |
| `httpd` streaming route | 2–3 KB | 1–1.5 KB | 推 |
| `cfgflash.c` in `cfgstore`, `brokerd`, `init` (each static) | 3 × 1.5 KB | 2 KB | 推 |
| `init`: counter helper + `client.c` + `proto.c` | 4 KB | 2 KB | 推 |
| **total** | | **about 20–25 KB, 20–25 steps** | leaves about 42–47 of the 67 steps (43,008–48,128 B), 推 |

A new statically linked program would cost more than the code it carries — 讀 the smallest static
programs in this desk's `build/rlxfw-user/` (not tracked) are `linkprobe` at 16,240 B and `ifupd`
at 23,164 B (Sep 30 builds), against about 4 KB for § 5's helper inside `init` — so nothing here
adds one. The image is measured by the build; the table is a guess to be refuted by it.

🔄 2026-10-23, 量 the first build (`s144k1`, recipe `b1c23023`, built from `0446468c`: phase 1
without `/proc/rtl819x-spi-inst`, with `CONFIG_FILE_LOCKING`, around `v1.0`'s userspace, whose
manifest differs from `v1.0`'s only in `/bin/mfgtest`, 32,620 → 32,619 B): `nfjrom` 1,124,352 B,
1,098 steps — **14 steps (14,336 B) above `v1.0`'s 1,084, and 53 steps (54,272 B) below the
slot's 1,151**; `vmlinux.elf` 4,659,342 B, +37,390; the decompressed image 4,161,536 B of the
5,242,880-byte ceiling, 79.4 %. The kernel rows above guessed 7.5–9 KB in the image, about 8–9
steps, for what took 14 together with `CONFIG_FILE_LOCKING`, which the table did not have
(`fs/locks.o` is 14,460 B of text and read-only data by the host's `size`, § 3.2). 量 by 1B,
`rtl819x-spi.o`'s `.text` grew 24,092 → 31,300 B (+7,208) for the glue alone, compiled with the
armed cell's flags, against the 3–4 KB guessed for the glue and the handoff TU together; in
`s144k1` its `.text*` sections total 31,716 B, and `rlxfw-boot.o`'s 292 B with 460 B of
`.init.text`, freed after boot. The userspace rows are still guesses (§§ 3–5 are unbuilt).
`SPEC.md` `FW-267` holds the numbers.

## 3. The store on flash

### 3.1 Reading: `/dev/mtd2ro`, and why nothing else

讀 the four candidates:

| path | serialised with the install path? | verdict |
|---|---|---|
| `/dev/mtd2ro` (`c 90 5`, mode 0400, `config/rlxfw-initramfs.tsv:303`): `rtl819x_spi_mtd_read` | yes — it takes `rtl819x_spi_lock` for the whole read (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:1230-1243`), the mutex an install holds from its arm check to its disarm (`:3153-3165`) | **used**; 4-byte-aligned offset and length (`:1227-1228`): `0x3C0000`, `0x3D0000`, 4,096 ✓ |
| `/dev/mtd0ro`, `/dev/mtd1ro` | no — the vendor's driver, "which drives the same four registers with no lock" (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:11-13`) | not used: a read during an install would share the controller unlocked |
| `/proc/rtl819x-spi-map` | — | digests only, by design (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:37-42`) |
| the window at `0xBD000000`, the install's read-back | — | kernel-only; no `nod` row declares `/dev/mem`, and the declared nodes are the only ones the image can hold (`config/rlxfw-initramfs.tsv:197-204`) |

Because the reader takes the mutex an install holds, a reader sees a slot before or after a
store write, never during one — 讀 a stronger property than `cfg_load_info`'s CRCs alone give, and
it holds only for this path. 推 a 4,096-byte read costs about 4 ms: 量 `FW-48` bounds the PIO rate
below at 1,065,510 B/s, measured through `/dev/mtd2ro` itself (`notes/spi-mtd-driver.md:1704`;
the row's other figure, 318,129 B/s, is the `verify` walk's per byte compared, which the row
itself says is not the PIO rate).

**An erased slot reads as absent.** The flash backend reports `got = 0` for a slot whose 4,096
bytes are all `0xFF`, so a store with both regions erased is "no store yet" exactly as a missing
file is today (`src/lib/cfg.c:544-548`), and one with one erased slot loads the other.

### 3.2 Writing one slot

`cfg_store` (`src/lib/cfg.c:824-827`, its body now `store_rec`, `:751-822`) keeps its rules — validate, read both slots,
`newseq = max + 1`, target the slot not selected (`:804-805`), build the 4,096-byte image from the
whole record (`cfg_slot_image`, `:454-469`), read back and parse — and replaces only
`write_at`/`fsync` with `cfg_flash_write_slot(s, img)`:

1. `flock(LOCK_EX)` on `/run/rlxfw-flash.lock` (讀 PID 1 mounts `/run` mode 0755,
   `src/init/mounts.c:58`, so only root creates the file; mode 0600), bounded: 30 s of
   `LOCK_NB` retries, else `-CFGE_IO`. Every writer of `/proc/rtl819x-spi` verbs takes it
   (`cfgstore`, `brokerd`, `init`'s helper), so one process's `img reset` → stage → arm → install
   cannot interleave with another's (`D20`'s lock is per verb; the staging buffer and the arm are
   shared state between verbs). 🔄 2026-10-23: 讀 no kernel built here could take it:
   `CONFIG_FILE_LOCKING` was not set in any of them, `v1.0`'s included, so `flock(2)` returned
   `-ENOSYS` and a writer following this design would have failed closed on every store write.
   Ruled: the delta sets it (`config/rlxfw-kernel.delta:427`); 量 the first build carries it and
   `flock_lock_file_wait` (`SPEC.md` `FW-266`).
2. `disarm`, `img reset` (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3420-3429`).
3. one `write(2)` of 4,096 bytes to `/proc/rtl819x-spi-img`; it returns only after
   `copy_from_user` under the mutex (`:3185-3226`).
4. read `/proc/rtl819x-spi`: `img_len 4096`, `img_err none`, and `n_writes` noted.
5. `arm 0x3c0000 0x3d0000 0x10000` (or `0x3d0000 0x3e0000`).
6. `install cfgN sha=<64 hex>` — the digest computed by the writer with `src/lib/sha256.c`, already
   linked into `cfgstore` and `brokerd` (`RLXLIB_NAMES`, `src/lib/Makefile:38`; `KDFSRC`,
   `src/brokerd/Makefile:42`). In the shipped image the digest is the writer's, not a person's, so it no longer
   authorises anything (`P6r-10`'s most-likely-wrong); what it still does is refuse a staging that
   differs from the writer's buffer — a short or interleaved one (`SHA`).
7. read `/proc/rtl819x-spi`: `inst_reason OK`, `inst_cmp_ok 1`, `inst_cmp_diff 0`, and
   `n_writes` moved by exactly **32**; anything else is `-CFGE_IO` with the reason logged.
8. `img reset` (frees the staging buffer,
   `kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3171-3180`), release the lock; then
   `cfg_store`'s own read-back through `/dev/mtd2ro` and `cfg_parse_record`
   (`src/lib/cfg.c:705-719`).

讀 one `write(2)` per verb, so `FW-247`'s triple handler call (busybox ash re-writing after a
refused write) does not arise, and `/proc` keeps the reason of the call this code made.

### 3.3 `n_writes` per store write

讀 `rlxfw_spi_inst_plan_init`
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:847-866`): `ne = 65,536 / 4,096 =
16` erases (the grain is 4,096, 量 `FW-244`), `np = ⌈4,096 / 256⌉ = 16` programs — **32 per store
write**, the header page last (`:873-907`), the whole 64 KiB read back
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2802-2820`). `erase cfgN`: 16. 推 a store
write lasts about 0.4–0.5 s: 量 `FW-246`, a 64 KiB region with 89 ops took 480–510 ms; this has 32.

### 3.4 Which programs change

- `src/lib/cfg.h`: `CFG_FLASH_DEV "/dev/mtd2ro"`, `CFG_FLASH_OFF0 0x3C0000`,
  `CFG_FLASH_OFF1 0x3D0000`, `CFG_FLASH_REGION 0x10000`. The PINNED declarations
  (`src/lib/cfg.h:51-133`) do not change: `cfg_load_info`/`cfg_store` dispatch on
  `path == CFG_FLASH_DEV`, and the file backend stays for the host suites (the torn-write sweep,
  `notes/config-store.md` § 5).
- `src/lib/cfgflash.c` (new): `cfg_flash_read_slot`, `cfg_flash_write_slot`, the lock; a guard
  that refuses any offset range overlapping `[0, 0x10000)` before the `open`.
- `cfgstore`: default path `CFG_FLASH_DEV` (`src/cfgstore/main.c:52`); `dump --hex` reads through
  the backend instead of `fopen` (`src/cfgstore/main.c:471-511`). ⚠️ `dump --hex` prints
  `admin.pwhash`'s bytes by design (`src/cfgstore/main.c:34-39`): no card may type it after a
  password is set (§ 6.4).
- `brokerd`: `BK_CFG_PATH` (`src/brokerd/brokerd.h:24`) → `CFG_FLASH_DEV`. `init`: `PATH_CFG`
  likewise (`src/init/main.c:1013`, `:966`).
- `init` links `cfg.c` but never stores; if `cfg.c` calls `cfgflash.c`'s writer, `init` links
  `sha256.c` too (about 2 KB, in § 2.9's table).

### 3.5 `FW-184`'s per-request reload, on flash

讀 `brokerd` reloads the whole store before every request (`src/brokerd/ops.c:646-698`, called
at `:727`), 8 KiB. On flash that is two PIO reads: 推 ≤ 8 ms each request, and about 550
`UPDATE_DATA` requests per upload (§ 4) → ≤ 4.5 s. **Optional, after a measurement**: cache the
parsed record keyed on the two 24-byte headers, re-reading a slot only when its header bytes
changed. Sound for this store's own writes — an install erases the slot first (header → `0xFF`),
then writes the header last (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:873-907`)
with a new `seq` and CRCs — and it keeps `FW-184`'s promise.

### 3.6 Making a slot invalid on the die, and `cfgstore show`

- **Option A (chosen; the DoD reads *both erased*): erase.** `erase cfg1` makes slot 1 absent;
  `cfgstore show` then loads slot 0 (*one slot erased, the other loads*). Erasing both makes the
  store "no store yet": `load_or_die`'s strict path does not fire (`src/cfgstore/main.c:105`:
  `file_bytes > 0` is false), `show` prints `source default` with `admin.pwhash <unset>`
  (`src/cfgstore/main.c:207-236`), and `brokerd` answers every `LOGIN` `AUTH`
  (`src/brokerd/ops.c:438-444`). Deterministic and nameable (§ 6.3).
- **Option B (not taken; it would be needed if "invalid" had to mean garbage):** `show` loads
  non-strictly and prints the store line, the two slot verdicts and the table, then exits 4 for a
  store that holds bytes but no record. No case of `test_cli.c` asserts `show` on a corrupt store
  today (`src/cfgstore/test_cli.c:259-291` covers `get`, `set`, `dump`, `init`).

### 3.7 Two owners of two numbers

`0x3C0000`/`0x3D0000` live in the kernel's table and in `cfg.h`. The host test includes both
(`tools/test-spi-install.c` with `-DWITH_CFG_H`) and fails on a difference, the pattern by which
`rtl819x-spi-install.h` restates `container.h`
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:670-679`). A drift that escaped it
fails closed on the die: the arm `cfg.c` types would not equal the region (`ARM_WINDOW`).

### 3.8 Without a shell (ruled 2026-10-23 for the shipped image)

The shipped image drops the console root shell (`BENCH_SHELL=0`) and gains a console
first-password step that runs only while the store holds no `admin.pwhash`; the bench image keeps
the shell. Nothing in §§ 3–5 needs a person at a root shell:

- every store write in normal operation is `brokerd`'s (`SET`, `PWSET` through `httpd`) or the
  first-password step's; `PWSET` with no stored hash stays root-only (`src/brokerd/ops.c:564-568`),
  so the first password stays a console act;
- ⚠️ **the first-password step must write over a corrupt store.** 讀 `cfgstore passwd` loads
  strictly and refuses a store with bytes and no valid record (`src/cfgstore/main.c:642`,
  `:105-114`). On a
  shell-less image there is no `cfgstore init --force` to type, so a corrupt store would make the
  first password impossible. The step has to write a fresh record (defaults + hash) into slot 0
  without reading the corrupt one — fail-closed already held, since a corrupt store loads as
  defaults with no hash;
- the update and the counter are driven by `httpd`, `brokerd` and `init`, and print their verdicts
  on the console (§ 4.5, § 5); a failed install leaves the old image running and the next upload
  retries (§ 4.5), and `STATUS` gains one TLV with the last update's result for a web user;
- the bench reads (`cfgstore show`, `/proc/rtl819x-spi`) and the bench-only verbs (§§ 2.3, 2.6,
  2.7) need the bench image. § 6.2 says which images the round uses.

## 4. The update path

### 4.1 `httpd`: a bounded streaming upload

讀 the limits it lives in: a 4,096-byte body cap checked at the header line and at the end of the
headers (`src/httpd/http.c:402-413`, `:445-469`; `src/httpd/http.h:31`), a 10 s per-`recv` body
timeout (`src/httpd/http.h:37`, `src/httpd/serve.c:365-369`), a 20 s alarm on the whole connection
child (5 + 10 + 5, `src/httpd/serve.c:713-714`), fork per connection with at most 8 children
(`src/httpd/serve.c:541-742`, `src/httpd/http.h:38`), and one broker request per connection with
a 2,048-byte body and a 15 s I/O deadline (`src/lib/proto.h:29`, `src/lib/client.c:20-21`,
`:94-209`). The route exists and answers 501 after the session and CSRF checks
(`src/httpd/routes.c:1018-1029`, `:1059`).

The design, inside that architecture:

1. **The parser learns one streaming route.** When the request line is `POST /api/firmware`,
   `Content-Length` is bounded by `HTTP_UPLOAD_MAX` = 1,179,648 (the slot,
   `src/rlxboot/rlxboot.h:76`) instead of `HTTP_BODY_MAX`; `end_of_headers` returns a new code
   instead of entering `HS_BODY`, and `srv_conn` (`src/httpd/serve.c:307-370`) hands the socket and
   the bytes already read past the headers to `upload.c`. A larger `Content-Length` is `413` at the
   header line, before any body byte is kept: **refused whole**. `Transfer-Encoding` stays `501`
   (`src/httpd/http.c:414-419`).
2. **Authentication before the body.** `upload.c` runs `route_dispatch`'s `RF_SESS`/`RF_CSRF`
   checks (`src/httpd/routes.c:1148-1164`), then `UPDATE_BEGIN` (body: the declared length) —
   `brokerd` checks the session and the CSRF token there (`src/brokerd/ops.c:754-763`) and refuses
   before a byte of the body is forwarded. Only then is the body read.
3. **The body, in broker-sized pieces.** Read up to 2,044 bytes at a time (2,048 less the
   offset); send each as `UPDATE_DATA` (body: a 4-byte offset, then the bytes); stop at the first
   refusal and answer it. For a 1.13 MB container about 550 calls.
4. **Timeouts for this route only.** After the checks of step 2 pass, the child resets its alarm
   to `HTTP_UPLOAD_ALARM_S` (proposed 180 s); the per-`recv` 10 s stays; before `UPDATE_END` it
   calls `bk_set_timeouts(5, 60)` (`src/lib/client.c:26-32`, per process, so per child).
5. **The answer.** `UPDATE_END`'s verdict as JSON: `{"ok":true,"slot":"A","version":7}` or
   `{"ok":false,"error":"update","reason":"digest"}` with the reason name (§ 4.6).

`httpd` keeps no image: at most one 2,044-byte piece in its stack.

### 4.2 `brokerd`: three ops and a bounded staging buffer

讀 the three ops are already in the table, unsupported, uid 100 only, session and CSRF required
(`src/brokerd/ops.c:39-51`, the columns named at `:39`; `src/lib/proto.h:64-66`). They become
supported:

- **`UPDATE_BEGIN`** `u32 total`: refuse `INVAL handoff` if `/proc/rlxfw-boot` reads `none`
  (§ 4.4 step 2, fired early so a RAM boot never receives the body); `too_big` if
  `total > 1,179,648`; `short` if `total < 160`; `BUSY` if another session holds a staging. Else
  `malloc` the buffer (`total` bytes), bind it to the session token, reply `OK` with the
  destination letter.
- **`UPDATE_DATA`** `u32 offset` + bytes: same session; `offset == received` and
  `received + n <= total`, else `INVAL sequence` and the staging is **poisoned** (the kernel's
  `D12` rule, `kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:600-607`) until a new
  `BEGIN`.
- **`UPDATE_END`** `u32 total`: `received == total`, not poisoned, then § 4.4.

One staging at a time, discarded after 30 s without a `DATA` (swept in the main loop beside the
connection deadlines, `src/brokerd/loop.c:409-419`). The buffer is `brokerd`'s heap, freed after
`END`: 推
about 2.4 MB at the peak of § 4.4 (staging + one slot read), against 量 `MemFree` 20,924–20,932 kB
on an earlier image (`SPEC.md` `MEM-19`, `MEM-20` — before `R7`'s userspace, so 推 for `v1.0`). The
`/run` and `/tmp` ramfs is not used, so its being unbounded (`docs/known-issues/v1.0.md:78`)
does not reach this path.

### 4.3 `rlxboot`'s own code, in `brokerd`

The DoD asks for `rlxboot`'s checks in `rlxboot`'s order with no second implementation. 讀
`container.c` was written to build anywhere: nothing in it touches hardware, allocates or recurses
(`src/rlxboot/container.h:49-53`), and it already builds three ways —

- for the device, `-ffreestanding -O2 -Werror` by the rsdk gcc 3.4.6 (`src/rlxboot/Makefile:101-107`,
  `:238-241`);
- for the host, gcc-13 and clang-18 at `-Werror`, and under ASan/UBSan
  (`src/rlxboot/test/run-host-tests.sh:27-28`, `:40-63`, `:79`);
- **as a Linux user-mode program by the same rsdk gcc, statically linked against uClibc**,
  big-endian, run under `qemu-mips-static` (`src/rlxboot/test/run-qemu-tests.sh:3`, `:21-25`,
  `:48-68`: `container.c`, `slots.c`, `sha256b.c`, `ed25519.c`, `sha512.c`).

That third build is `brokerd`'s situation exactly: the toolchain is the one the userspace build
names (the root `Makefile:95-96`; `brokerd`'s target build, `src/brokerd/Makefile:281-295`,
`:350-356`). So `brokerd` links the five files unchanged. Four things differ, each a `Makefile`
matter and none an edit to a `BUILD_ID` input:

- `brokerd`'s flags are `-Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow -static
  -fno-builtin -fno-strict-aliasing -fno-common` (`src/brokerd/Makefile:288-289`); 推 the files
  that compile clean at `-O2 -Werror` under the same gcc (`rlxboot`'s payload) do at `-Os`; the
  first build settles it.
- `ed25519.c` needs its one exemption, `-Wno-sign-compare` (`src/rlxboot/Makefile:127-134`), and
  `brokerd`'s target loop compiles every source with one flag set (`src/brokerd/Makefile:350-356`).
- `src/rlxboot/container.c:75` includes `"../lib/ed25519.h"`, and `brokerd`'s target build stages
  its sources flat (`src/brokerd/Makefile:308-315`): the staging keeps `rlxboot/` and `lib/` as
  directories.
- `brokerd` defines neither `ED25519_SIGN` nor `ED25519_KEYGEN`, and a gate reads the artefact for
  a signer, as `rlxboot`'s does (`src/rlxboot/Makefile:308-314`).

The production key is the same file `rlxboot` compiles in, `src/rlxboot/prodkey.h` (public key
`4a6eda72…096e`), never a copy. The host build of `brokerd` uses the development key, as
`rlxboot`'s host tests do.

### 4.4 `UPDATE_END`: the checks, in order

1. **staging** complete and not poisoned — else `incomplete`/`sequence`;
2. **handoff**: `/proc/rlxfw-boot` reads `slot X ver N` — else `handoff`;
3. **counter** from flash: the 512 bytes at `0x3F0000` through `/dev/mtd2ro`, decoded by
   `rlxu_counter_from_bitmap` (`src/rlxboot/container.c:180-207`) — `rlxboot`'s function, not a
   copy;
4. **the counter has caught up**: `ctr >= N`, else `ctr_behind` (the boot's advance, § 5, has not
   run yet; retry). With it, step 8 compares against a counter at least the running version, so a
   validly signed container below it is refused by name as `rollback` — the DoD's reason — and
   not later as `would_not_boot`;
5. **both slots from flash**, each read as `rlxboot` reads it — the 160-byte header first, the rest
   only if it begins `RLXU` and its length fits (`src/rlxboot/slots.c:182-198`) — into one reused
   buffer, and verified by `rlxu_verify` with `rlxboot`'s own environment: RAM
   `0x80000000`–`0x82000000`, the stage-2 window, the slot's own RAM buffer and base, form `WHOL`
   (`src/rlxboot/slots.c:169-173`, `src/rlxboot/main.c:382-411`, `src/rlxboot/rlxboot.h:33-36`,
   `:74-78`), the counter of step 3, the production key. One deliberate difference: `rlxboot`'s own
   range comes from its linker symbols (`src/rlxboot/main.c:384-385`), which `brokerd` cannot see,
   so `brokerd` uses `0x81800000`–`0x818FFFFF` (`notes/update-chain.md:102-105`), a superset —
   stricter, never looser. **Fallback, taken only on a measured timeout**: if `UPDATE_END`'s time
   on the die (§ 9 item 6) does not fit the deadline of § 4.1 step 4, the destination slot — the
   one about to be overwritten, whose verdict only feeds step 6 — is checked by header and
   signature only (steps 1–3 of `rlxu_verify`, no payload digest), and the running slot is still
   verified whole. 推 what that gives up is small: an install programs the header page last
   (§ 3.3), so a torn install leaves no valid header, and a valid header over a torn payload needs
   damage after a completed write. The choice is a build constant, never a run-time one;
6. **cross-check**: `rlxb_choose` (`src/rlxboot/slots.c:223-235`, linked, not restated) over the two verdicts
   must name slot `X` at version `N` — else `handoff_mismatch`. This is the DoD's *"checked against
   both slots' flash contents"*: the slot `rlxboot` says it booted must be the slot `rlxboot` would
   boot from what is in flash now;
7. **destination** = the other slot (the DoD's rule; and § 2.5's fence refuses the running one in
   the kernel too);
8. **the upload** through `rlxu_verify` with `write_at` = the destination's base, `write_form` =
   `WHOL`, the destination's RAM buffer, the counter of step 3 — rlxboot's steps 1–5 in rlxboot's
   order (`src/rlxboot/container.c:233-408`; `notes/update-chain.md:99-108`);
9. **would it boot**: `rlxb_choose` with the upload's verdict in the destination and the running
   slot's in its own must choose the destination — else `would_not_boot` (a tie boots A,
   `src/rlxboot/slots.c:228-229`, so an equal version written to B would never run). An addition
   to `rlxboot`'s checks, after them, refusing only;
10. `OK`: reply `dest`, `version`, set `pending_update` — the install runs after the reply is on the
    socket, as `REBOOT` does (`src/brokerd/ops.c:772-779`, `src/brokerd/loop.c:266-289`,
    `:308-325`).

**Nothing is staged for flash before step 10.** Steps 1–9 read flash and `/proc`, and write
neither; the host suite asserts that every refusal leaves the stub `/proc` directory with no
`img`, `arm` or `install` write (§ 4.8).

### 4.5 After the reply: stage, arm, install, compare, reboot

1. Take the flash lock and **keep it until `reboot(2)`**, so a `cfgstore` write cannot start in the
   last second and be cut by the reboot.
2. `disarm`, `img reset`; write the container in 4,096-byte `write(2)`s. **`FW-248`**: 量 when the
   host's sender reported done, a read of `img_len` on the device still came short, and complete
   about 7 s later; 推 the mechanism, the host's sender counting bytes once they were in its
   socket buffer while the device's `nc` still drained them (`notes/spi-mtd-driver.md:1860-1867`).
   Here the writer is the only writer (the lock) and each `write(2)` returns after
   `copy_from_user` under the mutex
   (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3192-3224`), so 推 `img_len` is final
   when the last call returns. It is still read back — `img_len` equal to the staged length,
   `img_err none` — before the arm, and the install's `sha=` is the last net (`:2707-2717`;
   `notes/spi-mtd-driver.md:1864-1865`: "an early read costs a refusal, never a wrong write").
3. `arm <base> <base+0x120000> 0x120000`; `install slot<X> sha=<sha256 of the staging>`.
4. Read `/proc/rtl819x-spi`: `inst_reason OK`, `inst_cmp_ok 1`, `inst_cmp_diff 0`, `n_writes`
   moved by `288 + ⌈len/256⌉`
   (`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h:863-864`; 量 `FW-246`: 4,621
   for 1,109,152 B).
   Log one console line: `brokerd: UPDATE slot <X> written: <inst_reason> cmp_diff <d> n_writes +<k> ms <t>`.
5. `img reset`, `sync()`, `sleep(1)`, `reboot(RB_AUTOBOOT)` — 讀 a watchdog bite:
   `kernel_restart` → `bsp_machine_restart` sets `WDTCNR = 0` and spins (`src/init/main.c:380-382`);
   量 the same syscall from `busybox reboot -f` resets this board (`FW-37`). 推 for `brokerd`'s own
   call, which no capture has.
6. On any failure in 2–4: log it, release the lock, **do not reboot** — the running slot is
   untouched, `rlxboot` would refuse a torn destination and boot it anyway, and the next upload
   starts with `img reset`.

### 4.6 Each refusal the DoD names, where it fires

| case (`P6r-10`) | container | fires at | reason | `n_writes` |
|---|---|---|---|---|
| a payload bit flipped | U with one payload bit flipped | `rlxu_verify` step 4, `src/rlxboot/container.c:375-383` | `digest` | unchanged |
| a header bit flipped | U with bit 0 of byte 28 flipped — the digest field (`src/rlxboot/container.c:260`), which no step-2 bound reads (`:255-363`), so step 3 is the first to fail; 讀 `t_container`'s *"a flipped digest bit (signature covers it)"* is the same case (`notes/rlxboot.md:397-399`) | step 3, `src/rlxboot/container.c:369-371` | `sig` | unchanged |
| signed for the running slot | V (`flash_at 0x190000`) while V runs from B | step 2, `src/rlxboot/container.c:329-332` | `flash_match` | unchanged |
| the development key | `mkfw2 build --dev-seed`, `--flash-at 0x070000 --flash-form whole`, version ≥ the counter | step 3 | `sig` | unchanged |
| booted from RAM through the loader | any | `UPDATE_BEGIN` (§ 4.2) and again at `END` step 2 | `handoff` | unchanged |
| below the counter (`P6r-11`) | T (`v1.0`'s release asset: version 5, slot A) with the counter at 6 | step 5, `src/rlxboot/container.c:401-403` | `rollback` | unchanged |
| a body larger than a slot | — | `httpd`'s header line, before `BEGIN` | `413` | unchanged |

Each also prints `brokerd: UPDATE refused: <reason>` on the console. That line is a mark, not the
gate: the round's images keep the bench shell (§ 6.2), and the card gates on
`/proc/rtl819x-spi` — `n_writes` and the `inst_*` fields — read before and after each upload
(`CLAUDE.md` § At the bench: a `/proc` field, never a console mark).

### 4.7 Timings, every one 推

Upload: about 550 broker calls, each with § 3.5's ≤ 8 ms reload — about 5–8 s with the LAN
transfer. `UPDATE_END`: two slot reads (≤ 2.2 s at `FW-48`'s rate), three SHA-256 over about
1.1 MB and three Ed25519 (`rlxboot` spends about 1.3 s a slot on this core with the window read,
量 `FW-250`) — about 4–6 s, inside the 60 s of § 4.1 step 4. Install 10.3–11.2 s (量 `FW-246`).
From `busybox reboot -f` to the mainline's prompt about 15.6 s (量 `FW-250`, `F05`), and
`rlxfw: lan up` comes before the prompt (`src/init/main.c:627`, printed from `lan_up()` before the
child table starts). From the upload's first byte to `lan up`, about 35–45 s: the DoD reads it
from the captures, between `brokerd: UPDATE_BEGIN` and `rlxfw: lan up`.

### 4.8 Host tests

`src/brokerd/test_update.c`, with a 4 MiB file standing in for `/dev/mtd2ro` (slots and a bitmap
made by `mkfw2.py` with the development seed) and a stub `/proc` directory recording every write:
`BEGIN` without a session `AUTH`, wrong CSRF `PERM`, uid 101 `PERM`, handoff `none` `INVAL
handoff`; `total` 1,179,649 `too_big`; an out-of-order `DATA` poisons; at `END` each § 4.6 case by
name, plus `ctr_behind`, `handoff_mismatch`, `would_not_boot`; an accepted container produces
exactly `disarm`, `img reset`, the staging writes, the arm line and the install line, in that
order, and **every refusal produces none of them**. `test_authz.c` walks the flipped rows
(`src/brokerd/ops.c:49-51`). `httpd`'s `test_routes`/`test_serve`: no session → `401` with no broker call;
`Content-Length` 1,179,649 → `413`, no call; a stream → `BEGIN`, ⌈n/2,044⌉ `DATA` with offsets,
`END`; an early EOF → no `END`.

## 5. The counter advance

**Who.** A helper PID 1 forks once — not a new program (§ 2.9), not a supervised child (a one-shot
child would read as a fast failure, `src/init/supervise.h:34-38`) — after `lan_up()` has printed
`rlxfw: lan up` (`src/init/main.c:1045-1048`, `:599-637`, the line at `:627`) and the child table
has started `brokerd` (`:829`, `:1078`, `:1118`). PID 1 reaps it like any orphan: 讀 `sv_reap_all`
ignores a pid not in the table (`src/init/supervise.c:215-218`). In a `RLXFW_SWITCH_BRINGUP=0`
build there is no `lan up` and no helper.

**How "up" is decided.** The DoD's two conditions: `lan up` printed — the helper exists only after
it — and `brokerd` answering: a `STATUS` through the broker socket as root (`bk_call`,
`src/lib/client.c:94-209`; `init` links `client.c` and `proto.c`), retried every 500 ms for up to
60 s.

**What it does.** Read `/proc/rlxfw-boot`:

- `none` → print `rlxfw: ctr not advanced: no handoff (not started by rlxboot)`, exit. The
  kernel would refuse anyway (§ 2.4.5).
- `slot X ver N` → take the flash lock, write `ctr N`, read `ctr_*` back, print
  `rlxfw: ctr 0 -> 6 OK pp=6` (or `SAME`, or the refusal), release, exit.

If `brokerd` never answers, nothing advances and the older slot stays bootable — the
availability side of *"only after up"*. A build switch `RLXFW_CTR_ADVANCE` (default 1) lets the
stop-loss path ship persistence alone (`P6r-10`'s stop-loss) without the counter write.

**Why eager, at boot, and not at the next update.** Advancing inside the update path (when an
upload begins) also satisfies "only after up", and it would keep the cut rounds of § 6.5 from
advancing anything. Rejected because the advance would then be a write made while handling a
request that may be refused, and the DoD requires every refused upload to leave `n_writes`
unchanged; at boot, the write happens once per new version and never inside an upload.

**What it costs, said plainly (`P6r-11`'s most-likely-wrong).** The first boot of V advances the
counter to 6, after which T — `v1.0`'s image, version 5 — never boots from flash again; from then on,
after every successful update the other slot holds an image below the floor, so the device has one
bootable slot until the next update writes the other. A torn update never writes the running slot
(§ 2.5, § 4.4 step 7), so it cannot leave neither slot valid; the bench recovers anything else
through the loader's RAM boot.

## 6. The order of flash writes for the card

### 6.1 The bootstrap

A first ordering put the update test (container U, version 6, slot B, through `httpd`) right
after the store regions. 讀 the image that runs then cannot take it: slot A holds T, `v1.0`, built
with `CONFIG_MTD_RTL819X_WRITE=n` (`docs/known-issues/v1.0.md:32-36`), whose `brokerd` answers
`NOTSUP` to `UPDATE_*` (`src/brokerd/ops.c:49-51`) and whose `httpd` answers `501`
(`src/httpd/routes.c:1018-1029`). So
the first image with an update path reaches a slot through the console install path, from RAM —
a payload the list does not name. The numbering below follows from that: **V**, version 6, slot B,
installed from the console; **U**, version 7, slot A, installed through `httpd`. U must differ
from V in `config/`, or both print the same `RLXFW-ID0` (`docs/known-issues/v1.0.md:26-31`).

### 6.2 The images

| image | how it runs | for |
|---|---|---|
| `8dce09c5` (armed, `v1.0`'s kernel, has `nc` and the `rlxboot`/`rescue`/`slotB` regions) | RAM, through the prompt | W1, W2 |
| **V** (v6, slot B) and **U** (v7, slot A): the bench build of the P6r-10 tree (`BENCH_SHELL=1`) | flash, through `rlxboot` | the round; the card reads `/proc` and runs `cfgstore` |
| V-armed (V's tree, `nc`, no `mtd` nodes) | RAM | K1 |

Every update and counter write in the round is issued by a daemon — the upload through `httpd`
and `brokerd`, the counter advance by `init`'s helper — so the round shows those two working with
no shell command even on a bench image. The round's store writes (W4, W5, K2) and the erases
(W8, W9) are typed at the bench image's shell; in normal operation the store's writes are
`brokerd`'s (§ 3.8). The shell is otherwise used to read results. The shell-less build of the same
tree is another image with the same `RLXFW-ID0` (`docs/known-issues/v1.0.md:26-31`).

### 6.3 The writes

Precondition: **`P5e-6` filmed** (T booting from slot A under build `127a71cf`). Each destination
pre-read before its write (`CLAUDE.md` § Flash; `map` digests from the image, never bytes). Every
row needs the owner's dated `owner-yes` naming what the column says.

| id | what | region | how | the yes names | `n_writes` |
|---|---|---|---|---|---|
| W1 | new `rlxboot` (`cs6c`) | `rlxboot` `0x010000` | `8dce09c5` from RAM: `install rlxboot sha=…` | the `cs6c` image's sha256 | 16 + ⌈len/256⌉ (89 for 18,642 B, 量 `FW-246`) |
| B1 | cold boot | — | — | — | `RLXBOOT-V1 build=<new>`, `FROM 05010000`, A ok ver=5, B ok ver=4, `SLOT A`, `HANDOFF slot=A ver=5`; T runs, `RLXFW-ID0=9BB2BEC7`, `lan up` |
| W2 | V | `slotB` `0x190000` | `8dce09c5` from RAM, `nc` staging, `install slotB sha=…` | V's sha256 | 288 + ⌈len/256⌉ |
| B2 / W3 | cold boot; counter 0 → 6 | state `0x3F0000` | `init`'s helper | a category: region the state block, operation `ctr 6`, bound 6, issued by V (V's sha256) — six one-byte programs at `0x3F0000`, values `7F 3F 1F 0F 07 03` | +6 |
| B3 | warm reboot | — | `busybox reboot -f` | — | `RLXBOOT-VER cur=5 ctr=6 bad`, `VERDICT A bad=rollback`, B ok ver=6 `ctr=6`, `SLOT B` — **D21 settled and the `rlxboot` half of the rollback refusal**, with T as the container |
| W4 | defaults record, seq 1 | `cfg0` | `cfgstore init --force` | the record's sha256, computed by the host build of `cfgstore` | +32 |
| W5 | the disposable password, seq 2 | `cfg1` | `cfgstore passwd` (§ 6.4) | a category: region `cfg1`, 4,096 B, operation `cfgstore passwd`, bound seq 2, issued by V (V's sha256), a salted record (§ 0.2 item 1) | +32 |
| C1 | cold power cycle | — | — | — | `cfgstore show`: `source slot1 seq 2`; `/api/status`: `cfgsrc 2 cfgseq 2`; `/api/login`: the password `200`, another `401` |
| R1–R5 | refusals: T, V, dev-key, U payload flip, U header flip | — | `httpd` | — | each its reason (§ 4.6), `n_writes` read before and after: unchanged |
| R6 | V from RAM through the loader; upload U | — | `httpd` | — | `/proc/rlxfw-boot none`; helper: not advanced; `handoff`; unchanged |
| W6 | U | `slotA` `0x070000` | `httpd` (§ 4) | U's sha256 | 288 + ⌈len/256⌉; `RLXFW-SI-END OK … cmp=1` |
| B4 / W7 | watchdog reset; counter 6 → 7 | state | `init`'s helper | a category: region the state block, operation `ctr 7`, bound 7, issued by U (U's sha256) — one byte at `0x3F0000`, value `01` | +1; A ok ver=7, B ok ver=6, `SLOT A`, `RLXFW-ID0=<U>`; slot B's `map` digests unchanged; upload → `lan up` from the captures |
| K1–K3 | the cut rounds | § 6.5 | | | |
| W8, W9 | `erase cfg1`, then `erase cfg0` | `cfg1`, `cfg0` | console, each under its arm | the erase of that region | +16 each |

The `W`, `B`, `C`, `R` and `K` ids are this note's own; the card numbers its cells.

🔄 2026-10-23, ruled (1B's item 8): no install has issued a one-byte `PP` on this die — the tail
path of `pp_page` with no full word before it, which is every program `ctr` makes; 1B read the
vendor's `ComSrlCmd_ComWrite` for a one-byte write and found the same register sequence. So the card
runs `ctrloop` on the probe block (`0x3E0000`) before the first `ctr` on the state block, which in
the table above is `B2`/`W3`: a one-byte-`PP` defect then shows on scratch, never at `0x3F0000`.

### 6.4 The password a card sets (ruled 2026-10-23; the DoD as amended)

讀 `tools/console-capture.py` writes every `--send` into the committed `.meta.json` as `sent` and
`sent_hex` (`tools/console-capture.py:518-519`, `:761-762`), and `cfgstore passwd` leaves the
tty's echo on — it only prints a prompt when `isatty` (`src/cfgstore/main.c:592-593`) — so the
password would also be in the capture's text.

**Chosen: a disposable password, declared on the card and its publication accepted by the owner
in writing, which the same seating destroys.** The card's last writes are W8 and W9 (§ 6.3), which
leave both store regions erased: no hash, every login refused — that is also the DoD's *"both
erased … every login refused"*, so the destruction is a measured step with its own reading
(`/api/login` with the published password → `401`). The unit's working password is then set off
card by the owner, at the console — the shell-less image's first-password step, or
`cfgstore passwd` on a bench image — and never passes through a tool that records. No browser can
set it: with no stored hash every `LOGIN` answers `AUTH` (§ 3.6) and `PWSET` is root-only (§ 3.8),
so no session exists to reach `/api/password`. One tool change: `cfgstore passwd` and the
first-password step turn echo off on a tty. The password a card sets still reaches `.meta.json` as
`sent`/`sent_hex`, which is why it is disposable.

The alternative, not taken, is a digest-only send. It needs two more changes and a control, and is
the better choice only if a card must ever use the working password: `console-capture.py` gains a
mode that reads the secret from a file outside the repository and records only its sha256; and a
control sends a canary through both paths into a loopback that echoes, then searches every file
the tool wrote (`.log`, `.timing`, `.meta.json`) for the canary and its hex: the normal path must
find it (the search can see), the digest-only path must find 0. Host cells that log in
(`/api/login`) need the same treatment.

### 6.5 The cut rounds (`P6r-11`), each followed by a cold boot read to its verdict

| id | write cut | how | why there, and why it is safe | verdict |
|---|---|---|---|---|
| K1 | an unpaced slot write, the kind an update makes | V-armed from RAM, V staged by `nc`, `install slotB sha=<V> repeat=5` (≈ 55 s); the owner pulls inside the window | no scratch region is slot-sized (§ 0.2 item 3); slot B is the non-running slot and V is below the floor (7), so B never wins whether torn or whole | `SLOT A` every time; `VERDICT B bad=magic`/`digest` (torn) or `bad=rollback` (complete) says which; the phase from the last `RLXFW-SI` line |
| K2 | a store write | on U from flash: `i=0; while [ $i -lt 100 ]; do cfgstore set sys.hostname=h$i; i=$((i+1)); done` (≈ 70 s, 推) | the store's own criterion needs a cut inside a real store write; by design a write touches only the slot not selected (`src/lib/cfg.c:804-805`) | `cfgstore show`: `seq` = the last `written: … seq S` captured, or S+1; never `default`; the phase from the last `RLXFW-SI` line |
| K3 | a counter advance | on U: `arm 0x3e0000 0x3f0000 0x10000`, `ctrloop 30` (≈ 60 s, 推) | a one-bit program lasts about 0.5 ms; the routine is § 2.4's | `ctrloop show` twice: `malformed=0` unless the last line was `erase`; `value` within the 256 bits after the last `bit=` line; the two reads differ by ≤ 1 |

K2's 100 records each carry the hash W5 set, salt included (§ 0.2 item 1), so none of them can be
computed before power: K2 is named as a category — regions `cfg0` and `cfg1`, operation
`cfgstore set sys.hostname=h0` … `h99`, bound seq 3 … 102, issued by U (U's sha256). K1's yes
names V's sha256 and the count 5; K3's names the region `probe`, the passes and U's sha256. K2's
flash writes are made by `cfgstore` on the device, not by a verb its `--send` names, which is the
boundary `cardcheck` cannot see past (`notes/spi-mtd-driver.md:1742-1745`); the card declares
them, and `cardcheck` learns that form (§ 2.9).

## 7. Threat-model deltas (`docs/threat-model.md` §§ 3, 9, 10)

**`T2`, a LAN peer with valid credentials (§ 3).** Gains the update path: it can install any
container the owner's key signed whose version is at or above the counter, into the slot not
running. It cannot install a downgrade (the counter, § 4.4 step 8; and `rlxboot` at boot), a
container for the running slot (`flash_match`, the fence), or anything unsigned. New: its
configuration changes and a password it sets now **persist** — on `v1.0` a reboot left no
password at all (`docs/known-issues/v1.0.md:36-38`); now a stolen session can lock the owner out
until a console act. Also new: flash wear by repeated updates (288 sector erases of the other slot
per update) and a few seconds of `brokerd` per `UPDATE_END`; a per-boot rate limit on `UPDATE_END`
is cheap and not in this design. Unchanged and worse in weight: no TLS, so the session cookie and
the container cross the LAN in clear (`P6r-12`).

**`T8`, a malicious or corrupt update image (§ 9).** From "bounded for the verification half only"
(`docs/threat-model.md:58`) to: verified twice — by `brokerd` with `rlxboot`'s own code before any write, by `rlxboot` at
boot — and the rollback half read from flash once the counter moves (§ 6.3 B3). The kernel's
install path still does not verify signatures (`D7`,
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:2269-2273`), so the write is
authorised by `brokerd`'s verdict alone, and root can stage anything (`rlxboot` refuses it at
boot). The handoff can be forged only by code that runs before the kernel, a position that already
writes flash (§ 1.6). A key compromise is total, as before.

**`T9`, a peer that already holds a uid (§ 10).** uid 100 (`httpd`, if taken over) reaches the
update ops only with a session token, as `T2`; it cannot open `/proc/rtl819x-spi` for writing
(0644), `/proc/rtl819x-spi-img` (0200; both
`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c:3498`, `:3529`), `/dev/mtd2ro` (0400) or
`/run`'s lock (🔄 2026-10-23: nor read `/proc/rtl819x-spi-inst`, 0400, `:3539`), and inside its
chroot it sees none of them (`src/httpd/serve.c:155-209`). uid 101 unchanged. **Root** gains a flash write
path one `echo` away: every region the shipped table names — with § 2.1's shrink, the slots, the
store regions and the probe, not `rlxboot` or the rescue — and the counter only to the booted
version (§ 2.4.5). ⚠️ Root keeps the vendor's route regardless: the image holds `mtd_spi_write`
and `mtd_spi_erase` on the vendor's partitions (`docs/known-issues/v1.0.md:73-76`), and a root
process can create a writable node and a program to drive it, so **burning the counter to 4,096,
erasing both slots, or rewriting `rlxboot`** — every update refused, or a bench recovery — stays
within root's reach; `T9` has to say so. The loader and `H601` stay outside every rlxfw verb
(`kernel/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h:131-132`, checked on every
operation).

## 8. What this design does not establish

- That any of it runs on the die: nothing here was built or measured; every timing is 推 (§ 4.7).
  🔄 2026-10-23: §§ 1–2 are built and gated at the desk (`SPEC.md` `FW-264`, `FW-267`); none of it
  has run on the die, and the chain `rlxboot` → `rtkload` → kernel has not run even in emulation.
- That the vendor toolchain assembles the patch as the host's binutils did, or that `start.o` is
  first in the link; the artefact gate (§ 1.3) reads both. 🔄 2026-10-23: 量 on the first build,
  both as designed (§ 1.3).
- What the loader's `J` leaves in a0–a3 (§ 1.6).
- That a page programmed one bit at a time 2,048 times between erases reads back right on this
  part: the datasheet is not in hand (`FW-191`); `ctrloop` measures the scratch block, not the state
  block (§ 9 item 4).
- A cut inside a chosen sub-phase, the state block's own behaviour under a cut, or the counter past
  the values the seatings write — `P6r-11`'s own list.
- That the upload is secret (no TLS), or resistant to root (§ 7).
- That `brokerd`'s 2.4 MB peak fits on `v1.0`'s userspace: `MEM-19`/`MEM-20` predate it.
- That an update from the WAN side works (`P6r-9`).
- That the headroom table is right: it is a guess to be refuted by the first build (§ 2.9).
  🔄 2026-10-23: refuted for the kernel side, which took 14 steps (§ 2.9); the userspace rows wait
  for their build.

## 9. Open questions only a measurement settles

1. The handoff end to end: `/proc/rlxfw-boot` after a slot boot by the new `rlxboot` (B2), after a
   rescue boot (`none why=magic`), after a RAM boot (R6).
2. What the loader's `J` leaves in a0: the `none` line's `a0=` at R6 (for
   `docs/loader-command-semantics.md` § d).
3. Whether `rlxboot` reads the counter through `0xBD3F0000` at all — D21's 推: the kernel's PIO
   read-back says 6 (W3) and `rlxboot` prints `ctr=6` (B3), two readings of one byte by two paths.
4. Repeated partial programming: `ctrloop`'s read-back of every bit across N passes, and a marginal
   bit after a cut read twice (K3).
5. `brokerd`'s reload cost per request on flash, before deciding § 3.5's cache (STATUS latency
   before and after).
6. `UPDATE_END`'s time with userspace SHA-256 and Ed25519 on the 4181 (R1–R5, W6).
7. A store write's duration and `n_writes` +32 (W4).
8. The image's actual growth against § 2.9 (the first build). 🔄 2026-10-23: the kernel's is 14
   steps, 53 left (§ 2.9, `FW-267`); the userspace's is open.
9. `MemFree` on V with `brokerd` holding a staging (W6).
10. The time from the upload's first byte to `lan up` (W6/B4).
