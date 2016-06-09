#! /usr/env python

import sys
import Modflow

base_url = sys.argv[1]    # this contains a string, eg. http://localhost:8090 or http://app.dev.inowas.com
executable = sys.argv[2]  # this contains a string of the executable name, eg. mf2005 of /usr/local/lib/mf2005
workspace = sys.argv[3]   # this contains the path to the project, eg. ../data/modflow/123112443-1112212-3433317/
input_file = sys.argv[4]  # this contains a filename, eg. /tmp/modflow/filename.in

modflow = Modflow.Modflow(workspace)
modflow.set_input_file(input_file)
modflow.set_base_url(base_url)
modflow.set_executable(executable)
modflow.create_and_run()
