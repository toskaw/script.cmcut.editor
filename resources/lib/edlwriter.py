'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import xbmcgui, xbmc, xbmcvfs

from resources.lib.notifications import notify, yesno

# Set to True if you want to be able to adjust marker time
# Warning: this is experimental (i.e. not working well!)
ADVANCED_MODE = True

# Define types of marker
# This isn't implemented yet...
EDL_CUT = 0
EDL_MUTE = 1
EDL_SCENE_MARKER = 2
EDL_COMMERCIAL_BREAK = 3

# Define how big we want our steps to be if using Advanced Mode (in seconds)
SMALL_STEP = 100
BIG_STEP = 500
REFRESH = 500

# Constants for Advanced Mode menu
BIG_STEP_BACK = 0
SMALL_STEP_BACK = 1
SMALL_STEP_FORWARD = 2
BIG_STEP_FORWARD = 3
DONE = 4

# Define action
ADD_POINT = 0
DELETE_LIST_ITEM = 1 
CANCEL = -1

Select = xbmcgui.Dialog().select

MENU_LIST = [(BIG_STEP_BACK, "Big step back"),
             (SMALL_STEP_BACK, "Small step back"),
             (SMALL_STEP_FORWARD, "Small step forward"),
             (BIG_STEP_FORWARD, "Big step forward"),
             (DONE, "Done")]

ACTION_LIST = [(ADD_POINT, "Add point"),
               (DELETE_LIST_ITEM, "Delete list item"),
               (CANCEL, "Cancel")]

class EDLWriter(object):
    def __init__(self, default = EDL_COMMERCIAL_BREAK):
        self.videoname = None
        self.is_open = False
        self.edllist = []
        self.current = {}
        self.default = default
        self.totaltime = 0
        self.first  = True
        self.capture = xbmc.RenderCapture()

    def SetVideoName(self, vname):
        self.videoname = vname
        
    def ReadEdl(self, totaltime):
        editlist =  xbmc.getInfoLabel('Player.Editlist')
        if editlist == "":
            return
        edl = editlist.split(",")
        self.current = {}
        self.totaltime = totaltime
        for index, val in enumerate(edl):
            time = float(val) * totaltime / 100
            if not (index % 2) :
                self.current["start"] = time
            else:
                self.current["end"] = time
                self.current["type"] = EDL_COMMERCIAL_BREAK
                self.edllist.append(self.current)
                self.current = {}
        
    def AddPoint(self, marktime, player):
        self.player = player
        update = True
        action = Select("Select action", [x[1] for x in ACTION_LIST])
        if action == ADD_POINT:
            self.ExecAddPoint(marktime, player)
        elif action == DELETE_LIST_ITEM:
            self.ExecDelete()
        else:
            pass
        
    def ExecAddPoint(self, marktime, player):
        # Check if this the first marker
        if not self.is_open and self.first:
            self.first = False
            first = yesno("This is your first marker. "
                          "Do you want to create a marker from the beginning of"
                          " the video to here?")
            if first:
                self.current["start"] = 0
                self.is_open = True
                
        # If using advanced mode then we call the necessary function
        if ADVANCED_MODE:
            update, marktime = self.adjustTime(marktime)

        # If we want to add the marker...
        if update:

            if self.is_open:
                self.current["end"] = self.player.toMillis(marktime) / 1000.0
                self.current["type"] = self.default
                self.edllist.append(self.current)
                notify("New markers added.")
                self.current = {}
                self.is_open = False

            else:
                self.current["start"] = self.player.toMillis(marktime) / 1000.0
                notify("Starting marker added.")
                self.is_open = True

    def ExecDelete(self):
        Item = self.selectItem()
        if Item == CANCEL:
            return
        # delete item
        self.edllist.pop(Item)

    def selectItem(self):
        menu = [(CANCEL, "Cancel")]
        for index, item in enumerate(self.edllist):
            menu.append((index, str(item["start"]) + " sec - " + str(item["end"]) + "sec"))
        item = Select("Select delete item", [x[1] for x in menu])
        return menu[item][0]
        
    def selectEDLtype(self):
        edl = Select("EDL Writer", [x[1] for x in TYPE_MENU])
        return TYPE_MENU[edl][0]

    def adjustTime(self, adjustTime):
        finished = False
        update = False
        seektime = adjustTime

        while not finished:
            seek = False

            #self.takeSnapshot()

            action = Select("EDL Writer", [x[1] for x in MENU_LIST])

            selected = MENU_LIST[action][0]

            if selected == BIG_STEP_BACK:
                seektime = self.player.calcTime(seektime, BIG_STEP, True)
                seek = True

            elif selected == SMALL_STEP_BACK:
                seektime = self.player.calcTime(seektime, SMALL_STEP, True)
                seek = True

            elif selected == SMALL_STEP_FORWARD:
                seektime = self.player.calcTime(seektime, SMALL_STEP)
                seek = True

            elif selected == BIG_STEP_FORWARD:
                seektime = self.player.calcTime(seektime, BIG_STEP)
                seek = True

            elif selected == DONE:
                finished = True
                update = True

            else:
                finished = True

            # User wants to adjust time
            if seek:
                self.player.seekVideoTime(seektime)

        return update, seektime

    def takeSnapshot(self):

        self.capture.capture(400, 400)
        size = (self.capture.getWidth(), self.capture.getHeight())
        mode = 'RGBA'

    def Finish(self):
        path = "{0}.edl".format(self.videoname)
        if self.is_open:
            self.current["end"] = self.totaltime
            self.current["type"] = self.default
            self.edllist.append(self.current)
            self.is_open = False
            
        with xbmcvfs.File(path, "w") as edl:
            buffer = ""
            for scene in self.edllist:
                buffer += ("{start:.3f}\t{end:.3f}\t{type}\n".format(**scene))
            buffer += ("## File generated by script.edl.creator addon for Kodi.")
            edl.write(buffer)
        notify("EDL file written successfully!")
