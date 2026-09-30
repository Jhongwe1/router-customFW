/* test_netutil.c -- R7 host test for src/lib/netutil.c.
 *
 * Every refusal is asserted BY ITS CODE and not merely as "refused": a parser
 * that rejects "1.2.3" for the wrong reason is a parser whose next change will
 * accept it.  The netmask contiguity case (`255.0.255.0`) is the subject of
 * mutation control M2 in notes/init.md 6.
 */

#include "../lib/netutil.h"

#include <stdio.h>
#include <string.h>

static int checks, fails;

#define CK(cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
	} \
} while (0)

/* Assert that `s` parses to `want`. */
static void ok_quad(const char *s, uint32_t want)
{
	uint32_t got = 0xDEADBEEFu;
	int rc = nu_parse_ipv4(s, &got);

	checks++;
	if (rc != 0 || got != want) {
		fails++;
		printf("FAIL parse ok: \"%s\" rc=%d (%s) got=%08lx want=%08lx\n",
		       s, rc, nu_strerror(rc), (unsigned long)got,
		       (unsigned long)want);
	}
}

/* Assert that `s` is refused with exactly `code`. */
static void no_quad(const char *s, int code)
{
	uint32_t got = 0xDEADBEEFu;
	int rc = nu_parse_ipv4(s, &got);

	checks++;
	if (rc != -code) {
		fails++;
		printf("FAIL parse refuse: \"%s\" rc=%d (%s) want=%d (%s)\n",
		       s, rc, nu_strerror(rc), -code, nu_strerror(code));
	}
}

static void t_parse_accept(void)
{
	ok_quad("0.0.0.0", 0x00000000u);
	ok_quad("1.2.3.4", 0x01020304u);
	ok_quad("10.1.1.1", 0x0A010101u);
	ok_quad("192.168.0.100", 0xC0A80064u);
	ok_quad("255.255.255.255", 0xFFFFFFFFu);
	ok_quad("255.255.255.0", 0xFFFFFF00u);
	ok_quad("8.8.4.4", 0x08080404u);
	/* A single zero octet is legal; only a zero with a digit after it is
	 * not.  This is the pair that makes NU_E_LEADZERO a real rule. */
	ok_quad("10.0.0.1", 0x0A000001u);
	ok_quad("0.0.0.1", 0x00000001u);
}

static void t_parse_refuse(void)
{
	char digits[65];
	char withnul[8];

	no_quad("1.2.3", NU_E_FIELDS);
	no_quad("1.2.3.4.5", NU_E_FIELDS);
	no_quad("256.1.1.1", NU_E_RANGE);
	no_quad("01.2.3.4", NU_E_LEADZERO);
	no_quad("1.2.3.04", NU_E_LEADZERO);
	no_quad("1.2.3.4 ", NU_E_CHAR);
	no_quad(" 1.2.3.4", NU_E_CHAR);
	no_quad("+1.2.3.4", NU_E_CHAR);
	no_quad("-1.2.3.4", NU_E_CHAR);
	no_quad("", NU_E_EMPTY);
	no_quad("1.2.3.4a", NU_E_CHAR);
	no_quad("1.2.3.4\n", NU_E_CHAR);
	no_quad("1.2.3.4\t", NU_E_CHAR);
	no_quad("0x7f.0.0.1", NU_E_CHAR);
	no_quad("1..2.3", NU_E_DOT);
	no_quad(".1.2.3.4", NU_E_DOT);
	no_quad("1.2.3.", NU_E_FIELDS);
	no_quad("1234.1.1.1", NU_E_OCTLEN);
	no_quad("1.2.3.1234", NU_E_OCTLEN);
	no_quad("999.999.999.999", NU_E_RANGE);
	no_quad("1.2.3.4;reboot", NU_E_CHAR);
	no_quad("$(reboot)", NU_E_CHAR);
	no_quad("1.2.3.256", NU_E_RANGE);

	/* 64 bytes of digits: refused on length, before a digit is looked at. */
	memset(digits, '9', sizeof(digits) - 1);
	digits[sizeof(digits) - 1] = '\0';
	no_quad(digits, NU_E_LONG);
	CK(strlen(digits) == 64);

	/* An embedded NUL, both ways.  Through the counted parser it is a bad
	 * character inside the field; through the NUL-terminated one it simply
	 * shortens the string, and what is left is not four octets. */
	memcpy(withnul, "1.2\0" ".3.4", 8);
	CK(nu_parse_ipv4_n(withnul, 8, NULL) == -NU_E_EMPTY);
	{
		uint32_t v;

		CK(nu_parse_ipv4_n(withnul, 8, &v) == -NU_E_CHAR);
		CK(nu_parse_ipv4(withnul, &v) == -NU_E_FIELDS);
	}
	/* The counted parser never reads past n: "1.2.3.4X" with n = 7. */
	{
		uint32_t v = 0;

		CK(nu_parse_ipv4_n("1.2.3.4X", 7, &v) == 0);
		CK(v == 0x01020304u);
	}
	/* NULL and zero length. */
	{
		uint32_t v;

		CK(nu_parse_ipv4(NULL, &v) == -NU_E_EMPTY);
		CK(nu_parse_ipv4_n("", 0, &v) == -NU_E_EMPTY);
		CK(nu_parse_ipv4_n("1.2.3.4", 7, NULL) == -NU_E_EMPTY);
	}
}

