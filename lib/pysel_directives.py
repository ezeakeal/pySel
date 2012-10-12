#!/usr/bin/python

import pysel_core as core
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import logging

import os, re, textwrap, time

try:
  import json
except ImportError:
  import simplejson as json

######################################################################
# Returns list of common objects between two lists using '_id'
######################################################################
def _common_elements(list1, list2):
  commonList = []
  for se1 in list1:
    se1_id = se1._id
    for se2 in list2:
      se2_id = se2._id
      if se2_id == se1_id:
        commonList.append(se1)      
  return commonList

def _clickable(element_list):
  return_list = []
  for element in element_list:
    if (element.is_enabled() and element.is_displayed()):
      return_list.append(element)
  return return_list

######################################################################
# Returns an object from a parent selector (can be driver)
######################################################################
def _getObject(parent, selectorObject, timeout=0):
  foundObject = None

  selectorKeys = selectorObject.keys()
  primarySelectors = []

  if timeout == 0:
    timeout = core.IMPLICIT_WAIT
  
  # Iterate over selectorKeys narrowing down a list of primarySelectors until there is exactly 1 element (ideally)
  for selKey in selectorKeys:
    selectorList = []
    selVal = selectorObject[selKey]
    logging.debug("Finding object by  %s: %s" % (selKey, selVal))

    # If the selector Key is 'text', make the necessary adjustments to do an identical search using xpath (only way)
    if (selKey == "text"):
      selKey = "xpath"
      selVal = "//*[contains(.,'%s')]" % selVal

    # Determine the desired methodName
    methodName = "find_elements_by_%s" % selKey
    if (methodName in dir(parent)): # Ensure methodName exists
      locationMethod = getattr(parent, methodName) # Retrieve method
      wait = WebDriverWait(core.DRIVER, timeout) # Create a webDriver wait
      selectorList = wait.until(lambda d: _clickable(locationMethod(selVal))) # Return a refined selection of elements containing those which are visible and enabled
    

    # Display IDs of selectors available during this iteration
    logging.debug("Available Selectors for (%s: %s)" % (selKey, selVal))
    for se in selectorList:
      logging.debug("Available Selector (%s) ID (%s)" % (se, se._id))

    # If primary selectors are still empty, set it to the results of the first scan
    if len(primarySelectors) == 0: 
      primarySelectors = selectorList
    else:
      # Otherwise, merge the two lists using the auto-generated ID for each element ('_id')
      primarySelectors = _common_elements(selectorList, primarySelectors)
    
    # Displays IDs of selectors currently on the primary Stack - this has to be reduced to 1 for safe testing.
    logging.debug("Current Selectors for (%s: %s)" % (selKey, selVal))
    for se in primarySelectors:
      logging.debug("Primary Selector(s) (%s) ID (%s)" % (se, se._id))

    if len(primarySelectors) == 1: # if there is only one element found break out of loop
      break

  # Raise Error if empty selectors
  if len(primarySelectors) == 0:
    core.raiseError("No Selectors found", selectorObject)
  # Return the primary selector if only one left
  if len(primarySelectors) == 1:
    return primarySelectors[0]
  # If we somehow have more than 1 selector, attempt to continue while selecting the first, but raise a warning
  if len(primarySelectors) > 1:
    core.raiseWarning("Multiple Selectors found", selectorObject)
    return primarySelectors[0]

######################################################################
# Navigate to a page
######################################################################
def navigateUrl(stepData):
  driver = core.DRIVER
  url = stepData['value']
  logging.debug("TEST:\tnavigateUrl\t%s" % url)
  driver.get(url)

######################################################################
# Send keys to object
######################################################################
def typeKeys(stepData):
  selector = stepData["selector"]
  keyValue = stepData["value"]
  parent = core.DRIVER

  logging.debug("TEST:\ttyping\t%s" % keyValue)

  if "parent" in stepData.keys():
    parent = _getObject(parent, stepData["parent"])

  webObject = _getObject(parent, selector)
  webObject.send_keys(keyValue)

######################################################################
# Click on Object
######################################################################
def click(stepData):
  selector = stepData["selector"]
  parent = core.DRIVER

  logging.debug("TEST:\tclicking\t")

  if "parent" in stepData.keys():
    parent = _getObject(parent, stepData["parent"])

  webObject = _getObject(parent, selector)
  
  driver = core.DRIVER
  elem_visible = WebDriverWait(driver, core.IMPLICIT_WAIT).until(lambda driver : webObject.is_displayed()) 
  
  webObject.click()
  time.sleep(0.1)

######################################################################
# Validate Element Exists
######################################################################
def assertElement(stepData):
  logging.debug("TEST:\t Assert Element \t")

  parent = core.DRIVER
  if "parent" in stepData.keys():
    parent = _getObject(parent, stepData["parent"])

  selector = stepData["selector"]
  webObject = _getObject(parent, selector)

  if webObject:
    return True
  else:
    core.raiseWarning("Assertion Failed. No element found!", stepData)
  
######################################################################
# Validate Element Does Not Exist
######################################################################
def assertNoElement(stepData):
  logging.debug("TEST:\t Assert No Element \t")

  parent = core.DRIVER
  if "parent" in stepData.keys():
    parent = _getObject(parent, stepData["parent"])

  selector = stepData["selector"]
  webObject = _getObject(parent, selector)

  if webObject:
    core.raiseWarning("Assertion Failed. Element found!", stepData)
  else:
    return True