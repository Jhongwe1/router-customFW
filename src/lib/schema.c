/* schema.c -- SPEC-R7 § 4's table and the per-field rules.  See schema.h for
 * what min/max mean per type and why the IPv4 rules are a switch.
 */

#include <string.h>

#include "schema.h"
#include "tlv.h"

/* Ids strictly ascending: schema_self_check refuses a table that is not, and
 * cfg_encode_record walks this array in order, which is where "ascending on
 * the wire" comes from. */
const struct cfg_key cfg_keys[CFG_NKEYS] = {
	{ CFG_ID_HOSTNAME,    "sys.hostname",  CT_STR,   WEB_RW,     1, CFG_HOSTNAME_MAX },
	{ CFG_ID_LAN_IP,      "lan.ipaddr",    CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_LAN_MASK,    "lan.netmask",   CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_DHCPD_EN,    "dhcpd.enable",  CT_BOOL,  WEB_RW,     0, 1 },
	{ CFG_ID_DHCPD_START, "dhcpd.start",   CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_DHCPD_END,   "dhcpd.end",     CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_DHCPD_LEASE, "dhcpd.lease",   CT_U32,   WEB_RW,   120, 604800 },
	{ CFG_ID_DNS_UP,      "dns.upstream",  CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_WAN_MODE,    "wan.mode",      CT_ENUM,  WEB_RW,     0, CFG_WAN_MODE_MAX },
	{ CFG_ID_WAN_IP,      "wan.ipaddr",    CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_WAN_MASK,    "wan.netmask",   CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_WAN_GW,      "wan.gateway",   CT_IPV4,  WEB_RW,     0, 0 },
	{ CFG_ID_FW_NAT,      "fw.nat",        CT_BOOL,  WEB_RW,     0, 1 },
	{ CFG_ID_FW_LAN_ICMP, "fw.lan_icmp",   CT_BOOL,  WEB_RW,     0, 1 },
	{ CFG_ID_HTTP_PORT,   "http.port",     CT_U16,   WEB_R,      1, 65535 },
	{ CFG_ID_PWHASH,      "admin.pwhash",  CT_BYTES, WEB_HIDDEN, CFG_PWHASH_LEN,
								      CFG_PWHASH_LEN }
};

/* ------------------------------------------------------------------------- */
/* Table lookup.  Moved here from cfg.c by `R7-8` so that a caller needing the
 * table can link schema.c + tlv.c and nothing else; see schema.h.            */
/* ------------------------------------------------------------------------- */

const struct cfg_key *cfg_key_by_id(uint16_t id)
{
	int i;

	for (i = 0; i < CFG_NKEYS; i++) {
		if (cfg_keys[i].id == id)
			return &cfg_keys[i];
	}
	return NULL;
}

const struct cfg_key *cfg_key_by_name(const char *name)
{
	int i;

	if (name == NULL)
		return NULL;
	for (i = 0; i < CFG_NKEYS; i++) {
		if (strcmp(cfg_keys[i].name, name) == 0)
			return &cfg_keys[i];
	}
	return NULL;
}

const struct cfg_key *cfg_key_at(unsigned i)
{
	if (i >= (unsigned)CFG_NKEYS)
		return NULL;
	return &cfg_keys[i];
}

/* ------------------------------------------------------------------------- */
/* Defaults.  `admin.pwhash` is absent from this table on purpose: it is the
 * key with no default, and that absence is the fail-closed property (cfg.h).  */
/* ------------------------------------------------------------------------- */

struct schema_def {
	uint16_t id;
	uint16_t len;
	uint8_t v[CFG_VAL_MAX];
};

#define IP4(a, b, c, d) { (a), (b), (c), (d) }

static const struct schema_def schema_defs[] = {
	{ CFG_ID_HOSTNAME,    5, { 'r', 'l', 'x', 'f', 'w' } },
	{ CFG_ID_LAN_IP,      4, IP4(10, 1, 1, 1) },
	{ CFG_ID_LAN_MASK,    4, IP4(255, 255, 255, 0) },
	{ CFG_ID_DHCPD_EN,    1, { 1 } },
	{ CFG_ID_DHCPD_START, 4, IP4(10, 1, 1, 100) },
	{ CFG_ID_DHCPD_END,   4, IP4(10, 1, 1, 199) },
	{ CFG_ID_DHCPD_LEASE, 4, { 0x00, 0x01, 0x51, 0x80 } },	/* 86400 */
	{ CFG_ID_DNS_UP,      4, IP4(10, 1, 1, 2) },
	{ CFG_ID_WAN_MODE,    1, { 0 } },
	{ CFG_ID_WAN_IP,      4, IP4(0, 0, 0, 0) },
	{ CFG_ID_WAN_MASK,    4, IP4(0, 0, 0, 0) },
	{ CFG_ID_WAN_GW,      4, IP4(0, 0, 0, 0) },
	{ CFG_ID_FW_NAT,      1, { 0 } },
	{ CFG_ID_FW_LAN_ICMP, 1, { 1 } },
	{ CFG_ID_HTTP_PORT,   2, { 0x00, 0x50 } }		/* 80 */
};

