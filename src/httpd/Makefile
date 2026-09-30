# src/httpd/Makefile -- host build, host tests, sanitizers, fuzzers, coverage,
# the chroot-tree check, and the big-endian MIPS target build.
#
# The target half follows config/rlxfw-user/linkprobe/Makefile, which owns the
# reasons this one repeats without restating them: the rsdk compiler is a 32-bit
# i386 ELF whose stat() returns EOVERFLOW on every DrvFs path, so the sources are
# staged onto ext4 and the staged copy is proved equal to the repository's by
# sha256 before anything is compiled; the compiler runs only under
# tools/vendor-tripwire.sh; and CFLAGS carries NO -march at all, because the
# wrapper's default is the 4181 core and -march=mips32 miscompiles the exposed
# load delay slot silently.
#
# O= is required by every target and must be absolute (SPEC-R7 section 2).
#
# Targets
#   host       $(O)/host/httpd and every test binary
#   test       run the tests; non-zero exit on the first failure
#   asan       the tests under -fsanitize=address,undefined
#   both       the whole host build under gcc-13 AND clang-18, each also sanitized
#   fuzz       the two afl++ harnesses
#   cov        gcov-instrumented copies of the same two harnesses
#   mutate     the two mutation controls: a check is removed, the suite must go red
#   chrootcheck    walk ROOT= and refuse an ELF, a symlink, a setuid bit, a device
#   target     the static big-endian MIPS ELF, its objects, and hazlint over it

SHELL      := /bin/sh
HERE       := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO       := $(abspath $(HERE)../..)
LIB        := $(REPO)/src/lib

PYTHON     ?= /usr/bin/python3
HAZLINT    := $(REPO)/tools/hazlint

ifeq ($(strip $(O)),)
$(error O= is required and must be an absolute output directory)
endif

# ---------------------------------------------------------------- the sources
# stub/client.c stands in for src/lib/client.c: both implement SPEC-R7 section 6's
# wire format, so the conditional below switches to the real one the moment it
# exists, with no edit here.
#
# stub/cfgtab.c is GONE (`R7-8`).  It was a second transcription of SPEC-R7 § 4's
# key table, kept because src/lib/schema.h exposed the table only as
# `extern const struct cfg_key cfg_keys[CFG_NKEYS]` and not as the accessors
# routes.c calls.  量 `R7-8`: the two transcriptions were identical on all
# sixteen rows in every column either of them carried, and the reconciliation was
# done by compiling both tables and diffing their dumps, not by eye.  The three
# accessors (cfg_key_at, cfg_key_by_id, cfg_key_by_name) now live in
# src/lib/schema.c, so httpd links schema.c + tlv.c -- and NOT cfg.c, which is
# the store.  A build of httpd that reached cfg_load or cfg_store still fails to
# link, which is the guard src/httpd/stub/cfg.h used to provide by omission.
SRC_CORE   := $(HERE)routes.c $(HERE)rl.c $(HERE)http.c $(LIB)/json.c \
              $(LIB)/schema.c $(LIB)/tlv.c
ifeq ($(wildcard $(LIB)/client.c),)
$(error REFUSED: $(LIB)/client.c is absent and src/httpd/stub/client.c is gone)
endif
SRC_CLIENT := $(LIB)/client.c $(LIB)/proto.c
SRC_KDF    := $(LIB)/sha256.c $(LIB)/kdf.c

# Tests that bring their own bk_call (so they must not link the real one):
TESTS_FAKE := test_routes test_serve
# Tests that link the real client but never call it:
TESTS_PLAIN:= test_http test_json test_rl

# ------------------------------------------------------------------- host side
HOSTCC     ?= gcc-13
HCFLAGS    := -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
              -Wno-unused-parameter -O1 -g -I$(HERE) -I$(LIB)
SANFLAGS   := -fsanitize=address,undefined -fno-omit-frame-pointer
HOST_OUT   := $(O)/host

# The mutants are built WITHOUT -Werror.  Removing a check leaves the variable it
# read unused, and a mutant that will not compile is a control that never ran --
# the very failure mode these controls exist to catch.  Nothing built with these
# flags is ever installed or measured; it is compiled, run, and required to fail.
MCFLAGS    := $(filter-out -Werror,$(HCFLAGS)) \
              -Wno-unused-but-set-variable -Wno-unused-variable \
              -Wno-unused-function -Wno-unused-value

