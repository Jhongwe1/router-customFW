/* src/brokerd/test_help.h -- fixtures shared by the host tests.  Not compiled
 * into brokerd itself and not on the target path.
 */
#ifndef RLXFW_TEST_HELP_H
#define RLXFW_TEST_HELP_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "brokerd.h"
#include "kdf.h"

/* Install a known admin.pwhash, so LOGIN and PWSET have ONE determined answer
 * instead of two indistinguishable ones ("wrong password" and "no password
 * set" are both AUTH on the wire, deliberately).
 *
 * `FW-184`: and WRITE it to bk->cfg_path.  bk_dispatch() re-reads the store
 * before every request, so a hash that lived only in bk->cfg would be gone by
 * the first dispatch: the store is the one place a password lives, here as on
 * the device.  A fixture that cannot write it stops the binary, rather than
 * letting every later LOGIN fail for a reason that is not the code's. */
static void bk_test_set_pw(struct broker *bk, const char *pw)
{
	uint8_t h[BK_PWHASH_LEN];
	int i, rc;

	memset(h, 0, sizeof(h));
	h[0] = 1;                                   /* alg = scrypt */
	h[1] = BK_KDF_LOG2N;
	proto_put_be16(h + 2, BK_KDF_R);
	proto_put_be16(h + 4, BK_KDF_P);
	for (i = 0; i < 16; i++)
		h[8 + i] = (uint8_t)(0x11 * (i + 1));
	(void)kdf_scrypt((const uint8_t *)pw, strlen(pw), h + 8,
	                 BK_KDF_LOG2N, BK_KDF_R, BK_KDF_P, h + 24);
	(void)cfg_set(&bk->cfg, CFGID_ADMIN_PWHASH, h, BK_PWHASH_LEN);
	rc = cfg_store(bk->cfg_path, &bk->cfg);
	if (rc != 0) {
		(void)printf("  FAIL fixture: cfg_store(%s) rc=%d (%s)\n",
		             bk->cfg_path, rc, cfg_strerror(rc));
		exit(2);
	}
}

static int bk_test_write_file(const char *path, const char *text)
{
	FILE *f = fopen(path, "w");

	if (f == 0)
		return -1;
	(void)fputs(text, f);
	return fclose(f) == 0 ? 0 : -1;
}

#endif /* RLXFW_TEST_HELP_H */
