/* iperf_config.h -- hand written for the RTL8196E cross build.
 *
 * This replaces the file ./configure would have generated.  Every #define
 * below, and every deliberate omission, is a MEASUREMENT taken against this
 * exact toolchain -- rsdk-1.3.6-4181-EB (gcc 3.4.6, uClibc 0.9.30, Linux
 * 2.6.30 headers, LINUX_VERSION_CODE 132638) -- by config/rlxfw-user/iperf3/probe.sh, which
 * compiles a probe per header/macro/struct-member and greps libc.a's symbol
 * table for each function.  Nothing here is inherited from a host configure
 * run and nothing here is assumed.
 */

#ifndef IPERF_CONFIG_H
#define IPERF_CONFIG_H

/* ---- identity.  configure would take these from AC_INIT. --------------- */
#define PACKAGE_NAME      "iperf"
#define PACKAGE_TARNAME   "iperf"
#define PACKAGE_VERSION   "3.1.3"
#define PACKAGE_STRING    "iperf 3.1.3"
#define PACKAGE_BUGREPORT "https://github.com/esnet/iperf"
#define PACKAGE_URL       "http://software.es.net/iperf/"
#define VERSION           "3.1.3"

/* ---- measured PRESENT ------------------------------------------------- */
#define HAVE_STDINT_H          1  /* probe: #include <stdint.h> + uint64_t compiles */
#define HAVE_SYS_SOCKET_H      1  /* probe: header compiles */
#define HAVE_TCP_CONGESTION    1  /* probe: TCP_CONGESTION defined in <netinet/tcp.h> */
#define HAVE_SENDFILE          1  /* probe: `sendfile' defined in libc.a */
#define HAVE_SCHED_SETAFFINITY 1  /* probe: `sched_setaffinity' defined in libc.a */
#define HAVE_CPU_AFFINITY      1  /* implied by the line above, as configure.ac does */

/* %lld, not %qd.  HAVE_QUAD_SUPPORT selects 64-bit CSV formats;
 * HAVE_PRINTF_QD would select the BSD %qd spelling, which this libc's
 * printf does not document.  Left undefined on purpose so the %lld arm is
 * taken -- and `long long' printf is verified by RUNNING a probe under
 * qemu-mips-static rather than by reading a header. */
#define HAVE_QUAD_SUPPORT      1

/* ---- measured ABSENT: deliberately NOT defined -------------------------
 *   HAVE_NETINET_SCTP_H        <netinet/sctp.h> does not exist in this sysroot
 *   HAVE_SCTP                  ditto -- iperf_sctp.c compiles to stubs
 *   HAVE_STRUCT_SCTP_ASSOC_VALUE   ditto
 *   HAVE_SO_MAX_PACING_RATE    SO_MAX_PACING_RATE is not in <sys/socket.h>
 *                              (it is a 3.13-era sockopt; this is 2.6.30)
 *   HAVE_CPUSET_SETAFFINITY    FreeBSD spelling; absent from libc.a
 *   HAVE_PRINTF_QD             see above
 *   HAVE_FLOWLABEL             IPV6_FLOWLABEL_MGR *is* present in
 *                              <linux/in6.h>, so this could be defined.  It is
 *                              left off: it is an IPv6-only convenience
 *                              (--flowlabel) on a device with no IPv6 use here,
 *                              and src/flowlabel.h re-declares kernel structs.
 *                              Turning it on is a one-line change and the
 *                              probe says the macro is there.
 */

#endif /* IPERF_CONFIG_H */
