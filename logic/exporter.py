# coding=UTF-8

import c4d
from c4d import documents

class ThreeJsWriter(object):

	def write(self, settings):
		self.settings = settings
		self.vertices = []
		self.faces = []
		self.normals = []
		self.uvs = []
		self.faceUVMap = defaultdict(list)
		self.bones = []
		self.animations = []
		self.skinIndices = []
		self.skinWeights = []
		self.jointKeyframeSummary = {}
		self.mesh = op.GetClone() # create a clone to work on
		self.fps = settings.fps
		self.minTime = doc.GetMinTime()
		self.maxTime = doc.GetMaxTime()
		self.firstFrame = self.minTime.GetFrame(self.fps)
		self.lastFrame = self.maxTime.GetFrame(self.fps)

		print 'Exporting object \'' + self.mesh.GetName() + ':'
		print ' '
		print '✓     Created an internal clone'

		# save current frame
		currentTime = doc.GetTime()
		self.currentFrame = currentTime.GetFrame(self.fps)

		if self.settings.triangulate == True:
			c4d.utils.SendModelingCommand(c4d.MCOMMAND_TRIANGULATE, [self.mesh])
			print '✓     Mesh triangulated'

		if self.settings.breakPhong == True:
			c4d.utils.SendModelingCommand(c4d.MCOMMAND_BREAKPHONG, [self.mesh])
			print '✓     Phong break done'

		if hasattr(self.settings, 'armature'):
			typeId = 1019362 # Joint
			self.allJoints = []
			FindObjects(self.settings.armature, typeId, self.allJoints)

		if hasattr(self.settings, 'bonesOn') and hasattr(self.settings, 'armature'):
			# reset to bind pose?
			self._exportBones()
			print '✓     Bones exported'

		if hasattr(self.settings, 'weightOn'):
			self._exportWeights()
			print "✓     Weights exported"

		self._exportMesh()

		if hasattr(self.settings, 'skeletalAnim') and hasattr(self.settings, 'armature'):
			self._exportKeyframeAnimations()
			print '✓     Exported keyframe animations'

		# return to original frame
		self._goToFrame(self.currentFrame)

		print ' '
		print 'Saving to: ', self.settings.path

		output = {
			'metadata': {
				'formatVersion': 3.1,
				'generatedBy': 'Cinema 4D Exporter'
			},

			'vertices': self.vertices,
			'uvs': [self.uvs],
			'faces': self.faces,
			'normals': self.normals,
		}

		if hasattr(self.settings, 'bonesOn') and hasattr(self.settings, 'armature'):
			output['bones'] = self.bones

		if hasattr(self.settings, 'weightOn'):
			output['skinIndices'] = self.skinIndices
			output['skinWeights'] = self.skinWeights
			output['influencesPerVertex'] = self.settings.influencesPerVertex

		if hasattr(self.settings, 'skeletalAnim'):
			output['animations'] = self.animations

		with file(self.settings.path, 'w') as f:
			if hasattr(self.settings, 'prettyOutput'):
				f.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
			else:
				f.write(json.dumps(output, separators=(",",":")))

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

	def _exportMesh(self):
		if hasattr(self.settings, 'vertices'):
			self._exportVertices()

		if hasattr(self.settings, 'faceNormals'):
			self._exportFaceNormals()
			print '✓     Face normals exported'

		if hasattr(self.settings, 'vertexNormals'):
			self._exportVertexNormals()
			print '✓     Vertex normals exported'

		if hasattr(self.settings, 'uvs'):
			self._exportFaceVertexUVs()
			print '✓     UVs exported'

		if hasattr(self.settings, 'faces'):
			self._exportFaces()
			print "✓     Faces exported"

	def _exportVertices(self):
		for vector in self.mesh.GetAllPoints():
			self.vertices += [round(vector.x, self.settings.floatPrecision)]
			self.vertices += [round(vector.y, self.settings.floatPrecision)]
			self.vertices += [round(vector.z, self.settings.floatPrecision)]

	def _exportFaceNormals(self):
		for p in self.mesh.GetAllPolygons():
			points = op.GetAllPoints()
			p1, p2, p4 = points[p.a], points[p.b], points[p.d]
			normal = (p2 - p1).Cross(p4 - p1).GetNormalized()

			# Again polygons are in different order than blender/maya
			self.normals.append(self._cleanFloat(normal.x))
			self.normals.append(self._cleanFloat(normal.y))
			self.normals.append(self._cleanFloat(normal.z))

	def _exportVertexNormals(self):
		for normal in self.mesh.CreatePhongNormals():
			if not self._isNull(normal):	# probably not good enough to separate quads
				self.normals += [round(normal.x, self.settings.floatPrecision), round(normal.y, self.settings.floatPrecision), round(normal.z, self.settings.floatPrecision)]

	def _exportFaceVertexUVs(self):
		uniqueUVs = []
		key = 0

		for p, face in enumerate(self.mesh.GetAllPolygons()):
			uv = self.settings.uvtag.GetSlow(p)

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
			if hasattr(self.settings, 'flipU'):
				u = 1 - uv.x
			else:
				u = uv.x
			if hasattr(self.settings, 'flipV'):
				v = 1 - uv.y
			else:
				v = uv.y
			self.uvs.append(round(u, self.settings.floatPrecision))
			self.uvs.append(round(v, self.settings.floatPrecision))

	def _exportFaces(self):

		uvs = []

		for index, face in enumerate(self.mesh.GetAllPolygons()):

			hasMaterial = False										# not interested
			hasFaceUvs = False 										# not supported in OBJ
			hasFaceVertexUvs = self.settings.uvs
			hasFaceNormals = self.settings.faceNormals
			hasFaceVertexNormals = self.settings.vertexNormals
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

			self.bones.append({
				"parent": parentIndex,
				"name": joint.GetName(),
				"pos": self._getPos(joint),
				"rotq": self._getRot(joint)
			})

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

	def _indexOfJoint(self, name):
		if not hasattr(self, '_jointNames'):
			self._jointNames = dict([(joint.GetName(), i) for i, joint in enumerate(self.allJoints)])

		if name in self._jointNames:
			return self._jointNames[name]
		else:
			return -1

	def _exportWeights(self):
		wtag = self.settings.weighttag
		maxInfluences = self.settings.influencesPerVertex
		jointCount = wtag.GetJointCount()
		vertexCount = self.mesh.GetPointCount()

		# Iterate vertices and display weight for each bone
		for vertexIndex in range(vertexCount):
			numWeights = 0
			for jointIndex in range(jointCount):
				joint  = wtag.GetJoint(jointIndex, doc)
				weight = wtag.GetWeight(jointIndex, vertexIndex)

				if weight > 0:
					self.skinWeights.append(weight)
					self.skinIndices.append(self._indexOfJoint(joint.GetName()))
					#self.skinIndices.append(jointIndex)
					numWeights += 1

			if numWeights > maxInfluences:
				print '?     Warning: More than ' + str(maxInfluences) + ' influences on vertex id ' + vertexIndex

			# append zeros (? shouldn't it be -1) for no bone id when there is no influence
			for i in range(0, maxInfluences - numWeights):
				self.skinWeights.append(0)
				self.skinIndices.append(0)

	def _exportKeyframeAnimations(self):
		hierarchy = []
		i = -1

		# CUT INTO MULTIPLE ANIMATIONS

		self._buildBoneKeyframeSummary()

		for joint in self.allJoints:
			hierarchy.append({
				"parent": i,
				"keys": self._getBoneKeyframeData(joint)
			})
			i += 1

		self.animations.append({
			"name": "AnimationName",
			"length": (self.maxTime - self.minTime).Get(),
			"fps": self.fps,
			"hierarchy": hierarchy
		})

	def _buildBoneKeyframeSummary(self):
		# iterate curves for each bone, add frames to ordered unique list
		for joint in self.allJoints:
			frames = []

			trackCount = len(joint.GetCTracks())
			print '  >     Joint ' + joint.GetName() + ' has ' + str(trackCount) + ' tracks'

			for track in joint.GetCTracks():
				curve = track.GetCurve()
				keyCount = curve.GetKeyCount()
				print '  >     Track ' + track.GetName() + ' has ' + str(keyCount) + ' keyframes'

				for keyIndex in range(keyCount):
					key = curve.GetKey(keyIndex)
					time = key.GetTime()
					frame = time.GetFrame(self.fps)
					frames.append(frame)

			self.jointKeyframeSummary[joint.GetGUID()] = sorted(set(frames))

	def _getBoneKeyframeData(self, joint):
		keys = []
		frames = self.jointKeyframeSummary[joint.GetGUID()]

		for frame in frames:
			self._goToFrame(frame)
			keys.append(self._getCurrentKeyframeData(joint, frame))
		
		if keys: return keys
		else: return False

	def _goToFrame(self, frame):
		time = c4d.BaseTime(frame, self.fps)
		doc.SetTime(time)
		doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_0) 	#try BUILDFLAGS_INTERNALRENDERER
		c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)						#update timeline

	def _getCurrentKeyframeData(self, joint, frame):
		# 2DO: Read scale

		if frame == self.lastFrame:
			lastFrameTrimProtection = 0.001
		else:
			lastFrameTrimProtection = 0

		return {
			'time': float(frame - self.firstFrame) / self.fps - lastFrameTrimProtection,
			'pos': self._getPos(joint),
			'rot': self._getRot(joint),
			'scl': [1,1,1]
		}

	def _roundPos(self, pos):
		return map(lambda x: round(x, self.settings.floatPrecision), [pos.x, pos.y, pos.z])

	def _roundQuat(self, rot):
		return map(lambda x: round(x, self.settings.floatPrecision), [rot.v.x, rot.v.y, rot.v.z, rot.w])

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
