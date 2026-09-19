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

SRC          ?= ../src313/src
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

OBJS := $(CFILES:%.c=%.o)

all: iperf3

%.o: $(SRC)/%.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

iperf3.elf: $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)

iperf3: iperf3.elf
	cp $< $@
	$(STRIP) $@

clean:
	rm -f $(OBJS) iperf3 iperf3.elf

.PHONY: all clean
