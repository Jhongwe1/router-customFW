# src/cfgstore/Makefile -- the config-store CLI: host build, the host test
# matrix, and the big-endian MIPS target build.
#
# SPEC-R7 § 2 fixes the three entry points, all requiring an absolute O=:
#
#     make host   O=<dir>                      -> $O/host/cfgstore + its tests
#     make test   O=<dir>                      -> runs the suites; non-zero fails
#     make target O=<dir> TC=<root> TRIP=<...>  -> $O/target/cfgstore[.stripped]
#                                                  and $O/target/obj/cfgstore/*.o
#
# ---------------------------------------------------------------------------
# WHAT `test` ACTUALLY RUNS, AND WHY IT IS FOUR PASSES
# ---------------------------------------------------------------------------
#
# gcc-13 and clang-18, each with and without -fsanitize=address,undefined.
# Two compilers because -Wall -Wextra -Werror is a different set of warnings in
# each, and because one of them optimising away a bounds check is exactly the
# kind of thing a single-compiler suite cannot see.  Sanitized AND unsanitized
# because ASan changes the heap layout: a read one byte past a malloc is a
# report under ASan and is usually silent without it, so the unsanitized pass
# is the one that says the code is correct rather than merely instrumented.
#
# -fno-sanitize-recover=all is load-bearing: UBSan's default is to print and
# CONTINUE, which means a suite full of undefined behaviour exits 0.
#
# ---------------------------------------------------------------------------
# WHY THE TARGET BUILD STAGES ITS SOURCES
# ---------------------------------------------------------------------------
#
# config/rlxfw-user/linkprobe/Makefile owns this reason and this file repeats it
# without restating it: the rsdk driver is a 32-bit i386 ELF and every DrvFs
# path returns EOVERFLOW to its stat(), so the sources are copied onto ext4
# first and the copy is proved equal to the repo's by sha256 before anything is
# compiled.  The compiler's working directory is inside $O, never the repo root
# and never src-vendor/ (CLAUDE.md), and every vendor binary runs under
# tools/vendor-tripwire.sh.

SHELL := /bin/sh
HERE  := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
REPO  := $(abspath $(HERE)/../..)
PROG  := cfgstore

# The default goal, declared BEFORE the include: src/lib/Makefile defines no
# targets for exactly this reason, and this line does not depend on that.
.PHONY: all host test target check-one target-inner gate-target clean help \
        mutants
all: help

include $(HERE)/../lib/Makefile

# O is required for everything that builds.  Refuse with a reason, at parse
# time, rather than creating /host/cfgstore at the filesystem root.
NEEDS_O := host test target check-one target-inner gate-target mutants
ifneq ($(filter $(NEEDS_O),$(MAKECMDGOALS)),)
  ifeq ($(strip $(O)),)
    $(error REFUSED: O=<absolute output directory> is required)
  endif
  ifneq ($(patsubst /%,,$(O)),)
    $(error REFUSED: O must be an absolute path, got "$(O)")
  endif
endif

help:
	@echo "make host   O=<abs dir>"
	@echo "make test   O=<abs dir>                        # 4 configurations"
	@echo "make mutants O=<abs dir>                       # the flash suites' controls"
	@echo "make target O=<abs dir> TC=<rsdk root> TRIP=<vendor-tripwire.sh>"

# ---------------------------------------------------------------------------
# Host build
# ---------------------------------------------------------------------------

HOSTCC   ?= gcc-13
SAN      ?= 0
HOSTOUT  ?= $(O)/host
HOSTOBJ  := $(HOSTOUT)/obj/$(PROG)

# NOT $(if ...): the comma in -fsanitize=address,undefined would split the
# function's arguments, and the flag list would come out mangled with the
# sanitizer half-applied.  Found by the first build.
ifeq ($(SAN),1)
  SANFLAGS := -fsanitize=address,undefined -fno-sanitize-recover=all \
              -fno-omit-frame-pointer
else
  SANFLAGS :=
endif

HOSTCFLAGS   := -std=gnu99 -Wall -Wextra -Werror -O1 -g $(SANFLAGS)
HOSTCPPFLAGS := $(RLXLIB_CPPFLAGS) -I$(HERE)

TESTNAMES := test_crc32 test_tlv test_schema test_cfg test_cli test_spictl \
             test_flash
TESTBINS  := $(addprefix $(HOSTOUT)/,$(TESTNAMES))
HOSTLIBO  := $(addprefix $(HOSTOBJ)/,$(addsuffix .o,$(RLXLIB_NAMES)))
HOSTDEPS  := $(RLXLIB_HDRS) $(HERE)/test_util.h $(HERE)/simkern.h

