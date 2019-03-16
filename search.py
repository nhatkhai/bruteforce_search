#!/bin/python
#!/usr/bin/env python3
"""
TODO - Documentation
"""

import os
import sys
import signal
import logging
import datetime
import argparse
from pw_spec import iterfromrule

log=logging.getLogger(__name__)
stop_signal=False

def start_brute(rulefile, cfg):
    """ Brute-force main routine """
    global stop_signal

    save_state_file = rulefile + ".sav"
    if os.path.isfile(save_state_file):
      log.info("Read saved state file %s...", save_state_file)
      combinations = iterfromrule(save_state_file)
    else:
      log.info("Read rule file %s...", rulefile)
      combinations = iterfromrule(rulefile)

    do_initialize(cfg)

    log.info("starting brute-force...")
    for candidate in combinations:
      log.log(0, "Try %s", candidate)

      if do_checkpass(candidate, cfg):
        log.info("Password found: ", candidate)
        return

      if stop_signal:
        log.info("Save current search states into %s...", save_state_file)
        combinations.save_state(save_state_file)
        break
  
    log.error("Password not found.")


def signal_handler(sig, frame):
  global stop_signal

  # Force exit for second times
  if stop_signal:
    sys.exit(0)

  stop_signal = True


def do_initialize(cfg):
    """ Unmount TrueCrypt drive """
    log.info("Unmouting drive...")
    cmd = "truecrypt /l{:s} /d /s /q".format(cfg.drive)
    ret = os.system(cmd)


def do_checkpass(password, cfg):
    """ Check password """
    cmd = "truecrypt /v {:s} /l{:s} /a /p {:s} /e /b /s /q".format(
        cfg.volume, cfg.drive, password)
    os.system(cmd)
    ret = os.path.exists(cfg.drive + ":\\")
    return ret


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-v", '--volume'
        , help="path to a TrueCrypt volume"
        , required=True )
    parser.add_argument("-l", '--drive'
        , help="driver letter to mount the volume as"
       , required=True )
    parser.add_argument("-r", "--rule"
        , help="Specify which rule file will be use"
        , default="rules.txt")

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    a = datetime.datetime.now()
    start_brute(args.rule, args)
    b = datetime.datetime.now()
    log.info("Operations took {0} seconds.".format(b-a))


if __name__ == "__main__":
  FORMAT= '%(asctime)s [%(filename)s:%(lineno)-4d] %(levelname)7s - %(message)s'
  logging.basicConfig(format=FORMAT, level=logging.DEBUG)

  main()
