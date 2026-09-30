# src/init/Makefile -- rlxfw's PID 1.   R7.
#
# Shape and reasons: config/rlxfw-user/linkprobe/Makefile, which owns them and
# which this repeats without restating -- above all WHY THE SOURCES ARE STAGED
# ONTO ext4 BEFORE THE TARGET COMPILER SEES THEM: the rsdk driver is a 32-bit
# i386 ELF and every DrvFs path returns EOVERFLOW to its stat().  A build whose
# $O is under /mnt/c fails in the linker with no useful message.
#
#   make -C src/init host   O=<abs dir>
#   make -C src/init test   O=<abs dir>                 gcc-13 AND clang-18, both
#                                                       with -fsanitize=address,undefined
#   make -C src/init mutants O=<abs dir>                the two mutation controls
#   make -C src/init target O=<abs dir> TC=<toolchain root> TRIP=<vendor-tripwire.sh>
#
# `O=` is required everywhere: there is no in-tree build, because the tree may be
# on DrvFs and because a stray object under src/ is a file the census counts.
#
# BENCH_SHELL=0 builds PID 1 without the console shell (see init.h).
# LAN_IF / WAN_IF override the interface names.

SHELL      := /bin/sh
HERE       := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SRCROOT    := $(abspath $(HERE)/..)
REPO       := $(abspath $(HERE)/../..)
PROG       := init

ifeq ($(strip $(O)),)
$(error O= is required and must be an absolute directory (never under /mnt/c for a target build))
endif

PYTHON     ?= /usr/bin/python3
BENCH_SHELL ?= 1
LAN_IF     ?=
WAN_IF     ?=

# --- the config loader ------------------------------------------------------
# src/lib/cfg.c is the config store.  `R7-8` deleted src/init/stub/, which stood
# in for it, so an absent src/lib/cfg.c REFUSES rather than falling back.  量
# `R7-8` what the stub had guessed: CFG_NKEYS 16 and the key order were right;
# the eleven CFGE_* numbers were all wrong and one name, CFGE_BOUND, does not
# exist in the real header (it is CFGE_RANGE).  init reads neither, so nothing
# it does changes -- which is why the stub was survivable and also why nobody
# would have noticed.
ifeq ($(wildcard $(SRCROOT)/lib/cfg.c),)
$(error REFUSED: $(SRCROOT)/lib/cfg.c is absent and there is no longer a stub)
endif
CFG_C      := $(SRCROOT)/lib/cfg.c
CFG_INC    := $(SRCROOT)/lib
CFG_WHICH  := src/lib/cfg.c

OWN_SRC    := $(HERE)/main.c $(HERE)/mounts.c $(HERE)/supervise.c \
              $(SRCROOT)/lib/netutil.c
# The real cfg.c needs the rest of the store's translation units; the stub was
# self-contained, which is the one way the swap is not a Makefile one-liner.
CFG_DEPS   := $(SRCROOT)/lib/schema.c $(SRCROOT)/lib/tlv.c $(SRCROOT)/lib/crc32.c
SRCS       := $(OWN_SRC) $(CFG_C) $(CFG_DEPS)
TEST_SRCS  := $(HERE)/test_supervise.c $(HERE)/test_mounts.c

DEFS       := -DRLXFW_BENCH_SHELL=$(BENCH_SHELL)
ifneq ($(strip $(LAN_IF)),)
DEFS       += -DRLXFW_LAN_IF='"$(LAN_IF)"'
endif
ifneq ($(strip $(WAN_IF)),)
DEFS       += -DRLXFW_WAN_IF='"$(WAN_IF)"'
endif

INCS       := -I$(HERE) -I$(SRCROOT)/lib -I$(CFG_INC)

# Where the image manifest looks for the product.  The convention is
# config/rlxfw-user/linkprobe's: $REPO/build/rlxfw-user/<prog>/<prog>, gitignored.
# `mkinitramfs build` REFUSES a `file` row whose source is not there, and
# tools/test-config-gates.sh E5/E6 run it on the real declaration at the desk, so
# this has to exist before the image is built.
INSTALLDIR ?= $(REPO)/build/rlxfw-user/$(PROG)

.PHONY: all host test mutants target target-inner install clean which
all: host

which:
	@echo "cfg loader: $(CFG_WHICH)"

# ===========================================================================
# HOST
# ===========================================================================
HOSTW      := -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow -O1 -g
SAN        := -fsanitize=address,undefined -fno-omit-frame-pointer
HOSTCCS    ?= gcc-13 clang-18

