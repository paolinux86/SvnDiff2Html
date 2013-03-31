# -*- coding: utf-8 -*-
from svndiff2html.SvnDiff2Html import SvnDiff2Html

def __callCommand(command):
	import os, subprocess

	oldLang = os.environ['LANG']
	os.environ['LANG'] = 'C'
	try:
		result = subprocess.check_output(command, shell = True)
	finally:
		os.environ['LANG'] = oldLang

	return result

diff = __callCommand("svnlook diff /svn/invaders3/ -r 1")
sdiff = SvnDiff2Html(diff)
# print sdiff.output_css()

print sdiff.output_formatted_diff()



diff = __callCommand("svnlook diff /svn/repos_mine/ -r 33")
sdiff = SvnDiff2Html(diff)
# print sdiff.output_css()

print sdiff.output_formatted_diff()



diff = 	__callCommand("svnlook diff /svn/repos_mine/ -r 18")
sdiff = SvnDiff2Html(diff)
# print sdiff.output_css()

print sdiff.output_formatted_diff()
