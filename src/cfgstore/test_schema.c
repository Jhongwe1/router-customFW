/* test_schema.c -- SPEC-R7 § 4: every key, every type, at its boundaries, plus
 * one case per cross-field rule and the refusal that keeps the hash unprintable.
 *
 * ---------------------------------------------------------------------------
 * WHAT "BOUNDARY" MEANS PER TYPE
 * ---------------------------------------------------------------------------
 *
 * For BOOL, ENUM, U16 and U32 it is the interval: min, max, min-1, max+1.
 * For STR it is the LENGTH interval, so min-1 is the empty string and max+1 is
 * one character too many.  For BYTES it is the exact length, 55 and 57 bytes.
 * For IPV4 there is no interval -- the rule is a predicate -- so the boundary
 * cases are the predicate's edges: 0.0.0.0 and 255.255.255.255 either side of
 * unicast, 126/127 and 223/224 across the class edges, and /7 /8 /30 /31 /32
 * plus a non-contiguous mask across the netmask rule.
 *
 * Every accepted case is also round-tripped text -> value -> text and must come
 * back byte-identical.  That is what makes this a round-trip test and not just
 * a validator test: an encoder and a decoder that are wrong in the same
 * direction pass the second and fail the first.
 */

#include <stdint.h>
#include <string.h>

#include "cfg.h"
#include "schema.h"
#include "test_util.h"

struct vcase {
	uint16_t id;
	const char *text;
	int ok;			/* 1 accept, 0 reject */
	const char *why;
};

