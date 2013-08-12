# -*- coding: utf-8 -*-

import re

from dateutil.parser import parse
from dateutil.tz import *

from SvnOutputParser import SvnOutputParser

'''
Created on 10/ago/2013

@author: paolo
'''
class SvnDiffConverter(object):
	'''
	classdocs
	'''

	def __init__(self, diff, changes):
		'''
		Constructor
		'''
		self.__diff = StandardSvnDiffOutputParser(diff)
		self.__changes = SvnLogOutputParser(changes)

	def convert(self):
		out = ""

		self.__diff.resetCurrentLine()
		while not self.__diff.isEndReached():
			line = self.__diff.cleanCurrentLine()
			if not line:
				self.__diff.goToNextLine()
				continue

			if self.__diff.isFileChangeLine():
				if out != "":
					out += "\n"

				out += self.__handleFileChange()
			else:
				out += self.__handleOtherLines()

			self.__diff.goToNextLine()

		return out

	def __handleFileChange(self):
		out = ""

		m = self.__diff.isFileChangeLine()
		filename = m.group(1)
		changeType = self.__changes.getChangeType(filename)
		out = changeType + ": " + filename + "\n"

		self.__diff.goToNextLine()
		separatorLine = self.__diff.cleanCurrentLine()
		out += separatorLine + "\n"

		self.__diff.goToNextLine()
		before = self.__diff.cleanCurrentLine()
		if self.__diff.isBinaryDiffLine(before):
			# dump next line
			self.__diff.goToNextLine()
			out += "(Binary files differ)\n"
			return out

		rev1 = self.__getRevision(before)
		self.__diff.goToNextLine()
		after = self.__diff.cleanCurrentLine()
		rev2 = self.__getRevision(after)

		if changeType == "Added":
			out += "--- " + self.__getFilename(before) + "\t\t" + "                       " + " (rev " + rev1 + ")\n"
		else:
			out += "--- " + self.__getFilename(before) + "\t\t" + self.__changes.getDateTime() + " (rev " + rev1 + ")\n"
		out += "+++ " + self.__getFilename(after) + "\t\t" + self.__changes.getDateTime() + " (rev " + rev2 + ")\n"

		return out

	def __getRevision(self, revisionLine):
		m = re.match(r".*\(revision (\d+)\)$", revisionLine)
		return m.group(1)

	def __getFilename(self, revisionLine):
		m = re.match(r"(.*)\(revision \d+\)$", revisionLine)

		filename = m.group(1)[4:].strip("\t ")
		return filename

	def __handleOtherLines(self):
		line = self.__diff.getCurrentLine()

		if self.__diff.isBinaryDiffLine(line):
			# dump next line
			self.__diff.goToNextLine()
			return "(Binary files differ)\n"
		else:
			return line + "\n"

class StandardSvnDiffOutputParser(SvnOutputParser):
	def isFileChangeLine(self):
		curLine = self.getCurrentLine()
		return re.match(r"^Index: (.*)", curLine)

	def isBinaryDiffLine(self, line):
		return re.match(r"Cannot display: file marked as a binary type\.", line)

class SvnLogOutputParser(object):
	__types = {
		"   M": "Modified",
		"   A": "Added",
		"   D": "Deleted",
	}

	def __init__(self, changes):
		self.__changes = changes

		lines = self.__changes.splitlines()
		secondLine = lines[1]
		splittedSecondLine = secondLine.split(" | ");

		dateTimeAsString = splittedSecondLine[2]
		dateTimeAsString = re.sub(r"\(.*\)$", r"", dateTimeAsString)
		dateTime = parse(dateTimeAsString)

		self.__datetime = dateTime.astimezone(tzutc()).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S UTC")

	def getDateTime(self):
		return self.__datetime

	def getChangeType(self, filename):
		changeType = "   M"
		for line in self.__changes.splitlines():
			if filename in line:
				changeType = line[0:4]

		return self.__types[changeType]

class SvnLogConverter(object):
	def __init__(self, files):
		self.__files = files

	def convert(self):
		out = ""
		for line in self.__files.splitlines():
			if line.startswith("   "):
				out += line[3] + "   " + line[6:] + "\n"

		return out.rstrip("\n")
