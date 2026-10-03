# src/brokerd/Makefile -- brokerd: host build, host tests, sanitizers, the
# mutation controls, the fuzz harness, and the big-endian MIPS target build.
#
# O=<absolute out dir> is required by every target (SPEC-R7 § 2).  The target
# build runs the rsdk compiler under TRIP=tools/vendor-tripwire.sh with its
# working directory inside $O, and STAGES THE SOURCES ONTO ext4 FIRST: the rsdk
# driver is a 32-bit i386 ELF and every DrvFs path returns EOVERFLOW to its
# stat(), so a build straight out of /mnt/c cannot work.  That is
# config/rlxfw-user/linkprobe/Makefile's G0 and this file repeats it rather than
# restating why.
#
# CFG/KDF HEADERS: src/lib/{cfg,kdf}.h.  `R7-8` deleted src/brokerd/stub/, which
# stood in for them while the two halves were written in parallel, so an absent
# header REFUSES rather than falling back.  量 `R7-8` what the stub had guessed
# wrong: CFG_NKEYS 17 against the real 16, and seven CFGE_* numbers none of which
# matched; cfg_last_key() was guessed right, signature included.

SHELL := /bin/sh
HERE  := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO  := $(abspath $(HERE)../..)
LIB   := $(REPO)/src/lib

ifeq ($(O),)
$(error O=<absolute output directory> is required)
endif
ifeq ($(patsubst /%,,$(O)),$(O))
$(error O must be absolute, got "$(O)")
endif

# Which cfg/kdf do we have?
REAL_CFG := $(wildcard $(LIB)/cfg.h)
REAL_KDF := $(wildcard $(LIB)/kdf.h)
ifeq ($(REAL_CFG),)
$(error REFUSED: $(LIB)/cfg.h is absent and there is no longer a stub)
endif
ifeq ($(REAL_KDF),)
$(error REFUSED: $(LIB)/kdf.h is absent and there is no longer a stub)
endif
CFGINC   := $(LIB)
KDFINC   := $(LIB)
CFGSRC   := $(LIB)/cfg.c $(LIB)/schema.c $(LIB)/tlv.c $(LIB)/crc32.c
KDFSRC   := $(LIB)/kdf.c $(LIB)/sha256.c
STUBSRC  :=
WHICHCFG := src/lib/cfg.h

INCS := -I$(HERE) -I$(LIB) -I$(CFGINC) -I$(KDFINC)

# brokerd's own sources, and the library sources it needs.
BK_SRC  := $(HERE)main.c $(HERE)session.c $(HERE)ops.c
LIB_SRC := $(LIB)/proto.c
ALL_SRC := $(BK_SRC) $(LIB_SRC) $(CFGSRC) $(KDFSRC) $(STUBSRC)

# Everything but main.c, for the tests to link against.
OBJ_NOMAIN_SRC := $(HERE)session.c $(HERE)ops.c $(LIB_SRC) $(CFGSRC) $(KDFSRC) \
                  $(STUBSRC) $(LIB)/client.c

TESTS := test_proto test_authz test_session test_ratelimit test_entropy \
         test_ping test_wire test_reload

# `FW-184`: test_reload changes the password through the real cfgstore, so the
# host build makes one, from the sources the image's cfgstore is made from.
CFGSTORE_SRC := $(REPO)/src/cfgstore/main.c $(CFGSRC) $(KDFSRC)

# ---------------------------------------------------------------- host build
HOSTCC   ?= gcc-13
HOSTCC2  ?= clang-18
HCFLAGS  := -std=gnu99 -Wall -Wextra -Werror -O1 -g $(INCS)
SANFLAGS := -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: all host test sanitize mutants fuzz fuzzrun cov target clean show

all: host

$(O)/host:
	@mkdir -p $@

host: $(O)/host
	@echo "cfg header: $(WHICHCFG)"
	$(HOSTCC) $(HCFLAGS) -o $(O)/host/brokerd $(ALL_SRC)
	$(HOSTCC2) $(HCFLAGS) -o $(O)/host/brokerd.clang $(ALL_SRC)
	$(HOSTCC) $(HCFLAGS) -o $(O)/host/pinghelp $(HERE)test_pinghelp.c
	$(HOSTCC) $(HCFLAGS) -DPINGHELP_SLOW=1 -o $(O)/host/pinghelp_slow $(HERE)test_pinghelp.c
	$(HOSTCC) $(HCFLAGS) -o $(O)/host/cfgstore $(CFGSTORE_SRC)
	@for t in $(TESTS); do \
	   $(HOSTCC) $(HCFLAGS) -o $(O)/host/$$t $(HERE)$$t.c $(OBJ_NOMAIN_SRC) || exit 1; \
	   $(HOSTCC2) $(HCFLAGS) -o $(O)/host/$$t.clang $(HERE)$$t.c $(OBJ_NOMAIN_SRC) || exit 1; \
	 done
	@echo "host build ok: $(HOSTCC) and $(HOSTCC2), -Wall -Wextra -Werror"

