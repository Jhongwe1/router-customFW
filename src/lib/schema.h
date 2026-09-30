/* schema.h -- SPEC-R7 § 4's table, and the per-field rules that go with it.
 *
 * The table is the single source of ids, names, types, web visibility and
 * bounds.  `cfg.c` walks it in order for every encode, so "ids strictly
 * ascending" on the wire is a consequence of the table being sorted rather
 * than of an encoder remembering to sort; `schema_self_check` is what makes
 * that a checked claim instead of a hope.
 *
 * min/max carry the bound for the types where a bound is a number:
 *   CT_BOOL   0..1          the value
 *   CT_ENUM   0..n          the value
 *   CT_U16    the value     (1..65535 for http.port)
 *   CT_U32    the value     (120..604800 for dhcpd.lease)
 *   CT_STR    1..32         the LENGTH in bytes
 *   CT_BYTES  56..56        the LENGTH in bytes, exact
 *   CT_IPV4   0..0          unused: an IPv4 bound is not an interval, so the
 *                           rules (unicast; contiguous netmask; /8../30) are
 *                           per-id code in schema_check_value.
 * Overloading min/max was not a free choice -- `struct cfg_key` is pinned and
 * has no flags field -- and the per-id switch is where the IPv4 rules went
 * instead of into a wider struct.
 */
#ifndef RLXFW_SCHEMA_H
#define RLXFW_SCHEMA_H

#include "cfg.h"

#define CFG_ID_HOSTNAME    0x0001
#define CFG_ID_LAN_IP      0x0010
#define CFG_ID_LAN_MASK    0x0011
#define CFG_ID_DHCPD_EN    0x0020
#define CFG_ID_DHCPD_START 0x0021
#define CFG_ID_DHCPD_END   0x0022
#define CFG_ID_DHCPD_LEASE 0x0023
#define CFG_ID_DNS_UP      0x0030
#define CFG_ID_WAN_MODE    0x0040
#define CFG_ID_WAN_IP      0x0041
#define CFG_ID_WAN_MASK    0x0042
#define CFG_ID_WAN_GW      0x0043
#define CFG_ID_FW_NAT      0x0050
#define CFG_ID_FW_LAN_ICMP 0x0051
#define CFG_ID_HTTP_PORT   0x0060
#define CFG_ID_PWHASH      0x0070

/* The `CFGID_*` spellings, for the programs that were written against SPEC-R7
 * § 4 directly rather than against this header.  `R7-8` found the same sixteen
 * ids transcribed in FOUR places: here, src/httpd/stub/cfgtab.c, src/init/init.h
 * (nine of them) and src/brokerd/stub/cfg.h (four).  量 all four agreed, on every
 * id they carried.  They are aliases of the CFG_ID_* above, so the numbers are
 * still written exactly once. */
#define CFGID_SYS_HOSTNAME  CFG_ID_HOSTNAME
#define CFGID_LAN_IPADDR    CFG_ID_LAN_IP
#define CFGID_LAN_NETMASK   CFG_ID_LAN_MASK
#define CFGID_DHCPD_ENABLE  CFG_ID_DHCPD_EN
#define CFGID_DHCPD_START   CFG_ID_DHCPD_START
#define CFGID_DHCPD_END     CFG_ID_DHCPD_END
#define CFGID_DHCPD_LEASE   CFG_ID_DHCPD_LEASE
#define CFGID_DNS_UPSTREAM  CFG_ID_DNS_UP
#define CFGID_WAN_MODE      CFG_ID_WAN_MODE
#define CFGID_ADMIN_PWHASH  CFG_ID_PWHASH

#define CFG_HOSTNAME_MAX   32
#define CFG_PWHASH_LEN     56		/* SPEC-R7 § 4.2 */
#define CFG_WAN_MODE_MAX   2		/* 0 off, 1 dhcp, 2 static */

extern const struct cfg_key cfg_keys[CFG_NKEYS];

/* The three accessors a caller that wants the TABLE and nothing else needs.
 * They live here, beside the table, rather than in cfg.c: `R7-8` had two
 * transcriptions of § 4's rows (this one and src/httpd/stub/cfgtab.c, which is
 * gone) because httpd could not link cfg.c -- cfg.c is the store, and httpd
 * must not be able to reach a store function even by accident.  With these
 * three here, httpd links schema.c + tlv.c and the absence of cfg_load and
 * cfg_store from its link line is still the guard it was.
 *
 * cfg_key_by_id and cfg_key_by_name are declared in cfg.h because SPEC-R7 § 5
 * pins them there; only the index form is new. */
const struct cfg_key *cfg_key_at(unsigned i);	/* i < CFG_NKEYS, else NULL */

/* Field rules only: length for the type, then the id's own bounds.  0 or
 * -CFGE_TYPE / -CFGE_RANGE. */
int schema_check_value(const struct cfg_key *k, const uint8_t *v, uint16_t len);

/* The encoded default for an id.  0 with v and len set, or -CFGE_NOENT for a key
 * with no default (`admin.pwhash` is the only one), or -CFGE_UNKNOWN. */
int schema_default(uint16_t id, const uint8_t **v, uint16_t *len);

/* Asserts what the rest of the library assumes: CFG_NKEYS matches the table,
 * ids are strictly ascending, every name is unique and non-empty, every type
 * and web value is one of the enums, every default passes schema_check_value,
 * and every type's fixed length fits CFG_VAL_MAX.  0, or -CFGE_*.  Called by
 * every program at startup and by every test; a schema edited wrongly fails
 * here rather than somewhere downstream. */
int schema_self_check(void);

/* Exposed because the cross-field rules in cfg.c and the tests both need
 * them, and two copies of a netmask predicate is how they drift apart. */
int schema_ipv4_is_unicast(uint32_t a);
int schema_mask_is_contiguous(uint32_t m);	/* 0 counts as contiguous */
int schema_mask_prefix_len(uint32_t m);		/* 0..32, contiguous only */

#endif /* RLXFW_SCHEMA_H */
