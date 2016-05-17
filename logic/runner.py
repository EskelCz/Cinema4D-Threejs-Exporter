import c4d

from logic import ids
from logic.maindialog import MainDialog


# this class is the basic plugin
class Runner(c4d.plugins.CommandData):

	__dialog = None


	# we could also just execute some code here - the dialog is optional 
	def Execute(self, doc):
	
		# create a maindialog object if it hasn't been initialized jet
		if self.__dialog is None:            
			self.__dialog = MainDialog()

		# return the successful opening of the dialog
		return self.__dialog.Open(c4d.DLG_TYPE_ASYNC, ids.PLUGINID)
	
		
	# needed to restore minimized dialogs and for startup layout integration
	def RestoreLayout(self, sec_ref):
	
		# create a maindialog object if it hasn't been initialized jet
		if self.__dialog is None:            
			self.__dialog = MainDialog()

		# return the successful restauration of the dialog
		return self.__dialog.Restore(ids.PLUGINID, sec_ref)