#define SCHEMA_NDEFS ((int)(sizeof schema_defs / sizeof schema_defs[0]))

int schema_default(uint16_t id, const uint8_t **v, uint16_t *len)
{
	int i;

	if (cfg_key_by_id(id) == NULL)
		return -CFGE_UNKNOWN;
	for (i = 0; i < SCHEMA_NDEFS; i++) {
		if (schema_defs[i].id == id) {
			if (v != NULL)
				*v = schema_defs[i].v;
			if (len != NULL)
				*len = schema_defs[i].len;
			return 0;
		}
	}
	return -CFGE_NOENT;
}

/* ------------------------------------------------------------------------- */
/* IPv4 predicates                                                           */
/* ------------------------------------------------------------------------- */

/* "unicast" here means: usable as an interface or peer address on this device.
 * 0.0.0.0, 127/8 (loopback), 224/4 and above (multicast and the reserved
 * classes, which takes 255.255.255.255 with it) are refused.  It does NOT
 * refuse the host-part-all-zeros or all-ones addresses -- those are only
 * meaningful against a netmask, so they are cross-field rules (cfg.c). */
int schema_ipv4_is_unicast(uint32_t a)
{
	uint32_t top = (a >> 24) & 0xFFu;

	if (a == 0)
		return 0;
	if (top == 0 || top == 127 || top >= 224)
		return 0;
	return 1;
}

int schema_mask_is_contiguous(uint32_t m)
{
	/* A contiguous high-run mask is exactly one for which ~m + 1 is a power
	 * of two (or m is all ones).  Written with the complement so that no
	 * loop can be the thing that is wrong. */
	uint32_t inv = ~m;

	if (inv == 0)
		return 1;			/* /32 */
	return (inv & (inv + 1u)) == 0;
}

int schema_mask_prefix_len(uint32_t m)
{
	int n = 0;

	if (!schema_mask_is_contiguous(m))
		return -1;
	while (m & 0x80000000u) {
		n++;
		m <<= 1;
	}
	return n;
}

/* ------------------------------------------------------------------------- */
/* Field rules                                                               */
/* ------------------------------------------------------------------------- */

static int hostname_ok(const uint8_t *v, uint16_t len)
{
	uint16_t i;

	if (len < 1)
		return 0;
	if (v[0] == '-' || v[len - 1] == '-')
		return 0;
	for (i = 0; i < len; i++) {
		uint8_t c = v[i];

		if (c >= 'A' && c <= 'Z')
			continue;
		if (c >= 'a' && c <= 'z')
			continue;
		if (c >= '0' && c <= '9')
			continue;
		if (c == '-')
			continue;
		return 0;		/* NUL included: it is not in the charset */
	}
	return 1;
}