# `test` runs the suite twice: the plain build and the sanitizer build.  A
# refusing suite is fast, so the count of what ran is printed beside the time.
test: host
	@set -e; n=0; \
	 for t in $(TESTS); do \
	   echo "=== $$t (gcc-13) ==="; \
	   case $$t in \
	     test_ping) $(O)/host/$$t $(O)/host/pinghelp $(O)/host/pinghelp_slow ;; \
	     test_wire) $(O)/host/$$t $(O)/host/brokerd ;; \
	     test_reload) $(O)/host/$$t $(O)/host/cfgstore ;; \
	     *)         $(O)/host/$$t ;; \
	   esac; \
	   n=$$((n+1)); \
	 done; \
	 for t in $(TESTS); do \
	   echo "=== $$t (clang-18) ==="; \
	   case $$t in \
	     test_ping) $(O)/host/$$t.clang $(O)/host/pinghelp $(O)/host/pinghelp_slow ;; \
	     test_wire) $(O)/host/$$t.clang $(O)/host/brokerd.clang ;; \
	     test_reload) $(O)/host/$$t.clang $(O)/host/cfgstore ;; \
	     *)         $(O)/host/$$t.clang ;; \
	   esac; \
	   n=$$((n+1)); \
	 done; \
	 echo "PASS: $$n test binaries ran (both compilers)"
	@$(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) sanitize

sanitize: $(O)/host
	@set -e; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/brokerd.san $(ALL_SRC); \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/pinghelp.san $(HERE)test_pinghelp.c; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -DPINGHELP_SLOW=1 -o $(O)/host/pinghelp_slow.san $(HERE)test_pinghelp.c; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/cfgstore.san $(CFGSTORE_SRC); \
	 n=0; \
	 for t in $(TESTS); do \
	   $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/$$t.san \
	     $(HERE)$$t.c $(OBJ_NOMAIN_SRC); \
	 done; \
	 for t in $(TESTS); do \
	   echo "=== $$t (clang-18 asan+ubsan) ==="; \
	   case $$t in \
	     test_ping) $(O)/host/$$t.san $(O)/host/pinghelp.san $(O)/host/pinghelp_slow.san ;; \
	     test_wire) $(O)/host/$$t.san $(O)/host/brokerd.san ;; \
	     test_reload) $(O)/host/$$t.san $(O)/host/cfgstore.san ;; \
	     *)         $(O)/host/$$t.san ;; \
	   esac; \
	   n=$$((n+1)); \
	 done; \
	 echo "PASS: $$n test binaries ran under -fsanitize=address,undefined"

# ------------------------------------------------------------- the mutations
# Each mutation is a sed-copy of the real source: proto.c itself never carries a
# switch that could be flipped.  Every mutant must make the suite FAIL; a
# mutant that passes is reported, because that is the honest result.
$(O)/mut:
	@mkdir -p $@

