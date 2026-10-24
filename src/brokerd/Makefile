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
CFGSRC   := $(LIB)/cfg.c $(LIB)/schema.c $(LIB)/tlv.c $(LIB)/crc32.c $(LIB)/cfgflash.c $(LIB)/spictl.c
KDFSRC   := $(LIB)/kdf.c $(LIB)/sha256.c
STUBSRC  :=
WHICHCFG := src/lib/cfg.h

INCS := -I$(HERE) -I$(LIB) -I$(CFGINC) -I$(KDFINC)

# brokerd's own sources, and the library sources it needs.
BK_SRC  := $(HERE)main.c $(HERE)session.c $(HERE)ops.c $(HERE)update.c \
           $(HERE)loop.c
LIB_SRC := $(LIB)/proto.c

# notes/self-update.md § 4.3: rlxboot's verifier, LINKED UNCHANGED -- the five
# files src/rlxboot/test/run-qemu-tests.sh already builds as a uClibc program
# with this toolchain.  No file of them is edited to link here (container.c is
# a BUILD_ID input); what differs is all in this file: ed25519.c's one
# exemption (src/rlxboot/Makefile's ED_EXEMPT, for the same imported line),
# and the target staging, which keeps rlxboot/ and lib/ as directories because
# container.c includes "../lib/ed25519.h" and update.c "../rlxboot/*.h".
# ED25519_SIGN and ED25519_KEYGEN are defined nowhere here; the target rule
# reads the artefact for a signer.
RLXB      := $(REPO)/src/rlxboot
UPD_SRC   := $(RLXB)/container.c $(RLXB)/slots.c $(RLXB)/sha256b.c $(LIB)/sha512.c
ED_SRC    := $(LIB)/ed25519.c
ED_EXEMPT := -Wno-sign-compare

# FLAT_SRC is staged flat for the target (every one of them includes its
# headers by bare name); ALL_SRC is everything a host brokerd compiles but
# ed25519.c, which each build compiles alone, with its exemption.
FLAT_SRC := $(BK_SRC) $(LIB_SRC) $(CFGSRC) $(KDFSRC) $(STUBSRC)
ALL_SRC  := $(FLAT_SRC) $(UPD_SRC)

# Everything but main.c, for the tests to link against.
OBJ_NOMAIN_SRC := $(HERE)session.c $(HERE)ops.c $(HERE)update.c $(HERE)loop.c \
                  $(LIB_SRC) $(CFGSRC) $(KDFSRC) $(STUBSRC) $(LIB)/client.c \
                  $(UPD_SRC)

TESTS := test_proto test_authz test_session test_ratelimit test_entropy \
         test_ping test_wire test_reload test_update test_update_prod test_e2e

# The update path's suites run against src/cfgstore/simkern.c, a simulated
# rtl819x-spi built from the kernel's own install header (3S's, linked here
# unchanged), so they link with its --wrap list.  test_update_prod is
# test_update.c compiled WITHOUT BK_UPD_KEY_DEV: update.c then holds
# src/rlxboot/prodkey.h, the device's key.  test_e2e adds httpd's request path:
# its six sources, compiled with httpd's own warning set (src/httpd/Makefile's
# HCFLAGS, restated in E2E_HFLAGS: a drift there changes this test's compile
# only, never httpd's build).
CFGSTORE   := $(REPO)/src/cfgstore
HTTPD      := $(REPO)/src/httpd
KDEV       := $(REPO)/kernel/linux-2.6.30/drivers/mtd/devices
SIMK_SRC   := $(CFGSTORE)/simkern.c
SIMK_INC   := -I$(CFGSTORE) -I$(KDEV)
SIMK_WRAP  := -Wl,--wrap=open,--wrap=close,--wrap=write,--wrap=flock,--wrap=nanosleep,--wrap=lseek
E2E_HSRC   := $(HTTPD)/serve.c $(HTTPD)/upload.c $(HTTPD)/routes.c \
              $(HTTPD)/rl.c $(HTTPD)/http.c $(LIB)/json.c
E2E_HFLAGS := -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
              -Wno-unused-parameter -O1 -g -I$(HTTPD) -I$(LIB)
PYTHON     ?= /usr/bin/python3

# `FW-184`: test_reload changes the password through the real cfgstore, so the
# host build makes one, from the sources the image's cfgstore is made from.
CFGSTORE_SRC := $(REPO)/src/cfgstore/main.c $(CFGSRC) $(KDFSRC)

