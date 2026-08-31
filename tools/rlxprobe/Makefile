# rlxprobe -- bare-metal probe payloads for the Lexra core in the RTL8196E.
#
# The one thing to understand about this file
# -------------------------------------------
# `hazlint` is a GATE, not a lint.  `<payload>.bin` depends on `<payload>.gate`,
# and that file does not exist unless `tools/hazlint` exited 0.  There is no
# target that produces a runnable payload while skipping it, and `make -k` will
# not get you one either.
#
# That is layer two.  Upstream's `P9-12` post-mortem ends on exactly this point:
# adding two `nop`s made that day pass, and teaching the build to refuse is what
# stops tomorrow's payload.  Item 7 delivered the checker; this line is the half
# that makes it matter.
#
#   make                    build every payload, gated
#   make P=probe1           build one
#   make gate-check         prove the gate FAILS on a planted hazard
#   make dis P=probe1       disassemble what was actually emitted
#   make show P=probe1      the numbers that go in the runsheet cell
#   make qemu P=probe1      run it under qemu-system-mips -- HARNESS ONLY
#   make clean
#
# Knobs:
#   LOADADDR=0x80500000   where the payload is linked and jumped to
#   RESET=1               arm the watchdog when main returns (0 = spin instead)
#   CROSS=mips-linux-gnu-
#
# probe1 only:
#   RESULT_BASE=0x80A00000   the block the payload writes and `DW` reads back.
#                            0x80A00000 and NOT 0x81000000: MEM-14 measured that
#                            0x81000000's word 1 is rewritten to 0x00000144 on
#                            every boot, three times reproduced, so a canary
#                            there is destroyed by the thing it is meant to
#                            survive.  MEM-10 measured 0x80A00000 surviving
#                            three warm resets byte for byte.
#   GEOM=0                   arm the cache-sizing walk.  OFF by default: while
#                            the caches are isolated, a core that does not
#                            implement Status.IsC writes real memory across
#                            [GEOM_BASE, +1 MiB].  See cache.S.
#   GEOM_BASE=0x80B00000     the window it is allowed to scribble on.  Whatever
#                            this is set to, the runsheet reads it before and
#                            after -- it has not been probed the way 0x80A00000
#                            was (MEM-13).

CROSS      ?= mips-linux-gnu-
CC          = $(CROSS)gcc
OBJCOPY     = $(CROSS)objcopy
OBJDUMP     = $(CROSS)objdump
NM          = $(CROSS)nm

LOADADDR   ?= 0x80500000
STACK_SIZE ?= 0x4000
RESET      ?= 1
GEOM       ?= 0
GEOM_BASE  ?= 0x80B00000

# THE RESULT BLOCK, AND WHY THE DEFAULT IS PER PAYLOAD SINCE 2026-08-26.
#
# It was one global default, 0x80A00000, and `docs/probe3-cells.md` §10b says
# probe3 "must be given 0x80A02000 explicitly".  A knob that must be typed every
# time is a knob that will eventually not be, and what it costs here is a
# MEASUREMENT: probe1's block at 0x80A00000 holds `R1d`'s six cells and probe2's
# at 0x80A01000 holds the CP0 census, both recovered from DRAM by `DW` after
# their seatings.  A probe3 built with the default would poison one of them.
#
# So each payload names its own, a command line still wins (`?=` plus make's
# rule that command-line variables beat everything), and the RB_CLASH check
# further down turns the remaining case -- an explicit value that lands on
# another payload's block -- into a parse-time refusal rather than a comment.
RESULT_BASE_probe0 := 0x80A00000
RESULT_BASE_probe1 := 0x80A00000
RESULT_BASE_probe2 := 0x80A01000
RESULT_BASE_probe3 := 0x80A02000
RESULT_BASE?= $(RESULT_BASE_$(P))
# The 16550. These are the DEVICE's addresses and nothing but qemu-run.sh ever
# overrides them -- see rlxdefs.h. On this part the registers are four bytes
# apart, so LSR is THR + 0x14 and not THR + 5.
UART_THR   ?= 0xB8002000
UART_LSR   ?= 0xB8002014
# The exception vectors. R3000 layout, and the default is the only one that
# is right for this device -- see rlxdefs.h. qemu-run.sh is the only caller
# that may change them, because qemu has no MIPS-I core.
VEC_UTLB   ?= 0x80000000
VEC_GENERAL?= 0x80000080
CLEAR_BEV  ?= 0
# qemu only: return from the handler with `eret` instead of the R3000 `jr`+`rfe`.
RET_ERET   ?= 0

