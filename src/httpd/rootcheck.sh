#!/bin/bash
# src/httpd/rootcheck.sh -- the half of httpd the host suite cannot reach.
#
# srv_drop() needs to be root to run at all, and srv_loop()'s accept/fork/limiter
# loop needs a listening socket and several peers, so neither is in `make test`.
# This script runs the real binary as root on a throwaway port and asks the
# questions that only a live process can answer:
#
#   1. does the process end up as uid 100 / gid 100 with no supplementary groups?
#   2. is the chroot real -- can a request reach a file outside the web root?
#   3. does the parent answer a normal request while four silent peers from another
#      address are holding their connections open?
#   4. does the login limiter, which lives in the PARENT and is asked over a
#      socketpair, actually return 429 after its burst -- end to end, through a
#      fork, not through a unit test's function pointer?
#
# Every question is asked with a control beside it: a case that must succeed next
# to the case that must fail, because a server that refuses everything would pass
# a test made only of refusals.
#
# Usage:  sudo src/httpd/rootcheck.sh <httpd binary> <web root> [port]
# Exit:   0 every check held, 1 a check failed, 2 usage / not root.
#
# What it does NOT establish: anything about the device.  This is Linux 6.x on
# x86-64 under WSL; the syscalls are the same ones and the kernel is not.
set -u

BIN=${1:-}
ROOT=${2:-}
PORT=${3:-18080}
[ -x "$BIN" ] || { echo "usage: rootcheck.sh <httpd> <webroot> [port]"; exit 2; }
[ -d "$ROOT" ] || { echo "usage: rootcheck.sh <httpd> <webroot> [port]"; exit 2; }
[ "$(id -u)" = 0 ] || { echo "REFUSED: rootcheck.sh must be root"; exit 2; }
command -v curl > /dev/null || { echo "REFUSED: no curl"; exit 2; }

n=0
bad=0
ok() {
	n=$((n + 1))
	if [ "$1" = 1 ]; then printf 'ok %d - %s\n' "$n" "$2"
	else bad=$((bad + 1)); printf 'not ok %d - %s: %s\n' "$n" "$2" "${3:-}"; fi
}

"$BIN" --root "$ROOT" --port "$PORT" --sock /run/no-broker.sock \
	> /tmp/rootcheck.$$ 2>&1 &
PID=$!
# wait for the port, up to 2 s, without sleeping blindly
i=0
while [ $i -lt 40 ]; do
	if curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$PORT/" 2>/dev/null; then
		break
	fi
	i=$((i + 1))
	sleep 0.05
done
kill -0 "$PID" 2>/dev/null || { echo "not ok - httpd exited:"; cat /tmp/rootcheck.$$; exit 1; }

# ---- 1. the credentials the kernel actually gave it -------------------------
CPID=$PID
UID_NOW=$(awk '/^Uid:/{print $2}' "/proc/$CPID/status" 2>/dev/null)
GID_NOW=$(awk '/^Gid:/{print $2}' "/proc/$CPID/status" 2>/dev/null)
GRP_NOW=$(awk '/^Groups:/{$1=""; print}' "/proc/$CPID/status" 2>/dev/null | tr -d ' ')
ok "$([ "$UID_NOW" = 100 ] && echo 1 || echo 0)" "the process runs as uid 100" \
	"Uid: $UID_NOW"
ok "$([ "$GID_NOW" = 100 ] && echo 1 || echo 0)" "and gid 100" "Gid: $GID_NOW"
ok "$([ -z "$GRP_NOW" ] && echo 1 || echo 0)" \
	"with an empty supplementary group list" "Groups: $GRP_NOW"
RT=$(readlink "/proc/$CPID/root" 2>/dev/null)
ok "$([ "$RT" = "$ROOT" ] && echo 1 || echo 0)" "and a root of $ROOT" "root=$RT"