# The flash backend's two suites link with -Wl,--wrap: test_spictl records
# what src/lib/spictl.c calls; test_flash and cfgstore-sim (main.c, the same
# objects) run against simkern.c's simulated rtl819x-spi, which compiles the
# install header the kernel compiles.  simkern.o is in no target list.
KDEV        := $(REPO)/kernel/linux-2.6.30/drivers/mtd/devices
SPICTL_WRAP := -Wl,--wrap=open,--wrap=write,--wrap=flock,--wrap=nanosleep
SIMK_WRAP   := -Wl,--wrap=open,--wrap=close,--wrap=write,--wrap=flock,--wrap=nanosleep,--wrap=lseek
SIMK_DEPS   := $(KDEV)/rtl819x-spi-install.h $(KDEV)/rtl819x-spi-wrpolicy.h

# Without this, make treats every pattern-rule object as intermediate and
# deletes it after the link, so every invocation is a full rebuild.
.SECONDARY:

host: $(HOSTOUT)/$(PROG) $(HOSTOUT)/$(PROG)-sim $(TESTBINS)

$(HOSTOBJ)/%.o: $(RLXLIB_DIR)/%.c $(HOSTDEPS)
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) $(HOSTCPPFLAGS) -c $< -o $@

$(HOSTOBJ)/%.o: $(HERE)/%.c $(HOSTDEPS)
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) $(HOSTCPPFLAGS) -c $< -o $@

$(HOSTOUT)/$(PROG): $(HOSTLIBO) $(HOSTOBJ)/main.o
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $(HOSTLIBO) $(HOSTOBJ)/main.o

$(HOSTOUT)/test_%: $(HOSTOBJ)/test_%.o $(HOSTLIBO)
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $< $(HOSTLIBO)

$(HOSTOBJ)/simkern.o: $(HERE)/simkern.c $(HOSTDEPS) $(SIMK_DEPS)
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) $(HOSTCPPFLAGS) -I$(KDEV) -c $< -o $@

$(HOSTOUT)/test_spictl: $(HOSTOBJ)/test_spictl.o $(HOSTLIBO)
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $< $(HOSTLIBO) $(SPICTL_WRAP)

$(HOSTOUT)/test_flash: $(HOSTOBJ)/test_flash.o $(HOSTOBJ)/simkern.o $(HOSTLIBO)
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $< $(HOSTOBJ)/simkern.o $(HOSTLIBO) $(SIMK_WRAP)

$(HOSTOUT)/$(PROG)-sim: $(HOSTLIBO) $(HOSTOBJ)/main.o $(HOSTOBJ)/simkern.o
	@mkdir -p $(@D)
	$(HOSTCC) $(HOSTCFLAGS) -o $@ $(HOSTLIBO) $(HOSTOBJ)/main.o \
	    $(HOSTOBJ)/simkern.o $(SIMK_WRAP)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# ASAN/UBSAN: abort on the first finding, and count a leak as a finding.
SANENV := ASAN_OPTIONS=detect_leaks=1:abort_on_error=0:exitcode=1 \
          UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1

# TESTS_MIN is the number of test programs, MEASURED 2026-10-17 (the five in
# TESTNAMES then) and 2026-10-23 (seven: test_spictl and test_flash, the flash
# backend's), typed rather than counted from the list it guards: a list that
# loses one REFUSES in every configuration instead of passing with fewer.  Each
# run prints one `ok` or `FAIL` line indented by exactly two spaces, the shape
# tools/ci-census.py counts in CI; a failing run still stops the configuration.
TESTS_MIN := 7
CONF      := $(HOSTCC)$(if $(filter 1,$(SAN)),+san,)

check-one: host
	@echo "--- suite: CC=$(HOSTCC) SAN=$(SAN) out=$(HOSTOUT) ---"
	@set -e; ran=0; for t in $(TESTNAMES); do \
	   case $$t in \
	     test_cfg|test_spictl) set -- $(HOSTOUT) ;; \
	     test_cli) set -- $(HOSTOUT)/$(PROG) $(HOSTOUT) ;; \
	     test_flash) set -- $(HOSTOUT) $(HOSTOUT)/$(PROG)-sim ;; \
	     *)        set -- ;; \
	   esac; \
	   echo "$(SANENV) $(HOSTOUT)/$$t $$*"; \
	   if $(SANENV) $(HOSTOUT)/$$t "$$@"; then \
	     printf '  ok    cfgstore/%s %s\n' "$$t" "$(CONF)"; \
	   else printf '  FAIL  cfgstore/%s %s\n' "$$t" "$(CONF)"; exit 1; fi; \
	   ran=$$((ran+1)); \
	 done; \
	 [ $$ran -ge $(TESTS_MIN) ] || { \
	   echo "REFUSED: cfgstore ran $$ran test programs under $(CONF); the floor" \
	        "is $(TESTS_MIN), the measured count"; exit 1; }
	@echo "--- suite OK: CC=$(HOSTCC) SAN=$(SAN) ---"

