#!/bin/sh
# rlxfw's /init.  R3 rung 1.
#
# This is the ONLY executable content in the initramfs that is not this unit's
# own (config/rlxfw-initramfs.tsv).  It is four commands because Decision B is
# that userspace stays a controlled variable: if the shell does not come up,
# the shell is not the new thing.
#
# The string below is the seating's rung-1 discriminator.  It is emitted by
# code, at a point in the boot, from a file that exists only in this tree --
# `strings` over this unit's own kernel and rootfs does not contain it, and
# that is checked at the desk before the seating (RUNSHEET.md B5, P6).
echo "rlxfw: init running, RLXFW-R3-RUNG1-OK"

mount -t proc  proc  /proc
mount -t sysfs sysfs /sys

# `exec` and not a call: PID 1 must not exit.  If the shell dies the kernel
# panics with "Attempted to kill init", which is a distinct capture from the
# hang that a missing /dev/console produces, and the seating sheet has to be
# able to tell those two apart.
exec /bin/sh
