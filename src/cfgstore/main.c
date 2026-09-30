/* main.c -- `cfgstore`, the console CLI for the R7 config store.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT IS FOR
 * ---------------------------------------------------------------------------
 *
 * SPEC-R7 § 3 gives cfgstore one job the web UI cannot do: reach the store
 * directly when brokerd is down, from a root console.  So it is the tool that
 * sets the first password and the tool that reads a store nothing else will
 * load.  Both of those mean it runs when something is already wrong, which is
 * why `dump` exists and why every refusal names the key it is about.
 *
 * There is no shell anywhere in it: no system(), no popen(), no exec at all.
 * It reads and writes one file through src/lib/cfg.c and prints.
 *
 * ---------------------------------------------------------------------------
 * EXIT CODES (SPEC-R7, this assignment)
 * ---------------------------------------------------------------------------
 *
 *   0  ok
 *   1  usage: no such verb, a missing operand, an argument without `=`
 *   2  invalid value, and the message names the key
 *   3  I/O, and -- see `cmd_passwd` -- the KDF being absent
 *   4  the store is there and neither slot is a valid record
 *
 * An unknown KEY NAME exits 2, not 1: the code that names a key is the one a
 * caller can act on, and "no such key: lan.ipadr" is a value problem in every
 * sense that matters to whoever typed it.
 *
 * ---------------------------------------------------------------------------
 * WHAT `get` WILL NOT PRINT
 * ---------------------------------------------------------------------------
 *
 * `admin.pwhash` prints as `set` or `unset` and never as bytes.  That is not
 * enforced here by remembering to special-case it: cfg_value_to_text() refuses
 * every WEB_HIDDEN key, so a future hidden key is covered by the same refusal
 * and the code below could not print one even if it tried.  `dump --hex` is the
 * documented exception -- it prints the record as it is on the medium, hash
 * bytes included, because a diagnostic that hides bytes cannot diagnose them.
 */

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "cfg.h"
#include "kdf.h"
#include "schema.h"

#define CFGSTORE_DEFAULT_PATH "/var/lib/cfg.bin"
#define CFGSTORE_MAXARG       64	/* assignments or names in one command */
#define CFGSTORE_NAME_MAX     40	/* > the longest schema name + slack */
#define CFGSTORE_PW_MAX       64	/* SPEC-R7 § 6: LOGIN password 1..64 */

#define EX_OK      0
#define EX_USAGE   1
#define EX_INVAL   2
#define EX_IO      3
#define EX_CORRUPT 4

static const char *g_path = CFGSTORE_DEFAULT_PATH;

static void usage(void)
{
	fputs("usage: cfgstore [--file PATH] <command>\n"
	      "  get [<name>...]        print name=value (all keys if none named)\n"
	      "  set <name>=<value>...  validate everything, then one store write\n"
	      "  unset <name>...        revert keys to their defaults\n"
	      "  show                   table: name, value, source, seq\n"
	      "  dump --hex             the raw record of each slot\n"
	      "  init --force           write the defaults as a new record\n"
	      "  passwd                 set the admin password, read from stdin\n",
	      stderr);
}

static void say_key(const char *verb, const char *name, int rc)
{
	fprintf(stderr, "cfgstore: %s: %s: %s\n", verb,
		(name != NULL) ? name : "?", cfg_strerror(rc));
}

/* ------------------------------------------------------------------------- */
/* Loading, and the one place "corrupt" is decided                           */
/* ------------------------------------------------------------------------- */

/* strict != 0: a store whose file holds bytes but no valid record is an error.
 * strict == 0: the caller wants whatever could be read (dump, init).
 *
 * The distinction matters because falling back to defaults is right for a
 * daemon at boot and wrong for `set`: basing a new record on defaults would
 * quietly throw away a configuration whose only problem might be one flipped
 * bit in the slot nobody is reading. */
static int load_or_die(struct cfg *c, struct cfg_store_info *info, int strict,
		       const char *verb)
{
	int rc = cfg_load_info(g_path, c, info);

	if (rc != 0) {
		fprintf(stderr, "cfgstore: %s: %s: %s\n", verb, g_path,
			cfg_strerror(rc));
		return EX_IO;
	}
	if (strict && info->selected == 0 && info->file_bytes > 0) {
		fprintf(stderr,
			"cfgstore: %s: %s: no valid record in either slot "
			"(slot0 %s; slot1 %s)\n", verb, g_path,
			cfg_strerror(info->rc[0]), cfg_strerror(info->rc[1]));
		fputs("cfgstore: refusing to act on defaults over a store that "
		      "exists; `cfgstore dump --hex` shows what is there\n",
		      stderr);
		return EX_CORRUPT;
	}
	return EX_OK;
}

