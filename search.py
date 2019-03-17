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
import subprocess
from pw_spec import iterfromrule

log=logging.getLogger(__name__)
log.setLevel(logging.INFO)
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
    try:
      for candidate in combinations:
        log.log(0, "Try %s", candidate)

        if do_checkpass(candidate, cfg):
          log.info("Password found: %s", candidate)
          return

        # Check if we reach maximum number of try
        if cfg.ntry is not None:
          cfg.ntry -= 1
          if not cfg.ntry: 
            raise RuntimeError("Reach try limit")

        # User hit Ctrl+C
        if stop_signal:
          raise RuntimeError("User canceled")

    except RuntimeError as e:
      log.error("%s", e);
      log.info("Save current search states into %s...", save_state_file)
      combinations.save_state(save_state_file)
  
    log.error("Password not found.")


def signal_handler(sig, frame):
  global stop_signal

  # Force exit for second times
  if stop_signal:
    sys.exit(0)

  stop_signal = True


def do_initialize(cfg):
    cmd_args = cfg.cmd_args
    log.debug(cmd_args)
    ret = subprocess.call(cmd_args)
    if ret != 0:
      raise RuntimeError("{0} return error code of {1}".format(cmd_args, ret))


def do_checkpass(password, cfg):
    cmd_args = cfg.cmd_args + [password]
    log.debug(cmd_args)
    ret = subprocess.call(cmd_args)
    if ret > 1:
      raise RuntimeError("{0} return error code of {1}".format(cmd_args, ret))

    return ret==0


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-r", '--rule'
        , help="specify which rule file will be use"
        , default="rules.txt")
    parser.add_argument("-c", '--cmd'
        , help="""specify what script will be executed with the candidate
               password. The first call will pass the candidate password.
               It intend for initialization call."""
        , default="truecrypt.py")
    parser.add_argument('cmd_args'
        , help="""arguments pass to CMD script. Using -- before pass all 
               arguments will work better"""
        , metavar='...'
        , nargs=argparse.REMAINDER)
    parser.add_argument('-n', '--ntry'
        , help="Specify maximum number of password will be checked on"
        , type=int)


    args = parser.parse_args()

    # Adjust cmd_args
    if '--' in args.cmd_args[0:1]: 
      del args.cmd_args[0]
    args.cmd_args.insert(0, args.cmd)

    signal.signal(signal.SIGINT, signal_handler)

    a = datetime.datetime.now()
    start_brute(args.rule, args)
    b = datetime.datetime.now()
    log.info("Operations took {0} seconds.".format(b-a))


if __name__ == "__main__":
  FORMAT= '%(asctime)s [%(filename)15s:%(lineno)-4d] %(levelname)7s - %(message)s'
  logging.basicConfig(format=FORMAT, level=logging.DEBUG)
  main()
