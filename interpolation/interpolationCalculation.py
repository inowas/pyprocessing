#! /usr/env python

import sys
from interpolation import Interpolation

input_file_name = sys.argv[1]
output_file_name = ''

if sys.argv[2]:
    output_file_name = sys.argv[2]

ip = Interpolation()
ip.from_file(input_file_name)
ip.calculate()
ip.render_output(output_file_name)