static void t_format(void)
{
	char b[NU_QUAD_BUF];

	CK(nu_format_ipv4(0u, b, sizeof(b)) == 7);
	CK(strcmp(b, "0.0.0.0") == 0);
	CK(nu_format_ipv4(0xFFFFFFFFu, b, sizeof(b)) == 15);
	CK(strcmp(b, "255.255.255.255") == 0);
	CK(nu_format_ipv4(0x0A010101u, b, sizeof(b)) == 8);
	CK(strcmp(b, "10.1.1.1") == 0);
	/* One byte short of the NUL is a refusal, not a truncation. */
	CK(nu_format_ipv4(0xFFFFFFFFu, b, 15) == -NU_E_SPACE);
	CK(nu_format_ipv4(0u, b, 0) == -NU_E_SPACE);
	CK(nu_format_ipv4(0u, NULL, 8) == -NU_E_SPACE);
}

static void t_roundtrip(void)
{
	/* A deterministic sweep: 20,000 values through format and back.  The
	 * generator is a plain LCG so the population is the same on both
	 * compilers and on both endiannesses. */
	uint32_t x = 0x12345678u;
	int i, bad = 0;

	for (i = 0; i < 20000; i++) {
		char b[NU_QUAD_BUF];
		uint32_t back = 0;

		x = x * 1103515245u + 12345u;
		if (nu_format_ipv4(x, b, sizeof(b)) < 0 ||
		    nu_parse_ipv4(b, &back) != 0 || back != x)
			bad++;
	}
	CK(bad == 0);
	/* And every prefix mask, which is the population that matters. */
	for (i = 0; i <= 32; i++) {
		uint32_t m = i == 0 ? 0u : (0xFFFFFFFFu << (32 - i));
		char b[NU_QUAD_BUF];
		uint32_t back = 0;

		CK(nu_format_ipv4(m, b, sizeof(b)) > 0);
		CK(nu_parse_ipv4(b, &back) == 0);
		CK(back == m);
		CK(nu_mask_prefix(m) == i);
	}
}

static void t_mask(void)
{
	int p;

	/* Contiguity.  M2's mutation removes the check that makes these red. */
	CK(nu_mask_prefix(0x00FF00FFu) == -NU_E_MASK);   /* 0.255.0.255 */
	CK(nu_mask_prefix(0xFF00FF00u) == -NU_E_MASK);   /* 255.0.255.0 */
	CK(nu_mask_prefix(0x00FFFFFFu) == -NU_E_MASK);   /* 0.255.255.255 */
	CK(nu_mask_prefix(0xFFFFFF01u) == -NU_E_MASK);   /* 255.255.255.1 */
	CK(nu_mask_prefix(0x00000001u) == -NU_E_MASK);
	CK(nu_mask_prefix(0xFFFEFFFFu) == -NU_E_MASK);

	CK(nu_mask_prefix(0u) == 0);
	CK(nu_mask_prefix(0xFFFFFFFFu) == 32);
	CK(nu_mask_prefix(0xFFFFFFFEu) == 31);
	CK(nu_mask_prefix(0xFFFFFF00u) == 24);
	CK(nu_mask_prefix(0xFF000000u) == 8);

	/* nu_mask_ok(m, 8, 30): the schema's LAN rule.  /8../30 accepted, and
	 * /0../7 and /31,/32 refused as PREFIX -- a different code from MASK,
	 * so a test cannot confuse "not contiguous" with "out of range". */
	for (p = 8; p <= 30; p++) {
		uint32_t m = 0xFFFFFFFFu << (32 - p);

		CK(nu_mask_ok(m, 8, 30) == 0);
	}
	CK(nu_mask_ok(0u, 8, 30) == -NU_E_PREFIX);
	CK(nu_mask_ok(0xFE000000u, 8, 30) == -NU_E_PREFIX);         /* /7 */
	CK(nu_mask_ok(0xFFFFFFFEu, 8, 30) == -NU_E_PREFIX);         /* /31 */
	CK(nu_mask_ok(0xFFFFFFFFu, 8, 30) == -NU_E_PREFIX);         /* /32 */
	CK(nu_mask_ok(0xFF00FF00u, 8, 30) == -NU_E_MASK);
	/* A contiguous mask inside the range is not made legal by the range. */
	CK(nu_mask_ok(0xFF00FF00u, 0, 32) == -NU_E_MASK);
}

