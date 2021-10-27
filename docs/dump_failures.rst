Dump Failures
**************************

This script will display information about failing tests given a push.

DUMP_FAILURES_EDIT_COMMAND
=========================
This is an environment variable in ``dump_failures`` file that is needed to be set to automatically open failures in vim.

How to set Environment Variable
-------------------------

At the command line:

>>> export DUMP_FAILURES_EDIT_COMMAND="vim +/{test} +:vnew +':let f=append(1,{context})' /path/to/mozilla-central/{manifest}"

Run ``dump_failures`` file in terminal using citools

 >>> citools push failures arg=branch arg=rev

 Expected output:

 display failures in vim






