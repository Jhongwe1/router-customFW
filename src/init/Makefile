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
#   make -C src/init mutants O=<abs dir>                the mutation controls (M1, and
#                                                       the one-shot children's eight)
#   make -C src/init target O=<abs dir> TC=<toolchain root> TRIP=<vendor-tripwire.sh>
#
# `O=` is required everywhere: there is no in-tree build, because the tree may be
# on DrvFs and because a stray object under src/ is a file the census counts.
#
# BENCH_SHELL=0 builds PID 1 without the console shell and with the console
# first-password step (see init.h).  CTR_ADVANCE=0 builds it without the
# counter advance; SWITCH_BRINGUP=0 without the LAN bring-up, and so without
# the counter advance too.  Each is 0 or 1.  A build with BENCH_SHELL=1 and no
# counter advance links exactly the objects it linked before either existed.
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
CTR_ADVANCE ?= 1
SWITCH_BRINGUP ?= 1
LAN_IF     ?=
WAN_IF     ?=

$(foreach v,BENCH_SHELL CTR_ADVANCE SWITCH_BRINGUP,$(if $(filter-out 0 1,$($(v))),\
  $(error REFUSED: $(v)=$($(v)); it is 0 or 1)))
$(foreach v,BENCH_SHELL CTR_ADVANCE SWITCH_BRINGUP,$(if $(strip $($(v))),,\
  $(error REFUSED: $(v) is empty; it is 0 or 1)))

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
CFG_DEPS   := $(SRCROOT)/lib/schema.c $(SRCROOT)/lib/tlv.c $(SRCROOT)/lib/crc32.c $(SRCROOT)/lib/cfgflash.c $(SRCROOT)/lib/spictl.c $(SRCROOT)/lib/sha256.c

# The one-shot children (init.h; notes/self-update.md §§ 5 and 3.8), each linked
# only into a build that has it.  The counter advance talks to brokerd through
# src/lib/client.c, which needs proto.c; the first-password step derives the
# hash with src/lib/kdf.c (sha256.c is already in CFG_DEPS).
CTR_ON     := $(and $(filter 1,$(CTR_ADVANCE)),$(filter 1,$(SWITCH_BRINGUP)))
FP_ON      := $(filter 0,$(BENCH_SHELL))
CTR_SRC    := $(HERE)/ctradv.c $(SRCROOT)/lib/client.c $(SRCROOT)/lib/proto.c
FP_SRC     := $(HERE)/firstpw.c $(SRCROOT)/lib/kdf.c
SRCS       := $(OWN_SRC) $(CFG_C) $(CFG_DEPS) $(if $(CTR_ON),$(CTR_SRC)) \
              $(if $(FP_ON),$(FP_SRC))

# The test programs, and what each links besides itself.  test_ctradv compiles
# the install header the kernel compiles (its simulated `ctr`) and reads
# brokerd.h for the one constant it holds equal; both wrap libc calls to record
# them (see each file's header).
TESTS      := test_supervise test_mounts test_ctradv test_firstpw
TEST_SRCS  := $(addprefix $(HERE)/,$(addsuffix .c,$(TESTS)))
KDEV       := $(REPO)/kernel/linux-2.6.30/drivers/mtd/devices
T_SV       := $(HERE)/supervise.c $(HERE)/mounts.c $(SRCROOT)/lib/netutil.c
TREST_test_supervise := $(T_SV)
TREST_test_mounts    := $(T_SV)
TREST_test_ctradv    := $(HERE)/supervise.c $(SRCROOT)/lib/spictl.c \
                        $(SRCROOT)/lib/client.c $(SRCROOT)/lib/proto.c \
                        -Wl,--wrap=open,--wrap=close,--wrap=write,--wrap=flock,--wrap=nanosleep
TREST_test_firstpw   := $(CFG_C) $(CFG_DEPS) $(SRCROOT)/lib/kdf.c \
                        -Wl,--wrap=tcsetattr
TMOD_test_ctradv     := $(HERE)/ctradv.c
TMOD_test_firstpw    := $(HERE)/firstpw.c
TINC_test_ctradv     := -I$(KDEV) -I$(SRCROOT)/brokerd
TINC_test_firstpw    := -I$(SRCROOT)/brokerd

DEFS       := -DRLXFW_BENCH_SHELL=$(BENCH_SHELL) -DRLXFW_CTR_ADVANCE=$(CTR_ADVANCE) \
              -DRLXFW_SWITCH_BRINGUP=$(SWITCH_BRINGUP)
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