static void t_addr_class(void)
{
	CK(nu_is_unicast(0x0A010101u) == 1);
	CK(nu_is_unicast(0xC0A80001u) == 1);
	CK(nu_is_unicast(0u) == 0);
	CK(nu_is_unicast(0xFFFFFFFFu) == 0);
	CK(nu_is_unicast(0x7F000001u) == 0);           /* 127.0.0.1 */
	CK(nu_is_unicast(0x7FFFFFFFu) == 0);
	CK(nu_is_unicast(0xE0000001u) == 0);           /* 224.0.0.1 */
	CK(nu_is_unicast(0xEFFFFFFFu) == 0);
	CK(nu_is_unicast(0xF0000001u) == 0);           /* class E */
	CK(nu_is_unicast(0xDFFFFFFFu) == 1);           /* 223.x is still unicast */

	CK(nu_is_net_or_bcast(0xC0A80100u, 0xFFFFFF00u) == 1);   /* .0 */
	CK(nu_is_net_or_bcast(0xC0A801FFu, 0xFFFFFF00u) == 1);   /* .255 */
	CK(nu_is_net_or_bcast(0xC0A80101u, 0xFFFFFF00u) == 0);
	CK(nu_is_net_or_bcast(0x0A000001u, 0xFFFFFFFCu) == 0);   /* /30 host */
	CK(nu_is_net_or_bcast(0x0A000000u, 0xFFFFFFFCu) == 1);
	CK(nu_is_net_or_bcast(0x0A000003u, 0xFFFFFFFCu) == 1);
	CK(nu_is_net_or_bcast(0x0A000001u, 0xFFFFFFFFu) == 0);   /* /32 */
}

static void t_ifname(void)
{
	CK(nu_ifname_ok("rlx0") == 0);
	CK(nu_ifname_ok("eth4") == 0);
	CK(nu_ifname_ok("br-lan.100") == 0);
	CK(nu_ifname_ok("a") == 0);
	CK(nu_ifname_ok("123456789012345") == 0);        /* exactly 15 */
	CK(nu_ifname_ok("1234567890123456") == -NU_E_IFNAME);  /* 16 */
	CK(nu_ifname_ok("") == -NU_E_IFNAME);
	CK(nu_ifname_ok(NULL) == -NU_E_IFNAME);
	CK(nu_ifname_ok("eth0;reboot") == -NU_E_IFNAME);
	CK(nu_ifname_ok("eth0 up") == -NU_E_IFNAME);
	CK(nu_ifname_ok("../../dev/mtd0") == -NU_E_IFNAME);
	CK(nu_ifname_ok("$(id)") == -NU_E_IFNAME);
	CK(nu_ifname_ok("eth0\n") == -NU_E_IFNAME);
}

static void t_strerror(void)
{
	int e;

	/* Every code has a token, in both signs, and none is NULL or empty:
	 * these strings go on a console and into the test expectations. */
	for (e = 0; e < NU_E_MAX; e++) {
		CK(nu_strerror(e) != NULL && nu_strerror(e)[0] != '\0');
		CK(nu_strerror(-e) == nu_strerror(e));
	}
	CK(strcmp(nu_strerror(NU_E_MAX), "unknown") == 0);
	CK(strcmp(nu_strerror(-99999), "unknown") == 0);
	CK(strcmp(nu_strerror(0), "ok") == 0);
}

int main(void)
{
	t_parse_accept();
	t_parse_refuse();
	t_format();
	t_roundtrip();
	t_mask();
	t_addr_class();
	t_ifname();
	t_strerror();
	printf("test_netutil: %d checks, %d failures\n", checks, fails);
	return fails == 0 ? 0 : 1;
}
