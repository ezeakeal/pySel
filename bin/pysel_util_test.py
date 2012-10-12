#!/usr/bin/python
import sys, os, re, textwrap
sys.path.append( os.path.join(os.path.dirname(__file__), "../lib" ))

import pysel_core as core
import pysel_directives as directives
import traceback
import logging

try:
  import json
except ImportError:
  import simplejson as json

######################################################################
# Load the contents of a test file
######################################################################
def loadTestfile(testPath):
  logging.debug("LOAD:\tLoading test file %s" % testPath)
  if not os.path.exists(testPath):
    logging.error("ERROR:\tNo Test found at (%s)" % testPath)
    return False

  f = open(testPath, 'r')
  test = json.load(f)
  f.close()

  test = augment_import(test) # Include other tests

  return test

# ----------------------------------------------
# Augment content of test file with another test
# ----------------------------------------------
def augment_import(test_json):
  steps = test_json["steps"]
  stepIndex = 0
  for step in steps:
    step = steps[stepIndex]
    stepType = step.keys()[0]
    if (stepType == "import_test"):
      importName = os.path.join('import', step["import_test"]["name"])
      logging.debug("LOAD:\tAugmenting test at step (%s) with test (%s)" % (stepIndex, importName))
      del test_json["steps"][stepIndex]
      importPath = os.path.join(core.DIR_TEST, importName+'.'+core.EXT_TEST) 
      importTest_json = loadTestfile(importPath)
      if (not importTest_json):
        return test_json
      stepInserts = importTest_json["steps"]
      for stepInsert in reversed(stepInserts):
        test_json["steps"].insert(stepIndex, stepInsert)
    stepIndex = stepIndex + 1
  return test_json

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
    core.takeScreenShot()
    return core.PYSEL_OK, result
  except Exception, e:
    core.takeScreenShot("ERROR")
    return core.PYSEL_SEV5, e
  
######################################################################
# Once a URL has been generated - or otherwise ready - run the test
######################################################################
def executeTest(testName, testObject):
  testName = os.path.basename(testName)
  testSteps = testObject.get('steps')
  numSteps = len(testSteps)
  for currentStep in range(numSteps):
    core.drawProgress(currentStep, numSteps)

    step = testSteps[currentStep]
    status, output = manageStep(step)
    if (status != core.PYSEL_OK):
      logging.error("Error detected: %s" % output)
      core.raiseError("Error in Step %s. Sub-section of steps shown below:" % currentStep)
      core.displayTest(testObject, offset=currentStep-1, currentStep=currentStep, numSteps=3)
      currentStep = core.suggestContinue()
    else:
      currentStep = currentStep + 1
  core.drawProgress(currentStep, numSteps)