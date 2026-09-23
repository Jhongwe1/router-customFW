#!/bin/sh
# rlxfw's /init.  R3 rung 1; P2-2 brings the LAN up.
#
# This is the ONLY executable content in the initramfs that is not this unit's
# own (config/rlxfw-initramfs.tsv).  It stays a handful of commands because
# Decision B is that userspace stays a controlled variable: if the shell does
# not come up, the shell is not the new thing.
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

# P2-2, 2026-09-23 (P2 settled item 3): the LAN comes up here, before the
# shell, so a boot reaches "network up" with no verb typed and P2 can time it.
# These are the four verbs every seating since B30 typed by hand (cell
# `A2-UP`), in that order: the switch core first, because rlx0 carries nothing
# without it (B43's control).  No netmask, as in every one of those cells.
# Two console lines bracket the bring-up, so a boot that hangs inside it says
# where; a verb that fails prints its own error and the next one still runs,
# and nothing here can stop the shell from starting.
#   What this gives up: R6b's NET-25 needs eth4 to be the first interface
#   opened after power-on, and this opens rlx0 first -- that seating boots an
#   /init without these lines.
echo "rlxfw: lan bring-up"
echo unlock i-mean-it > /proc/rtl819x-switch
echo start > /proc/rtl819x-switch
echo unlock > /proc/rtl819x-nic
echo netdev on > /proc/rtl819x-nic
ifconfig rlx0 10.1.1.3 up
echo "rlxfw: lan up, rlx0 10.1.1.3"

# `exec` and not a call: PID 1 must not exit.  If the shell dies the kernel
# panics with "Attempted to kill init", which is a distinct capture from the
# hang that a missing /dev/console produces, and the seating sheet has to be
# able to tell those two apart.
exec /bin/sh
