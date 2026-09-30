# src/rlxboot/Makefile -- rlxboot, the signed-container second-stage loader.
#
# THREE THINGS BUILD HERE AND THEY ARE NOT INTERCHANGEABLE.
#
#   make payload     the device image, 0x81800000, rsdk gcc 3.4.6, no libc,
#                    gated by tools/hazlint.  This is the artefact.
#   make hosttest    the same container.c and the same crypto, built by gcc-13
#                    and clang-18 at -Wall -Wextra -Werror and run, plus a
#                    -fsanitize=address,undefined pass.
#   make qemutest    the same sources cross-compiled BIG-ENDIAN MIPS by the same
#                    rsdk gcc and run under qemu-mips-static.  This is the
#                    second source that a little-endian-only bug cannot pass.
#
# qemu CERTIFIES LOGIC AND NEVER CODEGEN OR THE ISA.  That is this repository's
# own rule and it applies with full force here: qemu interlocks the load delay
# slot this core exposes, so a payload that computes the right answer under qemu
# says the control flow is right and nothing whatever about the silicon.  What
# `qemutest` adds over `hosttest` is BYTE ORDER and the vendor compiler's
# codegen being exercised at all -- not a statement that the device will agree.
#
# STAGING.  Every vendor binary runs with its cwd inside $(STAGE), which is under
# $(FWRE_WORK)/rebuild and therefore on ext4.  `config/rlxfw-user/linkprobe/Makefile`
# owns the reason and this one repeats it without restating it: the rsdk driver
# is a 32-bit i386 ELF and every DrvFs path returns EOVERFLOW to its stat().
# Run the whole thing under the tripwire, from a scratch directory:
#
#     tools/vendor-tripwire.sh -- make -C <repo>/src/rlxboot payload
#
#   make hazlint     the gate on its own, plus its refusal control
#   make flashsafe   prove the image cannot program or erase flash
#   make mutate      the two mutation controls: weaken the digest compare, and
#                    reorder verification, and show which test goes red
#   make show        the numbers that go on the bench card
#   make clean

HERE  := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO  := $(abspath $(HERE)../..)
PROBE := $(REPO)/tools/rlxprobe

FWRE_WORK ?= /home/key/fwre-work
STAGE     ?= $(FWRE_WORK)/rebuild/rlxboot
SD        := $(STAGE)/src
BD        := $(STAGE)/build
OUT       ?= $(STAGE)/out

TCROOT ?= $(FWRE_WORK)/rebuild/src-vendor/rtl819x-toolchain/toolchain
TC     ?= rsdk-1.3.6-4181-EB-2.6.30-0.9.30
TCBIN  := $(TCROOT)/$(TC)/bin
CC      = $(TCBIN)/mips-linux-gcc
OBJCOPY = $(TCBIN)/mips-linux-objcopy
OBJDUMP = $(TCBIN)/mips-linux-objdump
NM      = $(TCBIN)/mips-linux-nm

HAZLINT := $(REPO)/tools/hazlint
STAGE2  ?= $(FWRE_WORK)/stage2.bin
PYTHON  ?= /usr/bin/python3

HOSTCC1 ?= gcc-13
HOSTCC2 ?= clang-18

# SPEC-R8a.md s4.  0x81800000, and NOT rlxprobe's 0x80500000 -- that is where
# the payload rlxboot boots is staged, so a rlxboot linked there would verify a
# container whose destination is itself.
LOADADDR   ?= 0x81800000
STACK_SIZE ?= 0x8000

# NO -march.  SPEC-R8a s4 and linkprobe's gate G7a: this toolchain's default IS
# the 4181, and naming an ISA level here is how a payload ends up built for a
# core this die is not.  -fno-stack-protector is absent because gcc 3.4.6 does
# not have it (measured: "unrecognized command line option").
ARCH   = -EB -mabi=32 -msoft-float -G0 -mno-abicalls -fno-pic
CWARN  = -Wall -Wextra -Werror -Wundef -Wshadow
CFLAGS = $(ARCH) -O2 -std=gnu99 -ffreestanding -fno-builtin \
         -fomit-frame-pointer -fno-common $(CWARN) \
         -DRLX_RESET=1 -DRLX_GEOM=0 -DRLX_ISC=0 -DRLX_CLEAR_BEV=0 \
         -DRLX_RET_ERET=0 -DRLX_RESULT_BASE=0u -DRLX_GEOM_BASE=0u \
         -DRLXBOOT_BUILD=0x$(BUILD_ID)u $(CFLAGS_EXTRA)
