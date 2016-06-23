# coding=UTF-8

import c4d

from c4d import documents
from logic import ids
from logic import exporter

class MainDialog(c4d.gui.GeDialog):

	VERSION = '0.0.3'

	# called once when the dialog is initialized
	def __init__(self):

		# kill the menu-bar
		self.AddGadget(c4d.DIALOG_NOMENUBAR, ids.MAINDIALOG);

	# called when the dialog is opened - load or generate the GUI here
	def CreateLayout(self):

		self.uvtag = None
		self.weighttag = None
		self.armatures = {}
		self.doc = documents.GetActiveDocument()
		self.op  = self.doc.GetActiveObject()

		# load and parse the dialog layout from the resource file
		dialog = self.LoadDialogResource(ids.MAINDIALOG, None, flags= c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT )
		instruction = 'Choose what to export for the selected object `' + self.op.GetName() + '`'

		# dynamic dialog changes
		self.SetString(ids.INSTRUCTION, instruction)
		self.SetTitle('Three.js exporter v.' + self.VERSION)

		# find markers
		self.markers = []
		curMarker = c4d.documents.GetFirstMarker(self.doc)
		while curMarker is not None:
			self.markers.append(curMarker)
			curMarker = curMarker.GetNext()
		self.markers.sort(key=self._getMarkerSecond)

		# find bones
		for i, obj in enumerate(self.doc.GetObjects()):
			if obj.GetType() == 1019362: # Joint
				self.armatures[i] = obj.GetGUID()
				self.AddChild(ids.BONESELECT, i, obj.GetName())

		# find UV and Weight tag
		for tag in self.op.GetTags():
			tagName = tag.GetName()
			if tagName == 'UVW' or tagName == 'UVTex':
				self.uvtag = tag
			if tagName == 'Weight':
				self.weighttag = tag

		return dialog

	# called after 'CreateLayout()' - used to initialize the GUI elements
	#and reset values
	def InitValues(self): 

		# set values
		fps = self.doc.GetFps()
		self.minFrame = self.doc.GetLoopMinTime().GetFrame(fps)
		self.maxFrame = self.doc.GetLoopMaxTime().GetFrame(fps)
		self.SetInt32(ids.PRECISION, 6)
		self.SetBool(ids.PRETTY, True)
		self.SetBool(ids.TRIANGULATE, True)
		self.SetBool(ids.VERTICES, True)
		self.SetBool(ids.FACES, True)
		self.SetBool(ids.NORMALS, True)
		self.SetInt32(ids.NORMALSELECT, ids.NORMALSVERTEX)
		self.SetBool(ids.UVS, True)
		self.SetBool(ids.FLIPV, True)
		self.SetBool(ids.BONES, True)
		self.SetBool(ids.WEIGHTS, True)
		self.SetBool(ids.SKANIM, True)
		self.SetInt32(ids.INFLUENCES, 2)
		self.SetInt32(ids.FPS, fps)
		self.SetBool(ids.POS, True)
		self.SetBool(ids.ROT, True)
		self.SetInt32(ids.MINFRAME, self.minFrame)
		self.SetInt32(ids.MAXFRAME, self.maxFrame)
		self.SetBool(ids.MARKERS, True)

		# disable animations if no bones found
		if not self.armatures:
			self.ToggleAnimation(False)
			print '?     Warning: Joints not found'

		# disable UV if no tag found
		if self.GetBool(ids.UVS) and self.uvtag is None:
			self.ToggleUV(False)
			print '?     Warning: UV tag not found'

		# disable weight if no tag found
		if self.GetBool(ids.WEIGHTS) and self.weighttag is None:
			self.ToggleWeight(False)
			print '?     Warning: Weight tag not found'

		# disable markers if no markers found
		if self.GetBool(ids.MARKERS) and not self.markers:
			self.Enable(ids.MARKERS, False)
			self.SetBool(ids.MARKERS, False)
			print '?     Warning: No markers found'

		return True

	def ToggleWeight(self, value):
		self.SetBool(ids.WEIGHTS, value)
		self.Enable(ids.WEIGHTS, value)
		self.Enable(ids.INFLUENCESLABEL, value)
		self.Enable(ids.INFLUENCES, value)

	def ToggleUV(self, value):
		self.SetBool(ids.UVS, value)
		self.SetBool(ids.FLIPV, value)
		self.Enable(ids.UVS, value)
		self.Enable(ids.FLIPU, value)
		self.Enable(ids.FLIPV, value)

	def ToggleAnimation(self, value):
		self.SetBool(ids.BONES, value)
		self.SetBool(ids.SKANIM, value)
		self.Enable(ids.BONES, value)
		self.Enable(ids.SKANIM, value)
		self.Enable(ids.BONESELECT, value)
		self.Enable(ids.INFLUENCESLABEL, value)
		self.Enable(ids.INFLUENCES, value)
		self.Enable(ids.FPSLABEL, value)
		self.Enable(ids.FPS, value)
		self.Enable(ids.POS, value)
		self.Enable(ids.ROT, value)
		self.Enable(ids.SCL, value)
		self.SetBool(ids.POS, value)
		self.SetBool(ids.ROT, value)
		self.SetBool(ids.SCL, value)
		self.Enable(ids.MARKERS, value)
		self.SetBool(ids.MARKERS, value)
		self.Enable(ids.MINFRAME, value)
		self.Enable(ids.MINFRAME, value)
		self.Enable(ids.MAXFRAMELABEL, value)
		self.Enable(ids.MAXFRAMELABEL, value)

	def _getMarkerSecond(self, marker):
		if marker is None:
			return None
		return marker[c4d.TLMARKER_TIME].Get()

	# called on every GUI-interaction - check the 'id' against those of
	#your GUI elements
	def Command(self, id, msg):

		# normals
		if(self.GetBool(ids.NORMALS) == False):
			self.Enable(ids.NORMALSELECT, False)
		else:
			self.Enable(ids.NORMALSELECT, True)

		# UVs
		if(self.GetBool(ids.UVS) == False):
			self.Enable(ids.FLIPU, False)
			self.Enable(ids.FLIPV, False)
		else:
			self.Enable(ids.FLIPU, True)
			self.Enable(ids.FLIPV, True)

		# bones
		if(self.GetBool(ids.BONES) == False):
			self.Enable(ids.BONESELECT, False)
		else:
			self.Enable(ids.BONESELECT, True)

		# weights
		if(self.GetBool(ids.WEIGHTS) == False):
			self.Enable(ids.INFLUENCES, False)
			self.Enable(ids.POS, False)
			self.Enable(ids.ROT, False)
			self.Enable(ids.SCL, False)
		else:
			self.Enable(ids.INFLUENCES, True)
			self.Enable(ids.POS, True)
			self.Enable(ids.ROT, True)
			self.Enable(ids.SCL, True)

		# animations
		if(self.GetBool(ids.SKANIM) == False):
			self.Enable(ids.FPS, False)
			self.Enable(ids.POS, False)
			self.Enable(ids.ROT, False)
			self.Enable(ids.SCL, False)
		else:
			self.Enable(ids.FPS, True)
			self.Enable(ids.POS, True)
			self.Enable(ids.ROT, True)
			self.Enable(ids.SCL, True)

		# "Ok"
		if id == 1:   

			# Save file
			self.folder = self.doc.GetDocumentPath()

			if self.GetBool(ids.DESTINATION) == True or self.folder == '':
				self.path = c4d.storage.LoadDialog(title="Save File for JSON Export", flags=c4d.FILESELECT_SAVE, force_suffix="json")
				if self.path == None:
					c4d.gui.MessageDialog('Canceled: 	✘ Please specify an output folder')
					return False
			else:
				self.path = self.folder + '/' + self.doc.GetDocumentName().replace('.c4d', '') + '.json'

			writer = exporter.ThreeJsWriter()
			writer.write(self)

			self.Close()

		# "Cancel"
		if id == 2:
			# just close the dialog - this will call 'AskClose()' first (see bottom)
			self.Close()

		return True
