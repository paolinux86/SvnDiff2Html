# -*- coding: utf-8 -*-

'''
Created on 30/mar/2013

@author: paolo
'''

import re
from HtmlTag import HtmlTag
from TagMode import TagMode
from SvnOutputParser import SvnOutputParser
from svndiff2html.HtmlTag import HtmlTag
from svndiff2html.TagMode import TagMode

class SvnDiff2Html(object):
	'''
	classdocs
	'''

	UNLIMITED_LENGTH = 0

	max_length = UNLIMITED_LENGTH

	__html_escape_table = {
		"&": "&amp;",
		'"': "&quot;",
		"'": "&apos;",
		">": "&gt;",
		"<": "&lt;",
	}

	__types = {
		"Modified": "modfile",
		"Added": "addfile",
		"Deleted": "delfile",
		"Copied": "copfile",
	}

	__changeCodes = {
		"U": "Modified Paths",
		"A": "Added Paths",
		"D": "Removed Paths",
		"_": "Property Changed"
	}

	def __init__(self, diff, files):
		'''
		Constructor
		'''
		self.__diff = SvnOutputParser(diff)
		self.__fileChanges = SvnOutputParser(files)
		self.__inDiv = False
		self.__inSpan = None
		self.__seen = {}
		self.__files = { "U": [], "A": [], "D": [], "_": [], }

	def output_file_lists(self):
		out = ""
		while not self.__fileChanges.isEndReached():
			line = self.__fileChanges.cleanCurrentLine()
			m = re.match("^(.)(.).+", line)
			if m:
				filename = re.sub("^(.)(.)\s+", "", line)
				self.__files[m.group(1)].append(filename)
				if m.group(2) != " " and m.group(1) != "_":
					self.__files["_"].append(filename)
			self.__fileChanges.goToNextLine()

		for t in [ "U", "A", "D", "_", ]:
			if not self.__files[t]:
				continue

			tag = HtmlTag("h3")
			tag.setText(self.__changeCodes[t])
			out += tag.toHtml(TagMode.CLOSED) + "\n" + HtmlTag("ul").toHtml() + "\n"
			for filename in self.__files[t]:
				f = self.html_escape(filename)
				if f.endswith("/") and t != "_":
					# Directories don't link, unless it's a prop change
					li = HtmlTag("li")
					li.setText(f)
					out += li.toHtml(TagMode.CLOSED) + "\n"
				else:
					html_id = re.sub(r"[^\w_]", r"", f)
					aTag = HtmlTag("a")
					aTag.setText(f)
					aTag.addAttribute("href", "#" + html_id)
					li = HtmlTag("li")
					li.setInnerHtml(aTag.toHtml(TagMode.CLOSED))
					out += li.toHtml(TagMode.CLOSED) + "\n"

			out += "</ul>\n\n"

		return out

	def output_formatted_diff(self):
		length = 0

		tag = HtmlTag("h3")
		tag.setText("Diff")
		divTag = HtmlTag("div", "patch")
		divTag.setInnerHtml("\n" + tag.toHtml(TagMode.CLOSED))
		out = divTag.toHtml() + "\n"

		self.__diff.resetCurrentLine()
		while not self.__diff.isEndReached():
			line = self.__diff.cleanCurrentLine()
			if not line:
				self.__diff.goToNextLine()
				continue

			length += len(line)
			if self.__isMaxLengthReached(length):
				out += self.__closeAfterMaxLength()
				break

			if self.__diff.isFileChangeLine():
				out += self.__handleFileChange()
			else:
				out += self.__handleOtherLines()

			self.__diff.goToNextLine()

		if self.__inSpan:
			out += self.__inSpan.getCloseTag()
		if self.__inDiv:
			out += HtmlTag.printCloseTag("span")
			out += HtmlTag.printCloseTag("pre") + "\n"
			out += HtmlTag.printCloseTag("div") + "\n"
		out += HtmlTag.printCloseTag("div") + "\n"

		return out;

	def __isMaxLengthReached(self, length):
		return self.max_length > 0 and length >= self.max_length

	def __closeAfterMaxLength(self):
		out = ""

		if self.__inSpan:
			out += self.__inSpan.getCloseTag()

		tag = HtmlTag("span")
		tag.addClass("lines")
		tag.setText("@@ Diff output truncated at " + str(self.max_length) + " characters. @@\n")
		out += tag.toHtml(TagMode.CLOSED)

		self.__inSpan = None

		return out

	def __handleFileChange(self):
		out = ""

		m = self.__diff.isFileChangeLine()
		action = m.group(1)
		theClass = self.__types[action]
		if m.group(2) in self.__seen:
			self.__seen[m.group(2)] += 1
		else:
			self.__seen[m.group(2)] = 1

		filename = self.html_escape(m.group(2))
		html_id = re.sub(r"[^\w_]", r"", filename)

		if self.__inSpan:
			out += self.__inSpan.getCloseTag()
		if self.__inDiv:
			out += HtmlTag.printCloseTag("span")
			out += HtmlTag.printCloseTag("pre")
			out += HtmlTag.printCloseTag("div") + "\n"

		# Dump line, but check it's content.
		self.__diff.goToNextLine()
		line = self.__diff.getCurrentLine()
		if not self.__diff.hasDiffAttached(line):
			# Looks like they used --no-diff-added or --no-diff-deleted.
			out += self.__handleNoDiffAttached(html_id, theClass, action, filename)
			return out

		self.__diff.goToNextLine()
		before = self.__diff.cleanCurrentLine()

		if self.__diff.isBinaryDiffLine(before):
			# Just output the whole filename div.
			out += self.__handleBinaryDiff(before, html_id, action, filename)
			return out

		rev1 = self.__getRevision(before)
		self.__diff.goToNextLine()
		after = self.__diff.cleanCurrentLine()
		rev2 = self.__getRevision(after)

		# Output the headers.
		tag = HtmlTag("a", html_id)
		out += tag.toHtml(TagMode.CLOSED) + "\n"

		tag = HtmlTag("div")
		tag.addClass(theClass)
		out += tag.toHtml()

		tag = HtmlTag("h4")
		tag.setText(action + ": " + filename + " (" + rev1 + " => " + rev2 + ")")
		out += tag.toHtml(TagMode.CLOSED) + "\n"

		tag = HtmlTag("pre")
		tag.addClass("diff")
		out += tag.toHtml() + HtmlTag("span").toHtml() + "\n"

		tag = HtmlTag("span")
		tag.addClass("info")
		out += tag.toHtml()

		self.__inDiv = True
		out += self.html_escape(before) + "\n"
		out += self.html_escape(after) + "\n"
		out += HtmlTag.printCloseTag("span")
		self.__inSpan = None

		return out

	def __handleNoDiffAttached(self, html_id, theClass, action, filename):
		out = ""

		self.__inSpan = None
		self.__inDiv = False
		tag = HtmlTag("a", html_id)
		out += tag.toHtml(TagMode.CLOSED) + "\n"

		tag = HtmlTag("div")
		tag.addClass(theClass)
		out += tag.toHtml()

		tag = HtmlTag("h4")
		tag.setText(action + ": " + filename)
		out += tag.toHtml(TagMode.CLOSED)
		out += HtmlTag.printCloseTag("div") + "\n"
		self.__diff.goToNextLine()

		return out

	def __handleBinaryDiff(self, line, html_id, action, filename):
		out = ""

		tag = HtmlTag("a", html_id)
		out += tag.toHtml(TagMode.CLOSED) + "\n"

		tag = HtmlTag("div")
		tag.addClass("binary")
		out += tag.toHtml()

		tag = HtmlTag("h4")
		tag.setText(action + ": " + filename)
		out += tag.toHtml(TagMode.CLOSED) + "\n"

		tag = HtmlTag("pre")
		tag.addClass("diff")
		out += tag.toHtml() + HtmlTag("span").toHtml() + "\n"

		tag = HtmlTag("span")
		tag.addClass("cx")
		tag.setText(line + "\n")
		out += tag.toHtml(TagMode.CLOSED)

		out += HtmlTag.printCloseTag("span") + HtmlTag.printCloseTag("span")
		out += HtmlTag.printCloseTag("pre") + HtmlTag.printCloseTag("div") + "\n"

		self.__inSpan = None
		self.__inDiv = False
		self.__diff.goToNextLine()

		return out

	def __handleOtherLines(self):
		out = ""
		line = self.__diff.getCurrentLine()

		m1 = re.match(r"^Property changes on: (.*)", line)
		if m1 and (not m1.group(1) in self.__seen or self.__seen[m1.group(1)] <= 0):
			out += self.__handlePropertyChange(m1)
		elif re.match(r"^\@\@", line):
			if self.__inSpan:
				out += self.__inSpan.getCloseTag()
			spanTag = HtmlTag("span")
			spanTag.addClass("lines")
			spanTag.setText(self.html_escape(line) + "\n")
			out += spanTag.toHtml(TagMode.CLOSED)
			self.__inSpan = None
		else:
			m2 = re.match(r"^([-+])", line)
			if m2:
				out += self.__handleDiff(m2)
			else:
				if self.__inSpan == "cx":
					out += self.html_escape(line) + "\n"
				else:
					if self.__inSpan:
						out += self.__inSpan.getCloseTag()
					spanTag = HtmlTag("span")
					spanTag.addClass("cx")
					spanTag.setText(self.html_escape(line) + "\n")
					out += spanTag.toHtml()
					self.__inSpan = HtmlTag("span")

		return out

	def __handlePropertyChange(self, m):
		out = ""

		# It's just property changes.
		filename = self.html_escape(m.group(1))
		html_id = re.sub(r"[^\w_]", r"", filename)

		# Dump line.
		self.__diff.goToNextLine()

		# Output the headers.
		if self.__inSpan:
			out += self.__inSpan.getCloseTag()
		if self.__inDiv:
			out += HtmlTag.printCloseTag("span") + HtmlTag.printCloseTag("pre") + HtmlTag.printCloseTag("div") + "\n"

		out += HtmlTag("a").setText(html_id).toHtml(TagMode.CLOSED) + "\n" + HtmlTag("div").addClass("propset").toHtml()
		out += HtmlTag("h4").setText("Property changes: " + filename).toHtml(TagMode.CLOSED) + "\n"
		out += HtmlTag("pre").addClass("diff").toHtml() + HtmlTag("span").toHtml() + "\n"
		self.__inDiv = True
		self.__inSpan = None

		return out

	def __handleDiff(self, m):
		out = ""
		if m.group(1) == "+":
			t = "ins"
		else:
			t = "del"

		line = self.__diff.getCurrentLine()
		if self.__inSpan and self.__inSpan.tagname == t:
			out += self.html_escape(line) + "\n"
		else:
			if self.__inSpan:
				out += self.__inSpan.getCloseTag()
			out += "<" + t + ">" + self.html_escape(line) + "\n"
			self.__inSpan = HtmlTag(t)

		return out

	def __getRevision(self, revisionLine):
		m = re.match(r".*\(rev (\d+)\)$", revisionLine)
		return m.group(1)

	def html_escape(self, text):
		"""Produce entities within text."""
		return "".join(self.__html_escape_table.get(c, c) for c in text)

	def output_css(self):
		out = "#msg dl.meta { border: 1px #006 solid; background: #369; padding: 6px; color: #fff; }\n"
		out += "#msg dl.meta dt { float: left; width: 6em; font-weight: bold; }\n"
		out += "#msg dt:after { content:':';}\n"
		out += "#msg dl, #msg dt, #msg ul, #msg li, #logmsg { font-family: ), verdana,arial,helvetica,sans-serif; font-size: 10pt;  }\n"
		out += "#msg dl a { font-weight: bold}\n"
		out += "#msg dl a:link    { color:#fc3; }\n"
		out += "#msg dl a:active  { color:#ff0; }\n"
		out += "#msg dl a:visited { color:#cc6; }\n"
		out += "#patch h3 { font-family: verdana,arial,helvetica,sans-serif; font-size: 10pt; font-weight: bold; }\n"
		out += "#msg pre { overflow: auto; background: #ffc; border: 1px #fa0 solid; padding: 6px; }\n"
		out += "#logmsg { background: #ffc; border: 1px #fa0 solid; padding: 1em 1em 0 1em; }\n"
		out += "#logmsg p, #logmsg pre, #logmsg blockquote { margin: 0 0 1em 0; }\n"
		out += "#logmsg p, #logmsg li, #logmsg dt, #logmsg dd { line-height: 14pt; }\n"
		out += "#logmsg h1, #logmsg h2, #logmsg h3, #logmsg h4, #logmsg h5, #logmsg h6 { margin: .5em 0; }\n"
		out += "#logmsg h1:first-child, #logmsg h2:first-child, #logmsg h3:first-child, #logmsg h4:first-child, #logmsg h5:first-child, #logmsg h6:first-child { margin-top: 0; }\n"
		out += "#logmsg ul, #logmsg ol { padding: 0; list-style-position: inside; margin: 0 0 0 1em; }\n"
		out += "#logmsg ul { text-indent: -1em; padding-left: 1em; }\n"
		out += "#logmsg ol { text-indent: -1.5em; padding-left: 1.5em; }\n"
		out += "#logmsg > ul, #logmsg > ol { margin: 0 0 1em 0; }\n"
		out += "#logmsg pre { background: #eee; padding: 1em; }\n"
		out += "#logmsg blockquote { border: 1px solid #fa0; border-left-width: 10px; padding: 1em 1em 0 1em; background: white;}\n"
		out += "#logmsg dl { margin: 0; }\n"
		out += "#logmsg dt { font-weight: bold; }\n"
		out += "#logmsg dd { margin: 0; padding: 0 0 0.5em 0; }\n"
		out += "#logmsg dd:before { content:'\\00bb';}\n"
		out += "#logmsg table { border-spacing: 0px; border-collapse: collapse; border-top: 4px solid #fa0; border-bottom: 1px solid #fa0; background: #fff; }\n"
		out += "#logmsg table th { text-align: left; font-weight: normal; padding: 0.2em 0.5em; border-top: 1px dotted #fa0; }\n"
		out += "#logmsg table td { text-align: right; border-top: 1px dotted #fa0; padding: 0.2em 0.5em; }\n"
		out += "#logmsg table thead th { text-align: center; border-bottom: 1px solid #fa0; }\n"
		out += "#logmsg table th.Corner { text-align: left; }\n"
		out += "#logmsg hr { border: none 0; border-top: 2px dashed #fa0; height: 1px; }\n"
		out += "#patch { width: 100%; }\n"
		out += "#patch h4 {font-family: verdana,arial,helvetica,sans-serif;"
		out += "font-size:10pt;padding:8px;background:#369;color:#fff; margin:0;}\n"
		out += "#patch .propset h4, #patch .binary h4 {margin:0;}\n"
		out += "#patch pre {padding:0;line-height:1.2em;margin:0;}\n"
		out += "#patch .diff {width:100%;background:#eee;padding: 0 0 10px 0; overflow:auto;}\n"
		out += "#patch .propset .diff, #patch .binary .diff  {padding:10px 0;}\n"
		out += "#patch span {display:block;padding:0 10px;}\n"
		out += "#patch .modfile, #patch .addfile, #patch .delfile, #patch .propset, #patch .binary, #patch .copfile {border:1px solid #ccc; margin:10px 0;}\n"
		out += "#patch ins {background:#dfd;text-decoration:none;display:block; padding:0 10px;}\n"
		out += "#patch del {background:#fdd;text-decoration:none;display:block; padding:0 10px;}\n"
		out += "#patch .lines, .info {color:#888;background:#fff;}"

		return out
