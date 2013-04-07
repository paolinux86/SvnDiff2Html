'''
Created on 31/mar/2013

@author: paolo
'''
from TagMode import TagMode

class HtmlTag(object):
	'''
	classdocs
	'''

	def __init__(self, tagname, tagid = ""):
		'''
		Constructor
		'''
		self.tagname = tagname
		self.tagid = tagid

		self.classes = []
		self.text = ""
		self.html = ""
		self.attrs = {}

	def addClass(self, theClass):
		self.classes.append(theClass)

	def addClasses(self, classes = []):
		self.classes.extend(classes)

	def setText(self, text):
		self.text = text

	def setInnerHtml(self, html):
		self.html = html

	def addAttribute(self, attribute, value):
		self.attrs[attribute] = value

	def toHtml(self, tagMode = TagMode.OPEN):
		out = "<" + self.tagname
		if self.tagid:
			out += " id=\"" + self.tagid + "\""
		if self.classes:
			out += " class=\"" + " ".join(self.classes) + "\""
		if self.attrs:
			for attr, value in self.attrs.iteritems():
				out += " " + attr + "=\"" + value + "\""
		out += ">"

		if self.text:
			out += self.text
		elif self.html:
			out += self.html

		if tagMode == TagMode.CLOSED:
			out += self.getCloseTag()

		return out

	def getCloseTag(self):
		return "</" + self.tagname + ">"

	@staticmethod
	def printCloseTag(tagname):
		return "</" + tagname + ">"