host: which
	@set -e; for cc in $(HOSTCCS); do \
	  d=$(O)/host/$$cc; mkdir -p $$d; \
	  echo "--- $$cc: $(PROG) ---"; \
	  $$cc $(HOSTW) $(SAN) $(DEFS) $(INCS) -o $$d/$(PROG) $(SRCS); \
	  for t in $(TEST_SRCS); do \
	    b=$$(basename $$t .c); \
	    echo "--- $$cc: $$b ---"; \
	    $$cc $(HOSTW) $(SAN) $(DEFS) $(INCS) -o $$d/$$b $$t \
	         $(HERE)/supervise.c $(HERE)/mounts.c $(SRCROOT)/lib/netutil.c; \
	  done; \
	done
	@echo "host build OK for: $(HOSTCCS)"

# `test` builds AND runs, under every host compiler, with both sanitizers on.
# Exit status is the suite's; a tool's own totals line is never its verdict.
test: host
	@set -e; rc=0; ran=0; \
	for cc in $(HOSTCCS); do \
	  for t in $(TEST_SRCS); do \
	    b=$$(basename $$t .c); \
	    printf '=== %s / %s ===\n' "$$cc" "$$b"; \
	    ( cd $(O)/host/$$cc && ASAN_OPTIONS=detect_leaks=1 \
	      UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 ./$$b ) || rc=1; \
	    ran=$$((ran+1)); \
	  done; \
	done; \
	echo "init suite: $$ran test binaries ran, rc=$$rc"; \
	[ $$ran -gt 0 ] || { echo "REFUSED: 0 test binaries ran"; exit 1; }; \
	exit $$rc

# ===========================================================================
# MUTATION CONTROL M1 -- remove the crash-loop cap
#
# The unmutated suite must pass FIRST (a mutation run on a red suite says
# nothing), then the cap is removed in a COPY of supervise.c under $O and the
# suite must go RED.  A mutant the suite still passes is reported as a hole.
# ===========================================================================
mutants: test
	@set -e; m=$(O)/mut/init; rm -rf $$m; mkdir -p $$m; \
	cp $(HERE)/supervise.c $(HERE)/supervise.h $(HERE)/mounts.c \
	   $(HERE)/mounts.h $(HERE)/init.h $(TEST_SRCS) $$m/; \
	cp $(SRCROOT)/lib/netutil.c $(SRCROOT)/lib/netutil.h $$m/; \
	sed -i 's|if (c->fails >= (unsigned)SV_FAIL_MAX) {|if (0) { /* M1: cap removed */|' \
	   $$m/supervise.c; \
	grep -q 'M1: cap removed' $$m/supervise.c || \
	   { echo "REFUSED: M1's anchor did not match; the mutation was not applied"; exit 1; }; \
	gcc-13 $(HOSTW) -Wno-error $(SAN) $(DEFS) -I$$m -o $$m/test_supervise \
	   $$m/test_supervise.c $$m/supervise.c $$m/mounts.c $$m/netutil.c; \
	if ( cd $$m && ./test_supervise >out.txt 2>&1 ); then \
	   echo "HOLE: M1 (crash-loop cap removed) and test_supervise still PASSED"; \
	   sed -n '1,20p' $$m/out.txt; exit 1; \
	else \
	   echo "M1 OK: cap removed -> test_supervise FAILS as it must"; \
	   grep -c '^FAIL' $$m/out.txt | sed 's/^/  failing checks: /'; \
	   grep -m4 '^FAIL' $$m/out.txt | sed 's/^/  /'; \
	fi

# ===========================================================================
# TARGET.  One tripwire snapshot for the whole toolchain phase: the vendor
# binaries all run inside this single `$(TRIP) --`.
# ===========================================================================
target:
ifeq ($(strip $(TC)),)
	@echo "REFUSED: TC=<toolchain root> is required for a target build" >&2; exit 1
else
ifeq ($(strip $(TRIP)),)
	@echo "REFUSED: TRIP=<path to tools/vendor-tripwire.sh> is required; the" >&2
	@echo "         rsdk binaries are vendor binaries and never run unwrapped." >&2; exit 1
