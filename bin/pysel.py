#!/usr/bin/python
import sys, os
import pysel_core
import logging
import argparse

######################################################################
# Functions
######################################################################
def isValidTestName(s):
    if ('.' in s):
      msg = "%s contains periods, so I think it has an extension. Periods are not allowed." % s
      raise argparse.ArgumentTypeError(msg)
    testPath = os.path.join(pysel_core.DIR_TEST, s+'.'+pysel_core.EXT_TEST)
    if not os.path.exists(testPath):
      dirList = os.listdir(pysel_core.DIR_TEST)
      testNames = []
      for f in dirList:
        if f.endswith(".json"): testNames.append(f.split(".")[0])
      msg = "'%s' does not match a valid test name. The available test names are:\n-----------------\n%s\n-----------------" % (s, "\n".join(sorted(testNames)))
      raise argparse.ArgumentTypeError(msg)
    return s

def generateParser():
  parser = argparse.ArgumentParser()

  subparsers = parser.add_subparsers(help='action', dest='action')

  parser.add_argument('-v', '--verbose', action='count', default=0,
                    help='Increases verbosity of output')
  parser.add_argument('-s', '--silent', action='count',
                    help='Starts pySel in Silent-mode for automation purposes')
  parser.add_argument('-l', '--nolog', action='count',
                    help='Brings output to stdout instead of log')

  # A test command
  test_parser = subparsers.add_parser('test', help='Execute a selenium test')
  test_parser.add_argument('test_name', action='store', type=isValidTestName, help='Name of selenium testcase')
  create_parser = subparsers.add_parser('create', help='Create a selenium test using an interactive session with the driver')

  return parser

def configureLogging(numeric_level, nolog):
  logfile = os.path.join(pysel_core.DIR_LOG, pysel_core.FILE_LOG + '.' + pysel_core.EXT_LOG)
  default_level = 30 # DEBUG = 10 .... ERROR = 40
  debug_level = default_level - (numeric_level * 10)
  if not isinstance(debug_level, int):
    debug_level=0
  if nolog:
    logging.basicConfig(
      level=debug_level,
      format='%(asctime)s [%(levelname)s in %(module)s] %(message)s', 
      datefmt='%Y/%m/%dT%I:%M:%S'
    )
  else:
    logging.basicConfig(
      filename=logfile, 
      level=debug_level,
      format='%(asctime)s [%(levelname)s in %(module)s] %(message)s', 
      datefmt='%Y/%m/%dT%I:%M:%S'
    )

######################################################################
# MAIN FUNCTION
######################################################################

def main(argv):
  parser           = generateParser()
  # Parse command line arguments
  results          = parser.parse_args()
  pysel_core.DEBUG = results.verbose
  configureLogging(results.verbose, (results.nolog) or (results.action == 'create'))

  # Execute all the tests
  try:
    if results.action == 'test':
      return pysel_core.runTest(results.test_name)
    if results.action == 'create':
      return pysel_core.createTest()

    else:
      logging.error('Unsupported command: %s' % results.action)
      return pysel_core.PYSEL_SEV1

  except Exception, err:
    logging.error("Type=%s" % type(err))
    logging.exception("Error Caught:")
    logging.error("%s" % err)
    return 1

######################################################################
# MAIN PROGRAM
######################################################################
if __name__ == '__main__':
  sys.exit(main(sys.argv))