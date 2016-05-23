import c4d

from c4d import documents
from logic import ids
from logic import exporter

class MainDialog(c4d.gui.GeDialog):

	VERSION = '0.0.1'

	uvtag = None
	weighttag = None
	armatures = {}

	# called once when the dialog is initialized
	def __init__(self):

		# kill the menu-bar
		self.AddGadget(c4d.DIALOG_NOMENUBAR, ids.MAINDIALOG);

	# called when the dialog is opened - load or generate the GUI here
	def CreateLayout(self):

		self.doc = documents.GetActiveDocument()
		self.op  = self.doc.GetActiveObject()

		# load and parse the dialog layout from the resource file
		dialog = self.LoadDialogResource(ids.MAINDIALOG, None, flags= c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT )
		instruction = 'Choose what to export for the selected object `' + self.op.GetName() + '`'

		# dynamic dialog changes
		self.SetString(ids.INSTRUCTION, instruction)
		self.SetTitle('Three.js exporter v.' + self.VERSION)

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
		self.SetString(ids.PRECISION, 6)
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
		self.SetString(ids.INFLUENCES, 2)
		self.SetString(ids.FPS, 30)

		# disable animations if no bones found
		if len(self.armatures) == 0:
			self.ToggleAnimation(False)
			print '?     Warning: Joints not found'

		# disable UV if no tag found
		if hasattr(self, 'uvtag') and self.uvtag is None:
			self.ToggleUV(False)
			print '?     Warning: UV tag not found'

		# disable weight if no tag found
		if hasattr(self, 'weighttag') and self.weighttag is None:
			self.ToggleWeight(False)
			print '?     Warning: Weight tag not found'

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


	# called on every GUI-interaction - check the 'id' against those of
	#your GUI elements
	def Command(self, id, msg):
			  
		# "Ok"
		if id == 1:   
			"""
			enableState = 0
			# collect the needed parameters and...
			if self.GetBool(ids.MAINDIALOG_CHECK_ENABLE):
				if self.GetLong(ids.MAINDIALOG_RADIO_GRP) == ids.MAINDIALOG_RADIO_DALL:
					enableState = 1
						
				if self.GetLong(ids.MAINDIALOG_RADIO_GRP) == ids.MAINDIALOG_RADIO_EALL:
					enableState = 2

			# ...run the exporter.
			result = worker.work(aEnabledState  = enableState, 
								 aSetEditor     = self.GetBool(ids.MAINDIALOG_CHECK_SETEDITOR),
								 aSetRender     = self.GetBool(ids.MAINDIALOG_CHECK_SETRENDER),
								 aEditor        = self.GetLong(ids.MAINDIALOG_SLIDER_EDITOR),
								 aRender        = self.GetLong(ids.MAINDIALOG_SLIDER_RENDER),
								 aInc           = self.GetBool(ids.MAINDIALOG_CHECK_INC))
			"""

		# "Cancel"
		if id == 2:
			# just close the dialog - this will call 'AskClose()' first (see bottom)
			self.Close()

		return True
