# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 15:33:06 2016

@author: aybulat
"""

import sys
from geoImage import RasterImage

input_file_name = sys.argv[1]
output_file_name = sys.argv[2]

r = RasterImage()
r.from_file(input_file_name)
r._name = output_file_name
newFile = r.makeImage()
print newFile
