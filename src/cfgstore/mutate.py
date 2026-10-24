#!/usr/bin/env python3
"""src/cfgstore/mutate.py -- plant one named defect in a COPY of src/lib.

`make -C src/cfgstore mutants O=...` copies src/lib under $O/mut/<name>/lib,
runs this on the copy, rebuilds the two flash suites against it, and requires
them to go RED.  The real sources never carry a switch that could be flipped.
Each mutation REFUSES unless its anchor matches exactly once, because a cut
that silently matched nothing turns a mutation run into a green line that
means nothing.

  nwrites      cfgflash.c: the "n_writes moved by exactly 32" check never
               fires.  test_flash's +31 and +33 cases must go red.
  badstage     cfgflash.c: img_len that is not 4,096 no longer stops the
               sequence, so the arm and the install follow a bad staging.
               test_flash's img_len case must go red.
  nolock       cfgflash.c: cfg_flash_lock hands back a descriptor without
               taking the lock.  The held-lock, ENOSYS and every accepted
               write list (which begin with the lock) must go red.
  noguard      spictl.c: spictl_flash_read's refusal of [0, 0x10000) and of a
               wrapping range is gone.  test_spictl's guard cases must go red.
  nocleanup    cfgflash.c: a deviation is no longer followed by `img reset`.
               Every deviation's write list must go red.
  ptrdispatch  cfg.c: the backend is chosen by POINTER equality with one
               copy of CFG_FLASH_DEV.  `--file /dev/mtd2ro` (an argv string)
               then reaches the file backend, which reads the chip from 0:
               test_flash's dispatch and CLI cases must go red.
  noregular    cfg.c: cfg_load_info no longer refuses a path that is not a
               regular file, so /dev/mtd0ro and //dev/mtd2ro are read from
               offset 0.  test_flash's non-regular cases must go red.

    mutate.py <name> <copied lib dir>
Exit: 0 planted, 2 usage, 3 an anchor did not match exactly once.
"""
import os
import sys

MUTATIONS = {
    "nwrites": ("cfgflash.c",
                "\tif ((uint32_t)(nw1 - nw0) != CFG_FLASH_NWRITES) {\n",
                "\tif (0 && (uint32_t)(nw1 - nw0) != CFG_FLASH_NWRITES) {\n"),
    "badstage": ("cfgflash.c",
                 "\t\treturn cf_abort(s, \"img_len\", d);\n",
                 "\t\t(void)d;\n"),
    "nolock": ("cfgflash.c",
               "\tfd = spictl_lock(&spictl_dev, CFG_FLASH_LOCK_S);\n",
               "\tfd = 99;\n"),
    "noguard": ("spictl.c",
                "\tif (off < SPICTL_GUARD_HI)\n"
                "\t\treturn -EPERM;\n"
                "\tif (len > (size_t)(0xFFFFFFFFu - off))\n"
                "\t\treturn -EPERM;\n",
                ""),
    "nocleanup": ("cfgflash.c",
                  "\t(void)cf_fail(s, step, detail);\n"
                  "\trc = spictl_verb(&spictl_dev, \"img reset\");\n",
                  "\t(void)cf_fail(s, step, detail);\n"
                  "\trc = 0;\n"),
    "ptrdispatch": ("cfg.c",
                    "\treturn (path != NULL && strcmp(path, CFG_FLASH_DEV) == 0) ? 1 : 0;\n",
                    "\tstatic const char *const flash_dev = CFG_FLASH_DEV;\n"
                    "\n"
                    "\treturn (path != NULL && path == flash_dev) ? 1 : 0;\n"),
    "noregular": ("cfg.c",
                  "\t\tif (file_not_regular(fd, path)) {\n"
                  "\t\t\tclose(fd);\n"
                  "\t\t\treturn -CFGE_IO;\t/* before any read */\n"
                  "\t\t}\n",
                  ""),
}


def main(argv):
    if len(argv) != 3 or argv[1] not in MUTATIONS:
        sys.stderr.write("usage: mutate.py {%s} <copied lib dir>\n"
                         % "|".join(sorted(MUTATIONS)))
        return 2
    name, libdir = argv[1], argv[2]
    fname, old, new = MUTATIONS[name]
    path = os.path.join(libdir, fname)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    n = text.count(old)
    if n != 1:
        sys.stderr.write("mutate.py: REFUSED: the anchor for %s matches %d "
                         "times in %s, want exactly 1\n" % (name, n, path))
        return 3
    out = text.replace(old, new, 1)
    if out == text:
        sys.stderr.write("mutate.py: REFUSED: %s changed nothing\n" % name)
        return 3
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, path)
    sys.stdout.write("mutate.py: planted %s in %s\n" % (name, path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
