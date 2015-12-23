#!/usr/bin/env python
#
# Akash Shende
#

import re
import sys
import json
import time
import traceback
import subprocess

'''
Regex to find issue number:
	re = r'\#(?P<issue>[\d]+)'
'''

__all__ = ['add_issue_details', 'mark_issue_resolved']

user = ''
passwd = ''

account_name = "akash0x53"
repo_name = "test-repo"

issue_url = 'https://api.bitbucket.org/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}'
comment_url = 'https://api.bitbucket.org/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}/comments'

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
	return set([num for num in re.findall(regex, msg, re.MULTILINE)])

def format_issue(number):
	title = get_issue(number).get('title')
	msg = u"#{0}: {1}\n".format(number, title)
	return msg

def get_issue(issue_id):
	'''
	Use bitbucket APIs to fetch issue details.

	#TODO: Using Request module. But but but... Mercurial python don't have requests
	module loaded, and you cant just import it here. Really need to dig into this
	but later..

	So i'm gonna use subprocess and curl.
	'''
	credentials = "{0}:{1}".format(user, passwd)
	url = issue_url.format(accountname=account_name, repo_slug=repo_name, issue_id=issue_id)
	default = {'title':  url}

	try:
		out = subprocess.check_output(["curl", "-s", "--user", credentials, url])
		res = json.loads(out)
		return res or default
	except:
		traceback.print_exc()
		return default

def change_status(issue):
	'''
	change issue status to resolved & assign back to reporter
	'''
	req_url = 'https://api.bitbucket.org/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}'
	url = req_url.format(accountname=account_name, repo_slug=repo_name, issue_id=issue["local_id"])

	reporter = issue["reported_by"]["username"]
	credentials = "{0}:{1}".format(user, passwd)
	payload = "status={status}&responsible={assignto}"
	payload = payload.format(status="resolved", assignto=reporter)

	try:
		out = subprocess.check_output(\
				["curl", "-X", "PUT", "-s", "--user", credentials, "--data", payload, url])
		return json.loads(out)
	except:
		pass

def post_comment(issue_id, repo, comment=''):
	'''
	Post comment on resolved issue, this will prompt you for message.
	'''
	url = comment_url.format(accountname=account_name, repo_slug=repo_name, issue_id=issue_id)
	credentials = "{0}:{1}".format(user, passwd)

	commit = "Commit: " + repo.hex() + "  \n"
	date = "Verify after build generated after " + time.ctime(time.time()) + "  \n"

	if comment:
		comment += "\n" + commit
	else:
		comment = commit + date

	payload = "content={comment}"
	payload = payload.format(comment=comment)

	try:
		out = subprocess.check_output(\
				["curl", "-X", "POST", "-s", "--user", credentials, "--data", payload, url])
		return json.loads(out)
	except:
		traceback.print_exc()


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

		if new_msg:
			_msg = '-'*10 + 'BEGIN COMMIT MSG' + '-'*10 + '\n' + _msg

		ctx._text = new_msg.encode("utf-8") + _msg.encode("utf-8")

		return orig_commitctx(ctx, err)

	repo.commitctx = func_commitctx

def mark_issue_resolved(repo, ui, *args, **kwargs):
	''' This smart push hook find issue number in outgoing changeset and mark all
	issues resolved. It prompts user to enter comment if user wants.

	Change status and assign back to reported:
		o https://api.bitbucket.org/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}
		o Method: PUT
		o parameters:
			- status=new|open|resolved|on hold|invalid
			- responsible = bitbucket userid

	Post comment:
		o https://api.bitbucket.org/1.0/repositories/{accountname}/{repo_slug}/issues/{issue_id}/comments
		o Method: POST
		o parameters:
			- content=comment msg

	'''
	tip = repo['tip']
	commit_msg = tip.description()

	global user, passwd

	user = ui.username()
	user = user[user.find("<")+1: user.find(">")]
	if user:
		passwd = ui.getpass(prompt="Enter Password:")

	for _id in find_issue_number(commit_msg):
		issue = get_issue(_id)
		if not issue.get('reported_by', ''):
			continue
		change_status(issue)
		extra_comment = ui.prompt("Enter Comment - hit enter to finish.", default='')
		post_comment(_id, tip, extra_comment)