static const char *source_name(int source)
{
	switch (source) {
	case 1:
		return "slot0";
	case 2:
		return "slot1";
	default:
		return "default";
	}
}

/* ------------------------------------------------------------------------- */
/* get                                                                       */
/* ------------------------------------------------------------------------- */

static int print_one(const struct cfg *c, const struct cfg_key *k)
{
	uint8_t v[CFG_VAL_MAX];
	char text[CFG_TEXT_MAX];
	uint16_t len = 0;
	int rc;

	if (k->web == WEB_HIDDEN) {
		rc = cfg_present(c, k->id);
		printf("%s=%s\n", k->name, (rc == 1) ? "set" : "unset");
		return EX_OK;
	}

	rc = cfg_get(c, k->id, v, &len);
	if (rc != 0) {
		say_key("get", k->name, rc);
		return EX_INVAL;
	}
	rc = cfg_value_to_text(k, v, len, text, sizeof text);
	if (rc < 0) {
		say_key("get", k->name, rc);
		return EX_INVAL;
	}
	printf("%s=%s\n", k->name, text);
	return EX_OK;
}

static int cmd_get(int argc, char **argv)
{
	struct cfg c;
	struct cfg_store_info info;
	int i, rc, worst = EX_OK;

	rc = load_or_die(&c, &info, 1, "get");
	if (rc != EX_OK)
		return rc;

	if (argc == 0) {
		for (i = 0; i < CFG_NKEYS; i++) {
			rc = print_one(&c, &cfg_keys[i]);
			if (rc != EX_OK)
				worst = rc;
		}
		return worst;
	}
	for (i = 0; i < argc; i++) {
		const struct cfg_key *k = cfg_key_by_name(argv[i]);

		if (k == NULL) {
			say_key("get", argv[i], -CFGE_NAME);
			return EX_INVAL;
		}
		rc = print_one(&c, k);
		if (rc != EX_OK)
			worst = rc;
	}
	return worst;
}

/* ------------------------------------------------------------------------- */
/* show                                                                      */
/* ------------------------------------------------------------------------- */

static int cmd_show(void)
{
	struct cfg c;
	struct cfg_store_info info;
	int i, rc;

	rc = load_or_die(&c, &info, 1, "show");
	if (rc != EX_OK)
		return rc;

	printf("store  %s  bytes %lu  source %s  seq %lu\n", g_path,
	       (unsigned long)info.file_bytes, source_name(c.source),
	       (unsigned long)c.seq);
	printf("slot0  %s (seq %lu)   slot1  %s (seq %lu)\n",
	       cfg_strerror(info.rc[0]), (unsigned long)info.seq[0],
	       cfg_strerror(info.rc[1]), (unsigned long)info.seq[1]);
	printf("\n%-14s %-18s %-8s %s\n", "NAME", "VALUE", "SOURCE", "SEQ");

	for (i = 0; i < CFG_NKEYS; i++) {
		const struct cfg_key *k = &cfg_keys[i];
		uint8_t v[CFG_VAL_MAX];
		char text[CFG_TEXT_MAX];
		uint16_t len = 0;
		int in_rec = (cfg_present(&c, k->id) == 1);
		const char *src = in_rec ? source_name(c.source) : "default";
		unsigned long seq = in_rec ? (unsigned long)c.seq : 0ul;

		if (k->web == WEB_HIDDEN) {
			printf("%-14s %-18s %-8s %lu\n", k->name,
			       in_rec ? "<set>" : "<unset>", src, seq);
			continue;
		}
		if (cfg_get(&c, k->id, v, &len) != 0 ||
		    cfg_value_to_text(k, v, len, text, sizeof text) < 0) {
			printf("%-14s %-18s %-8s %lu\n", k->name, "<error>",
			       src, seq);
			continue;
		}
		printf("%-14s %-18s %-8s %lu\n", k->name, text, src, seq);
	}
	return EX_OK;
}