static const struct vcase cases[] = {
	/* CT_STR: sys.hostname, 1..32 of [A-Za-z0-9-], not leading/trailing - */
	{ CFG_ID_HOSTNAME, "r", 1, "min length" },
	{ CFG_ID_HOSTNAME, "rlxfw", 1, "the default" },
	{ CFG_ID_HOSTNAME, "abcdefghijabcdefghijabcdefghij12", 1, "max length 32" },
	{ CFG_ID_HOSTNAME, "", 0, "min-1: empty" },
	{ CFG_ID_HOSTNAME, "abcdefghijabcdefghijabcdefghij123", 0, "max+1: 33" },
	{ CFG_ID_HOSTNAME, "-rlx", 0, "leading hyphen" },
	{ CFG_ID_HOSTNAME, "rlx-", 0, "trailing hyphen" },
	{ CFG_ID_HOSTNAME, "r-l-x", 1, "interior hyphens" },
	{ CFG_ID_HOSTNAME, "rlx_fw", 0, "underscore is not in the charset" },
	{ CFG_ID_HOSTNAME, "rlx fw", 0, "space is not in the charset" },
	{ CFG_ID_HOSTNAME, "rlx.fw", 0, "dot is not in the charset" },

	/* CT_IPV4 unicast: lan.ipaddr, dns.upstream */
	{ CFG_ID_LAN_IP, "10.1.1.1", 1, "the default" },
	{ CFG_ID_LAN_IP, "1.0.0.1", 1, "lowest unicast top octet" },
	{ CFG_ID_LAN_IP, "223.255.255.254", 1, "highest unicast top octet" },
	{ CFG_ID_LAN_IP, "0.0.0.0", 0, "refused by name in § 4" },
	{ CFG_ID_LAN_IP, "0.1.1.1", 0, "top octet 0" },
	{ CFG_ID_LAN_IP, "127.0.0.1", 0, "loopback" },
	{ CFG_ID_LAN_IP, "126.0.0.1", 1, "126 is below loopback" },
	{ CFG_ID_LAN_IP, "224.0.0.1", 0, "multicast" },
	{ CFG_ID_LAN_IP, "255.255.255.255", 0, "broadcast" },
	{ CFG_ID_DNS_UP, "10.1.1.2", 1, "the default" },
	{ CFG_ID_DNS_UP, "0.0.0.0", 0, "not unicast" },

	/* text-format strictness, which is a rule about the PARSER */
	{ CFG_ID_LAN_IP, "010.1.1.1", 0, "a leading zero could be read as octal" },
	{ CFG_ID_LAN_IP, "10.1.1", 0, "three fields" },
	{ CFG_ID_LAN_IP, "10.1.1.1.1", 0, "five fields" },
	{ CFG_ID_LAN_IP, "10.1.1.1.", 0, "trailing dot" },
	{ CFG_ID_LAN_IP, "10.1.1.256", 0, "field over 255" },
	{ CFG_ID_LAN_IP, "10.1.1.1 ", 0, "trailing space" },
	{ CFG_ID_LAN_IP, " 10.1.1.1", 0, "leading space" },
	{ CFG_ID_LAN_IP, "0x0a.1.1.1", 0, "hex field" },
	{ CFG_ID_LAN_IP, "10..1.1", 0, "empty field" },
	{ CFG_ID_LAN_IP, "-10.1.1.1", 0, "signed field" },

	/* CT_IPV4 netmask: /8../30 contiguous */
	{ CFG_ID_LAN_MASK, "255.0.0.0", 1, "/8, the minimum" },
	{ CFG_ID_LAN_MASK, "254.0.0.0", 0, "/7, min-1" },
	{ CFG_ID_LAN_MASK, "255.255.255.252", 1, "/30, the maximum" },
	{ CFG_ID_LAN_MASK, "255.255.255.254", 0, "/31, max+1" },
	{ CFG_ID_LAN_MASK, "255.255.255.255", 0, "/32" },
	{ CFG_ID_LAN_MASK, "255.0.255.0", 0, "not contiguous" },
	{ CFG_ID_LAN_MASK, "0.0.0.0", 0, "/0" },
	{ CFG_ID_LAN_MASK, "255.255.255.0", 1, "/24, the default" },
	{ CFG_ID_WAN_MASK, "0.0.0.0", 1, "§ 4 allows 0 for the WAN mask" },
	{ CFG_ID_WAN_MASK, "255.255.0.0", 1, "contiguous" },
	{ CFG_ID_WAN_MASK, "255.0.255.0", 0, "not contiguous" },
	{ CFG_ID_WAN_MASK, "255.255.255.255", 1, "/32 is contiguous, and § 4 puts"
						 " no prefix bound on the WAN mask" },

	/* CT_IPV4 with an empty bounds column: the cross-field rules own these */
	{ CFG_ID_DHCPD_START, "10.1.1.100", 1, "the default" },
	{ CFG_ID_DHCPD_START, "0.0.0.0", 1, "no field rule in § 4" },
	{ CFG_ID_WAN_IP, "0.0.0.0", 1, "the default" },
	{ CFG_ID_WAN_GW, "0.0.0.0", 1, "the default" },

	/* CT_BOOL */
	{ CFG_ID_DHCPD_EN, "0", 1, "min" },
	{ CFG_ID_DHCPD_EN, "1", 1, "max" },
	{ CFG_ID_DHCPD_EN, "2", 0, "max+1" },
	{ CFG_ID_DHCPD_EN, "-1", 0, "min-1" },
	{ CFG_ID_DHCPD_EN, "255", 0, "far above" },
	{ CFG_ID_FW_NAT, "0", 1, "the default" },
	{ CFG_ID_FW_NAT, "2", 0, "max+1" },
	{ CFG_ID_FW_LAN_ICMP, "1", 1, "the default" },
	{ CFG_ID_FW_LAN_ICMP, "2", 0, "max+1" },

	/* CT_ENUM wan.mode 0..2 */
	{ CFG_ID_WAN_MODE, "0", 1, "off" },
	{ CFG_ID_WAN_MODE, "1", 1, "dhcp" },
	{ CFG_ID_WAN_MODE, "2", 1, "static" },
	{ CFG_ID_WAN_MODE, "3", 0, "max+1" },
	{ CFG_ID_WAN_MODE, "-1", 0, "min-1" },

	/* CT_U32 dhcpd.lease 120..604800 */
	{ CFG_ID_DHCPD_LEASE, "120", 1, "min" },
	{ CFG_ID_DHCPD_LEASE, "119", 0, "min-1" },
	{ CFG_ID_DHCPD_LEASE, "604800", 1, "max" },
	{ CFG_ID_DHCPD_LEASE, "604801", 0, "max+1" },
	{ CFG_ID_DHCPD_LEASE, "86400", 1, "the default" },
	{ CFG_ID_DHCPD_LEASE, "4294967295", 0, "u32 max" },
	{ CFG_ID_DHCPD_LEASE, "4294967296", 0, "over u32" },
	{ CFG_ID_DHCPD_LEASE, "007", 0, "leading zeros" },
	{ CFG_ID_DHCPD_LEASE, "+120", 0, "signed" },
	{ CFG_ID_DHCPD_LEASE, "120 ", 0, "trailing space" },
	{ CFG_ID_DHCPD_LEASE, "", 0, "empty" },
	{ CFG_ID_DHCPD_LEASE, "12a0", 0, "not a number" },

	/* CT_U16 http.port 1..65535 */
	{ CFG_ID_HTTP_PORT, "1", 1, "min" },
	{ CFG_ID_HTTP_PORT, "0", 0, "min-1" },
	{ CFG_ID_HTTP_PORT, "65535", 1, "max" },
	{ CFG_ID_HTTP_PORT, "65536", 0, "max+1" },
	{ CFG_ID_HTTP_PORT, "80", 1, "the default" },

	/* CT_BYTES admin.pwhash, exactly 56 bytes = 112 hex characters */
	{ CFG_ID_PWHASH,
	  "0108000800010000"
	  "000102030405060708090a0b0c0d0e0f"
	  "101112131415161718191a1b1c1d1e1f"
	  "202122232425262728292a2b2c2d2e2f", 1, "56 bytes" },
	{ CFG_ID_PWHASH,
	  "0108000800010000"
	  "000102030405060708090a0b0c0d0e0f"
	  "101112131415161718191a1b1c1d1e1f"
	  "202122232425262728292a2b2c2d2e", 0, "55 bytes, min-1" },
	{ CFG_ID_PWHASH,
	  "0108000800010000"
	  "000102030405060708090a0b0c0d0e0f"
	  "101112131415161718191a1b1c1d1e1f"
	  "202122232425262728292a2b2c2d2e2f30", 0, "57 bytes, max+1" },
	{ CFG_ID_PWHASH, "0g", 0, "not hex" },
	{ CFG_ID_PWHASH, "010", 0, "odd number of hex digits" }
};

