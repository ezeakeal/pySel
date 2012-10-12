#!/usr/bin/python
import sys, os, re, textwrap
sys.path.append( os.path.join(os.path.dirname(__file__), "../lib" ))

import pysel_directives as directives

import traceback
import logging
import readline

import texttable as tt
from colorama import Fore, Back, Style

import pysel_util_core    as util_core

try:
  import json
except ImportError:
  import simplejson as json

############ GLOBALS #################
DRIVER        =None
TEST_BASE_DIR =None
############ INITIAL #################
readline.parse_and_bind("tab: complete")

######################################################################
# Display help for various sections of the interface
######################################################################
def _displayHelp(section, colorCode=("%s" % Fore.MAGENTA + Style.BRIGHT)):
  print colorCode
  if section == "main":
    print "------------------------------------------------------------------------"
    print "%10s: Add a step to the test (navigate to a url, type a string, click an element)" % "add"
    print "%10s: Import a range of steps from an existing test file" % "import"
    print "%10s: Execute a range of steps from the current test" % "exec"
    print "%10s: View and optionally delete elements from the current test" % "review"
    print "%10s: Save the current test to disk" % "save"
    print "------------------------------------------------------------------------"
  if section == "add":
    print "------------------------------------------------------------------------"
    print "%13s: Set the value of a typeKeys (text to type) or navigate (which URL to go to) operation" % "set_Value"
    print "%13s: Set the DOM element to type in or click on" % "set_Selector"
    print "%13s: Set the DOM element to search within when locating the selector" % "set_Parent"
    print "%13s: Add this step to the current test" % "commit"
    print "------------------------------------------------------------------------"
  if section == "create":
    print "------------------------------------------------------------------------"
    print "Please specify a selector type and selector value to identify the DOM element to perform an action on"
    print "Multiple selectors can be combined to make a more robust selector"
    print Style.BRIGHT + "You will see a warning if multiple elements are returned from a selector, if so, use multiple selectors or use a better selector" + Style.RESET_ALL + colorCode
    print "------------------------------------------------------------------------"
  if section == "import":
    print "------------------------------------------------------------------------"
    print "%10s: Opens a test file to import test steps from" % "open"
    print "%10s: Reduces the steps in 'Import Data' to a specific range for importing sections of a test only" % "setRange"
    print "%10s: Insert the steps within 'Import Data' at a specific point in the current test" % "importData"
    print "------------------------------------------------------------------------"
  if section == "review":
    print "------------------------------------------------------------------------"
    print "%10s: Delete a step from the test data" % "delete"
    print "%10s: Save the modified test data" % "commit"
    print "------------------------------------------------------------------------"

  print Style.RESET_ALL
######################################################################
# Display a Banner to help user interface
######################################################################
def _displayBanner(bannerText, colorCode):
  bannerLength = 32
  offset= int((bannerLength/2) - (len(bannerText)/2))
  print colorCode
  print "#"*bannerLength
  print " "*offset + bannerText
  print "#"*bannerLength,
  print Style.RESET_ALL

######################################################################
# Create a Step for the testObject
######################################################################
def _promptChoice(choices, hide=False, lType="Action"):
  completer = Completer(choices + ["cancel"])
  readline.set_completer(completer.complete)

  if not hide:
    print ("\n%s List" % lType).upper()
    print "-----------------"
    for choice in choices:
      print "- %s" % choice
    print "-----------------"
    print "- cancel"
    print "-----------------"
      
  choice = ""
  while choice not in (choices):
    choice = raw_input("Enter %s: " % lType)
    if choice == "cancel":
      return False
  return choice

######################################################################
# Create a Selector
######################################################################
def _createSelector():
  selector = {}
  os.system('clear')
  _displayBanner("Create Selector", Fore.YELLOW)
  _displayHelp("create")
  while True:
    choices = ["id", "link_text", "name", "tag_name", "class_name", "css_selector", "text"]
    choice = _promptChoice(choices, lType="Selector Type")
    if not choice:
      return None
    value = raw_input("Enter Selector(%s) Value: " % choice)
    selector[choice] = value

    print "Current Selector: %s" % selector
    print "Searching for element...",
    try:
      elements = directives._getObject(DRIVER, selector, 3)
      print Style.BRIGHT + Fore.GREEN + "Element Found!" + Style.RESET_ALL
    
    except Exception, e:
      print Style.BRIGHT + Fore.RED + "Element Not Found! Aborting Selector Creation." + Style.RESET_ALL
      raw_input("Continue..")
      return None

    print ""
    choice = ""
    while choice not in ["a", "s", "c"]:
      choice = raw_input(Style.BRIGHT + "Select: (A)ppend," + Fore.GREEN + " (S)ubmit," + Fore.RESET + " (C)ancel >> [s]" + Style.RESET_ALL).lower()
      if len(choice) == 0:
        choice = "s"
    if choice == "s":
      return selector
    if choice == "c":
      return None

