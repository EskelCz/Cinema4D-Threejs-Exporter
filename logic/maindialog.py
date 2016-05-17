import c4d

from logic import ids
from logic import exporter

VERSION = '0.0.1'

class MainDialog(c4d.gui.GeDialog):

	# called once when the dialog is initialized
	def __init__(self):

		# kill the menu-bar
		self.AddGadget(c4d.DIALOG_NOMENUBAR, ids.MAINDIALOG);


	# called when the dialog is opened - load or generate the GUI here
	def CreateLayout(self):

		# load and parse the dialog layout from the resource file
		return self.LoadDialogResource(ids.MAINDIALOG, None, flags= c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT )


	# called after 'CreateLayout()' - used to initialize the GUI elements
	#and reset values
	def InitValues(self): 

		# init the sliders
		#self.SetReal(ids.MAINDIALOG_SLIDER_EDITOR, 2, 0, 6, 1.0, c4d.FORMAT_LONG)

		# disable elements that are dependent on checkbox-settings
		#self.Enable(ids.MAINDIALOG_SLIDER_EDITOR, False)

		return True


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
