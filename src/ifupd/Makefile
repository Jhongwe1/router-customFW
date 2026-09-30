# src/ifupd/Makefile -- the compiled replacement for udhcpc's -s shell script.
#
# Same shape and same reasons as src/init/Makefile; see that file, and
# config/rlxfw-user/linkprobe/Makefile, which owns them.
#
#   make -C src/ifupd host    O=<abs dir>
#   make -C src/ifupd test    O=<abs dir>
#   make -C src/ifupd mutants O=<abs dir>
#   make -C src/ifupd target  O=<abs dir> TC=<toolchain root> TRIP=<vendor-tripwire.sh>

SHELL      := /bin/sh
HERE       := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SRCROOT    := $(abspath $(HERE)/..)
REPO       := $(abspath $(HERE)/../..)
PROG       := ifupd

ifeq ($(strip $(O)),)
$(error O= is required and must be an absolute directory (never under /mnt/c for a target build))
endif

PYTHON     ?= /usr/bin/python3

SRCS       := $(HERE)/main.c $(HERE)/netcfg.c $(SRCROOT)/lib/netutil.c
TEST_SRCS  := $(HERE)/test_netutil.c $(HERE)/test_ifupd.c
LIBSRC     := $(HERE)/netcfg.c $(SRCROOT)/lib/netutil.c
INCS       := -I$(HERE) -I$(SRCROOT)/lib

INSTALLDIR ?= $(REPO)/build/rlxfw-user/$(PROG)

.PHONY: all host test mutants target target-inner sysscan install clean
all: host

# ===========================================================================
# HOST
# ===========================================================================
HOSTW      := -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow -O1 -g
SAN        := -fsanitize=address,undefined -fno-omit-frame-pointer
HOSTCCS    ?= gcc-13 clang-18

host:
	@set -e; for cc in $(HOSTCCS); do \
	  d=$(O)/host/$$cc; mkdir -p $$d; \
	  echo "--- $$cc: $(PROG) ---"; \
	  $$cc $(HOSTW) $(SAN) $(INCS) -o $$d/$(PROG) $(SRCS); \
	  for t in $(TEST_SRCS); do \
	    b=$$(basename $$t .c); \
	    echo "--- $$cc: $$b ---"; \
	    $$cc $(HOSTW) $(SAN) $(INCS) -o $$d/$$b $$t $(LIBSRC); \
	  done; \
	done
	@echo "host build OK for: $(HOSTCCS)"

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
	echo "ifupd suite: $$ran test binaries ran, rc=$$rc"; \
	[ $$ran -gt 0 ] || { echo "REFUSED: 0 test binaries ran"; exit 1; }; \
	exit $$rc

# ===========================================================================
# MUTATION CONTROL M2 -- remove the netmask contiguity check
#
# The unmutated suite passes first, then `nu_mask_prefix`'s "the bits below the
# leading ones must all be zero" test is deleted in a COPY, and 255.0.255.0
# becomes a /8.  test_netutil must go RED.
# ===========================================================================
mutants: test
	@set -e; m=$(O)/mut/ifupd; rm -rf $$m; mkdir -p $$m/ifupd $$m/lib; \
	cp $(SRCROOT)/lib/netutil.c $(SRCROOT)/lib/netutil.h $$m/lib/; \
	cp $(HERE)/netcfg.c $(HERE)/netcfg.h $(TEST_SRCS) $$m/ifupd/; \
	n=$$(grep -c 'return -NU_E_MASK;' $$m/lib/netutil.c); \
	[ "$$n" = "1" ] || { echo "REFUSED: M2's anchor matches $$n times, not 1"; exit 1; }; \
	sed -i 's|return -NU_E_MASK;|return p; /* M2: contiguity check removed */|' \
	   $$m/lib/netutil.c; \
	grep -q 'M2: contiguity check removed' $$m/lib/netutil.c || \
	   { echo "REFUSED: M2 did not land"; exit 1; }; \
	gcc-13 $(HOSTW) -Wno-error $(SAN) -I$$m/ifupd -I$$m/lib -o $$m/test_netutil \
	   $$m/ifupd/test_netutil.c $$m/lib/netutil.c; \
	if ( cd $$m && ./test_netutil >out.txt 2>&1 ); then \
	   echo "HOLE: M2 (netmask contiguity removed) and test_netutil still PASSED"; \
	   sed -n '1,20p' $$m/out.txt; exit 1; \
	else \
	   echo "M2 OK: contiguity removed -> test_netutil FAILS as it must"; \
	   grep -c '^FAIL' $$m/out.txt | sed 's/^/  failing checks: /'; \
	   grep -m4 '^FAIL' $$m/out.txt | sed 's/^/  /'; \
	fi

# ===========================================================================
# TARGET
# ===========================================================================
target:
ifeq ($(strip $(TC)),)
	@echo "REFUSED: TC=<toolchain root> is required for a target build" >&2; exit 1
else
ifeq ($(strip $(TRIP)),)
	@echo "REFUSED: TRIP=<path to tools/vendor-tripwire.sh> is required" >&2; exit 1
