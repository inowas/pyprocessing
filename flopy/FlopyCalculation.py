#! /usr/env python

import InowasFlopy
import sys

fp = InowasFlopy.InowasFlopy()


data_folder = sys.argv[1]
calculation_url = sys.argv[2]
model_url = sys.argv[3]
submit_heads_url = sys.argv[4]
api_key = sys.argv[5]

fp.from_webapi(data_folder, calculation_url, model_url, submit_heads_url, api_key)