#define NCASES ((int)(sizeof cases / sizeof cases[0]))

/* Builds a cfg whose LAN/DHCP values are the defaults, made explicit so that a
 * cross-field case can move exactly one of them. */
static void base_cfg(struct cfg *c)
{
	int i;

	cfg_defaults(c);
	for (i = 0; i < CFG_NKEYS; i++) {
		const uint8_t *dv;
		uint16_t dl;

		if (schema_default(cfg_keys[i].id, &dv, &dl) == 0)
			cfg_set(c, cfg_keys[i].id, dv, dl);
	}
}

static void set_ip(struct cfg *c, uint16_t id, const char *text)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;
	const struct cfg_key *k = cfg_key_by_id(id);
	int rc = cfg_text_to_value(k, text, v, &len);

	CHECK(rc == 0, "set_ip %s=%s refused by the field rules: %s", k->name,
	      text, cfg_strerror(rc));
	if (rc == 0)
		CHECK(cfg_set(c, id, v, len) == 0, "cfg_set %s", k->name);
}

/* A cross-field case: apply `text` to `id` on top of the defaults and require
 * cfg_validate to refuse, blaming `blame`. */
static void cross_bad(uint16_t id, const char *text, uint16_t blame,
		      const char *what)
{
	struct cfg c;
	int rc;

	base_cfg(&c);
	set_ip(&c, id, text);
	rc = cfg_validate(&c);
	CHECK(rc == -CFGE_CROSS, "%s: rc=%d (%s), want -CFGE_CROSS", what, rc,
	      cfg_strerror(rc));
	CHECK(cfg_last_key() == blame, "%s: blamed 0x%04X, want 0x%04X (%s)",
	      what, (unsigned)cfg_last_key(), (unsigned)blame,
	      cfg_key_by_id(blame)->name);
}

