#! /usr/env python

import InowasFlopy
import sys

fp = InowasFlopy.InowasFlopy()

api_url = sys.argv[1]
data_folder = sys.argv[2]
model_id = sys.argv[3]
api_key = sys.argv[4]

fp.from_webapi(api_url, data_folder, model_id, api_key)