/* ------------------------------------------------------------------------- */
/* set / unset -- all-or-nothing, one store write                            */
/* ------------------------------------------------------------------------- */

static int commit(struct cfg *c, const char *verb)
{
	int rc = cfg_validate(c);

	if (rc != 0) {
		const struct cfg_key *k = cfg_key_by_id(cfg_last_key());

		say_key(verb, (k != NULL) ? k->name : NULL, rc);
		return EX_INVAL;
	}
	rc = cfg_store(g_path, c);
	if (rc != 0) {
		const struct cfg_key *k = cfg_key_by_id(cfg_last_key());

		if (rc == -CFGE_IO || rc == -CFGE_SEQ) {
			fprintf(stderr, "cfgstore: %s: %s: %s\n", verb, g_path,
				cfg_strerror(rc));
			return EX_IO;
		}
		say_key(verb, (k != NULL) ? k->name : NULL, rc);
		return EX_INVAL;
	}
	printf("written: slot %d, seq %lu\n", c->source - 1,
	       (unsigned long)c->seq);
	return EX_OK;
}

static int cmd_set(int argc, char **argv)
{
	struct cfg c;
	struct cfg_store_info info;
	int i, rc;

	if (argc < 1) {
		usage();
		return EX_USAGE;
	}
	if (argc > CFGSTORE_MAXARG) {
		fprintf(stderr, "cfgstore: set: at most %d assignments\n",
			CFGSTORE_MAXARG);
		return EX_USAGE;
	}
	rc = load_or_die(&c, &info, 1, "set");
	if (rc != EX_OK)
		return rc;

	/* Every assignment is parsed and applied to the in-memory copy, and the
	 * cross-field rules run over the result, BEFORE anything is written.
	 * The store write is the last statement, and there is exactly one. */
	for (i = 0; i < argc; i++) {
		char name[CFGSTORE_NAME_MAX];
		const char *eq = strchr(argv[i], '=');
		const struct cfg_key *k;
		uint8_t v[CFG_VAL_MAX];
		uint16_t len = 0;
		size_t nl;

		if (eq == NULL) {
			fprintf(stderr, "cfgstore: set: `%s' is not name=value\n",
				argv[i]);
			return EX_USAGE;
		}
		nl = (size_t)(eq - argv[i]);
		if (nl == 0 || nl >= sizeof name) {
			fprintf(stderr, "cfgstore: set: key name too long or empty\n");
			return EX_USAGE;
		}
		memcpy(name, argv[i], nl);
		name[nl] = '\0';

		k = cfg_key_by_name(name);
		if (k == NULL) {
			say_key("set", name, -CFGE_NAME);
			return EX_INVAL;
		}
		if (k->web == WEB_HIDDEN) {
			fprintf(stderr, "cfgstore: set: %s is not settable here;"
				" use `cfgstore passwd'\n", k->name);
			return EX_INVAL;
		}
		if (strlen(eq + 1) >= (size_t)CFG_TEXT_MAX) {
			say_key("set", k->name, -CFGE_TEXT);
			return EX_INVAL;
		}
		rc = cfg_text_to_value(k, eq + 1, v, &len);
		if (rc != 0) {
			say_key("set", k->name, rc);
			return EX_INVAL;
		}
		rc = cfg_set(&c, k->id, v, len);
		if (rc != 0) {
			say_key("set", k->name, rc);
			return EX_INVAL;
		}
	}
	return commit(&c, "set");
}

static int cmd_unset(int argc, char **argv)
{
	struct cfg c;
	struct cfg_store_info info;
	int i, rc;

	if (argc < 1) {
		usage();
		return EX_USAGE;
	}
	if (argc > CFGSTORE_MAXARG) {
		fprintf(stderr, "cfgstore: unset: at most %d names\n",
			CFGSTORE_MAXARG);
		return EX_USAGE;
	}
	rc = load_or_die(&c, &info, 1, "unset");
	if (rc != EX_OK)
		return rc;

	for (i = 0; i < argc; i++) {
		const struct cfg_key *k = cfg_key_by_name(argv[i]);

		if (k == NULL) {
			say_key("unset", argv[i], -CFGE_NAME);
			return EX_INVAL;
		}
		rc = cfg_unset(&c, k->id);
		if (rc != 0) {
			say_key("unset", k->name, rc);
			return EX_INVAL;
		}
	}
	return commit(&c, "unset");
}

