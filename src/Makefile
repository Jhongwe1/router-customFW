# src/Makefile -- the one place that builds all of rlxfw's userspace.
#
# Written by `R7-8`, which is the first step that needs every program at once:
# the image.  Each src/<prog>/Makefile is unchanged and owns its own flags, its
# own tests and its own gates; this file only iterates them and gives each one a
# private output directory.
#
# WHY A PRIVATE O= PER PROGRAM, and it is not tidiness.  Four of the six stage
# their target sources FLAT into $(O)/target/{src,stage} (brokerd, dnsfwd and
# httpd) or into $(O)/target/src/<prog> (init, ifupd).  Sharing one O= would let
# brokerd's main.c and httpd's main.c land on the same path, and the loser would
# be compiled as the winner without any check firing -- every staging gate here
# compares the staged copy against ITS OWN source, so both would still pass.
# $(O)/<prog>/ makes that collision impossible rather than unlikely.
#
# Targets, all requiring O=<absolute directory> (SPEC-R7 § 2):
#
#   host     every program and its test binaries, host compilers
#   test     every program's suite; the first failure stops the run
#   target   the big-endian MIPS ELFs, via tools/vendor-tripwire.sh
#   install  each stripped target ELF -> $(REPO)/build/rlxfw-user/<prog>/<prog>
#   sizes    the stripped size and hazlint verdict of each target ELF
#
# rlxboot is NOT in this list.  It is a freestanding loader payload (`R8a`), not
# a Linux process and not an initramfs entry, and its Makefile has its own verb
# names.  `make rlxboot` runs its host suite and builds its payload, so that a
# reconciliation commit still exercises it.

SHELL   := /bin/sh
HERE    := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO    := $(abspath $(HERE)..)

# The six Linux processes, in the order the image starts them.
PROGS   := init cfgstore brokerd httpd dnsfwd ifupd

TC      ?=
TRIP    ?= $(REPO)/tools/vendor-tripwire.sh
PYTHON  ?= /usr/bin/python3
HAZLINT := $(REPO)/tools/hazlint
INSTALLROOT ?= $(REPO)/build/rlxfw-user

.PHONY: all host test target install sizes rlxboot clean show help
all: help

ifeq ($(strip $(O)),)
NEED_O := 1
endif
ifneq ($(strip $(O)),)
ifeq ($(patsubst /%,,$(O)),$(O))
$(error REFUSED: O=$(O) is not absolute)
endif
endif

# A goal that needs O= refuses without one, by name, rather than by a make error
# about an empty variable.
define need_o
	@[ -n "$(strip $(O))" ] || { \
	   echo "REFUSED: O=<absolute output directory> is required for '$@'"; \
	   exit 1; }
endef

host:
	$(need_o)
	@set -e; for p in $(PROGS); do \
	   echo "===== host: $$p ====="; \
	   $(MAKE) --no-print-directory -C $(HERE)$$p host O=$(O)/$$p; \
	 done
	@echo "host build: $(words $(PROGS)) programs"