######################################################################
# Test a Step
######################################################################
def _execStep(step):
  print Fore.YELLOW + "Executing Step.." + Style.RESET_ALL
  stepType = step.keys()[0]
  stepData = step[stepType]
  methodToCall = getattr(directives, stepType)
  try:
    result = methodToCall(stepData)
    return result
  except Exception, e:
    return e

######################################################################
# Draws a Step
######################################################################
def _drawStep(action, value, parent, selector):
  tab = tt.Texttable(max_width=1000)
  headerRow = ["Command", "Value", "Parent", "Selector"]
  tab.header(headerRow)
  
  row = []
  row.append(action)
  row.append(value)
  row.append(parent)
  row.append(selector)
  tab.add_row(row)

  print Style.BRIGHT + Fore.CYAN + tab.draw() + Style.RESET_ALL

######################################################################
# Create a Step for the testObject
######################################################################
def _createStep():
  selector = {}
  parent = None
  action = None
  value = None

  os.system('clear')
  _displayBanner("ADD STEP", Style.BRIGHT + Fore.GREEN)
  _displayHelp("add")
  actions = ["navigateUrl", "typeKeys", "click"]
  action = _promptChoice(actions, lType="Test Action")
  if not action:
    return False
  
  choices = ["commit"]
  if action in ["navigateUrl", "typeKeys"]:
    choices.append("set_Value")
  if action in ["typeKeys", "click"]:
    choices = choices + ["set_Selector", "set_Parent"]
  
  if "set_Value" in choices: # Set value before being prompted to help make this more fluid
    print "Set the value of typeKeys (text to type) or navigate (which URL to go to)"
    value = raw_input("Enter Value for (%s): " % action)
  if "set_Selector" in choices: # Set value before being prompted to help make this more fluid
    selector = _createSelector()
    
  while True:
    os.system('clear')
    _displayBanner("ADD STEP", Style.BRIGHT + Fore.GREEN)
    _displayHelp("add")

    print "\nCurrent Step:"
    _drawStep(action, value, parent, selector)

    choice = _promptChoice(choices)
    if not choice or choice == "cancel":
      return None

    if choice == "set_Value":
      value = raw_input("Enter Value for (%s): " % action)
    elif choice == "set_Selector":
      selector = _createSelector()
    elif choice == "set_Parent":
      parent = _createSelector()
     
    elif choice == "commit":
      step = { action : {} }
      if parent:
        step[action]["parent"] = parent
      step[action]["selector"] = selector
      step[action]["value"] = value
      _execStep(step)
      return step

######################################################################
# Add a step to the test
######################################################################
def create_add(testObject):
  step = _createStep()
  if step:
    testObject["steps"].append(step)
  return testObject

######################################################################
# Insert a step to the test
######################################################################
def create_exec(testObject):
  execObject = testObject
  
  os.system('clear')
  _displayBanner("EXEC", Style.BRIGHT + Fore.RED)

  print "\nCurrent Test:"
  util_core.displayTest(testObject)

  print "\nPlease Enter the Range of Steps to execute:"
  startIndex = max(int(raw_input("Enter number of first step: "))-1, 0)
  endIndex = min(int(raw_input("Enter number of last step: ")), len(testObject["steps"]))
  numSteps = endIndex - startIndex 
  execObject["steps"] = testObject["steps"][startIndex:numSteps]

  os.system('clear')
  _displayBanner("EXEC", Style.BRIGHT + Fore.RED)
  print "\nCurrent Test:"
  util_core.displayTest(execObject)

  choices = ["execute"]
  choice = _promptChoice(choices)
  
  testSteps = testObject.get('steps')
  if choice and choice == "execute":
    for step in testSteps:
      status = _execStep(step)

  return testObject

