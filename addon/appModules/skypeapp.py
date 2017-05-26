#appModules/skypeapp.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2016-2017 NV Access Limited, Joseph Lee
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

"""Routines for universal app version of Skype."""

import re
import appModuleHandler
import ui
from NVDAObjects.UIA import UIA
import api
import controlTypes
import addonHandler
addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		for pos in xrange(10):
			self.bindGesture("kb:control+nvda+%s"%pos, "readMessage")
		for pos in xrange(1, 5):
			self.bindGesture("kb:alt+%s"%pos, "moveToArea")

	def event_NVDAObject_init(self, obj):
		if isinstance(obj, UIA):
			# Skype Preview 11.9 includes audio/video config combo boxes but they are not labeled correctly.
			# Thankfully the label is right next door.
			if obj.role == controlTypes.ROLE_COMBOBOX and obj.name == "" and obj.UIAElement.cachedAutomationID.startswith("AudioVideoDevices"):
				obj.name = obj.previous.name

	def event_gainFocus(self, obj, nextHandler):
		# Skype message/channel info and other extraneous text should not be announced.
		# Credit: Derek Riemer
		uiElement = obj.UIAElement
		if uiElement.cachedAutomationID == "Message" and uiElement.cachedClassName == "ListViewItem":
			self.reportMessage(obj.name)
			return
		nextHandler()

	# Locate various elements, as this is one of the best ways to do this in Skype Preview.
	# The best criteria is automation ID (class names are quite generic).
	def locateElement(self, automationID):
		# Foreground isn't reliable.
		fg = api.getForegroundObject()
		if fg.getChild(1).childCount > 0:
			screenContent = fg.getChild(1)
		else:
			screenContent = fg.getChild(2)
		# Thanks to My Peple in Redstone 3, screen content so far could actually be the title bar, and the actual foreground window is next door.
		# In other words, Skype window is embedded inside My People window.
		if screenContent.UIAElement.cachedAutomationID == "TitleBar":
			# The following traversal path may change in future builds.
			screenContent = screenContent.next.simpleLastChild.simpleFirstChild
		# Element placement (according to UIA changes from time to time.
		# Wish there is a more elegant way to do this...
		for element in screenContent.children:
			if isinstance(element, UIA) and element.UIAElement.cachedAutomationID == automationID:
				return element
		return None

	# Borrowed from Skype for Desktop app module (NVDA Core).
	# #14: Drop channel type (e.g. Skype Message).
	# Also match multi-line messages.
	RE_MESSAGE = re.compile(r"\AFrom (?P<from>.*), Skype (?P<body>.*), sent on (?P<time>.*?)(?: Edited by .* at .*?)?(?: Not delivered|New)?\Z", re.M|re.S)

	def reportMessage(self, message):
		# Just like Desktop client, messages are quite verbose.
		m = self.RE_MESSAGE.match(message)
		if m:
			messageBody = m.group("body")
			message = "%s, %s" % (m.group("from"), messageBody[messageBody.find(", ")+2:])
		ui.message(message)

	def event_nameChange(self, obj, nextHandler):
		if isinstance(obj, UIA):
			uiElement = obj.UIAElement
			if uiElement.cachedClassName == "TextBlock" and obj.next is not None:
				# Announce typing indicator (same as Skype for Desktop).
				nextElement = obj.next.UIAElement
				# Make sure to catch all possible UI placement changes between Skype Preview releases.
				if nextElement.cachedAutomationID in ("ChatEditBox", "ChatTranslationSettings"):
					# Translators: Presented when someone stops typing in Skype app (same as Skype for Desktop).
					ui.message(obj.name if obj.name != "" else _("Typing stopped"))
			elif uiElement.cachedAutomationID == "Message" and uiElement.cachedClassName == "ListViewItem":
				self.reportMessage(obj.name)
		nextHandler()

	def script_readMessage(self, gesture):
		chatHistory = self.locateElement("chatMessagesListView")
		# Position of chat history in object hierarchy changes based on which tabv is active.
		# Wish there is a more elegant way to do this...
		if chatHistory is None:
			# Translators: Presented when message history isn't found in Skype Preview app.
			ui.message(_("Chat history not found"))
			return
		pos = int(gesture.displayName[-1])
		if pos == 0: pos += 10
		try:
			message = chatHistory.getChild(0-pos)
			api.setNavigatorObject(message)
			self.reportMessage(message.name)
			return
		except IndexError:
			return
	# Translators: Input help mode message for a command in Skype Preview app.
	script_readMessage.__doc__ = _("Reports and moves the review cursor to a recent message")

	# Various utility scripts to move to various parts of Skype Preview.
	# Tuple below holds UIA automation ID for the element and errors if the element is not found.
	moveTo = (
	(None, None),
	("ConversationHistoryPanel", "Conversation history not found"),
	("ContactList", "Contacts list not found"),
	(" BotList", "Skype bots list not found"),
	("ChatEditBox", "Chat edit field not found"),
	)

	def script_moveToArea(self, gesture):
		area = int(gesture.displayName.split("+")[-1])
		# However, since March 2017, areas received keyboard shortcuts, such as Alt+2 for contacts list.
		if self.productVersion >= "11.13.133.0" and area < 4:
			gesture.send()
			return
		element = self.locateElement(self.moveTo[area][0])
		if element is None:
			ui.message(self.moveTo[area][1])
			return
		element.setFocus()
		return
