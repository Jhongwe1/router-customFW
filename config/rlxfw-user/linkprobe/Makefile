# config/rlxfw-user/linkprobe/Makefile -- builds `linkprobe`, R6b-6's caller of
# the three ethtool ops `rtl819x-nic` has carried since 1.3.
#
# The shape is config/rlxfw-user/isaprobe/Makefile's, and that file owns the
# reasons this one repeats without restating: why the source is staged onto
# ext4 first (the rsdk driver is a 32-bit i386 ELF, and every DrvFs path
# returns EOVERFLOW to its stat()), why breaks are counted by opcode, and why
# exactly two of them inside `__GI_abort` is a bound and not a waiver.
#
# Run it under tools/vendor-tripwire.sh from a scratch directory, as every
# other use of the rsdk binaries is:
#
#     tools/vendor-tripwire.sh -- make -C <repo>/config/rlxfw-user/linkprobe
#
# ---------------------------------------------------------------------------
# WHAT IS DIFFERENT FROM uprobe, AND WHY
# ---------------------------------------------------------------------------
#
# One C file and no assembly, so there is no `.set noreorder` question and no
# generated payload to check (no G0-emit, no G3).  What it adds is about the
# ABI and about the bytes the image carries:
#
# G5  the linked ELF and the stripped binary hold the bytes `rtl819x` ZERO
#     times.  linkprobe prints the driver name the kernel hands back; if the
#     name were in the binary, a line saying `driver "rtl819x-nic"` could have
#     come from this program.  It also keeps the image's `str:` witnesses
#     (config/rlxfw-marks.tsv MK9, MK10) from being satisfied by this file,
#     which sits in `.init.ramfs`.  A guard against an accident, not an
#     adversary: a string assembled at run time passes it.  Its counter is
#     shown firing on a control file first.
# G6  the ABI, two sources: the three struct regions, the ETHTOOL_G* and
#     BUSINFO_LEN defines, SIOCETHTOOL, EOPNOTSUPP/ENODEV and
#     __NR_clock_gettime/__NR_Linux must be byte-identical between the
#     kernel tree (KTREE) and the toolchain's userspace headers.  KTREE
#     defaults to the drop every stage copies: 量 2026-09-26, the six headers
#     are byte-identical between the drop and the staged `r6b2q2` tree, and a
#     cell tree is deleted by the next build of that cell.  `make
#     KTREE=<cell>/top/linux-2.6.30` re-runs it on a staged tree.  An absent
#     KTREE REFUSES; it never skips.  The comparison is shown finding a
#     difference first (drvinfo against ringparam).
# G7  no `-march` in CFLAGS at all -- so never `-march=mips32`, whose exposed
#     load delay slot miscompiles silently -- the linked ELF's e_flags equal
#     uprobe's, read from uprobe's ELF at build time and never typed here, and
#     there is no PT_INTERP.
#     🔴 NOT BIT FOR BIT, and the proposal said bit for bit.  量 2026-09-26,
#     the first build: linkprobe 0x1007 (noreorder, pic, cpic, o32, mips1)
#     against uprobe 0x1005 (noreorder, cpic, o32, mips1).  The one bit is
#     EF_MIPS_PIC, and it follows from what is linked: uprobe and ucost link a
#     hand-written non-PIC `.S` (both 0x1005, both with the link warning
#     "linking PIC files with non-PIC files"), while linkprobe and iperf3 are
#     C only (both 0x1007, no warning).  So bit 1 is masked and every other
#     bit -- the arch field, the ABI, noreorder, cpic -- must be equal; the
#     masked comparison is shown refusing a changed arch field first.  And G4
#     reads "the link printed nothing" rather than uprobe's "exactly the one
#     known warning", for the same measured reason.
#
# The compile-time half of the ABI is in linkprobe.c itself: sizeof and
# offsetof of every field it reads, and the four request numbers, are
# asserted, so a header that drifted fails the compile.

SHELL      := /bin/sh
HERE       := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO       := $(abspath $(HERE)../../..)

FWRE_WORK  ?= /home/key/fwre-work
STAGE      ?= $(FWRE_WORK)/rebuild/rlxfw-user/linkprobe
SRC        := $(STAGE)/src
OBJ        := $(STAGE)/build
INSTALL    ?= $(REPO)/build/rlxfw-user/linkprobe

