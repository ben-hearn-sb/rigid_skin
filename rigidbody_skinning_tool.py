import pymel.core as pm
import maya.mel as mel

progressBarVar = -1
placeholders = []

def freezeTranforms(obj):
	pm.xform(obj, piv = (0, 0, 0), ws = True)
	pm.makeIdentity(obj, a = True, t = True, r = True, s = True)

#returns a dictionary with {joint: name, [vert positions]}
def gatherVertexPositions(sourceObj):
	skinObjects = []
	jointsVerts = []
	numOfVerts = -1

	# Need to use range so we can keep track of which array index to place things in

	for obj in sourceObj:           # iterate through the objects in the array
		freezeTranforms(obj)
		parent = pm.listRelatives(obj, p=True)   # Get the parent joint of the object being iterated over
		parent = parent[0].fullPath()
		node = pm.PyNode(obj)

		vertIndices = pm.polyEvaluate(node, v=True)
		print 'Vert indices', node, vertIndices

		tempDict = [parent, vertIndices]
		jointsVerts.append(tempDict)
		skinObjects.append(obj)

		# We place locators to get around the maya bug of joint deletion if empty
		parentNode = pm.listRelatives(obj, p=True)
		pm.spaceLocator()
		pm.parent(pm.ls(sl=True), parentNode)
		placeholders.append(pm.ls(sl=True))

	return skinObjects, jointsVerts, numOfVerts

def combineAndName(skinObjects, target,  root):
	targetNode = pm.polyUnite(skinObjects, n=target, ch = False)
	targetNode = pm.parent(targetNode, root)
	pm.xform(targetNode, piv=(0, 0, 0), ws = True) # Have to set pivot to 0 otherwise our animations wont work correctly
	pm.makeIdentity(targetNode, a = True, t = True, r = True, s = True) # freeze the transforms
	return targetNode[0]

def skinObject(jointVertPos, objectToSkin, numOfVerts):
	""" This function skins the object
	 	We are selecting the verts in order of their combination then skinning the selection """
	print "Skinning function entered"
	jointCluster = []
	transformCluster =[]

	for joint in jointVertPos:
		if pm.objectType(joint[0])== 'joint':
			jointCluster.append(joint[0])
		else:
			transformCluster.append(joint[0])

	jointCluster        = list(set(jointCluster))
	transformCluster    = list(set(transformCluster))

	# If we do not have a joint cluster we may have only a transform cluster so we must account for this
	if len(jointCluster):
		pm.skinCluster(jointCluster, objectToSkin, tsb=True) # Skin the object (i) to the joints (stored in joints[0, 1, 2 etc.])
		for tr in transformCluster:
			pm.skinCluster(objectToSkin, edit=True, ai=tr)
	else:
		pm.skinCluster(transformCluster, objectToSkin, tst=True)
	skinClusterName = mel.eval('findRelatedSkinCluster ' + objectToSkin)
	myNode = pm.PyNode(objectToSkin)

	pm.select(cl = True)
	vertIndexStart = 0
	for myJoint in jointVertPos:
		vertIndexEnd = vertIndexStart+myJoint[1] # Get the vert index to end at. As we run through each object we need to add the current index with the new count

		# Try to select the verts
		try:
			pm.select(myNode.vtx[vertIndexStart:vertIndexEnd])
		except IndexError:
			# If we get an index error we have tried to select one to many verts, -1 to fix this
			vertIndexEnd -= 1
			pm.select(myNode.vtx[vertIndexStart:vertIndexEnd])

		vertIndexStart = vertIndexEnd

		pm.skinPercent(skinClusterName, transformValue=[(myJoint[0]), 1])
		pm.select(cl = True)

	# Legacy stuff....no harm in keeping, it seems to work if no errors
	for p in placeholders:
		try:
			pm.delete(p)
		except:
			print 'Failed to delete placeholder'