int schema_check_value(const struct cfg_key *k, const uint8_t *v, uint16_t len)
{
	uint32_t n;

	if (k == NULL || (v == NULL && len != 0))
		return -CFGE_TYPE;
	if ((size_t)len > (size_t)CFG_VAL_MAX)
		return -CFGE_TYPE;

	switch (k->type) {
	case CT_BOOL:
	case CT_ENUM:
		if (len != 1)
			return -CFGE_TYPE;
		if ((uint32_t)v[0] < k->min || (uint32_t)v[0] > k->max)
			return -CFGE_RANGE;
		return 0;

	case CT_U16:
		if (len != 2)
			return -CFGE_TYPE;
		n = (uint32_t)tlv_get_be16(v);
		if (n < k->min || n > k->max)
			return -CFGE_RANGE;
		return 0;

	case CT_U32:
		if (len != 4)
			return -CFGE_TYPE;
		n = tlv_get_be32(v);
		if (n < k->min || n > k->max)
			return -CFGE_RANGE;
		return 0;

	case CT_STR:
		if ((uint32_t)len < k->min || (uint32_t)len > k->max)
			return -CFGE_TYPE;
		if (k->id == CFG_ID_HOSTNAME) {
			if (!hostname_ok(v, len))
				return -CFGE_RANGE;
			return 0;
		}
		/* No other STR row exists yet.  A new one without a charset
		 * rule must not silently accept NUL. */
		if (memchr(v, 0, (size_t)len) != NULL)
			return -CFGE_RANGE;
		return 0;

	case CT_BYTES:
		if ((uint32_t)len < k->min || (uint32_t)len > k->max)
			return -CFGE_TYPE;
		return 0;

	case CT_IPV4:
		if (len != 4)
			return -CFGE_TYPE;
		n = tlv_get_be32(v);
		switch (k->id) {
		case CFG_ID_LAN_IP:
		case CFG_ID_DNS_UP:
			if (!schema_ipv4_is_unicast(n))
				return -CFGE_RANGE;
			return 0;
		case CFG_ID_LAN_MASK: {
			int p = schema_mask_prefix_len(n);

			if (p < 8 || p > 30)
				return -CFGE_RANGE;
			return 0;
		}
		case CFG_ID_WAN_MASK:
			if (n != 0 && !schema_mask_is_contiguous(n))
				return -CFGE_RANGE;
			return 0;
		case CFG_ID_DHCPD_START:
		case CFG_ID_DHCPD_END:
		case CFG_ID_WAN_IP:
		case CFG_ID_WAN_GW:
			/* § 4's bounds column is empty for these four: what
			 * constrains them is the cross-field rules. */
			return 0;
		default:
			return -CFGE_UNKNOWN;
		}

	default:
		return -CFGE_TYPE;
	}
}

/* ------------------------------------------------------------------------- */

int schema_self_check(void)
{
	int i, j;

	if ((int)(sizeof cfg_keys / sizeof cfg_keys[0]) != CFG_NKEYS)
		return -CFGE_UNKNOWN;

	for (i = 0; i < CFG_NKEYS; i++) {
		const struct cfg_key *k = &cfg_keys[i];
		const uint8_t *dv;
		uint16_t dl;
		int rc;

		if (i > 0 && !(cfg_keys[i - 1].id < k->id))
			return -CFGE_ORDER;
		if (k->name == NULL || k->name[0] == '\0')
			return -CFGE_NAME;
		if (strlen(k->name) >= 32)
			return -CFGE_NAME;
		if (k->type < CT_BOOL || k->type > CT_BYTES)
			return -CFGE_TYPE;
		if (k->web != WEB_HIDDEN && k->web != WEB_R && k->web != WEB_RW)
			return -CFGE_TYPE;
		if (k->min > k->max)
			return -CFGE_RANGE;
		for (j = 0; j < i; j++) {
			if (strcmp(cfg_keys[j].name, k->name) == 0)
				return -CFGE_NAME;
		}
		/* Every fixed-length type must fit the value array. */
		switch (k->type) {
		case CT_STR:
		case CT_BYTES:
			if (k->max > (uint32_t)CFG_VAL_MAX)
				return -CFGE_SPACE;
			break;
		default:
			break;
		}
		rc = schema_default(k->id, &dv, &dl);
		if (rc == 0) {
			rc = schema_check_value(k, dv, dl);
			if (rc != 0)
				return rc;
		} else if (rc != -CFGE_NOENT) {
			return rc;
		}
	}

	/* Every default row names a key that exists, and no row is duplicated. */
	for (i = 0; i < SCHEMA_NDEFS; i++) {
		if (cfg_key_by_id(schema_defs[i].id) == NULL)
			return -CFGE_UNKNOWN;
		if (schema_defs[i].len > (uint16_t)CFG_VAL_MAX)
			return -CFGE_SPACE;
		for (j = 0; j < i; j++) {
			if (schema_defs[j].id == schema_defs[i].id)
				return -CFGE_UNKNOWN;
		}
	}
	/* Exactly one key without a default, and it is the hidden one. */
	if (SCHEMA_NDEFS != CFG_NKEYS - 1)
		return -CFGE_NOENT;
	if (schema_default(CFG_ID_PWHASH, NULL, NULL) != -CFGE_NOENT)
		return -CFGE_NOENT;
	if (cfg_key_by_id(CFG_ID_PWHASH)->web != WEB_HIDDEN)
		return -CFGE_PERM;

	return 0;
}