TCROOT     ?= $(FWRE_WORK)/rebuild/src-vendor/rtl819x-toolchain/toolchain
TC         ?= rsdk-1.3.6-4181-EB-2.6.30-0.9.30
TCBIN      := $(TCROOT)/$(TC)/bin
TCINC      := $(TCROOT)/$(TC)/include

CC         := $(TCBIN)/mips-linux-gcc
OBJDUMP    := $(TCBIN)/mips-linux-objdump
READELF    := $(TCBIN)/mips-linux-readelf
STRIP      := $(TCBIN)/mips-linux-strip
NM         := $(TCBIN)/mips-linux-nm

KTREE      ?= $(FWRE_WORK)/rebuild/src-vendor/rtl819x-toolchain/linux-2.6.30
UPROBE_ELF ?= $(FWRE_WORK)/rebuild/rlxfw-user/isaprobe/build/uprobe.elf

HAZLINT    := $(REPO)/tools/hazlint
PYTHON     ?= /usr/bin/python3

# The two inputs that decide the artefact.  The board prints this digest on
# its LP0 line, so a capture names a build rather than echoing a typed name.
IN_NAMES   := linkprobe.c
BUILD_ID   := $(shell cat $(HERE)linkprobe.c $(HERE)Makefile 2>/dev/null | sha256sum | cut -c1-16)

# -Os -static -fno-builtin for uprobe's reasons, and NO -march: the rsdk
# driver's default is the 4181 core (G7).
CFLAGS     := -Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
              -fno-builtin -fno-strict-aliasing -fno-common \
              -DLP_BUILD_ID='"$(BUILD_ID)"'
LDFLAGS    := -static

ELF        := $(OBJ)/linkprobe.elf
BIN        := $(OBJ)/linkprobe
OUT        := $(INSTALL)/linkprobe

.PHONY: all stage gate install show dis clean
all: install

# ---------------------------------------------------------------------------
# G0  stage onto ext4, then prove the copy is the source
# ---------------------------------------------------------------------------
stage:
	@mkdir -p $(SRC) $(OBJ)
	@cp -f $(HERE)linkprobe.c $(SRC)/linkprobe.c
	@a=$$(sha256sum $(HERE)linkprobe.c | cut -d' ' -f1); \
	 b=$$(sha256sum $(SRC)/linkprobe.c | cut -d' ' -f1); \
	 [ "$$a" = "$$b" ] || { echo "REFUSED: the staged copy is not the source"; exit 1; }
	@echo "staged linkprobe.c to $(SRC), hash equal to the repo's"

$(OBJ)/linkprobe.o: stage
	@echo '--- gate G7a: no -march in CFLAGS ---'
	@case " $(CFLAGS) " in *" -march="*) \
	   echo "REFUSED: CFLAGS carries a -march; this build takes the driver's 4181 default"; exit 1 ;; \
	 esac; echo "no -march in CFLAGS"
	$(CC) $(CFLAGS) -c $(SRC)/linkprobe.c -o $@

$(ELF): $(OBJ)/linkprobe.o
	$(CC) $(LDFLAGS) -o $@ $(OBJ)/linkprobe.o 2>$(OBJ)/link.log; rc=$$?; \
	 cat $(OBJ)/link.log; exit $$rc

