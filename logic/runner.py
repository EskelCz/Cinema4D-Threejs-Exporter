# coding=UTF-8

import c4d
import ctypes

from c4d import documents
from logic import ids
from logic.maindialog import MainDialog


# this class is the basic plugin
class Runner(c4d.plugins.CommandData):

	__dialog = None

	# we could also just execute some code here - the dialog is optional 
	def Execute(self, doc):

		# check all requirements
		self.doc = documents.GetActiveDocument()
		if self.doc is None:
			c4d.gui.MessageDialog('Error:	✘ No active document')
			return False 

		self.op = self.doc.GetActiveObject()
		if self.op is None:
			c4d.gui.MessageDialog('Error: 	✘ No selected object for export')
			return False

		if self.op.GetType() != c4d.Opolygon:
			c4d.gui.MessageDialog('Error: 	✘ Selected Object is not an editable mesh')
			return False

		winWidth  = 440
		winHeight = 725

		# center to the screen 
		if hasattr(ctypes, 'windll'):
			user32 = ctypes.windll.user32
			x = user32.GetSystemMetrics(0)/2 - winWidth/2
			y = user32.GetSystemMetrics(1)/2 - winHeight/2
		else:
			x = 200
			y = 200

		# create a maindialog object if it hasn't been initialized jet
		if self.__dialog is None:            
			self.__dialog = MainDialog()

		# return the successful opening of the dialog
		return self.__dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL_RESIZEABLE, pluginid=ids.PLUGINID, xpos=x, ypos=y, defaultw=winWidth, defaulth=winHeight)


	# needed to restore minimized dialogs and for startup layout integration
	"""
	def RestoreLayout(self, sec_ref):
	
		# create a maindialog object if it hasn't been initialized jet
		if self.__dialog is None:            
			self.__dialog = MainDialog()

		# return the successful restauration of the dialog
		return self.__dialog.Restore(ids.PLUGINID, sec_ref)
	"""