mutants: host $(O)/mut
	@set -e; \
	 echo "--- control: the UNMUTATED suite must pass first ---"; \
	 $(O)/host/test_proto > $(O)/mut/control.out 2>&1 \
	   || { echo "REFUSED: the unmutated suite fails; a mutation run would prove nothing"; \
	        tail -20 $(O)/mut/control.out; exit 1; }; \
	 echo "control: test_proto passes"; \
	 caught=0; missed=0; \
	 mkmut() { \
	   name=$$1; expr=$$2; \
	   sed "$$expr" $(LIB)/proto.c > $(O)/mut/$$name.c; \
	   if cmp -s $(O)/mut/$$name.c $(LIB)/proto.c; then \
	     echo "REFUSED: mutation $$name changed nothing; the sed did not match"; exit 1; \
	   fi; \
	 }; \
	 run() { \
	   name=$$1; \
	   $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/mut/$$name \
	     $(HERE)test_proto.c $(O)/mut/$$name.c 2>$(O)/mut/$$name.cc || { \
	       echo "  $$name: CAUGHT at compile time"; caught=$$((caught+1)); return; }; \
	   if $(O)/mut/$$name > $(O)/mut/$$name.out 2>&1; then \
	     echo "  $$name: *** NOT CAUGHT *** (the suite still passes)"; \
	     missed=$$((missed+1)); \
	   else \
	     echo "  $$name: CAUGHT ($$(grep -c FAIL $(O)/mut/$$name.out || true) FAIL lines, or a sanitizer abort)"; \
	     caught=$$((caught+1)); \
	   fi; \
	 }; \
	 echo "--- M1: the body_len bound removed ---"; \
	 mkmut m1_nobound 's/if (blen > PROTO_REQ_BODY_MAX)/if (0)/'; \
	 run m1_nobound; \
	 echo "--- M2: the header length off by one (47 instead of 48) ---"; \
	 mkmut m2_hdroff 's/rx->want = PROTO_REQ_HDR;/rx->want = PROTO_REQ_HDR - 1;/'; \
	 run m2_hdroff; \
	 echo "--- M3: the magic check inverted to accept all but one value ---"; \
	 mkmut m3_nomagic 's/if (magic != PROTO_REQ_MAGIC)/if (magic == 0xDEADBEEFu)/'; \
	 run m3_nomagic; \
	 echo "--- M4: big-endian read turned into the wrong byte order ---"; \
	 mkmut m4_endian 's/^	return ((uint32_t)p\[0\] << 24)/	return ((uint32_t)p[3] << 24)/'; \
	 run m4_endian; \
	 echo "--- M5: the version check removed ---"; \
	 mkmut m5_nover 's/if (hdr\[PROTO_RQ_O_VERSION\] != PROTO_VERSION)/if (0)/'; \
	 run m5_nover; \
	 echo "--- M6: the constant-time compare given an early exit ---"; \
	 echo "    (functionally identical, so it MUST NOT be caught -- a unit test"; \
	 echo "     cannot observe a timing side channel; see the report)"; \
	 /usr/bin/python3 $(HERE)mutate.py early $(HERE)session.c $(O)/mut/session_early.c; \
	 if $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/mut/m6_early \
	      $(HERE)test_session.c $(O)/mut/session_early.c $(HERE)ops.c \
	      $(LIB_SRC) $(CFGSRC) $(KDFSRC) $(STUBSRC) $(LIB)/client.c \
	      2>$(O)/mut/m6.cc; then \
	   if $(O)/mut/m6_early > $(O)/mut/m6.out 2>&1; then \
	     echo "  m6_early: NOT CAUGHT -- as predicted before the run."; \
	     missed=$$((missed+1)); \
	   else \
	     echo "  m6_early: CAUGHT (unexpected -- read $(O)/mut/m6.out)"; \
	     caught=$$((caught+1)); \
	   fi; \
	 else \
	   echo "  m6_early: compile failed; see $(O)/mut/m6.cc"; exit 1; \
	 fi; \
	 echo "mutants: $$caught caught, $$missed not caught (6 planted)"; \
	 [ $$caught -ge 5 ] || { echo "REFUSED: fewer than 5 of 6 caught"; exit 1; }

# ------------------------------------------------------------------- fuzzing
AFLCC ?= afl-clang-fast
FUZZ  := $(REPO)/src/fuzz

