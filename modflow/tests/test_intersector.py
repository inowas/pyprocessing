# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 16:04:21 2016

@author: aybulat
"""
import unittest
from imports.utils import intersector


class Test_line_area_intersectr(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_if_output_equals_to_expected(self):

        nx, ny = 11, 11
        xmin, xmax, ymin, ymax = 0., 400., 0., 400.
        line = [[0., 0.], [0., 300.], [400., 300.],
                 [400., 0.], [0., 0.]]

        line_cols, line_rows = intersector.line_area_intersect(line, xmax, xmin, ymax,
                                                   ymin, nx, ny)

        control_line_cols = [0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,10,10,10,
                             10,10,10,10,10,10,9,8,7,6,5,4,3,2,1]
        control_line_rows = [0,1,2,3,4,5,6,7,8,8,8,8,8,8,8,8,8,8,8,
                             7,6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0]


        self.assertEqual(line_cols.tolist(), control_line_cols)
        self.assertEqual(line_rows.tolist(), control_line_rows)

if __name__ == '__main__':
    unittest.main()