# Whether cache.S's `rlx_isc_inv` -- the Status.IsC/SwC path -- is LINKED AT ALL.
# Per payload, and `override` below, and that is the point rather than tidiness.
#
# `FLUSH_ISC` used to be an ordinary knob here. Two things happened on
# 2026-08-25. `docs/rlxprobe-audit-2026-08-25.md` Must-fix 3 found that the two
# probe2 images it produced were indistinguishable on every channel -- no header
# word, no `field()`, no banner, absent from `make show`, same `rb=`, command
# lines four characters apart. Then probe1 cell 4 MEASURED that this core does
# not isolate and that those byte stores reach DRAM (`07` CORRUPT on both
# victims, top byte of each word at stride 4). So the conclusion was not "stamp
# the knob" but "the knob should stop existing".
#
# ISC_probe1 is 1 because probe1 cell 4 IS that measurement and its result is a
# finding (CPU-35). Everything else is 0, and `make P=probe2 ISC=1` cannot
# change it -- a command-line variable beats a plain assignment, which is
# exactly what `override` is for.
ISC_probe0 := 0
ISC_probe1 := 1
ISC_probe2 := 0
# probe3 writes CP0 Status in two places and neither of them is this routine.
# `rlx_status_or`/`rlx_status_poke` in cells.S set `CU3` (Group M) and `IsC`
# with two control bits (Group S), each with NO memory reference inside the
# window -- which is M5, and M5 is probe1 cell 4's `07` CORRUPT measured on both
# victims.  `rlx_isc_inv` is the routine whose byte stores DID reach DRAM, and
# it stays unlinked here for the same reason it is unlinked in probe2.
ISC_probe3 := 0

HERE       := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
HAZLINT    := $(HERE)../hazlint
BUILD      ?= $(HERE)build

PAYLOADS   := probe0 probe1 probe2 probe3

# -march=mips1 needs -msoft-float on gcc 12.4.0, which rejects the flag on its
# own: "cc1: error: '-march=mips1' requires '-mfp32'".  Measured 2026-08-24;
# SPEC.md TC-06.  -msoft-float rather than -mfp32 because this core has no FPU
# and saying so is more honest than saying the FPU is 32-bit.
#
# -G0 turns off small-data addressing, which would need a $gp this payload never
# establishes.  -mno-abicalls -fno-pic because there is no dynamic loader and
# the image is linked at a fixed address.
ARCH        = -march=mips1 -mabi=32 -msoft-float -EB -G0 -mno-abicalls -fno-pic

DEFS        = -DRLX_RESET=$(RESET) -DRLX_GEOM=$(GEOM) \
              -DRLX_RESULT_BASE=$(RESULT_BASE)u -DRLX_GEOM_BASE=$(GEOM_BASE)u \
              -DRLX_ISC=$(ISC) \
              -DRLX_UART_THR=$(UART_THR) -DRLX_UART_LSR=$(UART_LSR) \
              -DRLX_VEC_UTLB=$(VEC_UTLB) -DRLX_VEC_GENERAL=$(VEC_GENERAL) \
              -DRLX_CLEAR_BEV=$(CLEAR_BEV) -DRLX_RET_ERET=$(RET_ERET)

CFLAGS      = $(ARCH) -O2 -std=gnu99 \
              -ffreestanding -fno-builtin -fno-stack-protector \
              -fomit-frame-pointer -fno-common \
              -Wall -Wextra -Werror -Wundef -Wshadow \
              $(DEFS)
