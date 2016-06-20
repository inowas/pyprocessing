#! /usr/env python

import sys
import Modflow

# usage: python modflowResult.py data result_raster.json
workspace = sys.argv[1]   # this contains the path to the project, eg. ../data/modflow/123112443-1112212-3433317/
input_file = sys.argv[2]  # this contains a filename, eg. /tmp/modflow/filename.in
output_file = sys.argv[3]  # this contains a filename, eg. /tmp/modflow/filename.out

modflow = Modflow.Modflow(workspace)
modflow.set_input_file(input_file)
modflow.set_output_file(output_file)
modflow.get_result()