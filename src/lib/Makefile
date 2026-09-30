# src/lib/Makefile -- an INCLUDE FRAGMENT, not a buildable directory.
#
# SPEC-R7 § 2: `src/lib/` is shared code compiled into each program; there are
# no shared libraries and no `librlxfw.a` either -- a static archive would let
# a program link an object it was not built with, and the R7 census counts the
# objects that went into each ELF.  So each program compiles these sources
# itself, into its own object directory, and this file only says where they are
# and what they need.
#
# Usage, from src/<prog>/Makefile:
#
#     all: <the program>                  # declare YOUR default goal FIRST
#     include ../lib/Makefile
#     ... $(RLXLIB_SRCS) ... $(RLXLIB_CPPFLAGS) ...
#
# DELIBERATELY NO TARGETS.  GNU make takes the default goal from the first
# target it sees in ANY makefile, included ones included; a rule here would
# silently become the default goal of whichever program included this file
# before declaring its own.  So this fragment defines variables only, and
# `make -C src/lib` correctly says there is nothing to make.
#
# Every variable is prefixed RLXLIB_ so that a program's own names cannot
# collide with them.

# The directory this file is in, absolute, with no trailing slash.  Taken from
# MAKEFILE_LIST at the moment of inclusion, which is this file -- not from the
# includer's path, and not from a relative path that would break the moment a
# program's Makefile is invoked with -C from somewhere else.
RLXLIB_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

# Compilation units, in link order.  A program that needs a subset still
# compiles all of them: the dependency graph between four files is not worth a
# per-program list that can go stale.
# `R7-8` added sha256 and kdf: cfgstore's `passwd` reaches the real scrypt now
# (it used to refuse, because kdf.h was a declaration returning -ENOSYS), and
# kdf.c needs sha256.c.  src/cfgstore/Makefile is this fragment's only includer,
# so the cost is one extra object in one program.
RLXLIB_NAMES  := crc32 tlv schema cfg sha256 kdf
RLXLIB_SRCS   := $(addprefix $(RLXLIB_DIR)/,$(addsuffix .c,$(RLXLIB_NAMES)))
RLXLIB_HDRS   := $(addprefix $(RLXLIB_DIR)/,crc32.h tlv.h schema.h cfg.h kdf.h                                             sha256.h)
RLXLIB_CPPFLAGS := -I$(RLXLIB_DIR)

# Sanity: a stale include path is a link error pages later, so say it here.
ifeq ($(wildcard $(RLXLIB_DIR)/cfg.c),)
$(error src/lib/Makefile: RLXLIB_DIR=$(RLXLIB_DIR) does not hold cfg.c)
endif

RLXLIB_HAVE := 1
