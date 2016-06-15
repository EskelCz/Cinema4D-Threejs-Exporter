# coding=UTF-8

import sys
import os.path
import json
import shutil
import c4d
import math
import ctypes

from logic import ids
from collections import defaultdict, OrderedDict
from c4d import documents, UVWTag, storage, plugins, gui, modules, bitmaps, utils
from c4d.utils import *

class ThreeJsWriter(object):

	vertices = []
	faces = []
	normals = []
	uvs = []
	faceUVMap = defaultdict(list)
	output = OrderedDict()
	bones = []
	markers = []
	skinIndices = []
	skinWeights = []
	influences = 0
	animations = []
	jointKeyframeSummary = {}

	def write(self, dialog):

		self.dialog = dialog
		self.doc = documents.GetActiveDocument()
		self.op  = self.doc.GetActiveObject()
		self.mesh = self.op.GetClone() # create a clone to work on
		self.fps = self.dialog.GetInt32(ids.FPS)
		self.minTime = self.doc.GetMinTime()
		self.maxTime = self.doc.GetMaxTime()
		self.firstFrame = self.minTime.GetFrame(self.fps)
		self.lastFrame = self.maxTime.GetFrame(self.fps)
		currentTime = self.doc.GetTime()
		self.currentFrame = currentTime.GetFrame(self.fps)
		self.floatPrecision = self.dialog.GetInt32(ids.PRECISION)

		print 'Exporting object \'' + self.mesh.GetName() + ':'
		print '\n✓     Created an internal clone'

		self.output['metadata'] = {
			'formatVersion': 3.1,
			'generatedBy': 'Cinema 4D Exporter ' + self.dialog.VERSION
		}

		# Mesh export
		if self.dialog.GetBool(ids.TRIANGULATE) == True:
			c4d.utils.SendModelingCommand(c4d.MCOMMAND_TRIANGULATE, [self.mesh])
			print '✓     Mesh triangulated'

		if self.dialog.GetBool(ids.PHONG) == True:
			c4d.utils.SendModelingCommand(c4d.MCOMMAND_BREAKPHONG, [self.mesh])
			print '✓     Phong break done'

		if self.dialog.GetBool(ids.VERTICES):
			self._exportVertices()
			if self.vertices: self.output['vertices'] = self.vertices
			print '✓     Vertices exported'

		if self.dialog.GetBool(ids.NORMALSFACE):
			self._exportFaceNormals()
			if self.normals: self.output['normals'] = self.normals
			print '✓     Face normals exported'

		if self.dialog.GetBool(ids.NORMALSVERTEX):
			self._exportVertexNormals()
			if self.normals: self.output['normals'] = self.normals
			print '✓     Vertex normals exported'

		if self.dialog.GetBool(ids.UVS):
			for tag in self.mesh.GetTags():
				tagName = tag.GetName()
				if tagName == 'UVW' or tagName == 'UVTex':
					uvtag = tag
			if uvtag:
				self._exportFaceVertexUVs(uvtag)
				if self.uvs: self.output['uvs'] = [self.uvs]
				print '✓     UVs exported'

		if self.dialog.GetBool(ids.FACES):
			self._exportFaces()
			if self.faces: self.output['faces'] = self.faces
			print "✓     Faces exported"

		# Bones
		self.bonesOn = self.dialog.GetBool(ids.BONES)
		if self.bonesOn:
			bonesGUID = self.dialog.armatures[self.dialog.GetInt32(ids.BONESELECT)]
			for obj in self.doc.GetObjects():
				if obj.GetGUID() == bonesGUID:
					self.armature = obj

			if self.armature:
				typeId = 1019362 # Joint
				self.allJoints = []
				FindObjects(self.armature, typeId, self.allJoints)
				self._exportBones()
				if self.bones: self.output['bones'] = self.bones
				print '✓     Bones exported'

		# Weights
		if self.dialog.GetBool(ids.WEIGHTS):
			for tag in self.mesh.GetTags():
				tagName = tag.GetName()
				if tagName == 'Weight':
					weighttag = tag
			if weighttag:
				self.influences = self.dialog.GetInt32(ids.INFLUENCES)
				self._exportWeights(weighttag, self.influences)
				if self.influences: self.output['influencesPerVertex'] = self.influences
				if self.skinIndices: self.output['skinIndices'] = self.skinIndices
				if self.skinWeights: self.output['skinWeights'] = self.skinWeights
				print '✓     Weights exported'

		# Animations
		if self.dialog.GetBool(ids.SKANIM) and self.armature:
			self._buildJointKeyframeSummary()
			self._buildMarkerSummary()
			self._exportKeyframeAnimations()
			if self.animations: self.output['animations'] = self.animations
			print '✓     Exported keyframe animations'

		# Save
		print '\nSaving to: ', self.dialog.path
		with file(self.dialog.path, 'w') as f:
			if self.dialog.GetBool(ids.PRETTY):
				f.write(json.dumps(self.output, indent=4, separators=(',', ': ')))
			else:
				f.write(json.dumps(self.output, separators=(",",":")))

		# Return to original frame
		self._goToFrame(self.currentFrame)


	"""
	HELPER METHODS
	"""

	def _cleanFloat(self, num):
		return float(('%f' % num).rstrip('0').rstrip('.'))

	def _getVertexCount(self, face):
		if face.IsTriangle():
			return 3
		else:
			return 4

	def _getVertices(self, face):
		if face.IsTriangle():
			return [face.a, face.b, face.c]
		else:
			return [face.a, face.b, face.c, face.d]

	def _setBit(self, value, position, on):
		if on:
			mask = 1 << position
			return (value | mask)
		else:
			mask = ~(1 << position)
			return (value & mask)

	def _isNull(self, vector):
		if vector.x == 0 and vector.y == 0 and vector.z == 0:
			return True
		else:
			return False

	"""
	EXPORT METHODS
	"""

	def _exportVertices(self):
		for vector in self.mesh.GetAllPoints():
			self.vertices += [round(vector.x, self.floatPrecision)]
			self.vertices += [round(vector.y, self.floatPrecision)]
			self.vertices += [round(vector.z, self.floatPrecision)]

	def _exportFaceNormals(self):
		for p in self.mesh.GetAllPolygons():
			points = self.mesh.GetAllPoints()
			p1, p2, p4 = points[p.a], points[p.b], points[p.d]
			normal = (p2 - p1).Cross(p4 - p1).GetNormalized()

			# Again polygons are in different order than blender/maya
			self.normals.append(self._cleanFloat(normal.x))
			self.normals.append(self._cleanFloat(normal.y))
			self.normals.append(self._cleanFloat(normal.z))

	def _exportVertexNormals(self):
		for normal in self.mesh.CreatePhongNormals():
			if not self._isNull(normal):	# probably not good enough to separate quads
				self.normals += [round(normal.x, self.floatPrecision), round(normal.y, self.floatPrecision), round(normal.z, self.floatPrecision)]

	def _exportFaceVertexUVs(self, uvtag):
		uniqueUVs = []
		key = 0

		for p, face in enumerate(self.mesh.GetAllPolygons()):
			uv = uvtag.GetSlow(p)

			# if the face is quad, use D vertice as well
			if face.IsTriangle(): 	vecList = ['a', 'b', 'c']
			else: 					vecList = ['c', 'd', 'a', 'b']

			for vec in vecList:
				vector = uv[vec]
				if vector in uniqueUVs:						# indice found
					index = uniqueUVs.index(vector)			# get key of the vertice
					self.faceUVMap[p].append(index) 		# save it
				else:
					uniqueUVs.append(vector) 				# save new indice to uniqueUVs
					self.faceUVMap[p].append(key) 			# save key
					key += 1

		for index, uv in enumerate(uniqueUVs):
			if self.dialog.GetBool(ids.FLIPU):
				u = 1 - uv.x
			else:
				u = uv.x
			if self.dialog.GetBool(ids.FLIPV):
				v = 1 - uv.y
			else:
				v = uv.y
			self.uvs.append(round(u, self.floatPrecision))
			self.uvs.append(round(v, self.floatPrecision))

	def _exportFaces(self):

		# Depends on faceUVMap
		uvs = []

		for index, face in enumerate(self.mesh.GetAllPolygons()):

			hasMaterial = False										# not interested
			hasFaceUvs = False 										# not supported in OBJ
			hasFaceVertexUvs = self.dialog.GetBool(ids.UVS)
			hasFaceNormals = self.dialog.GetBool(ids.NORMALSFACE)
			hasFaceVertexNormals = self.dialog.GetBool(ids.NORMALSVERTEX)
			hasFaceColors = False 									# not interested
			hasFaceVertexColors = False 							# not supported in OBJ

			faceType = 0
			faceType = self._setBit(faceType, 0, not face.IsTriangle())
			faceType = self._setBit(faceType, 1, hasMaterial)
			faceType = self._setBit(faceType, 2, hasFaceUvs)
			faceType = self._setBit(faceType, 3, hasFaceVertexUvs)
			faceType = self._setBit(faceType, 4, hasFaceNormals)
			faceType = self._setBit(faceType, 5, hasFaceVertexNormals)
			faceType = self._setBit(faceType, 6, hasFaceColors)
			faceType = self._setBit(faceType, 7, hasFaceVertexColors)

			faceData = []
			faceData.append(faceType)

			# must clamp in case on polygons bigger than quads
			nVertices = self._getVertexCount(face) # is it triangle or quad

			# add face vertices
			faceData.append(face.a)
			faceData.append(face.b)
			faceData.append(face.c)
			if nVertices == 4:
				faceData.append(face.d)

			if hasMaterial:
				faceData.append(0) # face['material']

			if hasFaceVertexUvs and self.faceUVMap:
				for key in self.faceUVMap[index]:
					faceData.append(key)

			if hasFaceNormals:
				faceData.append(index)

			if hasFaceVertexNormals:
				for i in xrange(nVertices):
					faceData.append(index * nVertices + i)

			self.faces += faceData

	def _exportBones(self):

		# go to the first frame of animation
		self._goToFrame(self.firstFrame)

		# cycle joints to capture PRS values
		for joint in self.allJoints:
			if joint.GetUp():
				parentIndex = self._indexOfJoint(joint.GetUp().GetName())
			else:
				parentIndex = -1

			initialPRS = {
				"parent": parentIndex,
				"name": joint.GetName()
			}

			if self.dialog.GetBool(ids.POS):
				initialPRS["pos"] = self._getPos(joint)

			if self.dialog.GetBool(ids.ROT):
				initialPRS["rotq"] = self._getRot(joint)

			if self.dialog.GetBool(ids.SCL):
				initialPRS["scl"] = self._getScl(joint)

			self.bones.append(initialPRS)

	def _getPos(self, obj):
		#locRelPos = joint.GetRelPos()
		#locAbsPos = joint.GetAbsPos()
		globPos = obj.GetMg().off
		return self._roundPos(globPos)

	def _getRot(self, obj):
		#rotq = joint.getRotation(quaternion=True) * joint.getOrientation()
		rot = obj.GetRelRot()
		rotq = c4d.Quaternion()
		rotq.SetHPB(rot)
		return self._roundQuat(rotq)

	def _getScl(self, obj):
		scl = obj.GetRelScale()
		return self._roundScl(scl)

	def _indexOfJoint(self, name):
		if not hasattr(self, '_jointNames'):
			self._jointNames = dict([(joint.GetName(), i) for i, joint in enumerate(self.allJoints)])

		if name in self._jointNames:
			return self._jointNames[name]
		else:
			return -1

	def _exportWeights(self, weighttag, influences):
		jointCount = weighttag.GetJointCount()
		vertexCount = self.mesh.GetPointCount()

		# Iterate vertices and display weight for each bone
		for vertexIndex in range(vertexCount):
			numWeights = 0
			for jointIndex in range(jointCount):
				joint  = weighttag.GetJoint(jointIndex, self.doc)
				weight = weighttag.GetWeight(jointIndex, vertexIndex)

				if weight > 0:
					self.skinWeights.append(weight)
					self.skinIndices.append(self._indexOfJoint(joint.GetName()))
					#self.skinIndices.append(jointIndex)
					numWeights += 1

			if numWeights > influences:
				print '?     Warning: More than ' + str(influences) + ' influences on vertex id ' + str(vertexIndex)

			# append zeros (? shouldn't it be -1) for no bone id when there is no influence
			for i in range(0, influences - numWeights):
				self.skinWeights.append(0)
				self.skinIndices.append(0)

	def _getMarkerSecond(self, marker):
		if marker is None:
			return None
		return marker[c4d.TLMARKER_TIME].Get()

	def _buildMarkerSummary(self):
		self.markers = []
		curMarker = c4d.documents.GetFirstMarker(self.doc)
		while curMarker is not None:
			self.markers.append(curMarker)
			curMarker = curMarker.GetNext()

		self.markers.sort(key=self._getMarkerSecond)

	def _buildJointKeyframeSummary(self):
		self.jointKeyframeSummary = {}
		# iterate curves for each bone, add frames to ordered unique list
		for joint in self.allJoints:
			frames = []

			trackCount = len(joint.GetCTracks())
			print '  >     Joint ' + joint.GetName() + ' has ' + str(trackCount) + ' tracks'

			for track in joint.GetCTracks():
				curve = track.GetCurve()
				keyCount = curve.GetKeyCount()
				print '  >          Track ' + track.GetName() + ' has ' + str(keyCount) + ' keyframes'

				for keyIndex in range(keyCount):
					key = curve.GetKey(keyIndex)
					time = key.GetTime()
					frame = time.GetFrame(self.fps)
					frames.append(frame)

			self.jointKeyframeSummary[joint.GetGUID()] = sorted(set(frames))

	def _exportKeyframeAnimations(self):
		if self.markers:
			print '✓     ' + str(len(self.markers)) + ' markers found, segmenting animation'
			i = 0
			for marker in self.markers:
				start = marker[c4d.TLMARKER_TIME]
				nextIndex = i + 1
				if nextIndex < len(self.markers):
					nextMarker = self.markers[nextIndex]
					oneFrame = c4d.BaseTime(1, self.fps)
					end = nextMarker[c4d.TLMARKER_TIME] - oneFrame
				else:
					end = self.maxTime

				self._addKeyframeAnimation(marker.GetName(), start, end)
				i += 1

		else:
			print '✓     No markers found, making single animation'
			self._addKeyframeAnimation('Animation', self.minTime, self.maxTime)

	def _addKeyframeAnimation(self, name, startTime, endTime):
		hierarchy = []
		i = -1
		for joint in self.allJoints:
			if self.jointKeyframeSummary[joint.GetGUID()]:
				hierarchy.append({
					"parent": i,
					"keys": self._getBoneKeyframeData(joint, name, startTime.GetFrame(self.fps), endTime.GetFrame(self.fps))
				})
				i += 1

		self.animations.append({
			"name": name,
			"length": (endTime - startTime).Get(),
			"fps": self.fps,
			"hierarchy": hierarchy
		})

	def _getBoneKeyframeData(self, joint, name, startFrame, endFrame):

		# 2DO: only export frames in between startFrame and endFrame
		# clean up (comments)
		# test if current document timeline range has effect on this. if so, expand it and then return

		keys = []
		frames = self.jointKeyframeSummary[joint.GetGUID()]

		if not(startFrame in frames):
				print '?     Warning: No keyframe at the start of marker ' + name + ' for joint ' + joint.GetName()
		if not(endFrame in frames):
				print '?     Warning: No keyframe at the end of marker ' + name + ' for joint ' + joint.GetName()

		for frame in frames:
			#print frame > 0, 20, 21, 40
			self._goToFrame(frame)
			keys.append(self._getCurrentKeyframeData(joint, frame))
		
		if keys: return keys
		else: return False

	def _goToFrame(self, frame):
		time = c4d.BaseTime(frame, self.fps)
		self.doc.SetTime(time)
		self.doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_0) 	#try BUILDFLAGS_INTERNALRENDERER
		c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)						#update timeline

	def _getCurrentKeyframeData(self, joint, frame):
		if frame == self.lastFrame:
			lastFrameTrimProtection = 0.001
		else:
			lastFrameTrimProtection = 0

		keyframe = {
			'time': float(frame - self.firstFrame) / self.fps - lastFrameTrimProtection,
		}

		if self.dialog.GetBool(ids.POS):
			keyframe["pos"] = self._getPos(joint)

		if self.dialog.GetBool(ids.ROT):
			keyframe["rot"] = self._getRot(joint)

		if self.dialog.GetBool(ids.SCL):
			keyframe["scl"] = self._getScl(joint)

		return keyframe

	def _roundPos(self, pos):
		return map(lambda x: round(x, self.floatPrecision), [pos.x, pos.y, pos.z])

	def _roundScl(self, scl):
		return map(lambda x: round(x, self.floatPrecision), [scl.x, scl.y, scl.z])

	def _roundQuat(self, rot):
		return map(lambda x: round(x, self.floatPrecision), [rot.v.x, rot.v.y, rot.v.z, rot.w])

def FindObjects(obj, typeId, collection):
	if obj.CheckType(typeId):
		collection.append(obj)
	for child in obj.GetChildren():
		FindObjects(child, typeId, collection)
	return collection

def GetGlobalPosition(obj):
	return obj.GetMg().off

def GetGlobalRotation(obj):
	return utils.MatrixToHPB(obj.GetMg())

def GetGlobalScale(obj):
	m = obj.GetMg()
	return c4d.Vector(  m.v1.GetLength(),
						m.v2.GetLength(),
						m.v3.GetLength())

def LocalToGlobal(obj, local_pos):
	#Returns a point in local coordinate in global space.
	obj_mg = obj.GetMg()
	return obj_mg * local_pos
 
def GlobalToLocal(obj, global_pos):
	#Returns a point in global coordinate in local space.
	obj_mg = obj.GetMg()
	return ~obj_mg * global_pos