# Four configurations.  make stops at the first non-zero recipe line, so a red
# pass ends the run and `test` exits non-zero.
test:
	@$(MAKE) --no-print-directory -C $(HERE) check-one O=$(O) \
	    HOSTCC=gcc-13   SAN=0 HOSTOUT=$(O)/host/gcc13
	@$(MAKE) --no-print-directory -C $(HERE) check-one O=$(O) \
	    HOSTCC=clang-18 SAN=0 HOSTOUT=$(O)/host/clang18
	@$(MAKE) --no-print-directory -C $(HERE) check-one O=$(O) \
	    HOSTCC=gcc-13   SAN=1 HOSTOUT=$(O)/host/gcc13-san
	@$(MAKE) --no-print-directory -C $(HERE) check-one O=$(O) \
	    HOSTCC=clang-18 SAN=1 HOSTOUT=$(O)/host/clang18-san
	@echo "test: 4 configurations x 7 suites, all green"

# ---------------------------------------------------------------------------
# Mutation controls (`make mutants O=`, not part of `test`)
# ---------------------------------------------------------------------------
#
# Each plants one named defect, through mutate.py, in a COPY of src/lib under
# $O/mut/<name>, rebuilds test_spictl, test_flash and cfgstore-sim against the
# copy with gcc-13, and must turn the flash suites RED.  The unmutated copy is
# built and run the same way first; a red control refuses the run, and a
# mutant that does not COMPILE refuses it too (-Werror: a build failure is not
# a kill).
MUTANTS := nwrites badstage nolock noguard nocleanup ptrdispatch noregular
MUTCC   := gcc-13 -std=gnu99 -Wall -Wextra -Werror -O1 -g

mutants:
	@set -e; m=$(O)/mut; rm -rf $$m; mkdir -p $$m; \
	 build() { d=$$1; libs=; \
	   for n in $(RLXLIB_NAMES); do libs="$$libs $$d/lib/$$n.c"; done; \
	   $(MUTCC) -I$$d/lib -I$(HERE) -o $$d/test_spictl \
	     $(HERE)/test_spictl.c $$libs $(SPICTL_WRAP) && \
	   $(MUTCC) -I$$d/lib -I$(HERE) -I$(KDEV) -o $$d/test_flash \
	     $(HERE)/test_flash.c $(HERE)/simkern.c $$libs $(SIMK_WRAP) && \
	   $(MUTCC) -I$$d/lib -I$(HERE) -I$(KDEV) -o $$d/$(PROG)-sim \
	     $(HERE)/main.c $(HERE)/simkern.c $$libs $(SIMK_WRAP); }; \
	 suites() { d=$$1; r=0; \
	   $$d/test_spictl $$d > $$d/spictl.out 2>&1 || r=1; \
	   $$d/test_flash $$d $$d/$(PROG)-sim > $$d/flash.out 2>&1 || r=$$((r+2)); \
	   return $$r; }; \
	 c=$$m/control; mkdir -p $$c/lib; cp $(RLXLIB_DIR)/*.c $(RLXLIB_DIR)/*.h $$c/lib/; \
	 build $$c > $$c/cc.log 2>&1 || { cat $$c/cc.log; \
	   echo "REFUSED: the unmutated copy does not build"; exit 1; }; \
	 if suites $$c; then echo "control: the unmutated flash suites pass"; \
	 else echo "REFUSED: the unmutated flash suites fail ($$c/*.out);" \
	   "a mutation run on a red suite proves nothing"; exit 1; fi; \
	 caught=0; missed=0; \
	 for x in $(MUTANTS); do \
	   d=$$m/$$x; mkdir -p $$d/lib; cp $(RLXLIB_DIR)/*.c $(RLXLIB_DIR)/*.h $$d/lib/; \
	   $(PYTHON) $(HERE)/mutate.py $$x $$d/lib || { \
	     echo "REFUSED: mutation $$x was not planted"; exit 1; }; \
	   build $$d > $$d/cc.log 2>&1 || { cat $$d/cc.log; \
	     echo "REFUSED: mutant $$x does not compile, so it cannot be a kill"; exit 1; }; \
	   if suites $$d; then \
	     echo "  $$x: *** NOT CAUGHT *** (both flash suites still pass)"; \
	     missed=$$((missed+1)); \
	   else \
	     echo "  $$x: CAUGHT -- FAIL lines: test_spictl $$(grep -c '^FAIL' $$d/spictl.out || true)," \
	          "test_flash $$(grep -c '^FAIL' $$d/flash.out || true)"; \
	     caught=$$((caught+1)); \
	   fi; \
	 done; \
	 echo "mutants: $$caught caught, $$missed not caught ($(words $(MUTANTS)) planted)"; \
	 [ $$missed -eq 0 ] || { echo "REFUSED: a mutant survived"; exit 1; }

# ---------------------------------------------------------------------------
# Target build (big-endian MIPS, static, uClibc 0.9.30)
# ---------------------------------------------------------------------------

TC      ?=
TRIP    ?=
TCBIN   := $(TC)/bin
TCC     := $(TCBIN)/mips-linux-gcc
TSTRIP  := $(TCBIN)/mips-linux-strip

TGTOUT  := $(O)/target
TGTOBJ  := $(TGTOUT)/obj/$(PROG)
TGTSRC  := $(TGTOUT)/src
TGTELF  := $(TGTOUT)/$(PROG)
TGTBIN  := $(TGTOUT)/$(PROG).stripped

HAZLINT := $(REPO)/tools/hazlint
PYTHON  ?= /usr/bin/python3
READELF ?= readelf

# Read the flag from the file that owns it rather than typing it here
# (config/rlxfw-cflags: -fno-if-conversion, SPEC.md TC-25).  Its own header says
# it cannot reach a prebuilt libc.a; it still applies to OUR objects, and
# hazlint over the linked ELF is the check that decides.
RLXFW_CFLAGS := $(shell sed -e 's/\#.*//' $(REPO)/config/rlxfw-cflags 2>/dev/null | tr -s ' \t\n' ' ')

