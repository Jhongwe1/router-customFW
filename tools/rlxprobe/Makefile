# rlxprobe -- bare-metal probe payloads for the Lexra core in the RTL8196E.
#
# The one thing to understand about this file
# -------------------------------------------
# `hazlint` is a GATE, not a lint.  `probe0.bin` depends on `probe0.gate`, and
# `probe0.gate` does not exist unless `tools/hazlint` exited 0.  There is no
# target that produces a runnable payload while skipping it, and `make -k` will
# not get you one either.
#
# That is layer two.  Upstream's `P9-12` post-mortem ends on exactly this
# point: adding two `nop`s made that day pass, and teaching the build to refuse
# is what stops tomorrow's payload.  Item 7 delivered the checker; this line is
# the half that makes it matter.
#
#   make               build, gated
#   make gate-check    prove the gate FAILS on a planted hazard
#   make dis           disassemble what was actually emitted
#   make show          the numbers that go in the runsheet cell
#   make clean
#
# Knobs:
#   LOADADDR=0x80500000   where the payload is linked and jumped to
#   RESET=1               arm the watchdog when main returns (0 = spin instead)
#   CROSS=mips-linux-gnu-

CROSS      ?= mips-linux-gnu-
CC          = $(CROSS)gcc
OBJCOPY     = $(CROSS)objcopy
OBJDUMP     = $(CROSS)objdump

LOADADDR   ?= 0x80500000
STACK_SIZE ?= 0x4000
RESET      ?= 1

HERE       := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
HAZLINT    := $(HERE)../hazlint
BUILD      ?= $(HERE)build

# -march=mips1 needs -msoft-float on gcc 12.4.0, which rejects the flag on its
# own: "cc1: error: '-march=mips1' requires '-mfp32'".  Measured 2026-08-24;
# SPEC.md TC-06.  -msoft-float rather than -mfp32 because this core has no FPU
# and saying so is more honest than saying the FPU is 32-bit.
#
# -G0 turns off small-data addressing, which would need a $gp this payload
# never establishes.  -mno-abicalls -fno-pic because there is no dynamic
# loader and the image is linked at a fixed address.
ARCH        = -march=mips1 -mabi=32 -msoft-float -EB -G0 -mno-abicalls -fno-pic

CFLAGS      = $(ARCH) -O2 -std=gnu99 \
              -ffreestanding -fno-builtin -fno-stack-protector \
              -fomit-frame-pointer -fno-common \
              -Wall -Wextra -Werror -Wundef -Wshadow \
              -DRLX_RESET=$(RESET)
ASFLAGS     = $(ARCH) -DRLX_RESET=$(RESET) -Wa,--fatal-warnings
# --orphan-handling=error: no section may end up in this image that the linker
# script did not place by name.  A section nobody placed lands at an address
# nobody chose, and `objcopy -O binary` would then either drop it or pad the
# image out to reach it -- both silently.
LDFLAGS     = $(ARCH) -nostdlib -nostartfiles -static \
              -Wl,--build-id=none -Wl,--nmagic -Wl,--fatal-warnings \
              -Wl,--orphan-handling=error \
              -Wl,-T,$(HERE)rlxprobe.lds \
              -Wl,--defsym,LOAD_ADDR=$(LOADADDR) \
              -Wl,--defsym,STACK_SIZE=$(STACK_SIZE) \
              -Wl,-Map,$(BUILD)/probe0.map

OBJS        = $(BUILD)/start.o $(BUILD)/uart.o $(BUILD)/probe0.o

.PHONY: all clean dis show gate-check
.DELETE_ON_ERROR:

all: $(BUILD)/probe0.bin

$(BUILD):
	@mkdir -p $(BUILD)

$(BUILD)/%.o: $(HERE)%.S | $(BUILD)
	$(CC) $(ASFLAGS) -c -o $@ $<

$(BUILD)/%.o: $(HERE)%.c $(HERE)rlxprobe.h | $(BUILD)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD)/probe0.elf: $(OBJS) $(HERE)rlxprobe.lds
	$(CC) $(LDFLAGS) -o $@ $(OBJS)

# THE GATE.  Nothing downstream of this exists unless hazlint exited 0.
$(BUILD)/probe0.gate: $(BUILD)/probe0.elf $(HAZLINT)
	@echo '--- gate: tools/hazlint on the linked payload ---'
	$(HAZLINT) $<
	@touch $@

