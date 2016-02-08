#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2015 NV Access Limited
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
# Extended by Joseph Lee (released under GPL)

from nvdaBuiltin.appModules.searchui import *

class AppModule(AppModule):

	# Past responses from Cortana (cached to prevent repetition, initially an empty string).
	CortanaResponseCache = ""
	# NVDA should not speak while Cortana is speaking.
	CortanaIsListening = False 

	def event_nameChange(self, obj, nextHandler):
		if self.CortanaIsListening: return
		# NVDA, can you act as a mouthpiece for Cortana?
		if isinstance(obj, UIA):
			element = obj.UIAElement
			# There are two Cortana response lines. Usually line 2 is more reliable.
			if element.cachedAutomationID in ("SpeechContentLabel", "GreetingLine2"):
					ui.message(obj.name)
		nextHandler()

	def event_appModule_gainFocus(self):
		import globalPlugins
		if globalPlugins.wintenObjs.letCortanaListen:
			self.CortanaIsListening = True

	def event_appModule_loseFocus(self):
		if self.CortanaIsListening:
			self.CortanaIsListening = False
			import globalPlugins
			globalPlugins.wintenObjs.letCortanaListen = False