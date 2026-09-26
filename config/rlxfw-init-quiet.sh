#!/bin/sh
# rlxfw's quiet /init: config/rlxfw-init.sh without its LAN block.  R6b-8.
#
# It reaches an image only through
#   tools/mkinitramfs.py build --init config/rlxfw-init-quiet.sh
# which replaces the source of the declaration's one /init row and refuses a
# file that is not tracked under config/, not 100755 in the index, or whose
# first command is not the rung-1 line below.
#
# Why it exists: NET-25 needs eth4 to be the first interface opened after
# power-on, and the standard /init opens rlx0 before the shell starts (its
# `ifconfig rlx0 10.1.1.3 up`).  This one opens no interface and writes to no
# /proc node, so which interface opens first is decided by the card.  Every
# card on an image built with it types the LAN verbs itself: a cell copied
# from a standard-/init card assumes a LAN that is not up.
#
# It names no driver's /proc node, on purpose: this text is packed into the
# image's .init.ramfs, and a marks witness that searches the image for a
# driver's name would find it here whether or not the driver is built (FW-143).
#
# The string below is the seating's rung-1 discriminator.  It is emitted by
# code, at a point in the boot, from a file that exists only in this tree --
# `strings` over this unit's own kernel and rootfs does not contain it, and
# that is checked at the desk before the seating (RUNSHEET.md B5, P6).  It is
# also byte-identical across every committed rlxfw boot, which
# tools/bootbytes.py relies on, so it does not change.
echo "rlxfw: init running, RLXFW-R3-RUNG1-OK"

mount -t proc  proc  /proc
mount -t sysfs sysfs /sys

# `exec` and not a call: PID 1 must not exit.  If the shell dies the kernel
# panics with "Attempted to kill init", which is a distinct capture from the
# hang that a missing /dev/console produces, and the seating sheet has to be
# able to tell those two apart.
exec /bin/sh
