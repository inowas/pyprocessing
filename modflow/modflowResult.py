#! /usr/env python

import sys

workspace = sys.argv[1]   # this contains the path to the project, eg. ../data/modflow/123112443-1112212-3433317/
input_file = sys.argv[2]  # this contains a filename, eg. /tmp/modflow/filename.in
output_file = sys.argv[3]  # this contains a filename, eg. /tmp/modflow/filename.out

modflow = Modflow(workspace)
modflow.setInputFile(input_file)
modflow.setOutputFile(output_file)
modflow.getResult()
