# -*- coding: utf-8 -*-

'''
Created on 30/mar/2013

@author: paolo
'''

import re
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

	__inDiv = False

	__inSpan = None

	__seen = {}

	__lines = []

	__currentLine = 0

	def __init__(self, diff):
		'''
		Constructor
		'''
		self.__lines = diff.splitlines()

	def output_formatted_diff(self):
		length = 0

		tag = HtmlTag("h3")
		tag.setText("Diff")
		divTag = HtmlTag("div", "patch")
		divTag.setInnerHtml("\n" + tag.toHtml(TagMode.CLOSED))
		out = divTag.toHtml() + "\n"

		lines_length = len(self.__lines)

		self.__currentLine = 0
		while self.__currentLine < lines_length:
			line = self.__cleanCurrentLine()
			if not line:
				self.__goToNextLine()
				continue

			length += len(line)
			if self.__isMaxLengthReached(length):
				out += self.__closeAfterMaxLength()
				break

			m = re.match(r"^(Modified|Added|Deleted|Copied): (.*)", line)
			if m:
				out += self.__handleFileChange(m)
			else:
				m1 = re.match(r"^Property changes on: (.*)", line)
				if m1 and self.__seen[m1.group(1)] <= 0:
					out += self.__handlePropertyChange()
				elif re.match(r"^\@\@", line):
					if self.__inSpan:
						out += self.__inSpan.getCloseTag()
					out += "<span class=\"lines\">" + self.html_escape(line) + "\n</span>"
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
							out += "<span class=\"cx\">" + self.html_escape(line) + "\n"
							self.__inSpan = HtmlTag("span")
			self.__goToNextLine()

		if self.__inSpan:
			out += self.__inSpan.getCloseTag()
		if self.__inDiv:
			out += "</span></pre>\n</div>\n"
		out += "</div>\n"

		return out;

	def __isMaxLengthReached(self, length):
		return self.max_length > 0 and length >= self.max_length

	def __goToNextLine(self):
		self.__currentLine += 1

	def __getCurrentLine(self):
		return self.__lines[self.__currentLine]

	def __cleanCurrentLine(self):
		curLine = self.__getCurrentLine()
		return re.sub(r"[\n\r]+$", r"", curLine)

	def __clean(self, line):
		return re.sub(r"[\n\r]+$", r"", line)

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

	def __handleFileChange(self, m):
		out = ""

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
			out += HtmlTag.printCloseTag("span") + HtmlTag.printCloseTag("pre") + HtmlTag.printCloseTag("div") + "\n"

		# Dump line, but check it's content.
		self.__goToNextLine()
		m = re.match(r"^=", self.__getCurrentLine())
		if not m:
			# Looks like they used --no-diff-added or --no-diff-deleted.
			self.__inSpan = None
			__inDiv = False
			tag = HtmlTag("a", html_id)
			out += tag.toHtml(TagMode.CLOSED) + "\n"

			tag = HtmlTag("div")
			tag.addClass(theClass)
			out += tag.toHtml()

			tag = HtmlTag("h4")
			tag.setText(action + ": " + filename)
			out += tag.toHtml(TagMode.CLOSED)
			out += HtmlTag.printCloseTag("div") + "\n"
			self.__goToNextLine()
			return out

		self.__goToNextLine()
		before = self.__cleanCurrentLine()

		if re.match(r"\(Binary files differ\)", before):
			# Just output the whole filename div.
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
			tag.setText(before + "\n")
			out += tag.toHtml(TagMode.CLOSED)

			out += HtmlTag.printCloseTag("span") + HtmlTag.printCloseTag("span")
			out += HtmlTag.printCloseTag("pre") + HtmlTag.printCloseTag("div") + "\n"

			self.__inSpan = None
			self.__inDiv = False
			self.__goToNextLine()
			return out

		rev1 = self.__getRevision(before)
		self.__goToNextLine()
		after = self.__cleanCurrentLine()
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

	def __handlePropertyChange(self, m):
		out = ""

		# It's just property changes.
		filename = self.html_escape(m.group(1))
		html_id = re.sub(r"[^\w_]", r"", filename)

		# Dump line.
		self.__goToNextLine()

		# Output the headers.
		if self.__inSpan:
			out += self.__inSpan.getCloseTag()
		if self.__inDiv:
			out += HtmlTag.printCloseTag("span") + HtmlTag.printCloseTag("pre") + HtmlTag.printCloseTag("div") + "\n"

		out += "<a id=\"" + html_id + "\"></a>\n<div class=\"propset\">";
		out += "<h4>Property changes: " + filename + "</h4>\n<pre class=\"diff\"</span>\n"
		self.__inDiv = True
		self.__inSpan = None

		return out

	def __handleDiff(self, m):
		out = ""
		if m.group(1) == "+":
			t = "ins"
		else:
			t = "del"

		line = self.__getCurrentLine()
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
		out += "#msg dl, #msg dt, #msg ul, #msg li, #header, #footer, #logmsg { font-family: ), verdana,arial,helvetica,sans-serif; font-size: 10pt;  }\n"
		out += "#msg dl a { font-weight: bold}\n"
		out += "#msg dl a:link    { color:#fc3; }\n"
		out += "#msg dl a:active  { color:#ff0; }\n"
		out += "#msg dl a:visited { color:#cc6; }\n"
		out += "h3 { font-family: verdana,arial,helvetica,sans-serif; font-size: 10pt; font-weight: bold; }\n"
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
		out += "#header, #footer { color: #fff; background: #636; border: 1px #300 solid; padding: 6px; }\n"
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