# ---- 2. the chroot, refusing and permitting ---------------------------------
st() { curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$@"; }
ok "$([ "$(st "http://127.0.0.1:$PORT/")" = 200 ] && echo 1 || echo 0)" \
	"CONTROL: / is served (200), so a 404 below means something" \
	"got $(st "http://127.0.0.1:$PORT/")"
ok "$([ "$(st "http://127.0.0.1:$PORT/static/style.css")" = 200 ] && echo 1 || echo 0)" \
	"CONTROL: /static/style.css is served (200)"
for p in "/etc/passwd" "/static/../../../etc/passwd" "/static/%2e%2e/etc/passwd"; do
	c=$(st "http://127.0.0.1:$PORT$p")
	ok "$([ "$c" != 200 ] && echo 1 || echo 0)" "$p is not served" "got $c"
done
# and the bytes: nothing that looks like /etc/passwd comes back
B=$(curl -s --max-time 3 "http://127.0.0.1:$PORT/etc/passwd")
ok "$(printf '%s' "$B" | grep -q 'root:' && echo 0 || echo 1)" \
	"no /etc/passwd content in the answer"

# ---- 3. the security headers, on a real response ---------------------------
Hh=$(curl -s -D - -o /dev/null --max-time 3 "http://127.0.0.1:$PORT/")
for h in "X-Frame-Options: DENY" "Content-Security-Policy: default-src 'self'" \
	 "X-Content-Type-Options: nosniff" "Connection: close"; do
	ok "$(printf '%s' "$Hh" | grep -qiF "$h" && echo 1 || echo 0)" \
		"header on the wire: $h"
done
Hs=$(curl -s -D - -o /dev/null --max-time 3 "http://127.0.0.1:$PORT/api/status")
ok "$(printf '%s' "$Hs" | grep -qiF "Cache-Control: no-store" && echo 1 || echo 0)" \
	"/api/* carries Cache-Control: no-store"
ok "$(printf '%s' "$Hh" | grep -qiF "Cache-Control: no-store" && echo 0 || echo 1)" \
	"CONTROL: / does not (so the check can tell them apart)"

# ---- 4. four silent peers must not hold the server shut --------------------
# The silent peers come from 127.0.0.1 and the live request from 127.0.0.2, which
# is a different peer address to the kernel, so this tests the per-address
# connection cap rather than the total.
PEERS=""
for i in 1 2 3 4; do
	(exec 3<>/dev/tcp/127.0.0.1/$PORT; read -r -t 3 -u 3 || true) &
	PEERS="$PEERS $!"
done
sleep 0.5
c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 --interface 127.0.0.2 \
	"http://127.0.0.1:$PORT/" 2>/dev/null)
ok "$([ "$c" = 200 ] && echo 1 || echo 0)" \
	"a request from another address is answered while 4 peers sit silent" \
	"got $c"
c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 \
	"http://127.0.0.1:$PORT/" 2>/dev/null)
ok "$([ "$c" = 503 ] && echo 1 || echo 0)" \
	"and the fifth from the SAME address is 503, not a queue" "got $c"
# The parent writes that 503 itself, on a different call path from every other
# response, so its Content-Length is computed by different code.  curl exits 18 on
# a body shorter than the declared length, so curl's exit status IS the check: the
# hand-written blob this replaced declared 29 bytes for a 28-byte body, and no test
# in the suite could see it.
curl -s -o /dev/null --max-time 4 "http://127.0.0.1:$PORT/" 2>/dev/null
crc=$?
ok "$([ "$crc" = 0 ] && echo 1 || echo 0)" \
	"the parent's own 503 body is as long as its Content-Length" \
	"curl exit $crc (18 = short body)"
# `wait` with no argument would wait for the SERVER too, which never exits.
for q in $PEERS; do wait "$q" 2>/dev/null; done

# ---- 5. the login limiter, through a fork and a socketpair ----------------
# The broker is not there, so a granted login is 503 and a refused one is 429.
# The burst is 3 (RL_KDF_BURST), so: 503, 503, 503, then 429.
codes=""
for i in 1 2 3 4 5; do
	c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 \
		-H 'Content-Type: application/json' \
		--data '{"password":"abcdefgh"}' \
		"http://127.0.0.1:$PORT/api/login" 2>/dev/null)
	codes="$codes $c"
done
echo "# /api/login codes:$codes"
ok "$(printf '%s' "$codes" | grep -q '503' && echo 1 || echo 0)" \
	"CONTROL: the first logins get the grant (503, no broker)"
ok "$(printf '%s' "$codes" | grep -q '429' && echo 1 || echo 0)" \
	"the limiter refuses with 429 once its burst is spent"
RA=$(curl -s -D - -o /dev/null --max-time 4 -H 'Content-Type: application/json' \
	--data '{"password":"abcdefgh"}' "http://127.0.0.1:$PORT/api/login" \
	2>/dev/null | grep -i '^Retry-After' | tr -d '\r')
ok "$([ -n "$RA" ] && echo 1 || echo 0)" "and the 429 carries a Retry-After" "$RA"

# ---- 6. no zombies, and the parent is still there -------------------------
Z=$(ps -o stat= --ppid "$PID" 2>/dev/null | grep -c Z || true)
ok "$([ "${Z:-0}" = 0 ] && echo 1 || echo 0)" "no zombie children" "$Z zombies"
ok "$(kill -0 "$PID" 2>/dev/null && echo 1 || echo 0)" \
	"the parent survived every case above"

kill "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
rm -f /tmp/rootcheck.$$

printf '# %d/%d passed\n' "$((n - bad))" "$n"
[ "$n" -ge 23 ] || { echo "REFUSED: only $n cases ran"; exit 1; }
[ "$bad" = 0 ] || exit 1
exit 0
