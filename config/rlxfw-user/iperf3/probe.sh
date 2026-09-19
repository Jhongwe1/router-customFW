#!/bin/bash
# a7-iperf-probe.sh -- measure, do not assume.
# Every line of the hand-written config.h has to come from one of these probes.
W=/home/key/fwre-work/iperf3-port
TC=/home/key/fwre-work/rebuild/r2ab/tc/rsdk-1.3.6-4181-EB-2.6.30-0.9.30
CC=$TC/bin/mips-linux-gcc
NM=$TC/bin/mips-linux-nm
SYSINC=$TC/mips-linux/include
mkdir -p $W/probe
cd $W/probe || exit 1     # NEVER the repo root, NEVER src-vendor

pass() { printf '%-34s %s\n' "$1" "$2"; }

# ---- 1. does gcc 3.4.6 take -std=gnu99 at all -------------------------
echo "== compiler flags =="
echo 'int main(void){ for(int i=0;i<1;i++){} int j=1; j++; return j-1; }' > f.c
$CC -std=gnu99 -c f.c -o f.o 2>e.txt && pass "-std=gnu99 + mixed decls" OK || { pass "-std=gnu99" FAIL; head -3 e.txt; }
printf 'struct s{int a;int b;};\nstruct s x = { .b = 2, .a = 1 };\nint main(void){return x.a-1;}\n' > d.c
$CC -std=gnu99 -c d.c -o d.o 2>e.txt && pass "designated initialisers" OK || { pass "designated init" FAIL; head -3 e.txt; }
printf 'struct s{int a;};\nint f(struct s v){return v.a;}\nint main(void){return f((struct s){1})-1;}\n' > cl.c
$CC -std=gnu99 -c cl.c -o cl.o 2>e.txt && pass "compound literals" OK || { pass "compound literals" FAIL; head -3 e.txt; }
printf '#include <stdint.h>\nint main(void){uint64_t x=1;return (int)x-1;}\n' > si.c
$CC -std=gnu99 -c si.c -o si.o 2>e.txt && pass "stdint.h / uint64_t" OK || { pass "stdint.h" FAIL; head -3 e.txt; }
# default arch: what does it actually emit?
echo 'int main(void){return 0;}' > a.c
$CC -c a.c -o a.o 2>/dev/null && $TC/bin/mips-linux-readelf -h a.o 2>/dev/null | grep -iE 'Flags|Machine|Data' | sed 's/^/    default: /'

# ---- 2. headers -------------------------------------------------------
echo
echo "== headers =="
for h in sys/socket.h netinet/tcp.h netinet/in.h netinet/sctp.h linux/in6.h \
         stdint.h getopt.h poll.h sched.h sys/sendfile.h pthread.h \
         sys/select.h arpa/inet.h netdb.h sys/uio.h; do
  printf '#include <%s>\nint main(void){return 0;}\n' "$h" > h.c
  if $CC -std=gnu99 -c h.c -o h.o 2>/dev/null; then pass "$h" present; else pass "$h" ABSENT; fi
done

# ---- 3. macros the source branches on ---------------------------------
echo
echo "== socket-option / feature macros =="
probe_macro() {   # $1 = header, $2 = macro
  printf '#include <%s>\n#ifdef %s\nyes_it_is_there\n#endif\n' "$1" "$2" > m.c
  if $CC -std=gnu99 -E m.c 2>/dev/null | grep -q yes_it_is_there; then pass "$2" present; else pass "$2" ABSENT; fi
}
probe_macro netinet/tcp.h TCP_CONGESTION
probe_macro netinet/tcp.h TCP_INFO
probe_macro netinet/tcp.h TCP_NODELAY
probe_macro netinet/tcp.h TCP_MAXSEG
probe_macro sys/socket.h  SO_MAX_PACING_RATE
probe_macro linux/in6.h   IPV6_FLOWLABEL_MGR
probe_macro netinet/in.h  IPV6_V6ONLY
probe_macro sys/socket.h  MSG_DONTWAIT

# ---- 4. struct tcp_info and the members iperf reads -------------------
echo
echo "== struct tcp_info members =="
for m in tcpi_snd_cwnd tcpi_snd_mss tcpi_rtt tcpi_rttvar tcpi_total_retrans tcpi_retransmits tcpi_unacked tcpi_sacked tcpi_lost tcpi_fackets; do
  printf '#include <netinet/tcp.h>\n#include <stdio.h>\nint main(void){struct tcp_info t; return (int)sizeof(t.%s);}\n' "$m" > t.c
  if $CC -std=gnu99 -c t.c -o t.o 2>/dev/null; then pass "$m" present; else pass "$m" ABSENT; fi
done

# ---- 5. libc.a symbol census -----------------------------------------
echo
echo "== libc.a / libm.a symbols (T or W = defined) =="
LIBC=$TC/mips-linux/lib/libc.a
LIBM=$TC/mips-linux/lib/libm.a
ls -la $LIBC $LIBM 2>&1 | sed 's/^/    /'
SYMS=$($NM --defined-only $LIBC 2>/dev/null | awk '{print $3}' | sort -u)
MSYMS=$($NM --defined-only $LIBM 2>/dev/null | awk '{print $3}' | sort -u)
for s in socket connect bind listen accept setsockopt getsockopt shutdown \
         getaddrinfo freeaddrinfo gai_strerror getnameinfo inet_ntop inet_pton \
         select poll sigaction signal nanosleep gettimeofday clock_gettime \
         getopt_long getopt_long_only setvbuf fdopen fileno snprintf vsnprintf \
         vfprintf strtod strtoll atoll sendfile sched_setaffinity \
         cpuset_setaffinity getline strsep strdup; do
  if echo "$SYMS" | grep -qx "$s"; then pass "libc:$s" present
  elif echo "$MSYMS" | grep -qx "$s"; then pass "libm:$s" present
  else pass "$s" ABSENT; fi
done
for s in sqrt floor; do
  if echo "$MSYMS" | grep -qx "$s"; then pass "libm:$s" present
  elif echo "$SYMS" | grep -qx "$s"; then pass "libc:$s" present
  else pass "$s" ABSENT; fi
done

# ---- 6. %qd / quad printf support (HAVE_PRINTF_QD / HAVE_QUAD_SUPPORT)
echo
echo "== printf quad =="
grep -nE '__UCLIBC_HAS_(LONG_LONG|FLOATS|WCHAR)__|LONG_LONG' $SYSINC/bits/uClibc_config.h 2>/dev/null | head -8 | sed 's/^/    /'
echo "  (HAVE_QUAD_SUPPORT/HAVE_PRINTF_QD are iperf's own; see where they are used)"
