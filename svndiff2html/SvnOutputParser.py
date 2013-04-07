'''
Created on 31/mar/2013

@author: paolo
'''

import re

class SvnOutputParser(object):
	'''
	classdocs
	'''

	def __init__(self, diff):
		'''
		Constructor
		'''
		self.lines = diff.splitlines()
		self.linesCount = len(self.lines)
		self.resetCurrentLine()

	def resetCurrentLine(self):
		self.currentLine = 0

	def isEndReached(self):
		return self.currentLine >= self.linesCount

	def goToNextLine(self):
		self.currentLine += 1

	def getCurrentLine(self):
		return self.lines[self.currentLine]

	def cleanCurrentLine(self):
		curLine = self.getCurrentLine()
		return re.sub(r"[\n\r]+$", r"", curLine)

	def clean(self, line):
		return re.sub(r"[\n\r]+$", r"", line)

	def isFileChangeLine(self):
		curLine = self.getCurrentLine()
		return re.match(r"^(Modified|Added|Deleted|Copied): (.*)", curLine)

	def isBinaryDiffLine(self, line):
		return re.match(r"\(Binary files differ\)", line)

	def hasDiffAttached(self, line):
		return re.match(r"^=", line)