else
	@case "$(O)" in /mnt/c/*) \
	   echo "REFUSED: O=$(O) is on DrvFs; the rsdk driver cannot stat() such a path" >&2; \
	   exit 1 ;; esac
	@$(TRIP) -- $(MAKE) --no-print-directory -f $(HERE)/Makefile target-inner \
	   O=$(O) TC=$(TC) TRIP=$(TRIP) BENCH_SHELL=$(BENCH_SHELL) \
	   LAN_IF=$(LAN_IF) WAN_IF=$(WAN_IF)
endif
endif

TCBIN      = $(TC)/bin
TCC        = $(TCBIN)/mips-linux-gcc
TSTRIP     = $(TCBIN)/mips-linux-strip
TNM        = $(TCBIN)/mips-linux-nm
TREADELF   = $(TCBIN)/mips-linux-readelf

# -Os -static -fno-builtin for uprobe's reasons, and NO -march at all: the
# driver's default is the 4181 core and -march=mips32 miscompiles the exposed
# load delay slot silently.  -fno-if-conversion comes from config/rlxfw-cflags
# (TC-25); on a userspace object it is expected to buy NOTHING -- 量 on the
# iperf3 cross build, this gcc's own objects emitted zero conditional moves
# either way -- and it is carried because a policy with an exception per
# artefact is not a policy.  What is claimed is hazlint's 0, not the flag.
TCFLAGS    = -Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
             -fno-builtin -fno-strict-aliasing -fno-common -fno-if-conversion
TLDFLAGS   = -static

TOBJDIR    = $(O)/target/obj/$(PROG)
TSTAGE     = $(O)/target/src
TSRCDIR    = $(TSTAGE)/$(PROG)

# The stage MIRRORS src/'s layout -- src/<prog>/ beside src/lib/ -- so that the
# sources compile unchanged.  A flat stage breaks `#include "../lib/netutil.h"`,
# and editing the includes to suit the staging would make the thing that is
# compiled differ from the thing that is read.
# `R7-8`: cfg.c and cfg.h moved from PROG_STAGE to LIB_STAGE, where they belong
# -- they are src/lib files and this stage mirrors src/ -- and the rest of the
# store came with them, because the real cfg.c is not self-contained the way the
# deleted stub was.  -I../lib mirrors the host build's -I$(SRCROOT)/lib, so that
# init.h's `#include "schema.h"` resolves in both.  gcc 3.4.6 reports a missing
# include and then KEEPS GOING, so the first symptom of getting this wrong is a
# list of undeclared identifiers, not the missing header.
PROG_STAGE = $(HERE)/main.c $(HERE)/mounts.c $(HERE)/supervise.c \
             $(HERE)/init.h $(HERE)/mounts.h $(HERE)/supervise.h
LIB_STAGE  = $(SRCROOT)/lib/netutil.c $(SRCROOT)/lib/netutil.h \
             $(SRCROOT)/lib/cfg.c $(SRCROOT)/lib/cfg.h \
             $(SRCROOT)/lib/schema.c $(SRCROOT)/lib/schema.h \
             $(SRCROOT)/lib/tlv.c $(SRCROOT)/lib/tlv.h \
             $(SRCROOT)/lib/crc32.c $(SRCROOT)/lib/crc32.h
PROG_C     = main.c mounts.c supervise.c
LIB_C      = netutil.c cfg.c schema.c tlv.c crc32.c
TINCS      = -I. -I../lib

target-inner: which
	@case " $(TCFLAGS) " in *" -march="*) \
	   echo "REFUSED: TCFLAGS carries a -march; this build takes the driver's 4181 default" >&2; \
	   exit 1 ;; esac
	@echo "no -march in TCFLAGS"
	@mkdir -p $(TOBJDIR) $(TSRCDIR) $(TSTAGE)/lib $(O)/target
	@# --- stage onto ext4 and prove every copy is the source -----------
	@set -e; for f in $(PROG_STAGE); do \
	  cp -f $$f $(TSRCDIR)/; \
	  a=$$(sha256sum $$f | cut -d' ' -f1); \
	  b=$$(sha256sum $(TSRCDIR)/$$(basename $$f) | cut -d' ' -f1); \
	  [ "$$a" = "$$b" ] || { echo "REFUSED: the staged copy of $$f is not the source" >&2; exit 1; }; \
	done; \
	for f in $(LIB_STAGE); do \
	  cp -f $$f $(TSTAGE)/lib/; \
	  a=$$(sha256sum $$f | cut -d' ' -f1); \
	  b=$$(sha256sum $(TSTAGE)/lib/$$(basename $$f) | cut -d' ' -f1); \
	  [ "$$a" = "$$b" ] || { echo "REFUSED: the staged copy of $$f is not the source" >&2; exit 1; }; \
	done
	@echo "staged $(words $(PROG_STAGE) $(LIB_STAGE)) files to $(TSTAGE), every hash equal to the tree's"
	@# --- compile, with the working directory inside $O ----------------
	@set -e; cd $(TSRCDIR); for f in $(PROG_C); do \
	  echo "  CC $(PROG)/$$f"; \
	  $(TCC) $(TCFLAGS) $(TINCS) $(DEFS) -c $$f -o $(TOBJDIR)/$${f%.c}.o; \
	done; \
	for f in $(LIB_C); do \
	  echo "  CC lib/$$f"; \
	  $(TCC) $(TCFLAGS) $(TINCS) $(DEFS) -c ../lib/$$f \
	      -o $(TOBJDIR)/$${f%.c}.o; \
	done
	@cd $(O)/target && $(TCC) $(TLDFLAGS) -o $(O)/target/$(PROG) $(TOBJDIR)/*.o
	@cp -f $(O)/target/$(PROG) $(O)/target/$(PROG).stripped
	@$(TSTRIP) $(O)/target/$(PROG).stripped
	@# --- gate: no PT_INTERP, and the ELF is big-endian MIPS -----------
	@$(TREADELF) -l $(O)/target/$(PROG) | grep -q INTERP && \
	   { echo "REFUSED: the ELF has a PT_INTERP; it is not static" >&2; exit 1; } || true
	@$(TREADELF) -h $(O)/target/$(PROG) | grep -q "big endian" || \
	   { echo "REFUSED: the ELF is not big-endian" >&2; exit 1; }
	@# --- gate: no system/popen/exec-a-shell in the shipped bytes ------
	@$(MAKE) --no-print-directory -f $(HERE)/Makefile sysscan \
	   O=$(O) TC=$(TC) ELF=$(O)/target/$(PROG)
	@# --- gate: hazlint, 0 violations ---------------------------------
	@HAZLINT_CHILD=1 $(PYTHON) $(REPO)/tools/hazlint $(O)/target/$(PROG)
	@ls -l $(O)/target/$(PROG) $(O)/target/$(PROG).stripped
	@echo "objects kept at $(TOBJDIR):" && ls $(TOBJDIR)

# The forbidden-symbol scan, with its positive control in the same target: a
# scan that has never been shown going red is not a scan.
BADSYMS    = system popen execl execlp execle execv execvp execvpe wordexp
.PHONY: sysscan
sysscan:
	@set -e; bad=0; \
	for s in $(BADSYMS); do \
	  if $(TNM) $(ELF) 2>/dev/null | awk -v s="$$s" '$$3==s{print}' | grep -q .; then \
	    echo "  FOUND $$s in $(ELF)"; bad=1; \
	  fi; \
	done; \
	[ $$bad -eq 0 ] || { echo "REFUSED: a forbidden libc symbol is linked in" >&2; exit 1; }; \
	echo "sysscan: none of [$(BADSYMS)] is linked into $(notdir $(ELF))"
	@# positive control: the same scan over an object that DOES call system()
	@set -e; c=$(O)/target/ctl; mkdir -p $$c; \
	printf '#include <stdlib.h>\nint main(void){return system("true");}\n' > $$c/ctl.c; \
	( cd $$c && $(TCC) -Os -static -o ctl ctl.c ) >/dev/null 2>&1; \
	if $(TNM) $$c/ctl 2>/dev/null | awk '$$3=="system"{print}' | grep -q .; then \
	  echo "sysscan control: system IS found in the control ELF -- the scan can see it"; \
	else \
	  echo "REFUSED: the scan cannot even see system() in a program that calls it" >&2; \
	  exit 1; \
	fi

# The STRIPPED binary is what ships: the manifest counts every declared byte 1:1
# into .init.ramfs, and the symbol table buys the image nothing.  The unstripped
# ELF and every .o stay under $O for the gate's pre-link scan.
install:
	@test -f $(O)/target/$(PROG).stripped || \
	  { echo "REFUSED: no $(O)/target/$(PROG).stripped; run the target build first" >&2; exit 1; }
	@mkdir -p $(INSTALLDIR)
	@cp -f $(O)/target/$(PROG).stripped $(INSTALLDIR)/$(PROG)
	@chmod 0755 $(INSTALLDIR)/$(PROG)
	@echo "installed $(INSTALLDIR)/$(PROG)  ($$(stat -c %s $(INSTALLDIR)/$(PROG)) bytes)"
	@echo "manifest row source: \$$REPO/build/rlxfw-user/$(PROG)/$(PROG)"

clean:
	rm -rf $(O)/host $(O)/target $(O)/mut
