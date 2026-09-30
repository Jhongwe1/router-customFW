# src/dnsfwd/Makefile -- dnsfwd: host build, test battery, mutation controls,
# fuzz harness and the big-endian target build.
#
# The shape is config/rlxfw-user/linkprobe/Makefile's, and that file owns the
# reasons this one repeats without restating: why the target sources are staged
# onto ext4 first (the rsdk driver is a 32-bit i386 ELF and every DrvFs path
# returns EOVERFLOW to its stat()), why the vendor compiler runs only through
# tools/vendor-tripwire.sh, and why there is no -march anywhere.
#
# Goals, all requiring O=<absolute out dir> (SPEC-R7 s 2):
#   host     $O/host/dnsfwd, plus the tests built with BOTH compilers
#   test     runs the suite on both compilers, then the two mutation controls;
#            non-zero on any failure.  The mutants are interpreted only after
#            the unmutated suite passed -- a mutation run is a claim about the
#            controls, so the controls have to be green first.
#   mutants  the mutation controls alone
#   fuzz     $O/fuzz/fuzz_dns (afl-clang-fast), $O/fuzz/fuzz_dns_cov (clang
#            coverage) and $O/fuzz/fuzz_dns_bug: a COPY OF THE TREE with an
#            off-by-one planted in the label-length bound
#   target   $O/target/dnsfwd[.stripped] and every object at
#            $O/target/obj/dnsfwd/*.o, hazlint clean
#   qemu     the same decode case on the host ELF and on the target ELF under
#            qemu-mips-static; the outputs must be identical

SHELL   := /bin/sh
HERE    := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO    := $(abspath $(HERE)../..)
PROG    := dnsfwd
PYTHON  ?= /usr/bin/python3

ifeq ($(O),)
$(error O=<absolute out dir> is required)
endif
ifeq ($(patsubst /%,,$(O)),$(O))
$(error O must be an absolute path, got "$(O)")
endif

# --------------------------------------------------------------------------
# The broker client is src/lib/client.c.  `R7-8` deleted src/dnsfwd/stub/,
# which stood in for it while the two were written in parallel, so there is no
# fallback any more: an absent src/lib/client.h REFUSES rather than quietly
# building something else.  (The stub's `BK_*` names for SPEC-R7 § 6's ops and
# statuses survive as aliases in src/lib/client.h; 量 `R7-8` that the stub's
# values and the real ones agreed on every one.)
# --------------------------------------------------------------------------
LIBDIR    := $(REPO)/src/lib
LIBCLIENT := $(wildcard $(LIBDIR)/client.h)
ifeq ($(LIBCLIENT),)
$(error REFUSED: $(LIBDIR)/client.h is absent and there is no longer a stub)
endif
CLIENT_DEF :=
CLIENT_SRC := ../lib/client.c ../lib/proto.c
CLIENT_MSG := using src/lib/client.c + src/lib/proto.c

# dns.c is the whole parser and policy; the tests never link main.c, so they
# cannot reach a syscall even by accident.
CORE     := dns.c
DAEMON   := main.c $(CLIENT_SRC)
# Staged for the target build: dnsfwd's own files from $(HERE), the library's
# from $(LIBDIR), both flattened into $(TSTAGE).
TSTAGED  := dns.c dns.h main.c
LIBSTAGED := client.c client.h proto.c proto.h
TCOMPILE := $(CORE) main.c client.c proto.c
TESTS    := test_dns.c

# --------------------------------------------------------------------------
# A named mutation may not reach a product.  Shown BOTH ways: the guard runs
# on the real flags, and `make mutant-guard-selftest` proves it refuses.
# --------------------------------------------------------------------------
MUTCHECK = case " $(1) " in *DNSFWD_MUT_*) \
             echo "REFUSED: a DNSFWD_MUT_* mutation must not reach a product"; \
             exit 1 ;; esac

HOSTCC1 ?= gcc-13
HOSTCC2 ?= clang-18
HCFLAGS := -std=gnu99 -Wall -Wextra -Werror -O1 -g -fno-common \
           -fsanitize=address,undefined -fno-omit-frame-pointer
SANENV  := ASAN_OPTIONS=detect_leaks=1 \
           UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1

.PHONY: all host test mutants fuzz target qemu clean show \
        mutant-guard-selftest
all: host