ASFLAGS = $(ARCH) -DRLX_RESET=1 -DRLX_GEOM=0 -DRLX_ISC=0 -DRLX_CLEAR_BEV=0 \
          -Wa,--fatal-warnings $(CFLAGS_EXTRA)
# --defsym BEFORE -T, and it is not cosmetic: this binutils (2.16-era, shipped
# with gcc 3.4.6) reads the script when it sees -T and a --defsym that comes
# later is not yet in scope, so the link failed with
# "undefined symbol `LOAD_ADDR' referenced in expression".  Newer binutils --
# what `tools/rlxprobe` builds with -- does not care about the order, which is
# exactly why this is written down here rather than left as a working accident.
LDFLAGS = $(ARCH) -nostdlib -nostartfiles -static \
          -Wl,--fatal-warnings \
          -Wl,--defsym,LOAD_ADDR=$(LOADADDR) \
          -Wl,--defsym,STACK_SIZE=$(STACK_SIZE) \
          -Wl,-T,$(SD)/rlxboot/rlxboot.lds

# EXACTLY ONE FILE GETS A WARNING EXEMPTION, and it is an imported one.
# `src/lib/ed25519.c` is TweetNaCl; its `vn()` compares a u32 index with an int
# bound, which is one -Wsign-compare at one site under both host compilers and
# under gcc 3.4.6.  The alternative was editing imported crypto to silence a
# warning, which is not a trade this gate makes.  Every file rlxfw wrote is
# built with the full set and no exemption -- including `src/lib/sha512.c`,
# which is also imported and needs none.
ED_EXEMPT = -Wno-sign-compare

# The sources, and which tree each comes from.  The four rlxprobe files are
# REUSED UNMODIFIED: start.S brings the entry, the stack and the .bss zeroing,
# uart.S the 16550 and the watchdog reset, report.c the two output helpers and
# SAFE_A0's frame, cache.S `rlx_cctl` and `rlx_call2_uncached`.  exc.S is NOT
# here: rlxboot installs no handler.
PROBE_SRC := start.S uart.S cache.S report.c
PROBE_HDR := rlxdefs.h rlxasm.h rlxprobe.h
MY_C      := main.c container.c sha256b.c flashread.c klib.c
MY_S      := jump.S
MY_HDR    := rlxboot.h container.h sha256b.h devkey.h rlxboot.lds
LIB_C     := ed25519.c sha512.c
LIB_HDR   := ed25519.h sha512.h

# The build id: the first 8 hex of the sha256 of every source that reaches the
# image, in a fixed order.  It is what `RLXBOOT-V1 build=` prints, and it is
# RE-DERIVABLE -- the main session identifies a booted image by recomputing it,
# never by comparing it with a number someone typed.
BUILD_ID := $(shell cat \
	$(addprefix $(HERE),$(MY_C) $(MY_S) $(MY_HDR)) \
	$(addprefix $(REPO)/src/lib/,$(LIB_C) $(LIB_HDR)) \
	$(addprefix $(PROBE)/,$(PROBE_SRC) $(PROBE_HDR)) \
	2>/dev/null | sha256sum | cut -c1-8)

ELF := $(BD)/rlxboot.elf
BIN := $(OUT)/rlxboot.bin

.PHONY: all payload stage hazlint hazlint-control flashsafe hosttest qemutest \
        mutate show clean vectors import-check qemu-elf qemupayload

all: payload

# ---------------------------------------------------------------- staging ---

stage:
	@mkdir -p $(SD)/rlxboot $(SD)/lib $(SD)/probe $(BD) $(OUT)
	@cp -f $(addprefix $(HERE),$(MY_C) $(MY_S) $(MY_HDR)) $(SD)/rlxboot/
	@cp -f $(addprefix $(REPO)/src/lib/,$(LIB_C) $(LIB_HDR)) $(SD)/lib/
	@cp -f $(addprefix $(PROBE)/,$(PROBE_SRC) $(PROBE_HDR)) $(SD)/probe/
	@# The rlxprobe sources #include "rlxdefs.h" and "rlxprobe.h" by bare
	@# name, so the include path has to reach them; main.c does the same.
	@echo "staged into $(SD)  (build id $(BUILD_ID))"

# ----------------------------------------------------------------- payload ---