int main(void)
{
	struct cfg c;
	int i, rc;

	T_GROUP("self check");
	rc = schema_self_check();
	CHECK(rc == 0, "schema_self_check: %s", cfg_strerror(rc));
	CHECK(CFG_NKEYS == 16, "SPEC-R7 § 4 has 16 rows, CFG_NKEYS=%d", CFG_NKEYS);

	T_GROUP("lookup");
	for (i = 0; i < CFG_NKEYS; i++) {
		CHECK(cfg_key_by_id(cfg_keys[i].id) == &cfg_keys[i],
		      "by_id %s", cfg_keys[i].name);
		CHECK(cfg_key_by_name(cfg_keys[i].name) == &cfg_keys[i],
		      "by_name %s", cfg_keys[i].name);
		CHECK(cfg_index_by_id(cfg_keys[i].id) == i, "index %s",
		      cfg_keys[i].name);
	}
	CHECK(cfg_key_by_id(0x0002) == NULL, "0x0002 is not a key");
	CHECK(cfg_key_by_id(0xFFFF) == NULL, "0xFFFF is not a key");
	CHECK(cfg_key_by_name("nope") == NULL, "`nope' is not a key");
	CHECK(cfg_key_by_name("") == NULL, "the empty name is not a key");
	CHECK(cfg_key_by_name(NULL) == NULL, "NULL is not a key");

	T_GROUP("boundaries and round trip");
	for (i = 0; i < NCASES; i++) {
		const struct cfg_key *k = cfg_key_by_id(cases[i].id);
		uint8_t v[CFG_VAL_MAX];
		char back[CFG_TEXT_MAX];
		uint16_t len = 0;

		CHECK(k != NULL, "case %d names no key", i);
		if (k == NULL)
			continue;
		rc = cfg_text_to_value(k, cases[i].text, v, &len);
		if (cases[i].ok) {
			CHECK(rc == 0, "%s=`%s' (%s) refused: %s", k->name,
			      cases[i].text, cases[i].why, cfg_strerror(rc));
			if (rc != 0)
				continue;
			/* Round trip.  The hidden key cannot go through
			 * cfg_value_to_text by design, so it round-trips
			 * through the hex renderer instead. */
			if (k->web == WEB_HIDDEN) {
				CHECK(cfg_value_to_text(k, v, len, back,
						        sizeof back) ==
				      -CFGE_PERM,
				      "%s must refuse to render", k->name);
				CHECK(cfg_value_to_hex(v, len, back,
						       sizeof back) > 0,
				      "hex render of %s", k->name);
			} else {
				rc = cfg_value_to_text(k, v, len, back,
						       sizeof back);
				CHECK(rc > 0, "render %s: %s", k->name,
				      cfg_strerror(rc));
			}
			CHECK(strcmp(back, cases[i].text) == 0,
			      "%s round trip: `%s' -> `%s'", k->name,
			      cases[i].text, back);
			/* And the value itself must survive cfg_set/cfg_get. */
			base_cfg(&c);
			if (cfg_set(&c, k->id, v, len) == 0) {
				uint8_t g[CFG_VAL_MAX];
				uint16_t gl = 0;

				CHECK(cfg_get(&c, k->id, g, &gl) == 0,
				      "get %s", k->name);
				CHECK(gl == len && memcmp(g, v, len) == 0,
				      "%s: cfg_get did not return what cfg_set"
				      " took", k->name);
			}
		} else {
			CHECK(rc != 0, "%s=`%s' (%s) was ACCEPTED and must not"
			      " be", k->name, cases[i].text, cases[i].why);
		}
	}

	T_GROUP("wrong length for the type");
	{
		static const uint8_t z[8] = { 0 };
		int t;
		static const uint16_t fixed[] = {
			CFG_ID_DHCPD_EN, CFG_ID_WAN_MODE, CFG_ID_HTTP_PORT,
			CFG_ID_DHCPD_LEASE, CFG_ID_LAN_IP, CFG_ID_PWHASH
		};
		static const uint16_t want[] = { 1, 1, 2, 4, 4, 56 };

		for (t = 0; t < (int)(sizeof fixed / sizeof fixed[0]); t++) {
			const struct cfg_key *k = cfg_key_by_id(fixed[t]);
			uint16_t n;

			for (n = 0; n <= 8; n++) {
				rc = schema_check_value(k, z, n);
				if (n == want[t])
					continue;	/* value may still fail */
				CHECK(rc == -CFGE_TYPE,
				      "%s with len %u gave %s, want -CFGE_TYPE",
				      k->name, n, cfg_strerror(rc));
			}
		}
	}

	T_GROUP("hidden value cannot be rendered");
	{
		uint8_t v[CFG_PWHASH_LEN];
		char out[CFG_TEXT_MAX];

		memset(v, 0xA5, sizeof v);
		v[0] = 1;		/* alg = scrypt, SPEC-R7 § 4.2 */
		CHECK(cfg_value_to_text(cfg_key_by_id(CFG_ID_PWHASH), v,
					(uint16_t)sizeof v, out, sizeof out) ==
		      -CFGE_PERM,
		      "cfg_value_to_text must refuse a WEB_HIDDEN key");
		CHECK(cfg_key_by_id(CFG_ID_PWHASH)->web == WEB_HIDDEN,
		      "admin.pwhash must be WEB_HIDDEN");
		CHECK(cfg_key_by_id(CFG_ID_HTTP_PORT)->web == WEB_R,
		      "http.port is read-only over the web");
	}

	/* ------------------------------------------------------------------ */
	/* Cross-field: one case per rule in SPEC-R7 § 4, each blaming a key.  */
	/* ------------------------------------------------------------------ */

	T_GROUP("cross-field: the defaults pass");
	base_cfg(&c);
	rc = cfg_validate(&c);
	CHECK(rc == 0, "the shipped defaults must satisfy every rule: %s",
	      cfg_strerror(rc));
	cfg_defaults(&c);
	CHECK(cfg_validate(&c) == 0,
	      "an all-absent cfg validates through its defaults");

	T_GROUP("cross-field R1: start <= end");
	cross_bad(CFG_ID_DHCPD_START, "10.1.1.200", CFG_ID_DHCPD_START,
		  "start .200 > end .199");

	T_GROUP("cross-field R2: pool inside the LAN subnet");
	cross_bad(CFG_ID_DHCPD_START, "10.2.1.100", CFG_ID_DHCPD_START,
		  "start outside the subnet");
	cross_bad(CFG_ID_DHCPD_END, "10.2.1.199", CFG_ID_DHCPD_END,
		  "end outside the subnet");

	T_GROUP("cross-field R3: pool ends are not network/broadcast");
	cross_bad(CFG_ID_DHCPD_START, "10.1.1.0", CFG_ID_DHCPD_START,
		  "start is the network address");
	cross_bad(CFG_ID_DHCPD_END, "10.1.1.255", CFG_ID_DHCPD_END,
		  "end is the broadcast address");

	T_GROUP("cross-field R4: lan.ipaddr is a host address");
	{
		struct cfg d;

		/* .0 with a /24 is the network address; reachable only by
		 * moving the mask, since 10.1.1.0 also fails R5 otherwise. */
		base_cfg(&d);
		set_ip(&d, CFG_ID_LAN_MASK, "255.255.0.0");
		set_ip(&d, CFG_ID_LAN_IP, "10.1.0.0");
		rc = cfg_validate(&d);
		CHECK(rc == -CFGE_CROSS && cfg_last_key() == CFG_ID_LAN_IP,
		      "lan.ipaddr = the network address: rc=%d key=0x%04X", rc,
		      (unsigned)cfg_last_key());
		base_cfg(&d);
		set_ip(&d, CFG_ID_LAN_IP, "10.1.1.255");
		rc = cfg_validate(&d);
		CHECK(rc == -CFGE_CROSS && cfg_last_key() == CFG_ID_LAN_IP,
		      "lan.ipaddr = the broadcast address: rc=%d key=0x%04X", rc,
		      (unsigned)cfg_last_key());
	}

	T_GROUP("cross-field R5: lan.ipaddr outside the pool");
	cross_bad(CFG_ID_LAN_IP, "10.1.1.150", CFG_ID_LAN_IP,
		  "lan.ipaddr inside [start, end]");
	cross_bad(CFG_ID_LAN_IP, "10.1.1.100", CFG_ID_LAN_IP,
		  "lan.ipaddr = start");
	cross_bad(CFG_ID_LAN_IP, "10.1.1.199", CFG_ID_LAN_IP,
		  "lan.ipaddr = end");

	T_GROUP("cross-field R6: wan.mode = static");
	{
		struct cfg d;
		uint8_t one[1];

		base_cfg(&d);
		one[0] = 2;
		CHECK(cfg_set(&d, CFG_ID_WAN_MODE, one, 1) == 0, "wan.mode=2");
		rc = cfg_validate(&d);
		CHECK(rc == -CFGE_CROSS && cfg_last_key() == CFG_ID_WAN_IP,
		      "static with wan.ipaddr 0: rc=%d key=0x%04X", rc,
		      (unsigned)cfg_last_key());

		set_ip(&d, CFG_ID_WAN_IP, "192.0.2.10");
		rc = cfg_validate(&d);
		CHECK(rc == -CFGE_CROSS && cfg_last_key() == CFG_ID_WAN_MASK,
		      "static with wan.netmask 0: rc=%d key=0x%04X", rc,
		      (unsigned)cfg_last_key());

		set_ip(&d, CFG_ID_WAN_MASK, "255.255.255.0");
		rc = cfg_validate(&d);
		CHECK(rc == -CFGE_CROSS && cfg_last_key() == CFG_ID_WAN_GW,
		      "static with the gateway off-subnet: rc=%d key=0x%04X", rc,
		      (unsigned)cfg_last_key());

		set_ip(&d, CFG_ID_WAN_GW, "192.0.2.1");
		CHECK(cfg_validate(&d) == 0,
		      "a complete static WAN triple must pass");

		/* and mode 0/1 must not require any of it: the control that
		 * R6 is conditional rather than always-on. */
		base_cfg(&d);
		one[0] = 1;
		cfg_set(&d, CFG_ID_WAN_MODE, one, 1);
		CHECK(cfg_validate(&d) == 0, "dhcp needs no WAN triple");
		one[0] = 0;
		cfg_set(&d, CFG_ID_WAN_MODE, one, 1);
		CHECK(cfg_validate(&d) == 0, "off needs no WAN triple");
	}

	T_GROUP("fail-closed: admin.pwhash has no default");
	{
		uint8_t v[CFG_VAL_MAX];
		uint16_t len = 0;

		cfg_defaults(&c);
		CHECK(cfg_present(&c, CFG_ID_PWHASH) == 0,
		      "absent in a defaults-only cfg");
		CHECK(cfg_get(&c, CFG_ID_PWHASH, v, &len) == -CFGE_NOENT,
		      "cfg_get must report -CFGE_NOENT, never a zero hash");
		CHECK(schema_default(CFG_ID_PWHASH, NULL, NULL) == -CFGE_NOENT,
		      "and there must be no default row for it");
		/* every OTHER key has one */
		for (i = 0; i < CFG_NKEYS; i++) {
			if (cfg_keys[i].id == CFG_ID_PWHASH)
				continue;
			CHECK(cfg_get(&c, cfg_keys[i].id, v, &len) == 0,
			      "%s must have a default", cfg_keys[i].name);
		}
	}

	T_GROUP("mask helpers");
	CHECK(schema_mask_prefix_len(0xFFFFFF00u) == 24, "/24");
	CHECK(schema_mask_prefix_len(0x00000000u) == 0, "/0");
	CHECK(schema_mask_prefix_len(0xFFFFFFFFu) == 32, "/32");
	CHECK(schema_mask_prefix_len(0xFF00FF00u) == -1, "non-contiguous is -1");
	CHECK(schema_mask_is_contiguous(0xFFFFFFFEu) == 1, "/31 is contiguous");
	CHECK(schema_mask_is_contiguous(0x7FFFFFFFu) == 0, "0x7F.. is not");
	CHECK(schema_ipv4_is_unicast(0x0A010101u) == 1, "10.1.1.1");
	CHECK(schema_ipv4_is_unicast(0xE0000001u) == 0, "224.0.0.1");

	return t_done("schema");
}
