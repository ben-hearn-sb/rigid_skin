"""
	Rigid body skinning tool that allows the user to
"""
__author__ = 'Ben_Hearn'


import maya.mel as mel
mel.eval('source "namedCommandSetup.mel"')
import sys

try:
	reload(RS)
	reload(RSU)
	reload(config)
	reload(ProcessDialog)
except:
	pass

import pymel.core as pm
from PySide import QtCore, QtGui
import rigidbody_skinning_tool as RS
import rigid_skin_utils as RSU
import config
from rigid_skin_dialog import ProcessDialog
import traceback
import ast

class RigidSkin(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)

		#global skinningWindow
		self.resize(450, 600)
		self.setWindowTitle("Rigid Master")
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		
		# Master display is the table view that shows our 
		self.masterDisplay = QtGui.QTableWidget()
		self.masterDisplay.setColumnCount(2)
		self.masterDisplay.setHorizontalHeaderLabels(['Objects', 'Target Mesh'])
		width = self.masterDisplay.width()
		# Setting the stretch to expand with the table
		self.masterDisplay.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
		self.masterDisplay.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
		self.masterDisplay.verticalHeader().hide()
		#self.masterDisplay.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

		self.rigidSkinDialog    = ProcessDialog()
		config.rigidSkinDialog  = self.rigidSkinDialog
		self.rigidSkinDialog.setFixedHeight(100)

		buttonsGrid = QtGui.QGridLayout()

		# Parent of skinned object display
		parent       = QtGui.QLabel('Parent of selected')
		joint        = QtGui.QLabel()
		parentLayout = QtGui.QHBoxLayout()
		parentLayout.addWidget(parent)
		parentLayout.addWidget(joint)

		# Create target layout
		btnCreateTarget = QtGui.QPushButton('Create Target Mesh')
		btnDeleteTarget = QtGui.QPushButton('Delete Target Mesh')
		btnMark         = QtGui.QPushButton('Mark To Target')
		btnUnMark       = QtGui.QPushButton('Unmark From Target')
		btnRetarget     = QtGui.QPushButton('Retarget to selected root')
		btnSkin         = QtGui.QPushButton('Skin Selection')

		btnCreateTarget.setStyleSheet('QPushButton {background-color: white; color: black;}')
		btnDeleteTarget.setStyleSheet('background-color: red;')
		btnMark.setStyleSheet('QPushButton {background-color: lightBlue; color: black;}')
		btnUnMark.setStyleSheet('background-color: red;')
		btnSkin.setStyleSheet('background-color: green;')

		buttonsGrid.addWidget(btnCreateTarget, 0, 0)
		buttonsGrid.addWidget(btnDeleteTarget, 0, 1)
		buttonsGrid.addWidget(btnMark, 1, 0)
		buttonsGrid.addWidget(btnUnMark, 1, 1)
		buttonsGrid.addWidget(btnRetarget, 2, 0)
		buttonsGrid.addWidget(btnSkin, 2, 1)

		masterLayout = QtGui.QVBoxLayout()
		masterLayout.addWidget(self.masterDisplay)
		masterLayout.addLayout(parentLayout)
		masterLayout.addLayout(buttonsGrid)
		masterLayout.addWidget(self.rigidSkinDialog)

		self.setLayout(masterLayout)
		self.setupTargetRows(self.masterDisplay)

		# Class globals
		self.focusedWidget = None

		btnCreateTarget.clicked.connect	(lambda: self.createNewSkinTarget(self.masterDisplay))
		btnDeleteTarget.clicked.connect	(self.deleteSkinTarget)
		btnMark.clicked.connect			(lambda: self.markToTarget(self.masterDisplay, self.masterDisplay.currentItem()))
		btnUnMark.clicked.connect		(lambda: self.unMarkFromTarget(self.masterDisplay))
		btnRetarget.clicked.connect     (lambda: self.retargetRoot(cells=self.masterDisplay.selectedItems()))
		btnSkin.clicked.connect			(lambda: self.skinSelection(self.masterDisplay, self.masterDisplay.selectedItems()))

	def closeEvent(self, event):
		""" On close we are removing the Qt window from memory """
		self.deleteLater()
		event.accept()


	# Need to plug this in and debug
	def clearWidgetSelection(self):
		self.focusedWidget = QtGui.qApp.focusWidget()
		print 'our widget is', self.focusedWidget

	def createNewSkinTarget(self, table):
		""" Creates a new skin target node """
		global newDialog
		newDialog = QtGui.QDialog()
		newDialog.setWindowTitle("Enter Target Name")
		newDialog.resize(300, 25)
		newDialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		newDialog.setModal(True)

		layout = QtGui.QVBoxLayout()
		newName = QtGui.QLineEdit()
		layout.addWidget(newName)

		newDialog.setLayout(layout)
		newDialog.show()

		newName.returnPressed.connect(lambda: RSU.createTargetNode(newName.text(), table))
		newName.returnPressed.connect(newDialog.close)

	def refreshUI(self):
		for row in reversed(range(self.masterDisplay.rowCount())):
			self.masterDisplay.removeRow(row)
		self.setupTargetRows(table=self.masterDisplay)

	def setupTargetRows(self, table):
		""" Setting up our initial table """
		skinTargetNodes = RSU.returnMayaObjects('skinTarget_*')
		rowNum = -1
		for target in skinTargetNodes:
			rowNum += 1
			name = RSU.splitName(target.nodeName(),'skinTarget_', -1)
			RSU.createTargetRow(table, name)
			if len(pm.listAttr(target, userDefined=True)) > 0:
				self.createTree(target.nodeName(), table, rowNum)

	def refreshTreeWidget(self, table=None, row=0, node=None):
		""" Refreshing the tree widget in the specified cell """
		table.removeCellWidget(row, 0)
		self.createTree(node, table, row)

	def markToTarget(self, table, cell):
		""" Marks the selected objects in Maya to the target object """
		config.rigidSkinDialog.clearLog()
		matchRoots = False
		matchRootObjects = []

		if cell is None:
			return
		row = cell.row()
		target = RSU.returnCellTarget(table, cell)
		targetNode = pm.PyNode(target)
		selectedObjects = pm.ls(selection=True, type='transform')

		# We run our pre mark checks and get the root returned
		objectRoot = RSU.preMarkChecks(table=table, cell=cell, selectedObjects=selectedObjects)
		if objectRoot == 0:
			return

		rootAttr = RSU.getExtraAttr(obj=targetNode, attrName='root')
		if rootAttr == '':
			RSU.addExtraAttr(obj=targetNode, attrName='root', attrType='string')
			RSU.setExtraAttr(obj=targetNode, attrName='root', attrContent=objectRoot)

		skinAttrName = config.skinObjectsAttr
		skinObjectsList = RSU.getExtraAttr(obj=targetNode, attrName=skinAttrName)
		if skinObjectsList == '':
			pm.addAttr(targetNode, ln=skinAttrName, dt='string')
			skinObjectsList = []
		else:
			skinObjectsList = ast.literal_eval(skinObjectsList)

		for i in selectedObjects:
			try:
				try:
					matchRoots = RSU.checkMatchingParents(objectRoot, table, row)
				except:
					traceback.print_exc(file=sys.stdout)
					pass
				if matchRoots == True:
					matchRootObjects.append(i)
					continue

				skinObjectsList.append(i.fullPath().split(objectRoot.nodeName())[-1])
				self.rigidSkinDialog.updateLog(process='Marking to target: %s'%i.nodeName())
			except:
				print '\nERROR IN SETTING ATTR\n'
				traceback.print_exc(file=sys.stdout)

		skinObjectsList = list(set(skinObjectsList))
		RSU.setExtraAttr(obj=targetNode, attrName=config.skinObjectsAttr, attrContent=str(skinObjectsList))

		if len(matchRootObjects) > 0:
			RSU.createSimpleMsgBox('You tried to mark objects from a different root\nThey have been ignored and are printed in the console', table)
			print matchRootObjects

		self.refreshTreeWidget(table, row, targetNode)

	# TODO: You cant unmark from 2 seprate skin target nodes at once
	def unMarkFromTarget(self, table):
		""" Unmarks selected tree widget items from the node and the tree """
		tree = QtGui.qApp.focusWidget()
		if type(tree) is not QtGui.QListWidget:
			print 'Cannot unmark non list item'
			return

		for i in range(table.rowCount()):
			if table.cellWidget(i, 0) == tree:
				row = i
				break

		nodeName = 'skinTarget_'+table.item(row, 1).text()
		skinTargetNode = pm.PyNode(nodeName)
		nodeAttrs =  pm.listAttr(skinTargetNode, userDefined=True)

		selectedRows = []
		selectedItems = tree.selectedItems()
		skinObjects = ast.literal_eval(RSU.getExtraAttr(obj=skinTargetNode, attrName=config.skinObjectsAttr))
		for item in selectedItems:
			itemText = str(item.text()).strip()
			currentItemRow = tree.row(item)
			selectedRows.append(currentItemRow)

			existingObj = RSU.checkForExistingObj(skinObjects=skinObjects,skinTarget=skinTargetNode, objectName=itemText)

			# If the user has selected the root then delete all the attr from the node
			if existingObj == 'root':
				for obj in nodeAttrs:
					pm.deleteAttr(skinTargetNode, at=obj)
				table.removeCellWidget(row, 0)
				table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
				self.rigidSkinDialog.updateLog(process='Unmarked Root object: %s'%itemText, warning=True)
				return

			if existingObj is not None:
				skinObjects.remove(existingObj)
				table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
			self.rigidSkinDialog.updateLog(process='Unmarked node: %s'%itemText)

		RSU.setExtraAttr(obj=skinTargetNode, attrName=config.skinObjectsAttr, attrContent=str(skinObjects))
		for rowId in reversed(selectedRows):
			tree.takeItem(rowId)

	def createTree(self, node, table, row):
		node = pm.PyNode(node)
		color = ''
		try:
			root = pm.getAttr(node.root)
		except:
			return

		# If the root does not exist i.e. has been renamed or deleted we clean up and remove the faulty nodes
		if len(pm.ls(root)) < 1:
			color = 'orange'

		tree = QtGui.QListWidget()
		tree.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		treeRoot = RSU.createListItem(root, color=color)
		tree.addItem(treeRoot)

		skinObjects = RSU.getExtraAttr(obj=node, attrName=config.skinObjectsAttr)
		try:
			skinObjects = ast.literal_eval(skinObjects)
		except:
			return 0

		for obj in skinObjects:
			skinObject = obj.split('|')[-1]
			skinListObject = RSU.createListItem('    '+skinObject, color=color)
			if not len(pm.ls(root+obj)):
				#skinListObject.setTextColor(QtGui.QColor('orange'))
				RSU.setWidgetBackground(item=skinListObject, color='orange')
			tree.addItem(skinListObject)

		RSU.resizeListWidget(listWidget=tree)
		tree.itemSelectionChanged.connect(lambda: RSU.selectFromMaya(selectedItems=tree.selectedItems(), targetNode=node))
		table.setCellWidget(row, 0, tree)
		table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

	def skinSelection(self, table=None, cells=None):
		targetRows = []
		targetNodes = []
		duplicate = 0
		config.rigidSkinDialog.clearLog()
		if len(cells) == 0:
			config.rigidSkinDialog.updateLog(process='No cells selected to skin', warning=True)
			return
		# We need to go through each cell and gather each root to ask the user if they want to back up the original
		for cell in cells:
			target = RSU.returnCellTarget(table, cell)
			targetNodes.append(pm.PyNode(target))
			targetRows.append(cell.row())

		config.rigidSkinDialog.updateLog(process='Verifying selected target info')
		result, roots = RSU.verifyTargetInfo(targetNodes=targetNodes)

		if result == 0:
			config.rigidSkinDialog.updateLog(process='Some objects in your target nodes no longer exist. Please fix!', error=True)
			self.refreshUI()
			return 0

		# Here we ask if
		roots = list(set(roots))
		if len(roots):
			unDuped = []
			for r in roots:
				if not len(pm.ls(r+config.rootSkinConv)):
					unDuped.append(r)

			if len(unDuped):
				duplicate = RSU.createChoiceBox(text='Would you like to backup your roots?')
				if duplicate == 1:
					for r in unDuped:
						pm.duplicate(r, n=r+config.rootSkinConv, ic=True, un=True, st=True)
			else:
				# We need to set this flag so that the target node is re-targetd to the unskinned version of the mesh
				duplicate = 1

		for targetNode in targetNodes:
			config.rigidSkinDialog.updateLog(process='Gathering info for %s' %targetNode.nodeName())
			targetName = targetNode.nodeName().split('skinTarget_')[-1]
			root = RSU.getExtraAttr(obj=targetNode, attrName=config.rootAttr)
			try:
				fullPathSkinObjs = []
				skinObjects = ast.literal_eval(RSU.getExtraAttr(obj=targetNode, attrName=config.skinObjectsAttr))
				for o in skinObjects:
					skinObj = root+o
					fullPathSkinObjs.append(skinObj)
			except:
				continue

			sourceObjects, jointsVerts, numVerts = RS.gatherVertexPositions(fullPathSkinObjs)
			if len(sourceObjects) > 1:
				objectToSkin = RS.combineAndName(sourceObjects, targetName, root)
			else:
				objectToSkin = sourceObjects
			RS.skinObject(jointVertPos=jointsVerts, objectToSkin=objectToSkin, numOfVerts=numVerts)

		targetNodes = list(set(targetNodes)) # Remove dupes
		self.deleteSkinTarget(targetRows=targetRows, targetNodes=targetNodes, duplicate=duplicate)
		config.rigidSkinDialog.updateLog(process='Skin Successful', success=True)

	# TODO: Fix this to work with the button
	def deleteSkinTarget(self, targetRows=None, targetNodes=None, duplicate=0):
		""" Delete the currently selected skin target nodes """
		if targetRows and targetNodes:
			if not duplicate:
				for rowId in reversed(sorted(targetRows)):
					self.masterDisplay.removeRow(rowId)
			for node in targetNodes:
				if duplicate:
					# We need to retarget our nodes to the new duplicated root name
					rootName = RSU.getExtraAttr(obj=node, attrName=config.rootAttr)
					RSU.setExtraAttr(obj=node, attrName=config.rootAttr, attrContent=rootName+config.rootSkinConv)
				else:
					pm.delete(node)
			if duplicate:
				self.refreshUI()
		else:
			targetRows = []
			targetNodes = []
			for cell in self.masterDisplay.selectedItems():
				target = RSU.returnCellTarget(self.masterDisplay, cell)
				targetNode = pm.PyNode(target)
				targetRows.append(cell.row())
				targetNodes.append(targetNode)
			self.deleteSkinTarget(targetRows=targetRows, targetNodes=targetNodes)

	def retargetRoot(self, cells=None):
		config.rigidSkinDialog.clearLog()
		targetNodes = []
		if len(cells) == 0:
			return

		for cell in cells:
			target = RSU.returnCellTarget(table=self.masterDisplay, cell=cell)
			targetNodes.append(pm.PyNode(target))
		selectedRoot = pm.ls(sl=True)
		if len(selectedRoot) > 1:
			config.rigidSkinDialog.updateLog(process='You cannot retarget to more than one root', warning=True)
			return
		elif len(selectedRoot) < 1:
			config.rigidSkinDialog.updateLog(process='Please select a root from your Maya Hierarchy to retarget to', warning=True)
			return
		else:
			selectedRoot = selectedRoot[0]
		if len(pm.listRelatives(selectedRoot, p=True)) > 0:
			config.rigidSkinDialog.updateLog(process='Object selected is not top level root', warning=True)
		else:
			rootName = selectedRoot.nodeName()
			for target in targetNodes:
				RSU.setExtraAttr(obj=target, attrName=config.rootAttr, attrContent=rootName)
		self.refreshUI()

def main():
	winName = 'RIGID_MASTER'
	if pm.windows.window(winName, exists=True):
		print 'Window already exists'
		return
	global myWindow
	myWindow = RigidSkin()
	myWindow.setObjectName(winName)
	myWindow.show()