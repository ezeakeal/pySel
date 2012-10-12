#!/usr/bin/python

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from termcolor import colored, cprint

import os, re, sys, time, datetime, pwd, grp
import socket, httplib, urllib2
import logging
import texttable as tt
from colorama import Fore, Back, Style
from time import strftime as date

import pysel_util_core    as util_core
import pysel_util_create  as util_create

try:
  import json
except ImportError:
  import simplejson as json

# Debugging
DEBUG = 0
INTERACTIVE = False

# Directory specifiers
APP                = 'pysel'
DIR_APP_ROOT       = '%s'                     % os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')) # Don't even.
DIR_APP            = '%s'                     % (DIR_APP_ROOT)
DIR_TEST           = '%s/test'                % (DIR_APP)
DIR_LIB            = '%s/lib'                 % (DIR_APP)
DIR_CONF           = '%s/conf'                % (DIR_APP)
DIR_LOG            = '%s/output/log'          % (DIR_APP_ROOT)
DIR_RAW            = '%s/output/raw'          % (DIR_APP_ROOT)
DIR_REPORT         = '%s/output/report'       % (DIR_APP_ROOT)
DIR_RESPONSE       = '%s/output/response'     % (DIR_APP_ROOT)
DIR_CONF           = '%s/conf'                % (DIR_APP)

# File Extensions
EXT_TEST           = 'json'
EXT_RAW            = 'raw'
EXT_LOG            = 'log'
EXT_REPORT         = 'rpt'
EXT_RESPONSE       = 'txt'
BASH_EXEC          = '/bin/bash'

FILE_LOG           = 'pysel_%s' % (date("%Y%m%dT%H%M%S"))

# Customize the HTTP Request Headers
USER_AGENT_STR     = 'FeedHenry PySel Automated Tester 0.2'
CONNECTION_TIMEOUT = 30

# Customize the Implicit waits for elements
IMPLICIT_WAIT      = 30

# Create global counters
COUNT_ERROR        = 0
COUNT_WARNING      = 0
COUNT_PIC          = 0

# Define our own severity levels
PYSEL_OK           = 0                    # OK
PYSEL_SEV1         = 1                    # HTTP 50x errors
PYSEL_SEV2         = 2                    # HTTP 40x errors
PYSEL_SEV3         = 3                    # Response Timeout
PYSEL_SEV4         = 4                    # Assertion Failure
PYSEL_SEV5         = 5                    # Other

# Permissions
USER               = os.getenv("USER")
GROUP              = os.getenv("USER")

try: # os.chown can only use the IDs for user and groups instead of stirngs. 
  UID = pwd.getpwnam(USER).pw_uid
  GID = grp.getgrnam(GROUP).gr_gid
except KeyError:
  logging.error("Getting KeyError trying to find UID of %s or GID of %s" % (USER, GROUP))
  logging.error("Please check that both the user and group exist")
  logging.error("PySel will still run but ownership/permissions of files may be incorrect")
  UID = -1 # Apparently, this will cause the chown commands to ignore this variable -
  GID = -1 # both user and group

# http://code.google.com/p/chromedriver/wiki/GettingStarted
DRIVER = None

######################################################################
# Create webdriver
######################################################################
def initDriver():
  global DRIVER
  # DRIVER = webdriver.Firefox()
  driverPath = "%s/chromedriver" % DIR_LIB
  sys.path.append(DIR_LIB)
  DRIVER = webdriver.Chrome(driverPath)
  DRIVER.implicitly_wait(IMPLICIT_WAIT)

######################################################################
# Quit the driver
######################################################################
def quitDriver():
  global DRIVER
  DRIVER.quit() 

######################################################################
# Raise an Error in the manner which you are acustomed to
######################################################################
def raiseError(str, data=None):
  global COUNT_ERROR
  COUNT_ERROR = COUNT_ERROR + 1
  cprint("\nError: %s " % str, 'red')
  if data:
    cprint(json.dumps(data, sort_keys=True, indent=4), 'cyan')

######################################################################
# Raise a Warning for the craic
######################################################################
def raiseWarning(str, data=None):
  global COUNT_WARNING
  COUNT_WARNING = COUNT_WARNING + 1
  cprint("\nWarning: %s " % str, 'yellow')
  if data:
    cprint(json.dumps(data, sort_keys=True, indent=4), 'cyan')

######################################################################
# Summarise test results with various info
######################################################################
def endSummary(reportPath):
  state = "Success"
  sumCol = "green"
  if COUNT_WARNING > 0:
    state = "Warning"
    sumCol = "yellow"
  if COUNT_ERROR > 0:
    state = "Error"
    sumCol = "red"

  cprint("\n########## TEST SUMMARY ##########", sumCol)
  print "State:\t",
  cprint(state, sumCol)
  print "Warns:\t", 
  cprint(COUNT_WARNING, "yellow")
  print "Errors:\t", 
  cprint(COUNT_ERROR, "red")
  print "Report:\t", 
  cprint(reportPath, "cyan")
  print "Log:\t", 
  cprint(os.path.join(DIR_LOG, FILE_LOG + '.' + EXT_LOG), "cyan")
  cprint("##################################", sumCol)

