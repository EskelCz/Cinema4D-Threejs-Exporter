import c4d
from c4d import documents


# walks the actual document to find and modify HyperNURBS objects   
def work(aEnabledState = 0, aSetEditor = False, aSetRender = False, aEditor = 2, aRender = 3, aInc = False):

	# get the active document and die if there is none
	doc = documents.GetActiveDocument()
	if doc is None: return False   

	# we are going to modify scene objects, so let's add an undo
	doc.StartUndo()
	# call the walker with the first object of the scene
	result = getObj(doc.GetFirstObject(), aEnabledState, aSetEditor, aSetRender, aEditor, aRender, aInc)
	# end the undo recording
	doc.EndUndo()

	# add an update event so the scene get's redrawn
	c4d.EventAdd()

	return result


# this will walk all objects on the same level as the given one and call
#itself recursively for any children
def getObj(aObj, aEnabledState = 0, aSetEditor = False, aSetRender = False, aEditor = 2, aRender = 3, aInc = False):

	foundOne = False

	# as long as the object is not None...
	while aObj:
		# check of there is a child and recurse...
		if aObj.GetDown() :
			foundOne = getObj(aObj.GetDown(), aEnabledState, aSetEditor, aSetRender, aEditor, aRender, aInc)

		# we found a HyperNURBS object!
		if aObj.CheckType(c4d.Osds):
			foundOne = True

			# in-/decrement the editor-subdevisions
			if aSetEditor:
				if not aInc:
					aObj[c4d.SDSOBJECT_SUBEDITOR_CM] = aEditor
				else:
					aObj[c4d.SDSOBJECT_SUBEDITOR_CM] += aEditor

			# in-/decrement the render-subdevisions
			if aSetRender:
				if not aInc:
					aObj[c4d.SDSOBJECT_SUBRAY_CM] = aRender
				else:
					aObj[c4d.SDSOBJECT_SUBRAY_CM] += aRender

			# set the generator state to off/on/flip
			if aEnabledState == 1:
				aObj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = False
				
			if aEnabledState == 2:
				aObj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = True
				
			if aEnabledState == 3:
				aObj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = not aObj[c4d.ID_BASEOBJECT_GENERATOR_FLAG]

		# ...and on to the next object...
		aObj = aObj.GetNext()

	return foundOne