fuzz: $(O)/host
	@mkdir -p $(O)/fuzz/in $(O)/fuzz/out
	$(AFLCC) -std=gnu99 -Wall -Wextra -Werror -O2 -g $(INCS) \
	  -o $(O)/fuzz/fuzz_proto $(FUZZ)/fuzz_proto.c $(LIB)/proto.c
	@# Clear first: a stale seed left from an earlier corpus silently changes
	@# what the run was given, and the file count is what gets reported.
	@rm -f $(O)/fuzz/in/*
	@cp -f $(FUZZ)/corpus/proto/* $(O)/fuzz/in/
	@a=$$(ls $(FUZZ)/corpus/proto | wc -l); b=$$(ls $(O)/fuzz/in | wc -l); \
	 echo "fuzz harness at $(O)/fuzz/fuzz_proto; corpus $$b files"; \
	 [ "$$a" = "$$b" ] || { echo "REFUSED: staged $$b seeds from a corpus of $$a"; exit 1; }

# The planted defect: body_len bounded at 2049 instead of 2048, i.e. ONE byte
# of overflow past rx->req.body.  ASan turns it into a crash, which is what the
# fuzzer reports.  If afl-fuzz does NOT find it, the harness is not connected
# and any coverage number from the clean run is void.
fuzzdefect: $(O)/host
	@mkdir -p $(O)/fuzz/dmut $(O)/fuzz/din $(O)/fuzz/dout
	/usr/bin/python3 $(HERE)mutate.py off1 $(LIB)/proto.c $(O)/fuzz/dmut/proto_off1.c
	AFL_USE_ASAN=1 $(AFLCC) -std=gnu99 -Wall -Wextra -Werror -O1 -g $(INCS) \
	  -o $(O)/fuzz/fuzz_proto_off1 $(FUZZ)/fuzz_proto.c $(O)/fuzz/dmut/proto_off1.c
	@rm -f $(O)/fuzz/din/*
	@cp -f $(FUZZ)/corpus/proto/* $(O)/fuzz/din/
	@# Pre-screen: a seed that already crashes the mutant would be reported by
	@# AFL as a calibration failure, not as a discovery.  Drop those, and name
	@# them, so the crash the run reports is one the fuzzer made.
	@set -e; dropped=0; kept=0; \
	 for f in $(O)/fuzz/din/*; do \
	   if $(O)/fuzz/fuzz_proto_off1 $$f >/dev/null 2>&1; then kept=$$((kept+1)); \
	   else echo "  pre-screen: DROPPED $$(basename $$f) (already crashes the mutant)"; \
	        rm -f $$f; dropped=$$((dropped+1)); fi; \
	 done; \
	 echo "defect seeds: $$kept kept, $$dropped dropped"; \
	 [ $$kept -gt 0 ] || { echo "REFUSED: every seed crashes; nothing left to fuzz"; exit 1; }
	@echo "defect harness at $(O)/fuzz/fuzz_proto_off1"

# ---------------------------------------------------------------- coverage
cov: $(O)/host
	@mkdir -p $(O)/cov
	$(HOSTCC2) -std=gnu99 -Wall -Wextra -Werror -O0 -g $(INCS) \
	  -fprofile-instr-generate -fcoverage-mapping \
	  -o $(O)/cov/fuzz_proto_cov $(FUZZ)/fuzz_proto.c $(LIB)/proto.c
	@echo "coverage harness at $(O)/cov/fuzz_proto_cov"

# ------------------------------------------------------------- target build
TC    ?=
TRIP  ?=
TSTAGE := $(O)/target/src
TOBJ   := $(O)/target/obj/brokerd
TSCRATCH := $(O)/target/scratch

TCFLAGS := -Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
           -static -fno-builtin -fno-strict-aliasing -fno-common
TLDFLAGS := -static

target:
	@[ -n "$(TC)" ] || { echo "REFUSED: TC=<toolchain root> is required"; exit 1; }
	@[ -n "$(TRIP)" ] || { echo "REFUSED: TRIP=<vendor-tripwire.sh> is required"; exit 1; }
	@[ -x "$(TC)/bin/mips-linux-gcc" ] || { echo "REFUSED: no mips-linux-gcc under $(TC)/bin"; exit 1; }
	@case " $(TCFLAGS) " in *" -march="*) \
	    echo "REFUSED: TCFLAGS carries a -march; this build takes the driver's 4181 default"; exit 1 ;; \
	  esac; echo "no -march in TCFLAGS"
	@case "$(O)" in /mnt/*) \
	    echo "REFUSED: O=$(O) is on DrvFs; the rsdk driver cannot stat() those paths"; exit 1 ;; \
	  esac
	@mkdir -p $(TSTAGE) $(TOBJ) $(TSCRATCH) $(O)/target
	@# G0: stage onto ext4 and prove the copy is the source.
	@# `R7-8`: schema.h, tlv.h, crc32.h and sha256.h joined this list.  The stub
	@# cfg.h was self-contained; the real store is five translation units and
	@# four headers, and gcc 3.4.6 reports a missing include and then KEEPS
	@# GOING, so a short list here shows up as undeclared identifiers.
	@set -e; for f in $(ALL_SRC) $(HERE)brokerd.h $(LIB)/proto.h $(LIB)/client.h \
	     $(CFGINC)/cfg.h $(KDFINC)/kdf.h $(LIB)/schema.h $(LIB)/tlv.h \
	     $(LIB)/crc32.h $(LIB)/sha256.h; do \
	   cp -f $$f $(TSTAGE)/; \
	   a=$$(sha256sum $$f | cut -d' ' -f1); \
	   b=$$(sha256sum $(TSTAGE)/$$(basename $$f) | cut -d' ' -f1); \
	   [ "$$a" = "$$b" ] || { echo "REFUSED: the staged copy of $$f is not the source"; exit 1; }; \
	 done
	@echo "staged $$(ls $(TSTAGE) | wc -l) files onto ext4, every hash equal to the repo's"
	@set -e; cd $(TSCRATCH) && $(TRIP) -- $(MAKE) --no-print-directory \
	   -f $(HERE)Makefile O=$(O) TC=$(TC) target-compile
	@echo "--- hazlint over the linked ELF ---"
	@HAZLINT_CHILD=1 /usr/bin/python3 $(REPO)/tools/hazlint $(O)/target/brokerd
	@echo "--- no system/popen/shell symbol in the artefact, detector shown firing first ---"
	@# THE POSITIVE CONTROL is a linked ELF that really does call system() and
	@# popen(): if the detector cannot see it there, its 0 on brokerd means
	@# nothing.  Built with the same compiler and the same static libc.
	@set -e; cd $(TSCRATCH) && printf '%s\n' \
	   '#include <stdio.h>' '#include <stdlib.h>' \
	   'int main(void){ FILE *f = popen("x", "r"); (void)f; return system("x"); }' \
	   > ctl.c && $(TC)/bin/mips-linux-gcc -Os -static -o ctl ctl.c
	@pat=' (T|t|U|W) (system|popen|execl|execlp|execv|execvp|execvpe)$$'; \
	 c=$$($(TC)/bin/mips-linux-nm $(TSCRATCH)/ctl | grep -cE "$$pat" || true); \
	 echo "control ELF (calls system+popen): $$c matching symbols"; \
	 [ "$$c" -ge 2 ] || { echo "REFUSED: the detector cannot see system/popen in an ELF that calls them"; exit 1; }; \
	 n=$$($(TC)/bin/mips-linux-nm $(O)/target/brokerd | grep -cE "$$pat" || true); \
	 echo "brokerd: $$n matching symbols"; \
	 [ "$$n" = "0" ] || { echo "REFUSED: a shell-invoking symbol is linked into brokerd"; \
	   $(TC)/bin/mips-linux-nm $(O)/target/brokerd | grep -E "$$pat"; exit 1; }
	@# And the string, with its own control: /bin/sh must not be in the image.
	@s=$$(grep -a -c -F '/bin/sh' $(TSCRATCH)/ctl || true); \
	 b=$$(grep -a -c -F '/bin/sh' $(O)/target/brokerd || true); \
	 echo "'/bin/sh' string: control=$$s brokerd=$$b"; \
	 [ "$$s" -ge 1 ] || { echo "REFUSED: the string counter cannot see /bin/sh in the control"; exit 1; }; \
	 [ "$$b" = "0" ] || { echo "REFUSED: brokerd carries the string /bin/sh"; exit 1; }
	@$(TC)/bin/mips-linux-readelf -h $(O)/target/brokerd | \
	   grep -qE "big endian" || { echo "REFUSED: not big-endian"; exit 1; }
	@[ "$$($(TC)/bin/mips-linux-readelf -l $(O)/target/brokerd | grep -c INTERP)" = "0" ] \
	   || { echo "REFUSED: a PT_INTERP in a static build"; exit 1; }
	@$(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) TC=$(TC) target-show

# Runs INSIDE the tripwire, with cwd in $O/target/scratch.
target-compile:
	@set -e; for c in $(notdir $(ALL_SRC)); do \
	   o=$(TOBJ)/$${c%.c}.o; \
	   $(TC)/bin/mips-linux-gcc $(TCFLAGS) -I$(TSTAGE) -c $(TSTAGE)/$$c -o $$o; \
	   echo "  CC $$c -> $$o"; \
	 done
	$(TC)/bin/mips-linux-gcc $(TLDFLAGS) -o $(O)/target/brokerd $(TOBJ)/*.o
	cp -f $(O)/target/brokerd $(O)/target/brokerd.stripped
	$(TC)/bin/mips-linux-strip $(O)/target/brokerd.stripped

target-show:
	@echo "objects   $$(ls $(TOBJ)/*.o | wc -l) in $(TOBJ)"
	@echo "elf       $$(wc -c < $(O)/target/brokerd) bytes"
	@echo "stripped  $$(wc -c < $(O)/target/brokerd.stripped) bytes"
	@echo "sha256    $$(sha256sum $(O)/target/brokerd.stripped | cut -d' ' -f1)"
	@echo "machine   $$($(TC)/bin/mips-linux-readelf -h $(O)/target/brokerd | awk -F: '/Machine|Data/{print $$2}' | tr -d ' ' | paste -sd, -)"
	@echo "cfg       $(WHICHCFG)"

show:
	@echo "REPO      $(REPO)"
	@echo "O         $(O)"
	@echo "cfg hdr   $(WHICHCFG)"
	@echo "sources   $(ALL_SRC)"
	@echo "tests     $(TESTS)"

clean:
	rm -rf $(O)/host $(O)/mut $(O)/fuzz $(O)/cov $(O)/target
