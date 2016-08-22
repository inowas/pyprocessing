#! /usr/env python

import InowasFlopy

fp = InowasFlopy.InowasFlopy()


test = fp.from_files('./tests/testInput/testmodel')
#test = fp.from_webapi('http://localhost:8090/api', '855a9dcd-8c85-41e1-b520-ab26549b20de', 'cd8c12b4-d4a9-460e-822f-2a4cea9b469f')