# ---------------------------------------------------------------------------
# The gates.  The product does not exist unless every one passes.
# ---------------------------------------------------------------------------
gate: $(ELF)
	@echo '--- gate G1: break count over our object, BY OPCODE ---'
	@n=$$($(PYTHON) $(REPO)/tools/elfops.py count $(OBJ)/linkprobe.o --ops break --quiet | sed -n 's/^  break *//p'); \
	 echo "break linkprobe.o=$$n"; \
	 [ "$$n" = "0" ] || { echo "REFUSED: a break in code this project wrote"; exit 1; }
	@echo '--- gate G1b: the LINKED ELF, and every break in it named ---'
	@$(PYTHON) $(REPO)/tools/elfops.py where $(ELF) --op break > $(OBJ)/breaks.txt; \
	 n=$$(sed -n 's/^break *//p' $(OBJ)/breaks.txt); \
	 lo=$$($(NM) -S $(ELF) | awk '$$4=="__GI_abort"{printf "%d", strtonum("0x"$$1); exit}'); \
	 sz=$$($(NM) -S $(ELF) | awk '$$4=="__GI_abort"{printf "%d", strtonum("0x"$$2); exit}'); \
	 echo "linked break=$$n  __GI_abort=[$$lo,+$$sz)"; \
	 [ -n "$$lo" ] || { echo "REFUSED: no __GI_abort symbol to account against"; exit 1; }; \
	 out=0; \
	 for a in $$(grep -oE '^  0x[0-9A-F]+' $(OBJ)/breaks.txt | tr -d ' 	'); do \
	   d=$$(printf '%d' $$a); \
	   if [ $$d -lt $$lo ] || [ $$d -ge $$((lo + sz)) ]; then \
	     echo "  OUTSIDE __GI_abort: $$a"; out=$$((out + 1)); \
	   fi; \
	 done; \
	 [ "$$n" = "2" ] && [ "$$out" = "0" ] || { \
	   echo "REFUSED: expected exactly 2 breaks, both inside __GI_abort"; exit 1; }
	@echo '--- gate G2: hazlint over the linked ELF ---'
	@HAZLINT_CHILD=1 $(PYTHON) $(HAZLINT) $(ELF)
	@echo '--- gate G4: the link printed nothing ---'
	@u=$$(grep -c . $(OBJ)/link.log || true); \
	 echo "link.log lines=$$u"; \
	 [ "$$u" = "0" ] || { echo "REFUSED: the link said something:"; cat $(OBJ)/link.log; exit 1; }
	@echo '--- gate G5: zero `rtl819x` in the ELF, counter shown firing first ---'
	@printf 'x rtl819x y\n' > $(OBJ)/g5-control; \
	 c=$$(grep -a -o 'rtl819x' $(OBJ)/g5-control | wc -l); \
	 e=$$(grep -a -o 'rtl819x' $(ELF) | wc -l); \
	 echo "control=$$c (want 1)  linkprobe.elf=$$e (want 0)"; \
	 [ "$$c" = "1" ] || { echo "REFUSED: the G5 counter cannot see the string"; exit 1; }; \
	 [ "$$e" = "0" ] || { echo "REFUSED: the ELF holds rtl819x"; exit 1; }
	@echo '--- gate G6: the ABI, kernel tree against toolchain headers ---'
	@[ -f $(KTREE)/include/linux/ethtool.h ] || { \
	   echo "REFUSED: no kernel tree at KTREE=$(KTREE); G6 does not skip"; exit 1; }; \
	 [ -f $(TCINC)/linux/ethtool.h ] || { echo "REFUSED: no toolchain headers at $(TCINC)"; exit 1; }; \
	 reg() { sed -n "/^struct $$2 {/,/^};/p" "$$1"; }; \
	 dfn() { grep -E "^#define[[:space:]]+$$2[[:space:]]" "$$1"; }; \
	 same() { if [ -z "$$2" ]; then echo "  $$1: EMPTY"; return 1; fi; \
	          if [ "$$2" = "$$3" ]; then echo "  $$1: identical"; return 0; fi; \
	          echo "  $$1: DIFFERS"; return 1; }; \
	 same "control: drvinfo vs ringparam" "$$(reg $(KTREE)/include/linux/ethtool.h ethtool_drvinfo)" \
	      "$$(reg $(TCINC)/linux/ethtool.h ethtool_ringparam)" \
	   && { echo "REFUSED: G6's comparison calls two different structs identical"; exit 1; }; \
	 bad=0; \
	 for s in ethtool_drvinfo ethtool_value ethtool_ringparam; do \
	   same "struct $$s" "$$(reg $(KTREE)/include/linux/ethtool.h $$s)" \
	        "$$(reg $(TCINC)/linux/ethtool.h $$s)" || bad=1; \
	 done; \
	 for d in ETHTOOL_GDRVINFO ETHTOOL_GLINK ETHTOOL_GRINGPARAM ETHTOOL_BUSINFO_LEN; do \
	   same "$$d" "$$(dfn $(KTREE)/include/linux/ethtool.h $$d)" \
	        "$$(dfn $(TCINC)/linux/ethtool.h $$d)" || bad=1; \
	 done; \
	 same SIOCETHTOOL "$$(dfn $(KTREE)/include/linux/sockios.h SIOCETHTOOL)" \
	      "$$(dfn $(TCINC)/linux/sockios.h SIOCETHTOOL)" || bad=1; \
	 same EOPNOTSUPP "$$(dfn $(KTREE)/arch/rlx/include/asm/errno.h EOPNOTSUPP)" \
	      "$$(dfn $(TCINC)/asm/errno.h EOPNOTSUPP)" || bad=1; \
	 same ENODEV "$$(dfn $(KTREE)/include/asm-generic/errno-base.h ENODEV)" \
	      "$$(dfn $(TCINC)/asm-generic/errno-base.h ENODEV)" || bad=1; \
	 for d in __NR_Linux __NR_clock_gettime; do \
	   same "$$d" "$$(dfn $(KTREE)/arch/rlx/include/asm/unistd.h $$d)" \
	        "$$(dfn $(TCINC)/asm/unistd.h $$d)" || bad=1; \
	 done; \
	 [ $$bad = 0 ] || { echo "REFUSED: the toolchain's ABI is not the kernel's"; exit 1; }
	@echo '--- gate G7b: e_flags equal uprobe'"'"'s but for EF_MIPS_PIC, and no PT_INTERP ---'
	@[ -f $(UPROBE_ELF) ] || { echo "REFUSED: no uprobe ELF at $(UPROBE_ELF) to read e_flags from"; exit 1; }; \
	 f=$$($(READELF) -h $(ELF) | awk '/Flags:/{sub(",","",$$2); print $$2}'); \
	 u=$$($(READELF) -h $(UPROBE_ELF) | awk '/Flags:/{sub(",","",$$2); print $$2}'); \
	 i=$$($(READELF) -l $(ELF) | grep -c INTERP || true); \
	 echo "e_flags linkprobe=$$f uprobe=$$u interp=$$i"; \
	 case "$$f$$u" in *0x*0x*) ;; *) echo "REFUSED: an e_flags word did not parse"; exit 1 ;; esac; \
	 fm=$$(( $$f & ~2 )); um=$$(( $$u & ~2 )); cm=$$(( ($$u ^ 0x10000000) & ~2 )); \
	 [ "$$cm" != "$$um" ] || { echo "REFUSED: the masked comparison cannot see an arch change"; exit 1; }; \
	 [ "$$fm" = "$$um" ] || { echo "REFUSED: e_flags differ from uprobe's beyond EF_MIPS_PIC"; exit 1; }; \
	 [ "$$i" = "0" ] || { echo "REFUSED: a PT_INTERP in a static build"; exit 1; }; \
	 echo "equal with bit 1 (EF_MIPS_PIC) masked; an arch change would be refused"