######################################################################
# Insert a step to the test
######################################################################
def create_import(testObject):
  defaultObject = testObject
  importData    = {"steps": []}
  while True:
    os.system('clear')
    _displayBanner("IMPORT", Style.BRIGHT + Fore.BLUE)
    _displayHelp("import")
    print "\nCurrent Import Data:"
    util_core.displayTest(importData)

    choices = ["open", "setRange", "importData"]
    choice = _promptChoice(choices)

    if not choice:
      return defaultObject
    # OPEN: display available files for import
    if choice == "open":
      testList = util_core.getTestList(TEST_BASE_DIR)
      util_core.drawTestTable(testList)
      testIndex = int(raw_input("Enter Number of test to import: "))-1
      print Fore.YELLOW + "Loading Test.." + Style.RESET_ALL
      try:
        testPath = testList[testIndex]
        importData = util_core.loadTestfile(testPath)
      except Exception, e:
        raiseError("Error loading test", e)
    
    # SETRANGE: Prunes the steps of importData to the range specified
    if choice == "setRange":

      startIndex = max(int(raw_input("Enter number of first step to include (start step): "))-1, 0)
      endIndex = min(int(raw_input("Enter number of last step to include (end step): ")), len(importData["steps"]))
      numSteps = endIndex - startIndex 
      importData["steps"] = importData["steps"][startIndex:numSteps]
    
    # IMPORTDATA: Imports the test above or below a particular test number
    if choice == "importData":
      os.system("clear")
      _displayBanner("IMPORT", Style.BRIGHT + Fore.BLUE)
      
      print "\nCurrent Test:"
      util_core.displayTest(testObject)
      print "\nCurrent Import Data:"
      util_core.displayTest(importData)
      
      posChoices = ["before", "after"]
      choice = _promptChoice(posChoices, lType="Insert_Position")

      if choice:
        try:
          importIndex = int(raw_input("Enter Index to insert import data %s: " % choice))
          if choice == "before":
            importIndex = max(importIndex - 1, 0)
          stepInserts = importData["steps"]
          for stepInsert in reversed(stepInserts):
            testObject["steps"].insert(importIndex, stepInsert)
          os.system("clear")
          _displayBanner("IMPORT", Style.BRIGHT + Fore.BLUE)
          print Fore.GREEN + "Import Successful!"
          print "\nCurrent Test:"
          util_core.displayTest(testObject)
          comChoices = ["commit"]
          comChoice = _promptChoice(comChoices)
          if comChoice and comChoice == "commit":
            return testObject
        except Exception, e:
          raiseError("Error importing test!", e)

    if choice =="commit":
      return testObject

######################################################################
# Insert a step to the test
######################################################################
def create_review(testObject):
  defaultObject = testObject
  while True:
    os.system('clear')
    _displayBanner("REVIEW", Style.BRIGHT + Fore.CYAN)
    _displayHelp("review")

    print "\nCurrent Test:"
    util_core.displayTest(testObject)
    choices = ["delete", "commit"]
    choice = _promptChoice(choices)

    if not choice:
      return defaultObject
    if choice == "commit":
      return testObject
    if choice == "delete":
      stepDel = int(raw_input("Enter Step to Delete: "))-1
      try:
        del testObject["steps"][stepDel]
      except Exception, e:
        raiseError("Error deleteing step (%s)" % stepDel, e)
    
######################################################################
# Insert a step to the test
######################################################################
def create_save(testObject):
  os.system('clear')
  _displayBanner("SAVE", Style.BRIGHT + Fore.BLUE)
  
  test_path = ""
  while True:
    test_path = raw_input("Full Path of Save: ")
    dirOfTest = os.path.dirname(test_path)
    if os.path.exists(dirOfTest):
      break
    else:
      print "Directory (%s) does not exist." % dirOfTest

  if not test_path.endswith('.json'):
    test_path = "%s.json" % test_path

  try:
    testText = json.dumps(testObject, indent=2)
    testFile = open(test_path, 'w')
    testFile.write(testText)
    testFile.close()
    print Fore.GREEN + "Success!" + Style.RESET_ALL
    raw_input("Continue..")

  except Exception, e:
    raiseError("Error saving file!", e)
  return testObject

######################################################################
# Raise an Error in the manner which you are acustomed to
######################################################################
def raiseError(strext, data=None):
  print Fore.RED + "\nError: %s " % strext
  if data:
    print Fore.CYAN + json.dumps(data, sort_keys=True, indent=4)

######################################################################
# Raise a Warning for the craic
######################################################################
def raiseWarning(strext, data=None):
  print Fore.YELLOW + "\nWarning: %s " % strext
  if data:
    print Fore.CYAN + json.dumps(data, sort_keys=True, indent=4)

# ------------------------------------------
# Class for autocompletion
# ------------------------------------------
class Completer:
  def __init__(self, words):
    self.words = words
    self.prefix = None

  def complete(self, prefix, index):
    if prefix != self.prefix:
      self.matching_words = [w for w in self.words if w.startswith(prefix)]
      self.prefix = prefix
    else:
      pass                
    try:
      return self.matching_words[index]
    except IndexError:
      return None