# NO -march: the wrapper's default is the 4181 core, and -march=mips32
# miscompiles the exposed load delay slot silently (CLAUDE.md).
TCFLAGS  := -Os -std=gnu99 -Wall -Wextra -Werror -fno-builtin \
            -fno-strict-aliasing -fno-common $(RLXFW_CFLAGS)
TCPPFLAGS := -I. -DNDEBUG
TLDFLAGS := -static

TGT_CSRC  := $(addsuffix .c,$(RLXLIB_NAMES)) main.c
TGT_OBJS  := $(addprefix $(TGTOBJ)/,$(addsuffix .o,$(RLXLIB_NAMES)) main.o)

target:
	@test -n "$(TC)"    || { echo "REFUSED: TC=<rsdk toolchain root> is required"; exit 1; }
	@test -x "$(TCC)"   || { echo "REFUSED: no cross compiler at $(TCC)"; exit 1; }
	@test -n "$(TRIP)"  || { echo "REFUSED: TRIP=<repo>/tools/vendor-tripwire.sh is required"; exit 1; }
	@test -x "$(TRIP)"  || { echo "REFUSED: $(TRIP) is not executable"; exit 1; }
	@case " $(TCFLAGS) " in *" -march="*) \
	   echo "REFUSED: a -march reached the target CFLAGS"; exit 1 ;; esac; \
	 echo "no -march in the target CFLAGS"
	$(TRIP) --quiet -- $(MAKE) --no-print-directory -C $(HERE) target-inner \
	    O=$(O) TC=$(TC)
	@$(MAKE) --no-print-directory -C $(HERE) gate-target O=$(O) TC=$(TC)

