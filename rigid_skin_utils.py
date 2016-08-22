import pymel.core as pm
from PySide import QtGui, QtCore
import ast

import config

def returnCellTarget(table=None, cell=None):
	row = cell.row()
	targetCellData = table.item(row, 1).text()
	target = 'skinTarget_'+ str(targetCellData)
	return target

def returnSkinList(node=None, root=''):
	""" Return the objects for skinning """
	skinList = []
	nodeAttr = pm.listAttr(node, userDefined=True)

	for n in nodeAttr:
		# Continue if we find the root node
		if n == 'root':
			continue

		# objList is a list of all objects in the scene with the current search name
		# If we have mutiple of the same name then we must return the object under the correct root
		skinList.append(pm.getAttr(getattr(node, n)))
	return skinList

def checkForExistingObj(skinObjects=None, skinTarget=None, objectName=''):
	""" Checking that the object already exists or not in our attributes """
	if getExtraAttr(obj=skinTarget, attrName=config.rootAttr).split('|')[-1] == objectName:
		return 'root'
	existingObj = [obj for obj in skinObjects if obj.split('|')[-1] == objectName]
	if len(existingObj) < 1:
		return None
	else:
		return existingObj[0]

def returnTopParent(objArray=None):
	# Get First Parent
	parentList = []
	for obj in objArray:
		varA = pm.listRelatives(obj,p=True)

		# Loop All Parents  
		while(len(varA) > 0):
			varB = varA[0]
			varA = pm.listRelatives(varA[0],p=True)
		parentList.append(varB)

	# We are removing all duplicates
	parentList = list(set(parentList))

	# We cannot have more than one parent
	if len(parentList) > 1:
		return None
	else:
		return varB

def checkMatchingParents(objectParent, table, row):
	try:
		# If this fails then we must skip it and return False
		treeWidget = table.cellWidget(row, 0)
		treeRoot = treeWidget.topLevelItem(0)
	except:
		return False

	if objectParent != treeRoot.text(0):
		return True
	else:
		return False

def splitName(name, split, index):
	return name.split(split)[index]

def createSimpleMsgBox(text, table=None):
	#QtGui.QMessageBox.information(table, 'Information', text)
	msgBox = QtGui.QMessageBox()
	msgBox.setText(text)
	msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
	msgBox.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
	msgBox.exec_()

def createChoiceBox(text='', parent=None):
	msgBox = QtGui.QMessageBox()
	msgBox.setText(text)
	msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
	msgBox.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
	result = msgBox.exec_()
	if result == QtGui.QMessageBox.Yes:
		return 1
	else:
		return 0

def returnMayaObjects(searchTerm):
	return pm.ls(searchTerm)

def verifyTargetDestination(table, selectedMayaObjects):
	""" Does not allow the user to put the same object in any target twice """
	skinTargets = returnMayaObjects(config.targetConv+'*')
	for target in skinTargets:
		#root = getExtraAttr(obj=target, attrName='root')
		skinObjects = getExtraAttr(obj=target, attrName=config.skinObjectsAttr)
		if skinObjects:
			skinObjects = ast.literal_eval(skinObjects)

		for obj in selectedMayaObjects:
			match = [i for i in skinObjects if i.split('|')[-1] == obj.nodeName()]
			if len(match):
				return True, obj.nodeName()
	return False, None

def checkNonMeshObjs(selectedMayaObjs=None):
	if selectedMayaObjs is None:
		selectedMayaObjs = []

	for obj in selectedMayaObjs:
		objShape = pm.ls(sl=True)[0].getShape()
		if objShape:
			if pm.objectType(objShape) != 'mesh':
				return 0, obj.nodeName()
		else:
			return 0, obj.nodeName()
	return 1, None

def createTargetNode(name='', table=None):
	""" Creating a new target node """
	name = str(name.replace(' ', '_'))
	skinTargetNodes = returnMayaObjects(config.targetConv+'*')
	skinTargetName = config.targetConv+name

	for target in skinTargetNodes:
		if skinTargetName == target.nodeName() or name in pm.ls(type='transform'):
			createSimpleMsgBox('Target name already exists\nPlease use another name', table)
			return

	pm.createNode('group', name=skinTargetName)
	createTargetRow(table, name)
	config.rigidSkinDialog.updateLog(process='New Target node created: %s'%name)