ASFLAGS     = $(ARCH) $(DEFS) -Wa,--fatal-warnings
# --orphan-handling=error: no section may end up in this image that the linker
# script did not place by name.  A section nobody placed lands at an address
# nobody chose, and `objcopy -O binary` would then either drop it or pad the
# image out to reach it -- both silently.  It is also what turns "I renamed a
# section and forgot the script" into a build failure, which is how `.victims`
# is kept out of `.text`'s catch-all.
LDFLAGS     = $(ARCH) -nostdlib -nostartfiles -static \
              -Wl,--build-id=none -Wl,--nmagic -Wl,--fatal-warnings \
              -Wl,--orphan-handling=error \
              -Wl,-T,$(HERE)rlxprobe.lds \
              -Wl,--defsym,LOAD_ADDR=$(LOADADDR) \
              -Wl,--defsym,STACK_SIZE=$(STACK_SIZE)

# One payload per invocation.  `all` recurses over PAYLOADS.  Two payloads do
# not justify an $(eval) template, and a template is exactly the kind of
# indirection that hides which flags reached which object.
P          ?= probe0
override ISC := $(ISC_$(P))

# THE RESULT-BLOCK COLLISION GUARD, and it refuses at PARSE TIME so no goal can
# reach around it.
#
# Three payloads now write three blocks and two of them hold measurements that
# were recovered from DRAM after their seatings: probe1's six R1d cells at
# 0x80A00000 (`bench/2026-08-25/H1c.log`) and probe2's 256-row CP0 census at
# 0x80A01000 (`bench/2026-08-25b/H2g.log`).  A payload built for the wrong base
# does not fail.  It runs, poisons hundreds of words over somebody else's
# measurement, and reports a perfectly well-formed block of its own.
#
# The per-payload defaults above make the common case right.  This makes the
# remaining case -- an explicit `RESULT_BASE=` that lands on another payload's
# block -- a refusal.  probe0 is not in the list: it writes no result block at
# all, so it cannot collide with one.
#
# The `subst` chain is a case fold.  `make` has no `tolower`, and 0x80A00000 and
# 0x80a00000 are the same address; a guard that only caught one spelling would
# be a guard the next person spells around by accident.
RB_LC        := $(subst A,a,$(subst B,b,$(subst C,c,$(subst D,d,$(subst E,e,$(subst F,f,$(RESULT_BASE)))))))
RB_LC_BARE   := $(patsubst 0x%,%,$(RB_LC))
RB_LC_probe1 := 0x80a00000
RB_LC_probe2 := 0x80a01000
RB_LC_probe3 := 0x80a02000
#
# probe0 IS EXEMPT AND THE FIRST VERSION OF THIS WAS NOT, which broke every
# probe0 case in the suite at once. probe0 writes no result block -- it has no
# RESULT_BASE in its sources at all -- but it inherits the same default address
# as probe1, so a check that only excluded `$(P)` saw probe0 sitting on probe1's
# block and refused to build it. A guard that stops a payload which cannot
# collide is not a stricter guard, it is a broken one.
RB_CLASH     := $(if $(filter probe0,$(P)),,$(filter-out $(P),$(strip \
                  $(foreach q,probe1 probe2 probe3,$(if $(filter $(RB_LC),$(RB_LC_$(q))),$(q))))))
