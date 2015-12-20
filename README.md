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



