#!/rlxsim/busybox sh
# shellcheck shell=sh
# maltarun-rdinit.sh -- the loader `make run` puts in its SECOND cpio.  The
# kernel runs it as rdinit=/rlxsim/load inside qemu-system-mips -M malta and
# nowhere else; it is not part of v1.0 and not part of rlxfw.  Its interpreter
# is Debian's static busybox at /rlxsim/busybox, so on any host this file
# cannot run at all.
#
# It does four things, then hands PID 1 to v1.0's own /init:
#   1. loads Debian's mii.ko and pcnet32.ko, the driver for qemu's PCnet card,
#      which stands in for the board's NIC and switch drivers;
#   2. renames the card eth0 -> rlx0, so that /init's own interface setup
#      (SIOCSIFADDR, SIOCSIFNETMASK, SIOCSIFFLAGS on rlx0) runs;
#   3. given rlxsim.omit=brokerd or rlxsim.omit=httpd on the kernel command
#      line, deletes that one program from the unpacked root: the host test's
#      two red controls.  The cpio bytes are the same in every run;
#   4. unmounts the /proc it mounted to read the command line, and execs /init.
#
# Every path it adds lives under /rlxsim/; it replaces none of v1.0's
# (tools/maltarun.py checks the two cpio listings before every boot).
B=/rlxsim/busybox
say() { $B echo "rlxsim: $*"; }

say "simulation loader, tools/maltarun-rdinit.sh: not v1.0, not the device"
$B mount -t proc proc /proc || say "mount /proc FAILED"
$B insmod /rlxsim/mii.ko || say "insmod mii.ko FAILED"
$B insmod /rlxsim/pcnet32.ko || say "insmod pcnet32.ko FAILED"
if $B ip link set dev eth0 name rlx0; then
	say "eth0 renamed rlx0"
else
	say "eth0 -> rlx0 rename FAILED"
fi
for tok in $($B cat /proc/cmdline); do
	case "$tok" in
	rlxsim.omit=brokerd | rlxsim.omit=httpd)
		p="/usr/sbin/${tok#rlxsim.omit=}"
		if $B rm "$p"; then
			say "left out $p ($tok)"
		else
			say "could not leave out $p ($tok)"
		fi
		;;
	esac
done
$B umount /proc || say "umount /proc FAILED"
exec /init