/* ------------------------------------------------------------------------- */
/* init --force                                                              */
/* ------------------------------------------------------------------------- */

static int cmd_init(int argc, char **argv)
{
	struct cfg c;
	struct cfg_store_info info;
	int i, rc;

	if (argc != 1 || strcmp(argv[0], "--force") != 0) {
		fputs("cfgstore: init requires --force (it overwrites a slot)\n",
		      stderr);
		return EX_USAGE;
	}
	/* Not strict: init is the verb that repairs a store nothing can load. */
	rc = load_or_die(&c, &info, 0, "init");
	if (rc != EX_OK)
		return rc;

	rc = cfg_defaults(&c);
	if (rc != 0) {
		say_key("init", NULL, rc);
		return EX_INVAL;
	}
	/* The defaults are written OUT, not left implicit.  A record that names
	 * its values is a record a later change of default cannot silently
	 * reconfigure a deployed device through.  admin.pwhash has no default
	 * and stays absent, which is the fail-closed state. */
	for (i = 0; i < CFG_NKEYS; i++) {
		const uint8_t *dv;
		uint16_t dl;
		int drc = schema_default(cfg_keys[i].id, &dv, &dl);

		if (drc == -CFGE_NOENT)
			continue;
		if (drc != 0) {
			say_key("init", cfg_keys[i].name, drc);
			return EX_INVAL;
		}
		rc = cfg_set(&c, cfg_keys[i].id, dv, dl);
		if (rc != 0) {
			say_key("init", cfg_keys[i].name, rc);
			return EX_INVAL;
		}
	}
	return commit(&c, "init");
}

/* ------------------------------------------------------------------------- */
/* dump --hex                                                                */
/* ------------------------------------------------------------------------- */

static void hexdump(const uint8_t *p, size_t n, size_t base)
{
	size_t i, j;

	for (i = 0; i < n; i += 16) {
		printf("%04lx ", (unsigned long)(base + i));
		for (j = 0; j < 16; j++) {
			if (i + j < n)
				printf("%02x", (unsigned)p[i + j]);
			else
				fputs("  ", stdout);
			if ((j & 3u) == 3u)
				putchar(' ');
		}
		putchar('|');
		for (j = 0; j < 16 && i + j < n; j++) {
			unsigned ch = p[i + j];

			putchar((ch >= 0x20u && ch < 0x7Fu) ? (int)ch : '.');
		}
		puts("|");
	}
}

static int cmd_dump(int argc, char **argv)
{
	struct cfg c;
	struct cfg_store_info info;
	uint8_t slot[CFG_SLOT_SIZE];
	FILE *f;
	int s, rc;

	if (argc != 1 || strcmp(argv[0], "--hex") != 0) {
		fputs("cfgstore: dump requires --hex\n", stderr);
		return EX_USAGE;
	}
	/* Not strict: dumping a broken store is the whole point. */
	rc = load_or_die(&c, &info, 0, "dump");
	if (rc != EX_OK)
		return rc;

	f = fopen(g_path, "rb");
	if (f == NULL) {
		fprintf(stderr, "cfgstore: dump: %s: %s\n", g_path,
			strerror(errno));
		return EX_IO;
	}
	printf("store %s  bytes %lu  selected %s\n", g_path,
	       (unsigned long)info.file_bytes, source_name(info.selected));

	for (s = 0; s < CFG_NSLOTS; s++) {
		size_t got = fread(slot, 1, sizeof slot, f);
		size_t show;

		printf("\nslot %d  offset %lu  read %lu  verdict %s  seq %lu\n",
		       s, (unsigned long)((size_t)s * CFG_SLOT_SIZE),
		       (unsigned long)got, cfg_strerror(info.rc[s]),
		       (unsigned long)info.seq[s]);
		if (got == 0)
			continue;

		/* The record's own extent when the header can be believed,
		 * otherwise a fixed window: printing 4 KiB of 0xFF fill down a
		 * 38400 baud console is not diagnosis. */
		show = 0;
		if (got >= (size_t)CFG_HDR_LEN) {
			uint32_t paylen = ((uint32_t)slot[12] << 24) |
					  ((uint32_t)slot[13] << 16) |
					  ((uint32_t)slot[14] << 8) |
					  (uint32_t)slot[15];

			if (info.rc[s] == 0 &&
			    paylen <= (uint32_t)(CFG_SLOT_SIZE - CFG_HDR_LEN))
				show = (size_t)CFG_HDR_LEN + (size_t)paylen;
		}
		if (show == 0 || show > got) {
			show = (got < 64u) ? got : 64u;
			printf("  (header not believable; first %lu bytes)\n",
			       (unsigned long)show);
		}
		hexdump(slot, show, (size_t)s * CFG_SLOT_SIZE);
	}
	fclose(f);
	return EX_OK;
}

