HG Hooks
=======

Hooks
----
1. `add_issue_details`  
    This execute on `hg commit`. Find issue numbers mentioned in commit message and
	fetched corresponding title from `Bitbucket` and add it to the original commit
	message.

	Usage:  
	Add following line in `.hgrc`

	```
	[hooks]  
	precommit = python:/path/to/hooks.py:add_issue_details  
	```

2. `mark_issue_resolved`
	This smart hook runs after you push your changeset to remote (bitbucket) repo.
	And not only mark mentioned issues resolved but also assign back to reporter.
	Also add commit message in bug report.

	Usage:
	Add following line in `hooks` section in your `.hgrc` file.

	```
	post-push = python:/path/to/hooks.py:mark_issue_resolved
	```



