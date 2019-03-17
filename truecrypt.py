#!/bin/python
#!/usr/bin/env python3
#
# exitcode  = 0 - For password OK, initial OK
# exitcode  = 1 - For password not OK, or initial not OK
# exitcode >= 2 - For fatal error, or initial not OK
#
import os
import sys
import argparse
import logging
import subprocess

log=logging.getLogger(__name__)

def do_initialize(cfg):
    log.info("Unmouting drive %s...", cfg.letter)
    ret = subprocess.call(["truecrypt",
      '/s', '/q',
      '/d', '/l', cfg.letter,
    ])

    if ret !=0:
      log.error("Unable to execute truecrypt with error code of %s", ret)
      sys.exit(1)

    if os.path.isdir(cfg.letter + ":\\"):
      log.error("Unable to unmount drive %s", cfg.letter)
      sys.exit(1)

def do_checkpass(cfg):
    """ Check password """
    ret = subprocess.call(['truecrypt',
      '/s', '/q',
      '/v', cfg.volume,
      '/l', cfg.letter,
      '/p', cfg.password,
      ])

    if ret !=0:
      log.warn("truecrypt return %s", ret)
      sys.exit(1)

    if not os.path.isdir(cfg.letter + ":\\"):
      sys.exit(1)

def main(): 
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('password', help="path to a TrueCrypt volume"
      , nargs='?')
  parser.add_argument("-l", '--letter' 
      , help="driver letter to mount the volume as (X for example)."
    , required=True )
  parser.add_argument("-v", '--volume'
      , help="path to a TrueCrypt volume, such as \Device\Harddisk1\Partition1"
      , required=True )
  parser.add_argument("-c", '--checkdrive'
      , help="check driver letter that should always exist")

  args = parser.parse_args()

  if not os.path.isdir(args.checkdrive + ":\\"):
    log.error("Cannot found drive %s", args.checkdrive)
    sys.exit(2)

  if args.password is None:
    return do_initialize(args)
  else:
    return do_checkpass(args)

if __name__ == "__main__":
  FORMAT= '%(asctime)s [%(filename)15s:%(lineno)-4d] %(levelname)7s - %(message)s'
  logging.basicConfig(format=FORMAT, level=logging.WARN)
  main()
