#! /usr/env python

import sys

base_url = sys.argv[1]    # this contains a string, eg. http://localhost:8090 or http://app.dev.inowas.com
executable = sys.argv[2]  # this contains a string of the executable name, eg. mf2005 of /usr/local/lib/mf2005
workspace = sys.argv[3]   # this contains the path to the project, eg. ../data/modflow/123112443-1112212-3433317/
input_file = sys.argv[4]  # this contains a filename, eg. /tmp/modflow/filename.in

modflow = Modflow(workspace)
modflow.setInputFile(input_file)
modflow.setBaseUrl(base_url)
modflow.setExecutable(executable)
modflow.create_and_run()