# One test program's compile-and-link line, inside the shell's loop over $$cc.
# ONE line on purpose: a newline in an expansion inside a recipe makes a
# separate shell, which would cut the loop in two.
build_test = echo "--- $$cc: $(1) ---"; $$cc $(HOSTW) $(SAN) $(DEFS) $(INCS) $(TINC_$(1)) -o $$d/$(1) $(HERE)/$(1).c $(TMOD_$(1)) $(TREST_$(1));

# main.c's one-shot glue is compiled out by switch, so the configured build
# alone leaves its other shapes uncompiled.  Each BENCH_SHELL:CTR_ADVANCE:
# SWITCH_BRINGUP shape is compiled here (-c only: the configured shape is the
# one linked above).
GLUE_SHAPES := 1:1:1 1:0:1 0:1:1 0:0:1 1:1:0 0:1:0

host: which
	@set -e; for cc in $(HOSTCCS); do \
	  d=$(O)/host/$$cc; mkdir -p $$d; \
	  echo "--- $$cc: $(PROG) ---"; \
	  $$cc $(HOSTW) $(SAN) $(DEFS) $(INCS) -o $$d/$(PROG) $(SRCS); \
	  $(foreach t,$(TESTS),$(call build_test,$(t))) \
	  for s in $(GLUE_SHAPES); do \
	    b=$${s%%:*}; r=$${s#*:}; a=$${r%%:*}; w=$${r#*:}; \
	    $$cc $(HOSTW) $(SAN) -DRLXFW_BENCH_SHELL=$$b -DRLXFW_CTR_ADVANCE=$$a \
	      -DRLXFW_SWITCH_BRINGUP=$$w $(INCS) -c -o $$d/main-glue.o $(HERE)/main.c; \
	  done; \
	  echo "--- $$cc: main.c compiles in all $(words $(GLUE_SHAPES)) switch shapes ---"; \
	done
	@echo "host build OK for: $(HOSTCCS)"

# `test` builds AND runs, under every host compiler, with both sanitizers on.
# Exit status is the suite's; a tool's own totals line is never its verdict.
#
# TESTS_MIN is the number of test programs, MEASURED 2026-10-17 (test_supervise,
# test_mounts) and typed here rather than counted from TEST_SRCS, the list it
# guards: a list that loses a program REFUSES instead of passing with fewer, and
# so does an empty HOSTCCS.  Each run prints one `ok` or `FAIL` line indented by
# exactly two spaces, the shape tools/ci-census.py counts in CI.  4 since the
# one-shot children's two (test_ctradv, test_firstpw).
TESTS_MIN  := 4

test: host
	@set -e; rc=0; ran=0; ncc=0; \
	for cc in $(HOSTCCS); do \
	  ncc=$$((ncc+1)); \
	  for t in $(TEST_SRCS); do \
	    b=$$(basename $$t .c); \
	    printf '=== %s / %s ===\n' "$$cc" "$$b"; \
	    if ( cd $(O)/host/$$cc && ASAN_OPTIONS=detect_leaks=1 \
	      UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 ./$$b ); then \
	      printf '  ok    init/%s %s\n' "$$b" "$$cc"; \
	    else printf '  FAIL  init/%s %s\n' "$$b" "$$cc"; rc=1; fi; \
	    ran=$$((ran+1)); \
	  done; \
	done; \
	need=$$(($(TESTS_MIN) * ncc)); \
	echo "init suite: $$ran test binaries ran, rc=$$rc"; \
	[ $$ran -gt 0 ] && [ $$ran -ge $$need ] || { \
	  echo "REFUSED: init ran $$ran test binaries; the floor is $$need --" \
	       "$(TESTS_MIN) measured test programs under each of $$ncc compiler(s)"; \
	  exit 1; }; \
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
	@$(MAKE) --no-print-directory -f $(HERE)/Makefile mutants-oneshot O=$(O)

# ===========================================================================
# THE ONE-SHOT CHILDREN'S MUTATION CONTROLS -- src/init/mutate.py plants each
# in a COPY of ctradv.c or firstpw.c under $O/mut/<name>/, the suite's own test
# is rebuilt against the copy with the suite's own flags (-Werror included: a
# mutant that does not compile is NOT A KILL and stops the run), and it must
# exit non-zero WITH at least one FAIL line -- a crash is not a check going red,
# and neither is a hang: each run gets 300 s (`timeout`), and one cut off with
# no FAIL line printed is NOT A KILL.  Run by `mutants`, after the unmutated
# suite passed.
# ===========================================================================
MUT_CTR    := early onnone twice nolock
MUT_FP     := overhash echo nowait noconfirm
MUT_ENV    := ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1

# mutant name, module (ctradv|firstpw), test program
define mut_one
md=$(O)/mut/$(1); rm -rf $$md; mkdir -p $$md; cp $(HERE)/$(2).c $$md/; \
$(PYTHON) $(HERE)/mutate.py $(1) $$md/$(2).c || exit 1; \
if ! gcc-13 $(HOSTW) $(SAN) $(DEFS) $(INCS) $(TINC_$(3)) -o $$md/$(3) $(HERE)/$(3).c $$md/$(2).c $(TREST_$(3)) > $$md/cc.txt 2>&1; then \
  echo "NOT A KILL: $(1) does not compile"; sed -n '1,12p' $$md/cc.txt; exit 1; fi; \
if ( cd $$md && $(MUT_ENV) timeout 300 ./$(3) > out.txt 2>&1 ); then \
  echo "HOLE: $(1) and $(3) still PASSED"; sed -n '1,20p' $$md/out.txt; exit 1; fi; \
f=$$(grep -c '^FAIL' $$md/out.txt || true); \
if [ "$$f" -lt 1 ]; then \
  echo "NOT A KILL: $(1) made $(3) exit non-zero with no FAIL line"; sed -n '1,20p' $$md/out.txt; exit 1; fi; \
echo "$(1) OK: $(3) FAILS as it must ($$f failing checks)"; \
grep -m3 '^FAIL' $$md/out.txt | sed 's/^/  /'; \
n=$$((n+1));
endef

.PHONY: mutants-oneshot
mutants-oneshot:
	@set -e; n=0; \
	$(foreach m,$(MUT_CTR),$(call mut_one,$(m),ctradv,test_ctradv)) \
	$(foreach m,$(MUT_FP),$(call mut_one,$(m),firstpw,test_firstpw)) \
	echo "one-shot mutants: $$n of $(words $(MUT_CTR) $(MUT_FP)) went red"; \
	[ $$n -eq $(words $(MUT_CTR) $(MUT_FP)) ]

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
	   CTR_ADVANCE=$(CTR_ADVANCE) SWITCH_BRINGUP=$(SWITCH_BRINGUP) \
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
# The one-shot children's sources are staged whatever the switches say and
# compiled only when the build has them (CTR_ON, FP_ON), so a build without
# either compiles and links the objects it did before they existed; the object
# directory is emptied first, because the link takes $(TOBJDIR)/*.o and an
# object left by an earlier build with the other switches would otherwise be
# linked into this one.
PROG_STAGE = $(HERE)/main.c $(HERE)/mounts.c $(HERE)/supervise.c \
             $(HERE)/init.h $(HERE)/mounts.h $(HERE)/supervise.h \
             $(HERE)/ctradv.c $(HERE)/ctradv.h $(HERE)/firstpw.c $(HERE)/firstpw.h
LIB_STAGE  = $(SRCROOT)/lib/netutil.c $(SRCROOT)/lib/netutil.h \
             $(SRCROOT)/lib/cfg.c $(SRCROOT)/lib/cfg.h $(SRCROOT)/lib/cfgflash.c \
             $(SRCROOT)/lib/schema.c $(SRCROOT)/lib/schema.h $(SRCROOT)/lib/spictl.c $(SRCROOT)/lib/spictl.h \
             $(SRCROOT)/lib/tlv.c $(SRCROOT)/lib/tlv.h $(SRCROOT)/lib/sha256.c $(SRCROOT)/lib/sha256.h \
             $(SRCROOT)/lib/crc32.c $(SRCROOT)/lib/crc32.h \
             $(SRCROOT)/lib/client.c $(SRCROOT)/lib/client.h $(SRCROOT)/lib/proto.c $(SRCROOT)/lib/proto.h \
             $(SRCROOT)/lib/kdf.c $(SRCROOT)/lib/kdf.h
PROG_C     = main.c mounts.c supervise.c $(if $(CTR_ON),ctradv.c) $(if $(FP_ON),firstpw.c)
LIB_C      = netutil.c cfg.c cfgflash.c spictl.c sha256.c schema.c tlv.c crc32.c \
             $(if $(CTR_ON),client.c proto.c) $(if $(FP_ON),kdf.c)
TINCS      = -I. -I../lib

target-inner: which
	@case " $(TCFLAGS) " in *" -march="*) \
	   echo "REFUSED: TCFLAGS carries a -march; this build takes the driver's 4181 default" >&2; \
	   exit 1 ;; esac
	@echo "no -march in TCFLAGS"
	@mkdir -p $(TOBJDIR) $(TSRCDIR) $(TSTAGE)/lib $(O)/target
	@rm -f $(TOBJDIR)/*.o
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
