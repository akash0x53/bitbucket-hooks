#!/usr/bin/env python
#
# Akash Shende 
# 

import re
import sys
import json
import traceback
import subprocess

'''
Regex to find issue number:
	re = r'\#(?P<issue>[\d]+)'
'''

__all__ = ['add_issue_details']

user = ''
passwd = ''

def find_issue_number(msg):
	'''
	>>> from main import find_issue_number
	>>> for i in find_issue_number("#1234 #1 1233(plain number) @231(refrence) 23>23(compare) #9999#887"): 
		...     print i
		... 
		1234
		1
		9999
		887

	'''
	regex = r'\#(?P<issue>[\d]+)'
	return (num for num in re.findall(regex, msg, re.MULTILINE))

def format_issue(number):
	title = fetch_issue_title(number)
	msg = u"#{0}: {1}\n".format(number, title)
	return msg

def fetch_issue_title(issue_id):
	'''
	Use bitbucket APIs to fetch issue details.
	
	#TODO: Using Request module. But but but... Mercurial python don't have requests 
	module loaded, and you cant just import it here. Really need to dig into this
	but later..
	
	So i'm gonna use subprocess and curl.
	'''
	req_url = "https://bitbucket.org/api/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}"
	url = req_url.format(accountname="anoosmar", repo_slug="vaultize-issues", issue_id=issue_id)
	credentials = "{0}:{1}".format(user, passwd)
	default = 'https://bitbucket.org/anoosmar/vaultize-issues/issues/' + issue_id
	
	try:
		out = subprocess.check_output(["curl", "-s", "--user", credentials, url])
		res = json.loads(out)
		title = res.get('title', default)
		return title
	except:
		pass
		return default

def add_issue_details(repo, ui, *args, **kwargs):
	'''
	Find issue numbers --followed by # -- from commit message, fetch issue title
	from Bitbucket and add to original commit message.
	'''
	orig_commitctx = repo.commitctx

	def func_commitctx(ctx, err):
		_msg = ctx._text
		new_msg = ''
		global user, passwd

		user = ui.username()
		user = user[user.find("<")+1: user.find(">")]
		if user:
			passwd = ui.getpass(prompt="Enter Password:")

		for idx, issue_num in enumerate(find_issue_number(_msg), 1):
			new_msg += ''.join(format_issue(issue_num))

		if new_msg:
			_title = u''.join(_msg.split('\n', 1)[0]) + '\n'
			_msg = u''.join(_msg.split('\n', 1)[1:])
			new_msg = _title + new_msg

		if _msg:
			_msg = '-'*10 + 'BEGIN COMMIT MSG' + '-'*10 + '\n' + _msg
		
		ctx._text = new_msg.encode("utf-8") + _msg.encode("utf-8")
		
		return orig_commitctx(ctx, err)

	repo.commitctx = func_commitctx