# ONE RECIPE, NOT PER-FILE RULES, and it is a deliberate simplification: every
# object depends on every -D through BUILD_ID, so an incremental build would
# need the flag-stamp machinery `tools/rlxprobe/Makefile` carries for exactly
# that reason.  This build is eleven translation units; rebuilding all of them
# costs less than the first stale object would.
$(ELF): stage
	@set -e; cd $(STAGE); \
	for f in $(MY_C); do \
	    $(CC) $(CFLAGS) -Isrc/rlxboot -Isrc/probe -c -o build/$${f%.c}.o src/rlxboot/$$f; \
	done; \
	for f in $(MY_S); do \
	    $(CC) $(ASFLAGS) -Isrc/rlxboot -Isrc/probe -c -o build/$${f%.S}.o src/rlxboot/$$f; \
	done; \
	$(CC) $(CFLAGS) $(ED_EXEMPT) -Isrc/lib -c -o build/ed25519.o src/lib/ed25519.c; \
	$(CC) $(CFLAGS) -Isrc/lib -c -o build/sha512.o src/lib/sha512.c; \
	for f in $(filter %.S,$(PROBE_SRC)); do \
	    $(CC) $(ASFLAGS) -Isrc/probe -c -o build/p_$${f%.S}.o src/probe/$$f; \
	done; \
	for f in $(filter %.c,$(PROBE_SRC)); do \
	    $(CC) $(CFLAGS) -Isrc/probe -c -o build/p_$${f%.c}.o src/probe/$$f; \
	done; \
	$(CC) $(LDFLAGS) -Wl,-Map,build/rlxboot.map -o build/rlxboot.elf \
	    build/p_start.o build/main.o build/container.o build/sha256b.o \
	    build/flashread.o build/klib.o build/jump.o \
	    build/ed25519.o build/sha512.o \
	    build/p_uart.o build/p_cache.o build/p_report.o
	@echo "linked $(ELF)"

# THE GATE.  `$(BIN)` depends on `$(BD)/rlxboot.gate`, and that file does not
# exist unless hazlint exited 0.  There is no target that produces a runnable
# image while skipping it -- `tools/rlxprobe/Makefile`'s layer two, copied
# because the reason is the same reason.
$(BD)/rlxboot.gate: $(ELF)
	@echo '--- gate: tools/hazlint on the linked payload ---'
	@if [ ! -f $(STAGE2) ]; then \
	    echo "  REFUSED  hazlint's population control needs $(STAGE2)."; \
	    echo "           Pass STAGE2=<path to this unit's stage2.bin>."; \
	    exit 2; \
	 fi
	$(HAZLINT) --stage2 $(STAGE2) $(ELF)
	@touch $@

hazlint: $(BD)/rlxboot.gate hazlint-control

# The control on the gate.  A gate that has never refused anything is a gate
# nobody has shown to be closed.  This plants upstream's P9-12 bug -- a load
# followed by a use of the loaded register -- and fails if hazlint takes it.
hazlint-control: stage
	@echo '--- control: the gate must REFUSE a planted load-use hazard ---'
	@printf '\t.set noreorder\n\t.set nomacro\n\t.text\n\t.globl _hz\n_hz:\n\tlbu\t$$10,0($$9)\n\tandi\t$$10,$$10,0x60\n\tjr\t$$31\n\tnop\n' > $(BD)/planted.S
	@cd $(STAGE) && $(CC) $(ASFLAGS) -c -o build/planted.o build/planted.S
	@if HAZLINT_CHILD=1 $(HAZLINT) $(BD)/planted.o >$(BD)/planted.log 2>&1; then \
	    echo '  FAIL   the gate accepted a load-use hazard'; \
	    sed 's/^/         /' $(BD)/planted.log; exit 1; \
	 else \
	    echo '  ok     the gate refused it:'; \
	    grep -E 'VIOLATIONS|reads \$$' $(BD)/planted.log | sed 's/^/         /'; \
	 fi

$(BIN): $(BD)/rlxboot.gate
	@mkdir -p $(OUT)
	cd $(STAGE) && $(OBJCOPY) -O binary build/rlxboot.elf $(BIN)
	@bs=$$($(NM) $(ELF) | awk '$$3=="_bss_start"{print $$1}'); \
	 want=$$(( 0x$$bs - $(LOADADDR) )); got=$$(wc -c < $(BIN)); \
	 if [ "$$want" != "$$got" ]; then \
	     echo "  FAIL   raw image is $$got bytes, sections with contents are $$want"; \
	     exit 1; \
	 fi; \
	 echo "  ok     raw image == every section that has contents, $$got bytes"
	@w=$$($(OBJDUMP) -d $(ELF) | awk '/^[0-9a-f]+ <_start>:/{getline; print $$2; exit}'); \
	 b=$$(od -An -tx1 -N4 $(BIN) | tr -d ' \n'); \
	 if [ "$$w" != "$$b" ]; then \
	     echo "  FAIL   image starts with $$b, _start's first instruction is $$w"; \
	     exit 1; \
	 fi; \
	 echo "  ok     byte 0 of the image is _start's first instruction, $$b"
	@# No signer in the device image.  ED25519_SIGN and ED25519_KEYGEN are
	@# never defined for this build, and this reads the artefact rather than
	@# the flags -- `rlxfw-marks verify`'s discipline.
	@if $(NM) $(ELF) | grep -qE 'rlx_ed25519_sign|rlx_ed25519_pubkey_from_seed|crypto_sign'; then \
	     echo "  FAIL   the device image contains a signer"; exit 1; \
	 fi
	@echo "  ok     no signer and no key generator in the device image"