.PHONY: all host test asan both fuzz cov mutate chrootcheck rootcheck target \
        target-real targetkdf targetkdf-real kdfbench kdfbench-target show clean

all: host

host:
	@mkdir -p $(HOST_OUT)
	$(HOSTCC) $(HCFLAGS) $(EXTRA) -o $(HOST_OUT)/httpd \
	  $(HERE)main.c $(HERE)serve.c $(SRC_CORE) $(SRC_CLIENT)
	@set -e; for b in $(TESTS_PLAIN); do \
	   $(HOSTCC) $(HCFLAGS) $(EXTRA) -o $(HOST_OUT)/$$b \
	     $(HERE)$$b.c $(SRC_CORE) $(SRC_CLIENT); \
	 done
	@set -e; for b in $(TESTS_FAKE); do \
	   $(HOSTCC) $(HCFLAGS) $(EXTRA) -o $(HOST_OUT)/$$b \
	     $(HERE)$$b.c $(HERE)serve.c $(SRC_CORE); \
	 done
	@if [ -f $(LIB)/kdf.c ] && [ -f $(HERE)test_kdf.c ]; then \
	   $(HOSTCC) $(HCFLAGS) $(EXTRA) -o $(HOST_OUT)/test_kdf \
	     $(HERE)test_kdf.c $(SRC_KDF) || exit 1; \
	 else echo "note: src/lib/kdf.c or test_kdf.c absent -- test_kdf not built"; fi
	@echo "host build in $(HOST_OUT) (CC=$(HOSTCC) EXTRA=$(EXTRA))"

test: host
	@fail=0; ran=0; \
	 for b in test_json test_http test_rl test_routes test_serve test_kdf; do \
	   [ -x $(HOST_OUT)/$$b ] || continue; \
	   echo "=== $$b ==="; \
	   $(HOST_OUT)/$$b || fail=1; \
	   ran=$$((ran + 1)); \
	 done; \
	 echo "--- $$ran test programs ran ---"; \
	 [ $$ran -ge 5 ] || { echo "REFUSED: fewer than five test programs ran"; \
	                      exit 1; }; \
	 [ $$fail = 0 ] || { echo "SUITE FAILED"; exit 1; }; \
	 echo "SUITE PASSED ($$ran programs)"

asan:
	@$(MAKE) --no-print-directory -C $(HERE) test O=$(O)/asan \
	  HOSTCC=$(HOSTCC) EXTRA="$(SANFLAGS)"

both:
	@$(MAKE) --no-print-directory -C $(HERE) test O=$(O)/gcc   HOSTCC=gcc-13
	@$(MAKE) --no-print-directory -C $(HERE) test O=$(O)/clang HOSTCC=clang-18
	@$(MAKE) --no-print-directory -C $(HERE) test O=$(O)/gccsan \
	  HOSTCC=gcc-13 EXTRA="$(SANFLAGS)"
	@$(MAKE) --no-print-directory -C $(HERE) test O=$(O)/clangsan \
	  HOSTCC=clang-18 EXTRA="$(SANFLAGS)"
	@echo "gcc-13 and clang-18, each plain and with address+undefined: clean"

# ------------------------------------------------------------------- fuzzing
AFLCC      ?= afl-clang-fast
FCFLAGS    := -std=gnu99 -Wall -Wextra -Werror -Wno-unused-parameter -O2 -g \
              -I$(HERE) -I$(LIB)

fuzz:
	@mkdir -p $(O)/fuzz
	$(AFLCC) $(FCFLAGS) $(EXTRA) -o $(O)/fuzz/fuzz_http \
	  $(REPO)/src/fuzz/fuzz_http.c $(HERE)http.c
	$(AFLCC) $(FCFLAGS) $(EXTRA) -o $(O)/fuzz/fuzz_json \
	  $(REPO)/src/fuzz/fuzz_json.c $(LIB)/json.c
	@echo "afl harnesses in $(O)/fuzz"

cov:
	@mkdir -p $(O)/cov
	cd $(O)/cov && $(HOSTCC) -std=gnu99 -O0 -g --coverage -I$(HERE) -I$(LIB) \
	  -o cov_http $(REPO)/src/fuzz/fuzz_http.c $(HERE)http.c
	cd $(O)/cov && $(HOSTCC) -std=gnu99 -O0 -g --coverage -I$(HERE) -I$(LIB) \
	  -o cov_json $(REPO)/src/fuzz/fuzz_json.c $(LIB)/json.c
	@echo "coverage binaries in $(O)/cov"