/* ------------------------------------------------------------------------- */
/* passwd -- and it cannot succeed in R7                                     */
/* ------------------------------------------------------------------------- */

/* Reads one line from stdin into buf, strips a trailing \n and \r, and refuses
 * a line longer than the buffer instead of truncating it: a silently truncated
 * password is a password the user cannot type again. */
static int read_line(char *buf, size_t cap, size_t *len)
{
	size_t i = 0;
	int ch;

	for (;;) {
		ch = fgetc(stdin);
		if (ch == EOF) {
			if (i == 0)
				return -1;
			break;
		}
		if (ch == '\n')
			break;
		if (i + 1 >= cap)
			return -2;		/* too long */
		buf[i++] = (char)ch;
	}
	while (i > 0 && buf[i - 1] == '\r')
		i--;
	buf[i] = '\0';
	*len = i;
	return 0;
}

static int cmd_passwd(int argc, char **argv)
{
	char pw[CFGSTORE_PW_MAX + 1];
	size_t pwlen = 0;
	int rc;

	(void)argv;
	if (argc != 0) {
		fputs("cfgstore: passwd takes no arguments; the password is read"
		      " from stdin and never from argv\n", stderr);
		return EX_USAGE;
	}

	/* FAIL CLOSED, AND BEFORE ANYTHING ELSE.  No salt is drawn, no store is
	 * opened, no password is read: with no KDF there is nothing that could
	 * be done with any of them, and a tool that goes through the motions and
	 * then fails teaches the operator that the failure is cosmetic.
	 *
	 * SPEC-R7 § 4.2 leaves the scrypt parameters to the anti-DoS budget in
	 * plan D8 (ruling 4) and they are not settled, so src/lib/kdf.h carries
	 * the interface and no implementation.  See its header comment. */
	if (!KDF_IMPLEMENTED) {
		fputs("cfgstore: passwd: REFUSED -- no key derivation function.\n"
		      "  src/lib/kdf.h: kdf_scrypt() is declared and returns "
		      "ENOSYS; the scrypt\n"
		      "  parameters come from plan D8's anti-DoS budget and are "
		      "not settled yet.\n"
		      "  Nothing was written.  admin.pwhash stays absent, so no "
		      "login can succeed.\n", stderr);
		return EX_IO;
	}

	/* `R7-8`: this half used to end in "unreachable" and EX_IO, because
	 * src/lib/kdf.h was a declaration with -ENOSYS when cfgstore was written.
	 * It is the real thing now, and it has to be: `admin.pwhash` has no
	 * default, httpd's /api/password needs a session, and a session needs a
	 * password -- so without a working `cfgstore passwd` this image could
	 * never have one set at all.  The store write is the ordinary one
	 * (cfg_set + commit), so `set`'s cross-field validation and two-slot
	 * discipline apply to a password like to anything else.
	 *
	 * The password is read ONCE, from stdin, exactly as the code above was
	 * written to do; there is no confirmation prompt, and `dump` is how an
	 * operator checks that a hash landed. */
	if (isatty(STDIN_FILENO))
		fputs("new password: ", stderr);
	rc = read_line(pw, sizeof pw, &pwlen);
	if (rc == -2) {
		fprintf(stderr, "cfgstore: passwd: longer than %d bytes\n",
			CFGSTORE_PW_MAX);
		return EX_INVAL;
	}
	if (rc != 0 || pwlen < 8) {
		memset(pw, 0, sizeof pw);
		fputs("cfgstore: passwd: 8..64 bytes required\n", stderr);
		return EX_INVAL;
	}
	{
		uint8_t salt[KDF_SALT_LEN];
		uint8_t blob[PWHASH_LEN];
		struct cfg c;
		struct cfg_store_info info;
		int ent;

		/* FAIL CLOSED ON ENTROPY, and before the store is touched.  A
		 * salt drawn from a pool that is not ready is a salt an attacker
		 * can guess, and this board's pool 量 0 at 768 s uptime on the
		 * previous image (SPEC-R7 § 6). pwhash_salt() makes the reading
		 * itself, refuses below KDF_ENTROPY_MIN, and never returns a
		 * weak salt; the reading is printed either way so that a refusal
		 * says how far off it was. */
		ent = kdf_entropy_avail();
		rc = pwhash_salt(salt);
		if (rc != 0) {
			fprintf(stderr,
				"cfgstore: passwd: REFUSED -- the kernel entropy "
				"pool is not ready\n"
				"  entropy_avail = %d, %d needed (%s).  Nothing "
				"was written.\n", ent, KDF_ENTROPY_MIN,
				(rc == -KDFE_ENTROPY) ? "pool too small"
						      : "/dev/urandom or /proc unreadable");
			memset(pw, 0, sizeof pw);
			return EX_IO;
		}
		rc = pwhash_make((const uint8_t *)pw, pwlen, KDF_LOG2N, KDF_R,
				 KDF_P, salt, blob);
		memset(pw, 0, sizeof pw);
		memset(salt, 0, sizeof salt);
		if (rc != 0) {
			fprintf(stderr, "cfgstore: passwd: the KDF refused "
				"(-%d); nothing was written\n", -rc);
			memset(blob, 0, sizeof blob);
			return EX_IO;
		}
		rc = load_or_die(&c, &info, 1, "passwd");
		if (rc != EX_OK) {
			memset(blob, 0, sizeof blob);
			return rc;
		}
		if (cfg_set(&c, CFG_ID_PWHASH, blob, PWHASH_LEN) != 0) {
			memset(blob, 0, sizeof blob);
			fputs("cfgstore: passwd: the schema refused the 56-byte "
			      "blob; nothing was written\n", stderr);
			return EX_INVAL;
		}
		memset(blob, 0, sizeof blob);
		rc = commit(&c, "passwd");
		if (rc == EX_OK)
			printf("admin.pwhash set: scrypt log2N=%d r=%d p=%d, "
			       "entropy_avail was %d\n", KDF_LOG2N, KDF_R,
			       KDF_P, ent);
		return rc;
	}
}