# --------------------------------------------------------------------------
# Host
# --------------------------------------------------------------------------
host:
	@$(call MUTCHECK,$(HCFLAGS) $(CLIENT_DEF))
	@mkdir -p $(O)/host
	@echo "client: $(CLIENT_MSG)"
	$(HOSTCC1) $(HCFLAGS) $(CLIENT_DEF) -I$(HERE) -I$(LIBDIR) -o $(O)/host/$(PROG) \
	    $(addprefix $(HERE),$(CORE) $(DAEMON))
	$(HOSTCC2) $(HCFLAGS) $(CLIENT_DEF) -I$(HERE) -I$(LIBDIR) -o $(O)/host/$(PROG).clang \
	    $(addprefix $(HERE),$(CORE) $(DAEMON))
	$(HOSTCC1) $(HCFLAGS) -I$(HERE) -I$(LIBDIR) -o $(O)/host/test_dns.gcc \
	    $(addprefix $(HERE),$(CORE) $(TESTS))
	$(HOSTCC2) $(HCFLAGS) -I$(HERE) -I$(LIBDIR) -o $(O)/host/test_dns.clang \
	    $(addprefix $(HERE),$(CORE) $(TESTS))
	@echo "host build clean on $(HOSTCC1) and $(HOSTCC2), -Wall -Wextra -Werror"

# The mutants get their own names so that no product can ever be one.
$(O)/host/mut_ptr:
	@mkdir -p $(O)/host
	$(HOSTCC1) $(HCFLAGS) -DDNSFWD_MUT_NO_PTR_GUARD -I$(HERE) -o $@ \
	    $(addprefix $(HERE),$(CORE) $(TESTS))
$(O)/host/mut_qmatch:
	@mkdir -p $(O)/host
	$(HOSTCC1) $(HCFLAGS) -DDNSFWD_MUT_NO_QMATCH -I$(HERE) -o $@ \
	    $(addprefix $(HERE),$(CORE) $(TESTS))

test: host
	@echo '--- the suite, $(HOSTCC1), ASan + UBSan ---'
	@$(SANENV) $(O)/host/test_dns.gcc
	@echo '--- the suite, $(HOSTCC2), ASan + UBSan ---'
	@$(SANENV) $(O)/host/test_dns.clang
	@$(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) mutants

# A green suite is a claim about its controls; this is what tests them.
mutants: $(O)/host/mut_ptr $(O)/host/mut_qmatch
	@echo '--- mutation control 1: the compression-pointer guards removed ---'
	@if $(SANENV) $(O)/host/mut_ptr >$(O)/host/mut_ptr.out 2>&1; then \
	   echo "REFUSED: the suite PASSED with the pointer guards removed, so"; \
	   echo "         the battery does not test them."; exit 1; \
	 else rc=$$?; echo "went red as required (exit $$rc):"; \
	   grep -m2 -E 'TIMED OUT|^FAIL' $(O)/host/mut_ptr.out || true; fi
	@echo '--- mutation control 2: the question half of the match removed ---'
	@if $(SANENV) $(O)/host/mut_qmatch >$(O)/host/mut_qmatch.out 2>&1; then \
	   echo "REFUSED: the suite PASSED without the question-section check,"; \
	   echo "         so the anti-spoof cases do not test it."; exit 1; \
	 else rc=$$?; echo "went red as required (exit $$rc):"; \
	   grep -m2 -E '^FAIL' $(O)/host/mut_qmatch.out || true; fi

mutant-guard-selftest:
	@if $(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) \
	      HCFLAGS=-DDNSFWD_MUT_NO_PTR_GUARD host >/dev/null 2>&1; then \
	   echo "REFUSED: the mutation guard permitted a mutated product"; exit 1; \
	 else echo "the guard REFUSES a product build carrying a mutation"; fi
	@$(MAKE) --no-print-directory -f $(HERE)Makefile O=$(O) host >/dev/null
	@echo "and PERMITS the real one"

# --------------------------------------------------------------------------
# Fuzzing
# --------------------------------------------------------------------------
FUZZSRC := $(REPO)/src/fuzz/fuzz_dns.c
AFLCC   ?= afl-clang-fast
COVCC   ?= clang-18
ANCHOR  := if (pos + 1 + (size_t)c > n) return -DNSE_SHORT;