# TMPDIR is set, and on ext4, deliberately.  httpd's test_routes builds its web
# root under $TMPDIR or, with none, under the CWD -- which for a `make -C src`
# run is inside the repository, i.e. DrvFs.  DrvFs reports every file 0777, so
# `chmod 0644` on the fixture is a no-op, and send_file() then correctly refuses
# its own style.css as an executable: five cases fail for a reason that has
# nothing to do with the code under test.  $(O) is required to be ext4 for the
# target build already, so this costs nothing.
test:
	$(need_o)
	@mkdir -p $(O)/tmp
	@case "$(O)" in /mnt/*) echo "note: O=$(O) is on DrvFs; httpd's fixture"\
	   " needs 0644 to mean 0644 -- expect test_routes to fail" ;; esac
	@set -e; n=0; for p in $(PROGS); do \
	   echo "===== test: $$p ====="; \
	   TMPDIR=$(O)/tmp $(MAKE) --no-print-directory -C $(HERE)$$p test O=$(O)/$$p; \
	   n=$$((n+1)); \
	 done; \
	 echo "test: $$n of $(words $(PROGS)) program suites ran and passed"

target:
	$(need_o)
	@[ -n "$(strip $(TC))" ] || { \
	   echo "REFUSED: TC=<toolchain root> is required for 'target'"; exit 1; }
	@case "$(O)" in /mnt/*) \
	   echo "REFUSED: O=$(O) is on DrvFs; the rsdk driver's stat() gets EOVERFLOW"; \
	   exit 1 ;; esac
	@set -e; for p in $(PROGS); do \
	   echo "===== target: $$p ====="; \
	   $(MAKE) --no-print-directory -C $(HERE)$$p target O=$(O)/$$p \
	     TC=$(TC) TRIP=$(TRIP); \
	 done
	@echo "target build: $(words $(PROGS)) big-endian MIPS ELFs"

# Deliberately NOT delegated to the two programs that happen to have their own
# `install` rule: one copier, one set of modes, one place to read.
install:
	$(need_o)
	@set -e; for p in $(PROGS); do \
	   s=$(O)/$$p/target/$$p.stripped; \
	   [ -f $$s ] || { echo "REFUSED: no $$s; run 'target' first"; exit 1; }; \
	   mkdir -p $(INSTALLROOT)/$$p; \
	   cp -f $$s $(INSTALLROOT)/$$p/$$p; \
	   chmod 0755 $(INSTALLROOT)/$$p/$$p; \
	   printf '  %-9s %8d bytes -> %s\n' $$p \
	     $$(wc -c < $(INSTALLROOT)/$$p/$$p) $(INSTALLROOT)/$$p/$$p; \
	 done
	@echo "installed $(words $(PROGS)) binaries under $(INSTALLROOT)"

sizes:
	$(need_o)
	@set -e; t=0; for p in $(PROGS); do \
	   e=$(O)/$$p/target/$$p; s=$$e.stripped; \
	   [ -f $$s ] || { echo "REFUSED: no $$s; run 'target' first"; exit 1; }; \
	   b=$$(wc -c < $$s); t=$$((t+b)); \
	   h=$$(HAZLINT_CHILD=1 $(PYTHON) $(HAZLINT) $$e >/dev/null 2>&1 \
	        && echo "0-violations" || echo "HAZLINT-FAILED"); \
	   printf '  %-9s %8d  %-14s %s\n' "$$p" "$$b" "$$h" \
	     "$$(sha256sum $$s | cut -c1-16)"; \
	 done; \
	 echo "  total     $$t bytes stripped, $(words $(PROGS)) programs"

# rlxboot: its own verbs, and no install -- it is not an initramfs entry.
#
# TC MEANS SOMETHING ELSE HERE, and passing this file's TC through would build
# nothing: src/rlxboot/Makefile splits the toolchain into TCROOT (the directory
# of toolchains) and TC (the rsdk directory's BASENAME), while every other
# program's TC is the rsdk root itself.  So the two halves are derived from the
# one value rather than forwarded.
rlxboot:
	$(need_o)
	@$(MAKE) --no-print-directory -C $(HERE)rlxboot hosttest O=$(O)/rlxboot
	@if [ -n "$(strip $(TC))" ]; then \
	   $(MAKE) --no-print-directory -C $(HERE)rlxboot payload O=$(O)/rlxboot \
	     TCROOT=$(dir $(patsubst %/,%,$(TC))) TC=$(notdir $(patsubst %/,%,$(TC))) \
	     TRIP=$(TRIP); \
	 else \
	   echo "note: TC= unset, so only rlxboot's host suite ran"; \
	 fi

show:
	@echo "REPO        $(REPO)"
	@echo "O           $(O)"
	@echo "PROGS       $(PROGS)"
	@echo "TC          $(TC)"
	@echo "TRIP        $(TRIP)"
	@echo "INSTALLROOT $(INSTALLROOT)"

help:
	@echo "make -C src <goal> O=<absolute dir> [TC=<toolchain root>]"
	@echo "  host test target install sizes rlxboot show"
	@echo "programs: $(PROGS)   (rlxboot is separate; see the header)"

clean:
	$(need_o)
	@set -e; for p in $(PROGS) rlxboot; do \
	   $(MAKE) --no-print-directory -C $(HERE)$$p clean O=$(O)/$$p || true; \
	 done