#---------------------------------------------------------------------
# Offer the User to abandon the test as is in case of an error!
#---------------------------------------------------------------------
def suggestContinue():
  cont = ""
  while cont not in ["y", "n"] and not AUTO_PILOT:
    cont = raw_input("Continue? (y/n) ").lower()
  if cont == "n":
    quitDriver()
  else:
    stepNum = raw_input("Enter Step Number To Continue From: ")
    return int(stepNum) - 1

######################################################################
# Take a screenshot
######################################################################
def takeScreenShot(name=None):
  global COUNT_PIC
  if (name == None):
    screenShotPath = "%s/screen_%s.png" % (DIR_REPORT, COUNT_PIC)
  else:
    screenShotPath = "%s/screen_%s_%s.png" % (DIR_REPORT, COUNT_PIC, name)  

  COUNT_PIC = COUNT_PIC +1 
  logging.debug("SCREEN:\tSaving Screenshot to: %s" % screenShotPath)
  DRIVER.save_screenshot(screenShotPath)

######################################################################
# Find, load, and execute a test
######################################################################
def runTest(testName):
  global exitCode, DIR_REPORT, exitMsg
  exitCode = 0

  DIR_REPORT = os.path.join(DIR_REPORT, testName)
  util_core.mkdir(DIR_REPORT)
  util_core.clearDirectory(DIR_REPORT, recursive)

  # Check if file is already reachable using the file name given.
  try:
    initDriver()
    
    logging.debug('\nTEST:\tName=%s' % (testName))
    logging.debug('Processing: %s' % (testName))
    testPath = os.path.join(DIR_TEST, testName+'.'+EXT_TEST) 
    testObject = util_core.loadTestfile(testPath)
    
    logging.info("TEST:\tTest File Loaded! %s" % testName)
    util_core.displayTest(testObject)
    
    executeTest(testName, testObject)
    exitMsg = 'Test processed with overall status: %s' % (exitCode)
  except:
    exitCode = PYSEL_SEV1
    logging.critical("ERROR!")
    logging.error(traceback.format_exc())
  finally:
    quitDriver()

  endSummary(DIR_REPORT)
  return exitCode

######################################################################
# Execute the specified test by sending the appropriate HTTP request
######################################################################
def manageStep(step):
  stepType = step.keys()[0]
  logging.debug("TEST:\tRunning step: %s" % stepType)
  logging.info(json.dumps(step, sort_keys=True, indent=4))

  stepData = step[stepType]

  methodToCall = getattr(directives, stepType)
  try:
    result = methodToCall(stepData)
    takeScreenShot()
    return PYSEL_OK, result
  except Exception, e:
    takeScreenShot("ERROR")
    return PYSEL_SEV5, e
  
######################################################################
# Once a URL has been generated - or otherwise ready - run the test
######################################################################
def executeTest(testName, testObject):
  testName = os.path.basename(testName)
  testSteps = testObject.get('steps')
  numSteps = len(testSteps)
  for currentStep in range(numSteps):
    drawProgress(currentStep, numSteps)

    step = testSteps[currentStep]
    status, output = manageStep(step)
    if (status != PYSEL_OK):
      logging.error("Error detected: %s" % output)
      raiseError("Error in Step %s. Sub-section of steps shown below:" % currentStep)
      displayTest(testObject, offset=currentStep-1, currentStep=currentStep, numSteps=3)
      currentStep = suggestContinue()
    else:
      currentStep = currentStep + 1
  drawProgress(currentStep, numSteps)
  
######################################################################
# Prompt Loop to interact with user
######################################################################
def createTest():
  global exitCode, IMPLICIT_WAIT

  exitCode = 0
  IMPLICIT_WAIT = 3
  initDriver()

  util_create.DRIVER = DRIVER
  util_create.TEST_BASE_DIR = DIR_TEST
  
  testObject = {"steps": []}
  
  choices = [
    "add", "import", 
    "exec", "review", 
    "save","quit"
  ]

  while True:
    os.system('clear')
    util_create._displayBanner("MAIN", Style.BRIGHT + Fore.GREEN)
    
    util_create._displayHelp("main")
    
    choice = util_create._promptChoice(choices)
    if not choice or choice == "quit":
      break
    methodToCall = getattr(util_create, "create_%s" % choice)
    try:
      testObject = methodToCall(testObject) 
    except Exception, e:
      raiseError("Error occured! Quitting", e)
      break
  
  quitDriver()
  return exitCode