fuzz:
	@$(call MUTCHECK,$(CLIENT_DEF))
	@mkdir -p $(O)/fuzz
	AFL_QUIET=1 $(AFLCC) -std=gnu99 -Wall -Wextra -Werror -O2 -g \
	    -fsanitize=address -I$(HERE) -I$(LIBDIR) -o $(O)/fuzz/fuzz_dns \
	    $(HERE)$(CORE) $(FUZZSRC)
	$(COVCC) -std=gnu99 -Wall -Wextra -Werror -O1 -g \
	    -fprofile-instr-generate -fcoverage-mapping \
	    -I$(HERE) -I$(LIBDIR) -o $(O)/fuzz/fuzz_dns_cov $(HERE)$(CORE) $(FUZZSRC)
	@# THE PLANTED DEFECT, in a COPY of the tree: the label-length bound
	@# becomes `> n + 1`, so one byte past the datagram can be read.
	@rm -rf $(O)/fuzz/bugtree && mkdir -p $(O)/fuzz/bugtree
	@cp $(HERE)dns.c $(HERE)dns.h $(O)/fuzz/bugtree/
	@n=$$(grep -c 'pos + 1 + (size_t)c > n' $(O)/fuzz/bugtree/dns.c); \
	 [ "$$n" = "1" ] || { echo "REFUSED: the anchor matches $$n times, not 1"; \
	                      exit 1; }
	@sed -i 's|pos + 1 + (size_t)c > n)|pos + 1 + (size_t)c > n + 1) /*PLANTED*/|' \
	    $(O)/fuzz/bugtree/dns.c
	@grep -q 'PLANTED' $(O)/fuzz/bugtree/dns.c || \
	   { echo "REFUSED: the off-by-one was not planted"; exit 1; }
	@if cmp -s $(HERE)dns.c $(O)/fuzz/bugtree/dns.c; then \
	   echo "REFUSED: the bug tree is identical to the real one"; exit 1; fi
	AFL_QUIET=1 $(AFLCC) -std=gnu99 -Wall -Wextra -O2 -g \
	    -fsanitize=address -I$(O)/fuzz/bugtree \
	    -o $(O)/fuzz/fuzz_dns_bug $(O)/fuzz/bugtree/dns.c $(FUZZSRC)
	@echo "built: fuzz_dns (afl), fuzz_dns_cov (llvm-cov), fuzz_dns_bug (planted)"

# --------------------------------------------------------------------------
# Target: big-endian MIPS, static, through the tripwire, sources on ext4
# --------------------------------------------------------------------------
TC       ?=
TRIP     ?= $(REPO)/tools/vendor-tripwire.sh
HAZLINT  := $(REPO)/tools/hazlint
TOBJ     := $(O)/target/obj/$(PROG)
TSTAGE   := $(O)/target/stage
TCFLAGS  := -Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
            -fno-builtin -fno-strict-aliasing -fno-common
TLDFLAGS := -static
# Names that would let dnsfwd start a process.  R7's pass condition is that
# none of them is an undefined symbol of anything shipped.
NOSTART  := system popen execl execlp execle execv execvp execve execvpe \
            fexecve fork vfork posix_spawn posix_spawnp clone daemon