# ---------------------------------------------------------------- host build
HOSTCC   ?= gcc-13
HOSTCC2  ?= clang-18
# BK_UPD_KEY_DEV: the host build trusts the DEVELOPMENT key (update.c), as
# rlxboot's host suite does.  HPFLAGS is the same set without it, so update.c
# compiles in src/rlxboot/prodkey.h, as the target build does.
HCFLAGS  := -std=gnu99 -Wall -Wextra -Werror -O1 -g $(INCS) -DBK_UPD_KEY_DEV
HPFLAGS  := $(filter-out -DBK_UPD_KEY_DEV,$(HCFLAGS))
SANFLAGS := -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: all host test sanitize mutants mutants-update fixtures fuzz fuzzrun \
        cov target clean show

all: host

$(O)/host:
	@mkdir -p $@

# `bt CC EXTRA TAG TEST` builds $(O)/host/TEST$(TAG): the generic link, the
# simkern suites' (their include paths and --wrap list), or the e2e's (with
# httpd's objects for TAG, from `objs`).  `objs CC EXTRA TAG` makes ed25519's
# object, with its one exemption, and httpd's six for the e2e.  Shell
# functions, as `mutants` below writes its own.
BT = bt() { cc=$$1; ex=$$2; tag=$$3; t=$$4; o=$(O)/host/$$t$$tag; \
  ed=$(O)/host/ed25519$$tag.o; \
  case $$t in \
  test_update) $$cc $(HCFLAGS) $$ex $(SIMK_INC) -o $$o $(HERE)test_update.c \
    $(OBJ_NOMAIN_SRC) $(SIMK_SRC) $$ed $(SIMK_WRAP) ;; \
  test_update_prod) $$cc $(HPFLAGS) $$ex $(SIMK_INC) -o $$o $(HERE)test_update.c \
    $(OBJ_NOMAIN_SRC) $(SIMK_SRC) $$ed $(SIMK_WRAP) ;; \
  test_e2e) $$cc $(HCFLAGS) $$ex $(SIMK_INC) -o $$o $(HERE)test_e2e.c \
    $(OBJ_NOMAIN_SRC) $(SIMK_SRC) $(O)/host/e2e$$tag/*.o $$ed $(SIMK_WRAP) ;; \
  *) $$cc $(HCFLAGS) $$ex -o $$o $(HERE)$$t.c $(OBJ_NOMAIN_SRC) $$ed ;; \
  esac; }; \
  objs() { cc=$$1; ex=$$2; tag=$$3; mkdir -p $(O)/host/e2e$$tag; \
  $$cc $(HCFLAGS) $$ex $(ED_EXEMPT) -c -o $(O)/host/ed25519$$tag.o $(ED_SRC); \
  for s in $(E2E_HSRC); do b=$$(basename $$s .c); \
    $$cc $(E2E_HFLAGS) $$ex -c -o $(O)/host/e2e$$tag/$$b.o $$s || return 1; \
  done; }

host: $(O)/host
	@echo "cfg header: $(WHICHCFG)"
	@set -e; $(BT); objs $(HOSTCC) "" ""; objs $(HOSTCC2) "" .clang
	$(HOSTCC) $(HCFLAGS) -o $(O)/host/brokerd $(ALL_SRC) $(O)/host/ed25519.o
	$(HOSTCC2) $(HCFLAGS) -o $(O)/host/brokerd.clang $(ALL_SRC) \
	  $(O)/host/ed25519.clang.o
	$(HOSTCC) $(HCFLAGS) -o $(O)/host/pinghelp $(HERE)test_pinghelp.c
	$(HOSTCC) $(HCFLAGS) -DPINGHELP_SLOW=1 -o $(O)/host/pinghelp_slow $(HERE)test_pinghelp.c
	$(HOSTCC) $(HCFLAGS) -o $(O)/host/cfgstore $(CFGSTORE_SRC)
	@set -e; $(BT); for t in $(TESTS); do \
	   bt $(HOSTCC) "" "" $$t; \
	   bt $(HOSTCC2) "" .clang $$t; \
	 done
	@echo "host build ok: $(HOSTCC) and $(HOSTCC2), -Wall -Wextra -Werror"

# The containers test_update and test_e2e read: tools/mkfw2.py, the
# development seed (mkfix.sh says which is which).
fixtures:
	@mkdir -p $(O)/run
	@PYTHON=$(PYTHON) HOSTCC=$(HOSTCC) sh $(HERE)mkfix.sh $(REPO) $(O)/fix

# `test` runs the suite twice: the plain build and the sanitizer build.  A
# refusing suite is fast, so the count of what ran is printed beside the time.
#
# TESTS_MIN is the number of test programs, MEASURED 2026-10-17: the eight in
# TESTS (test_pinghelp.c is test_ping's helper, not a test).  It is typed rather
# than counted from TESTS, the list it guards, so a list that loses one REFUSES
# -- per compiler here and in `sanitize` -- instead of passing with fewer.  Each
# run prints one `ok` or `FAIL` line indented by exactly two spaces, the shape
# tools/ci-census.py counts in CI; the first failure still stops the run.
# 2026-10-23 (s144, P6r-10): eleven -- test_update, test_update_prod, test_e2e.
TESTS_MIN := 11

test: host fixtures
	@set -e; n=0; \
	 for t in $(TESTS); do \
	   echo "=== $$t (gcc-13) ==="; \
	   case $$t in \
	     test_ping) set -- $(O)/host/$$t $(O)/host/pinghelp $(O)/host/pinghelp_slow ;; \
	     test_wire) set -- $(O)/host/$$t $(O)/host/brokerd ;; \
	     test_reload) set -- $(O)/host/$$t $(O)/host/cfgstore ;; \
	     test_update|test_update_prod|test_e2e) \
	       set -- $(O)/host/$$t $(O)/fix $(O)/run/$$t ;; \
	     *)         set -- $(O)/host/$$t ;; \
	   esac; \
	   if "$$@"; then printf '  ok    brokerd/%s %s\n' "$$t" "$(HOSTCC)"; \
	   else printf '  FAIL  brokerd/%s %s\n' "$$t" "$(HOSTCC)"; exit 1; fi; \
	   n=$$((n+1)); \
	 done; \
	 for t in $(TESTS); do \
	   echo "=== $$t (clang-18) ==="; \
	   case $$t in \
	     test_ping) set -- $(O)/host/$$t.clang $(O)/host/pinghelp $(O)/host/pinghelp_slow ;; \
	     test_wire) set -- $(O)/host/$$t.clang $(O)/host/brokerd.clang ;; \
	     test_reload) set -- $(O)/host/$$t.clang $(O)/host/cfgstore ;; \
	     test_update|test_update_prod|test_e2e) \
	       set -- $(O)/host/$$t.clang $(O)/fix $(O)/run/$$t.clang ;; \
	     *)         set -- $(O)/host/$$t.clang ;; \
	   esac; \
	   if "$$@"; then printf '  ok    brokerd/%s %s\n' "$$t" "$(HOSTCC2)"; \
	   else printf '  FAIL  brokerd/%s %s\n' "$$t" "$(HOSTCC2)"; exit 1; fi; \
	   n=$$((n+1)); \
	 done; \
	 [ $$n -ge $$((2 * $(TESTS_MIN))) ] || { \
	   echo "REFUSED: brokerd ran $$n test binaries; the floor is" \
	        "$$((2 * $(TESTS_MIN))) -- $(TESTS_MIN) measured test programs under" \
	        "each of two compilers"; exit 1; }; \
	 echo "PASS: $$n test binaries ran (both compilers)"
	@$(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) sanitize

sanitize: $(O)/host fixtures
	@set -e; $(BT); objs $(HOSTCC2) "$(SANFLAGS)" .san; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/brokerd.san $(ALL_SRC) \
	   $(O)/host/ed25519.san.o; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/pinghelp.san $(HERE)test_pinghelp.c; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -DPINGHELP_SLOW=1 -o $(O)/host/pinghelp_slow.san $(HERE)test_pinghelp.c; \
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/host/cfgstore.san $(CFGSTORE_SRC); \
	 n=0; \
	 for t in $(TESTS); do \
	   bt $(HOSTCC2) "$(SANFLAGS)" .san $$t; \
	 done; \
	 for t in $(TESTS); do \
	   echo "=== $$t (clang-18 asan+ubsan) ==="; \
	   case $$t in \
	     test_ping) set -- $(O)/host/$$t.san $(O)/host/pinghelp.san $(O)/host/pinghelp_slow.san ;; \
	     test_wire) set -- $(O)/host/$$t.san $(O)/host/brokerd.san ;; \
	     test_reload) set -- $(O)/host/$$t.san $(O)/host/cfgstore.san ;; \
	     test_update|test_update_prod|test_e2e) \
	       set -- $(O)/host/$$t.san $(O)/fix $(O)/run/$$t.san ;; \
	     *)         set -- $(O)/host/$$t.san ;; \
	   esac; \
	   if "$$@"; then printf '  ok    brokerd/%s %s+san\n' "$$t" "$(HOSTCC2)"; \
	   else printf '  FAIL  brokerd/%s %s+san\n' "$$t" "$(HOSTCC2)"; exit 1; fi; \
	   n=$$((n+1)); \
	 done; \
	 [ $$n -ge $(TESTS_MIN) ] || { \
	   echo "REFUSED: brokerd ran $$n sanitized test binaries; the floor is" \
	        "$(TESTS_MIN), the measured count"; exit 1; }; \
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
	 $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) $(ED_EXEMPT) -c -o $(O)/mut/ed25519.o $(ED_SRC); \
	 if $(HOSTCC2) $(HCFLAGS) $(SANFLAGS) -o $(O)/mut/m6_early \
	      $(HERE)test_session.c $(O)/mut/session_early.c $(HERE)ops.c \
	      $(HERE)update.c $(LIB_SRC) $(CFGSRC) $(KDFSRC) $(STUBSRC) \
	      $(LIB)/client.c $(UPD_SRC) $(O)/mut/ed25519.o \
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
	@$(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) mutants-update

# The update path's controls (notes/self-update.md § 4.8), mutate.py's way: a
# named defect planted in a COPY of update.c or loop.c, exactly one anchor,
# compiled with the real flags (-Werror included -- a mutant that does not
# compile REFUSES the run, because a mutant that does not build is not a
# kill), linked as test_update is, and required to make test_update FAIL.
# The unmutated suite runs first and must pass.
UPD_MUTANTS := upd_stage_early:update.c upd_no_handoff_begin:update.c \
               upd_no_handoff_end:update.c upd_install_undelivered:loop.c \
               upd_reboot_failed:update.c upd_no_nwrites:update.c \
               upd_env_loose_self:update.c upd_env_loose_ldr:update.c \
               upd_no_poison:update.c
UPD_MUTANTS_N := 9

mutants-update: host fixtures $(O)/mut
	@set -e; \
	 echo "--- control: the UNMUTATED test_update must pass first ---"; \
	 $(O)/host/test_update $(O)/fix $(O)/mut/upd_control > $(O)/mut/upd_control.out 2>&1 \
	   || { echo "REFUSED: the unmutated test_update fails; a mutation run would prove nothing"; \
	        tail -20 $(O)/mut/upd_control.out; exit 1; }; \
	 echo "control: test_update passes ($$(grep -c '^  FAIL' $(O)/mut/upd_control.out || true) FAIL lines)"; \
	 caught=0; n=0; \
	 for m in $(UPD_MUTANTS); do \
	   name=$${m%%:*}; file=$${m#*:}; d=$(O)/mut/$$name; mkdir -p $$d; \
	   /usr/bin/python3 $(HERE)mutate.py $$name $(HERE)$$file $$d/$$file >/dev/null; \
	   srcs=$$(echo " $(OBJ_NOMAIN_SRC) " | sed "s# $(HERE)$$file # $$d/$$file #"); \
	   case "$$srcs" in *" $$d/$$file "*) ;; \
	     *) echo "REFUSED: $$name: $$file is not in the link"; exit 1 ;; esac; \
	   if ! $(HOSTCC) $(HCFLAGS) $(SIMK_INC) -o $$d/test_update $(HERE)test_update.c \
	        $$srcs $(SIMK_SRC) $(O)/host/ed25519.o $(SIMK_WRAP) 2>$$d/cc.out; then \
	     echo "REFUSED: mutant $$name does not compile (not a kill):"; \
	     head -5 $$d/cc.out; exit 1; \
	   fi; \
	   n=$$((n+1)); \
	   if $$d/test_update $(O)/fix $$d/run > $$d/out 2>&1; then \
	     echo "  $$name: *** NOT CAUGHT *** (test_update still passes)"; \
	   else \
	     echo "  $$name: CAUGHT ($$(grep -c '^  FAIL' $$d/out || true) FAIL lines)"; \
	     caught=$$((caught+1)); \
	   fi; \
	 done; \
	 echo "mutants-update: $$caught of $$n caught"; \
	 [ $$n = $(UPD_MUTANTS_N) ] && [ $$caught = $$n ] || \
	   { echo "REFUSED: $$caught of $$n caught, want all $(UPD_MUTANTS_N)"; exit 1; }

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
# rlxboot's three and lib's two, staged as the directories they are in the
# repository, beside TSTAGE: container.c's "../lib/ed25519.h" and update.c's
# "../rlxboot/container.h" then resolve exactly as they do in src/.
TRLXB := $(O)/target/rlxboot
TLIBD := $(O)/target/lib
RLXB_STAGE := $(RLXB)/container.c $(RLXB)/container.h $(RLXB)/slots.c \
              $(RLXB)/slots.h $(RLXB)/sha256b.c $(RLXB)/sha256b.h \
              $(RLXB)/rlxboot.h $(RLXB)/prodkey.h $(RLXB)/devkey.h
LIBD_STAGE := $(LIB)/ed25519.c $(LIB)/ed25519.h $(LIB)/sha512.c $(LIB)/sha512.h
SIGNER_PAT := rlx_ed25519_sign|rlx_ed25519_pubkey_from_seed|crypto_sign

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
	@case " $(TCFLAGS) " in *BK_UPD_KEY_DEV*) \
	    echo "REFUSED: TCFLAGS names BK_UPD_KEY_DEV; the device's brokerd trusts src/rlxboot/prodkey.h"; exit 1 ;; \
	  esac
	@# D15's gate, rlxboot's own: the key header holds one key, not the
	@# development key, on the curve.  update.c's #error is the second fence.
	@$(PYTHON) -B $(RLXB)/mkprodkey.py check $(RLXB)/prodkey.h
	@case "$(O)" in /mnt/*) \
	    echo "REFUSED: O=$(O) is on DrvFs; the rsdk driver cannot stat() those paths"; exit 1 ;; \
	  esac
	@mkdir -p $(TSTAGE) $(TOBJ) $(TSCRATCH) $(O)/target $(TRLXB) $(TLIBD)
	@# G0: stage onto ext4 and prove the copy is the source.
	@# `R7-8`: schema.h, tlv.h, crc32.h and sha256.h joined this list.  The stub
	@# cfg.h was self-contained; the real store is five translation units and
	@# four headers, and gcc 3.4.6 reports a missing include and then KEEPS
	@# GOING, so a short list here shows up as undeclared identifiers.
	@set -e; for f in $(FLAT_SRC) $(HERE)brokerd.h $(LIB)/proto.h $(LIB)/client.h \
	     $(CFGINC)/cfg.h $(KDFINC)/kdf.h $(LIB)/schema.h $(LIB)/tlv.h \
	     $(LIB)/crc32.h $(LIB)/sha256.h $(LIB)/spictl.h; do \
	   cp -f $$f $(TSTAGE)/; \
	   a=$$(sha256sum $$f | cut -d' ' -f1); \
	   b=$$(sha256sum $(TSTAGE)/$$(basename $$f) | cut -d' ' -f1); \
	   [ "$$a" = "$$b" ] || { echo "REFUSED: the staged copy of $$f is not the source"; exit 1; }; \
	 done
	@set -e; for f in $(RLXB_STAGE); do d=$(TRLXB); \
	   cp -f $$f $$d/; \
	   [ "$$(sha256sum < $$f)" = "$$(sha256sum < $$d/$$(basename $$f))" ] || \
	     { echo "REFUSED: the staged copy of $$f is not the source"; exit 1; }; \
	 done; \
	 for f in $(LIBD_STAGE); do d=$(TLIBD); \
	   cp -f $$f $$d/; \
	   [ "$$(sha256sum < $$f)" = "$$(sha256sum < $$d/$$(basename $$f))" ] || \
	     { echo "REFUSED: the staged copy of $$f is not the source"; exit 1; }; \
	 done
	@echo "staged $$(ls $(TSTAGE) | wc -l) files flat, $$(ls $(TRLXB) | wc -l) in rlxboot/ and $$(ls $(TLIBD) | wc -l) in lib/, every hash equal to the repo's"
	@set -e; cd $(TSCRATCH) && $(TRIP) -- $(MAKE) --no-print-directory \
	   -f $(HERE)Makefile O=$(O) TC=$(TC) target-compile
	@echo "--- which key the artefact holds, the scanner shown seeing one first ---"
	@k=$$($(PYTHON) -B $(HERE)keyscan.py $(TSCRATCH)/update-devkey.o $(RLXB)/devkey.h); \
	 p=$$($(PYTHON) -B $(HERE)keyscan.py $(O)/target/brokerd.stripped $(RLXB)/prodkey.h); \
	 d=$$($(PYTHON) -B $(HERE)keyscan.py $(O)/target/brokerd.stripped $(RLXB)/devkey.h); \
	 echo "control (update.c built with BK_UPD_KEY_DEV): devkey $$k; brokerd: prodkey $$p, devkey $$d"; \
	 [ "$$k" -ge 1 ] 2>/dev/null || { echo "REFUSED: the scanner cannot see the development key in an object that holds it"; exit 1; }; \
	 [ "$$p" -ge 1 ] 2>/dev/null || { echo "REFUSED: brokerd does not hold src/rlxboot/prodkey.h's key"; exit 1; }; \
	 [ "$$d" = 0 ] || { echo "REFUSED: brokerd holds the development key"; exit 1; }
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
	@set -e; for c in $(notdir $(FLAT_SRC)); do \
	   o=$(TOBJ)/$${c%.c}.o; \
	   $(TC)/bin/mips-linux-gcc $(TCFLAGS) -I$(TSTAGE) -c $(TSTAGE)/$$c -o $$o; \
	   echo "  CC $$c -> $$o"; \
	 done
	@set -e; for c in container slots sha256b; do \
	   $(TC)/bin/mips-linux-gcc $(TCFLAGS) -c $(TRLXB)/$$c.c -o $(TOBJ)/$$c.o; \
	   echo "  CC rlxboot/$$c.c -> $(TOBJ)/$$c.o"; \
	 done
	$(TC)/bin/mips-linux-gcc $(TCFLAGS) -c $(TLIBD)/sha512.c -o $(TOBJ)/sha512.o
	$(TC)/bin/mips-linux-gcc $(TCFLAGS) $(ED_EXEMPT) -c $(TLIBD)/ed25519.c -o $(TOBJ)/ed25519.o
	$(TC)/bin/mips-linux-gcc $(TLDFLAGS) -o $(O)/target/brokerd $(TOBJ)/*.o
	cp -f $(O)/target/brokerd $(O)/target/brokerd.stripped
	$(TC)/bin/mips-linux-strip $(O)/target/brokerd.stripped
	@# No signer in the device's brokerd: ED25519_SIGN and ED25519_KEYGEN are
	@# defined nowhere in this file, and this reads the artefact rather than
	@# the flags, as src/rlxboot/Makefile does for its payload.  The control is
	@# the same ed25519.c compiled WITH both: the detector must see them there.
	@$(TC)/bin/mips-linux-gcc $(TCFLAGS) $(ED_EXEMPT) -DED25519_SIGN -DED25519_KEYGEN \
	   -c $(TLIBD)/ed25519.c -o $(TSCRATCH)/ed25519-signer.o
	@c=$$($(TC)/bin/mips-linux-nm $(TSCRATCH)/ed25519-signer.o | grep -cE '$(SIGNER_PAT)' || true); \
	 n=$$($(TC)/bin/mips-linux-nm $(O)/target/brokerd | grep -cE '$(SIGNER_PAT)' || true); \
	 echo "signer symbols: control (ED25519_SIGN, ED25519_KEYGEN) $$c, brokerd $$n"; \
	 [ "$$c" -ge 2 ] || { echo "REFUSED: the detector cannot see a signer in an object that has one"; exit 1; }; \
	 [ "$$n" = 0 ] || { echo "REFUSED: brokerd links a signer"; exit 1; }
	@# The key scan's control (see `target`): update.c with the development key.
	@$(TC)/bin/mips-linux-gcc $(TCFLAGS) -DBK_UPD_KEY_DEV -I$(TSTAGE) \
	   -c $(TSTAGE)/update.c -o $(TSCRATCH)/update-devkey.o

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
	rm -rf $(O)/host $(O)/mut $(O)/fuzz $(O)/cov $(O)/target $(O)/fix $(O)/run
