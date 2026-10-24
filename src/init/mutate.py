#!/usr/bin/env python3
"""src/init/mutate.py -- plant one named defect in a COPY of ctradv.c or firstpw.c.

`make -C src/init mutants O=...` copies the module under $O/mut/<name>/, runs
this on the copy, rebuilds the module's own test against it with the suite's
flags, and requires the test to go RED with at least one FAIL line.  The real
sources never carry a switch that could be flipped.  Each mutation REFUSES
unless every one of its anchors matches exactly once, because a cut that
silently matched nothing turns a mutation run into a green line that means
nothing.

  ctradv.c (test_ctradv):
  early      the helper does not wait for brokerd: the first STATUS counts as
             an answer whatever it said.  The never-answering broker's case
             (nothing written, 121 tries, 60,000 ms) must go red.
  onnone     `none` in /proc/rlxfw-boot is not the end of it: the helper goes
             on to the lock and the verb (`ctr 0`).  The `none` case (no verb,
             no lock) must go red.
  twice      the verb is written two times.  Every accepted case's "exactly one
             `ctr N`" must go red.
  nolock     the flash lock is never taken.  The accepted case's event list
             (lock, verb, unlock) and the held-lock case (no verb) must go red.

  firstpw.c (test_firstpw):
  overhash   the re-read before the write no longer stops at a stored hash:
             the step writes a new hash over it.  The hashed store's case
             (nothing written, the bytes unchanged) must go red.
  echo       ECHO is no longer cleared and the read-back no longer checks it.
             The pty case (the password never in what the console showed)
             must go red.
  nowait     a short entropy pool fails the step instead of being waited out.
             The pool-fills-later case must go red.
  noconfirm  the two entries are no longer compared.  The mismatch case
             (nothing written) must go red.

    mutate.py <name> <copied module file>
Exit: 0 planted, 2 usage, 3 an anchor did not match exactly once.
"""
import os
import sys

# name: (module, [(old, new), ...])
MUTATIONS = {
    "early": ("ctradv.c", [
        ("\t\tif (e->broker_up(e->ctx) == 1)\n\t\t\treturn 1;\n",
         "\t\tif (e->broker_up(e->ctx) == 1 || k > 0)\n\t\t\treturn 1;\n"),
    ]),
    "onnone": ("ctradv.c", [
        ("\tif (h == CTR_BOOT_NONE) {\n",
         "\tif (h == CTR_BOOT_NONE && 0) {\n"),
        ("\tif (h != CTR_BOOT_SLOT) {\n",
         "\tif (h != CTR_BOOT_SLOT && h != CTR_BOOT_NONE) {\n"),
    ]),
    "twice": ("ctradv.c", [
        ("\twrc = spictl_verb(e->sp, verb);\n",
         "\twrc = spictl_verb(e->sp, verb);\n"
         "\twrc = spictl_verb(e->sp, verb);\n"),
    ]),
    "nolock": ("ctradv.c", [
        ("\tlk = spictl_lock(e->sp, e->lock_s);\n",
         "\tlk = 99999;\n"),
    ]),
    "overhash": ("firstpw.c", [
        ("\t\tif (fp_has_hash(&cur)) {\n",
         "\t\tif (fp_has_hash(&cur) && 0) {\n"),
    ]),
    "echo": ("firstpw.c", [
        ("\tt.c_lflag &= ~(tcflag_t)(ECHO | ECHOE | ECHOK | ECHONL);\n",
         "\tt.c_lflag &= ~(tcflag_t)(ECHOE | ECHOK | ECHONL);\n"),
        ("\tif (tcgetattr(fd, &t) != 0 || (t.c_lflag & (tcflag_t)ECHO) != 0)\n",
         "\tif (tcgetattr(fd, &t) != 0)\n"),
    ]),
    "nowait": ("firstpw.c", [
        ("\t\tif (rc != -KDFE_ENTROPY) {\n",
         "\t\tif (rc != 0) {\n"),
    ]),
    "noconfirm": ("firstpw.c", [
        ("\t\t} else if (n1 != n2 || memcmp(pw, pw2, n1) != 0) {\n",
         "\t\t} else if (0 && (n1 != n2 || memcmp(pw, pw2, n1) != 0)) {\n"),
    ]),
}


def main(argv):
    if len(argv) != 3 or argv[1] not in MUTATIONS:
        sys.stderr.write("usage: mutate.py {%s} <copied module file>\n"
                         % "|".join(sorted(MUTATIONS)))
        return 2
    name, path = argv[1], argv[2]
    module, pairs = MUTATIONS[name]
    if os.path.basename(path) != module:
        sys.stderr.write("mutate.py: REFUSED: %s plants into %s, not %s\n"
                         % (name, module, path))
        return 2
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    out = text
    for old, new in pairs:
        n = out.count(old)
        if n != 1:
            sys.stderr.write("mutate.py: REFUSED: an anchor of %s matches %d "
                             "times in %s, want exactly 1:\n%s"
                             % (name, n, path, old))
            return 3
        out = out.replace(old, new, 1)
    if out == text:
        sys.stderr.write("mutate.py: REFUSED: %s changed nothing\n" % name)
        return 3
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, path)
    sys.stdout.write("mutate.py: planted %s in %s (%d anchor%s)\n"
                     % (name, path, len(pairs), "" if len(pairs) == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