# ------------------------------------------------------- the mutation controls
# Each removes a check the suite says it enforces; each must make the suite go
# RED, and the recipe FAILS if the suite stays green.  mutate.py refuses if its
# anchor moved, so a control cannot rot into a no-op.
mutate:
	@set -e; M=$(O)/mutate; rm -rf $$M; \
	 for d in traversal hdrcap; do \
	   mkdir -p $$M/$$d/httpd $$M/$$d/lib; \
	   cp -a $(HERE). $$M/$$d/httpd/; cp -a $(LIB)/. $$M/$$d/lib/; \
	   echo "=== control: $$d ==="; \
	   $(PYTHON) $(HERE)mutate.py $$d $$M/$$d/httpd/http.c; \
	   $(HOSTCC) $(MCFLAGS) -I$$M/$$d/httpd -I$$M/$$d/lib -o $$M/$$d/t \
	     $$M/$$d/httpd/test_http.c $$M/$$d/httpd/routes.c \
	     $$M/$$d/httpd/rl.c $$M/$$d/httpd/http.c $$M/$$d/lib/json.c \
	     $$M/$$d/lib/schema.c $$M/$$d/lib/tlv.c \
	     $$M/$$d/lib/client.c $$M/$$d/lib/proto.c; \
	   if $$M/$$d/t > $$M/$$d/out 2>&1; then \
	     echo "REFUSED: the suite PASSED with $$d removed."; \
	     echo "         It is therefore not testing what it claims to."; \
	     tail -3 $$M/$$d/out; exit 1; \
	   fi; \
	   n=$$(grep -c '^not ok' $$M/$$d/out || true); \
	   echo "  RED as required: $$n failing cases"; \
	   grep '^not ok' $$M/$$d/out | head -3 | sed 's/^/    /'; \
	 done; \
	 echo "both mutation controls went red; the suite's checks are load bearing"

# --------------------------------------------------------------- chrootcheck
# ROOT= is the directory that will BE the chroot.  A gate condition of R7, so it
# is a build step and not a note.
chrootcheck:
	@test -n "$(ROOT)" || { echo "REFUSED: ROOT= is required"; exit 1; }
	$(PYTHON) $(HERE)chrootcheck.py $(ROOT)

# The half the host suite cannot reach: the privilege drop and the accept loop,
# which need root and a listening socket.  ROOT= must be a root-owned copy of the
# web root; PORT= defaults to 18080.  Run it with sudo; it refuses otherwise rather
# than half-testing.
rootcheck: host
	@test -n "$(ROOT)" || { echo "REFUSED: ROOT= is required"; exit 1; }
	@test "$$(id -u)" = 0 || { \
	   echo "REFUSED: rootcheck needs root (sudo make ... rootcheck)"; exit 1; }
	$(HERE)rootcheck.sh $(HOST_OUT)/httpd $(ROOT) $(if $(PORT),$(PORT),18080)

# --------------------------------------------------------------- target build
TCBIN      := $(TC)/bin
TCC        := $(TCBIN)/mips-linux-gcc
TSTRIP     := $(TCBIN)/mips-linux-strip
TREADELF   := $(TCBIN)/mips-linux-readelf
TNM        := $(TCBIN)/mips-linux-nm

# -Os -std=gnu99 -static -fno-builtin -fno-strict-aliasing -fno-common are
# linkprobe's; -fno-if-conversion is config/rlxfw-cflags' one flag, and that file
# says in as many words that it cannot reach the prebuilt libc.a it links, so it
# is claimed for this project's own objects and nothing else.  hazlint over the
# linked ELF is the check that decides.  NO -march, ever.
TCFLAGS    := -Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
              -Wno-unused-parameter \
              -fno-builtin -fno-strict-aliasing -fno-common -fno-if-conversion \
              -ffunction-sections -fdata-sections
TLDFLAGS   := -static -Wl,--gc-sections

TOUT       := $(O)/target
TOBJ       := $(TOUT)/obj/httpd
TSRC       := $(TOUT)/src
TFILES     := main.c serve.c routes.c rl.c http.c
# The library halves, staged flat into $(TSRC)/lib and compiled from there.
LFILES     := json.c schema.c tlv.c client.c proto.c
LHDRS      := json.h schema.h tlv.h client.h proto.h cfg.h sha256.h kdf.h