# No --only-section here, on purpose.  A hard-coded section list is a filter
# that drops silently; these two assertions are checks that fail loudly.
#
#   1. the raw image is exactly as long as the linked image (_end - LOAD_ADDR),
#      so nothing was dropped on the way out and nothing padded it;
#   2. byte 0 of the raw image is the first instruction of _start, because the
#      loader's `J` goes to the load address and not to an entry symbol.
$(BUILD)/probe0.bin: $(BUILD)/probe0.gate
	$(OBJCOPY) -O binary $(BUILD)/probe0.elf $@
	@end=$$($(CROSS)nm $(BUILD)/probe0.elf | awk '$$3=="_end"{print $$1}'); \
	 want=$$(( 0x$$end - $(LOADADDR) )); \
	 got=$$(wc -c < $@); \
	 if [ "$$want" != "$$got" ]; then \
	     echo "  FAIL   raw image is $$got bytes, linked image is $$want (_end = 0x$$end)"; \
	     exit 1; \
	 fi; \
	 echo "  ok     raw image == linked image, $$got bytes"
	@w=$$($(OBJDUMP) -d $(BUILD)/probe0.elf \
	       | awk '/^[0-9a-f]+ <_start>:/{getline; print $$2; exit}'); \
	 b=$$(od -An -tx1 -N4 $@ | tr -d ' \n'); \
	 if [ "$$w" != "$$b" ]; then \
	     echo "  FAIL   image starts with $$b, _start's first instruction is $$w"; \
	     exit 1; \
	 fi; \
	 echo "  ok     byte 0 of the image is _start's first instruction, $$b"
	@echo
	@$(MAKE) --no-print-directory show

# The control on the gate.  A gate that has never refused anything is a gate
# nobody has shown to be closed.  This plants P9-12's own bug -- a `lbu`
# followed by an `andi` on the loaded register -- and fails the build if the
# gate lets it through.
gate-check: | $(BUILD)
	@echo '--- gate-check: the build must REFUSE a planted load-use hazard ---'
	@printf '\t.set noreorder\n\t.set nomacro\n\t.text\n\t.globl _hazard\n_hazard:\n\tlbu\t$$10,0($$9)\n\tandi\t$$10,$$10,0x60\n\tjr\t$$31\n\tnop\n' > $(BUILD)/planted.S
	@$(CC) $(ASFLAGS) -c -o $(BUILD)/planted.o $(BUILD)/planted.S
	@if $(HAZLINT) $(BUILD)/planted.o >$(BUILD)/planted.log 2>&1; then \
	    echo '  FAIL   the gate accepted a payload with P9-12'"'"'s own bug in it'; \
	    sed 's/^/         /' $(BUILD)/planted.log; exit 1; \
	 else \
	    rc=$$?; \
	    if [ $$rc -ne 1 ]; then \
	        echo "  FAIL   the gate exited $$rc, not 1 -- it refused for the wrong reason"; \
	        sed 's/^/         /' $(BUILD)/planted.log; exit 1; \
	    fi; \
	    echo '  ok     the gate refused it, exit 1:'; \
	    grep -E 'VIOLATIONS|reads \$$' $(BUILD)/planted.log | sed 's/^/         /'; \
	 fi

dis: $(BUILD)/probe0.elf
	$(OBJDUMP) -d -m mips:3000 $< | sed -n '/Disassembly/,$$p'

show: $(BUILD)/probe0.bin
	@echo 'payload    $(BUILD)/probe0.bin'
	@echo 'load addr  $(LOADADDR)      entry is byte 0 of the image'
	@printf 'size       %s bytes\n' "$$(wc -c < $(BUILD)/probe0.bin)"
	@printf 'sha256     %s\n' "$$(sha256sum $(BUILD)/probe0.bin | cut -d' ' -f1)"
	@printf 'first word %s   (must be the first instruction of _start)\n' \
	        "$$($(OBJDUMP) -d $(BUILD)/probe0.elf | sed -n 's/^ *$(patsubst 0x%,%,$(LOADADDR)):\t\([0-9a-f]*\).*/\1/p' | head -1)"
	@echo 'reset      RESET=$(RESET)   1 = arm the watchdog and hand the prompt back with no power cycle'

clean:
	rm -rf $(BUILD)
