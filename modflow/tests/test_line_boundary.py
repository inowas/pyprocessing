# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 16:19:59 2016

@author: aybulat
"""

import unittest
from imports.utils import line_boundary_interpolation


class Test_line_area_intersector(unittest.TestCase):

    def setUp(self):
        self.points = [[0., 0.], [400., 300.]]
        self.nx, self.ny = 11, 11
        self.point_vals = [[50,100], [50,100], [50,100]]
        self.stress_period_list = [0, 1, 2]
        self.interract_layers = [0, 1]
        self.xmin, self.xmax, self.ymin, self.ymax = 0., 400., 0., 400.
        self.line = [[0., 0.], [0., 300.], [400., 300.],
                     [400., 0.], [0., 0.]]
        self.layers_botm = [0,-10]
        self.strt_head_mode = 'warmed_up'
        self.stress_period_data = line_boundary_interpolation.give_SPD(points,
                                                                 point_vals,
                                                                 line,
                                                                 stress_period_list,
                                                                 interract_layers,
                                                                 xmax, xmin, ymax, ymin, nx, ny,
                                                                 layers_botm,
                                                                 strt_head_mode)

    def tearDown(self):
        self.points = None
        self.nx, self.ny = None
        self.point_vals = None
        self.stress_period_list = None
        self.interract_layers = None
        self.xmin, self.xmax, self.ymin, self.ymax = None
        self.line = None
        self.layers_botm = [0,-10]
        self.strt_head_mode = None
        self.stress_period_data = None

    def check_number_of_stress_periods(self):
        if self.strt_head_mode == 'warmed_up':
            self.assertEqual(len(self.stress_period_data),
                             len(self.stress_period_list) + 1)
        else:
            self.assertEqual(len(self.stress_period_data),
                             len(self.stress_period_list))


if __name__ == '__main__':
    unittest.main()