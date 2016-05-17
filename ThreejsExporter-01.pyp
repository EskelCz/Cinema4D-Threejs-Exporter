import os
import sys

# add this plugin to the python search path
folder = os.path.dirname(__file__)
if folder not in sys.path:
	sys.path.insert(0, folder)

import c4d

from logic import ids
from logic import runner
from logic import maindialog

# make the GeResource object available to modules which need 
#access to the *.res or *.str files
maindialog.__res__ = __res__

#register the plugin
if __name__ == "__main__":

	# load an icon from the 'res' folder
	icon = c4d.bitmaps.BaseBitmap()
	icon.InitWith(os.path.join(os.path.dirname(__file__), "res", "icon.tif"))

	# get the plugin title from the string resource
	title = c4d.plugins.GeLoadString(ids.PLUGIN_NAME_STR)

	c4d.plugins.RegisterCommandPlugin(ids.PLUGINID, title, 0, icon, title, runner.Runner())