# -*- coding: utf-8 -*-
'''
*config.py: Configuration options*
----------------------------------
This file created in SelectConfigSetting on 11 09 2024 13:16
'''

import os.path
import GSASIIpath

Main_Pos = (-25, -27)
'''Main window location - will be updated & saved when user moves
it. If position is outside screen then it will be repositioned to default
'''

Main_Size = (1600, 909)
'''Main window size (width, height) - initially uses wx.DefaultSize but will updated
 and saved as the user changes the window
'''

Plot_Pos = (621, 388)
'''Plot window location - will be updated & saved when user moves it
these widows. If position is outside screen then it will be repositioned to default
'''

Plot_Size = (700, 687)
'''Plot window size (width, height) - initially uses wx.DefaultSize but will updated
 and saved as the user changes the window
'''

previous_GPX_files = [
	  "/home/mkscd/YAG.gpx",
	  "/home/mkscd",
   ]
'''A list of previously used .gpx files
'''