target:
	@$(call MUTCHECK,$(TCFLAGS) $(CLIENT_DEF))
	@[ -n "$(TC)" ] || { echo "REFUSED: TC=<toolchain root> is required"; exit 1; }
	@[ -x "$(TC)/bin/mips-linux-gcc" ] || \
	   { echo "REFUSED: no mips-linux-gcc under TC=$(TC)"; exit 1; }
	@[ -x "$(TRIP)" ] || { echo "REFUSED: TRIP=$(TRIP) is not executable"; exit 1; }
	@case "$(O)" in /mnt/*) \
	   echo "REFUSED: O=$(O) is on DrvFs; the rsdk driver's stat() gets \
EOVERFLOW there"; exit 1 ;; esac
	@case " $(TCFLAGS) " in *" -march="*) \
	   echo "REFUSED: a -march reached CFLAGS"; exit 1 ;; esac
	@echo "no -march in CFLAGS; O is not on DrvFs"
	@rm -rf $(TSTAGE); mkdir -p $(TSTAGE) $(TOBJ)
	@for f in $(TSTAGED); do cp -f $(HERE)$$f $(TSTAGE)/$$f; done
	@for f in $(LIBSTAGED); do cp -f $(LIBDIR)/$$f $(TSTAGE)/$$f; done
	@for f in $(TSTAGED); do \
	   a=$$(sha256sum $(HERE)$$f | cut -d' ' -f1); \
	   b=$$(sha256sum $(TSTAGE)/$$f | cut -d' ' -f1); \
	   [ "$$a" = "$$b" ] || { echo "REFUSED: staged $$f is not the source"; \
	                          exit 1; }; done
	@for f in $(LIBSTAGED); do \
	   a=$$(sha256sum $(LIBDIR)/$$f | cut -d' ' -f1); \
	   b=$$(sha256sum $(TSTAGE)/$$f | cut -d' ' -f1); \
	   [ "$$a" = "$$b" ] || { echo "REFUSED: staged lib/$$f is not the source"; \
	                          exit 1; }; done
	@echo "staged $(words $(TSTAGED) $(LIBSTAGED)) files onto $(TSTAGE), every hash equal"
	@printf '%s\n' \
	  '#!/bin/sh' 'set -e' 'cd "$$1"' \
	  'for f in $(TCOMPILE); do' \
	  '  "$$3/bin/mips-linux-gcc" $(TCFLAGS) $(CLIENT_DEF) -I. -c "$$f" \' \
	  '      -o "$$2/$$(basename $$f .c).o"' \
	  'done' \
	  '"$$3/bin/mips-linux-gcc" $(TLDFLAGS) -o "$$4" "$$2"/*.o' \
	  > $(O)/target/build.sh
	@chmod 755 $(O)/target/build.sh
	$(TRIP) -- $(O)/target/build.sh $(TSTAGE) $(TOBJ) $(TC) \
	    $(O)/target/$(PROG)
	@cp -f $(O)/target/$(PROG) $(O)/target/$(PROG).stripped
	@$(TC)/bin/mips-linux-strip $(O)/target/$(PROG).stripped
	@echo '--- hazlint over the linked ELF ---'
	@HAZLINT_CHILD=1 $(PYTHON) $(HAZLINT) $(O)/target/$(PROG)
	@echo '--- big-endian MIPS, static, no PT_INTERP ---'
	@$(TC)/bin/mips-linux-readelf -h $(O)/target/$(PROG) | \
	    grep -E "Data:|Machine:|Flags:"
	@i=$$($(TC)/bin/mips-linux-readelf -l $(O)/target/$(PROG) | \
	      grep -c INTERP || true); \
	 [ "$$i" = "0" ] || { echo "REFUSED: a PT_INTERP in a static build"; exit 1; }
	@echo '--- the pre-link objects: no process-starting undefined symbol ---'
	@$(TC)/bin/mips-linux-nm -u $(TOBJ)/*.o | awk 'NF{print $$NF}' | sort -u \
	    > $(O)/target/undef.txt
	@c=$$(grep -Fx socket $(O)/target/undef.txt | wc -l); \
	 [ "$$c" = "1" ] || { echo "REFUSED: the counter cannot see socket \
(positive control read $$c); it would report 0 for anything"; exit 1; }; \
	 echo "  positive control: socket IS undefined ($$c)"
	@bad=0; for s in $(NOSTART); do \
	   if grep -Fxq "$$s" $(O)/target/undef.txt; then \
	     echo "  FOUND: $$s"; bad=1; fi; done; \
	 [ $$bad = 0 ] || { echo "REFUSED: dnsfwd imports a process starter"; \
	                    exit 1; }; \
	 echo "  none of the $(words $(NOSTART)) process-starting names is \
undefined in $$(ls $(TOBJ)/*.o | wc -l) objects"
	@echo "target ok: $$(wc -c < $(O)/target/$(PROG)) bytes linked, \
$$(wc -c < $(O)/target/$(PROG).stripped) stripped"

# One decoded packet, on both endiannesses, as a second source for "the code
# does not depend on the host's byte order".
# Split into three variables rather than continued with a backslash: make
# turns a backslash-newline into a SPACE, which would split the argument in the
# recipe and hand python half a vector.
QV1 := 123481800001000100000000
QV2 := 03777777076578616d706c6503636f6d0000010001
QV3 := c00c000100010000012c00045db8d822
QVEC := $(QV1)$(QV2)$(QV3)

qemu:
	@[ -x $(O)/target/$(PROG) ] || { echo "REFUSED: make target first"; exit 1; }
	@[ -x $(O)/host/$(PROG) ]   || { echo "REFUSED: make host first"; exit 1; }
	@command -v qemu-mips-static >/dev/null || \
	   { echo "REFUSED: no qemu-mips-static"; exit 1; }
	@mkdir -p $(O)/qemu
	@$(PYTHON) -c 'import sys;open(sys.argv[1],"wb").write(bytes.fromhex(sys.argv[2]))' \
	    $(O)/qemu/reply_a.bin '$(QVEC)'
	@[ $$(wc -c < $(O)/qemu/reply_a.bin) = 49 ] || \
	   { echo "REFUSED: the vector is not 49 bytes"; exit 1; }
	@$(O)/host/$(PROG) --decode $(O)/qemu/reply_a.bin > $(O)/qemu/host.txt
	@qemu-mips-static $(O)/target/$(PROG) --decode $(O)/qemu/reply_a.bin \
	    > $(O)/qemu/target.txt
	@cat $(O)/qemu/target.txt
	@if diff -u $(O)/qemu/host.txt $(O)/qemu/target.txt; then \
	   echo "IDENTICAL: little-endian host and big-endian target agree"; \
	 else echo "REFUSED: the two decodes differ"; exit 1; fi

show:
	@echo "prog     $(PROG)"
	@echo "client   $(CLIENT_MSG)"
	@echo "core     $(CORE)"
	@echo "daemon   $(DAEMON)"
	@echo "O        $(O)"

clean:
	rm -rf $(O)/host $(O)/target $(O)/fuzz $(O)/qemu