payload: $(BIN) flashsafe
	@$(MAKE) --no-print-directory show

show: $(BIN)
	@echo
	@echo 'payload     $(BIN)'
	@printf 'size        %s bytes\n' "$$(wc -c < $(BIN))"
	@printf 'sha256      %s\n' "$$(sha256sum $(BIN) | cut -d' ' -f1)"
	@echo 'load/entry  $(LOADADDR)   byte 0 of the image is _start'
	@echo 'build id    $(BUILD_ID)   printed as RLXBOOT-V1 build=$(BUILD_ID)'
	@echo 'stack       $(STACK_SIZE) reserved above .bss'
	@printf 'bss         %s bytes\n' \
	    "$$(( $$(printf '%d' 0x$$($(NM) $(ELF) | awk '$$3=="_bss_end"{print $$1}')) - \
	          $$(printf '%d' 0x$$($(NM) $(ELF) | awk '$$3=="_bss_start"{print $$1}')) ))"
	@echo 'container   0x81000000   staged by the loader TFTP, limit 0x81700000'
	@echo 'ram counter 0x81700000   "RCNT" + 512 bytes, used when the magic matches'
	@echo 'flash ctr   0xBD3F0000   512 bytes, READ ONLY -- see make flashsafe'

# ------------------------------------------------------------- flash safety ---

flashsafe: $(ELF)
	@$(HERE)test/flashsafe.sh $(OBJDUMP) $(ELF) $(CC) "$(ASFLAGS)" $(BD)

# ---------------------------------------------------------------- host tests ---

vectors:
	@echo "mk-vectors needs the two RFC texts; pass RFC8032= and RFC6234="
	$(PYTHON) $(HERE)test/mk-vectors.py check --rfc8032 $(RFC8032) \
	    --rfc6234 $(RFC6234) --out $(HERE)test/vectors.h

import-check:
	@$(HERE)test/check-import.sh $(REPO)

hosttest:
	@$(HERE)test/run-host-tests.sh $(REPO) $(HOSTCC1) $(HOSTCC2) $(STAGE)/hosttest

# THE USER-MODE ARCH IS NOT THE BARE-METAL ONE, and this cost a debugging round.
# `-G0 -mno-abicalls -fno-pic` are right for a payload linked at a fixed address
# with no dynamic loader and wrong for a Linux binary linked against uClibc: the
# link warned "linking PIC files with non-PIC files" on every object and the
# result segfaulted immediately under qemu-mips-static.  The qemu user-mode build
# gets the byte order, the ABI and the soft float, and nothing else.
QARCH = -EB -mabi=32 -msoft-float

qemutest: stage
	@$(HERE)test/run-qemu-tests.sh $(REPO) $(CC) $(STAGE)/qemutest "$(QARCH)"

# The ELF alone, ungated, for the emulator.  It is NOT `payload`: the UART is
# somewhere else, the gate is not run, and no `.bin` is produced -- so nothing
# this target makes can be mistaken for the artefact.  `run-qemu-payload.sh`
# passes CFLAGS_EXTRA with Malta's 16550 addresses.
qemu-elf: $(ELF)
	@echo
	@echo '  *** NOT A DEVICE BUILD ***  CFLAGS_EXTRA=$(CFLAGS_EXTRA)'
	@echo '  No hazlint gate and no raw image.  For qemu-system-mips only.'

qemupayload:
	@$(HERE)test/run-qemu-payload.sh $(REPO) $(CC) $(OBJCOPY) \
	    $(STAGE)/qemupayload "$(ARCH)" $(STAGE2)

mutate:
	@$(HERE)test/mutate.sh $(REPO) $(HOSTCC1) $(STAGE)/mutate

clean:
	rm -rf $(BD) $(SD) $(OUT) $(STAGE)/hosttest $(STAGE)/qemutest $(STAGE)/mutate
