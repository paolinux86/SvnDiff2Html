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

# svn log svn://localhost/svn/invaders3 -r 0:1 -v | grep -E "^   [A-Z]{1} " | sed -r "s#^   ([A-Z]{1}) /#\1 #g"

diff = __callCommand("svnlook diff /svn/invaders3/ -r 1")
files = __callCommand("svnlook changed /svn/invaders3/ -r 1")
sdiff = SvnDiff2Html(diff, files)
# print sdiff.output_css()

print sdiff.output_file_lists()
print sdiff.output_formatted_diff()



diff = __callCommand("svnlook diff /svn/repos_mine/ -r 33")
files = __callCommand("svnlook changed /svn/repos_mine/ -r 33")
sdiff = SvnDiff2Html(diff, files)
# print sdiff.output_css()

print sdiff.output_file_lists()
print sdiff.output_formatted_diff()



diff = 	__callCommand("svnlook diff /svn/repos_mine/ -r 18")
files = __callCommand("svnlook changed /svn/repos_mine/ -r 18")
sdiff = SvnDiff2Html(diff, files)
# print sdiff.output_css()

print sdiff.output_file_lists()
print sdiff.output_formatted_diff()