else
	@case "$(O)" in /mnt/c/*) \
	   echo "REFUSED: O=$(O) is on DrvFs; the rsdk driver cannot stat() such a path" >&2; \
	   exit 1 ;; esac
	@$(TRIP) -- $(MAKE) --no-print-directory -f $(HERE)/Makefile target-inner \
	   O=$(O) TC=$(TC) TRIP=$(TRIP)
endif
endif

TCBIN      = $(TC)/bin
TCC        = $(TCBIN)/mips-linux-gcc
TSTRIP     = $(TCBIN)/mips-linux-strip
TNM        = $(TCBIN)/mips-linux-nm
TREADELF   = $(TCBIN)/mips-linux-readelf
TCFLAGS    = -Os -std=gnu99 -Wall -Wextra -Werror -Wundef -Wshadow \
             -fno-builtin -fno-strict-aliasing -fno-common -fno-if-conversion
TLDFLAGS   = -static
TOBJDIR    = $(O)/target/obj/$(PROG)
TSTAGE     = $(O)/target/src
TSRCDIR    = $(TSTAGE)/$(PROG)

# The stage mirrors src/'s layout; see src/init/Makefile for why.
PROG_STAGE = $(HERE)/main.c $(HERE)/netcfg.c $(HERE)/netcfg.h
LIB_STAGE  = $(SRCROOT)/lib/netutil.c $(SRCROOT)/lib/netutil.h
PROG_C     = main.c netcfg.c

target-inner:
	@case " $(TCFLAGS) " in *" -march="*) \
	   echo "REFUSED: TCFLAGS carries a -march" >&2; exit 1 ;; esac
	@echo "no -march in TCFLAGS"
	@mkdir -p $(TOBJDIR) $(TSRCDIR) $(TSTAGE)/lib $(O)/target
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
	@set -e; cd $(TSRCDIR); for f in $(PROG_C); do \
	  echo "  CC $(PROG)/$$f"; \
	  $(TCC) $(TCFLAGS) -c $$f -o $(TOBJDIR)/$${f%.c}.o; \
	done; \
	echo "  CC lib/netutil.c"; \
	$(TCC) $(TCFLAGS) -c ../lib/netutil.c -o $(TOBJDIR)/netutil.o
	@cd $(O)/target && $(TCC) $(TLDFLAGS) -o $(O)/target/$(PROG) $(TOBJDIR)/*.o
	@cp -f $(O)/target/$(PROG) $(O)/target/$(PROG).stripped
	@$(TSTRIP) $(O)/target/$(PROG).stripped
	@$(TREADELF) -l $(O)/target/$(PROG) | grep -q INTERP && \
	   { echo "REFUSED: the ELF has a PT_INTERP" >&2; exit 1; } || true
	@$(TREADELF) -h $(O)/target/$(PROG) | grep -q "big endian" || \
	   { echo "REFUSED: the ELF is not big-endian" >&2; exit 1; }
	@$(MAKE) --no-print-directory -f $(HERE)/Makefile sysscan \
	   O=$(O) TC=$(TC) ELF=$(O)/target/$(PROG)
	@HAZLINT_CHILD=1 $(PYTHON) $(REPO)/tools/hazlint $(O)/target/$(PROG)
	@ls -l $(O)/target/$(PROG) $(O)/target/$(PROG).stripped
	@echo "objects kept at $(TOBJDIR):" && ls $(TOBJDIR)

# ifupd must additionally hold no `fork` and no `exec*` AT ALL: it is the one
# program in R7 that a hostile party can make run, and "never executes anything"
# is its whole claim.  `system` and `popen` are covered with the rest.
BADSYMS    = system popen execl execlp execle execv execve execvp execvpe \
             fork vfork wordexp posix_spawn
sysscan:
	@set -e; bad=0; \
	for s in $(BADSYMS); do \
	  if $(TNM) $(ELF) 2>/dev/null | awk -v s="$$s" '$$3==s{print}' | grep -q .; then \
	    echo "  FOUND $$s in $(ELF)"; bad=1; \
	  fi; \
	done; \
	[ $$bad -eq 0 ] || { echo "REFUSED: a forbidden libc symbol is linked into ifupd" >&2; exit 1; }; \
	echo "sysscan: none of [$(BADSYMS)] is linked into $(notdir $(ELF))"
	@set -e; c=$(O)/target/ctl-ifupd; mkdir -p $$c; \
	printf '#include <stdlib.h>\nint main(void){return system("true");}\n' > $$c/ctl.c; \
	( cd $$c && $(TCC) -Os -static -o ctl ctl.c ) >/dev/null 2>&1; \
	if $(TNM) $$c/ctl 2>/dev/null | awk '$$3=="system"{print}' | grep -q .; then \
	  echo "sysscan control: system IS found in the control ELF -- the scan can see it"; \
	else \
	  echo "REFUSED: the scan cannot see system() in a program that calls it" >&2; exit 1; \
	fi

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
