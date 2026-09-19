# Hand-written cross Makefile for iperf 3.1.3 -> TOTOLINK N150RT
# (Realtek RTL8196E, Lexra RLX4181, MIPS-I big-endian, Linux 2.6.30, uClibc 0.9.30).
#
# WHY THERE IS NO ./configure HERE.
# configure would run 200+ link-and-run tests with a cross compiler that cannot
# run its own output, so every AC_RUN_IFELSE falls to its cross default and the
# answers are guesses wearing a cache-variable name.  Every line of
# src/iperf_config.h was instead produced by a compile probe against THIS
# toolchain's own headers and a symbol census of THIS libc.a --
# see a7-iperf-probe.sh.
#
# ARCH FLAGS ARE DELIBERATELY ABSENT.
# 量 (readelf -h on a default-flag .o): this toolchain already defaults to
#   Machine: MIPS R3000 / Data: 2's complement, big endian / Flags: o32, mips1
# so -march/-mabi/-EB would only restate it.  -march=mips32 is BANNED on this
# core: the load delay slot is architecturally exposed and mips32 miscompiles
# silently (CLAUDE.md).
#
# -fno-if-conversion IS NOT A PREFERENCE, IT IS A DEFECT WORKAROUND.
# 量, config/rlxfw-cflags + SPEC.md TC-25: this gcc's if-conversion emits
# movz/movn that read a register a load two instructions earlier wrote.  A
# flagless kernel build of this project carried SEVEN such load-use hazards and
# every gate stayed green.  The flag removes 98.8 % of the conditional moves.
# Build the control with EXTRA_CFLAGS= to see the difference.

TC           ?= /home/key/fwre-work/rebuild/r2ab/tc/rsdk-1.3.6-4181-EB-2.6.30-0.9.30
CROSS        := $(TC)/bin/mips-linux-
CC           := $(CROSS)gcc
STRIP        := $(CROSS)strip
READELF      := $(CROSS)readelf

# WHERE THINGS GO, AND WHY NOT HERE.
# `RECIPE_ID` is `find config -type f` with no exclusions and does not consult
# .gitignore (讀 tools/rlxfw-kbuild.sh:262-263), so a single .o left beside this
# Makefile would silently move the id the board prints.  Objects therefore go
# under $FWRE_WORK and the product goes to $REPO/build/, which is gitignored --
# the same split config/rlxfw-user/isaprobe/Makefile:62 uses, and the same
# reason config/rlxfw-initramfs.tsv gives for uprobe and ucost.
HERE         := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO         := $(abspath $(HERE)../../..)
FWRE_WORK    ?= /home/key/fwre-work
STAGE        ?= $(FWRE_WORK)/rebuild/rlxfw-user/iperf3
OBJDIR       := $(STAGE)/build
INSTALL      ?= $(REPO)/build/rlxfw-user/iperf3
OUT          := $(INSTALL)/iperf3

# ⚠️ SRC IS NOT STAGED, AND THAT IS A STATED LIMIT RATHER THAN AN OVERSIGHT.
# isaprobe copies its sources into $(STAGE)/src before building; this does not.
# iperf 3.1.3's tree is 6 MB and carries two GENERATED headers -- iperf_config.h
# (this directory's, produced by probe.sh) and version.h (from version.h.in) --
# which config/rlxfw-user/iperf3/build.sh staged INTO the source tree.  So a
# clean clone cannot build this target: it needs an src313 tree that has already
# been staged.  Carried forward rather than fixed here, because inventing a
# staging rule in the hour before a bench card is frozen is how a guard gets
# written wrong.
SRC          ?= $(FWRE_WORK)/iperf3-port/src313/src
EXTRA_CFLAGS ?= -fno-if-conversion

CPPFLAGS     := -D_GNU_SOURCE -I$(SRC)
CFLAGS       := -std=gnu99 -O2 -Wall $(EXTRA_CFLAGS)
LDFLAGS      := -static
LIBS         := -lm

# main.c plus libiperf_la_SOURCES from src/Makefile.am, minus the t_*.c test
# programs.  iperf_sctp.c is kept: it guards its own body on HAVE_SCTP, which
# iperf_config.h leaves undefined because netinet/sctp.h is measured ABSENT.
CFILES := main.c cjson.c iperf_api.c iperf_client_api.c iperf_error.c \
          iperf_locale.c iperf_sctp.c iperf_server_api.c iperf_tcp.c \
          iperf_udp.c iperf_util.c net.c tcp_info.c tcp_window_size.c \
          timer.c units.c

OBJS := $(CFILES:%.c=$(OBJDIR)/%.o)
ELF  := $(OBJDIR)/iperf3.elf
BIN  := $(OBJDIR)/iperf3

all: install

$(OBJDIR):
	@mkdir -p $(OBJDIR)

$(OBJDIR)/%.o: $(SRC)/%.c | $(OBJDIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(ELF): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)

$(BIN): $(ELF)
	cp $< $@
	$(STRIP) $@

install: $(BIN)
	@mkdir -p $(INSTALL)
	cp -f $(BIN) $(OUT)
	@echo "installed $(OUT)"
	@sha256sum $(OUT)
	@# $(BIN) and not $(OUT): the rsdk readelf is 32-bit and a DrvFs
	@# inode overflows its stat().  Same bytes, ext4 side.
	@$(READELF) -h $(BIN) | grep -E 'Class|Data|Machine|Flags'

# Every number a bench card would state about this artefact, printed by the
# artefact's own build so the card quotes a measurement and not a memory.
show: install
	@echo "bytes   $$(stat -c %s $(OUT))"
	@echo "sha256  $$(sha256sum $(OUT) | cut -d' ' -f1)"
	@echo "dynamic $$($(READELF) -d $(BIN) 2>&1 | grep -c 'no dynamic section') (1 = static)"

clean:
	rm -rf $(OBJDIR)
	rm -f $(OUT)

.PHONY: all install show clean