# Everything that runs a vendor binary lives in here, so that one tripwire
# invocation covers the whole compile-link-strip sequence.
target-inner:
	@mkdir -p $(TGTSRC) $(TGTOBJ)
	@for f in $(TGT_CSRC); do \
	   if [ -f $(RLXLIB_DIR)/$$f ]; then s=$(RLXLIB_DIR)/$$f; else s=$(HERE)/$$f; fi; \
	   cp -f $$s $(TGTSRC)/$$f || exit 1; \
	   a=$$(sha256sum $$s | cut -d' ' -f1); \
	   b=$$(sha256sum $(TGTSRC)/$$f | cut -d' ' -f1); \
	   [ "$$a" = "$$b" ] || { echo "REFUSED: staged $$f is not the source"; exit 1; }; \
	 done
	@for h in $(RLXLIB_HDRS); do cp -f $$h $(TGTSRC)/ || exit 1; done
	@echo "staged $(words $(TGT_CSRC)) sources and $(words $(RLXLIB_HDRS)) headers to $(TGTSRC)"
	@cd $(TGTSRC) && for f in $(TGT_CSRC); do \
	   o=$(TGTOBJ)/$${f%.c}.o; \
	   echo "  CC $$f"; \
	   $(TCC) $(TCFLAGS) $(TCPPFLAGS) -c $$f -o $$o || exit 1; \
	 done
	@cd $(TGTSRC) && $(TCC) $(TLDFLAGS) -o $(TGTELF) $(TGT_OBJS) \
	    2>$(TGTOUT)/link.log; rc=$$?; cat $(TGTOUT)/link.log; exit $$rc
	@cp -f $(TGTELF) $(TGTBIN)
	@cd $(TGTSRC) && $(TSTRIP) $(TGTBIN)
	@echo "linked $(TGTELF) and stripped $(TGTBIN)"
	@# T4's positive control: an ELF from THIS toolchain and THIS libc that
	@# really calls system(), so that gate T4's source 1 is shown firing
	@# before it is believed.  It is never installed anywhere.
	@printf '%s\n' \
	  '#include <stdlib.h>' \
	  'int main(void) { return system("/bin/true"); }' \
	  > $(TGTSRC)/noshell-positive.c
	@cd $(TGTSRC) && $(TCC) -Os -std=gnu99 -static -o \
	    $(TGTOUT)/noshell-positive.elf noshell-positive.c
	@echo "built T4's positive control $(TGTOUT)/noshell-positive.elf"

# The gates.  Nothing here runs a vendor binary: hazlint is this repository's
# own Python, and readelf is target-independent for reading.
gate-target:
	@echo '--- T1: every object kept, and it is every source ---'
	@n=$$(ls $(TGTOBJ)/*.o 2>/dev/null | wc -l); \
	 echo "objects in $(TGTOBJ): $$n (want $(words $(TGT_CSRC)))"; \
	 [ "$$n" = "$(words $(TGT_CSRC))" ] || { echo "REFUSED: object count"; exit 1; }
	@echo '--- T2: hazlint over the linked ELF ---'
	@HAZLINT_CHILD=1 $(PYTHON) $(HAZLINT) $(TGTELF)
	@echo '--- T3: big-endian MIPS, static, no PT_INTERP ---'
	@h=$$($(READELF) -h $(TGTELF)); \
	 echo "$$h" | grep -q "big endian" || { echo "REFUSED: not big-endian"; exit 1; }; \
	 echo "$$h" | grep -qi "MIPS" || { echo "REFUSED: not MIPS"; exit 1; }; \
	 echo "$$h" | grep -q "EXEC (Executable file)" || { echo "REFUSED: not an executable"; exit 1; }; \
	 i=$$($(READELF) -l $(TGTELF) | grep -c INTERP || true); \
	 [ "$$i" = "0" ] || { echo "REFUSED: a PT_INTERP in a static build"; exit 1; }; \
	 echo "$$h" | sed -n 's/^  \(Class\|Data\|Type\|Machine\|Flags\):/  \1:/p'
	@echo '--- T4: no way to reach a shell, two sources, five controls ---'
	@test -f $(TGTOUT)/noshell-positive.elf || { \
	   echo "REFUSED: no positive control ELF; run the target build, which"; \
	   echo "  cross-compiles one that calls system()"; exit 1; }
	@$(HERE)/noshell-gate.sh --elf $(TGTELF) --bin $(TGTBIN) \
	    --positive $(TGTOUT)/noshell-positive.elf --readelf $(READELF) \
	    --work $(TGTOUT)/gate
	@echo '--- sizes ---'
	@echo "elf_bytes       $$(wc -c < $(TGTELF))"
	@echo "stripped_bytes  $$(wc -c < $(TGTBIN))"
	@echo "sha256          $$(sha256sum $(TGTBIN) | cut -d' ' -f1)"
	@$(READELF) -S -W $(TGTELF) | awk \
	  '{for (i = 1; i <= NF; i++) \
	      if ($$i == ".text" || $$i == ".rodata" || $$i == ".data" || \
	          $$i == ".bss") printf "  %-8s 0x%s\n", $$i, $$(i + 4)}'

clean:
	@test -n "$(O)" || { echo "REFUSED: O is required"; exit 1; }
	rm -rf $(O)/host $(O)/target
