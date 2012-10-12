#!/usr/bin/python
import os, re, sys, time, datetime, pwd, grp
import socket, httplib, urllib2
import logging
import texttable as tt
from colorama import Fore, Back, Style
from time import strftime as date

try:
  import json
except ImportError:
  import simplejson as json

######################################################################
# Create directory structure for file if folders are missing
######################################################################
def mkdir(path):
  if not os.path.isdir(path):
    logging.warning("OS:\tCreating Directory (%s) " % path)
    os.makedirs(path)

  os.chown(path, UID, GID)

def clearDirectory(path, recursive=False):
  if not os.path.isdir(path):
    logging.warning("OS:\tDirectory does not exist (%s) " % path)
    return
  for delObj in os.listdir(path):
    delPath = os.path.join(path, delObj)
    try:
        if (not recursive):
          if os.path.isfile(delPath):
            os.unlink(delPath)
        else:
          os.unlink(delPath)
    except Exception, e:
      raiseError("Error deleting files!", e)

######################################################################
# Baby function to draw progress bar given a max and current value
######################################################################
def drawProgress(current, maxNum):
  barWidth = int(int((os.popen('stty size', 'r').read().split())[1]) - 25)
  countComplete = int(current*barWidth/maxNum)
  countIdle = int(barWidth-countComplete)
  progressBar = '[' + ('#'*countComplete) + ('-'*countIdle) + ']'
  sys.stdout.write("\rStep: (%i/%i) %s" % (current, maxNum, progressBar))
  sys.stdout.flush()

######################################################################
# Display the steps in a test, indicating what ones have been completed optionally
######################################################################
def displayTest(testObject, offset=0, currentStep=0, numSteps=None):
  testSteps = testObject.get('steps')
  tab = tt.Texttable(max_width=1000)
  headerRow = ["#", "Command", "Value", "Parent", "Selector"]
  tab.header(headerRow)
  
  if numSteps:
    numSteps = offset + numSteps
  testSteps=testSteps[offset:numSteps]

  stepNum=offset
  for step in testSteps:
    row = []
    row.append(stepNum+1)

    step_com = step.keys()[0]
    stepData = step[step_com]
    step_val = stepData["value"] if "value" in stepData.keys() else ""
    step_pnt = json.dumps(stepData["parent"]) if "parent" in stepData.keys() else ""
    step_str = json.dumps(stepData["selector"]) if "selector" in stepData.keys() else ""

    row.append(step_com)
    row.append(step_val)
    row.append(step_pnt)
    row.append(step_str)
    tab.add_row(row)
    stepNum = stepNum + 1
  print Style.BRIGHT + Fore.CYAN + tab.draw() + Style.RESET_ALL

#---------------------------------------------------------------------
# Get a list of available tests
#---------------------------------------------------------------------
def getTestList(testDir):
  testList=[]
  for root, subFolders, files in os.walk(testDir):
    for f in files:
      f = os.path.join(root,f)
      if f.endswith('.json'):
        testList.append(f)
  return testList

#---------------------------------------------------------------------
# Draw a table of available test names
#---------------------------------------------------------------------
def drawTestTable(testList):
  tab = tt.Texttable(max_width=1000)
  headerRow = ["#", "TestName", "StepCount"]
  tab.header(headerRow)

  for index, f in enumerate(testList):
    try:
      row = []
      numSteps = "NA"
      with open(f, 'r') as testFile:
        testJson = json.load(testFile)
        numSteps = len(testJson['steps'])
      row.append(index+1)
      row.append(f)
      row.append(numSteps)
      tab.add_row(row)
    except Exception, e:
      logging.error("Error reading json file: (%s): %s" % (f, e))
  print Fore.BLUE + tab.draw() + Style.RESET_ALL


######################################################################
# Load the contents of a test file
######################################################################
def loadTestfile(testPath):
  logging.debug("LOAD:\tLoading test file %s" % testPath)
  if not os.path.exists(testPath):
    logging.error("ERROR:\tNo Test found at (%s)" % testPath)
    return False

  f = open(testPath, 'r')
  testData = json.load(f)
  f.close()

  basePath = os.path.dirname(testPath)
  testData = augment_import(testData, basePath) # Include other tests

  return testData

# ----------------------------------------------
# Augment content of test file with another test
# ----------------------------------------------
def augment_import(test_json, basePath):
  steps = test_json["steps"]
  stepIndex = 0
  for step in steps:
    step = steps[stepIndex]
    stepType = step.keys()[0]
    if (stepType == "import_test"):
      importRelPath = step["import_test"]["name"]
      logging.debug("LOAD:\tAugmenting test at step (%s) with test (%s)" % (stepIndex, importRelPath))
      del test_json["steps"][stepIndex]
      importPath = os.path.join(basePath, importRelPath) 
      importTest_json = loadTestfile(importPath)
      if (not importTest_json):
        return test_json
      stepInserts = importTest_json["steps"]
      for stepInsert in reversed(stepInserts):
        test_json["steps"].insert(stepIndex, stepInsert)
    stepIndex = stepIndex + 1
  return test_json