/* ------------------------------------------------------------------------- */

int main(int argc, char **argv)
{
	int i = 1;
	int rc;

	/* The schema is what every other check is expressed in terms of, so it
	 * is checked before any of them, in every program, on every run. */
	rc = schema_self_check();
	if (rc != 0) {
		fprintf(stderr, "cfgstore: schema self-check failed: %s\n",
			cfg_strerror(rc));
		return EX_IO;
	}

	while (i < argc && argv[i][0] == '-' && argv[i][1] == '-') {
		if (strcmp(argv[i], "--file") == 0) {
			if (i + 1 >= argc) {
				fputs("cfgstore: --file needs a path\n", stderr);
				return EX_USAGE;
			}
			g_path = argv[i + 1];
			i += 2;
			continue;
		}
		if (strcmp(argv[i], "--help") == 0) {
			usage();
			return EX_OK;
		}
		break;		/* a verb's own option: leave it to the verb */
	}

	if (i >= argc) {
		usage();
		return EX_USAGE;
	}

	if (strcmp(argv[i], "get") == 0)
		return cmd_get(argc - i - 1, argv + i + 1);
	if (strcmp(argv[i], "set") == 0)
		return cmd_set(argc - i - 1, argv + i + 1);
	if (strcmp(argv[i], "unset") == 0)
		return cmd_unset(argc - i - 1, argv + i + 1);
	if (strcmp(argv[i], "show") == 0) {
		if (argc - i - 1 != 0) {
			usage();
			return EX_USAGE;
		}
		return cmd_show();
	}
	if (strcmp(argv[i], "dump") == 0)
		return cmd_dump(argc - i - 1, argv + i + 1);
	if (strcmp(argv[i], "init") == 0)
		return cmd_init(argc - i - 1, argv + i + 1);
	if (strcmp(argv[i], "passwd") == 0)
		return cmd_passwd(argc - i - 1, argv + i + 1);

	fprintf(stderr, "cfgstore: no such command: %s\n", argv[i]);
	usage();
	return EX_USAGE;
}