ifneq ($(RB_CLASH),)
$(error RESULT_BASE=$(RESULT_BASE) is $(RB_CLASH)'s result block and $(RB_CLASH) has a measurement in it. Refusing to build $(P) onto it)
endif
SRC_probe0 := start.S uart.S report.c probe0.c
SRC_probe1 := start.S uart.S report.c cache.S victims.S probe1.c
SRC_probe2 := start.S uart.S report.c cache.S exc.S probe2.c
# probe3 links exc.S for the handler and the `break` control, cache.S for
# `rlx_cctl` / `rlx_call0_primed` / `rlx_call2_uncached`, and cells.S for
# everything the cell table needs that neither of those already has.  It does
# NOT link victims.S: its victim is two words and lives in a template cells.S
# assembles, which the arena is a run-time copy of -- so the sixteen 1 KiB-
# aligned functions probe1 carries would be 16 KiB of `.text` nothing executes.
SRC_probe3 := start.S uart.S report.c cache.S exc.S cells.S probe3.c
SRC        := $(SRC_$(P))
# The result block's length in words, so `show` prints a DW that reads all of it.
# 88 was printed for BOTH payloads until 2026-08-25 and is right for neither: it
# returns probe1's header and ten of its thirteen rows, stopping before the seal
# -- the one word that separates a completed run from a truncated one.
#
# probe2 went 537 -> 809 on 2026-08-25, when the census gained its second pass:
# 40 header words, 256 rows of three (two primed reads and a state word), and
# the seal.
#
# These mirror RB_WORDS in the payload sources and `tools/test-rlxprobe.sh` is
# what keeps them honest; it recomputes both from the C and fails if they drift.
RB_WORDS_probe0 := 0
RB_WORDS_probe1 := 137
RB_WORDS_probe2 := 809
# probe3: 64 header + 205 cell results + 16 rows x 8 + 256 scratchpad bitmap
# words + 64 RETAINED bitmap words + seal.
# 🔄 2026-08-31: 641 -> 707.  The retained bitmap got its own region (the block
# advertised a pattern the shared scratchpad no longer held) and Group W's M(T)
# ladder took two result words.
# 🔄 2026-08-31: 707 -> 718.  Group F -- the memory-mapped SPI window --
# took eleven, and it is the only instrument that can answer `FW-34`'s last row
# now that `LDR-42` has shown no loader command reads through that window.
# The read-back is `DW 80A02000 718` = 15 + 2 + 47 x 180 + 9 = 8,486 bytes and
# 2.21 s at 3840 B/s (LDR-07, fitted over 91 captures by tools/reply-size.py) --
# 0.04 s more than the 707-word block and 0.23 s more than the 641-word one.
# That is 88 % of the largest `DW` this loader has ever executed -- 820 words /
# 9,661 bytes, 量 H2g -- and three digits, so it does not test whether the
# loader accepts a four-digit decimal length.  Cell `P3` tests that separately
# and nothing here depends on the answer.
#
# ⚠️ THE OVER-RUN MARGIN IS TWO VISIBLE WORDS, AND IT IS NO LONGER LUCK.
# `DW` rounds up to a multiple of four, so 641 returned 644 and w641..w643 of
# the poison margin came back free; 707 returned 708 and only w707 did; 718
# returns 720 and w718..w719 do.  Each of those was the remainder falling out
# that way -- so probe3.c now carries `rb_layout_adds_up`'s sibling,
# `rb_readback_shows_poison`, which refuses to BUILD a layout whose word count
# is a multiple of four and would therefore return no poison word at all.  The
# control itself is unweakened either way: a payload that writes past its own
# block writes UPWARD from the seal, so the first poison word is the first one
# it reaches.  RB_POISON_W is still RB_WORDS + 8 and a longer explicit `DW`
# reads the rest.
RB_WORDS_probe3 := 718

# probe2's build stamp, recomputed here from the same bit positions probe2.c's
# FLAGS_W uses. It is a SECOND copy of that arithmetic on purpose: the payload
# materialises the constant into its own code, `show` computes it from the
# knobs, and `tools/test-rlxprobe.sh` F1 asserts the two agree by finding the
# top half in the disassembly. A number printed beside an image has to have been
# derived independently of it, or it is the image repeating itself.
FLAGS_HEX   = $(shell printf '%08x' $$(( 0x50000000 | 0x0002 \
                | ($(RESET) << 16) | ($(CLEAR_BEV) << 17) \
                | ($(RET_ERET) << 18) | ($(ISC) << 19) | ($(GEOM) << 20) )))

OBJDIR     := $(BUILD)/$(P)
OBJS       := $(patsubst %.S,$(OBJDIR)/%.o,$(filter %.S,$(SRC))) \
              $(patsubst %.c,$(OBJDIR)/%.o,$(filter %.c,$(SRC)))
ELF        := $(OBJDIR)/$(P).elf
BIN        := $(OBJDIR)/$(P).bin

.PHONY: all payload clean dis show gate-check qemu
.DELETE_ON_ERROR:

all:
	@for p in $(PAYLOADS); do \
	    echo "=== $$p ==="; \
	    $(MAKE) --no-print-directory payload P=$$p || exit 1; \
	 done

payload: $(BIN)

$(OBJDIR):
	@mkdir -p $(OBJDIR)

# Every knob above reaches the compiler through -D and through nothing else, so
# without this stamp a rebuild after `RESULT_BASE=...` changed prints `Nothing to
# be done for 'payload'` and ships the previous binary -- while `show` prints the
# RESULT_BASE you asked for beside it.  Measured 2026-08-25, on the artefact that
# was in this tree: a probe2 built for 0x80A00000 would have been uploaded as the
# 0x80A01000 build and poisoned probe1's result block.  The suite never saw it
# because every case in it builds into a fresh BUILD= directory -- a good habit
# hiding the bug it would otherwise have caught.  R3/R4 there build twice into
# one directory and fail without this.
#
# Evaluated at parse time rather than as a FORCE-driven phony target, so that
# `.flags` stays an ordinary file prerequisite and `make -n` still reports
# honestly about what would rebuild.
# LOADADDR and STACK_SIZE are in the stamp although neither reaches a -D. They
# reach the LINKER, through --defsym, and nothing downstream of $(OBJS) depends
# on them -- so `make LOADADDR=0x81000000` in a directory that already held a
# 0x80500000 build relinked nothing and left an image for the wrong address with
# `show` printing the address that had been asked for beside it. That is the
# same defect class as the RESULT_BASE one measured on 2026-08-25, in the one
# knob whose drift ships an image linked somewhere the loader will not jump.
# `docs/rlxprobe-audit-2026-08-25.md` parked it with the suite work; this is the
# suite work. Objects rebuild too, which is wasteful and correct.
$(shell mkdir -p $(OBJDIR); echo '$(DEFS) LOADADDR=$(LOADADDR) STACK_SIZE=$(STACK_SIZE)' \
        | cmp -s - $(OBJDIR)/.flags \
        || echo '$(DEFS) LOADADDR=$(LOADADDR) STACK_SIZE=$(STACK_SIZE)' > $(OBJDIR)/.flags)

$(OBJDIR)/%.o: $(HERE)%.S $(HERE)rlxdefs.h $(OBJDIR)/.flags | $(OBJDIR)
	$(CC) $(ASFLAGS) -c -o $@ $<

$(OBJDIR)/%.o: $(HERE)%.c $(HERE)rlxprobe.h $(HERE)rlxdefs.h $(OBJDIR)/.flags | $(OBJDIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(ELF): $(OBJS) $(HERE)rlxprobe.lds
	$(CC) $(LDFLAGS) -Wl,-Map,$(OBJDIR)/$(P).map -o $@ $(OBJS)

# THE GATE.  Nothing downstream of this exists unless hazlint exited 0.
$(OBJDIR)/$(P).gate: $(ELF) $(HAZLINT)
	@echo '--- gate: tools/hazlint on the linked payload ---'
	$(HAZLINT) $<
	@touch $@

# No --only-section here, on purpose.  A hard-coded section list is a filter
# that drops silently; these two assertions are checks that fail loudly.
#
#   1. the raw image is exactly as long as every section that HAS contents
#      (_bss_start - LOAD_ADDR), so nothing was dropped on the way out and
#      nothing padded it.  Not `_end`, which is past `.bss`: `.bss` is NOBITS
#      and objcopy is right not to emit it, so comparing against `_end` would
#      fail on any payload that has one -- and probe1 does;
#   2. byte 0 of the raw image is the first instruction of _start, because the
#      loader's `J` goes to the load address and not to an entry symbol.
$(BIN): $(OBJDIR)/$(P).gate
	$(OBJCOPY) -O binary $(ELF) $@
	@bs=$$($(NM) $(ELF) | awk '$$3=="_bss_start"{print $$1}'); \
	 be=$$($(NM) $(ELF) | awk '$$3=="_bss_end"{print $$1}'); \
	 want=$$(( 0x$$bs - $(LOADADDR) )); \
	 got=$$(wc -c < $@); \
	 if [ "$$want" != "$$got" ]; then \
	     echo "  FAIL   raw image is $$got bytes, the sections WITH CONTENTS are $$want (_bss_start = 0x$$bs)"; \
	     exit 1; \
	 fi; \
	 echo "  ok     raw image == every section that has contents, $$got bytes"; \
	 echo "  ok     .bss is $$(( 0x$$be - 0x$$bs )) bytes, and start.S zeroes it"
	@w=$$($(OBJDUMP) -d $(ELF) \
	       | awk '/^[0-9a-f]+ <_start>:/{getline; print $$2; exit}'); \
	 b=$$(od -An -tx1 -N4 $@ | tr -d ' \n'); \
	 if [ "$$w" != "$$b" ]; then \
	     echo "  FAIL   image starts with $$b, _start's first instruction is $$w"; \
	     exit 1; \
	 fi; \
	 echo "  ok     byte 0 of the image is _start's first instruction, $$b"
	@echo
	@$(MAKE) --no-print-directory show P=$(P)

# The control on the gate.  A gate that has never refused anything is a gate
# nobody has shown to be closed.  This plants P9-12's own bug -- a `lbu`
# followed by an `andi` on the loaded register -- and fails the build if the
# gate lets it through.
gate-check: | $(OBJDIR)
	@echo '--- gate-check: the build must REFUSE a planted load-use hazard ---'
	@printf '\t.set noreorder\n\t.set nomacro\n\t.text\n\t.globl _hazard\n_hazard:\n\tlbu\t$$10,0($$9)\n\tandi\t$$10,$$10,0x60\n\tjr\t$$31\n\tnop\n' > $(OBJDIR)/planted.S
	@$(CC) $(ASFLAGS) -c -o $(OBJDIR)/planted.o $(OBJDIR)/planted.S
	@if $(HAZLINT) $(OBJDIR)/planted.o >$(OBJDIR)/planted.log 2>&1; then \
	    echo '  FAIL   the gate accepted a payload with P9-12'"'"'s own bug in it'; \
	    sed 's/^/         /' $(OBJDIR)/planted.log; exit 1; \
	 else \
	    rc=$$?; \
	    if [ $$rc -ne 1 ]; then \
	        echo "  FAIL   the gate exited $$rc, not 1 -- it refused for the wrong reason"; \
	        sed 's/^/         /' $(OBJDIR)/planted.log; exit 1; \
	    fi; \
	    echo '  ok     the gate refused it, exit 1:'; \
	    grep -E 'VIOLATIONS|reads \$$' $(OBJDIR)/planted.log | sed 's/^/         /'; \
	 fi

dis: $(ELF)
	$(OBJDUMP) -d -m mips:3000 $< | sed -n '/Disassembly/,$$p'

show: $(BIN)
	@echo 'payload    $(BIN)'
	@echo 'load addr  $(LOADADDR)      entry is byte 0 of the image'
	@printf 'size       %s bytes\n' "$$(wc -c < $(BIN))"
	@printf 'sha256     %s\n' "$$(sha256sum $(BIN) | cut -d' ' -f1)"
	@printf 'first word %s   (must be the first instruction of _start)\n' \
	        "$$($(OBJDUMP) -d $(ELF) | sed -n 's/^ *$(patsubst 0x%,%,$(LOADADDR)):\t\([0-9a-f]*\).*/\1/p' | head -1)"
	@echo 'reset      RESET=$(RESET)   1 = arm the watchdog and hand the prompt back with no power cycle'
ifneq ($(filter $(P),probe2 probe3),)
	@echo 'flags      $(FLAGS_HEX)   header word 5, and the banner prints it'
	@echo 'flush      CCTL 0x002 -- measured sufficient, R1d decision 1. Not a knob'
	@echo 'isc        ISC=$(ISC)   1 = rlx_isc_inv is linked. probe2/probe3 must be 0'
endif
ifeq ($(P),probe3)
	@printf 'template   %s .. %s   the two-word victim, GUARD FIRST\n' \
	        "$$($(NM) $(ELF) | awk '$$3=="rlx_vic_template"{print "0x"$$1}')" \
	        "$$($(NM) $(ELF) | awk '$$3=="rlx_vic_template_end"{print "0x"$$1}')"
	@printf 'cp3 stubs  %s   eight, 12 bytes each\n' \
	        "$$($(NM) $(ELF) | awk '$$3=="rlx_cp3_stubs"{print "0x"$$1}')"
	@printf 'outside I  %s cache op(s) + %s mfc3 -- every word in this image that\n' \
	        "$$($(OBJDUMP) -d $(ELF) | grep -cE '[.]word[[:space:]]+0xbd[0-9a-f]{6}')" \
	        "$$($(OBJDUMP) -d $(ELF) | grep -cE '[[:space:]]mfc3[[:space:]]')"
	@echo '           is not MIPS-I. tools/test-rlxprobe.sh names each one and'
	@echo '           fails if the set changes -- probe1/probe2 assert zero, and'
	@echo '           probe3 cannot, because executing them IS question (c).'
	@echo 'stale check the banner must read  rb=$(RB_LC_BARE)  -- LOWER case, because'
	@echo '           report.c s digit table is 0123456789abcdef while the loader s'
	@echo '           is upper. rb=80a00000 or rb=80a01000 means this image is a'
	@echo '           probe1/probe2-based build and is about to poison a measurement.'
endif
ifneq ($(filter $(P),probe1 probe2 probe3),)
	@echo 'result     RESULT_BASE=$(RESULT_BASE)   read it back with: DW $(patsubst 0x%,%,$(RESULT_BASE)) $(RB_WORDS_$(P))'
ifneq ($(filter $(P),probe1),)
	@printf 'victims    %s .. %s\n' \
	        "$$($(NM) $(ELF) | awk '$$3=="rlx_victims"{print "0x"$$1}')" \
	        "$$($(NM) $(ELF) | awk '$$3=="rlx_victims_end"{print "0x"$$1}')"
endif
	@echo 'geom       GEOM=$(GEOM)   base $(GEOM_BASE)   1 = ARMED, and it can write 1 MiB'
	@echo 'uart       THR $(UART_THR)  LSR $(UART_LSR)'
	@echo 'vectors    UTLB $(VEC_UTLB)  general $(VEC_GENERAL)   CLEAR_BEV=$(CLEAR_BEV)'
	@if [ '$(VEC_GENERAL)' != '0x80000080' ] || [ '$(CLEAR_BEV)' != '0' ] || [ '$(RET_ERET)' != '0' ] \
	    || [ '$(UART_THR)' != '0xB8002000' ]; then \
	    echo; echo '  *** NOT A DEVICE BUILD ***  one of UART_THR / VEC_GENERAL /'; \
	    echo '  CLEAR_BEV / RET_ERET is not at its default. This image is'; \
	    echo '  for qemu.  It does not check VEC_UTLB or UART_LSR.'; \
	 fi
endif

# qemu validates the HARNESS and never an answer.  qemu-system-mips interlocks
# the load delay slot and this core does not, so a payload that computes the
# right value under qemu tells you the control flow is right and nothing about
# the silicon.  `tools/rlxprobe/qemu-run.sh` carries the machine and the UART
# base and the reasons for both.
qemu: $(BIN)
	@$(HERE)qemu-run.sh $(P) $(BIN) $(ELF)

clean:
	rm -rf $(BUILD)