$(BIN): gate
	cp $(ELF) $@
	$(STRIP) $@
	@e=$$(grep -a -o 'rtl819x' $@ | wc -l); \
	 [ "$$e" = "0" ] || { echo "REFUSED: the stripped binary holds rtl819x"; exit 1; }

install: $(BIN)
	@mkdir -p $(INSTALL)
	cp -f $(BIN) $(OUT)
	@echo "installed $(OUT)  build_id=$(BUILD_ID)"

# Every number a card states about this artefact, printed by its own build.
show: install
	@echo "tc          $(TC)"
	@echo "build_id    $(BUILD_ID)"
	@echo "elf_bytes   $$(wc -c < $(ELF))"
	@echo "bin_bytes   $$(wc -c < $(BIN))"
	@echo "sha256      $$(sha256sum $(BIN) | cut -d' ' -f1)"
	@echo "entry       $$($(READELF) -h $(ELF) | awk '/Entry point/{print $$4}')"
	@echo "flags       $$($(READELF) -h $(ELF) | awk -F'Flags:' '/Flags:/{print $$2}')"
	@echo "interp      $$($(READELF) -l $(ELF) | grep -c INTERP || true)"
	@echo "rtl819x     $$(grep -a -o 'rtl819x' $(BIN) | wc -l)"

dis: $(ELF)
	$(OBJDUMP) -d $(ELF)

clean:
	rm -rf $(STAGE) $(INSTALL)