target:
	@test -n "$(TC)" || { echo "REFUSED: TC= is required"; exit 1; }
	@test -n "$(TRIP)" || { echo "REFUSED: TRIP= is required"; exit 1; }
	@test -x "$(TCC)" || { echo "REFUSED: no cross compiler at $(TCC)"; exit 1; }
	@case " $(TCFLAGS) " in *" -march="*) \
	   echo "REFUSED: TCFLAGS carries a -march"; exit 1 ;; esac
	@echo "no -march in TCFLAGS"
	$(TRIP) -- $(MAKE) --no-print-directory -C $(HERE) target-real O=$(O) TC=$(TC)

target-real:
	@mkdir -p $(TOBJ) $(TSRC)/lib
	@for f in $(TFILES) http.h routes.h rl.h serve.h; do \
	   cp -f $(HERE)$$f $(TSRC)/$$f; \
	 done
	@for f in $(LFILES) $(LHDRS) sha256.c kdf.c; do \
	   if [ -f $(LIB)/$$f ]; then cp -f $(LIB)/$$f $(TSRC)/lib/$$f; fi; \
	 done
	@bad=0; for f in $(TFILES); do \
	   a=$$(sha256sum $(HERE)$$f | cut -d' ' -f1); \
	   b=$$(sha256sum $(TSRC)/$$f | cut -d' ' -f1); \
	   if [ "$$a" != "$$b" ]; then echo "REFUSED: staged $$f is not the source"; \
	      bad=1; fi; \
	 done; \
	 for f in $(LFILES); do \
	   a=$$(sha256sum $(LIB)/$$f | cut -d' ' -f1); \
	   b=$$(sha256sum $(TSRC)/lib/$$f | cut -d' ' -f1); \
	   if [ "$$a" != "$$b" ]; then echo "REFUSED: staged lib/$$f is not the source"; \
	      bad=1; fi; \
	 done; \
	 if [ $$bad != 0 ]; then exit 1; fi; \
	 echo "staged onto $(TSRC), every hash equal to the repository's"
	@set -e; cd $(TSRC) && for f in $(TFILES) $(addprefix lib/,$(LFILES)); do \
	   o=$$(echo $$f | tr '/' '_'); \
	   $(TCC) $(TCFLAGS) -I. -I./lib -c $$f -o $(TOBJ)/$${o%.c}.o; \
	 done
	@set -e; cd $(TSRC) && $(TCC) $(TLDFLAGS) -o $(TOUT)/httpd $(TOBJ)/*.o
	cp -f $(TOUT)/httpd $(TOUT)/httpd.stripped
	$(TSTRIP) $(TOUT)/httpd.stripped
	@echo '--- gate: static, big-endian MIPS, no PT_INTERP ---'
	@i=$$($(TREADELF) -l $(TOUT)/httpd | grep -c INTERP || true); \
	 if [ "$$i" != "0" ]; then echo "REFUSED: a PT_INTERP in a static build"; \
	    exit 1; fi; \
	 $(TREADELF) -h $(TOUT)/httpd | grep -qi "big endian" || { \
	   echo "REFUSED: the ELF is not big-endian"; exit 1; }; \
	 $(TREADELF) -h $(TOUT)/httpd | awk -F: '/Flags|Machine/{print "  "$$0}'
	@echo '--- gate: hazlint over the linked ELF, 0 violations ---'
	@HAZLINT_CHILD=1 $(PYTHON) $(HAZLINT) $(TOUT)/httpd
	@echo '--- gate: system() and popen() are not in this binary ---'
	@for s in system popen; do \
	   n=$$($(TNM) $(TOUT)/httpd 2>/dev/null | awk -v s=$$s '$$3 == s {c++} END {print c + 0}'); \
	   echo "  $$s = $$n"; \
	   if [ "$$n" != "0" ]; then echo "REFUSED: $$s is linked into httpd"; exit 1; fi; \
	 done
	@echo "stripped $$(wc -c < $(TOUT)/httpd.stripped) bytes"
	@ls -1 $(TOBJ)

# kdfbench: one scrypt evaluation, timed and weighed, host and target.  The
# `noop` mode is subtracted from the `eval` mode so the figure is the KDF's and
# not the runtime's.
kdfbench:
	@mkdir -p $(O)/bench
	$(HOSTCC) -std=gnu99 -Wall -Wextra -Werror -O2 -I$(HERE) -I$(LIB) \
	  -o $(O)/bench/kdfbench $(HERE)kdfbench.c $(SRC_KDF)
	@echo "host kdfbench in $(O)/bench"

kdfbench-target:
	@test -n "$(TC)" || { echo "REFUSED: TC= is required"; exit 1; }
	@test -n "$(TRIP)" || { echo "REFUSED: TRIP= is required"; exit 1; }
	$(TRIP) -- $(MAKE) --no-print-directory -C $(HERE) kdfbench-target-real \
	  O=$(O) TC=$(TC)

kdfbench-target-real:
	@mkdir -p $(TOBJ) $(TSRC)/lib
	@for f in sha256.c sha256.h kdf.c kdf.h; do cp -f $(LIB)/$$f $(TSRC)/lib/$$f; done
	@cp -f $(HERE)kdfbench.c $(TSRC)/kdfbench.c
	@set -e; cd $(TSRC) && for f in lib/sha256.c lib/kdf.c kdfbench.c; do \
	   o=$$(echo $$f | tr '/' '_'); \
	   $(TCC) $(TCFLAGS) -I. -I./lib -c $$f -o $(TOBJ)/$${o%.c}.o; \
	 done
	@set -e; cd $(TSRC) && $(TCC) $(TLDFLAGS) -o $(TOUT)/kdfbench \
	   $(TOBJ)/lib_sha256.o $(TOBJ)/lib_kdf.o $(TOBJ)/kdfbench.o
	@echo "target kdfbench: $(TOUT)/kdfbench"

# The KDF's RFC vectors, cross-built and run under qemu-mips-static.  This is the
# check that separates "correct" from "correct little-endian": Salsa20's words are
# little-endian inside a big-endian program, so an implementation that casts
# instead of shifting passes every host test and fails here.  QEMU= may point at
# another emulator; a missing one REFUSES rather than skipping.
QEMU       ?= qemu-mips-static

targetkdf:
	@test -n "$(TC)" || { echo "REFUSED: TC= is required"; exit 1; }
	@test -n "$(TRIP)" || { echo "REFUSED: TRIP= is required"; exit 1; }
	@command -v $(QEMU) > /dev/null || { \
	   echo "REFUSED: no $(QEMU); this check does not skip"; exit 1; }
	@test -f $(LIB)/kdf.c || { echo "REFUSED: no $(LIB)/kdf.c"; exit 1; }
	$(TRIP) -- $(MAKE) --no-print-directory -C $(HERE) targetkdf-real O=$(O) \
	  TC=$(TC)
	@echo '--- the vectors, on the big-endian target binary under $(QEMU) ---'
	$(QEMU) $(TOUT)/test_kdf
	@echo '--- hazlint over it, since it is a target ELF like any other ---'
	@HAZLINT_CHILD=1 $(PYTHON) $(HAZLINT) $(TOUT)/test_kdf

targetkdf-real:
	@mkdir -p $(TOBJ) $(TSRC)/lib
	@for f in sha256.c sha256.h kdf.c kdf.h; do cp -f $(LIB)/$$f $(TSRC)/lib/$$f; done
	@cp -f $(HERE)test_kdf.c $(TSRC)/test_kdf.c
	@a=$$(sha256sum $(LIB)/kdf.c | cut -d' ' -f1); \
	 b=$$(sha256sum $(TSRC)/lib/kdf.c | cut -d' ' -f1); \
	 [ "$$a" = "$$b" ] || { echo "REFUSED: staged kdf.c is not the source"; exit 1; }
	@set -e; cd $(TSRC) && for f in lib/sha256.c lib/kdf.c test_kdf.c; do \
	   o=$$(echo $$f | tr '/' '_'); \
	   $(TCC) $(TCFLAGS) -I. -I./lib -c $$f -o $(TOBJ)/$${o%.c}.o; \
	 done
	@set -e; cd $(TSRC) && $(TCC) $(TLDFLAGS) -o $(TOUT)/test_kdf \
	   $(TOBJ)/lib_sha256.o $(TOBJ)/lib_kdf.o $(TOBJ)/test_kdf.o

show:
	@echo "repo      $(REPO)"
	@echo "O         $(O)"
	@echo "core      $(SRC_CORE)"
	@echo "client    $(SRC_CLIENT)"

clean:
	rm -rf $(O)/host $(O)/asan $(O)/gcc $(O)/clang $(O)/gccsan \
	       $(O)/clangsan $(O)/fuzz $(O)/cov $(O)/mutate $(O)/target