def createTargetRow(table, contents=''):
	""" Creating a new target row with the target name """
	table.insertRow(table.rowCount())
	rowNum = table.rowCount()-1
	item = QtGui.QTableWidgetItem(contents)
	item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
	table.setItem(rowNum, 1, item)

def preMarkChecks(table, cell, selectedObjects):
	if len(selectedObjects) < 1:
		config.rigidSkinDialog.updateLog(process='Please select an object in your Maya Hierarchy', warning=True)
		return 0

	# Error with objects that have no root
	try:
		objectRoot = returnTopParent(selectedObjects)
	except:
		config.rigidSkinDialog.updateLog(process='You cannot target a top level object', warning=True)
		return 0

	# If there are 2 different roots then we cannot run the skinning process
	if objectRoot is None:
		config.rigidSkinDialog.updateLog(process='You cannot mark from 2 different roots', warning=True)
		return 0

	# Checking objects are not already targeted
	illegalObjects, illegalObj = verifyTargetDestination(table, selectedObjects)
	if illegalObjects == True:
		config.rigidSkinDialog.updateLog(process='Target object already targeted: %s'%illegalObj, warning=True)
		return 0

	nonMeshObjs, nonMesh = checkNonMeshObjs(selectedObjects)
	if nonMeshObjs == 0:
		config.rigidSkinDialog.updateLog(process='You have tried to target a non mesh obj: %s'%nonMesh, warning=True)
		return 0
	return objectRoot

def createListItem(text='', color=''):
	item = QtGui.QListWidgetItem(text)
	if color:
		#item.setTextColor(QtGui.QColor(color))
		setWidgetBackground(item=item, color=color)
	item.setSizeHint(QtCore.QSize(32,20))
	return item

def resizeListWidget(listWidget):
	rows = listWidget.count()
	rowSize = listWidget.sizeHintForRow(0)+2
	height = rows * rowSize
	if height > 250:
		height = 250
	listWidget.setFixedHeight(height)

def setWidgetBackground(item=None, color=''):
	color = QtGui.QColor(color)
	brush = QtGui.QBrush()
	brush.setColor(color)
	brush.setStyle(QtCore.Qt.Dense7Pattern)
	item.setBackground(brush)

def getExtraAttr(obj, attrName=''):
	""" Returns the extra attribute we need """
	obj = str(obj)
	try:
		attr = pm.getAttr('%s.%s' % (obj, attrName))
		return attr
	except:
		return ''

def addExtraAttr(obj, attrName, attrType):
	""" Try to get the attribute to check that it does not already exist """
	obj = str(obj)
	try:
		pm.getAttr('%s.%s' % (obj, attrName))
		return
	except:
		if attrType == 'string':
			pm.addAttr(obj, longName=attrName, dataType=attrType)
		else:
			pm.addAttr(obj, longName=attrName, at=attrType)

def setExtraAttr(obj, attrName, attrContent):
	""" Set the extra attribute to the data we want """
	obj = str(obj)
	pm.setAttr('%s.%s' % (obj, attrName), attrContent)

def selectFromMaya(selectedItems, targetNode):
	selectionList = []
	targetRoot = getTargetRoot(targetNode=targetNode)
	for s in selectedItems:
		sText = str(s.text()).strip()
		for item in ast.literal_eval(getExtraAttr(obj=targetNode, attrName=config.skinObjectsAttr)):
			if sText == item.split('|')[-1]:
				selectionList.append(targetRoot+item)
	try:
		pm.select(selectionList)
	except:
		return

def verifyTargetInfo(targetNodes=None):
	dupeRoots = []
	errorPackage = (0, None)
	if targetNodes is None:
		targetNodes = []

	for target in targetNodes:
		root = getTargetRoot(targetNode=target)
		if len(pm.ls(root)) == 0:
			return errorPackage
		dupeRoots.append(root)
		skinObjs = getExtraAttr(obj=target, attrName=config.skinObjectsAttr)
		if skinObjs:
			skinObjs = ast.literal_eval(skinObjs)

		for so in skinObjs:
			fullPath = root+so
			if len(pm.ls(fullPath)) == 0:
				return errorPackage
	dupeRoots = list(set(dupeRoots))
	return 1, dupeRoots

def getTargetRoot(targetNode):
	return getExtraAttr(obj=targetNode, attrName=config.rootAttr)
